# Prepare coherent fairydust boot integration

**Goal:** Prepare and verify the complete fairydust boot inputs, stage them without changing the selected boot, and use protected boot evidence to prepare paired activation and rollback.
**Mode:** full — daily-driver boot-chain work.
**Branch:** `codex/dev147-fairydust-build`
**Linear:** DEV-147; DEV-163 owns USB data acceptance.
**Started:** 2026-09-05
**Reconciled:** 2026-09-05

## Context

The [fresh build plan](2026-09-04-dev147-fairydust-build.md) completed the offline kernel milestone. Its [dated evidence](../evidence/dev-147-fairydust-build-2026-09-04.md) records the full kernel, 1,862 modules and J413 DTB at Linux commit `83604c8b18e4673ed91e1172aef9aebeb0af20ce`, release `7.1.12-dev147-fairydust1`. These artifacts remain frozen in `/home/david/Work/dev147-fairydust-build`.

On 2026-09-05 the user authorized proceeding with the fresh plan. This continuation handles the next boot-integration milestone. The code worktree is `/home/david/Work/omarchy-dev147-fairydust-build`; new output belongs in `/home/david/Work/dev147-fairydust-boot-20260905`. The running kernel is still `7.1.6-1-1-ARCH`, and Omarchy remains dev-linked to `/home/david/o-live`.

## Approach

Build a new initramfs from the full candidate module tree with the installed Asahi hooks and firmware. Assemble an m1n1 stage-2 bundle privately from the installed m1n1/U-Boot binaries and pinned J413 DT. Stage the versioned files without selecting them. Retain the existing package guard.

m1n1 prepares Apple firmware and memory properties before GRUB. Supplying the raw DTB through GRUB skips that work. Replacing shared `boot.bin` also changes the DT used by the old default kernel. Therefore activation must pair the new m1n1 bundle with the exact new kernel/initramfs selection. A normal reboot or old GRUB entry is not a full rollback after that replacement.

The agent prepares and tests the complete staging command. David runs privileged operations himself, as required by the machine profile. The agent does not run sudo. Protected GRUB and old integration state are inspected and preserved by the reviewed stage helper; exact paired activation follows from those inputs.

## Execution Protocol

Use full `self-correction-loop`. The initramfs builder and stage-helper author own disjoint files. The orchestrator owns this plan and m1n1 assembly. Independent QA re-derives the artifact and preservation claims. Keep kernel, initramfs, staging, activation and hardware results distinct. Record failures before changing the recipe; stop and re-plan after the same failure twice or three fix cycles in one slice.

## Steps

- [x] Slice 1: Assemble complete offline boot inputs.
  Goal: private candidate initramfs and m1n1/U-Boot/DT bundle alongside the already-built kernel/modules.
  Probe first: inspect current loader versions, boot layout, effective initramfs hooks and firmware paths; test missing/tampered inputs before accepting new validation stages.
  Implementation: use isolated real mkinitcpio with explicit kernel/config/output and `--nopost`; assemble the boot bundle without executing `update-m1n1` or writing its `/run` paths.
  Validation: the offline boot gate checks exact inputs, bundle segmentation, initramfs module and firmware contents, dependency closure, and preserved live boot hashes.
  Exit criteria: artifacts, manifest, logs and limits pass independent QA.
  Evidence: `validate-boot.sh` exits 0 for author and independent reviewer; final independent run is `checks/offline-gate.k7tooauD` under the boot output. Kernel, actual initramfs/startup files, m1n1 segments, external firmware and all manifest checks pass.
  Assumption: installed m1n1 1.6.1 prepares the SIO/DP properties required by pinned fairydust, and all required build inputs are readable.
  Verify: inspect upstream m1n1 source and installed/live versions; validate DT aliases, firmware inputs and real image content. Runtime preparation remains a boot gate.
