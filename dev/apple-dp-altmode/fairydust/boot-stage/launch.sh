#!/bin/bash
set -euo pipefail

[[ $# == 0 && $EUID != 0 ]] || { printf 'Run this fixed launcher as David without arguments.\n' >&2; exit 1; }
umask 077
stage_root=/home/david/Work/dev147-fairydust-boot-20260905/stage
results="$stage_root/manual-results"
helper=/home/david/Work/omarchy-dev147-fairydust-build/dev/apple-dp-altmode/fairydust/boot-stage/stage.py
helper_hash=12501982dfd4adb347103671ce5dbf9650b53b628474a434de3c458fd98ad6a7
delivery=/home/david/Work/dev147-fairydust-boot-20260905/delivery
manifest_hash=f33054856e60d3baf5cb7630cb8d7dfc60ffa586e16456c3e7313fffe6f7c59d
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
