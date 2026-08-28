# DEV-147 C4 E boot-readiness evidence — 2026-08-28

**Host / scope:** M2 J413/T8112; read-only readiness checks and a conditional one-time E handoff with separate W recovery.
**Approval boundary:** Prepare the exact handoff. David confirms all work is saved and the Mac recovery guide is available on another device, and asks to reboot when ready. Availability/read-through of the new E/W handoff outside Linux, final task release, and choosing this exact case remain required. No reboot occurred.
**Repo state:** Public checkpoint `eb501fb966be5f6da009ff23b9b741e10f1ccf6f`; source, images, helpers, and sealed evidence remain unchanged.

## Result

Physical setup is confirmed and the recorded machine checks pass. Independent saved-readiness QA and exact handoff safety review pass. The [main plan](../plans/dev-147-m2-displayport.md#current-c4-handoff--one-user-selected-e-boot-living) owns the prepared conditional E procedure and its separate conditional W recovery. **E is staged but UNBOOTED.** This record is not a startup, USB, charging, reliability, or boot-safety result.

David confirmed MagSafe, the monitor on the front/lower left USB-C port, a physical image on both screens, normal responsiveness, and nothing connected to the monitor's USB ports. He later confirmed all work was saved, requested reboot when ready, and confirmed the Mac recovery guide was available on another device. Those holds are superseded by his reports. The new E/W handoff must also be available/read outside Linux, and he must choose the exact released case before action; another chat reply is not intrinsically required to satisfy these remaining conditions.

## Read-only checks

| Check | Recorded result and limit |
|---|---|
| Kernel, packages, dev link | `uname -r`, the seven-package `pacman -Q` check, and `omarchy dev status` agree with the pinned environment. Kernel is `7.1.6-1-1-ARCH`; the dev-linked live checkout remains untouched. These orientation results were retained from the same turn, not rerun solely for this record. |
| Power status | Battery 100%, `Charging`; AC, MagSafe PD, and front-port PD report online. This does not prove USB-C-only charging. |
| Integrity | All 37 readable fixed-row hashes and five separate artifact identities match. Root-private image/GRUB bytes and logs still rely on the qualified [C3 user-run validator](dev-147-usbearly-staging-2026-08-28.md), not new privileged reads. |
| Retained seals | C3 preparation's 601-file manifest, manifest identity, and 16 fixed pins pass. The separate 28-file C3 staging-result seal and its manifest identity also pass. |
| Metadata and absence checks | E, W, and the retained failed-v1 image keep their expected root-private ownership, mode, single-link status, and sizes. No package lock or persistent `update-m1n1` override is present. Metadata is not an independent image-byte check. |
| Current display and loaded identities | Internal 2560×1664 at 60 Hz and external 3440×1440 at 99.982 Hz are present. Working patched TIPD and packaged DWC3/ATC build IDs match. Taint is 4100. This is readiness in the existing working session, not an E boot result or a clean-log claim. |

No fresh complete journal or monitor-USB enumeration result is claimed here. The private boot identity is retained only for comparison with a later boot and is not published. After any E selection, a new boot identity and David's exact selected filename are required: E and W use the same loaded module build IDs, so those IDs alone cannot establish which image booted.

E remains the C2 image, `initramfs-linux-asahi-dpalt-usbearly1.img`, 19,191,513 bytes, SHA-256 `4d4f0557af57eebcc33322f004bcc7968254e644b069a11102375df0b31a52ae`. It adds packaged DWC3 availability and the required indexes, not diagnostic or rebuilt control modules. Zero diagnostic markers are expected. The [C2 record](dev-147-c2-offline-preparation-2026-08-28.md) owns its archive proof; the [C3 record](dev-147-usbearly-staging-2026-08-28.md) owns staging and protected-byte provenance. No duplicate sudo read or staging replay is needed.

## Handoff review and remaining prerequisites

The exact procedures live only in the main plan. They preserve the stock-to-E filename substitution, unchanged kernel line/arguments, visible-GRUB-only editing, and missed-edit stop without retry. The [GNU GRUB menu editor reference](https://www.gnu.org/software/grub/manual/grub/html_node/Menu-entry-editor.html) supports Ctrl-x to boot the temporary edit and Esc to cancel. A direct page fetch timed out; the primary GNU result supplied those instructions.

Static handoff review clarified the recovery stock-to-W filename and the cancel/missed-edit stop. It also resolved the recovery branch: one normal W restart requires responsive Linux, a usable screen, and a safe restart; unresponsive Linux, no usable screen, or unusable visible GRUB requires the retained offline Mac guide instead. These were documentation corrections before use, not boot failures. Independent review accepted the corrected handoff. Public-document QA/review is separate; the final task response must release this exact case before use.

Saved work and the Mac guide on another device are confirmed. After the final task response releases the case and before manual action, David must choose this exact single E case and its conditional recovery and also have read the complete new E/W handoff with it available outside Linux. Keep the Mac guide available, the lid open, battery strictly above 50%, and all cables, port/orientation, monitor input/modes, HDMI connection, and empty downstream USB ports unchanged. Any changed setup, power, kernel/package, screen-health, or responsiveness condition requires a new review.

Missing monitor USB devices alone with healthy displays is HOLD, not a recovery trigger. Safety loss takes priority over evidence capture. One conditional W recovery is distinct from the old consumed recovery handoff and is not a second test. The Mac guide has not been runtime-tested; never use blind keys, invented identifiers, or repeated power cycles.

Normal boot selection remains unchanged, and neither W nor normal stock boot restores the original DTB. Keep all images, both timestamped backups, both Mac restore bundles, and all evidence. B/G images remain unprepared; no boot ladder, retry, reconnect, USB-device test, mode change, suspend, live swap, permanent integration, or upstream submission follows. D3 video causality remains unknown and full Gate 4b/USB acceptance stays HOLD.
