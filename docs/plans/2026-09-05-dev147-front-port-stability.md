# Qualify front-port DisplayPort and contribute isolated fixes

**Goal:** Deliver a reproducible front-port DisplayPort build that passes a defined daily-driver acceptance matrix, and prepare independently reviewable driver fixes for Asahi. Preserve a path to automatic two-port routing and full USB-C/USB4 support.
**Mode:** full — experimental kernel on a daily driver.
**Branch:** `codex/dev147-fairydust-build`
**Linear:** DEV-147; existing DEV-163 owns monitor-hub data loss.
**Started:** 2026-09-05

## Context

Worktree: `/home/david/Work/omarchy-dev147-fairydust-build`. Frozen kernel source: `/home/david/Work/dev147-fairydust-build/linux`, commit `83604c8b18e4673ed91e1172aef9aebeb0af20ce`. Running release: `7.1.12-dev147-fairydust1`. It combines pinned Asahi fairydust with corrected AFK service reuse and the attributed PR582 timeout change. Source, installed artifacts and recovery inputs must remain frozen during baseline acceptance.

The [paired activation plan](2026-09-05-dev147-paired-activation.md) owns completed boot preparation and recovery. This plan supersedes its open hardware follow-ups as the execution owner. The user has booted the candidate. Front-port display has returned on three reported connections, at 3840×2160 near 60 Hz. The monitor was not detected when already attached at boot. Reconnect latency varies by user observation, and physical insertion times were not recorded. The near-MagSafe port has no display route in the current fixed device tree; this is a software limitation.

Historical [AFK exhaustion evidence](../evidence/dev-147-afk-service-exhaustion-2026-09-02.md) records a 16-service capacity on endpoint 0x28, followed by rejected announcements. Firmware channel numbers are not host array indices. Repeated connection calls are not reliable counts of distinct service generations.

Do not edit `/home/david/o`, `/home/david/o-live`, selected boot files or frozen recovery code. No agent sudo, automatic reboot, cable action, suspend, driver unbind or reads of Type-C partner `usb_mode`. David performs physical and privileged steps. Do not rerun pre-activation gates against the activated state.

## Approach

First measure and qualify the working front-port path. Fix shared lifecycle and startup behavior with small patches; do not add fixed-port shortcuts, arbitrary sleeps or automatic cable-reset workarounds. Check upstream routing architecture early, but implement two-port support later unless diagnosis establishes it as a prerequisite for correctness.

A stable front-port release and an upstream contribution are separate deliverables. An isolated AFK fix can be prepared for Asahi before the entire release qualifies. Mainline Linux acceptance is a separate upstream process. Do not duplicate PR582 or claim its authorship.

## Execution Protocol

Use full `self-correction-loop`. Root owns scope and documentation. One SWE owns implementation; independent QA runs the relevant gate and reviews claims. Freeze each test candidate. Change one cause at a time. Preserve failed evidence and stop the physical sequence on the first failure. Human image confirmation and software state are separate facts.

## Steps

- [x] Slice 1: Establish trustworthy front-port acceptance capture.
  Goal: one read-only command records each attended test without losing failure evidence or mistaking collection success for hardware PASS.
  Probe first: confirm live release, endpoint capacity, available logs and existing safe sysfs interfaces. Confirm negative cases reject wrong release and unavailable evidence.
  Implementation: add the small collector and focused tests under `/home/david/Work/omarchy-dev147-fairydust-build/dev/apple-dp-altmode/fairydust/acceptance/`. Write unique private results under `/home/david/Work/dev147-fairydust-acceptance-20260905`.
  Validation: the acceptance directory's single `validate.sh` command must test its actual entry point, declared fixture boundaries, incomplete evidence and live read-only capture. Independent QA must rerun it.
  Exit criteria: exact commands ready; current baseline captured; source-derived AFK threshold recorded; no system writes or unsafe sysfs reads.
  Assumption: current logs can demonstrate accepted service announcements beyond the old capacity.
  Verify: count endpoint-specific announcements and errors in one complete boot; if logs are incomplete, mark the endurance claim inconclusive and add bounded diagnostics before testing.
  Evidence: `bash dev/apple-dp-altmode/fairydust/acceptance/validate.sh` exits 0 for corrected author run `checks/collector.ivHF8J3n` and independent run `checks/collector.s1QPrrz2`. Eight actual-entry-point controls, lint, format, strict mypy, syntax and honest live capture pass. Independent review finds no remaining blocker. Live capture reports twelve external announcements/six arithmetic pairs, nine firmware error records and no collection issues; it does not accept endurance. See [milestone evidence](../evidence/dev-147-front-stability-start-2026-09-05.md).
