#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

git_migration="$ROOT/migrations/1784672586.sh"
stable_migration="$ROOT/migrations/1787399318.sh"
[[ -f $git_migration ]] || fail "legacy Quickshell git package migration exists"
[[ -f $stable_migration ]] || fail "stable Quickshell package migration exists"

mapfile -t pending_migrations < <(printf '%s\n' "$git_migration" "$stable_migration" | sort)

test_tmp=$(mktemp -d)
trap 'rm -rf "$test_tmp"' EXIT

stub_bin="$test_tmp/bin"
package_state="$test_tmp/packages"
calls="$test_tmp/calls"
mkdir -p "$stub_bin"

cat >"$stub_bin/omarchy-pkg-present" <<'SH'
#!/bin/bash

grep -qxF "$1" "$PACKAGE_STATE"
SH

cat >"$stub_bin/sudo" <<'SH'
#!/bin/bash

printf '%s\n' "$*" >>"$TEST_LOG"
case $* in
  "pacman -S --noconfirm --ask 4 quickshell")
    printf '%s\n' quickshell >"$PACKAGE_STATE"
    ;;
  "pacman -S --noconfirm --ask 4 quickshell-git")
    exit 1
    ;;
esac
SH

chmod +x "$stub_bin"/*

run_migration() {
  local migration="$1"

  PATH="$stub_bin:$PATH" \
    PACKAGE_STATE="$package_state" \
    TEST_LOG="$calls" \
    OMARCHY_PATH="$ROOT" \
    bash -euo pipefail "$migration" >/dev/null
}

run_pending_migrations() {
  local migration

  for migration in "${pending_migrations[@]}"; do
    if ! run_migration "$migration"; then
      return 1
    fi
  done
}

printf '%s\n' quickshell-git >"$package_state"
: >"$calls"
run_migration "$stable_migration"

grep -qxF 'pacman -S --noconfirm --ask 4 quickshell' "$calls" ||
  fail "migration replaces quickshell-git in one noninteractive transaction" "$(cat "$calls")"
(( $(wc -l <"$calls") == 1 )) ||
  fail "migration performs exactly one package transaction" "$(cat "$calls")"
pass "migration replaces quickshell-git in one noninteractive transaction"

run_migration "$stable_migration"
(( $(wc -l <"$calls") == 1 )) ||
  fail "migration does not repeat after the stable package is installed" "$(cat "$calls")"
pass "migration no-ops after replacing quickshell-git"

printf '%s\n' quickshell >"$package_state"
: >"$calls"
run_migration "$stable_migration"

[[ ! -s $calls ]] ||
  fail "migration leaves an already-migrated install unchanged" "$(cat "$calls")"
pass "migration leaves an already-migrated install unchanged"

# Both package migrations can still be pending on an existing install. Exercise
# them in the same filename order as omarchy-migrate.
printf '%s\n' quickshell-git >"$package_state"
: >"$calls"
run_pending_migrations ||
  fail "pending package migrations replace quickshell-git with stable Quickshell" "$(cat "$calls")"

[[ $(cat "$package_state") == "quickshell" ]] ||
  fail "pending package migrations leave stable Quickshell installed" "$(cat "$package_state")"
grep -qxF 'pacman -S --noconfirm --ask 4 quickshell' "$calls" ||
  fail "pending package migrations use the stable replacement transaction" "$(cat "$calls")"
(( $(wc -l <"$calls") == 1 )) ||
  fail "pending package migrations perform one package transaction" "$(cat "$calls")"
pass "pending package migrations replace quickshell-git with stable Quickshell"

printf '%s\n' quickshell >"$package_state"
: >"$calls"
run_pending_migrations ||
  fail "pending package migrations accept an already-stable install" "$(cat "$calls")"

[[ $(cat "$package_state") == "quickshell" ]] ||
  fail "pending package migrations keep stable Quickshell installed" "$(cat "$package_state")"
[[ ! -s $calls ]] ||
  fail "pending package migrations do not reinstall unavailable quickshell-git" "$(cat "$calls")"
pass "pending package migrations no-op on an already-stable install"
