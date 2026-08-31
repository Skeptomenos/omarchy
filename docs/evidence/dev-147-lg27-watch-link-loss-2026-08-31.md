# DEV-147 — LG27 watch detected link loss, 2026-08-31

Host/scope: the existing M2 front/lower USB-C display path, in the working-driver boot. Approval: David requested passive checks about every ten minutes. The fixed watch requires a pause after external loss or a new fault. This record does not establish an unattended or spontaneous failure: physical actions around the event remain unconfirmed.

## Result

The 05:23:31 CEST sample found DP-1 disconnected/disabled, with no modes and no compositor output. The internal output remained connected/enabled at 2560×1664/60 Hz. Monitor-port USB-PD was offline. MagSafe was online; battery was Full/100%, with reported current 0. Boot, kernel and the two module notes match the [working baseline](dev-147-lg27-watch-baseline-2026-08-31.md).

Sixteen earlier scheduled samples retained the baseline display/power states and had no new matching fault signatures. The last was 05:10:39 CEST. These are sampled software observations, not visible-pixel checks or continuous uptime. The final sample began 772 seconds (12m52s) after the previous sample ended. No intervening sample is claimed.

The new journal interval records this sequence at about 05:17:35 CEST:

| Time within that second | Saved event |
|---|---|
| .647 | DPTX FIFO error interrupt |
| .648 | IOAV video interface terminated; display HPD removed |
| .672 | Hotplug callback reports disconnected |
| .675 | DCP poweroff completes |
| .682 | DPTX disconnect |

The interval contains one FIFO error diagnostic. It has no matching RTKit/DCP crash or panic, timeout, atomic-rejection, or suspend/resume record. This is not proof that firmware is healthy or that a crash guard is clear. It differs from the earlier connected/disabled, modes-present recovery failure. The power snapshot does not establish when USB-PD dropped or whether that preceded the video loss. No cable fault, monitor fault, PR582 causation or initiating software defect is established.

## Capture and checks

The one bounded, unprivileged snapshot read the fixed DRM attributes, compositor status, known standard power supplies, boot/module identity and only the new kernel-journal interval. All nine commands exited 0 with empty stderr. Before/after boot identity matches. The interval has 152 valid same-boot records, unique cursors, no overlap and ordered/newer timestamps. It is 134,482 bytes; SHA-256 is `433b70e0d7d3226d47e1f274e4a1a9dfa5083e4af96b7b0c76b1f6e90b5c268b`.

Independent saved-file QA confirms capture integrity and the changed display/power state. Its first summary reversed the two supply labels and omitted the FIFO diagnostic. The corrected review agrees: MagSafe is online; monitor PD is offline; one FIFO diagnostic is present. This correction preceded the saved result and this record.

Raw journals, serials, boot IDs and cursors remain private. DEV-147 holds the watch/sample pointers. The private result and state preserve the last good sample, changed state, event times, sampling gap and pause reason.

## Stop and next boundary

The existing same-task watch was changed to PAUSED. The scheduler tool confirmed that status. No further live query, retry, repair, driver or display action followed the sample. No system configuration, image, default boot or recovery file changed. The original baseline and all earlier results remain intact.

Ask David whether the USB-C cable, monitor input or monitor power changed around 05:17 CEST. Keep MagSafe connected. No reboot or reconnect is requested yet. Resume or establish a new baseline only after his reply and a separate agreed next step. All earlier live-action, candidate, staging, device and recovery holds remain. The [main plan](../plans/dev-147-m2-displayport.md#passive-lg27-observation-living) owns the current boundary.
