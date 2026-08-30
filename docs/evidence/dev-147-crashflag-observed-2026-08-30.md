# DEV-147 — external crash guard observed, 2026-08-30

Scope: result of the [released corrected one-shot diagnostic](dev-147-crashflag-v2-manual-release-2026-08-30.md), not a recovery test.

## User-run result

David supplied PREPARED followed by OBSERVED. The observation has `connector_type: 10` and `crashed: 1`. Both `failures` and `cleanup_failures` are empty. The exact process identifier, command and root-private evidence paths are retained in the private normalized receipt.

The operational-v2 SHA-256 still matches the released helper. Independent receipt QA accepts this as a qualified user-validator result: the external DCP crash guard is set at observation time, and the helper reports successful owned-object cleanup, including its absence checks. The root-private artifacts were not independently read or exported; the pasted output is not an independently observed process exit.

This confirms a concrete recovery blocker. The pinned [atomic check](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/gpu/drm/apple/dcp.c) rejects new modes when this guard is set. It does not identify the writer, prove which branch rejected earlier requests, explain the original spontaneous loss or establish restored video. The timeout writer remains a hypothesis.

## Preservation and cleanup

The one-use release is consumed. Do not rerun the probe. The helper reports no cleanup failure, so the receipt does not call for a cleanup command. Any later recovery must use verified exact-owned metadata, never global trace clearing.

The existing evidence bundle is under /run and is volatile. Preserve/export it before a planned reboot. No extra privileged evidence is indispensable before offline patch review. Its trace.json contains sanitized evidence and a raw-byte digest, not the original raw trace. A later export must copy existing artifacts, not trigger another measurement.

The [path correction and 24-test result](dev-147-crashflag-path-correction-2026-08-30.md), original refusal, release records and all prior failure/success evidence remain unchanged. No source, image, boot file, display setting or cable changed during this result review.

## Next decision

The confirmed guard justifies review of [PR #582](https://github.com/AsahiLinux/linux/pull/582) as a narrow prevention candidate. It does not clear the guard in this running boot. The [main plan](../plans/dev-147-m2-displayport.md#minimum-remaining-path-living) owns candidate scope, preserved evidence and the future attended test. No build, staging, boot, further live diagnostic or upstream submission is released by this receipt.
