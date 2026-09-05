#!/bin/bash
set -euo pipefail
[[ $# == 0 ]] || exit 2
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
root=/home/david/Work/dev147-clear-wait-trial
umask 077
mkdir -p "$root/checks"
checks=$(mktemp -d "$root/checks/stage.XXXXXXXX")
trap 'status=$?; printf "%s\n" "$status" > "$checks/exit-status"' EXIT
printf 'Trial staging gate: %s\n' "$checks"
tools=/home/david/Work/dev147-fairydust-boot-20260905/stage/uv-cache/archive-v0
"$tools/NN8oF-CHP05mnrav/bin/ruff" check "$script_dir" > "$checks/ruff.log"
"$tools/NN8oF-CHP05mnrav/bin/ruff" format --check --config 'indent-width=2' "$script_dir" > "$checks/format.log"
"$tools/BzCSLx7VfLpHd_Z9/bin/mypy" --strict --cache-dir="$checks/mypy-cache" "$script_dir" > "$checks/mypy.log"
for script in "$script_dir"/*.sh; do
  bash -n "$script"
done
python3 "$script_dir/test_stage.py" > "$checks/tests.log" 2>&1
sha256sum "$script_dir"/*.py "$script_dir"/*.sh > "$checks/source.sha256"
printf 'PASS: staged-only namespace controls; no real staging or selection.\n' | tee "$checks/result.txt"
