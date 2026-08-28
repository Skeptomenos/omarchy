# DEV-147 — display recovery after the intended W restart

Date: 2026-08-28. Scope: the same M2 J413 front/lower left USB-C setup. Public checkpoint before this record: `8dd24ad48bec6ad1409be3684bc267b866f5a7a2`.

## Outcome and attribution

David reports restarting and seeing the external image again after the exact W handoff. A fresh boot has both native outputs. This is observed functional display recovery after intended W recovery, not independently proven W artifact startup: the user did not repeat the filename in this report, and W/E share loaded module IDs. The [confirmed E failure](dev-147-c4-selection-confirmation-2026-08-28.md) remains unchanged; neither this recovery nor the earlier failure proves a cause.

| Read-only check | Result and limit |
|---|---|
| Displays | `eDP-1` 2560×1664 / 60 Hz and `DP-1` 3440×1440 / 99.982 Hz, with adjacent desktop geometry and `mirrorOf: none`. |
| USB | Root hubs only. Monitor hub `0bda:5411` and LG controls `043e:9a39` remain absent; USB/full Gate 4b stays HOLD. |
| Power/platform | Battery 100%, Full; AC and both PD sources online. Taint 4100. Kernel `7.1.6-1-1-ARCH` and package pins unchanged. This is not a USB-C-only charging test. |
| Identity/integrity | Packaged DWC3/ATC and working patched TIPD IDs match the shared W/E identities. All 37 readable protected/proof hashes match; four root-private file bytes retain qualified C3 user-validator provenance. |

## Bounded kernel evidence

Eighteen pages contain 1,122 unique, ordered records from the fresh boot, spanning 20:26:16.914–20:30:38.809 UTC. Per-record cursors and the terminal-record reread agree. The final display cursor differs at the time-window boundary; scan-end cursor equality is not claimed.

Six crossbar deferrals recover into binding. External DCP reports connected with 14 modes at 6.759 seconds and native mode at 6.791 seconds. These startup transitions are not an intentional mode test. Known external EDT/CAHandler/PMU diagnostics occur 4/3/3 times; internal CAHandler/PMU occur once each. No kernel WARNING trace or DART fault was observed in this window. The log reports 444 suppressed audit callbacks. This is not a clean-firmware or unrestricted completeness result. Zero diagnostic markers are expected for the uninstrumented recovery path; they establish no call order or image identity.

## Separate login-focus observation

David also reports a login-screen focus issue. Read-only records show SDDM `0.21.0-7` in a separate Hyprland greeter session. The same greeter process adds the internal view at 4.837 seconds and the adjacent external view at 7.045 seconds, about 2.208 seconds later. This shows view arrival, not a proven primary-monitor switch.

The installed theme and greeter configuration match the public [Main.qml](../../default/sddm/omarchy/Main.qml) and [hyprland.lua](../../default/sddm/hyprland.lua) by SHA-256. The theme has one password `TextInput` per view, dots tied to that field, `focus: true`, and `forceActiveFocus()` at completion (lines 75, 85, 100, and 116). The greeter configuration has no monitor/focus policy. [SDDM v0.21.0](https://github.com/sddm/sddm/blob/v0.21.0/src/greeter/GreeterApp.cpp#L132-L270) creates per-screen views, handles screen additions, and requests activation for its primary screen. These source paths suggest a possible hotplug/focus issue; the component that moved focus is unproven, and no authentication bug was reproduced.

## Boundary

The [main plan](../plans/dev-147-m2-displayport.md#current-state--display-recovery-observed-living) consumes the W handoff. No new reboot, reconnect, sudo command, USB-device test, mode change, suspend, module/helper operation, or greeter test is authorized. A separate greeter-only fix and disposable tests need approval; no fix was made here.

Preserve images, backups, all prior dated evidence, and raw records privately. Normal boot remains unchanged, not full DTB rollback; Mac restore execution remains untested. This is not reliability, causality, permanent integration, or upstream-submission evidence. Private boot IDs, host paths, and raw logs are excluded.
