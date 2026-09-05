#!/bin/bash
set -euo pipefail
[[ $# == 3 ]] || { printf 'Usage: %s INITRAMFS_RUN INITRAMFS_GATE_DIRECTORY BUILD_GATE_LOG\n' "$0" >&2; exit 2; }
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
source "$script_dir/../validate-build.sh"
root=/home/david/Work/dev147-clear-wait-trial
release=7.1.12-dev147-clearwait100
commit=d2f36591abdb0db296ac24e5a2b9dade5ae40ef1
config_hash=f69e63e55cbc6b257a951c82b3e581ffc60d4614a5965561cbc322960767bdff
candidate="$root/artifacts/candidate-$release"
baseline=/home/david/Work/dev147-fairydust-build/artifacts/candidate-7.1.12-dev147-fairydust1
modules="$root/artifacts/root/lib/modules/$release"
delivery="$root/delivery"
run=$(realpath -e "$1")
gate=$(realpath -e "$2")
build_log=$(realpath -e "$3")
image="$run/initramfs-$release.img"
umask 077
[[ ! -e $delivery && ! -L $delivery ]]
[[ $run == "$root/initramfs/"* && $gate == "$root/checks/"* && $build_log == "$root/"* ]]
[[ $(cat "$build_log.exit-status") == 0 && $(cat "$gate/exit-status") == 0 ]]
rg -Fx 'PASS: offline source, build, 1862 modules, AFK controls, and J413 DP/SIO wiring' "$build_log" > /dev/null
rg -Fx 'PASS: offline initramfs bytes, startup, modules, and negative controls; no boot or hardware acceptance.' "$gate/result.txt" > /dev/null
for name in source.sha256 module-controls.log startup-controls.log truncated-control.log image.log; do
  [[ -s $gate/$name ]]
done
for name in receipt.json SHA256SUMS mkinitcpio.log verification.log builder.sha256 host-recipe.sha256 firmware-inputs.sha256; do
  [[ -s $run/$name ]]
done
for name in source-commit.txt kernelrelease.txt bundle-base.txt source.bundle build-command.sh; do
  [[ -s $candidate/$name ]]
done
build_evidence=("$root/logs/offline-gate-make.log" "$root/logs/offline-gate-depmod.stdout" "$root/logs/offline-gate-depmod.stderr")
for mode in stock unsafe unsafe-send unsafe-race; do
  build_evidence+=("$root/logs/offline-gate-afk-$mode.stdout" "$root/logs/offline-gate-afk-$mode.stderr")
done
for name in "${build_evidence[@]}"; do
  [[ -f $name && ! -L $name ]]
done
patches=("$candidate"/*.patch)
[[ ${#patches[@]} == 3 ]]
[[ $(git -C "$root/linux" rev-parse HEAD) == "$commit" && -z $(git -C "$root/linux" status --porcelain) ]]
[[ $(cat "$candidate/source-commit.txt") == "$commit" && $(cat "$candidate/kernelrelease.txt") == "$release" ]]
printf '%s  %s\n' "$config_hash" "$candidate/config" | sha256sum --check --strict
(cd "$candidate" && sha256sum --check --strict --status SHA256SUMS)
(cd "$root/artifacts/root" && sha256sum --check --strict --status "$candidate/modules.sha256")
(cd "$run" && sha256sum --check --strict --status SHA256SUMS)
verify_module_tree "$root/build" "$modules"
[[ $(find "$modules/kernel" -type f -name '*.ko' -printf '.\n' | wc -l) == 1862 ]]
cmp "$candidate/Image" "$root/build/arch/arm64/boot/Image"
cmp "$candidate/config" "$root/build/.config"
cmp "$candidate/t8112-j413.dtb" "$baseline/t8112-j413.dtb"
cmp "$candidate/t8112-j413.dtb" "$root/build/arch/arm64/boot/dts/apple/t8112-j413.dtb"
printf '%s  %s\n' 9831d42f9c271ce35dd3e32b5c8298e1c13849568853aea0779f40bb67377b80 "$candidate/t8112-j413.dtb" | sha256sum --check --strict
image_hash=$(sha256sum "$image" | cut -d ' ' -f1)
kernel_image_hash=$(sha256sum "$candidate/Image" | cut -d ' ' -f1)
jq -e --arg release "$release" --arg commit "$commit" --arg image "$image" --arg hash "$image_hash" \
  '.status == "PASS" and .kernelrelease == $release and .source_commit == $commit and .image == $image and .image_sha256 == $hash and .offline == true and .installed == false and .hardware_validated == false and .autodetect == false' "$run/receipt.json" > /dev/null
image_checks=("$gate"/image-validation.*/image.sha256)
[[ ${#image_checks[@]} == 1 && -f ${image_checks[0]} ]]
cmp "${image_checks[0]}" <(printf '%s  %s\n' "$image_hash" "$image")
[[ $(find "$modules" -type l -printf '%P\n') == build ]]
[[ -z $(find "$modules" ! -type f ! -type d ! -type l -print -quit) ]]
mkdir "$delivery"
mkdir -p "$delivery/root/lib/modules" "$delivery/receipts/kernel-source" "$delivery/receipts/build-gate" "$delivery/receipts/initramfs-run" "$delivery/receipts/initramfs-gate"
cp --reflink=auto "$candidate/Image" "$candidate/config" "$delivery/"
cp --reflink=auto "$image" "$delivery/initramfs.img"
printf '%s  %s\n' "$kernel_image_hash" "$delivery/Image" "$image_hash" "$delivery/initramfs.img" "$config_hash" "$delivery/config" | sha256sum --check --strict
cp -a --reflink=auto "$modules" "$delivery/root/lib/modules/"
unlink "$delivery/root/lib/modules/$release/build"
verify_module_tree "$root/build" "$delivery/root/lib/modules/$release"
cp "$candidate/modules.sha256" "$delivery/modules.sha256"
cp "$run/receipt.json" "$delivery/receipts/initramfs.json"
cp "$build_log" "$delivery/receipts/build-gate.log"
cp "$build_log.exit-status" "$delivery/receipts/build-gate.exit-status"
cp "${build_evidence[@]}" "$delivery/receipts/build-gate/"
for name in SHA256SUMS source-commit.txt kernelrelease.txt bundle-base.txt source.bundle build-command.sh; do
  cp "$candidate/$name" "$delivery/receipts/kernel-source/$name"
done
cp "$candidate"/*.patch "$delivery/receipts/kernel-source/"
for kind in initramfs-run initramfs-gate; do
  evidence="$run"
  [[ $kind != "initramfs-gate" ]] || evidence="$gate"
  (
    cd "$evidence"
    while IFS= read -r -d '' name; do
      cp --parents "$name" "$delivery/receipts/$kind/"
    done < <(find . -type f \( -name '*.log' -o -name '*.json' -o -name '*.txt' -o -name '*.conf' -o -name '*.sha256' -o -name '*.stdout' -o -name '*.stderr' -o -name '*exit-status' -o -name SHA256SUMS \) -not -path '*/extracted/*' -not -path '*/build/*' -print0)
  )
done
jq -n --arg release "$release" --arg commit "$commit" --arg config "$config_hash" \
  --arg image "$kernel_image_hash" \
  --arg dt "$(sha256sum "$candidate/t8112-j413.dtb" | cut -d ' ' -f1)" \
  '{status:"PASS_OFFLINE_ONLY",kernelrelease:$release,source_commit:$commit,config_sha256:$config,image_sha256:$image,dtb_sha256:$dt,dtb_matches_fairydust1:true,module_count:1862,esp_update_required:false,installed:false,hardware_validated:false,build_gate:"receipts/build-gate.log",initramfs_gate:"receipts/initramfs-gate",evidence_scope:"Original check receipts and text logs retained; extracted images and large module fixtures excluded."}' > "$delivery/receipts/kernel-source-config.json"
(cd "$delivery/root" && sha256sum --check --strict --status ../modules.sha256)
[[ -z $(find "$delivery" ! -type f ! -type d -print -quit) ]]
[[ -z $(find "$delivery" -type f -links +1 -print -quit) ]]
(
  cd "$delivery"
  find . -type f ! -path ./SHA256SUMS -printf '%P\0' | LC_ALL=C sort -z | xargs -0 sha256sum > SHA256SUMS
  sha256sum --check --strict --status SHA256SUMS
)
printf 'ASSEMBLED_UNSTAGED: %s\n' "$delivery"
sha256sum "$delivery/SHA256SUMS"
