# DEV-147 — post-C4 display loss, image selection unconfirmed

Date: 2026-08-28. Scope: one M2 J413 front/lower left USB-C setup after the intended E handoff. Public source checkpoint before this record: `4aaee3164c28c919b969fe1b7e5e276fee85ee66`.

## Outcome and attribution

David reports that the internal screen works and Linux responds, but the external monitor has no image after reboot. Private comparison confirms a new boot since the [readiness checkpoint](dev-147-usbearly-boot-readiness-2026-08-28.md). The exact selected initramfs filename is still unconfirmed. This is a confirmed post-reboot display loss, not a verified E boot or E failure.

E remains staged. W and E use the same packaged USB module IDs and working patched TIPD core. Their loaded identities cannot distinguish the image, and zero diagnostic markers cannot resolve that ambiguity. The earlier [D3 failure](dev-147-usbdiag-startup-failure-2026-08-28.md) and [successful W recovery](dev-147-dp-recovery-2026-08-28.md) remain separate immutable results.

## Read-only observations

| Check | Result and limit |
|---|---|
| Display | Internal `eDP-1` active at 2560×1664 / 60 Hz. `DP-1` disconnected/disabled and absent from the compositor. This agrees with David's report. |
| Loaded modules | Packaged DWC3 build ID `0bb1b6c1d98eba0efc8abe4085670e3ab619b4ab`; packaged ATC `c75fe6ddcee74ac30ad4d6e66d0df2b3acf66525`; patched TIPD `8fd9e3d39ee211f439471a812fb5eaa2622f7585`. Shared W/E identities, not image proof. |
| Power | Battery 100%, Full. AC and both PD sources online. This does not prove USB-C-only active charging. |
| USB | Controller `502280000` exposes root hubs `1d6b:0002` and `1d6b:0003` only. Monitor hub `0bda:5411` and LG controls `043e:9a39` are absent from the named USB identity snapshot. |
| Kernel/packages | Kernel `7.1.6-1-1-ARCH` and seven package pins unchanged. No package lock or `update-m1n1` override. |
| Integrity | All 37 readable rows from the 41 expected protected/proof records match. Four root-private protected files and staged E bytes still rely on the qualified [C3 user validation](dev-147-usbearly-staging-2026-08-28.md), not a new privileged read. Image metadata is unchanged. |

`lsusb` was unavailable and returned 127. Named USB sysfs identity attributes supplied the bounded check; no package was installed. No Type-C partner `usb_mode` read was made.

## Fixed kernel envelope

The saved window spans 2026-08-28 19:32:27.901–19:39:08.485 UTC. Sixteen pages contain 1,012 unique, monotonic records from one boot. The last printed record matches the capture-start terminal record and an independent reread. The final `--show-cursor` marker differs from that printed record because of the time-bounded scan. Pagination uses per-record cursors; scan-end marker equality is not claimed.

Twelve `dp-xbar` `-517` deferrals subsequently bind. External DCP boots and reports `connected=0`, `valid_mode=0`, and `nr_modes=0`. The window has no later `connected=1` or external mode. Two secondary/no-timing messages are retained. These observations do not establish why video failed.

No external EDT, CAHandler, or PMU message appears while the external pipeline is inactive. This is not a clean-firmware result. Internal CAHandler and PMU `e00800d8` each appear once. Existing PMGR, MTP, missing AVD firmware, Wi-Fi, and wireless-extensions deprecation warnings remain. No kernel WARNING trace, BUG, panic, or DART/IOMMU fault was found in this window. The log reports 457 suppressed audit callbacks; it is not an unrestricted completeness claim.

Zero diagnostic markers are expected for uninstrumented E. Their absence is not a trace failure, a call-order result, or proof that E was selected.

## Current boundary

The [main plan](../plans/dev-147-m2-displayport.md#current-handoff--post-reboot-selection-hold-living) owns the selection HOLD. The intended E handoff is consumed. Obtain David's exact selected filename; do not retry E. The prepared one-use W recovery received conditional safety-review approval only if exact E selection is confirmed. It is not released or performed. A missed, other, or uncertain selection must be resolved first.

Saved work and access to the offline Mac guide were confirmed before this reboot. Keep cables and settings unchanged. The agent made no privileged call, further reboot, reconnect, tracing/helper/test execution, or configuration change. Do not duplicate C3 validation with another sudo read. Preserve all images, backups, and raw evidence privately. Normal boot selection is unchanged; neither normal boot nor W restores the original DTB, and Mac restore execution remains untested.

Startup USB/full Gate 4b remains HOLD. B/G images remain unprepared. This record establishes no cause, fix, reliability, boot-safety guarantee, or upstream submission. Boot identities, raw journal, host identifiers, and private capture paths are excluded.
