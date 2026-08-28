# DEV-147 one-boot preparation evidence — 2026-08-27

> Public archival copy, prepared 2026-08-28. Actual boot IDs are redacted where present. Local evidence links are marked as private. Commit references identify the retained private branch unless they name upstream source. Recorded hashes and past QA results describe the private originals, not this edited export. Commands below are historical records, not instructions to run the public helpers.

Status: immutable account of Gate 4a preparation. The separate image was built and compared with stock. It was not staged or booted at this cutoff. Later results belong in a dated addendum. The [living plan](../plans/dev-147-m2-displayport.md) owns next actions.

Host/scope: `omarchy-air`, MacBook Air M2 J413/T8112, kernel `7.1.6-1-1-ARCH`. Source worktree: `/home/david/o/.dev147-stage/prototype`, branch `codex/dev-147-m2-dp-altmode`, starting commit `8e2195c6`. The unrelated main checkout and the live `/home/david/o-live` checkout were not edited.

Approval: David's “continue” followed the reconciled, contained plan. David ran the protected-stock reader himself. The agents did not run sudo, stage an image in `/boot`, change a live driver, reboot, change device state, install a package, or alter persistent boot configuration. The earlier [Gate 0–3 history](dev-147-prototype-history-2026-08-27.md) remains unchanged.

## What happened

1. Read the live Linear issue and confirmed the active prototype, recovery artifacts, installed kernel/toolchain, boot layout, and effective initramfs configuration. The running system remained dev-linked to `/home/david/o-live`.
2. Added the [offline builder](../../dev/apple-dp-altmode/prepare-one-boot-initramfs.sh), [literal configuration](../../dev/apple-dp-altmode/one-boot-mkinitcpio.conf), [protected-stock reader](../../dev/apple-dp-altmode/read-protected-stock.sh), and focused tests. The builder uses a full private module tree and the installed hooks. It does not use a preset, UKI, extra Type-C preload, or custom hook.
3. Independent real-tool QA found two defects before use. `dd oflag=excl` is invalid in the installed GNU tool; it was corrected to `conv=excl,fsync` and tested with real files. The early-image verifier wrongly required DPTX/crossbar modules that the retained hooks do not select. The required list was corrected; package-verified normal-root availability was recorded separately. A locale-configuration pin was added. No hook or preload was added to satisfy a verifier.
4. Ran one real candidate build, as the normal user in the managed sandbox, beginning at 19:09:29 UTC. It exited 0 with `BUILD CHECKS ONLY`. The output directory was new. Neither the existing stage artifacts nor the stock image was overwritten.
5. David ran the reader. Its record completed at 19:11:15 UTC. Fixed root-only readers verified stock initramfs and GRUB hashes before and after, streamed the stock image into a normal-user private writer, and returned a filtered GRUB entry. There was no root extraction or privileged destination write.
6. Independent QA compared both early and main archives. It checked every final member's metadata/digest and separately checked module bytes, build ID, vermagic, dependencies, runtime hooks, selected extraction hashes, and package provenance.
7. A second reviewer checked the image and the complete comparison. Static content readiness passed with explicit rebuild differences and residual startup risks. This did not authorize boot.
8. Added the [staging-only helper](../../dev/apple-dp-altmode/stage-one-boot-initramfs.sh) and real-file tests. A completion-marker conflict was caught and corrected before handoff. Scoped QA and independent review passed. The helper was not run as root. It can only add the fixed non-default image after its guards pass; it cannot select or boot it.

The builder's exact command is retained in build-command.txt (retained privately). Its critical arguments were:

```text
mkinitcpio --config <new-output>/mkinitcpio.conf
  --hookdir /usr/lib/initcpio --nopost
  --kernel 7.1.6-1-1-ARCH
  --moduleroot <new-output>/module-root
  --builddir <new-output>/tmp --save
  --generate <new-output>/initramfs-linux-asahi-dpalt.img
```

External tools used a cleared environment. The outer command had a 295-second timeout and a five-second kill grace. It did not time out. The full private module tree had independent files, not hardlinks to the installed tree. Only the candidate core and allowed generated depmod indexes could change before image generation.

