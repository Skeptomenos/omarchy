#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

require_command node
node "$SHELL_TEST_DIR/fixtures/plugin-ui-contract.cjs" "$ROOT"
