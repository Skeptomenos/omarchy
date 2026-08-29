# DEV-147 offline-readiness NO-GO — 2026-08-29

**Status: REVIEWED NO-GO.** Independent completion-audit and safety review passed on 2026-08-29. This is the accepted result for the current autonomous run. It is not a technical rejection or pass of T1, and it does not permit work to resume. The [main plan](../plans/dev-147-m2-displayport.md) owns current authority. The [diagnostic subplan](../plans/dev-147-usb-startup-diagnostic.md) owns the retained A0–A4 sequence.

## Objective and verdict

The autonomous objective was to prepare one contained M2 front/lower USB-C startup experiment through the first manual review or staging boundary. A GO required the complete offline package: one justified candidate or diagnostic, fresh contained tests and real-tool controls, a verified image and capture binding, an implemented power guard, a tested no-replace staging-only helper, reviewed recovery and one-case instructions, independent QA and safety review, a private seal, own-branch publication, and DEV-147 synchronization.

**Reviewed verdict: NO-GO for the current autonomous run.** A0, A1, and substantial A2 evidence are complete. The selected T1 sender diagnostic remains justified. However, David's explicit battery-incident hold suspended the earlier authority to execute the remaining offline workloads. The real 424-child E control, T1 image, operational collector binding, power-guard implementation, staging helper, and A3/A4 package cannot be completed safely or permissibly without new authority.

This is the goal's authority-based NO-GO path. It is not a shortcut for uncertainty, failed tests, or unfinished work. Continuing would cross an explicit user stop. Calling the unexecuted semantic draft or zero-child models sufficient would misstate evidence.

## Requirement-by-requirement audit

| Objective requirement | Current evidence | Audit result |
|---|---|---|
| Compare preserved W/E/D3 evidence and pinned TIPD, DWC3, ATC, and boot sources | The [A0 investigation](../research/dev-147-hpd-startup-2026-08-29.md) records source pins, saved timing, competing explanations, capture limits, and the latest W filename qualification. It separates proved software behavior from unproved runtime causality. | **Proved for A0.** No causal fix follows. |
| Select one minimal justified candidate or diagnostic | Independent A1 review selected the bounded TIPD sender diagnostic `dev147-tipddiag1-v1`. It preserves hardware operations and uses E-equivalent packaged-DWC3 availability. | **Proved for A1.** T1 remains a diagnostic, not a fix. |
| Do not replay E/D3 or queue B/G | Plans and accepted checkpoints keep E and D3 consumed, W recovery consumed, and B/G unprepared. | **Proved.** No replay or ladder ran. |
| Fresh verified unprivileged containment with fixed pins | The [T1 foundation](dev-147-t1-offline-foundation-2026-08-29.md) records fresh isolation, seven smoke checks, fixed read-only bindings, bounded workloads, and unchanged inputs. | **Proved for completed A2 workloads.** A later workload still needs a fresh probe. |
| Focused source regression with genuine RED/GREEN | T1 source has retained RED and 22 passing focused methods. The original operation models and 13 test bodies remain. | **Proved within the userspace seam.** No kernel or hardware safety follows. |
| Candidate module, ABI, import/export, and frontend checks | The private T1 module is reproducible. Scoped review accepts four data tables, 46 callback bindings, nine exports, 99 imports, shared layouts, and the selected 688-byte wrapper. SHA-256 is `a0fdadc351261643545e5afd8561923be99431661c447084336c9318f5b0c02f`; build ID is `40aa54382047ba36b02c9ac0da65a213862a77ad`. | **Proved within recorded limits.** Zero CRCs and the missing production SN debug entry remain qualified. No load occurred. |
| Structural parser and bounded capture rules | The strict T1 parser passes 31 methods. The capture package passes 21 methods after a retained two-assertion RED. It binds submitted module notes and enforces bounded, complete receipt structure. | **Proved structurally.** Active collection and accepted-image provenance remain closed. |
| E-control boundary and fixed real-tool recipe | The boundary passes 18 methods and 11 harmless children. The pure recipe passes 16 zero-child methods and authenticates the exact 424-command plan and retained E model. | **Partly proved.** The real 424-child no-change/index control has not run. Fixture bytes are not operational evidence. |
| Real E no-change/index control | No accepted execution or result exists. | **Missing GO requirement.** Explicitly prohibited while the hold remains. |
| One verified T1 image with exact archive preservation | No T1 image exists. The pure image contract passes 15 methods only. | **Missing GO requirement.** Assembly must follow the real E control. |
| Fixed image/module/revision/target/component capture binding and collector | The capture contract remains closed to operational provenance. No active collector or accepted-image binding exists. | **Missing GO requirement.** |
| Focused proof that stock Type-C and USB-PD paths are preserved | Static review found no direct PD-contract, PDO, source/sink, power-status, or suspend/resume edit. It also found indirect serialized-callback delay and display-complex power risks. The [power-guard design](../research/dev-147-power-guard-design-2026-08-29.md) is reviewed. | **Design evidence only.** No implemented or tested guard exists, and runtime power safety remains unproved. |
| Tested fixed-source, no-replace staging-only helper | No T1 staging helper exists. | **Missing A3 GO requirement.** Old D2/C3 helpers are consumed and cannot substitute. |
| Exact one-case manual handoff with stop/cancel rules and recovery | The [visible recovery card](../plans/dev-147-visible-recovery-card.md) passed offline documentation QA and safety review. It is not rehearsed or released. No T1-specific final handoff exists. | **Partly proved.** Separate-device availability, David's read-through, normal-shutdown rehearsals, the Linux-volume label, and final T1 handoff remain open. |
| Independent QA, safety review, seal, own-branch publication, and DEV-147 sync | Accepted A0/A1 and partial A2 checkpoints have their recorded reviews. This NO-GO dossier passed independent completion-audit and safety review. | **Missing for the final T1 package.** No A3/A4 seal, reviewed publication, remote readback, or final Linear sync exists. |
| Stop before the first manual staging/review boundary | No T1 helper, stage, selection, or live action occurred. | **Proved.** The run stopped earlier at the authority boundary. |

