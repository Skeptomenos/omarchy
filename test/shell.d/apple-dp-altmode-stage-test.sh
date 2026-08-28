#!/bin/bash

set -euo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"
helper="$ROOT/dev/apple-dp-altmode/stage-one-boot-initramfs.sh"
[[ -f $helper ]] || fail "the staging-only helper exists"
source "$helper"

(( EUID != 0 )) || fail "staging tests must run unprivileged"
stage_test_tmp=$(mktemp -d /tmp/dev147-stage-test.XXXXXXXXXX)
trap '[[ $stage_test_tmp == /tmp/dev147-stage-test.* ]] && rm -rf -- "$stage_test_tmp"' EXIT
umask 077

expect_refusal() {
  local description="$1"
  shift
  if ( "$@" ) >"$stage_test_tmp/refusal.log" 2>&1; then
    fail "$description"
  fi
  pass "$description"
}

expect_refusal "nonroot production entrypoint refuses before staging" /bin/bash "$helper"
grep -Fq 'root' "$stage_test_tmp/refusal.log" || fail "production refusal identifies the privilege boundary"
dpstage_secure_directory "$stage_test_tmp" "$EUID"
expect_refusal "relative directory is refused" dpstage_secure_directory . "$EUID"
expect_refusal "dot-dot directory is refused" dpstage_secure_directory "$stage_test_tmp/../" "$EUID"
mkdir "$stage_test_tmp/real-parent"
ln -s "$stage_test_tmp/real-parent" "$stage_test_tmp/linked-parent"
expect_refusal "symlink directory is refused" dpstage_secure_directory "$stage_test_tmp/linked-parent" "$EUID"
chmod 0777 "$stage_test_tmp/real-parent"
expect_refusal "group/world-writable directory is refused" dpstage_secure_directory "$stage_test_tmp/real-parent" "$EUID"
chmod 0700 "$stage_test_tmp/real-parent"
expect_refusal "wrong directory owner is refused" dpstage_secure_directory "$stage_test_tmp" 0

printf 'candidate fixture bytes\n' >"$stage_test_tmp/source.img"
source_hash=$(sha256sum "$stage_test_tmp/source.img")
source_hash=${source_hash%% *}
source_size=$(stat -c '%s' "$stage_test_tmp/source.img")
source_before=$(sha256sum "$stage_test_tmp/source.img")
mkdir "$stage_test_tmp/private" "$stage_test_tmp/boot"
dpstage_copy_verified "$stage_test_tmp/source.img" "$stage_test_tmp/private/image.img" "$source_hash" "$source_size"
[[ $(stat -c '%a' "$stage_test_tmp/private/image.img") == 600 ]] || fail "copied image is mode 0600"
[[ $(sha256sum "$stage_test_tmp/source.img") == "$source_before" ]] || fail "copy leaves source intact"
dpstage_publish_verified "$stage_test_tmp/private/image.img" "$stage_test_tmp/boot/image.img" "$source_hash" "$source_size"
cmp -s "$stage_test_tmp/source.img" "$stage_test_tmp/boot/image.img" || fail "published bytes match source"
[[ $(stat -c '%a' "$stage_test_tmp/boot/image.img") == 600 ]] || fail "published image remains mode 0600"
[[ ! -e $stage_test_tmp/private/image.img ]] || fail "publication is a rename, not an extra copy"
pass "real dd/mv/stat/sync preserve source, published bytes, and private mode"

expect_refusal "wrong hash refuses before copy/publication" dpstage_copy_verified \
  "$stage_test_tmp/source.img" "$stage_test_tmp/private/wrong.img" \
  0000000000000000000000000000000000000000000000000000000000000000 "$source_size"
[[ ! -e $stage_test_tmp/private/wrong.img ]] || fail "wrong-hash refusal leaves no new copy"
expect_refusal "wrong size refuses before copy/publication" dpstage_copy_verified \
  "$stage_test_tmp/source.img" "$stage_test_tmp/private/wrong-size.img" "$source_hash" 1
