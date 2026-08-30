# DEV-147 — working-driver recovery after PR582, 2026-08-31

Scope: one approved attended W recovery on the M2 J413 after [LG 27 and LG 35 failed on the candidate](dev-147-pr582-lg35-failure-2026-08-31.md). Source checkpoint before this record: `e5b5f8735840350ebac17d925d255cc06fae931f`.

## Result

David reports rebooting and LG 35 working. A bounded read-only snapshot at 01:14:59 CEST corroborates external video recovery. Both DRM connectors are connected/enabled and both compositor outputs are active:

| Check | Observed result |
|---|---|
| External DP-1 | 3440×1440 / 99.982 Hz, DPMS on |
| Internal eDP-1 | 2560×1664 / 60 Hz, DPMS on |
| Kernel | `7.1.6-1-1-ARCH` |
| AppleDRM build ID | `dd5e291114047bb4d7c83a529cddb4f4ac9292d7`, matching the installed packaged module's note |
| `tps6598x_core` build ID | `8fd9e3d39ee211f439471a812fb5eaa2622f7585`, matching the earlier working core |
| Monitor-port / MagSafe supplies | Both report online with PD selected |
| Battery | 100%, Full; current 0 |

The PR582 candidate AppleDRM and T1 diagnostic core are no longer loaded. This is consistent with the intended `initramfs-linux-asahi-dpalt.img` selection. David did not restate the exact filename, and shared module identities are not whole-image proof. A fresh physical internal-screen/responsiveness confirmation was requested; the captured software state alone does not replace it.

## Saved evidence

The journal and compositor reads exited 0 with empty stderr. All 1,094 valid JSON journal records and distinct cursors belong to one new boot, different from the failed candidate boot; before/after boot IDs match. Records span 1.917652–90.383117 seconds. Independent saved-file QA passed for identities, capture integrity, display/power state and the scoped log interpretation. Raw logs remain private. Journal size: 804,810 bytes. SHA-256: `0ed7e4b01be09b62a25e04d9e8ca6f67d04c4df698026447b694d9412149a9c9`.

External DCP connects at about 4.875 seconds and announces connected state with 14 modes at about 7.079 seconds. The final compositor snapshot has the native LG 35 mode above. No relevant clear-swap timeout, explicit coprocessor crash, kernel WARNING/BUG/panic, DART/IOMMU fault or controller event-read error was found in this captured interval. Probe deferrals and known PMU/frequency firmware errors remain; this is not a clean-firmware or long-term reliability claim. No T1 markers are expected from the working, uninstrumented core.

Reads used bounded GNU module-note/DRM/power-supply attributes, `hyprctl -j monitors all`, and time/file-size-limited `journalctl -b 0 -k --no-pager -o json`. `readelf -n` checked the installed AppleDRM note; `jq`, `cmp` and `sha256sum` checked saved files. No old helper, suite, unsafe partner `usb_mode` read, sudo, probe or live driver/mode operation ran. No runtime or boot file changed.

## Meaning and next boundary

Functional LG 35 recovery is established; the candidate configuration remains a failed trial. W is not the matched PR582 control: at least AppleDRM and TIPD identities change, and reboot resets state. This result does not identify the responsible code change or validate timeout recovery. Physical cable sameness was not freshly confirmed. USB data and sustained monitor-only charging were not tested.

The W recovery handoff is consumed. Preserve the working setup with MagSafe and both failed snapshots; no additional reboot, reconnect or device test is released. Next, compare the saved working/candidate startup and image differences offline before proposing any new attended test. Do not rebuild or replay accepted checks without a concrete reason.

Defaults, all images and backups remain unchanged. W/default retain the prototype DTB, so this is not full stock rollback. LG 27 recovery, sustained power, USB data, sleep/reliability, permanent integration and upstream submission remain open.
