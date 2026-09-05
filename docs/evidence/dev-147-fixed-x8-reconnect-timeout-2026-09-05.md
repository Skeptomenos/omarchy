# DEV-147 fixed-X8 reconnect and late clear-swap replies — 2026-09-05

The requested control left the X8 connected while reconnecting the front monitor. User-visible image confirmation remains pending. Boot is `09746091-1f14-41ea-97b1-d3339f3a23af`.

Capture `trace-capture.6sA5Hx5x` spans 2987.67–3032.68 seconds and retains 1326/1326 records with all 24 loss counters zero, exit 0 and clean instance removal. Report SHA256: `f8021d19c7399143848fbf0fdc41c7cde5eab94f451996f4438974b80c69077a`.

## Captured timeout

| Stage | Boot seconds | Elapsed |
|---|---:|---:|
| Clear swap start push | 2990.599285 | — |
| Start ACK | 2990.647496 | 48.211 ms |
| Clear swap submit push | 2990.647501 | — |
| Submit ACK | 2990.651034 | 3.533 ms |
| Host timeout warning | 2990.652012 | — |

The request-to-final-ACK interval is 51.749 ms, beyond the nominal 50 ms completion wait. D576 hotplug handling and its host ACK occur between 2990.647529 and 2990.651010, within the submit interval. No abort-swaps, last-client-close or set-power-state method follows. This matches the timeout return in the current PR582-derived path. The callback cookie and exact wait-expiry instant are not directly traced, so do not infer their ordering solely from the warning print timestamp.

This establishes late protocol replies rather than a permanently missing start/submit acknowledgement in this attempt. It does not establish that the X8 caused the delay or that increasing the timeout alone is a release-quality fix.

## Reconnection and SSD continuity

DP pin C returns at 2999.632402 and HPD at 2999.989089. Snapshot `front-reconnect-x8-fixed.6otpi76m` verifies both displays enabled. AFK channels 13/15 appear. The X8 remains device `4-1`, device number 2, speed 10000 Mb/s, and `/dev/sda`; no rear reset, disconnect, re-enumeration or storage error is recorded in the bounded interval. Rear trace IRQ events are empty. No storage workload was run.

The four diagnostics are FIFO, clear-swap timeout, clock and PMU messages from this interval. Independent review verified trace and snapshot integrity, ACK pairing, absent shutdown continuation and retained SSD state.

The [rear-empty control](dev-147-rear-empty-reconnect-2026-09-05.md) completed its clear chain in 32.907 ms; this attempt took 51.749 ms. A single comparison cannot attribute timing variation to the drive. Reconnection in kernel state with the SSD present contradicts an always-blocking drive effect, while intermittent interaction remains unresolved.

## Next work

Record visible image confirmation. Stop blind reconnect cycles and review the bounded clear-wait budget and shutdown continuation contract using these actual late replies. Keep PR582's no-crash behavior and genuine timeout reporting. Do not combine rear PHY, USB enumeration and startup fixes in one speculative patch.

Rechecked [upstream PR582](https://github.com/AsahiLinux/linux/pull/582) on 2026-09-05: it remains open and deliberately preserves the 50 ms wait and return control flow while removing the permanent crash latch. The captured late reply is additional evidence for a separate follow-up; no upstream submission was sent.
