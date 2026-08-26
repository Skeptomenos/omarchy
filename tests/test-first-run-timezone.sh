#!/bin/bash
# Checks when the first-run timezone prompt fires. A machine on the image's
# default has never been told where it is; one that has been set should not be
# nagged. Needs no root: timedatectl is stubbed on PATH.

set -uo pipefail

LEAF="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)/install/user/first-run/timezone.sh"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
pass=0
failures=0

check() {
  local label="$1"
  shift
  if "$@"; then
    echo "✓ $label"
    ((++pass))
  else
    echo "✗ $label"
    ((++failures))
  fi
}

not() {
  ! "$@"
}

# The leaf is sourced by the first-run driver, so it is sourced here too. Record
# the notification argv exactly, and preserve the sender's exit status.
run_timezone_leaf() {
  local timezone="$1" notification_status="${2:-0}"
  rm -rf "$WORK/bin" "$WORK/notification-args"
  mkdir -p "$WORK/bin"
  printf '#!/bin/bash\necho %s\n' "$timezone" >"$WORK/bin/timedatectl"
  cat >"$WORK/bin/omarchy-notification-send" <<'SH'
#!/bin/bash
printf '%s\0' "$@" >"$OMARCHY_TEST_NOTIFICATION_ARGS"
exit "$OMARCHY_TEST_NOTIFICATION_STATUS"
SH
  chmod +x "$WORK/bin"/*

  OMARCHY_TEST_NOTIFICATION_ARGS="$WORK/notification-args" \
    OMARCHY_TEST_NOTIFICATION_STATUS="$notification_status" \
    PATH="$WORK/bin:$PATH" bash -c "source '$LEAF'" >/dev/null 2>&1
}

prompts_for_timezone() {
  run_timezone_leaf "$1" || return
  [[ -e $WORK/notification-args ]]
}

uses_safe_notification_argv() {
  local -a actual expected=(
    -u critical -g 󰥔
    "Set your timezone"
    "This machine is on UTC. Click to choose yours."
    --exec
    omarchy-launch-floating-terminal-with-presentation
    omarchy-cmd-tzupdate-enhanced
  )

  run_timezone_leaf UTC || return
  mapfile -d '' -t actual <"$WORK/notification-args"
  ((${#actual[@]} == ${#expected[@]})) || return 1

  local i
  for ((i = 0; i < ${#expected[@]}; i++)); do
    [[ ${actual[i]} == "${expected[i]}" ]] || return 1
  done
}

reports_notification_failure() {
  local status
  run_timezone_leaf UTC 23
  status=$?
  (( status == 23 ))
}

check "a machine still on UTC is prompted" prompts_for_timezone UTC
check "a machine with a real zone is left alone" \
  not prompts_for_timezone America/New_York
check "an unset timezone is prompted" prompts_for_timezone ""
check "another real zone is left alone" not prompts_for_timezone Europe/London
check "the notification carries a safe click argv" uses_safe_notification_argv
check "a notification failure fails the timezone step" reports_notification_failure

echo
echo "=== $pass checks passed, $failures failed ==="
(( failures == 0 ))
