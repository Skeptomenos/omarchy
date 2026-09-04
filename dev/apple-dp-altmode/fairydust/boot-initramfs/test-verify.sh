#!/bin/bash
set -euo pipefail
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
source "$script_dir/verify.sh"
[[ $# == 2 ]]
build_root=$(realpath -e "$1")
work=$(mktemp -d "$2/test-initramfs.XXXXXX")
original="$build_root/artifacts/root/lib/modules/7.1.12-dev147-fairydust1/kernel/drivers/gpu/drm/apple/appledrm.ko"
cp "$original" "$work/appledrm.ko"
verify_module_bytes "$work/appledrm.ko" "$original"
printf X >> "$work/appledrm.ko"
if verify_module_bytes "$work/appledrm.ko" "$original"; then
  printf 'FAIL: modified module accepted\n' >&2
  exit 1
fi
if verify_module_bytes "$work/missing.ko" "$original"; then
  printf 'FAIL: missing module accepted\n' >&2
  exit 1
fi
if verify_release_tree "$work" 7.1.12-dev147-fairydust1; then
  printf 'FAIL: empty release tree accepted\n' >&2
  exit 1
fi
mkdir -p "$work/lib/modules/7.1.12-dev147-fairydust1"
verify_release_tree "$work" 7.1.12-dev147-fairydust1
mkdir -p "$work/lib/modules/7.1.6-1-1-ARCH"
if verify_release_tree "$work" 7.1.12-dev147-fairydust1; then
  printf 'FAIL: mixed releases accepted\n' >&2
  exit 1
fi
printf 'PASS: real module mutation, missing module, empty and mixed release controls\n'
