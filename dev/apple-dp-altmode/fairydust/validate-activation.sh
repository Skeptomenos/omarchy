#!/bin/bash
set -euo pipefail
[[ $# == 0 ]] || exit 2
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
boot=/home/david/Work/dev147-fairydust-boot-20260905
checks=$(mktemp -d "$boot/checks/activation-gate.XXXXXXXX")
trap 'gate_status=$?; printf "%s\n" "$gate_status" > "$checks/exit-status"' EXIT
printf 'Activation verification logs: %s\n' "$checks"
bash "$script_dir/validate-staged.sh" > "$checks/staged-gate.log" 2>&1
ruff="$boot/stage/uv-cache/archive-v0/NN8oF-CHP05mnrav/bin/ruff"
mypy="$boot/stage/uv-cache/archive-v0/BzCSLx7VfLpHd_Z9/bin/mypy"
"$ruff" check "$script_dir/boot-activate" > "$checks/ruff.log"
"$ruff" format --check --config 'indent-width=2' "$script_dir/boot-activate" > "$checks/format.log"
"$mypy" --strict --cache-dir="$checks/mypy-cache" "$script_dir/boot-activate" > "$checks/mypy.log"
for file in "$script_dir"/boot-activate/*.sh "$script_dir/validate-activation.sh"; do bash -n "$file"; done
python3 "$script_dir/boot-activate/test_topology.py" > "$checks/topology-tests.log" 2>&1
python3 "$script_dir/boot-activate/test_activate.py" > "$checks/namespace-tests.log" 2>&1
python3 - "$script_dir/boot-activate" "$boot" <<'PY' > "$checks/frozen-inputs.log"
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
source, boot = map(Path, sys.argv[1:])
sys.path.insert(0, str(source))
import activate
for name, expected in activate.PINS.items():
    assert hashlib.sha256((source / name).read_bytes()).hexdigest() == expected, name
for name in ("launch.sh", "restore.sh"):
    launcher = (source / name).read_text()
    helper_hash = launcher.split("helper_hash=", 1)[1].splitlines()[0]
    topology_hash = launcher.split("topology_hash=", 1)[1].splitlines()[0]
    assert helper_hash == hashlib.sha256((source / "activate.py").read_bytes()).hexdigest()
    assert topology_hash == hashlib.sha256((source / "topology.py").read_bytes()).hexdigest()
    bootstrap = launcher.split("<<'DEV147_ACTIVATION_BOOTSTRAP'\n", 1)[1].split("\nDEV147_ACTIVATION_BOOTSTRAP", 1)[0]
    result = subprocess.run(["/usr/bin/python3", "-I", "-c", bootstrap, str(source / "activate.py"), helper_hash, str(source / "topology.py"), topology_hash, "preflight"], capture_output=True, text=True, check=True, timeout=30)
    assert not result.stderr
    assert json.loads(result.stdout)["status"] == "READ_ONLY_TOPOLOGY_PASS"
    print(name, result.stdout.strip())
research = boot / "research/activation-recovery"
blocks = lambda text: re.findall(r"```sh\n(.*?)\n```", text, re.S)
assert blocks((source / "RECOVERY.md").read_text()) == blocks((research / "recovery-design.md").read_text())
print("PASS: frozen payload, both exact launch bootstraps read-only, recovery shell block identity")
PY
probe="$boot/research/activation-design/probe_dispatcher.py"
printf '%s  %s\n' acebd75bd3d856cad88c2583b29ad566668a60b69b85ca21dfd24236ecf6f954 "$probe" | sha256sum --check --strict > "$checks/probe-pin.log"
python3 "$probe" "$checks/grub-runtime" > "$checks/grub-probes.log" 2>&1
for name in dispatcher.cfg old.cfg candidate.cfg old.sha256 candidate.sha256; do
  cmp "$script_dir/boot-activate/$name" "$checks/grub-runtime/prototype/$name"
done
bash "$boot/research/activation-recovery/test-guards.sh" > "$checks/recovery-guards.log" 2>&1
sha256sum "$script_dir"/boot-activate/*.py "$script_dir"/boot-activate/*.sh "$script_dir"/boot-activate/*.cfg "$script_dir"/boot-activate/*.sha256 "$script_dir/boot-activate/RECOVERY.md" "$script_dir/validate-activation.sh" > "$checks/code-identities.sha256"
printf 'PASS: activation and restore implementation, namespace failure controls, live read-only preflight, staged delivery and real GRUB routing\n' | tee "$checks/result.txt"
printf 'LIMIT: namespace replaces topology discovery and prior-state receipt identity; no live activation, reboot, real FAT publication or hardware test.\n' | tee "$checks/limits.txt"
