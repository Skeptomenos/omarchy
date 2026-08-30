#!/bin/bash
set -euo pipefail
umask 077

# Private workload only. The reviewed launcher owns isolation and the outer deadline.
SOURCE_MANIFEST_SHA256=cc413aa2a31a2579ef06afd75f641fcc2e5ecf44f59333d2dd62a809600d82b2
COMPANION_SHA256=cf6c9145c03878418d21958328a3bce2c70a489a1fa80d2ecc19a23107758da0
[[ $EUID == 1001 && $PWD == /work && ! -e /proc && ! -e /sys && ! -e /boot ]] || exit 1
[[ $# == 1 && ($1 == baseline || $1 == patched) ]] || exit 1
[[ $SOURCE_MANIFEST_SHA256 =~ ^[0-9a-f]{64}$ && $COMPANION_SHA256 =~ ^[0-9a-f]{64}$ ]] || {
  printf 'STOP: reviewed source-manifest/companion binding is incomplete\n' >&2
  exit 1
}
printf '%s  %s\n' \
  "$SOURCE_MANIFEST_SHA256" /inputs/source-manifest \
  "$COMPANION_SHA256" /inputs/recipe/build_support.py \
  58413a7a58c2084f87ecded07f959dc7acec871633fbc23d8e3630367c662b6b /inputs/upstream-patch \
  137a58ad1417e413962dbe6e91dbb0b2385fbc8733db7d4ecf659959cd9bac82 /inputs/headers/Makefile \
  d5eea549b9333f717fdc932683ea6633d58049c1e3f8f9e0be12e05d7610dd82 /inputs/headers/Module.symvers \
  701d1270a36cb57047558ab78e7d825900cc76935e42fd96003c319d1b9050e4 /inputs/headers/.config \
  32b70e3a145454b430a0c9375a67ce93b30e0ee6afdefba590aac6f92ead4e15 /inputs/headers/vmlinux \
  6720f51a6a3b0f439e5d74fb07acfcd75bed599fd333c819eb3b1ced441f56ed /inputs/pahole/usr/bin/pahole \
  68e844d07125b4e59a183e7d07e80413a30999ffc1ef30d7a279d73431c1018d /inputs/runtime/libdw.so.1 \
  dbffe74e13a43e15e47fdc5eafe32eb1829b114a3f02f15fe6b18507d622b0e3 /inputs/stock/appledrm.ko \
  | /usr/bin/sha256sum --check --strict

# Both variants use exactly the same source/output path and unmodified native Makefile.
export LD_LIBRARY_PATH=/inputs/pahole/usr/lib:/inputs/runtime
[[ $(/inputs/pahole/usr/bin/pahole --version) == "v1.31" ]] || exit 1
/usr/bin/python3.14 -I -S -B /inputs/recipe/build_support.py prepare "$1"
/usr/bin/mkdir /work/inspection
cd /work/apple
# The reviewed launcher supplies the existing outer deadline and isolation policy.
/usr/bin/make -f /inputs/headers/Makefile M=/work/apple \
  ARCH=arm64 PAHOLE=/inputs/pahole/usr/bin/pahole -j2 modules \
  > /work/inspection/build.stdout 2> /work/inspection/build.stderr

/usr/bin/readelf -aW appledrm.ko > /work/inspection/readelf-all.txt
/usr/bin/modinfo appledrm.ko > /work/inspection/modinfo.txt
/usr/bin/nm -a -S --format=posix appledrm.ko > /work/inspection/symbols-all.txt
/usr/bin/nm -u appledrm.ko | /usr/bin/sort > /work/inspection/imports.txt
/usr/bin/nm --defined-only appledrm.ko | /usr/bin/sort > /work/inspection/defined-symbols.txt
/usr/bin/awk '$3 ~ /^__ksymtab_/ {print $3}' /work/inspection/defined-symbols.txt \
  > /work/inspection/exports.txt
/usr/bin/objdump -drwC appledrm.ko > /work/inspection/disassembly-all.txt
for symbol in iomfb_poweroff_v12_3 iomfb_poweroff_v13_3 dcp_rtk_crashed dcp_crtc_atomic_check; do
  /usr/bin/grep -Eq " [tT] $symbol\$" /work/inspection/defined-symbols.txt
  /usr/bin/objdump -drwC --disassemble="$symbol" appledrm.ko \
    > "/work/inspection/$symbol.disassembly.txt"
done
/inputs/pahole/usr/bin/pahole -F dwarf -C apple_dcp appledrm.ko \
  > /work/inspection/apple_dcp-dwarf.txt 2> /work/inspection/apple_dcp-dwarf.stderr
/usr/bin/objcopy --dump-section .BTF.base=/work/inspection/appledrm.btfbase \
  appledrm.ko /work/inspection/appledrm.inspection-copy.ko
/usr/bin/cmp appledrm.ko /work/inspection/appledrm.inspection-copy.ko
[[ -s /work/inspection/appledrm.btfbase ]] || exit 1
/inputs/pahole/usr/bin/pahole -F btf --btf_base=/work/inspection/appledrm.btfbase -C apple_dcp appledrm.ko \
  > /work/inspection/apple_dcp-btf.txt 2> /work/inspection/apple_dcp-btf.stderr
for format in dwarf btf; do
  [[ -s /work/inspection/apple_dcp-$format.txt && ! -s /work/inspection/apple_dcp-$format.stderr ]] || exit 1
  [[ $(/usr/bin/head -n 1 "/work/inspection/apple_dcp-$format.txt") == 'struct apple_dcp {' ]] || exit 1
done
/usr/bin/python3.14 -I -S -B /inputs/recipe/build_support.py sections

/usr/bin/modinfo /inputs/stock/appledrm.ko > /work/inspection/stock-modinfo.txt
/usr/bin/nm -u /inputs/stock/appledrm.ko | /usr/bin/sort > /work/inspection/stock-imports.txt
/usr/bin/nm --defined-only /inputs/stock/appledrm.ko | /usr/bin/sort > /work/inspection/stock-defined-symbols.txt
/usr/bin/awk '$3 ~ /^__ksymtab_/ {print $3}' /work/inspection/stock-defined-symbols.txt \
  > /work/inspection/stock-exports.txt
for field in name vermagic depends alias; do
  [[ $(/usr/bin/modinfo -F "$field" appledrm.ko) == $(/usr/bin/modinfo -F "$field" /inputs/stock/appledrm.ko) ]] || {
    printf 'STOP: appledrm metadata differs from stock in %s\n' "$field" >&2
    exit 1
  }
done
/usr/bin/sha256sum appledrm.ko /work/preparation.json /work/inspection/*
printf 'OFFLINE BUILD/INSPECTION ONLY: %s; independent comparison pending; nothing loaded or staged\n' "$1"
