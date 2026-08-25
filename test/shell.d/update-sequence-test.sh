#!/bin/bash

set -euo pipefail

source "$(dirname "$0")/base-test.sh"

test_tmp=$(mktemp -d)
trap 'rm -rf "$test_tmp"' EXIT

stub_bin="$test_tmp/bin"
mkdir -p "$stub_bin"

# Every step omarchy-update runs, recorded in order with the unattended flag it
# was handed. One of them can be told to fail.
steps=(
  omarchy-update-lock
  omarchy-update-requires-free-space
  omarchy-update-pkg-prune
  omarchy-update-stay-awake
  omarchy-update-dev
  omarchy-update-keyring
  omarchy-update-system-pkgs
  omarchy-migrate
  omarchy-hook
  omarchy-update-aur-pkgs
  omarchy-update-mise
  omarchy-update-orphan-pkgs
  omarchy-update-analyze-logs
  omarchy-update-status
  omarchy-update-restart
)

for step in "${steps[@]}"; do
  cat >"$stub_bin/$step" <<'STUB'
#!/bin/bash
printf '%s unattended=%s\n' "${0##*/}" "${OMARCHY_UPDATE_UNATTENDED:-}" >>"$STEP_LOG"
[[ ${FAILING_STEP:-} != "${0##*/}" ]] || exit 1
STUB
  chmod +x "$stub_bin/$step"
done

cat >"$stub_bin/omarchy-snapshot" <<'STUB'
#!/bin/bash
printf 'omarchy-snapshot %s unattended=%s\n' "${1:-}" "${OMARCHY_UPDATE_UNATTENDED:-}" >>"$STEP_LOG"
case "${1:-}" in
check)
  if (( ${SNAPSHOT_CHECK_STATUS:-0} != 0 )); then
    echo "Automatic rollback unavailable in test" >&2
    exit "$SNAPSHOT_CHECK_STATUS"
  fi
  ;;
create)
  if (( ${SNAPSHOT_CREATE_STATUS:-0} != 0 )); then
    echo "Snapshot creation failed in test" >&2
    exit "$SNAPSHOT_CREATE_STATUS"
  fi
  [[ ${FAILING_STEP:-} != "omarchy-snapshot" ]] || exit 1
  ;;
esac
STUB
chmod +x "$stub_bin/omarchy-snapshot"

cat >"$stub_bin/omarchy-update-confirm" <<'STUB'
#!/bin/bash
if [[ ${1:-} == "--no-rollback" ]]; then
  printf 'omarchy-update-confirm --no-rollback unattended=%s\n' "${OMARCHY_UPDATE_UNATTENDED:-}" >>"$STEP_LOG"
  exit "${NO_ROLLBACK_CONFIRM_STATUS:-0}"
else
  printf 'omarchy-update-confirm unattended=%s\n' "${OMARCHY_UPDATE_UNATTENDED:-}" >>"$STEP_LOG"
  exit "${CONFIRM_STATUS:-0}"
fi
STUB
chmod +x "$stub_bin/omarchy-update-confirm"

# OMARCHY_UPDATE_LOGGED stands in for the script(1) wrapper the update re-execs
# itself under; the stubbed lock reports itself already held.
run_update() {
  : >"$test_tmp/steps"
  STEP_LOG="$test_tmp/steps" \
    FAILING_STEP="${FAILING_STEP:-}" \
    SNAPSHOT_CHECK_STATUS="${SNAPSHOT_CHECK_STATUS:-0}" \
    SNAPSHOT_CREATE_STATUS="${SNAPSHOT_CREATE_STATUS:-0}" \
    CONFIRM_STATUS="${CONFIRM_STATUS:-0}" \
    NO_ROLLBACK_CONFIRM_STATUS="${NO_ROLLBACK_CONFIRM_STATUS:-0}" \
    OMARCHY_UPDATE_LOGGED=1 \
    PATH="$stub_bin:$PATH" \
    bash "$ROOT/bin/omarchy-update" "$@" >"$test_tmp/out" 2>"$test_tmp/err"
}

steps_run() {
  awk '
    $1 == "omarchy-snapshot" { print $1, $2; next }
    $1 == "omarchy-update-confirm" && $2 == "--no-rollback" { print $1, $2; next }
    { print $1 }
  ' "$test_tmp/steps"
}

