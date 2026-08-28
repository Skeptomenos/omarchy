# DEV-147 diagnostic startup failure — 2026-08-28

**Scope:** One attended diagnostic restart on the M2 J413/T8112 machine, kernel `7.1.6-1-1-ARCH`.
**Approval:** The previously reviewed D3 handoff permitted one user-selected diagnostic boot. David reported using that selection and rebooting. This checkpoint records the result and read-only investigation, not permission for a correction or another diagnostic boot.
**Repo state:** Public branch `codex/dev-147-m2-dp-altmode-public` was at `6d0ad30ddf8916114177a065eeb25ec4eb26f6fc` before this documentation update. No driver or helper source changed.

## Result

D3 ended with external-display FAIL and measurement INCONCLUSIVE. David reported no external image, a normal built-in screen, and a responsive system. The intended modules were loaded, but the saved journal contained no diagnostic markers. A source-level target-name defect explains the missing trace. It does not establish the cause of the external-video failure.

The [readiness record](dev-147-usbdiag-boot-readiness-2026-08-28.md) remains historical evidence. Its diagnostic handoff was consumed. The agent requested no reconnect, second diagnostic boot, live swap, mode change, or suspend, and performed no device action. No such follow-up action was reported by David. External-image loss triggered the stop condition; the responsive machine's evidence was captured without deliberately extending the test for the planned 30-second observation.

## Fresh boot observations

| Check | Recorded result |
|---|---|
| Boot identity | A new boot was confirmed. All 963 retained journal envelopes identify that one boot. Raw identifiers stay private. |
| Internal display | `card2-eDP-1` connected/enabled; 2560×1664 at 60 Hz. David reported a normal physical image. |
| External display | `card2-DP-1` disconnected/disabled. David reported no physical image. |
| Power | Battery 100%, Full; AC and both MagSafe/monitor USB-PD sources online. This does not prove isolated USB-C active charging. |
| Taint | Fresh value 4100. The earlier boot's 4612 value was not carried forward. |
| Target binding | `502280000.usb` bound to `dwc3-apple`, with OF node `/soc/usb@502280000`. `503000000.phy` bound to `phy-apple-atc`, with OF node `/soc/phy@503000000`. Root compatibility includes `apple,j413` and `apple,t8112`. |
| Integrity | All 37 readable records from the retained 40-pin D2 transcript matched. Three root-private records retain David's successful D2 validator as provenance; they were not reread. |
| Images | Working and diagnostic staged images remained root-owned, mode 0600, single-link regular files of 19,184,103 and 19,647,739 bytes respectively. Metadata does not replace a fresh protected-byte read. |

The loaded GNU build IDs matched the intended artifacts:

| Loaded module | Verified build ID |
|---|---|
| `dwc3_apple` diagnostic | `4e3a8536657283ecc0ac9d5c49e19990a32150db` |
| `phy_apple_atc` diagnostic | `5e40dcc39aef0914b9fcba1a779b237f99a39f48` |
| `tps6598x_core` working DP core | `8fd9e3d39ee211f439471a812fb5eaa2622f7585` |

These post-boot identities do not replace missing first-probe records or establish operation order.

## Capture checks and limits

The private all-priority kernel capture contains 963 records from 30 retained pages, through the declared cutoff at 13:09:02 UTC. Original journal fields and cursors were preserved. All required envelope fields were present; monotonic order, the single-boot check, all 963 unique cursors, and the terminal matching record check passed. The full capture and its SHA-256 were verified against the retained capture metadata. The raw capture, digest, boot identifiers, cursors, and device records remain private.

Read-only `jq` inspection counted zero `dev147` markers. Priority counts were 20 at level 3, 24 at level 4, 103 at level 5, 805 at INFO/6, and 11 at DEBUG/7. This was not a warning-only capture. Valid envelopes and a declared collection boundary do not prove that printk produced every required event or that no records were lost before collection. With no diagnostic start markers or operation pairs, measurement completeness failed.

The collection history retains an unsupported journal option, a rejected boot-ID representation, and a final-page cursor check that initially stopped. The installed interface and accepted identifier representation were then used. Saved pages were recovered and checked against the last matching JSON record's own cursor, rather than a reported cursor beyond that record. No matching records were discarded. A pre-reboot in-memory pin cache was unavailable; the frozen D2 transcript supplied the integrity records instead.

