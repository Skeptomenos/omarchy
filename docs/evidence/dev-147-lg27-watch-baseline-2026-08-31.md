# DEV-147 — LG27 observation baseline, 2026-08-31

Scope: David reports manually switching from LG35 to LG27, seeing an image, and a healthy internal screen/responsive system. He requests checks about every ten minutes and continued offline work. This is a new observation baseline, not an agent-performed cable test or proof of long-term stability.

## Baseline result

The read-only snapshot at 01:20:20 CEST is in the same boot as the [LG35 recovery](dev-147-w-recovery-after-pr582-2026-08-31.md). Packaged AppleDRM and the working TIPD notes remain unchanged. Both DRM connectors are connected/enabled and compositor DPMS is on:

| Output / supply | Saved state |
|---|---|
| LG27 DP-1 | 3840×2160 / 59.997 Hz |
| Internal eDP-1 | 2560×1664 / 60 Hz |
| Monitor-port and MagSafe | Both PD supplies online |
| Battery | 100%, Full; current 0 |

The 933,007-byte journal has 1,248 valid same-boot JSON records and unique cursors. Its first 1,094 parsed records equal the earlier recovery capture; 154 were added. Before/after boot identities match. Journal/compositor exits are 0 with empty stderr. Independent saved-file QA verifies state, cursor, identities and private file permissions. Journal SHA-256: `dee8d879fc180a66046cc7c53b199568f0e736cbe53ffb30a0321a7909a178e3`.

The added interval has one external FIFO error at about 263.446 s, a disconnect, then DPTX connect at about 268.124 s and 16 modes at about 270.354 s. These are recorded around the user's monitor change; exact physical action times were not measured. Preserve the FIFO diagnostic without calling it harmless or a spontaneous recurrence. Final 4K60 output works by both user report and software state.

## Scheduled observation

The same-task heartbeat **Observe LG27 display every 10 minutes** was created ACTIVE. Saved scheduler configuration confirms a ten-minute interval and this task as its target. Its baseline/cursor and fixed procedure remain private; DEV-147 holds their paths. No scheduled observation has yet been claimed by this creation record.

Each wake permits one bounded, unprivileged snapshot of known display/compositor, boot/module, standard power-supply status and the new kernel-journal interval only. It records changes and gaps. It must not read partner `usb_mode`, run old helpers, change hardware/configuration or repair a loss. A lost external output, identity change, new fault/power concern or timeout pauses the watch after preserving that sample, pending David. Ordinary DPMS blanking is not automatically a driver failure.

The watch does not change sleep/idle settings. Local tasks need the machine available and app running; unavailable intervals are gaps, not successful uptime. See the [official scheduling requirements](https://learn.chatgpt.com/docs/automations?surface=app). Software state cannot guarantee visible pixels or measure which supply carries current. Both PD supplies online is not sustained monitor-only charging proof.

No agent ran sudo, reboot, driver/mode/cable operations, probes, new builds or test suites. Only private evidence/scheduler state and project records changed. Existing boot defaults, images, backups and runtime configuration remain intact. The [main plan](../plans/dev-147-m2-displayport.md#passive-lg27-observation-living) owns continuation and stop conditions.
