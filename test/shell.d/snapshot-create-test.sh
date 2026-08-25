#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

snapshot="$ROOT/bin/omarchy-snapshot"

test_tmp=$(mktemp -d)
trap 'rm -rf "$test_tmp"' EXIT

fake_bin="$test_tmp/bin"
mkdir -p "$fake_bin"

boot_root="$test_tmp/boot"
etc_root="$test_tmp/etc"
compatible_file="$test_tmp/compatible"

cat >"$fake_bin/findmnt" <<'STUB'
#!/bin/bash
if [[ $* == *"FSTYPE"* ]]; then
  echo "${ROOT_FSTYPE:-btrfs}"
fi
STUB
chmod +x "$fake_bin/findmnt"

cat >"$fake_bin/uname" <<'STUB'
#!/bin/bash
echo "${TEST_ARCH:-x86_64}"
STUB
chmod +x "$fake_bin/uname"

cat >"$fake_bin/systemctl" <<'STUB'
#!/bin/bash
printf 'systemctl %s\n' "$*" >>"$TEST_LOG"
case "${1:-}" in
is-enabled)
  (( ${LIMINE_SYNC_ENABLED:-1} ))
  ;;
is-active)
  (( ${LIMINE_SYNC_ACTIVE:-1} ))
  ;;
esac
STUB
chmod +x "$fake_bin/systemctl"

cat >"$fake_bin/sudo" <<'STUB'
#!/bin/bash
printf 'sudo %s\n' "$*" >>"$TEST_LOG"
exec "$@"
STUB
chmod +x "$fake_bin/sudo"

cat >"$fake_bin/omarchy-cmd-missing" <<'STUB'
#!/bin/bash
case "$1" in
snapper)
  [[ ${SNAPPER_PRESENT:-1} == "0" ]]
  ;;
limine-snapper-restore)
  [[ ${LIMINE_RESTORE_PRESENT:-1} == "0" ]]
  ;;
limine-entry-tool)
  [[ ${LIMINE_ENTRY_TOOL_PRESENT:-1} == "0" ]]
  ;;
omarchy-mac-snapshot-restore)
  [[ ${MAC_RESTORE_PRESENT:-0} == "0" ]]
  ;;
*)
  exit 1
  ;;
esac
STUB
chmod +x "$fake_bin/omarchy-cmd-missing"

cat >"$fake_bin/omarchy-version" <<'STUB'
#!/bin/bash
echo 4.0.0
STUB
chmod +x "$fake_bin/omarchy-version"

cat >"$fake_bin/snapper" <<'STUB'
#!/bin/bash
printf 'snapper %s\n' "$*" >>"$TEST_LOG"
if [[ $* == *"list-configs"* ]]; then
  echo "config,subvolume"
  if [[ ${SNAPPER_CONFIGURED:-1} == "1" ]]; then
    echo "root,${SNAPPER_ROOT_SUBVOLUME:-/}"
  fi
fi
STUB
chmod +x "$fake_bin/snapper"

cat >"$fake_bin/limine-snapper-restore" <<'STUB'
#!/bin/bash
printf 'limine-snapper-restore %s\n' "$*" >>"$TEST_LOG"
STUB
chmod +x "$fake_bin/limine-snapper-restore"

cat >"$fake_bin/omarchy-mac-snapshot-restore" <<'STUB'
#!/bin/bash
printf 'omarchy-mac-snapshot-restore %s\n' "$*" >>"$TEST_LOG"
STUB
chmod +x "$fake_bin/omarchy-mac-snapshot-restore"

prepare_platform() {
  rm -rf "$boot_root"
  mkdir -p "$boot_root"
  rm -rf "$etc_root"
  mkdir -p "$etc_root"

  case "${TEST_BOOT_MODE:-limine}" in
  limine)
    : >"$boot_root/limine.conf"
    ;;
  grub)
    mkdir -p "$boot_root/grub"
    : >"$boot_root/grub/grub.cfg"
    : >"$boot_root/limine.conf"
    ;;
  grub-only)
    mkdir -p "$boot_root/grub"
    : >"$boot_root/grub/grub.cfg"
    ;;
  systemd-boot)
    mkdir -p "$boot_root/loader"
    : >"$boot_root/loader/loader.conf"
    : >"$boot_root/limine.conf"
    ;;
  none) ;;
  esac

  if [[ ${TEST_GRUB_ETC_CONFIG:-0} == "1" ]]; then
    mkdir -p "$etc_root/default"
    : >"$etc_root/default/grub"
  fi

  if [[ ${TEST_APPLE_SILICON:-0} == "1" ]]; then
    printf 'apple,j413\0' >"$compatible_file"
  else
    printf 'linux,dummy\0' >"$compatible_file"
  fi
}

