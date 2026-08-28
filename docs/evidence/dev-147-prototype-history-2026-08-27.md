# DEV-147 prototype history — 2026-08-27

> Public archival copy, prepared 2026-08-28. Actual boot IDs are redacted where present. Local evidence links are marked as private. Commit references identify the retained private branch unless they name upstream source. Recorded hashes and past QA results describe the private originals, not this edited export. Commands below are historical records, not instructions to run the public helpers.

Status: immutable dated account through the first successful Gate 3 live session. Later corrections belong in a dated addendum. Use the [living plan](../plans/dev-147-m2-displayport.md) for current decisions and next actions.

Host/scope: `omarchy-air`, MacBook Air M2 J413/T8112, kernel `7.1.6-1-1-ARCH`. David authorized a contained prototype on this machine and ran the privileged gates himself. He later asked to reconcile the plan while keeping the history.

The original Linear issue snapshot is retained privately. It preserves the pre-reconciliation description and all nine existing comments verbatim, including superseded claims and incorrect advice. It is not part of this public export. The former guide is preserved on the private archival branch at `8db5ef5b:docs/apple-silicon-external-display.md`. This account does not replace the raw evidence or rewrite those records.

Original issue snapshot SHA-256: `10d59c0435d8a9c190339d6f543527130435e2a6aa84c6504722b93833e0fb74`.

## Historical stock baseline and initial research

Before activation, only the internal `eDP-1` connector existed. External `dcpext` was disabled; its alias and both USB-C `displayport` properties were absent. The packaged core was in-tree, and no persistent `update-m1n1` override existed. These were the original baseline, not the state after Gate 3.

