# DEV-147 AFK reuse safety correction

**Date:** 2026-09-02
**Scope:** Offline Apple DRM design and lifecycle validation

## Correction

The earlier [AFK service-slot exhaustion record](dev-147-afk-service-exhaustion-2026-09-02.md) proposed disabled service entries as the reuse boundary. Independent QA disproved that hypothesis.

Endpoint `0x28` teardown can set `enabled=false` while a command remains in `cmd_map`. The driver keeps torn-down services routable because a teardown can arrive as a side effect of a command whose reply is still pending. Clearing a disabled record can therefore erase DMA pointers, a completion pointer, a command tag, and lock state before the late reply arrives.

The first offline candidate reproduced this unsafe erasure. It is rejected and must not be built or booted.

Independent review rejected a second candidate because command reservation and the AFK send were not one serialized operation. Teardown could enter after reservation and before send. A later timeout could then retain a command that firmware never received. The final candidate holds the service lock through admission, reservation, command-record setup, and the AFK send boundary. A failed send releases the bitmap before unlock.

## Corrected boundary

Reuse needs explicit opt-in and quiescence. A DisplayPort service record is eligible only after all these conditions are true:

- the endpoint owner requested retirement after teardown;
- `torndown` is true;
- the command bitmap is empty;
- no transient external user holds the service;
- the owner cookie is clear;
- no debugfs entry or scratch allocation exists.

The service stays enabled until that boundary. This preserves channel lookup for a late reply. The owner pointer is protected by a nonblocking lock and transient user count. No teardown wait is permitted because endpoint messages use one ordered AFK workqueue.

## Offline result

The exact-code lifecycle runner produced the required controls:

```text
CAPACITY: generation=8 member=0 slots=16
UNSAFE_REUSE: disabled pending slot erased
UNSAFE_SEND: post-teardown command stranded retirement
UNSAFE_RACE: teardown transitioned between reserve and send
```

The corrected candidate then passed ten two-service generations plus pending-command, late-reply, owner-release, stale-owner, debugfs, deferred-buffer, command-admission, serialized-send, send-failure, and all-live-capacity cases. Patch application, Python syntax, checkpatch, source-cleanliness, and fresh QA checks passed. At this checkpoint, final independent review and a real Apple DRM build remained required. The later [offline build record](dev-147-afk-reuse-build-2026-09-02.md) closes those two gates.

No accepted kernel source, live module, boot image, package, boot file, or running-system state changed during this correction.
