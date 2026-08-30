# DEV-147 — saved crash-flag capture exported, 2026-08-31

Scope: preserve and inspect the existing diagnostic, not take another measurement. David ran the reviewed read-only export after asking to advance through export, staging and attended testing.

## Result

The export receipt is exit 0. The agent independently read the user-owned archive: 40,960 bytes, mode 0600, SHA-256 `20f750cf71637cd6232f03261dcfc7dab1a028613b703e7cdbffbf9963d1289a`. This matches David's console output and the saved checksum.

Two fresh runs in the unchanged accepted v6 sandbox inspected the archive. `run-wy5b4btt` ran `bsdtar -tvf /inputs/capture`: one root directory and 14 regular JSON files, with no links or special files. After that member review, `run-e4t9pxar` streamed only the fixed JSON filenames with `bsdtar -xOf` into private sandbox output files and parsed each with `jq`. Both runs returned exit 0, unchanged inputs and no timeout. Both isolation probes passed. Output writes used fixed filenames in private sandbox storage, not destinations supplied by the archive.

Independent saved-result QA passed:

- Observation, event format, profile and sanitized trace agree on one external-connector observation with `crashed=1`, connector type 10, one profile hit and zero misses.
- All eight saved CPU statistics have zero overrun, commit-overrun and dropped-event counters. One CPU has the single recorded event.
- `result.json` records the owned trace stop, event disable, instance removal and definition deletion. Its capture and cleanup failure lists are empty.
- `cleanup.json` is the fallback guide, not the cleanup-success result.

The capture and its sandbox review files remain private. The [original observation](dev-147-crashflag-observed-2026-08-30.md) remains intact as the earlier, qualified user-validator checkpoint.

## Limits and preservation

This independent file review confirms the saved observation and recorded cleanup. It does not inspect current live tracing state, identify the crash-flag writer or explain the initial monitor dropout. The original raw trace was not retained: the archive contains sanitized text, its original byte count and a raw-byte digest. That digest cannot be independently recomputed from the sanitized text.

No diagnostic, driver operation, cable action, boot-file write or reboot ran during this review. The diagnostic and export handoffs are consumed; do not rerun either. Keep the original root bundle, exported archive and prior evidence. There is no live change to roll back.

The [main plan](../plans/dev-147-m2-displayport.md) owns the remaining staging and attended test steps. The existing paired PR #582 images need no rebuild. Their actual startup and timeout recovery remain untested.
