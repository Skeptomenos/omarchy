# DEV-147 targeted trace preparation — 2026-09-05

The runtime preflight succeeded. The six required formats and monotonic clock are present; see the [preflight addendum](dev-147-trace-preflight-2026-09-05.md). Hardware tracing remains pending. No agent ran sudo or enabled tracing.

The recorder uses a unique trace instance and a 4096 KiB buffer per CPU for 45 seconds. It selects external DCP `271c00000.dcp`, limits mailbox events to IOMFB endpoint 55, and retains method pushes and callbacks for context reconstruction. Available CD321x events are included without a port attribution claim. The launcher reports boot ID, time boundaries, filters and per-CPU loss counters before reading its stopped trace. It disables events and removes its own instance on ordinary exit or handled signals. No global trace settings are changed.

Kernel source confirms instance `current_tracer` and `nop` support despite stale documentation: `kernel/trace/trace.c` creates tracer files for the instance; `kernel/trace/trace_nop.c` permits instances. Actual filter writes remain a runtime check before READY. The user must perform one attended reconnect after that cue.

`bash -n` passed. Disposable bwrap controls execute the unchanged launcher and literal payload with a fake sudo, regular-file tracefs fixture and immediate sleep. They verify normal completion with retained nonzero loss counters, failure before READY, signal cleanup and isolation from a global sentinel. This does not test kernel filter semantics or real timing. Uncatchable termination cannot run shell cleanup.

The existing collector gate `checks/collector.xLubTzlg` returned 1 at its live snapshot step: a quiet journal window produced `SNAPSHOT_INCOMPLETE/journal_failed`. Its eight fixture controls, Ruff, formatting and strict typing passed. This is an unresolved collector limitation, not a trace-recorder failure or clean hardware baseline. The trace recorder does not invoke that collector.

Launcher SHA256: `a3b86e438af68b50c7336a3820e9aad39cee7a2b164d7c9c3a4e9bd1eb45df62`. Test SHA256: `6b47a6571b72812c438072423da5c21c89f323fc11dd9e7d9f9110f2616f0f6d`.

No cause-backed kernel fix or release acceptance is claimed. The next result must establish trace completeness, request/reply timing around the timeout, and the user's visible outcome before further action.

## Final software checks

Author, root and independent reviewer ran `python3 dev/apple-dp-altmode/fairydust/acceptance/test_trace_capture.py`: four tests passed, covering six paths. The added cleanup-failure control requires exit 1, an explicit failure report and a retained but disabled instance. Shell syntax and diff checks returned 0. Independent source review found no blocking defect.

Author receipt: `/home/david/Work/dev147-fairydust-acceptance-20260905/checks/collector.xLubTzlg/trace-qa.json`, SHA256 `6a0d517b55d07c6341ddbe868b4e904653e497b8c48cfb74529358706cfb9a41`. The separate collector gate failure remains open as described above. These checks qualify the capture handoff only; live tracing and hardware outcomes await David.
