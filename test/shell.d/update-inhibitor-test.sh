#!/bin/bash

set -euo pipefail
source "$(dirname "$0")/base-test.sh"

test_tmp=$(mktemp -d)
cleanup() {
  if [[ -s $test_tmp/child ]]; then
    kill "$(<"$test_tmp/child")" 2>/dev/null || true
  fi
  if [[ -s $test_tmp/wrapper ]]; then
    kill "$(<"$test_tmp/wrapper")" 2>/dev/null || true
  fi
  rm -rf "$test_tmp"
}
trap cleanup EXIT
mkdir -p "$test_tmp/bin" "$test_tmp/home" "$test_tmp/runtime"
export HOME="$test_tmp/home" XDG_RUNTIME_DIR="$test_tmp/runtime"
export PATH="$test_tmp/bin:$ROOT/bin:$PATH" TEST_TMP="$test_tmp"

cat >"$test_tmp/bin/pkexec" <<'SH'
#!/bin/bash
# Keep a real wrapper and child. TERM teardown takes longer than the old budget.
if [[ ${1:-} == "-v" ]]; then exit 0; fi
echo "$$" >"$TEST_TMP/wrapper"
trap 'touch "$TEST_TMP/signalled"; sleep 2; kill "$child" 2>/dev/null || true; wait "$child" || true; exit 0' TERM
sleep "${WRAPPER_START_DELAY:-0}"
"$@" <&0 &
child=$!
wait "$child"
sleep 1.2
SH
cat >"$test_tmp/bin/systemd-inhibit" <<'SH'
#!/bin/bash
while [[ $1 == --* ]]; do shift; done
echo "$$" >"$TEST_TMP/child"
exec "$@"
SH
cat >"$test_tmp/bin/omarchy-toggle-idle" <<'SH'
#!/bin/bash
exit 0
SH
chmod +x "$test_tmp/bin/"*
cp "$test_tmp/bin/pkexec" "$test_tmp/bin/sudo"
cat >"$test_tmp/deny-signals" <<'SH'
kill() {
  touch "$TEST_TMP/denied-signal"
  return 1
}
SH

