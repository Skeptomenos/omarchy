# Monitor hub initialization comparison — 2026-08-31

The saved failures start before the later suspend warning. Some attempts fail while reading or validating the device descriptor. Another reaches hub setup, then fails a status request. The present logs do not expose the original result of that request. No PM or driver fix is justified yet.

This is saved-data analysis, not a new hardware test. The [user clarification](../evidence/dev-147-lg27-reconnect-usb-loss-2026-08-31.md#correction--no-new-reconnect-2026-08-31-1113z) is settled: there was no new reconnect during the later PM window. The [PM plan](../plans/2026-08-31-dev147-usb-pm-recurrence.md) owns the next measurement. The [main plan](../plans/dev-147-m2-displayport.md) owns boot and recovery holds.

## Compared observations

The inputs are the [identified W startup](../evidence/dev-147-w-lg27-startup-2026-08-31.md), the [attended reconnect and earlier-gap journal](../evidence/dev-147-lg27-reconnect-usb-loss-2026-08-31.md). They share a boot. Device numbers below are local to each bus generation, not permanent identities.

| Case / hub and controls device numbers | Furthest observed stage | First recorded failure or loss |
|---|---|---|
| Startup, 2 / 3 | Hub identifies, finds five ports; LG controls bind HID and ACM interfaces | None in the saved startup excerpt |
| Original reconnect, 2 / 3 then 4 / 5 on recreated bus | Same identities and bindings | Disconnects at 11:47:39.249 and 11:47:59.590 CEST |
| Earlier-gap recovery, 14 / 15 | Same identities and bindings | Disconnect at 11:58:16.764 CEST |
| Attempt 16 | High-speed enumeration attempt; no identified descriptor | Descriptor read/64 reports `-71` |
| Attempt 21 | High-speed enumeration attempt; no identified descriptor | Descriptor read/all reports `-71` |
| Hub 22 | Identifies and finds five ports; no controls enumeration | TT fallback `-71`, then fatal hub-status/configuration error `-5` |
| Hub 24 | Read/64 error, then identification and five ports | Initial `-71` is not terminal; disconnect occurs later |

Successful identifications match: high-speed hub `0bda:5411`, revision 1.55, at `1-1`; full-speed LG controls `043e:9a39`, revision 4.11, at `1-1.3`. Attempts 16 and 21 lack descriptor identity; their path alone does not establish it. Interface binding does not test an external mouse, USB-A reliability or USB3 throughput.

The original reconnect's USB loss and the later loss of hub 14 precede these retry errors. Their initiating cause is still unknown. The earlier-gap segment has no DP, Type-C or bus-recreation event. The later no-action statement does not establish the physical trigger of this older interval.

## What the source adds

Source is pinned to AsahiLinux/linux `e2e1930a9595bffafad92cec2b5504525efb9cd4`. These are code-path interpretations, not captured USB requests.

- The first-64-byte descriptor helper can preserve a negative transfer result or generate `-EPROTO` (`-71`) after a nonnegative transfer when descriptor fields are invalid. The message alone does not identify a host-controller transfer error. [Descriptor validation](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/usb/core/hub.c#L4838).
- Hub setup attempts multi-transaction-translator mode through interface 0, alternate 1. Its failure falls back to single-TT mode without aborting setup. The saved `-71` is consistent with the SET_INTERFACE request failing; this is not a direct transfer trace. [Hub setup](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/usb/core/hub.c#L1482), [interface request/error path](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/usb/core/message.c#L1637).
- Two hub-setup sites use the same status-failure wording. The first requests standard device status, two bytes. Its helper maps unexpected transfer results, including negative errors and short responses, to `-EIO` (`-5`). The later class-hub status path would add a separate failure diagnostic that is absent here. Thus the first site is the supported inference, conditional on the retained log interval; the original transfer result remains hidden. [Both status sites](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/usb/core/hub.c#L1651), [class-status diagnostic](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/usb/core/hub.c#L987), [result remapping](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/usb/core/message.c#L1184).

Hub 22's source-monotonic order is TT warning at 2905.617452 s, configuration failure at 2905.617591 s, xHCI suspend guard at 2905.628033 s, failed suspend at 2905.628175 s, then disconnect at 2905.631461 s. The [earlier source analysis](../evidence/dev-147-lg27-reconnect-usb-loss-2026-08-31.md#addendum--action-report-and-earlier-suspend-failure-2026-08-31-1106z) supports a failed runtime-suspend attempt after hub failure. Probe cleanup can request it. Neither successful suspension nor an initiating PM cause is established.

## Smallest useful next measurement — proposal only

Record the first control-transfer result and PM transition order for one observed hub generation. A one-second PM snapshot cannot resolve hub 22's approximately 170 ms attempt-to-disconnect interval.

Use a bounded, bus-scoped control-URB record: setup fields, submission/completion identity, status and requested/actual length. Include root, default-address and newly allocated addresses; do not filter only the old device number. Pair it with narrowly selected `rpm_suspend`, `rpm_resume`, `rpm_status` and `rpm_return_int` events for the child and its port/root/controller ancestry. The kernel provides these [runtime-PM event definitions](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/include/trace/events/rpm.h#L54).

Retain headers only, not payload data. This can separate a negative transfer completion from a nonnegative short response. It cannot identify a malformed descriptor field without a separately justified minimal payload capture. usbmon observes the driver/HCD boundary, not electrical traffic. [usbmon interface and limits](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/Documentation/usb/usbmon.rst).

Before release, verify collector availability, privilege requirements, clock alignment, loss counters, exact duration/byte caps and cleanup. Arm before the agreed physical action. Stop if identity, display health or power changes unexpectedly; keep raw records private. Missing/dropped events must produce an inconclusive result, not a PM conclusion. Device generation and request identity must survive bus/address reuse.

No collector is prepared or armed here. Trace activation or module loading may require sudo and changes to diagnostic state. Those remain held, as do cable action, device insertion, PM changes, image rebuild and reboot. This proposal requires no new boot image in principle; installed support has not been verified for release. If the capture starts after failure or no failure occurs, it cannot settle the cause.

## Verification and limits

Independent saved-data QA verifies all three selected journal hashes, JSON parsing, counts of 1,151 / 273 / 407 rows, common boot and ordered wall/journal-monotonic fields. Independent source review agrees with the distinctions above. Raw journals stay private; their locations and receipts are in DEV-147.

| Selected journal | SHA-256 |
|---|---|
| W startup | `5430a897b347de057472ee237d1234c38b926bf89eb420167102114e5807724e` |
| Original reconnect | `3b9914421aab04ca08c561cf5e0e2419501bc5ab8a39bba2029be538b760bd02` |
| Earlier gap | `a948de818fb0e95aaed8034d0a1e088126708abb8036b759f083b18d7ee4a1cd` |

Journal receipt clocks and kernel source clocks are distinct. Startup wall/source mapping changes; do not use wall-time subtraction for elapsed runtime across that interval. No selected log proves wire-level integrity, PM causality, lasting USB operation or a reliable kernel fix. No live capture, system change or historical image/fixture suite was run for this comparison.

## Addendum — collector feasibility, 2026-08-31

Unprivileged checks confirm kernel `7.1.6-1-1-ARCH` on aarch64, event/PM tracing support and `CONFIG_USB_MON=m`. The matching usbmon module is installed but not loaded. Tracefs/debugfs directories are root-only. This establishes compiled support, not the protected event formats or live capture behavior. The initial package query stopped because `linux-asahi-headers` was not found; a separate support inventory completed without installing anything. No kernel build is needed for this metadata check.

The source review exposes limits in the proposed capture:

- A bus-specific usbmon descriptor does not follow USB-bus recreation. Reopening creates a gap; the all-bus endpoint would broaden scope and is not approved. [Bus lifecycle](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/usb/mon/mon_main.c#L175).
- usbmon's zero-data-allocation GETX call delivers only headers to userspace, but the kernel ring still buffers payload. Its timestamps use realtime, and its drop counter omits lost submission-error events. Thus header-only delivery and zero reported drops do not establish zero-payload acquisition or completeness. [Binary implementation](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/usb/mon/mon_bin.c#L490).
- Native xHCI URB events lack setup/controller fields. More importantly, the giveback trace runs before USB core assigns final status. Root-hub requests also bypass the xHCI enqueue path. These events alone cannot supply the required setup/result stream. [Fields](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/usb/host/xhci-trace.h#L243), [trace order](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/usb/host/xhci-ring.c#L841), [USB-core routing and completion](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/usb/core/hcd.c#L1535).
- TRB events lack a safe controller/device/URB join, and unfiltered records can contain immediate payload. Generic usbcore events describe allocation/state rather than transfer results. Do not substitute adjacency for identity or enable broad tracing. [TRB fields](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/usb/host/xhci-trace.h#L100), [usbcore events](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/usb/core/trace.h).

Independent source and safety reviewers recommend one small protected metadata read before selecting acquisition machinery. The [read-only helper](../../dev/apple-dp-altmode/usb-event-capture/README.md) is prepared and independently tested; it reads 15 fixed format/control-metadata files, not trace buffers or device traffic. The actual root-run inventory is still pending. Its success would not remove these source-defined limits, authorize new instrumentation or establish a usable collector. The [PM plan](../plans/2026-08-31-dev147-usb-pm-recurrence.md) owns that manual boundary.
