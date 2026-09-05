# Ten front-port recoveries: capacity crossed, faults remain

David confirms four additional reconnects restored an image in about six seconds each, bringing this boot to ten visible recoveries. The [bounded record](dev-147-front-ten-generations-2026-09-05.json) binds the capture and kernel events. External DP remains connected/enabled.

The same external DCP boot accepted twenty endpoint 0x28 service announcements, on odd firmware channels 1 through 39, followed by ten completed display modesets. Accepted announcements 17–20 exceed the original sixteen-service capacity. Firmware channel IDs are not host slot indices. This is positive evidence for the bounded AFK capacity/recovery checkpoint; it is not a direct trace of retirement invariants or a matched unpatched-kernel control.

Independent read-only review returns `PASS_WITH_KNOWN_FAULTS` for this narrow checkpoint. It verifies the saved hashes, live pins, kernel/boot identity and event counts. Its scan of all 3,120 retained current-boot records finds no AFK-capacity, expected-announce, panic, Oops, BUG or RTKit/DCP-crash signatures. Retained records begin before the DCP boot; this remains a log-based observation. The JSON evidence binds the private review receipt. No unchanged software gate was rerun for this hardware record review.

## Faults during the latest batch

The collector `ten-confirmed.mlonvf2b` reports `SNAPSHOT_CAPTURED_WITH_ERRORS`, with no collection issues, twelve classified firmware errors and three classified host errors. The host warnings are poweroff clear-swap timeouts at boot-relative 4763.158026, 4776.878005 and 4806.623228 seconds. Each is followed by a successful display recovery.

The warning is the exact path supplied by the attributed PR582 timeout change in `drivers/gpu/drm/apple/iomfb_template.c`: a clear-swap completion wait expires after 50 ms, warns and returns without setting the permanent `crashed` flag. Recovery occurred after this path on this candidate. That does not establish why completion failed, whether cleanup is complete, or whether changing the timeout would be correct. Do not extend the wait or hide the warning as a substitute for diagnosis.

A separate full-journal check finds four USB descriptor `error -71` messages between 4784.984027 and 4785.745043 seconds. The USB core then attempts a port power cycle. The monitor hub subsequently enumerates below high speed during that connection. At the later final snapshot, hub `0bda:5411` is back at 480 Mb/s and LG controls `043e:9a39` at 12 Mb/s. No throughput or transfer-integrity test was performed. Track the transient enumeration fault under existing DEV-163; it is not proof of permanent hub loss.

The collector's selected-driver diagnostics do not include every USB or system error. The full-journal check is therefore distinct from its summary. Repeated firmware clock/PMU/FIFO diagnostics also remain unclassified as to cause; they are not assumed harmless.

## Decision

Pause the requested reversed-orientation ten-cycle batch. David confirms it had not started. Keep the monitor connected and preserve the working kernel. Diagnose disconnect completion and USB enumeration before further stress testing. The twenty-generation target, reversed orientation, startup detection and complete release matrix remain open. Ten images alone do not meet the front-port stability release gate.
