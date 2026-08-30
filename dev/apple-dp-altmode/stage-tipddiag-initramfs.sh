#!/bin/bash

# A3 T1 TIPD diagnostic staging source. Public copies have invalid host and source constants.
# Only the separately reviewed, pinned private copy is eligible for live use.
# David alone may run that private copy after the staging safety handoff.
readonly D2ST_KERNEL="7.1.6-1-1-ARCH"
readonly D2ST_SOURCE="/LOCAL_ONLY_DEV147_T1_A2/sandbox-tools/run-mvqmtbw_/work/initramfs-linux-asahi-dpalt-tipddiag1.img"
readonly D2ST_PROOFS="/LOCAL_ONLY_DEV147_T1_A2"
readonly D2ST_DESTINATION="/boot/initramfs-linux-asahi-dpalt-tipddiag1.img"
readonly D2ST_IMAGE_SHA="c72c36736cebba0d6d5b67f47b02330c35d3ef81fed9bf5b3315095b0dd765fe"
readonly D2ST_IMAGE_SIZE=19209545
readonly D2ST_RESERVE=16777216
readonly D2ST_ROOT_UUID="LOCAL_ONLY_ROOT_UUID"
readonly D2ST_PACKAGES=$'linux-asahi 7.1.6.asahi1-1\nm1n1 1.6.1-1\nmesa 26.1.8-1\nmkinitcpio 41.1-1\nopenssl 3.6.4-1\ncoreutils 9.11-2\nkmod 34.2-1'

d2stage_die() { printf 'REFUSED: %s\n' "$*" >&2; exit 1; }
d2stage_clean() { /usr/bin/env -i PATH=/usr/bin:/bin LANG=C.UTF-8 /usr/bin/timeout --signal=TERM --kill-after=5 30 "$@"; }

d2stage_check_environment() {
  local name names
  names=$(compgen -e) || d2stage_die "cannot inspect exported environment"
  while IFS= read -r name; do
    case "$name" in
      BASH_ENV | ENV | LD_PRELOAD | LD_LIBRARY_PATH | MKINITCPIO_* | OMARCHY_DPALT_* | DPALT_* | DPST_* | D2ST_* | BASH_FUNC_*)
        d2stage_die "unexpected environment override: $name" ;;
    esac
  done <<<"$names"
}

