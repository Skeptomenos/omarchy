# Activate and recover the paired fairydust stack

**Goal:** Select the staged fairydust kernel, initramfs and m1n1-prepared device tree together, with a complete route back to the existing stack.
**Mode:** full — daily-driver boot-chain work.
**Branch:** `codex/dev147-fairydust-build`
**Linear:** DEV-147
**Started:** 2026-09-05
**Reconciled:** 2026-09-05

**Continuation:** The [front-port stability plan](2026-09-05-dev147-front-port-stability.md) now owns open hardware acceptance, fixes and release work. This plan retains the completed activation/recovery evidence.

## Context

The user ran the reviewed stage launcher on 2026-09-05. Its private result is `/home/david/Work/dev147-fairydust-boot-20260905/stage/manual-results/result.json`. The historical stage result reports exit 0 and `STAGED_UNSELECTED`. Subsequent activation and boot succeeded; the running kernel is now `7.1.12-dev147-fairydust1`.

The candidate release is `7.1.12-dev147-fairydust1`. Its boot files are in `/boot/dev147-fairydust-7.1.12-dev147-fairydust1` and its modules are in `/usr/lib/modules/7.1.12-dev147-fairydust1`. The [boot preparation plan](2026-09-05-dev147-fairydust-boot-integration.md) owns the completed offline milestone. Source and build inputs remain frozen.

The stage result exports the protected GRUB configuration. It selects entry 0 unless `next_entry` is set. Both existing Linux entries use the old kernel and initramfs. It sources an optional `/boot/grub/custom.cfg` at the end; that file was absent. m1n1 prepares the device tree before GRUB. Therefore the old GRUB menu is not a complete fallback after replacing the shared EFI `m1n1/boot.bin`.

The EFI partition is FAT and accessible from macOS/Recovery. `/boot/grub` is on ext4. A recovery procedure must not assume macOS can write ext4. David activated the reviewed pair on 2026-09-05; the receipt reports `ACTIVATED_NOT_REBOOTED`. The first restart now runs `7.1.12-dev147-fairydust1`; hardware acceptance remains open.

## Approach

The staged publication and paired selection design now pass offline verification. Use the reviewed GRUB dispatcher to select the kernel from the hash of the EFI boot bundle. Install it while the old bundle remains active, then replace the bundle. Restoring the old bundle selects the old kernel again. Real GRUB probes establish this routing; candidate boot and physical interruption remain untested.

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
- [x] Slice 2: Prove paired selection and FAT-accessible recovery design.
  Goal: specify one coherent kernel/DT selection for every reachable activation and restore state.
  Probe first: inspect the exact GRUB hash command, parser and module availability; test original/candidate/unknown/missing inputs and saved/next-entry behavior.
  Implementation: retain primary-source evidence and a concrete selection prototype in private output, then promote only a supported design.
  Validation: real GRUB tooling and independent review; enumerate interrupted writes and failure before GRUB starts.
  Exit criteria: complete recovery does not require macOS ext4 writes, and no normal route selects an old kernel with the new DT.
  Evidence: the author and orchestrator each run the real GRUB probe with 19/19 PASS; independent run is `research/activation-design/root-independent-probes/runtime-probe-receipt.json`. Old, candidate, restored-old, missing commands, invalid inputs, config return and stale environment cases pass. The actual candidate config is instrumented at Linux/initrd dispatch and timeout, with one pre-menu environment echo; exact boot arguments and cleared settings pass. All 37 module dependencies match package and stage-protected hashes. The corrected macOS shell guards pass 14 local cases after six unsafe baseline continuations were reproduced. macOS/Recovery execution and actual boot remain untested; this checkbox covers design and executable offline semantics only.
  Assumption: installed GRUB can reliably identify the selected bundle and route to the paired stack.
  Verify: source inspection plus executable GRUB probes. A shell imitation or syntax-only check cannot prove runtime selection.
- [x] Slice 3: Prepare the reviewed activation and restore handoff.
  Goal: exact user-run commands with preserved recovery files and explicit post-boot checks.
  Probe first: test drift, incorrect identities, existing destinations, partial states and interrupted publication in a disposable namespace.
  Implementation: bounded input verification, durable backups, ordered writes, captured results and a standalone recovery guide.
  Validation: one complete activation gate, including real-entrypoint rehearsal and selection probes.
  Exit criteria: independent QA passes before the command is offered; actual activation remains open until the user runs it.
  Assumption: the selected design can preserve recovery through interrupted writes across FAT and ext4.
  Verify: inject selected-file replacement failures and review preparation/flush ordering in source. Do not claim cross-filesystem atomicity, fsync fault injection, SIGKILL or physical interruption coverage.
  Evidence: `bash dev/apple-dp-altmode/fairydust/validate-activation.sh` exits 0 in author run `checks/activation-gate.H3xj4U2r` and independent run `checks/activation-gate.xMLQu9Tn`. Both pass 22 namespace controls, four topology tests, 19 real GRUB probes, 14 recovery guard cases, exact launcher read-only preflights and the chained staging/full boot gates. Ruff, strict mypy and shell syntax pass. The [handoff](../../dev/apple-dp-altmode/fairydust/boot-activate/README.md) gives the exact commands.
