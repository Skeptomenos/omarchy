# DEV-147 TIPD host-role request rejection

**Date:** 2026-09-04
**Host:** `omarchy-air`
**Boot ID:** `061c4b0f-2ca9-484a-b6f0-005d9a432d3b`
**Controller:** `0-003f` through `/sys/class/typec/port1`
**Provenance:** User-pasted terminal output; no retained filesystem receipt was reported.

## Scope and guards

The contained diagnostic used one standard Type-C sysfs role request on the current failed display state. The output identified the expected boot and controller. MagSafe was online, and the battery was at 100 percent. An isolated TIPD trace instance used a bounded buffer and time window. Its cleanup ran on every exit.

Before the request, `data_role` was `host [device]`, `DP-1` was disconnected, xHCI was absent, and the UDC count was zero.

## Result

The single write of `host` to `/sys/class/typec/port1/data_role` exited with status 1 and reported `Operation not permitted`. The post-state was identical: `data_role=host [device]`, `DP-1=disconnected`, xHCI absent, and UDC count zero.

The user-pasted output reported zero entries in the bounded TIPD trace. Cleanup succeeded, and the temporary isolated trace instance was absent afterward. No retained trace receipt exists, so the empty output does not independently prove that controller `0-003f` received no traceable event.

## Interpretation

The TIPD SWDF request was rejected with Linux `EPERM`. This is consistent with the driver's mapping of firmware `TASK_REJECTED` to `EPERM`. A simple live host-role request cannot recover this current failed state.

The result does not show why firmware rejected the request. It does not identify the cause of the generation-4 link failure. The ten-generation AFK reuse test remains blocked before its reuse boundary.

## Next gate

Observe one physical disconnect and reconnect with an isolated bounded TIPD trace. Do not issue another hardware sysfs write. Capture the role, xHCI, UDC, DP, HPD, physical display, and system state on both sides of that one cable cycle.