The [haripako reference](https://github.com/haripako/dp-altmode) targeted M1 `t8103-j293`. Its installer, rebuild script, DTB, and board/mux constants were not run or installed on the M2. The investigation found the generic HPD change useful, while the M2 route needed its own J413/T8112 device-tree work.

The selected source changes are preserved in the repository:

- Base: Asahi `asahi-7.1.6-1`; the reference Type-C base matched that source.
- [J413 DT patch](../../dev/apple-dp-altmode/t8112-j413-dp-altmode.patch): M2 subset from `ad272ad5d6742869cdd13320e43f9ed01bd1fb33`.
- [CD321x HPD patch](../../dev/apple-dp-altmode/tipd-cd321x-hpd.patch): `3d28209d04c77904e9909b6ab52046910c585a55` and `1aab123a6d57feae519268f55119c82e52e4adac`.

Only the front/lower USB-C controller `0-003f` received the DisplayPort route, using ATC PHY1 and mux index 2. The rear/upper `0-0038` route stayed unchanged. David moved the cable to the front/lower port. The full fairydust kernel, audio, SIO, suspend always-on, and `appledrm` patches were excluded. This was a video-only experiment, not adoption of the whole reference.

## Build, baseline, and recovery preparation

1. Gate 1 build/review was recorded on 2026-08-26 UTC in [the first build checkpoint](https://linear.app/helmus/issue/DEV-147/usb-c-displayport-external-monitor-unavailable-on-m2-macbook-air#comment-a4e4bf46). Commit `fb48bf6c` added the contained prototype. Stock DTB/boot reproduction was byte-for-byte; only the J413 candidate DTB changed. The candidate module's vermagic, dependencies, and defined symbols matched stock; only the reviewed DRM/fwnode imports were added.
2. David reported running the headers package-add command. The actual module build used matching headers extracted privately from the pinned package, not a proven system header installation. The build checkpoint records that no installed headers or package-owned kernel files changed.
3. The managed tool namespace showed EFI read-only while host fstab selected read-write. Gate scripts were tightened to verify EFI identity and use checked, trapped read-write transactions with return to read-only. This distinction was not evidence that the host was already read-only.
4. David ran `00-baseline-and-backup.sh` and supplied `Gate 0 PASS`. Independent verification was recorded on 2026-08-27 in [the backup checkpoint](https://linear.app/helmus/issue/DEV-147/usb-c-displayport-external-monitor-unavailable-on-m2-macbook-air#comment-79a5f258). `20260826T222113Z` identifies the backup/stage set; it is not a claimed observation time for that verification. Both stock backups matched, and the privileged baseline captured stock boot, initramfs, and GRUB hashes.
5. The initial recovery note covered Linux only. Gate 2 was held while the out-of-band recovery gap was resolved. Partition presence was not accepted as proof of usable recovery.
6. David confirmed normal macOS boots and Recovery is accessible, but chose not to visit or rehearse either now. [That choice](https://linear.app/helmus/issue/DEV-147/usb-c-displayport-external-monitor-unavailable-on-m2-macbook-air#comment-a2e42c80) was recorded as user attestation, not a tested EFI restore.
7. Commit `8db5ef5b` added the offline Mac recovery script and guide. They need no editor, Linux filesystem, or network. [Recovery preparation](https://linear.app/helmus/issue/DEV-147/usb-c-displayport-external-monitor-unavailable-on-m2-macbook-air#comment-b96f082d) passed static checks. The helper defaults to a check; restoration requires explicit root-only execution. The original Gate 0 note and backups remained unchanged. Runtime execution in macOS was not tested.

The [saved build helper](../../bin/omarchy-dev-dp-altmode) records a Linux 7.1 Kbuild pitfall: external module-output overrides can overwrite the header Makefile. The successful path used fresh private headers, cleared output overrides, kept the working directory equal to the module source, invoked the header Makefile explicitly, and rechecked its hash after the build. The saved module build log (retained privately) records successful CC, LD, MODPOST, and BTF steps. It is the successful build log, not a retained log of every earlier build attempt.

The persistent stage was `/home/david/o/.dev147-stage` on ext4. The original `/tmp/omarchy-dev147-m2-dp` checkout disappeared on reboot because `/tmp` is temporary. The branch and persistent artifacts survived. On 2026-08-27, the branch was restored as a checkout at `/home/david/o/.dev147-stage/prototype` for this documentation reconciliation. The old build command's `/tmp` cache paths are historical, not instructions to rebuild the current stage.

## Recorded automated QA

The recovery-preparation checkpoint recorded:

- Focused tests: 7/7 passed.
- Command metadata: 455 passed.
- Syntax checks: 458 passed.
- Independent safety review: PASS.
- Aggregate `./test/all`: exit 1; 5 of 233 unchanged tests failed. Three tests lacked the `omarchy-pkgs` checkout. `network-qr` failed sandbox route detection. `windows-vm-compose` attempted a real credentials write, which the sandbox blocked. No unsandboxed retry was made.

The full-suite log (retained privately) retains the failures. This history does not describe the suite as all green. Later live integrity checks were separate read-only checks, not full-suite reruns.

## Gate 2 — activation succeeded, then DTB-only boot succeeded

David ran `02-activate-dtb.sh` and supplied `Gate 2 activation PASS`. The [activation checkpoint](https://linear.app/helmus/issue/DEV-147/usb-c-displayport-external-monitor-unavailable-on-m2-macbook-air#comment-9f01ae3c) verified the candidate active boot, both stock backups, and the Mac script/guide copied to EFI. It did not yet claim the new DTB had booted.

After David rebooted, he confirmed the built-in screen worked. The [DTB-only boot checkpoint](https://linear.app/helmus/issue/DEV-147/usb-c-displayport-external-monitor-unavailable-on-m2-macbook-air#comment-0282aee8) verified:

- Booted `dcpext` enabled with its alias and firmware compatibility `<13 5 0>`.
- The front connector's DisplayPort phandle matched external DCP; the rear connector lacked it.
- ATC PHY1 and crossbar drivers were bound, with mux index 2.
- `DP-1` now existed but was disconnected, with zero EDID bytes and no modes. No external image was established at this point.
- Internal `eDP-1` stayed connected at `2560×1664`, 60 Hz. Stock Type-C modules and stock initramfs were still in use.

Four early `Failed to get dp-xbar: -517` messages resolved into successful mux acquisition, DCP binding, and DCP boot. They were recorded as recovered probe dependencies. A later USB `-71` address-setup error recovered through re-enumeration. Further setup-address, port-enable, and invalid-context warnings also occurred before the candidate module loaded; they remain comparison evidence, not candidate-caused failures.

## Gate 3 — hold, incorrect advice, refusal, then one successful swap

Battery was initially 20%, then 25%, so Gate 3 stayed on hold. The script requires battery strictly above 50%, not merely 50%.

The DTB-only checkpoint incorrectly said MagSafe could remain attached for the live swap. The [correction checkpoint](https://linear.app/helmus/issue/DEV-147/usb-c-displayport-external-monitor-unavailable-on-m2-macbook-air#comment-ddb60c19) explicitly withdrew that advice. MagSafe registers as Type-C partner `0-003a`. The existing guard correctly rejects every partner, including MagSafe. The guard was not weakened. Battery reached 54% during preparation.

David first invoked `03-live-module.sh` with cables attached. Checksums passed, then it refused with the unplug warning. [The refusal checkpoint](https://linear.app/helmus/issue/DEV-147/usb-c-displayport-external-monitor-unavailable-on-m2-macbook-air#comment-85f7b4a2) verified that the guard ran before the module operations. Stock modules remained loaded, all PD controllers remained bound, and no swap occurred. After cables were removed, the battery was 61%. A retry was appropriate only because the refused call had made no driver change.

David then ran the script with MagSafe and all USB-C cables disconnected. He attached only the monitor to the front/lower port after the patched-core prompt. The script reported the partner at `0-003f`, and David confirmed, “monitor shows an image now!” Exactly one real live module swap was performed.

## First-image result and its limits

The [Gate 3 success checkpoint](https://linear.app/helmus/issue/DEV-147/usb-c-displayport-external-monitor-unavailable-on-m2-macbook-air#comment-eeef7473) links the authoritative first-image measurement record (retained privately). Observations span 19:46:36–19:49:24 CEST on 2026-08-27.

Evidence SHA-256: `7c73fb635cdbd065aeeb2654b3a72f84c5dd3948882d4ae5f5b6617eb3a498f5`. Preserve that JSON unchanged; it contains the scoped full firmware log rather than only warning-priority excerpts.

Observed results:

- External LG HDR WQHD: `3440×1440` at 99.982 Hz, the preferred/native EDID timing, enabled and physically confirmed.
- Internal display: `2560×1664` at 60 Hz, enabled. No display settings were changed by the agent.
- EDID was 256 bytes with 14 modes. The live core build ID matched the candidate: `8fd9e3d39ee211f439471a812fb5eaa2622f7585`.
- Monitor charging worked; battery rose from 63% to 66%. MagSafe was disconnected. The Realtek hub and LG USB controls were present, and all three PD controllers remained bound.
- Logs showed candidate load, `dcp_dptx_connect`, HPD assertion, connected status with modes, and completion of the native modeset. The helper's partner-detection PASS alone would not have proved these outcomes.
- Independent integrity QA passed for the active boot, four artifacts, both stock backups, stock reconstruction, EFI recovery files, and unchanged packaged DTB/core. Root-only stock initramfs and GRUB contents were not rehashed during this live check; their metadata was read.

The live core had the expected out-of-tree `O` flag. Global taint rose from the pre-existing 4 to 4100. The pre-existing bit was linked to the boot's non-architectural VGIC warning; it was not introduced by the candidate.

Full firmware syslog also contained a frequency-setup `EDT ERROR`, a CAHandler data-version diagnostic, and PMU return `0xe00002d8`. Review mapped the PMU value to `kIOReturnNotReady` in [Apple's IOReturn definitions](https://github.com/apple-oss-distributions/xnu/blob/main/iokit/IOKit/IOReturn.h). The proprietary frequency/CAHandler consequences remained unresolved. [RTKit forwards these messages at info priority](https://github.com/torvalds/linux/blob/master/drivers/soc/apple/rtkit.c), so warning-only logs were insufficient.

No display loss, kernel crash, DART/IOMMU fault, or charging/USB degradation was observed in that bounded post-swap check. This does not establish clean firmware operation or long-term safety. No startup with the patched module, repeated hotplug, cold-start, suspend, full rollback, or permanent installation was proved. The minimal route plus HPD patch was sufficient for this one native live result; the excluded patches were not needed for it.

## Recovery artifacts and unexecuted work

The privileged baseline manifest (retained privately), artifact manifest (retained privately), two timestamped stock backups, and offline Mac recovery guide (retained privately) were retained. The existing Linux rollback script is `/home/david/o/.dev147-stage/commands/02-rollback-dtb.sh`. Full rollback execution was still pending.

At this cutoff, the alternate initramfs was not built, no persistent GRUB entry or `update-m1n1` override existed, and no permanent driver installation was made. The live module would disappear on a normal reboot; the DTB would not. The next steps belong to the [living plan](../plans/dev-147-m2-displayport.md), not to commands copied from this historical record.
