# Prepare a capture of hub power state before USB loss

**Goal:** Prepare a bounded reader and reviewed handoff for measuring hub/controls PM state during the next attended reconnect, without changing the working display drivers or PM policy.
**Mode:** light — passive reader and fixture checks; no kernel or system mutation.
**Branch:** `codex/dev-147-t1-image-offline`
**Linear:** DEV-147
**Started:** 2026-08-31

Status, reconciled 2026-08-31 10:22Z: preparation complete; the first bounded live window has ended. It captured 180 root-only samples. David's physical-action report remains pending; the reconnect classification and child-PM objective are inconclusive. The instruction is expired. Do not reconnect, repeat or rearm automatically. See the [dated window addendum](../evidence/dev-147-lg27-reconnect-usb-loss-2026-08-31.md#addendum--first-bounded-pm-window-2026-08-31-10151018z).

## Context

The [attended reconnect](../evidence/dev-147-lg27-reconnect-usb-loss-2026-08-31.md) restored video but only transient USB devices. Final USB loss occurred about 32 seconds after bus recreation. The later capture missed child PM state. The current working W image, all old experiments, backups and the paused timer watch remain unchanged. This continuation supersedes the completed startup plan's proposed reconnect, not its history.

## Approach

Prepare a small unprivileged reader under `/home/david/o/.dev147-stage/tipd-image-code-20260829.TPjkwkTaMa/worktree/dev/apple-dp-altmode/`. It will sample only the selected DWC3 controller's USB subtree. Arm it before requesting any new physical action. A sample records current PM policy and counters, not causal ordering between samples.

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
- [ ] Clarify physical execution and obtain the missing child-PM observation.
  Goal: distinguish an unperformed or out-of-window action from an observed reconnect.
  Validation: correlate David's action report with the saved 12:15:03.933–12:18:03.962 CEST window; only then decide whether a separately armed case is needed.
  Exit criteria: an observed child generation has readable PM state before loss, or an explicit recorded reason it could not be measured. No PM fix follows from this root-only window.
- [x] FINAL: independently verify the live-window checkpoint.
  Goal: re-derive the new capture claims without repeating hardware actions or old fixture suites.
  Validation: saved-data gate below and independent semantic review.
  Exit criteria: capture claims verified; physical execution and missing child PM remain explicitly open.
  Evidence: independent verifier `pm_window_qa` re-derives all 33 checksums, sample schema/ordinals/statuses, three boot brackets, journal identity/order/cursor, exits/stderr, sizes/hashes and after-state claims. Diff hygiene passes. No blocking discrepancy; this checkpoint does not complete the open measurement above.

## Validation

From the feature worktree, run the complete reader gate:

```bash
bash -n dev/apple-dp-altmode/usb-pm-recorder.sh && bash -n dev/apple-dp-altmode/usb-pm-recorder-test.sh && bash dev/apple-dp-altmode/usb-pm-recorder-test.sh && git diff --check
```

Expected: 14 `PASS` checks, `VERDICT: PASS` and exit 0. Tests use real filesystem fixtures. Optional `DEV147_TEST_ROOT` selects a private fixture parent; otherwise they use the system temporary directory. Fixtures remain available for review. The gate never calls live `--record`. No runtime environment override is needed for the reader. Build, package, image and graphical suites are not part of this non-installed diagnostic reader. Do not reinterpret fixture success as a live hardware test.

Recorder SHA-256: `d821433f9ee253221a3c3329f2e354612bfe4fb08a4da2920cd6f6b9854e2fef`. Tests: `20a4745e08ee4af963924ae51d07c5248029b6bc1ba9bb436a99d96a16282e8f`.

Later live invocation, only after readiness and private output setup: `timeout --kill-after=2s 195s /bin/bash <reviewed-private-reader> --record`. The agent runs this unprivileged; David does not need a shell command. Keep stdout, stderr, exit status and boot/time brackets in a fresh private directory. Do not reuse a result path or automatically retry.

