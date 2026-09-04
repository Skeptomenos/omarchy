# DEV-147 TIPD failed reconnect capture

**Date:** 2026-09-04
**Host:** `omarchy-air`
**Boot ID:** `061c4b0f-2ca9-484a-b6f0-005d9a432d3b`
**Controller:** `0-003f` through `/sys/class/typec/port1`
**Provenance:** The retained source is user-pasted terminal output plus David's explicit physical-display confirmation. No separate filesystem receipt exists.

## Attended cycle

David confirmed the manual safety preconditions. LG27 was connected and blank on the lower/front left USB-C port. He disconnected it once, waited five seconds, reconnected the same cable to the same port, and reported the cycle complete. LG27 remained blank. The internal display stayed physically normal, and Linux stayed responsive.

The pre-state and post-state were identical:

```text
partner=present
data_role=host [device]
DP-1=disconnected
DP-1_enabled=disabled
eDP-1=connected
eDP-1_enabled=enabled
xHCI=absent
UDC_count=0
```

The bracketed Type-C value means that the device data role remained active. This observation does not establish that the data role caused the display failure.

## Trace integrity and parser defect

The isolated trace retained 37 of 37 raw entries. Twenty-one entries came from the `irq/116-0-003f` thread and are attributable to controller `0-003f`. All per-CPU overrun, commit-overrun, and dropped-event counters were zero.

The capture script incorrectly counted zero total and attributed events. Its parser searched for ` tps6598x:`, but the raw trace names are `cd321x_irq`, `tps6598x_status`, and `cd321x_data_status`. The resulting `trace_result=empty` and `TRACE HOLD` are false negatives. The raw event names and threaded IRQ task provide the corrected counts above.

## Controller timeline

- 9302.436 to 9302.472 seconds: disconnect handling reported `STATUS_UPDATE`, then `PLUG_EVENT|DATA_STATUS_UPDATE|STATUS_UPDATE`, a `no-conn` status, and an empty data-status payload.
- 9302.984 seconds: the journal reported DPTX status `0x2` and `dcp_dptx_disconnect(port=0)`.
- 9316.580 to 9316.584 seconds: reconnect handling reported `PLUG_EVENT|DATA_STATUS_UPDATE|STATUS_UPDATE`, a connected status, and `DATA_CONNECTION|USB_DATA_ROLE|0x80000000`.
- 9316.623 to 9317.622 seconds: later data updates added and removed USB2 and USB3 connection flags, but none reported `DP_CONNECTION` or `DP_SINK`.
- 9317.336 and 9318.129 seconds: the journal again reported only DPTX status `0x2` and `dcp_dptx_disconnect(port=0)`.

Controller `0-003f` reported no `POWER_STATUS_UPDATE`, `HPD_LEVEL`, or `HPD_IRQ` event. The bounded journal contained no DPTX connect or HPD assertion. It contained no new AFK service allocation. Some status payloads contain power-related fault tokens, but this capture does not establish a power fault.

## Localization

The physical reconnect reached the CD321x interrupt and status path. Its firmware-reported data state never reached DisplayPort connection or sink flags. The journal stayed on the disconnect path. This localizes the failed generation before DisplayPort alternate-mode and DisplayPort mux setup, DPTX connection, AppleDRM service creation, and AFK allocation. Plain USB mux setup can still occur. This result does not identify the cause inside firmware or Type-C negotiation.

[Asahi Linux commit `82432bbf`](https://github.com/AsahiLinux/linux/commit/82432bbfb9e83b7e81d04660fe129b99a29b2ac2) states that CD321x firmware negotiates the target alternate mode and only informs the CPU after selection; the CPU cannot influence that choice. On 2026-09-04, the accepted source at [`e2e1930a`](https://github.com/AsahiLinux/linux/commit/e2e1930a9595bffafad92cec2b5504525efb9cd4) and Asahi default branch `asahi` at [`77cb8f24`](https://github.com/AsahiLinux/linux/commit/77cb8f24c2381a8abb7272d7bbdec548d6426a8a) were compared. Their `drivers/usb/typec/tipd/core.c` files were byte-identical. The code path used when firmware reports no `DP_CONNECTION` contains no driver-side recovery.

## Result

This capture explains why generation 4 did not test AFK reuse: the connection did not reach DisplayPort alternate-mode or DisplayPort mux setup, DPTX, AppleDRM, or AFK. Plain USB mux setup can still occur. The ten-generation AFK gate remains open and blocked.

The next test must capture the first LG27 attach after a fresh candidate reboot with the monitor initially disconnected. It uses the same monitor, cable, and port as a positive control. It is not a fully matched trace because boot freshness and link generation differ. A corrected parser must count the real event names and retain a loss-free controller-attributed trace. Compare that positive-control sequence with this failed reconnect before any recovery design is selected.
