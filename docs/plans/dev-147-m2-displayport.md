# DEV-147 — contained M2 DisplayPort prototype

Updated: 2026-08-29, with [A0 findings](../research/dev-147-hpd-startup-2026-08-29.md) and [T1 selected after A1 review](dev-147-usb-startup-diagnostic.md#a1-selection--t1-tipd-sender-diagnostic-living) for offline A2–A4 under the [autonomous offline next-test package](#autonomous-offline-goal--next-test-package-living). The goal ends before the first manual staging/review boundary; it does not authorize live testing. The [latest functional display recovery](../evidence/dev-147-w-recovery-after-e-2026-08-28.md) retains its filename qualification: shared W/E IDs do not independently prove W startup. That handoff is consumed. The [confirmed E failure](../evidence/dev-147-c4-selection-confirmation-2026-08-28.md) and D3 external-display FAIL / measurement INCONCLUSIVE remain separate, with causes unknown. The last captured USB state has root hubs only; firmware questions and full Gate 4b/USB acceptance stay HOLD. David's USB-C-only charging report is recorded below, separate from USB data acceptance. [C3 staging](../evidence/dev-147-usbearly-staging-2026-08-28.md) remains consumed with qualified root-private provenance. The login-focus issue stays outside this goal. [Linear DEV-147](https://linear.app/helmus/issue/DEV-147/usb-c-displayport-external-monitor-unavailable-on-m2-macbook-air) owns issue status and dated checkpoints.

Public-copy boundary: source and reviewed notes were published on `codex/dev-147-m2-dp-altmode-public` at `c781312d1221da675e686b318a30ddd10d9ef3c4`; remote readback matched. The original branch and its 14 local commits remain private and unchanged. Boot IDs are redacted here; raw Linear exports and machine records are excluded. The older public boot/staging helpers have invalid machine identifiers and are not the byte-identical, tested operational copies. The later C2 exports preserve exact workload bytes but require private sandbox inputs. Do not run any of these helpers live. See the [source archive](../../dev/apple-dp-altmode/usbdiag/README.md) and [dated checkpoint](../evidence/dev-147-public-source-checkpoint-2026-08-28.md).

The first live test produced a working external image. This is not a permanent fix or a reliability result. See the [dated history and evidence](../evidence/dev-147-prototype-history-2026-08-27.md) for what happened, including failed prerequisites and corrected advice.

Gate 4a is complete. David ran the reviewed staging helper and supplied `STAGING ONLY PASS` for `/boot/initramfs-linux-asahi-dpalt.img`. He then completed the clarified one-time GRUB selection and reported both screens working after reboot. The loaded candidate build ID and early boot log verify that earlier startup. Its external display was at 3440×1440 / 99.982 Hz; the internal panel was at 2560×1664 / 60 Hz. These describe that earlier boot; D3 failure and recovery are separate records. Normal boot selection remains unchanged. Keep the [preparation evidence](../evidence/dev-147-one-boot-preparation-2026-08-27.md), [staging checkpoint](../evidence/dev-147-one-boot-staging-2026-08-27.md), and [startup evidence](../evidence/dev-147-one-boot-startup-2026-08-27.md). This was one restart, not a cold-start or reliability pass.

The monitor's USB hub and LG controls were absent at the earlier working-image startup, although video and USB-PD were present. USB-1 restored those devices without a driver change. A stock-driver boot also began with only root hubs, so a candidate-specific regression is not established. Our earlier read of a Type-C partner's `usb_mode` status triggered a kernel WARN in `usb_mode_show`; do not repeat that read. The reconnect added one firmware FIFO error at unplug and repeated the three known firmware diagnostics. No new kernel WARN or fatal event was found in that captured interval. The [dated investigation](../research/dev-147-usb-startup-2026-08-28.md) owns that comparison. The [diagnostic subplan](dev-147-usb-startup-diagnostic.md), [D3 failure record](../evidence/dev-147-usbdiag-startup-failure-2026-08-28.md), and [recovery record](../evidence/dev-147-dp-recovery-2026-08-28.md) keep the later cases separate. Earlier permission to disconnect during offline work is not a confirmed action or test. The latest intended W recovery has both native outputs but only root USB hubs; monitor hub and controls remain absent in that capture. Preserve the working setup. Newly reviewed isolated offline builds/tests are authorized by the goal below; live helper execution, old-helper replay, reboot, sudo, reconnect, USB-device test, live swap, mode change, suspend, and greeter testing are not. Do not repeat completed staging or run public archival helpers live.

The earlier 22:18 stock-driver boot and rejected Bash `initrd` command remain in the [handoff correction](../evidence/dev-147-stock-driver-boot-2026-08-27.md). That was not a candidate startup failure. No agent ran a privileged command, reboot, cable action, driver operation, or package change during this validation. The status read did have the recorded WARN/taint side effect.

## Scope and safety boundaries

- One machine: `omarchy-air`, Apple MacBook Air M2 J413/T8112, kernel `7.1.6-1-1-ARCH`.
- One display path: the known working monitor and cable on the front/lower left USB-C port, controller `0-003f`, ATC PHY1, mux index 2. The rear/upper port, `0-0038`, is not routed by this prototype. Do not add a dock, MST device, or another display.
- Keep the internal screen usable and the lid open. No clamshell testing.
- Keep the packaged kernel, DTB, Type-C module, stock initramfs, GRUB configuration, and `/etc/default/update-m1n1` unchanged. The last path must remain absent. Do not run `update-m1n1` or `grub-mkconfig`.
- Do not edit or switch `/home/david/o-live`. Current public source and documentation are on `codex/dev-147-m2-dp-altmode-public`. The original `codex/dev-147-m2-dp-altmode` branch at `/home/david/o/.dev147-stage/prototype` remains a private archive with the tested operational helpers. Keep artifacts and raw evidence private in the existing persistent stage. Use fresh private continuation directories for D1 outputs. Do not regenerate the old stage or replay Gates 0–3.
- David runs every privileged command. Before a future mutation, review its exact command, rollback, file targets, and evidence checks with him. He must be present, with saved work and battery strictly above 50%.
- Recheck the running and installed kernel, boot-chain and backup hashes before a new gate. Stop on kernel/package drift or a package update during testing. Never load this binary into another kernel.
- Normal macOS and Recovery access are user-attested. David chose not to rehearse recovery. The offline Mac restore bundle was verified on EFI, but has not run in macOS. Do not call that recovery path runtime-tested.

## Progress (LIVING)

| Gate | Current state | Meaning |
|---|---|---|
| 0 — baseline and backups | Complete | Backup set `20260826T222113Z` exists on EFI and in the persistent stage. The recovery rehearsal was not performed. |
| 1 — minimal build and static review | Complete, with QA qualifications | Pinned private headers and minimal M2 DT/HPD changes produced verified artifacts. The prior aggregate suite was not all green; see history. |
| 2 — DTB activation and boot | Complete | Patched DTB booted with the stock module/initramfs. Internal screen stayed healthy; external connector appeared but was disconnected. |
| 3 — live module test | Functional success only | One real swap produced native external video. The earlier invocation stopped at the cable guard before any swap. Do not repeat this gate. |
| 4a — isolated image preparation, review, and staging | Complete | David's reviewed helper reached final PASS after protected post-checks and image verification. The same staged image was subsequently selected for Gate 4b. Root-only contents/logs were not re-read by the agent. |
| 4b — one-time startup test | Display startup/recovery PASS; overall acceptance HOLD | The working-image boots have both native displays. D3 lost external video; one separate recovery restored it. Automatic USB enumeration, firmware findings, reliability, and full rollback remain open. |
| USB-1 — one attended reconnect | Functional PASS | Internal screen stayed usable; external image returned in about 5 seconds. Hub and LG controls enumerated. One unplug-time FIFO error and the known firmware diagnostics remain recorded. Do not repeat this case. |
| USB startup investigation | Read-only comparison complete; runtime question open | Stock USB-glue first-probe ordering defect confirmed in source and corroborated by the binary. D3 produced no valid trace. Runtime sequence and hardware causality remain unmeasured. |
| USB diagnostic D0 / D1 | D0 reviewed; offline D1 complete | 59 trace, 58 archive, and 55 assembly tests pass. Private builds, import/logging checks, no-change controls, and the 413-command private image verification pass. All 200 modules resolve without loading. |
| USB diagnostic D2 / D3 | D2 staging PASS; D3 external-display FAIL / measurement INCONCLUSIVE | D3 loaded IDs match, but all diagnostic markers are absent because of the frozen v1 target-name guard defect. The D3 handoff is consumed; no retry. |
| Recovery after D3 | One functional display PASS | Both native displays and responsiveness are restored with packaged USB drivers and the working patched DP core. Only root hubs enumerate. Handoff consumed; not full DTB rollback or a diagnostic fix. |
| Correction design C0 | Complete; retained design | Exact referenced-node guard, production-path regression tests, and W/E/B/G comparison design remain the contract in the diagnostic subplan. C0 itself added no executed test or hardware result. |
| Correction C1 | Focused QA and independent source/test review PASS | Genuine two-target generation-zero RED precedes the v2 correction. 10 target tests / 54 fixture executions, 65 trace tests, and format/cap checks pass. No module, image, or hardware test. |
| Preparation C2 | Offline artifact checks, independent review, and seal PASS | Fresh unmodified/v2 module pairs and only E are verified. E contains packaged DWC3 and unchanged ATC; no diagnostic module. B/G images remain unprepared. The 2,270-file checkpoint stays sealed. |
| C3 — E-only staging | Complete; user-run staging PASS | All 41 visible initial-preflight rows match. David's complete final report evidences the later private checks; independent readable hashes and metadata agree. E is staged. Handoff consumed; no retry. |
| C4 — E case | External-display FAIL; E selection confirmed | User confirmation plus saved boot capture establish the result, not shared IDs alone. Cause unknown; handoff consumed and no retry. |
| Recovery after E | Functional display recovery observed; handoff consumed | Fresh boot has both native outputs after the intended W handoff. Filename was not restated, so shared IDs do not prove W artifact startup. Root hubs only; USB acceptance HOLD. |
| Autonomous offline goal | A2 E-control execution boundary GREEN; T1 implementation still pending | The [zero-child execution boundary](../evidence/dev-147-e-execution-boundary-2026-08-29.md) retains exact RED, one stopped GREEN, and corrected 3/3 GREEN with zero workload children. One separately reviewed 424-child offline E control is next. No T1 source, binary, image, live change, or hardware PASS yet. |
| Source publication checkpoint | Published and verified | `c781312d1` on the clean public branch contains source, fixtures, plans, and reviewed notes. Raw private records and the original local history remain private. This is not a build or hardware acceptance pass. |
| 5 — controlled behavior tests | Pending; held at Gate 4b | Refresh-rate, repeated hotplug, cold-start, and suspend reliability are unproved. Startup modesets do not count as controlled mode tests. |
| 6 — full rollback proof | Pending | Reboot alone does not restore the original DTB. |
| Permanent integration | Separate future design and approval | Not part of the completed prototype or this documentation update. |

Historical checkpoint, 2026-08-27 at 23:31 CEST: that boot used the candidate core and DTB. Both DRM outputs were connected/enabled at their native modes; monitor USB hub/controls were present. Battery was 100%, Full; monitor and MagSafe reported USB-PD online. This did not prove USB-C-only active charging. Taint was 4612 from the earlier diagnostic WARN. Fourteen readable integrity pins passed. Protected stock initramfs/GRUB and staged-image contents were not freshly reread; their validation remained David's staging PASS. Do not carry these output or taint values into later boots. The [D3 failure](../evidence/dev-147-usbdiag-startup-failure-2026-08-28.md) and [recovery](../evidence/dev-147-dp-recovery-2026-08-28.md) records own those separate measurements.

## Gate 4a — prepare and review a separate one-boot image

The [offline helper](../../dev/apple-dp-altmode/prepare-one-boot-initramfs.sh) and [literal configuration](../../dev/apple-dp-altmode/one-boot-mkinitcpio.conf) passed scoped QA and independent review. They use the installed `mkinitcpio 41.1`, a full private module-tree copy, an explicit kernel version and output, packaged hooks, and `--nopost`. The private configuration preserves the current effective host hooks, including Asahi vendor firmware. Do not use a preset, UKI generation, a new early preload, or a custom hook. See the [installed-interface reference](https://man.archlinux.org/man/mkinitcpio.8.en).

The one generated image is initramfs-linux-asahi-dpalt.img (retained privately), SHA-256 `ae8f1ed7f4f258f89931209cd7de6030be9f6875372d7329151b822a6ba2281f`, 19,184,103 bytes. Its local marker says `BUILD CHECKS ONLY`. The build log retains six warnings. A successful build is not a clean-firmware or startup result.

David ran the [protected-stock reader](../../dev/apple-dp-altmode/read-protected-stock.sh). The private readback (retained privately) completed at 19:11:15 UTC. Stock initramfs and GRUB hashes matched Gate 0 before and after the read. No root extraction or privileged destination write occurred. Keep this archive private and do not rerun the reader into the same directory.

1. Recheck the exact kernel, artifact pins, active candidate `boot.bin`, both stock backups, and both EFI recovery files before staging. Gate 0 recorded stock `boot.bin`, initramfs, and GRUB; packaged DTB/core pins are separate. The new pre-Gate-4 kernel-image digest is `ee36d989d62f2dd498b818e15c2044350c79d814a2017ffca61fdc2ad1aa95b6`. Both the boot copy and package copy match the installed kernel package. This is new dated evidence, not a retrospective Gate 0 hash. All 1,987 package file digests passed; `pacman -Qkk` reported 11 timestamp-only differences in generated module indexes, so do not call its metadata check an unqualified pass. David performs protected hash reads; metadata is not a substitute.
2. Keep the reviewed installed-tool and configuration pins. `--moduleroot` expects a root containing `lib/modules/7.1.6-1-1-ARCH`. Explicit `--config` bypasses host drop-ins, so do not substitute the base configuration alone. The helper refuses drift and an existing output directory.
3. The separate module-root and image have already been built once. Their matching dependencies and candidate bytes are verified. Keep `/usr/lib/modules` unchanged. Do not rebuild this image, regenerate the old stage, or overwrite any existing artifact to repeat a completed check.
4. Both archives and the exact build command have been inspected. Candidate bytes/build ID, other modules, built-in dependencies, extracted index resolution, and vendor-firmware hooks passed static review. The full stock comparison is recorded below. These checks do not prove startup.
5. Independent review passed for the build, actual boot layout, one-time edit, and bounded staging-only helper. David then ran that exact helper successfully. No persistent entry or default change is allowed.
6. Completed: the supplied final PASS establishes successful user-run post-checks, including all protected input hashes and the new image's size/hash. Independent read-only metadata and readable-hash checks agree. The root-private logs remain unread by the agent; this distinction is recorded in the staging evidence. Preserve both backups and the offline recovery instructions. Do not rerun staging.

Exit met through reviewed preparation and David's successful staging validator: the separate image and one-time selection instructions passed review; protected files matched their pins; the staged image matched the reviewed size and hash. Building or staging the image is not a boot-test pass.

### Comparison result and completed staging

Both images contain the same 1,163 paths and 199 modules. Only the intended core differs among those modules; all seven module indexes match. The whole image has five byte changes: core, buildconfig, runtime config with duplicate HID preloads removed, and two verified OpenSSL 3.6.4 libraries. It also has six mode-only changes. The [dated evidence](../evidence/dev-147-one-boot-preparation-2026-08-27.md) explains each. OpenSSL remains a real startup-test variable because the retained encrypt hook can call cryptsetup.

Scoped tests and static content review passed. The aggregate suite still has five pre-existing failures; this is not a full-suite or release pass. Build warnings and prior firmware diagnostics remain open.

The [staging-only helper](../../dev/apple-dp-altmode/stage-one-boot-initramfs.sh) pins this exact image, its size, the kernel, protected stock files, active boot, both backups, both recovery bundles, and current OpenSSL inputs. It refuses an existing destination, including a symlink. It copies at most the pinned byte count into a new root-private directory, verifies it, then publishes with an atomic non-overwriting rename on the same filesystem. It never changes the stock image, GRUB, EFI mount, modules, or live displays. Failure retains its private directory and any partial image for inspection. No cleanup runs.

David completed this staging command and supplied its final PASS. The exact command and evidence provenance are in the [dated staging record](../evidence/dev-147-one-boot-staging-2026-08-27.md). Checks were retained in `/boot/.dev147-dpalt-stage.e5Cys4arMi`. The helper prints PASS only after its protected post-checks, final image verification, syncs, and completion marker. Do not rerun it: the destination now exists. Do not delete files or weaken a guard to repeat a completed step.

Independent checks at 22:00 CEST confirmed the destination is root-owned, mode `0600`, and 19,184,103 bytes; its log directory is root-owned, mode `0700`. The source image, active boot, both backups, recovery files, packaged DTB/core, and both kernel-image copies matched their pins. The agent could not read the root-only staged image, stock initramfs/GRUB, or retained logs. Their post-check result comes from David's successful validator output, not an independent re-read. No additional privileged readback is needed merely to repeat those completed checks.

Staging an unselected alternate image does not change normal startup. Its rollback is to leave it unselected. This does not undo the pre-existing prototype DTB. Keep all artifacts and both stock backups.

## Gate 4b — user-selected one-time startup test

David completed the one-time selection and reboot. Boot ID `REDACTED_CANDIDATE_BOOT` uses candidate build ID `8fd9e3d39ee211f439471a812fb5eaa2622f7585`. David confirmed a physical image on both screens. The full startup log shows external DCP binding, HPD, and native modesets. The [startup record](../evidence/dev-147-one-boot-startup-2026-08-27.md) owns the measurements, USB comparison, warning trace, and capture limits.

The startup USB criterion is still open. Only xHCI root hubs enumerated at candidate startup; Gate 3 had the monitor hub and LG controls. USB-1 later restored them in the same candidate boot. An earlier verified stock-driver boot initially had only root hubs too, then enumerated those devices after controller removal/re-registration. Its trigger is unknown. Do not assign the initial absence to the candidate without a controlled comparison. The diagnostic-read WARN happened after USB absence was already observed; it is not evidence that the read caused the missing enumeration.

Gate 4b acceptance exit remains unmet: both physical screens must work at startup with the verified candidate module, USB and charging must remain usable, and the captured logs and firmware findings must be reviewed. The earlier working-image boot passed the display part only. USB-1 restored USB after reconnect; automatic enumeration at attached startup remains unresolved. Today's recovery alone cannot meet this full exit or close the diagnostic-read and firmware findings.

David approved the bounded USB diagnostic and completed one disconnect/reconnect. He had reported only another HDMI cable, with no downstream USB device. Independent design and result reviews passed for this single functional case. Exclude partner `usb_mode` reads from diagnostics; retain their trace for separate investigation. That case authorized no kernel patch. The later D1 approval permits offline diagnostic instrumentation only, not a behavior fix or live kernel action. Gate 5 remains on hold until Gate 4b acceptance is resolved.

### USB-1 — one attended monitor reconnect, functional PASS

The [dated USB-1 record](../evidence/dev-147-usb-reconnect-2026-08-27.md) owns the preflight, physical report, event sequence, timing limits, and result. Preserve the preflight directory (retained privately) and result directory (retained privately). Earlier pending instructions are superseded by this completed checkpoint; do not replay them.

David reports that the internal screen stayed usable while disconnected and the external image returned in about 5 seconds after reconnect. Both native modes are restored. USB2 hub `0bda:5411` and LG controls `043e:9a39` now enumerate. Both PD sources remain online, with a full battery. The same boot/core/kernel and all 14 readable pins pass. No HDMI/input change was reported; the OSD input was not independently read. Linux DPTX and modeset events verify USB-C DP recovery independently of an HDMI picture.

All 159 entries after the pre-action cursor through 23:32:10 CEST were retained at every priority. The interval contains one FIFO error at unplug and one recurrence each of EDT, CAHandler, and PMU diagnostics. No new kernel WARN, fatal-pattern match, or USB error was found. This is not a clean-firmware result. Controller removal to registration spans 31.875 seconds; the requested 10-second physical wait was not independently verified. The logged native modeset finishes 2.470 seconds after DPTX connect; that is distinct from David's approximate visible recovery time.

USB-1 proves one functional recovery, not automatic USB enumeration at attached startup or Gate 5 reliability. The later offline D1 approval allows the monitor to be unplugged; this is not another hardware test. Recheck the actual setup before a future attended case. The saved-evidence comparison is now complete; use the findings below before designing any further case. Do not repeat USB-1 or reboot just to clear the old taint.

### USB startup investigation — completed

The [2026-08-28 investigation](../research/dev-147-usb-startup-2026-08-28.md) records the matched controller startup, missing downstream attachment, source/binary provenance, and remaining alternatives. The first USB2 HOST request in stock `dwc3-apple` precedes acquisition of its PHY handle. A later HCD path supplies a HOST setter, so this is a missed early configuration step, not proof that HOST is never set. It is the strongest lead, not a proven cause or tested fix. No change to the DP HPD patch or `appledrm` is justified by the present evidence.

The source review found no clear-swap-timeout/crashed-latch sequence in USB-1. Completed poweroff and the later modeset argue against that specific workaround. FIFO and the other firmware diagnostics remain open. Gate 4b acceptance and Gate 5 remain on hold; this investigation adds no hardware-test pass.

### USB startup diagnostic — D3 failed; measurement inconclusive

The [diagnostic subplan](dev-147-usb-startup-diagnostic.md) passed initial source/measurement, image/rollback, and safety review. D0's historical review is complete, but D3 exposed missed target-name semantic coverage. Both frozen v1 guards compare a leaf name with an absolute OF path and suppress all records. The [failure record](../evidence/dev-147-usbdiag-startup-failure-2026-08-28.md) owns that proof and boot result. The later, separately approved [C1 correction](../evidence/dev-147-usbdiag-c1-correction-2026-08-28.md) changes source only. It does not repair the archived D3 image or supply the still-unmeasured first-probe/retry sequence. No diagnostic retry or hardware causal claim follows.

The working image contains ATC but not DWC3 glue. The [verified private image](../evidence/dev-147-private-diagnostic-image-2026-08-28.md) retains all 199 original module paths, replaces ATC, and adds the diagnostic glue: 200 modules total. It replaces only the dependency and alias binary indexes, preserving the original symbol index, both builtin indexes, and every unrelated raw record. It is 19,647,739 bytes, SHA-256 `a11bf3a2bac1f105aa57b08ce9fad338c68882851247f7524d09f4b7c94188ca`. Adding glue can advance automatic probing; this is not a timing-matched A/B test. The [real control record](../evidence/dev-147-real-archive-controls-2026-08-28.md) retains the earlier exact reconstruction, 199 original lookups, and format/scratch-output corrections. Keep the working image and old helpers unchanged.

David approved D1: offline implementation, focused QA, independent review, and private module/image preparation in an actual unprivileged sandbox. Its recorded checks passed. The [D1 hold record](../evidence/dev-147-usbdiag-d1-hold-2026-08-28.md) retains the three earlier failed sandbox rounds; the [R4 record](../evidence/dev-147-sandbox-r4-2026-08-28.md) records the later probe PASS. The earlier missing errno remains unknown. Dated [source](../evidence/dev-147-public-source-checkpoint-2026-08-28.md), [trace/build](../evidence/dev-147-trace-and-module-builds-2026-08-28.md), [helper-QA](../evidence/dev-147-offline-helper-qa-2026-08-28.md), [real-control](../evidence/dev-147-real-archive-controls-2026-08-28.md), and [image](../evidence/dev-147-private-diagnostic-image-2026-08-28.md) records preserve failures and corrections. The [D2 preparation record](../evidence/dev-147-usbdiag-staging-helper-2026-08-28.md) preserves initial RED, environment-loop and EXIT-trap failures, corrections, and final independent 38-test PASS. David then ran the final private helper and supplied its complete PASS. The [D2 staging record](../evidence/dev-147-usbdiag-staging-2026-08-28.md) owns that result: all 40 reported pin records match, and image/log-directory metadata agree. Protected post-checks are evidenced by David's validated run, not an independent root-log read. The frozen D1/D2 preparation evidence and old helpers remain unchanged. The [boot-readiness record](../evidence/dev-147-usbdiag-boot-readiness-2026-08-28.md) is historical; its diagnostic handoff was consumed. David selected the distinct diagnostic image and reported external-display failure. Retain that image and the new evidence. Do not rerun staging or the diagnostic boot.

No diagnostic patch, binary, image, or staging helper was created during D0. Preserve the working `/boot/initramfs-linux-asahi-dpalt.img`, stock files, backups, current DP route, and recovery instructions. No live swap, sysfs write, register access, partner `usb_mode` read, automated device action, or mouse test. The design evidence archive (retained privately) retains the checks and review record. Full Gate 4b remains on hold.

<a id="current-recovery-handoff--previous-working-dp-image-living"></a>

### Recovery after D3 — completed; do not repeat

David completed the separately reviewed selection of `initramfs-linux-asahi-dpalt.img`, without `usbdiag1`. He reports an external image, normal built-in screen, and responsive system. Read-only loaded-ID and output checks confirm one functional display recovery. The [dated recovery record](../evidence/dev-147-dp-recovery-2026-08-28.md) owns the measurements and limits. The monitor hub and LG controls remain absent. This is not a diagnostic retry, reliability pass, or full DTB rollback. The handoff is consumed.

The steps and conditions below are retained as history, not current authority. At handoff, the internal screen was normal and Linux was responsive. The instructions required saved work, battery strictly above 50%, and an open lid. MagSafe, the same front/lower monitor cable and orientation, HDMI cable, monitor input, and downstream USB ports were to stay unchanged. The old unplug-all rule applied only to the completed live swap.

Fresh checks and their limits are in the [D3 failure record](../evidence/dev-147-usbdiag-startup-failure-2026-08-28.md). Stop if internal-display health, responsiveness, charging, physical setup, or kernel/package state changes. Keep these instructions and the existing private offline recovery guide available on another device. The GRUB editor appears before Linux starts, not in desktop Terminal or macOS Recovery. No Recovery visit is required for this selection; actual Mac restore execution remains untested.

1. When ready, David runs `sudo reboot` in the desktop Terminal. The agent does not run it.
2. At the visible GRUB menu, press an arrow key to stop its countdown. Highlight the normal `Arch Linux` entry and press `e`. Do not use blind key presses through Apple or U-Boot screens.
3. On the existing `initrd` line, replace only `initramfs-linux-asahi.img` with `initramfs-linux-asahi-dpalt.img`. Keep its `/boot/` prefix and all other entry contents. Do not add `usbdiag1`.
4. Leave the `linux /boot/vmlinuz-linux-asahi ...` line and every kernel argument unchanged. Press Ctrl-x once to boot this in-memory edit. Esc cancels it. See the [GRUB menu-editor reference](https://www.gnu.org/software/grub/manual/grub/html_node/Menu-entry-editor.html).
5. After login, report both physical screens and system responsiveness. Keep cables, input settings, and modes unchanged. Stop for read-only loaded-ID and boot-log validation. Do not reconnect, retry, change modes, suspend, or load a module to recover an image.

Expected GRUB entry contents, not a Terminal command:

```text
initrd /boot/initramfs-linux-asahi-dpalt.img
```

If the menu, normal filename, or path differs, press Esc and stop. If startup misses the edit, report the missed selection; do not repeat the boot or type `initrd` in Terminal. If external video remains absent, report that result without further device actions. Stop immediately on internal-screen failure, lost responsiveness, charging regression, or a safety-stop event. If Linux cannot boot or display, use the existing offline Mac recovery guide; do not improvise device identifiers or overwrite targets.

This edit does not change the saved boot default or restore the original DTB. The earlier unplug-and-normal-restart fallback is historical and separately gated; it does not authorize another boot now. An unedited boot selects the stock driver and may still lack external video. Keep both images, backups, and all evidence.

<a id="next-step--offline-correction-design-only-living"></a>

<a id="next-review-gate--offline-source-correction-only-living"></a>

<a id="next-review-gate--c2-modulecontrol-image-preparation-living"></a>

<a id="next-review-gate--c3-e-only-staging-preparation-living"></a>

<a id="current-handoff--c3-staging-only-living"></a>

<a id="current-handoff--c4-readiness-hold-living"></a>

<a id="current-c4-handoff--one-user-selected-e-boot-living"></a>

<a id="current-handoff--post-reboot-selection-hold-living"></a>

<a id="current-recovery-handoff--working-image-w-living"></a>

### Current state — display recovery observed (LIVING)

David reports a restart and restored external image after the intended W handoff. The [new recovery record](../evidence/dev-147-w-recovery-after-e-2026-08-28.md) confirms both native outputs on a fresh boot, with adjacent non-mirrored desktop geometry. This is an observed functional display recovery, not independently proven W artifact startup: the report did not repeat the filename, and loaded IDs are shared with E.

The W handoff is consumed. The saved USB snapshot has root hubs only; USB/full Gate 4b remains HOLD. Known firmware diagnostics remain, and neither reliability nor E/D3 causality is established. Preserve all images, backups, and evidence. The offline goal below permits fresh isolated work, not reboot, reconnect, sudo, USB-device tests, mode changes, suspend, live module/helper operations, old-helper replay, or greeter testing. Normal boot still does not restore the original DTB; Mac restore execution remains untested.

User report, 2026-08-28: the monitor charges the MacBook Air over USB-C without MagSafe. This is user-attested USB-C-only charging success, separate from missing USB data and earlier full-battery/MagSafe observations. It is not a controlled power test, measured rate, or verification of the present cable configuration. No MagSafe reconnection is needed now. Any future live gate needs fresh battery, power-safety, and setup checks; do not reuse an old MagSafe-required handoff silently.

The login-focus report is separate. Saved greeter observations show a second display view appearing later, and the theme has per-view password fields. The component that moved focus is not established. Any greeter-only fix needs separate approval and disposable tests; do not reproduce it by restarting the active greeter or change display-driver work to address it.

### Autonomous offline goal — next-test package (LIVING)

Current offline step, 2026-08-29: the fixed E-control execution boundary passed its contained zero-child RED/GREEN gate after one retained Python 3.14 path-type stop. The accepted subject binds five authenticated sources, the exact eight-input/593-mount policy, and bounded collectors. All operational entry points remain closed. Independent pre-execution review of one fixed 424-child offline E no-change control is next. The [T1 sender-only selection](dev-147-usb-startup-diagnostic.md#a1-selection--t1-tipd-sender-diagnostic-living) remains unchanged and T1 implementation has not begun. The source proves a pre-registration drop mechanism, not that it caused E's failure. No new manual step is released.

Goal: reach the furthest evidence-led offline outcome for dependable video and monitor-USB startup on the existing front/lower M2 path, while preserving the working setup. Deliver one fully reviewed next-test package, or an independently reviewed NO-GO dossier if an indispensable observation or authority is missing. David authorized progress without manual intervention. This plan must pass review before follow-on work. The [diagnostic subplan](dev-147-usb-startup-diagnostic.md#autonomous-offline-technical-gates-living) owns the technical gates: authenticate saved inputs, compare evidence/source, select one justified candidate or diagnostic, implement and verify only that selection, then prepare and seal its handoff.

All new artifacts and raw evidence use fresh private directories with fixed tool/input pins. Do not edit old seals, operational helpers, images, or backups. Read-only source and named benign attributes are allowed; never read partner `usb_mode`. New bounded build/test/helper execution is allowed only in a fresh verified unprivileged sandbox, with read-only inputs and private outputs. Kernel/dependency drift stops work; no installation, silent repinning, or unrestricted fallback is authorized.

Excluded: privilege; host writes under `/boot`, `/usr/lib/modules`, `/etc`, `/dev`, live configuration, or `o-live`; live module changes, sysfs mutation, binding/reload/tracing/device operations; reboot, suspend, cable changes, or adding a mouse/device. Keep monitor USB ports empty for this case. A mouse is a separate later test only after hub enumeration and review. Boot-default changes, release/permanent integration, upstream submission, and SDDM focus fixes are outside the goal. There is no automatic E retry or B/G sequence.

Package completion requires independent QA and safety review; exact selected source/artifact pins; retained RED/GREEN and real-tool controls; stock-preservation proof; a fixed-source, no-replace staging-only helper tested solely on private/synthetic files; offline recovery instructions and one-case acceptance/stop rules; and a sealed private evidence package. Commit and push reviewed source/docs to the existing own branch, verify readback, and sync DEV-147. Stop with the package ready for the **first manual staging/review boundary**, before sudo, staging, a cable action, or reboot. Completion is not hardware acceptance or a promised root cause.

Offline stock-preservation proof means preserved private archive payloads, verified no-host-write containment, and fresh readable pins. Earlier root-private files retain qualified user-validator provenance until a future user-run staging preflight. Do not request duplicate sudo reads to complete this goal.

The alternative valid outcome is an independently reviewed NO-GO dossier after bounded source/evidence investigation. It must establish the indispensable missing observation or authority and specify the minimal next capture/action; seal its evidence, publish reviewed findings, and sync DEV-147. Uncertainty, slow work, or failing tests alone do not qualify. Do not fabricate a fix or speculative image, or call NO-GO a completed test package. A successful internal gate does not authorize any live step.

### W recovery handoff after E (historical)

The following one-use handoff is consumed. Its former pending instructions are preserved as history, not permission to repeat the recovery.

David has confirmed selecting E. The [selection addendum](../evidence/dev-147-c4-selection-confirmation-2026-08-28.md) resolves the earlier hold and records fresh same-boot readiness checks. External-image loss persists. The reviewed R-E condition is satisfied; this prepares **one** W recovery for final task release, not a new test or a completed recovery. Do not act until that response releases this exact case.

Before action, save work and keep this W procedure and the existing Mac guide available outside Linux. Keep the lid open, battery strictly above 50%, MagSafe connected, and the same cables, port, orientation, monitor input, modes, and empty downstream USB ports unchanged. Linux must remain responsive with a usable screen and a normal restart must be safe. Stop on changed readiness; never delay a safety response for more capture. The agent must not run the reboot command.

1. Run `sudo reboot` yourself in Linux Terminal.
2. At visible GRUB, stop the countdown with an arrow key, select `Arch Linux`, and press `e`.
3. On the existing `initrd` line, replace only `initramfs-linux-asahi.img` with `initramfs-linux-asahi-dpalt.img`. Keep `/boot/`, the kernel line, every argument, and all other contents unchanged. There must be NO `usbearly1` or diagnostic suffix.
4. Press Ctrl-x once. After login, report both screens and responsiveness, then stop. No further test or recovery loop is approved.

Expected recovery GRUB line — **not a Terminal command**:

```text
initrd /boot/initramfs-linux-asahi-dpalt.img
```

If the recovery menu, normal filename, or path differs, press Esc and stop. If you miss the recovery edit, report that result; do not make another attempt. If Linux is unresponsive, no screen is usable, or visible GRUB is unusable, use the retained offline Mac guide; never type blind commands or keys, invent device identifiers, or force repeated power cycles. The [GNU GRUB manual](https://www.gnu.org/software/grub/manual/grub/html_node/Menu-entry-editor.html) documents the editor controls.

W previously restored both displays, but success is not guaranteed. Neither W nor an unedited stock boot restores the original DTB; Mac restore execution remains untested. Preserve all images, backups, logs, and restore bundles. No E retry, staging replay, reconnect, B/G boot, USB-device test, mode change, suspend, live swap, or cleanup is authorized. Missing USB alone remains HOLD, not a reason for another recovery.

### Post-reboot selection HOLD (historical)

The following hold records the earlier unconfirmed selection. David's later confirmation supersedes it; only the current W handoff above can be released.

David reports a normal internal screen and responsive system, but no external image after reboot. The [bounded capture](../evidence/dev-147-post-c4-display-loss-2026-08-28.md) confirms a new boot, a disconnected external connector, and root hubs only. The exact selected initramfs filename remains unconfirmed. Packaged DWC3/ATC and the patched TIPD IDs are shared by W and E; they cannot identify this boot as E.

Current action: obtain the exact filename selected. The intended E handoff is consumed; do not repeat it. The prepared one-use W recovery has conditional safety-review approval only if David confirms exact E selection. It is not released or performed. If the selection was missed, different, or uncertain, stop and resolve that first; do not restart automatically. Keep cables and settings unchanged. Missing USB alone remains HOLD, not a recovery trigger.

Preserve all images, backups, and evidence. Do not replay staging, request a duplicate privileged read, run helpers, or change configuration. Safety loss takes priority over further capture; never use blind commands or keys. The retained Mac guide remains untested, and neither normal boot nor W restores the original DTB. B/G images remain unprepared; no new test sequence or upstream submission is authorized.

### Intended C4 E handoff and R-E recovery (historical)

The following procedure is preserved from the readiness checkpoint. Its E handoff is now consumed. Its R-E procedure is retained but not released under the current selection HOLD above. Do not act on its former pending instructions.

This is a prepared conditional handoff, not an executed test or blanket reboot permission. Readiness QA and exact handoff safety review pass. Perform it only after the final task response releases this exact case, the prerequisites below are met, and David accepts it. E retains the working DP patch and adds packaged DWC3 to the initial image; it contains no diagnostic module. External video can fail again. This test is not needed merely to keep the picture that works now. The [readiness record](../evidence/dev-147-usbearly-boot-readiness-2026-08-28.md) owns the physical confirmations and machine checks. Root-private image/GRUB validation still comes from David's successful C3 validator, not fresh privileged reads; staging is consumed.

David confirms all work is saved and the Mac recovery guide is available on another device, and asks to reboot when ready. Before manual action, he must still choose this exact single E case and its conditional recovery and read this entire new E/W handoff with it also available on another device or paper without Linux. Keep the confirmed Mac guide available too. The new E/W access/read-through and exact-case choice remain user actions. A link available only on this Linux installation is insufficient. No extra chat reply is intrinsically required, but if any prerequisite is missing, stop before the reboot command.

Keep the lid open and battery strictly above 50%. Keep MagSafe and the same USB-C cable, port, orientation, HDMI connection, monitor input, modes, and empty downstream USB ports unchanged. If kernel/packages, power, internal-screen health, responsiveness, or setup changes, stop for a new review. No package update belongs to this case.

#### E — one test boot

1. Once the final task response releases this case, all prerequisites are met, and David chooses it, he runs `sudo reboot` in the normal Linux desktop Terminal. The agent must not run it.
2. At the visible GRUB menu, press an arrow key to stop the countdown. Highlight the normal `Arch Linux` entry and press `e`. Do not press keys blindly through Apple or U-Boot screens.
3. On the existing `initrd` line, replace only `initramfs-linux-asahi.img` with `initramfs-linux-asahi-dpalt-usbearly1.img`. Keep `/boot/` and every other entry component. Do not add `usbdiag1` or `usbdiag2`.
4. Leave the `linux /boot/vmlinuz-linux-asahi ...` line and every kernel argument unchanged. Press Ctrl-x once to boot the temporary edit. Esc cancels it.
5. After login, report the exact initramfs filename selected, whether both screens show an image, and whether the system responds normally. Leave cables and settings unchanged; stop for read-only evidence capture.

Expected GRUB line — **not a Terminal command**:

```text
initrd /boot/initramfs-linux-asahi-dpalt-usbearly1.img
```

If the visible menu, normal filename, or path differs, press Esc and stop. If the edit is missed and Linux starts normally, report the missed selection; do not repeat the restart or type `initrd` in Terminal. There is no automatic E retry or next B/G boot. The [GNU GRUB manual](https://www.gnu.org/software/grub/manual/grub/html_node/Menu-entry-editor.html) documents Ctrl-x and Esc. The temporary edit does not change the saved boot default or undo the prototype DTB.

#### After E — observe once

If the external image is blank but the internal screen and Linux remain usable, report that result without unplugging or reconnecting. A prompt read-only capture may preserve the failure evidence. Safety loss takes priority: do not delay recovery to collect more data if a safety condition appears.

A healthy picture with missing monitor USB hub/controls is USB HOLD, not permission for another reboot, reconnect, USB-device test, mode change, suspend, or live swap. E is uninstrumented; zero diagnostic markers are expected and are not a trace failure. Post-boot verification must establish a new boot identity and retain David's exact selected filename. E and W use the same loaded USB module build IDs, so those IDs alone cannot identify the image. Review ordinary all-priority kernel/firmware logs, both outputs, power, and target hub/controls without reading partner `usb_mode`.

#### R-E — separate conditional recovery to W

This is recovery only, not a second test or the old consumed W handoff. Use it only for persistent external-image loss or a new display, responsiveness, charging, or other safety failure after E. Missing USB enumeration alone with healthy displays does not trigger recovery. Stop the E case at a safety failure. Only if Linux remains responsive with a usable screen and a normal restart is safe may David make **one** recovery restart:

1. Run `sudo reboot` in Linux Terminal.
2. At visible GRUB, stop the countdown with an arrow key, select `Arch Linux`, and press `e`.
3. On the existing `initrd` line, replace only `initramfs-linux-asahi.img` with `initramfs-linux-asahi-dpalt.img`. Keep `/boot/`, the kernel line, every argument, and all other contents unchanged. There must be no `usbearly1` or diagnostic suffix.
4. Press Ctrl-x once. After login, report both screens and responsiveness, then stop. No further test or recovery loop is approved.

Expected recovery GRUB line — **not a Terminal command**:

```text
initrd /boot/initramfs-linux-asahi-dpalt.img
```

If the recovery menu, normal filename, or path differs, press Esc and stop. If the recovery edit is missed, report that result; do not make another attempt. If Linux is unresponsive, no screen is usable, or visible GRUB is unusable, do not type commands blindly or invent recovery targets. Use the retained offline Mac guide. That route is not runtime-tested. Do not force repeated power cycles or experiment with device identifiers.

W restored both displays in the earlier reviewed recovery; this new conditional use is not a guarantee. An unedited stock boot may lose external video. Neither W nor stock boot restores the original DTB. Keep all images, logs, both timestamped backups, and both Mac restore bundles. Do not rerun staging, remove files, regenerate GRUB/initramfs, update m1n1, change the normal default, or edit the live checkout. B/G images remain unprepared. D3 causality, full Gate 4b/USB acceptance, rollback, reliability, permanent integration, and upstream submission remain open and separate.

## Gate 5 — one variable at a time

Run only after Gate 4b passes. Review live compositor configuration and advertised modes before providing exact temporary mode commands. Do not write permanent display settings.

1. Test native `3440×1440` at about 100 Hz, then the same resolution at about 60 Hz. Record the actual advertised timing and observed refresh rate for each. Restore the previous tested mode between unrelated cases.
2. Test three controlled unplug/replug cycles on the same front/lower port. Capture each disconnect and recovery separately.
3. Test a full cold start with the cable attached. Select the candidate initramfs for that boot.
4. Test startup without the cable, then attach it after login. Select the candidate initramfs for that boot too.
5. Test suspend/resume last, once only, with David present and ready to recover. Review all earlier logs before approving this case. The reference implementation reported an unresolved reconnect-after-suspend problem.

Keep the lid open throughout. Do not automate these actions or mix a port, cable, power-source, or mode change into another test. For each case, save the kernel/RTKit log window, DRM state, EDID/modes, compositor state, charging state, USB devices/errors, user-visible result, and any recovery action.

Exit: every case has its own result and evidence. An omitted or failed case remains open; a working initial image does not fill in missing tests.

## Firmware investigation and stop conditions

The Gate 3 record contains a frequency-setup `EDT ERROR`, a CAHandler data-version diagnostic, and PMU return `0xe00002d8`. The startup capture repeats these external-DCP classes: four frequency messages, three CAHandler messages, and three PMU messages. USB-1 adds one FIFO error interrupt `COMMON_INT_STA_3=0x00000010` at deliberate unplug, followed by successful poweroff/reconnect, and one recurrence of each known class. Five initial crossbar `-517` deferrals recover into successful binding. The PMU return was previously mapped to `kIOReturnNotReady`; the frequency and CAHandler consequences remain unresolved. Do not describe these messages as harmless or the firmware as clean. The earlier `usb_mode_show` WARN belongs to the diagnostic read, not the DCP startup sequence; its trace and taint change remain open.

RTKit forwards firmware messages at info priority. Always inspect full firmware syslog, not only warning-priority journal output. Compare frequency and recurrence across modes, startup, and reconnect cases. Earlier USB `-71` setup-address failures, port-enable failures, and an invalid-context warning occurred before the patched module; preserve that baseline instead of assigning them to the candidate.

Stop the current test on unexpected or persistent display loss, failure to recover after an intentional unplug/replug, repeated timeouts, a new DCP/coprocessor crash, DART/IOMMU faults, kernel BUG/panic, or charging/USB regression. An intentional unplug is not itself a failure. Capture evidence if the machine remains responsive, then use the appropriate rollback below. Do not repeat a live swap.

Do not add the `appledrm` poweroff patch unless evidence reproduces its exact proposed failure: a clear-swap timeout followed by persistent atomic-commit `-EINVAL`. Any such patch needs a separate high-risk review. The current result does not require it.

## Gate 6 — prove full rollback, then retain the evidence

This gate is pending and separately gated. It is not the completed D3 recovery above. The stock-driver and full-DTB procedures below are retained alternatives that need their own review before use; they do not authorize a cable action or additional boot now. David runs any later approved commands one at a time.

For driver-only rollback, unplug the monitor and run `sudo reboot`. Boot normally without the test initramfs. This discards the live candidate module; it does not undo the DTB.

For full rollback, use the existing transactional script:

```bash
sudo bash /home/david/o/.dev147-stage/commands/02-rollback-dtb.sh
```

Only after it reports `Gate 2 rollback PASS`, reboot:

```bash
sudo reboot
```

Use the stock initramfs on that boot. If Linux cannot boot or display, follow the existing offline Mac recovery guide (retained privately). Do not improvise a new partition target.

After the stock boot:

- Verify `dcpext` is disabled, its alias is absent, and neither USB-C connector has the prototype `displayport` property.
- Verify the loaded Type-C core is the stock in-tree module. Confirm the internal screen is normal.
- Compare stock `boot.bin`, initramfs, and GRUB with the privileged baseline manifest (retained privately). Obtain root-only hash checks from David. Compare the packaged DTB/core with their recorded pins, and the kernel image with the new dated pre-Gate-4 baseline if Gate 4 was undertaken. If rollback happens before that baseline exists, state that the original kernel-image digest is missing; do not claim a retrospective hash match. Verify the pinned kernel package and `pacman -Qkk linux-asahi` results, and explain any discrepancy.
- Confirm `/etc/default/update-m1n1` remains absent and no persistent GRUB or display settings were added. Record the rollback output, resulting hashes, and live state.

Exit: every system file placed in scope matches its baseline and the stock boot/driver are verified. Do not mark full rollback passed from a successful copy or reboot alone.

Do not remove the test image, stage, source, evidence, notes, or either backup automatically. Retain both `boot.bin.pre-dpalt-20260826T222113Z` copies: one under `/boot/efi/m1n1` and one under `/home/david/o/.dev147-stage/recovery`. Any cleanup needs a later explicit, bounded approval after rollback proof.

## Separate future permanent integration

Only propose permanent integration after Gates 4–6 and review of the firmware findings. It needs a new design and explicit approval. Require an uninstall path, exact kernel-version pin or compatibility check, and protection/fallback for kernel updates. Never reuse the old binary with a new kernel. A permanent module, initramfs change, boot override, or automatic startup action is outside this reconciliation.

### Fork integration and upstream contribution

The reviewed source is already on the fork's `codex/dev-147-m2-dp-altmode-public` branch. Preserve that research history. Source publication is not release or deployment, and merging the archive alone does not install the patched driver or DTB. After acceptance, propose a small opt-in integration PR against `Skeptomenos/omarchy-mac:quattro-arm`, not the fork's default `main`. Keep private images/logs and temporary diagnostics out of the release. Resolve or explicitly waive recorded release-test failures. Release approval and deployment through `omarchy update` remain separate.

The [unsent contribution draft](../research/dev-147-upstream-contribution-draft-2026-08-28.md) separates the saved M2 replication report from a maintainer inquiry. It adds no new hardware result or permission to send either text. The read-only check found [haripako's PR #289](https://github.com/omarchy-mac/omarchy-mac/pull/289) open; do not duplicate it. Confirm repository terms and disclose material AI assistance before any submission. C2 approval authorizes no external message, issue, PR, or comment.

- `haripako/dp-altmode`: a narrow M2 replication report is a possible first contribution, after confirming the owner's contribution channel, licensing, and policy on AI-assisted work. Its [replication guide](https://github.com/haripako/dp-altmode/blob/main/REPLICATION.md) documents one M1 machine; separate our observed M2 results from hypotheses and untested cases.
- [Omarchy Mac](https://github.com/omarchy-mac/omarchy-mac): the former `malik-na/omarchy-mac` URL now redirects here. Propose reusable Apple Silicon integration after validation. Keep kernel/DT changes separate. Hardware-independent Omarchy improvements alone belong with Basecamp.
- Asahi: its [Generative AI Policy](https://asahilinux.org/docs/project/policies/slop/) forbids materially AI-assisted contributions, including code, documentation, and engineering decisions. This work cannot be submitted as a compliant Asahi contribution. Human review does not remove that provenance. Do not use another repository or a mailing list to disguise it. David may personally ask maintainers, with disclosure, whether they welcome his own hardware observations; acceptance is not assumed.
- Preserve original author credit and per-file licenses. The HPD forwarding derives from the cited Asahi commits; it is not a new invention from this experiment. No upstream issue, PR, comment, release, or deployment is authorized by D2 preparation.

## Decision Log (LIVING)

- 2026-08-29: Accept the fixed E-control zero-child execution boundary. Preserve RED `run-0zk61la1`, stopped first GREEN `run-_l2w9p_k`, and corrected 3/3 GREEN `run-nr5woop4`. The accepted subject is `39496435f113c7d9256e5592effd3fece8c52b0e61b774e8283fe96eb84d4add`; inputs stayed unchanged and no workload child or operational artifact existed. Keep all operational APIs and live/manual holds closed. Require a separate review before one fixed 424-child offline E control. This is launch-boundary evidence, not fresh-control, T1, image, or hardware evidence.

- 2026-08-29: Link the dated A0 HPD investigation and select T1 for offline A2–A4 after independent safety, documentation QA, and source/design review agreement. Preserve the proposal anchor and exact containment gates. No T1 source, binary, or image exists yet; source/read-only checks do not establish runtime causality or permit a behavior fix. Preserve the working setup, E/D3 history, qualified latest W recovery, and USB/firmware HOLD. No manual action is released.

- 2026-08-28: Define the user-authorized autonomous offline goal with two reviewed outcomes: one tested package ready for the first manual boundary, or a substantiated NO-GO dossier naming an indispensable missing observation/authority and minimal next action. Select one evidence-justified candidate or diagnostic only after review; retain fixed pins, fresh containment, RED/GREEN, QA, safety review, seals, own-branch publication, and DEV-147 sync. No live change, E retry/B/G ladder, greeter fix, or hardware-PASS claim follows. Record the user's USB-C-only charging success separately from USB data acceptance; this is not a controlled power test or current-configuration verification, and no MagSafe reconnection is needed now.

- 2026-08-28: Record functional display recovery after the intended W handoff and consume it. A fresh boot has both native outputs, but the user did not restate the filename and shared IDs do not independently prove W startup. USB/full Gate 4b stays HOLD; known firmware diagnostics and causality limits remain. Keep the login-focus observation separate as a possible greeter hotplug/focus bug, with no reproduced authentication failure or identified focus-moving component. A fix and disposable tests need separate approval; no further device or greeter action follows.

- 2026-08-28: Accept David's confirmation of the E filename with the saved boot capture as E external-display FAIL, not evidence of a cause. Fresh same-boot readiness checks agree. The prior R-E selection condition is satisfied; prepare its one W recovery for final task release, with unchanged safety and no-retry rules. W has not been performed. Keep the earlier selection-HOLD evidence and procedures unchanged; no E retry, cable action, or B/G test follows.

- 2026-08-28: Record external-image loss after the intended C4 reboot, with internal screen and responsiveness normal. New boot and bounded ordinary logs are verified, but the selected filename is not. Do not label this a verified E failure. Consume the intended E handoff; hold for exact selection. W recovery remains conditionally reviewed, not released or performed. Preserve all earlier evidence and procedures, root-private provenance limits, zero-marker expectations, and USB/full Gate 4b HOLD; no retry or cable action.

- 2026-08-28: Physical setup, read-only machine readiness, independent readiness QA, and exact handoff safety review now pass. David confirms saved work and the Mac guide on another device, and requests reboot when ready. Prepare one conditional E handoff and a separate one-use W recovery, without an E boot result. Final task release, new E/W instructions available/read outside Linux, and choosing the exact case remain required. Preserve loaded-identity ambiguity, uninstrumented zero-marker expectations, safety-first recovery, and USB-only HOLD. Keep C3/old boot handoffs consumed, all earlier evidence unchanged, and no retry or B/G ladder.

- 2026-08-28: Accept C3 user-run staging PASS from David's complete report, with qualified independent receipt QA. All 41 visible initial-preflight rows match; later checks/markers remain root-private. No separate numeric exit status was captured. Independent readable hashes, source identities, seal, and destination metadata agree. E is staged but unbooted; consume the staging handoff without replay or duplicate sudo read. Hold C4 for fresh physical/readiness confirmation and a separately reviewed one-time selection/recovery proposal. No new hardware result or reboot permission follows.

- 2026-08-28: After the sealed C2 checkpoint, prepare the distinct E-only C3 staging helper. Preserve two genuine old-image/proof RED assertions before the minimal correction. Syntax, all 42 focused methods, independent saved-run QA, helper review, and exact three-assignment private-copy review pass; all 38 old bodies remain unchanged. The 33 protected + 8 proof rows are producer-contract evidence, not production preflight. Next is David's one staging-only command. E is unstaged/unbooted; no cable action or C4 permission follows.

- 2026-08-28: Record C2 offline artifact checks and independent QA PASS after retained metadata, E-delta, and v2-version-boundary REDs. Fresh controls/v2 modules and only E are verified; no diagnostic module is in E, and B/G images remain unprepared. Preserve all historical source and evidence. After checkpoint review/sealing, proceed with a new E-only C3 staging helper and focused review. David runs any later privileged staging command; image selection and recovery readiness remain separate. No new hardware or acceptance result follows.

- 2026-08-28: David asked to update the plan and continue until manual support is required. Authorize C2 offline module/control-image preparation, focused QA, and independent review in fresh contained outputs, then prepare the next exact manual handoff. No C2 PASS is implied. Stop before monitor connection, sudo, staging, or reboot; preserve all safety gates and historical evidence. Prepare an unsent M2 report/inquiry, respect existing PR #289 and contribution policies, and make no external submission.

- 2026-08-28: Under separate C1 approval, reproduce generation-zero RED in both frozen v1 guards before changing source. Apply only the exact OF node/reference guard and strict v2 token, then pass focused target, trace, and format/cap checks. Independent focused QA and source/test review pass. Keep v1 images, binary/build helpers, C0, D3, and recovery evidence unchanged. C2 preparation needs separate approval; no new device action or acceptance result follows.

- 2026-08-28: Complete independent review of the correction design in the existing diagnostic subplan, not a parallel plan. Prefer exact OF-path lookup plus referenced-node identity, with the narrow metadata-lock/refcount timing exception disclosed. Require real target semantics in the production generation-to-marker tests and distinguish early availability, rebuild, and instrumentation controls. The user scope is C0 planning only; next approval is contained C1 source/tests without module or image builds. Preserve the separate failed D3 and successful recovery records. No new hardware result or action is implied.

- 2026-08-28: Accept one attended working-image recovery as a functional display PASS after David reports both screens normal and read-only checks confirm packaged DWC3/ATC plus the unchanged working patched core. The monitor hub/controls remain absent, so full Gate 4b stays HOLD. Preserve the failed D3 outcome, unfixed logging defect, prior evidence, and historical tests. The recovery handoff is consumed; next is an offline correction-design proposal only. No implementation or further device action is authorized.

- 2026-08-28: Record D3 as external-display FAIL and measurement INCONCLUSIVE. David used the diagnostic selection; the internal screen remains normal. Intended loaded IDs match, but the 963-record journal has no diagnostic markers. The pinned OF implementation proves a leaf-name/absolute-path guard mismatch. This explains missing instrumentation, not the video failure. Preserve the failed image, full private capture, earlier evidence, and historical offline PASS results; record the missed semantic coverage. The D3 handoff is consumed and must not repeat.
- 2026-08-28: Hand off a separately reviewed, single attended recovery selection of the previously working `initramfs-linux-asahi-dpalt.img`. Leave cables, input settings, kernel arguments, and the saved boot default unchanged. Recovery is pending and not guaranteed; it is not full DTB rollback. After physical recovery and loaded-ID validation, scope offline target-semantic regression coverage and review earlier DWC3 availability. No fix, build, diagnostic retry, hotplug, live swap, mode test, or suspend is authorized.

- 2026-08-28: David confirmed MagSafe, the front/lower USB-C monitor, no other active work, both physical images normal, and no downstream USB device. Fresh checks match 37 readable protected/proof files, source/helper hashes, versions, image metadata, and the 12-file D2 result seal; battery is 100%. Root-private contents retain David's D2 validation provenance. Release the narrow one-time D3 GRUB handoff, with the diagnostic filename, unchanged kernel arguments, and no retry. This records readiness and handoff only, not an executed boot or hardware result.

- 2026-08-28: Accept D2 as successful user-run staging after the pinned helper's complete final PASS, exact 40-record comparison, and independent metadata checks. Root logs stay in `/boot/.dev147-usbdiag-stage.ESqzIgLr8I`; they were not independently reread. Preserve both frozen preparation archives and the working image. Supersede pending staging instructions; do not rerun them. Keep D3 unauthorized until fresh readiness review and explicit approval.

- 2026-08-28: Complete D2 helper preparation after genuine RED, two bounded corrections, 38 passing isolated tests, and independent QA/static review. Preserve the environment-loop failure and the EXIT-trap scope defect with their regression evidence. Hand David only the final pinned private staging copy; the earlier copy is retained but superseded. No privileged preflight, staging, or reboot ran. Keep D3, acceptance, release, and upstream gates open.
- 2026-08-28: David said “ok, update the plan if necessary and proceed” after the D2-preparation recommendation. Approve offline staging-helper implementation, focused QA, and independent review only. Use fresh private outputs and preserve the frozen D1 archive. Hand off the exact privileged staging command after review; David executes it. D3, fork release, deployment, and upstream submission remain separate. Record the fork route and current upstream contribution constraints without rewriting earlier evidence.

- 2026-08-26/27: Use the minimal J413/M2 DT route plus generic CD321x HPD forwarding. Reject the M1 installer/DTB and leave the full fairydust, audio, SIO, suspend always-on, and `appledrm` changes out. Rationale and pins are in the dated history.
- 2026-08-27: Add an offline Mac restore bundle after finding the initial Linux-only recovery gap. Accept David's macOS/Recovery attestation and his choice not to rehearse it. Keep runtime restore validation explicitly unproved.
- 2026-08-27: Correct the Gate 3 power rule: MagSafe is Type-C partner `0-003a` and must be disconnected along with all USB-C cables for that swap. The first call refused before mutation; exactly one later swap ran. Preserve the incorrect advice and correction in history.
- 2026-08-27: Treat Gate 3 as functional live-session success, not stability or permanence. Do not replay it. Split Gate 4 into image preparation/review and a separately selected startup test.
- 2026-08-27: Use native ~100 Hz and same-resolution ~60 Hz, controlled reconnect/startup cases, and suspend last. Review full firmware logs at all priorities.
- 2026-08-27: Separate rollback proof from cleanup. Supersede the old instruction to remove staging and retain only one backup; retain both backups and all evidence until explicit cleanup approval.
- 2026-08-27: Reconcile documentation only. Preserve the original issue description and all nine comments in the private Linear snapshot, excluded from this public export. The dated history owns past events; this plan owns future gates.
- 2026-08-27: Continue with isolated Gate 4a preparation after David's request. Keep all 27 original artifact/evidence/recovery files and all four Gates 0–3 scripts byte-identical. Build in a fresh private directory, not over the old stage or stock files. The user-run protected readback is separate from staging and boot authority.
- 2026-08-27: Correct two defects found before use: GNU `dd` requires `conv=excl,fsync`, and DPTX/crossbar must not be forced into the early image when the retained hooks do not select them. Real exclusive-copy regression tests now pass. Keep package-verified normal-root driver availability; do not add preloads to satisfy a verifier.
- 2026-08-27: Accept the recorded current-package OpenSSL rebuild difference for a contained startup experiment, not as proof of runtime compatibility. Keep the stock image untouched and require separate user-selected boot validation. Do not describe the whole image as core-only.
- 2026-08-27: Hand off reviewed staging only, with a clean environment before Bash. Keep a separate stop before reboot. Staging and startup results remain pending until David runs their gates. After an interruption, `INCOMPLETE` alongside `RESULT.txt` is a hold: recheck; do not automatically retry or clean up.
- 2026-08-27: David ran the pinned staging helper and supplied final `STAGING ONLY PASS`; the root-private check directory is `/boot/.dev147-dpalt-stage.e5Cys4arMi`. Accept its protected post-checks as validated user-run execution, not agent-read root logs. Independent metadata/readable-hash checks agree. Gate 4a is complete; Gate 4b is the next separately selected action. Keep the normal boot entry unchanged and preserve all prior evidence. No startup, reliability, or full rollback pass is claimed.
- 2026-08-27: Record the 22:18 reboot as stock-core operation, not a failed candidate test. The terminal `initrd` error exposed an unclear handoff between desktop Bash and the pre-login GRUB editor. Separate those contexts explicitly and establish that the user saw the menu before another attempt. Do not infer the chosen image solely from the loaded core, repeat the live swap, or make the test persistent to bypass this handoff.
- 2026-08-27: David completed the clarified one-time GRUB selection. The new boot, early candidate-core load, both native outputs, and his physical confirmation establish display startup success. Keep overall Gate 4b on hold: monitor USB enumeration is missing, and the same initial absence occurred in an earlier verified stock-driver boot. Preserve this as an unresolved comparison, not a new candidate-specific regression. Both PD sources are online with a full battery; isolated USB-C charging remains untested.
- 2026-08-27: Our read-only partner-status loop triggered `usb_mode_show` / `sysfs_emit_at` WARN while reading `usb_mode`. Record this diagnostic side effect and the taint increase from 4100 to 4612. Do not repeat that read or patch the kernel in this checkpoint. Keep startup evidence separate from the later warning. Hold Gate 5 and review a single attended USB diagnostic case next; no further device action ran.
- 2026-08-27: David approved proceeding with USB-1. Read-only preflight and bounded design review passed. Require a physical check for devices on the unseen monitor hub before release; software enumeration alone is insufficient. Keep MagSafe connected, use one identical-port reconnect, and stop on internal-screen loss or failed recovery. No cable action has run at this checkpoint; physical hub check and saved-work readiness are pending.
- 2026-08-27: David reports only another HDMI cable on the monitor. Treat the USB-device check as cleared. Keep HDMI and input settings unchanged; automatic input switching is an interpretation caveat, not proof of USB-C recovery. Fresh pre-action checks and independent review passed. Hand off one reconnect after saved-work readiness; result remains pending.
- 2026-08-27: USB-1 completed with functional PASS: internal screen remained usable, external image returned in about 5 seconds, and USB hub/LG controls enumerated. Preserve the unplug-time FIFO error and three known firmware recurrences; no new kernel WARN or fatal-pattern/USB-error match appeared in the captured interval. This supersedes the pending handoff above, not the startup USB hold. Do not repeat the case. Compare saved startup and reconnect initialization read-only before any new reviewed device/boot test. Full Gate 4b, Gate 5, full rollback, and permanent integration remain open.
- 2026-08-28: Complete the read-only startup/reconnect investigation. Record the stock USB-glue first-probe ordering defect as a strong causal lead, not a measured runtime event or tested fix. Retain the later HCD HOST setter and mux-power-order qualifications. Do not add an appledrm patch for the observed FIFO event. Supersede the pending comparison with a proposed offline, controller-attributed one-boot diagnostic design; require separate review/approval before implementation, build, staging, or boot. Preserve the working DP image, all earlier evidence, and both backups. No hardware state changed; full Gate 4b remains on hold.
- 2026-08-28: Complete D0 offline diagnostic design after independent source/measurement, image/rollback, and safety review. Capture retry generations and diagnostic identity from first probe; missing final records cannot prove no late setter occurred. Record the earlier-probe timing change from adding DWC3 glue to the image. Require a no-change archive/index control and preserve builtin indexes with pinned missing inputs. D1 implementation/QA/private build needs approval as one phase; D2 staging and D3 attended startup remain separate. No diagnostic source or image was created, no hardware action ran, and no acceptance hold was cleared.
- 2026-08-28: David approved D1, then preparation stopped after three sandbox QA failures. Save source drafts, schema, unrun RED fixtures, recovered inputs, and all failed runs. The namespace assertion needs an observed return/errno before it can classify denial; no escape or isolation pass is established. Ask before one further correction/check. No module/image build, live driver action, staging, or reboot ran. D1 does not require the monitor connected; a permitted unplug was not confirmed or counted as a test. Full Gate 4b and all later gates remain open.
- 2026-08-28: David approved the narrow assertion correction and one additional sandbox QA round. R4 passed; its exact namespace denials and seven focused tests are retained in new evidence. Preserve the old three failures without inferring their missing errno. The initial isolation hold is cleared; remaining offline D1 implementation, tests, and private builds are next. No driver/image build or hardware action ran in R4. Full Gate 4b and later acceptance gates remain open; D2 and D3 still require separate review and user action.
- 2026-08-28: David asked to commit and push all work, then proceed. Prepare `codex/dev-147-m2-dp-altmode-public` from the verified public base. The original 14-commit private history contains a raw Linear export, so retain it unchanged instead of publishing it or rewriting history. Export authored source, fixtures, plans, and reviewed notes; use invalid public machine-identity placeholders and keep raw logs, manifests, packages, binaries, boot files, and recovery backups private. Commit and push completed reviewed checkpoints, not only local documentation. No release or permanent deployment is authorized.
- 2026-08-28: Resume approved offline D1 in fresh private outputs after the R4-equivalent isolation probe passed. Run the frozen trace and image stubs once to establish RED: 32 trace tests report 40 NotImplementedError errors; 16 image tests report 30. Both runs preserve inputs and do not time out. These failures prove missing implementation, not correctness or hardware safety. Keep the old checkpoints unchanged and proceed to implementation and independent QA.
- 2026-08-28: Publish and verify the first source checkpoint. Implement the trace validator; independent QA finds three ATC-finalize false positives, then the correction passes all 59 tests. Authenticate pahole in private output, compile two unmodified controls and two diagnostic modules with BTF, and check basic metadata. Retain the armored-keyring and metadata-filename failures without rebuilding successful controls. Import/logging review and real archive/index/image gates remain open. No live state changed; keep D2/D3 unauthorized and full Gate 4b on hold.
- 2026-08-28: Push trace checkpoint `d28fbc169` and verify it remotely. Complete exact diagnostic-import QA and userspace log-format/cap checks, after retaining a link failure and supplying only pinned private runtime inputs. The strict archive helper passes all 48 fixtures, including real filesystem failure cases. The saved gzip stream is valid and fits its size bound. Proceed to real no-change archive/index controls; no diagnostic image, load, staging, or boot is yet claimed.
- 2026-08-28: Push helper checkpoint `8bf097882` and verify it remotely. Real parsing exposes valid archive zero link counts and directory trailing slashes; correct only those format rules, preserving physical hardlink guards. All 58 archive tests then pass. Retain the later depmod scratch-output stop; permit only its verified, header-only modules.weakdep outside the image. The fresh control passes exact image/index reconstruction and all 199 binary-only lookups. Next is the private diagnostic image, not staging or boot.
- 2026-08-28: Push real-control checkpoint `dd4442710` and verify it remotely. Retain the first assembly's symbol-index stop and the independent alias-spelling failure. Prove priority-only drift, preserve the original symbol index, and correct alias-key normalization without changing raw symbol keys. All 55 assembly fixtures and the real 413-command assembly pass. The new private image has 200 modules and exactly four archive changes; the original 199 dependency results remain unchanged. Offline D1 is complete. Next requires D2 approval; no staging, live load, reboot, hardware causality, or reliability pass is implied.
