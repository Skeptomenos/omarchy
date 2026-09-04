# AFK service-slot reuse prototype

This folder holds an offline prototype for repeated Apple DCP DisplayPort service generations.

The accepted Asahi source at commit `e2e1930a9595bffafad92cec2b5504525efb9cd4` uses `num_channels` as a monotonic high-water mark. Endpoint `0x28` announces two services per external display generation. The ninth generation reaches the 16-entry limit even after the earlier DisplayPort services stop.

## Retirement contract

The candidate does not treat `enabled=false` as sufficient evidence for reuse. It adds an explicit opt-in to the two endpoint-`0x28` service operations. No other AFK service operation opts in.

An opted-in service becomes retired only after all these conditions are true:

- its endpoint owner requested retirement after teardown;
- `torndown` is true;
- no transient external user holds the service;
- its command bitmap is empty;
- its owner cookie is clear;
- no debugfs entry or scratch buffer exists.

The service stays enabled before that boundary. This lets a late command reply resolve the old channel. The allocator rechecks the complete contract under the service lock and clears the service record only after retirement.

The DCP AV owner uses a spinlock-protected, nonblocking get and put path. Teardown clears the matching owner pointer before it requests retirement. If a newer service owns the shared pointer, teardown leaves that pointer intact and clears only the old service's matching cookie. The last command release and the last transient-user release retry retirement. There is no teardown wait and no new workqueue dependency.

A caller can acquire the service immediately before teardown. Command admission therefore rechecks `enabled` and `torndown` under the service lock before it reserves a command slot. A post-teardown call returns `-ESHUTDOWN`, does not send a message, and leaves the command bitmap empty. The caller's final put can then retire the service.

The free-on-ack reply path copies DMA buffer addresses and sizes to local variables before it releases the command bitmap. It frees those local buffers after it unlocks the service. New service announcements run on the same ordered AFK endpoint workqueue, so an announcement cannot reuse that record before the reply handler completes those frees. The other command-release path is reached by the protected DCP AV caller while its transient user reference remains held. The opted-in DCP DP service has no external command caller in the accepted source.

## Offline test

Run:

```bash
python3 -I -S -B dev/apple-dp-altmode/afk-service-reuse/test_afk_service_reuse.py \
  --source-root /home/david/o/.dev147-stage/dev147-integration-source.SGVnPytGQN/linux
```

The runner performs these checks without modifying the accepted source tree:

- It verifies the exact source commit and clean state.
- It applies the patch to a temporary copy of all five affected files.
- It extracts the exact allocator, retirement, command, owner-init, owner-teardown, owner-get, and owner-put functions from that copy.
- It compiles and executes those exact functions in the C lifecycle harness.
- It proves the stock ninth-generation failure.
- It proves that the earlier disabled-slot candidate erases a pending command and is unsafe.
- It proves that the earlier command path admits a post-teardown command and strands retirement.
- It proves that releasing the service lock before send lets teardown enter between reservation and send.
- It verifies ten quiescent two-service generations.
- It verifies disabled-but-pending preservation and enabled torn-down late-reply lookup.
- It verifies owner-pointer clearing, delayed command and transient-user release, mismatched old-owner teardown, opt-in scope, debugfs exclusion, post-quiescence stale-state clearing, deferred buffer ownership, and safe all-live exhaustion.
- It verifies deterministic get, teardown, rejected send, empty command bitmap, final put, and retirement ordering.
- It verifies that teardown cannot enter between reservation and send, and that a failed send releases its command slot before unlock.
- It checks the patched reply-buffer ordering and the protected EDID get/copy/put sequence.
- It rejects new code comments in the patch.

Use `--red-only` to run all four failure probes. That command exits 1 after it observes:

```text
CAPACITY: generation=8 member=0 slots=16
UNSAFE_REUSE: disabled pending slot erased
UNSAFE_SEND: post-teardown command stranded retirement
UNSAFE_RACE: teardown transitioned between reserve and send
```

`build-appledrm.sh` builds the fresh control and candidate in the retained offline sandbox. `build-initramfs.py` replaces only `appledrm.ko` in the accepted image. The [offline build record](../../../docs/evidence/dev-147-afk-reuse-build-2026-09-02.md) owns the hashes and review result.

## Staging handoff

The first staging wrapper was rejected because it could execute mutable user-owned code as root. `stage-image-bootstrap.txt` replaces that design. Its literal command creates a fresh root-owned private transaction on `/boot`, writes the embedded publisher exclusively, verifies the copied bytes, and executes only that authenticated root-owned file in an empty environment. The publisher copies the candidate by file descriptor, rechecks host facts and protected paths, publishes without replacement, and changes the transaction marker atomically from `INCOMPLETE` to `COMPLETE`.

Do not execute `stage-image.py` or `stage-image-bootstrap.txt` by pathname. David pasted the reviewed literal once, and the authenticated publisher staged `/boot/initramfs-linux-asahi-m2-displayport-afk-reuse.img` as a separate non-default candidate. [Staging readiness](../../../docs/evidence/dev-147-afk-reuse-staging-readiness-2026-09-02.md) owns its hashes, tests, review, staging result, and provenance. The [living plan](../../../docs/plans/2026-09-01-dev147-video-completion.md) owns the next attended action.

This artifact is for contained local evaluation. It is not an upstream contribution. It does not authorize a live module, boot, cable, device, power, package, or recovery change. The attended non-default candidate boot and repeated-generation hardware gate remain mandatory.
