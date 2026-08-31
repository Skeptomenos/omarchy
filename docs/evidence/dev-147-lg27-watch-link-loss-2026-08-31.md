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

## Addendum — morning user confirmation, 2026-08-31

David reports that he did not unplug the cable, switch the monitor input, or make any change to the monitor or this machine. This resolves the physical-action question above as user-attested: no user-triggered change preceded the overnight loss. It supports an uncommanded link loss with the setup left unchanged. It does not exclude an automatic monitor transition, an electrical interruption, controller negotiation loss, or software/firmware action. No current screen, power or connector state was sampled for this addendum.

Independent saved-file comparison finds the same FIFO → interface/HPD removal → completed poweroff → DPTX-disconnect sequence during the baseline manual swap and the overnight loss. The baseline then reconnects within seconds and publishes 16 modes. No corresponding reconnection appears in the overnight captured interval; monitor PD is offline at the later sample. The shared teardown sequence does not prove that FIFO caused the loss, and the power snapshots do not time PD loss relative to video loss. No crash or prior crash-guard recurrence is established.

Keep the watch paused. The next proposed observation, held for separate approval and fresh internal-screen/MagSafe confirmation, is one bounded, unprivileged check of front-port Type-C partner directory presence and standard power state, with the cable unchanged. Read directory presence only, never partner `usb_mode`. It can distinguish whether Linux still represents a USB-C partner from a display-only failure; it cannot recover the initiating event or authorize a repair. No new live query, reconnect, reboot, build or system change occurred for this addendum.

## Addendum — authorized follow-up and near-four-hour timing, 2026-08-31

David approved the check and asked the agent to perform necessary checks and contained work without repeated permission requests, stopping when manual support is needed. One bounded snapshot at 09:43:22 CEST confirms the same working-driver boot, internal native output active, external disconnected/disabled with no modes, monitor PD offline, MagSafe online and battery Full/100%. A subsequent metadata-only check, outside that timestamped window, maps controller `003f` to `port2`, whose partner is absent. Its exact time was not recorded. The initial fixed `port1` path was stale and is not evidence of partner absence. No partner attributes, including `usb_mode`, were read.

All 12 recorded commands exited 0 with empty stderr: ten hardware-status captures, one Linear context read and the correcting metadata-only mapping. The incremental journal has 2,500 valid, unique, ordered same-boot records, with no old-cursor overlap and no matching new display/controller/crash/suspend/resume event. Retained record times span 05:24:05–09:43:17 CEST; this is not continuous screen observation. Its 2,245,997 bytes hash to `fa7814bbff1cbab1283164320907360181e3c20a0056f81d8399ffc1824844be`. Independent saved-file QA passed. The original watch remains paused; this follow-up is not another scheduled sample.

Saved LG27 link-up at 01:17:54.097123 CEST precedes HPD removal at 05:17:35.648549 by **3h59m41.551426s**, 18.448574 seconds short of four hours. Wall and monotonic deltas agree within one microsecond. SMC electrical messages precede FIFO in both the manual-swap and overnight sequences. Thus FIFO is not the first retained cross-subsystem event. The SMC codes are not decoded or port-attributed; their order does not establish electrical or PD causality. Monitor power-on and last-button times were not measured.

This makes monitor-side Automatic Standby a concrete hypothesis. LG's [27UD88 manual](https://www.lg.com/us/support/products/documents/27MU88-W%20Owners%20Manual.pdf), despite the URL filename, documents a four-hour auto-off default for Europe/ErP versions and selectable standby timers. Its short joystick press powers on the monitor. This is an example USB-C model, **not identification of David's LG27**. LG's [general auto-off guide](https://www.lg.com/us/support/help-library/lg-monitor-how-to-schedule-the-auto-off-feature-CT30017684-20153185242484) gives Settings → General → Automatic Standby and warns that menus vary. No cited source proves that this unknown model removes USB-PD on standby. The exact model, enabled timer and timer start remain unknown; a driver or electrical cause is not excluded.

Next manual discriminator: keep USB-C and MagSafe connected; briefly press the monitor joystick once, without holding, resetting or switching inputs. Report whether video returns and the action time. If its menu opens, read the exact model and Automatic Standby value without changing it. An unlit LED alone is not proof of power-off. Recovery would support monitor power-state involvement, not prove timer causality. The agent can capture the follow-up without another routine permission request. No new image, driver patch or reboot is justified by this clue. Monitor setting changes and any later stability watch follow the reported result, one variable at a time. Earlier startup, cable-compatibility, USB-hub and crash-guard issues remain separate and unresolved.
