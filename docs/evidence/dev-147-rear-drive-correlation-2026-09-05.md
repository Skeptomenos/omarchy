# DEV-147 rear-drive correlation audit — 2026-09-05

David identifies the rear accessory as an external hard drive. He confirms the monitor remained blank after the reset attempt, and that it first went blank only after the later monitor reconnect, not immediately when the drive was inserted. Drive/enclosure model, protocol and successful disk enumeration remain unconfirmed.

## Timeline in the retained boot

| Boot seconds | Observation |
|---:|---|
| 7268.964 | Rear xHCI starts at MMIO `0x382280000`, USB buses 3 and 4 |
| 7405.603 | Front monitor USB hub disconnects |
| 7405.995 | Front hub suspend returns `-32`, followed by disconnect |
| 7409.624 | Front xHCI is removed |
| 7413.313 | External DCP logs HPD removal during the attended reconnect |
| 7413.367 | DCP poweroff completes, with clear-swap replies inside the timeout |
| 7855.232 | Rear xHCI removal begins |
| 8419.799–8420.839 | Later front attachment still reports device role without DP/HPD |

The rear controller starts roughly 136.6 seconds before the front hub disconnect. The bounded kernel journal contains rear root-hub creation but no downstream USB-device, SCSI or UAS disk enumeration in that interval. This does not identify the drive protocol or prove a defective drive. No immediate DCP disconnect is logged at rear controller creation, consistent with David's clarification. Removing the drive did not restore the later front attachment.

## Source audit

In pinned `arch/arm64/boot/dts/apple/t8112-jxxx.dtsi`, rear controller `0x38` maps to DWC3_0 and ATC0; front `0x3f` maps to DWC3_1 and ATC1. Only the front connector holds the external DisplayPort reference. The ports share I2C0 and GPIO8 interrupt wiring.

TIPD instances have separate state, locks and delayed work. The shared interrupt invokes the handlers separately; an empty event returns without scheduling a connection update. Simultaneous empty IRQ records therefore do not establish port confusion. `drivers/phy/apple/atc.c` allocates PHY state and locks per platform instance. No direct rear-port overwrite of the front PHY, mux or DRM connector was identified in this bounded review. Independent review confirms shared one-shot interrupt handling and serialized I2C transfers, so a slow handler can delay service of the shared line. Shared firmware, power and event-ordering effects remain possible; this is not a proof of isolation across the full system.

The existing failure occurs before firmware reports DisplayPort selection. It is not evidence that the rear drive consumed the external display route or exhausted AFK slots. An interaction triggered by rear insertion remains plausible, but timing alone does not establish causation.

## Controlled next step

Recover a working front-monitor baseline with the rear port empty. If a Mac restart is needed, record it as recovery and a new boot, not a matched result. With a working monitor, first record one front reconnect with the rear empty. Only then introduce the same rear drive while tracing, hold the front cable fixed, and test one later front reconnect if the display remains healthy. Stop on the first failure. Identify the enclosure and whether it is USB or Thunderbolt/USB4 before interpreting absent storage enumeration. Never unplug a mounted drive as part of the test.

No kernel, PHY, role or boot configuration was changed during this audit. The [failed trace](dev-147-targeted-reconnect-failure-2026-09-05.md) and [later attach](dev-147-monitor-reset-attach-2026-09-05.md) own the raw evidence references.

Independent review also identified existing robustness gaps: TIPD clears interrupt bits before reading updated state, and some mux/role-switch return values are ignored. No matching read/PHY/mux failure was found in this boot. Repeated successful front data-status reads without DP/HPD do not support naming either gap as the drive-triggered cause. Both remain hypotheses, not changes to apply. Source audit and journal correlation are complete for the retained evidence; reproduction remains pending.
