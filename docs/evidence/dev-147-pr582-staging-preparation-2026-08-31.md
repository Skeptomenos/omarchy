# DEV-147 — minimal PR582 staging handoff, 2026-08-31

Scope: David approved step 1 of the minimum reboot path and requested the sudo command for step 2. This record covers preparation, not staging or reboot.

## Change

A new private 138-line wrapper coordinates the two already accepted PR582 images. It authenticates the exact retained staging library in memory, removes only its fixed main-dispatch footer, and evaluates the unchanged definitions. It does not run the consumed T1 entry point or modify that helper.

The wrapper reuses kernel/package, mount, power, boot-chain, backup and protected-file checks. It adds pins for both PR582 images, their accepted manifest/result, staged T1 and packaged AppleDRM. It requires both new destinations absent and both image sizes plus the existing 16 MiB reserve.

One root-private evidence directory and one incomplete marker cover the pair. Both copies verify before either publication. Each publication is atomic and no-replace, but the pair is not atomic. Both final images and the before/pre-publication/after proof records verify before the explicit pair PASS. A failed second publication retains the first image and all remaining evidence; no automatic deletion or retry follows.

## Checks

Independent static review passed. The wrapper SHA-256 is `0df4e987d43000bbf8e4aa1a2189a7621310a070d048b2c25cec089cbb8e3d8a`. The retained library remains `6b20d119791f4322e101a92b9e5b850ba3098d35dbf966f2d7918cb3918694f9`.

One fresh accepted-v6 sandbox run, `run-xzzmt8oq`, ran `python3.14 -I -S -B /inputs/pair/test_stage_pr582_pair.py`. All 14 methods passed in 0.834 seconds. The run returned exit 0, unchanged inputs and no timeout; the isolation probe and seven standard-library smoke tests passed. Independent saved-result QA confirmed the result and all 583 v6 runtime bindings. Test SHA-256: `22bc7ccdd629a6e37653cba6fd599ab937db97bebd2504a71fb481f131ca9fdb`.

The real-file checks cover authentication, copy and publication, corrupt sources/copies, destination collisions, symlink/hardlink refusal, the space boundary, completion records, unprivileged/argument refusal and process-local TERM. A source check fixes main ordering and single finalization. The wrapper and tests were drafted together; no pre-implementation RED result is claimed. The existing stdlib/unittest no-install exception remains. Ruff, mypy, Pytest and the broad Omarchy suite were not run. The accepted 54-method library suite and image builds were not replayed.

Fresh unprivileged checks found the expected kernel and seven package versions, unchanged image hashes, expected private source metadata, ample space, and both intended destinations absent. These do not replace the manual helper's protected preflight.

## Manual boundary

David must be present with saved work, a healthy internal screen, responsive Linux, lid open, physical MagSafe connected, battery above 50%, and the recovery guide available on another device. Keep the current cable/device setup unchanged. The private handoff supplies one sudo command under a 240-second timeout plus 5-second kill grace, with an explicit exit receipt. This is not a guarantee against uninterruptible kernel I/O.

Require both `PAIR STAGING PASS` and exit 0. Stop for review after any invocation. No root main, real hardware preflight, protected publication, outer sudo/timeout path, driver operation or reboot ran during preparation. Offline tests are not proof that the images boot or restore video.

The only new image targets are `/boot/initramfs-linux-asahi-dpalt-pr582-control.img` and `/boot/initramfs-linux-asahi-dpalt-pr582-candidate.img`. Existing images, installed modules, DTB, GRUB and default startup stay unchanged. To abandon a successful staging operation, leave these images unselected; this does not restore the original DTB.

The [main plan](../plans/dev-147-m2-displayport.md#minimum-remaining-path-living) owns the separate attended candidate boot and later timeout/control comparison. The [saved diagnostic export](dev-147-crashflag-export-2026-08-31.md) is already preserved. No new probe, cable test or source rebuild is a prerequisite for the next boot.
