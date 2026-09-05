#!/bin/bash
set -euo pipefail
[[ $# == 1 ]] || exit 2
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
root=/home/david/Work/dev147-clear-wait-trial
image=$(realpath -e "$1")
umask 077
mkdir -p "$root/checks"
checks=$(mktemp -d "$root/checks/initramfs.XXXXXXXX")
trap 'status=$?; printf "%s\n" "$status" > "$checks/exit-status"' EXIT
printf 'Trial initramfs gate: %s\n' "$checks"
for script in "$script_dir"/*.sh; do
  bash -n "$script"
done
bash "$script_dir/test-verify.sh" "$root" "$checks" > "$checks/module-controls.log" 2>&1
bash "$script_dir/validate-image.sh" "$image" "$root" "$checks" > "$checks/image.log" 2>&1
extracted=("$checks"/image-validation.*/extracted)
[[ ${#extracted[@]} == 1 && -d ${extracted[0]} ]]
bash "$script_dir/test-startup.sh" "${extracted[0]}" "$checks" > "$checks/startup-controls.log" 2>&1
bash "$script_dir/test-image.sh" "$image" "$root" "$checks" > "$checks/truncated-control.log" 2>&1
sha256sum "$script_dir"/*.sh > "$checks/source.sha256"
printf 'PASS: offline initramfs bytes, startup, modules, and negative controls; no boot or hardware acceptance.\n' | tee "$checks/result.txt"
