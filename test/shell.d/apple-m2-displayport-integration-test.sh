#!/bin/bash

set -euo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

integration="$ROOT/dev/apple-dp-altmode/m2-j413/integration.sh"
prepare="$ROOT/dev/apple-dp-altmode/m2-j413/prepare-bundle.sh"
hook_template="$ROOT/dev/apple-dp-altmode/m2-j413/05-omarchy-m2-displayport-guard.hook"
[[ -f $integration ]] || fail "M2 DisplayPort integration exists"
[[ -f $prepare ]] || fail "M2 DisplayPort bundle preparation exists"
[[ -f $hook_template ]] || fail "M2 DisplayPort package guard exists"
source "$integration"
source "$prepare"

test_root=$(mktemp -d /tmp/omarchy-m2dp-integration-test.XXXXXXXXXX)
trap '[[ $test_root == /tmp/omarchy-m2dp-integration-test.* ]] && rm -rf -- "$test_root"' EXIT
umask 077

expected_module_sha=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
expected_build_id=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb

stage_files_from() {
  local rollback_source="$1"
  local rollback_sha rollback_size
  shift
  rollback_sha=$(sha256sum "$rollback_source")
  rollback_sha=${rollback_sha%% *}
  rollback_size=$(stat -c '%s' "$rollback_source")
  m2dp_stage_files "$@" "$rollback_source" "$rollback_sha" "$rollback_size"
}

expect_refusal() {
  local description="$1"
  shift
  if ("$@") >"$test_root/refusal.stdout" 2>"$test_root/refusal.stderr"; then
    fail "$description"
  fi
  pass "$description"
}

hostile_output=$(/usr/bin/env 'BASH_FUNC_printf%%=() { /usr/bin/printf "PWNED\n"; }' \
  /usr/bin/bash "$integration" --help 2>&1 || true)
[[ $hostile_output != *PWNED* && $hostile_output == *'run this command with sudo /usr/bin/bash'* ]] ||
  fail "integration entrypoint retained an exported function"
pass "integration entrypoint re-executes without exported functions"

usage_output=$(m2dp_usage)
[[ $usage_output == *'/var/lib/omarchy/m2-displayport/active/rollback.sh rollback'* ]] ||
  fail "usage does not use the preserved rollback entrypoint"
pass "usage selects the preserved rollback entrypoint"

expect_refusal "sourced environment check rejects an exported function" \
  /usr/bin/env 'BASH_FUNC_hostile%%=() { :; }' /usr/bin/bash -c \
  'source "$1"; m2dp_check_environment' bash "$integration"
pass "environment check detects exported functions after Bash import"

make_root() {
  local root="$1"
  mkdir -p \
    "$root/proc/device-tree/soc/dcp@271c00000" \
    "$root/boot/efi/m1n1" \
    "$root/etc/default" \
    "$root/etc/pacman.d/hooks" \
    "$root/usr/lib/modules/7.1.6-1-1-ARCH/kernel/drivers/usb/typec/tipd" \
    "$root/var/lib/omarchy/m2-displayport"
  printf 'apple,j413\0apple,t8112\0' >"$root/proc/device-tree/compatible"
  printf 'disabled\0' >"$root/proc/device-tree/soc/dcp@271c00000/status"
  printf 'pre-install boot\n' >"$root/boot/efi/m1n1/boot.bin"
  printf 'stock default image\n' >"$root/boot/initramfs-linux-asahi.img"
  printf 'accepted W image\n' >"$root/boot/initramfs-linux-asahi-dpalt.img"
  printf 'stock module\n' >"$root/usr/lib/modules/7.1.6-1-1-ARCH/kernel/drivers/usb/typec/tipd/tps6598x-core.ko"
  printf 'stock grub\n' >"$root/boot/grub.cfg"
}