run_snapshot() {
  prepare_platform
  : >"$test_tmp/calls.log"
  set +e
  snapshot_output=$(
    ROOT_FSTYPE="${TEST_ROOT_FSTYPE:-btrfs}" \
    TEST_ARCH="${TEST_ARCH:-x86_64}" \
    SNAPPER_PRESENT="${TEST_SNAPPER_PRESENT:-1}" \
    SNAPPER_CONFIGURED="${TEST_SNAPPER_CONFIGURED:-1}" \
    SNAPPER_ROOT_SUBVOLUME="${TEST_SNAPPER_ROOT_SUBVOLUME:-/}" \
    LIMINE_RESTORE_PRESENT="${TEST_LIMINE_RESTORE_PRESENT:-1}" \
    LIMINE_ENTRY_TOOL_PRESENT="${TEST_LIMINE_ENTRY_TOOL_PRESENT:-1}" \
    LIMINE_SYNC_ENABLED="${TEST_LIMINE_SYNC_ENABLED:-1}" \
    LIMINE_SYNC_ACTIVE="${TEST_LIMINE_SYNC_ACTIVE:-1}" \
    MAC_RESTORE_PRESENT="${TEST_MAC_RESTORE_PRESENT:-0}" \
    OMARCHY_APPLE_COMPATIBLE="$compatible_file" \
    OMARCHY_SNAPSHOT_BOOT_ROOT="$boot_root" \
    OMARCHY_SNAPSHOT_ETC_ROOT="$etc_root" \
    TEST_LOG="$test_tmp/calls.log" \
    PATH="$fake_bin:$PATH" \
      bash "$snapshot" "$1" 2>&1
  )
  snapshot_status=$?
  set -e
}

run_snapshot check
(( snapshot_status == 0 )) || fail "snapshot check accepts a configured Btrfs root with Limine restore" "$snapshot_output"
grep -qF 'Automatic rollback is ready' <<<"$snapshot_output" || fail "snapshot check reports readiness" "$snapshot_output"
! grep -q '^sudo ' "$test_tmp/calls.log" || fail "snapshot check stays read-only" "$(cat "$test_tmp/calls.log")"
pass "snapshot check reports a ready Btrfs and Limine installation"

TEST_ROOT_FSTYPE=ext4 run_snapshot check
(( snapshot_status != 0 )) || fail "snapshot check rejects a plain ext4 root"
grep -qF '/ uses ext4' <<<"$snapshot_output" || fail "snapshot check names the unsupported root filesystem" "$snapshot_output"
grep -qF 'https://github.com/Skeptomenos/omarchy-mac/blob/quattro-arm/manual/47-system-snapshots.md' <<<"$snapshot_output" || fail "snapshot check points to the durable fork recovery guide" "$snapshot_output"
! grep -q '^sudo ' "$test_tmp/calls.log" || fail "unsupported snapshot check stays read-only" "$(cat "$test_tmp/calls.log")"
pass "snapshot check explains that plain ext4 has no rollback snapshots"

TEST_SNAPPER_CONFIGURED=0 run_snapshot check
(( snapshot_status != 0 )) || fail "snapshot check rejects an unconfigured Btrfs root"
grep -qF 'no Snapper root configuration' <<<"$snapshot_output" || fail "snapshot check identifies an unconfigured snapshot-capable root" "$snapshot_output"
grep -qF 'Configure Snapper with:' <<<"$snapshot_output" || fail "snapshot check gives Btrfs configuration advice" "$snapshot_output"
pass "snapshot check separates unconfigured Btrfs from unsupported ext4"

TEST_SNAPPER_PRESENT=0 run_snapshot check
(( snapshot_status == 127 )) || fail "snapshot check keeps missing Snapper distinguishable" "got $snapshot_status: $snapshot_output"
grep -qF 'Snapper is not installed' <<<"$snapshot_output" || fail "snapshot check identifies missing Snapper" "$snapshot_output"
pass "snapshot check keeps the missing-Snapper status distinct"

