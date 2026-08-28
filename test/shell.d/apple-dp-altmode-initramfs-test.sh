#!/bin/bash

set -euo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"
helper="$ROOT/dev/apple-dp-altmode/prepare-one-boot-initramfs.sh"
config="$ROOT/dev/apple-dp-altmode/one-boot-mkinitcpio.conf"
[[ -f $helper ]] || fail "the offline one-boot preparation helper exists"
source "$helper"

test_tmp=$(mktemp -d /tmp/dev147-initramfs-test.XXXXXXXXXX)
trap '[[ $test_tmp == /tmp/dev147-initramfs-test.* ]] && rm -rf -- "$test_tmp"' EXIT
umask 077

expect_refusal() {
  local description="$1"
  shift
  if ( "$@" ) >"$test_tmp/refusal.log" 2>&1; then
    fail "$description"
  fi
  pass "$description"
}

dpalt_require_user 1000
expect_refusal "root is refused before any preparation" dpalt_require_user 0
for override in BASH_ENV ENV MKINITCPIO_CONF MKINITCPIO_INSTALL MKINITCPIO_POST_HOOKS OMARCHY_DPALT_TEST_ROOT; do
  if ( export "$override=unexpected"; dpalt_check_environment ) >"$test_tmp/refusal.log" 2>&1; then
    fail "environment override is refused: $override"
  fi
done
pass "configuration, hook, shell, and old test bypass overrides are refused"

[[ $(dpalt_new_output "$test_tmp/new output") == "$test_tmp/new output" ]] ||
  fail "pure output validation preserves a new canonical path with spaces"
for path in / /boot/dev147 /etc/dev147 /usr/dev147 /var/dev147 /run/dev147 /proc/dev147 /sys/dev147 /dev/dev147 /home/david/o-live/dev147 /home/david/o/.dev147-stage/artifacts/new /home/david/o/.dev147-stage/prototype/new; do
  expect_refusal "protected output is refused: $path" dpalt_new_output "$path"
done
expect_refusal "relative outputs are refused" dpalt_new_output relative
expect_refusal "dot-dot outputs are refused" dpalt_new_output "$test_tmp/../new"
expect_refusal "newline outputs are refused" dpalt_new_output "$test_tmp/line"$'\n'"break"
mkdir "$test_tmp/existing" "$test_tmp/parent"
ln -s "$test_tmp/parent" "$test_tmp/link"
expect_refusal "existing empty directories are not reused" dpalt_new_output "$test_tmp/existing"
expect_refusal "symlink ancestors are refused" dpalt_new_output "$test_tmp/link/new"
expect_refusal "a missing parent is refused" dpalt_new_output "$test_tmp/missing/new"
if [[ $(findmnt -n -o FSTYPE -T "$test_tmp") == "tmpfs" ]]; then
  expect_refusal "production rejects tmpfs without any test bypass" dpalt_persistent_output "$test_tmp/new"
fi

source_tree="$test_tmp/source"
private_tree="$test_tmp/private"
mkdir -p "$source_tree/$(dirname -- "$DPALT_CORE_REL")" "$source_tree/kernel/other"
printf 'stock core\n' >"$source_tree/$DPALT_CORE_REL"
printf 'untouched module\n' >"$source_tree/kernel/other/keep.ko"
printf 'kernel/builtin.ko\n' >"$source_tree/modules.builtin"
printf 'old dependency index\n' >"$source_tree/modules.dep"
before=$(dpalt_tree_manifest "$source_tree")
dpalt_copy_tree "$source_tree" "$private_tree"
[[ ! $source_tree/$DPALT_CORE_REL -ef $private_tree/$DPALT_CORE_REL ]] ||
  fail "private copy uses independent inodes"
[[ $(dpalt_tree_manifest "$private_tree") == "$before" ]] || fail "copy preserves original bytes"
printf 'patched core\n' >"$private_tree/$DPALT_CORE_REL"
printf 'new dependency index\n' >"$private_tree/modules.dep"
dpalt_check_tree_delta "$source_tree" "$private_tree"
[[ $(dpalt_tree_manifest "$source_tree") == "$before" ]] || fail "copy changes cannot change the source tree"
pass "independent copy permits only the candidate core and depmod indexes to differ"

