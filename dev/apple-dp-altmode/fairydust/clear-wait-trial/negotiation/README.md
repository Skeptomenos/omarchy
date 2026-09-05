# Monitor power negotiation capture

This capture records one monitor-only recovery control on `7.1.12-dev147-clearwait100`. The cause of the failed negotiation remains unproven. It requires no kernel rebuild. Existing acceptance tools remain unchanged.

Run this command as the normal user in a terminal when the control is requested:

```bash
bash /home/david/Work/omarchy-dev147-fairydust-build/dev/apple-dp-altmode/fairydust/clear-wait-trial/negotiation/trace-capture.sh monitor-power
```

Enter the sudo password. Wait for `READY`. Keep all USB cables connected. Turn the LG27 off with its power button, wait five seconds, then turn it on once. Make no further changes until the 45-second capture ends. The power button may leave the USB-C link or PD controller powered. An unchanged trace does not establish that an electrical reset occurred.

The literal privileged payload uses one new trace instance. It requires `tps6598x_status` and `tps6598x_power_status` before `READY`. It retains external DCP events and optional CD321x data/IRQ events. TPS6598x events have no port identity in their format, so they must not be assigned to a port from the event name alone. DCP send/receive events retain the endpoint 55 filter and the `271c00000.dcp` controller filter.

Private output appears under `/home/david/Work/dev147-clear-wait-trial/negotiation/trace-capture.*`. Each run saves `report.txt`, `stderr.log`, and `exit-status`. The report includes boot ID, uptime boundaries, event configuration, per-CPU loss counters, trace data, and cleanup status. `CAPTURED` means the procedure ended. It does not establish visual recovery or a loss-free capture. Inspect the loss counters before interpreting an absent event.

Cleanup disables and removes only this run's instance on ordinary exit and handled signals. A cleanup error returns nonzero and retains its evidence. SIGKILL or power loss cannot run shell cleanup. The script writes private capture files and changes only its own tracing instance; it does not alter boot files or request device resets.

Run the software gate without sudo:

```bash
bash /home/david/Work/omarchy-dev147-fairydust-build/dev/apple-dp-altmode/fairydust/clear-wait-trial/negotiation/validate.sh
```

The gate runs the actual launcher and literal payload inside disposable namespaces. `uname`, sudo, tracefs files, the terminal, the timer, and instance removal use explicit fixtures. Tests cover the exact trial release, rejection of other releases and modes, both required events missing separately, filter failure, loss reporting, cleanup failure, and INT/TERM/HUP cleanup. Regular-file fixtures do not prove kernel filter parsing, real event delivery, or 45-second scheduling. No live trace runs in this gate.
