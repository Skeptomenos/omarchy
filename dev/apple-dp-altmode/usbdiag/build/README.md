# Private build workload source archive

These files preserve reviewed private build workloads. They are not installation commands. Do not run them on a live machine or rerun them in an old output directory. They require the separately reviewed private sandbox, pinned read-only inputs, and fresh private output. The public archive does not include the tool manifest, packages, private headers, runtime libraries, or binaries.

Reconciled: 2026-08-28. The [C2 evidence](../../../../docs/evidence/dev-147-c2-offline-preparation-2026-08-28.md) owns the fresh module identities, exact imports, retained REDs, and independent QA. The [diagnostic plan](../../../../docs/plans/dev-147-usb-startup-diagnostic.md#c2-result--offline-artifacts-living) owns the next manual boundary. No module here was loaded in C2.

## Historical v1 checkpoint

The [original module-build record](../../../../docs/evidence/dev-147-trace-and-module-builds-2026-08-28.md) owns the following results. These sources remain unchanged.

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

## Distinct C2 workloads

| Source | Scope |
|---|---|
| [build-controls-c2.sh](build-controls-c2.sh) | Fresh unmodified controls. Uses the proper packaged `.ko` pathname and fixed source/recipe/package pins. Complete metadata/import checks pass. |
| [test_control_metadata_red.py](test_control_metadata_red.py) | Frozen expected RED against the exact old metadata block. Real proper-`.ko` prechecks pass before both extensionless-name failures. |
| [test_control_metadata_green.py](test_control_metadata_green.py) | Same focused contract against the fixed C2 builder; 3 methods pass. |
| [build-diagnostics-v2.sh](build-diagnostics-v2.sh) | Final bound builder for unchanged C1 v2 sources. Exact fresh control hashes were fixed after independent QA, before this build. No identity learning or v1 verifier reuse. |

All four new files match their frozen reviewed private bytes. Build success alone does not approve imports or identities; the separate [strict v2 verifier](../kernel/verify_modules_v2.py), actual binary review, and [C2 record](../../../../docs/evidence/dev-147-c2-offline-preparation-2026-08-28.md) supply those checks. Rebuilt controls are not the packaged binaries. E uses packaged DWC3 and unchanged packaged ATC, not either new pair. B/G images remain unprepared. Preserve the old helpers and every failed result.
