#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

test_tmp=$(mktemp -d)
trap 'rm -rf "$test_tmp"' EXIT

led_class="$test_tmp/leds"
mock_bin="$test_tmp/bin"
state_file="$test_tmp/brightness"
saved_file="$test_tmp/saved"
call_log="$test_tmp/calls"
osd_log="$test_tmp/osd"
mkdir -p "$led_class/kbd_backlight" "$mock_bin"
printf '128\n' >"$state_file"

cat >"$mock_bin/brightnessctl" <<'SH'
#!/bin/bash

printf '%s\n' "$*" >>"$CALL_LOG"
max="${MOCK_MAX_OUTPUT:-255}"

case "${1:-}" in
-d)
  case "${3:-}" in
  max)
    [[ ${FAIL_MAX:-0} == "1" ]] && exit 3
    printf '%s\n' "$max"
    ;;
  get)
    [[ ${FAIL_GET:-0} == "1" ]] && exit 4
    if [[ -n ${MOCK_CURRENT_OUTPUT:-} ]]; then
      printf '%s\n' "$MOCK_CURRENT_OUTPUT"
    else
      cat "$STATE_FILE"
    fi
    ;;
  set)
    [[ ${FAIL_SET:-0} == "1" ]] && exit 5
    target="${4:-}"
    if [[ $target == *% ]]; then
      percent="${target%%%}"
      printf '%d\n' "$(( (10#$percent * max + 50) / 100 ))" >"$STATE_FILE"
    else
      printf '%d\n' "$target" >"$STATE_FILE"
    fi
    ;;
  *)
    exit 2
    ;;
  esac
  ;;
-sd)
  [[ ${FAIL_SET:-0} == "1" ]] && exit 5
  cp "$STATE_FILE" "$SAVED_FILE"
  printf '0\n' >"$STATE_FILE"
  ;;
-rd)
  [[ ${FAIL_RESTORE:-0} == "1" ]] && exit 6
  cp "$SAVED_FILE" "$STATE_FILE"
  ;;
*)
  exit 2
  ;;
esac
SH

cat >"$mock_bin/omarchy-osd" <<'SH'
#!/bin/bash
printf '%s\n' "$*" >>"$OSD_LOG"
SH

chmod +x "$mock_bin/brightnessctl" "$mock_bin/omarchy-osd"

run_keyboard() {
  CALL_LOG="$call_log" \
  STATE_FILE="$state_file" \
  SAVED_FILE="$saved_file" \
  OSD_LOG="$osd_log" \
  OMARCHY_KEYBOARD_BACKLIGHT_LED_CLASS="$led_class" \
  OMARCHY_BRIGHTNESSCTL="$mock_bin/brightnessctl" \
  FAIL_MAX="${FAIL_MAX:-0}" \
  FAIL_GET="${FAIL_GET:-0}" \
  FAIL_SET="${FAIL_SET:-0}" \
  FAIL_RESTORE="${FAIL_RESTORE:-0}" \
  MOCK_MAX_OUTPUT="${MOCK_MAX_OUTPUT:-}" \
  MOCK_CURRENT_OUTPUT="${MOCK_CURRENT_OUTPUT:-}" \
  PATH="$mock_bin:$ROOT/bin:$PATH" \
    "$ROOT/bin/omarchy-brightness-keyboard" "$@"
}

[[ $(run_keyboard get) == "50" ]] || fail "keyboard get returns an integer percentage"
pass "keyboard get returns an integer percentage"

run_keyboard set 73
[[ $(run_keyboard get) == "73" ]] || fail "keyboard set applies an exact percentage"
grep -Fx -- '-i keyboard -p 73' "$osd_log" >/dev/null || fail "keyboard set displays its percentage in the OSD"
pass "keyboard set applies an exact percentage with OSD"

osd_count=$(wc -l <"$osd_log")
run_keyboard --no-osd set 08
[[ $(run_keyboard get) == "8" ]] || fail "keyboard set accepts a zero-padded percentage"
(( $(wc -l <"$osd_log") == osd_count )) || fail "--no-osd suppresses keyboard set OSD"
pass "keyboard set supports --no-osd"

before=$(<"$state_file")
for invalid in -1 101 1.5 bright 999999999999999999999999999999999999999; do
  if run_keyboard set "$invalid" >/dev/null 2>&1; then
    fail "keyboard set rejects invalid percentage: $invalid"
  fi
done
if run_keyboard set >/dev/null 2>&1; then
  fail "keyboard set requires a percentage"
fi
[[ $(<"$state_file") == "$before" ]] || fail "invalid keyboard percentages do not change brightness"
pass "keyboard set validates the 0-100 integer range"

calls_before=$(wc -l <"$call_log")
if run_keyboard set 999999999999999999999999999999999999999 >/dev/null 2>&1; then
  fail "keyboard set rejects an overflow-length percentage"
