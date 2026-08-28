#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

command_path="$ROOT/bin/omarchy-dev-dp-altmode"
patch_dir="$ROOT/dev/apple-dp-altmode"
doc_path="$ROOT/docs/apple-silicon-external-display.md"
export OMARCHY_PATH="$ROOT"

[[ -x $command_path ]] || fail "the contained Apple DP-alt-mode prototype command exists"

grep -Fq '# omarchy:group=dev' "$command_path" ||
  fail "the prototype is routed as an Omarchy development command"
grep -Fq '# omarchy:summary=' "$command_path" ||
  fail "the prototype has command metadata"
[[ -f $doc_path ]] && grep -Fq 'experimental work in progress' "$doc_path" ||
  fail "the prototype has a durable experimental status document"
grep -Fq 'docs/apple-silicon-external-display.md' "$ROOT/README.md" ||
  fail "the repository documentation links the prototype status"

[[ -f $patch_dir/t8112-j413-dp-altmode.patch ]] ||
  fail "the prototype carries the pinned J413 device-tree patch"
[[ -f $patch_dir/tipd-cd321x-hpd.patch ]] ||
  fail "the prototype carries the pinned generic CD321x HPD patch"
[[ -f $patch_dir/tps6598x-core.Makefile ]] ||
  fail "the prototype carries a minimal out-of-tree module Makefile"

grep -Fq 'ad272ad5d6742869cdd13320e43f9ed01bd1fb33' "$patch_dir/t8112-j413-dp-altmode.patch" ||
  fail "the J413 patch records its fairydust source commit"
grep -Fq 'mux-index = <2>;' "$patch_dir/t8112-j413-dp-altmode.patch" ||
  fail "the J413 patch selects the M2 display crossbar lane"
! grep -Eq 't8103|j293|mux-index = <0>|ps_atc1_common|apple,always-on|&sio|dpaudio1' "$patch_dir/t8112-j413-dp-altmode.patch" ||
  fail "the first J413 patch excludes M1, suspend, SIO, and audio changes"
grep -Fq 'usb-pd@3f' "$patch_dir/t8112-j413-dp-altmode.patch" ||
  fail "the device-tree patch identifies usb-pd@3f as the DisplayPort connector"
grep -Fq 'usb-pd@38' "$patch_dir/t8112-j413-dp-altmode.patch" ||
  fail "the device-tree patch records that usb-pd@38 must stay unchanged"

grep -Fq '3d28209d04c77904e9909b6ab52046910c585a55' "$patch_dir/tipd-cd321x-hpd.patch" ||
  fail "the HPD patch records the fairydust data-status commit"
grep -Fq '1aab123a6d57feae519268f55119c82e52e4adac' "$patch_dir/tipd-cd321x-hpd.patch" ||
  fail "the HPD patch records the fairydust DRM hotplug commit"
grep -Fq 'drm_connector_oob_hotplug_event' "$patch_dir/tipd-cd321x-hpd.patch" ||
  fail "the HPD patch forwards the controller event to DRM"
grep -Fxq 'obj-m += tps6598x-core.o' "$patch_dir/tps6598x-core.Makefile" ||
  fail "the module build targets only tps6598x-core"
! grep -Eq '(^|[[:space:]])tps6598x\.o|i2c\.o' "$patch_dir/tps6598x-core.Makefile" ||
  fail "the module build does not require the omitted I2C wrapper source"
grep -Fq '23945f8ca60a6db63ef81bbd95ee4cdd9bb63f54cd6b07b001c677f0a15ef07b' "$command_path" ||
  fail "the command pins the measured 64-character minimal DTB checksum"
grep -Fq 'make -f "$header_build/Makefile"' "$command_path" ||
  fail "the module build uses the non-chdir Kbuild interface"
! grep -Fq 'make -C "$header_build"' "$command_path" ||
  fail "the module build cannot rewrite the staged Kbuild Makefile"
grep -Fq 'candidate-added-imports.txt' "$command_path" ||
  fail "the module gate records the exact added import surface"
pass "the prototype pins only the reviewed M2 device-tree and generic HPD changes"

test_tmp=$(mktemp -d)
trap 'rm -rf "$test_tmp"' EXIT

