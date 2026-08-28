# DEV-147 USB startup diagnostic source archive

This directory preserves the offline diagnostic work for one M2 J413 USB-C startup investigation.

Reconciled: 2026-08-28, after C1 source correction and focused GREEN tests. The [owned C1 result](../../../docs/plans/dev-147-usb-startup-diagnostic.md#c1-result--source-only-correction-living) and [dated C1 evidence](../../../docs/evidence/dev-147-usbdiag-c1-correction-2026-08-28.md) distinguish corrected v2 source from the retained, unfixed v1 artifacts. Independent focused QA and source/test review pass. The [C0 design](../../../docs/evidence/dev-147-usbdiag-correction-design-2026-08-28.md), [recovery](../../../docs/evidence/dev-147-dp-recovery-2026-08-28.md), and [D3 failure](../../../docs/evidence/dev-147-usbdiag-startup-failure-2026-08-28.md) remain separate records. No new module, image, or hardware result was produced; USB acceptance stays HOLD.

> Public archival copy. Do not run these helpers on a live machine. The public sandbox has deliberately invalid `LOCAL_ONLY_*` paths and no host tool manifest. The public parent build/staging helpers also have invalid machine-identity placeholders. The operational, machine-pinned originals remain private. Edited public helpers are not byte-identical to the previously tested originals. R4's isolation proof applies to its private pinned launcher and inputs, not this public copy.

The [diagnostic plan](../../../docs/plans/dev-147-usb-startup-diagnostic.md) owns current work and authority. The [main plan](../../../docs/plans/dev-147-m2-displayport.md) owns display acceptance and rollback. The [public-source checkpoint](../../../docs/evidence/dev-147-public-source-checkpoint-2026-08-28.md) records the export boundary and initial isolated RED runs. Historical evidence links to raw files are labeled “retained privately”; those files are not missing publication deliverables.

## Contents and state

| Directory | Contents | State at this checkpoint |
|---|---|---|
| [kernel](kernel/) | Current v2 drivers/patch, source-gate and logging tests; retained v1 patch and binary verifier | C1: 10 target tests / 54 synthetic-FDT fixture executions and format/cap checks PASS. No v2 module built. D3's v1 image remains external-display FAIL / trace INCONCLUSIVE. |
| [trace](trace/) | Strict v2 schema/validator and fixtures; retained v1 schema | 65 isolated tests PASS, including explicit v1/mixed-revision and identity rejection. Software-order contracts, not hardware evidence. |
| [image](image/README.md) | Bounded newc helper, filesystem guards, fixtures, real control, private assembly | 58 archive and 55 assembly tests PASS. Exact no-change controls and the 200-module diagnostic image pass offline QA. The later D3 startup failed; preserve the image unchanged. |
| [staging](staging/README.md) | Fixed-source staging helper and real-file failure fixtures | 38 isolated tests, independent safety review, and user-run D2 staging PASS. Public constants are invalid. Staging is complete; do not repeat it. |
| [build](build/README.md) | Historical v1 authentication, extraction, build, and control-QA workload sources | Deliberately unchanged; not suitable for v2 preparation. C2 requires separate approval and exact new binary/import validation. |
| [sandbox](sandbox/) | R4 launcher, isolation probe, stdlib smoke tests, launcher test, proof input | PUBLIC REFERENCE ONLY. Invalid fixed paths; private runtime manifest deliberately omitted. |

Both initial RED runs used frozen private stubs in a fresh, reviewed sandbox. Inputs remained unchanged and neither run timed out. The [trace/build checkpoint](../../../docs/evidence/dev-147-trace-and-module-builds-2026-08-28.md) records trace GREEN, review failures and correction, authentication, and private builds. The [helper-QA record](../../../docs/evidence/dev-147-offline-helper-qa-2026-08-28.md) records import/logging checks, the retained link failure, initial 48 archive tests, and saved-gzip validation. The later [real-control record](../../../docs/evidence/dev-147-real-archive-controls-2026-08-28.md) records actual format and scratch-output failures, narrow corrections, 58 tests, and exact archive/index controls. The [image record](../../../docs/evidence/dev-147-private-diagnostic-image-2026-08-28.md) preserves the assembly sequencing miss, real index failures, independent investigation, correction tests, and the successful 413-command private assembly. Earlier failed workload sources and raw results remain private.

The [D2 preparation record](../../../docs/evidence/dev-147-usbdiag-staging-helper-2026-08-28.md) preserves the genuine RED runs, environment-loop failure, EXIT-trap defect, corrections, and final independent 38-test PASS. The private staging helper differs only in three fixed assignments. The subsequent [D2 staging record](../../../docs/evidence/dev-147-usbdiag-staging-2026-08-28.md) records David's successful private invocation and independent metadata checks. Root-private bytes/logs were not independently reread.

No public install or quick-start command is provided. Tests and builds need a separately reviewed private continuation with pinned read-only inputs and fresh writable output/temp directories. Do not weaken a guard, create an unrestricted fallback, or rerun a frozen checkpoint's launcher. D2 staging is complete. The [D3 readiness handoff](../../../docs/evidence/dev-147-usbdiag-boot-readiness-2026-08-28.md) and [working-DP recovery handoff](../../../docs/plans/dev-147-m2-displayport.md#current-recovery-handoff--previous-working-dp-image-living) are consumed; do not repeat them. The [next approval](../../../docs/plans/dev-147-m2-displayport.md#next-step--offline-correction-design-only-living) is separate C2 module/control-image preparation after completed C1 source/test QA. Staging and any single attended case need later review and user action. The W/E/B/G comparison design is not a boot schedule. No module/image build, reboot, diagnostic reconnect, USB-device test, live swap, mode change, or suspend is authorized by C1. Permitted monitor disconnection during offline work is not a confirmed action or test.

## Provenance and design limits

The two kernel drafts derive from Asahi Linux commit [`e2e1930a9595bffafad92cec2b5504525efb9cd4`](https://github.com/AsahiLinux/linux/tree/e2e1930a9595bffafad92cec2b5504525efb9cd4), tag `asahi-7.1.6-1`, for kernel `7.1.6-1-1-ARCH`:

- [`drivers/usb/dwc3/dwc3-apple.c`](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/usb/dwc3/dwc3-apple.c): original SHA-256 `6d2ff775e11b62d1f343b07fbcfdf4a73b4159ac38ff2c2e1ee7c6df1b4a4420`.
- [`drivers/phy/apple/atc.c`](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/phy/apple/atc.c): original SHA-256 `75b9b68c3096a151d31828650887cf7a7caa88c7f0dd5655f4c4727959953939`.

SPDX notices and upstream author attribution are retained. Both patches target those original kernel paths. Kernel indentation is preserved; it is not reformatted as Omarchy shell code.

The archived v1 records use revision `dev147-usbdiag1-v1`, board `j413`, and target `front_lower`. The intended targets are `/soc/usb@502280000` and `/soc/phy@503000000`. Its guard compares these absolute paths with the leaf value from `of_node_full_name()`; this returns generation zero and suppresses every marker. The [D3 evidence](../../../docs/evidence/dev-147-usbdiag-startup-failure-2026-08-28.md#confirmed-logging-defect) proves the mismatch from exact pinned OF sources. It explains missing instrumentation, not the external-video failure.

Current drivers and [usbdiag2.patch](kernel/usbdiag2.patch) use `dev147-usbdiag2-v1`. The exact referenced-node guard is implemented and passes the production-gate-to-first-marker userspace tests. It adds the disclosed OF metadata-lock/refcount timing cost, not a hardware operation or driver-control change. The 128-record component cap and 384-byte bound are unchanged. The [C1 evidence](../../../docs/evidence/dev-147-usbdiag-c1-correction-2026-08-28.md) owns source/patch pins and the limits of this GREEN result.

[usbdiag1.patch](kernel/usbdiag1.patch), [usbdiag1.schema.json](trace/usbdiag1.schema.json), [verify_modules.py](kernel/verify_modules.py), and [build-diagnostics.sh](build/build-diagnostics.sh) remain historical v1 artifacts. The latter two do not prepare or validate v2. Current source tests and [usbdiag2.schema.json](trace/usbdiag2.schema.json) are v2-only; new module identities/imports must be established during separately approved C2. No broad revision or binary-pin fallback is provided.

Software order cannot prove PHY latching or hardware causation. A complete-looking sequence prefix cannot prove that no late setter occurred. Adding the missing DWC3 glue to an early image can itself change probe timing. The schema and synthetic fixtures are contracts, not hardware simulations or evidence of a fix. Synthetic boot IDs and repeated hash strings in fixtures are intentionally retained.

Python uses typed standard-library models and unittest under the no-install exception. Pydantic, pytest, Ruff, and strict type-check tooling are not installed or claimed as passing. Native kernel INFO/JSON logging is the documented exception to application-logger rules. No new package or framework is required by this archive.

## What stays private

The original 14-commit branch, raw Linear exports, device/journal records, host path/inode manifests, source-input provenance manifests, downloaded packages, module binaries, initramfs images, EFI files, and recovery backups stay on the machine. The original D1 and R4 checkpoints remain sealed. This public source branch does not replace either recovery copy or create a permanent installation.
