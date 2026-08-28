# DEV-147 USB startup investigation — 2026-08-28

> Public archival copy, prepared 2026-08-28. Actual boot IDs are redacted where present. Local evidence links are marked as private. Commit references identify the retained private branch unless they name upstream source. Recorded hashes and past QA results describe the private originals, not this edited export. Commands below are historical records, not instructions to run the public helpers.

**Scope:** `omarchy-air`, M2 J413/T8112, kernel `7.1.6-1-1-ARCH`, monitor controller `0-003f` / USB controller `502280000.usb`.
**Approval:** David said “ok, proceed” to saved-log comparison, source investigation, and recording findings. No new hardware test or kernel change.
**Repo state:** `codex/dev-147-m2-dp-altmode`, base commit `e84769aaee29fe6809c5ebcd4ef18a8eec0af91f`.

This dated investigation owns the findings below. The [living plan](../plans/dev-147-m2-displayport.md) owns decisions and future gates. Earlier startup and reconnect evidence remains unchanged.

## Conclusion

There is a confirmed source-level first-probe ordering defect in the stock Apple USB glue driver. Its early USB2 HOST-mode request uses a PHY handle that has not yet been acquired. The generic PHY API silently accepts a null handle without configuring hardware. The installed glue binary corroborates that order. This particular boot was not instrumented, so the null argument is a source-level conclusion, not a captured runtime event.

This is the strongest lead for the monitor hub appearing after reconnect but not at attached startup. It is not a proven hardware cause or a tested fix. A later generic HCD path supplies a HOST setter, after DWC3 core initialization. Do not conclude that HOST mode is never set at startup.

The display HPD patch does not change this stock USB-glue path. The saved FIFO event also does not justify the separate `appledrm` poweroff workaround. Firmware impact and automatic USB startup remain unresolved.

## Saved-log comparison

The [startup record](../evidence/dev-147-one-boot-startup-2026-08-27.md) contains 1,085 unique kernel entries. The [USB-1 record](../evidence/dev-147-usb-reconnect-2026-08-27.md) contains 159. Their 13-file and four-file manifests were rechecked successfully. The compact USB-1 log retains the boot identity in each journal cursor even though it omits `_BOOT_ID`.

Both paths register `xhci-hcd.3.auto` at MMIO `0x502280000` and expose both root hubs. Their controller properties and LPM-disabling message match. The missing event is downstream monitor attachment, not controller registration.

| Event, seconds since the same candidate boot | Startup | USB-1 reconnect |
|---|---:|---:|
| xHCI registration | 4.798123 | 2634.747027 |
| DPTX connect | 4.812009 | 2634.757899 |
| Monitor hub `0bda:5411` | Absent from startup capture | 2635.422120 |
| LG controls `043e:9a39` | Absent from startup capture | 2635.810033 |
| Native modeset finished | 7.258486 | 2637.228022 |

After reconnect, the hub appears 0.675093 seconds after controller registration; LG controls follow at 1.063006 seconds. `usbhid` loads after the LG device appears. Its earlier absence does not explain why the USB hub itself was absent.

The retained, filtered stock-driver comparison also starts with root hubs only. Its controller is removed at 30.000033 seconds and registered again at 44.977145. The monitor hub appears at 45.628190 and LG controls at 46.009141. That recovery's physical trigger is unknown. This is corroboration, not a controlled stock/candidate A/B test.

## Source and binary findings

Source snapshots are pinned to Asahi tag `asahi-7.1.6-1`: tag object `57ec09a998a70c45b197d85266c1a7ff9608ee3d`, commit `e2e1930a9595bffafad92cec2b5504525efb9cd4`. The original stock TIPD source pin matches. Thirteen snapshots, source URLs, binary disassembly, selected live observations, and a normalized comparison are in the private investigation archive (retained privately). This is not a reproducible-build equivalence claim for every source file.

At 00:09:03 CEST, the boot ID remained `REDACTED_CANDIDATE_BOOT`. Installed and loaded `dwc3-apple` build IDs both were `0bb1b6c1d98eba0efc8abe4085670e3ab619b4ab`. Installed module SHA-256 was `d150400f9782c876972b2745d95617cd44e23574452f63980704911a467f7767`.

| Step | First probe | Later reconnect |
|---|---|---|
| Glue object / PHY handle | Zeroed object; USB2 handle not acquired yet | Previously acquired handle retained |
| Early USB2 HOST request | Null handle makes the API return success without a setter call | Valid handle allows the ATC setter before core reinitialization |
| Core initialization | First core probe obtains the PHY | Existing core is reinitialized |
| Generic HCD initialization | Later HOST setter path exists | Same later path exists |

