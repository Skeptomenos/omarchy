#!/bin/bash
set -euo pipefail
[[ $# == 2 ]]
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
build_root=$(realpath -e "$1")
output=$(realpath -m "$2")
candidate="$build_root/artifacts/candidate-7.1.12-dev147-fairydust1"
[[ ! -e $output && $(cat "$candidate/kernelrelease.txt") == "7.1.12-dev147-fairydust1" ]]
(cd "$candidate" && sha256sum --check --strict --status SHA256SUMS)
(cd "$build_root/artifacts/root" && sha256sum --check --strict --status "$candidate/modules.sha256")
mkdir -p "$output"
sha256sum "$script_dir"/*.sh > "$output/builder.sha256"
bwrap --unshare-all --die-with-parent --new-session --uid 0 --gid 0 \
  --ro-bind /usr /usr --ro-bind /etc /etc \
  --symlink usr/lib /lib --symlink usr/bin /bin --symlink usr/bin /sbin \
  --proc /proc --dev /dev --tmpfs /tmp --dir /sys --dir /run --dir /home \
  --bind "$output" /work --ro-bind "$build_root/artifacts/root" /candidate \
  --ro-bind "$candidate/Image" /kernel-image --ro-bind "$script_dir" /recipe \
  --clearenv --setenv PATH /usr/bin --setenv HOME /tmp --setenv LC_ALL C \
  --chdir /work /usr/bin/fakeroot /usr/bin/bash /recipe/build-inner.sh > "$output/mkinitcpio.log" 2>&1
bash "$script_dir/verify.sh" "$output/extracted" "$build_root" > "$output/verification.log" 2>&1
jq -n --arg image "$output/initramfs-7.1.12-dev147-fairydust1.img" \
  --arg hash "$(sha256sum "$output/initramfs-7.1.12-dev147-fairydust1.img" | cut -d ' ' -f1)" \
  --arg source "$(cat "$candidate/source-commit.txt")" \
  '{status:"PASS",image:$image,image_sha256:$hash,source_commit:$source,kernelrelease:"7.1.12-dev147-fairydust1",offline:true,installed:false,hardware_validated:false,autodetect:false}' > "$output/receipt.json"
(cd "$output" && sha256sum initramfs-*.img *.conf *.txt *.sha256 receipt.json > SHA256SUMS)
cat "$output/verification.log"
