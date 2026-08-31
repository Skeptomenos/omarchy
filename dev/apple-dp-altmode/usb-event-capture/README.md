# USB trace capability snapshot

This helper reads fixed kernel trace metadata to check which event fields are available before designing a bounded USB diagnostic capture. It does not collect USB traffic or start tracing.

## Use

Run the offline tests from the repository root:

```bash
/usr/bin/timeout --kill-after=2s 20s /bin/bash dev/apple-dp-altmode/usb-event-capture/capabilities-test.sh
```

The live entrypoint is `capabilities.sh` with no arguments. It requires root. The DEV-147 owner must provide the reviewed, private one-shot invocation with a clean environment, a 20-second outer timeout and private output files. This README does not authorize that run. The helper does not invoke `sudo` or accept a replacement root path. It ignores stdin and has no configuration variables. `DEV147_TEST_ROOT` optionally selects the parent directory for retained test fixtures; it does not affect the helper.

The helper prints the kernel release from `uname -r`. It then reads these 15 fixed files under `/sys/kernel/tracing`:

| Group | Files or event formats |
|---|---|
| Trace metadata | `trace_clock`, `current_tracer`, `tracing_on` |
| `events/rpm` | `rpm_suspend`, `rpm_resume`, `rpm_status`, `rpm_return_int` |
| `events/xhci-hcd` | `xhci_urb_enqueue`, `xhci_urb_dequeue`, `xhci_urb_giveback`, `xhci_queue_trb`, `xhci_handle_transfer`, `xhci_handle_port_status` |
| `events/usbcore` | `usb_alloc_dev`, `usb_set_device_state` |

Each event path ends in `/format`. The helper emits `BEGIN`, `STATUS`, `BYTES`, the bounded file body and `END` for each path. `BYTES` excludes the framing newline. It keeps at most 16 KiB per body and reads one extra byte to detect truncation. The fixed inventory stays below 256 KiB of stdout. Each read has a one-second timeout; the required outer timeout bounds the whole invocation.

Exit `0` and `INVENTORY complete` mean that every fixed metadata read completed without truncation. They do not mean a capture ran or that the monitor passed a test. Exit `1` means an incomplete inventory; missing files, unsafe types, symlinks, unreadable files and failed reads remain explicit. Exit `64` refuses arguments. Exit `77` refuses non-root execution. Review stdout, stderr and the outer timeout exit together. Missing tracefs or events are findings, not instructions to mount tracefs or load a module.

## Boundaries

The data flow is fixed kernel metadata → bounded reads → stdout. The helper uses Bash and existing GNU coreutils. Base64 preserves exact byte counts in shell memory; the output contains the original bounded metadata text.

It does not read `trace`, `trace_pipe`, `available_events`, USB payloads, device attributes or port attributes. It does not write trace controls, clear buffers, create instances, change permissions, mount filesystems, load modules or rebuild an image. It rejects symlinks in every path component. Those checks assume the kernel paths remain trusted; they do not provide an atomic defense against a concurrent privileged path replacement. The snapshot is not atomic.

The event formats describe fields, not captured values. Their presence does not establish final USB completion status, correct device filtering, loss-free capture or a common usable clock. A header-only userspace export also does not prove that a kernel USB capture ring excludes payloads. This helper does not solve those collector design limits. No complete collector or automatic action follows this inventory. See the [saved hub comparison](../../../docs/research/dev-147-usb-hub-init-comparison-2026-08-31.md) for the diagnostic question and source limits.

## Test coverage

The tests execute the real entrypoint in an unprivileged Bubblewrap namespace. Only read-only `/usr` runtime files, the helper and a synthetic read-only `/sys` tree are visible. Host `/sys`, `/proc`, `/run`, `/home` and device nodes are absent. The tests cover the fixed allowlist, stdin isolation, argument and non-root refusal, missing files, symlink components, special files, unreadable files, exact and exceeded byte limits, total output size and Bash syntax. Fixtures remain private for review.

Bubblewrap or namespace failures stop the test. There is no host fallback. These fixtures do not reproduce tracefs I/O faults or timeouts, prove installed event availability, or exercise a live privileged run. No kernel, display, driver or boot test is part of this gate.

## Scoped control-result recorder

`capture.py` prepares a separate bounded recorder. Its public entrypoint is **unreleased** and exits before reading host state. It accepts no arguments, environment configuration or stdin instructions. Do not run it with sudo. A later reviewed private copy needs an exact boot binding, an attended window, separate coordination and David's manual invocation. No install, dependency or new image is required for preparation.

Run the complete offline gate from the repository root:

```bash
DEV147_TEST_ROOT=/home/david/o/.dev147-stage/usb-control-prep-20260831.Cr8fHxv7ec /usr/bin/timeout --kill-after=2s 60s /bin/bash dev/apple-dp-altmode/usb-event-capture/capture-test.sh
```

`DEV147_TEST_ROOT` applies only to the fixture gate. This outer timeout is for offline tests. A live capture must not use a forced timeout or SIGKILL. The gate uses a real Bubblewrap root with only the read-only Python runtime and source plus a private writable fixture directory. Host `/sys`, `/proc`, `/run`, `/home` and devices are absent. Namespace setup failure stops the gate without a host fallback.

