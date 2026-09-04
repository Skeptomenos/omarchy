#!/bin/bash
set -euo pipefail
[[ $# == 0 ]] || exit 2
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo=$(realpath "$script_dir/../../..")
build=/home/david/Work/dev147-fairydust-build
boot=/home/david/Work/dev147-fairydust-boot-20260905
delivery="$boot/delivery"
checks=$(mktemp -d "$boot/checks/offline-gate.XXXXXXXX")
printf 'Validation logs: %s\n' "$checks"
printf '%s  %s\n' f33054856e60d3baf5cb7630cb8d7dfc60ffa586e16456c3e7313fffe6f7c59d "$delivery/SHA256SUMS" | sha256sum --check --strict > "$checks/manifest-pin.log"
(cd "$delivery" && sha256sum --check --strict SHA256SUMS) > "$checks/delivery.log"
bash "$script_dir/validate-offline.sh" "$build" > "$checks/kernel.log" 2>&1
source "$script_dir/validate-offline.sh"
verify_module_tree "$build/build" "$delivery/root/lib/modules/7.1.12-dev147-fairydust1" > "$checks/modules.log" 2>&1
for name in Image config t8112-j413.dtb; do
  cmp "$delivery/$name" "$build/artifacts/candidate-7.1.12-dev147-fairydust1/$name"
done
bash "$script_dir/boot-bundle/bundle.sh" verify "$build" "$delivery/boot.bin" > "$checks/bundle.log" 2>&1
bash "$script_dir/boot-bundle/test-bundle.sh" "$build" "$delivery/boot.bin" > "$checks/bundle-tests.log" 2>&1
bash "$script_dir/boot-initramfs/validate-image.sh" "$delivery/initramfs.img" "$build" "$checks" > "$checks/initramfs.log" 2>&1
startup_check=$(find "$checks" -mindepth 1 -maxdepth 1 -type d -name 'image-validation.*')
[[ -d $startup_check/extracted ]]
bash "$script_dir/boot-initramfs/test-startup.sh" "$startup_check/extracted" "$checks" > "$checks/startup-tests.log" 2>&1
bash "$script_dir/boot-initramfs/test-verify.sh" "$build" "$checks" > "$checks/initramfs-tests.log" 2>&1
bash "$script_dir/boot-initramfs/test-image.sh" "$delivery/initramfs.img" "$build" "$checks" > "$checks/initramfs-truncated.log" 2>&1
for script in "$script_dir"/boot-bundle/*.sh "$script_dir"/boot-initramfs/*.sh "$script_dir"/boot-stage/*.sh; do
  bash -n "$script"
done
ruff="$boot/stage/uv-cache/archive-v0/NN8oF-CHP05mnrav/bin/ruff"
mypy="$boot/stage/uv-cache/archive-v0/BzCSLx7VfLpHd_Z9/bin/mypy"
"$ruff" check "$script_dir/boot-stage" > "$checks/ruff.log"
"$ruff" format --check --config 'indent-width=2' "$script_dir/boot-stage" > "$checks/format.log"
"$mypy" --strict --cache-dir="$checks/mypy-cache" "$script_dir/boot-stage" > "$checks/mypy.log"
python3 "$script_dir/boot-stage/test_stage.py" > "$checks/stage-tests.log" 2>&1
cp -a "$boot/stage/full-delivery-sandbox" "$checks/prior-stage-run"
python3 "$script_dir/boot-stage/test_full_delivery.py" > "$checks/stage-full.log" 2>&1
cp -a "$boot/stage/full-delivery-sandbox" "$checks/stage-run"
printf '%s  %s\n' \
  203ab7027536c8d16f373d02c1f6346a5c34cfe095a9dafd0cfe37d2b354090c /boot/efi/m1n1/boot.bin \
  469820ad7cfd015a22cff979b0aa70d62e82dcc7cc05951dca92f40cd660f2bd /etc/pacman.d/hooks/05-omarchy-m2-displayport-guard.hook \
  7c2ce145ec9bb390c2377e6e83d1aacc3817dd227909b0e62b0febe96d2f451f /boot/efi/vendorfw/firmware.cpio \
  2f3ab6e0d7d2fb8ab11746094c1d02a3ef00da9a8037bfdac583eb4b8d31cea1 /usr/lib/firmware/vendor/.vendorfw.manifest | sha256sum --check --strict > "$checks/live-pins.log"
git -C "$repo" diff --check
printf 'PASS: complete offline boot delivery and unselected staging rehearsal\n' | tee "$checks/result.txt"
printf 'LIMIT: real staging, selected-boot activation, rollback execution and hardware acceptance remain open.\n'