expected_tail() {
  printf '%s\n' \
    omarchy-update-stay-awake \
    omarchy-update-dev \
    omarchy-update-keyring \
    omarchy-update-system-pkgs \
    omarchy-migrate \
    omarchy-hook \
    omarchy-update-aur-pkgs \
    omarchy-update-mise \
    omarchy-update-orphan-pkgs \
    omarchy-update-analyze-logs \
    omarchy-update-status \
    omarchy-update-stay-awake \
    omarchy-update-restart
}

expected_unattended() {
  printf '%s\n' \
    omarchy-update-lock \
    omarchy-update-requires-free-space \
    'omarchy-snapshot check' \
    omarchy-update-pkg-prune \
    'omarchy-snapshot create'
  expected_tail
}

expected_interactive() {
  printf '%s\n' \
    omarchy-update-lock \
    omarchy-update-requires-free-space \
    'omarchy-snapshot check' \
    omarchy-update-confirm \
    omarchy-update-pkg-prune \
    'omarchy-snapshot create'
  expected_tail
}

run_update -y || fail "an update where everything works reports a failure"
diff <(expected_unattended) <(steps_run) >"$test_tmp/order" || fail "an unattended update does not check rollback before pruning" "$(cat "$test_tmp/order")"
grep -q '^omarchy-update-system-pkgs unattended=1$' "$test_tmp/steps" || fail "-y does not mark the update unattended"
pass "an unattended update checks rollback before pruning and then runs every step"

run_update </dev/null || fail "a confirmed update reports a failure"
diff <(expected_interactive) <(steps_run) >"$test_tmp/order" || fail "an interactive update does not check rollback before confirmation and pruning" "$(cat "$test_tmp/order")"
grep -q '^omarchy-update-system-pkgs unattended=$' "$test_tmp/steps" || fail "an update a person confirmed is treated as unattended"
pass "an interactive update checks rollback before its normal confirmation"

SNAPSHOT_CREATE_STATUS=1 run_update </dev/null || fail "accepting a late no-rollback risk reports a failure"
{
  printf '%s\n' \
    omarchy-update-lock \
    omarchy-update-requires-free-space \
    'omarchy-snapshot check' \
    omarchy-update-confirm \
    omarchy-update-pkg-prune \
    'omarchy-snapshot create' \
    'omarchy-update-confirm --no-rollback'
  expected_tail
} >"$test_tmp/expected"
diff "$test_tmp/expected" <(steps_run) >"$test_tmp/order" || fail "a late snapshot failure does not require its dedicated confirmation" "$(cat "$test_tmp/order")"
grep -qF 'WARNING: Automatic rollback became unavailable after the preflight.' "$test_tmp/err" || fail "a late snapshot failure does not warn" "$(cat "$test_tmp/err")"
pass "an interactive update confirms a late snapshot failure before package changes"

NO_ROLLBACK_CONFIRM_STATUS=1 SNAPSHOT_CREATE_STATUS=1 run_update </dev/null || fail "cancelling a late no-rollback risk is not an update error"
printf '%s\n' \
  omarchy-update-lock \
  omarchy-update-requires-free-space \
  'omarchy-snapshot check' \
  omarchy-update-confirm \
  omarchy-update-pkg-prune \
  'omarchy-snapshot create' \
  'omarchy-update-confirm --no-rollback' \
  omarchy-update-stay-awake >"$test_tmp/expected"
diff "$test_tmp/expected" <(steps_run) >"$test_tmp/order" || fail "cancelling a late snapshot failure still mutates packages" "$(cat "$test_tmp/order")"
! grep -q '^omarchy-update-system-pkgs ' "$test_tmp/steps" || fail "cancelling a late snapshot failure still updates packages"
pass "cancelling a late snapshot failure stops before installed package changes"