- [ ] Slice 2: Prove front-port reconnect endurance.
  Goal: establish recovery through repeated teardown and reconnection beyond the old failure window.
  Probe first: count current accepted endpoint 0x28 services; inspect original and patched allocation/retirement semantics.
  Implementation: run attended batches on the same monitor/cable/port; five seconds unplugged, then wait up to 30 seconds for image. Record each failure immediately and retain disconnected/connected snapshots and user visual confirmation.
  Validation: first reach a ten-generation checkpoint in one boot, then at least 20 successful display generations for release qualification. Require accepted service announcements beyond the original 16-service capacity, no service exhaustion, crash, stuck display or missing evidence. Then cover both cable orientations; do not infer orientation from unrecorded actions.
  Exit criteria: generation count and visual outcomes agree. A failure reopens lifecycle diagnosis; successes below threshold remain partial. Thirty seconds is a test timeout, not an acceptable latency target.
  Assumption: the corrected AFK lifecycle survives late replies and repeated teardown.
  Verify: compare observed transitions with the existing positive/negative lifecycle harness; review any timeout or unexpected announcement before further cycles.
- [ ] Slice 3: Fix attached-at-boot detection and characterize latency.
  Goal: an already attached front-port monitor works after boot without a manual reconnect, with measured connection timing.
  Probe first: trace the source path from CD321x state to connector notification, mux/PHY readiness and external DCP initialization. Compare boot versus successful reconnect. Review available upstream fixes before writing one.
  Implementation: add the smallest cause-backed shared driver fix in an isolated candidate; retain the current working candidate for comparison. If correct routing is prerequisite, re-plan this slice around upstream routing rather than patching around it.
  Validation: matched cable/monitor configuration, explicit insertion markers, at least five attached-display boots and five detached-then-connect boots. Separate insertion-to-detection, detection-to-modeset and user-visible delay. Set the latency acceptance bound from measured known-good comparison before declaring PASS.
  Exit criteria: all startup cases recover without manual workaround, latency has an agreed evidence-based bound, and Slice 2 regression checks pass on the new candidate.
  Assumption: startup loss can be fixed independently of two-port routing.
  Verify: source ordering and runtime observations; abandon that assumption if the notification contract requires broader routing support.
- [ ] Slice 4: Prepare the smallest upstream contribution.
  Goal: a reviewer can reproduce the original defect and assess our novel fix independently of Omarchy packaging.
  Probe first: recheck current Asahi branches and submissions for superseding fixes and maintainer conventions.
  Implementation: prepare a clean patch/draft with rationale, lifecycle invariants, reproduction, before/after evidence, hardware coverage and explicit limits. Attribute borrowed changes. Keep unrelated startup, packaging and routing changes separate.
  Validation: relevant kernel build and lifecycle regression gate, independently reviewed diff, no unsupported causal claims. Historical failures on a different kernel are supporting evidence, not a matched control proving this patch alone caused recovery.
  Exit criteria: submission-ready artifact and recommended upstream target. User authorization is required before sending a public submission/comment; preparation proceeds without waiting.
  Assumption: our AFK correction remains novel and fits the target branch.
  Verify: compare exact target source and existing submissions immediately before preparation.
- [ ] Slice 5: Qualify and package the front-port release.
  Goal: an explicitly scoped daily-driver release with reproducible installation and tested rollback.
  Probe first: inventory all untested acceptance cells and boot warnings; inspect existing DEV-163 before USB data work.
  Implementation: close blockers, package the coherent kernel/modules/device tree/firmware dependencies, retain provenance and guarded rollback.
  Validation: both cable orientations; checksum-verified USB2/USB3 transfers where devices permit; simultaneous display/data/power; measured charging; external audio; internal display/audio/backlight regression checks; at least ten attended suspend/resume cycles with and without the display; an extended normal-use session; tested rollback and reinstall. Required unavailable equipment or scenarios stay open, not PASS.
  Exit criteria: all declared front-port release cells pass on the release candidate. Package installation success alone is insufficient. Rear-port display remains explicitly unsupported in this release.
  Assumption: the experimental base can meet the declared release scope without regressions elsewhere on the laptop.
  Verify: compare against the retained known-good system and resolve blocking regressions before release.
- [ ] FINAL: independent verification.
  Goal: non-author re-derives completed claims and reviews the release and upstream artifacts.
  Validation: rerun the applicable offline gates and audit recorded hardware matrix as VERIFIED, DISPUTED or UNVERIFIABLE HERE. Hardware records do not become repeat tests by being reviewed.
  Exit criteria: no disputed release claim; remaining limits explicit. Keep this plan open until the scoped release and submission-ready contribution are complete.

