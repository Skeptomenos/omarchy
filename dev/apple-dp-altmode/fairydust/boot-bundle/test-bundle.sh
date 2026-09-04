#!/bin/bash
set -euo pipefail
[[ $# == 2 ]] || exit 2
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
build_root=$1
bundle=$2
fixture=$(mktemp -d)
trap 'rm -rf -- "$fixture"' EXIT
bash "$script_dir/bundle.sh" verify "$build_root" "$bundle" > "$fixture/good.log"
for mode in missing truncated altered trailing symlink; do
  target="$fixture/$mode.bin"
  case $mode in
    missing) ;;
    truncated) head -c 1186227 "$bundle" > "$target" ;;
    altered) cp "$bundle" "$target"; printf '\377' | dd of="$target" bs=1 seek=1114112 conv=notrunc status=none ;;
    trailing) cat "$bundle" > "$target"; printf 'unreviewed-config\n' >> "$target" ;;
    symlink) ln -s "$bundle" "$target" ;;
  esac
  if bash "$script_dir/bundle.sh" verify "$build_root" "$target" > "$fixture/$mode.log" 2>&1; then
    printf 'FAIL: %s bundle accepted\n' "$mode" >&2
    exit 1
  fi
  printf 'PASS: %s bundle rejected\n' "$mode"
done
if bash "$script_dir/bundle.sh" assemble "$build_root" "$bundle" > "$fixture/existing.log" 2>&1; then
  printf 'FAIL: existing output accepted\n' >&2
  exit 1
fi
printf 'PASS: valid bundle and existing-output refusal\n'