The external DCP logged fourteen `dp-xbar` deferrals with return `-517`. It later acquired the mux, bound, and reported boot completion, followed by disconnected/no-valid-mode/no-modes state. No USB host-controller registration pattern was present in this capture. This is an absence in the retained journal, not proof of an unobserved hardware or callback sequence.

Review found no kernel BUG/panic or WARN-trace pattern, module-loader rejection, coprocessor crash, DART/IOMMU fault, or watchdog-lockup pattern. This is not a clean-log claim. The ordinary wireless-extension deprecation warning remains recorded. Four audit-suppression notices total 461 callbacks. They limit blanket completeness claims; they do not prove that the diagnostic markers were dropped by audit suppression.

## Confirmed logging defect

Both diagnostic guards compare `of_node_full_name()` with absolute OF paths. A mismatch returns generation zero. Their reserve functions immediately reject generation zero, and every diagnostic macro depends on that reservation. See [DWC3 lines 38–87](../../dev/apple-dp-altmode/usbdiag/kernel/dwc3-apple.c#L38) and [ATC lines 65–111](../../dev/apple-dp-altmode/usbdiag/kernel/atc.c#L65).

The exact pinned Asahi source at `e2e1930a9595bffafad92cec2b5504525efb9cd4` establishes the mismatch:

1. [`include/linux/of.h`, lines 261–264](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/include/linux/of.h#L261) returns the stored node name directly.
2. [`drivers/of/fdt.c`, lines 202 and 215–222](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/of/fdt.c#L202) copies the FDT node name into that field and stores its parent separately. It does not build an absolute path there.
3. [`scripts/dtc/libfdt/fdt_ro.c`, lines 303–333](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/scripts/dtc/libfdt/fdt_ro.c#L303) returns the leaf/unit name. It strips parent paths for old FDT formats too.

Thus these FDT-created target nodes yield `usb@502280000` and `phy@503000000`, not the compared `/soc/...` strings. The board and binding observations rule out those alternative missing-target explanations. The source defect can be established without another boot.

Read-only `sha256sum` checks matched each public source against both its frozen diagnostic input and the actual compiled-work source:

| Source | Matching SHA-256 |
|---|---|
| `dwc3-apple.c` | `2ce7c85eb7d5324d13629a1030436d8350cb426cd646cf43cd40c0dbd8c1c752` |
| `atc.c` | `852f5d8e19894473390fc74464496029e20ef440aef37618cf530264b49cb113` |

The pinned local build header has the same helper implementation. Its saved configuration enables OF, early FDT, and PRINTK. Both first-probe markers precede fallible setup. The record cap alone cannot explain zero records because earlier records and a cap marker would precede suppression. No live settings were changed to test these facts.

The historical trace/archive/assembly/staging suites and build/import/logging checks remain PASS within their recorded scope. Their source review and fixtures missed the real OF target-name semantics. The userspace logging checks covered format and cap behavior with shims, not a positive match through the kernel OF helper. Preserve that coverage gap without rewriting earlier evidence as a hardware pass or claiming that the offline checks had failed.

## Recovery and open work at this checkpoint

A separate recovery handoff passed review and remained pending for David. It selects the previously working `initramfs-linux-asahi-dpalt.img`, without `usbdiag1`, once in the visible GRUB editor. Cables, monitor input, kernel arguments, and the saved boot default stay unchanged. Success is not guaranteed. This does not restore the original DTB. The [main plan's current recovery handoff](../plans/dev-147-m2-displayport.md#current-recovery-handoff--previous-working-dp-image-living) owns the exact steps and stop conditions; the old stock-driver unplug/reboot fallback is not the current instruction.

After the physical recovery report and read-only loaded-ID validation, a possible next investigation is an offline guard correction with a real OF-name-semantic regression fixture. Review the image's earlier DWC3 availability separately as a timing variable. Neither is an approved implementation or new boot here. The cause of the external-video failure and the intended USB call order remain unknown.

Keep the failed diagnostic image, working image, old helpers, frozen evidence, both backups, and offline Mac recovery bundle unchanged. No cleanup, source correction, build, new diagnostic boot, hotplug, live swap, or suspend is authorized by this checkpoint. Full Gate 4b remains HOLD; Gate 5, full rollback proof, and permanent integration remain open.
