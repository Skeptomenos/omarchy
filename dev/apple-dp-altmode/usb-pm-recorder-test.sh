#!/bin/bash
set -euo pipefail
stage=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
reader=$stage/usb-pm-recorder.sh
fixture=$(mktemp -d "${DEV147_TEST_ROOT:-${TMPDIR:-/tmp}}/dev147-usb-pm-fixture.XXXXXXXXXX")
fixture_root=$fixture/controller
mkdir -p "$fixture_root/xhci-hcd.7.auto/usb3" "$fixture_root/xhci-hcd.7.auto/usb4"
fail() { printf 'FAIL: %s\n' "$1" >&2; exit 1; }
check() { jq -e "$1" <<< "$snapshot" >/dev/null || fail "$2"; printf 'PASS: %s\n' "$2"; }
capture() { snapshot=$(timeout --kill-after=2s 5s /bin/bash "$reader" --sample "$fixture_root"); }
refuse() {
  local status=0
  timeout --kill-after=2s 5s /bin/bash "$reader" "$@" > "$fixture/refused.stdout" 2> "$fixture/refused.stderr" || status=$?
  (( status == 64 )) || fail "invalid invocation returned $status"
  [[ ! -s $fixture/refused.stdout ]] || fail 'invalid invocation wrote a snapshot'
}
capture
check '.sample == 1 and (.objects | map(.path)) == [".","xhci-hcd.7.auto","xhci-hcd.7.auto/usb3","xhci-hcd.7.auto/usb4"]' 'roots-only discovery'
check '.begin.wall != "" and .end.wall != "" and (.end.uptime_seconds | tonumber) >= (.begin.uptime_seconds | tonumber)' 'sample timestamps'
check 'all(.objects[]; .inode != null and .state == "observed")' 'object inode identities'
check 'all(.objects[].attributes[]; .status == "missing" and .value == null)' 'missing attributes stay missing'
hub=$fixture_root/xhci-hcd.7.auto/usb3/3-1
controls=$hub/3-1.4
mkdir -p "$controls/power" "$hub/power" "$hub/3-1:1.0" "$hub/3-1.4/3-1.4.2" "$fixture_root/phy/power" "$fixture_root/xhci-hcd.7.auto/usb3/usb3-port1/power"
printf '9\n' > "$hub/devnum"
printf '043e\n' > "$hub/idVendor"
printf '9a60\n' > "$hub/idProduct"
printf 'auto\n' > "$hub/power/control"
printf 'suspended\n' > "$hub/power/runtime_status"
printf '100\n' > "$hub/power/runtime_active_time"
printf '200\n' > "$hub/power/runtime_suspended_time"
printf '2000\n' > "$hub/power/autosuspend_delay_ms"
printf 'disabled\n' > "$hub/power/wakeup"
printf 'disabled\n' > "$hub/power/usb2_hardware_lpm"
printf '10\n' > "$controls/devnum"
printf '043e\n' > "$controls/idVendor"
printf '9a70\n' > "$controls/idProduct"
printf 'unsafe "quoted" \\ value\nsecond\tline\n' > "$controls/power/control"
printf 'sensitive-serial\n' > "$controls/serial"
printf 'sensitive-product\n' > "$controls/product"
printf 'sensitive-config\n' > "$controls/configusb_mode"
printf 'excluded-port\n' > "$fixture_root/xhci-hcd.7.auto/usb3/usb3-port1/power/autosuspend_delay_ms"
printf 'excluded-phy\n' > "$fixture_root/phy/power/autosuspend_delay_ms"
mkdir "$controls/power/runtime_status"
printf '123\n' > "$controls/power/runtime_active_time"
chmod 000 "$controls/power/runtime_active_time"
capture
before=$snapshot
check '(.objects | length) == 6 and ([.objects[].path | select(endswith("3-1.4"))] | length) == 1' 'two nested USB levels and excluded interface/deeper/PHY/port paths'
check '.objects[] | select(.path | endswith("/3-1")) | .attributes.devnum.value == "9" and .attributes.idVendor.value == "043e" and .attributes.idProduct.value == "9a60" and .attributes["power/runtime_status"].value == "suspended" and .attributes["power/usb2_hardware_lpm"].value == "disabled"' 'USB identities and PM allowlist'
check '.objects[] | select(.path | endswith("3-1.4")) | .attributes["power/control"].value == "unsafe \"quoted\" \\ value\nsecond\tline"' 'safe JSON escaping'
check '.objects[] | select(.path | endswith("3-1.4")) | .attributes["power/runtime_active_time"].status == "unreadable" and .attributes["power/runtime_active_time"].value == null and .attributes["power/runtime_status"].status == "unsafe_type"' 'unreadable and unsafe attributes are distinct from missing'
[[ $snapshot != *sensitive-* && $snapshot != *excluded-* ]] || fail 'out-of-scope contents leaked'
printf 'PASS: excluded identity strings\n'
printf '%4194304s' '' > "$hub/power/control"
status=0
timeout --kill-after=2s 5s /bin/bash "$reader" --sample "$fixture_root" > "$fixture/encoding-failure.stdout" 2> "$fixture/encoding-failure.stderr" || status=$?
(( status != 0 && status != 124 && status != 137 )) || fail 'object encoding failure was concealed or timed out'
[[ ! -s $fixture/encoding-failure.stdout ]] || fail 'object encoding failure emitted an incomplete snapshot'
printf 'auto\n' > "$hub/power/control"
printf 'PASS: object encoding failure aborts the snapshot\n'
mv -- "$hub" "$fixture/removed-hub"
capture
jq -en --argjson before "$before" --argjson after "$snapshot" '($before.objects | map(.path)) - ($after.objects | map(.path)) == ["xhci-hcd.7.auto/usb3/3-1", "xhci-hcd.7.auto/usb3/3-1/3-1.4"]' >/dev/null || fail 'disappearance not visible in complete object set'
printf 'PASS: disappearance between snapshots\n'
for invalid in '' --unknown --sample --record=1; do refuse "$invalid"; done
refuse
refuse --record extra
refuse --sample relative
refuse --sample "$fixture_root" extra
refuse --sample /
refuse --sample /sys
refuse --sample /proc
refuse --sample /dev
printf 'PASS: malformed invocation refusal\n'
ln -s /sys "$fixture/sysfs-link"
refuse --sample "$fixture/sysfs-link"
ln -s /etc/passwd "$fixture_root/foreign-link"
refuse --sample "$fixture_root"
mv -- "$fixture_root/foreign-link" "$fixture/foreign-link"
mkfifo "$fixture_root/unsafe-fifo"
refuse --sample "$fixture_root"
mv -- "$fixture_root/unsafe-fifo" "$fixture/unsafe-fifo"
printf 'PASS: special-file and symlink refusal without reads\n'
if unshare --user --map-root-user true 2>/dev/null; then
  status=0
  unshare --user --map-root-user /bin/bash "$reader" --sample "$fixture_root" > "$fixture/root.stdout" 2> "$fixture/root.stderr" || status=$?
  (( status == 64 )) && [[ ! -s $fixture/root.stdout ]] || fail 'root invocation not refused'
  printf 'PASS: root invocation refusal in isolated user namespace\n'
else
  printf 'SKIP: root-refusal runtime test; unprivileged user namespaces unavailable\n'
fi
printf 'Fixture retained: %s\nVERDICT: PASS\n' "$fixture"