system_root="$test_tmp/system"
mkdir -p \
  "$system_root/proc/device-tree" \
  "$system_root/proc/device-tree/soc/dcp@271c00000" \
  "$system_root/proc/device-tree/soc/i2c@235010000/usb-pd@38/connector" \
  "$system_root/proc/device-tree/soc/i2c@235010000/usb-pd@3f/connector" \
  "$system_root/etc/default" \
  "$system_root/usr/lib/modules/7.1.6-1-1-ARCH/dtbs" \
  "$system_root/usr/lib/modules/7.1.6-1-1-ARCH/kernel/drivers/usb/typec/tipd" \
  "$system_root/usr/lib/asahi-boot" \
  "$system_root/boot/efi/m1n1" \
  "$system_root/boot"
printf 'apple,j413\0apple,t8112\0apple,arm-platform\0' >"$system_root/proc/device-tree/compatible"
printf 'disabled\0' >"$system_root/proc/device-tree/soc/dcp@271c00000/status"
: >"$system_root/usr/lib/modules/7.1.6-1-1-ARCH/dtbs/t8112-j413.dtb"
: >"$system_root/usr/lib/modules/7.1.6-1-1-ARCH/kernel/drivers/usb/typec/tipd/tps6598x-core.ko"
: >"$system_root/usr/lib/asahi-boot/m1n1.bin"
: >"$system_root/usr/lib/asahi-boot/u-boot-nodtb.bin"
: >"$system_root/boot/efi/m1n1/boot.bin"
: >"$system_root/boot/initramfs-linux-asahi.img"

OMARCHY_DPALT_TEST_ROOT="$system_root" \
  OMARCHY_DPALT_TEST_KERNEL_RELEASE="7.1.6-1-1-ARCH" \
  "$command_path" check >/dev/null ||
  fail "the prototype accepts the exact J413 and kernel test fixture"
pass "the host gate accepts only the intended M2 baseline"

printf 'apple,j293\0apple,t8103\0apple,arm-platform\0' >"$system_root/proc/device-tree/compatible"
if OMARCHY_DPALT_TEST_ROOT="$system_root" \
  OMARCHY_DPALT_TEST_KERNEL_RELEASE="7.1.6-1-1-ARCH" \
  "$command_path" check >"$test_tmp/wrong-hardware.out" 2>&1; then
  fail "the prototype refuses M1 hardware"
fi
grep -Fq 'requires apple,j413 and apple,t8112' "$test_tmp/wrong-hardware.out" ||
  fail "the wrong-hardware refusal explains the required board"

printf 'apple,j413\0apple,t8112\0apple,arm-platform\0' >"$system_root/proc/device-tree/compatible"
if OMARCHY_DPALT_TEST_ROOT="$system_root" \
  OMARCHY_DPALT_TEST_KERNEL_RELEASE="7.2.0-1-ARCH" \
  "$command_path" check >"$test_tmp/wrong-kernel.out" 2>&1; then
  fail "the prototype refuses a different running kernel"
fi
grep -Fq 'requires kernel 7.1.6-1-1-ARCH' "$test_tmp/wrong-kernel.out" ||
  fail "the wrong-kernel refusal explains the exact pin"

: >"$system_root/etc/default/update-m1n1"
if OMARCHY_DPALT_TEST_ROOT="$system_root" \
  OMARCHY_DPALT_TEST_KERNEL_RELEASE="7.1.6-1-1-ARCH" \
  "$command_path" check >"$test_tmp/update-m1n1.out" 2>&1; then
  fail "the prototype refuses a persistent update-m1n1 override"
fi
grep -Fq 'update-m1n1 override exists' "$test_tmp/update-m1n1.out" ||
  fail "the update-m1n1 refusal identifies the persistent override"
rm -f "$system_root/etc/default/update-m1n1"
pass "the host gate refuses wrong hardware, kernel drift, and persistent boot overrides"

printf 'okay\0' >"$system_root/proc/device-tree/soc/dcp@271c00000/status"
if OMARCHY_DPALT_TEST_ROOT="$system_root" \
  OMARCHY_DPALT_TEST_KERNEL_RELEASE="7.1.6-1-1-ARCH" \
  "$command_path" check >"$test_tmp/enabled-dcp.out" 2>&1; then
  fail "the prototype refuses to start over an already enabled external DCP"
fi
grep -Fq 'baseline external DCP is not disabled' "$test_tmp/enabled-dcp.out" ||
  fail "the enabled-DCP refusal explains the baseline drift"
printf 'disabled\0' >"$system_root/proc/device-tree/soc/dcp@271c00000/status"

OMARCHY_DPALT_LIBRARY=1 source "$command_path"

