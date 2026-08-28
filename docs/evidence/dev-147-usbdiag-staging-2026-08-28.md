# DEV-147 diagnostic staging evidence — 2026-08-28

Host / scope: J413/T8112 on `omarchy-air`, kernel `7.1.6-1-1-ARCH`. Record David's returned staging result and corroborating read-only checks. No agent-run privileged command, driver action, or diagnostic boot.

Approval: David ran the exact private command from the [reviewed D2 preparation](dev-147-usbdiag-staging-helper-2026-08-28.md) and supplied the complete output. That action completes staging only; it does not approve D3.

Source checkpoint: `be0ccdea893bd6909e859a89193f579705dfe5bf` on `codex/dev-147-m2-dp-altmode-public`. The staging helper and its 38-test evidence are unchanged.

## Result and provenance

David's transcript ends with `STAGING ONLY PASS: /boot/initramfs-linux-asahi-dpalt-usbdiag1.img`, the retained directory `/boot/.dev147-usbdiag-stage.ESqzIgLr8I`, and the normal-boot-unchanged warning. No refusal or failure message appears. The original attachment has SHA-256 `1065ecc6df3a412a2e6ce76913714346b8d86f8eb8521aa47a2a9a5f83ee47f5`; its text is preserved privately.

The final private helper still hashes to `aaedcffd6f614864406055e63a9e3f88e885c44d9ef74e48469c3b3aadfc8c51`. Independent static comparison found exactly 40 matching hash/path pairs: 32 protected files and eight D1 proof files. None is missing, unexpected, mismatched, or duplicated. The helper was not invoked or sourced for this comparison.

In that reviewed helper, the final PASS follows bounded copying, atomic no-replace publication, final image hash/size/mode/single-link validation, repeated live preflights, matching before/before-publication/after pin logs, sync, and completion-marker finalization. Accept these checks as David's successful validator execution. The paste does not separately capture a numeric exit status, and the agent did not reread root-private image bytes or logs.

## Independent read-only checks

`stat -c '%F|%a|%u|%g|%h|%s|%n'` returned the following metadata:

| Target | Observed metadata |
|---|---|
| Diagnostic image `/boot/initramfs-linux-asahi-dpalt-usbdiag1.img` | Regular file; 19,647,739 bytes; mode 0600; UID/GID 0; one link. |
| Retained staging check directory | Directory; mode 0700; UID/GID 0. |
| Working DP image `/boot/initramfs-linux-asahi-dpalt.img` | Regular file; 19,184,103 bytes; mode 0600; UID/GID 0; one link. |

The diagnostic image's validated hash remains `a11bf3a2bac1f105aa57b08ce9fad338c68882851247f7524d09f4b7c94188ca`. Its staged-byte check comes from the user-run helper, not the independent metadata call.

`uname -r` and `pacman -Q linux-asahi m1n1 mesa mkinitcpio openssl coreutils kmod` still match the pinned kernel and seven package versions. The helper's own SHA-256 check passed. `sha256sum --check --quiet SHA256SUMS` returned zero for both the frozen 4,528-file D1 archive and the frozen 3,146-file D2 preparation archive. Neither archive was edited or reused for outputs. The dev link still resolves this session to `/home/david/o-live`; no live checkout change occurred.

## Disposition and rollback

D2 is complete: user-run staging PASS, with independent metadata and source/output review. Pending staging instructions are superseded. Keep the new image and root-private check directory. Do not rerun the final helper, the superseded private copy, or any old gate.

The distinct image remains unselected. Leaving it unselected preserves the normal boot choice. Staging did not replace the working image, stock image, GRUB, EFI boot bundle, or installed modules. Normal boot still uses the pre-existing experimental DTB; it does not perform full rollback. Keep both stock backups and the Mac restore bundle. Do not remove any artifact as cleanup.

## Open

D3 remains unauthorized. Before one attended diagnostic restart, confirm saved work, a healthy internal screen, battery strictly above 50%, recovery readiness, and David's attendance. Recheck the actual front/lower port, cable/orientation, MagSafe, HDMI/input settings, and any downstream USB/storage devices. Unknown physical state is a hold.

Only after that review and approval should a new GRUB handoff name `initramfs-linux-asahi-dpalt-usbdiag1.img`. The old working-DP filename is not this diagnostic image. No reboot or live driver/device action occurred in this checkpoint. Startup, USB enumeration, firmware interpretation, reliability, full rollback, release, and upstream contribution remain separate. The [living diagnostic plan](../plans/dev-147-usb-startup-diagnostic.md) owns the next action.