## Validation

The next milestone gate is `bash /home/david/Work/omarchy-dev147-fairydust-build/dev/apple-dp-altmode/fairydust/acceptance/validate.sh` once implemented. Its PASS means the collector is trustworthy, not that the hardware is stable. Later kernel changes require their source/build/lifecycle gates plus the relevant attended matrix. The old pre-activation gates intentionally require obsolete selected state and are not a release check for this running candidate.

Release scope is front-port DisplayPort with working associated daily-driver behavior. Full support additionally requires automatic routing to either USB-C port, coherent USB4/Thunderbolt integration, and a new regression matrix. No completion date is inferred from three successful cable connections.

## Progress (LIVING)

- 2026-09-05: David confirms all latest three front-port reconnects restored the image in about five seconds each. This brings confirmed visible recoveries to six. `python3 dev/apple-dp-altmode/fairydust/acceptance/snapshot.py six-confirmed` records `six-confirmed.8o5egq0k`: DP connected/enabled, twelve external announcements/six pairs, one external DCP boot, nine firmware error records, zero classified host errors and no collection issues. Exit 1 correctly means captured error records, not a collection failure. Four further successful generations are required for the ten-generation checkpoint; endurance remains open.

- 2026-09-05: Slice 1 completed after one QA correction for mixed-controller counting. Final author and independent gates both exit 0 with eight controls. The measured pre-batch-to-current increase is six external service announcements. The latest three visual outcomes remain pending; Slice 2 stays open. All frozen activation inputs still match; no kernel or boot change was made.

- 2026-09-05: User approved front-port stability first, early upstream architecture check, isolated fixes, then two-port support. Started acceptance collector implementation and independent source review of AFK capacity and startup notification behavior. DEV-147 remains In Progress.
- 2026-09-05: `git ls-remote https://github.com/AsahiLinux/linux.git` still reports fairydust `b8810ad6442699f610984f3eceea2e3234a50b77` and `bits/200-dcp` `52f0b76aaae7b9a1cc2100f4a9b33257b450d5c0`; no newer tip on those branches to substitute for this baseline. This is not a search of every submitted patch. Saved the six-announcement pre-batch baseline and requested three attended reconnects while the collector is prepared.

## Discoveries (LIVING)

- `AFK_MAX_CHANNEL` is 16 in the pinned kernel. Historical endpoint 0x28 announcements exhausted that capacity. The physical reconnect count must be derived from actual generations, not assumed from cable actions or increasing firmware channel IDs.
- Independent source review confirms two endpoint 0x28 services per observed generation: generation nine crosses the stock capacity; generation ten matches the existing harness target. The pre-batch snapshot had six announcements, channels 1/3, 5/7 and 9/11, with one external DCP boot. The later 11:17:24Z snapshot has 12 announcements/six pairs. Human image confirmation for the latest batch remains pending. Ten and twenty generations are bounded coverage targets, not indefinite-stability proof.
- Current acceptance consists of three user-reported front-port recoveries; attached-at-boot detection fails. A 2.530-second logged DPTX-connect-to-modeset interval does not measure cable-insertion latency.
- Independent source review identifies a startup notification-loss window: CD321x can queue attached-state HPD before DRM registers the connector; `drm_connector_oob_hotplug_event()` drops an absent-connector lookup and does not retain it for replay. The later DCP readiness replay covers HDMI GPIO, which J413 lacks. Current timestamps are consistent but do not prove the initial HPD bit or send time. Next diagnostic must correlate those events before writing a fix.
- Collector QA reproduced a counting bug before handoff: ten announcements on each of two DCP controllers were summarized as twenty, although capacity applies separately. Restrict the checkpoint summary to the fixed external DCP `271c00000.dcp`, endpoint 0x28, and add a mixed-controller entry-point regression. Initial gate PASS did not establish correct summary scope; retain the counterexample and rerun after correction.

## Decision Log (LIVING)

- 2026-09-05: Stabilize shared behavior on one working route before expanding the hardware matrix. Preserve source portability; no new fixed-port shortcuts.
- 2026-09-05: Separate upstream fix readiness from full package release. Do not hold a proven isolated fix for unrelated feature completeness.
- 2026-09-05: Keep the running candidate and recovery artifacts unchanged while collecting baseline evidence. Two-port implementation becomes active only after these milestones or a demonstrated architectural dependency.

## Follow-ups

- Automatic DP routing to either physical USB-C port, then both-port regression matrix.
- Complete coherent upstream USB4/Thunderbolt support and prerequisites; DP Alt Mode success does not establish tunneling.
- Additional monitor/cable coverage beyond the current LG setup before a broader hardware-support claim.
