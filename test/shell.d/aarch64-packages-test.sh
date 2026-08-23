#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

base_packages="$ROOT/install/omarchy-base.packages"
unavailable="$ROOT/install/omarchy-aarch64-unavailable.packages"

mapfile -t unavailable_packages < <(grep -vE '^[[:space:]]*(#|$)' "$unavailable")
(( ${#unavailable_packages[@]} )) || fail "the aarch64 unavailable list names at least one package"

# An entry for a package the set never installs is dead weight that reads like
# coverage, so keep the list answerable against the set it filters.
for package in "${unavailable_packages[@]}"; do
  grep -qxF "$package" "$base_packages" ||
    fail "every unavailable entry is in the default package set" "not in the set: $package"
done
pass "every unavailable entry is in the default package set"

grep -qF 'package_is_unavailable_here' "$ROOT/install.sh" ||
  fail "the installer filters the default set through the unavailable list"
pass "the installer filters the default set through the unavailable list"

# The list is a default, not a verdict: AUR packages gain ARM support over time,
# so a stale entry has to cost a prompt rather than be permanently wrong.
grep -qF 'OMARCHY_TRY_UNAVAILABLE' "$ROOT/install.sh" ||
  fail "the unavailable list can be overridden"
grep -qF '[[ -r /dev/tty ]] || return 1' "$ROOT/install.sh" ||
  fail "the installer skips without a terminal instead of blocking on a prompt"
pass "the unavailable list is a prompt-able default, and never blocks a headless install"

# These have aarch64 builds in the Omarchy ARM repo, so skipping them would
# trade a slow install for a broken one.
for package in herdr omacalc omacut omawrite; do
  for entry in "${unavailable_packages[@]}"; do
    [[ $entry == "$package" ]] &&
      fail "packages the ARM repo provides are installed, not skipped" "wrongly skipped: $package"
  done
done
pass "packages the ARM repo provides are installed, not skipped"

arm_builds="$ROOT/install/omarchy-aarch64-build.packages"
[[ -f $arm_builds ]] || fail "the Apple Silicon installer declares its native ARM package builds"
grep -qxF 'quickshell' "$base_packages" ||
  fail "fresh installs use the stable Quickshell package"
grep -qxF 'quickshell-git' "$base_packages" &&
  fail "fresh installs do not use the moving Quickshell git package"
for package in quickshell quickshell-git; do
  grep -qxF "$package" "$arm_builds" &&
    fail "repository packages are not built in the Apple Silicon package path" "$package is still in the build list"
done
pass "fresh Apple Silicon installs use stable Quickshell without building it"

for package in herdr ttfx; do
  grep -qxF "$package" "$arm_builds" ||
    fail "the ARM build list includes the validated native package" "$package is missing"
done
grep -qF 'omarchy-aarch64-build.packages' "$ROOT/build-packages.sh" ||
  fail "the package builder consumes the ARM build list"
pass "validated native ARM builds are part of the Mac package path"

# The official Tensaku package is still x86_64-only. The AUR binary package is
# a native ARM provider, so both fresh installs and later migrations must use
# the same override.
grep -qF 'OMARCHY_TENSAKU_PACKAGE' "$ROOT/install.sh" ||
  fail "the fresh installer exposes the Tensaku ARM package override"
grep -qF 'tensaku-bin' "$ROOT/install.sh" ||
  fail "the fresh installer defaults Tensaku to the ARM binary package"
grep -qF 'OMARCHY_TENSAKU_PACKAGE' "$ROOT/bin/omarchy-pkg-add" ||
  fail "the migration package helper exposes the Tensaku ARM package override"
pass "Tensaku uses one explicit ARM package override for install and migration"

# Mise is required by user provisioning but is not in the Arch Linux ARM
# package repositories. Keep Basecamp's generic mise-bin package declaration,
# but resolve it back to the logical mise contract before the ARM package loop
# and bootstrap the verified official binary before provisioning.
grep -qxF 'mise-bin' "$base_packages" ||
  fail "the generic package set retains Basecamp's mise-bin package"
grep -qF '$package == "mise-bin"' "$ROOT/install.sh" ||
  fail "the Apple Silicon installer resolves mise-bin for ARM"
grep -qF '$install_package == "mise"' "$ROOT/install.sh" ||
  fail "the Apple Silicon package loop skips the logical mise package"
grep -qF 'install/helpers/mise.sh' "$ROOT/install.sh" ||
  fail "the installer loads the shared verified mise bootstrap"
grep -qF 'omarchy_ensure_arm_mise' "$ROOT/install.sh" ||
  fail "the installer bootstraps mise before user provisioning"
grep -qF 'OMARCHY_MISE_SHA256' "$ROOT/install/helpers/mise.sh" ||
  fail "the mise bootstrap verifies its downloaded ARM binary"
pass "mise keeps the generic package and verified ARM bootstrap paths"

# Without a repo carrying them, herdr pulls zig0.15 and builds it for hours
# before aarch64 rejects it.
for config in "$ROOT"/default/pacman/pacman*.conf; do
  grep -qF '[omarchy-aarch64]' "$config" ||
    fail "every shipped pacman config offers the Omarchy ARM repo" "missing in: $(basename "$config")"
  # A Server line needs no mirrorlist installed alongside it, unlike an Include.
  grep -A3 -F '[omarchy-aarch64]' "$config" | grep -qE '^Server[[:space:]]*=' ||
    fail "the ARM repo is reached by Server, not an Include" "in: $(basename "$config")"
done
pass "every shipped pacman config offers the Omarchy ARM repo"

grep -qF 'OMARCHY_ARM_PACKAGE_SERVER' "$ROOT/install.sh" ||
  fail "the ARM package repository can be redirected to a controlled channel"
pass "the ARM package repository has an explicit owner-controlled override"

# The shipped config only reaches /etc during post-install, which runs after the
# package set. Adding the repo any later leaves herdr building zig from source
# for two hours, so the order in main() is the whole point of the fix.
repo_call=$(grep -n '^  ensure_arm_package_repo$' "$ROOT/install.sh" | cut -d: -f1)
set_call=$(grep -n '^  install_default_package_set$' "$ROOT/install.sh" | cut -d: -f1)
[[ -n $repo_call && -n $set_call ]] || fail "the installer adds the ARM repo and installs the set"
(( repo_call < set_call )) ||
  fail "the ARM repo is added before the default package set is installed"
pass "the ARM repo is added before the default package set is installed"
