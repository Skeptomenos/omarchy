# DEV-147 TIPD first-attach positive control

**Date:** 2026-09-04
**Host:** `omarchy-air`
**Boot ID:** `d91d49a5-025e-43f6-9bb4-72ec84622e64`
**Kernel:** `7.1.6-1-1-ARCH`
**AppleDRM build ID:** `1ca52ad1cea00559d5fdfd32177e4d1e694994e1`
**Controller:** dynamic Type-C class port `port2`, mapped to `/sys/devices/platform/soc/235010000.i2c/i2c-0/0-003f`
**Provenance:** User-pasted terminal output retained at `/home/david/.codex/attachments/123ffa9c-6b5d-4e36-9807-2874bca916e0/pasted-text.txt`, including the authenticated root handoff and David's `DEV147_IMAGE_HEALTHY` physical-result token. David later said that he might have connected the monitor too early.

## Attended result

The AFK reuse candidate started with LG27 disconnected. After tracing was enabled and read back, the recorder repeated the candidate and live-state guards. Its pre-state reported no partner, DP-1 disconnected and disabled, and the internal display connected and enabled. It then printed `ARMED`. David connected LG27 to the lower/front left USB-C port and supplied `DEV147_IMAGE_HEALTHY`.

The post-state reported the partner present, the host data role active, DP-1 connected and enabled, and the internal display still connected and enabled. The physical token also confirms that Linux remained responsive. The kernel journal published 16 external modes and completed a 3840×2160 modeset.

David later said that he might have connected the monitor too early. The run does not need repetition. The state-before record was emitted only after tracing was active, and it proved that the target partner was absent and DP-1 was disconnected. The loss-free trace then captured the first target-controller event and the complete observed successful sequence.

## Trace integrity

The isolated trace retained 26 of 26 entries. Sixteen entries came from the `irq/116-0-003f` thread. All per-CPU overrun, commit-overrun, and dropped-event counters were zero. The recorder reported:

```text
trace_loss_total=0
loss_fields_complete=1
trace_event_total=26
attributed_0-003f_event_total=16
trace_result=integrity_pass
TRACE INTEGRITY PASS
```

The controller sequence included a `POWER_STATUS_UPDATE`, then `DP_CONNECTION` with DisplayPort pin assignment C, then `DP_CONNECTION|HPD_LEVEL` with the same pin assignment. The kernel journal reported `dcp_dptx_connect(port=0)`, HPD assertion, AFK service creation on channels 1 and 3, 16 modes, and a completed 3840×2160 mode.

The journal also registered the `/sys/devices/platform/soc/502280000.usb/xhci-hcd.3.auto` child. It enumerated the `0bda:5411` LG hub and `043e:9a39` LG Monitor Controls device. The recorder's post-state `xHCI=absent` field is false. That field checked the obsolete path `/sys/bus/platform/drivers/xhci-hcd/502280000.usb`. Do not use this state field as xHCI evidence.

## Comparison with the failed reconnect

The [generation-4 failed reconnect](dev-147-tipd-failed-reconnect-2026-09-04.md) reported `conn-no-Ra`, `USB_DATA_ROLE`, the device data role, and no `POWER_STATUS_UPDATE`, DisplayPort connection, HPD, DPTX connect, or AFK service. This successful first attach reported `conn-Ra`, no `USB_DATA_ROLE` flag, the host data role, `POWER_STATUS_UPDATE`, DisplayPort pin assignment C, HPD, DPTX connect, and AFK channels 1 and 3.

These are correlated firmware-reported differences. They do not prove that Ra detection, the reported data role, or the power-status transition caused either outcome. The comparison is not fully matched. The success is a fresh-boot first generation, while the failure is a generation-4 reconnect on an older boot.

## Cleanup

The root script's EXIT trap emitted no `CLEANUP INCOMPLETE` message. Exact absence of `/sys/kernel/tracing/instances/dev147-first-attach-once` was not independently verifiable without root access because tracefs is root-only. An unprivileged post-run check found no `/run/dev147-first-attach.*` root-handoff directory. The capture changed no boot artifact and requires no rollback.

## Result and next step

The fresh-boot LG27 first-attach positive-control gate passes. It proves that the candidate can complete the firmware-reported DisplayPort selection, DPTX connection, AFK allocation, and native 4K display path on the same monitor, cable, controller, and port used by the failed reconnect.

The smallest next step is offline only. Select one bounded test that can discriminate the firmware role and DisplayPort-selection sequence before any further live action is authorized. The AFK ten-generation hardware gate remains open because this run tested only the first link generation.
