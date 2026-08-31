#!/bin/bash
set -euo pipefail
umask 077
stage=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
fixture=$(mktemp -d "${DEV147_TEST_ROOT:-${TMPDIR:-/tmp}}/dev147-usb-control.XXXXXXXXXX")
sandbox=(/usr/bin/bwrap --unshare-all --die-with-parent --new-session --clearenv --tmpfs / --ro-bind /usr /usr --symlink usr/bin /bin --symlink usr/lib /lib --symlink usr/lib /lib64 --dir /work --ro-bind "$stage/capture.py" /work/capture.py --ro-bind "$stage/test_capture.py" /work/test_capture.py --bind "$fixture" /fixtures --chdir /work --setenv PATH /usr/bin:/bin --setenv LANG C.UTF-8 --setenv TMPDIR /fixtures --uid 0 --gid 0 --cap-drop ALL)
printf 'Fixture retained: %s\n' "$fixture"
"${sandbox[@]}" /bin/bash -c '[[ $EUID == 0 && ! -e /sys && ! -e /proc && ! -e /run && ! -e /home && ! -e /dev ]]'
status=0
"${sandbox[@]}" /usr/bin/python3.14 -I -S -B /work/test_capture.py > "$fixture/tests.stdout" 2> "$fixture/tests.stderr" || status=$?
/usr/bin/sed -n '1,180p' "$fixture/tests.stderr"
(( status == 0 )) || exit "$status"
/bin/bash -n "${BASH_SOURCE[0]}"
git -C "$stage" diff --check
printf 'VERDICT: PASS\n'
