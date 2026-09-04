#!/bin/bash
set -euo pipefail
[[ $# == 3 ]]
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
image=$(realpath -e "$1")
build_root=$(realpath -e "$2")
checks=$(realpath -e "$3")
work=$(mktemp -d "$checks/image-validation.XXXXXX")
mkdir "$work/extracted"
sha256sum "$image" > "$work/image.sha256"
bwrap --unshare-all --die-with-parent --new-session --uid 0 --gid 0 \
  --ro-bind /usr /usr --ro-bind /etc /etc \
  --symlink usr/lib /lib --symlink usr/bin /bin --symlink usr/bin /sbin \
  --proc /proc --dev /dev --tmpfs /tmp --dir /sys --dir /run --dir /home \
  --bind "$work/extracted" /work --ro-bind "$image" /image \
  --clearenv --setenv PATH /usr/bin --setenv HOME /tmp --setenv LC_ALL C \
  --chdir /work /usr/bin/fakeroot /usr/bin/lsinitcpio -x /image > "$work/extract.log" 2>&1
bash "$script_dir/verify.sh" "$work/extracted" "$build_root" > "$work/verification.log" 2>&1
sha256sum --check --strict "$work/image.sha256"
sha256sum "$script_dir"/*.sh > "$work/validator.sha256"
cat "$work/verification.log"
printf 'Evidence: %s\n' "$work"