The early request is in [the Apple glue](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/usb/dwc3/dwc3-apple.c#L227). The [generic API](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/phy/phy-core.c#L379) returns immediately for a null PHY. [Core initialization](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/usb/dwc3/core.c#L1380) obtains the handle later. The glue's own comment warns that late USB2 setup can take effect only on a subsequent DWC3 initialization. That warning supports the hypothesis; it is not a hardware measurement.

Installed-binary disassembly shows the USB2 handle load and `phy_set_mode_ext` call before `dwc3_apple_init.part.0`, which performs reset deassertion and first core probe. These compiler-generated function boundaries differ from the source but preserve the relevant order.

Two qualifications matter:

1. The [generic HCD path](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/usb/core/hcd.c#L2806) tries HOST_SS and falls back to HOST. The [ATC USB2 setter](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/phy/apple/atc.c#L1964) rejects HOST_SS and accepts HOST. The live USB DT node names both PHYs; `xhci-skip-phy-init-quirk` was absent there, on `/soc`, and on the root node. The source path and controller registration corroborate later setup. Its exact runtime timing and effect remain unmeasured.
2. CD321x configures the mux before setting the USB role. The [ATC configuration path](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/phy/apple/atc.c#L1879) already powers USB2 on in both cases. Therefore, reconnect is not evidence that the early setter runs while USB2 is powered off. The confirmed difference is handle availability and ordering before DWC3 core initialization.

### Other explanations

The [stock CD321x code](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/usb/typec/tipd/core.c) and retained candidate source were compared. Attached startup and IRQ handling use the same debounced worker. Both the worker and IRQ path hold `tps->lock`; no ordinary unlocked snapshot race was established. The candidate leaves USB role calculation and mux-before-role order unchanged.

Stale or missing DATA_STATUS updates remain possible. The worker does not reread hardware, and the IRQ path refreshes that register only for the relevant update event. A published Type-C `host` role alone does not prove hardware initialization. Monitor/repeater readiness and input/power behavior also remain unexcluded. No PD/PHY register capture or controller-attributed first-start trace is available. The stock-glue ordering defect ranks ahead of these unproved alternatives; direct HPD-patch suppression of USB is unsupported.

## FIFO and display-driver review

USB-1 records the FIFO interrupt at 2602.875023 seconds, HPD removal at 2602.877403, and `dcp_poweroff()` completion at 2602.906873. DPTX later reconnects and the native modeset completes. The [pinned poweroff source](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/gpu/drm/apple/iomfb_template.c#L927) returns before the completion message if the clear-swap timeout sets the crashed flag. The [atomic-check path](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/gpu/drm/apple/dcp.c#L340) then rejects commits. The observed completed poweroff and later modeset do not reproduce that failure chain.

Firmware messages about a swallowed swap are not proof of a missing swap acknowledgement. The [submit callback](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/gpu/drm/apple/iomfb_template.c#L725) completes that wait on acknowledgement. No display-driver workaround is justified by this capture.

| External DCP `271c00000` diagnostic | Startup count | USB-1 count |
|---|---:|---:|
| EDT frequency setup | 4 | 1 |
| CAHandler version | 3 | 1 |
| PMU return | 3 | 1 |
| FIFO interrupt | 0 | 1 |

These diagnostics remain unexplained. Successful recovery does not make them harmless or establish clean firmware. No causal link from them to the missing startup USB hub was found.

## Checks and limits

`sha256sum -c SHA256SUMS` returned 13 `OK` results in the startup archive and four in the USB-1 archive. Independent log review confirmed unique cursors, boot attribution, event order, and the stock-comparison limitation. `git ls-remote` resolved the exact source tag/commit above. Read-only installed-module disassembly and build-ID checks corroborated the first-probe order. Independent source and firmware reviews agreed with the stated qualifications.

The investigation made no driver, boot-file, package, device, power, display-mode, or runtime-config change. It did not use `sudo`, read partner `usb_mode`, access hardware registers, enable kernel tracing, or run a new physical test. The 23:31 CEST USB-1 record remains the last full display/power/14-pin checkpoint. No new protected initramfs/GRUB or staged-image readback is claimed. Earlier full-suite failures remain open; source inspection is not a test-suite pass.

## Smallest useful follow-up

A controller-attributed, diagnostic-only one-boot design should capture first-probe versus reused state, USB2 handle presence as a boolean, actual ATC mode-set calls and return codes, and their order relative to mux power-up and DWC3 core initialization. It must also capture downstream hub/controls enumeration and both usable displays. Root hubs alone are insufficient. Existing TIPD tracepoints lack a controller identifier; do not attribute all events to the monitor while MagSafe is connected.

That diagnostic can confirm the sequence, not its causal effect. A later causal experiment would change one initialization detail while preserving the working DP setup. A wired mouse can test downstream data operation, but cannot distinguish these startup explanations.

The [plan](../plans/dev-147-m2-displayport.md#usb-startup-investigation--completed) owns review, authorization, containment, and stop conditions for any follow-up. No such image or patch was prepared here. Keep the working DP image and all backups unchanged. Normal boot restores the stock driver image, not the original DTB; the existing full rollback gate and offline Mac recovery bundle remain unchanged.
