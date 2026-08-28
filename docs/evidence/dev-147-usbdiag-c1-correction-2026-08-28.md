# DEV-147 source-only diagnostic correction evidence — 2026-08-28

**Scope:** C1 source correction and focused userspace tests for the M2 J413 diagnostic guard.
**Approval:** Contained offline source/tests only. No kernel module, image, staging, or device action.
**Starting checkpoint:** Reviewed C0 plan at `41d55e286e32a0e0d83ee1870d6ff9a311ff26a4`.

## What happened

The [owned correction design](../plans/dev-147-usb-startup-diagnostic.md#correction-design--usbdiag2-living) was implemented in the two diagnostic producers. The [C0 design](dev-147-usbdiag-correction-design-2026-08-28.md), [failed D3 startup](dev-147-usbdiag-startup-failure-2026-08-28.md), and [working-image recovery](dev-147-dp-recovery-2026-08-28.md) remain separate, unchanged evidence.

Before any producer edit, two tests ran against frozen v1 source. Both correct FDT targets returned generation `0`, sequence `0`, and no first marker instead of generation `1`. Both child processes and compilation succeeded; reference checks balanced. These were two genuine assertion failures, not setup, source-pin, compilation, or revision-rejection errors. The old 59-test trace suite and 57-site logging checks had separately passed, which demonstrates their missing target-gate coverage.

The v2 source changes only each generation guard and its fixed revision token. Each guard keeps the existing J413 board check, rejects a null device node, looks up the exact absolute OF path, and requires a non-null result equal to the device node. It releases the lookup reference before rejection, counter increment, or logging. No hardware/error/retry path changes. Static review caught a missing early null-node rejection in the first draft; it was added before v2 tests or patch generation. The two valid-board null-node fixtures now require exactly one balanced board-root reference and no target lookup.

Both producers, source-test pins, strict trace validator, and new schema use `dev147-usbdiag2-v1`. Explicit old-v1 and mixed-component/late-record negatives remain. Historical `usbdiag1.patch`, `usbdiag1.schema.json`, `verify_modules.py`, and `build/build-diagnostics.sh` stay unchanged. The last two retain v1 pins and cannot prepare or validate v2. No new binary identity or import set is claimed.

## Source and patch pins

| Artifact | SHA-256 |
|---|---|
| [DWC3 source](../../dev/apple-dp-altmode/usbdiag/kernel/dwc3-apple.c) | `247f8bbe481699e288dc9476a6b1143484b3b9dbf9b1aaab5d7f9ea8241e4de1` |
| [ATC source](../../dev/apple-dp-altmode/usbdiag/kernel/atc.c) | `352bfd35397e76a487176404a715f2388595f070b97ad2c657cdf08f0e439ac4` |
| [Complete v2 diagnostic patch](../../dev/apple-dp-altmode/usbdiag/kernel/usbdiag2.patch) | `1bebc07def173e439d6ff2ceab3242f1578c498f1f9c200418408d6726100d88` |
| [V2 record schema](../../dev/apple-dp-altmode/usbdiag/trace/usbdiag2.schema.json) | `f642513d41f4c6dff4aeda09810316b0c4f32cfae7a6bfabdef4c4c54d30fe8a` |

The complete patch byte-matches pinned GNU `diff -u` output from both original Asahi source files to the frozen v2 files. Each diff exited `1` because it found the expected changes; that is not a failed test. The new schema differs from v1 only in title and revision literal.

## Executed checks and result

These are the exact workload arguments inside reviewed fresh private sandboxes, not standalone host instructions. Each outer run had a 295-second deadline. Read-only inputs and new writable output/temp directories were verified; no existing run was reused.

| Workload command | Observed result |
|---|---|
| `/usr/bin/python3.14 -I -S -B /inputs/target-tests/test_target_gates.py TargetGateTests.test_dwc3_correct_target_reaches_first_probe TargetGateTests.test_atc_correct_target_reaches_first_probe` | Frozen v1: exit `1`, exactly two generation-zero assertion failures. Both fixture children exit `0`; compile/setup PASS. |
| `/usr/bin/python3.14 -I -S -B /inputs/target-tests/test_target_gates.py` | V2: exit `0`; 10 methods PASS, 54 retained fixture executions. |
| `/usr/bin/python3.14 -I -S -B -m unittest discover -s /inputs/trace -p 'test_*.py'` | Exit `0`; 65 tests PASS, including strict old/mixed revision and both components' hash/build-ID rejection. |
| `/usr/bin/python3.14 -I -S -B /inputs/logging` | Exit `0`; 57 actual call sites, ten eight-thread cap rounds, maximum 277 bytes with newline. Each component's 128-record budget includes one final cap marker. |

Each GREEN workload ran once. Independent QA verified exact arguments and read-only input bindings, all 35 pinned inputs before/after, and every actual isolation probe. No timeout, retry, input drift, or setup failure occurred. All 54 fixture children exited `0`; references and locks balanced, rejected targets consumed no counters, and all emitted markers were v2. Compiler, fixture, and logging stderr was empty; target/trace stderr contained passing unittest output only.

The [target harness](../../dev/apple-dp-altmode/usbdiag/kernel/test_target_gates.py) extracts the real generation/reservation/first-probe code and pinned OF helpers. Real pinned libfdt builds and reads synthetic FDT nodes with leaf/unit names. Cases include wrong board/root/path/port, missing/null targets, foreign same-leaf pointers, case/near-match variants, retries, both-order interleaving of independent counters, caps, and source/extraction drift. Valid uppercase/later-list J413 compatibility retains the existing API semantics. Adapters bound metadata, reference/lock bookkeeping, atomics, and output; they do not simulate hardware.

Independent focused QA and full source/test review both returned PASS. The source review confirmed only guard/token driver deltas and preserved historical artifacts. The pinned OF fragments retain their original signed-length comparisons under a scoped warning pragma; adapters/producers keep strict compiler diagnostics. This is not kernel scheduling, kobject-concurrency, module-loading, boot-order, or hardware validation. The separate logging verifier still bypasses generation and tests format/caps only.

Publication whitespace review treats the new patch as a nested diff: its 222 reported flags are required context prefixes, not changed source whitespace. The exact GNU-diff bytes are retained. Non-patch files require their normal whitespace check; no global policy or attribute exception was added. Final documentation/publication QA remains a separate check.

## Rollback and retained state

C1 performed no live driver, boot-file, package, system-configuration, or device operation, so no hardware rollback was needed. Userspace executables and fixture outputs remain private. Working/failed images, v1 source and test snapshots, old helpers, backups, and recovery evidence remain retained. The permitted monitor disconnection was not confirmed or counted as a test.

## Open

C2 module/control-image preparation needs separate approval, fresh containment, and actual import/binary-identity checks. Staging and any one attended selection need later independent reviews and user actions, with an approved recovery handoff available beforehand. W/E/B/G are comparison definitions, not a boot schedule. C1 corrects instrumentation source only. D3 video causality, runtime USB order, full Gate 4b, firmware findings, reliability, and full rollback remain open.
