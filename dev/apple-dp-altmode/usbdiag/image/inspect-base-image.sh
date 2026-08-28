#!/bin/bash
set -euo pipefail
umask 077

[[ $EUID == 1001 && $PWD == /work && ! -e /proc && ! -e /sys && ! -e /boot ]] || exit 1
printf '%s  %s\n' ae8f1ed7f4f258f89931209cd7de6030be9f6875372d7329151b822a6ba2281f /inputs/image | /usr/bin/sha256sum --check --strict
[[ $(/usr/bin/stat -c %s /inputs/image) == 19184103 ]] || exit 1
# The saved D0 boundary is fixed. This only validates and lists the gzip stream.
# It does not extract members or create an initramfs.
/usr/bin/dd if=/inputs/image bs=1048576 skip=10240 iflag=skip_bytes status=none | /usr/bin/gzip --test
/usr/bin/dd if=/inputs/image bs=1048576 skip=10240 iflag=skip_bytes status=none | /usr/bin/gzip --list
printf 'VERDICT: PASS; fixed saved boundary and gzip only; no archive transformation\n'
