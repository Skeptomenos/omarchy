# DEV-147 battery-depletion addendum — 2026-08-29

This dated addendum preserves facts learned after the immutable [initial incident record](dev-147-battery-depletion-2026-08-29.md) was published. It does not rewrite that record. The [main plan](../plans/dev-147-m2-displayport.md) owns current authority.

## Physical-power clarification

David confirmed that he disconnected MagSafe before leaving the machine. The powered monitor and its front/lower USB-C cable were the only intended external power source. He found the monitor in standby after the incident. He reconnected MagSafe for the recovery boot.

This rules out a demonstrated loss of MagSafe charging and a simultaneous failure of two independent sources. It narrows the operational result: monitor-only USB-C input stopped supplying enough net power between the final fully charged sample and the first discharging sample. It does not identify why.

The retained data cannot distinguish among monitor standby or power-saving behavior, a monitor or cable interruption, a changed or inadequate USB-PD contract, controller firmware behavior, or an indirect timing interaction with the patched Type-C core. No retained per-source voltage, current, or PD-contract telemetry exists. The monitor being powered and later found in standby is consistent with a monitor-side power transition, but it does not prove one.

## Patch blast-radius addendum

Static comparison found no direct patch edit to PD-contract commands, PDO handling, source/sink selection, power-supply registration or properties, power-status reads, or TIPD suspend/resume.

The new DisplayPort hotplug callbacks run synchronously inside the serialized CD321x update worker while its lock is held. They can delay later Type-C status handling and `power_supply_changed` notification. The patched DTB also enables the external display complex and power domains, which can increase awake or suspend load. These are indirect risks. They are not proof that the patch stopped USB-C input.

The enabled Omarchy Stay Awake state kept the machine awake after monitor-only input became inadequate. The later `s2idle` entry followed UPower's critical-battery suspend request. It did not start the initial drain.

## Current correction and safety state

A later read-only check on the default stock-core boot showed 54% battery, `Charging`, about 41.0 W, MagSafe source online, aggregate AC online, and the monitor source online. This proves only that the recovery boot was charging with MagSafe present. It does not reproduce monitor-only power.

A separate read-only check showed that Omarchy Stay Awake was still enabled after reboot. This state persists. The initial incident record's recharge-only advice is therefore incomplete. Before any unattended normal use, keep MagSafe connected and restore normal idle with:

```bash
omarchy toggle idle allow-idle
omarchy toggle idle status
```

The first command must print `enabled`. The second must report `"enabled":false`, which means Stay Awake is off and normal idle is permitted. Until that visible check passes, do not leave the running machine unattended on battery.

The initial incident record also proposed a reviewed visible fallback for an unresponsive candidate. That fallback is not yet available. The existing macOS/Recovery guide begins only after macOS or Recovery Terminal is available. A physical hung-Linux-to-visible-stock-selection bridge must be written and independently reviewed before any candidate handoff can be released.

The direct operational conclusion is bounded: monitor-only charging was not reliable for this unattended candidate session, and persistent Stay Awake converted the loss of net input into full battery depletion. All candidate boots and T1 work remain on safety hold.
