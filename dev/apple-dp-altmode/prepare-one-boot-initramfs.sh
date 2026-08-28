#!/bin/bash

# Offline only. Invoke with bash in the managed sandbox; never with sudo.
# Sourcing exposes pure validation/copy helpers for tests, not an execution bypass.
readonly DPALT_VERSION="7.1.6-1-1-ARCH"
readonly DPALT_CORE_REL="kernel/drivers/usb/typec/tipd/tps6598x-core.ko"
readonly DPALT_STAGE="/home/david/o/.dev147-stage"
readonly DPALT_CANDIDATE_SHA="bc02723db427639c6586d29eea7918e084874c741b60bf145585c6349fd07d70"
readonly DPALT_BUILD_ID="8fd9e3d39ee211f439471a812fb5eaa2622f7585"
readonly DPALT_CONFIG_SHA="d3f2be936eefc1adce733259fceab552c94af29cf8e017456a5a2193a8bbad69"
readonly DPALT_LIBRARY_SHA="10aec97e97c739903bed997999a1b522c396f62d64fb2f148a2db956821d98a8"

dpalt_die() { printf 'REFUSED: %s\n' "$*" >&2; exit 1; }
dpalt_clean() { /usr/bin/env -i PATH=/usr/bin:/bin LANG=C.UTF-8 "$@"; }
dpalt_require_user() { (( $1 > 0 )) || dpalt_die "run as the normal user, never root"; }

dpalt_check_environment() {
  local name
  while IFS= read -r name; do
    case "$name" in
      BASH_ENV | ENV | MKINITCPIO_* | OMARCHY_DPALT_TEST*)
        dpalt_die "unexpected environment override: $name" ;;
    esac
  done < <(compgen -v)
}

