# DEV-147 USB-1 reconnect evidence — 2026-08-27

> Public archival copy, prepared 2026-08-28. Actual boot IDs are redacted where present. Local evidence links are marked as private. Commit references identify the retained private branch unless they name upstream source. Recorded hashes and past QA results describe the private originals, not this edited export. Commands below are historical records, not instructions to run the public helpers.

**Host / scope:** `omarchy-air`, M2 J413/T8112, one monitor on front/lower USB-C `0-003f`.
**Approval:** David approved the bounded diagnostic, then reported one disconnect/reconnect and the physical result.
**Repo state:** `codex/dev-147-m2-dp-altmode`, source commit `02f1d4fc1` before this record.

This dated record owns this case's evidence. The [living plan](../plans/dev-147-m2-displayport.md) owns current status and next actions. It does not replace the [candidate-startup record](dev-147-one-boot-startup-2026-08-27.md).

## What happened

The 23:21 CEST preflight and 23:28 pre-action check found the same candidate boot/core/kernel, both native display modes, both PD sources online, battery 100% Full, and all 14 readable integrity pins matching. Only two USB root hubs were present. The two saved intervening windows contained 220 and 65 entries respectively, all audit or firewall messages. No new hardware/firmware event appeared in those windows.

David reported only another HDMI cable on the monitor, with no downstream USB device. The reviewed case kept MagSafe, HDMI, monitor input settings, lid, port, and orientation unchanged. It requested one USB-C disconnect at the laptop, a 10-second wait, one reconnect, and 30 seconds of observation. It allowed no retry, mode change, driver operation, or suspend.

David then reported that the internal screen stayed usable while USB-C was disconnected. The external image returned about 5 seconds after reconnect. No HDMI/input change was reported. The OSD input was not independently read; an HDMI picture alone is not proof of USB-C recovery. Linux's DPTX reconnect, HPD, and native modeset independently establish recovery of the USB-C display path.

The observed controller removal-to-registration interval was 31.875 seconds. The requested 10-second physical wait was not independently verified. Do not represent the requested timing as measured compliance.

## Result

**USB-1 functional recovery: PASS.** This is one user-performed reconnect, not a repeated-hotplug or startup-reliability result.

The 23:31:46 CEST live readback found:

| Check | Observed result |
|---|---|
| Boot / kernel | Same boot `REDACTED_CANDIDATE_BOOT`; `7.1.6-1-1-ARCH` |
| Loaded core | Candidate build ID `8fd9e3d39ee211f439471a812fb5eaa2622f7585` |
| External / internal | Connected and enabled at 3440×1440 / 99.982 Hz and 2560×1664 / 60 Hz |
| USB | Monitor USB2 hub `0bda:5411` and LG USB Controls `043e:9a39` enumerated under controller `502280000.usb` |
| Power | Monitor and MagSafe PD online; battery 100%, Full |
| Integrity | All 14 readable pins passed; kernel/packages and EDID unchanged |
| Kernel warning state | Taint stayed 4612; the complete captured interval had no new kernel WARN or fatal-pattern match |

The allowlisted sysfs reads, compositor query, package queries, build-ID read, and hash checks are retained in `live-readings.txt`. They did not read partner `usb_mode`. Protected stock initramfs/GRUB and staged-image bytes were not re-read. Their last protected verification remains David's staging PASS.

The all-priority `journalctl` query used the saved pre-action cursor, current boot ID, kernel transport, and a fixed end of `@1787866330` (23:32:10 CEST). Its exact command is in `result.json`. All 159 entries parsed; all 159 cursors were unique. Of these entries, 36 were audit and seven were firewall messages. Every message, priority, cursor, and realtime/monotonic timestamp was retained. Other journal metadata was omitted from the compact archive.

| Seconds since boot | Recorded event |
|---|---|
| 2602.872–2602.873 | One xHCI controller removal, logged for its two root buses |
| 2602.875 | DCP FIFO error interrupt `COMMON_INT_STA_3=0x00000010` |
| 2602.877–2602.918 | HPD removed, poweroff completed, DPTX disconnected |
| 2634.747–2634.758 | xHCI registered; DPTX connected |
| 2635.422 / 2635.810 | Monitor hub / LG controls enumerated |
| 2636.902–2637.228 | HPD asserted; native modeset requested and completed |

Native modeset completion was 2.470 seconds after the logged DPTX connect. That is not a measurement of human-visible recovery latency. Extra DPTX callbacks do not establish another physical reconnect.

The unplug-time FIFO error remains open. Reconnect also produced one recurrence each of the known EDT frequency, CAHandler version, and PMU `e00002d8` diagnostics. No new kernel WARN, fatal-pattern match, or USB error was found in the captured window. This is not a clean-firmware claim. The log does not reproduce the proposed appledrm clear-swap timeout followed by persistent atomic-commit `-EINVAL`; no such patch was added.

Independent saved-file review returned `VERDICT: PASS` for functional recovery and capture consistency, with the timing, firmware, and startup limits retained. The four-file `sha256sum -c SHA256SUMS` check returned four `OK` results.

### Retained evidence

Private preflight and released handoff (retained privately) remain unchanged. The new private result directory (retained privately) contains:

| File | SHA-256 |
|---|---|
| `result.json` | `710665806812251e32adcb067425f8cc4036ff1bdab073f9d0569452877a1031` |
| `kernel-after-reconnect.jsonl` | `d21c1187168b8411b1c813d307ef5e2c81f9f715b6f07099e05d447adb075d7d` |
| `live-readings.txt` | `9627f58fd9aed38279345d96d599c1a090b8c7d938f33fe2b21c2edb0f568bcd` |
| `linear-before-result.json` | `25450768a8bffecdd659436291c45a45881e640ceba512dc5b9e0931857e16c9` |

The Linear snapshot preserves the prior description and all 15 then-existing comments. Raw logs contain device identifiers and remain private. Earlier dated evidence was not rewritten.

## Rollback

No agent changed a boot file, driver, package, mode, cable, or power state during this validation. No reboot, suspend, privileged command, or cleanup ran. The user-performed reconnect recovered; no rollback was needed.

A normal unedited boot selects the stock driver but retains the candidate DTB. Full rollback remains the user-run `sudo bash /home/david/o/.dev147-stage/commands/02-rollback-dtb.sh`, followed only after PASS by a stock-initramfs reboot and the [plan's verification checks](../plans/dev-147-m2-displayport.md#gate-6--prove-full-rollback-then-retain-the-evidence). This is a recovery reference, not an instruction to reboot now. Keep both timestamped backups and the offline Mac restore bundle. Actual macOS restore execution remains untested.

## Open

- Automatic USB enumeration at attached startup remains unresolved. Reconnect recovery does not repair or retest startup. Earlier stock-driver startup showed the same initial absence, so candidate-specific causation is unproved.
- The earlier diagnostic-read WARN and the firmware findings remain open. Do not read partner `usb_mode` again.
- USB enumeration does not establish USB3 throughput or downstream-storage transfer. Full battery with two PD sources does not establish isolated USB-C active charging.
- Full Gate 4b, Gate 5 reliability cases, full rollback proof, and permanent integration remain open.
- The next investigation is a read-only comparison of saved startup negotiation/controller initialization with reconnect, before a separately reviewed device or boot case. Do not repeat USB-1 or start mode/suspend testing from this record.