## Image and stock comparison

| Item | Verified result |
|---|---|
| Candidate image | 19,184,103 bytes; SHA-256 `ae8f1ed7f4f258f89931209cd7de6030be9f6875372d7329151b822a6ba2281f` |
| Stock readback | 18,865,028 bytes; SHA-256 `625641095075a9a2396bc701ffd48ac58f2c8a1758e250fa3f6b55b29dcae296` |
| Final archive paths | Identical 1,163 paths: 801 regular files, 194 links, 168 directories |
| Modules | 199 each; 198 byte-identical, only the intended Type-C core differs |
| Module metadata | 199 vermagics and 111 dependency edges passed; all seven embedded indexes are byte-identical |
| Selected extraction | 225/225 selected regular-file hashes passed for each image |
| Runtime hooks | Asahi/init/udev/Plymouth/keymap/encrypt payloads and runtime order are unchanged |
| Firmware route | Both images retain `/usr/lib/firmware/vendor -> /vendorfw` and the Asahi vendor-firmware hook |
| Candidate core | SHA-256 `bc02723db427639c6586d29eea7918e084874c741b60bf145585c6349fd07d70`; build ID `8fd9e3d39ee211f439471a812fb5eaa2622f7585` |

The whole image is **not a core-only byte change**. Five regular files differ:

- The intended candidate core.
- `buildconfig`, which now records the reviewed literal configuration.
- Runtime `config`, whose only change removes a repeated `hid_apple hid_magicmouse` pair. It does not remove a driver or change runtime hook order.
- `usr/lib/libcrypto.so.3` and `usr/lib/ossl-modules/legacy.so`, from the currently installed OpenSSL 3.6.4 package.

Both candidate OpenSSL files match the installed files, installed package mtree, cached package mtree, and payload streams. A normal-user, read-only check outside the sandbox confirmed the same two host hashes. Stock libcrypto identifies itself as 3.6.3; the package log records the upgrade to 3.6.4-1 on 2026-08-26 at 16:16:24 +0200. The old legacy provider's precise package build was not independently established.

The retained encrypt hook can invoke cryptsetup even on this unencrypted root. Required library paths and libcryptsetup symbol versions exist. These are static checks, not runtime ABI validation. The OpenSSL changes remain an additional startup-test variable. No package was upgraded or downgraded during this work.

Six files differ only in permissions: four generated files (`early_cpio`, `VERSION`, empty `etc/fstab`, empty `etc/ld.so.conf`) are 0600 instead of 0644; identical `mount`/`umount` binaries are 0755 instead of 04755. Root archive ownership is unchanged. The inspected initramfs runs these calls as root. Review found no static access blocker; this is not a boot rehearsal.

Stock early cpio has one extra duplicate `lib -> usr/lib` link. Both main archives contain that link, so final paths are identical. The main gzip archive starts at byte 10,240 in both images. The candidate core contains debug sections that the stock module lacks; file-size growth is not all executable code.

The full comparison report (retained privately) records exact old/new hashes and methods. SHA-256: `3c017f5371ddee26bbc078d0ea9eeac987349787dcc838546658b9c2c2522d51`. Its 35-entry evidence manifest passed completely; manifest SHA-256: `1c41f464486f4747bf12da9fdc2bd4c8bf83fe06d7e6adf3ee9bfe0edc5f156b`.

Two incomplete comparison probes are retained in that report. A legacy-provider version search returned no banner. A Node subprocess probe met a sandbox EPERM; direct sandboxed shell metadata reads and a pure-data check completed the audit. Neither was presented as a final pass or retried outside the sandbox.

## Build warnings and startup limits

The successful build log (retained privately) retains six warnings:

