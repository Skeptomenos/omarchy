#!/bin/bash
set -euo pipefail
umask 077

[[ $EUID == 1001 && $PWD == /work && ! -e /proc && ! -e /sys && ! -e /boot ]] || exit 1
printf '%s  %s\n' \
  2ce7c85eb7d5324d13629a1030436d8350cb426cd646cf43cd40c0dbd8c1c752 /inputs/source/dwc3-apple.c \
  852f5d8e19894473390fc74464496029e20ef440aef37618cf530264b49cb113 /inputs/source/atc.c \
  daf576b4c5748e4cc6072db983e4c87331a2846764602de3aa96b7aac0cd90f8 /inputs/source/glue.h \
  eb4d2c4130f0c8d88dbc3b99be05363131b4503945f0e2fd46eb0d6edd88797a /inputs/source/core.h \
  137a58ad1417e413962dbe6e91dbb0b2385fbc8733db7d4ecf659959cd9bac82 /inputs/headers/Makefile \
  d5eea549b9333f717fdc932683ea6633d58049c1e3f8f9e0be12e05d7610dd82 /inputs/headers/Module.symvers \
  701d1270a36cb57047558ab78e7d825900cc76935e42fd96003c319d1b9050e4 /inputs/headers/.config \
  6720f51a6a3b0f439e5d74fb07acfcd75bed599fd333c819eb3b1ced441f56ed /inputs/pahole/usr/bin/pahole \
  68e844d07125b4e59a183e7d07e80413a30999ffc1ef30d7a279d73431c1018d /inputs/runtime/libdw.so.1 \
  | /usr/bin/sha256sum --check --strict

export LD_LIBRARY_PATH=/inputs/pahole/usr/lib:/inputs/runtime
[[ $(/inputs/pahole/usr/bin/pahole --version) == "v1.31" ]] || exit 1
/usr/bin/mkdir /work/diagnostic
/usr/bin/cp /inputs/source/dwc3-apple.c /inputs/source/atc.c \
  /inputs/source/glue.h /inputs/source/core.h /inputs/recipe/Makefile /work/diagnostic/
cd /work/diagnostic
/usr/bin/make -f /inputs/headers/Makefile M=/work/diagnostic \
  ARCH=arm64 PAHOLE=/inputs/pahole/usr/bin/pahole -j2 modules

for module in dwc3-apple phy-apple-atc; do
  /usr/bin/sha256sum "$module.ko"
  /usr/bin/readelf -n -S "$module.ko"
  /usr/bin/modinfo "$module.ko"
  for field in name vermagic depends alias; do
    actual=$(/usr/bin/modinfo -F "$field" "$module.ko")
    expected=$(/usr/bin/modinfo -F "$field" "/inputs/controls/$module.ko")
    [[ $actual == "$expected" ]] || {
      printf 'STOP: diagnostic %s differs in %s\n' "$module" "$field" >&2
      exit 1
    }
  done
  /usr/bin/nm -u "$module.ko" | /usr/bin/sort >"$module.imports"
  /usr/bin/nm -u "/inputs/controls/$module.ko" | /usr/bin/sort >"$module.control-imports"
  if /usr/bin/diff -u "$module.control-imports" "$module.imports"; then
    printf 'No import delta for %s\n' "$module"
  else
    printf 'Import delta retained for independent review: %s\n' "$module"
  fi
done
printf 'DIAGNOSTIC BUILD AND BASIC METADATA CHECKS PASS; imports and cap still need review; no module loaded\n'
