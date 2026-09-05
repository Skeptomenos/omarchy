# DEV-147 trace preflight — 2026-09-05

Status at preparation: software review PASS; manual runtime inventory pending. No tracing or privileged command was run by the agents. See the runtime addendum below for the later result.

The frozen candidate already includes `dcp:iomfb_push`, `dcp:dcp_send_msg`, `dcp:dcp_recv_msg` and `dcp:iomfb_callback` source events. Method pushes and mailbox ACK headers can distinguish clear-swap start and submit reply stages. Preserve the external controller context stack when interpreting nested calls. This does not directly establish host completion-cookie delivery. Normal `iomfb_swap_submit` and firmware `iomfb_swap_complete` are not substitutes for that evidence.

Function tracing is disabled in this build. Duplicate static callback symbols make simple symbol-name kprobes ambiguous. First inspect the running event formats, then prepare a bounded metadata capture. No diagnostic rebuild is justified yet.

The 43-line `trace-preflight.sh` reads exactly eight fixed tracefs paths inside a literal privileged block, after checking `7.1.12-dev147-fairydust1`. Result files are created by the normal user. It performs no tracing writes or cable action. `bash -n` returned 0; independent static review returned PASS.

- Launcher SHA256: `f91950dee986669412132e3a84c8ba0353888c80e0b64e696a066b2d2c84ef98`.
- Private source and review receipt: `/home/david/Work/dev147-fairydust-acceptance-20260905/diagnostic-design/clear-swap-trace-design.json`.
- Receipt SHA256: `fa1c52b821899c10dd7135c3f2315f284a54420913c2f024724a0dc9cfb173c1`.
- Existing snapshot, test and validation-script pins are unchanged.

Hardware qualification and fault diagnosis remain open. Further reconnect stress tests remain paused. The next dependency at preparation was David's password-assisted read-only inventory; its result determines the trace recorder design.

## Runtime inventory addendum — 2026-09-05

David ran the launcher successfully on `7.1.12-dev147-fairydust1`. Private result: `/home/david/Work/dev147-fairydust-acceptance-20260905/trace-preflight.13eipvPS`. `exit-status` is 0; `stderr.log` is empty. `report.txt` SHA256 is `733fd6b27d81f34ec410c0760452eabb194166740195818a20eb0ba0b619b2b2`. All six requested event formats exist. Available tracer is `nop`; clock choices include `mono`.

The DCP method event exposes device, method, context, offset and depth. Send/receive events expose device, endpoint and 64-bit message header. Callback events expose device, tag and name. These fields support an external-controller filter, endpoint 55 for IOMFB messages, and acknowledgement-stage reconstruction. The CD321x events expose no device/port field; any captured Type-C events remain unattributed without other evidence.