- [x] FINAL: independent verification.
  Goal: a non-author re-derives every completed claim and reruns the relevant whole gate.
  Validation: classify claims as VERIFIED, DISPUTED or UNVERIFIABLE HERE.
  Exit criteria: disputed claims return to open work; hardware-only claims remain explicit acceptance steps.
  Evidence: the independent whole gate passes with unchanged executable and recovery inputs and no blocking review finding. The [dated activation preparation evidence](../evidence/dev-147-fairydust-activation-preparation-2026-09-05.md) records verified claims and limits. Actual activation, physical FAT publication, macOS execution and hardware behavior remain UNVERIFIABLE HERE.

## Validation

The completed offline preparation gate remains `bash /home/david/Work/omarchy-dev147-fairydust-build/dev/apple-dp-altmode/fairydust/validate-boot.sh`. It validates unchanged build and delivery inputs. Slice 1 adds `bash /home/david/Work/omarchy-dev147-fairydust-build/dev/apple-dp-altmode/fairydust/validate-staged.sh`, which chains the whole preparation gate, verifier controls and actual-publication check. The [dated staging evidence](../evidence/dev-147-fairydust-staged-2026-09-05.md) records both successful runs. The released activation gate chains these checks and executable selection/recovery probes. Its PASS covers the prepared handoff only.

## Progress (LIVING)

- 2026-09-05: Near-MagSafe connection produces no image after 20 seconds. USB-C partner/PD detection occurs, but no DPTX connection follows. Source and live DT inspection identify the current fixed PHY1/front-port DP route; only typec1 has the display binding. See [rear-port evidence](../evidence/dev-147-fairydust-rear-port-2026-09-05.md). Both-port DP routing requires further integration, not more waiting on this connection.

- 2026-09-05: Second front-port reconnect succeeds, with user-reported 10–12 seconds to image after about five seconds unplugged. Kernel disconnect-to-connect interval is 15.046 seconds; connect-to-modeset completion is 2.530 seconds. Physical reinsertion is not timestamped. See [second reconnect evidence](../evidence/dev-147-fairydust-front-reconnect2-2026-09-05.md). Delayed detection and attached-at-boot failure remain open.

- 2026-09-05: David clarifies that the monitor was attached throughout boot on the front/lower USB-C port. It showed no image until a reconnect. Current DP is connected/enabled; logs show DPTX connection, HPD and a 3840×2160 nominal 60 Hz modeset after reconnect. Record one hot-plug success and an attached-at-boot detection defect, not full display acceptance. See [front-port evidence](../evidence/dev-147-fairydust-front-display-2026-09-05.md).

- 2026-09-05: First candidate boot succeeds. Running release and command line match `7.1.12-dev147-fairydust1`. Live SIO firmware parameters are present; SIO protocol v9 and both DCP boots are logged. Internal eDP is connected/enabled; external DP is disconnected. See [first-boot evidence](../evidence/dev-147-fairydust-first-boot-2026-09-05.md) for warnings and limits. Proceed to one attended display connection before repeated reconnect or suspend testing.

- 2026-09-05: David ran the activation launcher successfully. `activation/activate-results.iUG81ebY` reports exit 0, empty stderr and `ACTIVATED_NOT_REBOOTED`. Readable live hashes match the candidate bundle, old recovery bundle, copied guide and retained guard. GRUB and its support directory are root-private; their successful final verification is established by the pinned privileged helper's receipt, not a second unprivileged read. No package lock remains. See the [activation evidence](../evidence/dev-147-fairydust-activated-2026-09-05.md). Do not rerun activation or gates that require the original selected state.

- 2026-09-05 07:59Z: Read the saved stage result and live issue. DEV-147 remains In Progress. The result reports `STAGED_UNSELECTED`; the current kernel and active Omarchy dev link remain unchanged. Started actual-publication verification and independent recovery design research.
- 2026-09-05: Actual stage milestone passes the complete author and independent gates. The active boot bundle, package guard and vendor firmware remain at their pinned hashes. All five saved configuration strings match their protected receipt hashes. Only the current GRUB configuration among those five files remains unreadable without root; a later privileged activation helper must recheck it before writing.
- 2026-09-05: Corrected GRUB selection passes all 19 real-parser/disk-image probes for author and orchestrator. Root and ESP images use the actual filesystem types and UUIDs. The emulator does not execute the candidate kernel or dynamically load EFI modules; those remain distinct source/inventory and hardware checks. The accepted dispatcher is `58fd5692f3e28013ce54df8de255c552117c1786a7d027e2da21b7fc8a63a9d2`; candidate config is `d4082978c51d96419e98218e472b76653ca52bf1c357fc12ba50786f671efcf6`.

