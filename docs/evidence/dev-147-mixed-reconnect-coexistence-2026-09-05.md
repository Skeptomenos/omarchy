# DEV-147 mixed reconnect and device coexistence — 2026-09-05

David reports that he disconnected/reconnected the X8 first and then the front monitor during the requested monitor-only test. Preserve this deviation: it is not the controlled fixed-rear comparison. User-visible image confirmation remains pending.

Capture `trace-capture.p4ZYkATZ` spans 2073.92–2118.92 seconds in boot `09746091-1f14-41ea-97b1-d3339f3a23af`. It retains 1337/1337 records with all 24 loss counters zero, exit 0 and clean instance removal. Report SHA256: `11e94da6c4ddfbb059d7f89160ed3a76c5f17b34e45d64b54d98c45077130545`.

Rear data status clears at 2075.908047, then reports host USB connection at 2079.627685. Front data status clears at 2081.132463. Front attachment is reported at 2086.101563, clears again briefly at 2086.219959, then returns at 2086.865132. DP pin C appears at 2087.509801 and HPD at 2087.899544. This short front bounce is recorded without attributing its cause.

## Both devices now enumerate

The X8 binds to UAS at 2083.593009 seconds and is identified as Crucial X8 SSD at 2084.485015. Current rear device `4-1` is `0634:5600`, speed 10000 Mb/s; `/dev/sda` is a 931.5 GiB USB disk with two partitions. A read-only mount-status check shows neither partition mounted at inspection. No drive contents were read or written.

Snapshot `mixed-drive-monitor-reconnect.okapjl38` confirms both DRM displays enabled, six external AFK service announcements and one external DCP boot. Monitor hub/controls remain enumerated. This establishes simultaneous device enumeration and enabled display state; it does not establish sustained storage transfers, visual continuity or a controlled cause/effect result.

Known FIFO, clock and PMU diagnostics appear during the monitor reconnect. The actual shutdown clear-swap start ACK takes 33.361 ms, submit ACK 0.212 ms, combined 33.577 ms. The journal reports poweroff completion at 2081.855119; no clear-swap timeout appears in the sampled interval. Independent review distinguished this shutdown pair from an earlier normal frame swap.

## Next boundary

The intended comparison remains open because rear state changed first. Preserve the current working device state. After confirming the visible image, perform one front-monitor reconnect with the now-enumerated X8 and its cable completely untouched. No new reboot, SSD reconnect, disk operation or driver change is needed for that test.

## Rear PHY warning

During X8 disconnection the rear PHY `383000000.phy` logs `Pipehandler lock not acked` at 2076.423031 and `Failed to lock pipehandler` at 2076.423647. Both have warning priority 4. In pinned `drivers/phy/apple/atc.c`, this matches the dummy-PHY transition warning path, which continues after the 1000 microsecond hardware ACK wait expires. The host-mode setup path uses error priority instead. This is a rear transition fault, not a clean mixed run or proof of a front-port cause.

The existing snapshot driver filter omits this PHY prefix. Its three classified firmware diagnostics are not the full fault inventory. Preserve the explicit kernel-journal warnings alongside the trace. The SSD's later recovery does not erase them.

User visual addendum: David confirms the external monitor image is present after the mixed sequence. This establishes image recovery alongside the enumerated X8. It does not remove the sequence confound, rear PHY warning or untested storage I/O. The next control is one front-only reconnect with the X8 left untouched.
