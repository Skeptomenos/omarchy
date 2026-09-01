# W attach-after-login — 2026-09-01

Result: DEV-147 Case B PASS with one documented boot-argument qualification. The M2 MacBook Air booted the accepted W image without an external monitor. LG27 video became active after login when David attached the known-good cable and woke or powered the monitor. The internal display and Linux stayed healthy.

## User-observed sequence

David kept the external monitor disconnected, rebooted, followed the exact W-image selection, and completed login on the internal display. He then attached the monitor under the coordinated instruction from the boot-error task. That task records that the monitor was turned on or woken before the image appeared. David reports images on both physical displays and a responsive system.

The temporary GRUB edit selected:

```text
initrd /boot/initramfs-linux-asahi-dpalt.img
```

The same combined boot appended `disablehooks=encrypt` to test a separate boot warning. `/proc/cmdline` confirms that token. It is temporary and did not change W, the kernel, DTB, display modules, saved GRUB configuration, or display settings. The result is accepted as a functional attach-after-login video test. A later integrated candidate must still pass with its intended production arguments.

## Captured identity and result

Boot ID: `9ea6173e-8683-4a67-9b66-212b006b94df`.

| Area | Observation |
|---|---|
| Kernel/package | `7.1.6-1-1-ARCH`; `linux-asahi 7.1.6.asahi1-1` |
| TIPD | `8fd9e3d39ee211f439471a812fb5eaa2622f7585`, matching the accepted patched core |
| AppleDRM | `dd5e291114047bb4d7c83a529cddb4f4ac9292d7`, matching the packaged working driver |
| M2 external DCP | Device-tree status `okay` |
| Internal | eDP-1 connected and enabled at 2560×1664/60 Hz; DPMS on |
| External | LG HDR 4K DP-1 connected and enabled at 3840×2160/59.997 Hz; DPMS on; 16 advertised modes |
| Layout | External starts at compositor x=1600 and does not mirror eDP-1 |
| Power | MagSafe controller and monitor controller online; aggregate AC online; battery Full/100% |
| System | Zero failed systemd units and zero active systemd jobs at capture |

The external-DCP sequence records disconnect/connect callbacks at 288.417/288.451 seconds after boot, HPD asserted at 290.635 seconds, a 4K mode request at 290.751 seconds, and another connected callback at 290.992 seconds. The known EDT frequency, CAHandler data-version, and PMU diagnostics recur. A separate bounded scan finds no kernel BUG/panic/Oops, DART/IOMMU fault, RTKit/coprocessor crash, or AFK exhaustion on this boot.

## Provenance and limits

David verified W immediately before the reboot with SHA-256 `ae8f1ed7f4f258f89931209cd7de6030be9f6875372d7329151b822a6ba2281f`. The selected filename and physical pixels are user provenance. The boot ID, command line, module notes, DTB status, DRM/compositor modes, power state, systemd state, and bounded kernel messages are same-boot software observations.

The exact physical attach-to-image duration was not measured. Because the monitor needed a wake or power action, this result does not prove that cable attachment alone wakes a sleeping monitor. It does prove video after boot-without-monitor and later attach on the accepted display stack.

No reconnect loop, second-monitor switch, suspend, module change, boot-file write, mode command, USB-data test, or upstream action occurred during the DEV-147 capture. `disablehooks=encrypt` is a separate one-boot variable and is not part of the external-display implementation.
