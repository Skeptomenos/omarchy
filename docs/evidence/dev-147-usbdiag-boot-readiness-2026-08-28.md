# DEV-147 — diagnostic boot readiness, 2026-08-28

Host / scope: the existing M2 J413/T8112 prototype; one attended diagnostic restart only. Source base: `093276d83ae8420da5032fc8677b4dee26f52daa`.

## Approval and physical report

David asked what comes next after D2 staging. He confirmed MagSafe and the monitor on the lower USB-C port, no other active work, both physical screens normal, and no USB device attached to the monitor. These reports clear the physical readiness hold. The [diagnostic plan](../plans/dev-147-usb-startup-diagnostic.md#current-d3-handoff--one-user-selected-restart) now holds the exact user-selected handoff. No agent reboot or device action is authorized.

## Read-only checks

- `uname -r` and `pacman -Q` match kernel `7.1.6-1-1-ARCH` and the seven pinned package versions. No package lock or persistent update-m1n1 override is present.
- Named battery and power attributes report 100% / Full, AC online, and both MagSafe and front/lower monitor power sources online. This does not prove isolated USB-C charging.
- All 37 readable records from the 40-row D2 protected/proof set match with `sha256sum`. This includes both timestamped boot backups, both Mac restore scripts/guides, the active candidate boot chain, and packaged kernel/driver files.
- The three root-private protected files—stock initramfs, GRUB configuration, and working DP initramfs—were not reread. Their checks retain the [validated D2 execution](dev-147-usbdiag-staging-2026-08-28.md) as provenance. The new root-private diagnostic image was likewise not independently rehashed.
- The readable source image still hashes to `a11bf3a2bac1f105aa57b08ce9fad338c68882851247f7524d09f4b7c94188ca`. The completed private staging helper still hashes to `aaedcffd6f614864406055e63a9e3f88e885c44d9ef74e48469c3b3aadfc8c51`; it was not executed again.
- `stat` confirms the diagnostic image remains root-owned, mode 0600, one link, and 19,647,739 bytes. Working-image metadata and the root-private check directory also match.
- `sha256sum --check --quiet SHA256SUMS` passes all 12 entries of the frozen D2 staging-result checkpoint. Its raw evidence remains private and unchanged.
- Named live DT properties, the current boot identity/taint baseline, and compositor state were read without sweeping sysfs. No partner `usb_mode` read occurred. A prior readiness attempt found `lsusb` unavailable; no package was installed, and software enumeration was not substituted for David's physical check.

One read-only orchestration selector initially expected the candidate digest in the console transcript, which does not print it. The selector stopped before hashing. Reading the saved JSON text field resolved that assumption. No staging helper or test was invoked.

## Handoff and rollback

The handoff changes only the initramfs filename in the visible pre-login GRUB editor. It preserves the kernel and its arguments. Cancel if the entry differs or the menu is missed. No repeat test, persistent entry, live swap, cable action, mode change, or suspend is included.

Before boot, Esc cancels the entry edit. Leaving the new image unselected retains normal startup. After a diagnostic boot, the normal stock-image boot does not restore the original DTB; the candidate DTB stays installed and external video may be unavailable. The [main plan](../plans/dev-147-m2-displayport.md#gate-6--prove-full-rollback-then-retain-the-evidence) owns full rollback; both backups and the private offline macOS bundle remain intact. Mac restore execution is still untested.

## Open

No diagnostic boot, startup trace, automatic USB-enumeration result, reliability result, or rollback proof is claimed. D3 remains pending until David performs the one-time selection and reports the physical outcome. The next capture must use that new boot's identity and complete all-priority window. Full Gate 4b and all later acceptance gates remain open.
