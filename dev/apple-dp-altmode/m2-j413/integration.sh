#!/bin/bash

if [[ ${BASH_SOURCE[0]} == "$0" && $- != *p* ]]; then
  /usr/bin/env -i PATH=/usr/bin:/bin LANG=C.UTF-8 SUDO_UID="${SUDO_UID:-}" \
    /usr/bin/bash --noprofile --norc -p "${BASH_SOURCE[0]}" "$@"
else
set -euo pipefail

readonly M2DP_KERNEL_RELEASE="7.1.6-1-1-ARCH"
readonly M2DP_KERNEL_PACKAGE="linux-asahi 7.1.6.asahi1-1"
readonly M2DP_M1N1_PACKAGE="m1n1 1.6.1-1"
readonly M2DP_UBOOT_PACKAGE="uboot-asahi 2026.04.asahi2-1"
readonly M2DP_STOCK_BOOT_SHA256="bb6829c44d8de26d6615406b41edc0beef2254766b5ed114afad2029db7ae856"
readonly M2DP_BOOT_SHA256="203ab7027536c8d16f373d02c1f6346a5c34cfe095a9dafd0cfe37d2b354090c"
readonly M2DP_BOOT_SIZE="6205569"
readonly M2DP_IMAGE_SHA256="a93dd0c1b3a6c4d81bf76f2f43c7c7a2b8b7e1e0306bc487de018667f9c8c196"
readonly M2DP_IMAGE_SIZE="19184210"
readonly M2DP_MODULE_SHA256="69d220a692d1bbc0dc5d40069c36ff118a0f0816137e0aa548f4f232efcba811"
readonly M2DP_MODULE_BUILD_ID="50ee94a5f8dbae780c676a73b611a7ad5197e47a"
readonly M2DP_HOOK_SHA256="469820ad7cfd015a22cff979b0aa70d62e82dcc7cc05951dca92f40cd660f2bd"
readonly M2DP_HOOK_SIZE="303"
readonly M2DP_IMAGE_PATH="/boot/initramfs-linux-asahi-m2-displayport.img"
readonly M2DP_ACTIVE_BOOT_PATH="/boot/efi/m1n1/boot.bin"
readonly M2DP_HOOK_PATH="/etc/pacman.d/hooks/05-omarchy-m2-displayport-guard.hook"
readonly M2DP_STATE_PARENT="/var/lib/omarchy/m2-displayport"

m2dp_die() {
  printf 'REFUSED: %s\n' "$*" >&2
  return 1
}

m2dp_clean() {
  /usr/bin/env -i PATH=/usr/bin:/bin LANG=C.UTF-8 "$@"
}

m2dp_path() {
  local root="$1"
  local path="$2"
  if [[ $root == "/" ]]; then
    printf '%s\n' "$path"
  else
    printf '%s%s\n' "$root" "$path"
  fi
}

