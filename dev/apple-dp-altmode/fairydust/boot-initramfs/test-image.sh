#!/bin/bash
set -euo pipefail
[[ $# == 3 ]]
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
work=$(mktemp -d "$3/truncated-image.XXXXXX")
head -c 1024 "$1" > "$work/truncated.img"
if bash "$script_dir/validate-image.sh" "$work/truncated.img" "$2" "$work" > "$work/result.log" 2>&1; then
  printf 'FAIL: truncated real image accepted\n' >&2
  exit 1
fi
printf 'PASS: truncated real image rejected; evidence %s\n' "$work"
