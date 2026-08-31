# LG27 reconnect restores video but not stable USB — 2026-08-31

Result: qualified video recovery PASS; USB-data readiness FAIL. David reports one unplug, five-second wait and reconnect, with the external image returning after about ten seconds. The hub and controls returned briefly, but disappeared again before the read-only snapshot. The [previous loss and PM evidence](dev-147-lg27-usb-data-loss-2026-08-31.md) remains unchanged.

## Observations

| Time, CEST | Saved event |
|---|---|
| 11:47:19–20 | Brief hub/controls enumeration and loss before controller teardown |
| 11:47:21 | xHCI teardown, one DCP FIFO diagnostic, then HPD removal |
| 11:47:27.752 | USB bus recreated |
| 11:47:28.568–28.953 | Hub `0bda:5411` and LG controls `043e:9a39` enumerate |
| 11:47:39.249–39.993 | Both disconnect and enumerate again |
| 11:47:43.789 | External HPD asserted |
| 11:47:44.101 | 4K modeset completes |
| 11:47:59.590 | Hub and controls disconnect again |
| 11:48:00–07 | Seven enable failures, two setup-address failures, one `-71` and two final enumeration failures |
| 11:49:14 | Only root hubs remain; both native displays and PD sources are active |

Final USB loss is 31.838 seconds after bus recreation and 15.489 seconds after the completed modeset. No later DCP disconnect/HPD-loss, controller teardown or TIPD transition accompanies that final loss in the saved journal. Earlier DCP disconnect calls during display establishment and the teardown-time FIFO diagnostic are not omitted or assigned as causes.

The snapshot has eDP-1 at 2560×1664/60 Hz and DP-1 at 3840×2160/59.997 Hz, both enabled with DPMS on. MagSafe and monitor PD report online; battery is Full/100%. The same W boot, kernel/packages and loaded AppleDRM/TIPD notes match. xHCI, root hubs and root ports were recreated, so their current PM counters do not describe uninterrupted pre-reconnect history. The missing children's pre-loss PM state is still unknown.

## Checks and limits

Independent saved-evidence QA PASS: all 25 raw checksums, nine boot brackets across the related captures, module-note bytes, cursor uniqueness and timestamp order agree. The new journal has 273 records and 224,814 bytes. It covers 11:39:07–11:48:26.431 CEST, not the entire interval to the snapshot. It is an ordered, non-overlapping cursor continuation, not exact sequence-number adjacency or proof of complete logging.

Journal SHA-256: `3b9914421aab04ca08c561cf5e0e2419501bc5ab8a39bba2029be538b760bd02`.

Five capture wrappers exit zero. `upstream-pm` exits 1 with two root-port `autosuspend_delay_ms` EIOs. These unavailable fields were not retried; the other saved values remain usable. Future readers exclude delay attributes on PHY/port objects. Raw data and receipts remain private in DEV-147.

David's ten-second visual estimate stays approximate. Logs show HPD absent for 22.075 seconds and bus-recreation-to-modeset time of 16.349 seconds. Neither measures the exact physical reconnect-to-visible-image interval. The latest user message reports external recovery; internal enablement is software-corroborated, not a fresh physical observation by the agent.

## Source-based narrowing

The kernel's cable-warning text is a generic reset-retry failure, not a cable test. The setup-address warning maps a USB transaction error to `-EPROTO`. Neither establishes the initiating cause. See the [pinned hub reset path](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/usb/core/hub.c#L2953-L3151), [xHCI completion mapping](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/usb/host/xhci.c#L4435-L4446) and [USB error definitions](https://docs.kernel.org/driver-api/usb/error-codes.html).

Ordinary xHCI USB2 hardware LPM excludes hubs and devices behind non-root hubs. The observed monitor hub and its LG control device meet those exclusion conditions. This narrows that specific L1 mechanism; it does not exclude runtime autosuspend, PHY/controller-internal power behavior or routing faults. See the [eligibility test](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/usb/host/xhci.c#L4776-L4793) and [independent programming guard](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/usb/host/xhci.c#L4674-L4686).

## Next boundary

The reconnect handoff is consumed. Do not repeat it, add a mouse, change PM or try another image. A post-report snapshot missed the short-lived hub state. The [recurrence plan](../plans/2026-08-31-dev147-usb-pm-recurrence.md) therefore prepares a bounded passive reader that must be armed before a separately attended reconnect. No cause or fix is claimed.

## Addendum — passive reader preparation, 2026-08-31

The non-installed reader and its fixture tests are prepared. Separate Bash syntax checks, 14 real-filesystem checks and integrated-copy diff hygiene pass. Independent reader QA also passes. A discovered per-object encoding failure is fixed and covered by an oversized-file regression; the retained RED evidence is not a hardware failure. Public source bytes match the reviewed private copies. The plan records hashes, execution-provenance limits and the exact focused gate.

No live `--record` run occurred. Snapshot cadence, live discovery and mid-read hardware races remain untested. The next boundary is user availability for one newly armed, attended case; it is not permission to repeat the old reconnect now.

## Addendum — first bounded PM window, 2026-08-31 10:15–10:18Z

David replied “ready”. Fresh checks matched the same W boot, packages and module notes. The agent armed the reviewed reader before releasing one reconnect instruction. The recorder finished normally after 180 samples. No completion or physical-action report had arrived when this record was written. The instruction expired with the window; the agent told David not to reconnect or repeat it now.

Capture integrity PASS; reconnect classification and child-PM measurement INCONCLUSIVE. Every sample contains the same controller, xHCI and two root hubs, with no monitor hub or controls. The controller/xHCI report `on`/`active` and zero cumulative runtime-suspend time. The empty root hubs report `auto`/`suspended`. This does not establish what David physically did, exclude a missed transition, or explain the earlier USB loss.

The first-to-last sample brackets span 12:15:03.933–12:18:03.962 CEST. There are 180 valid, contiguous ordinals, 470,592 bytes and only `ok`/`missing` attribute statuses. Sample-start intervals are 1.00–1.01 seconds by the saved uptime clock. Recorder exit is 0 and stderr is empty. `sha256sum -c capture.sha256` verifies all 33 captured files. Samples SHA-256: `7259e9ec73a9d4a24f9205078a74ec5e9f5e7f38fa80e304e1f937ab891657e8`.

The incremental journal contains 48 ordered records and 42,909 bytes, from 12:15:39.774 through 12:19:41.500 CEST. It contains only audit/network entries, with no USB/display event. Its exit is 0 and stderr is empty. Journal SHA-256: `8b58fb069a4a2b138a1641cbdcb8fe08d6d03f619be602ef8d17c0518b11f5b5`. Silence in this journal is not proof of complete hardware observation.

The same-boot after-snapshot has both native outputs enabled with DPMS on, both PD sources online and battery Full/100%. This is software state, not a fresh visible-image report. No boot, driver, PM, timer or system configuration changed. Raw captures remain private in the DEV-147 checkpoint. The [living plan](../plans/2026-08-31-dev147-usb-pm-recurrence.md) owns the pending action clarification; no automatic rearm follows.