make_bundle() {
  local bundle="$1"
  mkdir -m 700 "$bundle"
  printf 'candidate boot\n' >"$bundle/candidate-boot.bin"
  printf 'candidate image\n' >"$bundle/candidate-initramfs.img"
  local boot_sha image_sha boot_size image_size
  boot_sha=$(sha256sum "$bundle/candidate-boot.bin")
  boot_sha=${boot_sha%% *}
  image_sha=$(sha256sum "$bundle/candidate-initramfs.img")
  image_sha=${image_sha%% *}
  boot_size=$(stat -c '%s' "$bundle/candidate-boot.bin")
  image_size=$(stat -c '%s' "$bundle/candidate-initramfs.img")
  printf '%s\n' \
    'format=1' \
    'compatible=apple,j413' \
    'soc=apple,t8112' \
    'kernel_release=7.1.6-1-1-ARCH' \
    'kernel_package=linux-asahi 7.1.6.asahi1-1' \
    "boot_sha256=$boot_sha" \
    "boot_size=$boot_size" \
    "image_sha256=$image_sha" \
    "image_size=$image_size" \
    "module_sha256=$expected_module_sha" \
    "module_build_id=$expected_build_id" >"$bundle/bundle.env"
  printf 'PREPARED\n' >"$bundle/PREPARED"
  chmod 0600 "$bundle"/*
  printf '%s\n' "$boot_sha"
}

root="$test_root/root"
bundle="$test_root/bundle"
make_root "$root"
expected_boot_sha=$(make_bundle "$bundle")
expected_image_sha=$(sha256sum "$bundle/candidate-initramfs.img")
expected_image_sha=${expected_image_sha%% *}
expected_image_size=$(stat -c '%s' "$bundle/candidate-initramfs.img")

m2dp_verify_host_tree "$root" '7.1.6-1-1-ARCH' 'linux-asahi 7.1.6.asahi1-1'
pass "exact M2 J413 and kernel host passes"

printf 'apple,j415\0apple,t8112\0' >"$root/proc/device-tree/compatible"
expect_refusal "wrong Apple model is refused" m2dp_verify_host_tree \
  "$root" '7.1.6-1-1-ARCH' 'linux-asahi 7.1.6.asahi1-1'
printf 'apple,j413\0apple,t8112\0' >"$root/proc/device-tree/compatible"
expect_refusal "wrong running kernel is refused" m2dp_verify_host_tree \
  "$root" '7.1.7-1-1-ARCH' 'linux-asahi 7.1.6.asahi1-1'
expect_refusal "wrong kernel package is refused" m2dp_verify_host_tree \
  "$root" '7.1.6-1-1-ARCH' 'linux-asahi 7.1.7.asahi1-1'
pass "model and kernel refusals are exact"

! m2dp_partner_is_external_usb_c /sys/devices/platform/soc/0-003a/typec/port0/port0-partner ||
  fail "MagSafe partner is treated as external USB-C"
m2dp_partner_is_external_usb_c /sys/devices/platform/soc/0-0038/typec/port0/port0-partner ||
  fail "rear USB-C partner is not detected"
m2dp_partner_is_external_usb_c /sys/devices/platform/soc/0-003f/typec/port1/port1-partner ||
  fail "front USB-C partner is not detected"
pass "MagSafe stays allowed while both USB-C controllers are gated"

m2dp_boot_input_supported "$M2DP_STOCK_BOOT_SHA256" || fail "supported stock boot is refused"
m2dp_boot_input_supported "$M2DP_BOOT_SHA256" || fail "accepted candidate boot is refused"
! m2dp_boot_input_supported 0000000000000000000000000000000000000000000000000000000000000000 ||
  fail "unknown boot input is accepted"
pass "live staging accepts only the pinned stock or candidate boot"

m2dp_validate_bundle "$bundle" "$expected_boot_sha" "$expected_image_sha" "$expected_image_size" \
  "$expected_module_sha" "$expected_build_id"
pass "exact bundle manifest and files pass"

cp -a "$bundle" "$test_root/duplicate-bundle"
printf 'format=1\n' >>"$test_root/duplicate-bundle/bundle.env"
expect_refusal "duplicate manifest field is refused" m2dp_validate_bundle \
  "$test_root/duplicate-bundle" "$expected_boot_sha" "$expected_image_sha" "$expected_image_size" \
  "$expected_module_sha" "$expected_build_id"
cp -a "$bundle" "$test_root/unknown-bundle"
printf 'extra=value\n' >>"$test_root/unknown-bundle/bundle.env"
expect_refusal "unknown manifest field is refused" m2dp_validate_bundle \
  "$test_root/unknown-bundle" "$expected_boot_sha" "$expected_image_sha" "$expected_image_size" \
  "$expected_module_sha" "$expected_build_id"
expect_refusal "wrong boot release pin is refused" m2dp_validate_bundle \
  "$bundle" 0000000000000000000000000000000000000000000000000000000000000000 \
  "$expected_image_sha" "$expected_image_size" "$expected_module_sha" "$expected_build_id"
expect_refusal "wrong image release pin is refused" m2dp_validate_bundle \
  "$bundle" "$expected_boot_sha" \
  0000000000000000000000000000000000000000000000000000000000000000 \
  "$expected_image_size" "$expected_module_sha" "$expected_build_id"
rm "$bundle/PREPARED"
expect_refusal "bundle without a prepared receipt is refused" m2dp_validate_bundle \
  "$bundle" "$expected_boot_sha" "$expected_image_sha" "$expected_image_size" \
  "$expected_module_sha" "$expected_build_id"
printf 'PREPARED\n' >"$bundle/PREPARED"
pass "bundle parser fails closed"

default_before=$(sha256sum "$root/boot/initramfs-linux-asahi.img")
w_before=$(sha256sum "$root/boot/initramfs-linux-asahi-dpalt.img")
module_before=$(sha256sum "$root/usr/lib/modules/7.1.6-1-1-ARCH/kernel/drivers/usb/typec/tipd/tps6598x-core.ko")
grub_before=$(sha256sum "$root/boot/grub.cfg")
previous_boot_sha=$(sha256sum "$root/boot/efi/m1n1/boot.bin")
previous_boot_sha=${previous_boot_sha%% *}
reviewed_rollback_source="$test_root/reviewed-integration.sh"
cp "$integration" "$reviewed_rollback_source"
chmod 0600 "$reviewed_rollback_source"
reviewed_rollback_sha=$(sha256sum "$reviewed_rollback_source")
reviewed_rollback_sha=${reviewed_rollback_sha%% *}
reviewed_rollback_size=$(stat -c '%s' "$reviewed_rollback_source")

bad_hook="$test_root/changed-package-guard.hook"
cp "$hook_template" "$bad_hook"
printf '\n' >>"$bad_hook"
expect_refusal "changed package guard is refused before staging" stage_files_from "$reviewed_rollback_source" \
  "$root" "$bundle" 20260901T225900Z "$EUID" \
  "$expected_boot_sha" "$expected_image_sha" "$expected_image_size" \
  "$expected_module_sha" "$expected_build_id" "$bad_hook" "$previous_boot_sha"
[[ ! -e $root/boot/initramfs-linux-asahi-m2-displayport.img ]] || fail "changed guard staged an image"
pass "package guard is pinned to exact reviewed bytes"

expect_refusal "changed active boot after release gate is refused" stage_files_from "$reviewed_rollback_source" \
  "$root" "$bundle" 20260901T225901Z "$EUID" \
  "$expected_boot_sha" "$expected_image_sha" "$expected_image_size" \
  "$expected_module_sha" "$expected_build_id" "$hook_template" \
  0000000000000000000000000000000000000000000000000000000000000000
[[ ! -e $root/boot/initramfs-linux-asahi-m2-displayport.img ]] || fail "changed boot staged an image"
pass "active boot is rechecked inside the staging transaction"

stage_files_from "$reviewed_rollback_source" "$root" "$bundle" 20260901T230000Z "$EUID" \
  "$expected_boot_sha" "$expected_image_sha" "$expected_image_size" \
  "$expected_module_sha" "$expected_build_id" "$hook_template" "$previous_boot_sha"

grep -Fxq 'pre-install boot' "$root/boot/efi/m1n1/boot.bin" || fail "preparation changed active boot"
cmp -s "$bundle/candidate-initramfs.img" "$root/boot/initramfs-linux-asahi-m2-displayport.img" ||
  fail "candidate image is staged"
grep -Fxq 'PREPARED' "$root/var/lib/omarchy/m2-displayport/active/RESULT" || fail "prepared phase is not published"
grep -Fxq "previous_boot_sha256=$previous_boot_sha" \
  "$root/var/lib/omarchy/m2-displayport/active/state.env" || fail "rollback manifest pins previous boot"
grep -Fxq 'active_boot_changed=1' \
  "$root/var/lib/omarchy/m2-displayport/active/state.env" || fail "changed boot is recorded"
rollback_entrypoint="$root/var/lib/omarchy/m2-displayport/active/rollback.sh"
cmp -s "$reviewed_rollback_source" "$rollback_entrypoint" || fail "reviewed rollback entrypoint is not preserved"
grep -Fxq "rollback_sha256=$reviewed_rollback_sha" \
  "$root/var/lib/omarchy/m2-displayport/active/state.env" || fail "rollback manifest does not bind entrypoint checksum"
grep -Fxq "rollback_size=$reviewed_rollback_size" \
  "$root/var/lib/omarchy/m2-displayport/active/state.env" || fail "rollback manifest does not bind entrypoint size"
[[ $(stat -c '%u %a' "$rollback_entrypoint") == "$EUID 700" ]] || fail "rollback entrypoint ownership or mode is unsafe"
grep -Fxq 'sudo /usr/bin/bash /var/lib/omarchy/m2-displayport/active/rollback.sh rollback' \
  "$root/var/lib/omarchy/m2-displayport/active/recovery.txt" || fail "recovery guide does not use preserved rollback entrypoint"
pass "preparation preserves and binds a root-owned rollback entrypoint"
cmp -s "$root/boot/efi/m1n1/boot.bin.pre-omarchy-m2-displayport-20260901T230000Z" \
  "$root/var/lib/omarchy/m2-displayport/active/pre-install-boot.bin" || fail "both rollback backups match"
[[ $(sha256sum "$root/boot/initramfs-linux-asahi.img") == "$default_before" ]] || fail "default image changed"
[[ $(sha256sum "$root/boot/initramfs-linux-asahi-dpalt.img") == "$w_before" ]] || fail "W changed"
[[ $(sha256sum "$root/usr/lib/modules/7.1.6-1-1-ARCH/kernel/drivers/usb/typec/tipd/tps6598x-core.ko") == "$module_before" ]] ||
  fail "stock module changed"
[[ $(sha256sum "$root/boot/grub.cfg") == "$grub_before" ]] || fail "GRUB changed"
pass "preparation preserves active boot, default image, W, stock module, and GRUB"

stage_boot_tmp="$root/boot/efi/m1n1/.boot.bin.omarchy-m2-displayport-20260901T230000Z.tmp"
cp "$root/var/lib/omarchy/m2-displayport/active/candidate-boot.bin" "$stage_boot_tmp"
m2dp_activate_files "$root" "$EUID"
cmp -s "$bundle/candidate-boot.bin" "$root/boot/efi/m1n1/boot.bin" || fail "candidate boot is not active"
grep -Fxq 'STAGED' "$root/var/lib/omarchy/m2-displayport/active/RESULT" || fail "staged phase is not published"
[[ ! -e $stage_boot_tmp ]] || fail "activation retained a staged boot temporary"
pass "activation recovers a prepared boot temporary and publishes the staged phase"

expect_refusal "second staging refuses every existing output" stage_files_from "$reviewed_rollback_source" \
  "$root" "$bundle" 20260901T230001Z "$EUID" \
  "$expected_boot_sha" "$expected_image_sha" "$expected_image_size" \
  "$expected_module_sha" "$expected_build_id" "$hook_template" "$expected_boot_sha"
pass "staging never overwrites an installed candidate"

printf '\n' >>"$reviewed_rollback_source"
[[ $(sha256sum "$rollback_entrypoint") == "$reviewed_rollback_sha  $rollback_entrypoint" ]] ||
  fail "changed source checkout altered preserved rollback entrypoint"
rm "$reviewed_rollback_source"
/usr/bin/bash -c 'source "$1"; m2dp_rollback_files "$2" "$3"' bash \
  "$rollback_entrypoint" "$root" "$EUID"
grep -Fxq 'pre-install boot' "$root/boot/efi/m1n1/boot.bin" || fail "rollback restores previous boot"
[[ ! -e $root/boot/initramfs-linux-asahi-m2-displayport.img ]] || fail "rollback removes candidate image"
[[ ! -e $root/etc/pacman.d/hooks/05-omarchy-m2-displayport-guard.hook ]] || fail "rollback removes package guard"
[[ ! -e $root/var/lib/omarchy/m2-displayport/active ]] || fail "active state remains after rollback"
[[ -f $root/var/lib/omarchy/m2-displayport/rolled-back-20260901T230000Z/state.env ]] ||
  fail "rollback evidence is retained"
[[ -f $root/boot/efi/m1n1/boot.bin.pre-omarchy-m2-displayport-20260901T230000Z ]] ||
  fail "EFI recovery backup is retained"
[[ $(sha256sum "$root/boot/initramfs-linux-asahi.img") == "$default_before" ]] || fail "default image changed during rollback"
[[ $(sha256sum "$root/boot/initramfs-linux-asahi-dpalt.img") == "$w_before" ]] || fail "W changed during rollback"
[[ -f $root/var/lib/omarchy/m2-displayport/rolled-back-20260901T230000Z/rollback.sh ]] ||
  fail "rollback evidence does not retain its entrypoint"
pass "root-owned rollback survives a changed and absent source checkout"
pass "rollback restores exact pre-install boot and retains recovery evidence"

drift_root="$test_root/drift-root"
drift_bundle="$test_root/drift-bundle"
make_root "$drift_root"
drift_boot_sha=$(make_bundle "$drift_bundle")
stage_files_from "$integration" "$drift_root" "$drift_bundle" 20260901T230100Z "$EUID" \
  "$drift_boot_sha" "$expected_image_sha" "$expected_image_size" \
  "$expected_module_sha" "$expected_build_id" "$hook_template" "$previous_boot_sha"
printf 'drift\n' >>"$drift_root/etc/pacman.d/hooks/05-omarchy-m2-displayport-guard.hook"
active_before=$(sha256sum "$drift_root/boot/efi/m1n1/boot.bin")
expect_refusal "changed package guard blocks rollback before mutation" m2dp_rollback_files "$drift_root" "$EUID"
[[ $(sha256sum "$drift_root/boot/efi/m1n1/boot.bin") == "$active_before" ]] || fail "failed rollback changed boot"
[[ -f $drift_root/boot/initramfs-linux-asahi-m2-displayport.img ]] || fail "failed rollback removed image"
pass "package-hook drift fails closed"

rollback_drift_root="$test_root/rollback-drift-root"
rollback_drift_bundle="$test_root/rollback-drift-bundle"
make_root "$rollback_drift_root"
rollback_drift_boot_sha=$(make_bundle "$rollback_drift_bundle")
stage_files_from "$integration" "$rollback_drift_root" "$rollback_drift_bundle" 20260901T230150Z "$EUID" \
  "$rollback_drift_boot_sha" "$expected_image_sha" "$expected_image_size" \
  "$expected_module_sha" "$expected_build_id" "$hook_template" "$previous_boot_sha"
rollback_drift_entrypoint="$rollback_drift_root/var/lib/omarchy/m2-displayport/active/rollback.sh"
rollback_drift_sha=$(sha256sum "$rollback_drift_entrypoint")
rollback_drift_sha=${rollback_drift_sha%% *}
rollback_drift_size=$(stat -c '%s' "$rollback_drift_entrypoint")
rollback_drift_boot_before=$(sha256sum "$rollback_drift_root/boot/efi/m1n1/boot.bin")
chmod 0744 "$rollback_drift_entrypoint"
expect_refusal "unsafe rollback entrypoint mode blocks rollback before mutation" \
  m2dp_rollback_files "$rollback_drift_root" "$EUID"
[[ $(sha256sum "$rollback_drift_root/boot/efi/m1n1/boot.bin") == "$rollback_drift_boot_before" ]] ||
  fail "unsafe rollback entrypoint mode changed boot"
chmod 0700 "$rollback_drift_entrypoint"
expect_refusal "wrong rollback entrypoint owner is refused" m2dp_verify_owned_file \
  "$rollback_drift_entrypoint" "$rollback_drift_sha" "$rollback_drift_size" "$(( EUID + 1 ))" 700
printf '\n' >>"$rollback_drift_entrypoint"
expect_refusal "changed rollback entrypoint blocks rollback before mutation" \
  m2dp_rollback_files "$rollback_drift_root" "$EUID"
[[ $(sha256sum "$rollback_drift_root/boot/efi/m1n1/boot.bin") == "$rollback_drift_boot_before" ]] ||
  fail "changed rollback entrypoint changed boot"
[[ -f $rollback_drift_root/boot/initramfs-linux-asahi-m2-displayport.img ]] ||
  fail "changed rollback entrypoint removed image"
pass "rollback entrypoint integrity, ownership, and mode fail closed"

same_root="$test_root/same-root"
same_bundle="$test_root/same-bundle"
make_root "$same_root"
same_boot_sha=$(make_bundle "$same_bundle")
cp "$same_bundle/candidate-boot.bin" "$same_root/boot/efi/m1n1/boot.bin"
stage_files_from "$integration" "$same_root" "$same_bundle" 20260901T230200Z "$EUID" \
  "$same_boot_sha" "$expected_image_sha" "$expected_image_size" \
  "$expected_module_sha" "$expected_build_id" "$hook_template" "$same_boot_sha"
grep -Fxq 'active_boot_changed=0' \
  "$same_root/var/lib/omarchy/m2-displayport/active/state.env" || fail "already active candidate is recorded"
m2dp_rollback_files "$same_root" "$EUID"
cmp -s "$same_bundle/candidate-boot.bin" "$same_root/boot/efi/m1n1/boot.bin" ||
  fail "rollback preserves identical pre-install boot"
pass "already active candidate stages and rolls back without replacing boot"

missing_hook_root="$test_root/missing-hook-root"
missing_hook_bundle="$test_root/missing-hook-bundle"
make_root "$missing_hook_root"
rmdir "$missing_hook_root/etc/pacman.d/hooks"
missing_hook_boot_sha=$(make_bundle "$missing_hook_bundle")
stage_files_from "$integration" "$missing_hook_root" "$missing_hook_bundle" 20260901T230300Z "$EUID" \
  "$missing_hook_boot_sha" "$expected_image_sha" "$expected_image_size" \
  "$expected_module_sha" "$expected_build_id" "$hook_template" "$previous_boot_sha"
grep -Fxq 'hook_parent_created=1' \
  "$missing_hook_root/var/lib/omarchy/m2-displayport/active/state.env" || fail "new hook directory is recorded"
m2dp_rollback_files "$missing_hook_root" "$EUID"
[[ ! -e $missing_hook_root/etc/pacman.d/hooks ]] || fail "rollback retained the newly created hook directory"
pass "missing pacman hook directory is created and rolled back"

grep -Fxq 'Target = linux-asahi' "$hook_template" || fail "kernel package is guarded"
grep -Fxq 'Target = m1n1' "$hook_template" || fail "m1n1 package is guarded"
grep -Fxq 'Target = uboot-asahi' "$hook_template" || fail "U-Boot package is guarded"
grep -Fxq 'When = PreTransaction' "$hook_template" || fail "guard runs before transaction"
grep -Fxq 'AbortOnFail' "$hook_template" || fail "guard aborts the package transaction"
grep -Fxq 'Exec = /usr/bin/false' "$hook_template" || fail "guard does not fail closed"
bash -n "$integration" || fail "integration script has valid Bash syntax"
bash -n "$prepare" || fail "bundle preparation script has valid Bash syntax"
pass "package guard covers boot-chain drift"

mkdir "$test_root/existing-prepared-bundle"
expect_refusal "existing preparation output is refused" m2dp_prepare_output_path "$test_root/existing-prepared-bundle"
expect_refusal "protected preparation output is refused" m2dp_prepare_output_path /boot/m2-displayport
pass "bundle preparation protects existing and system paths"

marker_bundle="$test_root/marker-bundle"
mkdir "$marker_bundle"
printf 'INCOMPLETE\n' >"$marker_bundle/INCOMPLETE"
m2dp_mark_prepared "$marker_bundle"
grep -Fxq 'PREPARED' "$marker_bundle/PREPARED" || fail "prepared marker content is wrong"
[[ ! -e $marker_bundle/INCOMPLETE ]] || fail "incomplete marker remains after preparation"
pass "bundle preparation publishes an unambiguous readiness marker"

entrypoint_output="$test_root/entrypoint-bundle"
expect_refusal "prepare entrypoint rejects an unpinned artifact before output" \
  bash "$prepare" --boot "$bundle/candidate-boot.bin" \
  --image "$bundle/candidate-initramfs.img" --output "$entrypoint_output"
[[ ! -e $entrypoint_output ]] || fail "rejected prepare entrypoint created output"
pass "prepare entrypoint applies release pins before archive processing"

hostile_prepare_output=$(/usr/bin/env 'BASH_FUNC_printf%%=() { /usr/bin/printf "PWNED\n"; }' \
  /usr/bin/bash "$prepare" --help 2>&1 || true)
[[ $hostile_prepare_output != *PWNED* && $hostile_prepare_output == *'Usage: /usr/bin/bash'* ]] ||
  fail "prepare entrypoint retained an exported function"
pass "prepare entrypoint re-executes without exported functions"

copy_source="$test_root/copy-source"
copy_destination="$test_root/copy-destination"
printf 'transactional copy\n' >"$copy_source"
copy_sha=$(sha256sum "$copy_source")
copy_sha=${copy_sha%% *}
copy_size=$(stat -c '%s' "$copy_source")
expect_refusal "failed transactional copy publishes no destination" m2dp_copy_new \
  "$copy_source" "$copy_destination" "$copy_sha" "$copy_size" invalid-mode
[[ ! -e $copy_destination ]] || fail "failed transactional copy left a destination"
if compgen -G "$test_root/.copy-destination.m2dp-copy.*" >/dev/null; then
  fail "failed transactional copy left a temporary"
fi
pass "transactional copy cleans failed temporary and destination files"

lock_parent="$test_root/operation-lock"
nested_lock_refuses() {
  ! m2dp_with_operation_lock "$lock_parent" "$EUID" true
}
m2dp_with_operation_lock "$lock_parent" "$EUID" nested_lock_refuses || fail "operation lock allowed a concurrent action"
pass "operation lock serializes stage and rollback"

failure_marker="$test_root/lock-failure-fell-through"
expect_refusal "operation wrapper propagates action failure" bash -c '
    set -e
    source "$1"
    locked_action_fails() {
      false
      printf "unsafe\n" >"$2"
    }
    m2dp_with_operation_lock "$3" "$4" locked_action_fails
  ' bash "$integration" "$failure_marker" "$lock_parent-child" "$EUID"
[[ ! -e $failure_marker ]] || fail "operation wrapper disabled action errexit"
pass "operation wrapper preserves action failure semantics"

printf 'VERDICT: PASS\n'
