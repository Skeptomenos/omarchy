# DEV-147 — working/candidate comparison, 2026-08-31

Scope: saved M2 startup logs, pinned source and accepted image manifests only. No new build, test suite, hardware operation or fix. This compares the [candidate failure](../evidence/dev-147-pr582-lg35-failure-2026-08-31.md) with [working-driver recovery](../evidence/dev-147-w-recovery-after-pr582-2026-08-31.md).

## Main finding

W and the PR582 candidate differ in five archive entries, not just the timeout patch. The observed candidate failure begins before DP link setup. Neither the recovery nor the source comparison isolates a faulty hunk. Keep the working setup; do not select a speculative fix.

## Proven artifact differences

| Image | Change from its base | Module count / driver family |
|---|---|---|
| W | Earlier working image | 199; packaged AppleDRM, working TIPD |
| E | W + packaged `dwc3-apple.ko`; replace `modules.dep.bin` and `modules.alias.bin` | 200; same AppleDRM/TIPD as W |
| T1 | E + diagnostic/rebuilt `tps6598x-core.ko` replacement | 200; packaged AppleDRM, T1 TIPD |
| PR582 control | T1 + rebuilt unmodified `appledrm.ko` replacement | 200; T1 TIPD |
| PR582 candidate | T1 + rebuilt patched `appledrm.ko` replacement | 200; T1 TIPD |

The [E record](../evidence/dev-147-c2-offline-preparation-2026-08-28.md#e-only-archive-result) preserves all 199 old module payloads and their dependency results, but early DWC3 availability can still change probing. The [T1 record](../evidence/dev-147-t1-private-image-2026-08-30.md) proves one TIPD replacement and seven unchanged indexes. The [PR582 pair](../evidence/dev-147-pr582-offline-2026-08-30.md) proves one AppleDRM replacement in each otherwise identical T1 archive.

Thus W → either paired image changes DWC3 availability, two indexes, TIPD and AppleDRM. W's older stock-image differences are inherited; do not count them again. Only PR582 control versus candidate is artifact-matched to the timeout hunk. There is no matched hardware result. A rebuilt control is not the packaged AppleDRM binary.

## First observed divergence

| Saved observation | Candidate | Working recovery |
|---|---|---|
| External DCP boots with no modes initially | Yes | Yes |
| TIPD initial cached state | HPD low at about 1.865 s; USB mux chosen; connected HPD skipped | Uninstrumented; no equivalent sender measurement |
| Connected notification / DPTX connect | No positive event in the saved capture | About 4.875 s |
| External modes published | None in the saved state | 14 modes at about 7.079 s |
| Final compositor output | External disconnected/disabled | LG35 native 3440×1440 / 99.982 Hz |

The expanded candidate capture reaches the explicit T1 cap at sequence 128, about 456.250 s. Before that cap it contains no cached HPD-high state or connected-HPD call. Later sender silence proves nothing. The controller event-read error at about 373.795 s is much later than the failed startup; it does not explain onset by timing alone.

The pinned [TIPD source/patch path](dev-147-hpd-startup-2026-08-29.md#exact-source-path) chooses USB only after excluding cached DP/TBT/USB4 connection states. The logged HPD is cached controller data, not an electrical measurement. This is a different signature from the previous LG27 incident that retained modes but rejected atomic commits.

## Source boundary and remaining hypotheses

Focused W/T1 source inspection preserves DATA_STATUS reads, cache writes, IRQ event gating, debounce, DP/HPD decoding and mux → role → connected-HPD order. The working source matches the retained T1 control source. T1 adds diagnostics/counters around those operations; existing semantic checks were reused, not rerun. There is no newly proven semantic defect in this boundary.

The packaged DWC3 glue registers the USB-role provider. TIPD requires that provider before initial DATA_STATUS acquisition and connection scheduling. Earlier DWC3 availability therefore has a concrete path to change sampling/worker timing. T1 logging while the worker holds its mutex can also change latency. Source proves these mechanisms exist, not that either caused the low cached state.

Both source versions refresh DATA_STATUS in IRQ handling only when the update-event bit is present; the worker consumes cached state. The unresolved discriminator is whether the controller never established DP/HPD, or Linux retained an earlier low value. Saved logs cannot distinguish those cases. The shared USB2 first-probe issue remains separate.

Counterevidence prevents absolute claims: [E already failed without T1 logging](dev-147-hpd-startup-2026-08-29.md#saved-cases), while [earlier T1 returned from connected-HPD calls twice](../evidence/dev-147-t1-boot-capture-2026-08-30.md#what-the-t1-trace-establishes) and later produced video. Do not claim that instrumentation always suppresses HPD or that early DWC3 always prevents video.

PR582 changes the later poweroff clear-swap timeout branch. Its atomic crash guard does not gate TIPD's earlier cached-state decision or the OOB connection callback. That guard alone does not explain this startup signature. Indirect effects and rebuild/timing differences are not ruled out.

## Next decision

Continue the separately authorized passive LG27 watch. No new live action is indispensable for this offline conclusion. If David later wants a causal test, the smallest available hardware discriminator is one separately approved boot of the already-staged PR582 control, with exact monitor/cable/port recorded and a reviewed W recovery boundary. It needs no new build. Failure there would show that the timeout hunk is not necessary for a paired-image startup failure; success would still need confirmation before attribution. Neither outcome alone validates timeout recovery.

Independent artifact and trace/source reviews agree within this scope. Original manifests, logs, images, failures and successes remain unchanged. The [main plan](../plans/dev-147-m2-displayport.md#minimum-remaining-path-living) owns authority; no control boot, new probe, source fix or upstream submission is released here.
