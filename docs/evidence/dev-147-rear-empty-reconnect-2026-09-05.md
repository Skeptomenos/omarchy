# DEV-147 rear-empty reconnect control — 2026-09-05

David confirms image recovery after one front-port reconnect with the rear drive kept disconnected. Boot remains `09746091-1f14-41ea-97b1-d3339f3a23af`.

Private trace `trace-capture.71zBNeFb` retained 1350/1350 records with all 24 loss counters zero and clean instance removal. Report SHA256: `9d451217514e56d5af5e4382145701d6dd825e23cb1274e8f2c881ab37a40bd3`. The capture window is 734.02–779.02 boot seconds.

Clear-swap start was pushed at 736.391947 and acknowledged at 736.424725 (32.778 ms). Submit was pushed at 736.424730 and acknowledged at 736.424854 (0.124 ms). Total interval is 32.907 ms; shutdown completes at 736.427202 without a clear-swap timeout.

Front firmware reports DP pin C at 743.562574 and HPD at 743.933913. AFK services on channels 5/7 appear, and modesetting completes at 746.979559. Snapshot `rear-empty-reconnect.em80zcnq` confirms both displays enabled, four external service announcements and one external DCP boot. User-visible image recovery makes this one reconnect a video PASS. It is not an endurance result.

The reconnect also restores USB enumeration: monitor hub `0bda:5411` appears at 744.819039, controls `043e:9a39` at 745.202015. Current speeds are 480 Mb/s and 12 Mb/s respectively. This is enumeration recovery, not transfer or input acceptance. The first-attachment USB failure and this recovery both occurred without the rear drive.

Known DCP FIFO/clock/PMU diagnostics remain in the journal. The snapshot reports five classified errors in its recent window and no collection issues; that window includes earlier records. No new USB enumeration failure or clear-swap timeout appears in this reconnect interval.

Independent review re-derived trace integrity, ACK timing, AFK generation, snapshot and USB state. Next compare rear-drive insertion while holding the working front cable fixed. Only after reviewing that result should one front reconnect with the drive present be considered. No disk read/write, role reset or kernel change is part of the insertion capture.

## Rear-insertion recorder preparation

Added allowlisted `rear-attach` mode. It changes only the instruction cue and mode field; existing filters, duration and cleanup remain unchanged. The cue keeps the front monitor connected and asks for one rear-drive insertion without unplugging either cable. No disk operations were added.

Author and root ran seven test methods successfully; shell syntax, Ruff, formatting, strict typing and diff checks pass. Launcher SHA256: `1e3d99d19cb8ab6c0b3552c415eb6b8ed2a8b523f16ffc14082a33cfce510b41`. Test SHA256: `37fd50a7812d7aba040393e84c105f8a989cf42cbbf6961f5c26ec0d2174fd18`. Author receipt: `/home/david/Work/dev147-fairydust-acceptance-20260905/checks/trace-rear-attach.hvcwpt9y/qa.json`, SHA256 `956904de8433aee7a7726fe279b71366788b5813b6b222ea30ae11bcea7e2811`. Actual rear insertion remains pending.

Independent review reran all seven tests, verified frozen hashes and syntax, and found no blocking code or instruction defect. The handoff is ready for one manual rear insertion; this does not qualify storage or both-port stability.
