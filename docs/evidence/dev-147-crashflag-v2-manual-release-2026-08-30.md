# DEV-147 — corrected crash-flag manual release, 2026-08-30

Scope: one user-run observation on omarchy-air. Source checkpoint: `ff77a34afbf8360d56c93137368eb2adbbd949b7`.

## Approval and integrity

David confirmed the complete readiness checklist in response to the invitation to release the corrected command: connected but blank LG 27; healthy internal display and responsive system; lid open; MagSafe connected; full battery; empty monitor USB ports; saved work and no other active work. These are user attestations, not new measurements.

Release the exact reviewed private operational-v2 command once. Its clean environment, isolated Python invocation and same-boot binding are unchanged. Read-only sha256sum checks match the approved private helper, public helper and test digests. The private helper remains a regular, single-link 0600 file inside 0700 directories. Reuse the accepted [24-test result and independent reviews](dev-147-crashflag-path-correction-2026-08-30.md); no helper or test was executed during this release.

The exact command and digest remain in a new private release record. Keep the old consumed release, operational-v1, corrected held draft and offline evidence unchanged. Root preflight must still verify live identity and display/path eligibility. A refusal does not authorize a guard change or retry.

## One operation, then review

This clears only the hold for one temporary owned, PID-filtered kernel probe and one ColorElements open-close without a content read. It does not restore video. No reboot, cable/device action, mode request, driver/image change, boot-file write or upstream submission is released.

Kernel instrumentation is not risk-free. Measurement and cleanup deadlines remain cooperative. SIGKILL, power loss or an uninterruptible kernel call can prevent cleanup. Preserve the exact evidence/cleanup paths printed with PREPARED; never clear global tracing or improvise recovery.

Await all user-run output, including PREPARED and the final JSON. Every attempt consumes this release, including REFUSED or INCOMPLETE. No live observation, cleanup proof or hardware success exists at this checkpoint. The [main plan](../plans/dev-147-m2-displayport.md#minimum-remaining-path-living) owns the next decision.
