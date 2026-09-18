#!/bin/bash
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/base-test.sh"

test_tmp=$(mktemp -d)
trap 'rm -rf "$test_tmp"' EXIT
mkdir -p "$test_tmp/bin"
export GNUPGHOME="$test_tmp/gnupg"
mkdir -m700 "$GNUPGHOME"
config="$test_tmp/pacman.conf"
calls="$test_tmp/calls"
cat >"$config" <<'CONF'
[options]
SigLevel = Required DatabaseOptional
[custom]
SigLevel = Optional TrustAll
Server = https://custom.example
  [omarchy-aarch64]
  SigLevel   = Optional TrustAll
Server = https://github.com/omarchy-mac/omarchy-pkgs-aarch64/releases/download/rc
[later]
SigLevel = Never
Server = file:///later
CONF

cat >"$test_tmp/bin/sudo" <<'SH'
#!/bin/bash
if [[ $1 == pacman-key && $2 == --populate ]]; then
  echo "populate $3" >>"$TEST_CALLS"
  exit 0
fi
if [[ $1 == pacman-key && $2 == --add ]]; then
  echo "add $3" >>"$TEST_CALLS"
  exit 0
fi
if [[ $1 == pacman-key && $2 == --lsign-key ]]; then
  echo "lsign $3" >>"$TEST_CALLS"
  exit 0
fi
if [[ $1 == pacman-key && $2 == --finger ]]; then
  printf 'Key fingerprint = FBD6 874D 423C 418D DB6D  143E ECE1 9CDD E306 DBD2\n'
  exit 0
fi
exit 99
SH
chmod +x "$test_tmp/bin/sudo"

pacman() {
  [[ $* == '-Q omarchy-mac-keyring' ]] || return 99
  printf 'omarchy-mac-keyring 20260914-2\n'
}
omarchy-pkg-missing() { return 1; }
omarchy-pkg-add() { echo "add $*" >>"$calls"; }
export TEST_CALLS="$calls"
export PATH="$test_tmp/bin:$PATH"
export OMARCHY_PATH="$ROOT"

# Redirect only the fixture's machine config reference.
sed "s|/etc/pacman.conf|$config|g" "$ROOT/migrations/1789316115.sh" >"$test_tmp/migration.sh"
(source "$test_tmp/migration.sh" >/dev/null)
(source "$test_tmp/migration.sh" >/dev/null)

[[ $(grep -c '^populate omarchy-mac$' "$calls") == 2 ]] || fail 'migration repopulates trust idempotently'
grep -qxF '  SigLevel   = Optional TrustAll' "$config" ||
  fail 'bootstrap migration changed policy before the signed repository exists'
sed -n '/^\[custom\]/,/^\[/p' "$config" | grep -qxF 'SigLevel = Optional TrustAll' ||
  fail 'migration changed another repository policy'
sed -n '/^\[later\]/,$p' "$config" | grep -qxF 'SigLevel = Never' ||
  fail 'migration changed a later repository policy'
pass 'existing installs populate fork trust while retaining the one-time bootstrap policy'

: >"$calls"
omarchy-pkg-missing() { return 0; }
pacman() { [[ $* == '-Q omarchy-mac-keyring' ]] || return 99; return 1; }
(source "$test_tmp/migration.sh" >/dev/null)
grep -qxF "add $ROOT/default/pacman/keyrings/omarchy-mac.gpg" "$calls" ||
  fail 'missing package imports the pinned checkout key' "$(cat "$calls")"
grep -qxF 'lsign FBD6874D423C418DDB6D143EECE19CDDE306DBD2' "$calls" ||
  fail 'missing package locally signs the pinned checkout key' "$(cat "$calls")"
! grep -q '^populate ' "$calls" || fail 'missing package cannot populate a packaged keyring'
pass 'ARM skip and git-link import the pinned checkout key instead of populating /usr'

source "$ROOT/install/helpers/arm-channel.sh"
missing="$test_tmp/missing-policy.conf"
sed '/SigLevel   = Optional TrustAll/d' "$config" >"$missing"
omarchy_arm_signature_policy_render "$missing" 'PackageRequired DatabaseOptional TrustedOnly' "$test_tmp/rendered"
omarchy_arm_signature_policy_assert "$test_tmp/rendered" 'PackageRequired DatabaseOptional TrustedOnly' ||
  fail 'renderer does not establish effective policy when the stanza inherited one'