fi
(( $(wc -l <"$call_log") == calls_before )) || fail "overflow-length percentage is rejected before brightnessctl"
pass "keyboard set rejects overflow-length integers before arithmetic or hardware access"

if FAIL_MAX=1 run_keyboard get >/dev/null 2>&1; then
  fail "keyboard get propagates a maximum read failure"
fi
if FAIL_GET=1 run_keyboard get >/dev/null 2>&1; then
  fail "keyboard get propagates a current read failure"
fi
if MOCK_MAX_OUTPUT=invalid run_keyboard get >/dev/null 2>&1; then
  fail "keyboard get rejects a non-numeric maximum"
fi
if MOCK_CURRENT_OUTPUT=invalid run_keyboard get >/dev/null 2>&1; then
  fail "keyboard get rejects a non-numeric current value"
fi
if MOCK_MAX_OUTPUT=9999999999 run_keyboard get >/dev/null 2>&1; then
  fail "keyboard get rejects an overflow-prone maximum"
fi
if MOCK_CURRENT_OUTPUT=9999999999 run_keyboard get >/dev/null 2>&1; then
  fail "keyboard get rejects an overflow-prone current value"
fi
if MOCK_CURRENT_OUTPUT=256 run_keyboard get >/dev/null 2>&1; then
  fail "keyboard get rejects a current value above maximum"
fi
pass "keyboard get propagates backend failures and validates raw numeric values"

osd_count=$(wc -l <"$osd_log")
if FAIL_SET=1 run_keyboard set 50 >/dev/null 2>&1; then
  fail "keyboard set propagates a backend write failure"
fi
(( $(wc -l <"$osd_log") == osd_count )) || fail "failed keyboard set does not display OSD"
if FAIL_SET=1 run_keyboard --no-osd up >/dev/null 2>&1; then
  fail "keyboard up propagates a backend write failure"
fi
if FAIL_SET=1 run_keyboard off >/dev/null 2>&1; then
  fail "keyboard off propagates a backend write failure"
fi
if FAIL_RESTORE=1 run_keyboard restore >/dev/null 2>&1; then
  fail "keyboard restore propagates a backend restore failure"
fi
pass "keyboard writes propagate backend failures without reporting success"

printf '100\n' >"$state_file"
run_keyboard --no-osd up
[[ $(<"$state_file") == "125" ]] || fail "keyboard up retains the raw ten-percent step"
run_keyboard --no-osd down
[[ $(<"$state_file") == "100" ]] || fail "keyboard down retains the raw ten-percent step"
printf '250\n' >"$state_file"
run_keyboard --no-osd cycle
[[ $(<"$state_file") == "0" ]] || fail "keyboard cycle wraps at maximum brightness"
printf '111\n' >"$state_file"
run_keyboard off
[[ $(<"$state_file") == "0" ]] || fail "keyboard off saves and clears brightness"
run_keyboard restore
[[ $(<"$state_file") == "111" ]] || fail "keyboard restore restores the saved brightness"
pass "existing keyboard brightness actions retain their behavior"

empty_led_class="$test_tmp/empty-leds"
mkdir -p "$empty_led_class"
if OMARCHY_KEYBOARD_BACKLIGHT_LED_CLASS="$empty_led_class" \
  OMARCHY_BRIGHTNESSCTL="$mock_bin/brightnessctl" \
  "$ROOT/bin/omarchy-brightness-keyboard" get >/dev/null 2>&1; then
  fail "keyboard helper rejects a missing backlight device"
fi
pass "keyboard helper detects kbd_backlight devices through the injected LED class"

manifest="$ROOT/shell/plugins/panels/keyboard/manifest.json"
panel="$ROOT/shell/plugins/panels/keyboard/Panel.qml"

jq -e '
  .schemaVersion == 1 and
  .id == "omarchy.keyboard" and
  (.kinds | index("panel")) != null and
  .entryPoints.panel == "Panel.qml"
' "$manifest" >/dev/null || fail "keyboard panel manifest follows the first-party plugin contract"
pass "keyboard panel manifest follows the first-party plugin contract"