- [x] Slice 2: Prepare unselected staging and protected evidence collection.
  Goal: one reviewed user-run command installs only new versioned files and modules, retaining all active boot inputs.
  Probe first: real-entrypoint sandbox tests must reject altered inputs, existing outputs and unsafe paths, and prove active-file preservation.
  Implementation: root-owned staging copies, manifest and byte verification, unique destinations, package-lock/drift checks, and protected GRUB/state snapshots for later activation design.
  Validation: run the same entry point in a disposable namespace; verify all new files and all protected before/after identities; syntax and relevant repository gates pass or baseline failures are disclosed.
  Exit criteria: fixed delivery inputs and exact manual command pass independent review. The live staging action remains open until David runs it.
  Evidence: independent complete gate exits 0; all 20 stage tests and a full real-delivery namespace rehearsal pass, including all 1,862 published module bytes. Helper SHA-256 is `12501982dfd4adb347103671ce5dbf9650b53b628474a434de3c458fd98ad6a7`.
  Assumption: unselected files in a dedicated `/boot/dev147-fairydust-*` directory and a unique module release do not change normal boot.
  Verify: inspect GRUB discovery rules and assert no active boot, GRUB, preset, hook or old module path changes in fixtures.
- [x] FINAL: independently verify the offline integration and staging handoff.
  Goal: all checked claims can be reproduced by a non-author.
  Validation: rerun the complete boot gate and inspect plan, receipts, real artifact inventories, failure cases and user handoff.
  Exit criteria: no disputed preparation claim. Live staging, activation and hardware acceptance remain separate open work.
  Evidence: independent exact gate exits 0 in 48.363 seconds; source, handoff and evidence review support the offline claims. Both retained startup counterexamples reject. No disputed preparation claim remains.

## Validation

The [dated evidence and receipt](../evidence/dev-147-fairydust-boot-preparation-2026-09-05.md) record results. The [staging guide](../../dev/apple-dp-altmode/fairydust/boot-stage/README.md) owns the exact user command.

Run `bash /home/david/Work/omarchy-dev147-fairydust-build/dev/apple-dp-altmode/fairydust/validate-boot.sh`. It combines the full kernel gate, the real initramfs/startup checks, m1n1 bundle checks, external firmware and delivery hashes, staging-helper controls and full-delivery namespace rehearsal, shell syntax, Ruff formatting/linting and strict mypy. Each run retains its own logs under the boot output’s `checks/` directory. The existing full kernel gate remains the source/build baseline; no changed kernel inputs are permitted.

## Progress (LIVING)

- 2026-09-05: Re-read the completed plan, Personal/project/machine instructions, and live DEV-147. The issue remains In Progress. No project or Personal index exists at the inspected local pointers; the README owns navigation here.
- 2026-09-05: Live inspection confirms root is ext4, EFI is `/dev/nvme0n1p4` at `/boot/efi`, kernel `7.1.6-1-1-ARCH`, m1n1 package 1.6.1, U-Boot 2026.04.asahi2, and mkinitcpio 41.1. GRUB config and old integration state are root-private. Current boot bundle and package guard remain readable and hash-pinned.
- 2026-09-05: Started independent initramfs assembly and boot-path research. The old 7.1.6 single-module replacement recipe is unsuitable for the new full kernel; use real mkinitcpio against the complete new module tree.

- 2026-09-05: m1n1 bundle assembly and independent segment parsing pass: m1n1 1,114,112 bytes, J413 DT 72,115 bytes, one gzip stream 303,204 bytes; decompressed U-Boot 639,624 bytes. Separate assembly reproduces the bundle hash. Missing, truncated, changed, trailing and symlink inputs plus existing output are rejected. Generic validation wording was corrected to avoid implying that content checks establish selection state.
- 2026-09-05: Initramfs run-003 and actual-image re-extraction pass: 334 exact candidate modules, dependency closure, builtin GPU, Asahi hook, and 12 firmware files including six AVD files. Image SHA-256 is `e4e70b766e463468f01d1830a4dd1b42b0cbefb4d07463bdf7e54451ecce730a`; size is 191,153,387 bytes. Independent review is running.
- 2026-09-05: Frozen delivery manifest covers 1,885 files, SHA-256 `f33054856e60d3baf5cb7630cb8d7dfc60ffa586e16456c3e7313fffe6f7c59d`. Every runtime module file matches the frozen kernel candidate. Only the development `build` symlink was omitted from the new delivery copy.
- 2026-09-05: Repository `./test/all` exits 1: three missing omarchy-pkgs checks, the known runtime IPC registration mismatch, and a bar-widget temporary-directory cleanup race. The focused bar-widget rerun exits 0. Command metadata passes all 455 entries; all 458 bin syntax checks pass. No whole-repository PASS is claimed.

