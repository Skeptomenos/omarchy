# DEV-147 targeted reconnect failure — 2026-09-05

David reports that the external image did not return. He confirms the same monitor cable, front port and orientation. The rear-port device remains unspecified. The running kernel is `7.1.12-dev147-fairydust1`, boot `f80d5566-d14a-4374-9824-15887a63c576`.

## Capture integrity

Private capture: `/home/david/Work/dev147-fairydust-acceptance-20260905/trace-capture.szD14MlJ`. Report SHA256: `52d57fd9abd662aeea846f43d79782e80ec3153bcaf32f5408530c232149f9e9`. Exit 0, empty stderr, 113 of 113 entries retained. All 24 loss counters across eight CPUs are zero. The report confirms removal of its instance. Clock is mono; observed window is 7403.64–7448.65 seconds. The kernel rounded the requested 4096 KiB buffer to 4107 KiB per CPU.

## Shutdown completed in this run

| Trace stage | Boot-relative seconds | Delay |
|---|---:|---:|
| Clear swap start method push | 7413.318401 | — |
| Context 2 start ACK | 7413.360704 | 42.303 ms from push |
| Clear swap submit method push | 7413.360709 | — |
| Context 2 submit ACK | 7413.364030 | 3.321 ms from push |

The combined interval is 45.629 ms. The subsequent abort-swaps, last-client-close and set-power-state methods receive replies. The journal reports `dcp_poweroff() done` and no clear-swap timeout in this interval. Source and trace ordering show progress beyond the clear-swap wait. This attempt does not reproduce the earlier timeout, and existing events do not directly trace the completion cookie or response swap ID.

## Reconnect stopped before DisplayPort selection

At 7412.401591 and 7412.444331 seconds, data-status events executed in the `irq/117-0-003f` thread report USB device-role flags, then USB2/USB3 connection flags. Neither reports DP_CONNECTION or HPD_LEVEL. The thread identity provides controller attribution in this capture; the event payload itself has no port field. No new DPTX connection or AFK service generation appears in the bounded journal.

The read-only snapshot `failed-targeted-trace.69o1__4r` reports external DP disconnected/disabled and internal eDP connected/enabled. Front `port1` maps to controller `0-003f`, reports device data role and sink/PD power. The front USB host controller was removed; only the rear controller root hubs remain. A USB hub suspend failure `-32` also occurred at 7405.995108 seconds. These observations do not establish which device or firmware caused negotiation to fail.

The [older failed reconnect](dev-147-tipd-failed-reconnect-2026-09-04.md) had the same broad no-DP/device-role signature. A [host-role request was already rejected](dev-147-tipd-host-role-rejection-2026-09-04.md). Do not repeat that write or treat this failure as new AFK exhaustion. The older [successful first attach](dev-147-tipd-first-attach-positive-control-2026-09-04.md) already provides a positive comparison, with different boot freshness.

## Next discriminator

Preserve Linux boot and kernel state. Disconnect the monitor USB-C cable, remove monitor AC power for 30 seconds, restore AC, then trace one fresh attachment with the same cable, port and orientation. This changes monitor power state and connection dwell time together; success would show recovery without a Mac reboot, not prove a monitor-only defect. Failure would keep host/controller state, cable and monitor negotiation under investigation. No driver reset, role request or timeout change is justified by this trace.

Private bounded analysis: `/home/david/Work/dev147-fairydust-acceptance-20260905/failed-trace-analysis/summary.json` and `kernel-window.json`. The next physical test and image result remain pending.

## Attach-mode preparation

Added an allowlisted `attach` argument to the recorder. It changes the READY cue to one connection and records the mode. The default reconnect behavior and capture boundaries remain intact. Author and root ran `python3 dev/apple-dp-altmode/fairydust/acceptance/test_trace_capture.py`: six tests passed, including attach cue and invalid arguments. Shell syntax, Ruff, formatting, strict typing and diff checks passed. No live capture or monitor reset ran during software validation.

- Launcher SHA256: `39795d207c7cc6136fec252510959a564ac2b1b95aeac87d0a8943d868c87675`.
- Test SHA256: `802b35255b3ceb7e5e83065d2dc05e43761bff2d4522c7183a5e088170cfd935`.
- Author receipt: `/home/david/Work/dev147-fairydust-acceptance-20260905/checks/trace-attach.9g88kw__/qa.json`, SHA256 `8e06b81a1774b7291e2a0b01f5552746e7c45feeea0c24dad2ffe7ef33f11d52`.

The previous default recorder's independent QA receipt is `/home/david/Work/dev147-fairydust-acceptance-20260905/trace-capture-independent-qa/receipt.json`, SHA256 `636b419f0bb8a6608a37dd4a8a8e829d60ff2171ff7fe665313d166a24874c4c`. It applies to the prior code; the actual failed capture subsequently verified runtime filters and cleanup for that run.

Independent review re-derived the trace timing and failure localization, found no blocking attach-mode defect, and reran the six test methods successfully. The monitor power-cycle/attach result remains pending.
