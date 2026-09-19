#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

if (( EUID != 0 )); then
  if unshare --user --map-root-user true 2>/dev/null; then
    exec unshare --user --map-root-user bash "$0"
  fi
  pass "no unprivileged user namespace; skipping factory account cleanup"
  exit 0
fi

test_tmp=$(mktemp -d)
trap 'rm -rf "$test_tmp"' EXIT

# Load the production functions without self-elevation or the reset entrypoint.
awk '
  /^[a-z_]+\(\) \{/ { copying = 1 }
  copying {
    gsub(">/var/lib/omarchy/factory-reset.lock", ">\"$TOP_MNT/live-lock\"")
    print
  }
  /^}/ { copying = 0 }
' "$ROOT/bin/omarchy-system-factory-reset" >"$test_tmp/functions"

cat >"$test_tmp/reset" <<'SH'
#!/bin/bash
set -euo pipefail
source "$1/functions"
TOP_MNT="$2"
NEXT_NAME=@omarchy-reset-next
PROVISIONING_DIR=/var/lib/omarchy/provisioning
LOG_FILE="$TOP_MNT/reset.log"
RESET_STATE="$TOP_MNT/.state"
RESET_TXN_STAMP=$(date +%s%N)
RESET_TXN_FS=fixture
RESET_BOOT_BACKEND=limine
mkdir -p "$RESET_STATE"
: >"$RESET_STATE/inventory"

log() { printf '%s\n' "$1" >>"$LOG_FILE"; }
fail() { log "$1"; exit 1; }

# Account tools are real. Only snapshots, boot rebuilding, and system services
# are replaced: all writes stay inside this test's disposable directory.
btrfs() {
  if [[ $1 == "subvolume" && $2 == "snapshot" ]]; then
    shift 2
    local readonly=false
    if [[ $1 == "-r" ]]; then readonly=true; shift; fi
    local source="$1" target="$2"
    mkdir -p "$target"
    cp -a "$source/." "$target/"
    printf '%s\n' "${target##*/}" >"$target/.uuid"
    printf '%s\n' "$readonly" >"$target/read-only"
  else
    return 1
  fi
}
systemd-id128() { printf '%032d\n' 1; }
install_provisioning_units() { :; }
encrypted_install() { return 1; }
rebuild_next_boot() { touch "$TOP_MNT/rebuilt"; }
sync() { :; }
reset_inventory_verify_sources() { :; }
reset_uuid() { cat "$1/.uuid"; }
reset_transaction_record() { :; }
reset_state_write() { printf '%s\n' "$2" >"$1"; }
reset_closure_install() { :; }
reset_default_set() { :; }

userdel() {
  [[ ${FAIL_COMMAND:-} == "userdel" && $2 == "$FAIL_ROOT" ]] && return 42
  command userdel "$@"
}
usermod() {
  [[ ${FAIL_COMMAND:-} == "usermod" && $2 == "$FAIL_ROOT" ]] && return 42
  command usermod "$@"
}
rm() {
  [[ ${FAIL_COMMAND:-} == "rm" && $* == *"$FAIL_ROOT/etc/shadow-"* ]] && return 42
  command rm "$@"
}

stage_full_reset
SH