- 2026-09-05: The final author and independent activation gates pass. Executable and recovery inputs are frozen. The handoff is ready; activation and hardware acceptance remain open. One earlier run refused a guide hash changed during its execution; repinning and both final reruns resolve that input-freeze invalidation.

## Discoveries (LIVING)

- The captured GRUB environment has no saved/next entry variables. Future activation must still handle these variables explicitly; current absence does not prove they remain absent.
- GRUB 2.14 `insmod` can return success after a load error. The missing-command execution path can also return success. The initial single-success hash selector therefore cannot be released. Source inspection and real emulator fault probes exposed this before any selected-boot write. Re-plan selection around two mutually exclusive hash results, an expected-false test sanity check and nonempty search results, then prove the revised behavior in GRUB.
- A recovery shell draft used validation commands joined by `&&` under `set -e`. A failed non-final test in such a list does not stop the shell. Split guards into separate commands and test them before promoting the recovery draft.
- The captured ESP contains `ubootefi.var`. U-Boot uses this file for persistent EFI variables, so its contents need not remain identical after another boot. Recovery must validate the old boot dependencies without requiring all unrelated pre-activation state to remain frozen. [U-Boot EFI variable storage](https://docs.u-boot.org/en/v2026.01/api/efi.html).

## Decision Log (LIVING)

- 2026-09-05: Continue from the staged candidate. Do not restage or rebuild unchanged artifacts. Prove the recovery route before handing off a selected-boot write.
- 2026-09-05: Use a top-level GRUB dispatcher, installed while the old bundle remains active. Require exactly one of the two bundle hash checks to match. A test sanity check and nonempty search results guard GRUB's missing-command behavior. Replacing only the EFI bundle then selects its paired kernel. Place the verified old bundle at `/boot/efi/m1n1/dev147-recovery/boot.bin.old-203ab702` before any active change. Restore that bundle first; restore original GRUB only afterward.
- 2026-09-05: Treat a damaged or missing EFI bundle as an early-boot recovery case. macOS can restore it by GPT UUID without ext4 writes. A GRUB console bypass to the preserved old configuration is available only after restoring the old bundle and fully rebooting; it is not a way to pair an old kernel with a device tree already loaded from the candidate.
- 2026-09-05: Verify live mount identity read-only, then independently recheck it in the privileged bootstrap before helper execution. Recheck directory device identities before active replacements. Unprivileged namespace fixtures cannot mount a real FAT filesystem, so they exercise the helper and pinned bootstrap with topology discovery as an explicit fixture boundary. Test topology parsing/rejection separately. Do not add a production bypass or claim a physical FAT transaction rehearsal.
- 2026-09-05: Namespace tests also need synthetic prior-state identities because the unprivileged agent cannot copy the 68 root-private old files. Keep the production stage-result digest fixed and prove rejection before substituting the fixture identity in the test harness. No production argument or environment override is added. The rehearsal covers unchanged helper logic with these two declared fixture boundaries; separate checks cover exact bootstrap bytes and live readable state. Production must still verify all historical protected identities before activation.
- 2026-09-05: Activation requires the staged candidate and historical protected state to match. Restore depends on the trusted old backups, original boot dependencies and guard, while preserving current unrelated state. It must not require intact candidate files or unchanged EFI-variable/package metadata. Check dynamic `custom.cfg` inputs explicitly so a new file cannot change the preserved configuration's routing.

## Follow-ups

- [ ] Review coherent upstream dynamic DP routing for both ports; the current fairydust DT wires only typec1/PHY1. Preserve the working front-port baseline.

- [ ] Diagnose already-attached display detection at boot; one front-port failure followed by successful reconnect is recorded.
- [ ] Repeat controlled front-port reconnects, then check the other port and orientations.

- [x] User-run activation; saved result and readable live pins verified.
- [x] Attended candidate boot; running release `7.1.12-dev147-fairydust1` verified.
- [ ] Verify running release, prepared SIO/DT properties, firmware, internal display, external DP and reconnects beyond the prior exhaustion window.
- [ ] USB data, audio and charging on both ports and orientations; suspend and power checks later.
- [ ] Complete the upstream USB4 series and its prerequisites after baseline acceptance, as tracked by the original fresh plan.