## Proved retained state

The current-run read-only status check matched the fixed kernel and package pins: running kernel `7.1.6-1-1-ARCH`, `linux-asahi 7.1.6.asahi1-1`, `m1n1 1.6.1-1`, and Mesa `26.1.8-1`. The documentation writer did not repeat a package query. Any later drift still stops execution.

The accepted A2 foundation includes:

- fresh containment and an uninstrumented working-HPD control;
- the scoped type, packaged-frontend, allocation-table, import, export, and binary checks;
- 22 T1 source methods after retained RED;
- 15 pure-image, 31 parser, 18 E-boundary, 16 pure-recipe, and 21 capture-package methods;
- a reproducible private T1 module with the exact identity above;
- bounded child-process and output behavior for the completed workloads;
- preservation of W, E, D3, stock files, backups, prior helpers, and sealed evidence.

None of those results executes the real E reconstruction, creates an initramfs, observes startup, proves receiver delivery, establishes USB enumeration, or proves charging safety.

## Retained unexecuted semantic draft

The separate private branch `codex/dev-147-t1-image-offline` remains dirty and untouched by this audit:

```text
 M dev/apple-dp-altmode/usbdiag/tipd-image/README.md
?? dev/apple-dp-altmode/usbdiag/tipd-image/e-control-semantic-test-contract.md
?? dev/apple-dp-altmode/usbdiag/tipd-image/test_e_control_semantic.py
```

Current read-only identities are:

| File | SHA-256 |
|---|---|
| Tracked `run_e_control.py` subject | `099be3713b7d7b40020de10ca38f0a943da3da60509acb153b2d3de390e44f1d` |
| Untracked semantic contract | `4d603fa01a1a1d36fb78034dcdc5d9558a269aff046069311fd03f4db08c90f9` |
| Untracked three-method test source | `fcaeea7e094c32bf0d2a4e7cddaf621f30171821d78ff03b3849a10ec033a672` |
| Modified README | `c5753c9c7eed7b83e65eda6c381aca61a7af896ff0e726ad3989c501586a6ece` |

The draft identifies itself as a third corrected, zero-child semantic RED source. It has not been executed. It cannot prove a real child, real depmod, real lookup, compression, archive preservation, image, load, stage, boot, or hardware result. The two rejected earlier semantic candidates remain retained outside that worktree. This audit does not import, compile, run, correct, accept, publish, or discard any draft byte.

## Point-in-time safety state

An already-completed bounded read-only check during this current run reported:

| Signal | Point-in-time value |
|---|---:|
| Battery capacity | 93% |
| Battery status | `Charging` |
| Aggregate input-power limit | 59,800,000 µW (59.8 W) |
| MagSafe source `0-003a` | online |
| Aggregate `macsmc-ac` | online |
| Monitor source `0-003f` | online |
| Omarchy Stay Awake | enabled |

This was a single default-stock-core snapshot. It is **not** the required 16-sample, 15-minute stock baseline. Source `online` values can be cached, aggregate AC does not identify delivered source power, and the input-power limit is not measured delivery. Keep MagSafe connected. Stay Awake must be disabled and visibly verified before unattended normal use; this audit did not change it.

## Indispensable authority and manual observations

The immediate blocker is authority, not missing code knowledge. David explicitly paused T1 and all candidate work after the battery incident. Earlier autonomous permission no longer authorizes the real E control, image assembly, collector activation, guard implementation, helper work, or another sandbox run.

The exact immediate user boundary is one idle-safety check and one decision. Before an unattended offline continuation, David runs `omarchy toggle idle allow-idle`, then `omarchy toggle idle status`, and verifies that it reports `"enabled":false`. A missing, malformed, or different status keeps the HOLD active. The agent does not run these commands.

