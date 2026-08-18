#!/bin/bash

source "$(dirname "$0")/base-test.sh"

test_tmp=$(mktemp -d)
trap 'rm -rf "$test_tmp"' EXIT

fake_omarchy="$test_tmp/omarchy"
home="$test_tmp/home"
mkdir -p "$fake_omarchy" "$home"
printf 'default about\n' >"$fake_omarchy/icon.txt"
printf 'default screensaver\n' >"$fake_omarchy/logo.txt"

run_branding() {
  HOME="$home" OMARCHY_PATH="$fake_omarchy" bash "$ROOT/install/user/branding.sh"
}

run_branding

[[ -f $home/.config/omarchy/branding/about.txt ]] || fail "branding setup creates about.txt"
[[ -f $home/.config/omarchy/branding/screensaver.txt ]] || fail "branding setup creates screensaver.txt"
cmp -s "$fake_omarchy/icon.txt" "$home/.config/omarchy/branding/about.txt" ||
  fail "branding setup copies the shipped about default"
cmp -s "$fake_omarchy/logo.txt" "$home/.config/omarchy/branding/screensaver.txt" ||
  fail "branding setup copies the shipped screensaver default"
[[ -r $home/.config/omarchy/branding/screensaver.txt ]] ||
  fail "branding setup creates a user-readable screensaver file"
pass "branding setup seeds missing defaults"

printf 'custom screensaver\n' >"$home/.config/omarchy/branding/screensaver.txt"
run_branding
grep -qxF 'custom screensaver' "$home/.config/omarchy/branding/screensaver.txt" ||
  fail "branding setup preserves custom branding"
pass "branding setup preserves existing branding"

rm "$home/.config/omarchy/branding/about.txt"
ln -s "$test_tmp/missing-about.txt" "$home/.config/omarchy/branding/about.txt"
run_branding
[[ -L $home/.config/omarchy/branding/about.txt ]] ||
  fail "branding setup preserves a broken branding symlink"
pass "branding setup preserves branding symlinks"
