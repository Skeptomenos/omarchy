#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

if ! command -v quickshell >/dev/null 2>&1; then
  pass "quickshell unavailable; skipping native palette namespace coverage"
  exit 0
fi
require_command timeout

test_tmp=$(mktemp -d)
trap 'rm -rf "$test_tmp"' EXIT
ulimit -c 0 2>/dev/null || true

mkdir -p "$test_tmp/home/.local/state/omarchy/current/theme" "$test_tmp/home/.config/omarchy" \
  "$test_tmp/runtime" "$test_tmp/bin"
chmod 700 "$test_tmp/runtime"
ln -s "$ROOT/shell/Commons" "$test_tmp/Commons"
ln -s "$ROOT/shell/Ui" "$test_tmp/Ui"
cp "$SHELL_TEST_DIR/fixtures/color-namespace/shell.qml" "$test_tmp/shell.qml"

cat >"$test_tmp/home/.local/state/omarchy/current/theme/colors.toml" <<'TOML'
foreground = "#d7e8f9"
background = "#102030"
accent = "#2468ac"
red = "#a12b3c"
TOML
cat >"$test_tmp/home/.local/state/omarchy/current/theme/shell.toml" <<'TOML'
[menu]
text = "#c0ffee"
background = "#203040"
border = "accent"
border-width = 3
[controls]
normal-color = "accent"
normal-fill-alpha = 1
TOML
: >"$test_tmp/home/.config/omarchy/shell.toml"

# Style starts these read-only helpers. Keep even those queries off the desktop.
cat >"$test_tmp/bin/hyprctl" <<'SH'
#!/bin/bash
printf '{"int":0}\n'
SH
cat >"$test_tmp/bin/fc-match" <<'SH'
#!/bin/bash
printf 'monospace'
SH
chmod +x "$test_tmp/bin/hyprctl" "$test_tmp/bin/fc-match"

output=$(env -u WAYLAND_DISPLAY -u DISPLAY -u HYPRLAND_INSTANCE_SIGNATURE \
  HOME="$test_tmp/home" XDG_CONFIG_HOME="$test_tmp/home/.config" \
  XDG_CACHE_HOME="$test_tmp/home/.cache" XDG_RUNTIME_DIR="$test_tmp/runtime" \
  DBUS_SESSION_BUS_ADDRESS="unix:path=$test_tmp/no-session-bus" \
  PATH="$test_tmp/bin:$PATH" QT_QPA_PLATFORM=offscreen QT_QPA_PLATFORMTHEME=basic QT_QUICK_BACKEND=software \
  timeout -k 2s 15s quickshell -p "$test_tmp" --no-color 2>&1) || \
  fail "native palette namespace fixture exits cleanly" "$output"

grep -q 'RESULT pass color namespace' <<<"$output" || \
  fail "native palette namespace values and updates match the theme" "$output"
if grep -Eq 'WARN|ERROR|RESULT fail' <<<"$output"; then
  fail "native palette namespace fixture has no QML warnings or errors" "$output"
fi
printf '%s\n' "$output"
pass "native palette namespace preserves theme values, singleton identity, internal lookups and updates"