for protected_path in / /boot /boot/dpalt /etc/dpalt /usr/lib/dpalt /proc/dpalt /sys/dpalt /dev/dpalt /run/dpalt /home/david/o-live/dpalt; do
  if validate_output_path "$protected_path" >/dev/null 2>&1; then
    fail "the output gate refuses protected path $protected_path"
  fi
done

safe_output="$test_tmp/stage"
if validate_output_path "$safe_output" >"$test_tmp/tmpfs.out" 2>&1; then
  fail "the output gate refuses a reboot-spanning stage on tmpfs"
fi
grep -Fq 'persistent filesystem' "$test_tmp/tmpfs.out" ||
  fail "the tmpfs refusal explains the persistence requirement"
export OMARCHY_DPALT_TEST_ALLOW_TMPFS=1
validated_output=$(validate_output_path "$safe_output") ||
  fail "the output gate accepts an isolated staging path"
[[ $validated_output == "$safe_output" ]] ||
  fail "the output gate returns the canonical staging path" "$validated_output"
pass "the output gate cannot target stock boot, module, config, runtime, or live-tree paths"

stage="$test_tmp/stage with spaces"
mkdir -p "$stage/artifacts" "$stage/evidence"
printf 'candidate boot\n' >"$stage/artifacts/boot.bin.dpalt"
printf 'candidate module\n' >"$stage/artifacts/tps6598x-core.ko"
printf 'candidate initramfs\n' >"$stage/artifacts/initramfs-linux-asahi-dpalt.img"
printf 'stock boot\n' >"$stage/evidence/boot.bin.stock"

write_command_plan "$stage" "20260826T230000Z"

for command_file in README.txt 00-baseline-and-backup.sh 02-activate-dtb.sh 02-rollback-dtb.sh 03-live-module.sh 04-one-boot-initramfs.txt 06-cleanup.txt; do
  [[ -f $stage/commands/$command_file ]] ||
    fail "the prototype writes command plan $command_file"
  [[ ! -x $stage/commands/$command_file ]] ||
    fail "command plan $command_file is deliberately non-executable"