printf 'unexpected\n' >"$private_tree/kernel/other/keep.ko"
expect_refusal "unrelated module changes are refused" dpalt_check_tree_delta "$source_tree" "$private_tree"
cp "$source_tree/kernel/other/keep.ko" "$private_tree/kernel/other/keep.ko"
printf 'changed builtin list\n' >"$private_tree/modules.builtin"
expect_refusal "modules.builtin is not treated as a generated index" dpalt_check_tree_delta "$source_tree" "$private_tree"
cp "$source_tree/modules.builtin" "$private_tree/modules.builtin"
printf 'extra\n' >"$private_tree/extra"
expect_refusal "extra files are refused" dpalt_check_tree_delta "$source_tree" "$private_tree"
rm -- "$private_tree/extra"
ln -s "$source_tree/kernel/other/keep.ko" "$private_tree/extra"
expect_refusal "symlinks in a private module tree are refused" dpalt_check_tree_delta "$source_tree" "$private_tree"
rm -- "$private_tree/extra"
ln "$source_tree/kernel/other/keep.ko" "$private_tree/extra"
expect_refusal "hardlinks in a private module tree are refused" dpalt_check_tree_delta "$source_tree" "$private_tree"

digest=$(sha256sum "$source_tree/$DPALT_CORE_REL")
digest=${digest%% *}
dpalt_check_hash "$source_tree/$DPALT_CORE_REL" "$digest"
expect_refusal "hash drift is refused" dpalt_check_hash "$source_tree/$DPALT_CORE_REL" "${digest/a/b}000"
pass "hash validation uses real files and SHA-256"

printf 'init\nusr/lib/modules/\nusr/lib/modules/%s/kernel/driver.ko\nusr/bin/\n' "$DPALT_VERSION" >"$test_tmp/archive.list"
dpalt_check_archive_names "$test_tmp/archive.list"
for member in /etc/escape ../escape usr/../../escape usr/./escape usr/lib/modules/wrong-kernel/driver.ko; do
  printf '%s\n' "$member" >"$test_tmp/archive.list"
  expect_refusal "archive path escape is refused: $member" dpalt_check_archive_names "$test_tmp/archive.list"
done
printf 'usr/lib/modules/%s/%s\n' "$DPALT_VERSION" "$DPALT_CORE_REL" "$DPALT_VERSION" "$DPALT_CORE_REL" >"$test_tmp/archive.list"
expect_refusal "duplicate candidate core archive entries are refused" dpalt_check_archive_names "$test_tmp/archive.list"

