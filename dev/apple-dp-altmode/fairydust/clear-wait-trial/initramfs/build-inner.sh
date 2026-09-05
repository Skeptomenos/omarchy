#!/bin/bash
set -euo pipefail
[[ $PWD == "/work" && $EUID == 0 && ! -e /boot && ! -e /sys/devices ]]
[[ ! -w /usr && ! -w /etc && ! -w /candidate ]]
export KERNELVERSION=7.1.12-dev147-clearwait100
set +u
source /etc/mkinitcpio.conf
for config in /etc/mkinitcpio.conf.d/*.conf; do
  source "$config"
done
set -u
declare -p MODULES BINARIES FILES HOOKS > effective-host.conf
offline_hooks=()
for hook in "${HOOKS[@]}"; do
  [[ $hook == "autodetect" ]] || offline_hooks+=("$hook")
done
HOOKS=("${offline_hooks[@]}")
MODULES+=(appledrm apple-sio tps6598x-core phy-apple-atc dwc3-apple apple-avd)
FILES+=(/usr/lib/firmware/apple/avd-fw-*.bin)
COMPRESSION=gzip
COMPRESSION_OPTIONS=(-n)
MODULES_DECOMPRESS=no
declare -p MODULES BINARIES FILES HOOKS COMPRESSION COMPRESSION_OPTIONS MODULES_DECOMPRESS > mkinitcpio.conf
sha256sum /usr/bin/mkinitcpio /usr/bin/lsinitcpio /usr/lib/initcpio/functions /etc/mkinitcpio.conf /etc/mkinitcpio.conf.d/*.conf /usr/lib/initcpio/install/* /usr/lib/initcpio/hooks/* > host-recipe.sha256
sha256sum /usr/lib/firmware/vendor/.vendorfw.manifest /usr/lib/firmware/apple/avd-fw-*.bin > firmware-inputs.sha256
mkdir build
mkinitcpio --nopost -n -c /work/mkinitcpio.conf -k /kernel-image -r /candidate -g /work/initramfs-7.1.12-dev147-clearwait100.img -t /work/build
lsinitcpio -l initramfs-7.1.12-dev147-clearwait100.img > inventory.txt
lsinitcpio -c initramfs-7.1.12-dev147-clearwait100.img > embedded-config.txt
mkdir extracted
cd extracted
lsinitcpio -x ../initramfs-7.1.12-dev147-clearwait100.img
