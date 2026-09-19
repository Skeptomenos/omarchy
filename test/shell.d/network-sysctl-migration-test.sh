#!/bin/bash

set -euo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"
require_command sysctl

test_tmp=$(mktemp -d)
trap 'rm -rf "$test_tmp"' EXIT
export CALL_LOG="$test_tmp/calls" SYSCTL_STATE="$test_tmp/runtime" REAL_SYSCTL
REAL_SYSCTL=$(command -v sysctl)
mkdir -p "$test_tmp/bin" "$test_tmp/home" "$test_tmp/queue/migrations"
conf="$test_tmp/99-omarchy-sysctl.conf"
marker="$test_tmp/markers/1789841147.sh"
# Redirect only fixed paths. Never inspect the host's pacman lock or sysctls.
sed "s|/var/lib/pacman/db.lck|$test_tmp/db.lck|" "$ROOT/bin/omarchy-migrate" >"$test_tmp/migrate"
cat >"$test_tmp/bin/sudo" <<'SH'
#!/bin/bash
[[ $1 == "sysctl" ]] || exit 97
echo apply >>"$CALL_LOG"
exec "$@"
SH
cat >"$test_tmp/bin/sysctl" <<'SH'
#!/bin/bash
set -euo pipefail
case "$1" in
  --dry-run) exec "$REAL_SYSCTL" "$@" ;;
  -n) awk -v key="$2" '$1 == key { print $3; found=1 } END { exit !found }' "$SYSCTL_STATE" ;;
  -p|--pattern)
    [[ ${APPLY_MODE:-success} != "error" ]] || exit 1
    values=$("$REAL_SYSCTL" --dry-run "$@")
    if [[ ${APPLY_MODE:-success} != "noop" ]]; then
      printf '%s\n' "$values" | cat "$SYSCTL_STATE" - | awk '$2 == "=" { v[$1]=$3 } END { for (key in v) print key " = " v[key] }' >"$SYSCTL_STATE.next"
      mv "$SYSCTL_STATE.next" "$SYSCTL_STATE"
    fi
    ;;
  *) exit 97 ;;
esac
SH
cat >"$test_tmp/bin/omarchy-notification-dismiss" <<'SH'
#!/bin/bash
exit 0
SH
chmod +x "$test_tmp/bin/"*
export PATH="$test_tmp/bin:$PATH" HOME="$test_tmp/home"
export OMARCHY_PATH="$test_tmp/queue" OMARCHY_MIGRATION_STATE="$test_tmp/markers"

reset_runtime() {
  printf '%s\n' 'net.ipv4.tcp_mtu_probing = 0' 'net.core.default_qdisc = fq_codel' \
    'net.ipv4.tcp_congestion_control = cubic' 'vm.swappiness = 60' >"$SYSCTL_STATE"
}
run_queue() {
  : >"$CALL_LOG"
  bash "$test_tmp/migrate" >"$test_tmp/output" 2>&1
}
pending() {
  if run_queue; then fail "$1 must fail"; fi
  [[ ! -e $marker ]] || fail "$1 must leave the successor pending"
  cmp "$conf" "$test_tmp/before" || fail "$1 preserves the installed config"
  pass "$1 leaves the successor pending and preserves the installed config"
}

# Establish the deployed false completion with the unchanged old migration.
printf '# Historical ARM payload\nnet.ipv4.tcp_mtu_probing=1\n' >"$conf"
cp "$conf" "$test_tmp/before"
reset_runtime
sed "s|/etc/sysctl.d/99-omarchy-sysctl.conf|$conf|g" "$ROOT/migrations/1789444042.sh" >"$OMARCHY_PATH/migrations/1789444042.sh"
run_queue
[[ -f $OMARCHY_MIGRATION_STATE/1789444042.sh && $(sysctl -n net.ipv4.tcp_congestion_control) == "cubic" && $(sysctl -n net.core.default_qdisc) == "fq_codel" ]] || fail 'old migration reproduces false completion'
[[ $(cat "$CALL_LOG") == "apply" ]] || fail 'old migration loaded the MTU-only file successfully'
pass 'old migration marks completion after sysctl -p exits 0 with cubic/fq_codel still active'

sed "s|/etc/sysctl.d/99-omarchy-sysctl.conf|$conf|g" "$ROOT/migrations/1789841147.sh" >"$OMARCHY_PATH/migrations/1789841147.sh"
pending 'MTU-only installed payload'
[[ ! -s $CALL_LOG ]] || fail 'invalid payload must fail before privilege escalation'

cat >"$conf" <<'CONF'
# Administrator comment must survive.
net.ipv4.tcp_mtu_probing = 1
net/core/default_qdisc = fq
net.ipv4.tcp_congestion_control = bbr
vm.swappiness = 42
CONF
cp "$conf" "$test_tmp/before"
APPLY_MODE=noop pending 'successful sysctl load without changed kernel values'
[[ $(cat "$CALL_LOG") == "apply" ]] || fail 'no-effect case reaches the apply operation'
APPLY_MODE=error pending 'failed sysctl load'
run_queue
[[ -f $marker && $(cat "$CALL_LOG") == "apply" ]] || fail 'successful apply records completion'
[[ $(sysctl -n net.ipv4.tcp_mtu_probing) == "1" && $(sysctl -n net.core.default_qdisc) == "fq" && $(sysctl -n net.ipv4.tcp_congestion_control) == "bbr" ]] || fail 'all network postconditions hold'
[[ $(sysctl -n vm.swappiness) == "60" ]] || fail 'network repair must not apply VM tuning'
cmp "$conf" "$test_tmp/before" || fail 'successful apply preserves administrator edits'
pass 'successful network-only apply verifies values before completion and preserves custom VM tuning'

rm "$marker"
run_queue
[[ -f $marker && ! -s $CALL_LOG ]] || fail 'already-applied state requires no privileged operation'
run_queue
[[ ! -s $CALL_LOG ]] || fail 'completed migration does not replay'
pass 'already-applied and completed states do not repeat privilege requests'

rm "$marker"
printf 'net.ipv4.tcp_congestion_control = cubic\n' >>"$conf"
cp "$conf" "$test_tmp/before"
pending 'last-value custom override even when the running state is already BBR/fq'
[[ ! -s $CALL_LOG ]] || fail 'conflicting custom value must not be applied or overwritten'
rm "$conf"
if run_queue; then fail 'missing installed file must fail'; fi
[[ ! -e $marker && ! -e $conf && ! -s $CALL_LOG ]] || fail 'missing file remains pending without creating config'
pass 'missing installed file remains pending without copying source defaults'
