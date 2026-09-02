# DEV-147 M2 DisplayPort opt-in preparation

**Date:** 2026-09-01
**Scope:** Offline reconstruction, packaging, and simulated rollback only
**Live mutation:** None

## Authority

David asked the task to continue until a sudo command, reboot, or physical
monitor action is required. The external monitor stayed disconnected. MagSafe
stayed connected.

## Source reconstruction

Authenticated Git access checked out the official Asahi tag
[`asahi-7.1.6-1`](https://github.com/AsahiLinux/linux/tree/asahi-7.1.6-1).
The annotated tag resolves to commit
`e2e1930a9595bffafad92cec2b5504525efb9cd4`. The official
[`linux-asahi` PKGBUILD](https://github.com/asahi-alarm/PKGBUILDs/blob/main/linux-asahi/PKGBUILD)
uses the same tag for package `7.1.6.asahi1-1`.

All six pinned source inputs matched the earlier prototype:

| Input | SHA-256 |
|---|---|
| `t8112-j413.dts` | `ba488713e2b84bb4993e8f120fa9341a27695d8c0cd093c7875dd17d95d22d78` |
| `t8112-jxxx.dtsi` | `3338b8bf62d5b6458b4f72f4ea583a8a6e0cbdb6a89d378570b5bebdcb327319` |
| `tipd/core.c` | `3f581b0837bf24c085fb08db0043329b6d3043fc1c9f6b25b005f7e7bdba0a72` |
| `tipd/tps6598x.h` | `cf71a3a19d7d9a39f1987c7631cc955f8a150f8a5761c9567b7c421fbd7fe545` |
| `tipd/trace.c` | `1aa4062980d6c62ddec438abdff474408ee6ff9c891ca134153a8187fbb92e87` |
| `tipd/trace.h` | `21a469e23cf48152c31f61c0eea8723d43b650facb730bbb352193c73e27e4e6` |

The retained matching headers and `pahole` rebuilt the candidate without
root. Results:

| Artifact | SHA-256 or build ID |
|---|---|
| Rebuilt stock `boot.bin` | `bb6829c44d8de26d6615406b41edc0beef2254766b5ed114afad2029db7ae856` |
| Patched J413 DTB | `23945f8ca60a6db63ef81bbd95ee4cdd9bb63f54cd6b07b001c677f0a15ef07b` |
| Candidate `boot.bin` | `203ab7027536c8d16f373d02c1f6346a5c34cfe095a9dafd0cfe37d2b354090c` |
| Rebuilt TIPD module | `69d220a692d1bbc0dc5d40069c36ff118a0f0816137e0aa548f4f232efcba811` |
| Rebuilt TIPD build ID | `50ee94a5f8dbae780c676a73b611a7ad5197e47a` |

The rebuilt stock bundle matched the preserved stock backup. The patched DTB
and candidate bundle matched the accepted prototype byte for byte.

The new module did not match the accepted module as a complete ELF file. The
absolute build directory changed its debug strings and GNU build ID. After
removing debug data and the build-ID note from both copies, their bytes were
identical with SHA-256
`e44472237cb439b58e251a3351214fe399b9734a27e146dbcd668e9cfb1b8c07`.
Their loadable code and data sections, vermagic, dependencies, defined symbols,
and imported symbols also matched.

## Candidate image

The first image attempt stopped before construction because the raw
`omarchy_hooks.conf` hash had changed. At build time, the installed file matched
the then-current Omarchy 4.0.1 checkout. Its effective Asahi, HID, encryption,
and firmware inputs matched the reviewed flattened build configuration.

The second build passed with the current input set:

- Image SHA-256:
  `a93dd0c1b3a6c4d81bf76f2f43c7c7a2b8b7e1e0306bc487de018667f9c8c196`
- Image size: `19,184,210` bytes
- Embedded build-configuration SHA-256:
  `d3f2be936eefc1adce733259fceab552c94af29cf8e017456a5a2193a8bbad69`
- Extracted image: 801 files, 194 links, and 169 directories

The extracted candidate and W trees differ at two files only. The TIPD module
is the newly rebuilt runtime-equivalent ELF. `/etc/os-release` changes from
Omarchy 4.0.0 to the installed Omarchy 4.0.1. The build configuration and all
other extracted files match.

## Reversible integration

The clean worktree started at `quattro-arm`
`575ecfa2a305e8990d37e67ecf82d8d4c9c4b70d`. Before final QA, the branch was
rebased to the current `quattro-arm` tip
`ebe6b8075aa62593f7022cbc03c0248b705f8492`.

The new base adds plain-root selection to the packaged mkinitcpio hook. It did
not mutate the installed hook or the already-built candidate. The integration
keeps the reviewed candidate image pinned. Any later candidate rebuild against
the new packaged hook requires a new image identity and acceptance cycle.

The integration stages a new
`/boot/initramfs-linux-asahi-m2-displayport.img`. It does not change the default
image, W, the installed module, or GRUB. Preparation also leaves the active
`boot.bin` unchanged. It stores the exact pre-install boot file in root-owned
state and on the EFI partition. It installs a pinned pre-transaction guard for
`linux-asahi`, `m1n1`, and `uboot-asahi`. The guard SHA-256 is
`469820ad7cfd015a22cff979b0aa70d62e82dcc7cc05951dca92f40cd660f2bd`.

A separate activation command replaces `boot.bin` only before an attended
reboot. Preparation, activation, and rollback share one root-owned operation
lock. Recoverable state is published before activation can change the boot
file. Rollback accepts both the prepared and activated phases. It restores the
pre-install boot bytes before it removes the candidate and guard. It retains
the EFI backup, recovery guide, and rollback evidence.

The focused test passed every group:

- exact model and kernel acceptance;
- wrong-model, wrong-kernel, and wrong-package refusal;
- strict manifest parsing, readiness receipt, and exact release pins;
- transactional file publication and serialized operations;
- separate preparation and activation phases;
- preservation of the default image, W, stock module, and GRUB;
- no-overwrite behavior;
- exact rollback from prepared and activated states;
- changed-hook refusal before rollback mutation;
- already-active candidate behavior;
- creation and removal of a previously absent pacman hook directory.

A final simulation used the corrected sealed bundle and a preserved stock
`boot.bin`. Preparation, activation, and rollback passed. The protected
sentinel hashes stayed unchanged. The retained simulation is
`/home/david/o/.dev147-stage/dev147-optin-simulation-final.n40ajXo9lR`.

The sealed bundle is
`/home/david/o/.dev147-stage/dev147-optin-bundle-final.iQVkvWr13p/bundle`.
Its manifest SHA-256 is
`f967202c3da1f31480b52c51e46ca2679e302f64596f9917edc56d0041449fb7`.
Its `PREPARED` receipt contains that exact word and has SHA-256
`9b19457b555251319ce2a8558e0a7bee3f6a5b6646284d13660b2e0d1037ccbc`.

An interruption after candidate publication but before active-state publication
can leave inactive staging evidence, the candidate image, or the package guard.
The active boot file stays unchanged. The operator must stop and retain the
evidence instead of retrying or rebooting.

## Live read-only preflight

The current machine passed the non-mutating gate:

- Apple J413/T8112;
- running kernel `7.1.6-1-1-ARCH`;
- exact `linux-asahi`, `m1n1`, and `uboot-asahi` packages;
- candidate destinations absent;
- external USB-C ports disconnected;
- MagSafe online;
- battery Full at 100 percent.

The `0-003a` Type-C partner is the allowed MagSafe power path. The integration
still refuses partners on the two external USB-C controllers, `0-0038` and
`0-003f`.

## Final verification

The final focused integration suite passed. Command metadata for 454 commands,
Bash syntax, whitespace, local documentation links, and the no-code-comments
scan passed. Independent QA verified the sealed bundle, extracted image
receipts, 14-field rollback state, protected-file equality, and exact stock
boot restoration. Independent review found no blocking defects.

The repository-wide test runner reached all 236 shell test files. The new
DisplayPort integration test passed. Three unrelated package-coverage tests
failed because the isolated worktree has no `omarchy-pkgs` checkout. Direct
reruns of `config-test.sh`, `unowned-system-paths-test.sh`, and
`zram-package-contract-test.sh` confirmed that same missing-checkout cause.

## Boundary at record close

At record close, no sudo preparation or activation command had run. No boot
file, package hook, module, driver, device, or running-kernel state had changed.
Preparation and activation remained separate manual gates. Activation must run
only immediately before the attended reboot. The new integrated image remained
untested at startup.
