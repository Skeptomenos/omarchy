# Record the identified W/LG27 startup

**Goal:** Establish what this one reported W startup actually supports, then name the smallest useful manual test.
**Mode:** light — read-only capture and documentation; no driver or system change.
**Branch:** `codex/dev-147-t1-image-offline`
**Linear:** DEV-147
**Started:** 2026-08-31

## Context

David reports selecting `initrd /boot/initramfs-linux-asahi-dpalt.img`, with both screens working and Linux responsive. W is the existing working experimental image, not a new build. This exact report resolves the filename question for this boot only.

The retained roadmap is `/home/david/o/.dev147-stage/tipd-image-code-20260829.TPjkwkTaMa/worktree/docs/plans/dev-147-m2-displayport.md`. This small continuation plan owns only the current capture and handoff. It does not restart completed builds, staging, recovery or tests. The new evidence is `/home/david/o/.dev147-stage/tipd-image-code-20260829.TPjkwkTaMa/worktree/docs/evidence/dev-147-w-lg27-startup-2026-08-31.md`.

## Approach

Capture ordinary identity, display, USB, power and current-boot kernel records once. Compare saved evidence, preserve earlier failures, and update the report without claiming a fix or general reliability. The successful USB enumeration removes the reason to prepare another speculative USB-startup image now.

## Execution Protocol

Use the light `self-correction-loop`. Run the saved-data gate below at commit and handoff, followed by independent verification. It reads saved files only. No live helper, driver operation, sysfs mutation, sudo, reboot or cable action is part of this slice. Never read partner `usb_mode`.

## Steps

- [x] Capture this identified startup.
  Goal: separate David's physical result from machine-side corroboration.
  Validation: one bounded capture at 11:16:31 CEST; all 12 capture exits are zero with empty stderr. Saved journal validation reports 1,151 unique, ordered records on the same new boot.
  Exit criteria: both native outputs, working module IDs, hub/controls and power state are recorded. Evidence: [startup record](../evidence/dev-147-w-lg27-startup-2026-08-31.md).
- [x] Reconcile the current checkpoint and manual boundary.
  Goal: report this case accurately without erasing earlier USB-startup failures.
  Validation: `validate-saved.sh` returns `VERDICT: PASS` with exit 0 and empty stderr in private `gate-1.*`. The final step checks semantics independently.
  Exit criteria: dated evidence, roadmap, diagnostic pointer and unsent replication report agree. No install, repeated test or upstream submission is claimed.
- [x] FINAL: independent verification.
  Goal: have a fresh-context verifier re-derive every completed claim.
  Validation: use the `self-correction-loop/references/verify-plan-prompt.md` protocol, rerun the gate and two targeted saved-data checks.
  Exit criteria: no unresolved DISPUTED claims. Record limits on independent physical observation and whole-image byte identity.
  Evidence: fresh-context verifier `w_startup_checkpoint_verifier` reran the full gate successfully, rejected both synthetic invalid inputs and independently confirmed USB-before-HPD timing. Both prior checkboxes are VERIFIED within the recorded limits; no disputed item remains.

## Validation

Run the complete scoped gate:

```bash
bash /home/david/o/.dev147-stage/w-lg27-startup-20260831.vzCuHy4DnT/validate-saved.sh
```

Expected: `PASS: saved W identity, displays, USB enumeration, power and 1151-record journal`, `PASS: checkpoint documents and diff hygiene`, then `VERDICT: PASS`.

The gate authenticates saved capture bytes, exact exits, boot brackets, module notes, physical-report fields, compositor modes, USB IDs, power, journal identity/order and document presence. It does not re-run hardware tests. Synthetic wrong-boot and duplicate-cursor inputs must fail the same journal validator. Build and runtime-smoke stages do not apply: no production source or artifact changed. Prior accepted build/test results remain historical evidence, not a new run.

## Progress (LIVING)

- 2026-08-31 09:16Z: one unprivileged capture saved. Both outputs, hub/controls and power are present.
- 2026-08-31: instructions refreshed. Existing feature worktree was clean. The complete historical roadmap was read; no old work was restarted.
- 2026-08-31: journal validator corrected to normalize the kernel's hyphenated boot ID to the journal's compact form. The original failed checks remain private. Corrected synthetic wrong-boot and duplicate-cursor checks each exit 5 with the specific reason; the original journal passes.
- 2026-08-31: complete scoped gate PASS after the documentation update. Independent verification is next. No old suite or hardware test was replayed.
- 2026-08-31: independent saved-data QA and semantic review PASS. Acquisition-provenance and diagnostic-name wording were corrected. DEV-147 now carries this checkpoint with its earlier description intact. This capture/documentation slice is complete; stop at David's mouse-insertion boundary.

## Discoveries (LIVING)

- USB devices `0bda:5411` and `043e:9a39` enumerate at 4.763 s and 5.146 s after boot. External HPD follows at 6.603 s. This is startup enumeration, not merely a later snapshot after a reconnect.
- The external clock, `load_ca_data` and PMU diagnostics recur 4/3/3 times. No clean-firmware claim follows.

## Decision Log (LIVING)

- 2026-08-31: accept the filename and visible pixels as David's testimony, corroborated by a new boot and matching loaded modules. Whole-image byte identity is not independently attested.
- 2026-08-31: accept the acquisition command, deadline and absence of agent runtime mutation as this task's execution record, not independently re-derived saved-data facts. The evidence states this boundary. No whole-system audit, fresh protected-image hash or repeat capture is required for this limited checkpoint.
- 2026-08-31: retain the large roadmap as history and overall safety scope. Use this small continuation plan for the refreshed method instead of requiring old work to pass new gates again.
- 2026-08-31: do not fix an unobserved failure. Prepare one mouse test after review; do not repeat the early-DWC3 experiment. Prior intermittent USB startup and source-order concerns remain open.

## Follow-ups

- One attended wired-mouse test through a monitor USB-A port. David must insert it and confirm movement/clicks. Keep USB-C, MagSafe, input selection and modes unchanged. No sudo or reboot is needed. Stop for loss of either display, input failure or system/power regression.
- Later, agree on a small repeated-startup/hotplug matrix. Suspend, cold-start, sustained monitor-only charging, alternate cables and full rollback stay separate.
- Timer-Off validation stays parked and the old watch stays paused. No new upstream submission or default-on installation is authorized.
