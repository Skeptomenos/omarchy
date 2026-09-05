#!/bin/bash
set -euo pipefail

verify_module_tree() {
  local kernel_build=$1 installed=$2 relative
  [[ -s $kernel_build/modules.order && -d $installed/kernel ]] || return 1
  cmp <(sed 's:^\(.*\)\.o$:kernel/\1.ko:' "$kernel_build/modules.order") "$installed/modules.order" || return 1
  cmp "$kernel_build/modules.builtin" "$installed/modules.builtin" || return 1
  cmp "$kernel_build/modules.builtin.modinfo" "$installed/modules.builtin.modinfo" || return 1
  [[ -z $(find "$installed/kernel" ! -type f ! -type d -print -quit) ]] || return 1
  diff -u <(sed 's/\.o$/.ko/' "$kernel_build/modules.order" | LC_ALL=C sort) <(find "$installed/kernel" -type f -printf '%P\n' | LC_ALL=C sort) || return 1
  while IFS= read -r relative; do
    [[ $relative == *.o ]] || return 1
    cmp "$kernel_build/${relative%.o}.ko" "$installed/kernel/${relative%.o}.ko" || return 1
  done < "$kernel_build/modules.order"
}

main() {
  local script_dir
  script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
  cmp <(sed -n '/^verify_module_tree()/,/^}/p' "$script_dir/../validate-offline.sh") <(sed -n '/^verify_module_tree()/,/^}/p' "${BASH_SOURCE[0]}")
  bash "$script_dir/../test-module-tree.sh"
  [[ $# == 1 ]] || { printf 'Usage: %s BUILD_ROOT\n' "$0" >&2; exit 2; }
  build_root=$(realpath -e "$1")
  release=7.1.12-dev147-clearwait100
  source_commit=d2f36591abdb0db296ac24e5a2b9dade5ae40ef1
  config_hash=f69e63e55cbc6b257a951c82b3e581ffc60d4614a5965561cbc322960767bdff
  candidate="$build_root/artifacts/candidate-$release"
  module_root="$build_root/artifacts/root/lib/modules/$release"

  for artifact in Image t8112-j413.dtb config System.map Module.symvers modules.order modules.sha256 kernelrelease.txt source-commit.txt source.bundle SHA256SUMS; do
    [[ -s $candidate/$artifact ]] || { printf 'FAIL: missing candidate artifact %s\n' "$artifact" >&2; exit 1; }
  done
  [[ -s $module_root/modules.dep && -s $module_root/modules.builtin ]]
  [[ $(git -C "$build_root/linux" rev-parse HEAD) == "$source_commit" ]]
  [[ -z $(git -C "$build_root/linux" status --porcelain) ]]
  [[ $(cat "$candidate/kernelrelease.txt") == "$release" ]]
  [[ $(cat "$candidate/source-commit.txt") == "$source_commit" ]]
  printf '%s  %s\n' "$config_hash" "$candidate/config" | sha256sum --check --strict
  (cd "$candidate" && sha256sum --check --strict SHA256SUMS)
  (cd "$build_root/artifacts/root" && sha256sum --check --strict "$candidate/modules.sha256")

  git -C "$build_root/linux" bundle verify "$candidate/source.bundle"
  [[ $(git -C "$build_root/linux" bundle list-heads "$candidate/source.bundle" HEAD) == "$source_commit HEAD" ]]

  "$build_root/build-command.sh" Image modules apple/t8112-j413.dtb > "$build_root/logs/offline-gate-make.log" 2>&1
  cmp "$candidate/Image" "$build_root/build/arch/arm64/boot/Image"
  cmp "$candidate/t8112-j413.dtb" "$build_root/build/arch/arm64/boot/dts/apple/t8112-j413.dtb"
  cmp "$candidate/config" "$build_root/build/.config"
  cmp "$candidate/System.map" "$build_root/build/System.map"
  cmp "$candidate/Module.symvers" "$build_root/build/Module.symvers"
  cmp "$candidate/modules.order" "$build_root/build/modules.order"
  verify_module_tree "$build_root/build" "$module_root"
  [[ $(od -An -tx1 -j56 -N4 "$candidate/Image" | tr -d ' \n') == "41524d64" ]]
  readelf -hW "$build_root/build/vmlinux" | rg 'Machine:.*AArch64' > /dev/null
  readelf -SW "$build_root/build/vmlinux" | rg '\.BTF[[:space:]]' > /dev/null
  rg '(^|/)drivers/gpu/drm/asahi/asahi\.ko$' "$module_root/modules.builtin" > /dev/null

  for symbol in RUST ARM64_16K_PAGES DRM_ASAHI DRM_APPLE_AUDIO DEBUG_INFO_BTF DEBUG_INFO_BTF_MODULES; do
    rg -x "CONFIG_$symbol=y" "$candidate/config" > /dev/null
  done
  for symbol in DRM_APPLE APPLE_SIO TYPEC_TPS6598X_CORE TYPEC_DP_ALTMODE PHY_APPLE_ATC USB_DWC3_APPLE; do
    rg -x "CONFIG_$symbol=m" "$candidate/config" > /dev/null
  done

  module_count=0
  while IFS= read -r -d '' module; do
    [[ $(modinfo -F vermagic "$module") == "$release "* ]]
    ((module_count += 1))
  done < <(find "$module_root/kernel" -type f -name '*.ko*' -print0)
  (( module_count == 1862 ))
  for name in appledrm apple-sio tps6598x-core phy-apple-atc; do
    modinfo -b "$build_root/artifacts/root" -k "$release" "$name" > /dev/null
  done
  depmod -n -e -F "$candidate/System.map" -b "$build_root/artifacts/root" "$release" > "$build_root/logs/offline-gate-depmod.stdout" 2> "$build_root/logs/offline-gate-depmod.stderr"
  [[ ! -s $build_root/logs/offline-gate-depmod.stderr ]]

  printf '%s  %s\n' 394f14849cc9861e435f2896d819ef422d0090d99ab2bc7b68cde1e65fbc733f "$build_root/afk-harness/harness.c" | sha256sum --check --strict
  cc -std=c11 -Wall -Wextra -Werror -Wno-unused-parameter "$build_root/afk-harness/harness.c" -o "$build_root/logs/offline-gate-afk"
  for mode in stock unsafe unsafe-send unsafe-race; do
    if "$build_root/logs/offline-gate-afk" "$mode" > "$build_root/logs/offline-gate-afk-$mode.stdout" 2> "$build_root/logs/offline-gate-afk-$mode.stderr"; then
      printf 'FAIL: AFK negative control passed: %s\n' "$mode" >&2
      exit 1
    else
      [[ $? == 1 ]]
    fi
  done
  rg '^CAPACITY:' "$build_root/logs/offline-gate-afk-stock.stderr" > /dev/null
  rg '^UNSAFE_REUSE:' "$build_root/logs/offline-gate-afk-unsafe.stderr" > /dev/null
  rg '^UNSAFE_SEND:' "$build_root/logs/offline-gate-afk-unsafe-send.stderr" > /dev/null
  rg '^UNSAFE_RACE:' "$build_root/logs/offline-gate-afk-unsafe-race.stderr" > /dev/null
  "$build_root/logs/offline-gate-afk" candidate

  export LD_LIBRARY_PATH="$build_root/tools/root/usr/lib"
  fdtget="$build_root/tools/root/usr/bin/fdtget"
  dtb="$candidate/t8112-j413.dtb"
  [[ $("$fdtget" -t s "$dtb" / compatible) == "apple,j413 apple,t8112 apple,arm-platform" ]]
  for node in /soc/dcp@271c00000 /soc/sio@236400000 /soc/audio-controller@238334000; do
    [[ $("$fdtget" -t s "$dtb" "$node" status) == "okay" ]]
  done
  [[ $("$fdtget" -t s "$dtb" /aliases dcpext) == "/soc/dcp@271c00000" ]]
  [[ $("$fdtget" -t s "$dtb" /aliases sio) == "/soc/sio@236400000" ]]
  [[ $("$fdtget" -t x "$dtb" /soc/i2c@235010000/usb-pd@3f/connector displayport) == "$("$fdtget" -t x "$dtb" /soc/dcp@271c00000 phandle)" ]]
  [[ $("$fdtget" -t x "$dtb" /soc/audio-controller@238334000 dmas) == "$("$fdtget" -t x "$dtb" /soc/sio@236400000 phandle) 66" ]]
  printf 'PASS: offline source, build, %s modules, AFK controls, and J413 DP/SIO wiring\n' "$module_count"
  printf 'LIMIT: inherited DT schema findings, boot assembly, firmware preparation, and hardware acceptance are separate.\n'
}

if [[ ${BASH_SOURCE[0]} == "$0" ]]; then
  main "$@"
fi