dpalt_new_output() {
  local path="$1" canonical parent
  [[ $path == /* && $path != *$'\n'* && $path != *$'\r'* && $path != *\\* ]] ||
    dpalt_die "output must be a plain absolute path"
  case "$path" in
    / | /boot | /boot/* | /etc | /etc/* | /usr | /usr/* | /lib | /lib/* | /var | /var/* | \
    /proc | /proc/* | /sys | /sys/* | /dev | /dev/* | /run | /run/* | /root | /root/* | \
    /home/david/o-live | /home/david/o-live/* | /usr/share/omarchy/* | \
    "$DPALT_STAGE"/artifacts/* | "$DPALT_STAGE"/evidence/* | "$DPALT_STAGE"/recovery/* | \
    "$DPALT_STAGE"/commands/* | "$DPALT_STAGE"/work/* | "$DPALT_STAGE"/prototype/*)
      dpalt_die "protected output path: $path" ;;
  esac
  [[ ! -e $path && ! -L $path ]] || dpalt_die "output already exists; nothing is overwritten"
  canonical=$(dpalt_clean realpath -m -- "$path") || dpalt_die "cannot resolve output"
  [[ $canonical == "$path" ]] || dpalt_die "output contains a symlink or noncanonical component"
  parent=${path%/*}
  [[ -d $parent && -w $parent && ! -L $parent ]] || dpalt_die "output parent must already exist"
  printf '%s\n' "$path"
}

dpalt_persistent_output() {
  local path filesystem
  path=$(dpalt_new_output "$1") || exit 1
  filesystem=$(dpalt_clean findmnt -n -o FSTYPE -T "${path%/*}") || dpalt_die "cannot identify output filesystem"
  [[ $filesystem == "ext4" ]] || dpalt_die "this host prototype requires persistent ext4 output"
  printf '%s\n' "$path"
}

dpalt_check_hash() {
  local file="$1" expected="$2" actual
  [[ -f $file && ! -L $file ]] || dpalt_die "not a regular pinned file: $file"
  actual=$(dpalt_clean sha256sum -- "$file") || dpalt_die "cannot hash $file"
  [[ ${actual%% *} == "$expected" ]] || dpalt_die "SHA-256 drift: $file"
}

dpalt_plain_tree() {
  [[ -d $1 && ! -L $1 ]] || dpalt_die "not a plain directory: $1"
  [[ -z $(dpalt_clean find "$1" -mindepth 1 ! -type f ! -type d -print -quit) ]] ||
    dpalt_die "tree contains a symlink or special file"
  [[ -z $(dpalt_clean find "$1" -type f -links +1 -print -quit) ]] || dpalt_die "tree contains hardlinks"
}

dpalt_tree_manifest() (
  dpalt_plain_tree "$1"
  cd -- "$1" || exit 1
  dpalt_clean find . -type f -print0 | dpalt_clean sort -z | dpalt_clean xargs -0 -r sha256sum
)

dpalt_copy_tree() {
  dpalt_plain_tree "$1"
  [[ ! -e $2 && ! -L $2 && $2 != "$1"/* ]] || dpalt_die "copy destination must be new and independent"
  dpalt_clean cp -a --reflink=auto --no-preserve=ownership -- "$1" "$2"
  dpalt_plain_tree "$2"
}

dpalt_check_tree_delta() {
  local before after
  before=$(dpalt_tree_manifest "$1") || exit 1
  after=$(dpalt_tree_manifest "$2") || exit 1
  [[ $(printf '%s\n' "$before" | dpalt_clean cut -c67-) == $(printf '%s\n' "$after" | dpalt_clean cut -c67-) ]] ||
    dpalt_die "private tree file set differs from stock"
  # These eleven files are depmod output. modules.builtin/order/modinfo are inputs.
  [[ $(printf '%s\n' "$before" | dpalt_immutable_records) == $(printf '%s\n' "$after" | dpalt_immutable_records) ]] ||
    dpalt_die "private tree changed more than the core and depmod indexes"
}

dpalt_immutable_records() {
  dpalt_clean awk -v core="./$DPALT_CORE_REL" '
    $2 != core && $2 !~ /^\.\/modules\.(alias(\.bin)?|builtin(\.alias)?\.bin|dep(\.bin)?|devname|softdep|symbols(\.bin)?|weakdep)$/ { print }
  '
}

dpalt_check_archive_names() {
  local entry core_count=0
  while IFS= read -r entry; do
    entry=${entry#./}
    [[ -n $entry && $entry != /* && "/$entry/" != */../* && "/$entry/" != */./* && $entry != *\\* ]] ||
      dpalt_die "unsafe archive member"
    case "$entry" in
      usr/lib/modules/ | lib/modules/) ;;
      usr/lib/modules/* | lib/modules/*)
        [[ $entry == "usr/lib/modules/$DPALT_VERSION" || $entry == "usr/lib/modules/$DPALT_VERSION/"* ||
           $entry == "lib/modules/$DPALT_VERSION" || $entry == "lib/modules/$DPALT_VERSION/"* ]] ||
          dpalt_die "archive contains another kernel" ;;
    esac
    if [[ $entry == "usr/lib/modules/$DPALT_VERSION/$DPALT_CORE_REL" ]]; then
      (( core_count += 1 ))
      (( core_count == 1 )) || dpalt_die "duplicate candidate core in archive"
    fi
  done <"$1"
}

dpalt_build_command() {
  DPALT_BUILD=(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C.UTF-8 /usr/bin/mkinitcpio
    --config "$1/mkinitcpio.conf" --hookdir /usr/lib/initcpio --nopost
    --kernel "$DPALT_VERSION" --moduleroot "$1/module-root" --builddir "$1/tmp"
    --save --generate "$1/initramfs-linux-asahi-dpalt.img")
}

dpalt_expected_inputs() {
  # Fixed, non-secret files only. Root-only stock initramfs/GRUB reads are a later gate.
  printf '%s  %s\n' \
    "$DPALT_CANDIDATE_SHA" "$DPALT_STAGE/artifacts/tps6598x-core.ko" \
    "ac7b9b7a92a95b88cf7d56cb134499cf8bae3d50a78745223e4c55b75a594e72" "/usr/lib/modules/$DPALT_VERSION/$DPALT_CORE_REL" \
    "3d64857f8964d05e41778ccc5b4b8abbcdfedaceb918add2eeff8cb41272a8a2" "/usr/lib/modules/$DPALT_VERSION/dtbs/t8112-j413.dtb" \
    "ee36d989d62f2dd498b818e15c2044350c79d814a2017ffca61fdc2ad1aa95b6" "/usr/lib/modules/$DPALT_VERSION/vmlinuz" \
    "ee36d989d62f2dd498b818e15c2044350c79d814a2017ffca61fdc2ad1aa95b6" "/boot/vmlinuz-linux-asahi" \
    "203ab7027536c8d16f373d02c1f6346a5c34cfe095a9dafd0cfe37d2b354090c" "/boot/efi/m1n1/boot.bin"
  local base
  for base in /boot/efi/m1n1 "$DPALT_STAGE/recovery"; do
    printf '%s  %s\n' \
      "bb6829c44d8de26d6615406b41edc0beef2254766b5ed114afad2029db7ae856" "$base/boot.bin.pre-dpalt-20260826T222113Z" \
      "dc0de17453ecc681c1420db03fde4ec8d24b022453f2489febbbdbd12c06ae64" "$base/RESTORE-DPALT-MAC-20260826T222113Z.sh" \
      "dcb10da1d75be23953382270fb2fd5bc82e32999e43745ae577e65d1887dd59a" "$base/RECOVERY-DPALT-MAC-20260826T222113Z.txt"
  done
  dpalt_clean cat <<'PINS'
53bb215d59e5eb813f95856ac3142257c3ddbaf524980fa805ecb626ca998de2  /etc/mkinitcpio.conf
12b3c91c93aea49284230b4f31cf5437c80283e9f8b819eb2cf9525319126fd7  /etc/mkinitcpio.conf.d/apple_hid_modules.conf
ddae32abcdf841a6ae41c2ef4420dc9ab90e0fecec3b2e83deb858492740a7c6  /etc/mkinitcpio.conf.d/omarchy_hooks.conf
46affe91a12ae618abe4e8617081af0ebc4b8d0244519db372c630e68b7d3799  /etc/mkinitcpio.conf.d/thunderbolt_module.conf
b80b9c165273a5fd1628e20111c044d3b99149eb7c373b2fb2c60b4c45fc07d1  /etc/mkinitcpio.conf.d/zz-asahi-vendorfw.conf
029ba11980730bb17aea57aea325e422d6979b5fc01938f197f948783370a35f  /etc/vconsole.conf
033252d5100cbb0028d7c15e075f63e4eb5ff7f1a923cd5cb547bcfd6b024f5b  /etc/locale.conf
85c1bc592c657ec3b6e35e0ab25101eef6e3e4f365ab5003ebcf7282f098b13e  /var/lib/pacman/local/linux-asahi-7.1.6.asahi1-1/mtree
b257763135820480951989ad10bd7d11f1b6ac2a3ca9d5013e3f7d76b797acc9  /usr/bin/mkinitcpio
a63d2b29f1c41036a0575f9310d90587d7eb6d71e3623a93b3e25b02930a8c13  /usr/bin/lsinitcpio
14add84fa083fca75eb50d78c5fa50c7558a5d6bed16fff858df3d376c454221  /usr/bin/kmod
87e2fb1103db1eb68154a3082b7a0fdce03f090448d9bdd262f2ab813f0db369  /usr/bin/gzip
817c2cbb5a520c14cae853f81a85db6937028a0aae40e7ecae48348abea3b13f  /usr/bin/bsdtar
ead53e85b173da37e9b553c04e2e631d037a40f99ea19563cc2a8e17482f150c  /usr/bin/bsdcpio
4bd135916c3cebba703b8d311e04f977e03d3cd998f57ed2d4c590f21166dbb7  /usr/bin/readelf
PINS
}

dpalt_library_manifest() {
  dpalt_plain_tree /usr/lib/initcpio
  dpalt_plain_tree /usr/share/asahi-scripts
  dpalt_clean find /usr/lib/initcpio /usr/share/asahi-scripts -type f -print0 |
    dpalt_clean sort -z | dpalt_clean xargs -0 sha256sum
}

dpalt_check_inputs() {
  local hash file libraries
  [[ ! -e /var/lib/pacman/db.lck && ! -L /var/lib/pacman/db.lck ]] || dpalt_die "package transaction is active"
  [[ ! -e /etc/default/update-m1n1 && ! -L /etc/default/update-m1n1 ]] || dpalt_die "persistent boot override exists"
  [[ $(dpalt_clean uname -r) == "$DPALT_VERSION" ]] || dpalt_die "running kernel differs"
  [[ $(dpalt_clean pacman -Q linux-asahi) == "linux-asahi 7.1.6.asahi1-1" ]] || dpalt_die "installed kernel differs"
  dpalt_clean tr '\0' '\n' </proc/device-tree/compatible | dpalt_clean grep -Fxq apple,j413 || dpalt_die "not J413"
  dpalt_clean tr '\0' '\n' </proc/device-tree/compatible | dpalt_clean grep -Fxq apple,t8112 || dpalt_die "not T8112"
  [[ $(dpalt_clean tr -d '\0' </proc/device-tree/soc/dcp@271c00000/status) == "okay" ]] || dpalt_die "prototype DTB is not booted"
  [[ $(dpalt_clean find /etc/mkinitcpio.conf.d -mindepth 1 -maxdepth 1 -printf '%f\n' | dpalt_clean sort) == \
     $'apple_hid_modules.conf\nomarchy_hooks.conf\nthunderbolt_module.conf\nzz-asahi-vendorfw.conf' ]] || dpalt_die "drop-in set changed"
  [[ -z $(dpalt_clean find /etc/initcpio -mindepth 2 -print -quit) ]] || dpalt_die "custom initcpio hooks exist"
  for file in /usr/bin/depmod /usr/bin/modinfo; do
    [[ $(dpalt_clean readlink -f "$file") == "/usr/bin/kmod" ]] || dpalt_die "kmod tool alias changed"
  done
  while read -r hash file; do
    dpalt_check_hash "$file" "$hash"
    printf '%s  %s\n' "$hash" "$file"
  done < <(dpalt_expected_inputs)
  libraries=$(dpalt_library_manifest | dpalt_clean sha256sum) || dpalt_die "cannot hash initcpio libraries"
  [[ ${libraries%% *} == "$DPALT_LIBRARY_SHA" ]] || dpalt_die "initcpio tools/hooks changed"
}

dpalt_package_manifest() {
  dpalt_clean gzip -cd /var/lib/pacman/local/linux-asahi-7.1.6.asahi1-1/mtree |
    dpalt_clean awk -v prefix="./usr/lib/modules/$DPALT_VERSION/" '
      index($1, prefix) == 1 {
        for (i=2; i<=NF; i++) if ($i ~ /^sha256digest=/) {
          digest=substr($i,14); path=substr($1,length(prefix)+1)
          if (digest !~ /^[a-f0-9]{64}$/ || path ~ /(^|\/)\.\.(\/|$)/) exit 1
          printf "%s  ./%s\n", digest, path
        }
      }' | dpalt_clean sort -k2
}

dpalt_require_image_module() {
  local extracted="$1" root="$2" module="$3" filename relative
  filename=$(dpalt_clean modinfo -b "$root" -k "$DPALT_VERSION" -F filename "$module") ||
    dpalt_die "unknown required module: $module"
  if [[ $filename == "(builtin)" ]]; then
    dpalt_clean awk -F/ -v name="${module//-/_}" '
      { n=$NF; sub(/\.ko$/,"",n); gsub(/-/,"_",n); if(n==name) found=1 }
      END {exit !found}' "$root/lib/modules/$DPALT_VERSION/modules.builtin" ||
      dpalt_die "builtin not proved: $module"
  else
    [[ $filename == "$root/lib/modules/$DPALT_VERSION/"* ]] || dpalt_die "module escaped private root"
    relative=${filename#"$root/lib/modules/$DPALT_VERSION/"}
    [[ -f $extracted/usr/lib/modules/$DPALT_VERSION/$relative && ! -L $extracted/usr/lib/modules/$DPALT_VERSION/$relative ]] ||
      dpalt_die "module missing from image: $module"
    dpalt_clean cmp -s -- "$filename" "$extracted/usr/lib/modules/$DPALT_VERSION/$relative" ||
      dpalt_die "wrong module bytes: $module"
  fi
}

dpalt_required_early_modules() {
  # Match the reviewed stock hook selection; do not add preload or custom hooks.
  printf '%s\n' appledrm phy-apple-atc tps6598x tps6598x-core typec \
    hid-apple hid-magicmouse nvme-apple apple-mailbox apple-dart i2c-pasemi-platform spi-apple spi-hid-apple spi-hid-apple-of \
    ext4 drm drm_dma_helper dm-crypt dm-integrity
}

dpalt_verify_image() {
  local output="$1" root="$1/module-root" image="$1/initramfs-linux-asahi-dpalt.img"
  local extracted="$1/extracted" core module file relative dependencies dependency
  local -a dependencies_array
  dpalt_clean lsinitcpio --early --list "$image" >"$output/archive-early.list"
  dpalt_clean lsinitcpio --cpio --list "$image" >"$output/archive-main.list"
  dpalt_clean cat "$output/archive-early.list" "$output/archive-main.list" >"$output/archive-all.list"
  dpalt_check_archive_names "$output/archive-all.list"
  dpalt_clean mkdir -m 0700 -- "$extracted"
  (cd -- "$extracted" && dpalt_clean lsinitcpio --extract "$image") >"$output/extraction.log" 2>&1
  core="$extracted/usr/lib/modules/$DPALT_VERSION/$DPALT_CORE_REL"
  dpalt_check_hash "$core" "$DPALT_CANDIDATE_SHA"
  [[ $(dpalt_clean readelf -n "$core" | dpalt_clean awk '/Build ID:/ {print $3}') == "$DPALT_BUILD_ID" ]] ||
    dpalt_die "candidate build ID differs"
  [[ $(dpalt_clean modinfo -F vermagic "$core") == $(dpalt_clean modinfo -F vermagic "/usr/lib/modules/$DPALT_VERSION/$DPALT_CORE_REL") ]] ||
    dpalt_die "candidate vermagic differs"
  dpalt_clean cmp -s "$output/mkinitcpio.conf" "$extracted/buildconfig" || dpalt_die "embedded build configuration differs"
  dpalt_clean cmp -s /etc/vconsole.conf "$extracted/etc/vconsole.conf" || dpalt_die "vconsole configuration differs"
  dpalt_clean cmp -s /usr/share/asahi-scripts/functions.sh "$extracted/usr/share/asahi-scripts/functions.sh" || dpalt_die "Asahi firmware helper missing"
  [[ -f $extracted/hooks/asahi && -f $extracted/init && -f $extracted/config ]] || dpalt_die "boot or firmware hook is absent"
  dpalt_clean grep -Fxq 'MODULES="hid_apple hid_magicmouse"' "$extracted/config" || dpalt_die "early module list changed"
  while IFS= read -r module; do
    dpalt_require_image_module "$extracted" "$root" "$module"
  done < <(dpalt_required_early_modules)
  while IFS= read -r -d '' file; do
    relative=${file#"$extracted/usr/lib/modules/$DPALT_VERSION/"}
    dpalt_clean cmp -s "$file" "$root/lib/modules/$DPALT_VERSION/$relative" || dpalt_die "image module differs from private source"
    dependencies=$(dpalt_clean modinfo -F depends "$file") || dpalt_die "cannot inspect module dependencies"
    IFS=, read -r -a dependencies_array <<<"$dependencies"
    for dependency in "${dependencies_array[@]}"; do
      [[ -z $dependency ]] || dpalt_require_image_module "$extracted" "$root" "$dependency"
    done
  done < <(dpalt_clean find "$extracted/usr/lib/modules/$DPALT_VERSION" -type f -name '*.ko' -print0)
  dpalt_clean sha256sum "$image" >"$output/image.sha256"
}

dpalt_main() {
  set -Eeuo pipefail
  umask 077
  dpalt_require_user "$EUID"
  dpalt_check_environment
  [[ $# == 2 && $1 == "--output" ]] || dpalt_die "usage: bash prepare-one-boot-initramfs.sh --output NEW_PERSISTENT_DIRECTORY"
  local output source_tree="/usr/lib/modules/$DPALT_VERSION" private_tree config status=0
  output=$(dpalt_persistent_output "$2") || exit 1
  config=$(dpalt_clean realpath -- "${BASH_SOURCE[0]%/*}/one-boot-mkinitcpio.conf") || exit 1
  dpalt_check_hash "$config" "$DPALT_CONFIG_SHA"
  dpalt_check_inputs >/dev/null
  dpalt_plain_tree "$source_tree"
  dpalt_clean mkdir -m 0700 -- "$output"
  printf 'INCOMPLETE: no staging or boot permission; retain this private directory on failure.\n' >"$output/INCOMPLETE"
  trap 'printf "Stopped. Keep the private output and inspect its INCOMPLETE marker/logs.\n" >&2' ERR
  dpalt_clean date --utc --iso-8601=seconds >"$output/started-at.txt"
  dpalt_check_inputs >"$output/inputs.before.sha256"
  dpalt_library_manifest >"$output/hooks.before.sha256"
  dpalt_tree_manifest "$source_tree" >"$output/source.before.sha256"
  dpalt_package_manifest >"$output/package.sha256"
  [[ $(dpalt_clean wc -l <"$output/package.sha256") == 1987 ]] || dpalt_die "unexpected kernel package file count"
  dpalt_clean cmp -s "$output/package.sha256" "$output/source.before.sha256" || dpalt_die "kernel package contents differ from mtree"
  dpalt_clean sha256sum \
    "$source_tree/kernel/drivers/phy/apple/phy-apple-dptx.ko" \
    "$source_tree/kernel/drivers/mux/mux-apple-display-crossbar.ko" >"$output/normal-root-availability.sha256"
  printf '%s\n' 'These package-verified modules remain available on the normal root.' \
    'They are not mandatory in the early image under the reviewed stock hook selection.' \
    'Their absence from an early image is not boot proof. Stock comparison and boot tests remain pending.' \
    >"$output/normal-root-availability.txt"
  dpalt_clean mkdir -m 0700 -- "$output/module-root" "$output/tmp"
  dpalt_clean mkdir -p -- "$output/module-root/lib/modules"
  private_tree="$output/module-root/lib/modules/$DPALT_VERSION"
  dpalt_copy_tree "$source_tree" "$private_tree"
  dpalt_clean cp --reflink=auto --no-preserve=ownership -- "$DPALT_STAGE/artifacts/tps6598x-core.ko" "$private_tree/$DPALT_CORE_REL"
  dpalt_check_hash "$private_tree/$DPALT_CORE_REL" "$DPALT_CANDIDATE_SHA"
  dpalt_clean depmod -b "$output/module-root" "$DPALT_VERSION" >"$output/depmod.log" 2>&1
  dpalt_check_tree_delta "$source_tree" "$private_tree"
  dpalt_tree_manifest "$private_tree" >"$output/private.before.sha256"
  dpalt_clean cp -- "$config" "$output/mkinitcpio.conf"
  dpalt_build_command "$output"
  printf '%q ' "${DPALT_BUILD[@]}" >"$output/build-command.txt"
  printf '\n' >>"$output/build-command.txt"
  "${DPALT_BUILD[@]}" >"$output/build.log" 2>&1 || status=$?
  dpalt_check_inputs >"$output/inputs.after.sha256"
  dpalt_tree_manifest "$source_tree" >"$output/source.after.sha256"
  dpalt_clean cmp -s "$output/source.before.sha256" "$output/source.after.sha256" || dpalt_die "stock tree changed during build"
  dpalt_check_tree_delta "$source_tree" "$private_tree"
  (( status == 0 )) || dpalt_die "mkinitcpio exited $status; any emitted image remains incomplete"
  dpalt_verify_image "$output"
  dpalt_check_hash "$config" "$DPALT_CONFIG_SHA"
  dpalt_check_inputs >"$output/inputs.final.sha256"
  printf '%s\n' 'BUILD CHECKS ONLY. Stock-image comparison, root-only stock hashes, independent review,' \
    'boot-entry review, staging, startup, behavior tests, and rollback proof remain pending.' >"$output/BUILD-CHECKS-ONLY.txt"
  dpalt_clean mv -T -- "$output/INCOMPLETE" "$output/build-start-marker.txt"
  printf 'BUILD CHECKS ONLY: %s\nStock comparison, review, staging and boot remain pending.\n' "$output"
}

if [[ ${BASH_SOURCE[0]} == "$0" ]]; then
  dpalt_main "$@"
fi
