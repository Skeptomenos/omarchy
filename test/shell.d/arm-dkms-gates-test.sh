#!/bin/bash

set -euo pipefail
source "$(dirname "$0")/base-test.sh"

test_tmp=$(mktemp -d)
trap 'rm -rf "$test_tmp"' EXIT
mkdir -p "$test_tmp/bin" "$test_tmp/modules/fixture/build"
export CALL_LOG="$test_tmp/calls" TEST_ARCH=aarch64
export PATH="$test_tmp/bin:$ROOT/bin:$PATH" OMARCHY_PATH="$ROOT"

cat >"$test_tmp/bin/uname" <<'SH'
#!/bin/bash
case $1 in
  -m) echo "$TEST_ARCH" ;;
  -r) echo fixture ;;
  *) exit 99 ;;
esac
SH
cat >"$test_tmp/bin/omarchy-hw-elgato-camlink-4k" <<'SH'
#!/bin/bash
exit "${NO_CAMERA:-0}"
SH
cat >"$test_tmp/bin/omarchy-pkg-add" <<'SH'
#!/bin/bash
printf 'packages %s\n' "$*" >>"$CALL_LOG"
SH
cat >"$test_tmp/bin/omarchy-pkg-present" <<'SH'
#!/bin/bash
exit "${MISSING_PACKAGE:-0}"
SH
cat >"$test_tmp/bin/sudo" <<'SH'
#!/bin/bash
printf 'sudo %s\n' "$*" >>"$CALL_LOG"
[[ $1 != tee ]] || cat >/dev/null
exit 0
SH
printf '#!/bin/bash\necho input\n' >"$test_tmp/bin/id"
printf '#!/bin/bash\nexit 0\n' >"$test_tmp/bin/lsmod"
chmod +x "$test_tmp/bin/"*

for entry in install/hardware/fix-elgato-camlink-4k.sh bin/omarchy-install-gaming-xbox-controllers; do
  script="$test_tmp/$(basename "$entry")"
  sed "s|/usr/lib/modules/|$test_tmp/modules/|g" "$ROOT/$entry" >"$script"

  : >"$CALL_LOG"
  rm -f "$test_tmp/modules/fixture/build/Makefile"
  if bash -euo pipefail -c 'source "$1"' bash "$script" >"$test_tmp/output" 2>&1; then
    fail "$entry must defer ARM DKMS setup without matching headers"
  fi
  [[ ! -s $CALL_LOG ]] || fail "$entry changed packages or hardware without headers" "$(cat "$CALL_LOG")"
  grep -q 'Install matching headers for fixture' "$test_tmp/output" || fail "$entry explains the missing headers"
  pass "$entry leaves ARM packages and hardware unchanged without matching headers"

  touch "$test_tmp/modules/fixture/build/Makefile"
  if MISSING_PACKAGE=1 bash -euo pipefail -c 'source "$1"' bash "$script" >/dev/null 2>&1; then
    fail "$entry must defer configuration when the ARM package helper skipped a dependency"
  fi
  ! grep -q '^sudo ' "$CALL_LOG" || fail "$entry configured an unavailable driver"
  pass "$entry keeps working hardware enabled when a dependency is unavailable"

  for arch in aarch64 x86_64; do
    : >"$CALL_LOG"
    TEST_ARCH="$arch" bash -euo pipefail -c 'source "$1"' bash "$script" >/dev/null
    grep -q '^packages ' "$CALL_LOG" || fail "$entry did not install the driver on $arch"
    grep -q '^sudo ' "$CALL_LOG" || fail "$entry did not configure the available driver on $arch"
    ! grep -q 'linux.*headers' "$CALL_LOG" || fail "$entry must not select an unrelated kernel"
    pass "$entry configures the available driver on $arch without replacing the kernel"
  done
done

: >"$CALL_LOG"
NO_CAMERA=1 bash -euo pipefail -c 'source "$1"' bash "$ROOT/install/hardware/fix-elgato-camlink-4k.sh"
[[ ! -s $CALL_LOG ]] || fail "an absent camera must not change the host"
pass "Cam Link setup leaves systems without the device unchanged"
