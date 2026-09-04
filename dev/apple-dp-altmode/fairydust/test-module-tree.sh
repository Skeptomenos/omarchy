#!/bin/bash
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
source "$script_dir/validate-offline.sh"
fixture=$(mktemp -d)
trap 'rm -rf -- "$fixture"' EXIT
mkdir -p "$fixture/build/drivers/usb" "$fixture/installed/kernel/drivers/usb"
printf 'drivers/usb/core.o\ndrivers/usb/leaf.o\n' > "$fixture/build/modules.order"
printf 'kernel/drivers/usb/core.ko\nkernel/drivers/usb/leaf.ko\n' > "$fixture/installed/modules.order"
printf 'builtin module\n' > "$fixture/build/modules.builtin"
printf 'builtin metadata\n' > "$fixture/build/modules.builtin.modinfo"
cp "$fixture/build/modules.builtin" "$fixture/build/modules.builtin.modinfo" "$fixture/installed/"
for name in core leaf; do
  printf 'vermagic=same-release\nmodule=%s\n' "$name" > "$fixture/build/drivers/usb/$name.ko"
  cp "$fixture/build/drivers/usb/$name.ko" "$fixture/installed/kernel/drivers/usb/$name.ko"
done
verify_module_tree "$fixture/build" "$fixture/installed"
printf 'PASS: complete matching module tree\n'

mv "$fixture/installed/kernel/drivers/usb/leaf.ko" "$fixture/leaf.saved"
if verify_module_tree "$fixture/build" "$fixture/installed" > "$fixture/missing.log" 2>&1; then
  printf 'FAIL: missing leaf module accepted\n' >&2
  exit 1
fi
mv "$fixture/leaf.saved" "$fixture/installed/kernel/drivers/usb/leaf.ko"
printf 'PASS: missing leaf module rejected\n'

printf 'vermagic=same-release\nmodule=changed\n' > "$fixture/installed/kernel/drivers/usb/leaf.ko"
if verify_module_tree "$fixture/build" "$fixture/installed" > "$fixture/changed.log" 2>&1; then
  printf 'FAIL: changed module with same vermagic accepted\n' >&2
  exit 1
fi
cp "$fixture/build/drivers/usb/leaf.ko" "$fixture/installed/kernel/drivers/usb/leaf.ko"
printf 'PASS: changed module with same vermagic rejected\n'

cp "$fixture/build/drivers/usb/leaf.ko" "$fixture/installed/kernel/drivers/usb/extra.ko"
if verify_module_tree "$fixture/build" "$fixture/installed" > "$fixture/extra.log" 2>&1; then
  printf 'FAIL: extra module accepted\n' >&2
  exit 1
fi
printf 'PASS: extra module rejected\n'
