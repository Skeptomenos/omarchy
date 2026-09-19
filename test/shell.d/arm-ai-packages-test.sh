#!/bin/bash

set -euo pipefail
source "$(dirname "$0")/base-test.sh"

test_tmp=$(mktemp -d)
trap 'rm -rf "$test_tmp"' EXIT
mkdir -p "$test_tmp/bin" "$test_tmp/home"
export AI_TEST_STATE="$test_tmp/installed" AI_TEST_LOG="$test_tmp/calls"
export PATH="$test_tmp/bin:$ROOT/bin:$PATH" HOME="$test_tmp/home" OMARCHY_PATH="$ROOT"

cat >"$test_tmp/bin/uname" <<'SH'
#!/bin/bash
echo aarch64
SH
cat >"$test_tmp/bin/sudo" <<'SH'
#!/bin/bash
exec "$@"
SH
cat >"$test_tmp/bin/pacman" <<'SH'
#!/bin/bash
printf '%s\n' "$*" >>"$AI_TEST_LOG"
case "$1" in
  -Q) [[ $2 == "openclaw" && -f $AI_TEST_STATE ]] ;;
  -Si) [[ $2 == "omarchy/openclaw" ]] ;;
  -S)
    [[ $* == "-S --noconfirm --needed omarchy/openclaw" ]] || exit 1
    touch "$AI_TEST_STATE"
    ;;
  *) exit 1 ;;
esac
SH
chmod +x "$test_tmp/bin/"*

"$ROOT/bin/omarchy-pkg-add" openclaw
grep -qx -- '-S --noconfirm --needed omarchy/openclaw' "$AI_TEST_LOG" || fail 'OpenClaw uses its explicit ARM repository'
! grep -qx -- '-Q omarchy/openclaw' "$AI_TEST_LOG" || fail 'installed queries use the plain package name'
: >"$AI_TEST_LOG"
"$ROOT/bin/omarchy-pkg-add" openclaw
[[ $(cat "$AI_TEST_LOG") == '-Q openclaw' ]] || fail 'installed OpenClaw avoids a second package transaction'
pass 'the package helper installs and verifies qualified OpenClaw idempotently'

cat >"$test_tmp/bin/omarchy-pkg-add" <<'SH'
#!/bin/bash
exit 0
SH
cat >"$test_tmp/bin/omarchy-pkg-present" <<'SH'
#!/bin/bash
exit 1
SH
for command in setsid omarchy-webapp-install omarchy-theme-refresh omarchy-theme-set-t3code omarchy-openclaw-onboard; do
  cat >"$test_tmp/bin/$command" <<'SH'
#!/bin/bash
echo "unexpected follow-up: $0 $*" >>"$AI_TEST_LOG"
exit 1
SH
done
chmod +x "$test_tmp/bin/"*

for installer in omarchy-install-openclaw-cli omarchy-install-ai-openclaw omarchy-install-ai-claude omarchy-install-ai-t3-code; do
  : >"$AI_TEST_LOG"
  if "$ROOT/bin/$installer" >"$test_tmp/output" 2>&1; then
    fail "$installer rejects an unavailable package"
  fi
  grep -q 'unavailable from the configured package sources' "$test_tmp/output" || fail "$installer explains the missing package"
  [[ ! -s $AI_TEST_LOG ]] || fail "$installer stops before launch, onboarding, or configuration changes"
  pass "$installer stops after a skipped package installation"
done
