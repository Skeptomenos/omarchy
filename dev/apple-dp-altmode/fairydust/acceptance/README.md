# Capture front-port acceptance evidence

The [living stability plan](../../../../docs/plans/2026-09-05-dev147-front-port-stability.md) owns test outcomes and release readiness. `snapshot.py` only captures evidence. It does not move cables, change system configuration, enable tracing or decide that hardware passed. The separate trace launcher below temporarily enables scoped tracing.

Run as the normal user on the frozen candidate:

```bash
python3 /home/david/Work/omarchy-dev147-fairydust-build/dev/apple-dp-altmode/fairydust/acceptance/snapshot.py front-connected
```

Each run prints a unique directory under `/home/david/Work/dev147-fairydust-acceptance-20260905`. It contains `snapshot.json`, categorized `journal.jsonl` and `SHA256SUMS`. Files are made read-only; their owner can still change permissions, so this is not tamper-proof storage.

The snapshot captures the release, boot ID, monotonic sampling interval, DRM connector state, explicitly allowed Type-C fields, and active/recovery/guard hashes. It never reads Type-C `usb_mode`. Journal output contains selected event fields and classifications instead of raw messages. Recent diagnostics cover selected drivers over fifteen minutes; service and DCP-boot records cover the current boot. Reaching a record limit makes the capture incomplete. This is not a full-system crash scan or full-boot error inventory; those remain separate acceptance checks.

| Status | Meaning |
|---|---|
| `SNAPSHOT_CAPTURED` | Required evidence was collected, with no classified errors in the sampled records |
| `SNAPSHOT_CAPTURED_WITH_ERRORS` | Evidence was collected and includes classified error records |
| `SNAPSHOT_INCOMPLETE` | Required evidence is missing or does not match the expected candidate |

Exit status is 0 only for `SNAPSHOT_CAPTURED`; both other capture states exit 1 and retain their evidence. Usage errors exit 2. None of these statuses means endurance or visual success. Existing firmware warnings must remain visible and be assessed separately from host driver errors.

Record the physical port, cable orientation, approximate insertion time and visible outcome separately. The checkpoint summary counts only external controller `271c00000.dcp`, endpoint `0x28`; categorized records retain other controller identities separately. Endpoint numbers in JSON are integers, so `0x28` is 40. Pair counts are arithmetic over announcement records, not proof of logical display generations or occupied host service slots. Do not count duplicate connect calls as extra successful reconnects.

Validate the collector software with:

```bash
bash /home/david/Work/omarchy-dev147-fairydust-build/dev/apple-dp-altmode/fairydust/acceptance/validate.sh
```

The gate combines formatting, lint, strict typing, namespace entry-point controls and live read-only capture checks. Fixtures replace DRM/Type-C trees and command outputs; protected pin files and boot ID remain live inputs. A software gate PASS can include a live snapshot with errors. It verifies honest capture, not a clean boot or stable display.

## Read-only trace preflight

Before preparing a bounded fault trace, run this launcher as the normal user and enter the sudo password:

```bash
bash /home/david/Work/omarchy-dev147-fairydust-build/dev/apple-dp-altmode/fairydust/acceptance/trace-preflight.sh
```

Keep the monitor connected. No cable action is needed. The privileged block checks the running release and reads eight fixed tracefs files: available tracers, clocks and six event formats. It does not enable tracing, read trace buffers or change event settings. The launcher retains `report.txt`, `stderr.log` and `exit-status` in a private directory and prints its path. Missing formats or read failures return a nonzero status. The recorded runtime result is in the trace preflight evidence below.

Shell syntax and independent source review passed. Existing IOMFB method and mailbox-header events can help locate a missing or late acknowledgement. They do not directly prove that the host clear-swap completion callback ran. See the [trace design evidence](../../../../docs/evidence/dev-147-trace-preflight-2026-09-05.md).

## One attended disconnect trace

After a successful preflight, keep the monitor on the working front USB-C port with the same cable orientation. Run from a terminal on the internal display:

```bash
bash /home/david/Work/omarchy-dev147-fairydust-build/dev/apple-dp-altmode/fairydust/acceptance/trace-capture.sh
```

Enter the sudo password. Wait for `READY`. Then unplug the front-port monitor cable once, wait five seconds, and reconnect it once. Leave it connected until the command finishes. Record whether the image returns and its approximate delay. Do not start a reconnect batch.

The capture lasts 45 seconds in its own trace instance. It selects external DCP method/callback metadata and IOMFB mailbox headers, plus available CD321x events. Type-C events have no port identity. The script stops tracing, records per-CPU loss statistics and the trace, then removes its instance. It replaces no kernel or boot files and does not reset drivers. Result files stay private and may contain process names; do not publish the raw report.

The terminal prints the result directory. Share that path and the visual result. Exit 0 means capture and cleanup completed; it does not establish loss-free tracing, successful image recovery or a fixed fault. Setup failure means no cable action is needed. A cleanup failure remains explicit in the report and must be reviewed before another run.

Validate the trace launcher in a disposable fixture with:

```bash
python3 /home/david/Work/omarchy-dev147-fairydust-build/dev/apple-dp-altmode/fairydust/acceptance/test_trace_capture.py
```

The test replaces sudo and tracefs inside bwrap. It does not enable live tracing. [Preparation evidence](../../../../docs/evidence/dev-147-targeted-trace-2026-09-05.md) records checks and their limits.

## Attach after monitor power cycling

Use this probe only after preserving the failed state. Keep Linux running. Disconnect the monitor USB-C cable from the Mac. Remove the monitor's AC power for 30 seconds, restore AC power and wait for the monitor to start. Keep the USB-C cable disconnected until READY.

```bash
bash /home/david/Work/omarchy-dev147-fairydust-build/dev/apple-dp-altmode/fairydust/acceptance/trace-capture.sh attach
```

Enter the password. At READY, connect the same cable once to the same front port with the same orientation. Wait until the capture finishes and report the image result. This mode changes only the instruction cue; capture filters, 45-second duration and cleanup remain the same. It issues no driver-reset or role-swap command.

The [failed reconnect evidence](../../../../docs/evidence/dev-147-targeted-reconnect-failure-2026-09-05.md) explains this probe. Recovery would establish that a Mac reboot is unnecessary for this attempt; it would not isolate monitor state from the longer disconnection interval.

## Rear-drive insertion comparison

After a verified working front-monitor baseline, leave its cable untouched and keep the drive disconnected until READY:

```bash
bash /home/david/Work/omarchy-dev147-fairydust-build/dev/apple-dp-altmode/fairydust/acceptance/trace-capture.sh rear-attach
```

At READY, connect the external drive once to the rear USB-C port. Leave both cables connected until the capture finishes. Report whether the monitor image stayed visible and whether the drive appeared. Do not start a front-port reconnect or unplug the drive during this capture. The recorder does not mount, read or write the disk; the desktop's normal device handling still applies.

This mode changes only the instruction cue and records its name. The existing Type-C events capture both ports, while DCP metadata stays filtered to the external display. The [rear-empty control](../../../../docs/evidence/dev-147-rear-empty-reconnect-2026-09-05.md) owns the starting observations.
