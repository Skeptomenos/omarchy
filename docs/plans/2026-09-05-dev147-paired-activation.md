# Activate and recover the paired fairydust stack

**Goal:** Select the staged fairydust kernel, initramfs and m1n1-prepared device tree together, with a complete route back to the existing stack.
**Mode:** full — daily-driver boot-chain work.
**Branch:** `codex/dev147-fairydust-build`
**Linear:** DEV-147
**Started:** 2026-09-05
**Reconciled:** 2026-09-05

## Context

The user ran the reviewed stage launcher on 2026-09-05. Its private result is `/home/david/Work/dev147-fairydust-boot-20260905/stage/manual-results/result.json`. The launcher reports exit 0 and `STAGED_UNSELECTED`. Independent verification of the published files is the first step below. The running kernel is still `7.1.6-1-1-ARCH`.

The candidate release is `7.1.12-dev147-fairydust1`. Its boot files are in `/boot/dev147-fairydust-7.1.12-dev147-fairydust1` and its modules are in `/usr/lib/modules/7.1.12-dev147-fairydust1`. The [boot preparation plan](2026-09-05-dev147-fairydust-boot-integration.md) owns the completed offline milestone. Source and build inputs remain frozen.

The stage result exports the protected GRUB configuration. It selects entry 0 unless `next_entry` is set. Both existing Linux entries use the old kernel and initramfs. It sources an optional `/boot/grub/custom.cfg` at the end; that file was absent. m1n1 prepares the device tree before GRUB. Therefore the old GRUB menu is not a complete fallback after replacing the shared EFI `m1n1/boot.bin`.

The EFI partition is FAT and accessible from macOS/Recovery. `/boot/grub` is on ext4. A recovery procedure must not assume macOS can write ext4. No selected-boot change has been made.

## Approach

First verify the real staged publication. Then prove a boot-selection design whose recovery restores the entire old stack using accessible files. Investigate a GRUB dispatcher that selects the kernel from the hash of the EFI boot bundle: installing the dispatcher while the old bundle remains active could preserve the old boot, and restoring that bundle could select the old kernel again. This is a hypothesis until the exact installed GRUB implementation and interruption cases pass checks.

Prepare the exact activation and restore artifacts only after that design is established. Keep the package guard and old integration state. David runs any privileged command himself under the machine profile; the agent performs preparation and checks without sudo.

## Execution Protocol

Use full `self-correction-loop`. The orchestrator owns documentation. One agent owns code changes at a time. Independent QA must re-derive the stage receipt and boot-selection claims. No hardware test is implied by a static check, sandbox result or successful file installation.

## Steps

- [x] Slice 1: Verify actual staging and bind its evidence.
  Goal: establish the published candidate and the retained active stack.
  Probe first: check launcher exit, fixed input identities, manifest, public file inventory and protected configuration export.
  Implementation: add a read-only verifier and retain a bounded receipt without publishing the private configuration snapshot.
  Validation: run the verifier against the actual staged files; reject altered or missing proof inputs in isolated controls.
  Exit criteria: all published boot/module bytes match the frozen delivery; current readable active pins and kernel match; independent QA agrees.
  Evidence: `bash dev/apple-dp-altmode/fairydust/validate-staged.sh` exits 0 for the author (`checks/staged-gate.XdDL0sq9`) and independent QA (`checks/staged-gate.OMOzM8fN`). All 1,885 manifested publication files and the copied manifest match; all 1,862 modules match; all 10 verifier controls pass. Independent protected-path comparison finds 4,522 matches, zero mismatches and 68 root-private paths covered only by the stage receipt.
  Assumption: successful launcher output corresponds to the exact reviewed inputs and complete publication.
  Verify: hash the launcher/helper, saved result, installed manifest and every published manifest entry.
- [ ] Slice 2: Prove paired selection and FAT-accessible recovery.
  Goal: specify one coherent kernel/DT selection for every reachable activation and restore state.
  Probe first: inspect the exact GRUB hash command, parser and module availability; test original/candidate/unknown/missing inputs and saved/next-entry behavior.
  Implementation: retain primary-source evidence and a concrete selection prototype in private output, then promote only a supported design.
  Validation: real GRUB tooling and independent review; enumerate interrupted writes and failure before GRUB starts.
  Exit criteria: complete recovery does not require macOS ext4 writes, and no normal route selects an old kernel with the new DT.
  Assumption: installed GRUB can reliably identify the selected bundle and route to the paired stack.
  Verify: source inspection plus executable GRUB probes. A shell imitation or syntax-only check cannot prove runtime selection.
- [ ] Slice 3: Prepare the reviewed activation and restore handoff.
  Goal: exact user-run commands with preserved recovery files and explicit post-boot checks.
  Probe first: test drift, incorrect identities, existing destinations, partial states and interrupted publication in a disposable namespace.
  Implementation: bounded input verification, durable backups, ordered writes, captured results and a standalone recovery guide.
  Validation: one complete activation gate, including real-entrypoint rehearsal and selection probes.
  Exit criteria: independent QA passes before the command is offered; actual activation remains open until the user runs it.
  Assumption: the selected design can preserve recovery through interrupted writes across FAT and ext4.
  Verify: exercise every write boundary and recovery state; do not claim cross-filesystem atomicity.
- [ ] FINAL: independent verification.
  Goal: a non-author re-derives every completed claim and reruns the relevant whole gate.
  Validation: classify claims as VERIFIED, DISPUTED or UNVERIFIABLE HERE.
  Exit criteria: disputed claims return to open work; hardware-only claims remain explicit acceptance steps.

## Validation

The completed offline preparation gate remains `bash /home/david/Work/omarchy-dev147-fairydust-build/dev/apple-dp-altmode/fairydust/validate-boot.sh`. It validates unchanged build and delivery inputs. Slice 1 adds `bash /home/david/Work/omarchy-dev147-fairydust-build/dev/apple-dp-altmode/fairydust/validate-staged.sh`, which chains the whole preparation gate, verifier controls and actual-publication check. The [dated staging evidence](../evidence/dev-147-fairydust-staged-2026-09-05.md) records both successful runs. Slice 2 must establish executable selection evidence before an activation gate and user command are released.

## Progress (LIVING)

- 2026-09-05 07:59Z: Read the saved stage result and live issue. DEV-147 remains In Progress. The result reports `STAGED_UNSELECTED`; the current kernel and active Omarchy dev link remain unchanged. Started actual-publication verification and independent recovery design research.
- 2026-09-05: Actual stage milestone passes the complete author and independent gates. The active boot bundle, package guard and vendor firmware remain at their pinned hashes. All five saved configuration strings match their protected receipt hashes. Only the current GRUB configuration among those five files remains unreadable without root; a later privileged activation helper must recheck it before writing.

## Discoveries (LIVING)

- The captured GRUB environment has no saved/next entry variables. Future activation must still handle these variables explicitly; current absence does not prove they remain absent.

## Decision Log (LIVING)

- 2026-09-05: Continue from the staged candidate. Do not restage or rebuild unchanged artifacts. Prove the recovery route before handing off a selected-boot write.

## Follow-ups

- [ ] User-run activation and attended candidate boot.
- [ ] Verify running release, prepared SIO/DT properties, firmware, internal display, external DP and reconnects beyond the prior exhaustion window.
- [ ] USB data, audio and charging on both ports and orientations; suspend and power checks later.
- [ ] Complete the upstream USB4 series and its prerequisites after baseline acceptance, as tracked by the original fresh plan.
