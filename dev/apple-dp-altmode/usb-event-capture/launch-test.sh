#!/bin/bash
set -euo pipefail
umask 077
stage=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
fixture=$(mktemp -d "${DEV147_TEST_ROOT:-${TMPDIR:-/tmp}}/dev147-usb-launch.XXXXXXXXXX")
script=$(< "$stage/launch.sh")
sandbox=(/usr/bin/bwrap --unshare-all --die-with-parent --new-session --clearenv --tmpfs / --ro-bind /usr /usr --symlink usr/bin /bin --symlink usr/lib /lib --symlink usr/lib /lib64 --setenv PATH /usr/bin:/bin --setenv LANG C.UTF-8 --uid 0 --gid 0 --cap-drop ALL --chdir /)
printf 'Fixture retained: %s\n' "$fixture"
fail() { printf 'FAIL: %s\nVERDICT: FAIL\n' "$1" >&2; exit 1; }
new_case() {
  case_dir=$(mktemp -d "$fixture/case.XXXXXXXXXX")
  mkdir -m 700 "$case_dir/run"
  printf '%s\n' 'from pathlib import Path' 'Path("/run/launched").write_text("fixture")' 'Path("/run/large-output").write_bytes(b"x" * 262144)' 'print("SAFE_LAUNCH_FIXTURE")' > "$case_dir/source.py"
  expected=$(/usr/bin/sha256sum "$case_dir/source.py")
  expected=${expected%% *}
  body=${script/UNRELEASED_SOURCE/\/fixture\/source.py}
  body=${body/UNRELEASED_SHA256/$expected}
}
run_case() {
  status=0
  /usr/bin/timeout --kill-after=1s 10s "${sandbox[@]}" --bind "$case_dir" /fixture --bind "$case_dir/run" /run /bin/bash -c "$1" > "$case_dir/stdout" 2> "$case_dir/stderr" || status=$?
}
refused() {
  (( status != 0 )) && [[ ! -s $case_dir/stdout && ! -e $case_dir/run/launched ]] || fail "$1 launched or returned success"
}
new_case
run_case "$script"
(( status == 77 )) && [[ ! -s $case_dir/stdout && $(< "$case_dir/stderr") == *UNRELEASED* ]] || fail 'public launcher must refuse before filesystem access'
[[ -z $(/usr/bin/find "$case_dir/run" -mindepth 1 -print -quit) ]] || fail 'unbound launcher created runtime files'
printf 'PASS: public launcher refuses before runtime access\n'
new_case
run_case "$body"
(( status == 0 )) && [[ $(< "$case_dir/stdout") == SAFE_LAUNCH_FIXTURE && -f $case_dir/run/launched ]] || fail 'verified root-private fixture was not executed'
[[ $(/usr/bin/stat -c %s "$case_dir/run/large-output") == 262144 ]] || fail 'copy size limit leaked into executed Python'
copied=()
while IFS= read -r path; do copied+=("$path"); done < <(/usr/bin/find "$case_dir/run" -mindepth 2 -maxdepth 2 -name capture.py -print)
(( ${#copied[@]} == 1 )) || fail 'expected one retained protected copy'
[[ $(/usr/bin/stat -c %a "${copied[0]}") == 600 ]] || fail 'copy permissions'
[[ $(/usr/bin/sha256sum "${copied[0]}") == "$expected "* ]] || fail 'executed copy differs from bound bytes'
printf 'PASS: exact inline body executes verified protected copy only\n'
new_case
printf '%s\n' 'raise RuntimeError("changed source must not execute")' >> "$case_dir/source.py"
run_case "$body"
refused 'changed-source hash failure'
[[ $(< "$case_dir/stderr") == *dev147-usb-launch.* ]] || fail 'failed-copy stage path missing'
printf 'PASS: source changed after binding is not executed\n'
new_case
chmod 000 "$case_dir/source.py"
run_case "$body"
refused 'unreadable copy source'
chmod 600 "$case_dir/source.py"
printf 'PASS: copy failure does not execute Python\n'
new_case
mv "$case_dir/source.py" "$case_dir/original.py"
ln -s /fixture/original.py "$case_dir/source.py"
run_case "$body"
refused 'source symlink'
printf 'PASS: source symlink is refused\n'
new_case
mv "$case_dir/source.py" "$case_dir/original.py"
mkfifo "$case_dir/source.py"
run_case "$body"
refused 'source FIFO'
printf 'PASS: nonregular source is refused without a read\n'
new_case
/usr/bin/truncate -s 131073 "$case_dir/source.py"
run_case "$body"
refused 'oversized source'
[[ -z $(/usr/bin/find "$case_dir/run" -name capture.py -print -quit) ]] || fail 'oversized source was copied'
printf 'PASS: oversized source cannot launch or write a helper copy\n'
for path in "$stage/launch.sh" "${BASH_SOURCE[0]}"; do /bin/bash -n "$path"; done
if /usr/bin/grep -nE '^[[:space:]]*#[^!]' "$stage/launch.sh" "${BASH_SOURCE[0]}"; then fail 'code comment'; fi
git -C "$stage" diff --check
printf 'VERDICT: PASS\n'
