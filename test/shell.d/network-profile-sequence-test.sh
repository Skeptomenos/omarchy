#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

qml_test_runner=$(command -v qmltestrunner6 || command -v qmltestrunner || true)
if [[ -z $qml_test_runner && -x /usr/lib/qt6/bin/qmltestrunner ]]; then
  qml_test_runner=/usr/lib/qt6/bin/qmltestrunner
fi
if [[ -z $qml_test_runner ]]; then
  pass "Qt Quick Test runner unavailable; skipping native network UUID sequence coverage (Node coverage remains in network-test.sh)"
  exit 0
fi

# A real Qt delegate converts nested arrays to sequences. Run offscreen so this
# boundary test never launches Quickshell or touches the active desktop.
QT_QPA_PLATFORM=offscreen QT_QUICK_BACKEND=software timeout -k 2s 30s "$qml_test_runner" \
  -input "$SHELL_TEST_DIR/fixtures/network-profile-sequence"

pass "network profile selection agrees across JavaScript rows and native QML delegates"
