# DEV-147 one-time candidate startup evidence — 2026-08-27

> Public archival copy, prepared 2026-08-28. Actual boot IDs are redacted where present. Local evidence links are marked as private. Commit references identify the retained private branch unless they name upstream source. Recorded hashes and past QA results describe the private originals, not this edited export. Commands below are historical records, not instructions to run the public helpers.

**Host / scope:** `omarchy-air`, M2 J413/T8112. User-selected startup; agent validation and documentation only.
**Approval:** David reported completing the clarified steps and rebooting, with images on both screens. His earlier request covers retaining the trial history and reconciling the plan.
**Repo state:** `194a1c4b64d606530e4b6cb6e22e36582f806836` before this checkpoint. Feature branch `codex/dev-147-m2-dp-altmode`; runtime remains `/home/david/o-live`.

## What happened

David completed the clarified one-time GRUB edit. At 22:49:52 CEST, `uptime -s` reported `2026-08-27 22:47:00`. The new boot ID is `REDACTED_CANDIDATE_BOOT`. He confirmed physical images on the built-in and external screens. This is a restart, not a controlled cold power-on.

The loaded candidate build note and its early kernel load support the reported selection. No agent performed a live swap or selected a boot entry. The exact alternate initramfs selection is user-reported; its root-only staged contents were not freshly read. The earlier [stock-driver boot and rejected Bash command](dev-147-stock-driver-boot-2026-08-27.md) remain separate history, not a candidate startup failure.

Agents ran read-only system commands. One status read triggered the kernel warning documented below. No privileged command, cable action, display-mode change, suspend, driver operation, package update, boot-file change, or cleanup ran during this validation.

## Result

Display startup PASS for one candidate restart. Overall Gate 4b acceptance remains HOLD. The monitor's USB devices are absent, and the later diagnostic warning needs separate follow-up. This is not a full startup, reliability, clean-kernel, rollback, or release pass.

| Check | Observed result |
|---|---|
| `uname -r`; package query | `7.1.6-1-1-ARCH`; linux-asahi `7.1.6.asahi1-1`, m1n1 `1.6.1-1`, Mesa `26.1.8-1`, OpenSSL `3.6.4-1`. No drift from staging. |
| Loaded core GNU build note | Candidate `8fd9e3d39ee211f439471a812fb5eaa2622f7585`; module taint `O`. Kernel log records its out-of-tree load at 1.841700 seconds. |
| DRM sysfs and Hyprland output | Both outputs connected/enabled, DPMS on. Internal `2560×1664 @ 60 Hz`; external `3440×1440 @ 99.982 Hz`; scale 1.6. David confirms both physical images. |
| External EDID | 256 bytes; SHA-256 `a7c65e10b79718d46379d7c46e4239283ea2ab09e897f6467e3ad5d22d9809e6`, matching Gate 3. |
| USB sysfs inventory | Only root hubs `1d6b:0002` and `1d6b:0003`. Monitor hub and LG controls are absent. Front `0-003f` reports host data role and sink power role. |
| Power-supply sysfs | Monitor `0-003f` and MagSafe `0-003a` both online with USB-PD. Battery 100%, Full. This is power availability, not an isolated USB-C active-charge test. |
| `sha256sum` | All 14 readable pins match: boot and backups, kernels, packaged DTB/core, candidate module/image, recovery files, and external EDID. |
| `stat` of staged image | Root-owned 0600, 19,184,103 bytes, unchanged 21:58:23 CEST mtime. Protected stock initramfs/GRUB and staged contents were not freshly rehashed; their last protected verification is David's staging PASS. |

At 23:00:34 CEST, both DRM outputs were still connected/enabled. `/etc/default/update-m1n1` and the package-manager lock were absent at the 22:59 check. These observations do not guarantee future stability.

### Startup logs and firmware qualifications

The first capture contains all 1,085 available kernel journal entries at all priorities through 22:50:14 CEST. All parse and have unique cursors. Its recorded monotonic range is 1.831764–133.195516 seconds. The follow-up capture contains 137 later entries through 22:59:34 CEST: 90 audit entries, nine firewall entries, and a 38-entry diagnostic WARN trace. All parse and have unique cursors. Clock values are retained as observed; do not derive new boot-time claims from wall-clock differences.

- Five external `dp-xbar: -517` probe deferrals recover. External DCP binds at 3.120968 seconds and boots at 4.141568 seconds.
- Native external modesets complete at 7.258486 and 15.220933 seconds. A 1920×1080 startup transition lies between them. These were not controlled Gate 5 mode tests; their cause was not established.
- External firmware repeats the Gate 3 diagnostic classes: four frequency `EDT ERROR` messages, three CAHandler version messages, and three PMU `e00002d8` messages. Their operational impact remains open. Internal DCP also reports CAHandler and a different PMU code, `e00800d8`.
- No DCP/coprocessor crash, DART/IOMMU fault, kernel BUG/panic, or proposed appledrm clear-swap/atomic-failure sequence was found in these captures. The later status-read WARN is real. An AVD firmware-load `-2` also remains outside the external-DCP path. Do not call the whole kernel or firmware clean.

### USB comparison: missing enumeration, not an established new regression

Gate 3 (retained privately) recorded the monitor's USB2 hub and LG controls alongside working video. This startup has no downstream attach event. Drivers for the active front DWC3/xHCI controller and ATC PHY are present. Both root-hub downstream ports report not attached, with no overcurrent or disabled-port indication. `lsusb` is not installed; sysfs confirms this is real enumeration state, not a missing utility's display problem.

An earlier verified stock-driver boot, `REDACTED_STOCK_BOOT`, also started with only root hubs. Its controller was removed at about 30 seconds and registered again at 44.977145 seconds. Hub `0bda:5411` appeared at 45.628190 seconds; LG controls `043e:9a39` appeared at 46.009141 seconds. The trigger was not recorded as a controlled cable, role, or rescan action. Do not infer which action caused recovery.

