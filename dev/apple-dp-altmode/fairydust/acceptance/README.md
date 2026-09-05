# Capture front-port acceptance evidence

The [living stability plan](../../../../docs/plans/2026-09-05-dev147-front-port-stability.md) owns test outcomes and release readiness. This tool only captures evidence. It does not move cables, change system configuration, enable tracing or decide that hardware passed.

Run as the normal user on the frozen candidate:

```bash
python3 /home/david/Work/omarchy-dev147-fairydust-build/dev/apple-dp-altmode/fairydust/acceptance/snapshot.py front-connected
```

Each run prints a unique directory under `/home/david/Work/dev147-fairydust-acceptance-20260905`. It contains `snapshot.json`, categorized `journal.jsonl` and `SHA256SUMS`. Files are made read-only; their owner can still change permissions, so this is not tamper-proof storage.

The snapshot captures the release, boot ID, monotonic sampling interval, DRM connector state, explicitly allowed Type-C fields, and active/recovery/guard hashes. It never reads Type-C `usb_mode`. Journal output contains selected event fields and classifications instead of raw messages. Recent diagnostics cover selected drivers over fifteen minutes; service and DCP-boot records cover the current boot. Reaching a record limit makes the capture incomplete. This is not a full-system crash scan or full-boot error inventory; those remain separate acceptance checks.

| Status | Meaning |
|---|---|
| `SNAPSHOT_CAPTURED` | Required evidence was collected, with no classified errors in the sampled records |
| `SNAPSHOT_CAPTURED_WITH_ERRORS` | Evidence was collected and includes classified error records |
| `SNAPSHOT_INCOMPLETE` | Required evidence is missing or does not match the expected candidate |

Exit status is 0 only for `SNAPSHOT_CAPTURED`; both other capture states exit 1 and retain their evidence. Usage errors exit 2. None of these statuses means endurance or visual success. Existing firmware warnings must remain visible and be assessed separately from host driver errors.

Record the physical port, cable orientation, approximate insertion time and visible outcome separately. The checkpoint summary counts only external controller `271c00000.dcp`, endpoint `0x28`; categorized records retain other controller identities separately. Endpoint numbers in JSON are integers, so `0x28` is 40. Pair counts are arithmetic over announcement records, not proof of logical display generations or occupied host service slots. Do not count duplicate connect calls as extra successful reconnects.

Validate the collector software with:

```bash
bash /home/david/Work/omarchy-dev147-fairydust-build/dev/apple-dp-altmode/fairydust/acceptance/validate.sh
```

The gate combines formatting, lint, strict typing, namespace entry-point controls and live read-only capture checks. Fixtures replace DRM/Type-C trees and command outputs; protected pin files and boot ID remain live inputs. A software gate PASS can include a live snapshot with errors. It verifies honest capture, not a clean boot or stable display.
