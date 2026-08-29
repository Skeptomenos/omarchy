# DEV-147 battery-depletion incident evidence — 2026-08-29

- **Host / scope:** `omarchy-air`, MacBook Air M2, the unattended working-display candidate session and the next default boot
- **Approval:** User asked to stop prototype work, investigate the empty battery and charging loss, and give safe next actions
- **Repo state:** Public worktree head `262efb6ca`; this record was prepared after the incident, with all prototype implementation paused

This dated file owns the immutable incident evidence. The [main plan](../plans/dev-147-m2-displayport.md) owns current machine state and overall authority. The [diagnostic subplan](../plans/dev-147-usb-startup-diagnostic.md#battery-depletion-safety-hold-living) owns the technical restart gates.

## What happened

The candidate session started at 22:26 CEST with a full battery. The startup journal reports Omarchy's saved stay-awake state and a canceled idle cycle. The machine then remained awake without supervision.

UPower history gives this bounded power timeline:

| Time (CEST) | Recorded state |
|---|---|
| 22:26 | Battery at 100%, fully charged |
| 23:16:35 | Voltage history still reports fully charged |
| 23:27:25 | Voltage history reports discharging |
| 23:53:28 | Battery at 99%, discharging |
| 23:53–05:37 | Continuous discharge at about 6.7–8.0 W |
| 05:37:17 | Battery at 2%, discharging |
| 05:37:37 | `upowerd` requested suspend |
| 05:37:38 | Kernel entered `s2idle`; the retained journal has no later resume or orderly shutdown |

The prior boot used the out-of-tree working-display Type-C core. The external display had worked. No new T1 image had been built, staged, or selected. The unfinished T1 work had touched only unprivileged private worktree and sandbox files.

The next boot used the normal kernel command line and stock Type-C core. The external display was unavailable, as expected with that stock core and the still-patched DTB. The internal display remained usable.

## Result

The retained journals and UPower history prove that the machine lost net external charging between 23:16:35 and 23:27:25. It then drained under an ordinary load until the low-battery suspend request. The evidence supports absence of net charging, not exceptional power consumption.

The next boot was unclean:

- system and user journals reported an unclean shutdown and were replaced;
- filesystem checking found and cleared the dirty bit;
- no retained kernel panic precedes the journal end;
- the previous journal ends at the `s2idle` entry.

Read-only checks on the next boot found:

```text
kernel: 7.1.6-1-1-ARCH
cmdline: BOOT_IMAGE=/boot/vmlinuz-linux-asahi ...
tps6598x_core build ID: 73c3659d1653dd2508ae81147a5e5cd4c877a060
battery: Charging
macsmc-ac online: 1
MagSafe source 0-003a online: 1
monitor source 0-003f online: 1
```

The read-only evidence commands were:

```bash
journalctl --list-boots
journalctl -b -1 --since '2026-08-28 22:20:00' --until '2026-08-29 05:40:00'
busctl call org.freedesktop.UPower /org/freedesktop/UPower/devices/battery_macsmc_battery org.freedesktop.UPower.Device GetHistory suu charge 43200 60
busctl call org.freedesktop.UPower /org/freedesktop/UPower/devices/battery_macsmc_battery org.freedesktop.UPower.Device GetHistory suu rate 43200 60
busctl call org.freedesktop.UPower /org/freedesktop/UPower/devices/battery_macsmc_battery org.freedesktop.UPower.Device GetHistory suu voltage 43200 60
uname -r
cat /proc/cmdline
upower -i /org/freedesktop/UPower/devices/battery_macsmc_battery
cat /sys/class/power_supply/macsmc-ac/online
cat /sys/class/power_supply/tps6598x-source-psy-0-003a/online
cat /sys/class/power_supply/tps6598x-source-psy-0-003f/online
```

At the last incident check, the battery had risen to 22% at about 49.8 W. This proves that the current stock/default boot can charge while MagSafe and the monitor source both report online. It does not show how much either source supplied and does not reproduce the earlier physical setup.

No privileged command, module operation, boot-file write, reboot request, cable action, or live configuration change was made during the unfinished offline T1 work. The operational failure was leaving an experimental Type-C session awake and unattended without continuous power telemetry, an independently verified power guard, or a finite attended timeout.

## Rollback

The machine is already on the known-good power-recovery state for this incident: the default stock-core boot. Keep that boot selected. Keep MagSafe attached. Recharge to at least 80%, preferably full, and verify that it remains `Charging` or `Fully charged` before leaving the machine unattended for normal use. Do not select `initramfs-linux-asahi-dpalt.img`, `initramfs-linux-asahi-dpalt-usbearly1.img`, any USB diagnostic image, or a future T1 image while this hold is active.

No file rollback or deletion is required. Preserve every candidate image, backup, recovery bundle, journal extract, and private T1 artifact. A normal boot restores the stock Type-C core but does not restore the original DTB; full DTB rollback remains a separate reviewed gate.

## Open

The evidence does **not** establish which physical source was present when charging stopped. David must confirm whether MagSafe had been disconnected before the machine was left and whether the monitor stayed powered or entered standby. Current source state cannot reconstruct that history.

The evidence also does not prove that the working-display Type-C change caused the loss of net charging, that the TPS6598x driver broke USB-PD, or that `s2idle` caused the initial drain. The Type-C/PD blast radius and temporal association make this an unresolved safety risk.

All candidate boots and the offline T1 continuation remain on safety HOLD. Before any later candidate boot, require:

1. A 15-minute same-topology stock baseline immediately before the one-shot reboot, sampled every 60 seconds. Require MagSafe online, state `Charging` or `Fully charged`, and a non-decreasing battery percentage.
2. A candidate starting at 80% or more, preferably full. Keep MagSafe independently online and do not rely on monitor USB-C power.
3. David present, an external 10-minute timer, suspend disabled for the case, the internal panel usable, and recovery instructions on another device.
4. Read-only power telemetry immediately after userspace starts and every 30 seconds until the case ends.
5. Immediate abort on `Discharging`, MagSafe loss, a battery fall greater than 1%, or a missing sample. If Linux and the internal screen are responsive, use a normal reboot to the unchanged stock default. Otherwise stop input and follow the reviewed visible recovery fallback; do not type blind commands or depend on candidate Type-C or `s2idle`.
6. One-shot, non-default candidate selection. The eventual handoff must test its fail-safe before release and must not change the stock default.
7. Independent review that the candidate preserves stock Type-C/PD behavior, with focused regression coverage.

The first later live case must be classified as a power-safety diagnostic. It cannot simultaneously count as video, USB-hub, or reliability acceptance.
