#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

migration="$ROOT/migrations/1786952219.sh"
helper="$ROOT/install/helpers/mise.sh"

[[ -f $helper ]] || fail "the verified ARM mise bootstrap is shared with migrations"
grep -qF 'install/helpers/mise.sh' "$migration" ||
  fail "the mise package migration loads the shared ARM bootstrap"

tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

payload="$tmpdir/mise"
cat >"$payload" <<'SH'
#!/bin/bash

if [[ ${1:-} == "--version" ]]; then
  echo "mise test-version"
fi
SH
chmod +x "$payload"
payload_checksum=$(sha256sum "$payload" | awk '{print $1}')

make_fake_bin() {
  local scenario="$1"
  local fake_bin="$tmpdir/$scenario/bin"

  mkdir -p "$fake_bin"
  for command in awk mktemp rm sha256sum; do
    ln -s "$(command -v "$command")" "$fake_bin/$command"
  done

  cat >"$fake_bin/uname" <<'SH'
#!/bin/bash
printf '%s\n' "$MISE_TEST_ARCH"
SH

  cat >"$fake_bin/omarchy-pkg-missing" <<'SH'
#!/bin/bash
printf 'pkg-missing %s\n' "$*" >>"$MISE_TEST_LOG"
exit 0
SH

  cat >"$fake_bin/curl" <<'SH'
#!/bin/bash

printf 'curl %s\n' "$*" >>"$MISE_TEST_LOG"
output=""
while (( $# > 0 )); do
  if [[ $1 == "-o" ]]; then
    output="$2"
    shift 2
  else
    shift
  fi
done

/bin/cp "$MISE_TEST_PAYLOAD" "$output"
SH

  cat >"$fake_bin/sudo" <<'SH'
#!/bin/bash

printf 'sudo %s\n' "$*" >>"$MISE_TEST_LOG"
if [[ ${1:-} == "install" && ${*: -1} == "/usr/local/bin/mise" ]]; then
  source_path=${*: -2:1}
  /bin/cp "$source_path" "$MISE_TEST_BIN/mise"
  /bin/chmod 755 "$MISE_TEST_BIN/mise"
fi
SH

  chmod +x "$fake_bin/uname" "$fake_bin/omarchy-pkg-missing" "$fake_bin/curl" "$fake_bin/sudo"
  printf '%s\n' "$fake_bin"
}

run_migration() {
  local fake_bin="$1"
  local arch="$2"
  local checksum="$3"
  local log="$4"

  PATH="$fake_bin" \
    MISE_TEST_ARCH="$arch" \
    MISE_TEST_BIN="$fake_bin" \
    MISE_TEST_LOG="$log" \
    MISE_TEST_PAYLOAD="$payload" \
    OMARCHY_MISE_SHA256="$checksum" \
    OMARCHY_MISE_URL="https://example.test/mise-arm64" \
    OMARCHY_PATH="$ROOT" \
    /bin/bash -euo pipefail "$migration"
}

working_bin=$(make_fake_bin working)
working_log="$tmpdir/working.log"
/bin/cp "$payload" "$working_bin/mise"
/bin/chmod 755 "$working_bin/mise"
run_migration "$working_bin" aarch64 "$payload_checksum" "$working_log"
[[ ! -s $working_log ]] ||
  fail "an existing working ARM mise needs no package or download action" "$(<"$working_log")"
pass "the ARM migration accepts an existing working mise"

missing_bin=$(make_fake_bin missing)
missing_log="$tmpdir/missing.log"
run_migration "$missing_bin" aarch64 "$payload_checksum" "$missing_log"
grep -qF 'curl --fail --location --retry 3 --silent --show-error https://example.test/mise-arm64' "$missing_log" ||
  fail "a missing ARM mise uses the verified download bootstrap" "$(<"$missing_log")"
grep -qF 'sudo install -Dm0755' "$missing_log" ||
  fail "a missing ARM mise installs the verified binary" "$(<"$missing_log")"
if grep -qF 'mise-bin' "$missing_log"; then
  fail "the ARM migration never asks pacman for mise-bin" "$(<"$missing_log")"
fi
"$missing_bin/mise" --version >/dev/null || fail "the ARM migration installs a working mise"

first_action_count=$(wc -l <"$missing_log")
run_migration "$missing_bin" aarch64 "$payload_checksum" "$missing_log"
second_action_count=$(wc -l <"$missing_log")
(( second_action_count == first_action_count )) ||
  fail "the ARM mise bootstrap is idempotent" "$(<"$missing_log")"
pass "the ARM migration self-heals a missing mise idempotently"

bad_checksum_bin=$(make_fake_bin bad-checksum)
bad_checksum_log="$tmpdir/bad-checksum.log"
if run_migration "$bad_checksum_bin" aarch64 "wrong-checksum" "$bad_checksum_log" 2>/dev/null; then
  fail "the ARM mise bootstrap rejects a checksum mismatch"
fi
[[ ! -x $bad_checksum_bin/mise ]] || fail "a checksum mismatch never installs mise"
pass "the ARM migration retains checksum verification"

x86_bin=$(make_fake_bin x86)
x86_log="$tmpdir/x86.log"
run_migration "$x86_bin" x86_64 "$payload_checksum" "$x86_log"
grep -qF 'pkg-missing mise-bin' "$x86_log" ||
  fail "the non-ARM migration checks the Basecamp mise-bin package" "$(<"$x86_log")"
grep -qF 'sudo pacman -S --noconfirm --ask=4 mise-bin' "$x86_log" ||
  fail "the non-ARM migration retains Basecamp's package swap" "$(<"$x86_log")"
pass "the non-ARM migration retains the mise-bin package swap"
