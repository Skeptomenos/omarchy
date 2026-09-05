#!/bin/bash
set -euo pipefail
[[ $# == 0 ]] || exit 2
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
root=/home/david/Work/dev147-clear-wait-trial/return-to-trial
umask 077
mkdir -p "$root/checks"
checks=$(mktemp -d "$root/checks/software.XXXXXXXX")
trap 'status=$?; printf "%s\n" "$status" > "$checks/exit-status"' EXIT
printf 'Return-to-trial gate: %s\n' "$checks"
tools=/home/david/Work/dev147-fairydust-boot-20260905/stage/uv-cache/archive-v0
"$tools/NN8oF-CHP05mnrav/bin/ruff" check "$script_dir" > "$checks/ruff.log"
"$tools/NN8oF-CHP05mnrav/bin/ruff" format --check --config 'indent-width=2' "$script_dir" > "$checks/format.log"
"$tools/BzCSLx7VfLpHd_Z9/bin/mypy" --strict --cache-dir="$checks/mypy-cache" "$script_dir" > "$checks/mypy.log"
cmp "$script_dir/baseline.py" "$script_dir/../../boot-activate/activate.py"
cmp "$script_dir/topology.py" "$script_dir/../../boot-activate/topology.py"
cmp "$script_dir/dispatcher.cfg" "$script_dir/../../boot-activate/dispatcher.cfg"
for script in "$script_dir"/*.sh; do
  bash -n "$script"
done
grub-script-check "$script_dir/candidate.cfg"
python3 "$script_dir/test_return.py" > "$checks/tests.log" 2>&1
python3 "$script_dir/probe_menu.py" "$checks/grub-menu" > "$checks/grub-menu.log" 2>&1
sha256sum "$script_dir"/*.py "$script_dir"/*.sh "$script_dir"/*.cfg > "$checks/source.sha256"
printf 'PASS: namespace return/restore controls; topology and prior-stage identity are fixtures; no live selection or hardware acceptance.\n' | tee "$checks/result.txt"
