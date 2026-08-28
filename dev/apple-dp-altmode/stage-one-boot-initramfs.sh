#!/bin/bash

# Public archival copy: the root identity is deliberately unusable. Do not run
# this copy live. Historical QA applies to the private machine-pinned original.

# David runs this standalone gate as root after review. It stages one fixed image.
# No source/config overrides, boot selection, device operations, or cleanup.
readonly DPST_KERNEL="7.1.6-1-1-ARCH"
readonly DPST_SOURCE="/home/david/o/.dev147-stage/gate4-20260827T190929Z/initramfs-linux-asahi-dpalt.img"
readonly DPST_DESTINATION="/boot/initramfs-linux-asahi-dpalt.img"
readonly DPST_IMAGE_SHA="ae8f1ed7f4f258f89931209cd7de6030be9f6875372d7329151b822a6ba2281f"
readonly DPST_IMAGE_SIZE=19184103
readonly DPST_ROOT_UUID="LOCAL_ONLY_ROOT_UUID"

dpstage_die() { printf 'REFUSED: %s\n' "$*" >&2; exit 1; }
dpstage_clean() { /usr/bin/env -i PATH=/usr/bin:/bin LANG=C.UTF-8 "$@"; }

dpstage_check_environment() {
  local name
  while IFS= read -r name; do
    case "$name" in
      BASH_ENV | ENV | LD_PRELOAD | LD_LIBRARY_PATH | MKINITCPIO_* | OMARCHY_DPALT_* | DPALT_* | DPST_*)
        dpstage_die "unexpected environment override: $name" ;;
    esac
  done < <(compgen -e)
}

