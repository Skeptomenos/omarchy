#!/bin/bash

# David runs this with bash, never sudo. Only the three fixed readers use sudo.
# No extraction, staging, boot changes, or privileged destination is permitted.
readonly DPALT_STOCK_IMAGE_SHA="625641095075a9a2396bc701ffd48ac58f2c8a1758e250fa3f6b55b29dcae296"

dpalt_readback_manifest() {
  printf '%s\n' \
    '625641095075a9a2396bc701ffd48ac58f2c8a1758e250fa3f6b55b29dcae296  /boot/initramfs-linux-asahi.img' \
    '68c36bbbb3c530dba8647f9435252da53adf53942b37b76e399ccd234cc0f24d  /boot/grub/grub.cfg'
}

dpalt_grub_filter() {
  printf '%s\n' \
    '/^[[:space:]]*(menuentry|submenu|initrd|initrdefi|search)[[:space:]]|^[[:space:]]*set[[:space:]]+(root|default)=/ {print NR ":" $0}' \
    '/^[[:space:]]*(linux|linuxefi)[[:space:]]/ {print NR ":" $1 " " $2 " [arguments omitted]"}'
}

dpalt_readback_check() {
  [[ ! -e /var/lib/pacman/db.lck && ! -L /var/lib/pacman/db.lck ]] || dpalt_die "package transaction is active"
  dpalt_readback_manifest | dpalt_clean /usr/bin/sudo /usr/bin/sha256sum --check --strict
}

dpalt_write_private_image() {
  dpalt_clean /usr/bin/dd of="$1" bs=1M iflag=fullblock conv=excl,fsync status=none
}

dpalt_readback_main() {
  set -Eeuo pipefail
  umask 077
  dpalt_require_user "$EUID"
  dpalt_check_environment
  [[ $# == 2 && $1 == "--output" ]] || dpalt_die "usage: bash read-protected-stock.sh --output NEW_PRIVATE_PERSISTENT_DIRECTORY"
  local output filter
  output=$(dpalt_persistent_output "$2") || exit 1
  [[ ! -e /var/lib/pacman/db.lck && ! -L /var/lib/pacman/db.lck ]] || dpalt_die "package transaction is active"
  filter=$(dpalt_grub_filter)
  dpalt_clean mkdir -m 0700 -- "$output"
  printf 'INCOMPLETE protected-stock readback. No staging or boot permission.\n' >"$output/INCOMPLETE"
  dpalt_readback_check >"$output/stock.before.log"
  dpalt_clean /usr/bin/sudo /usr/bin/cat /boot/initramfs-linux-asahi.img |
    dpalt_write_private_image "$output/stock-initramfs.img"
  dpalt_check_hash "$output/stock-initramfs.img" "$DPALT_STOCK_IMAGE_SHA"
  dpalt_clean /usr/bin/sudo /usr/bin/awk "$filter" /boot/grub/grub.cfg >"$output/grub-filtered.txt"
  dpalt_readback_check >"$output/stock.after.log"
  dpalt_clean chmod 0600 -- "$output/stock-initramfs.img"
  dpalt_clean sha256sum -- "$output/stock-initramfs.img" >"$output/stock-copy.sha256"
  dpalt_clean date --utc --iso-8601=seconds >"$output/captured-at.txt"
  printf 'Private readback only. No extraction, staging, or boot was performed or authorized.\n' >"$output/READBACK-ONLY.txt"
  dpalt_clean mv -T -- "$output/INCOMPLETE" "$output/readback-start-marker.txt"
  printf 'Readback captured only: %s\nNot staging or boot permission. Keep this archive private.\n' "$output"
}

if [[ ${BASH_SOURCE[0]} == "$0" ]]; then
  source "${BASH_SOURCE[0]%/*}/prepare-one-boot-initramfs.sh"
  dpalt_readback_main "$@"
fi