exec {OMARCHY_UPDATE_LOCK_FD}>"$test_tmp/runtime/omarchy-update.lock"
flock -n "$OMARCHY_UPDATE_LOCK_FD"
export OMARCHY_UPDATE_LOCK_FD
assert_retained_child() {
  for _ in {1..100}; do
    [[ -s $TEST_TMP/child ]] && break
    sleep 0.02
  done
  [[ -s $TEST_TMP/child ]] || fail "inhibitor wrapper started its child"
  child=$(<"$TEST_TMP/child")
  kill -0 "$child" 2>/dev/null || fail "inhibitor child is alive before stop"
  [[ $(awk '{print $3}' "/proc/$child/stat") != "Z" ]] || fail "inhibitor child is not a zombie before stop"
  [[ -p /proc/$child/fd/0 && $(readlink -f "/proc/$child/fd/0") == "$XDG_RUNTIME_DIR/omarchy-update-stay-awake/inhibit-control" ]] ||
    fail "inhibitor child reads the control FIFO before stop"
}
export -f assert_retained_child
"$ROOT/bin/omarchy-update-stay-awake" start
assert_retained_child
wrapper=$(<"$test_tmp/wrapper")
[[ $wrapper != "$child" ]] || fail "fixture retains a real wrapper"
for pid in "$wrapper" "$child"; do
  for fd in /proc/"$pid"/fd/*; do
    [[ $(readlink -f "$fd" 2>/dev/null || true) != "$test_tmp/runtime/omarchy-update.lock" ]] ||
      fail "inhibitor wrapper and child do not inherit the update lock"
  done
done
BASH_ENV="$test_tmp/deny-signals" "$ROOT/bin/omarchy-update-stay-awake" stop ||
  fail "stop waits for wrapper teardown even when signalling is denied"
[[ ! -e $test_tmp/denied-signal ]] || fail "stop does not need permission to signal the wrapper"
[[ ! -e $test_tmp/signalled ]] || fail "stop does not signal the privilege wrapper"
[[ ! -d $XDG_RUNTIME_DIR/omarchy-update-stay-awake ]] || fail "stop removes helper state"
kill -0 "$child" 2>/dev/null && fail "stop leaves no inhibitor child"
[[ ! -e /proc/$wrapper/stat || $(awk '{print $3}' "/proc/$wrapper/stat") == "Z" ]] ||
  fail "stop waits for wrapper exit"
"$ROOT/bin/omarchy-update-stay-awake" stop
pass "inhibitor stop waits for a real wrapper and child without an EXIT retry"

rm -f "$test_tmp/child" "$test_tmp/wrapper"
WRAPPER_START_DELAY=1 "$ROOT/bin/omarchy-update-stay-awake" start
for _ in {1..100}; do
  [[ -s $test_tmp/wrapper ]] && break
  sleep 0.02
done
[[ -s $test_tmp/wrapper && ! -e $test_tmp/child ]] || fail "immediate stop precedes child startup"
wrapper=$(<"$test_tmp/wrapper")
[[ -p /proc/$wrapper/fd/0 && $(readlink -f "/proc/$wrapper/fd/0") == "$XDG_RUNTIME_DIR/omarchy-update-stay-awake/inhibit-control" ]] ||
  fail "delayed wrapper retains the control FIFO before child startup"
"$ROOT/bin/omarchy-update-stay-awake" stop
[[ ! -d $XDG_RUNTIME_DIR/omarchy-update-stay-awake ]] || fail "immediate stop removes helper state"
[[ ! -e $test_tmp/signalled ]] || fail "immediate stop does not signal the privilege wrapper"
pass "an immediate stop reaches a child that has not started reading yet"

if (( EUID != 0 )); then
  rm -f "$test_tmp/child" "$test_tmp/wrapper"
  cat >"$test_tmp/terminal-driver" <<'SH'
#!/bin/bash
set -euo pipefail
source "$ROOT/test/shell.d/base-test.sh"
omarchy-update-stay-awake start
assert_retained_child
omarchy-update-stay-awake stop
SH
  chmod +x "$test_tmp/terminal-driver"
  script -qefc "$test_tmp/terminal-driver" /dev/null >"$test_tmp/terminal.out"
  [[ ! -d $XDG_RUNTIME_DIR/omarchy-update-stay-awake ]] || fail "terminal stop removes helper state"
  [[ ! -e $test_tmp/signalled ]] || fail "terminal stop does not signal the sudo wrapper"
  pass "terminal updates stop a retained sudo wrapper through its stdin"
fi

# A previous version's state has no pipe. Its delayed TERM path still works.
mkdir -p "$XDG_RUNTIME_DIR/omarchy-update-stay-awake"
rm -f "$test_tmp/child" "$test_tmp/wrapper"
pkexec systemd-inhibit sleep 30 >/dev/null 2>&1 &
legacy_pid=$!
printf '%s %s\n' "$legacy_pid" "$(awk '{print $22}' "/proc/$legacy_pid/stat")" >"$XDG_RUNTIME_DIR/omarchy-update-stay-awake/inhibit-pid"
sleep 0.1
"$ROOT/bin/omarchy-update-stay-awake" stop
[[ ! -d $XDG_RUNTIME_DIR/omarchy-update-stay-awake ]] || fail "legacy stop removes helper state"
wait "$legacy_pid"
pass "legacy state tolerates wrapper signal teardown longer than one second"

# Failure must remain visible and retain enough state for a later retry.
cat >"$test_tmp/bin/systemd-inhibit" <<'SH'
#!/bin/bash
echo "$$" >"$TEST_TMP/child"
exec sleep 30
SH
rm -f "$test_tmp/child" "$test_tmp/wrapper"
"$ROOT/bin/omarchy-update-stay-awake" start
assert_retained_child
if "$ROOT/bin/omarchy-update-stay-awake" stop >"$test_tmp/failed-stop.out" 2>&1; then
  fail "an unresponsive inhibitor makes stop fail"
fi
grep -qx 'Failed to stop the Omarchy update sleep inhibitor.' "$test_tmp/failed-stop.out" ||
  fail "stop reports an unresponsive inhibitor"
[[ -s $XDG_RUNTIME_DIR/omarchy-update-stay-awake/inhibit-pid && -p $XDG_RUNTIME_DIR/omarchy-update-stay-awake/inhibit-control ]] ||
  fail "failed stop retains the PID and control pipe for a retry"
kill "$(<"$test_tmp/child")"
"$ROOT/bin/omarchy-update-stay-awake" stop
[[ ! -d $XDG_RUNTIME_DIR/omarchy-update-stay-awake ]] || fail "retry removes helper state after the child exits"
pass "an unresponsive inhibitor fails cleanup and retains state for a retry"