TEST_LIMINE_RESTORE_PRESENT=0 run_snapshot check
(( snapshot_status != 0 )) || fail "snapshot check rejects a configured root without a restore backend"
grep -qF 'no supported automatic restore backend' <<<"$snapshot_output" || fail "snapshot check identifies the missing restore backend" "$snapshot_output"
pass "snapshot check reports configured snapshots without automatic restore"

TEST_SNAPPER_ROOT_SUBVOLUME=/home run_snapshot check
(( snapshot_status != 0 )) || fail "snapshot check rejects a root config for /home"
grep -qF 'does not target /' <<<"$snapshot_output" || fail "snapshot check explains the wrong Snapper target" "$snapshot_output"
! grep -q '^sudo ' "$test_tmp/calls.log" || fail "wrong-target snapshot check stays read-only" "$(cat "$test_tmp/calls.log")"
pass "snapshot check requires the root config to target slash"

TEST_LIMINE_SYNC_ENABLED=0 run_snapshot check
(( snapshot_status != 0 )) || fail "snapshot check rejects disabled Limine snapshot sync"
grep -qF 'no supported automatic restore backend' <<<"$snapshot_output" || fail "snapshot check reports disabled Limine sync as unavailable" "$snapshot_output"
pass "snapshot check requires Limine snapshot sync to be enabled"

TEST_LIMINE_SYNC_ACTIVE=0 run_snapshot check
(( snapshot_status != 0 )) || fail "snapshot check rejects inactive Limine snapshot sync"
grep -qF 'no supported automatic restore backend' <<<"$snapshot_output" || fail "snapshot check reports inactive Limine sync as unavailable" "$snapshot_output"
pass "snapshot check requires Limine snapshot sync to be active"

TEST_BOOT_MODE=none run_snapshot check
(( snapshot_status != 0 )) || fail "snapshot check accepts Limine helpers without canonical limine.conf"
pass "snapshot check requires canonical boot Limine configuration"

TEST_LIMINE_ENTRY_TOOL_PRESENT=0 run_snapshot check
(( snapshot_status != 0 )) || fail "snapshot check accepts Limine without its entry tool"
pass "snapshot check requires the Limine entry tool"

TEST_BOOT_MODE=grub run_snapshot check
(( snapshot_status != 0 )) || fail "snapshot check rejects stale Limine helpers on GRUB"
grep -qF 'no supported automatic restore backend' <<<"$snapshot_output" || fail "snapshot check reports GRUB as unavailable" "$snapshot_output"
pass "snapshot check does not equate stale Limine helpers with a restore backend"

TEST_GRUB_ETC_CONFIG=1 run_snapshot check
(( snapshot_status != 0 )) || fail "snapshot check accepts Limine when /etc/default/grub marks GRUB"
grep -qF 'no supported automatic restore backend' <<<"$snapshot_output" || fail "snapshot check reports the GRUB config marker as unavailable" "$snapshot_output"
pass "snapshot check rejects the GRUB config marker conservatively"

TEST_BOOT_MODE=systemd-boot run_snapshot check
(( snapshot_status != 0 )) || fail "snapshot check rejects stale Limine helpers on systemd-boot"
pass "snapshot check rejects systemd-boot markers conservatively"

TEST_ARCH=aarch64 TEST_APPLE_SILICON=1 TEST_BOOT_MODE=grub run_snapshot check
(( snapshot_status != 0 )) || fail "snapshot check rejects an Apple system without the Mac helper"
grep -qF 'no supported automatic restore backend' <<<"$snapshot_output" || fail "snapshot check ignores stale Limine helpers on Apple" "$snapshot_output"
pass "snapshot check only accepts the Mac restore backend on Apple Silicon"

TEST_ARCH=aarch64 TEST_APPLE_SILICON=1 TEST_BOOT_MODE=grub-only TEST_GRUB_ETC_CONFIG=1 TEST_MAC_RESTORE_PRESENT=1 run_snapshot check
(( snapshot_status == 0 )) || fail "snapshot check accepts the Mac helper on Apple Silicon" "$snapshot_output"
grep -qF 'omarchy-mac-snapshot-restore' <<<"$snapshot_output" || fail "snapshot check selects the Mac backend when both helpers exist" "$snapshot_output"
pass "snapshot check selects Mac restore when both helpers exist on Apple Silicon"

