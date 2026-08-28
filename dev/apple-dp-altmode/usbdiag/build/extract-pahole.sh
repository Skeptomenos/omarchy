#!/bin/bash
set -euo pipefail
umask 077

# Recheck authenticity in this same sandbox before extracting selected members.
/usr/bin/bash /inputs/authenticate
/usr/bin/mkdir /work/pahole
/usr/bin/bsdtar -x --no-same-owner -f /inputs/package -C /work/pahole \
  usr/bin/pahole \
  usr/lib/libdwarves.so usr/lib/libdwarves.so.1 usr/lib/libdwarves.so.1.0.0 \
  usr/lib/libdwarves_emit.so usr/lib/libdwarves_emit.so.1 usr/lib/libdwarves_emit.so.1.0.0 \
  usr/lib/libdwarves_reorganize.so usr/lib/libdwarves_reorganize.so.1 usr/lib/libdwarves_reorganize.so.1.0.0

printf '%s  %s\n' \
  6720f51a6a3b0f439e5d74fb07acfcd75bed599fd333c819eb3b1ced441f56ed \
  /work/pahole/usr/bin/pahole | /usr/bin/sha256sum --check --strict
/usr/bin/readelf -l -d /work/pahole/usr/bin/pahole \
  /work/pahole/usr/lib/libdwarves.so.1.0.0 \
  /work/pahole/usr/lib/libdwarves_emit.so.1.0.0 \
  /work/pahole/usr/lib/libdwarves_reorganize.so.1.0.0
/usr/bin/find /work/pahole -type f -exec /usr/bin/sha256sum '{}' +
