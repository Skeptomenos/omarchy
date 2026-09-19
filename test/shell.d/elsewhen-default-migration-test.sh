#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"
require_command jq

test_dir=$(mktemp -d)
trap 'rm -rf "$test_dir"' EXIT
mkdir -p "$test_dir/bin" "$test_dir/home"
export CALL_LOG="$test_dir/calls"
package_plugin="$test_dir/package"
queue="$test_dir/queue"
marker="$test_dir/home/.local/state/omarchy/migrations/1789581662.sh"
mkdir -p "$package_plugin" "$queue/migrations"
printf '{"id":"omacom.elsewhen"}\n' >"$package_plugin/manifest.json"
ln -s "$ROOT/config" "$queue/config"
sed "s|/usr/share/omarchy/plugins/omacom.elsewhen|$package_plugin|g" \
  "$ROOT/migrations/1789581662.sh" >"$queue/migrations/1789581662.sh"

cat >"$test_dir/bin/omarchy-pkg-add" <<'SH'
#!/bin/bash
printf 'package %s\n' "$*" >>"$CALL_LOG"
if [[ ${USE_REAL_PACKAGE_ADD:-0} == "1" ]]; then
  exec "$ROOT/bin/omarchy-pkg-add" "$@"
else
  exit "${PACKAGE_STATUS:-0}"
fi
SH
cat >"$test_dir/bin/pacman" <<'SH'
#!/bin/bash
case "$*" in
  '-Q elsewhen') [[ ${PACKAGE_INSTALLED:-1} == "1" ]] ;;
  '-Si elsewhen' | '-Si omarchy/elsewhen') exit 1 ;;
  *) echo "unexpected package operation: $*" >&2; exit 97 ;;
esac
SH
cat >"$test_dir/bin/uname" <<'SH'
#!/bin/bash
echo aarch64
SH
cat >"$test_dir/bin/omarchy-notification-dismiss" <<'SH'
#!/bin/bash
exit 0
SH
cat >"$test_dir/bin/omarchy-shell" <<'SH'
#!/bin/bash
printf '%s\n' "$*" >>"$CALL_LOG"
[[ $2 != "rescanPlugins" ]] || exit "${SCAN_STATUS:-0}"
printf '%s\n' "${TEST_PUT_RESULT:-ok}"
SH
cat >"$test_dir/bin/omarchy-restart-shell" <<'SH'
#!/bin/bash
echo 'migration must leave the restart to omarchy update' >&2
exit 1
SH
chmod +x "$test_dir/bin/"*

plugin="$test_dir/home/.config/omarchy/plugins/omacom.elsewhen"
run_migration() {
  : >"$CALL_LOG"
  HOME="$test_dir/home" OMARCHY_PATH="$ROOT" PATH="$test_dir/bin:$ROOT/bin:$PATH" \
    bash -euo pipefail "$queue/migrations/1789581662.sh" >"$test_dir/output" 2>&1
}

run_queue() {
  : >"$CALL_LOG"
  HOME="$test_dir/home" OMARCHY_PATH="$queue" PATH="$test_dir/bin:$ROOT/bin:$PATH" \
    bash "$ROOT/bin/omarchy-migrate" >"$test_dir/output" 2>&1
}

config="$test_dir/home/.config/omarchy/shell.json"
mkdir -p "${config%/*}"
cat >"$config" <<'JSON'
{"version":1,"bar":{"id":"local.custom-bar","centerAnchor":"local.anchor","layout":{"left":[{"id":"omacom.elsewhen","cities":["Tokyo"]}],"center":[{"id":"local.anchor"}],"right":[{"id":"omarchy.clock","format":"HH:mm"}]}},"customSetting":"keep"}
JSON
cp "$config" "$test_dir/config-before"

if PACKAGE_STATUS=1 run_migration; then
  fail "package failure stops the migration"
fi
[[ ! -e $plugin && ! -L $plugin && $(cat "$CALL_LOG") == "package elsewhen" ]] ||
  fail "package failure leaves the plugin and shell untouched"
