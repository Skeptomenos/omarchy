# DEV-147 working-image recovery evidence — 2026-08-28

**Host / scope:** One MacBook Air M2 J413/T8112, kernel `7.1.6-1-1-ARCH`; attended recovery after the failed D3 diagnostic startup.
**Approval:** David completed the separately reviewed one-time GRUB recovery and reported an external image, normal built-in screen, and responsive system.
**Repo state:** Recovery followed source checkpoint `bebfba9b98597145803ced62f1279b65059a280c`. This record changes documentation only.

## What happened

David selected the previously working `initramfs-linux-asahi-dpalt.img`, without `usbdiag1`, through the visible GRUB editor. He reports completing all reviewed steps. No physical reconnect was reported. The agent made no driver, cable, package, boot-file, or display-setting change.

This was a separate recovery, not another diagnostic trial. The [D3 failure record](dev-147-usbdiag-startup-failure-2026-08-28.md) remains external-display FAIL and measurement INCONCLUSIVE. Its target-name logging defect remains unfixed.

## Result

One functional display recovery PASS. A new boot is confirmed. Both outputs are connected/enabled and active in the compositor: internal eDP at 2560×1664 / 60 Hz, external DP at 3440×1440 / 99.982 Hz. David confirms both physical images and system responsiveness.

Named GNU build-ID note reads match the expected module identities:

| Loaded module | Build ID | Role |
|---|---|---|
| `dwc3_apple` | `0bb1b6c1d98eba0efc8abe4085670e3ab619b4ab` | Packaged, unmodified USB driver |
| `phy_apple_atc` | `c75fe6ddcee74ac30ad4d6e66d0df2b3acf66525` | Packaged, unmodified USB driver |
| `tps6598x_core` | `8fd9e3d39ee211f439471a812fb5eaa2622f7585` | Unchanged working patched DP core, not the stock core |

Read-only journal, named DRM/power/USB identity, package, hash, and metadata checks establish:

- The fixed-boot, all-priority `journalctl --dmesg` capture retains 1,119 records in 18 pages through 13:48:57 UTC. All cursors are unique; required envelope fields, one-boot identity, and monotonic order validate. The independently read terminal record has identical keys and values; serialized JSON key order differs. This is journal-envelope validation, not diagnostic call-order evidence.
- Four external-DCP crossbar deferrals recover into binding. DCP later reports connected with 14 modes and selects native external video. Startup also includes a 1920×1080 / 60 Hz modeset before returning to native resolution. Its cause is not assigned, and this is not an intentional mode-test pass.
- The target controller `502280000.usb` registers xHCI buses 1 and 2. Only their root hubs appear in both the journal and the current named USB identity snapshot. The monitor hub `0bda:5411` and LG controls `043e:9a39` remain absent. USB startup acceptance stays HOLD; no downstream-device test occurred.
- Battery is 100% / Full; AC, MagSafe, and monitor PD sources report online. This does not prove isolated USB-C charging. Fresh kernel taint is 4100.
- The reviewed capture retains four external EDT, three CAHandler, and three PMU diagnostics, plus existing platform, missing-AVD-firmware, and Wi-Fi messages. No fatal kernel event, WARN trace, loader rejection, or DART/IOMMU fault was observed in that window. Audit suppression totals 461 callbacks. This is not a clean-log or clean-firmware result.
- All 37 readable protected/proof hashes match. The three root-private files retain David's D2 validator as hash provenance, not a fresh agent read. Relevant package versions and both staged-image metadata remain unchanged. The complete prior failed-result 52-file seal verifies and remains preserved.

The raw journal, capture digest, boot identifiers, device-specific records, and local paths remain private. No test suite or build was rerun for this documentation checkpoint.

## Rollback and retained state

The recovery handoff is consumed. Its [historical steps](../plans/dev-147-m2-displayport.md#current-recovery-handoff--previous-working-dp-image-living) remain available but do not authorize another boot. The saved boot default is unchanged. The candidate DTB and patched DP core remain in use; this is not full DTB rollback. An unedited stock-driver boot can still lack external video. Both images, both timestamped backups, earlier failures, and the offline Mac recovery bundle are retained. Mac restore execution remains untested.

## Open

Recovery does not identify why the diagnostic image lost video. Different USB binaries, earlier DWC3 availability, and reboot/device state confound a causal comparison. The unfixed logging guard explains the missing D3 trace only. Full Gate 4b, automatic USB enumeration, firmware findings, reliability, full rollback, and permanent integration remain open.

The [main plan](../plans/dev-147-m2-displayport.md#next-step--offline-correction-design-only-living) owns the next step: an offline correction-design proposal with real OF-name-semantic regression coverage and separate review of the timing variable. Implementation, tests, builds, and another device trial require separate review. No further reboot, hotplug, USB-device test, live swap, mode change, or suspend is authorized by this recovery result.
