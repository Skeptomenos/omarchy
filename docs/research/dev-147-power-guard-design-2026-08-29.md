# DEV-147 power-guard design — 2026-08-29

Status: reviewed design only. No guard is implemented or approved for live use. This document does not release the battery-depletion safety hold or authorize a candidate boot.

The immutable [incident record](../evidence/dev-147-battery-depletion-2026-08-29.md) owns the initial observed facts. Its [later addendum](../evidence/dev-147-battery-depletion-addendum-2026-08-29.md) owns the physical-power clarification and current safety corrections. The [main plan](../plans/dev-147-m2-displayport.md) owns current authority. This file defines the minimum fail-closed contract for a future power-safety case.

## Fixed telemetry

Use only these literal sysfs inputs:

- `/sys/class/power_supply/tps6598x-source-psy-0-003a/online`
- `/sys/class/power_supply/macsmc-ac/online`
- `/sys/class/power_supply/macsmc-ac/input_power_limit`
- `/sys/class/power_supply/macsmc-battery/status`
- `/sys/class/power_supply/macsmc-battery/capacity`
- `/sys/class/power_supply/macsmc-battery/power_now`
- `/sys/class/power_supply/macsmc-battery/energy_now`

Cross-check the fixed UPower battery object at `/org/freedesktop/UPower/devices/battery_macsmc_battery`. Require `NativePath=macsmc-battery`, battery type, present state, state, percentage, energy, energy rate, warning level, and a fresh update time.

Do not enumerate power supplies. Do not use the UPower line-power object as the freshness source; its update time was stale in this investigation. Do not call UPower `Refresh`, `GetAll`, or live `GetHistory`. Never read a Type-C partner's `usb_mode`.

## Accepted sample

Each accepted sample must meet all conditions:

- MagSafe source `0-003a` is online.
- Aggregate `macsmc-ac` is online.
- The input-power limit is a positive integer.
- Sysfs status is `Charging` or `Full`.
- UPower state agrees and is charging or fully charged.
- The battery is present.
- Sysfs and UPower percentages are valid and differ by no more than one point.
- UPower data is no more than 120 seconds old and is not from the future.
- `power_now` is positive while charging. Zero is permitted only while full.
- Energy and rate values are finite and non-negative.

Treat `input_power_limit`, `power_now`, and UPower energy rate as reported limits or magnitudes. They do not prove delivered electrical power or direction. State and status control the charging-direction decision.

Bracket each UPower read with two reads of the fixed sysfs set. Require stable source-online, input-limit, status, and capacity values. Require the UPower update time to remain stable across the property read. Permit one bounded retry only for a safe coherence change. Any unsafe value, second incoherent attempt, read failure, malformed value, stale value, or timeout is a missing sample and fails closed.

Each field read has a one-second deadline. A complete attempt has a five-second deadline. Use fixed monotonic sampling deadlines and bounded, strict parsing.

## Stock baseline

Use the unchanged stock/default boot with the exact intended topology:

- MagSafe connected.
- Monitor connected to the front/lower USB-C port.
- Lid open.
- Monitor USB ports empty.
- No cable, monitor-power, input, kernel, package, or setup change during the window.

Collect 16 accepted samples at `t=0,60,...,900` seconds. Both percentage sources must be non-decreasing. The final percentage must be at least 80%. Save the minimum observed input-power limit as the baseline floor.

The baseline expires 120 seconds after its final sample or immediately after any setup change. A missing or failed sample means `REFUSE_CANDIDATE`. Remain on stock and do not reboot for the test.

## Candidate window

The candidate remains a one-shot selection. The stock boot remains the automatic default. Start an independent timer when the user selects the candidate.

- Finish the first accepted sample within 120 seconds.
- Require at least 80% battery at the first sample.
- Sample every 30 seconds.
- Require the input-power limit to remain at or above the stock-baseline floor.
- Do not permit either percentage to fall by more than one point below the baseline final value or candidate first value.
- Start a normal stock reboot at timer `T+9:00`.
- Require visible reboot progress by `T+9:30`.
- Treat `T+10:00` as the hard deadline.

A completed observation needs at least 15 accepted candidate samples across at least seven minutes. A shorter safe run is inconclusive. An all-green run means only `SAFE_POWER_WINDOW_OBSERVED`. It is not video, USB, charging-reliability, or causal acceptance.

Abort immediately on source loss, a zero or lower input-power limit, an unaccepted state, a fall greater than one point, stale or contradictory data, a late or missing sample, collector failure, lost visible heartbeat, or timer expiry.

The collector must remain read-only. It must never reboot, suspend, change power policy, touch a device, write sysfs, or change boot state.

## Recovery branches

If Linux and the internal screen remain responsive, stop collection, keep MagSafe attached, and use a visible normal reboot to the unchanged stock default. Do not wait for more evidence.

If Linux or the internal screen is not responsive, do not type blind commands and do not rely on `s2idle`. Keep MagSafe attached. Use a separately reviewed recovery card from another device.

The existing macOS/Recovery restore guide begins after macOS or Recovery Terminal is available. The [visible recovery card](../plans/dev-147-visible-recovery-card.md) now defines the physical hung-Linux power-off and direct Recovery bridge and has passed offline documentation QA and safety review. It is not an available fallback yet. The exact committed card and pinned guide must be available on a separate device, and normal-shutdown rehearsals must verify stock selection and non-mutating Recovery Terminal/guide access before any candidate handoff can pass.

After stock recovery, collect three accepted samples across 60 seconds and separately verify stock image identity.

## Offline acceptance before implementation

A future implementation must use fake files and a fake D-Bus adapter. Tests must cover every state and status, mismatched source states, monitor-online with MagSafe offline, malformed and lower input limits, stale/future/changing time, disagreement and incoherence, read timeouts and malformed output, every missing/late cadence case, percentage decline, all external-timer boundaries, collector failure, partial-receipt retention, responsive/unresponsive routing, recovery sampling, receipt tampering, and static absence of forbidden reads, writes, enumeration, reboot, suspend, or device commands.

No live power or boot action belongs to offline guard QA.

## Limits

- MagSafe `online` comes from cached TIPD status and can become stale if processing fails.
- Aggregate AC does not identify the actual source.
- Input-power limit is not delivered power.
- UPower and sysfs overlap at the kernel layer. They are cross-checks, not independent instruments.
- Battery percentage is coarse. A ten-minute window cannot prove unattended reliability.
- Software cannot prove user presence, physical cable identity, timer use, or monitor settings.

For these reasons, no future candidate session may be unattended or rely on monitor-only charging even after this guard passes.
