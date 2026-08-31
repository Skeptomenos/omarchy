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
