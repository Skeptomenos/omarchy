# DEV-147 rear-drive insertion capture — 2026-09-05

David ran rear-attach capture `trace-capture.9HlOlwF8`, exit 0. Physical image continuity, exact insertion timing, front-cable handling and enclosure model remain pending user confirmation. Boot remains `09746091-1f14-41ea-97b1-d3339f3a23af`.

Report SHA256: `6f176ccd16e1927c30dbfe336ef6743958f7d162fa4cfa9d048448ce64283c0e`. The 1187.62–1232.63 second capture retained 452/452 records, all 24 loss counters zero, empty stderr and successful instance removal.

Rear controller `0x38` reports USB host connection flags at 1191.082437 and 1191.184489 seconds. Rear xHCI starts at 1191.709029 on MMIO `0x382280000`, buses 3/4. No downstream rear USB or block device is present at inspection. Drive identity/protocol remain unknown; root-hub creation does not establish disk support.

Snapshot `rear-drive-inserted.9c21pyfu` confirms both displays still connected/enabled, four AFK service announcements and no collection issues. Front-controller trace has two empty IRQ events and no data-status change. No new front DP negotiation or teardown is established during this interval. Visible continuity still requires David's report.

## Front hub interruption

The kernel journal records front monitor hub disconnect at 1188.050144 seconds, port-enable failure at 1189.056033, an automatic USB port power cycle at 1189.282031, and successful hub re-enumeration at 1189.685027. LG controls return at 1190.070024. Thus the USB interval is not clean even though display state remains enabled.

The interruption starts roughly three seconds before the first recorded rear PD event at 1191.079337. The capture has no physical insertion marker, so this ordering cannot prove or disprove an electrical or mechanical interaction. A kernel suggestion about cable quality is not a diagnosis. Existing front USB failures also occurred with the rear empty.

Independent review verified capture integrity, snapshot manifest, controller attribution and the USB timeline. Pause the planned front reconnect until the user confirms the image result, front-cable handling and drive/enclosure model. Retain both cables in place while identifying whether the enclosure uses USB or Thunderbolt/USB4. No disk operations, role changes, resets or kernel edits were performed by the agent.

The rear-attach software's independent receipt is `/home/david/Work/dev147-fairydust-acceptance-20260905/checks/trace-rear-attach-independent.jk43cq__/receipt.json`, SHA256 `72ec4fbff1eaf9bd95dd0041bd1d812c12554624a0dfea1ba7aad11ac9f5e5bc`.
