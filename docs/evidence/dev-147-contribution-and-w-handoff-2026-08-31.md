# DEV-147 — contribution preparation and W handoff, 2026-08-31

Scope: David approved refreshing the M2 report and preparing the narrow diagnostic change, then asked for reboot instructions. No upstream message or submission was authorized. Timer-Off testing remains parked. No new kernel/image was built or staged, and no runtime, boot default, package or driver changed.

## Report and patch

The [refreshed M2 report](../research/dev-147-m2-replication-report-2026-08-31.md) remains UNSENT. An append-only pointer preserves the older report. It retains Asahi/fairydust and haripako credit, material AI-assistance disclosure, recipient-policy limits and the distinction between functional results and reliability.

The [patch artifact](../../dev/apple-dp-altmode/contributions/pr289-partner-absence.patch) targets Omarchy Mac PR #289 head `273e93970635e9f2bfeaec47185f93bb1b696d17`, checked unchanged/open through the GitHub API. Only the no-partner wording changes in production. One new test covers no partner, correct port and wrong port. The exact-head runner uses Bash for `*-test.sh`, so the new test need not have executable mode.

| Input or output | SHA-256 |
|---|---|
| Original diagnostic | `f3f78afdf0fb84e1c2b14fc3a25a7336044fcdf784273119a51e694b3ddb0dbe` |
| Original detector | `44bd3d6803011fb88d91e2148da547538e7e8986d00fb0fdc8b2f2c1dbc7f32e` |
| Original test base | `11baacdf613dfea610f6ff37f0e3cdb05b3f5b852d099dd62ba941470e990ac8` |
| Patched diagnostic | `53221eddb6a486ea8e470e4dd64149fc7b5680cc2fe6cb13bcce360743bbfd74` |
| New test | `73e201b9126f31124e15df4cb790441b3fcf5315f58cc84ddbb1cb0662c09915` |
| Exported patch | `424ec77fe795b310861502fe5adf6ae077fbd0e53a318f4b331f0651f7ca49c8` |

The three original files also match their exact Git blob identities. The standalone test uses the real pinned diagnostic and detector, with synthetic device-tree, Type-C and DRM paths. It does not execute the diagnostic against host hardware. New fixture source has no explanatory comments; functional shebang and existing command metadata remain intact. Unrelated upstream source was not rewritten.

SWE checks: the new assertion fails against the original diagnostic with exit 1; the two existing-behavior cases pass. After the wording change, all three cases pass with exit 0. Bash syntax and patch dry-run exit 0. Full connected/wrong-port output comparisons and unchanged detector/test-base comparisons exit 0. The exported patch is byte-identical to the tested patch. Independent code and handoff review found no blocking bug. Independent QA reran the three-case test with a cleared environment and 30-second deadline, checked syntax for all four files and performed a ten-second patch dry-run; every command exited 0. Its saved-file checks confirm RED/GREEN, output preservation and source/patch pins. The aggregate repository suite was not rerun: this is an isolated patch artifact, not integration into the fork's runtime commands or a release claim.

## Fresh machine-side readiness

The 10:27 CEST snapshot finds both native outputs active: internal 2560×1664/60 Hz and external 3840×2160/59.997 Hz. MagSafe and monitor PD are online; battery Full/100%, current 0. Kernel `7.1.6-1-1-ARCH`, installed kernel package and working AppleDRM/TIPD notes match the retained baseline. Before/after/final boot identities agree. These are software checks, not new physical-image attestation or sustained charging proof.

Fourteen saved exit records contain thirteen zero exits and one failure: `/usr/bin/lsusb` is absent, so that attempted command exited 127. No package was installed. A separate bounded read of standard USB `idVendor`/`idProduct` attributes exited 0 and found only root hubs `1d6b:0002` and `1d6b:0003`. Monitor USB data is not accepted. No Type-C partner `usb_mode` attribute was read.

All twelve readable W-source/kernel/packaged-DTB/core/active-boot/backup/recovery digests match the prior pins. Existing W metadata remains root-owned, mode 0600, 19,184,103 bytes, with its recorded modification time. Stock-image and GRUB metadata also match the retained records. The staged W and stock images and GRUB contents remain root-private; they were not freshly hashed. Their byte provenance remains David's accepted staging-validator result, not a new independent read. No persistent `update-m1n1` override exists. Independent saved-file readiness QA passed within these limits.

## Conditional manual boundary

One new attended W/LG27 startup is prepared. Before using it, David must save work, remain present, keep the lid open and the internal screen/system healthy, retain MagSafe and the same LG27/cable/front-lower port, leave monitor USB ports empty, and have the recovery guide on another device. False or uncertain conditions defer the boot. A readiness confirmation was requested; no new physical confirmation or reboot is claimed by this record.

The one-time GRUB edit changes only the normal initrd basename to `initramfs-linux-asahi-dpalt.img`, preserving `/boot/`, every other token and the kernel line. `sudo reboot` is the Terminal command; `initrd` is GRUB editor text, never a Terminal command. No `pr582`, `tipddiag`, `usbdiag` or `usbearly` suffix belongs in this W test. The private handoff in DEV-147 gives the exact steps and stop conditions; the [living plan](../plans/dev-147-m2-displayport.md#minimum-remaining-path-living) owns release and consumption.

After startup, capture physical screen reports, exact selected filename, loaded identities, display, USB, power and a bounded boot-journal window before any reconnect. External-only failure with healthy internal Linux means preserve the setup for evidence. Internal/system failure takes priority and uses the retained recovery guide, not blind commands or boot loops. The GRUB edit is temporary, but W and normal startup both retain the prototype DTB. Full rollback and Mac restore execution remain untested. No default-on integration follows.
