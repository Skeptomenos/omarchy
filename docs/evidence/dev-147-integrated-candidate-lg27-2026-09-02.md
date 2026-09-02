# DEV-147 integrated candidate LG27 result

**Date:** 2026-09-02
**Boot ID:** `fa500274-a4fd-49e3-a84a-82ec4948b8e3`
**Result:** Qualified video PASS

## Candidate identity

David selected this one-boot GRUB line:

```text
initrd /boot/initramfs-linux-asahi-m2-displayport.img
```

He reported a normal internal display and responsive Linux before attaching the
external monitor. The loaded `tps6598x_core` GNU build-ID note contains
`50ee94a5f8dbae780c676a73b611a7ad5197e47a`. This exactly identifies the fresh
integrated candidate. The running kernel is `7.1.6-1-1-ARCH`. Active
`boot.bin` remains the accepted candidate with SHA-256
`203ab7027536c8d16f373d02c1f6346a5c34cfe095a9dafd0cfe37d2b354090c`.

The boot command line still contains `disablehooks=encrypt`. David did not
report adding it during this selection. It is a retained boot-entry
qualification. It does not change the candidate module, device tree, display
driver, or display mode. A later boot-configuration cleanup must own its
removal. This candidate video result remains qualified until a production-args
boot exists.

## Initial external attach

Before attachment, `DP-1` was disconnected and `eDP-1` was active at
2560×1664/60 Hz. Both DCP nodes reported `okay`. Only the MagSafe Type-C partner
was present. MagSafe was online, the battery was Full/100%, and no systemd unit
or job had failed.

David attached the LG 27UN83A-W to the lower/front left USB-C port with the
known-good cable. He reported that the external image appeared quickly, in
about five to six seconds.

The kernel timeline agrees with that observation:

- external DCP connection began at 271.973 seconds;
- the LG USB hub identified at 272.349 seconds;
- LG Monitor Controls identified at 273.742 seconds;
- display HPD asserted at 274.187 seconds;
- 16 modes published at 274.256 seconds;
- the 3840×2160 modeset finished at 274.521 seconds;
- the external DPTX connection completed at 274.545 seconds.

Compositor state later showed LG HDR 4K on `DP-1` at
3840×2160/59.997 Hz with DPMS on. `eDP-1` remained enabled at
2560×1664/60 Hz with DPMS on. The lower/front controller partner was present,
monitor power delivery was online, MagSafe remained online, and the battery
remained Full/100%.

## Automatic link recovery

The same boot recorded one autonomous link and USB reset after the initial
success:

- the LG USB hub disconnected at 508.276 seconds;
- the external xHCI controller began removal at 509.424 seconds;
- DCP reported a FIFO error and removed HPD at 509.692–509.696 seconds;
- external DPTX disconnected at 509.756 seconds;
- xHCI and external DPTX initialization restarted at 516.752–516.759 seconds;
- HPD asserted again at 518.986 seconds;
- 16 modes republished at 519.060 seconds;
- the 3840×2160 modeset finished at 519.330 seconds;
- external DPTX completed at 519.344 seconds.

The visible display path recovered in about 9.6 seconds from HPD removal to
modeset completion. The Type-C partner and monitor power were present in the
later snapshot. At 685 seconds, both displays remained enabled at their native
modes with DPMS on. No later DPTX, HPD, FIFO, xHCI-removal, or USB-disconnect
transition was present.

The monitor USB hub and LG controls did not re-enumerate after the reset. Only
the two xHCI root hubs remained. This is a DEV-163 USB-data result. It is not a
failure of the recovered DEV-147 video path.

## Safety and boundary

No fatal kernel, DART, IOMMU, panic, oops, or watchdog pattern was present.
Known EDT frequency, CA data, and PMU diagnostics recurred during the successful
modesets. No driver reload, mode change, reconnect request, or system mutation
was performed by the read-only checks.

The physical external image and five-to-six-second timing are David's
observation. The internal image is physically confirmed before attachment;
post-attachment internal activity is confirmed by compositor state but still
needs David's physical confirmation. Attached-display suspend remains unsafe
and must not be repeated.
