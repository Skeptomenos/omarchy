# Prepare a capture of hub power state before USB loss

**Goal:** Prepare a bounded reader and reviewed handoff for measuring hub/controls PM state during the next attended reconnect, without changing the working display drivers or PM policy.
**Mode:** light — passive reader and fixture checks; no kernel or system mutation.
**Branch:** `codex/dev-147-t1-image-offline`
**Linear:** DEV-147
**Started:** 2026-08-31

Status, reconciled 2026-08-31 11:13Z: the [user clarification](../evidence/dev-147-lg27-reconnect-usb-loss-2026-08-31.md#correction--no-new-reconnect-2026-08-31-1113z) resolves the timing question. “Yes” referred to the earlier completed reconnect, not a new action during the PM window. The 180 root-only samples are a no-action baseline. Video remains the working prototype path; the open investigation concerns the monitor's USB hub/data connection. Child-PM measurement and cause remain open. No reconnect, repeat, PM change or automatic rearm.

Saved comparison, 2026-08-31 11:25Z: the [initialization-path analysis](../research/dev-147-usb-hub-init-comparison-2026-08-31.md) places descriptor/setup failures before the later suspend warning. Status error `-5` hides the original transfer result. The next useful measurement is event-level control-transfer results plus runtime-PM transitions, not another root-only sampling window. Its collection method and release remain open. No user action is needed now.

## Context

The [attended reconnect](../evidence/dev-147-lg27-reconnect-usb-loss-2026-08-31.md) restored video but only transient USB devices. Final USB loss occurred about 32 seconds after bus recreation. The later capture missed child PM state. The current working W image, all old experiments, backups and the paused timer watch remain unchanged. This continuation supersedes the completed startup plan's proposed reconnect, not its history.

## Approach

Prepare a small unprivileged reader under `/home/david/o/.dev147-stage/tipd-image-code-20260829.TPjkwkTaMa/worktree/dev/apple-dp-altmode/`. It will sample only the selected DWC3 controller's USB subtree. Arm it before requesting any new physical action. A sample records current PM policy and counters, not causal ordering between samples.

That reader is now prepared and its first window is complete. The saved comparison shows that some failed generations last less than one sample interval. Keep the reader as supporting evidence; do not reuse it alone to infer failure/PM ordering. A future event-level method needs its own containment review before activation.

## Execution Protocol

Use the light `self-correction-loop`. Validate saved capture integrity and the reader against filesystem fixtures; review independently before handoff. Never read partner `usb_mode`, issue USB control transfers, change PM, load drivers or use sudo. Exclude the known unsupported PHY/port delay fields. Keep the reader unarmed during preparation.

## Steps

- [x] Record the one reconnect outcome.
  Goal: distinguish restored video from USB reliability.
  Validation: `sha256sum -c capture.sha256` in the private reconnect case returns 25/25 OK; independent saved-data QA verifies event order, identities and the partial PM read.
  Exit criteria: [dated evidence](../evidence/dev-147-lg27-reconnect-usb-loss-2026-08-31.md) preserves user testimony, USB failure and uncertainty.
- [x] Prepare the bounded passive reader.
  Goal: record short-lived hub/controls generations before disappearance.
  Validation: the focused gate below passes both separate syntax checks, all 14 fixture checks and diff hygiene. Private and integrated script/test hashes match. The initial placeholder failure and the later encoding-failure RED are retained.
  Exit criteria: [reader](../../dev/apple-dp-altmode/usb-pm-recorder.sh) and [tests](../../dev/apple-dp-altmode/usb-pm-recorder-test.sh) reviewed, no live run. Live mode uses a fixed controller root, at most 180 samples near one-second cadence, and an outer 195-second timeout with two-second kill grace. No persistence or unattended retry.
  Assumption: ordinary USB-device PM metadata remains readable while the device exists.
  Verify: fixture tests cover disappearance; later live output must retain actual read errors and object identity. No claim of atomic or non-perturbing hardware observation follows.
- [x] Preparation: independent verification.
  Goal: re-derive the new evidence and reader claims, not replay historical image suites.
  Validation: fresh-context saved-data QA plus the complete focused reader gate and semantic containment review.
  Exit criteria: all new completed claims VERIFIED or explicitly qualified; no unresolved DISPUTED item.
  Evidence: fresh verifier `reconnect_evidence_qa` reruns the complete focused gate with exit 0 and all 14 checks passing, verifies hashes and saved capture checksums, and independently tests refusal, root-only discovery and encoding failure. No disputed claim or required reopened step remains. Live behavior and historical initial-RED provenance retain the explicit limits below.
- [x] Execute one bounded live window and preserve its limits.
  Goal: sample before a separately released reconnect, without system mutation.
  Validation: recorder exit 0; saved-data checks verify 180 contiguous samples, unchanged boot brackets and 33/33 raw checksums. The incremental journal parses and its wrapper exits 0.
  Exit criteria: capture preserved; no automatic repeat. This completes the recorder run, not the child-PM measurement.
- [x] Record the resolved physical-action report.
  Goal: separate the earlier completed reconnect from the later passive window.
  Validation: David explicitly says no monitor removal/change in the last hour and identifies his “yes” as the earlier five-second-wait/ten-second-video-return test; the dated correction retains this testimony.
  Exit criteria: no new reconnect is claimed; the agent's interpretation is withdrawn and the timing question is closed.
- [x] (2026-08-31 11:25Z) Compare saved initialization and define the missing measurement.
  Goal: identify the earliest supported divergence without assigning PM causality.
  Validation: three selected journal hashes and JSON/order checks pass; independent data and pinned-source reviews distinguish descriptor validation, nonfatal TT fallback, status-result remapping and later suspend failure.
  Exit criteria: [dated comparison](../research/dev-147-usb-hub-init-comparison-2026-08-31.md) separates observations from source hypotheses and specifies the next measurement; no new live method is released.
- [ ] Obtain the missing child-state and transfer observation.
  Goal: locate the first USB-hub failure without conflating it with working video or later PM cleanup.
  Validation: first review availability, privileges, device scope, shared clock alignment, loss detection, duration/byte caps and cleanup for control-URB headers plus scoped runtime-PM events. Any later attended capture needs a new, explicit cable instruction after arming; none is released now.
  Exit criteria: the first control-transfer failure is ordered against PM entry/return for the same generation, or the result records why that order remains unknown. No PM fix follows from the root-only window or an incomplete trace.
- [x] FINAL: independently verify the live-window checkpoint.
  Goal: re-derive the new capture claims without repeating hardware actions or old fixture suites.
  Validation: saved-data gate below and independent semantic review.
  Exit criteria: capture claims verified; child PM remains open. The later user clarification closes the physical-action question as no new reconnect.
  Evidence: independent verifier `pm_window_qa` re-derives all 33 checksums, sample schema/ordinals/statuses, three boot brackets, journal identity/order/cursor, exits/stderr, sizes/hashes and after-state claims. Diff hygiene passes. No blocking discrepancy; this checkpoint does not complete the open measurement above.
  Continuation evidence: the same verifier independently checks 21/21 new raw files, both journal intervals, joins, event timing and after-state. The earlier failed-suspend event is not covered by child PM samples and is not promoted to a cause.
- [x] FINAL: independently verify the saved-comparison checkpoint.
  Goal: re-derive new comparison and handoff claims, not replay old hardware or fixture tests.
  Validation: the selected-journal gate below, pinned-source review and independent review of the three changed documents.
  Exit criteria: completed claims VERIFIED or explicitly qualified; missing live transfer/PM evidence remains open.
  Evidence: `pm_window_qa` independently reruns `sha256sum -c selected-journals.sha256` (3/3 OK), the JSON/count/common-boot/order gate, local-link checks and `git diff --check`; VERDICT: PASS, no DISPUTED claim. `usb_suspend_source_check` independently reviews the final source interpretations and measurement limits; VERDICT: PASS. Current protected hashes, actual recovery execution, collector suitability and live causal ordering remain UNVERIFIABLE HERE, not accepted results.

## Validation

From the feature worktree, run the complete reader gate:

```bash
bash -n dev/apple-dp-altmode/usb-pm-recorder.sh && bash -n dev/apple-dp-altmode/usb-pm-recorder-test.sh && bash dev/apple-dp-altmode/usb-pm-recorder-test.sh && git diff --check
```

Expected: 14 `PASS` checks, `VERDICT: PASS` and exit 0. Tests use real filesystem fixtures. Optional `DEV147_TEST_ROOT` selects a private fixture parent; otherwise they use the system temporary directory. Fixtures remain available for review. The gate never calls live `--record`. No runtime environment override is needed for the reader. Build, package, image and graphical suites are not part of this non-installed diagnostic reader. Do not reinterpret fixture success as a live hardware test.

Recorder SHA-256: `d821433f9ee253221a3c3329f2e354612bfe4fb08a4da2920cd6f6b9854e2fef`. Tests: `20a4745e08ee4af963924ae51d07c5248029b6bc1ba9bb436a99d96a16282e8f`.

Later live invocation, only after readiness and private output setup: `timeout --kill-after=2s 195s /bin/bash <reviewed-private-reader> --record`. The agent runs this unprivileged; David does not need a shell command. Keep stdout, stderr, exit status and boot/time brackets in a fresh private directory. Do not reuse a result path or automatically retry.

For the live-window evidence-only checkpoint, validate the saved case, not the unchanged reader implementation: `sha256sum -c capture.sha256`, parse all samples and journal rows with `jq`, require ordinals 1–180, compare the three boot brackets, check recorded exits/stderr, then `git diff --check`. Independent review checks the claimed topology, clock limits and action uncertainty. The earlier implementation gate remains the gate for future source changes; this capture adds none.

For the later correlation-only checkpoint, use its separate 21-file manifest, both saved journals, cursor/boot joins, recorded exits/stderr and `git diff --check`. Do not rerun the recorder or old fixture suite to validate a documentation-only correlation.

For the saved initialization comparison, run `sha256sum -c selected-journals.sha256` in the private comparison case. Parse the three selected journals with `jq -s`; require 1,151 / 273 / 407 rows, one common boot, and ordered wall/journal-monotonic timestamps. Check the reported device milestones against the saved messages, then run `git diff --check` and independent source/document review. Private receipts and exact input paths are retained in DEV-147. No live sysfs, recorder, image, fixture or graphical suite is needed for this documentation-only gate.

## Progress (LIVING)

- 2026-08-31 09:49Z: captured the completed reconnect. Video recovery is corroborated; hub/controls fail again. Independent saved-data QA passes with the documented root-port EIO exception.
- 2026-08-31: private reader preparation started. No live recorder or further reconnect is running.
- 2026-08-31: author, independent reader QA and integrated-copy gates pass all 14 fixture checks. Both source hashes match the reviewed private copies. No installed runtime script, package, boot file or PM policy was changed; the reader remains unarmed.
- 2026-08-31: final independent plan, code, saved-data and handoff review PASS. Preparation ends at user availability for a new attended capture. No live action has run.
- 2026-08-31 10:15–10:18Z: after David's “ready”, the agent armed the reader and released one reconnect instruction. All 180 snapshots are root-only; no physical-action report has arrived. The process exited 0. The instruction is now expired; no repeat is running. Saved capture checks pass 33/33; the after-snapshot still has both outputs/PD active and Full/100% battery.
- 2026-08-31: independent saved-data QA PASS. The complete checkpoint gate exits 0 with `VERDICT: PASS`. DEV-147 readback preserves its prior history and In Progress state. Only this dated evidence and its two owning plan pointers change; the child-PM objective stays open.
- 2026-08-31 11:06Z: recorded David's exact “yes” and asked which reconnect it identifies. Saved-gap correlation and independent QA pass 21/21 checksums. Earlier USB errors include a failed runtime-suspend attempt; later logs do not locate a new reconnect. Both outputs/PD remain active in the snapshot. No physical action, source change, build or PM change was performed by the agent.
- 2026-08-31 11:13Z: David resolves the ambiguity: no new reconnect; “yes” meant the earlier reported test. Reclassified the PM window as a no-action baseline, preserved history and closed the timing question. This is a documentation correction, with no new hardware observation or action.
- 2026-08-31 11:25Z: saved initialization comparison and independent data/source checks complete. Descriptor errors can precede hub identification; hub 22 fails setup before failed suspend. Defined an event-level measurement, not a new image or PM workaround. Recorded cross-task boot/recovery preservation in the main plan; no hardware or package window is released.
- 2026-08-31: final independent saved-data/source/document review PASS with no disputed claim. Root's selected-data gate also passes. Only the dated comparison and its two plan owners change. Child transfer/PM measurement stays open; no runtime observation was added.

## Discoveries (LIVING)

- Independent review found that a failed per-object JSON encoder could be hidden by a later successful object, falsely implying disappearance. A real oversized fixture reproduced that failure. Explicit propagation now aborts with no partial snapshot; the regression test passes.
- Syntax checks must run once per script; passing two filenames to `bash -n` only parses the first.
- Clock fields are `uptime_seconds`, not journal-monotonic timestamps. `/proc/uptime` [includes suspend time](https://man7.org/linux/man-pages/man5/proc_uptime.5.html). Use the captured wall-time bracket for journal alignment. Samples are non-atomic; a short transition or same-path replacement can evade sampling.
- The first live window observes 1.00–1.01-second sample-start spacing by the saved uptime clock and only the same four root objects. Child discovery and child PM remain unmeasured. No new USB/display event appears in its journal; this is not evidence of a failed reconnect without the physical-action report.
- The earlier-gap journal records hub configuration errors before a failed runtime/autosuspend attempt on the same generation. This establishes a useful error path, not successful suspension or an initiating cause. The event predates the recorder and does not fill in missing child PM state.
- The descriptor helper can synthesize `-71`; the standard status helper can replace the original transfer result with `-5`. Kernel log errno alone therefore does not identify the wire/HCD failure. An approximately 170 ms generation also fits between one-second samples.

## Decision Log (LIVING)

- 2026-08-31: arm before asking for another reconnect because the previous post-report capture missed two short-lived child generations during the roughly 32-second interval from bus recreation to final loss. Do not add another kernel image or disable PM without the missing child-state evidence.
- 2026-08-31: keep source-based USB2 hardware-LPM exclusions separate from unmeasured runtime autosuspend. Neither the cable-warning string nor suspended empty root hubs establish cause.
- 2026-08-31: accept the initial placeholder RED as author execution provenance with retained failure text; do not call it independently replayed. Current fixture results and the corrected encoding-error behavior have independent execution evidence. Live cadence, topology and mid-read hardware races remain untested, not silently accepted as runtime PASS.
- 2026-08-31: retain the first live window as inconclusive for reconnect/child PM. Wait for the physical-action report instead of extending the bounded capture, repeating the cable instruction or changing PM. No response is not proof that David did nothing.
- 2026-08-31: preserve the compound-question “yes” without inventing a new event timestamp. Clarify new versus earlier reconnect; do not replace that missing association with log silence or the older failed-suspend event.
- 2026-08-31: accept the explicit clarification and withdraw the agent's initial interpretation. Keep successful video separate from USB-data reliability. Compare the saved initialization failures before proposing a new live test; do not disable PM on the strength of a warning that follows hub errors.
- 2026-08-31: select request status/length plus scoped PM transitions as the next measurement. This resolves an actual information gap; repeating the same root-only reader or rebuilding an image does not. Review the collection method before asking David for one coordinated action.

## Follow-ups

- The physical-action question is resolved. Prepare and review the event-level collection method before arranging any case: MagSafe, lid open, same monitor/cable/front port and empty monitor USB-A ports. Recheck current identity/root, arm before a new explicit instruction and preserve the bounded stop. No action is required from David now.
- Coordinate boot-hook, firmware/kernel package and Wi-Fi GPU/session windows using the [main plan's preservation handoff](dev-147-m2-displayport.md#cross-task-boot-and-recovery-handoff-living--not-released). Worktrees do not isolate the running kernel or desktop session.
- Mouse, PM mutation, sudo, new images, reboot, timer-Off experiment and upstream submission remain held. Do not resume the old watch.
