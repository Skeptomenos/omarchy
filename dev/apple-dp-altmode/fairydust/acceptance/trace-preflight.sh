#!/bin/bash
set -euo pipefail
[[ $# == 0 && $EUID != 0 ]] || { printf 'Run this launcher as the normal user without arguments.\n' >&2; exit 2; }
umask 077
root=/home/david/Work/dev147-fairydust-acceptance-20260905
mkdir -p -m 700 -- "$root"
[[ -d $root && ! -L $root && -O $root && $(stat -c '%a' "$root") == 700 ]] || { printf 'Expected a private owned result root.\n' >&2; exit 2; }
results=$(mktemp -d "$root/trace-preflight.XXXXXXXX")
if /usr/bin/sudo /bin/bash -s > "$results/report.txt" 2> "$results/stderr.log" <<'DEV147_TRACE_PREFLIGHT'
set -uo pipefail
release=$(/usr/bin/uname -r)
printf 'Running release: %s\n' "$release"
[[ $release == "7.1.12-dev147-fairydust1" ]] || { printf 'FAIL: unexpected kernel release.\n'; exit 2; }
status=0
for file in \
  /sys/kernel/tracing/available_tracers \
  /sys/kernel/tracing/trace_clock \
  /sys/kernel/tracing/events/dcp/iomfb_push/format \
  /sys/kernel/tracing/events/dcp/dcp_send_msg/format \
  /sys/kernel/tracing/events/dcp/dcp_recv_msg/format \
  /sys/kernel/tracing/events/dcp/iomfb_callback/format \
  /sys/kernel/tracing/events/tps6598x/cd321x_data_status/format \
  /sys/kernel/tracing/events/tps6598x/cd321x_irq/format; do
  printf '\nFILE %s\n' "$file"
  if [[ ! -e $file ]]; then
    printf 'MISSING: %s\n' "$file"
    status=1
  elif ! /usr/bin/cat -- "$file"; then
    printf 'READ FAILED: %s\n' "$file"
    status=1
  fi
done
printf '\nRead-only capability preflight exit: %s\n' "$status"
exit "$status"
DEV147_TRACE_PREFLIGHT
then
  status=0
else
  status=$?
fi
printf '%s\n' "$status" > "$results/exit-status"
printf 'Trace preflight exit: %s. Private result files: %s\n' "$status" "$results"
exit "$status"
