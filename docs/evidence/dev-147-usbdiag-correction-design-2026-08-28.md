# DEV-147 diagnostic correction-design evidence — 2026-08-28

**Scope:** Offline plan and read-only source review after the failed D3 startup and separately successful working-image recovery.
**Approval:** Correction-plan work only. No source correction, executed test, module/image build, staging, or device action.
**Repo state:** Plan work begins at recovery checkpoint `3c6ea54e4394313916cf178b85f678f2036ee8e5`.

## What happened

The existing [diagnostic subplan](../plans/dev-147-usb-startup-diagnostic.md#correction-design--usbdiag2-living) now owns the correction design. The main plan and archive README point there. Earlier [D3 failure](dev-147-usbdiag-startup-failure-2026-08-28.md) and [recovery](dev-147-dp-recovery-2026-08-28.md) evidence remains unchanged; this checkpoint adds no hardware observation.

The proposed guard preserves the J413 check and compares the device's OF node with a non-null, referenced lookup of its exact absolute path. Every lookup reference must be released. The plan excludes fallback or raw parent traversal and discloses the existing OF locking/refcount cost. It does not claim zero timing impact or authorize a hardware behavior fix.

## Read-only findings and review

The archived [logging verifier](../../dev/apple-dp-altmode/usbdiag/kernel/verify_logging.py) omits `*_new_generation()` from extracted fragments and calls both LOG macros with literal generation `1U` in its concurrent workload. It therefore bypasses the defective target gate. Historical formatting and cap checks remain valid only within that scope. New regression evidence must exercise the real production generation-to-first-marker path against pinned OF naming/path semantics.

The design requires a fixed new token, `dev147-usbdiag2-v1`, with strict producer/validator/fixture identities and preserved v1 negatives. Its W/E/B/G artifact definitions separate early availability, rebuild/toolchain, and instrumentation bundles. Exact no-change archive reconstruction remains a separate byte-level control, not boot-order proof. Failed D3 is not a logging-disabled control. E is only the preferred first later single attended proposal, not an approved or scheduled boot.

Read-only source/configuration/export inspection establishes:

- The pinned [OF path wrapper](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/include/linux/of.h#L280) calls the exported lookup. [Exact component matching](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/of/base.c#L921) preserves unit addresses, while [lookup](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/of/base.c#L975) uses the OF tree lock and returns a reference. [Release](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/of/dynamic.c#L34) must balance it even for a mismatching device.
- The retained build configuration enables dynamic OF and overlays; OF kernel unit tests are disabled. The pinned export table contains `of_find_node_opts_by_path` and `of_node_put`. Later binary imports still require exact validation; no module was built here.
- Pinned [libfdt](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/scripts/dtc/libfdt/fdt_ro.c#L303) provides real leaf/unit-name semantics. The existing board API is case-insensitive. Saved DTS distinguishes the front targets from the rear pair. Correct-target RED must specifically expose generation zero in both frozen v1 guards, not a setup or revision mismatch.
- The working [TIPD patch](../../dev/apple-dp-altmode/tipd-cd321x-hpd.patch) places USB-role handling before conditional DP-connected notification. The two retained patched-core copies match. Earlier glue availability is therefore a source-supported timing risk, not a measured D3 cause.

`sed`/`rg` source inspection and `sha256sum --check` confirm the nine public producer/patch/verifier/fixture pins remain unchanged. The retained 51-file recovery seal also verifies. Independent target/test-semantics and image/comparison-safety design reviews agree with the preferred design and report no blocker. This is design-review agreement, not an executed-test, build, or fresh hardware PASS. Final documentation QA is a separate publication check.

The first final-review draft was held for two C4 ambiguities; the correction separates uninstrumented E/B criteria from G trace criteria and requires approved, available recovery instructions before image selection.

## Rollback and retained state

No device or boot-state change occurred in this plan work, so no new hardware rollback was needed. Working and failed images, old helpers, private evidence, backups, and both consumed GRUB handoffs remain retained. The candidate DTB remains part of the previously validated setup; full rollback and Mac restore execution remain unproved.

## Open

C0 is plan-only. The next approval is C1: fresh contained source correction and focused userspace tests, without `.ko` or initramfs builds. Module/control-image preparation, staging, and any single attended case each require later review and user action. The existing full Gate 4b, firmware, reliability, rollback, release, and upstream gates remain open. Missing D3 trace and unknown external-video causality are not resolved by this design.
