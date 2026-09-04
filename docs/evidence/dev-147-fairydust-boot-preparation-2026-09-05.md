# DEV-147 fairydust boot preparation — 2026-09-05

The complete offline preparation gate passed for the author and independent reviewer. The independent run completed in 48.363 seconds with exit 0. This record covers private boot-artifact preparation and the unselected staging handoff. Live staging, selected-boot activation and hardware acceptance are separate results.

## Complete candidate inputs

The [kernel build evidence](dev-147-fairydust-build-2026-09-04.md) owns the frozen source and full kernel result. This continuation adds the initramfs and m1n1/U-Boot bundle for release `7.1.12-dev147-fairydust1`.

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| Image | 33,982,976 | `5175f41bb2d25abce49f6a844cdbe9233a4d090de34fa9aadcf6512c87590079` |
| Initramfs | 191,153,387 | `e4e70b766e463468f01d1830a4dd1b42b0cbefb4d07463bdf7e54451ecce730a` |
| J413 DTB | 72,115 | `9831d42f9c271ce35dd3e32b5c8298e1c13849568853aea0779f40bb67377b80` |
| m1n1 stage-2 bundle | 1,489,431 | `1ae29a2bfadb309562c205520d8c28e2a8df2283bc88bbfb52474e54333c3dff` |
| Delivery manifest | 1,885 file entries | `f33054856e60d3baf5cb7630cb8d7dfc60ffa586e16456c3e7313fffe6f7c59d` |

Delivery is `/home/david/Work/dev147-fairydust-boot-20260905/delivery`, about 2.2 GiB. All 1,862 runtime modules match the kernel build. The new delivery copy omits only the development `build` symlink. It includes configuration, module hashes, and source/initramfs/boot receipts. The frozen kernel candidate remains unchanged.

## Initramfs and firmware

Real mkinitcpio 41.1 ran inside Bubblewrap with read-only host inputs, existing fakeroot, explicit configuration and release, and `--nopost`. No preset, host package hook or installed module path was used as an output. The recipe preserves effective host startup hooks and adds current Apple module names. Offline fallback inclusion replaces hardware autodetection, explaining the larger image.

The image contains 334 exact candidate modules and 12 embedded firmware files, including all six AVD firmware files. Validation checks dependency closure, the builtin Asahi GPU, startup files, runtime configuration and Asahi hook identity and ordering. Independent review also checked 20 driver dependency paths and 12 executable/library closures.

The embedded files are not the full firmware supply. The Asahi startup hook loads `/boot/efi/vendorfw/firmware.cpio` before device discovery. Independent archive/manifest checks cover 217 files and 121 hardlinks, including the J413 trackpad firmware. The external archive is 32,530,132 bytes, SHA-256 `7c2ce145ec9bb390c2377e6e83d1aacc3817dd227909b0e62b0febe96d2f451f`. Its manifest matches `/usr/lib/firmware/vendor/.vendorfw.manifest`, SHA-256 `2f3ab6e0d7d2fb8ab11746094c1d02a3ef00da9a8037bfdac583eb4b8d31cea1`. Recheck these dependencies before activation.

Retained build warnings concern vendor/runtime firmware lookup, optional fallback Renesas firmware, the unsupported x86 microcode hook, no privacy-screen module and no console font. They are not converted into a firmware-clean or hardware-success claim.

The first build failed on ownership-preserving copies in the namespace. Fakeroot resolved that prerequisite. The first verifier also expected text module metadata that mkinitcpio removes; it now checks binary indexes and runs depmod with source metadata in a separate check copy. Independent review then demonstrated that deleting `/init_functions` incorrectly passed the checker. The real image contains that file; the checker and regression controls were corrected without rebuilding the image. A second counterexample used an absolute BusyBox symlink that compared equal on the host but could not start inside the image. Regular-file checks now reject it and the equivalent Asahi-helper symlink. The retained failures explain the changed validation contract.

## Boot path and recovery constraint

The new bundle is exactly installed m1n1 1.6.1, the pinned J413 DT, and one reproducible gzip stream of installed U-Boot. Separate assembly reproduces the bytes. Independent parsing verifies component boundaries, FDT size/magic, gzip termination and decompressed U-Boot identity. Both installed loader packages report zero altered files.

m1n1 prepares SIO firmware parameters, reservations and device-tree relationships before U-Boot/GRUB. The current live DT has no SIO alias and leaves SIO disabled. A raw GRUB DT replacement skips that work. The [Asahi boot guide](https://asahilinux.org/docs/alt/boot-process-guide/) and [pinned m1n1 SIO setup](https://github.com/AsahiLinux/m1n1/blob/06a4601a351ebfd1abb6abba9a44c34e40d94776/src/kboot.c#L2189) support this ordering.

Pinned stage 1 loads one configured internal-NVMe FAT path; no ordinary alternate-bundle menu was found. The documented temporary alternative uses tethered early proxy with another host and additional boot-policy prerequisites. It was not configured here. See the [m1n1 guide](https://asahilinux.org/docs/sw/m1n1-user-guide/).

Activation must pair the candidate m1n1 bundle with the exact candidate kernel/initramfs GRUB selection and handle saved/next/fallback overrides. Rebooting or selecting the old kernel under the new shared DT is not validated rollback. `boot.bin` is on FAT EFI, while `grub.cfg` is on ext4; they cannot be replaced as one atomic filesystem operation. macOS/Recovery can directly restore the FAT file, but restoring ext4 GRUB state needs an independently verified route. No selected-boot write is part of this handoff.

## Staging boundary and verification

The [staging guide](../../dev/apple-dp-altmode/fairydust/boot-stage/README.md) owns the exact user command and result paths. It adds only a new `/boot/dev147-fairydust-7.1.12-dev147-fairydust1` directory and matching module release, plus retained staging evidence. The existing transaction guard remains in place. The launcher verifies helper bytes in the privileged process and executes those same bytes; its delivery manifest is fixed.

Twenty real-entrypoint tests cover candidate hashes and inventory, root-owned copy verification, package locking, path/link/special-file rejection, existing-target refusal, protected-state drift and exact module bytes. Copies are bounded to 2.3 GB, 4,096 entries and depth 32, and stop at each file’s initial size. Tests reject oversized, growing and excessive-entry inputs before unbounded copies. The frozen input has 2,298,586,871 bytes, 2,247 entries and maximum depth 13. A full rehearsal uses the actual 2.2 GiB delivery in a disposable namespace. Its GRUB and old-state inputs are synthetic fixtures. The live stage will export the real protected configuration into user-private results for the next activation review.

The complete gate is `bash /home/david/Work/omarchy-dev147-fairydust-build/dev/apple-dp-altmode/fairydust/validate-boot.sh`. The [machine-readable receipt](dev-147-fairydust-boot-preparation-2026-09-05.json) and [living plan](../plans/2026-09-05-dev147-fairydust-boot-integration.md) retain final command exits and independent review.

Repository `./test/all` returned 1: three missing omarchy-pkgs checks, the known desktop IPC mismatch, and a temporary-directory cleanup failure in the bar-widget test. The focused bar-widget rerun returned 0. Metadata passed 455 commands; all 458 bin syntax checks passed. No whole-repository PASS is claimed.

No live staging, privileged installation, boot selection, reboot, device action or edit to `/home/david/o-live` occurred in this preparation. The running kernel remains `7.1.6-1-1-ARCH`. The 50 inherited DT schema findings, runtime firmware preparation, complete recovery, reconnect reliability, USB/audio/charging, second-port routing and suspend remain open.
