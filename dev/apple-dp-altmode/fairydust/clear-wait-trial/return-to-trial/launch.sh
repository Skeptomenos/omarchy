#!/bin/bash
set -euo pipefail

[[ $# == 0 && $EUID != 0 ]] || { printf 'Run this fixed launcher as David without arguments.\n' >&2; exit 1; }
umask 077
activation_root=/home/david/Work/dev147-clear-wait-trial/return-to-trial
helper=/home/david/Work/omarchy-dev147-fairydust-build/dev/apple-dp-altmode/fairydust/clear-wait-trial/return-to-trial/return.py
helper_hash=b68113720f9c23af4325bb6ad284c26c30b4cbe130601b62c70dfa7af027825c
topology_file=/home/david/Work/omarchy-dev147-fairydust-build/dev/apple-dp-altmode/fairydust/clear-wait-trial/return-to-trial/topology.py
topology_hash=fa5f4804a6d7323a4638b0550bba9921ede05adfa7106d0d1e05509564bc4530
baseline_file=/home/david/Work/omarchy-dev147-fairydust-build/dev/apple-dp-altmode/fairydust/clear-wait-trial/return-to-trial/baseline.py
baseline_hash=f8be9212515fa36ded7566e9ad368e3e7f63f97e3fa94e6004826ede0e14dd4e
action=return
mkdir -p -- "$activation_root"
results=$(mktemp -d "$activation_root/$action-results.XXXXXXXX")
bootstrap=$(cat <<'DEV147_ACTIVATION_BOOTSTRAP'
import hashlib
import json
import os
import stat
import sys
import types

helper, expected, topology_file, topology_expected, baseline_file, baseline_expected, action = sys.argv[1:]

def frozen_bytes(path, expected):
  descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
  with os.fdopen(descriptor, "rb") as stream:
    before = os.fstat(stream.fileno())
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size > 1048576:
      raise SystemExit("FAIL: invalid frozen code input")
    content = stream.read(before.st_size + 1)
    after = os.fstat(stream.fileno())
  if len(content) != before.st_size or (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_size, after.st_mtime_ns, after.st_ctime_ns) or hashlib.sha256(content).hexdigest() != expected:
    raise SystemExit("FAIL: frozen code hash or identity mismatch")
  return content

code = frozen_bytes(helper, expected)
baseline_code = frozen_bytes(baseline_file, baseline_expected)
topology_code = frozen_bytes(topology_file, topology_expected)
topology = {"__name__": "dev147_topology", "__file__": topology_file}
exec(compile(topology_code, topology_file, "exec"), topology)
validated = topology["discover"]()
if action == "preflight":
  print(json.dumps({"status": "READ_ONLY_TOPOLOGY_PASS", "directory_devices": validated, "helper_sha256": expected, "topology_sha256": topology_expected}))
  raise SystemExit(0)
baseline = types.ModuleType("baseline")
baseline.__file__ = baseline_file
sys.modules["baseline"] = baseline
exec(compile(baseline_code, baseline_file, "exec"), baseline.__dict__)
baseline.__dict__["validated_directory_devices"] = validated
sys.argv = [helper, action]
globals()["__file__"] = helper
exec(compile(code, helper, "exec"), globals())
DEV147_ACTIVATION_BOOTSTRAP
)

/usr/bin/python3 -I -c "$bootstrap" "$helper" "$helper_hash" "$topology_file" "$topology_hash" "$baseline_file" "$baseline_hash" preflight > "$results/preflight.json" 2> "$results/preflight.stderr"
printf 'Prepared %s. No reboot will be requested.\n' "$action"
if /usr/bin/sudo /usr/bin/env -i PATH=/usr/bin:/bin LANG=C.UTF-8 /usr/bin/python3 -I -c "$bootstrap" "$helper" "$helper_hash" "$topology_file" "$topology_hash" "$baseline_file" "$baseline_hash" "$action" > "$results/result.json" 2> "$results/stderr.log"; then
  status=0
else
  status=$?
fi
printf '%s\n' "$status" > "$results/exit-status"
printf 'helper_sha256=%s\ntopology_sha256=%s\nbaseline_file=%s\nbaseline_sha256=%s\naction=%s\n' "$helper_hash" "$topology_hash" "$baseline_file" "$baseline_hash" "$action" > "$results/input-identities"
printf '%s exit: %s. Private result files: %s\n' "$action" "$status" "$results"
exit "$status"
