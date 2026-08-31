# LG27 USB-data loss after successful W startup — 2026-08-31

Result: the monitor hub and LG controls are absent in the 11:29:19 CEST snapshot. Both native display outputs and both PD sources remain active. Hold the proposed mouse test. This does not erase the [successful startup](dev-147-w-lg27-startup-2026-08-31.md).

## Saved observations

The before/after boot IDs match the earlier W capture. Kernel/package versions and loaded AppleDRM/TIPD note bytes also match. No new boot or driver selection is inferred.

| Time, CEST | Recorded event |
|---|---|
| Earlier startup | Hub `0bda:5411` and controls `043e:9a39` enumerate; both physical images reported working |
| 11:19:48 | Hub and controls disconnect |
| 11:19:49 | Both enumerate again as new device numbers |
| 11:24:22 | Hub and controls disconnect again; descriptor/configuration reads fail with `-71` |
| 11:24:23–25 | Kernel retries fail, including setup-address requests; this is automatic USB handling, not an agent recovery action |
| 11:29:19 | Only root hubs `1d6b:0002` and `1d6b:0003` are present |

The final compositor snapshot has eDP-1 at 2560×1664/60 Hz and DP-1 at 3840×2160/59.997 Hz, both enabled with DPMS on. MagSafe `0-003a` and monitor `0-003f` report PD online; the battery is Full/100%. These are point-in-time readings, not proof of uninterrupted visible video or sustained charging.

All six bounded capture commands exited zero with empty stderr. The incremental all-priority kernel journal contains 163 unique, ordered records, 139,851 bytes, on the same boot. It continues after the previous cursor with no overlap. Monotonic coverage is 360.866030–1125.708138 seconds. Six USB messages contain `-71`. No DCP/HPD, xHCI-controller teardown, TIPD or FIFO message accompanies these events in the saved increment.

Journal SHA-256: `d2144ec9984f499a7fc080a4f67d71c1a1fad061aa759c4bff981bbb93e85f4f`.

Independent saved-evidence QA PASS: note-byte identity, all six exits, boot/cursor metadata, journal continuity, both disconnect sequences and final display/power/USB state agree. The first new journal sequence is exactly the prior last sequence plus one. USB-data readiness itself is FAIL, not a passing mouse test.

## Interpretation and limits

This is downstream USB-data loss, not the earlier absent-video/low-HPD candidate failure or evidence that the whole USB-C connection lost power. The earlier first-probe ordering lead does not by itself explain loss after successful enumeration. No firmware, driver, cable, monitor or power-management cause is established.

The installed errno header maps 71 to `EPROTO`. [Linux USB error documentation](https://docs.kernel.org/driver-api/usb/error-codes.html) describes several possible transfer failures under that status; it does not identify a faulty cable by itself. The cable's prior success on other devices remains relevant.

At this checkpoint, David has not yet said whether he changed cables, monitor inputs/settings or downstream USB devices between startup and these events. The events cannot yet be called spontaneous. The earlier four-hour display/PD standby hypothesis is a separate incident and does not explain this shorter USB-only sequence by itself.

Raw boot IDs, serials, audit/network records and capture receipts remain private. Their location is recorded in DEV-147. Capture commands were ordinary read-only metadata and bounded journal queries. No sudo, reboot, tracing, driver operation, USB reset, reconnect or device insertion was performed by this task.

## Next boundary

Preserve the working display, MagSafe, cables and evidence. Obtain the physical-change history before selecting a recovery or controlled test. Do not add the mouse, retry a boot image, disable power management or rebuild a driver from this error code alone. DEV-162 remains separate.
