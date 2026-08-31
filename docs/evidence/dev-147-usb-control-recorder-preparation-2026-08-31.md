# DEV-147 scoped USB recorder preparation — 2026-08-31

## Result

Offline preparation passes. The new recorder, tests and independent review are complete. No live trace, sudo, USB action, PM change, driver change, image build or reboot ran in this checkpoint. Capture and a hardware fix remain open in the [living plan](../plans/2026-08-31-dev147-usb-pm-recurrence.md).

The investigation concerns USB-hub/data reliability on the working display prototype. It does not establish a new picture failure. The prior root-only window contained no new reconnect; David's earlier confirmation referred to the already completed test. Keep that correction and the working W image intact.

## Measurement and source basis

One PID-restricted discovery probe observes a single read of the fixed DWC3 runtime-status attribute. Three later events use that raw controller pointer: synchronous `usb_control_msg` return, `usb_suspend_both` entry and `usb_resume_both` entry. The recorder saves setup scalars and signed return values, not USB payload, strings or stack arguments. It reads the USB bus's sysdev pointer value without dereferencing the sysdev allocation.

The saved kernel is `7.1.6-1-1-ARCH`, GNU build ID `ed32884ffd7e862fbffbd30b12082d5e8297c420`. Saved BTF and independently compiled header constants agree on 11 fields/sizes. The used offsets are `usb_device.devnum=0`, `usb_device.bus=80`, `usb_bus.sysdev=8`, and `usb_bus.busnum=16`. Vmlinux SHA-256 is `32b70e3a145454b430a0c9375a67ce93b30e0ee6afdefba590aac6f92ead4e15`. Both retained receipt manifests verify: 16 plus 5 entries, all OK. The old BTF reader returned 0 with 112 retained `BTF_KIND_DECL_TAG` warnings; this was not a warning-free run. Header compilation independently cross-checks the selected constants.

The [private source/layout review](/home/david/o/.dev147-stage/usb-control-prep-20260831.Cr8fHxv7ec/source-layout-review.md) owns exact commands, source links, input hashes and receipts. Pinned source is AsahiLinux/linux `e2e1930a9595bffafad92cec2b5504525efb9cd4`. [USB allocation and release](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/usb/core/usb.c) support the udev/bus lifetime argument. [USB PM code](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/usb/core/driver.c) defines entry-marker limits. [Probe implementation](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/kernel/trace/trace_kprobe.c) defines saved arguments, hit/miss accounting and return-time fetches. Two independent reviewers checked these interpretations.

Return timestamps are not precise hardware-completion times. The API can return errors before higher helpers replace them, but it does not cover all URBs or preserve partial length on error. PM entries are attempts, not successful transitions. Pointer and bus/device numbers are generation-local. `devnum=-1` deliberately produces INCOMPLETE with raw evidence retained, not a claim that the device state is invalid. PM-before-return alone cannot establish causation.

## Containment

