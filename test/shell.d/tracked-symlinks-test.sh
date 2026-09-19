#!/bin/bash

set -euo pipefail

source "$(dirname "$0")/base-test.sh"

require_command git

# Repository links must resolve inside the checkout without shell expansion.
# Elsewhen's user default instead points to its installed package payload.
# settings-package-units-test.sh checks that both package seed paths retain it.

tracked_symlinks() {
  git -C "$1" ls-files --stage | awk -F'\t' '$1 ~ /^120000 / { print $2 }'
}

check_tracked_symlinks() {
  local root="$1" symlink target resolved symlinks=()
  while IFS= read -r symlink; do
    [[ -n $symlink ]] && symlinks+=("$symlink")
  done < <(tracked_symlinks "$root")

  for symlink in "${symlinks[@]}"; do
    target=$(git -C "$root" cat-file -p ":$symlink")

    if [[ $symlink == "config/omarchy/plugins/omacom.elsewhen" ]]; then
      [[ $target == "/usr/share/omarchy/plugins/omacom.elsewhen" ]] ||
        fail "Elsewhen uses its exact package-owned target" "unexpected target: $target"
      grep -qxF 'elsewhen' "$root/install/omarchy-base.packages" ||
        fail "Elsewhen's link has its package in the default installation"
      continue
    fi

    [[ $target != /* ]] ||
      fail "tracked symlink is relative: $symlink" "absolute target: $target"

    [[ $target != *'$'* ]] ||
      fail "tracked symlink needs no shell expansion: $symlink" "unexpandable target: $target"

    resolved=$(realpath -m --relative-to="$root" "$root/$(dirname "$symlink")/$target")

    [[ $resolved != ../* ]] ||
      fail "tracked symlink stays inside the repo: $symlink" "escapes to: $target"

    [[ -e $root/$resolved ]] ||
      fail "tracked symlink resolves to a real path: $symlink" "dangling target: $target"
  done

  pass "tracked symlinks satisfy repository or exact package ownership (${#symlinks[@]} checked)"
}

check_tracked_symlinks "$ROOT"

test_dir=$(mktemp -d)
trap 'rm -rf "$test_dir"' EXIT
git -C "$test_dir" init -q
mkdir -p "$test_dir/config/omarchy/plugins" "$test_dir/install"
printf 'elsewhen\n' >"$test_dir/install/omarchy-base.packages"
touch "$test_dir/payload"
ln -s payload "$test_dir/relative-link"
plugin="$test_dir/config/omarchy/plugins/omacom.elsewhen"
ln -s /usr/share/omarchy/plugins/omacom.elsewhen "$plugin"
git -C "$test_dir" add .
check_tracked_symlinks "$test_dir"

expect_rejected() {
  if (check_tracked_symlinks "$test_dir") >"$test_dir/output" 2>&1; then
    fail "$1"
  fi
  grep -qF "$2" "$test_dir/output" || fail "$1" "$(cat "$test_dir/output")"
  pass "$1"
}

ln -sfn /usr/share/omarchy/plugins/local.unowned "$plugin"
git -C "$test_dir" add config/omarchy/plugins/omacom.elsewhen
expect_rejected "a wrong Elsewhen package target is rejected" "Elsewhen uses its exact package-owned target"

ln -sfn /usr/share/omarchy/plugins/omacom.elsewhen "$plugin"
git -C "$test_dir" add config/omarchy/plugins/omacom.elsewhen
ln -s /usr/share/omarchy/plugins/omacom.elsewhen "$test_dir/config/omarchy/plugins/local.unowned"
git -C "$test_dir" add config/omarchy/plugins/local.unowned
expect_rejected "the package target is rejected at any other tracked path" "tracked symlink is relative: config/omarchy/plugins/local.unowned"
git -C "$test_dir" rm -qf config/omarchy/plugins/local.unowned

: >"$test_dir/install/omarchy-base.packages"
expect_rejected "Elsewhen's link requires the package default" "Elsewhen's link has its package in the default installation"
printf 'elsewhen\n' >"$test_dir/install/omarchy-base.packages"

for target in '../outside' 'missing' '$HOME/payload'; do
  ln -sfn "$target" "$test_dir/relative-link"
  git -C "$test_dir" add relative-link
  expect_rejected "invalid repository target is rejected: $target" 'not ok - tracked symlink'
done
