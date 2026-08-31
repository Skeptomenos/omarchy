# USB trace metadata inventory — 2026-08-31

Result: the single protected metadata read completed. All 15 allowed files were read in full. This is not a USB capture, monitor test or collector acceptance.

## Saved evidence

The consumed private wrapper is `read-capabilities-once.sh` in `/home/david/o/.dev147-stage/usb-trace-prep-20260831.8VZum1d97G`. Its `manual-capabilities` directory now contains the saved result. Do not rerun it or replace that directory. The pasted command alone adds no new physical-monitor report.

| Check | Result |
|---|---|
| `sha256sum -c capture.sha256` | 3/3 OK |
| `stdout.txt` | 12,940 bytes; SHA-256 `60dc278db3f407f17543b18a2e0c21a46a3207c37ff87a3f9fb8c5e6911236da` |
| `stderr.txt` / `exit.txt` | Empty stderr; exit exactly `0\n` |
| Framing | Exact 15-path allowlist/order; 15 complete blocks; 10,734 body bytes; terminal `INVENTORY complete`; no trailing data |
| Kernel / format | `7.1.6-1-1-ARCH` / `dev147-trace-capabilities-v1` |

Independent saved-data QA reproduced the hashes, exact body lengths, framing and all 12 distinct event schemas. RPM, xHCI and usbcore field names/types match the retained sources at `e2e1930a9595bffafad92cec2b5504525efb9cd4`. No source or helper changed, so the prior fixture suite was not replayed.

## What is available, and what is still missing

- `trace_clock` selects `[local]`; `mono` is available. `current_tracer` is `nop`. The existing global `tracing_on` value is `1`. These fields do not identify enabled events or prove a capture ran. The helper changed none of them and read no trace buffers.
- Four RPM formats expose named suspend/resume, status and return records. Six xHCI formats expose URB, TRB and port records. Two usbcore formats describe allocation and device state.
- The URB schema has a signed `status` field, although its print format omits it. Its device name is not controller identity. It has no control-request setup fields. Finding the field does not repair the [pre-final-status placement](../research/dev-147-usb-hub-init-comparison-2026-08-31.md#addendum--collector-feasibility-2026-08-31).
- TRB fields still lack a safe setup-to-URB/controller join. usbcore device-state events do not supply transfer results. Metadata availability therefore does not make either proposed collector sufficient.

## Next measurement decision

Continue offline design at `usb_control_msg`, before its callers remap errors. Its entry exposes request/type/value/index/requested size. Its signed return preserves the synchronous API error or successful actual length. The saved descriptor, SET_INTERFACE and standard GET_STATUS paths use this function. See the pinned [control wrapper and wait path](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/usb/core/message.c#L50).

This is a narrower question than collecting every URB. A negative return can include allocation, submission or timeout failure; it is not uniquely HCD completion status and does not retain partial actual length. Async/direct URB paths bypass the wrapper. Entry-to-return is an API interval, not a transfer-completion timestamp; scheduler delay and a possible 200 ms quirk delay intervene. PM inside that interval leaves ordering unresolved.

Independent source review supports offline design only. Before a collector can be released, verify matched arm64 argument/return handling and device/controller identity, invocation correlation, probe misses and buffer loss, a common clock, bounds and cleanup. Return probes can retain entry scalar arguments, but pointer dereferences at return are not entry snapshots. Do not guess structure offsets, enable all-bus capture or publish a runnable probe on this evidence alone.

No agent reran the wrapper, enabled tracing, loaded modules, changed PM, built/staged an image, rebooted or requested a cable action in this review. The old watch remains paused. The [PM plan](../plans/2026-08-31-dev147-usb-pm-recurrence.md) owns the remaining design and measurement steps.
