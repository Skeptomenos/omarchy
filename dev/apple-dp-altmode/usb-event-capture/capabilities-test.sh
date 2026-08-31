#!/bin/bash
set -euo pipefail
umask 077
stage=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
reader=$stage/capabilities.sh
fixture=$(mktemp -d "${DEV147_TEST_ROOT:-${TMPDIR:-/tmp}}/dev147-trace-caps.XXXXXXXXXX")
trace_root=$fixture/sys/kernel/tracing
mkdir -p "$trace_root"
fail() { printf 'FAIL: %s\nFixture retained: %s\nVERDICT: FAIL\n' "$1" "$fixture" >&2; exit 1; }
pass() { printf 'PASS: %s\n' "$1"; }
sandbox=(/usr/bin/bwrap --unshare-all --die-with-parent --new-session --clearenv --tmpfs / --ro-bind /usr /usr --symlink usr/bin /bin --symlink usr/lib /lib --symlink usr/lib /lib64 --ro-bind "$fixture/sys" /sys --chdir / --setenv PATH /usr/bin:/bin --setenv LANG C.UTF-8 --cap-drop ALL)
probe_status=0
/usr/bin/timeout --kill-after=2s 5s "${sandbox[@]}" --uid 0 --gid 0 /bin/bash -c '[[ $EUID == 0 && ! -e /proc && ! -e /run && ! -e /home && ! -e /dev && -d /sys/kernel/tracing ]]' > "$fixture/sandbox.stdout" 2> "$fixture/sandbox.stderr" || probe_status=$?
(( probe_status == 0 )) || fail "private namespace unavailable (exit $probe_status); no fallback allowed"
pass 'private root with no host sysfs, procfs, runtime, home or devices'
paths=(trace_clock current_tracer tracing_on)
for event in rpm_suspend rpm_resume rpm_status rpm_return_int; do paths+=("events/rpm/$event/format"); done
for event in xhci_urb_enqueue xhci_urb_dequeue xhci_urb_giveback xhci_queue_trb xhci_handle_transfer xhci_handle_port_status; do paths+=("events/xhci-hcd/$event/format"); done
for event in usb_alloc_dev usb_set_device_state; do paths+=("events/usbcore/$event/format"); done
for relative in "${paths[@]}"; do
  mkdir -p "$(dirname -- "$trace_root/$relative")"
  printf 'fixture metadata: %s\n' "$relative" > "$trace_root/$relative"
