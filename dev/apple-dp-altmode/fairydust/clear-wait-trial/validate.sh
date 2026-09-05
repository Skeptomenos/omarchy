#!/bin/bash
set -euo pipefail
[[ $# == 0 ]] || exit 2
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
root=/home/david/Work/dev147-clear-wait-trial
umask 077
mkdir -p "$root/checks"
checks=$(mktemp -d "$root/checks/offline.XXXXXXXX")
trap 'status=$?; printf "%s\n" "$status" > "$checks/exit-status"' EXIT
printf 'Clear-wait gate: %s\n' "$checks"
tools=/home/david/Work/dev147-fairydust-boot-20260905/stage/uv-cache/archive-v0
"$tools/NN8oF-CHP05mnrav/bin/ruff" check "$script_dir" > "$checks/ruff.log"
"$tools/NN8oF-CHP05mnrav/bin/ruff" format --check --config 'indent-width=2' "$script_dir" > "$checks/format.log"
"$tools/BzCSLx7VfLpHd_Z9/bin/mypy" --strict --cache-dir="$checks/mypy-cache" "$script_dir" > "$checks/mypy.log"
for script in "$script_dir"/*.sh; do
  bash -n "$script"
done
python3 "$script_dir/verify.py" /home/david/Work/dev147-fairydust-build/linux "$checks/baseline" baseline > "$checks/baseline.json"
python3 "$script_dir/verify.py" "$root/linux" "$checks/candidate" candidate > "$checks/candidate.json"
find "$script_dir" -maxdepth 1 -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum > "$checks/source.sha256"
printf 'PASS: exact patch and deterministic completion controls; no hardware acceptance.\n' | tee "$checks/result.txt"
