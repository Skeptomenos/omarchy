#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

operational_consumers=(
  "$ROOT/bin/omarchy-upgrade-to-quattro-mac"
  "$ROOT/bin/omarchy-reinstall-pkgs"
  "$ROOT/bin/omarchy-reinstall"
)

missing_contract=()
for consumer in "${operational_consumers[@]}"; do
  grep -qF 'install/helpers/mise.sh' "$consumer" ||
    missing_contract+=("$(basename "$consumer"): shared helper")
  grep -qF 'omarchy_filter_mise_packages_for_arch' "$consumer" ||
    missing_contract+=("$(basename "$consumer"): ARM package filter")
  grep -qF 'omarchy_ensure_mise_for_arch' "$consumer" ||
    missing_contract+=("$(basename "$consumer"): verified bootstrap")
done

acceptance="$ROOT/test/acceptance.d/system-test.sh"
grep -qF 'install/helpers/mise.sh' "$acceptance" ||
  missing_contract+=("system-test.sh: shared helper")
grep -qF 'omarchy_is_arm_mise_package' "$acceptance" ||
  missing_contract+=("system-test.sh: ARM binary acceptance")

if (( ${#missing_contract[@]} )); then
  fail "every ARM base-package consumer uses the verified mise contract" "missing: ${missing_contract[*]}"
fi
pass "every ARM base-package consumer uses the verified mise contract"

tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT
fake_bin="$tmpdir/bin"
log="$tmpdir/actions.log"
mkdir -p "$fake_bin"

cat >"$fake_bin/fake-command" <<'SH'
#!/bin/bash

command_name=${0##*/}
case "$command_name" in
  uname)
    printf '%s\n' "$MISE_CONSUMER_TEST_ARCH"
    ;;
  mise)
    printf 'mise %s\n' "$*" >>"$MISE_CONSUMER_TEST_LOG"
    printf '%s\n' "mise test-version"
    ;;
  sudo|yay)
    printf '%s %s\n' "$command_name" "$*" >>"$MISE_CONSUMER_TEST_LOG"
    ;;
  tee)
    /bin/cat >/dev/null
    ;;
  *)
    printf '%s %s\n' "$command_name" "$*" >>"$MISE_CONSUMER_TEST_LOG"
    ;;
esac
SH
chmod +x "$fake_bin/fake-command"

for command_name in \
  bash cp gum mise omarchy-cmd-reboot omarchy-lazyvim-setup \
  omarchy-refresh-limine omarchy-refresh-pacman omarchy-refresh-plymouth \
  omarchy-reinstall-configs omarchy-reinstall-pkgs sudo tee uname yay; do
  ln -s fake-command "$fake_bin/$command_name"
done

assert_no_mise_package_action() {
  local description="$1"

  if grep -qE '^(sudo|yay) .*([[:space:]])mise(-bin)?([[:space:]]|$)' "$log"; then
    fail "$description" "$(<"$log")"
  fi
}

run_consumer() {
  local arch="$1"
  shift

  : >"$log"
  PATH="$fake_bin:/usr/bin:/bin" \
    HOME="$tmpdir/home" \
    MISE_CONSUMER_TEST_ARCH="$arch" \
    MISE_CONSUMER_TEST_LOG="$log" \
    OMARCHY_PATH="$ROOT" \
    /bin/bash "$@"
}

mkdir -p "$tmpdir/home"

run_consumer aarch64 "$ROOT/bin/omarchy-reinstall-pkgs"
assert_no_mise_package_action "the ARM package reinstaller excludes mise packages from pacman"
grep -qF 'sudo env OMARCHY_UPDATE_PACMAN=1 pacman -Syu' "$log" ||
  fail "the ARM package reinstaller still submits the default package set" "$(<"$log")"
grep -qE '^sudo .*([[:space:]])aether([[:space:]]|$)' "$log" ||
  fail "the ARM package reinstaller retains ordinary packages" "$(<"$log")"
grep -qF 'mise --version' "$log" ||
  fail "the ARM package reinstaller ensures a working mise" "$(<"$log")"
pass "the ARM package reinstaller uses the verified mise path"

run_consumer aarch64 "$ROOT/bin/omarchy-reinstall"
assert_no_mise_package_action "the full ARM reinstaller excludes mise packages from pacman"
grep -qF 'sudo pacman -Syu' "$log" ||
  fail "the full ARM reinstaller still submits the default package set" "$(<"$log")"
grep -qE '^sudo .*([[:space:]])aether([[:space:]]|$)' "$log" ||
  fail "the full ARM reinstaller retains ordinary packages" "$(<"$log")"
grep -qF 'mise --version' "$log" ||
  fail "the full ARM reinstaller ensures a working mise" "$(<"$log")"
pass "the full ARM reinstaller uses the verified mise path"

upgrade_functions=$(
  for function_name in load_unavailable_packages package_is_unavailable_here install_quattro_packages; do
    sed -n "/^${function_name}() {$/,/^}$/p" "$ROOT/bin/omarchy-upgrade-to-quattro-mac"
  done
)
: >"$log"
PATH="$fake_bin:/usr/bin:/bin" \
  MISE_CONSUMER_TEST_ARCH="aarch64" \
  MISE_CONSUMER_TEST_LOG="$log" \
  OMARCHY_CONSUMER_TEST_ROOT="$ROOT" \
  OMARCHY_CONSUMER_TEST_FUNCTIONS="$upgrade_functions" \
  /bin/bash -euo pipefail -c '
    checkout="$OMARCHY_CONSUMER_TEST_ROOT"
    log() { :; }
    warn() { :; }
    eval "$OMARCHY_CONSUMER_TEST_FUNCTIONS"
    install_quattro_packages
  '
assert_no_mise_package_action "the Apple Silicon upgrader excludes mise packages from yay"
grep -qF 'yay -S --needed --noconfirm aether' "$log" ||
  fail "the Apple Silicon upgrader still submits the default package set" "$(<"$log")"
grep -qF 'mise --version' "$log" ||
  fail "the Apple Silicon upgrader ensures a working mise" "$(<"$log")"
pass "the Apple Silicon upgrader uses the verified mise path"

run_consumer x86_64 "$ROOT/bin/omarchy-reinstall-pkgs"
grep -qE '^sudo .*([[:space:]])mise-bin([[:space:]]|$)' "$log" ||
  fail "the x86 package reinstaller retains mise-bin" "$(<"$log")"
if grep -qF 'mise --version' "$log"; then
  fail "the x86 package reinstaller does not use the ARM bootstrap" "$(<"$log")"
fi
pass "the x86 package reinstaller retains the Basecamp mise-bin path"