pass "package failure stops before linking or changing the shell"

if PACKAGE_INSTALLED=0 USE_REAL_PACKAGE_ADD=1 run_queue; then
  fail "a skipped ARM package installation leaves the migration pending"
fi
grep -qF "Skipping 'elsewhen'" "$test_dir/output" || fail "the real ARM helper exercised its unavailable-package path"
[[ ! -e $plugin && ! -L $plugin && ! -e $marker && $(cat "$CALL_LOG") == "package elsewhen" ]] ||
  fail "an unavailable package cannot link, enable, or complete the migration"
cmp -s "$config" "$test_dir/config-before" || fail "an unavailable package preserves the user's bar"
pass "a skipped ARM package leaves the plugin, bar, and migration marker untouched"

mv "$package_plugin" "$package_plugin.saved"
if run_queue; then
  fail "an installed package without its plugin payload must remain pending"
fi
[[ ! -e $plugin && ! -L $plugin && ! -e $marker && $(cat "$CALL_LOG") == "package elsewhen" ]] ||
  fail "a missing payload stops before linking, scanning, or completing"
mv "$package_plugin.saved" "$package_plugin"
pass "a missing package payload cannot create a broken link or completion marker"

run_migration
[[ $(readlink "$plugin") == "$package_plugin" ]] || fail "package link is installed"
[[ $(readlink "$ROOT/config/omarchy/plugins/omacom.elsewhen") == "/usr/share/omarchy/plugins/omacom.elsewhen" ]] || fail "fresh installs use the package link"
pass "migration and fresh installs link to the package"

expected=$'package elsewhen\nshell rescanPlugins\nshell putBarWidget omacom.elsewhen {"before":"omarchy.clock"}'
[[ $(cat "$CALL_LOG") == "$expected" ]] || fail "install, scan and placement run in order" "$(cat "$CALL_LOG")"
pass "real bar helper enables and places before the clock without restarting during reload"

run_migration
[[ $(cat "$CALL_LOG") == "$expected" ]] || fail "migration can be rerun"
pass "migration can be rerun with its package link present"

rm "$plugin"
mkdir "$plugin"
printf 'local work\n' >"$plugin/notes"
run_migration
[[ ! -L $plugin && $(cat "$plugin/notes") == "local work" ]] || fail "existing checkout is preserved"
pass "existing checkout and local files are preserved"

rm "$plugin/notes"
rmdir "$plugin"
ln -s "$test_dir/custom-plugin" "$plugin"
run_migration
[[ $(readlink "$plugin") == "$test_dir/custom-plugin" ]] || fail "existing symlink is preserved"
pass "existing symlink is preserved, including a missing target"

cmp -s "$config" "$test_dir/config-before" || fail "the migration rewrites a custom bar, clock anchor, placement, or settings"
[[ $(cat "$CALL_LOG") == "$expected" ]] || fail "an existing user plugin still uses the preserving bar put operation"
pass "custom bar identity, clock anchor, existing placement, and plugin settings are preserved"

for failure in 'SCAN_STATUS=1' 'TEST_PUT_RESULT=unknown'; do
  if env "$failure" HOME="$test_dir/home" OMARCHY_PATH="$queue" PATH="$test_dir/bin:$ROOT/bin:$PATH" \
    bash "$ROOT/bin/omarchy-migrate" >"$test_dir/output" 2>&1; then
    fail "$failure must leave the migration pending"
  fi
  [[ ! -e $marker ]] || fail "$failure cannot write a completion marker"
  pass "$failure leaves the migration pending"
done

run_queue
[[ -f $marker && $(cat "$CALL_LOG") == "$expected" ]] || fail "the successful migration records completion after placement"
run_queue
[[ ! -s $CALL_LOG ]] || fail "a completed migration does not repeat package or shell changes"
cmp -s "$config" "$test_dir/config-before" || fail "completion preserves the custom bar config"
pass "the real migration runner marks success only after all steps and does not replay it"