TEST_ARCH=aarch64 TEST_APPLE_SILICON=1 TEST_BOOT_MODE=limine TEST_MAC_RESTORE_PRESENT=1 run_snapshot check
(( snapshot_status != 0 )) || fail "snapshot check accepts the Mac helper without an active GRUB path"
grep -qF 'no supported automatic restore backend' <<<"$snapshot_output" || fail "snapshot check reports an Apple Limine path as unavailable" "$snapshot_output"
pass "snapshot check requires an unambiguous GRUB path for Mac restore"

TEST_ARCH=aarch64 TEST_APPLE_SILICON=1 TEST_BOOT_MODE=systemd-boot TEST_GRUB_ETC_CONFIG=1 TEST_MAC_RESTORE_PRESENT=1 run_snapshot check
(( snapshot_status != 0 )) || fail "snapshot check accepts the Mac helper with systemd-boot markers"
pass "snapshot check rejects systemd-boot for Mac restore"

TEST_ROOT_FSTYPE=ext4 run_snapshot create
(( snapshot_status != 0 )) || fail "snapshot create rejects a plain ext4 root"
grep -qF 'No snapshot can be created because / uses ext4' <<<"$snapshot_output" || fail "snapshot create gives an ext4-specific diagnostic" "$snapshot_output"
grep -qF 'https://github.com/Skeptomenos/omarchy-mac/blob/quattro-arm/manual/47-system-snapshots.md' <<<"$snapshot_output" || fail "snapshot create points to the durable fork recovery guide" "$snapshot_output"
! grep -qF 'Configure Snapper with:' <<<"$snapshot_output" || fail "snapshot create does not prescribe Snapper configuration on ext4" "$snapshot_output"
! grep -q '^snapper ' "$test_tmp/calls.log" || fail "snapshot create does not invoke Snapper on ext4" "$(cat "$test_tmp/calls.log")"
(( $(grep -cF '/ uses ext4' <<<"$snapshot_output") == 1 )) || fail "snapshot create prints one ext4 diagnostic" "$snapshot_output"
pass "snapshot create gives plain ext4 its own recovery advice"

TEST_SNAPPER_CONFIGURED=0 run_snapshot create
(( snapshot_status != 0 )) || fail "snapshot create fails when Btrfs has no root config"
grep -qF 'No Snapper root config found' <<<"$snapshot_output" || fail "snapshot create reports that no snapshot was created" "$snapshot_output"
grep -qF 'Configure Snapper with:' <<<"$snapshot_output" || fail "snapshot create retains actionable Btrfs configuration advice" "$snapshot_output"
! grep -q '^snapper -c .* create ' "$test_tmp/calls.log" || fail "snapshot create does not invent a config to snapshot"
pass "snapshot create fails loudly when Btrfs is unconfigured"

TEST_SNAPPER_ROOT_SUBVOLUME=/home run_snapshot create
(( snapshot_status != 0 )) || fail "snapshot create rejects a root config for /home"
grep -qF 'does not target /' <<<"$snapshot_output" || fail "snapshot create explains the wrong Snapper target" "$snapshot_output"
! grep -q '^snapper -c root create ' "$test_tmp/calls.log" || fail "snapshot create snapshots /home as root" "$(cat "$test_tmp/calls.log")"
pass "snapshot create requires the root config to target slash"

run_snapshot create
(( snapshot_status == 0 )) || fail "snapshot create succeeds on configured Btrfs" "$snapshot_output"
grep -qFx 'snapper -c root create -c number -d 4.0.0' "$test_tmp/calls.log" || fail "snapshot create snapshots each configured subvolume" "$(cat "$test_tmp/calls.log")"
grep -qFx 'snapper -c root cleanup number' "$test_tmp/calls.log" || fail "snapshot create prunes older snapshots"
grep -qF 'Snapshots can be selected during boot' <<<"$snapshot_output" || fail "snapshot create advertises boot selection with Limine" "$snapshot_output"
pass "snapshot create snapshots configured Btrfs and advertises Limine boot restore"

