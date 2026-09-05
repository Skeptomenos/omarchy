#!/bin/bash
set -euo pipefail

[[ $# == 0 && $EUID != 0 ]] || { printf 'Run this fixed launcher as David without arguments.\n' >&2; exit 1; }
umask 077
stage_root=/home/david/Work/dev147-clear-wait-trial/stage
results="$stage_root/manual-results"
helper=/home/david/Work/omarchy-dev147-fairydust-build/dev/apple-dp-altmode/fairydust/clear-wait-trial/stage/stage.py
helper_hash=96b4ef29a03897c612ff2a978a932b5dc31d6da2cf7dfc1eded7ab08ed20ea1f
delivery=/home/david/Work/dev147-clear-wait-trial/delivery
manifest_hash=a89c31f8b42c3f4f958ac8aca4c312c95a222baf2e80b8b5702dbe4549e8a857
[[ $manifest_hash =~ ^[0-9a-f]{64}$ ]] || { printf 'FAIL: reviewed trial delivery pins are not ready.\n' >&2; exit 1; }
mkdir -p -- "$stage_root"
mkdir -m 700 -- "$results"

bootstrap=$(cat <<'DEV147_STAGE_BOOTSTRAP'
import hashlib
import os
import stat
import sys

helper, expected, delivery, manifest = sys.argv[1:]
descriptor = os.open(helper, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
with os.fdopen(descriptor, "rb") as stream:
    if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
        raise SystemExit("FAIL: helper is not a regular file")
    code = stream.read(1048577)
if len(code) > 1048576 or hashlib.sha256(code).hexdigest() != expected:
    raise SystemExit("FAIL: frozen helper hash mismatch")
sys.argv = [helper, delivery, manifest]
globals()["__file__"] = helper
exec(compile(code, helper, "exec"), globals())
DEV147_STAGE_BOOTSTRAP
)

printf 'Stage only: the new kernel remains unselected.\n'
if /usr/bin/sudo /usr/bin/env -i PATH=/usr/bin:/bin LANG=C.UTF-8 /usr/bin/python3 -I -c "$bootstrap" "$helper" "$helper_hash" "$delivery" "$manifest_hash" > "$results/result.json" 2> "$results/stderr.log"; then
  status=0
else
  status=$?
fi
printf '%s\n' "$status" > "$results/exit-status"
printf 'helper_sha256=%s\nmanifest_sha256=%s\n' "$helper_hash" "$manifest_hash" > "$results/input-identities"
printf 'Stage exit: %s. Private result files: %s\n' "$status" "$results"
exit "$status"
