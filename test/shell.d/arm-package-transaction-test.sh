#!/bin/bash

set -euo pipefail
source "$(dirname "$0")/base-test.sh"
source "$ROOT/install/helpers/arm-package-sources.sh"

# Ubuntu's ordinary shell-test job has no pacman; the ARM install machine runs
# this test with real libalpm before attempting the network installation.
if ! command -v pacman >/dev/null; then
  pass 'pacman unavailable; package transaction regression runs in the ARM install machine'
  exit 0
fi

test_tmp=$(mktemp -d)
trap 'rm -rf "$test_tmp"' EXIT
mkdir -p "$test_tmp/db/local" "$test_tmp/db/sync"
printf '9\n' > "$test_tmp/db/local/ALPM_DB_VERSION"

write_desc() {
  printf '%%NAME%%\n%s\n\n%%VERSION%%\n%s\n\n%%ARCH%%\n%s\n\n' "$1" "$2" "$(uname -m)"
  printf '%%FILENAME%%\n%s-%s.pkg.tar.zst\n\n%%CSIZE%%\n1\n\n%%ISIZE%%\n1\n\n' "$1" "$2"
}
write_package() {
  local directory="$1/$2-$3"
  mkdir -p "$directory"
  write_desc "$2" "$3" > "$directory/desc"
}
for package in hyprland hyprtoolkit hyprland-guiutils asdcontrol openclaw perplexity v4l2-relayd normal; do
  write_package "$test_tmp/db/local" "$package" '2-1'
  : > "$test_tmp/db/local/$package-2-1/files"
  write_package "$test_tmp/extra" "$package" '4-1'
done
tar -czf "$test_tmp/db/sync/extra.db" -C "$test_tmp/extra" --transform='s|^\./||' .
cat > "$test_tmp/pacman.conf" <<CONF
[options]
Architecture = auto
DBPath = $test_tmp/db
LogFile = $test_tmp/pacman.log
SigLevel = Never
[extra]
Server = file:///nonexistent
[omarchy]
Usage = Sync
Server = file:///nonexistent
CONF

select_packages() {
  pacman --config "$test_tmp/pacman.conf" -Sup --needed --noconfirm \
    --print-format '%r/%n %v' "$@" 2> "$test_tmp/errors"
}
export OMARCHY_PACMAN_CONFIG="$test_tmp/pacman.conf"
mapfile -t targets < <(omarchy_arm_package_upgrade_args)
for version in 2-1 3-1 1-1; do
  rm -rf "$test_tmp/omarchy"
  for package in hyprland hyprtoolkit hyprland-guiutils asdcontrol openclaw perplexity v4l2-relayd tobi-try; do
    write_package "$test_tmp/omarchy" "$package" "$version"
  done
  tar -czf "$test_tmp/db/sync/omarchy.db" -C "$test_tmp/omarchy" --transform='s|^\./||' .
  selected=$(select_packages "${targets[@]}") || fail 'pacman resolves the protected transaction' "$(cat "$test_tmp/errors")"
  grep -qx 'extra/normal 4-1' <<< "$selected" || fail 'ordinary packages still upgrade'
  ! grep -q 'tobi-try' <<< "$selected" || fail 'removed optional defaults remain removed'
  ! grep -q '^extra/asdcontrol' <<< "$selected" || fail 'installed upstream-only optional defaults retain their selected source'
  ! grep -qE '^extra/(openclaw|perplexity|v4l2-relayd) ' <<< "$selected" || fail 'installed optional packages retain their explicit source'
  ! grep -q '^extra/hypr' <<< "$selected" || fail 'regular repository cannot replace the selected stack'
  if [[ $version == "2-1" ]]; then
    [[ $selected == 'extra/normal 4-1' ]] || fail 'unchanged compositor packages are not reinstalled'
    mapfile -t unprotected < <(omarchy_arm_package_targets)
    baseline=$(select_packages "${unprotected[@]}")
    grep -qx 'extra/hyprtoolkit 4-1' <<< "$baseline" || fail 'fixture reproduces the original --needed sysupgrade bug'
  else
    for package in hyprland hyprtoolkit hyprland-guiutils asdcontrol openclaw perplexity v4l2-relayd; do
      grep -qx "omarchy/$package $version" <<< "$selected" || fail 'changed packages use the explicit repository, including downgrades'
    done
  fi
  pass "real pacman preserves selected $version stack while upgrading ordinary packages"