For the live-window evidence-only checkpoint, validate the saved case, not the unchanged reader implementation: `sha256sum -c capture.sha256`, parse all samples and journal rows with `jq`, require ordinals 1–180, compare the three boot brackets, check recorded exits/stderr, then `git diff --check`. Independent review checks the claimed topology, clock limits and action uncertainty. The earlier implementation gate remains the gate for future source changes; this capture adds none.

## Progress (LIVING)

- 2026-08-31 09:49Z: captured the completed reconnect. Video recovery is corroborated; hub/controls fail again. Independent saved-data QA passes with the documented root-port EIO exception.
- 2026-08-31: private reader preparation started. No live recorder or further reconnect is running.
- 2026-08-31: author, independent reader QA and integrated-copy gates pass all 14 fixture checks. Both source hashes match the reviewed private copies. No installed runtime script, package, boot file or PM policy was changed; the reader remains unarmed.
- 2026-08-31: final independent plan, code, saved-data and handoff review PASS. Preparation ends at user availability for a new attended capture. No live action has run.
- 2026-08-31 10:15–10:18Z: after David's “ready”, the agent armed the reader and released one reconnect instruction. All 180 snapshots are root-only; no physical-action report has arrived. The process exited 0. The instruction is now expired; no repeat is running. Saved capture checks pass 33/33; the after-snapshot still has both outputs/PD active and Full/100% battery.
- 2026-08-31: independent saved-data QA PASS. The complete checkpoint gate exits 0 with `VERDICT: PASS`. DEV-147 readback preserves its prior history and In Progress state. Only this dated evidence and its two owning plan pointers change; the child-PM objective stays open.

## Discoveries (LIVING)

- Independent review found that a failed per-object JSON encoder could be hidden by a later successful object, falsely implying disappearance. A real oversized fixture reproduced that failure. Explicit propagation now aborts with no partial snapshot; the regression test passes.
- Syntax checks must run once per script; passing two filenames to `bash -n` only parses the first.
- Clock fields are `uptime_seconds`, not journal-monotonic timestamps. `/proc/uptime` [includes suspend time](https://man7.org/linux/man-pages/man5/proc_uptime.5.html). Use the captured wall-time bracket for journal alignment. Samples are non-atomic; a short transition or same-path replacement can evade sampling.
- The first live window observes 1.00–1.01-second sample-start spacing by the saved uptime clock and only the same four root objects. Child discovery and child PM remain unmeasured. No new USB/display event appears in its journal; this is not evidence of a failed reconnect without the physical-action report.

## Decision Log (LIVING)

- 2026-08-31: arm before asking for another reconnect because the previous post-report capture missed two short-lived child generations during the roughly 32-second interval from bus recreation to final loss. Do not add another kernel image or disable PM without the missing child-state evidence.
- 2026-08-31: keep source-based USB2 hardware-LPM exclusions separate from unmeasured runtime autosuspend. Neither the cable-warning string nor suspended empty root hubs establish cause.
- 2026-08-31: accept the initial placeholder RED as author execution provenance with retained failure text; do not call it independently replayed. Current fixture results and the corrected encoding-error behavior have independent execution evidence. Live cadence, topology and mid-read hardware races remain untested, not silently accepted as runtime PASS.
- 2026-08-31: retain the first live window as inconclusive for reconnect/child PM. Wait for the physical-action report instead of extending the bounded capture, repeating the cable instruction or changing PM. No response is not proof that David did nothing.

## Follow-ups

- First resolve whether David performed the expired instruction during the recorded window. If another case is needed, arrange it separately: MagSafe, lid open, same monitor/cable/front port and empty monitor USB-A ports. Recheck current identity/root, arm before a new instruction and preserve the bounded stop. Do not infer a no-action result from silence alone.
- Compare per-generation PM values with a bounded incremental journal. A recorded suspend is not by itself proof that it caused the loss; unsampled brief transitions remain possible.
- Mouse, PM mutation, sudo, new images, reboot, timer-Off experiment and upstream submission remain held. Do not resume the old watch.
