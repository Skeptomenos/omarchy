#!/bin/bash

set -euo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

require_command git
require_command tar
require_command sysctl
pkgs_root="${OMARCHY_PKGS_PATH:-$ROOT/../omarchy-pkgs}"
test_tmp=$(mktemp -d)
trap 'rm -rf "$test_tmp"' EXIT
source "$ROOT/build-inputs/prepare-recipes.sh"
prepare_omarchy_recipes "$pkgs_root" "$test_tmp/recipes"
mkdir -p "$test_tmp/source/omarchy"
git -C "$ROOT" ls-files -z config etc default applications logo.txt logo.svg icon.txt icon.png \
  bin/omarchy-upload-log bin/omarchy-debug bin/omarchy-debug-idle \
  | tar -C "$ROOT" --null -T - -cf - \
  | tar -C "$test_tmp/source/omarchy" -xf -

cat >"$test_tmp/expected" <<'CONF'
net.ipv4.tcp_mtu_probing = 1
net.core.default_qdisc = fq
net.ipv4.tcp_congestion_control = bbr
CONF

failed=0
for flavor in omarchy-settings omarchy-settings-dev; do
  for architecture in aarch64 x86_64; do
    (
      CARCH=$architecture OMARCHY_SRC="$test_tmp/source/omarchy"
      srcdir="$test_tmp/source" pkgdir="$test_tmp/$flavor-$architecture"
      mkdir -p "$pkgdir"
      source "$test_tmp/recipes/pkgbuilds/$flavor/PKGBUILD"
      # Keep the real package staging; icon conversion is outside this contract.
      magick() { :; }
      package >"$test_tmp/$flavor-$architecture.log" 2>&1
      conf=etc/sysctl.d/99-omarchy-sysctl.conf
      [[ $(stat -c %a "$pkgdir/$conf") == "644" ]] || fail "$flavor/$architecture sysctl mode is 0644"
      printf '%s\n' "${backup[@]}" | grep -Fxq "$conf" || fail "$flavor/$architecture protects local sysctl edits"
      if [[ $architecture == "aarch64" ]]; then
        sysctl --dry-run --load "$pkgdir/$conf" >"$test_tmp/actual-$flavor"
        diff -u "$test_tmp/expected" "$test_tmp/actual-$flavor"
        for excluded in \
          etc/limine-entry-tool.d etc/mkinitcpio.conf.d etc/systemd/oomd.conf.d \
          etc/systemd/zram-generator.conf etc/tmpfiles.d/omarchy-zswap.conf \
          etc/modprobe.d/omarchy-usb-autosuspend.conf \
          usr/lib/systemd/user/app.slice.d/10-oomd.conf \
          usr/lib/systemd/zram-generator.conf.d/90-omarchy.conf \
          usr/share/omarchy/default/limine; do
          [[ ! -e $pkgdir/$excluded ]] || fail "$flavor retains its ARM exclusion for $excluded"
        done
        pass "$flavor stages all three network values, no VM knobs, and the existing ARM exclusions"
      else
        cmp "$srcdir/omarchy/$conf" "$pkgdir/$conf"
        pass "$flavor leaves the x86_64 sysctl payload byte-identical to source"
      fi
    ) &
    # Wait outside a conditional so errexit still applies inside package().
    pid=$!
    wait "$pid" || failed=1
  done
done
(( failed == 0 ))
