#!/bin/bash
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/base-test.sh"

test_tmp=$(mktemp -d)
trap 'rm -rf "$test_tmp"' EXIT
export TEST_CALLS="$test_tmp/calls"
export GNUPGHOME="$test_tmp/gnupg"
mkdir -m700 "$GNUPGHOME"
new_key=FBD6874D423C418DDB6D143EECE19CDDE306DBD2
export TEST_NEW_KEY="$new_key"
mkdir -p "$test_tmp/source/migrations" "$test_tmp/source/default/pacman/keyrings"
fixture_key="$test_tmp/source/default/pacman/keyrings/omarchy-mac.gpg"
for name in 1789316115 1789407945; do
  cp "$ROOT/migrations/$name.sh" "$test_tmp/source/migrations/"
done
printf 'echo later >>"$TEST_CALLS"\n' >"$test_tmp/source/migrations/1789407946.sh"
pacman() {
  [[ $* == '-Q omarchy-mac-keyring' ]] || return 99
  [[ ${TEST_VERSION:-20260914-2} != missing ]] || return 1
  printf 'omarchy-mac-keyring %s\n' "${TEST_VERSION:-20260914-2}"
}
sudo() {
  printf '%s\n' "$*" >>"$TEST_CALLS"
  case "$*" in
    'pacman-key --populate omarchy-mac') return "${TEST_POPULATE_FAILURE:-0}" ;;
    "pacman-key --add $OMARCHY_PATH/default/pacman/keyrings/omarchy-mac.gpg") return "$TEST_IMPORT_FAILURE" ;;
    "pacman-key --lsign-key $TEST_NEW_KEY") return "$TEST_SIGN_FAILURE" ;;
    "pacman-key --finger $TEST_NEW_KEY")
      if [[ $TEST_MISSING_KEY == 1 ]]; then
        printf '%s\n' F3C5AE3FCFFC738C301E30A8F0C548C0D27279F7
      else
        printf '%s\n' "$TEST_NEW_KEY"
      fi
      return "$TEST_FINGER_FAILURE" ;;
    *) return 99 ;;
  esac
}
vercmp() {
  (( TEST_VERCMP_FAILURE == 0 )) || return "$TEST_VERCMP_FAILURE"
  command vercmp "$@"
}
omarchy-notification-dismiss() { :; }
export -f pacman sudo vercmp omarchy-notification-dismiss