d2stage_check_proof_root() {
  local actual
  (( $# == 1 )) || d2stage_die "exactly one proof-root value is required"
  actual=$(printf '%s' "$1" | d2stage_clean /usr/bin/sha256sum) || d2stage_die "cannot hash proof-root value"
  [[ $actual == "131ee2ef09e87694dc2be3e9f2a41bca8bd5384fe48990d070d68002e02bfd09  -" ]] || d2stage_die "private proof-root value changed"
}

d2stage_require_operational() {
  [[ $D2ST_ROOT_UUID =~ ^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$ &&
    $D2ST_SOURCE == "$D2ST_PROOFS/sandbox-tools/run-mvqmtbw_/work/initramfs-linux-asahi-dpalt-tipddiag1.img" ]] ||
    d2stage_die "public archival configuration is not operational; no overrides are accepted"
  d2stage_check_proof_root "$D2ST_PROOFS"
}

d2stage_canonical_path() {
  local path="$1" actual
  [[ $path == /* && $path != *$'\n'* && $path != *$'\r'* && $path != *\\* ]] || d2stage_die "path must be plain and absolute"
  actual=$(d2stage_clean /usr/bin/realpath -e -- "$path") || d2stage_die "path does not exist: $path"
  [[ $actual == "$path" ]] || d2stage_die "symlink or noncanonical path: $path"
}

d2stage_secure_directory() {
  local path="$1" owner="$2" info uid mode
  d2stage_canonical_path "$path"
  [[ -d $path && ! -L $path ]] || d2stage_die "not a real directory: $path"
  info=$(d2stage_clean /usr/bin/stat -c '%u %a' -- "$path") || d2stage_die "cannot stat directory"
  read -r uid mode <<<"$info" || d2stage_die "cannot parse directory metadata"
  [[ $uid == "$owner" && $mode =~ ^[0-7]{3,4}$ ]] || d2stage_die "directory ownership/mode mismatch"
  (( (8#$mode & 0022) == 0 )) || d2stage_die "directory permits group/world writes"
}

d2stage_real_file() {
  d2stage_canonical_path "$1"
  [[ -f $1 && ! -L $1 ]] || d2stage_die "not a regular nonsymlink file: $1"
}

d2stage_file_identity() {
  local info device inode links remaining
  d2stage_real_file "$1"
  # Exclude atime: reading a file must not invalidate its identity record.
  info=$(d2stage_clean /usr/bin/stat -c '%d:%i:%h:%u:%f:%s:%y:%z' -- "$1") || d2stage_die "cannot stat file"
  IFS=: read -r device inode links remaining <<<"$info" || d2stage_die "cannot parse file identity"
  [[ $device =~ ^[0-9]+$ && $inode =~ ^[0-9]+$ && $links == 1 && -n $remaining ]] || d2stage_die "file is not singly linked"
  printf '%s\n' "$info" || d2stage_die "cannot record file identity"
}

d2stage_same_identity() {
  local actual
  actual=$(d2stage_file_identity "$1") || d2stage_die "cannot verify source identity"
  [[ $actual == "$2" ]] || d2stage_die "source inode or metadata changed"
}

d2stage_hash_file() {
  local actual
  [[ $2 =~ ^[0-9a-f]{64}$ ]] || d2stage_die "invalid expected SHA-256"
  d2stage_real_file "$1"
  actual=$(d2stage_clean /usr/bin/sha256sum -- "$1") || d2stage_die "cannot hash $1"
  [[ ${actual%% *} == "$2" ]] || d2stage_die "SHA-256 mismatch: $1"
}

d2stage_verified_file() {
  local size
  [[ $2 =~ ^[1-9][0-9]{0,8}$ ]] || d2stage_die "invalid expected size"
  d2stage_file_identity "$1" > /dev/null
  size=$(d2stage_clean /usr/bin/stat -c '%s' -- "$1") || d2stage_die "cannot read file size"
  [[ $size == "$2" ]] || d2stage_die "size mismatch: $1"
  d2stage_hash_file "$1" "$3"
}

d2stage_destination_parent() {
  local path="$1" actual
  [[ $path == /* && $path != *$'\n'* && $path != *$'\r'* && $path != *\\* ]] || d2stage_die "destination must be plain and absolute"
  actual=$(d2stage_clean /usr/bin/realpath -m -s -- "$path") || d2stage_die "cannot resolve destination"
  [[ $actual == "$path" ]] || d2stage_die "noncanonical destination"
  d2stage_secure_directory "${path%/*}" "$EUID"
}

d2stage_absent_destination() { d2stage_destination_parent "$1"; d2stage_check_absent "$1" "destination"; }
d2stage_check_absent() { [[ ! -e $1 && ! -L $1 ]] || d2stage_die "$2 already exists; retain it"; }

d2stage_same_filesystem() {
  local first second
  first=$(d2stage_clean /usr/bin/stat -c '%d' -- "$1") || d2stage_die "cannot read source filesystem"
  second=$(d2stage_clean /usr/bin/stat -c '%d' -- "$2") || d2stage_die "cannot read destination filesystem"
  [[ $first =~ ^[0-9]+$ && $first == "$second" ]] || d2stage_die "publication would cross filesystems"
}

d2stage_check_space_record() {
  local record="$1" size="$2" reserve="$3" blocks unit needed
  [[ $record =~ ^([0-9]{1,18})\ ([1-9][0-9]{0,8})$ ]] || d2stage_die "invalid available-space record"
  blocks=${BASH_REMATCH[1]}; unit=${BASH_REMATCH[2]}
  [[ $size =~ ^[1-9][0-9]{0,8}$ && $reserve =~ ^[0-9]{1,9}$ ]] || d2stage_die "invalid space requirement"
  # Compare block counts instead of multiplying an untrusted large block count.
  needed=$(( (10#$size + 10#$reserve + 10#$unit - 1) / 10#$unit ))
  (( 10#$blocks >= needed )) || d2stage_die "insufficient available space for one image plus reserve"
}

d2stage_check_space() {
  local record
  record=$(d2stage_clean /usr/bin/stat -f -c '%a %S' -- "$1") || d2stage_die "cannot read available filesystem space"
  d2stage_check_space_record "$record" "$2" "$3"
}

d2stage_check_versions() {
  [[ $1 == "$D2ST_KERNEL" ]] || d2stage_die "running kernel changed"
  [[ $2 == "$D2ST_PACKAGES" ]] || d2stage_die "installed package versions changed"
}

d2stage_check_mount() {
  local filesystem uuid mountpoint extra
  [[ $2 =~ ^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$ && $1 != *$'\n'* && $1 != *$'\r'* ]] ||
    d2stage_die "invalid or ambiguous mount identity"
  read -r filesystem uuid mountpoint extra <<<"$1" || d2stage_die "cannot parse mount identity"
  [[ $filesystem == "ext4" && $uuid == "$2" && $mountpoint == "/" && -z $extra ]] || d2stage_die "/boot is not on the pinned ext4 root"
}

d2stage_check_battery() {
  [[ $1 =~ ^[0-9]{1,3}$ ]] || d2stage_die "battery capacity unreadable"
  (( 10#$1 > 50 && 10#$1 <= 100 )) || d2stage_die "battery must be strictly above 50%"
}

d2stage_check_pins() {
  local line hash file count=0 pattern='^([0-9a-f]{64})  (/.+)$'
  local -A seen=()
  [[ -n $1 ]] || d2stage_die "missing protected/proof records"
  (( ${#1} <= 32768 )) || d2stage_die "excessive protected/proof records"
  while IFS= read -r line; do
    [[ $line =~ $pattern ]] || d2stage_die "invalid protected/proof record"
    hash=${BASH_REMATCH[1]}; file=${BASH_REMATCH[2]}
    [[ ! -v seen["$file"] ]] || d2stage_die "duplicate protected/proof path"
    seen["$file"]=1
    count=$((count + 1))
    (( count <= 64 )) || d2stage_die "excessive protected/proof records"
    d2stage_hash_file "$file" "$hash"
    printf '%s  %s\n' "$hash" "$file" || d2stage_die "cannot record protected/proof check"
  done <<<"$1"
}

d2stage_copy_verified() (
  local source="$1" temporary="$2" hash="$3" size="$4" identity
  umask 077
  identity=$(d2stage_file_identity "$source") || d2stage_die "cannot pin source identity"
  d2stage_verified_file "$source" "$size" "$hash"
  d2stage_same_identity "$source" "$identity"
  d2stage_absent_destination "$temporary"
  d2stage_clean /usr/bin/dd if="$source" of="$temporary" bs=1M count="$size" \
    iflag=fullblock,count_bytes,nofollow conv=excl,fsync status=none || d2stage_die "copy failed; retain partial image"
  d2stage_clean /usr/bin/chmod 0600 -- "$temporary" || d2stage_die "cannot set private image mode"
  d2stage_verified_file "$temporary" "$size" "$hash"
  d2stage_verified_file "$source" "$size" "$hash"
  d2stage_same_identity "$source" "$identity"
  d2stage_sync "$temporary"
)

d2stage_publish_verified() {
  local temporary="$1" destination="$2" hash="$3" size="$4" inode mode final_inode
  d2stage_verified_file "$temporary" "$size" "$hash"
  mode=$(d2stage_clean /usr/bin/stat -c '%a' -- "$temporary") || d2stage_die "cannot stat private mode"
  [[ $mode == 600 ]] || d2stage_die "temporary image mode is not 0600"
  inode=$(d2stage_clean /usr/bin/stat -c '%d:%i' -- "$temporary") || d2stage_die "cannot pin temporary inode"
  d2stage_destination_parent "$destination"
  d2stage_same_filesystem "$temporary" "${destination%/*}"
  # This atomic no-replace operation, not an earlier existence check, handles collisions.
  d2stage_clean /usr/bin/mv --no-copy --update=none-fail -T -- "$temporary" "$destination" || d2stage_die "publication refused; retain candidate and destination"
  d2stage_verified_file "$destination" "$size" "$hash"
  final_inode=$(d2stage_clean /usr/bin/stat -c '%d:%i' -- "$destination") || d2stage_die "cannot verify published inode"
  mode=$(d2stage_clean /usr/bin/stat -c '%a' -- "$destination") || d2stage_die "cannot verify published mode"
  [[ $inode == "$final_inode" && $mode == 600 ]] || d2stage_die "published inode or mode changed"
  d2stage_sync "$destination"
  d2stage_sync "${destination%/*}"
}

d2stage_sync() { d2stage_clean /usr/bin/sync -f -- "$1" || d2stage_die "sync failed: $1"; }

d2stage_start() {
  d2stage_secure_directory "$1" "$EUID"
  (umask 077; set -C; printf 'INCOMPLETE staging. Retain all files. No boot permission.\n' >"$1/INCOMPLETE") || d2stage_die "cannot create exclusive incomplete marker"
  d2stage_sync "$1/INCOMPLETE"
  d2stage_sync "$1"
}

d2stage_restore_incomplete() {
  if [[ ! -e $1/INCOMPLETE && ! -L $1/INCOMPLETE ]]; then
    (umask 077; set -C; printf 'INCOMPLETE: completion was not confirmed. Retain all files; do not reboot.\n' >"$1/INCOMPLETE") ||
      printf 'HOLD: could not restore INCOMPLETE; a nonzero exit still invalidates completion.\n' >&2
    d2stage_clean /usr/bin/sync -f -- "$1/INCOMPLETE" >/dev/null 2>&1 || true
    d2stage_clean /usr/bin/sync -f -- "$1" >/dev/null 2>&1 || true
  fi
}

d2stage_finish() {
  local directory="$1" destination="$2" hash="$3" size="$4" name mode
  d2stage_secure_directory "$directory" "$EUID"
  for name in INCOMPLETE before.sha256 before-publication.sha256 after.sha256; do
    d2stage_file_identity "$directory/$name" > /dev/null
  done
  d2stage_clean /usr/bin/cmp -s "$directory/before.sha256" "$directory/before-publication.sha256" || d2stage_die "protected/proof checks changed before publication"
  d2stage_clean /usr/bin/cmp -s "$directory/before.sha256" "$directory/after.sha256" || d2stage_die "protected/proof checks changed after publication"
  d2stage_verified_file "$destination" "$size" "$hash"
  mode=$(d2stage_clean /usr/bin/stat -c '%a' -- "$destination") || d2stage_die "cannot check final mode"
  [[ $mode == 600 ]] || d2stage_die "final image mode changed"
  (umask 077; set -C; printf 'PROVISIONAL staging record. Completion requires exit 0, the final console PASS, and staging-start-marker.txt without INCOMPLETE. Default boot unchanged. No reboot permission.\n' >"$directory/RESULT.txt") || d2stage_die "cannot create exclusive provisional result"
  d2stage_sync "$directory/RESULT.txt"
  d2stage_sync "$directory"
  d2stage_clean /usr/bin/mv --no-copy --update=none-fail -T -- "$directory/INCOMPLETE" "$directory/staging-start-marker.txt" || d2stage_die "cannot finalize start marker"
  if ! d2stage_clean /usr/bin/sync -f -- "$directory"; then
    d2stage_restore_incomplete "$directory"
    d2stage_die "final marker sync failed; completion is not confirmed"
  fi
  printf 'STAGING ONLY PASS: %s\nChecks retained in %s\nNo reboot permission. Normal boot is unchanged; this T1 TIPD diagnostic image is untested at startup.\n' "$destination" "$directory" || d2stage_die "cannot report completion"
}

d2stage_protected_inputs() {
  local module_root="/usr/lib/modules/$D2ST_KERNEL" base
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
    "c8670dc6989098f8e4a9858fd6f4fd31cf4b70dd6b478b52db8e651f377e1027" "/usr/bin/dd" \
    "bf77551deae42b2d0aa5eaede07a8f9c2954409fe38ea79af2b0a238880c899c" "/usr/bin/sync" \
    "7539e28e3fc02160564cc93739e03d0d3e001a6fae58671371403a46b643439b" "/usr/bin/timeout" \
    "d150400f9782c876972b2745d95617cd44e23574452f63980704911a467f7767" "$module_root/kernel/drivers/usb/dwc3/dwc3-apple.ko" \
    "fd1c3d105bd69a649a38e89e2ca0bcbe6f656200a0f211d58211e8c7b3ec944b" "$module_root/kernel/drivers/phy/apple/phy-apple-atc.ko" \
    "ae8f1ed7f4f258f89931209cd7de6030be9f6875372d7329151b822a6ba2281f" "/boot/initramfs-linux-asahi-dpalt.img" \
    "a11bf3a2bac1f105aa57b08ce9fad338c68882851247f7524d09f4b7c94188ca" "/boot/initramfs-linux-asahi-dpalt-usbdiag1.img" \
    "4d4f0557af57eebcc33322f004bcc7968254e644b069a11102375df0b31a52ae" "/boot/initramfs-linux-asahi-dpalt-usbearly1.img" \
    "ae8f1ed7f4f258f89931209cd7de6030be9f6875372d7329151b822a6ba2281f" "/home/david/o/.dev147-stage/gate4-20260827T190929Z/initramfs-linux-asahi-dpalt.img" \
    "203ab7027536c8d16f373d02c1f6346a5c34cfe095a9dafd0cfe37d2b354090c" "/home/david/o/.dev147-stage/artifacts/boot.bin.dpalt" \
    "285333005f6ca16ff6131b84135d66a622b07d0187070cec80d46c5e69cfc47a" "/home/david/o/.dev147-stage/prototype/dev/apple-dp-altmode/prepare-one-boot-initramfs.sh" \
    "d35fa0311ee1baecec50561e9d50fabeea9570ba2fa8d4ef480bdb84836920e2" "/home/david/o/.dev147-stage/prototype/dev/apple-dp-altmode/stage-one-boot-initramfs.sh" \
    "f20a89f6be6b7e2b42a77abfbd14ff6aee376d320097c7b3be8eb13a529f6c9f" "/home/david/o/.dev147-stage/commands/00-baseline-and-backup.sh" \
    "3c363cf7ecf44d3e92648fc654dd76b86dd3c83cf065475e9a0da98c864cb868" "/home/david/o/.dev147-stage/commands/02-activate-dtb.sh" \
    "f7f825a6502da5741706275dba0768f47d9c819a31955cc481b66b3e9c841bbc" "/home/david/o/.dev147-stage/commands/03-live-module.sh" || d2stage_die "cannot produce protected records"
  for base in /boot/efi/m1n1 /home/david/o/.dev147-stage/recovery; do
    printf '%s  %s\n' \
      "bb6829c44d8de26d6615406b41edc0beef2254766b5ed114afad2029db7ae856" "$base/boot.bin.pre-dpalt-20260826T222113Z" \
      "dc0de17453ecc681c1420db03fde4ec8d24b022453f2489febbbdbd12c06ae64" "$base/RESTORE-DPALT-MAC-20260826T222113Z.sh" \
      "dcb10da1d75be23953382270fb2fd5bc82e32999e43745ae577e65d1887dd59a" "$base/RECOVERY-DPALT-MAC-20260826T222113Z.txt" || d2stage_die "cannot produce recovery records"
  done
}

d2stage_proof_inputs() {
  printf '%s  %s\n' \
    "215051ed006431c73f2e402e5a1d503daaa41dc9d4b9e2bb66a82ac868892a92" "$D2ST_PROOFS/candidate-source-v1/core.c" \
    "a0fdadc351261643545e5afd8561923be99431661c447084336c9318f5b0c02f" "$D2ST_PROOFS/sandbox-tools/run-zgkw4hqf/work/candidate/tps6598x-core.ko" \
    "95abe335e44a5f30781a1e80f3e26efc314746b5d6baf11bae658f4484d9ada3" "$D2ST_PROOFS/a2-candidate-build-evidence.json" \
    "1665fe5a0d5d58eb3fa029faaea066da5c4b026415d19c33d644c5ec0b44f96a" "$D2ST_PROOFS/sandbox-tools/run-988kuwr1/work/e-control-header.json" \
    "6bbbb024d616bfa767dfe71b4a6121a1e75233bb1a1c8bc47b81b93f28628709" "$D2ST_PROOFS/sandbox-tools/run-988kuwr1/work/e-control-evidence.json" \
    "5e08a383469bd65d402939d0b7ca9cef9c2febb77ca12de1d577454b0d2de8f2" "$D2ST_PROOFS/sandbox-tools/run-988kuwr1/work/e-control-result.json" \
    "10e0ad4b37efab56d04d910f959a6acb5ac53db6f8b1e04efdab91943f1d26c5" "$D2ST_PROOFS/sandbox-tools/run-mvqmtbw_/work/t1-assembly-result.json" \
    "c11ec0dc7d39dad155a75fe32c72edad6620506fa3f842f76549322a5360a4d4" "$D2ST_PROOFS/sandbox-tools/run-mvqmtbw_/command.json" \
    "c41b8de09b6bf2c08877af36fd48604309d8d1bfec2204a93d4cf0f51836fd59" "$D2ST_PROOFS/sandbox-tools/run-mvqmtbw_/inputs.json" \
    "eb52e8d04db7a847c19dc68e57f5b1b1331c46c45852100dc3ae19d7e9da96f2" "$D2ST_PROOFS/sandbox-tools/run-mvqmtbw_/security.json" \
    "995626ca50174bc34f03fdf59825ddb8c485ffcb59d62d20116b394620ac3a1f" "$D2ST_PROOFS/sandbox-tools/run-mvqmtbw_/result.json" || d2stage_die "cannot produce accepted T1/A2 proof records"
}

d2stage_check_external_power() {
  (( $# == 2 )) && [[ $1 == "1" && $2 == "1" ]] ||
    d2stage_die "both external-power online values must be exactly 1"
}

d2stage_preflight() {
  local kernel packages mount_info capacity ac_online source_online protected proofs metadata status alias dt="/proc/device-tree"
  d2stage_check_absent /var/lib/pacman/db.lck "package transaction"
  d2stage_check_absent /etc/default/update-m1n1 "persistent boot override"
  kernel=$(d2stage_clean /usr/bin/uname -r) || d2stage_die "cannot read kernel version"
  packages=$(d2stage_clean /usr/bin/pacman -Q linux-asahi m1n1 mesa mkinitcpio openssl coreutils kmod) || d2stage_die "cannot read package versions"
  d2stage_check_versions "$kernel" "$packages"
  d2stage_clean /usr/bin/tr '\0' '\n' <"$dt/compatible" | d2stage_clean /usr/bin/grep -Fxq apple,j413 || d2stage_die "not J413"
  d2stage_clean /usr/bin/tr '\0' '\n' <"$dt/compatible" | d2stage_clean /usr/bin/grep -Fxq apple,t8112 || d2stage_die "not T8112"
  status=$(d2stage_clean /usr/bin/tr -d '\0' <"$dt/soc/dcp@271c00000/status") || d2stage_die "cannot read DCP status"
  alias=$(d2stage_clean /usr/bin/tr -d '\0' <"$dt/aliases/dcpext") || d2stage_die "cannot read DCP alias"
  [[ $status == "okay" ]] || d2stage_die "prototype DCP not enabled"
  [[ $alias == "/soc/dcp@271c00000" ]] || d2stage_die "prototype alias changed"
  d2stage_clean /usr/bin/cmp -s "$dt/soc/dcp@271c00000/phandle" "$dt/soc/i2c@235010000/usb-pd@3f/connector/displayport" || d2stage_die "front-port route changed"
  d2stage_check_absent "$dt/soc/i2c@235010000/usb-pd@38/connector/displayport" "rear-port route"
  capacity=$(d2stage_clean /usr/bin/cat /sys/class/power_supply/macsmc-battery/capacity) || d2stage_die "cannot read battery capacity"
  d2stage_check_battery "$capacity"
  ac_online=$(d2stage_clean /usr/bin/cat /sys/class/power_supply/macsmc-ac/online) || d2stage_die "cannot read external AC online state"
  source_online=$(d2stage_clean /usr/bin/cat /sys/class/power_supply/tps6598x-source-psy-0-003a/online) || d2stage_die "cannot read external source online state"
  d2stage_check_external_power "$ac_online" "$source_online"
  d2stage_secure_directory /boot 0
  mount_info=$(d2stage_clean /usr/bin/findmnt -n -o FSTYPE,UUID,TARGET -T /boot) || d2stage_die "cannot identify /boot filesystem"
  d2stage_check_mount "$mount_info" "$D2ST_ROOT_UUID"
  d2stage_secure_directory "${D2ST_SOURCE%/*}" 1001
  d2stage_verified_file "$D2ST_SOURCE" "$D2ST_IMAGE_SIZE" "$D2ST_IMAGE_SHA"
  metadata=$(d2stage_clean /usr/bin/stat -c '%u %a' -- "$D2ST_SOURCE") || d2stage_die "cannot read source ownership"
  [[ $metadata == "1001 600" ]] || d2stage_die "private source ownership/mode changed"
  protected=$(d2stage_protected_inputs) || d2stage_die "protected-record producer failed"
  proofs=$(d2stage_proof_inputs) || d2stage_die "proof-record producer failed"
  d2stage_check_pins "$protected"$'\n'"$proofs"
  d2stage_check_absent /var/lib/pacman/db.lck "package transaction"
}

d2stage_install_exit_trap() {
  local quoted_directory
  # Bind the path now: Bash can unwind main's locals before an EXIT trap runs.
  printf -v quoted_directory '%q' "$1" || d2stage_die "cannot quote failure-record path"
  trap "stage_status=\$?; if (( stage_status != 0 )); then d2stage_restore_incomplete $quoted_directory; printf 'STAGING FAILED. Retain %s and any partial/final image. Do not reboot.\\n' $quoted_directory >&2; fi" EXIT || d2stage_die "cannot install failure handler"
}

d2stage_main() {
  set -Eeuo pipefail
  umask 077
  (( $# == 0 )) || d2stage_die "no arguments or path overrides are accepted"
  d2stage_check_environment
  d2stage_require_operational
  (( EUID == 0 )) || d2stage_die "David must run the reviewed private staging gate as root"
  local private_directory temporary directory_mode
  d2stage_preflight
  d2stage_absent_destination "$D2ST_DESTINATION"
  d2stage_check_space /boot "$D2ST_IMAGE_SIZE" "$D2ST_RESERVE"
  private_directory=$(d2stage_clean /usr/bin/mktemp -d /boot/.dev147-tipddiag-stage.XXXXXXXXXX) || d2stage_die "cannot create private staging directory"
  d2stage_install_exit_trap "$private_directory"
  d2stage_secure_directory "$private_directory" 0
  directory_mode=$(d2stage_clean /usr/bin/stat -c '%a' -- "$private_directory") || d2stage_die "cannot read staging directory mode"
  [[ $directory_mode == 700 ]] || d2stage_die "staging directory is not private"
  d2stage_start "$private_directory"
  (set -C; d2stage_preflight >"$private_directory/before.sha256") || d2stage_die "initial preflight record failed"
  d2stage_check_space /boot "$D2ST_IMAGE_SIZE" "$D2ST_RESERVE"
  temporary="$private_directory/.initramfs-linux-asahi-dpalt-tipddiag1.img.tmp"
  d2stage_copy_verified "$D2ST_SOURCE" "$temporary" "$D2ST_IMAGE_SHA" "$D2ST_IMAGE_SIZE"
  (set -C; d2stage_preflight >"$private_directory/before-publication.sha256") || d2stage_die "pre-publication record failed"
  d2stage_publish_verified "$temporary" "$D2ST_DESTINATION" "$D2ST_IMAGE_SHA" "$D2ST_IMAGE_SIZE"
  (set -C; d2stage_preflight >"$private_directory/after.sha256") || d2stage_die "post-publication record failed"
  d2stage_finish "$private_directory" "$D2ST_DESTINATION" "$D2ST_IMAGE_SHA" "$D2ST_IMAGE_SIZE"
}

if [[ ${BASH_SOURCE[0]} == "$0" ]]; then
  d2stage_main "$@"
fi
