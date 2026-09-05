#!/bin/bash
set -euo pipefail
[[ $# == 0 ]] || exit 2
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
boot=/home/david/Work/dev147-fairydust-boot-20260905
checks=$(mktemp -d "$boot/checks/staged-gate.XXXXXXXX")
trap 'gate_status=$?; printf "%s\n" "$gate_status" > "$checks/exit-status"' EXIT
printf 'Staged verification logs: %s\n' "$checks"
bash "$script_dir/validate-boot.sh" > "$checks/rehearsal.log" 2>&1
python3 "$script_dir/boot-stage/test_verify_staged.py" > "$checks/verifier-tests.log" 2>&1
python3 "$script_dir/boot-stage/verify-staged.py" > "$checks/published-stage.log" 2>&1
receipt=$(sed -n 's/^Private receipt: //p' "$checks/published-stage.log")
[[ $receipt == "$boot/stage/staged-verification."*/receipt.json ]]
cp -- "$receipt" "$checks/staged-receipt.json"
sha256sum "$script_dir/validate-staged.sh" "$script_dir/boot-stage/verify-staged.py" "$script_dir/boot-stage/test_verify_staged.py" > "$checks/verifier-identities.sha256"
printf 'PASS: complete rehearsal and actual published unselected stage verified\n' | tee "$checks/result.txt"
printf 'LIMIT: paired activation, boot, rollback execution and hardware acceptance require later evidence.\n'
