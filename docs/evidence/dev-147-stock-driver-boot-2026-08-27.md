# DEV-147 stock-driver boot and GRUB handoff evidence — 2026-08-27

> Public archival copy, prepared 2026-08-28. Actual boot IDs are redacted where present. Local evidence links are marked as private. Commit references identify the retained private branch unless they name upstream source. Recorded hashes and past QA results describe the private originals, not this edited export. Commands below are historical records, not instructions to run the public helpers.

**Host / scope:** `omarchy-air`, M2 J413/T8112. Read-only diagnosis after a user-run reboot; documentation/history correction only.
**Approval:** David reported the dark external screen and Bash error, and asked what went wrong. His earlier request covers retaining the trial history. No new system change or reboot was performed by an agent.
**Repo state:** `a9d6b37b88b403b0c2b05b7136d93325fca1f65a` before this correction; feature worktree clean, runtime still `/home/david/o-live`.

## What happened

David rebooted, reported no external image, and entered `initrd /boot/initramfs-linux-asahi.img` in the desktop terminal. Bash returned `command not found: initrd`. That line was meant as existing GRUB boot-entry content, not a terminal command. The handoff did not make that distinction clear enough. The rejected command did not select an image or change the boot entry.

## Result

At 22:21:40 CEST, `uptime -s` returned `2026-08-27 22:18:10`. The kernel remains `7.1.6-1-1-ARCH`; linux-asahi, m1n1, Mesa, and OpenSSL versions are unchanged.

- The loaded core's GNU build note is `73c3659d1653dd2508ae81147a5e5cd4c877a060`. `readelf -n` gives that exact ID for the packaged stock core. The candidate's ID is different: `8fd9e3d39ee211f439471a812fb5eaa2622f7585`. Loaded module taint is empty.
- DRM reports external `card2-DP-1` disconnected/disabled and internal `card2-eDP-1` connected/enabled. External DCP remains `okay`. Monitor `0-003f` and MagSafe `0-003a` partners are present. The user reports the physical external screen is dark.
- Battery is 100%, Full. The staged image still exists as a root-owned 0600 regular file of 19,184,103 bytes, with unchanged 21:58:23 CEST modification time. Its protected contents were not re-read.
- `sha256sum` matches the active candidate boot, both stock backups, private candidate image, and packaged stock core to their recorded pins.

This proves that the running core is stock. Together with the user's terminal attempt, it is consistent with normal startup without the one-time edit. The actual selected initramfs filename was not independently traced. Do not classify this as a candidate startup failure, successful candidate startup, clean-firmware result, or full rollback proof.

The raw read-only output and normalized report (retained privately) have SHA-256 `ece680c7561dcf76cc0e0597851efbd531d5185d19c6cf00a993db149dc707fb`. The pre-update Linear snapshot (retained privately) preserves the description and all 12 existing comments, SHA-256 `b58f8ab0994e4172ea632354447fb8ef4d791bfbf510214bf5ac020739d22a25`. Earlier evidence is unchanged.

## Rollback

No rollback is needed for the rejected Bash command. The current driver is already stock, but the prototype DTB is still active. Full rollback remains the separate [plan gate](../plans/dev-147-m2-displayport.md#gate-6--prove-full-rollback-then-retain-the-evidence). Keep the staged image, both backups, and recovery bundle. Do not repeat the live module swap.

## Open

Before another reboot, ask whether David saw a menu listing `Arch Linux`. `/etc/default/grub` requests a visible five-second menu; its actual appearance/timing is unconfirmed. Independent review of the installed manual confirms: arrow keys select, `e` opens the entry editor, Ctrl-x boots the edit, and Esc cancels. An arrow key stops the visible menu countdown; do not prescribe blind keys through earlier boot stages.

The corrected [Gate 4b instructions](../plans/dev-147-m2-displayport.md#gate-4b--user-selected-one-time-startup-test) distinguish the single desktop reboot command from editing the existing `initrd` filename before Linux starts. Candidate startup, behavior tests, firmware findings, full rollback, and Mac restore execution remain open. No test suite, source code, package, boot configuration, live driver, or display setting was changed by an agent.

Independent documentation QA: PASS. All 20 local links, two anchors, 10 command-note paths, and two evidence hashes passed. Four earlier evidence records remain unchanged. `git diff --check` passed. The review preserved the distinction between a confirmed stock running core and an inferred missed GRUB edit.
