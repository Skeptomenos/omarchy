#!/bin/bash
set -euo pipefail
umask 077

[[ $EUID == 1001 && $PWD == /work && ! -e /proc && ! -e /sys && ! -e /boot ]] || exit 1
for module in dwc3-apple phy-apple-atc; do
  candidate="/inputs/modules/control/$module.ko"
  stock="/inputs/modules/stock/$module.ko"
  for field in name vermagic depends alias; do
    actual=$(/usr/bin/modinfo -F "$field" "$candidate")
    expected=$(/usr/bin/modinfo -F "$field" "$stock")
    [[ $actual == "$expected" ]] || {
      printf 'STOP: control %s differs in %s\n' "$module" "$field" >&2
      exit 1
    }
  done
  /usr/bin/nm -u "$candidate" | /usr/bin/sort >"/work/$module.imports"
  /usr/bin/nm -u "$stock" | /usr/bin/sort >"/work/$module.stock-imports"
  /usr/bin/cmp "/work/$module.imports" "/work/$module.stock-imports"
  /usr/bin/readelf -S "$candidate" >"/work/$module.sections"
  /usr/bin/grep -E '\.BTF[[:space:]]' "/work/$module.sections"
  /usr/bin/readelf -n "$candidate"
  /usr/bin/modinfo "$candidate"
  printf 'CONTROL ABI/BTF PASS: %s\n' "$module"
done
printf 'VERDICT: PASS; metadata only, no module loaded\n'