[[ -f $config ]] || fail "the reviewed flattened configuration exists"
(
  source "$config"
  [[ ${MODULES[*]} == "hid_apple hid_magicmouse" ]] || fail "only the existing HID modules are preloaded"
  [[ ${#BINARIES[@]} == 0 && ${FILES[*]} == "/etc/vconsole.conf" ]] || fail "no extra files or keyfiles are configured"
  [[ ${HOOKS[*]} == "base asahi udev plymouth keyboard autodetect microcode modconf kms keymap consolefont block encrypt filesystems fsck" ]] ||
    fail "all effective stock hooks remain in their reviewed order"
  [[ $COMPRESSION == "gzip" && $MODULES_DECOMPRESS == "no" && ${#COMPRESSION_OPTIONS[@]} == 0 ]] ||
    fail "compression matches installed defaults"
)
pass "literal configuration preserves the effective stock drop-ins without extra Type-C preload"

expected_early=(appledrm phy-apple-atc tps6598x tps6598x-core typec hid-apple hid-magicmouse
  nvme-apple apple-mailbox apple-dart i2c-pasemi-platform spi-apple spi-hid-apple spi-hid-apple-of
  ext4 drm drm_dma_helper dm-crypt dm-integrity)
[[ $(dpalt_required_early_modules) == $(printf '%s\n' "${expected_early[@]}") ]] ||
  fail "required early modules match stock-hook selection, without DPTX or crossbar preloading"
pass "early archive requirements do not force modules absent from stock-hook selection"

dpalt_build_command "$test_tmp/output with spaces"
expected=(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C.UTF-8 /usr/bin/mkinitcpio
  --config "$test_tmp/output with spaces/mkinitcpio.conf" --hookdir /usr/lib/initcpio --nopost
  --kernel "$DPALT_VERSION" --moduleroot "$test_tmp/output with spaces/module-root"
  --builddir "$test_tmp/output with spaces/tmp" --save --generate "$test_tmp/output with spaces/initramfs-linux-asahi-dpalt.img")
[[ ${#DPALT_BUILD[@]} == ${#expected[@]} ]] || fail "build command has no extra arguments"
for index in "${!expected[@]}"; do
  [[ ${DPALT_BUILD[index]} == "${expected[index]}" ]] || fail "build argument is exact: $index"
done
pass "build command isolates config, module root, temporary tree, output, environment, and post-hooks"

reader="$ROOT/dev/apple-dp-altmode/read-protected-stock.sh"
[[ -f $reader ]] || fail "the protected-stock readback helper exists"
source "$reader"
printf 'fixture archive bytes\n' >"$test_tmp/dd-source"
dpalt_write_private_image "$test_tmp/dd-copy" <"$test_tmp/dd-source" ||
  fail "production stdin writer accepts the installed dd options"
cmp -s "$test_tmp/dd-source" "$test_tmp/dd-copy" || fail "stdin writer preserves copied bytes"
[[ $(stat -c '%a' "$test_tmp/dd-copy") == 600 ]] || fail "stdin writer keeps the copy private"
dd_before=$(sha256sum "$test_tmp/dd-copy")
expect_refusal "stdin writer refuses an existing destination" dpalt_write_private_image "$test_tmp/dd-copy" <"$test_tmp/dd-source"
[[ $(sha256sum "$test_tmp/dd-copy") == "$dd_before" ]] || fail "refused copy preserves the existing hash"
ln -s "$test_tmp/dd-copy" "$test_tmp/dd-link"
expect_refusal "stdin writer refuses a symlink destination" dpalt_write_private_image "$test_tmp/dd-link" <"$test_tmp/dd-source"
[[ -L $test_tmp/dd-link && $(sha256sum "$test_tmp/dd-copy") == "$dd_before" ]] || fail "refused copy preserves the symlink target"
pass "real stdin writer uses exclusive creation, preserves bytes, and never overwrites destinations"
[[ $(dpalt_readback_manifest | wc -l) == 2 ]] || fail "readback verifies exactly the two fixed protected files"
[[ $(dpalt_readback_manifest) != *boot.bin* ]] || fail "readback does not compare the intentionally changed DTB boot file"
printf '%s\n' "menuentry 'test' {" 'linux /boot/vmlinuz root=PRIVATE cryptkey=PRIVATE' \
  'initrd /boot/initramfs-linux-asahi.img' 'password_pbkdf2 user PRIVATE' >"$test_tmp/grub.fixture"
filtered=$(awk "$(dpalt_grub_filter)" "$test_tmp/grub.fixture")
[[ $filtered == *'2:linux /boot/vmlinuz [arguments omitted]'* && $filtered == *'3:initrd /boot/initramfs-linux-asahi.img'* ]] ||
  fail "GRUB readback retains image paths and omits kernel arguments"
[[ $filtered != *PRIVATE* && $filtered != *password_pbkdf2* ]] || fail "unneeded sensitive GRUB fields are omitted"
[[ $(rg -c 'dpalt_clean /usr/bin/sudo /usr/bin/(sha256sum|cat|awk)' "$reader") == 3 ]] ||
  fail "readback contains only its three fixed privileged readers"
! rg -n 'sudo.*(dd|cp |install|tee|mv |rm |bash)' "$reader" || fail "no readback destination is written as root"
pass "readback uses fixed sources and a real tested filter; no sudo was invoked by tests"

! rg -n '^[[:space:]]*(sudo|modprobe|insmod|rmmod|update-m1n1|grub-mkconfig|kernel-install)([[:space:]]|$)' "$helper" ||
  fail "offline preparation does not invoke activation or privileged commands"
! rg -n 'OMARCHY_DPALT_TEST_ALLOW_TMPFS|TEST_ROOT:-|--preset|--allpresets|--uki' "$helper" ||
  fail "production helper has no test-root, tmpfs, preset, or UKI bypass"
for syntax_file in "$helper" "$config" "$reader"; do
  bash -n "$syntax_file" || fail "valid syntax: $syntax_file"
done
pass "offline preparation exposes no persistent activation path"
printf 'VERDICT: PASS\n'