m2dp_canonical_existing() {
  local path="$1"
  local actual
  [[ $path == /* && $path != *$'\n'* && $path != *$'\r'* && $path != *\\* ]] || {
    m2dp_die "path must be plain and absolute: $path"
    return 1
  }
  actual=$(m2dp_clean realpath -e -- "$path") || {
    m2dp_die "path does not exist: $path"
    return 1
  }
  [[ $actual == "$path" ]] || {
    m2dp_die "path contains a symlink or noncanonical component: $path"
    return 1
  }
}

m2dp_directory_owned() {
  local path="$1"
  local expected_uid="$2"
  local uid mode
  m2dp_canonical_existing "$path" || return 1
  [[ -d $path && ! -L $path ]] || {
    m2dp_die "not a real directory: $path"
    return 1
  }
  read -r uid mode <<<"$(m2dp_clean stat -c '%u %a' -- "$path")"
  [[ $uid == "$expected_uid" ]] || {
    m2dp_die "wrong directory owner: $path"
    return 1
  }
  (( (8#$mode & 0022) == 0 )) || {
    m2dp_die "directory permits group or world writes: $path"
    return 1
  }
}

m2dp_regular_file() {
  local path="$1"
  m2dp_canonical_existing "$path" || return 1
  [[ -f $path && ! -L $path ]] || {
    m2dp_die "not a regular file: $path"
    return 1
  }
}

m2dp_verify_file() {
  local path="$1"
  local expected_sha="$2"
  local expected_size="$3"
  local actual
  [[ $expected_sha =~ ^[0-9a-f]{64}$ && $expected_size =~ ^[1-9][0-9]*$ ]] || {
    m2dp_die "invalid expected file identity"
    return 1
  }
  m2dp_regular_file "$path" || return 1
  [[ $(m2dp_clean stat -c '%s' -- "$path") == "$expected_size" ]] || {
    m2dp_die "file size mismatch: $path"
    return 1
  }
  actual=$(m2dp_clean sha256sum -- "$path") || return 1
  [[ ${actual%% *} == "$expected_sha" ]] || {
    m2dp_die "file checksum mismatch: $path"
    return 1
  }
}

m2dp_absent() {
  [[ ! -e $1 && ! -L $1 ]] || {
    m2dp_die "path already exists and will not be overwritten: $1"
    return 1
  }
}

m2dp_copy_new() (
  set -Eeuo pipefail
  local source="$1"
  local destination="$2"
  local sha="$3"
  local size="$4"
  local mode="$5"
  local parent="${destination%/*}"
  local temporary="" published=0
  trap '
    copy_status=$?
    if (( copy_status != 0 )); then
      if [[ -n $temporary && ( -e $temporary || -L $temporary ) ]]; then
        m2dp_clean rm -f -- "$temporary" || true
      fi
      if (( published == 1 )) && [[ -e $destination || -L $destination ]]; then
        m2dp_clean rm -f -- "$destination" || true
      fi
    fi
    exit "$copy_status"
  ' EXIT
  m2dp_verify_file "$source" "$sha" "$size" || return 1
  m2dp_canonical_existing "$parent" || return 1
  [[ -d $parent && ! -L $parent ]] || return 1
  m2dp_absent "$destination" || return 1
  temporary=$(m2dp_clean mktemp --tmpdir="$parent" ".${destination##*/}.m2dp-copy.XXXXXXXXXX") || return 1
  m2dp_regular_file "$temporary" || return 1
  m2dp_clean /usr/bin/dd if="$source" of="$temporary" bs=1M count="$size" \
    iflag=fullblock,count_bytes,nofollow oflag=nofollow conv=fsync,notrunc status=none || {
    m2dp_die "copy failed: $temporary"
    return 1
  }
  m2dp_clean chmod "$mode" -- "$temporary" || return 1
  m2dp_verify_file "$temporary" "$sha" "$size" || return 1
  m2dp_verify_file "$source" "$sha" "$size" || return 1
  m2dp_clean /usr/bin/mv --no-copy --update=none-fail -T -- "$temporary" "$destination" || return 1
  published=1
  temporary=""
  m2dp_verify_file "$destination" "$sha" "$size" || return 1
  m2dp_verify_file "$source" "$sha" "$size" || return 1
  trap - EXIT
)

m2dp_verify_host_tree() {
  local root="$1"
  local running_kernel="$2"
  local kernel_package="$3"
  local compatible status
  local compatible_path status_path override_path lock_path active_boot default_image
  compatible_path=$(m2dp_path "$root" /proc/device-tree/compatible)
  status_path=$(m2dp_path "$root" /proc/device-tree/soc/dcp@271c00000/status)
  override_path=$(m2dp_path "$root" /etc/default/update-m1n1)
  lock_path=$(m2dp_path "$root" /var/lib/pacman/db.lck)
  active_boot=$(m2dp_path "$root" "$M2DP_ACTIVE_BOOT_PATH")
  default_image=$(m2dp_path "$root" /boot/initramfs-linux-asahi.img)
  [[ $running_kernel == "$M2DP_KERNEL_RELEASE" ]] || {
    m2dp_die "running kernel is unsupported: $running_kernel"
    return 1
  }
  [[ $kernel_package == "$M2DP_KERNEL_PACKAGE" ]] || {
    m2dp_die "installed kernel package is unsupported: $kernel_package"
    return 1
  }
  [[ -r $compatible_path ]] || {
    m2dp_die "device-tree compatible data is unreadable"
    return 1
  }
  compatible=$(m2dp_clean tr '\0' '\n' <"$compatible_path")
  m2dp_clean grep -Fxq apple,j413 <<<"$compatible" &&
    m2dp_clean grep -Fxq apple,t8112 <<<"$compatible" || {
    m2dp_die "only Apple J413/T8112 is supported"
    return 1
  }
  [[ -r $status_path ]] || {
    m2dp_die "external DCP status is unreadable"
    return 1
  }
  status=$(m2dp_clean tr -d '\0' <"$status_path")
  [[ $status == "disabled" || $status == "okay" ]] || {
    m2dp_die "external DCP has an unexpected status: $status"
    return 1
  }
  [[ ! -e $override_path && ! -L $override_path ]] || {
    m2dp_die "persistent update-m1n1 override exists"
    return 1
  }
  [[ ! -e $lock_path && ! -L $lock_path ]] || {
    m2dp_die "a package transaction is active"
    return 1
  }
  m2dp_regular_file "$active_boot" || return 1
  m2dp_regular_file "$default_image" || return 1
}

m2dp_reset_bundle_fields() {
  M2DP_BUNDLE_FORMAT=""
  M2DP_BUNDLE_COMPATIBLE=""
  M2DP_BUNDLE_SOC=""
  M2DP_BUNDLE_KERNEL_RELEASE=""
  M2DP_BUNDLE_KERNEL_PACKAGE=""
  M2DP_BUNDLE_BOOT_SHA=""
  M2DP_BUNDLE_BOOT_SIZE=""
  M2DP_BUNDLE_IMAGE_SHA=""
  M2DP_BUNDLE_IMAGE_SIZE=""
  M2DP_BUNDLE_MODULE_SHA=""
  M2DP_BUNDLE_MODULE_BUILD_ID=""
  M2DP_BUNDLE_MANIFEST_SHA=""
  M2DP_BUNDLE_MANIFEST_SIZE=""
}

m2dp_read_bundle_manifest() {
  local manifest="$1"
  local line key value seen="|" count=0
  m2dp_reset_bundle_fields
  m2dp_regular_file "$manifest" || return 1
  while IFS= read -r line || [[ -n $line ]]; do
    [[ $line == *=* && $line != *$'\r'* ]] || {
      m2dp_die "invalid bundle manifest line"
      return 1
    }
    key=${line%%=*}
    value=${line#*=}
    [[ $seen != *"|$key|"* ]] || {
      m2dp_die "duplicate bundle manifest field: $key"
      return 1
    }
    seen+="$key|"
    (( count += 1 ))
    case "$key" in
      format) M2DP_BUNDLE_FORMAT="$value" ;;
      compatible) M2DP_BUNDLE_COMPATIBLE="$value" ;;
      soc) M2DP_BUNDLE_SOC="$value" ;;
      kernel_release) M2DP_BUNDLE_KERNEL_RELEASE="$value" ;;
      kernel_package) M2DP_BUNDLE_KERNEL_PACKAGE="$value" ;;
      boot_sha256) M2DP_BUNDLE_BOOT_SHA="$value" ;;
      boot_size) M2DP_BUNDLE_BOOT_SIZE="$value" ;;
      image_sha256) M2DP_BUNDLE_IMAGE_SHA="$value" ;;
      image_size) M2DP_BUNDLE_IMAGE_SIZE="$value" ;;
      module_sha256) M2DP_BUNDLE_MODULE_SHA="$value" ;;
      module_build_id) M2DP_BUNDLE_MODULE_BUILD_ID="$value" ;;
      *)
        m2dp_die "unknown bundle manifest field: $key"
        return 1
        ;;
    esac
  done <"$manifest"
  (( count == 11 )) || {
    m2dp_die "bundle manifest field count is $count, expected 11"
    return 1
  }
  [[ $M2DP_BUNDLE_FORMAT == "1" && $M2DP_BUNDLE_COMPATIBLE == "apple,j413" &&
    $M2DP_BUNDLE_SOC == "apple,t8112" && $M2DP_BUNDLE_KERNEL_RELEASE == "$M2DP_KERNEL_RELEASE" &&
    $M2DP_BUNDLE_KERNEL_PACKAGE == "$M2DP_KERNEL_PACKAGE" ]] || {
    m2dp_die "bundle platform identity is unsupported"
    return 1
  }
  [[ $M2DP_BUNDLE_BOOT_SHA =~ ^[0-9a-f]{64}$ && $M2DP_BUNDLE_IMAGE_SHA =~ ^[0-9a-f]{64}$ &&
    $M2DP_BUNDLE_MODULE_SHA =~ ^[0-9a-f]{64}$ && $M2DP_BUNDLE_MODULE_BUILD_ID =~ ^[0-9a-f]{40}$ &&
    $M2DP_BUNDLE_BOOT_SIZE =~ ^[1-9][0-9]*$ && $M2DP_BUNDLE_IMAGE_SIZE =~ ^[1-9][0-9]*$ ]] || {
    m2dp_die "bundle file identity is malformed"
    return 1
  }
  M2DP_BUNDLE_MANIFEST_SHA=$(m2dp_clean sha256sum -- "$manifest") || return 1
  M2DP_BUNDLE_MANIFEST_SHA=${M2DP_BUNDLE_MANIFEST_SHA%% *}
  M2DP_BUNDLE_MANIFEST_SIZE=$(m2dp_clean stat -c '%s' -- "$manifest")
}

