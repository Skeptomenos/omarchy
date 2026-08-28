# DEV-147 HPD startup investigation — 2026-08-29

Scope: saved M2 J413 front/lower USB-C results and pinned kernel source. This is a read-only comparison, dated in Europe/Berlin; the retained source/log checks began on 2026-08-28 UTC. No new boot, device action, source execution, or hardware measurement occurred. The [main plan](../plans/dev-147-m2-displayport.md#autonomous-offline-goal--next-test-package-living) owns authority; the [T1 selection](../plans/dev-147-usb-startup-diagnostic.md#a1-selection--t1-tipd-sender-diagnostic-living) owns the next diagnostic design and review gates.

## Finding and limit

The pinned DRM code drops an OOB hotplug notification if its connector is not yet in the global registered-connector list. It does not retain that event for registration-time replay. This is a source-proven mechanism, not proof that the confirmed E failure took that path. Saved timing makes sender/receiver ordering worth measuring. It does not establish the time or cached HPD state of TIPD's actual notification call.

The earlier [USB startup investigation](dev-147-usb-startup-2026-08-28.md) remains unchanged. Its first-probe USB2 handle-order defect is still source-supported, but it is not a proved cause of either missing USB enumeration or lost video. The new receiver finding does not justify a delay, forced reconnect, replay, or behavior fix.

## Saved cases

Times below are journal timestamps in seconds since each boot, rounded to milliseconds. They are not callback execution timestamps. The [D3 result](../evidence/dev-147-usbdiag-startup-failure-2026-08-28.md), [E capture](../evidence/dev-147-post-c4-display-loss-2026-08-28.md), later [E-selection confirmation](../evidence/dev-147-c4-selection-confirmation-2026-08-28.md), and [intended W recovery](../evidence/dev-147-w-recovery-after-e-2026-08-28.md) own the original observations.

| Saved case | Kernel records | xHCI registration | External DCP bind / “booted” | External video / downstream USB |
|---|---:|---:|---:|---|
| D3 | 963 | Not observed in retained window | 3.190 / 4.204 | External FAIL; no USB enumeration pattern retained |
| E, selection confirmed | 1,012 | 1.492 | 2.732 / 3.757 | External FAIL; root hubs only |
| Latest intended W | 1,122 | 4.543 | 2.860 / 3.886 | Native external recovery; root hubs only |

The latest recovery report did not restate its filename. W/E share loaded USB-module identities, so these cannot independently prove W artifact startup. Its external connected event occurs at 6.759 s and native mode at 6.791 s. The 14/12/6 crossbar deferrals in D3/E/intended W subsequently recover; deferrals alone do not explain the different results. Diagnostic USB binaries are not necessary for E's observed failure, but D3 and E need not share a cause.

E retains early packaged-DWC3 availability; W lacks that module in its initramfs. E's xHCI appears before external DCP binding, while the intended W capture has it later. Archive identity proves packaging, not actual call order. Root-hub registration does not prove downstream USB or display readiness. Known external firmware diagnostics in the working pipeline remain open; their absence from an inactive external pipeline is not a clean-firmware result.

Capture limits remain: audit suppression was 461/457/444 callbacks respectively; record uniqueness and terminal rereads do not prove unsuppressed message production. The saved scan-end cursors can differ from the last printed row at the time boundary. D3's final row precedes its declared cutoff; do not invent a complete-tail PASS. D3's broken v1 guard explains missing diagnostic markers, not video loss. Zero diagnostic markers are expected for uninstrumented E/W. Earlier root-private bytes retain user-validator provenance. USB-PD charging reported by David is separate from USB-data acceptance and does not establish present cabling or a controlled power result.

## Exact source path

All upstream links below use Asahi commit `e2e1930a9595bffafad92cec2b5504525efb9cd4`, tag `asahi-7.1.6-1`, for kernel `7.1.6-1-1-ARCH`. This is not reproducible-build equivalence for every packaged binary.

1. The working [TIPD HPD patch](../../dev/apple-dp-altmode/tipd-cd321x-hpd.patch) forwards cached HPD after the existing mux update and synchronous USB-role call. In the saved patched core these are lines 743, 746, and 749. Role errors remain ignored; a returned error alone does not skip HPD. The worker can return earlier on disconnection or partner-registration failure. Its connector reference comes from the saved `displayport` property. The [stock source](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/usb/typec/tipd/core.c#L637) supplies the unchanged surrounding flow.
2. [DRM lookup](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/gpu/drm/drm_connector.c#L3486) searches registered connectors by primary/secondary fwnode and takes a reference. [OOB dispatch](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/gpu/drm/drm_connector.c#L3522) returns silently on missing lookup; otherwise it calls the callback and releases the reference. It stores no pending state. [Registration](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/gpu/drm/drm_connector.c#L837) adds the global entry at line 876 without OOB replay.
3. [Apple setup](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/gpu/drm/apple/apple_drv.c#L329) links the connector before starting DCP. It attempts readiness waits and a 100 ms settle, then calls `drm_dev_register` at line 515. Creation/linking is not global registration. Readiness failures are warned about, not necessarily registration blockers.
4. The [Apple OOB callback](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/gpu/drm/apple/apple_drv.c#L87) prints its existing marker, calls DCP connect/disconnect, and ignores the result. [DCP connect](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/gpu/drm/apple/dcp.c#L376) can reject a missing PHY or disabled service without queuing replay. The marker proves callback entry when positively correlated; it has no diagnostic revision or target identity. Its absence cannot distinguish no send, lookup failure, or capture loss.
5. [IOMFB](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/gpu/drm/apple/iomfb_template.c#L1432) completes active/start-ready state in later callbacks after the “DCP booted” print. Neither that print nor `is_main_display` proves global connector registration. A later eligible TIPD worker with HPD high sends connected again even without a new HPD edge; an early missed send need not be permanent.
6. The [USB2 early setter](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/usb/dwc3/dwc3-apple.c#L227) precedes first handle acquisition; the generic API accepts null. But [ATC configuration](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/phy/apple/atc.c#L1879) can power USB2 before that setter, and [HCD](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/usb/core/hcd.c#L2828) has a later HOST_SS→HOST fallback. Neither an early handle fix nor a claim that HOST is never set follows from this comparison.

## Pins and checks

Fresh SHA-256 reads matched the retained control/source records. DWC3 and ATC controls also match the earlier investigation copies. The two saved patched TIPD core copies match each other. The five new receiver/allocation snapshots match the pinned GitHub blob IDs and byte sizes; they close the earlier missing-dispatcher/registration gap. The [I2C frontend](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/usb/typec/tipd/i2c.c#L14) allocates the exported `data->tps_struct_size` before `tipd_init`, which is relevant to the proposed core-local diagnostic state; this is source evidence, not an ABI/build test.

| Saved source | SHA-256 |
|---|---|
| Stock TIPD `core.c` | `3f581b0837bf24c085fb08db0043329b6d3043fc1c9f6b25b005f7e7bdba0a72` |
| Working HPD-patched TIPD `core.c` | `bb19187a1c41517e4b9f0fc3da7089fd41d26851774001ae3ad10c43139f2e15` |
| DWC3 glue / ATC control | `6d2ff775e11b62d1f343b07fbcfdf4a73b4159ac38ff2c2e1ee7c6df1b4a4420` / `75b9b68c3096a151d31828650887cf7a7caa88c7f0dd5655f4c4727959953939` |
| DRM connector | `112d87ede8e7e714813c187655a1121411d0a8d803f5fee2b5595ef3ede592ae` |
| Apple driver | `bddd3c477a84b73a64cee8b7eafdabea8fb4de7a8f96b3c7c198b231004d8418` |
| Apple connector `.c` / `.h` | `bbc24737128162405fa06a6a4344b48997bb2aa409cd6f7cef5eade88b479359` / `ca018ad0b77f71e97da53680056bca0dca286d910b9dd3d12041f25a8cf53116` |
| DCP / IOMFB template | `62ef6fb797f7875b8129dfe47f25a4b75ab8b4912c201154632aa0b66591608d` / `5177f0a09717cc279a8579a3c20ffe7e9b8068aae356be5980bb52101713aee3` |
| TIPD I2C frontend | `6051ba21184915fc3399599655ed3fc8c71a4b0b57d3c8b6ebe32b21025ce9e1` |

Selected C2 verification matched all 31 fixed inputs and the retained E image/result/delta against its saved manifest. It was not a fresh full 2,270-file seal run or image assembly. Independent saved-log review agreed within its selected scope. These checks add no test-suite, module-load, root-private readback, reliability, or hardware PASS. Raw logs, host identities, and private manifests remain private.

The remaining measurement is whether the exact front-controller worker chose and returned from the HPD call, with its queued state and surrounding mux/role outcomes. A sender-only trace cannot establish receiver delivery, register latching, or causality. At this record's publication checkpoint, independent safety, documentation QA, and source/design review agreed on T1 for offline A2–A4. The living plan owns that selection; no T1 source, binary, image, or manual action exists yet. Firmware findings and USB/full Gate 4b remain HOLD.