TEST_LIMINE_RESTORE_PRESENT=0 run_snapshot create
(( snapshot_status != 0 )) || fail "snapshot create reports partial failure without an automatic restore backend" "$snapshot_output"
grep -qF 'Snapshot created, but automatic restore is unavailable' <<<"$snapshot_output" || fail "snapshot create does not claim boot restore without a backend" "$snapshot_output"
! grep -qF 'selected during boot' <<<"$snapshot_output" || fail "snapshot create does not make a false boot-selection claim" "$snapshot_output"
pass "snapshot create signals that stored snapshots lack automatic restore"

TEST_SNAPPER_PRESENT=0 run_snapshot create
(( snapshot_status == 127 )) || fail "snapshot create exits 127 without Snapper" "got $snapshot_status"
pass "snapshot create keeps missing Snapper distinguishable"

TEST_LIMINE_RESTORE_PRESENT=0 run_snapshot restore
(( snapshot_status != 0 )) || fail "snapshot restore fails without a restore backend"
grep -qF 'No supported snapshot restore backend is active' <<<"$snapshot_output" || fail "snapshot restore explains why it cannot run" "$snapshot_output"
! grep -q '^sudo ' "$test_tmp/calls.log" || fail "snapshot restore never executes a missing helper" "$(cat "$test_tmp/calls.log")"
pass "snapshot restore fails clearly without a restore backend"

run_snapshot restore
(( snapshot_status == 0 )) || fail "snapshot restore runs Limine when available" "$snapshot_output"
grep -qFx 'sudo limine-snapper-restore' "$test_tmp/calls.log" || fail "snapshot restore selects Limine" "$(cat "$test_tmp/calls.log")"
pass "snapshot restore selects the Limine backend"

TEST_ARCH=aarch64 TEST_APPLE_SILICON=1 TEST_BOOT_MODE=grub-only TEST_GRUB_ETC_CONFIG=1 TEST_MAC_RESTORE_PRESENT=1 run_snapshot restore
(( snapshot_status == 0 )) || fail "snapshot restore runs the Mac backend when available" "$snapshot_output"
grep -qFx 'sudo omarchy-mac-snapshot-restore' "$test_tmp/calls.log" || fail "snapshot restore selects the Mac backend" "$(cat "$test_tmp/calls.log")"
! grep -qFx 'sudo limine-snapper-restore' "$test_tmp/calls.log" || fail "snapshot restore selects stale Limine on Apple" "$(cat "$test_tmp/calls.log")"
pass "snapshot restore selects the Mac backend"

TEST_BOOT_MODE=grub run_snapshot restore
(( snapshot_status != 0 )) || fail "snapshot restore rejects GRUB with stale Limine helpers"
grep -qF 'No supported snapshot restore backend is active' <<<"$snapshot_output" || fail "snapshot restore explains the ineligible backend" "$snapshot_output"
! grep -q '^sudo ' "$test_tmp/calls.log" || fail "snapshot restore invokes a helper on an ineligible platform" "$(cat "$test_tmp/calls.log")"
pass "snapshot restore rechecks backend eligibility before sudo"

TEST_SNAPPER_ROOT_SUBVOLUME=/home run_snapshot restore
(( snapshot_status != 0 )) || fail "snapshot restore rejects a root config for /home"
grep -qF 'does not target /' <<<"$snapshot_output" || fail "snapshot restore explains the wrong Snapper target" "$snapshot_output"
! grep -q '^sudo ' "$test_tmp/calls.log" || fail "snapshot restore invokes a helper for the wrong subvolume" "$(cat "$test_tmp/calls.log")"
pass "snapshot restore requires the root config to target slash"

# The quattro upgrade runs under set -e, so a failed snapshot has to be warned
# past there too or it aborts the whole upgrade at the snapshot step.
grep -qF 'omarchy-snapshot create || (($? == 127))' "$ROOT/bin/omarchy-upgrade-to-quattro" || fail "upgrade ignores only the missing-Snapper exit code"
grep -qF 'Continuing the upgrade without a snapshot' "$ROOT/bin/omarchy-upgrade-to-quattro" || fail "upgrade continues past a failed snapshot instead of aborting"
pass "upgrade to quattro survives a failed snapshot without passing it off"