done
for command_file in "$stage"/commands/*.sh; do
  bash -n "$command_file" || fail "generated gate script has valid Bash syntax: $command_file"
done

candidate_boot_sha=$(sha256sum "$stage/artifacts/boot.bin.dpalt" | cut -d' ' -f1)
grep -Fq "$candidate_boot_sha" "$stage/commands/02-activate-dtb.sh" ||
  fail "the DTB activation command pins the candidate checksum"
grep -Fq "'/boot/efi/m1n1/boot.bin.pre-dpalt-20260826T230000Z'" "$stage/commands/02-activate-dtb.sh" ||
  fail "the DTB rollback command names one immutable EFI backup"
grep -Fq "'/dev/nvme0n1p4'" "$stage/commands/00-baseline-and-backup.sh" ||
  fail "the EFI plan pins the known partition identity"
grep -Fq 'FSTYPE' "$stage/commands/00-baseline-and-backup.sh" ||
  fail "the EFI plan verifies the vfat filesystem"
grep -Fq 'remount,rw' "$stage/commands/02-activate-dtb.sh" ||
  fail "the DTB plan remounts the read-only ESP only for the transaction"
grep -Fq 'if [[ ,$mount_options, == *,rw,* ]]; then' "$stage/commands/00-baseline-and-backup.sh" &&
  grep -Fq 'if [[ ,$mount_options, == *,rw,* ]]; then' "$stage/commands/02-activate-dtb.sh" &&
  grep -Fq 'if [[ ,$mount_options, == *,rw,* ]]; then' "$stage/commands/02-rollback-dtb.sh" &&
  grep -Fq 'if [[ ,$mount_options, == *,rw,* ]]; then' "$stage/commands/03-live-module.sh" ||
  fail "every privileged gate normalizes a host read-write ESP to read-only"
grep -Fq 'remount,ro' "$stage/commands/02-activate-dtb.sh" ||
  fail "the DTB plan always returns the ESP to read-only"
grep -Fq 'trap remount_esp_ro EXIT' "$stage/commands/02-activate-dtb.sh" ||
  fail "the DTB plan traps every exit to restore the read-only ESP"
grep -Fq 'mv --no-copy -T' "$stage/commands/02-activate-dtb.sh" ||
  fail "the DTB plan atomically renames a same-filesystem temporary file"
! grep -Eq "install .*['\"]?(/boot/efi/m1n1/boot.bin|\$ACTIVE)['\"]?$" "$stage/commands/02-activate-dtb.sh" ||
  fail "the DTB plan never writes directly over active boot.bin"
grep -Fq 'activation_failed' "$stage/commands/02-activate-dtb.sh" &&
  grep -Fq 'EXPECTED_STOCK' "$stage/commands/02-activate-dtb.sh" ||
  fail "the DTB failure trap restores the verified stock image after a post-rename failure"
grep -Fq "*'/0-003f/'*" "$stage/commands/02-activate-dtb.sh" &&
  grep -Fq "!= *'/0-0038/'*" "$stage/commands/02-activate-dtb.sh" ||
  fail "the DTB activation gate requires the cold-plug monitor on 0-003f and never 0-0038"
grep -Fq 'Current active boot SHA-256' "$stage/commands/02-rollback-dtb.sh" ||
  fail "the rollback records an unknown active hash instead of refusing recovery"
! grep -Fq '"$EXPECTED_CANDIDATE" "$ACTIVE" | sha256sum --check' "$stage/commands/02-rollback-dtb.sh" ||
  fail "the rollback accepts a corrupt or otherwise unknown active boot file"
grep -Fq '2>/dev/null' "$stage/commands/02-rollback-dtb.sh" &&
  grep -Fq 'unreadable' "$stage/commands/02-rollback-dtb.sh" ||
  fail "the rollback tolerates a missing or unreadable active boot image"
! grep -Fq '[[ ! -e $TMP ]]' "$stage/commands/02-rollback-dtb.sh" ||
  fail "the rollback overwrites and re-verifies a stale recovery temporary file"
grep -Fq "'${stage}/artifacts/tps6598x-core.ko'" "$stage/commands/03-live-module.sh" ||
  fail "the live-module command quotes the isolated artifact path"
grep -Fq '/0-003f/' "$stage/commands/03-live-module.sh" ||
  fail "the live-module command proves the reconnected partner is on the DP-capable port"
grep -Fq "compgen -G '/sys/class/typec/port*-partner'" "$stage/commands/03-live-module.sh" ||
  fail "the live-module command requires every cable to be unplugged before driver unload"
grep -Fq 'macsmc-battery/capacity' "$stage/commands/03-live-module.sh" ||
  fail "the live-module command enforces the battery gate"
grep -Fq 'trap restore_stock EXIT ERR' "$stage/commands/03-live-module.sh" ||
  fail "the live-module command restores stock automatically on partial failure"
grep -Fq '/sys/bus/i2c/drivers/tps6598x/$controller' "$stage/commands/03-live-module.sh" ||
  fail "the live-module command verifies all three controller bindings"
grep -Fq 'attempt < 20' "$stage/commands/03-live-module.sh" ||
  fail "the live-module command polls while the reconnected Type-C partner appears"
grep -Fq 'sudo reboot' "$stage/commands/README.txt" ||
  fail "the live-module rollback is a reboot to the stock initramfs"
grep -Fq "'/boot/initramfs-linux-asahi-dpalt.img'" "$stage/commands/04-one-boot-initramfs.txt" ||
  fail "the one-boot plan uses a new initramfs filename"
grep -Fq 'Do not run grub-mkconfig' "$stage/commands/04-one-boot-initramfs.txt" ||
  fail "the one-boot plan forbids a persistent GRUB edit"

! rg -n '^[[:space:]]*(sudo[[:space:]]+)?(update-m1n1|grub-mkconfig)([[:space:]]|$)' "$stage/commands" >/dev/null ||
  fail "the generated plan never invokes persistent boot configuration tools"
! rg -n 'install .*tps6598x-core\.ko.*(/usr|/lib)/modules|install .*initramfs-linux-asahi\.img' "$stage/commands" >/dev/null ||
  fail "the generated plan never overwrites the stock module or initramfs"
pass "the staged command plan pairs every activation with an exact rollback without touching stock files"

mac_script="$stage/recovery/RESTORE-DPALT-MAC-20260826T230000Z.sh"
mac_guide="$stage/recovery/RECOVERY-DPALT-MAC-20260826T230000Z.txt"
for recovery_file in "$mac_script" "$mac_guide"; do
  [[ -f $recovery_file && ! -x $recovery_file ]] ||
    fail "the prototype writes a separate non-executable macOS recovery bundle"
done
bash -n "$mac_script" || fail "the macOS recovery script has valid Bash syntax"
grep -Fq 'mode="${1:---check}"' "$mac_script" ||
  fail "the macOS recovery script defaults to a read-only check"
grep -Fq '(( EUID == 0 ))' "$mac_script" ||
  fail "the macOS restore mode requires root"
grep -Fq 'LOCAL_ONLY_ESP_PARTUUID' "$mac_script" ||
  fail "public macOS recovery retains the intentionally unusable partition placeholder"
for field in DiskUUID FilesystemType VolumeName MountPoint; do
  grep -Fq "plist_value $field" "$mac_script" ||
    fail "macOS recovery verifies diskutil field $field"
done
grep -Fq '[[ $script_dir == "$mount_point/m1n1" ]]' "$mac_script" ||
  fail "macOS recovery binds its physical directory to the verified EFI mount"
grep -Fq '/usr/bin/shasum -a 256' "$mac_script" &&
  grep -Fq 'elif [[ -x /usr/bin/openssl ]] &&' "$mac_script" ||
  fail "macOS recovery falls back when shasum cannot run without Perl"
grep -Fq '[[ ! -L $active && ( ! -e $active || -f $active ) ]]' "$mac_script" ||
  fail "macOS recovery rejects a directory or symlink target but permits a missing boot.bin"
! grep -Eq 'sync -f|--no-copy|sha256sum|/home/david|/boot/efi|\$\{[^}]*,,\}' "$mac_script" ||
  fail "macOS recovery has no Linux-only commands, filesystem dependencies, or Bash 4 case conversion"
if [[ $(uname -s) != "Darwin" ]]; then
  if bash "$mac_script" >"$test_tmp/mac-refusal.out" 2>&1; then
    fail "the macOS recovery script refuses Linux without any writes"
  fi
  grep -Fq 'only runs in macOS or macOS Recovery' "$test_tmp/mac-refusal.out" ||
    fail "the macOS recovery refusal explains the host boundary"
fi
mac_script_sha=$(sha256sum "$mac_script" | cut -d' ' -f1)
mac_guide_sha=$(sha256sum "$mac_guide" | cut -d' ' -f1)
grep -Fq "$mac_script_sha" "$stage/commands/02-activate-dtb.sh" &&
  grep -Fq "$mac_guide_sha" "$stage/commands/02-activate-dtb.sh" ||
  fail "the DTB activation pins both macOS recovery bundle checksums"
mac_verified_line=$(grep -nF '"$EXPECTED_MAC_GUIDE" "$EFI_MAC_GUIDE" | sha256sum --check --strict' "$stage/commands/02-activate-dtb.sh" | cut -d: -f1)
mac_synced_line=$(grep -nF 'sync -f "$EFI_MAC_GUIDE"' "$stage/commands/02-activate-dtb.sh" | cut -d: -f1)
activate_line=$(grep -nF 'mv --no-copy -T "$TMP" "$ACTIVE"' "$stage/commands/02-activate-dtb.sh" | cut -d: -f1)
(( mac_verified_line < mac_synced_line && mac_synced_line < activate_line )) ||
  fail "the DTB activation verifies and syncs the offline bundle before replacing boot.bin"
grep -Fq 'unmount' "$mac_guide" && grep -Fq 'mount readOnly' "$mac_guide" &&
  grep -Fq 'sudo /bin/bash' "$mac_guide" && grep -Fq 'omit sudo' "$mac_guide" ||
  fail "the macOS guide separates read-only checks from writable restore and covers Recovery Terminal"
linux_note="$stage/recovery/ROLLBACK-20260826T230000Z.txt"
linux_note_sha=$(sha256sum "$linux_note" | cut -d' ' -f1)
touch -d '@1' "$linux_note"
write_command_plan "$stage" "20260826T230000Z"
[[ $(stat -c '%Y' "$linux_note") == 1 ]] &&
  [[ $(sha256sum "$linux_note" | cut -d' ' -f1) == "$linux_note_sha" ]] ||
  fail "regenerating the commands leaves the existing Gate 0 Linux recovery note untouched"
pass "the offline macOS recovery bundle is pinned, fail-closed, and available before DTB activation"

help_output=$($command_path --help)
[[ $help_output == *'never installs or activates them'* ]] ||
  fail "help states the non-activation boundary"
[[ $help_output == *'--header-root'* ]] ||
  fail "help documents the private header-root input"
[[ $help_output == *'front/lower left USB-C port'* ]] ||
  fail "help identifies the only wired J413 DisplayPort port"
pass "the prototype documents its no-privilege boundary and the correct physical port"