- **Keep HOLD:** no work resumes; preserve all state.
- **Release offline work only:** David explicitly states, “Release DEV-147 for contained unprivileged offline A2–A4 only. Keep every live-action, candidate selection/boot, production preflight/staging, sudo, reboot, cable, and device hold active.”

That release would authorize only the remaining unprivileged offline sequence below. It would not authorize production preflight/staging, candidate selection/boot, or another live action.

Separate later manual observations remain mandatory before any live handoff:

1. Put the exact committed recovery card and pinned restore guide on another device and confirm both are readable.
2. David reads the card and confirms the branches.
3. From a healthy stock boot, use normal shutdown only to rehearse visible startup options, record the exact Linux-volume label, select the unedited `Arch Linux` entry, and return to stock.
4. Use another normal shutdown to verify visible `Options` → Recovery authentication → Recovery Terminal and separate-device guide readability. Do not run the guide or mount EFI.
5. At a separately authorized live gate, confirm the exact physical setup and complete the 15-minute stock power baseline. The current 93% snapshot cannot substitute.

## Alternatives ruled out

- **Continue under the old autonomous approval:** ruled out because David's later explicit hold supersedes it.
- **Accept the semantic draft:** ruled out because it is unexecuted, dirty, zero-child source and is not accepted evidence.
- **Treat the pure 424-command recipe as the real control:** ruled out because it executes zero children and authenticates only a plan and fixture model.
- **Assemble T1 before the real E control:** ruled out because stock archive and index preservation would lack the required real-tool control.
- **Reuse E, D3, W, or an old helper:** ruled out because those handoffs are consumed and their results do not answer T1's sender question.
- **Automatically prepare B/G or replay a ladder:** ruled out by scope and because no evidence justifies those cases.
- **Convert T1 into a behavior fix:** ruled out because saved evidence does not prove receiver-side or hardware causality.
- **Rely on monitor-only power or the current snapshot:** ruled out by the depletion incident and the power-guard contract.
- **Treat recovery-card text review as a rehearsal:** ruled out because the visible picker, Recovery Terminal, guide access, and Linux-volume label remain unobserved in that rehearsal.
- **Declare a GO package from partial A2 evidence:** ruled out because the image, binding, guard, helper, A3/A4 seal, handoff, publication, and Linear closeout are absent.

## Precise work remaining after an offline-only release

1. Revalidate kernel/dependency pins and a fresh unprivileged containment probe. Stop on drift.
2. Review the retained semantic draft without executing it, correct it only if needed, preserve a genuine semantic RED, and obtain the focused GREEN required by its accepted contract.
3. Run and independently review the real 424-child E no-change/index control in a fresh private sandbox.
4. Assemble and verify only the T1 image. Require exact raw-record, payload, metadata, dependency, alias, symbol-index, and all-seven-index preservation evidence.
5. Activate the fixed image/module/revision/target/component capture binding and bounded collector only against the accepted artifact.
6. Implement the reviewed power guard and pass its fake-file/fake-D-Bus, cadence, timeout, refusal, partial-receipt, and forbidden-action tests.
7. Prepare the fixed-source, no-replace staging-only helper and test it only on synthetic/private files with the reviewed one-entry `sync` manifest delta.
8. Prepare the exact T1 one-case handoff, integrate the visible recovery card and later rehearsal gates, and retain stock as the automatic default.
9. Obtain independent QA and safety review. Seal private artifacts and evidence.
10. Update source and living docs, commit and push the reviewed checkpoint to the existing own branch, verify remote readback, and synchronize DEV-147.
11. Stop at the first manual review/staging boundary. Do not stage, select, boot, reconnect, or add a USB device.

## Preservation and audit limits

- Preserve the private dirty T1 worktree exactly as observed until a released, reviewed continuation owns it.
- Preserve all accepted and rejected drafts, old images, root-private files, backups, recovery bundles, helpers, journals, seals, and historical evidence.
- Keep `/home/david/o-live`, `/boot`, `/usr/lib/modules`, `/etc`, live devices, display state, and boot defaults unchanged.
- Root-private bytes retain qualified user-validator provenance. Do not request duplicate privileged reads.
- The visible recovery card is reviewed but unrehearsed. The restore script remains untested on macOS.
- T1 remains a justified diagnostic. This NO-GO does not show that T1 is unsafe, wrong, or unable to answer its bounded sender question.
- The current point-in-time charging state does not resolve monitor standby behavior or candidate Type-C power causality.
- This dossier is the accepted current-run REVIEWED NO-GO result. It does not accept or pass T1.

## Final review

Independent completion-audit and safety review passed on 2026-08-29. They accepted this authority-based NO-GO result, not T1 or an unfinished package. Every hold and the exact release boundary above remain active.

No T1 code, test, build, helper, stage, reboot, cable, module, device, or package action occurred in this audit. The only changes are this audit and its living documentation pointers.
