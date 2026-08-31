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

## Addendum — unchanged setup and PM check, 2026-08-31

David now confirms no changes, both physical images still working, and a responsive system. This resolves the earlier physical-context question by user testimony. The USB-data loss was uncommanded on that reported setup. It does not establish the initiating cause.

The 11:38:35 CEST capture is on the same W boot, with matching kernel/packages and module notes. Both native outputs, both PD supplies and battery Full/100% remain present. Only the two root USB devices remain. Fixed root-port/configuration reads followed at about 11:40; a final boot marker at 11:43:15 still matches. These are separate snapshots, not continuous observation.

| Object | Saved power-management state |
|---|---|
| DWC3 `502280000.usb` and xHCI `xhci-hcd.3.auto` | `control=on`, `runtime_status=active`, `runtime_suspended_time=0` |
| USB2 and USB3 roots | `control=auto`, `runtime_status=suspended`, autosuspend delay 0 |
| Both upstream root ports | Active, zero suspended time, `pm_qos_no_power_off=1`, over-current count 0 |
| ATC PHY | Runtime PM `unsupported`; its autosuspend-delay read returned EIO |
| Removed LG hub and controls | No current device objects; their earlier PM and USB2 hardware-LPM state are unknown |

[Kernel PM documentation](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/Documentation/ABI/testing/sysfs-devices-power) defines these residency counters as cumulative time, not event timestamps. There is no recorded runtime-suspend residency for the surviving host controllers or root ports. This does not exclude link-level PM, a removed child's earlier state, or electrical/firmware faults. Suspended empty root hubs are consistent with normal USB PM; the snapshot does not make suspension the cause.

There is also a configuration mismatch. `modinfo -F filename usbcore` returns `(builtin)`. Runtime `usbcore.autosuspend` is `2`, while `/etc/modprobe.d/omarchy-usb-autosuspend.conf` contains `options usbcore autosuspend=-1`. No `usbcore.*` argument is in the captured command line. [Linux USB PM documentation](https://docs.kernel.org/driver-api/usb/power-management.html) specifies a boot argument for built-in usbcore, rather than a modprobe option. The intended global disable is not in effect here. This default governs new devices; it does not prove that the missing LG hub was suspended or that PM caused its failures. No setting was changed.

The new incremental journal has 85 unique, ordered records, 76,022 bytes, covering 11:30:16–11:38:20 CEST. No USB/display/DCP/TIPD/xHCI fault or transition matches the scoped filter. Journal SHA-256: `338346600f0d50aa3087e1874e206f736eaee7f29e8cf5fd55b92071378e3d92`.

All ten capture wrappers exited zero, but the PHY EIO above is a partial-read exception: the loop continued, so exit zero does not mean every attribute read passed. That unavailable value was not retried. Raw evidence, exact user testimony, final boot bracket and checksums remain private in DEV-147.

Independent saved-data and document review PASS: all 39 raw checksums match; boot, cursor and ordering checks agree across the three captures. USB-data readiness remains FAIL. No production source changed and no historical build/test suite was replayed.

### Next manual boundary

Use one attended reconnect to seek a healthy hub baseline, not a new boot or PM workaround. Keep MagSafe, lid open, the same monitor, cable, front/lower port and input settings; leave monitor USB-A ports empty. Disconnect USB-C at the Mac, wait about five seconds, then reconnect it once in the same orientation. Do not repeat if recovery fails. Stop and report loss of the internal display, responsiveness, power safety or external recovery.

After David reports the result, take a bounded passive snapshot of any returned hub/controls and their upstream PM state, then decide whether a short recurrence capture is useful. Keep the mouse, global PM changes, new images and upstream submissions on hold. The older four-hour standby case stays parked.