dpstage_canonical_path() {
  local path="$1" actual
  [[ $path == /* && $path != *$'\n'* && $path != *$'\r'* && $path != *\\* ]] ||
    dpstage_die "path must be a plain absolute path"
  actual=$(dpstage_clean realpath -e -- "$path") || dpstage_die "path does not exist: $path"
  [[ $actual == "$path" ]] || dpstage_die "symlink or noncanonical path: $path"
}

dpstage_secure_directory() {
  local path="$1" expected_uid="$2" uid mode
  dpstage_canonical_path "$path"
  [[ -d $path && ! -L $path ]] || dpstage_die "not a real directory: $path"
  read -r uid mode <<<"$(dpstage_clean stat -c '%u %a' -- "$path")"
  [[ $uid == "$expected_uid" && $mode =~ ^[0-7]{3,4}$ ]] || dpstage_die "directory ownership/mode mismatch: $path"
  (( (8#$mode & 0022) == 0 )) || dpstage_die "directory permits group/world writes: $path"
}

dpstage_real_file() {
  dpstage_canonical_path "$1"
  [[ -f $1 && ! -L $1 ]] || dpstage_die "not a regular nonsymlink file: $1"
}

dpstage_hash_file() {
  local actual
  dpstage_real_file "$1"
  actual=$(dpstage_clean sha256sum -- "$1") || dpstage_die "cannot hash $1"
  [[ ${actual%% *} == "$2" ]] || dpstage_die "SHA-256 mismatch: $1"
}

dpstage_verified_file() {
  dpstage_real_file "$1"
  [[ $3 =~ ^[1-9][0-9]*$ ]] || dpstage_die "invalid expected size"
  [[ $(dpstage_clean stat -c '%s' -- "$1") == "$3" ]] || dpstage_die "size mismatch: $1"
  dpstage_hash_file "$1" "$2"
}

dpstage_destination_parent() {
  local path="$1" parent
  [[ $path == /* && $path != *$'\n'* && $path != *$'\r'* && $path != *\\* ]] ||
    dpstage_die "destination must be a plain absolute path"
  [[ $(dpstage_clean realpath -m -s -- "$path") == "$path" ]] || dpstage_die "noncanonical destination"
  parent=${path%/*}
  dpstage_secure_directory "$parent" "$EUID"
}

dpstage_absent_destination() {
  dpstage_destination_parent "$1"
  [[ ! -e $1 && ! -L $1 ]] || dpstage_die "destination already exists; it will not be overwritten"
}

dpstage_copy_verified() (
  local source="$1" temporary="$2" hash="$3" size="$4"
  umask 077
  dpstage_verified_file "$source" "$hash" "$size"
  dpstage_absent_destination "$temporary"
  # Limit the read even if a source changes after its initial size check.
  dpstage_clean /usr/bin/dd if="$source" of="$temporary" bs=1M count="$size" \
    iflag=fullblock,count_bytes,nofollow conv=excl,fsync status=none ||
    dpstage_die "copy failed; retain the private directory and partial image"
  dpstage_clean chmod 0600 -- "$temporary" || dpstage_die "cannot set private image mode"
  dpstage_verified_file "$temporary" "$hash" "$size"
  dpstage_verified_file "$source" "$hash" "$size"
  dpstage_clean sync -f "$temporary" || dpstage_die "temporary image sync failed"
)

dpstage_publish_verified() {
  local temporary="$1" destination="$2" hash="$3" size="$4"
  dpstage_verified_file "$temporary" "$hash" "$size"
  [[ $(dpstage_clean stat -c '%a' -- "$temporary") == 600 ]] || dpstage_die "temporary image mode is not 0600"
  dpstage_destination_parent "$destination"
  # The atomic no-replace operation, not an earlier existence check, handles races.
  dpstage_clean /usr/bin/mv --no-copy --update=none-fail -T -- "$temporary" "$destination" ||
    dpstage_die "publication refused; retain the private candidate and existing destination"
  dpstage_verified_file "$destination" "$hash" "$size"
  [[ $(dpstage_clean stat -c '%a' -- "$destination") == 600 ]] || dpstage_die "published image mode changed"
  dpstage_clean sync -f "$destination" || dpstage_die "published image sync failed"
  dpstage_clean sync -f "${destination%/*}" || dpstage_die "destination filesystem sync failed"
}

dpstage_protected_inputs() {
  local module_root="/usr/lib/modules/$DPST_KERNEL" base
  printf '%s  %s\n' \
    "bc02723db427639c6586d29eea7918e084874c741b60bf145585c6349fd07d70" "/home/david/o/.dev147-stage/artifacts/tps6598x-core.ko" \
    "ac7b9b7a92a95b88cf7d56cb134499cf8bae3d50a78745223e4c55b75a594e72" "$module_root/kernel/drivers/usb/typec/tipd/tps6598x-core.ko" \
    "3d64857f8964d05e41778ccc5b4b8abbcdfedaceb918add2eeff8cb41272a8a2" "$module_root/dtbs/t8112-j413.dtb" \
    "ee36d989d62f2dd498b818e15c2044350c79d814a2017ffca61fdc2ad1aa95b6" "$module_root/vmlinuz" \
    "ee36d989d62f2dd498b818e15c2044350c79d814a2017ffca61fdc2ad1aa95b6" "/boot/vmlinuz-linux-asahi" \
    "7a781b73e6525697ff57eacda649d2a41de5132f87692349d4113c983ed8f4d4" "$module_root/kernel/drivers/phy/apple/phy-apple-dptx.ko" \
    "02c862234455ce79403f8c00dff629e05e540fa5b4a58c9a3b574d7d40a3d2b9" "$module_root/kernel/drivers/mux/mux-apple-display-crossbar.ko" \
    "203ab7027536c8d16f373d02c1f6346a5c34cfe095a9dafd0cfe37d2b354090c" "/boot/efi/m1n1/boot.bin" \
    "625641095075a9a2396bc701ffd48ac58f2c8a1758e250fa3f6b55b29dcae296" "/boot/initramfs-linux-asahi.img" \
    "68c36bbbb3c530dba8647f9435252da53adf53942b37b76e399ccd234cc0f24d" "/boot/grub/grub.cfg" \
    "306c9340fedaa177cde4a5aada1d5928cbecb0d5f1316a62a3c90f5930683ff9" "/usr/lib/libcrypto.so.3" \
    "8c431284782552fea9d8a0a73ceeae2d8334ea4e45b3e794bfffa5a6caa67c9c" "/usr/lib/ossl-modules/legacy.so" \
    "5f8961fa59c447798ab5124045358083e668fbf3c66aa7f8cc474622c89cb5d1" "/usr/bin/mv" \
    "c8670dc6989098f8e4a9858fd6f4fd31cf4b70dd6b478b52db8e651f377e1027" "/usr/bin/dd"
  for base in /boot/efi/m1n1 /home/david/o/.dev147-stage/recovery; do
    printf '%s  %s\n' \
      "bb6829c44d8de26d6615406b41edc0beef2254766b5ed114afad2029db7ae856" "$base/boot.bin.pre-dpalt-20260826T222113Z" \
      "dc0de17453ecc681c1420db03fde4ec8d24b022453f2489febbbdbd12c06ae64" "$base/RESTORE-DPALT-MAC-20260826T222113Z.sh" \
      "dcb10da1d75be23953382270fb2fd5bc82e32999e43745ae577e65d1887dd59a" "$base/RECOVERY-DPALT-MAC-20260826T222113Z.txt"
  done
}

dpstage_preflight() {
  local filesystem uuid mountpoint capacity hash file mount_info
  local dt="/proc/device-tree"
  [[ ! -e /var/lib/pacman/db.lck && ! -L /var/lib/pacman/db.lck ]] || dpstage_die "package transaction is active"
  [[ ! -e /etc/default/update-m1n1 && ! -L /etc/default/update-m1n1 ]] || dpstage_die "persistent boot override exists"
  [[ $(dpstage_clean uname -r) == "$DPST_KERNEL" ]] || dpstage_die "running kernel changed"
  [[ $(dpstage_clean pacman -Q linux-asahi) == "linux-asahi 7.1.6.asahi1-1" ]] || dpstage_die "installed kernel changed"
  [[ $(dpstage_clean pacman -Q openssl) == "openssl 3.6.4-1" ]] || dpstage_die "OpenSSL package changed"
  dpstage_clean tr '\0' '\n' <"$dt/compatible" | dpstage_clean grep -Fxq apple,j413 || dpstage_die "not J413"
  dpstage_clean tr '\0' '\n' <"$dt/compatible" | dpstage_clean grep -Fxq apple,t8112 || dpstage_die "not T8112"
  [[ $(dpstage_clean tr -d '\0' <"$dt/soc/dcp@271c00000/status") == "okay" ]] || dpstage_die "prototype DCP not enabled"
  [[ $(dpstage_clean tr -d '\0' <"$dt/aliases/dcpext") == "/soc/dcp@271c00000" ]] || dpstage_die "prototype alias changed"
  dpstage_clean cmp -s "$dt/soc/dcp@271c00000/phandle" "$dt/soc/i2c@235010000/usb-pd@3f/connector/displayport" ||
    dpstage_die "front-port DisplayPort route changed"
  [[ ! -e $dt/soc/i2c@235010000/usb-pd@38/connector/displayport ]] || dpstage_die "rear-port route changed"
  capacity=$(< /sys/class/power_supply/macsmc-battery/capacity)
  [[ $capacity =~ ^[0-9]{1,3}$ ]] || dpstage_die "battery capacity unreadable"
  (( 10#$capacity > 50 && 10#$capacity <= 100 )) || dpstage_die "battery must be strictly above 50%"
  dpstage_secure_directory /boot 0
  mount_info=$(dpstage_clean findmnt -n -o FSTYPE,UUID,TARGET -T /boot) || dpstage_die "cannot identify /boot filesystem"
  [[ $mount_info != *$'\n'* ]] || dpstage_die "ambiguous /boot mount"
  read -r filesystem uuid mountpoint <<<"$mount_info"
  [[ $filesystem == "ext4" && $uuid == "$DPST_ROOT_UUID" && $mountpoint == "/" ]] ||
    dpstage_die "/boot is not on the pinned ext4 root filesystem"
  dpstage_canonical_path "${DPST_SOURCE%/*}"
  [[ -d ${DPST_SOURCE%/*} && ! -L ${DPST_SOURCE%/*} ]] || dpstage_die "source parent is not a real directory"
  dpstage_verified_file "$DPST_SOURCE" "$DPST_IMAGE_SHA" "$DPST_IMAGE_SIZE"
  while read -r hash file; do
    dpstage_hash_file "$file" "$hash"
    printf '%s  %s\n' "$hash" "$file"
  done < <(dpstage_protected_inputs)
}

dpstage_main() {
  set -Eeuo pipefail
  umask 077
  (( EUID == 0 )) || dpstage_die "this reviewed staging gate must be run by David as root"
  (( $# == 0 )) || dpstage_die "no arguments or path overrides are accepted"
  dpstage_check_environment
  local private_directory temporary
  dpstage_preflight
  dpstage_absent_destination "$DPST_DESTINATION"
  private_directory=$(dpstage_clean mktemp -d /boot/.dev147-dpalt-stage.XXXXXXXXXX) ||
    dpstage_die "cannot create private staging directory"
  trap 'stage_status=$?; if (( stage_status != 0 )); then printf "STAGING FAILED. Retain %s and any partial/final image. Do not reboot.\n" "$private_directory" >&2; fi' EXIT
  dpstage_secure_directory "$private_directory" 0
  [[ $(dpstage_clean stat -c '%a' -- "$private_directory") == 700 ]] || dpstage_die "staging directory is not private"
  printf 'INCOMPLETE staging. Retain this directory and partial files on failure. No boot permission.\n' >"$private_directory/INCOMPLETE"
  dpstage_preflight >"$private_directory/before.sha256"
  temporary="$private_directory/initramfs-linux-asahi-dpalt.img"
  dpstage_copy_verified "$DPST_SOURCE" "$temporary" "$DPST_IMAGE_SHA" "$DPST_IMAGE_SIZE"
  dpstage_preflight >"$private_directory/before-publication.sha256"
  dpstage_publish_verified "$temporary" "$DPST_DESTINATION" "$DPST_IMAGE_SHA" "$DPST_IMAGE_SIZE"
  dpstage_preflight >"$private_directory/after.sha256"
  dpstage_verified_file "$DPST_DESTINATION" "$DPST_IMAGE_SHA" "$DPST_IMAGE_SIZE"
  printf 'STAGING ONLY PASS. Default boot is unchanged. No reboot yet; the image remains untested at startup.\n' >"$private_directory/RESULT.txt"
  dpstage_clean sync -f "$private_directory/RESULT.txt" || dpstage_die "result sync failed"
  dpstage_clean sync -f /boot || dpstage_die "/boot sync failed"
  dpstage_clean /usr/bin/mv --no-copy --update=none-fail -T -- \
    "$private_directory/INCOMPLETE" "$private_directory/staging-start-marker.txt" ||
    dpstage_die "cannot record the completed staging marker"
  printf 'STAGING ONLY PASS: %s\nChecks retained in %s\nNo reboot yet. Normal boot is unchanged. This image remains untested at startup.\n' \
    "$DPST_DESTINATION" "$private_directory"
}

if [[ ${BASH_SOURCE[0]} == "$0" ]]; then
  dpstage_main "$@"
fi