SNAPSHOT_CREATE_STATUS=1 run_update -y || fail "an unattended late snapshot failure reports a failure"
diff <(expected_unattended) <(steps_run) >"$test_tmp/order" || fail "an unattended late snapshot failure does not continue in order" "$(cat "$test_tmp/order")"
grep -qF 'WARNING: Automatic rollback became unavailable after the preflight.' "$test_tmp/err" || fail "an unattended late snapshot failure does not warn" "$(cat "$test_tmp/err")"
grep -qF 'Unattended update will continue without automatic rollback.' "$test_tmp/err" || fail "an unattended late snapshot failure does not log continuation" "$(cat "$test_tmp/err")"
! grep -q '^omarchy-update-confirm' "$test_tmp/steps" || fail "an unattended late snapshot failure prompts"
pass "an unattended late snapshot failure warns and continues"

SNAPSHOT_CHECK_STATUS=1 SNAPSHOT_CREATE_STATUS=1 run_update </dev/null || fail "a confirmed update without rollback reports a failure"
{
  printf '%s\n' \
    omarchy-update-lock \
    omarchy-update-requires-free-space \
    'omarchy-snapshot check' \
    omarchy-update-confirm \
    'omarchy-update-confirm --no-rollback' \
    omarchy-update-pkg-prune \
    'omarchy-snapshot create'
  expected_tail
} >"$test_tmp/expected"
diff "$test_tmp/expected" <(steps_run) >"$test_tmp/order" || fail "an interactive no-rollback update does not require its dedicated confirmation" "$(cat "$test_tmp/order")"
grep -qF 'WARNING: This update has no automatic rollback.' "$test_tmp/err" || fail "an unavailable rollback emits a prominent warning" "$(cat "$test_tmp/err")"
(( $(grep -c '^omarchy-update-confirm --no-rollback ' "$test_tmp/steps") == 1 )) || fail "a preflight failure prompts for no-rollback risk more than once" "$(cat "$test_tmp/steps")"
pass "an interactive preflight failure confirms no-rollback risk only once"

NO_ROLLBACK_CONFIRM_STATUS=1 SNAPSHOT_CHECK_STATUS=1 run_update </dev/null || fail "cancelling the no-rollback confirmation is not an update error"
printf '%s\n' \
  omarchy-update-lock \
  omarchy-update-requires-free-space \
  'omarchy-snapshot check' \
  omarchy-update-confirm \
  'omarchy-update-confirm --no-rollback' \
  omarchy-update-stay-awake >"$test_tmp/expected"
diff "$test_tmp/expected" <(steps_run) >"$test_tmp/order" || fail "cancelling no-rollback risk still starts the update" "$(cat "$test_tmp/order")"
! grep -q '^omarchy-update-pkg-prune ' "$test_tmp/steps" || fail "cancelling no-rollback risk still prunes packages"
pass "cancelling the no-rollback confirmation stops before package pruning"

SNAPSHOT_CHECK_STATUS=1 run_update -y || fail "an unattended update without rollback reports a failure"
diff <(expected_unattended) <(steps_run) >"$test_tmp/order" || fail "an unattended no-rollback update does not continue in order" "$(cat "$test_tmp/order")"
grep -qF 'WARNING: This update has no automatic rollback.' "$test_tmp/err" || fail "an unattended no-rollback update does not warn" "$(cat "$test_tmp/err")"
grep -qF 'Unattended update will continue without automatic rollback.' "$test_tmp/err" || fail "an unattended no-rollback update does not log that it will continue" "$(cat "$test_tmp/err")"
! grep -q '^omarchy-update-confirm' "$test_tmp/steps" || fail "an unattended no-rollback update prompts for confirmation"
pass "an unattended no-rollback update warns and continues"

# Migrations ship with the packages the upgrade installs and are written against
# them. Running them against what is still on disk is the failure this ordering
# exists to prevent, so the update stops where the packages did.
if FAILING_STEP=omarchy-update-system-pkgs run_update -y; then
  fail "an update whose packages did not upgrade passes for a whole one"
fi
for step in omarchy-migrate omarchy-hook omarchy-update-aur-pkgs omarchy-update-restart; do
  if grep -q "^$step " "$test_tmp/steps"; then
    fail "a blocked package upgrade still runs $step"
  fi
done
pass "a blocked package upgrade stops the update before it migrates"

grep -qFx '# omarchy:hidden=true' "$ROOT/bin/omarchy-update-confirm" || fail "update confirmation helper is hidden from command listings"
pass "update confirmation helper stays internal"