grep -F 'function open(payloadJson)' "$panel" >/dev/null || fail "keyboard panel exposes open lifecycle"
grep -F 'function close()' "$panel" >/dev/null || fail "keyboard panel exposes close lifecycle"
grep -F 'Keys.onEscapePressed: root.dismiss()' "$panel" >/dev/null || fail "keyboard panel dismisses with Escape"
grep -F 'command: ["omarchy-brightness-keyboard", "--no-osd", "get"]' "$panel" >/dev/null || fail "keyboard panel reads brightness through the helper"
grep -F 'id: writeProc' "$panel" >/dev/null || fail "keyboard panel observes writes through a Process"
grep -F 'String(root.pendingPercent)' "$panel" >/dev/null || fail "keyboard panel writes the validated pending percentage"
grep -F 'root.writeFailed = exitCode !== 0' "$panel" >/dev/null || fail "keyboard panel observes write exit status"
grep -F 'root.startRead("confirm")' "$panel" >/dev/null || fail "keyboard panel confirms brightness after writes"
grep -F 'Could not set brightness' "$panel" >/dev/null && grep -F 'Could not confirm brightness' "$panel" >/dev/null || fail "keyboard panel exposes concise write failure states"
if grep -F 'Quickshell.execDetached' "$panel" >/dev/null; then
  fail "keyboard panel does not detach unobserved writes"
fi
grep -F 'property bool loading: true' "$panel" >/dev/null || fail "keyboard panel starts in loading state"
grep -F 'property bool loaded: false' "$panel" >/dev/null || fail "keyboard panel starts unavailable"
grep -F 'enabled: root.controlsEnabled' "$panel" >/dev/null || fail "keyboard panel disables the slider until ready"
grep -F 'if (!controlsEnabled) return false' "$panel" >/dev/null || fail "keyboard panel rejects writes while loading or applying"
grep -F 'minimum: 0' "$panel" >/dev/null && grep -F 'maximum: 100' "$panel" >/dev/null || fail "keyboard panel slider spans 0-100 percent"
grep -F 'text: "Shift+F1"' "$panel" >/dev/null && grep -F 'text: "Shift+F2"' "$panel" >/dev/null || fail "keyboard panel displays Apple Silicon shortcuts"
grep -F 'event.key === Qt.Key_Left' "$panel" >/dev/null && grep -F 'event.key === Qt.Key_Down' "$panel" >/dev/null || fail "keyboard panel supports decrement arrow keys"
grep -F 'event.key === Qt.Key_Right' "$panel" >/dev/null && grep -F 'event.key === Qt.Key_Up' "$panel" >/dev/null || fail "keyboard panel supports increment arrow keys"
grep -F 'event.key === Qt.Key_H' "$panel" >/dev/null && grep -F 'event.key === Qt.Key_L' "$panel" >/dev/null || fail "keyboard panel supports h/l brightness keys"
grep -F 'event.key === Qt.Key_Home' "$panel" >/dev/null && grep -F 'root.applyPercent(0)' "$panel" >/dev/null || fail "keyboard panel supports Home for zero"
grep -F 'event.key === Qt.Key_End' "$panel" >/dev/null && grep -F 'root.applyPercent(100)' "$panel" >/dev/null || fail "keyboard panel supports End for maximum"
grep -F 'root.stepPercent(-5)' "$panel" >/dev/null && grep -F 'root.stepPercent(5)' "$panel" >/dev/null || fail "keyboard panel uses five-percent keyboard steps"
pass "keyboard panel provides guarded loading, observed writes, confirmation, errors, and keyboard controls"

run_node_test <<'JS'
const fs = require('fs')
const menuModel = requireFromRoot('shell/plugins/menu/MenuModel.js')
const rows = menuModel.parseMenuJsonc(
  fs.readFileSync(path.join(root, 'default/omarchy/omarchy-menu.jsonc'), 'utf8')
)
const menu = Object.fromEntries(rows.map(row => [row.id, row]))

assert(menu['setup.keybindings'], 'existing Setup Keybindings entry remains present')
assert(menu['setup.input'], 'existing Setup Input entry remains present')
assertEqual(menu['setup.keyboard'].label, 'Keyboard', 'Setup exposes the Keyboard submenu')
assertEqual(menu['setup.keyboard.backlight'].label, 'Backlight…', 'Keyboard submenu exposes Backlight')
assertEqual(
  menu['setup.keyboard.backlight'].when,
  "compgen -G '/sys/class/leds/*kbd_backlight*' >/dev/null",
  'Backlight menu entry is gated by a kbd_backlight LED'
)
assertEqual(
  menu['setup.keyboard.backlight'].action,
  'omarchy-shell shell summon omarchy.keyboard',
  'Backlight menu entry summons the keyboard panel'
)
assert(menu['setup.keyboard.input'], 'Keyboard submenu exposes Input config')
assert(menu['setup.keyboard.keybindings'], 'Keyboard submenu exposes Keybindings')

for (const id of ['setup.keyboard', 'setup.keyboard.backlight', 'setup.keyboard.input', 'setup.keyboard.keybindings'])
  assertDeepEqual(menu[id].aliases, [], `${id} adds no aliases`)
JS

grep -F 'docs/apple-silicon-keyboard-backlight.md' "$ROOT/README.md" >/dev/null || fail "README links the keyboard backlight guide"
pass "README links the keyboard backlight guide"
