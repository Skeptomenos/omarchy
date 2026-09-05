#!/bin/bash
set -euo pipefail
[[ $EUID != 0 && $# == 1 && $1 == "monitor-power" ]] || { printf 'Run as the normal user with the single argument monitor-power.\n' >&2; exit 2; }
capture_mode=$1
umask 077
root=/home/david/Work/dev147-clear-wait-trial/negotiation
[[ -d $root && ! -L $root && -O $root && $(stat -c '%a' "$root") == 700 ]] || exit 2
results=$(mktemp -d "$root/trace-capture.XXXXXXXX")
if /usr/bin/sudo /bin/bash -s -- "$capture_mode" > "$results/report.txt" 2> "$results/stderr.log" <<'DEV147_TRACE_CAPTURE'
set -euo pipefail
[[ $# == 1 && $1 == "monitor-power" ]] || { printf 'FAIL: invalid capture mode.\n'; exit 2; }
capture_mode=$1
printf 'CAPTURE_MODE %s\n' "$capture_mode"
[[ $(/usr/bin/uname -r) == "7.1.12-dev147-clearwait100" ]] || { printf 'FAIL: unexpected kernel release.\n'; exit 2; }
exec 3>/dev/tty
printf 'BOOT_ID '; /usr/bin/cat /proc/sys/kernel/random/boot_id
instance=$(/usr/bin/mktemp -d /sys/kernel/tracing/instances/dev147-negotiation.XXXXXXXX)
cleanup() {
  status=$?
  trap - EXIT INT TERM HUP
  set +e
  printf 'CLEANUP_BEGIN %s\n' "$instance"
  printf '0\n' > "$instance/tracing_on" || status=1
  printf '0\n' > "$instance/events/enable" || status=1
  printf 'STOP_UPTIME '; /usr/bin/cat /proc/uptime || status=1
  stats_found=0
  for file in "$instance"/per_cpu/cpu*/stats; do
    [[ -f $file ]] || continue
    stats_found=1
    printf 'CPU_STATS %s\n' "${file#"$instance"/}"
    /usr/bin/cat -- "$file" || status=1
  done
  if (( stats_found == 0 )); then printf 'FAIL: per-CPU stats missing.\n'; status=1; fi
  printf 'TRACE_BEGIN\n'
  /usr/bin/cat -- "$instance/trace" || status=1
  printf '\nTRACE_END\n'
  if /usr/bin/rmdir -- "$instance"; then
    printf 'CLEANUP_REMOVED %s\n' "$instance"
  else
    printf 'FAIL: own instance removal failed: %s\n' "$instance"
    status=1
  fi
  printf 'CAPTURE_EXIT %s (overrun statistics require inspection)\n' "$status"
  exit "$status"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM HUP
printf '0\n' > "$instance/tracing_on"
printf '0\n' > "$instance/events/enable"
printf 'nop\n' > "$instance/current_tracer"
printf 'mono\n' > "$instance/trace_clock"
printf '4096\n' > "$instance/buffer_size_kb"
for event in iomfb_push iomfb_callback dcp_send_msg dcp_recv_msg; do
  filter='devname == "271c00000.dcp"'
  if [[ $event == "dcp_send_msg" || $event == "dcp_recv_msg" ]]; then filter+=' && endpoint == 55'; fi
  printf '%s\n' "$filter" > "$instance/events/dcp/$event/filter"
  printf 'FILTER %s ' "$event"; /usr/bin/cat "$instance/events/dcp/$event/filter"
  printf '1\n' > "$instance/events/dcp/$event/enable"
done
for event in tps6598x_status tps6598x_power_status; do
  [[ -f $instance/events/tps6598x/$event/enable ]] || { printf 'FAIL: required event missing: %s\n' "$event"; exit 1; }
  printf '1\n' > "$instance/events/tps6598x/$event/enable"
  printf 'REQUIRED_EVENT %s enabled; no port identity in format\n' "$event"
done
for event in cd321x_data_status cd321x_irq; do
  if [[ -f $instance/events/tps6598x/$event/enable ]]; then
    printf '1\n' > "$instance/events/tps6598x/$event/enable"
    printf 'OPTIONAL_EVENT %s enabled; no port identity in format\n' "$event"
  else
    printf 'OPTIONAL_EVENT %s unavailable\n' "$event"
  fi
done
printf 'INSTANCE %s\nCLOCK ' "$instance"; /usr/bin/cat "$instance/trace_clock"
printf 'BUFFER_KB_PER_CPU '; /usr/bin/cat "$instance/buffer_size_kb"
printf 'START_UPTIME '; /usr/bin/cat /proc/uptime
printf '1\n' > "$instance/tracing_on"
printf 'READY: capture active for 45 seconds. Keep ALL USB cables connected. Turn the LG27 off with its power button, wait 5 seconds, then turn it on once. Make no further changes until capture ends.\n' >&3
/usr/bin/sleep 45
printf 'CAPTURED: 45-second window ended; no hardware acceptance claim.\n'
DEV147_TRACE_CAPTURE
then
  status=0
else
  status=$?
fi
printf '%s\n' "$status" > "$results/exit-status"
printf 'Trace capture exit: %s. Private result files: %s\n' "$status" "$results"
exit "$status"
