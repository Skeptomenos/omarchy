# DEV-147 — visible recovery card

Reconciled: 2026-08-29. **REVIEWED OFFLINE REFERENCE — NOT AUTHORIZED OR REHEARSED.** Independent documentation QA and safety review pass. This card does not release the battery-depletion hold, authorize a candidate boot, or request a reboot. The [main plan](dev-147-m2-displayport.md) owns current authority.

This card covers one future M2 J413 candidate case on `omarchy-air`. It routes a responsive Linux candidate to the unchanged stock-core Linux boot. It routes an unresponsive candidate directly to the existing macOS/Recovery restore guide. Keep this card and the pinned guide visible on a separate device before any later candidate selection.

## Known boot facts and limits

- Every DEV-147 candidate selection used a temporary visible GRUB edit. It did not change the saved default.
- The normal visible GRUB entry is `Arch Linux`. Its unedited `initrd` line uses `/boot/initramfs-linux-asahi.img`, which loads the packaged stock Type-C core.
- The protected GRUB file is root-only. The unchanged-default claim comes from David's completed staging validators, successful default boots, and the retained one-shot handoff evidence. It is not a fresh unprivileged read of `grub.cfg`.
- A stock-core boot does **not** restore the original DTB. The experimental J413 DTB remains in `m1n1/boot.bin` until the separate pinned restore succeeds. External video can therefore remain blank on the stock-core boot.
- The existing `RECOVERY-DPALT-MAC-20260826T222113Z.txt` starts after normal macOS or macOS Recovery Terminal is visible. Its pinned restore script has passed static and integrity checks but has not run on macOS.
- Apple documents holding the Touch ID/power button for up to ten seconds when a Mac cannot shut down normally, then holding it again from the off state until startup options appear. The startup-options screen can boot a visible disk or enter Recovery. See [Apple's Recovery instructions](https://support.apple.com/en-gb/102518?choose-your-type-of-mac=mac-with-apple-silicon) and [startup-options reference](https://support.apple.com/en-au/102342).
- Asahi uses Apple's native boot picker for OS selection, then m1n1/U-Boot/GRUB for Linux. See the [Asahi boot-picker explanation](https://asahilinux.org/docs/platform/introduction/) and [open-OS boot layout](https://asahilinux.org/docs/platform/open-os-interop/).

## Choose one branch

Use the responsive branch whenever Linux and the internal screen still respond. The unresponsive branch is only for a future released candidate whose internal screen or Linux input is unusable, or whose visible recovery has not begun by its hard external deadline.

Missing external video or monitor USB alone is not an unresponsive state. Do not force power off while the internal screen and Linux remain usable.

### A — Linux and the internal screen respond

1. Stop evidence collection. Keep MagSafe connected, the lid open, and cables unchanged.
2. In a visible Linux Terminal, David runs:

   ```bash
   sudo reboot
   ```

3. At visible GRUB, press an arrow key to stop the countdown. Highlight `Arch Linux` and press Enter. Do **not** press `e` or `c`. Do not edit an `initrd` line.
4. If the countdown completes before input, do not restart again. Let the unchanged default boot continue.
5. After login, stop. Confirm that the internal screen works and Linux responds. External video can be absent on this stock core.

If the visible entry name differs, GRUB is missing, or GRUB is not usable, do not select or guess. If a visible countdown continues, let the unchanged saved default continue without another restart. Otherwise stop and obtain separate recovery help. Do not route an unexpected GRUB state back through Linux or force power off merely because the menu is different.

### B — Linux or the internal screen does not respond

Use a separate-device timer. Keep MagSafe attached. Do not type commands or GRUB keys blindly. First classify the state:

- **Known running and hung:** David directly observed this candidate running and then becoming unresponsive. No shutdown or restart was requested or visibly underway. Use B1.
- **Known off:** David just watched a visible normal shutdown complete, or B1 completed the documented force-off from a known-running state. Use B2.
- **Unknown:** The Mac was found black or dark, or the transition was not observed. Stop and obtain separate recovery help. Do not press the power button. Screen and keyboard darkness alone never establishes the off state.

#### B1 — known running and hung

1. Stop all keyboard and trackpad input. Do not wait beyond the candidate's hard external deadline for logs or external video.
2. Start a ten-second timer. Press and hold the Touch ID/power button for the full ten seconds, then release it. This forced shutdown can lose unsaved work and can leave filesystems dirty; use it only because the visible normal route is unavailable.
3. Wait 15 seconds with the button released. Do not close the lid, disconnect MagSafe, or change the monitor cable.
4. If `Loading startup options` or the visible startup-disk/Options screen appears during the wait, do not press power again; continue at B3. If any other visible startup or boot progress appears, do not long-press again. Stop and use only the visible normal route or obtain separate recovery help.
5. If the screen remains dark after the wait, the directly observed known-running state plus the completed documented force-off establishes the transition to B2. Darkness alone would not.

#### B2 — known off

1. Start a 30-second timer. Press and hold the Touch ID/power button.
2. Release the button when `Loading startup options` or the visible startup-disk/Options screen appears, then continue at B3.
3. If neither appears after 30 seconds, release the button and stop. Do not repeat the power cycle or guess keys. Record what remains visible and obtain separate recovery help.

#### B3 — visible Recovery route

1. Select `Options`, choose Continue, complete the normal Recovery authentication, and open Terminal from the Recovery menu.
2. Read the pinned `RECOVERY-DPALT-MAC-20260826T222113Z.txt` from the separate device. Follow it one command at a time. Do not select a Linux volume first. Do not invent a volume label, UUID, or disk number.
3. Do not attempt Linux until the restore script reports `RESTORE PASS` and the EFI partition unmount succeeds.

This branch permits one forced shutdown only. If startup options, Recovery, authentication, Terminal, or the pinned guide is unavailable, stop and obtain separate recovery help. Do not perform another forced cycle, select a Linux volume, or guess input.

## After a visible stock-core Linux recovery

Stop after the first usable internal-screen login. Do not reconnect a cable, test monitor USB, change a display mode, suspend, or select another image.

The later read-only recovery check must establish:

- the unchanged stock/default kernel command line;
- the packaged stock Type-C core identity;
- a usable internal panel and responsive Linux;
- MagSafe-specific and aggregate AC sources online;
- battery status `Charging` or `Full` with coherent fresh telemetry;
- three accepted power-guard samples across 60 seconds;
- Omarchy Stay Awake disabled before unattended use.

An external blank screen is expected and is not a recovery failure on this stock core. A successful stock-core boot is not full DTB rollback.

## After the macOS/Recovery restore route

The pinned guide owns the exact EFI mount, check, restore, and unmount commands. Run one command at a time. Restart only after `RESTORE PASS` and a successful unmount. The next Linux boot must use the unedited stock initramfs and must pass the separate full-rollback verification in the main plan.

## Acceptance before a candidate handoff

This card requires all of the following before it can be released:

1. Independent documentation QA and safety review of this exact text — PASS on 2026-08-29.
2. The exact Git commit and pinned private restore guide available and readable on the separate device.
3. David's read-through confirmation.
4. One attended rehearsal from a healthy stock/default boot using normal shutdowns only. First enter visible startup options, record the exact existing Linux-volume label, select it, and boot the unedited `Arch Linux` entry. Then shut down normally, enter startup options again, and verify `Options` → Recovery authentication → Recovery Terminal → separate-device guide readability. Do not run any guide command, mount the EFI partition, execute the restore, simulate failure with a forced shutdown, or select a candidate.
5. Update this card with the recorded volume label. Then complete a separate review of the rehearsal record and current stock boot identity.

The rehearsal tests the visible picker, stock-selection path, and non-mutating access to Recovery Terminal and the external guide. It does not test a real hang, forced-shutdown safety, the untested restore script, or candidate behavior. Apple owns the documented physical force-off behavior; DEV-147 does not reproduce it on a healthy system. If the Recovery rehearsal is declined or cannot reach Terminal and the guide, candidate release remains blocked.

No candidate boot is authorized merely because this card passes review or rehearsal.