for scenario in current newer missing older old-only version-error populate fingerprint fingerprint-command missing-file symlink old-key combined-key invalid-key import sign fallback-fingerprint fallback-fingerprint-command; do
  markers="$test_tmp/$scenario"
  mkdir "$markers"
  rm -f "$fixture_key"
  cp "$ROOT/default/pacman/keyrings/omarchy-mac.gpg" "$fixture_key"
  # Obsolete development markers must not prevent the retained successor.
  # This models marker handling only, not installing unsigned RC4 under strict policy.
  touch "$markers/1789316115.sh" "$markers/1789317000.sh" "$markers/1789390468.sh" "$markers/1789407944.sh"
  export TEST_VERSION=20260914-2 TEST_POPULATE_FAILURE=0 TEST_MISSING_KEY=0
  export TEST_VERCMP_FAILURE=0 TEST_IMPORT_FAILURE=0 TEST_SIGN_FAILURE=0 TEST_FINGER_FAILURE=0
  case "$scenario" in
    missing|missing-file|symlink|old-key|combined-key|invalid-key|import|sign|fallback-*) TEST_VERSION=missing ;;
  esac
  case "$scenario" in
    newer) TEST_VERSION=20260915-1 ;;
    older) TEST_VERSION=20260914-1 ;;
    old-only) TEST_VERSION=20260913-1 ;;
    version-error) TEST_VERCMP_FAILURE=1 ;;
    populate) TEST_POPULATE_FAILURE=1 ;;
    fingerprint|fallback-fingerprint) TEST_MISSING_KEY=1 ;;
    fingerprint-command|fallback-fingerprint-command) TEST_FINGER_FAILURE=1 ;;
    missing-file) rm "$fixture_key" ;;
    symlink) rm "$fixture_key"; ln -s "$ROOT/default/pacman/keyrings/omarchy-mac.gpg" "$fixture_key" ;;
    old-key) cp "$ROOT/test/fixtures/omarchy-mac-keyring-20260913-1/omarchy-mac.gpg" "$fixture_key" ;;
    combined-key) cp "$ROOT/test/fixtures/omarchy-mac-keyring-20260914-1/omarchy-mac.gpg" "$fixture_key" ;;
    invalid-key) printf 'not a key\n' >"$fixture_key" ;;
    import) TEST_IMPORT_FAILURE=1 ;;
    sign) TEST_SIGN_FAILURE=1 ;;
  esac
  : >"$TEST_CALLS"
  if OMARCHY_PATH="$test_tmp/source" OMARCHY_MIGRATION_STATE="$markers" bash "$ROOT/bin/omarchy-migrate" >"$test_tmp/result" 2>&1; then
    case "$scenario" in current|newer|missing) ;; *) fail "$scenario accepted" ;; esac
    [[ -f $markers/1789407945.sh && -f $markers/1789407946.sh ]] || fail 'successor queue markers missing'
    if [[ $scenario == "missing" ]]; then
      expected_calls="pacman-key --add $fixture_key"$'\n'"pacman-key --finger $new_key"$'\n'"pacman-key --lsign-key $new_key"$'\n''later'
    else
      expected_calls="pacman-key --populate omarchy-mac"$'\n'"pacman-key --finger $new_key"$'\n''later'
    fi
    [[ $(cat "$TEST_CALLS") == "$expected_calls" ]] || fail 'unexpected successor trust operations' "$(cat "$TEST_CALLS")"
    : >"$TEST_CALLS"
    OMARCHY_PATH="$test_tmp/source" OMARCHY_MIGRATION_STATE="$markers" bash "$ROOT/bin/omarchy-migrate" >/dev/null
    [[ ! -s $TEST_CALLS ]] || fail 'completed successor ran twice'
  else
    case "$scenario" in current|newer|missing) fail "$scenario failed" "$(cat "$test_tmp/result")" ;; esac
    [[ ! -e $markers/1789407945.sh && ! -e $markers/1789407946.sh ]] || fail 'failed successor advanced the queue'
    expected_error=""
    case "$scenario" in
      older|old-only) expected_error='20260914-2 or newer is required' ;;
      populate) expected_error='Could not populate Omarchy Mac signing trust' ;;
      fingerprint|fingerprint-command|fallback-fingerprint|fallback-fingerprint-command) expected_error='is missing after keyring population or import' ;;
      missing-file|symlink) expected_error='Pinned Omarchy Mac signing key is missing or unsafe' ;;
      old-key|combined-key) expected_error='must contain only signing primary' ;;
      invalid-key) expected_error='Could not read the pinned Omarchy Mac signing key' ;;
      import) expected_error='Could not import the pinned Omarchy Mac signing key' ;;
      sign) expected_error='Could not locally sign the pinned Omarchy Mac signing key' ;;
    esac
    if [[ -n $expected_error ]]; then
      grep -qF "$expected_error" "$test_tmp/result" || fail "$scenario has no useful diagnostic" "$(cat "$test_tmp/result")"
    fi
    if grep -qF 'can only `return' "$test_tmp/result"; then fail 'top-level return error'; fi
    case "$scenario" in
      older|old-only|version-error|missing-file|symlink|old-key|combined-key|invalid-key)
        [[ ! -s $TEST_CALLS ]] || fail "$scenario still touched trust" ;;
      import|fallback-fingerprint|fallback-fingerprint-command)
        if grep -qF -- '--lsign-key' "$TEST_CALLS"; then fail "$scenario still signed the key"; fi ;;
    esac
    if [[ $scenario == "sign" ]]; then
      TEST_SIGN_FAILURE=0
      : >"$TEST_CALLS"
      OMARCHY_PATH="$test_tmp/source" OMARCHY_MIGRATION_STATE="$markers" bash "$ROOT/bin/omarchy-migrate" >/dev/null
      [[ -f $markers/1789407945.sh && -f $markers/1789407946.sh ]] || fail 'retry did not complete the successor queue'
      [[ $(grep -c '^later$' "$TEST_CALLS") == 1 ]] || fail 'retry did not run the later migration'
    fi
  fi
  for name in 1789316115 1789317000 1789390468 1789407944; do
    [[ -f $markers/$name.sh ]] || fail 'successor removed an existing marker'
  done
done
pass 'renumbered successor repairs completed hosts through current packages or the pinned fallback, blocks later markers on failure and supports retry'
