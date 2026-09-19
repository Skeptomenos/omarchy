#!/bin/bash
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/base-test.sh"

umask 077
test_tmp=$(mktemp -d)
export GNUPGHOME="$test_tmp/gnupg"
trap 'gpgconf --homedir "$GNUPGHOME" --kill gpg-agent >/dev/null 2>&1 || true; rm -rf -- "$test_tmp"' EXIT
mkdir -m700 "$GNUPGHOME"
export TEST_CALLS="$test_tmp/calls"
export TEST_NEW_KEY=FBD6874D423C418DDB6D143EECE19CDDE306DBD2
mkdir -p "$test_tmp/source/migrations" "$test_tmp/source/default/pacman/keyrings"
for name in 1789316115 1789407945; do
  cp "$ROOT/migrations/$name.sh" "$test_tmp/source/migrations/"
done
printf 'echo later >>"$TEST_CALLS"\n' >"$test_tmp/source/migrations/1789407946.sh"

# Generate secret material only in the disposable home. Never print or commit it.
gpg --batch --pinentry-mode loopback --passphrase '' --quick-generate-key \
  'Disposable migration fixture' ed25519 cert 1d >/dev/null 2>&1
fixture_primary=$(gpg --batch --with-colons --list-secret-keys 2>/dev/null | awk -F: '$1 == "fpr" { print $10; exit }')
gpg --batch --pinentry-mode loopback --passphrase '' --quick-add-key \
  "$fixture_primary" ed25519 sign 1d >/dev/null 2>&1
fixture_key="$test_tmp/source/default/pacman/keyrings/omarchy-mac.gpg"
cat "$ROOT/default/pacman/keyrings/omarchy-mac.gpg" >"$fixture_key"
gpg --batch --pinentry-mode loopback --passphrase '' --export-secret-keys \
  "$fixture_primary" >>"$fixture_key" 2>/dev/null
gpg --batch --with-colons --show-keys "$fixture_key" 2>/dev/null |
  awk -F: '$1 == "pub" { pub++ } $1 == "sec" { sec++ } $1 == "ssb" { ssb++ } END { exit !(pub == 1 && sec == 1 && ssb == 1) }' ||
  fail 'mixed fixture must contain the approved public certificate and disposable secret records'

pacman() { [[ $* == '-Q omarchy-mac-keyring' ]] || return 99; return 1; }
omarchy-pkg-missing() { return 0; }
omarchy-pkg-add() { :; }
omarchy-notification-dismiss() { :; }
sudo() {
  printf '%s\n' "$*" >>"$TEST_CALLS"
  case "$*" in
    "pacman-key --add $OMARCHY_PATH/default/pacman/keyrings/omarchy-mac.gpg") return 0 ;;
    "pacman-key --finger $TEST_NEW_KEY") printf '%s\n' "$TEST_NEW_KEY" ;;
    "pacman-key --lsign-key $TEST_NEW_KEY") return 0 ;;
    *) return 99 ;;
  esac
}
export -f pacman omarchy-pkg-missing omarchy-pkg-add omarchy-notification-dismiss sudo

rejected=1
for state in pending successor; do
  markers="$test_tmp/$state"
  mkdir "$markers"
  if [[ $state == "successor" ]]; then
    touch "$markers/1789316115.sh"
  fi
  : >"$TEST_CALLS"
  if OMARCHY_PATH="$test_tmp/source" OMARCHY_MIGRATION_STATE="$markers" bash "$ROOT/bin/omarchy-migrate" >"$test_tmp/result" 2>&1; then
    printf 'not ok - %s queue accepted mixed public and secret certificates\n' "$state" >&2
    rejected=0
  else
    grep -qF 'must contain only signing primary' "$test_tmp/result" || fail "$state has no key rejection diagnostic"
    [[ ! -s $TEST_CALLS ]] || fail "$state touched trust before rejecting secret records"
    [[ ! -e $markers/1789407945.sh && ! -e $markers/1789407946.sh ]] || fail "$state advanced the queue"
    if [[ $state == "pending" ]]; then
      [[ ! -e $markers/1789316115.sh ]] || fail 'failed bootstrap marker was written'
    else
      [[ -f $markers/1789316115.sh ]] || fail 'completed bootstrap marker was removed'
    fi
    pass "$state rejects mixed public and secret certificates before trust operations or later markers"
  fi
done
(( rejected )) || fail 'secret records bypassed a migration validator'