The fixed data path is controller discovery → filtered function records → bounded private evidence → explicit cleanup. Discovery restricts `runtime_status_show` to the helper PID and reads one fixed DWC3 `runtime_status` attribute once. It saves exactly one verified record before stopping and disabling discovery. Three measurement events then select that numeric controller pointer: `usb_control_msg` return, `usb_suspend_both` entry and `usb_resume_both` entry.

The return probe preserves request, request type, value, index and size from entry arguments. It adds the signed API return and current USB device/bus identity at return. It does not capture data buffers, strings, stack arguments or payload bytes. PM events record function entry and the message flags, not successful suspension or resume. Pointer and bus/device number reuse can make joins ambiguous. A recorded `devnum=-1` deliberately produces INCOMPLETE with raw evidence retained; it is not assumed to be faulty data. Negative API results do not preserve partial transfer lengths. Calls outside this synchronous API remain unmeasured.

The future bound runner requires the exact recorded kernel, kernel build ID, loaded AppleDRM/TIPD build IDs and boot hash. It requires existing tracefs, global `nop`, no enabled global events and no existing instance. Conflicts cause refusal, not global state changes. It creates a unique private instance with `mono` clock and 64 KiB per CPU, with at most 16 CPU buffers. Before enabling any probe, it reads that instance's inherited `stacktrace` and `userstacktrace` options, requires both to be exactly disabled and retains their values; missing or unknown values cause refusal without changing the options. The control return probe uses maxactive 128. Global hit counts precede filtering and need not equal retained records. Nonzero or unknown miss/loss counters prevent a complete result. Zero counters cannot rule out numeric fetch faults, unfinished calls or untraced traffic.

Startup has a 15-second cooperative deadline. The attended window must retain at least 240 seconds before startup and arming. Measurement runs for 120 seconds from successful start, followed by bounded collection and cleanup. A 121-second cooperative limit covers the start action, the ARMED stderr flush and the wait, so slow output can shorten the usable window or produce INCOMPLETE. ARMED is the only phase that requests one reconnect. SIGINT, SIGTERM, SIGHUP and ordinary deadline expiry produce an incomplete result and owned cleanup. Cleanup defers further interruption signals and attempts each owned action independently. Python cannot bound an uninterruptible kernel syscall; power loss, kernel failure and SIGKILL can prevent cleanup.

Before any mutation, the runner saves exact owned recovery paths and probe definitions under a new root-private `/run/dev147-usb-*` directory. Setup mutations require durable attempted-action records. Critical cleanup records its attempt in memory, performs the control action first, then tries to save a completion record. Cleanup still attempts stop and disable if evidence writes fail, and reports that journal failure. It never truncates global probe controls, clears global buffers, removes unrelated instances or definitions, changes PM policy, reads `usb_mode`, issues USB requests, loads modules or writes boot files. Global clock/gate/definitions are compared after cleanup; unexpected drift is reported, not automatically restored.

Raw trace evidence contains local kernel addresses and task names. Keep it private. The recorder retains at most 8 MiB of measurement trace, 64 KiB of discovery trace and 256 KiB of other exported evidence, plus fixed framing. Phase JSON goes to stderr without raw pointers. Framed evidence goes to stdout for the attested inline handoff to save. Every frame includes a byte count and SHA-256. A save, export, readback or cleanup failure returns nonzero and retains the private evidence path. `CAPTURED` means the software checks passed, not that every call was observed, the monitor is reliable or a fix works.

The focused tests use typed standard-library dataclasses, unittest and real filesystem operations. They cover the real unreleased entrypoint, fixed fields, numeric filters, packed event formats, signed results, discovery PID, scope, loss, bounds, safe path handling, durable action ordering, cleanup selection and failures. This continues the no-install diagnostic exception: Pydantic, pytest, Ruff and strict type-check tools are not installed or claimed. Fixture success does not emulate tracefs, prove kernel acceptance, exercise the full live orchestration, validate recovery or demonstrate a hardware fix. Those checks remain separate in the [living investigation plan](../../../docs/plans/2026-08-31-dev147-usb-pm-recurrence.md).

### Delivery boundary

`launch.sh` is an unreleased template for an exact inline `sudo … bash -c` body, not a script to execute with sudo by its mutable user-owned pathname. The final manual command must contain the reviewed body with its fixed source path and helper SHA-256. The public template refuses before filesystem access.

The bound body creates a fresh root-owned `0700` directory under `/run` and reports its retained path on stderr. It copies at most 128 KiB with `cp --no-dereference`, a five-second copy timeout and a copy-only file-size limit. It refuses nonregular files and symlinks, sets the protected copy to root-owned `0600`, verifies that copy against the hardcoded digest, then executes only that protected copy with isolated Python. Nothing reads or executes the mutable source path after verification. The copy limit does not constrain the later recorder's evidence files. Copy/hash failures retain the stage and never launch the helper.

Run the delivery-only offline gate:

```bash
DEV147_TEST_ROOT=/home/david/o/.dev147-stage/usb-control-prep-20260831.Cr8fHxv7ec /usr/bin/timeout --kill-after=2s 60s /bin/bash dev/apple-dp-altmode/usb-event-capture/launch-test.sh
```

The gate runs the actual inline Bash body in a private Bubblewrap root. A harmless Python fixture proves verified-copy execution and a larger evidence write. Changed bytes, unreadable source, symlink, FIFO and oversized source fixtures must not execute. No sudo, live helper, device access or host `/run` write is part of this test.