| Warning | Static finding; remaining limit |
|---|---|
| Missing firmware for `xhci_pci` | Apple ASM2214 firmware exists in EFI vendor firmware and the live vendor tree, not in the image. Hook availability is checked; future loading is not. |
| Missing firmware for `dockchannel_hid` | J413 trackpad firmware exists in both vendor locations. A successful first startup is still required. |
| Missing firmware for `xhci_pci_renesas` | The named firmware was not found. No Renesas controller was seen in the PCI inventory; retain the warning. |
| Unsupported `aarch64` microcode hook | The installed hook handles x86 and skipped this architecture. This says nothing about Apple firmware health. |
| No `drm_privacy_screen_register` platform module | Optional discovery did not find one. The audited display dependency chain does not require it. |
| No console font configured | The host has no configured console font. Keymap support remains present. |

No warning is erased or declared harmless. Earlier DCP frequency/CAHandler/PMU diagnostics remain unresolved. No early Type-C startup, repeated hotplug, cold-start, suspend, or full rollback result follows from the static checks.

## Baselines and containment

Both `/boot/vmlinuz-linux-asahi` and the package's kernel image match `ee36d989d62f2dd498b818e15c2044350c79d814a2017ffca61fdc2ad1aa95b6`. This is new pre-Gate-4 evidence, not an original Gate 0 digest. All 1,987 installed package file digests match the local mtree and the exact path set. The normal-user `pacman -Qkk linux-asahi` check returned 11 timestamp-only differences in generated indexes; it was not an unqualified metadata pass. Sandbox UID/GID mappings were not treated as host permission drift.

The original 27 artifact/evidence/recovery files and four Gates 0–3 scripts remained byte-identical. Both stock boot backups, active candidate `boot.bin`, packaged core/DTB, and both Mac recovery bundles retained their pins. The original nine-comment Linear archive retained SHA-256 `10d59c0435d8a9c190339d6f543527130435e2a6aa84c6504722b93833e0fb74`.

David's readback logs show the stock image hash above and GRUB hash `68c36bbbb3c530dba8647f9435252da53adf53942b37b76e399ccd234cc0f24d` matched before and after. `/boot` is on the ext4 root filesystem, not the EFI partition. The actual normal entry uses `linux /boot/vmlinuz-linux-asahi` and `initrd /boot/initramfs-linux-asahi.img`. Kernel arguments were omitted from the captured public-facing filter and must remain unchanged.