make_fixture() {
  local top="$1" root_hash="${2:-original-root-hash}"
  local factory="$top/@factory"
  mkdir -p "$top/@" "$factory/etc" "$factory/home/seller" \
    "$factory/usr/bin" "$factory/usr/share/omarchy/install/provisioning" \
    "$factory/var/lib/omarchy/provisioning/packages" "$factory/root"
  touch "$top/@/old-system" "$factory/home/seller/private-file" \
    "$factory/usr/share/omarchy/install/provisioning/omarchy-provision-owner.service" \
    "$factory/var/lib/omarchy/provisioning/packages/node-v0.tar.gz"
  printf '#!/bin/bash\n' >"$factory/usr/bin/omarchy-provision-owner"
  chmod +x "$factory/usr/bin/omarchy-provision-owner"
  printf 'true\n' >"$factory/read-only"
  cat >"$factory/etc/passwd" <<'EOF'
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/:/usr/bin/nologin
seller:x:1000:1000:Seller:/home/seller:/bin/bash
EOF
  printf 'root:%s:20000:0:99999:7:::\ndaemon:*:20000:0:99999:7:::\nseller:original-user-hash:20000:0:99999:7:::\n' \
    "$root_hash" >"$factory/etc/shadow"
  printf 'root:x:0:\ndaemon:x:1:\nseller:x:1000:\nwheel:x:998:seller\n' >"$factory/etc/group"
  printf 'root:!::\ndaemon:!::\nseller:!::\nwheel:!::seller\n' >"$factory/etc/gshadow"
  printf 'USERGROUPS_ENAB yes\n' >"$factory/etc/login.defs"
  printf 'seller:100000:65536\n' >"$factory/etc/subuid"
  printf 'seller:100000:65536\n' >"$factory/etc/subgid"
  chmod 600 "$factory/etc/"{shadow,gshadow}
  for file in passwd shadow group gshadow subuid subgid; do
    cp "$factory/etc/$file" "$factory/etc/$file-"
  done
}

assert_scrubbed() {
  local root="$1" file
  [[ $(awk -F: '$1 == "root" { print $2 }' "$root/etc/shadow") == "!" ]] ||
    fail "reset erases the root hash while keeping the account locked"
  ! grep -q 'original-.*-hash\|seller' "$root/etc/"{passwd,shadow,group,gshadow} ||
    fail "reset removes seller account credentials and group membership"
  [[ ! -e $root/home/seller ]] || fail "reset removes the seller's baseline home"
  grep -q '^daemon:\*:' "$root/etc/shadow" || fail "reset preserves service accounts"
  [[ $(stat -c '%a' "$root/etc/shadow") == "600" ]] || fail "shadow stays private"
  for file in passwd shadow group gshadow subuid subgid; do
    [[ ! -e $root/etc/$file- ]] || fail "reset removes the $file backup"
  done
}

for scenario in normal locked; do
  top="$test_tmp/$scenario"
  if [[ $scenario == "locked" ]]; then
    make_fixture "$top" '!'
  else
    make_fixture "$top"
  fi
  bash "$test_tmp/reset" "$test_tmp" "$top" || fail "$scenario reset stages successfully"
  assert_scrubbed "$top/@factory"
  assert_scrubbed "$top/@"
  [[ $(cat "$top/@factory/read-only") == "true" ]] || fail "baseline returns to read-only"
  [[ -f $top/@/var/lib/omarchy/provisioning/pending && -f $top/rebuilt ]] ||
    fail "reset reaches provisioning after cleanup"

  bash "$test_tmp/reset" "$test_tmp" "$top" || fail "$scenario reset can be repeated"
  assert_scrubbed "$top/@factory"
  assert_scrubbed "$top/@"
  pass "$scenario reset scrubs both roots, preserves service accounts, and can be repeated"
done

for target in @omarchy-reset-next; do
  for command in userdel usermod rm; do
    top="$test_tmp/fail-$target-$command"
    make_fixture "$top"
    if FAIL_COMMAND="$command" FAIL_ROOT="$top/$target" bash "$test_tmp/reset" "$test_tmp" "$top"; then
      fail "reset accepted failed $command in $target"
    fi
    [[ -f $top/@/old-system && ! -e $top/rebuilt ]] ||
      fail "failed cleanup must not activate or rebuild the reset system"
    [[ $(cat "$top/@factory/read-only") == "true" ]] ||
      fail "failed cleanup must leave the baseline read-only"
    grep -q original-root-hash "$top/@factory/etc/shadow" ||
      fail "failed staging must leave the original baseline untouched"
    pass "failed $command in $target aborts reset before activation"
  done
done
