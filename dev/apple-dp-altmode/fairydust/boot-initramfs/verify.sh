#!/bin/bash
set -euo pipefail

verify_module_bytes() {
  [[ -f $1 && -f $2 ]] && cmp -s "$1" "$2"
}

verify_release_tree() {
  [[ -d $1/lib/modules/$2 ]] || return 1
  [[ $(find "$1/lib/modules" -mindepth 1 -maxdepth 1 -type d -printf '%f\n') == "$2" ]]
}

verify_startup() {
  local root=$1 name
  for name in init init_functions; do
    [[ -f $root/$name && ! -L $root/$name ]] || return 1
    cmp -s "$root/$name" "/usr/lib/initcpio/$name" || return 1
  done
  [[ -x $root/init && -x $root/usr/bin/busybox ]] || return 1
  [[ -f $root/usr/bin/busybox && ! -L $root/usr/bin/busybox ]] || return 1
  cmp -s "$root/usr/bin/busybox" /usr/lib/initcpio/busybox || return 1
  [[ $(readlink "$root/usr/bin/ash") == "busybox" ]] || return 1
  for name in asahi udev plymouth keymap encrypt; do
    [[ -f $root/hooks/$name && ! -L $root/hooks/$name && -x $root/hooks/$name ]] || return 1
    cmp -s "$root/hooks/$name" "/usr/lib/initcpio/hooks/$name" || return 1
  done
  [[ -f $root/usr/share/asahi-scripts/functions.sh && ! -L $root/usr/share/asahi-scripts/functions.sh ]] || return 1
  cmp -s "$root/usr/share/asahi-scripts/functions.sh" /usr/share/asahi-scripts/functions.sh || return 1
  [[ -f $root/config && ! -L $root/config ]] || return 1
  cmp -s "$root/config" <(cat <<'EOF'
MODULES="hid_apple hid_magicmouse appledrm apple_sio tps6598x_core phy_apple_atc dwc3_apple apple_avd"
EARLYHOOKS="asahi udev"
HOOKS="udev plymouth keymap encrypt"
LATEHOOKS="asahi plymouth"
CLEANUPHOOKS="udev"
EMERGENCYHOOKS="plymouth"
EOF
  )
}

verify_image() {
  local root=$1 build=$2 release=7.1.12-dev147-fairydust1 module relative firmware name dependency parameters dependencies
  local candidate="$build/artifacts/candidate-7.1.12-dev147-fairydust1"
  local original="$build/artifacts/root/lib/modules/$release"
  verify_release_tree "$root" "$release"
  verify_startup "$root"
  [[ $(readlink "$root/usr/lib/firmware/vendor") == "/vendorfw" ]]
  cmp "$root/usr/lib/modules/$release/modules.builtin.bin" "$original/modules.builtin.bin"
  cmp "$root/usr/lib/modules/$release/modules.builtin.alias.bin" "$original/modules.builtin.alias.bin"
  [[ $(modprobe -d "$root" -S "$release" --show-depends asahi) == "builtin asahi" ]]
  local module_count=0 firmware_count=0
  while IFS= read -r -d '' module; do
    relative=${module#"$root/usr/lib/modules/$release/"}
    verify_module_bytes "$module" "$original/$relative"
    [[ $(modinfo -F vermagic "$module") == "$release "* ]]
    ((module_count += 1))
  done < <(find "$root/usr/lib/modules/$release/kernel" -type f -name '*.ko' -print0)
  (( module_count > 0 ))
  for name in appledrm apple-sio tps6598x-core phy-apple-atc dwc3-apple apple-avd hid_apple hid_magicmouse; do
    module=$(modinfo -b "$root" -k "$release" -F filename "$name")
    [[ -f $module ]]
    dependencies=$(modprobe -d "$root" -S "$release" --show-depends "$name")
    while read -r dependency module parameters; do
      [[ $dependency != "insmod" || -f $module ]]
    done <<< "$dependencies"
  done
  while IFS= read -r -d '' firmware; do
    relative=${firmware#"$root"}
    cmp "$firmware" "$relative"
    ((firmware_count += 1))
  done < <(find "$root/usr/lib/firmware" -type f -print0)
  for firmware in /usr/lib/firmware/apple/avd-fw-*.bin; do
    cmp "$root$firmware" "$firmware"
  done
  local validation
  validation=$(mktemp -d "$root/../module-validation.XXXXXX")
  mkdir -p "$validation/lib/modules"
  cp -al "$root/usr/lib/modules/$release" "$validation/lib/modules/"
  cp "$original/modules.builtin" "$original/modules.builtin.modinfo" "$validation/lib/modules/$release/"
  find "$validation/lib/modules/$release/kernel" -type f -name '*.ko' -printf 'kernel/%P\n' | LC_ALL=C sort > "$validation/lib/modules/$release/modules.order"
  depmod -n -e -F "$candidate/System.map" -b "$validation" "$release" > "$root/../depmod.stdout" 2> "$root/../depmod.stderr"
  [[ ! -s $root/../depmod.stderr ]]
  printf 'PASS: exact startup contract, %s matching modules, dependency closure, %s firmware files, Asahi hook and built-in GPU\n' "$module_count" "$firmware_count"
}

if [[ ${BASH_SOURCE[0]} == "$0" ]]; then
  [[ $# == 2 ]]
  verify_image "$1" "$2"
fi