ln -s "$config" "$test_tmp/pacman-link.conf"
if omarchy_arm_signature_policy_apply "$test_tmp/pacman-link.conf" 'PackageRequired DatabaseOptional TrustedOnly' >/dev/null 2>&1; then
  fail 'policy application follows a pacman.conf symlink'
fi
pass 'policy rendering handles formatting and missing overrides while application rejects symlinks'

# Execute the pending queue as production does, using the real package helpers.
# A source checkout can reach this migration before the required package is
# available. GPG inspects real public fixtures; package and trust writes are stubbed.
unset -f omarchy-pkg-missing omarchy-pkg-add
export PATH="$ROOT/bin:$PATH"
export TEST_INSTALLED_VERSION="$test_tmp/installed-version"
pacman() {
  case "$*" in
    '-Q omarchy-mac-keyring')
      [[ -s $TEST_INSTALLED_VERSION ]] || return 1
      printf 'omarchy-mac-keyring %s\n' "$(cat "$TEST_INSTALLED_VERSION")" ;;
    '-Si omarchy-mac-keyring') [[ $TEST_AVAILABLE == 1 ]] ;;
    '-S --noconfirm --needed omarchy-mac-keyring')
      printf '%s\n' "$*" >>"$TEST_CALLS"
      [[ $TEST_AVAILABLE == 1 ]] || return 1
      (( TEST_INSTALL_FAILURE == 0 )) || return "$TEST_INSTALL_FAILURE"
      printf '%s\n' "$TEST_REPO_VERSION" >"$TEST_INSTALLED_VERSION" ;;
    *) return 99 ;;
  esac
}
sudo() {
  case "$*" in
    'pacman -S --noconfirm --needed omarchy-mac-keyring') pacman "${@:2}" ;;
    'pacman-key --populate omarchy-mac')
      printf '%s\n' "$*" >>"$TEST_CALLS"
      return "$TEST_POPULATE_FAILURE" ;;
    "pacman-key --add $OMARCHY_PATH/default/pacman/keyrings/omarchy-mac.gpg")
      printf '%s\n' "$*" >>"$TEST_CALLS"
      return "$TEST_IMPORT_FAILURE" ;;
    'pacman-key --lsign-key FBD6874D423C418DDB6D143EECE19CDDE306DBD2')
      printf '%s\n' "$*" >>"$TEST_CALLS"
      return "$TEST_SIGN_FAILURE" ;;
    'pacman-key --finger FBD6874D423C418DDB6D143EECE19CDDE306DBD2')
      printf '%s\n' "$*" >>"$TEST_CALLS"
      if [[ $TEST_MISSING_KEY == 1 ]]; then
        # Even a successful command returning the wrong key must fail the gate.
        printf '%s\n' F3C5AE3FCFFC738C301E30A8F0C548C0D27279F7
      else
        printf '%s\n' FBD6874D423C418DDB6D143EECE19CDDE306DBD2
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
mkdir -p "$test_tmp/source/migrations" "$test_tmp/source/default/pacman/keyrings"
fixture_key="$test_tmp/source/default/pacman/keyrings/omarchy-mac.gpg"
for name in 1789316115 1789407945; do
  cp "$ROOT/migrations/$name.sh" "$test_tmp/source/migrations/"
