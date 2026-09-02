# DEV-147 integrated candidate LG35 switch evidence — 2026-09-02

**Host / scope:** `omarchy-air`, M2 MacBook Air J413, integrated DisplayPort candidate
**Approval:** proceed-and-report tier; David performed the requested monitor switch
**Repo state:** `58ae88015960747452a5b31eacdd143361efdf54` before this evidence commit

## What happened

David disconnected the working LG 27UN83A-W and connected the LG 35 ultrawide
to the lower/front left USB-C port. He reported that the LG35 showed an image
after about five seconds. The operation stayed on boot
`fa500274-a4fd-49e3-a84a-82ec4948b8e3` and did not reload a driver, change a
display mode manually, suspend, or reboot.

## Result

The exact integrated candidate remained loaded:

- kernel: `7.1.6-1-1-ARCH`;
- TIPD GNU build ID: `50ee94a5f8dbae780c676a73b611a7ad5197e47a`;
- selected image: `/boot/initramfs-linux-asahi-m2-displayport.img`, from David's
  boot selection for this boot;
- retained command-line qualification: `disablehooks=encrypt`.

The kernel recorded a complete disconnect and new link setup:

- external HPD was removed at 1028.436 seconds;
- external DPTX disconnected at 1028.472 seconds;
- the new DPTX connection started at 1037.088 seconds;
- the LG USB hub identified at 1037.718 seconds;
- LG USB Controls identified at 1038.104 seconds;
- external HPD asserted at 1039.271 seconds;
- 14 external modes published at 1039.340 seconds;
- the 3440×1440 modeset finished at 1039.596 seconds;
- external DPTX setup completed at 1039.665 seconds.

The native modeset completed about 2.5 seconds after the new link setup began.
This supports David's approximately five-second visible result.

The live mode state changed to the LG35, but connector identity did not. The
DRM mode list contains 14 modes headed by 3440×1440, and DCP selected
3440×1440/99 Hz. The exported EDID still has SHA-256
`546b75f19b98c2863520cc2992f1399b0a9e8a8ee9298d66c19097e5697bc118`
and identifies the prior 3840×2160 LG HDR 4K display. Hyprland also retains the
prior display description. Treat these identity fields as stale hot-switch
metadata. They do not describe the active monitor after the physical switch.
The same metadata class was already observed during the prototype
investigation.

The read-only post-switch snapshot returned:

- `DP-1`: connected and enabled at 3440×1440/99.982 Hz with DPMS on;
- `eDP-1`: connected and enabled at 2560×1664/60 Hz with DPMS on;
- both Type-C partners present;
- MagSafe, aggregate AC, and monitor USB power online;
- battery Full/100%;
- zero failed systemd units;
- no kernel panic, oops, watchdog lockup, DART fault, or IOMMU fault.

David's report proves the physical LG35 image. The successful live commands
prove that Linux remained responsive. DRM and compositor state prove that the
internal output remained active. A direct physical confirmation of the
internal panel after this switch is still open.

Unlike the earlier autonomous LG27 reset, this physical switch re-enumerated
the LG USB hub and LG USB Controls. This is evidence for DEV-163. USB data is
not a DEV-147 acceptance requirement.

## Rollback

This capture was read-only and changed no system state. The installed candidate
retains its existing EFI backup and recovery guide. The documentation change
is reversible through Git.

## Open

- Confirm that the internal panel physically shows a normal image after the
  LG35 switch.
- Track stale EDID and compositor identity after a live monitor switch as an
  experimental limitation. It does not block native video on this result.
- Remove or explain the retained `disablehooks=encrypt` boot-entry token before
  an unqualified production-argument result.
- Keep attached-display suspend unsupported. Do not repeat the failed test.
- Track monitor USB-data reliability only in DEV-163.
