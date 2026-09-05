#!/bin/bash
set -euo pipefail
[[ $# == 0 && $EUID != 0 ]] || { printf 'Run this fixed repair launcher as David without arguments.\n' >&2; exit 2; }
umask 077
source_dir=/home/david/Work/omarchy-dev147-fairydust-build/dev/apple-dp-altmode/fairydust/clear-wait-trial/module-repair
helper_hash=713a0534da1bf9ffafef7c2490d885d57162651fb8fa882140a160bbfbc506cd
root=/home/david/Work/dev147-clear-wait-trial/module-repair
mkdir -p "$root"
results=$(mktemp -d "$root/repair-results.XXXXXXXX")
bootstrap=$(cat <<'DEV147_MODULE_REPAIR_BOOTSTRAP'
import hashlib
import os
import stat
import sys
import types

directory, expected, action = sys.argv[1:]

def frozen(name, digest):
  path = directory + "/" + name
  fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
  with os.fdopen(fd, "rb") as stream:
    before = os.fstat(stream.fileno())
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size > 1048576:
      raise SystemExit("FAIL: invalid frozen helper")
    content = stream.read(before.st_size + 1)
    after = os.fstat(stream.fileno())
  if len(content) != before.st_size or (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_size, after.st_mtime_ns, after.st_ctime_ns) or hashlib.sha256(content).hexdigest() != digest:
    raise SystemExit("FAIL: frozen helper changed")
  return path, content

for name, digest in (("protect", "f8be9212515fa36ded7566e9ad368e3e7f63f97e3fa94e6004826ede0e14dd4e"), ("copying", "12501982dfd4adb347103671ce5dbf9650b53b628474a434de3c458fd98ad6a7")):
  path, content = frozen(name + ".py", digest)
  module = types.ModuleType(name)
  module.__file__ = path
  sys.modules[name] = module
  exec(compile(content, path, "exec"), module.__dict__)
path, content = frozen("repair.py", expected)
sys.argv = [path] + (["preflight"] if action == "preflight" else [])
globals()["__file__"] = path
exec(compile(content, path, "exec"), globals())
DEV147_MODULE_REPAIR_BOOTSTRAP
)
/usr/bin/python3 -I -c "$bootstrap" "$source_dir" "$helper_hash" preflight > "$results/preflight.json" 2> "$results/preflight.stderr"
printf 'Repair two staged module releases and retain only those releases during cleanup. No boot selection or reboot.\n'
if /usr/bin/sudo /usr/bin/env -i PATH=/usr/bin:/bin LANG=C.UTF-8 /usr/bin/python3 -I -c "$bootstrap" "$source_dir" "$helper_hash" repair > "$results/result.json" 2> "$results/stderr.log"; then
  status=0
else
  status=$?
fi
printf '%s\n' "$status" > "$results/exit-status"
printf 'helper_sha256=%s\n' "$helper_hash" > "$results/input-identities"
printf 'Module repair exit: %s. Private result files: %s\n' "$status" "$results"
exit "$status"
