#!/bin/bash
set -euo pipefail
[[ $# == 0 ]] || exit 2
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
root=/home/david/Work/dev147-fairydust-acceptance-20260905
umask 077
mkdir -p "$root/checks"
checks=$(mktemp -d "$root/checks/collector.XXXXXXXX")
trap 'status=$?; printf "%s\n" "$status" > "$checks/exit-status"' EXIT
printf 'Collector gate: %s\n' "$checks"
tools=/home/david/Work/dev147-fairydust-boot-20260905/stage/uv-cache/archive-v0
"$tools/NN8oF-CHP05mnrav/bin/ruff" check "$script_dir" > "$checks/ruff.log"
"$tools/NN8oF-CHP05mnrav/bin/ruff" format --check --config 'indent-width=2' "$script_dir" > "$checks/format.log"
"$tools/BzCSLx7VfLpHd_Z9/bin/mypy" --strict --cache-dir="$checks/mypy-cache" "$script_dir" > "$checks/mypy.log"
bash -n "$script_dir/validate.sh"
python3 "$script_dir/test_snapshot.py" > "$checks/tests.log" 2>&1
status=0
python3 "$script_dir/snapshot.py" collector-validation > "$checks/live-summary.json" 2> "$checks/live.stderr" || status=$?
printf '%s\n' "$status" > "$checks/live-exit-status"
python3 - "$checks" <<'PY'
import hashlib
import json
import stat
import sys
from pathlib import Path
checks = Path(sys.argv[1])
summary = json.loads((checks / 'live-summary.json').read_text())
assert not (checks / 'live.stderr').read_text()
assert summary['status'] in ('SNAPSHOT_CAPTURED', 'SNAPSHOT_CAPTURED_WITH_ERRORS'), summary
assert int((checks / 'live-exit-status').read_text()) == (summary['status'] != 'SNAPSHOT_CAPTURED')
assert summary['endurance_accepted'] is False
snapshot = Path(summary['directory'])
assert snapshot.parent == Path('/home/david/Work/dev147-fairydust-acceptance-20260905')
assert stat.S_IMODE(snapshot.stat().st_mode) == 0o500
for line in (snapshot / 'SHA256SUMS').read_text().splitlines():
    expected, name = line.split('  ')
    assert name in ('snapshot.json', 'journal.jsonl')
    assert hashlib.sha256((snapshot / name).read_bytes()).hexdigest() == expected
    assert stat.S_IMODE((snapshot / name).stat().st_mode) == 0o400
print('PASS: collector software and honest live capture; live status=' + summary['status'])
print('LIMIT: no visual-success or endurance acceptance claim.')
PY
sha256sum "$script_dir/snapshot.py" "$script_dir/test_snapshot.py" "$script_dir/validate.sh" > "$checks/source.sha256"
printf 'PASS: read-only collector validation; hardware observations are in live-summary.json\n' | tee "$checks/result.txt"