ln -s "$stage_test_tmp/source.img" "$stage_test_tmp/source-link.img"
expect_refusal "symlink source is refused" dpstage_copy_verified \
  "$stage_test_tmp/source-link.img" "$stage_test_tmp/private/from-link.img" "$source_hash" "$source_size"
cp "$stage_test_tmp/source.img" "$stage_test_tmp/real-parent/source.img"
expect_refusal "symlink source ancestor is refused" dpstage_copy_verified \
  "$stage_test_tmp/linked-parent/source.img" "$stage_test_tmp/private/from-parent-link.img" "$source_hash" "$source_size"
expect_refusal "noncanonical destination parent is refused" dpstage_copy_verified \
  "$stage_test_tmp/source.img" "$stage_test_tmp/linked-parent/new.img" "$source_hash" "$source_size"

printf 'existing protected target\n' >"$stage_test_tmp/protected-target"
protected_hash=$(sha256sum "$stage_test_tmp/protected-target")
for kind in file symlink directory; do
  pending="$stage_test_tmp/private/pending-$kind.img"
  destination="$stage_test_tmp/boot/race-$kind.img"
  dpstage_absent_destination "$destination"
  dpstage_copy_verified "$stage_test_tmp/source.img" "$pending" "$source_hash" "$source_size"
  # The destination appears after the initial absence check, before real mv.
  case "$kind" in
    file) printf 'existing final file\n' >"$destination"; original=$(sha256sum "$destination") ;;
    symlink) ln -s "$stage_test_tmp/protected-target" "$destination" ;;
    directory) mkdir "$destination" ;;
  esac
  expect_refusal "existing $kind fails initial destination guard" dpstage_absent_destination "$destination"
  expect_refusal "real publication refuses racing $kind destination" dpstage_publish_verified \
    "$pending" "$destination" "$source_hash" "$source_size"
  dpstage_verified_file "$pending" "$source_hash" "$source_size"
  case "$kind" in
    file) [[ $(sha256sum "$destination") == "$original" ]] || fail "existing final file changed" ;;
    symlink) [[ -L $destination && $(sha256sum "$stage_test_tmp/protected-target") == "$protected_hash" ]] ||
      fail "existing symlink or target changed" ;;
    directory) [[ -d $destination && -z $(find "$destination" -mindepth 1 -print -quit) ]] ||
      fail "publication wrote inside an existing directory" ;;
  esac
done
ln -s "$stage_test_tmp/missing" "$stage_test_tmp/boot/broken-link.img"
expect_refusal "broken destination symlink is refused" dpstage_absent_destination "$stage_test_tmp/boot/broken-link.img"
[[ $(sha256sum "$stage_test_tmp/source.img") == "$source_before" ]] || fail "source changed during refusal tests"
pass "racing files, symlinks, and directories are preserved with the private candidate retained"

! rg -n '^[[:space:]]*(source |\\. |sudo |mount |reboot|modprobe|insmod|rmmod|update-m1n1|grub-mkconfig|rm )' "$helper" ||
  fail "standalone staging never sources helpers, cleans up, or changes runtime/boot configuration"
grep -Fq 'count_bytes' "$helper" || fail "production copy is bounded to its pinned byte count"
grep -Fq -- '--no-copy --update=none-fail -T' "$helper" || fail "publication explicitly refuses overwrite and cross-device copying"
grep -Fq 'STAGING ONLY PASS' "$helper" || fail "completion distinguishes staging from boot success"
grep -Fq -- '"$private_directory/INCOMPLETE" "$private_directory/staging-start-marker.txt"' "$helper" ||
  fail "successful staging retains the start marker under its completed name"
bash -n "$helper" || fail "staging helper has valid Bash syntax"
pass "production staging has bounded fixed actions and no activation path"
printf 'VERDICT: PASS\n'
