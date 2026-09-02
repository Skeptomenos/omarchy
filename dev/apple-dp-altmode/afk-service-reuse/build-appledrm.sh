#!/bin/bash
set -euo pipefail
umask 077

[[ $EUID == 1001 && $PWD == "/work" && ! -e /proc && ! -e /sys && ! -e /boot ]] || exit 1
[[ $# == 1 ]] || exit 1

case $1 in
  control)
    source_manifest_sha256=fca34cbadd373f18a1cad0f32d5e1a94cd0ad0317d665c8ef18733b82e2f41b3
    ;;
  candidate)
    source_manifest_sha256=9723ae20d424df7485f4e13270ad9424e1bcde5a6cd979b1d9b827e995215b3f
    ;;
  *)
    exit 1
    ;;
esac

printf '%s  %s\n' \
  "$source_manifest_sha256" /inputs/source-manifest \
  9b52faf901123ab4f9a0a486c2f7ba5718259dcb0ef68e4aebc9ce3d23a19e2c /inputs/patch \
  137a58ad1417e413962dbe6e91dbb0b2385fbc8733db7d4ecf659959cd9bac82 /inputs/headers/Makefile \
  d5eea549b9333f717fdc932683ea6633d58049c1e3f8f9e0be12e05d7610dd82 /inputs/headers/Module.symvers \
  701d1270a36cb57047558ab78e7d825900cc76935e42fd96003c319d1b9050e4 /inputs/headers/.config \
  32b70e3a145454b430a0c9375a67ce93b30e0ee6afdefba590aac6f92ead4e15 /inputs/headers/vmlinux \
  6720f51a6a3b0f439e5d74fb07acfcd75bed599fd333c819eb3b1ced441f56ed /inputs/pahole/usr/bin/pahole \
  68e844d07125b4e59a183e7d07e80413a30999ffc1ef30d7a279d73431c1018d /inputs/runtime/libdw.so.1 \
  dbffe74e13a43e15e47fdc5eafe32eb1829b114a3f02f15fe6b18507d622b0e3 /inputs/stockdir/appledrm.ko \
  | /usr/bin/sha256sum --check --strict

[[ $(/usr/bin/find /inputs/source -type f | /usr/bin/wc -l) == 40 ]] || exit 1
[[ $(/usr/bin/find /inputs/source -type d | /usr/bin/wc -l) == 2 ]] || exit 1
[[ $(/usr/bin/find /inputs/source -type l | /usr/bin/wc -l) == 0 ]] || exit 1
[[ $(/usr/bin/find /inputs/source ! -type f ! -type d | /usr/bin/wc -l) == 0 ]] || exit 1
(
  cd /inputs/source
  /usr/bin/sha256sum --check --strict /inputs/source-manifest
)

/usr/bin/mkdir /work/apple /work/inspection
/usr/bin/cp -a /inputs/source/. /work/apple/
export LD_LIBRARY_PATH=/inputs/pahole/usr/lib:/inputs/runtime
[[ $(/inputs/pahole/usr/bin/pahole --version) == "v1.31" ]] || exit 1
cd /work/apple
/usr/bin/make -f /inputs/headers/Makefile M=/work/apple \
  ARCH=arm64 PAHOLE=/inputs/pahole/usr/bin/pahole -j2 modules \
  > /work/inspection/build.stdout 2> /work/inspection/build.stderr

/usr/bin/readelf -hW appledrm.ko > /work/inspection/elf-header.txt
/usr/bin/readelf -SW appledrm.ko > /work/inspection/elf-sections.txt
/usr/bin/grep -Fq 'Machine:                           AArch64' /work/inspection/elf-header.txt
/usr/bin/modinfo appledrm.ko > /work/inspection/modinfo.txt
/usr/bin/nm -u appledrm.ko | /usr/bin/sort > /work/inspection/imports.txt
/usr/bin/nm --defined-only appledrm.ko | /usr/bin/sort > /work/inspection/defined-symbols.txt
/usr/bin/awk '$3 ~ /^__ksymtab_/ {print $3}' /work/inspection/defined-symbols.txt > /work/inspection/exports.txt
for symbol in afk_send_command dcp_get_modes; do
  /usr/bin/grep -Eq " [tT] $symbol\$" /work/inspection/defined-symbols.txt
  /usr/bin/objdump -drwC --disassemble="$symbol" appledrm.ko > "/work/inspection/$symbol.disassembly.txt"
done
if [[ $1 == "candidate" ]]; then
  for symbol in afk_service_get afk_service_put afk_service_request_retirement dcpavserv_get dcpavserv_put; do
    /usr/bin/grep -Eq " [tT] $symbol\$" /work/inspection/defined-symbols.txt
    /usr/bin/objdump -drwC --disassemble="$symbol" appledrm.ko > "/work/inspection/$symbol.disassembly.txt"
  done
fi
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
for field in name vermagic depends alias; do
  [[ $(/usr/bin/modinfo -F "$field" appledrm.ko) == $(/usr/bin/modinfo -F "$field" /inputs/stockdir/appledrm.ko) ]] || exit 1
done
/usr/bin/sha256sum appledrm.ko /work/inspection/*
printf 'OFFLINE APPLEDRM BUILD PASS: %s; nothing loaded or staged\n' "$1"
