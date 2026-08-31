#!/bin/bash
set -euo pipefail
umask 077
source_path='UNRELEASED_SOURCE'
expected_sha='UNRELEASED_SHA256'
(( $# == 0 )) || exit 64
[[ $expected_sha =~ ^[0-9a-f]{64}$ && $source_path == /* ]] || { printf '{"status":"UNRELEASED"}\n' >&2; exit 77; }
(( EUID == 0 )) || exit 77
launch_dir=$(/usr/bin/mktemp -d /run/dev147-usb-launch.XXXXXXXXXX)
printf '{"status":"LAUNCH_COPY","evidence":"%s"}\n' "$launch_dir" >&2
[[ $(/usr/bin/stat -c %u:%a -- "$launch_dir") == "0:700" ]] || exit 1
protected_copy=$launch_dir/capture.py
[[ -f $source_path && ! -L $source_path ]] || exit 1
source_size=$(/usr/bin/stat -c %s -- "$source_path")
[[ $source_size =~ ^[0-9]+$ ]] && (( source_size > 0 && source_size <= 131072 )) || exit 1
(
  ulimit -f 128
  /usr/bin/timeout --kill-after=1s 5s /usr/bin/cp --no-dereference -- "$source_path" "$protected_copy"
)
[[ -f $protected_copy && ! -L $protected_copy ]] || exit 1
/usr/bin/chmod 600 -- "$protected_copy"
[[ $(/usr/bin/stat -c %u:%a -- "$protected_copy") == "0:600" ]] || exit 1
copy_size=$(/usr/bin/stat -c %s -- "$protected_copy")
(( copy_size > 0 && copy_size <= 131072 )) || exit 1
printf '%s  %s\n' "$expected_sha" "$protected_copy" | /usr/bin/sha256sum --check --status -
exec /usr/bin/python3.14 -I -S -B "$protected_copy"
