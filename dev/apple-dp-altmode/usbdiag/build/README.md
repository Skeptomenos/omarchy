# Private build workload source archive

These files preserve the exact workload sources used in the [module-build checkpoint](../../../../docs/evidence/dev-147-trace-and-module-builds-2026-08-28.md). They are not installation commands. Do not run them on a live machine or rerun them in an old output directory. They require the separately reviewed private sandbox, pinned read-only inputs, and fresh private output. The public archive does not include the tool manifest, packages, private headers, runtime libraries, or binaries.

| Source | Recorded result |
|---|---|
| `authenticate-pahole-attempt1.sh` | Historical FAIL. gpgv could not use the installed armored public-key representation. No extraction or execution followed. |
| `authenticate-pahole.sh` | PASS. Exact pinned public-key bytes were decoded; gpgv authenticated the package. |
| `extract-pahole.sh` | PASS. Repeated authentication, selected extraction, executable hash, and ELF inspection only. `/inputs/authenticate` was the successful authentication source. |
| `Makefile` | Two external modules, using the unchanged private kernel headers. |
| `build-controls-attempt1.sh` | Both controls compiled with BTF. The later metadata check FAILED because its stock input name lacked `.ko`. This exact historical source is deliberately not repaired or presented as a working all-in-one helper. |
| `verify-controls.sh` | PASS. Checked the existing control outputs against correctly named stock `.ko` copies, without rebuilding them. |
| `build-diagnostics.sh` | Both diagnostics compiled with BTF; basic metadata PASS. This source displays import deltas for review; it does not approve them. |

The later [module verifier](../kernel/verify_modules.py) checks exact diagnostic identities, import additions, exports, and metadata. The [logging verifier](../kernel/verify_logging.py) tests copied producer fragments with userspace shims. Their [QA record](../../../../docs/evidence/dev-147-offline-helper-qa-2026-08-28.md) states the limits. No check here proves loader acceptance, hardware behavior, or boot safety. No live staging or reboot command is provided.
