# DEV-147 — crash-flag path correction, 2026-08-30

Scope: correct the diagnostic helper after the [pre-instrumentation refusal](dev-147-crashflag-preflight-refusal-2026-08-30.md). This is not a monitor-recovery result.

## Observed path and correction

David supplied metadata from the requested sudo namei command. The numeric DRM entry `/sys/kernel/debug/dri/2` is a symlink to `soc:display-subsystem`. The listed DP-1/ColorElements endpoint is a root-owned regular file. Tracefs kprobe_events and instances also exist with root ownership. This is user-supplied metadata, not an agent-run root inspection or a file-content read.

The numeric alias conflicts with the helper's deliberate nofollow path walk. The supplied target resolves to `/sys/kernel/debug/dri/soc:display-subsystem/DP-1/ColorElements`. This confirms a path defect; the old generic receipt does not identify which open failed first.

The correction changes two helper lines only:

- Use that fixed, device-named path instead of the numeric alias.
- Include the requested path and numeric errno in safe-open refusals.

No symlink following, path discovery, permission change, retry, probe, identity or cleanup change was added. Root preflight must still validate the direct path before instrumentation. The consumed operational-v1 and all earlier receipts remain unchanged.

## Focused executed checks

Both runs used the same reviewed private sandbox and runtime manifest. Each fresh isolation check passed. Inputs remained unchanged; neither run timed out. No host sysfs, procfs, runtime, home, boot or display-device mount was exposed.

- RED: `python3.14 -I -S -B /inputs/crashflag/test_crashflag.py FixedTargetPathTests` ran three new tests against the old helper. Exactly two assertions failed: the fixed target and actionable error receipt. The real-file nofollow fixture passed. Exit 1.
- GREEN: `python3.14 -I -S -B /inputs/crashflag/test_crashflag.py` ran all 24 tests against the correction. All passed in 2.004 seconds. Exit 0.

The original 21 test bodies are unchanged. New tests use ordinary temporary files and a numeric symlink fixture; they do not access debugfs. Independent saved-result QA verified the raw results, isolation, runtime/input hashes and retained test bodies. Independent containment review accepted the exact two-line source diff. No test was rerun for review.

Public helper SHA-256: `d319c9ef3e0753d997ac79b4398b50b6411dc27efab7683f740adf7b4b72137c`.
Test SHA-256: `8c4be42b148ff161d100a23acfe185df5fe3a925ac2a6dfdfe8f56b385479310`.

These checks establish local path behavior and retained software contracts. They do not prove live target access, probe operation, cleanup or hardware success. The existing no-install stdlib/unittest exception remains. No aggregate desktop suite, package install or live helper run occurred.

## Next manual boundary

A separate private operational-v2 candidate uses the corrected public bytes with only the same saved failed-boot binding. Its held handoff requires fresh attendance/readiness and explicit release for one user-run diagnostic. The old release remains consumed; this correction does not renew it.

No reboot is needed for the proposed observation. Keep the failed monitor setup unchanged. The helper still opens and closes ColorElements once without reading it, under one fixed PID-filtered probe. It cannot restore video. One valid crash flag would establish the current guard, not its writer or the initial link-loss cause. Zero remains inconclusive.

All cable/device, mode, driver/image, boot, recovery-rehearsal and upstream-submission holds remain. The [main plan](../plans/dev-147-m2-displayport.md#minimum-remaining-path-living) owns the release decision. Preserve the earlier [preparation](dev-147-crashflag-preparation-2026-08-30.md), [consumed manual release](dev-147-crashflag-manual-release-2026-08-30.md) and failure evidence as history.