- 2026-09-05: Independent review found two validation gaps. The initramfs checker accepted a removed startup file and then an absolute host-resolving BusyBox symlink; exact startup identity/type/config checks and five controls now reject them while the actual image passes. The stage helper copied to EOF before validation; fixed byte/entry/depth limits and exact-size copies now reject oversized, growing and excessive-entry sources. All 20 stage tests and a full actual-delivery rehearsal pass. The later complete gate and independent rerun both pass.

- 2026-09-05: Complete author gate PASS at `checks/offline-gate.ZDD7H3p9`; independent gate PASS at `checks/offline-gate.k7tooauD` in 48.363 seconds. All three preparation steps are verified. The manual launcher remains unrun; selected boot and all hardware acceptance remain open.

## Discoveries (LIVING)

- The current live DT has a `dcpext` alias but no `sio` alias. The new DT requires m1n1 SIO firmware preparation. A raw GRUB `devicetree` replacement cannot substitute for that preparation.
- `update-m1n1` writes `/run/m1n1.conf` even with an explicit output. Its default DT scan selects `*-ARCH`, which excludes the candidate release. Assemble privately with explicit inputs instead of invoking that updater.
- The installed Asahi initramfs hook references older optional module names. Explicit current Apple module names are required to prevent silent omissions; firmware and hook semantics must still be retained.

- First initramfs run failed because namespace-mapped ownership did not permit mkinitcpio ownership-preserving copies. Existing fakeroot inside the read-only sandbox resolves that build prerequisite; no system package change was needed. The second image passed mkinitcpio, but the validator wrongly expected text module metadata that mkinitcpio deliberately removes. Validation now checks retained binary indexes and uses source metadata only in a separate depmod check copy. Final run-003 passes.
- The initial stage-test sandbox failed before entering the helper because it tried to create a mount path under read-only `/`. Correcting the test mount established the intended missing-helper RED, then real-entrypoint GREEN. This was a fixture correction.
- Shared-branch code-writer concurrency was tightened after initial disjoint-directory edits: initramfs and bundle code are frozen while the stage author finishes. Independent QA remains read-only.

- The stage helper originally read files to EOF before checking drift. The fixed candidate-specific budget rejects oversized, growing and excessive-entry sources before unbounded copies. No disk-space guarantee or atomic cross-filesystem activation is claimed.
- macOS/Recovery can restore the FAT boot bundle, but cannot be assumed to restore ext4 GRUB files. The next activation design must supply and verify that recovery route.

## Decision Log (LIVING)

- 2026-09-05: Stage unselected files before activation. Shared stage-2 DT selection precedes GRUB; activating only half the stack would create an unvalidated kernel/DT combination.
- 2026-09-05: Keep the existing linux-asahi/m1n1/uboot-asahi transaction guard. This is a parallel experimental release, not a package upgrade or an uninstall of the earlier opt-in.

- 2026-09-05: The privileged stage helper uses a dependency-free typed parser and frozen dataclasses, following adjacent boot helpers. Do not introduce a new runtime Pydantic dependency into this recovery path. Root operations use the standard-library implementation tested in a namespace.

## Follow-ups

- [ ] David runs the reviewed staging command; inspect its retained protected evidence.
- [ ] Prepare and review exact paired m1n1 + kernel/initramfs GRUB activation, complete restore and macOS/Recovery instructions. Verify original protected identities before any selected-boot write.
- [ ] Attended candidate boot, then firmware/DT/driver identity and internal/external display checks.
- [ ] Reconnects beyond the old exhaustion window; USB data/audio/charging on both ports/orientations; suspend/power later.
- [ ] Complete upstream USB4 integration after baseline acceptance; retain the original fresh plan's remaining capability work.