m2dp_validate_bundle_contents() {
  local bundle="$1"
  local expected_boot_sha="$2"
  local expected_image_sha="$3"
  local expected_image_size="$4"
  local expected_module_sha="$5"
  local expected_build_id="$6"
  m2dp_canonical_existing "$bundle" || return 1
  [[ -d $bundle && ! -L $bundle ]] || {
    m2dp_die "bundle is not a real directory"
    return 1
  }
  m2dp_read_bundle_manifest "$bundle/bundle.env" || return 1
  [[ $M2DP_BUNDLE_BOOT_SHA == "$expected_boot_sha" &&
    $M2DP_BUNDLE_IMAGE_SHA == "$expected_image_sha" &&
    $M2DP_BUNDLE_IMAGE_SIZE == "$expected_image_size" &&
    $M2DP_BUNDLE_MODULE_SHA == "$expected_module_sha" &&
    $M2DP_BUNDLE_MODULE_BUILD_ID == "$expected_build_id" ]] || {
    m2dp_die "bundle release pins do not match this integration"
    return 1
  }
  m2dp_verify_file "$bundle/candidate-boot.bin" "$M2DP_BUNDLE_BOOT_SHA" "$M2DP_BUNDLE_BOOT_SIZE" || return 1
  m2dp_verify_file "$bundle/candidate-initramfs.img" "$M2DP_BUNDLE_IMAGE_SHA" "$M2DP_BUNDLE_IMAGE_SIZE" || return 1
  m2dp_verify_file "$bundle/bundle.env" "$M2DP_BUNDLE_MANIFEST_SHA" "$M2DP_BUNDLE_MANIFEST_SIZE" || return 1
}

m2dp_validate_bundle() {
  local bundle="$1"
  m2dp_regular_file "$bundle/PREPARED" || return 1
  [[ $(m2dp_clean stat -c '%s' -- "$bundle/PREPARED") == "9" ]] &&
    m2dp_clean grep -Fxq PREPARED "$bundle/PREPARED" || {
    m2dp_die "bundle readiness receipt is invalid"
    return 1
  }
  m2dp_absent "$bundle/INCOMPLETE" || return 1
  m2dp_validate_bundle_contents "$@"
}

m2dp_write_state() {
  local destination="$1"
  local timestamp="$2"
  local previous_sha="$3"
  local previous_size="$4"
  local previous_mode="$5"
  local hook_sha="$6"
  local changed="$7"
  local hook_parent_created="$8"
  local backup_name="boot.bin.pre-omarchy-m2-displayport-$timestamp"
  printf '%s\n' \
    'format=1' \
    "timestamp=$timestamp" \
    "kernel_release=$M2DP_KERNEL_RELEASE" \
    "previous_boot_sha256=$previous_sha" \
    "previous_boot_size=$previous_size" \
    "previous_boot_mode=$previous_mode" \
    "candidate_boot_sha256=$M2DP_BUNDLE_BOOT_SHA" \
    "candidate_boot_size=$M2DP_BUNDLE_BOOT_SIZE" \
    "candidate_image_sha256=$M2DP_BUNDLE_IMAGE_SHA" \
    "candidate_image_size=$M2DP_BUNDLE_IMAGE_SIZE" \
    "hook_sha256=$hook_sha" \
    "hook_parent_created=$hook_parent_created" \
    "active_boot_changed=$changed" \
    "efi_backup_name=$backup_name" >"$destination"
  m2dp_clean chmod 0600 "$destination"
}

m2dp_write_recovery_guide() {
  local destination="$1"
  local timestamp="$2"
  local previous_sha="$3"
  local backup_name="boot.bin.pre-omarchy-m2-displayport-$timestamp"
  printf '%s\n' \
    'Omarchy M2 DisplayPort recovery' \
    '' \
    "Pre-install boot SHA-256: $previous_sha" \
    "EFI backup: m1n1/$backup_name" \
    '' \
    'Linux rollback:' \
    'sudo /usr/bin/bash /path/to/integration.sh rollback' \
    '' \
    'macOS or macOS Recovery Terminal:' \
    'Mount the Linux EFI System Partition read-write.' \
    'Change to its m1n1 directory.' \
    "Verify: shasum -a 256 '$backup_name'" \
    "Copy: cp '$backup_name' '.boot.bin.omarchy-m2-displayport-restore.tmp'" \
    "Verify: shasum -a 256 '.boot.bin.omarchy-m2-displayport-restore.tmp'" \
    "Replace: mv -f '.boot.bin.omarchy-m2-displayport-restore.tmp' 'boot.bin'" \
    'Run sync, unmount the EFI partition, and restart.' \
    'Both verification results must equal the recorded pre-install SHA-256.' >"$destination"
  m2dp_clean chmod 0600 "$destination"
}

