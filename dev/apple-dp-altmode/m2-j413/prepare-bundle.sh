#!/bin/bash

if [[ ${BASH_SOURCE[0]} == "$0" && $- != *p* ]]; then
  /usr/bin/env -i PATH=/usr/bin:/bin LANG=C.UTF-8 \
    /usr/bin/bash --noprofile --norc -p "${BASH_SOURCE[0]}" "$@"
else
set -euo pipefail

if ! declare -F m2dp_validate_bundle >/dev/null; then
  source "${BASH_SOURCE[0]%/*}/integration.sh"
fi

readonly M2DP_BUILDCONFIG_SHA256="d3f2be936eefc1adce733259fceab552c94af29cf8e017456a5a2193a8bbad69"
readonly M2DP_CORE_RELATIVE="usr/lib/modules/$M2DP_KERNEL_RELEASE/kernel/drivers/usb/typec/tipd/tps6598x-core.ko"

m2dp_prepare_check_environment() {
  local name
  while IFS= read -r name; do
    case "$name" in
      BASH_ENV | ENV | LD_PRELOAD | LD_LIBRARY_PATH | MKINITCPIO_* | M2DP_*)
        m2dp_die "unexpected environment override: $name"
        return 1
        ;;
    esac
  done < <(compgen -e)
}

