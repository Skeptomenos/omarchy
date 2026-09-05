# DEV-147 fresh-boot monitor baseline — 2026-09-05

David rebooted and confirms the external image returned during the requested front-port attachment. Kernel remains `7.1.12-dev147-fairydust1`; boot is now `09746091-1f14-41ea-97b1-d3339f3a23af`. Rear Type-C partner is absent.

Capture `/home/david/Work/dev147-fairydust-acceptance-20260905/trace-capture.xK2wmHWI` used attach mode during 44.60–89.60 boot seconds. It retained 1430/1430 records with all 24 loss counters zero and removed its trace instance. Report SHA256: `cee1b4d62311cb564ab179d8d51b08301c36a3d19de171745fa8ad2e2011dc21`.

Front-controller data status has USB host role, DP pin assignment C at 58.061845 seconds and HPD_LEVEL at 58.653455. External modesetting completes around 61.724 seconds. Snapshot `reboot-monitor-only.yy7866wv` confirms both displays connected/enabled, two external AFK service announcements and one external DCP boot. This is a first-attachment video PASS, not reconnect or overall release qualification.

## USB fault without the rear drive

Front USB hub address assignment fails with `-71` at 59.776047 and 62.144029 seconds. At inspection only USB root hubs remain; the monitor hub has not enumerated. Thus the rear drive is not required for this USB enumeration fault. That does not rule out a separate rear-drive contribution to later DP negotiation failure.

The snapshot exits 1 with 18 classified driver diagnostics and no collection issues: fifteen `dp-xbar` dependency deferrals (`-517`) before startup, one internal DCP PMU diagnostic, and external clock/PMU diagnostics during modesetting. These counts do not include the USB errors; the collector's selected driver filter does not capture every USB message. The kernel journal supplies the USB evidence above.

## Next control

Keep the rear port empty. Perform exactly one traced front reconnect with the same cable/orientation. This tests recovery in the new boot before rear-drive insertion. Stop on a failed image. If it succeeds, prepare a separate drive-insertion comparison while retaining this boot. Do not call the baseline clean or repeat a stress batch.

Independent review verified the trace hash/count/loss fields, snapshot manifest, error classification and absent monitor USB hub. No clear-swap timeout, DCP crash or AFK exhaustion was found in this boot review. One diagnostic reconnect is the next control; overall hardware qualification remains open.
