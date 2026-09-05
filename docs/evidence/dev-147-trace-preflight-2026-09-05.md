# DEV-147 trace preflight — 2026-09-05

Status: software review PASS; manual runtime inventory pending. No tracing or privileged command was run by the agents.

The frozen candidate already includes `dcp:iomfb_push`, `dcp:dcp_send_msg`, `dcp:dcp_recv_msg` and `dcp:iomfb_callback` source events. Method pushes and mailbox ACK headers can distinguish clear-swap start and submit reply stages. Preserve the external controller context stack when interpreting nested calls. This does not directly establish host completion-cookie delivery. Normal `iomfb_swap_submit` and firmware `iomfb_swap_complete` are not substitutes for that evidence.

Function tracing is disabled in this build. Duplicate static callback symbols make simple symbol-name kprobes ambiguous. First inspect the running event formats, then prepare a bounded metadata capture. No diagnostic rebuild is justified yet.

The 43-line `trace-preflight.sh` reads exactly eight fixed tracefs paths inside a literal privileged block, after checking `7.1.12-dev147-fairydust1`. Result files are created by the normal user. It performs no tracing writes or cable action. `bash -n` returned 0; independent static review returned PASS.

- Launcher SHA256: `f91950dee986669412132e3a84c8ba0353888c80e0b64e696a066b2d2c84ef98`.
- Private source and review receipt: `/home/david/Work/dev147-fairydust-acceptance-20260905/diagnostic-design/clear-swap-trace-design.json`.
- Receipt SHA256: `fa1c52b821899c10dd7135c3f2315f284a54420913c2f024724a0dc9cfb173c1`.
- Existing snapshot, test and validation-script pins are unchanged.

Hardware qualification and fault diagnosis remain open. Further reconnect stress tests remain paused. The next dependency is David's password-assisted read-only inventory; its result determines the trace recorder design.