The [public helper and instructions](../../dev/apple-dp-altmode/usb-event-capture/README.md#scoped-control-result-recorder) remain unreleased. A private copy may change only the exact boot hash and expiry. Preflight requires the matched running kernel and loaded display-module notes, existing idle tracefs, no other instance, exact formats and verified filters before enablement. The owned instance's inherited kernel/user stack options must both read exactly disabled; otherwise the helper refuses. It never changes global options to make a test pass.

The recorder uses one unique instance and four uniquely named temporary probe definitions. The measurement uses the mono clock, 64 KiB per CPU, at most 16 CPUs and 120 seconds. Startup, ARMED output, collection and cleanup have cooperative deadlines. Raw evidence is capped at 8 MiB plus 64 KiB discovery and 256 KiB metadata. Miss/loss uncertainty, truncation, scope failure or cleanup failure prevents a complete result. Zero counters do not prove all-call completeness.

Before mutation, root-private recovery metadata identifies every owned object. Setup actions require durable attempted records. Cleanup attempts stop/disable before optional journal writes and continues after individual failures. It verifies owned-object absence and compares global tracing state. It does not clear global buffers, delete unrelated objects, change PM, issue USB requests, read `usb_mode`, or touch drivers/boot files. SIGKILL, power loss and uninterruptible kernel calls can prevent cleanup; do not wrap the live helper in a forced timeout.

Phase JSON goes to stderr. Framed private evidence goes to stdout, with per-file lengths and hashes. The attested inline handoff retains both streams, helper and tee exit statuses, then hashes those files. No automatic retry or rearm exists. Kernel addresses and task names remain private and must not be posted upstream without a separate redaction review.

## Tests and independent review

Run from the feature worktree:

```bash
DEV147_TEST_ROOT=/home/david/o/.dev147-stage/usb-control-prep-20260831.Cr8fHxv7ec /usr/bin/timeout --kill-after=2s 60s /bin/bash dev/apple-dp-altmode/usb-event-capture/capture-test.sh
```

Independent QA: exit 0, 26 tests, `VERDICT: PASS`. Its [receipt](/home/david/o/.dev147-stage/usb-control-prep-20260831.Cr8fHxv7ec/dev147-usb-control.xI7Dy1Ix9p/tests.stderr) is separate from the author's run. Root independently reproduces the full gate, exit 0, in [another fixture](/home/david/o/.dev147-stage/usb-control-prep-20260831.Cr8fHxv7ec/dev147-usb-control.DOzzN5VcDK). Syntax and diff hygiene pass. Namespace failure has no host fallback; host sysfs, procfs, run, home and devices are absent.

Tests use real files and subprocesses. They cover the unreleased entrypoint, exact fields, packed formats, scope, PID discovery, limits, loss, safe paths, journal ordering, cleanup and failures. A full-pipe subprocess proves cooperative interruption of blocked stderr. Review found and corrected cleanup-journal ordering, the ARMED timer gap and inherited stack options before release. Failing intermediate fixtures remain private; no failed snapshot is called released.

| Reviewed file | SHA-256 |
|---|---|
| `capture.py` | `f4435259daab3c0cc4313c3d0d855f13bf02ed73d9c419d2ca42ea8a17d5a2b8` |
| `test_capture.py` | `0be0402c6bfb0e67cafcd40d2765fe304f11b69d636d85d30d532450f2494eab` |
| `capture-test.sh` | `a1e32eebe2d1873ae5f89502be5fb6d452b29c35fa925305e7d5efb062299d19` |

This continues the existing no-install diagnostic exception: standard-library dataclasses and unittest. No Pydantic, pytest, Ruff or strict type-check result is claimed. Full bound orchestration is not emulated. Actual probe acceptance, kernel behavior, hardware recovery and monitor reliability remain unverified until a manual run.

## First private binding — withdrawn without execution

Prepared directory: `/home/david/o/.dev147-stage/usb-control-prep-20260831.Cr8fHxv7ec`, mode 0700. Its `operational/capture.py` is mode 0600, SHA-256 `59aecf513d8bc59d17007cd3281db4f63a8feb58c3417ff892b56e535f9b19be`. Independent static review confirms exactly two changed constants. The bound boot hash is `bc182be641828b0a4ae4fa4c48b0a2655a824582ef28b3e006770f4e5a5fc8be`: SHA-256 of the boot-ID file including newline, not an image digest. Root's 16:16Z read matches the known loaded kernel, TIPD and AppleDRM notes. No protected image was reread.

The proposed 16:20–16:35 UTC window was withdrawn unused and unreleased. The coordinator found that hashing a user-writable source and then executing its pathname as root did not pin execution to the checked bytes. The original wrapper remains UNRELEASED; do not replace its marker or run it. The old private binding remains retained history, not a command to use. This finding concerns delivery, not the reviewed recorder logic.

## Protected-copy delivery and new private binding

The small public launcher template remains unreleased. Its final body must be pasted literally inside clean-environment sudo, not loaded from a mutable launcher file. It creates a root-owned 0700 directory under `/run`, copies the source with a five-second timeout and copy-only 128 KiB cap, rejects unsafe file types, enforces a root-owned 0600 copy and verifies its hardcoded SHA-256. Python executes only that protected copy. It never reads the mutable source again after verification. The root stage is retained on failure or completion. No install or persistent boot change is involved.

Independent delivery QA passes all seven groups, exit 0, with [its receipt directory](/home/david/o/.dev147-stage/usb-control-prep-20260831.Cr8fHxv7ec/dev147-usb-launch.aymh8Wnowe). Root independently passes the same gate in [a separate fixture](/home/david/o/.dev147-stage/usb-control-prep-20260831.Cr8fHxv7ec/dev147-usb-launch.NcJKCF7nY1). The harmless helper writes 256 KiB, proving that the copy limit does not leak into later evidence writes. Altered bytes, failed copies, symlinks, FIFO and oversized inputs do not execute. Capture source and its 26-test suite remain unchanged and were not replayed for this delivery-only repair.

Delivery template SHA-256: `432f1ec2daf341ad8caf255385d653df424a51d206968a1d871a6b0540599186`. Delivery test SHA-256: `3b7d364bd8da26e511693d3e703fa94c42201a4a0e2df1aecacb44b3b2cdc347`.

The new private helper is `/home/david/o/.dev147-stage/usb-control-prep-20260831.Cr8fHxv7ec/operational-v2/capture.py`, SHA-256 `bbaba1461502ac6ac1f50c3cf64fa791009134d1125992c167a5d5fb50508159`. Its only differences from the public helper are the same boot hash and expiry `1788194700`. Root's 16:27:53Z read verifies the boot hash unchanged. The proposed new window is 16:30–16:45 UTC, with startup and arming by 16:41 UTC. This is a new proposal, not an extension of the withdrawn window.

The exact inline body is retained at `/home/david/o/.dev147-stage/usb-control-prep-20260831.Cr8fHxv7ec/launch-inline-v2.sh`, SHA-256 `489a874bda060b1416a6d1e9124f1378e86ecbf71ecf3e887ba576b976910693`. The complete manual text is retained at `/home/david/o/.dev147-stage/usb-control-prep-20260831.Cr8fHxv7ec/manual-capture-v2.bash`, SHA-256 `3fc9e477d58ae8362f1ecac1cd517a9cd0c86c4483c74d2452f93d6d871b452a`. These are review records, not pathnames to execute. The user must paste the attested text; its quoted heredoc feeds the exact body into sudo's clean-environment Bash. Independent QA accepts that delivery as equivalent to the tested inline `bash -c` body.

Coordinator reservation and final text attestation are still required before release. Reservation, manual execution and actual cleanup are separate facts. Time expiry alone does not prove cleanup. A changed boot or expired release requires a newly coordinated binding, not a replay.

The manual procedure is one invocation of the attested inline block with MagSafe connected, lid open, responsive internal screen, the same LG27/cable in the lower-left port, and empty monitor USB ports. After ARMED, disconnect once, wait five seconds, reconnect once and wait for the terminal result. Do not reboot, attach a mouse or repeat the cable action. The next analytical step is to review the capture and cleanup, order observed errors against PM entries, then decide whether any driver fix is justified.