m2dp_prepare_output_path() {
  local requested="$1"
  local canonical parent filesystem
  [[ $requested == /* && $requested != *$'\n'* && $requested != *$'\r'* && $requested != *\\* ]] || {
    m2dp_die "output must be a plain absolute path"
    return 1
  }
  case "$requested" in
    / | /boot | /boot/* | /etc | /etc/* | /usr | /usr/* | /lib | /lib/* | /var | /var/* | \
      /proc | /proc/* | /sys | /sys/* | /dev | /dev/* | /run | /run/* | /root | /root/* | \
      /home/david/o-live | /home/david/o-live/*)
      m2dp_die "output is protected: $requested"
      return 1
      ;;
  esac
  [[ ! -e $requested && ! -L $requested ]] || {
    m2dp_die "output already exists"
    return 1
  }
  canonical=$(m2dp_clean realpath -m -- "$requested") || return 1
  [[ $canonical == "$requested" ]] || {
    m2dp_die "output is noncanonical"
    return 1
  }
  parent=${requested%/*}
  m2dp_canonical_existing "$parent" || return 1
  [[ -d $parent && -w $parent && ! -L $parent ]] || {
    m2dp_die "output parent is not a writable directory"
    return 1
  }
  filesystem=$(m2dp_clean findmnt -n -o FSTYPE -T "$parent") || return 1
  [[ $filesystem != "tmpfs" && $filesystem != "ramfs" ]] || {
    m2dp_die "output must use persistent storage"
    return 1
  }
  printf '%s\n' "$requested"
}

m2dp_check_archive_names() {
  local list="$1"
  local entry core_count=0
  while IFS= read -r entry; do
    entry=${entry#./}
    [[ -n $entry && $entry != /* && "/$entry/" != */../* && "/$entry/" != */./* && $entry != *\\* ]] || {
      m2dp_die "unsafe initramfs member"
      return 1
    }
    case "$entry" in
      usr/lib/modules/ | lib/modules/) ;;
      usr/lib/modules/* | lib/modules/*)
        [[ $entry == "usr/lib/modules/$M2DP_KERNEL_RELEASE" ||
          $entry == "usr/lib/modules/$M2DP_KERNEL_RELEASE/"* ||
          $entry == "lib/modules/$M2DP_KERNEL_RELEASE" ||
          $entry == "lib/modules/$M2DP_KERNEL_RELEASE/"* ]] || {
          m2dp_die "initramfs contains another kernel"
          return 1
        }
        ;;
    esac
    if [[ $entry == "$M2DP_CORE_RELATIVE" ]]; then
      (( core_count += 1 ))
    fi
  done <"$list"
  (( core_count == 1 )) || {
    m2dp_die "initramfs must contain exactly one patched TIPD core"
    return 1
  }
}

m2dp_mark_prepared() {
  local output="$1"
  m2dp_regular_file "$output/INCOMPLETE" || return 1
  m2dp_absent "$output/PREPARED" || return 1
  m2dp_clean rm -- "$output/INCOMPLETE"
  printf 'PREPARED\n' >"$output/PREPARED"
  chmod 0600 "$output/PREPARED"
}

m2dp_prepare_bundle() {
  local boot="$1"
  local image="$2"
  local requested_output="$3"
  local output boot_size image_sha image_size core build_id
  local extracted manifest
  (( EUID != 0 )) || {
    m2dp_die "prepare the bundle without sudo"
    return 1
  }
  m2dp_prepare_check_environment || return 1
  boot=$(m2dp_clean realpath -e -- "$boot") || return 1
  image=$(m2dp_clean realpath -e -- "$image") || return 1
  output=$(m2dp_prepare_output_path "$requested_output") || return 1
  m2dp_regular_file "$boot" || return 1
  m2dp_regular_file "$image" || return 1
  boot_size=$(m2dp_clean stat -c '%s' -- "$boot")
  m2dp_verify_file "$boot" "$M2DP_BOOT_SHA256" "$boot_size" || return 1
  image_sha=$(m2dp_clean sha256sum -- "$image")
  image_sha=${image_sha%% *}
  image_size=$(m2dp_clean stat -c '%s' -- "$image")
  [[ $image_sha == "$M2DP_IMAGE_SHA256" && $image_size == "$M2DP_IMAGE_SIZE" ]] || {
    m2dp_die "candidate initramfs differs from the accepted release"
    return 1
  }
  mkdir -m 0700 -- "$output"
  printf 'INCOMPLETE\n' >"$output/INCOMPLETE"
  trap 'printf "PREPARATION FAILED. Retain %s for review.\n" "$output" >&2' ERR
  mkdir -m 0700 -- "$output/evidence" "$output/work" "$output/work/extracted"
  m2dp_clean lsinitcpio --early --list "$image" >"$output/evidence/archive-early.list"
  m2dp_clean lsinitcpio --cpio --list "$image" >"$output/evidence/archive-main.list"
  m2dp_clean cat "$output/evidence/archive-early.list" "$output/evidence/archive-main.list" >"$output/evidence/archive-all.list"
  m2dp_check_archive_names "$output/evidence/archive-all.list"
  extracted="$output/work/extracted"
  (cd "$extracted" && m2dp_clean lsinitcpio --extract "$image") >"$output/evidence/extraction.log" 2>&1
  core="$extracted/$M2DP_CORE_RELATIVE"
  m2dp_verify_file "$core" "$M2DP_MODULE_SHA256" "$(m2dp_clean stat -c '%s' -- "$core")"
  build_id=$(m2dp_clean readelf -n "$core" | m2dp_clean awk '/Build ID:/ {print $3}')
  [[ $build_id == "$M2DP_MODULE_BUILD_ID" ]] || {
    m2dp_die "patched TIPD build ID differs"
    return 1
  }
  [[ $(m2dp_clean modinfo -F vermagic "$core") == "$M2DP_KERNEL_RELEASE SMP preempt mod_unload aarch64" ]] || {
    m2dp_die "patched TIPD vermagic differs"
    return 1
  }
  m2dp_verify_file "$extracted/buildconfig" "$M2DP_BUILDCONFIG_SHA256" "$(m2dp_clean stat -c '%s' -- "$extracted/buildconfig")"
  [[ -f $extracted/hooks/asahi && -f $extracted/init && -f $extracted/config && -f $extracted/etc/vconsole.conf ]] || {
    m2dp_die "required boot or Asahi firmware content is absent"
    return 1
  }
  m2dp_clean grep -Fxq 'MODULES="hid_apple hid_magicmouse"' "$extracted/config" || {
    m2dp_die "early Apple HID module set differs"
    return 1
  }
  (cd "$extracted" && m2dp_clean find . -type f -print0 | m2dp_clean sort -z | m2dp_clean xargs -0 -r sha256sum) \
    >"$output/evidence/extracted-files.sha256"
  (cd "$extracted" && m2dp_clean find . -type l -printf '%p -> %l\n' | m2dp_clean sort) \
    >"$output/evidence/extracted-links.txt"
  m2dp_copy_new "$boot" "$output/candidate-boot.bin" "$M2DP_BOOT_SHA256" "$boot_size" 0600
  m2dp_copy_new "$image" "$output/candidate-initramfs.img" "$image_sha" "$image_size" 0600
  manifest="$output/bundle.env"
  printf '%s\n' \
    'format=1' \
    'compatible=apple,j413' \
    'soc=apple,t8112' \
    "kernel_release=$M2DP_KERNEL_RELEASE" \
    "kernel_package=$M2DP_KERNEL_PACKAGE" \
    "boot_sha256=$M2DP_BOOT_SHA256" \
    "boot_size=$boot_size" \
    "image_sha256=$image_sha" \
    "image_size=$image_size" \
    "module_sha256=$M2DP_MODULE_SHA256" \
    "module_build_id=$M2DP_MODULE_BUILD_ID" >"$manifest"
  chmod 0600 "$manifest"
  m2dp_validate_bundle_contents "$output" "$M2DP_BOOT_SHA256" "$M2DP_IMAGE_SHA256" "$M2DP_IMAGE_SIZE" \
    "$M2DP_MODULE_SHA256" "$M2DP_MODULE_BUILD_ID"
  m2dp_verify_file "$boot" "$M2DP_BOOT_SHA256" "$boot_size"
  m2dp_verify_file "$image" "$image_sha" "$image_size"
  m2dp_clean sha256sum -- "$output/candidate-boot.bin" "$output/candidate-initramfs.img" "$manifest" \
    >"$output/evidence/bundle.sha256"
  m2dp_mark_prepared "$output"
  m2dp_validate_bundle "$output" "$M2DP_BOOT_SHA256" "$M2DP_IMAGE_SHA256" "$M2DP_IMAGE_SIZE" \
    "$M2DP_MODULE_SHA256" "$M2DP_MODULE_BUILD_ID"
  trap - ERR
  printf 'BUNDLE PREPARATION PASS: %s\n' "$output"
}

m2dp_prepare_usage() {
  printf '%s\n' \
    'Usage: /usr/bin/bash prepare-bundle.sh --boot FILE --image FILE --output NEW_ABSOLUTE_DIRECTORY'
}

m2dp_prepare_main() {
  local boot="" image="" output=""
  while (( $# )); do
    case "$1" in
      --boot)
        [[ $# -ge 2 ]] || return 1
        boot="$2"
        shift 2
        ;;
      --image)
        [[ $# -ge 2 ]] || return 1
        image="$2"
        shift 2
        ;;
      --output)
        [[ $# -ge 2 ]] || return 1
        output="$2"
        shift 2
        ;;
      -h | --help)
        m2dp_prepare_usage
        return 0
        ;;
      *)
        m2dp_prepare_usage
        return 1
        ;;
    esac
  done
  [[ -n $boot && -n $image && -n $output ]] || {
    m2dp_prepare_usage
    return 1
  }
  m2dp_prepare_bundle "$boot" "$image" "$output"
}

if [[ ${BASH_SOURCE[0]} == "$0" ]]; then
  m2dp_prepare_main "$@"
fi
fi