m2dp_stage_files() (
  set -Eeuo pipefail
  umask 077
  local root="$1"
  local bundle="$2"
  local timestamp="$3"
  local bundle_uid="$4"
  local expected_boot_sha="$5"
  local expected_image_sha="$6"
  local expected_image_size="$7"
  local expected_module_sha="$8"
  local expected_build_id="$9"
  local hook_template="${10}"
  local expected_previous_sha="${11}"
  local system_uid active_boot image_path hook_path state_parent active_state staging_state
  local efi_dir efi_backup recovery_guide hook_sha hook_size previous_sha previous_size changed
  local recovery_sha recovery_size
  local previous_mode
  local hook_parent hook_parent_needed=0 hook_parent_created=0 lock_path
  local image_created=0 hook_created=0 state_published=0 boot_tmp
  [[ $timestamp =~ ^[0-9]{8}T[0-9]{6}Z$ ]] || {
    m2dp_die "invalid staging timestamp"
    return 1
  }
  system_uid=$(m2dp_clean stat -c '%u' -- "$root")
  m2dp_directory_owned "$bundle" "$bundle_uid" || return 1
  m2dp_validate_bundle "$bundle" "$expected_boot_sha" "$expected_image_sha" "$expected_image_size" \
    "$expected_module_sha" "$expected_build_id" || return 1
  m2dp_regular_file "$hook_template" || return 1
  hook_sha=$(m2dp_clean sha256sum -- "$hook_template")
  hook_sha=${hook_sha%% *}
  hook_size=$(m2dp_clean stat -c '%s' -- "$hook_template")
  [[ $hook_sha == "$M2DP_HOOK_SHA256" && $hook_size == "$M2DP_HOOK_SIZE" ]] || {
    m2dp_die "package guard differs from the accepted release"
    return 1
  }
  active_boot=$(m2dp_path "$root" "$M2DP_ACTIVE_BOOT_PATH")
  image_path=$(m2dp_path "$root" "$M2DP_IMAGE_PATH")
  hook_path=$(m2dp_path "$root" "$M2DP_HOOK_PATH")
  hook_parent=${hook_path%/*}
  state_parent=$(m2dp_path "$root" "$M2DP_STATE_PARENT")
  lock_path=$(m2dp_path "$root" /var/lib/pacman/db.lck)
  active_state="$state_parent/active"
  staging_state="$state_parent/.staging-$timestamp"
  efi_dir="${active_boot%/*}"
  efi_backup="$efi_dir/boot.bin.pre-omarchy-m2-displayport-$timestamp"
  recovery_guide="$efi_dir/RECOVERY-OMARCHY-M2-DISPLAYPORT-$timestamp.txt"
  boot_tmp="$efi_dir/.boot.bin.omarchy-m2-displayport-$timestamp.tmp"
  if [[ ! -e $state_parent && ! -L $state_parent ]]; then
    m2dp_directory_owned "${state_parent%/*}" "$system_uid" || return 1
    m2dp_clean mkdir -m 0700 -- "$state_parent"
  fi
  m2dp_directory_owned "$state_parent" "$system_uid" || return 1
  m2dp_directory_owned "${image_path%/*}" "$system_uid" || return 1
  if [[ -e $hook_parent || -L $hook_parent ]]; then
    m2dp_directory_owned "$hook_parent" "$system_uid" || return 1
  else
    m2dp_directory_owned "${hook_parent%/*}" "$system_uid" || return 1
    hook_parent_needed=1
  fi
  m2dp_directory_owned "$efi_dir" "$system_uid" || return 1
  m2dp_regular_file "$active_boot" || return 1
  m2dp_absent "$active_state" || return 1
  m2dp_absent "$staging_state" || return 1
  m2dp_absent "$image_path" || return 1
  m2dp_absent "$hook_path" || return 1
  m2dp_absent "$efi_backup" || return 1
  m2dp_absent "$recovery_guide" || return 1
  m2dp_absent "$boot_tmp" || return 1
  m2dp_absent "$lock_path" || return 1
  previous_sha=$(m2dp_clean sha256sum -- "$active_boot")
  previous_sha=${previous_sha%% *}
  previous_size=$(m2dp_clean stat -c '%s' -- "$active_boot")
  previous_mode=$(m2dp_clean stat -c '%a' -- "$active_boot")
  [[ $previous_sha == "$expected_previous_sha" ]] || {
    m2dp_die "active boot changed after the release gate"
    return 1
  }
  [[ $previous_size =~ ^[1-9][0-9]*$ ]]
  [[ $previous_mode =~ ^[0-7]{3,4}$ ]]
  changed=1
  [[ $previous_sha != "$M2DP_BUNDLE_BOOT_SHA" ]] || changed=0
  m2dp_clean mkdir -m 0700 -- "$staging_state"
  trap '
    stage_status=$?
    if (( stage_status != 0 )); then
      if (( state_published == 0 )); then
        if (( hook_created == 1 )) && m2dp_verify_file "$hook_path" "$hook_sha" "$hook_size" >/dev/null 2>&1; then
          m2dp_clean rm -- "$hook_path" || true
        fi
        if (( hook_parent_created == 1 )); then
          m2dp_clean rmdir -- "$hook_parent" >/dev/null 2>&1 || true
        fi
        if (( image_created == 1 )) && m2dp_verify_file "$image_path" "$M2DP_BUNDLE_IMAGE_SHA" "$M2DP_BUNDLE_IMAGE_SIZE" >/dev/null 2>&1; then
          m2dp_clean rm -- "$image_path" || true
        fi
        printf "STAGING FAILED. Pre-install evidence remains at %s\n" "$staging_state" >&2
      else
        printf "STAGING FAILED AFTER ROLLBACK STATE WAS PUBLISHED. Run the rollback command before retrying.\n" >&2
        printf "Recovery copies remain at %s and %s.\n" "$efi_backup" "$recovery_guide" >&2
      fi
    fi
    exit "$stage_status"
  ' EXIT
  m2dp_copy_new "$active_boot" "$staging_state/pre-install-boot.bin" "$previous_sha" "$previous_size" 0600
  m2dp_copy_new "$active_boot" "$efi_backup" "$previous_sha" "$previous_size" 0644
  if (( hook_parent_needed == 1 )); then
    m2dp_clean mkdir -m 0755 -- "$hook_parent"
    hook_parent_created=1
  fi
  m2dp_write_state "$staging_state/state.env" "$timestamp" "$previous_sha" "$previous_size" "$previous_mode" "$hook_sha" "$changed" "$hook_parent_created"
  m2dp_write_recovery_guide "$staging_state/recovery.txt" "$timestamp" "$previous_sha"
  recovery_sha=$(m2dp_clean sha256sum -- "$staging_state/recovery.txt")
  recovery_sha=${recovery_sha%% *}
  recovery_size=$(m2dp_clean stat -c '%s' -- "$staging_state/recovery.txt")
  m2dp_copy_new "$staging_state/recovery.txt" "$recovery_guide" "$recovery_sha" "$recovery_size" 0644
  m2dp_copy_new "$bundle/bundle.env" "$staging_state/bundle.env" "$M2DP_BUNDLE_MANIFEST_SHA" "$M2DP_BUNDLE_MANIFEST_SIZE" 0600
  m2dp_copy_new "$bundle/candidate-boot.bin" "$staging_state/candidate-boot.bin" "$M2DP_BUNDLE_BOOT_SHA" "$M2DP_BUNDLE_BOOT_SIZE" 0600
  m2dp_copy_new "$bundle/candidate-initramfs.img" "$image_path" "$M2DP_BUNDLE_IMAGE_SHA" "$M2DP_BUNDLE_IMAGE_SIZE" 0600
  image_created=1
  m2dp_copy_new "$hook_template" "$hook_path" "$hook_sha" "$hook_size" 0644
  hook_created=1
  m2dp_absent "$lock_path"
  if [[ $root == "/" ]]; then
    m2dp_verify_live_host
  fi
  m2dp_verify_file "$active_boot" "$previous_sha" "$previous_size"
  m2dp_validate_bundle "$bundle" "$expected_boot_sha" "$expected_image_sha" "$expected_image_size" \
    "$expected_module_sha" "$expected_build_id"
  printf 'PREPARED\n' >"$staging_state/RESULT"
  m2dp_clean chmod 0600 "$staging_state/RESULT"
  m2dp_clean sync -f "$image_path"
  m2dp_clean sync -f "$hook_path"
  m2dp_clean sync -f "$staging_state/state.env"
  m2dp_clean sync -f "$staging_state/pre-install-boot.bin"
  m2dp_clean sync -f "$staging_state/candidate-boot.bin"
  m2dp_clean sync -f "$staging_state/RESULT"
  m2dp_clean sync -f "$efi_backup"
  m2dp_clean sync -f "$recovery_guide"
  m2dp_clean /usr/bin/mv --no-copy --update=none-fail -T -- "$staging_state" "$active_state"
  state_published=1
  m2dp_clean sync -f "$active_state/RESULT"
  trap - EXIT
  printf 'PREPARATION PASS: %s\n' "$image_path"
)

m2dp_reset_state_fields() {
  M2DP_STATE_FORMAT=""
  M2DP_STATE_TIMESTAMP=""
  M2DP_STATE_KERNEL=""
  M2DP_STATE_PREVIOUS_SHA=""
  M2DP_STATE_PREVIOUS_SIZE=""
  M2DP_STATE_PREVIOUS_MODE=""
  M2DP_STATE_CANDIDATE_BOOT_SHA=""
  M2DP_STATE_CANDIDATE_BOOT_SIZE=""
  M2DP_STATE_CANDIDATE_IMAGE_SHA=""
  M2DP_STATE_CANDIDATE_IMAGE_SIZE=""
  M2DP_STATE_HOOK_SHA=""
  M2DP_STATE_HOOK_PARENT_CREATED=""
  M2DP_STATE_BOOT_CHANGED=""
  M2DP_STATE_EFI_BACKUP_NAME=""
}

m2dp_read_state() {
  local path="$1"
  local line key value seen="|" count=0
  m2dp_reset_state_fields
  m2dp_regular_file "$path" || return 1
  while IFS= read -r line || [[ -n $line ]]; do
    [[ $line == *=* && $line != *$'\r'* ]] || return 1
    key=${line%%=*}
    value=${line#*=}
    [[ $seen != *"|$key|"* ]] || return 1
    seen+="$key|"
    (( count += 1 ))
    case "$key" in
      format) M2DP_STATE_FORMAT="$value" ;;
      timestamp) M2DP_STATE_TIMESTAMP="$value" ;;
      kernel_release) M2DP_STATE_KERNEL="$value" ;;
      previous_boot_sha256) M2DP_STATE_PREVIOUS_SHA="$value" ;;
      previous_boot_size) M2DP_STATE_PREVIOUS_SIZE="$value" ;;
      previous_boot_mode) M2DP_STATE_PREVIOUS_MODE="$value" ;;
      candidate_boot_sha256) M2DP_STATE_CANDIDATE_BOOT_SHA="$value" ;;
      candidate_boot_size) M2DP_STATE_CANDIDATE_BOOT_SIZE="$value" ;;
      candidate_image_sha256) M2DP_STATE_CANDIDATE_IMAGE_SHA="$value" ;;
      candidate_image_size) M2DP_STATE_CANDIDATE_IMAGE_SIZE="$value" ;;
      hook_sha256) M2DP_STATE_HOOK_SHA="$value" ;;
      hook_parent_created) M2DP_STATE_HOOK_PARENT_CREATED="$value" ;;
      active_boot_changed) M2DP_STATE_BOOT_CHANGED="$value" ;;
      efi_backup_name) M2DP_STATE_EFI_BACKUP_NAME="$value" ;;
      *) return 1 ;;
    esac
  done <"$path"
  (( count == 14 )) || return 1
  [[ $M2DP_STATE_FORMAT == "1" && $M2DP_STATE_KERNEL == "$M2DP_KERNEL_RELEASE" &&
    $M2DP_STATE_TIMESTAMP =~ ^[0-9]{8}T[0-9]{6}Z$ &&
    $M2DP_STATE_PREVIOUS_SHA =~ ^[0-9a-f]{64}$ && $M2DP_STATE_CANDIDATE_BOOT_SHA =~ ^[0-9a-f]{64}$ &&
    $M2DP_STATE_CANDIDATE_IMAGE_SHA =~ ^[0-9a-f]{64}$ && $M2DP_STATE_HOOK_SHA =~ ^[0-9a-f]{64}$ &&
    $M2DP_STATE_PREVIOUS_SIZE =~ ^[1-9][0-9]*$ && $M2DP_STATE_PREVIOUS_MODE =~ ^[0-7]{3,4}$ &&
    $M2DP_STATE_CANDIDATE_BOOT_SIZE =~ ^[1-9][0-9]*$ &&
    $M2DP_STATE_CANDIDATE_IMAGE_SIZE =~ ^[1-9][0-9]*$ && $M2DP_STATE_HOOK_PARENT_CREATED =~ ^[01]$ &&
    $M2DP_STATE_BOOT_CHANGED =~ ^[01]$ &&
    $M2DP_STATE_EFI_BACKUP_NAME == "boot.bin.pre-omarchy-m2-displayport-$M2DP_STATE_TIMESTAMP" ]] || return 1
}

m2dp_activate_files() (
  set -Eeuo pipefail
  umask 077
  local root="$1"
  local expected_uid="$2"
  local active_boot image_path hook_path state_parent active_state efi_backup recovery_guide lock_path
  local boot_tmp result_tmp current_sha current_size hook_size recovery_sha recovery_size result result_size
  active_boot=$(m2dp_path "$root" "$M2DP_ACTIVE_BOOT_PATH")
  image_path=$(m2dp_path "$root" "$M2DP_IMAGE_PATH")
  hook_path=$(m2dp_path "$root" "$M2DP_HOOK_PATH")
  state_parent=$(m2dp_path "$root" "$M2DP_STATE_PARENT")
  lock_path=$(m2dp_path "$root" /var/lib/pacman/db.lck)
  active_state="$state_parent/active"
  m2dp_directory_owned "$active_state" "$expected_uid" || return 1
  m2dp_read_state "$active_state/state.env" || {
    m2dp_die "activation state is invalid"
    return 1
  }
  efi_backup="${active_boot%/*}/$M2DP_STATE_EFI_BACKUP_NAME"
  recovery_guide="${active_boot%/*}/RECOVERY-OMARCHY-M2-DISPLAYPORT-$M2DP_STATE_TIMESTAMP.txt"
  boot_tmp="${active_boot%/*}/.boot.bin.omarchy-m2-displayport-$M2DP_STATE_TIMESTAMP.tmp"
  result_tmp="$active_state/.RESULT.tmp"
  m2dp_regular_file "$active_state/RESULT" || return 1
  result=$(<"$active_state/RESULT")
  result_size=$(m2dp_clean stat -c '%s' -- "$active_state/RESULT")
  [[ $result == "PREPARED" && $result_size == "9" ]] || {
    m2dp_die "only a prepared candidate can be activated"
    return 1
  }
  m2dp_verify_file "$active_state/pre-install-boot.bin" "$M2DP_STATE_PREVIOUS_SHA" "$M2DP_STATE_PREVIOUS_SIZE" || return 1
  m2dp_verify_file "$active_state/candidate-boot.bin" "$M2DP_STATE_CANDIDATE_BOOT_SHA" "$M2DP_STATE_CANDIDATE_BOOT_SIZE" || return 1
  m2dp_verify_file "$efi_backup" "$M2DP_STATE_PREVIOUS_SHA" "$M2DP_STATE_PREVIOUS_SIZE" || return 1
  m2dp_regular_file "$active_state/recovery.txt" || return 1
  recovery_sha=$(m2dp_clean sha256sum -- "$active_state/recovery.txt")
  recovery_sha=${recovery_sha%% *}
  recovery_size=$(m2dp_clean stat -c '%s' -- "$active_state/recovery.txt")
  m2dp_verify_file "$recovery_guide" "$recovery_sha" "$recovery_size" || return 1
  m2dp_verify_file "$image_path" "$M2DP_STATE_CANDIDATE_IMAGE_SHA" "$M2DP_STATE_CANDIDATE_IMAGE_SIZE" || return 1
  hook_size=$(m2dp_clean stat -c '%s' -- "$hook_path")
  m2dp_verify_file "$hook_path" "$M2DP_STATE_HOOK_SHA" "$hook_size" || return 1
  m2dp_absent "$lock_path" || return 1
  m2dp_regular_file "$active_boot" || return 1
  current_sha=$(m2dp_clean sha256sum -- "$active_boot")
  current_sha=${current_sha%% *}
  current_size=$(m2dp_clean stat -c '%s' -- "$active_boot")
  if (( M2DP_STATE_BOOT_CHANGED == 1 )); then
    [[ $current_sha == "$M2DP_STATE_PREVIOUS_SHA" || $current_sha == "$M2DP_STATE_CANDIDATE_BOOT_SHA" ]] || {
      m2dp_die "active boot differs from both prepared identities"
      return 1
    }
  else
    [[ $current_sha == "$M2DP_STATE_PREVIOUS_SHA" && $current_size == "$M2DP_STATE_PREVIOUS_SIZE" ]] || {
      m2dp_die "unchanged active boot drifted"
      return 1
    }
  fi
  if [[ $root == "/" ]]; then
    m2dp_verify_live_host
  fi
  m2dp_absent "$lock_path"
  m2dp_clean sync -f "$active_state/RESULT"
  m2dp_clean sync -f "$efi_backup"
  m2dp_clean sync -f "$recovery_guide"
  m2dp_verify_file "$active_state/pre-install-boot.bin" "$M2DP_STATE_PREVIOUS_SHA" "$M2DP_STATE_PREVIOUS_SIZE"
  m2dp_verify_file "$efi_backup" "$M2DP_STATE_PREVIOUS_SHA" "$M2DP_STATE_PREVIOUS_SIZE"
  m2dp_verify_file "$recovery_guide" "$recovery_sha" "$recovery_size"
  m2dp_verify_file "$active_boot" "$current_sha" "$current_size"
  if (( M2DP_STATE_BOOT_CHANGED == 1 )) && [[ $current_sha == "$M2DP_STATE_PREVIOUS_SHA" ]]; then
    if [[ -e $boot_tmp || -L $boot_tmp ]]; then
      m2dp_verify_file "$boot_tmp" "$M2DP_STATE_CANDIDATE_BOOT_SHA" "$M2DP_STATE_CANDIDATE_BOOT_SIZE"
    else
      m2dp_copy_new "$active_state/candidate-boot.bin" "$boot_tmp" "$M2DP_STATE_CANDIDATE_BOOT_SHA" "$M2DP_STATE_CANDIDATE_BOOT_SIZE" 0755
    fi
    m2dp_clean /usr/bin/mv --no-copy -f -T -- "$boot_tmp" "$active_boot"
  elif [[ -e $boot_tmp || -L $boot_tmp ]]; then
    m2dp_verify_file "$boot_tmp" "$M2DP_STATE_CANDIDATE_BOOT_SHA" "$M2DP_STATE_CANDIDATE_BOOT_SIZE"
    m2dp_clean rm -- "$boot_tmp"
  fi
  m2dp_verify_file "$active_boot" "$M2DP_STATE_CANDIDATE_BOOT_SHA" "$M2DP_STATE_CANDIDATE_BOOT_SIZE"
  m2dp_clean sync -f "$active_boot"
  m2dp_verify_file "$active_boot" "$M2DP_STATE_CANDIDATE_BOOT_SHA" "$M2DP_STATE_CANDIDATE_BOOT_SIZE"
  if [[ -e $result_tmp || -L $result_tmp ]]; then
    m2dp_regular_file "$result_tmp" || return 1
    [[ $(m2dp_clean stat -c '%s' -- "$result_tmp") == "7" ]] &&
      m2dp_clean grep -Fxq STAGED "$result_tmp" || return 1
  else
    printf 'STAGED\n' >"$result_tmp"
    m2dp_clean chmod 0600 "$result_tmp"
    m2dp_clean sync -f "$result_tmp"
  fi
  m2dp_clean /usr/bin/mv --no-copy -f -T -- "$result_tmp" "$active_state/RESULT"
  m2dp_clean sync -f "$active_state/RESULT"
  printf 'ACTIVATION PASS: %s\n' "$active_boot"
)

m2dp_rollback_files() (
  set -Eeuo pipefail
  umask 077
  local root="$1"
  local expected_uid="$2"
  local active_boot image_path hook_path state_parent active_state rolled_state efi_backup
  local current_sha current_size hook_size boot_tmp stage_boot_tmp result result_size
  active_boot=$(m2dp_path "$root" "$M2DP_ACTIVE_BOOT_PATH")
  image_path=$(m2dp_path "$root" "$M2DP_IMAGE_PATH")
  hook_path=$(m2dp_path "$root" "$M2DP_HOOK_PATH")
  state_parent=$(m2dp_path "$root" "$M2DP_STATE_PARENT")
  active_state="$state_parent/active"
  m2dp_directory_owned "$active_state" "$expected_uid" || return 1
  m2dp_read_state "$active_state/state.env" || {
    m2dp_die "rollback state is invalid"
    return 1
  }
  rolled_state="$state_parent/rolled-back-$M2DP_STATE_TIMESTAMP"
  efi_backup="${active_boot%/*}/$M2DP_STATE_EFI_BACKUP_NAME"
  boot_tmp="${active_boot%/*}/.boot.bin.omarchy-m2-displayport-rollback-$M2DP_STATE_TIMESTAMP.tmp"
  stage_boot_tmp="${active_boot%/*}/.boot.bin.omarchy-m2-displayport-$M2DP_STATE_TIMESTAMP.tmp"
  m2dp_absent "$rolled_state" || return 1
  m2dp_absent "$boot_tmp" || return 1
  m2dp_regular_file "$active_state/RESULT" || return 1
  result=$(<"$active_state/RESULT")
  result_size=$(m2dp_clean stat -c '%s' -- "$active_state/RESULT")
  [[ ( $result == "PREPARED" && $result_size == "9" ) ||
    ( $result == "STAGED" && $result_size == "7" ) ]] || {
    m2dp_die "rollback phase is invalid"
    return 1
  }
  m2dp_verify_file "$active_state/pre-install-boot.bin" "$M2DP_STATE_PREVIOUS_SHA" "$M2DP_STATE_PREVIOUS_SIZE" || return 1
  m2dp_verify_file "$active_state/candidate-boot.bin" "$M2DP_STATE_CANDIDATE_BOOT_SHA" "$M2DP_STATE_CANDIDATE_BOOT_SIZE" || return 1
  m2dp_verify_file "$efi_backup" "$M2DP_STATE_PREVIOUS_SHA" "$M2DP_STATE_PREVIOUS_SIZE" || return 1
  if [[ -e $stage_boot_tmp || -L $stage_boot_tmp ]]; then
    m2dp_verify_file "$stage_boot_tmp" "$M2DP_STATE_CANDIDATE_BOOT_SHA" "$M2DP_STATE_CANDIDATE_BOOT_SIZE" || return 1
  fi
  if [[ -e $hook_path || -L $hook_path ]]; then
    m2dp_regular_file "$hook_path" || return 1
    hook_size=$(m2dp_clean stat -c '%s' -- "$hook_path")
    m2dp_verify_file "$hook_path" "$M2DP_STATE_HOOK_SHA" "$hook_size" || return 1
  fi
  if [[ -e $image_path || -L $image_path ]]; then
    m2dp_verify_file "$image_path" "$M2DP_STATE_CANDIDATE_IMAGE_SHA" "$M2DP_STATE_CANDIDATE_IMAGE_SIZE" || return 1
  fi
  m2dp_regular_file "$active_boot" || return 1
  current_sha=$(m2dp_clean sha256sum -- "$active_boot")
  current_sha=${current_sha%% *}
  current_size=$(m2dp_clean stat -c '%s' -- "$active_boot")
  if (( M2DP_STATE_BOOT_CHANGED == 1 )); then
    [[ $current_sha == "$M2DP_STATE_CANDIDATE_BOOT_SHA" || $current_sha == "$M2DP_STATE_PREVIOUS_SHA" ]] || {
      m2dp_die "active boot differs from both candidate and rollback backup"
      return 1
    }
  else
    [[ $current_sha == "$M2DP_STATE_PREVIOUS_SHA" && $current_size == "$M2DP_STATE_PREVIOUS_SIZE" ]] || {
      m2dp_die "unchanged active boot drifted"
      return 1
    }
  fi
  if (( M2DP_STATE_BOOT_CHANGED == 1 )) && [[ $current_sha == "$M2DP_STATE_CANDIDATE_BOOT_SHA" ]]; then
    m2dp_copy_new "$active_state/pre-install-boot.bin" "$boot_tmp" "$M2DP_STATE_PREVIOUS_SHA" "$M2DP_STATE_PREVIOUS_SIZE" "$M2DP_STATE_PREVIOUS_MODE"
    m2dp_clean /usr/bin/mv --no-copy -f -T -- "$boot_tmp" "$active_boot"
    m2dp_verify_file "$active_boot" "$M2DP_STATE_PREVIOUS_SHA" "$M2DP_STATE_PREVIOUS_SIZE"
  fi
  m2dp_verify_file "$active_boot" "$M2DP_STATE_PREVIOUS_SHA" "$M2DP_STATE_PREVIOUS_SIZE"
  m2dp_clean sync -f "$active_boot"
  m2dp_verify_file "$active_boot" "$M2DP_STATE_PREVIOUS_SHA" "$M2DP_STATE_PREVIOUS_SIZE"
  if [[ -e $stage_boot_tmp ]]; then
    m2dp_clean rm -- "$stage_boot_tmp"
  fi
  if [[ -e $hook_path ]]; then
    m2dp_clean rm -- "$hook_path"
  fi
  if (( M2DP_STATE_HOOK_PARENT_CREATED == 1 )) && [[ -d ${hook_path%/*} && ! -L ${hook_path%/*} ]]; then
    m2dp_clean rmdir -- "${hook_path%/*}" || true
  fi
  if [[ -e $image_path ]]; then
    m2dp_clean rm -- "$image_path"
  fi
  m2dp_clean /usr/bin/mv --no-copy --update=none-fail -T -- "$active_state" "$rolled_state"
  printf 'ROLLED BACK\n' >"$rolled_state/RESULT"
  m2dp_clean chmod 0600 "$rolled_state/RESULT"
  m2dp_clean sync -f "$rolled_state/RESULT"
  printf 'ROLLBACK PASS: %s\n' "$rolled_state"
)

m2dp_check_environment() {
  local declaration name
  while IFS= read -r declaration; do
    m2dp_die "exported Bash functions are unsupported: ${declaration##* }"
    return 1
  done < <(declare -Fx)
  while IFS= read -r name; do
    case "$name" in
      BASH_ENV | ENV | LD_PRELOAD | LD_LIBRARY_PATH | BASH_FUNC_* | M2DP_*)
        m2dp_die "unexpected environment override: $name"
        return 1
        ;;
    esac
  done < <(compgen -e)
}

m2dp_verify_live_host() {
  local kernel_package
  kernel_package=$(m2dp_clean pacman -Q linux-asahi) || return 1
  m2dp_verify_host_tree / "$(m2dp_clean uname -r)" "$kernel_package" || return 1
  [[ $(m2dp_clean pacman -Q m1n1) == "$M2DP_M1N1_PACKAGE" ]] || {
    m2dp_die "m1n1 package is unsupported"
    return 1
  }
  [[ $(m2dp_clean pacman -Q uboot-asahi) == "$M2DP_UBOOT_PACKAGE" ]] || {
    m2dp_die "U-Boot package is unsupported"
    return 1
  }
}

m2dp_partner_is_external_usb_c() {
  [[ $1 == *'/0-0038/'* || $1 == *'/0-003f/'* ]]
}

m2dp_boot_input_supported() {
  [[ $1 == "$M2DP_STOCK_BOOT_SHA256" || $1 == "$M2DP_BOOT_SHA256" ]]
}

m2dp_verify_live_safety() {
  local capacity online=0 supply partner resolved
  [[ -r /sys/class/power_supply/macsmc-battery/capacity ]] || {
    m2dp_die "battery capacity is unreadable"
    return 1
  }
  capacity=$(</sys/class/power_supply/macsmc-battery/capacity)
  [[ $capacity =~ ^[0-9]{1,3}$ ]] && (( 10#$capacity >= 50 && 10#$capacity <= 100 )) || {
    m2dp_die "battery must be at least 50 percent"
    return 1
  }
  for supply in /sys/class/power_supply/*; do
    [[ -r $supply/type && -r $supply/online ]] || continue
    [[ $(<"$supply/type") == "Battery" ]] && continue
    [[ $(<"$supply/online") == "1" ]] && online=1
  done
  (( online == 1 )) || {
    m2dp_die "external power is required"
    return 1
  }
  for partner in /sys/class/typec/port*-partner; do
    [[ -e $partner ]] || continue
    resolved=$(m2dp_clean readlink -f -- "$partner") || return 1
    if m2dp_partner_is_external_usb_c "$resolved"; then
      m2dp_die "disconnect every USB-C device before staging or rollback"
      return 1
    fi
  done
}

m2dp_with_writable_esp() {
  local action="$1"
  shift
  local mount_info filesystem target options was_rw=0
  mount_info=$(m2dp_clean findmnt -n -o FSTYPE,TARGET,OPTIONS -T /boot/efi) || return 1
  [[ $mount_info != *$'\n'* ]] || return 1
  read -r filesystem target options <<<"$mount_info"
  [[ $filesystem == "vfat" && $target == "/boot/efi" ]] || {
    m2dp_die "the m1n1 EFI filesystem is not the expected vfat mount"
    return 1
  }
  [[ ,$options, != *,rw,* ]] || was_rw=1
  if (( was_rw == 0 )); then
    m2dp_clean mount -o remount,rw /boot/efi
  fi
  trap '
    action_status=$?
    if (( was_rw == 0 )); then
      m2dp_clean mount -o remount,ro /boot/efi || action_status=1
    fi
    exit "$action_status"
  ' EXIT
  "$action" "$@"
  if (( was_rw == 0 )); then
    m2dp_clean mount -o remount,ro /boot/efi
  fi
  trap - EXIT
}

m2dp_with_operation_lock() (
  set -Eeuo pipefail
  local lock_parent="$1"
  local expected_uid="$2"
  shift 2
  local lock_path="$lock_parent/operation.lock" lock_uid lock_mode lock_fd
  if [[ ! -e $lock_parent && ! -L $lock_parent ]]; then
    m2dp_directory_owned "${lock_parent%/*}" "$expected_uid" || return 1
    m2dp_clean mkdir -m 0700 -- "$lock_parent" || [[ -d $lock_parent && ! -L $lock_parent ]] || return 1
  fi
  m2dp_directory_owned "$lock_parent" "$expected_uid" || return 1
  [[ ! -L $lock_path && ( ! -e $lock_path || -f $lock_path ) ]] || {
    m2dp_die "operation lock path is unsafe"
    return 1
  }
  exec {lock_fd}>"$lock_path"
  m2dp_clean chmod 0600 "$lock_path"
  m2dp_regular_file "$lock_path" || return 1
  read -r lock_uid lock_mode <<<"$(m2dp_clean stat -c '%u %a' -- "$lock_path")"
  [[ $lock_uid == "$expected_uid" && $lock_mode == "600" ]] || {
    m2dp_die "operation lock identity is unsafe"
    return 1
  }
  m2dp_clean flock --exclusive --nonblock "$lock_fd" || {
    m2dp_die "another M2 DisplayPort stage or rollback is active"
    return 1
  }
  "$@"
  m2dp_clean flock --unlock "$lock_fd"
  exec {lock_fd}>&-
)

m2dp_stage_live() {
  local bundle="$1"
  local bundle_uid="$2"
  local timestamp="$3"
  local hook_template="$4"
  local active_boot_sha
  m2dp_verify_live_host
  m2dp_verify_live_safety
  active_boot_sha=$(m2dp_clean sha256sum -- "$M2DP_ACTIVE_BOOT_PATH")
  active_boot_sha=${active_boot_sha%% *}
  m2dp_boot_input_supported "$active_boot_sha" || {
    m2dp_die "active boot.bin is neither the supported stock bundle nor the accepted candidate"
    return 1
  }
  m2dp_stage_files / "$bundle" "$timestamp" "$bundle_uid" \
    "$M2DP_BOOT_SHA256" "$M2DP_IMAGE_SHA256" "$M2DP_IMAGE_SIZE" \
    "$M2DP_MODULE_SHA256" "$M2DP_MODULE_BUILD_ID" "$hook_template" "$active_boot_sha"
}

m2dp_verify_live_release_state() {
  m2dp_read_state "$M2DP_STATE_PARENT/active/state.env" || {
    m2dp_die "active M2 DisplayPort state is invalid"
    return 1
  }
  [[ $M2DP_STATE_CANDIDATE_BOOT_SHA == "$M2DP_BOOT_SHA256" &&
    $M2DP_STATE_CANDIDATE_BOOT_SIZE == "$M2DP_BOOT_SIZE" &&
    $M2DP_STATE_CANDIDATE_IMAGE_SHA == "$M2DP_IMAGE_SHA256" &&
    $M2DP_STATE_CANDIDATE_IMAGE_SIZE == "$M2DP_IMAGE_SIZE" &&
    $M2DP_STATE_HOOK_SHA == "$M2DP_HOOK_SHA256" ]] || {
    m2dp_die "active state differs from the accepted release"
    return 1
  }
  m2dp_boot_input_supported "$M2DP_STATE_PREVIOUS_SHA" || {
    m2dp_die "rollback boot identity is unsupported"
    return 1
  }
}

m2dp_activate_live() {
  m2dp_verify_live_host
  m2dp_verify_live_safety
  m2dp_verify_live_release_state
  m2dp_activate_files / 0
}

m2dp_rollback_live() {
  m2dp_verify_live_host
  m2dp_verify_live_safety
  m2dp_verify_live_release_state
  m2dp_rollback_files / 0
}

m2dp_usage() {
  printf '%s\n' \
    'Usage:' \
    '  sudo /usr/bin/bash integration.sh stage --bundle ABSOLUTE_DIRECTORY' \
    '  sudo /usr/bin/bash integration.sh activate' \
    '  sudo /usr/bin/bash integration.sh rollback' \
    '' \
    'This experimental path supports only Apple J413/T8112 on linux-asahi 7.1.6-1-1-ARCH.' \
    'It stages a non-default image and never changes GRUB, the default image, W, or the stock module.' \
    'Suspend with an external display attached is unsupported.'
}

m2dp_main() {
  set -Eeuo pipefail
  umask 077
  (( EUID == 0 )) || {
    m2dp_die "run this command with sudo /usr/bin/bash"
    return 1
  }
  m2dp_check_environment || return 1
  local action="${1:-}"
  local bundle="" timestamp hook_template sudo_uid
  case "$action" in
    stage)
      [[ $# == 3 && $2 == "--bundle" ]] || {
        m2dp_usage
        return 1
      }
      bundle=$(m2dp_clean realpath -e -- "$3") || return 1
      sudo_uid="${SUDO_UID:-}"
      [[ $sudo_uid =~ ^[1-9][0-9]*$ ]] || {
        m2dp_die "stage must be invoked by a normal user through sudo"
        return 1
      }
      timestamp=$(m2dp_clean date -u +%Y%m%dT%H%M%SZ)
      hook_template=$(m2dp_clean realpath -e -- "${BASH_SOURCE[0]%/*}/05-omarchy-m2-displayport-guard.hook")
      m2dp_with_operation_lock /run/omarchy-m2-displayport 0 \
        m2dp_with_writable_esp m2dp_stage_live "$bundle" "$sudo_uid" "$timestamp" "$hook_template"
      ;;
    activate)
      [[ $# == 1 ]] || {
        m2dp_usage
        return 1
      }
      m2dp_with_operation_lock /run/omarchy-m2-displayport 0 \
        m2dp_with_writable_esp m2dp_activate_live
      ;;
    rollback)
      [[ $# == 1 ]] || {
        m2dp_usage
        return 1
      }
      m2dp_with_operation_lock /run/omarchy-m2-displayport 0 \
        m2dp_with_writable_esp m2dp_rollback_live
      ;;
    -h | --help | "")
      m2dp_usage
      ;;
    *)
      m2dp_usage
      return 1
      ;;
  esac
}

if [[ ${BASH_SOURCE[0]} == "$0" ]]; then
  m2dp_main "$@"
fi
fi
