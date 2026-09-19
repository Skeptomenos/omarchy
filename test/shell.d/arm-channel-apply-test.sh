#!/bin/bash

set -euo pipefail
source "$(dirname "$0")/base-test.sh"
source "$ROOT/install/helpers/arm-channel.sh"

test_tmp=$(mktemp -d)
trap 'rm -rf "$test_tmp"' EXIT
mkdir -p "$test_tmp/bin"
export PATH="$test_tmp/bin:$ROOT/bin:$PATH"
export CHANNEL_APPLY_LOG="$test_tmp/calls" CHANNEL_APPLY_DB="$test_tmp/db"

cat >"$test_tmp/bin/sudo" <<'SH'
#!/bin/bash
exec "$@"
SH
cat >"$test_tmp/bin/systemd-run" <<'SH'
#!/bin/bash
[[ $1 == "--scope" && $2 == "--quiet" && $3 == "--collect" ]] || exit 99
echo scope >>"$CHANNEL_APPLY_LOG"
shift 3
exec "$@"
SH
cat >"$test_tmp/bin/pacman-conf" <<'SH'
#!/bin/bash
echo "$CHANNEL_APPLY_DB"
SH
cat >"$test_tmp/bin/pacman" <<'SH'
#!/bin/bash
[[ $1 == "--config" && $2 == "$CHANNEL_APPLY_STAGE/frozen.conf" ]] || exit 99
shift 2
case "$1" in
  -Syy) exit 0 ;;
  -Sup) cat "$CHANNEL_APPLY_STAGE/expected" ;;
  -Syu)
    [[ $* == "-Syu --needed --noconfirm --ask 4 --ignore hyprland omarchy/hyprland omarchy-aarch64/omarchy omarchy-aarch64/omarchy-settings" ]] || exit 99
    [[ ${LC_ALL:-} == "C" && ${OMARCHY_UPDATE_PACMAN:-} == "1" ]] || exit 99
    echo transaction >>"$CHANNEL_APPLY_LOG"
    if [[ ${CHANNEL_APPLY_FAILURE:-} == "hook" ]]; then echo 'error: hook failed'; fi
    exit "${CHANNEL_APPLY_STATUS:-0}"
    ;;
  -Q) echo 'omarchy 4.0.3rc4-1' ;;
  *) exit 99 ;;
esac
SH
chmod +x "$test_tmp/bin/"*

for scenario in success failure hook; do
  export CHANNEL_APPLY_STAGE="$test_tmp/$scenario with spaces"
  stage="$CHANNEL_APPLY_STAGE"
  mkdir -p "$stage" "$CHANNEL_APPLY_DB/sync"
  config="$stage/pacman.conf"
  echo original >"$config"
  cp "$config" "$stage/original.conf"
  echo replacement >"$stage/source.conf"
  : >"$stage/frozen.conf"
  echo "$config" >"$stage/config-path"
  echo rc >"$stage/channel"
  echo 4.0.3rc4-1 >"$stage/pair-version"
  printf '%s\n' --ignore hyprland omarchy/hyprland omarchy-aarch64/omarchy omarchy-aarch64/omarchy-settings >"$stage/targets"
  echo 'frozen manifest' >"$stage/expected"
  : >"$CHANNEL_APPLY_LOG"
  export CHANNEL_APPLY_STATUS=0 CHANNEL_APPLY_FAILURE="$scenario"
  [[ $scenario != "failure" ]] || CHANNEL_APPLY_STATUS=42
  if omarchy_arm_channel_apply_prepared "$stage" >"$test_tmp/output" 2>&1; then
    [[ $scenario == "success" ]] || fail "$scenario must not report success"
    cmp -s "$config" "$stage/source.conf" || fail 'success commits the prepared config'
    [[ ! -e $stage/restore-sync ]] || fail 'success clears rollback state'
  else
    [[ $scenario != "success" ]] || fail 'the prepared transaction succeeds' "$(cat "$test_tmp/output")"
    cmp -s "$config" "$stage/original.conf" || fail "$scenario preserves the active config"
    [[ -f $stage/restore-sync ]] || fail "$scenario retains rollback state"
  fi
  expected=transaction
  if [[ -d /run/systemd/system && ! -L /run/systemd/system ]]; then expected=$'scope\ntransaction'; fi
  [[ $(cat "$CHANNEL_APPLY_LOG") == "$expected" ]] || fail "$scenario uses the guarded transaction wrapper"
  pass "$scenario preserves the frozen transaction, locale, scope selection, and config outcome"
done
