# Reconcile M2 port support with upstream

**Goal:** Select an upstream baseline, retain only necessary local changes, and define the work still needed for full M2 MacBook Air USB-C support.
**Mode:** light for this source assessment; later kernel integration and hardware validation require full mode.
**Branch:** `codex/dev147-upstream-assessment`
**Linear:** DEV-147; DEV-163 owns monitor USB-data failures.
**Started:** 2026-09-04
**Reconciled:** 2026-09-04

## Context

The current display experiment uses Linux Asahi 7.1.6, a reduced J413 device-tree backport, TIPD hotplug forwarding, and candidate AFK service reuse plus PR582 timeout semantics. It has hardware evidence for native external video and separate reconnect failures. The combined candidate has a user-reported staging PASS but no hardware acceptance result.

The original execution worktree is `/home/david/o/.dev147-stage/tipd-image-code-20260829.TPjkwkTaMa/worktree`. The opt-in integration worktree is `/home/david/o/.dev147-stage/dev147-optin-integration.RPAkznRRKE/worktree`. This assessment uses `/home/david/Work/omarchy-dev147-upstream-assessment`; it does not change either accepted worktree or the running system.

## Approach

Compare the local patch inventory with immutable upstream commits. Prove source composition in an isolated scratch directory and reuse existing lifecycle checks. Recommend a staged integration path after independent review; source compatibility does not establish kernel-build or hardware compatibility.

## Execution Protocol

Use the light `self-correction-loop` for this assessment. Validate source identities, patch coverage, composition results, documentation links, and diff hygiene at handoff. The independent verifier must distinguish source proof from unperformed build and hardware work.

## Steps

- [x] Inventory all local patch files, branches, integration code, and diagnostic-only changes.
  Goal: account for every local change without carrying historical experiments into the proposed runtime stack.
  Validation: Git inventories and local source reads agree with the assessment table.
  Exit criteria: each item has a keep, replace, drop-from-new-stack, or defer classification.
- [x] Compare upstream branches and prove the proposed source composition.
  Goal: identify a coherent base and the smallest remaining patch series.
  Validation: pinned branch ancestry, exact source comparisons, sequential patch application, and existing lifecycle harness results.
  Exit criteria: the report names the exact base, applied changes, dependency gaps, and evidence limits.
- [x] Write the recommendation and remaining capability roadmap.
  Goal: make the next implementation step clear without treating experimental video as full port support.
  Validation: each recommendation maps to source evidence or a named unresolved measurement.
  Exit criteria: research and evidence records are linked from the reader entry point and DEV-147.
- [x] FINAL: independent verification.
  Goal: re-derive the checked claims without relying on the report author's conclusions.
  Validation: a separate reviewer checks source identities, composition evidence, all patch classifications, and documentation checks.
  Exit criteria: disputes are corrected; unperformed builds and hardware tests remain explicit open work.

## Validation

Use `git ls-remote` for upstream pins and `git ls-tree` for the eight local patch files. Compare downloaded source hashes against the accepted 7.1.6 tree. Run `git apply --check` and sequential application only in scratch copies. Reuse the AFK test module's exact-function extraction and lifecycle harness without changing its historical source pin. Run repository documentation and standard QA checks before handoff. Record outputs in the dated evidence document.

## Progress (LIVING)

- 2026-09-04: Created an isolated assessment worktree from research commit `cfcc45d92`. The original task is idle. Upstream heads match the preceding read-only comparison. No system or boot change occurred.
- 2026-09-04: Accounted for all eight patch files and five historical branches in the [assessment](../research/dev-147-upstream-reconciliation-2026-09-04.md). Saved pins, patch order, hashes, and outputs in the [source receipt](../evidence/dev-147-upstream-reconciliation-2026-09-04.json).
- 2026-09-04: Both retained patches apply to fairydust and the alternate 7.2 source. Both extracted-function C harnesses passed the candidate and rejected four negative controls. This covers source composition only.
- 2026-09-04: Repository command metadata and syntax checks passed. `./test/all` returned 1: three shell test files lack the external package checkout; the desktop smoke test saw three IPC handler registrations for two screens. No application code changed in this assessment. These results do not constitute a green full-repository gate.
- 2026-09-04: Published the source recommendation and remaining work as an own-state [DEV-147 handoff](https://linear.app/helmus/issue/DEV-147/usb-c-displayport-external-monitor-unavailable-on-m2-macbook-air#comment-7683faf1). The issue remains In Progress. README links the assessment.
- 2026-09-04: Independent verifier returned **PASS for the source assessment** with no blocking findings. Fresh source downloads reproduced all base/combined hashes, sequential patch application, and all lifecycle outcomes. All eight patch blobs, five historical branch pins, six remote pins, document links, metadata, syntax, and QA-log identity were checked. Full repository QA remains FAIL as recorded. The verifier did not access Linear; the orchestrator separately verified the handoff comment and In Progress state through the live CLI.

## Discoveries (LIVING)

- `fairydust` is a small extension of `asahi-wip`, while `asahi-wip-7.2` contains a separate USB4 development stack. A newer branch name alone does not imply complete DisplayPort support.
- The pinned 7.2 branch deliberately gates the Asahi GPU driver with `depends on BROKEN`. It is unsuitable as the immediate Omarchy desktop base.
- The full M2 DT includes SIO/audio dependencies and an ATC power-domain workaround omitted by the local reduced DT. It still selects one DP port and does not establish correct suspend.
- Neither the AFK lifetime change nor PR582's timeout behavior is present in the inspected upstream sources. PR582 remains an upstream-authored pending proposal.

## Decision Log (LIVING)

- 2026-09-04: Keep this handoff at source-assessment scope. Preserve all accepted images, historical test pins, and recovery assets. New builds, staging, and hardware validation are later work.
- 2026-09-04: Recommend fairydust `b8810ad6442699f610984f3eceea2e3234a50b77` plus the corrected AFK patch and one PR582 application. Replace the local DT/TIPD backports. Preserve original PR582 authorship and provenance.
- 2026-09-04: Keep Linux source integration separate from Omarchy delivery. Use the complete upstream USB4 series and dependency chain for a later isolated integration; do not directly adopt the GPU-broken 7.2 branch.
- 2026-09-04: Retain the staged 7.1.6 AFK+PR582 candidate as an optional bounded hardware control while preparing fairydust. Its acceptance does not gate source integration or justify continued old-baseline delivery work.
- 2026-09-04: Independent review cannot establish build, ABI, boot, or hardware acceptance from this source assessment. Keep those as explicit follow-ups; do not carry source PASS into a release verdict. The four broader repository test failures remain recorded and unresolved.

## Follow-ups

- [ ] Build the selected complete kernel, modules, DTB, and boot assets in a subsequent implementation task. The six-file scratch composition is not a complete kernel tree.
- [ ] Complete USB data, charging, suspend, both-port routing, and USB4 acceptance separately from the external-video milestone.