done
printf 'must-not-read\n' > "$trace_root/trace"
printf 'must-not-read\n' > "$trace_root/trace_pipe"
printf 'must-not-read\n' > "$trace_root/available_events"
run_reader() {
  status=0
  /usr/bin/timeout --kill-after=2s 5s "${sandbox[@]}" --uid 0 --gid 0 --ro-bind "$reader" /capabilities.sh /bin/bash /capabilities.sh "$@" > "$fixture/result.stdout" 2> "$fixture/result.stderr" || status=$?
  output=$(< "$fixture/result.stdout")
}
run_reader
(( status == 0 )) || fail "complete inventory expected exit 0; got $status"
[[ $output == *'INVENTORY complete'* && $output != *must-not-read* ]] || fail 'complete inventory or read scope'
(( $(/usr/bin/grep -c '^BEGIN /sys/kernel/tracing/' "$fixture/result.stdout") == ${#paths[@]} )) || fail 'fixed inventory count'
[[ ! -s $fixture/result.stderr ]] || fail 'complete inventory stderr'
for relative in "${paths[@]}"; do
  [[ $(< "$trace_root/$relative") == "fixture metadata: $relative" ]] || fail 'fixture content changed'
done
pass 'real root entrypoint reads only the fixed metadata inventory'
run_reader <<< 'must-not-read-from-stdin'
(( status == 0 )) && [[ $output != *must-not-read-from-stdin* ]] || fail 'stdin affected the fixed inventory'
pass 'stdin supplies no paths or instructions'
run_reader --help
(( status == 64 )) && [[ $output == 'REFUSED arguments' ]] || fail 'argument refusal'
pass 'arguments are refused before the inventory'
status=0
/usr/bin/timeout --kill-after=2s 5s "${sandbox[@]}" --uid 1001 --gid 1001 --ro-bind "$reader" /capabilities.sh /bin/bash /capabilities.sh > "$fixture/nonroot.stdout" 2> "$fixture/nonroot.stderr" || status=$?
(( status == 77 )) && [[ $(< "$fixture/nonroot.stdout") == 'REFUSED root_required' && ! -s $fixture/nonroot.stderr ]] || fail 'non-root invocation refusal'
pass 'non-root entrypoint is refused before reads'
mv -- "$trace_root/current_tracer" "$fixture/current_tracer.saved"
run_reader
(( status == 1 )) && [[ $output == *'STATUS missing'* && $output == *'INVENTORY incomplete'* ]] || fail 'missing metadata is concealed'
mv -- "$fixture/current_tracer.saved" "$trace_root/current_tracer"
pass 'missing file yields an incomplete inventory'
mv -- "$trace_root/tracing_on" "$fixture/tracing_on.saved"
ln -s /usr/bin/bash "$trace_root/tracing_on"
run_reader
(( status == 1 )) && [[ $output == *'STATUS unsafe_symlink'* ]] || fail 'file symlink refusal'
mv -- "$trace_root/tracing_on" "$fixture/tracing_on.link"
mv -- "$fixture/tracing_on.saved" "$trace_root/tracing_on"
mv -- "$trace_root/events/rpm" "$trace_root/events/rpm.saved"
ln -s rpm.saved "$trace_root/events/rpm"
run_reader
(( status == 1 )) && [[ $output == *'STATUS unsafe_symlink'* ]] || fail 'parent symlink refusal'
mv -- "$trace_root/events/rpm" "$fixture/rpm.link"
mv -- "$trace_root/events/rpm.saved" "$trace_root/events/rpm"
pass 'file and parent symlinks are refused'
mv -- "$trace_root/tracing_on" "$fixture/tracing_on.saved"
mkfifo "$trace_root/tracing_on"
run_reader
(( status == 1 )) && [[ $output == *'STATUS unsafe_type'* ]] || fail 'FIFO refusal or blocked read'
mv -- "$trace_root/tracing_on" "$fixture/tracing_on.fifo"
mv -- "$fixture/tracing_on.saved" "$trace_root/tracing_on"
pass 'special files are refused without reading'
chmod 000 "$trace_root/tracing_on"
run_reader
(( status == 1 )) && [[ $output == *'STATUS unreadable'* ]] || fail 'unreadable metadata is concealed'
chmod 600 "$trace_root/tracing_on"
pass 'unreadable metadata yields an incomplete inventory'
printf '%16384s' '' > "$trace_root/trace_clock"
run_reader
(( status == 0 )) && [[ $output == *'BYTES 16384'* ]] || fail 'exact file limit rejected'
printf '%16385s' '' > "$trace_root/trace_clock"
run_reader
(( status == 1 )) && [[ $output == *'STATUS truncated'* && $output == *'BYTES 16384'* ]] || fail 'oversized file is not bounded and incomplete'
(( $(/usr/bin/wc -c < "$fixture/result.stdout") < 262144 )) || fail 'total output exceeds 256 KiB'
pass '16 KiB file boundary and total output cap'
for relative in "${paths[@]}"; do printf '%16384s' '' > "$trace_root/$relative"; done
run_reader
(( status == 0 )) || fail 'full-size fixed inventory did not complete'
(( $(/usr/bin/wc -c < "$fixture/result.stdout") < 262144 )) || fail 'all full-size files exceed 256 KiB'
pass 'entire fixed inventory remains below 256 KiB'
for script in "$reader" "${BASH_SOURCE[0]}"; do /bin/bash -n "$script" || fail 'Bash syntax'; done
if /usr/bin/grep -nE '^[[:space:]]*#[^!]' "$reader" "${BASH_SOURCE[0]}"; then fail 'code comment'; fi
pass 'Bash syntax and no code comments'
printf 'Fixture retained: %s\nVERDICT: PASS\n' "$fixture"