done
for scenario in current newer old-only combined-old missing install-current install-old install-failure version-error populate fingerprint fingerprint-command missing-file symlink old-key combined-key invalid-key import sign fallback-fingerprint fallback-fingerprint-command; do
  markers="$test_tmp/markers-$scenario"
  mkdir "$markers"
  rm -f "$fixture_key"
  cp "$ROOT/default/pacman/keyrings/omarchy-mac.gpg" "$fixture_key"
  printf '20260914-2\n' >"$TEST_INSTALLED_VERSION"
  export TEST_AVAILABLE=0 TEST_REPO_VERSION=20260914-2 TEST_POPULATE_FAILURE=0 TEST_MISSING_KEY=0
  export TEST_INSTALL_FAILURE=0 TEST_VERCMP_FAILURE=0 TEST_IMPORT_FAILURE=0 TEST_SIGN_FAILURE=0 TEST_FINGER_FAILURE=0
  case "$scenario" in
    missing|missing-file|symlink|old-key|combined-key|invalid-key|import|sign|fallback-*) : >"$TEST_INSTALLED_VERSION" ;;
  esac
  case "$scenario" in
    newer) printf '20260915-1\n' >"$TEST_INSTALLED_VERSION" ;;
    old-only) printf '20260913-1\n' >"$TEST_INSTALLED_VERSION" ;;
    combined-old) printf '20260914-1\n' >"$TEST_INSTALLED_VERSION" ;;
    install-current) : >"$TEST_INSTALLED_VERSION"; TEST_AVAILABLE=1 ;;
    install-old) : >"$TEST_INSTALLED_VERSION"; TEST_AVAILABLE=1; TEST_REPO_VERSION=20260913-1 ;;
    install-failure) : >"$TEST_INSTALLED_VERSION"; TEST_AVAILABLE=1; TEST_INSTALL_FAILURE=1 ;;
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
  if OMARCHY_PATH="$test_tmp/source" OMARCHY_MIGRATION_STATE="$markers" bash "$ROOT/bin/omarchy-migrate" >"$test_tmp/queue-result" 2>&1; then
    case "$scenario" in current|newer|install-current|missing) ;; *) fail "$scenario accepted" ;; esac
    [[ -f $markers/1789316115.sh && -f $markers/1789407945.sh ]] || fail 'bootstrap queue did not complete'
    if [[ $scenario == "missing" ]]; then
      expected_calls="pacman-key --add $fixture_key"$'\n''pacman-key --finger FBD6874D423C418DDB6D143EECE19CDDE306DBD2'$'\n''pacman-key --lsign-key FBD6874D423C418DDB6D143EECE19CDDE306DBD2'
      [[ $(cat "$TEST_CALLS") == "$expected_calls"$'\n'"$expected_calls" ]] || fail 'fallback queue did not import, verify and sign only the new primary twice' "$(cat "$TEST_CALLS")"
    else
      [[ $(grep -c '^pacman-key --populate omarchy-mac$' "$TEST_CALLS") == 2 ]] || fail 'packaged queue did not populate twice'
      if grep -qE -- '--(add|lsign-key)' "$TEST_CALLS"; then fail 'installed package used checkout fallback'; fi
    fi
    : >"$TEST_CALLS"
    OMARCHY_PATH="$test_tmp/source" OMARCHY_MIGRATION_STATE="$markers" bash "$ROOT/bin/omarchy-migrate" >/dev/null
    [[ ! -s $TEST_CALLS ]] || fail 'completed bootstrap queue reran'
  else
    case "$scenario" in current|newer|install-current|missing) fail "$scenario failed" "$(cat "$test_tmp/queue-result")" ;; esac
    [[ ! -e $markers/1789316115.sh && ! -e $markers/1789407945.sh ]] || fail 'failed bootstrap advanced the queue'
    expected_error=""
    case "$scenario" in
      populate) expected_error='Could not populate Omarchy Mac signing trust' ;;
      fingerprint|fingerprint-command|fallback-fingerprint|fallback-fingerprint-command) expected_error='is missing after keyring population or import' ;;
      missing-file|symlink) expected_error='Pinned Omarchy Mac signing key is missing or unsafe' ;;
      old-key|combined-key) expected_error='must contain only signing primary' ;;
      invalid-key) expected_error='Could not read the pinned Omarchy Mac signing key' ;;
      import) expected_error='Could not import the pinned Omarchy Mac signing key' ;;
      sign) expected_error='Could not locally sign the pinned Omarchy Mac signing key' ;;
      old-only|combined-old|install-old) expected_error='20260914-2 or newer is required' ;;
    esac
    if [[ -n $expected_error ]]; then
      grep -qF "$expected_error" "$test_tmp/queue-result" || fail "$scenario has no useful diagnostic" "$(cat "$test_tmp/queue-result")"
    fi
    case "$scenario" in
      old-only|combined-old|install-old|install-failure|version-error|missing-file|symlink|old-key|combined-key|invalid-key)
        if grep -qF 'pacman-key' "$TEST_CALLS"; then fail "$scenario touched trust"; fi ;;
      import|fallback-fingerprint|fallback-fingerprint-command)
        if grep -qF -- '--lsign-key' "$TEST_CALLS"; then fail "$scenario still signed the key"; fi ;;
    esac
    if grep -qF 'can only `return' "$test_tmp/queue-result"; then fail 'top-level return error'; fi
  fi
done
pass 'pending bootstrap uses real helpers, checks installed versions and pinned public bytes, and stops the marker queue on every trust failure'
