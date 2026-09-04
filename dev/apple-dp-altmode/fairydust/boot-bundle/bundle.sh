#!/bin/bash
set -euo pipefail

[[ $# == 3 && ( $1 == assemble || $1 == verify ) ]] || { printf 'Usage: %s assemble|verify BUILD_ROOT BUNDLE\n' "$0" >&2; exit 2; }
action=$1
build_root=$(realpath -e "$2")
bundle=$3
m1n1=/usr/lib/asahi-boot/m1n1.bin
uboot=/usr/lib/asahi-boot/u-boot-nodtb.bin
dtb="$build_root/artifacts/candidate-7.1.12-dev147-fairydust1/t8112-j413.dtb"
[[ ! -L $m1n1 && ! -L $uboot && ! -L $dtb && -f $m1n1 && -f $uboot && -f $dtb ]]
printf '%s  %s\n' \
  9ad086536d4b4f871530ad5231bf8eea8063bbf5ff9189ae713584ed74158fdd "$m1n1" \
  ef3a78ee1820d5fb296a957e34affa4c64a14fa274e069f6fec46d125354e14c "$uboot" \
  9831d42f9c271ce35dd3e32b5c8298e1c13849568853aea0779f40bb67377b80 "$dtb" | sha256sum --check --strict
[[ $(stat -c '%s' "$m1n1") == 1114112 && $(stat -c '%s' "$dtb") == 72115 ]]
export LD_LIBRARY_PATH="$build_root/tools/root/usr/lib"
fdtget="$build_root/tools/root/usr/bin/fdtget"
[[ $("$fdtget" -t s "$dtb" / compatible) == 'apple,j413 apple,t8112 apple,arm-platform' ]]
[[ $("$fdtget" -t s "$dtb" /aliases sio) == /soc/sio@236400000 ]]
[[ $("$fdtget" -t s "$dtb" /aliases dcpext) == /soc/dcp@271c00000 ]]
if [[ $action == assemble ]]; then
  (( EUID != 0 ))
  [[ ! -e $bundle && ! -L $bundle ]]
  [[ $(realpath -e "$(dirname -- "$bundle")") == "$(dirname -- "$bundle")" ]]
  [[ ! -e /etc/m1n1.conf && ! -L /etc/m1n1.conf ]]
  (
    set -o noclobber
    umask 077
    { cat "$m1n1" "$dtb"; gzip -n -9 -c "$uboot"; } > "$bundle"
  )
fi
[[ -f $bundle && ! -L $bundle ]]
expected_size=$((1114112 + 72115 + $(gzip -n -9 -c "$uboot" | wc -c)))
[[ $(stat -c '%s' "$bundle") == "$expected_size" ]]
cmp "$m1n1" <(head -c 1114112 "$bundle")
cmp "$dtb" <(dd if="$bundle" bs=1M skip=1114112 count=72115 iflag=skip_bytes,count_bytes status=none)
cmp <(gzip -n -9 -c "$uboot") <(tail -c +1186228 "$bundle")
printf 'PASS: exact m1n1 1.6.1 + J413 DT + gzip U-Boot\n'
sha256sum "$bundle"
