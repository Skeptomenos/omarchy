#!/bin/bash
set -euo pipefail
[[ $# == 2 ]]
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
source "$script_dir/verify.sh"
original=$(realpath -e "$1")
work=$(mktemp -d "$2/startup-controls.XXXXXX")
(cd "$original" && cp -a --parents init init_functions config hooks usr/bin/busybox usr/bin/ash usr/share/asahi-scripts/functions.sh "$work/")
verify_startup "$work"
for relative in usr/bin/busybox usr/share/asahi-scripts/functions.sh; do
  target="/$relative"
  [[ $relative != "usr/bin/busybox" ]] || target=/usr/lib/initcpio/busybox
  mv "$work/$relative" "$work/$relative.saved"
  ln -s "$target" "$work/$relative"
  if verify_startup "$work"; then
    printf 'FAIL: host symlink accepted: %s\n' "$relative" >&2
    exit 1
  fi
  unlink "$work/$relative"
  mv "$work/$relative.saved" "$work/$relative"
done
mv "$work/init_functions" "$work/init_functions.saved"
if verify_startup "$work"; then
  printf 'FAIL: missing init_functions accepted\n' >&2
  exit 1
fi
mv "$work/init_functions.saved" "$work/init_functions"
mv "$work/hooks/asahi" "$work/hooks/asahi.saved"
if verify_startup "$work"; then
  printf 'FAIL: missing Asahi hook accepted\n' >&2
  exit 1
fi
mv "$work/hooks/asahi.saved" "$work/hooks/asahi"
printf '\nMODULES=""\n' >> "$work/config"
if verify_startup "$work"; then
  printf 'FAIL: altered startup config accepted\n' >&2
  exit 1
fi
printf 'PASS: exact startup, host symlinks, missing init_functions/hook, and altered config controls\n'