The stock identity comes from the 22:21:40 saved check (retained privately): loaded and packaged build IDs both equal `73c3659d1653dd2508ae81147a5e5cd4c877a060`. That time falls within this boot's journal window, 22:17:51–22:44:11 CEST. The earlier JSON has no boot-ID field; this association is journal-window evidence. It is not a claim that this boot immediately preceded the current one.

USB startup acceptance remains open. Startup negotiation, controller/monitor state, and candidate interaction are not separated by this comparison. Do not fix the missing hub by installing a user-space utility or adding an unproved module preload.

### Diagnostic-read WARN: owned and bounded

At 22:53:29 CEST / 388.511 seconds, our USB-review subagent read partner `usb_mode` with `sed -n '1p'`. It read MagSafe `/sys/class/typec/port0-partner/usb_mode`, which returned empty, then monitor `/sys/class/typec/port2-partner/usb_mode`, which returned `usb4`. The journal records `sed/8340`, UID 1001, and `invalid sysfs_emit_at ... at:-1`. Its trace includes `usb_mode_show+0x90/0xc8 [typec]` on the sysfs read path.

The empty MagSafe path is the strongly supported trigger; the journal does not independently map that PID to an exact pathname. Installed-module disassembly shows the zero-length edge case: the formatter starts at zero and subtracts one before its final `sysfs_emit_at` call. If no mode bit produces output, that offset is -1. Its return offset matches the trace.

The loaded and packaged Type-C class module build ID is `62299e7994020ebac37890d9f101106ccd1f5639`. Installed, stock-extracted, and candidate-extracted `typec.ko` all have SHA-256 `24882742cef109bfbfd3f6fe695909fee770c9da31571fbda93b437967e9e43c`. This is shared formatter code, not the changed `tps6598x-core.ko`. No local C source was available; this conclusion uses the installed binary and saved image extracts.

Global kernel taint rose from 4100 to 4612, adding WARN bit 512. USB absence was observed before this read. The diagnostic did not establish the cause of missing USB enumeration. Neither `usb_mode` read was repeated; no patch or driver operation followed. Keep this attribute out of further prototype diagnostics. Do not suppress or mislabel the warning as startup firmware output.

### Retained evidence and validation limits

The private capture directory (retained privately) is mode 0700. It contains the complete journal windows, USB/display/power readings, binary audit, stock comparison, 14-pin integrity manifest, and a 13-file hash manifest (retained privately). Raw serial, audit, and network data stay private.

- Normalized report (retained privately): SHA-256 `014e0708a75fa887bd68162594f38072988e3bf0c6bb4268432c9e171160c692`.
- Initial full journal (retained privately): SHA-256 `7ba8a86bec724d897c49904c08d28ee862f581078c301c86865c4566bf732e09`.
- Later journal, including the WARN (retained privately): SHA-256 `429e1f38576df92e686b54d8e4986ff681a5f9b489c5a6f85e54e7af44090756`.
- Pre-update Linear snapshot (retained privately): SHA-256 `701006771f902659c94d015c7b9f588160ebb3b6d927d4db1182d4bdc38f759c`. It preserves the description and all 13 existing comments.

Large single-call journal reads exceeded output limits. They were rejected as incomplete and replaced by fixed-window captures checked for JSON validity and cursor uniqueness. The first hyphenated boot-ID selector returned no entries; the corrected 32-hex selector returned the recorded boot. No truncated or empty result was presented as a complete log. `lsusb` failures led to sysfs checks, not a package installation.

The five earlier tracked evidence records and the Gate 3 image record retain their hashes. No source, test, Gates 0–3 script, or old artifact was changed. The living plan, guide, and stage notes now distinguish display success from full acceptance. The prior five aggregate-suite failures and six build warnings remain open. No aggregate or device test suite was rerun for this documentation checkpoint.

Independent documentation QA: PASS. All 39 local links, three anchors, and 15 stage-note pointers resolve. Six reviewed files have no trailing whitespace; `git diff --check` passes. The 13-file evidence manifest passes. QA independently confirmed the journal counts, 1,222 unique cursors, diagnostic counts, stock-window association, and WARN attribution limits. This is documentation/evidence validation, not hardware acceptance or release approval.

Linear readback also passes: the current description matches the submitted update, status remains In Progress, all 13 prior comment IDs and bodies are unchanged, and exactly one [startup checkpoint](https://linear.app/helmus/issue/DEV-147/usb-c-displayport-external-monitor-unavailable-on-m2-macbook-air#comment-2632b8eb) was added. The issue now has 14 comments. The private directory retains the post-update snapshot and readback result.

## Rollback

No new boot-file mutation needs reversal. A later normal, unedited boot selects the stock driver; it does not restore the prototype DTB or prove full rollback. Use the [existing rollback gate](../plans/dev-147-m2-displayport.md#gate-6--prove-full-rollback-then-retain-the-evidence) if recovery is needed. Do not reboot merely to clear taint or repeat a live module swap. Keep both backups and all evidence. The existing offline Mac recovery bundle remains available but untested in macOS.

## Open

Keep the working session's cables unchanged. Do not start mode, routine hotplug, cold-start, or suspend tests. Next, review one attended USB diagnostic case on the same cable and port, with before/after evidence, a single action, stop conditions, and rollback. The review must exclude the warning-triggering status read. Do not add a kernel patch or permanent installation to bypass the hold.

The [living plan](../plans/dev-147-m2-displayport.md) owns next actions. Gate 4b USB acceptance, firmware impact, isolated USB-C charging, Gate 5 behavior, full rollback, and permanent integration remain open.
