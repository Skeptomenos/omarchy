# DEV-147 — crash-flag manual release, 2026-08-30

Host/scope: omarchy-air; one user-run crash-flag observation.
Approval: David replied “yes, i confirm. proceed” to the readiness checklist.
Source checkpoint: `dad6a8c08b0e3dacf214f6cc8f2629147f9691d1`.

## Decision and evidence

David confirms the internal screen is normal, the LG 27 remains connected but blank, the lid is open, MagSafe is connected, battery exceeds 50%, monitor USB ports are empty and work is saved. These are user attestations, not new hardware measurements.

Release the exact previously reviewed private command for David to run once. It uses clean-environment `/usr/bin/python3.14 -I -S -B` and the unchanged boot-bound helper. The complete command and private digest remain in the separate local release record. The historical held draft remains unchanged.

Read-only `sha256sum` checks match all three approved helper/test digests. Independent handoff-integrity QA also passed: exact command, single-literal private delta and private file/directory modes match. No helper or test was executed during release. Reuse the [21-test result and independent reviews](dev-147-crashflag-preparation-2026-08-30.md); do not repeat them. The helper's own root preflight must verify the actual boot, kernel, modules, display state and path eligibility before instrumentation. A mismatch is a stop, not permission to change a guard.

## Operation and cleanup limit

The sole exception to the live holds is this one temporary, owned, PID-filtered kernel probe and one target open-close without reading display data. No reboot, reconnect, mode request, driver change, boot-file write or upstream submission is authorized.

Kernel instrumentation is not risk-free. Measurement has a 10-second cooperative limit and each of at most seven cleanup operations has a separate 2-second limit. SIGKILL, a system failure or an uninterruptible kernel call can prevent cleanup. The helper prints the exact private cleanup-metadata path before mutation. Do not clear global tracing or improvise recovery commands.

## Pending result

No user-run result, live cleanup proof, crash-flag observation or restored video is recorded here. David must paste all output, including PREPARED and final JSON, and stop. REFUSED, INCOMPLETE or an interrupted process consumes this release too: no automatic retry, reconnect or reboot follows. Keep any printed cleanup path for review.

The [main plan](../plans/dev-147-m2-displayport.md#minimum-remaining-path-living) owns the next decision. All prior evidence and all other holds remain unchanged.