The intended later one-time edit changes only that initrd filename to `/boot/initramfs-linux-asahi-dpalt.img`. The [GRUB menu editor](https://www.gnu.org/software/grub/manual/grub/html_node/Menu-entry-editor.html) uses Ctrl-x to boot the edit and Esc to cancel it. No persistent entry/default change is required. These are future instructions, not evidence that the edit ran.

Read-only post-build checks still found the internal and external outputs connected/enabled, the reviewed live core build ID, and charging. The bounded full-priority kernel window had no new display event in its captured interval. The private raw record also includes unrelated audit/network data; do not publish its contents. This check does not extend the original physical-image confirmation or prove long-term stability.

Durable raw records:

- Preflight (retained privately), SHA-256 `3ba3340ef8e1428c95927f0299056e771f12f5a7a626cbbeb042991feb872fa8`.
- Post-build containment (retained privately). Its then-pending readback field is superseded by the later readback and comparison, not rewritten.
- User readback (retained privately), with before/after logs and stock-copy hash in the same private directory.
- Pre-update Linear snapshot (retained privately), SHA-256 `ac509c84c489f1a965b88cb00e5d9373ac7c4b8a741055b43f8638632f9d6c27`. All ten existing comments were retained.

## Automated QA

Builder/readback fix round 1 passed 42 focused checks, seven existing prototype checks, 455 command metadata checks, and shebang-aware syntax for 458 bin files plus the four new files. Production input pins and all 1,987 module-tree digests passed. The four source hashes were unchanged before, during, and after QA.

`./test/all` still failed in five of 234 shell test files: config, network-qr, unowned-system-paths, windows-vm-compose, and zram-package-contract. Three lacked the `omarchy-pkgs` fixture checkout. Network QR retained its existing sandbox-related failure. Windows VM setup attempted a real credentials-path write, which the sandbox blocked. The aggregate was not retried unsandboxed.

The round-1 logs (retained privately) were copied from temporary QA output into the persistent stage. Aggregate log SHA-256: `89b62c265e3405db6c28d96f2405313a36ab484bf03f3d178e4be37a36b311fb`. The initial aggregate log (retained privately) is also retained, SHA-256 `378d6cd461d1b954c61e49e713ed22f3616e39a8132c6c41c22452ece8621d8c`.

Final staging QA passed 21 staging checks, the 42 initramfs checks, seven prototype checks, and 12 additional real-fixture checks. Command metadata passed 455 checks; syntax passed for 458 bin files and all six new helper/config/test files. The candidate hash/size and 18 readable protected pins matched before and after. QA did not reread the two root-only originals; David's staging execution must check them again.

The final aggregate run returned exit 1 with the same five failures in 235 shell test files. There was no new failure or timeout. The staging QA evidence (retained privately) passed 23/23 manifest checks, SHA-256 `841d81d0f2ccda4104a0c8c3b35cda95269b9e1b28f2f9a248dde5b58e32300b`. Its aggregate log has 3,349 lines and SHA-256 `9fdbda86913671401334ec0feb5957f2eb0bd103b8d2e1fdcdf8cf79f8f2cc0b`.

All six source hashes were unchanged through final QA. The code manifest hash is `0273aed5204ca5ea0b26c7a8645b54d56ee099851243f414c89da14ece56edbe`. The reviewed staging helper hash is `d35fa0311ee1baecec50561e9d50fabeea9570ba2fa8d4ef480bdb84836920e2`; its test hash is `c97963be453067ed6c6e4d552d3d8885582f7b0a9af9ac9a778f4298708129a3`.

The reviewed user launcher puts `sudo /usr/bin/env -i PATH=/usr/bin:/bin LANG=C.UTF-8` before `/usr/bin/bash`. In-script environment guards cannot undo earlier BASH_ENV startup execution. Root execution remains untested; no agent ran that launcher.

One nonblocking marker limit remains: the image and result are synced before the final INCOMPLETE-to-start-marker rename, which has no following sync. A sudden interruption could leave `INCOMPLETE` beside `RESULT.txt`. Treat that combination as HOLD, not completion; recheck without automatic retry or cleanup. Static review did not find a default-boot or image-publication safety defect. It did not claim crash-proof markers.

A normal-user host check (retained privately) verified real /boot ownership (root, 0755), pinned ext4 root identity, tool hashes, and the front-port DT route outside the sandbox's UID mapping. It used no sudo or writes; SHA-256 `7abe820e2212847f961a09fa2d55479840d0a808d7d8819097ed480c88c5d0ee`. The later containment check (retained privately) again confirmed the original 27 files and four gate scripts, both image hashes, and absence of the alternate /boot image; SHA-256 `1b5c589f1082f348b96fae72ff89106aa7bf1cf44c3c1ff89c103dc31d67145f`. Both outputs were still connected/enabled; battery was 100%, Full. These are read-only observations, not a new physical-image confirmation.

## Rollback and open gates

No system mutation from this preparation needs rollback. Retain the private image, stock readback, source, and evidence. Do not automatically delete them.

The pre-existing Gate 3 state still has the prototype DTB and live candidate core. A normal stock-initramfs reboot restores only the driver. The [plan's full rollback](../plans/dev-147-m2-displayport.md#gate-6--prove-full-rollback-then-retain-the-evidence) uses the existing user-run DTB rollback script, then a verified stock boot. Keep both timestamped backups and both Mac recovery bundles.

Open: user-run staging and protected post-checks; one-time startup; behavior and firmware investigation; full rollback proof. Normal macOS/Recovery access remains user-attested, and actual Mac restore execution remains untested. No permanent install, release, or merge is approved by this preparation. Aggregate QA is not all green.

Instruction gap: the referenced `writing-plans`, `self-correction-loop`, and `linear-cli-*` skills were not available on this host. The work used the installed CLI help, the documentation skill, explicit gates, and independent QA/review. Suggested follow-up: a separate Linear issue to make those method skills discoverable or correct their canonical references. No framework edit or extra issue was made.
