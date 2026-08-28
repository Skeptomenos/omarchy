# DEV-147 one-boot image staging evidence — 2026-08-27

> Public archival copy, prepared 2026-08-28. Actual boot IDs are redacted where present. Local evidence links are marked as private. Commit references identify the retained private branch unless they name upstream source. Recorded hashes and past QA results describe the private originals, not this edited export. Commands below are historical records, not instructions to run the public helpers.

**Host / scope:** `omarchy-air`, M2 J413/T8112, kernel `7.1.6-1-1-ARCH`. Successful staging only; startup remains untested.
**Approval:** David ran the exact reviewed staging command and supplied its output. The standing request covers plan/history reconciliation and contained testing. Agents performed read-only validation and documentation work, not privileged execution or a reboot.
**Repo state:** Reviewed helper at `94c32743c86412b20718c3d8535bd7e8b5cdc4f7`, branch `codex/dev-147-m2-dp-altmode`. This record adds to the [preparation evidence](dev-147-one-boot-preparation-2026-08-27.md); it does not rewrite that earlier cutoff.

## What happened

David ran:

```bash
sudo /usr/bin/env -i PATH=/usr/bin:/bin LANG=C.UTF-8 /usr/bin/bash /home/david/o/.dev147-stage/prototype/dev/apple-dp-altmode/stage-one-boot-initramfs.sh
```

He supplied 20 pinned input digests and this final output:

```text
STAGING ONLY PASS: /boot/initramfs-linux-asahi-dpalt.img
Checks retained in /boot/.dev147-dpalt-stage.e5Cys4arMi
No reboot yet. Normal boot is unchanged. This image remains untested at startup.
```

The private reviewed helper at this checkpoint hashed to `d35fa0311ee1baecec50561e9d50fabeea9570ba2fa8d4ef480bdb84836920e2`. The linked [public source copy](../../dev/apple-dp-altmode/stage-one-boot-initramfs.sh) has since had its machine identity redacted and does not have that hash. Independent control-flow review confirmed that final PASS follows the post-publication preflight of all 20 inputs, staged-image size/hash verification, syncs, and completion-marker rename. Accept this as validated user-run execution. Do not call it an independent agent read of protected files.

The staged image has the reviewed size of 19,184,103 bytes and SHA-256 `ae8f1ed7f4f258f89931209cd7de6030be9f6875372d7329151b822a6ba2281f`. Its hash was checked by David's validator. Agents independently rehashed the private source image, not the root-only staged copy.

## Result

Read-only checks at 22:00 CEST returned:

- `stat`: staged image root-owned, mode `0600`, 19,184,103 bytes, modification time 21:58:23 CEST. The retained directory is root-owned, mode `0700`.
- `test -r`: the staged image, `RESULT.txt`, and `after.sha256` were unreadable to the agent's UID 1001. No permission change or privileged read was attempted. Root-only stock initramfs/GRUB post-checks are established by David's final PASS, not a fresh agent hash read.
- `sha256sum`: the source image, active candidate `boot.bin`, both original backups, both Mac recovery bundles, both kernel-image copies, and packaged DTB/core match their pins.
- `uname -r` and package queries: kernel `7.1.6-1-1-ARCH`, `linux-asahi 7.1.6.asahi1-1`, `openssl 3.6.4-1`.
- DRM sysfs: `card2-DP-1` and `card2-eDP-1` both connected and enabled. Battery: 100%, Full. The live core build note remains candidate `8fd9e3d39ee211f439471a812fb5eaa2622f7585`.
- Type-C sysfs: partners on monitor controller `0-003f` and MagSafe `0-003a`. No cable change was made by the agents. This is current software state, not a new physical-image or startup confirmation.

The normalized user-output excerpt and raw read-only tool results (retained privately) have SHA-256 `2b95c9a1e02406b5f058e7c25853065dc9ea1592d7204c1bd6551714403f2a03`. Protected root logs remain at the path printed by the helper. No redundant privileged readback is required merely because the logs are private.

The pre-update Linear snapshot (retained privately) preserves the then-current description and all 11 prior comments, SHA-256 `0204eab264805e7fb198ec3f5977b476b4887f55378e7141dbbd3e767506b780`. The original nine-comment archive, trial history, and preparation evidence remain unchanged.

Documentation QA and independent safety review: PASS. All 30 local Markdown links, three anchors, 12 command-file paths, and six frozen code hashes passed. `git diff --check` passed. Live Linear verification confirmed the exact new description, unchanged In Progress state, all 11 prior comment IDs/bodies, and one added staging comment. No test suite or device action ran during this documentation check.

## Rollback

The alternate image is not selected. Leaving it unselected preserves normal startup. Do not rerun staging, delete its evidence, or change the default boot entry. The stock initramfs, GRUB, packaged module/kernel/DTB, and existing backups remain protected.

If the future one-time boot fails and Linux responds, unplug the monitor and let David run `sudo reboot` with the normal unedited entry. This restores the stock driver, **not** the prototype DTB. Full restore still uses `sudo bash /home/david/o/.dev147-stage/commands/02-rollback-dtb.sh`, followed by a stock reboot only after `Gate 2 rollback PASS`. If Linux cannot boot or display, follow the existing offline Mac recovery guide (retained privately). Keep both timestamped backups. No cleanup or recovery command was run at this checkpoint.

## Open

Gate 4a is complete. [Gate 4b](../plans/dev-147-m2-displayport.md#gate-4b--user-selected-one-time-startup-test) starts only when David chooses the temporary GRUB edit. Keep the current cables and lid open. Check the internal screen/login first, then the physical external image. Stop for read-only driver/log validation before any hotplug, mode change, or suspend test.

Candidate startup, reliability, full rollback, and actual Mac restore execution remain unproved. The earlier OpenSSL/configuration/mode differences, six build warnings, and firmware diagnostics remain open. Prior scoped QA passed; the aggregate suite still has its recorded five failures. No full suite was rerun for this documentation-only checkpoint. In particular, do not run the known real-credentials-writing Windows fixture without its earlier sandbox protection. No permanent installation, release, or push is claimed.