done

for package in openclaw perplexity v4l2-relayd; do
  rm -rf "$test_tmp/db/local/$package-2-1"
done
mapfile -t targets < <(omarchy_arm_package_upgrade_args)
selected=$(select_packages "${targets[@]}") || fail 'removed optional packages still permit updates'
! grep -qE '(openclaw|perplexity|v4l2-relayd)' <<< "$selected" || fail 'intentionally removed optional packages stay removed'
pass 'OpenClaw, Perplexity, and the Cam Link relay upgrade through the explicit repository only while installed'

# Model fresh installs where these packages exist only in the Sync-only repo.
# Metadata lookup succeeds for a bare name, but transaction resolution must use
# the qualified name. The shim resolves with real pacman, then records only the
# selected metadata in the disposable local DB for the helper's post-check.
for package in openclaw perplexity v4l2-relayd; do
  rm -rf "$test_tmp/extra/$package-4-1"
done
tar -czf "$test_tmp/db/sync/extra.db" -C "$test_tmp/extra" --transform='s|^\./||' .
export ARM_PACKAGE_TEST_PACMAN="$(command -v pacman)" ARM_PACKAGE_TEST_ROOT="$test_tmp"
mkdir -p "$test_tmp/bin"
cat >"$test_tmp/bin/uname" <<'SH'
#!/bin/bash
echo aarch64
SH
cat >"$test_tmp/bin/sudo" <<'SH'
#!/bin/bash
[[ $1 == "pacman" ]] || exit 97
exec "$@"
SH
cat >"$test_tmp/bin/pacman" <<'SH'
#!/bin/bash
set -euo pipefail
case "$1" in
  -Q | -Si)
    exec "$ARM_PACKAGE_TEST_PACMAN" --config "$ARM_PACKAGE_TEST_ROOT/pacman.conf" "$@"
    ;;
  -S)
    shift
    "$ARM_PACKAGE_TEST_PACMAN" --config "$ARM_PACKAGE_TEST_ROOT/pacman.conf" \
      -Sp --print-format '%r/%n %v' "$@" >"$ARM_PACKAGE_TEST_ROOT/resolved"
    while read -r target version; do
      package="${target#*/}"
      local_record="$ARM_PACKAGE_TEST_ROOT/db/local/$package-$version"
      mkdir -p "$local_record"
      cp "$ARM_PACKAGE_TEST_ROOT/${target%/*}/$package-$version/desc" "$local_record/desc"
      : >"$local_record/files"
    done <"$ARM_PACKAGE_TEST_ROOT/resolved"
    ;;
  *) exit 97 ;;
esac
SH
chmod +x "$test_tmp/bin/"*

for package in openclaw perplexity v4l2-relayd; do
  "$ARM_PACKAGE_TEST_PACMAN" --config "$test_tmp/pacman.conf" -Si "$package" >/dev/null ||
    fail "bare $package metadata is visible in the Sync-only repository"
  if "$ARM_PACKAGE_TEST_PACMAN" --config "$test_tmp/pacman.conf" -Sp "$package" >"$test_tmp/errors" 2>&1; then
    fail "the fixture rejects bare $package installation from a Sync-only repository"
  fi
  grep -qF "target not found: $package" "$test_tmp/errors" || fail "$package fails specifically at target resolution"
  PATH="$test_tmp/bin:$PATH" "$ROOT/bin/omarchy-pkg-add" "$package" ||
    fail "the package helper resolves and verifies a fresh $package installation"
  [[ $(cat "$test_tmp/resolved") == "omarchy/$package 1-1" ]] || fail "$package installs from its explicit source"
  "$ARM_PACKAGE_TEST_PACMAN" --config "$test_tmp/pacman.conf" -Q "$package" >/dev/null || fail "$package has an installed record"
  : >"$test_tmp/resolved"
  PATH="$test_tmp/bin:$PATH" "$ROOT/bin/omarchy-pkg-add" "$package" || fail "$package repeat installation succeeds"
  [[ ! -s $test_tmp/resolved ]] || fail "$package repeat installation does not open another transaction"
  pass "real pacman resolves fresh $package through the helper's qualified source and skips installed copies"
done
