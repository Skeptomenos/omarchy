# DEV-147 USB startup diagnostic source archive

This directory preserves the offline diagnostic work for one M2 J413 USB-C startup investigation.

Reconciled: 2026-08-28, after independent correction-design review. The [owned design](../../../docs/plans/dev-147-usb-startup-diagnostic.md#correction-design--usbdiag2-living) and [dated design evidence](../../../docs/evidence/dev-147-usbdiag-correction-design-2026-08-28.md) add no code, tests, builds, or hardware result. The [recovery record](../../../docs/evidence/dev-147-dp-recovery-2026-08-28.md) and [D3 failure record](../../../docs/evidence/dev-147-usbdiag-startup-failure-2026-08-28.md) remain separate. This archive still contains the unfixed v1 guard; recovery did not validate it or close USB acceptance.

> Public archival copy. Do not run these helpers on a live machine. The public sandbox has deliberately invalid `LOCAL_ONLY_*` paths and no host tool manifest. The public parent build/staging helpers also have invalid machine-identity placeholders. The operational, machine-pinned originals remain private. Edited public helpers are not byte-identical to the previously tested originals. R4's isolation proof applies to its private pinned launcher and inputs, not this public copy.

The [diagnostic plan](../../../docs/plans/dev-147-usb-startup-diagnostic.md) owns current work and authority. The [main plan](../../../docs/plans/dev-147-m2-displayport.md) owns display acceptance and rollback. The [public-source checkpoint](../../../docs/evidence/dev-147-public-source-checkpoint-2026-08-28.md) records the export boundary and initial isolated RED runs. Historical evidence links to raw files are labeled “retained privately”; those files are not missing publication deliverables.

## Contents and state

| Directory | Contents | State at this checkpoint |
|---|---|---|
| [kernel](kernel/) | Instrumented drivers, matching patch, import and logging verifiers | Historical build/import/logging checks PASS. D3 loaded IDs match, but an OF target-name guard defect suppresses every marker. External-display FAIL; no valid call-order measurement. |
| [trace](trace/) | Event schema, typed validator, synthetic and independent review fixtures | Implemented; 59 isolated tests PASS after correction of three review failures. Software-order evidence only. |
| [image](image/README.md) | Bounded newc helper, filesystem guards, fixtures, real control, private assembly | 58 archive and 55 assembly tests PASS. Exact no-change controls and the 200-module diagnostic image pass offline QA. The later D3 startup failed; preserve the image unchanged. |
| [staging](staging/README.md) | Fixed-source staging helper and real-file failure fixtures | 38 isolated tests, independent safety review, and user-run D2 staging PASS. Public constants are invalid. Staging is complete; do not repeat it. |
| [build](build/README.md) | Exact authentication, extraction, build, and control-QA workload sources | Historical failures and successful private runs are labeled separately. Not a live installer or quick-start. |
| [sandbox](sandbox/) | R4 launcher, isolation probe, stdlib smoke tests, launcher test, proof input | PUBLIC REFERENCE ONLY. Invalid fixed paths; private runtime manifest deliberately omitted. |

Both initial RED runs used frozen private stubs in a fresh, reviewed sandbox. Inputs remained unchanged and neither run timed out. The [trace/build checkpoint](../../../docs/evidence/dev-147-trace-and-module-builds-2026-08-28.md) records trace GREEN, review failures and correction, authentication, and private builds. The [helper-QA record](../../../docs/evidence/dev-147-offline-helper-qa-2026-08-28.md) records import/logging checks, the retained link failure, initial 48 archive tests, and saved-gzip validation. The later [real-control record](../../../docs/evidence/dev-147-real-archive-controls-2026-08-28.md) records actual format and scratch-output failures, narrow corrections, 58 tests, and exact archive/index controls. The [image record](../../../docs/evidence/dev-147-private-diagnostic-image-2026-08-28.md) preserves the assembly sequencing miss, real index failures, independent investigation, correction tests, and the successful 413-command private assembly. Earlier failed workload sources and raw results remain private.

The [D2 preparation record](../../../docs/evidence/dev-147-usbdiag-staging-helper-2026-08-28.md) preserves the genuine RED runs, environment-loop failure, EXIT-trap defect, corrections, and final independent 38-test PASS. The private staging helper differs only in three fixed assignments. The subsequent [D2 staging record](../../../docs/evidence/dev-147-usbdiag-staging-2026-08-28.md) records David's successful private invocation and independent metadata checks. Root-private bytes/logs were not independently reread.

No public install or quick-start command is provided. Tests and builds need a separately reviewed private continuation with pinned read-only inputs and fresh writable output/temp directories. Do not weaken a guard, create an unrestricted fallback, or rerun a frozen checkpoint's launcher. D2 staging is complete. The [D3 readiness handoff](../../../docs/evidence/dev-147-usbdiag-boot-readiness-2026-08-28.md) and [working-DP recovery handoff](../../../docs/plans/dev-147-m2-displayport.md#current-recovery-handoff--previous-working-dp-image-living) are consumed; do not repeat them. The [next approval](../../../docs/plans/dev-147-m2-displayport.md#next-step--offline-correction-design-only-living) is C1 contained source correction and focused userspace tests only, after C0 design review. Kernel module/image preparation, staging, and any single attended case each need later review and user action. The W/E/B/G comparison design is not a boot schedule. No implementation, test run, rebuild, reboot, hotplug, USB-device test, live swap, mode change, or suspend is authorized by C0.

## Provenance and design limits

The two kernel drafts derive from Asahi Linux commit [`e2e1930a9595bffafad92cec2b5504525efb9cd4`](https://github.com/AsahiLinux/linux/tree/e2e1930a9595bffafad92cec2b5504525efb9cd4), tag `asahi-7.1.6-1`, for kernel `7.1.6-1-1-ARCH`:

- [`drivers/usb/dwc3/dwc3-apple.c`](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/usb/dwc3/dwc3-apple.c): original SHA-256 `6d2ff775e11b62d1f343b07fbcfdf4a73b4159ac38ff2c2e1ee7c6df1b4a4420`.
- [`drivers/phy/apple/atc.c`](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/phy/apple/atc.c): original SHA-256 `75b9b68c3096a151d31828650887cf7a7caa88c7f0dd5655f4c4727959953939`.

SPDX notices and upstream author attribution are retained. The draft patch targets those original kernel paths. Kernel indentation is preserved; it is not reformatted as Omarchy shell code.

The v1 records use revision `dev147-usbdiag1-v1`, board `j413`, and target `front_lower`. The intended targets are `/soc/usb@502280000` and `/soc/phy@503000000`. The implementation instead compares these absolute paths with the leaf value from `of_node_full_name()`; this returns generation zero and suppresses every marker. The [D3 evidence](../../../docs/evidence/dev-147-usbdiag-startup-failure-2026-08-28.md#confirmed-logging-defect) proves the mismatch from exact pinned OF sources. It explains missing instrumentation, not the external-video failure.

The intended fixed INFO/JSON records observe operation order without changing hardware calls, error handling, lock order, retries, or timing policy. The per-component limit is 128 records including a final cap marker, with a 384-byte bound. Historical compilation and userspace fragment/cap checks remain PASS. They use C11/stdio shims, not kernel atomic/printk execution, and missed the OF target-name semantics. The source remains unchanged at this plan checkpoint. The proposed `dev147-usbdiag2-v1` correction adds an exact referenced-node guard and a disclosed OF metadata-lock/refcount timing cost; it is not implemented. Its production-path test seam and strict revision checks are defined only in the [correction design](../../../docs/plans/dev-147-usb-startup-diagnostic.md#correction-design--usbdiag2-living).

Software order cannot prove PHY latching or hardware causation. A complete-looking sequence prefix cannot prove that no late setter occurred. Adding the missing DWC3 glue to an early image can itself change probe timing. The schema and synthetic fixtures are contracts, not hardware simulations or evidence of a fix. Synthetic boot IDs and repeated hash strings in fixtures are intentionally retained.

Python uses typed standard-library models and unittest under the no-install exception. Pydantic, pytest, Ruff, and strict type-check tooling are not installed or claimed as passing. Native kernel INFO/JSON logging is the documented exception to application-logger rules. No new package or framework is required by this archive.

## What stays private

The original 14-commit branch, raw Linear exports, device/journal records, host path/inode manifests, source-input provenance manifests, downloaded packages, module binaries, initramfs images, EFI files, and recovery backups stay on the machine. The original D1 and R4 checkpoints remain sealed. This public source branch does not replace either recovery copy or create a permanent installation.
