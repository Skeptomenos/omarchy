# DEV-147 — LG 27 spontaneous dropout and failed recovery — 2026-08-30

## Result

The [earlier 4K60 recovery](../research/dev-147-lg27-link-investigation-2026-08-30.md) was temporary. David reports that the LG 27 went blank without a cable or setting change. He then unplugged and reconnected it; the image did not return. The internal screen stayed normal and the system stayed responsive. Exact physical-action times are unknown. Keep the original success and failure records unchanged.

This is a new failure state: Linux detects the external monitor and its 16 modes, but cannot activate it. The compositor log shows kernel/DRM rejection of mode tests and an actual 640×480 commit with `EINVAL`. The poweroff crash latch is the leading recovery-failure hypothesis, not a proven cause. A separate display-service allocation fault is confirmed. Neither result identifies the cause of the initial spontaneous loss.

David also confirms that the other cable carries video with another MacBook and another monitor. Cable compatibility remains open; do not call the cable defective.

## Read-only evidence

| Check | Result |
|---|---|
| Kernel / loaded TIPD identity | `7.1.6-1-1-ARCH`; T1 build ID `40aa54382047ba36b02c9ac0da65a213862a77ad`; same boot as temporary 4K60 success |
| External DRM / compositor | DP-1 connected, disabled, 16 modes; Hyprland reports 0×0 with DPMS on |
| Internal DRM / physical report | Enabled, 2560×1664 at 60 Hz; David confirms normal image and responsiveness |
| After reported manual reconnect | DP-1 still connected/disabled with 16 modes; internal output enabled |
| Dedicated compositor log | Ordered disconnect, disable, reconnect, repeated atomic TEST_ONLY failures, then rejected 640×480 commit; errors say `Invalid argument` |
| Idle / configuration | Current Stay Awake flag enabled; no reported Hyprland config errors. The tooltip offers “Allow Idle Lock & Screensaver”; it is not the current idle state. This does not prove historical idle state. |
| Loaded / installed Apple DRM note | Both `dd5e291114047bb4d7c83a529cddb4f4ac9292d7`; installed module SHA-256 `dbffe74e13a43e15e47fdc5eafe32eb1829b114a3f02f15fe6b18507d622b0e3` |

The first recurrence identity read was at 17:38:31 UTC. The 640×480 attempt came from the compositor, not an agent command. No driver, setting, mode, idle state, boot file or cable was changed by an agent. Reading a matching module note is identity evidence, not a complete loaded-memory comparison.

Independent read-only disassembly of the installed module confirms the timeout store and silent atomic rejection in the actual packaged code. Both firmware-specific poweroff implementations set the same byte that the atomic check tests before returning -22. The other two rejection paths contain error logging. This closes the source-only assumption for the matched module; it still does not prove the branch executed during this failure. No probe was installed.

### Kernel sequence

Times are journal receipt times in seconds since boot. User reports establish physical order, not exact correspondence to each kernel event.

| Time | External DCP event |
|---|---|
| 6062.556597 | Last captured successful 3840×2160 modeset completes. |
| 6679.220029 | Firmware reports a FIFO error. |
| 6679.221042–6679.281206 | Interface terminates, HPD is removed, power-down proceeds, hotplug reports disconnected. |
| 6679.282009–6679.282122 | Firmware swallows swap 289 because controller power is off and timings are disabled. |
| 6688.943025 / 6688.946028 | AFK endpoint 0x28 rejects two new services: allocation table full. |
| 6689.108032–6689.177853 | Interface is published again; HPD and 16 modes return, with no valid active mode. |

The filtered kernel window has 302 records. No later external modeset or normal poweroff-completion message appears in that window. The compositor file has no timestamps; its ordered failures cannot be assigned exact kernel times. The user’s later replug may explain recovery events. Do not describe all reconnection events as automatic.

### Two distinct recovery findings

**Confirmed allocation fault.** A separate whole-boot filter yields 24 records: 16 service registrations, six duplicate-unit errors and two allocation failures. The 16 registrations consume channels 1–31, odd-numbered, by 6062.066431 seconds. The driver then successfully displays 4K. Thus full capacity and duplicate-unit errors alone did not immediately stop video.

At pinned Asahi source `e2e1930a9595bffafad92cec2b5504525efb9cd4`, [AFK allocation and teardown](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/gpu/drm/apple/afk.c#L262-L355) append entries without reclaiming torn-down slots. Endpoint 0x28 is DPAV, not DPTX or IOMFB. [DPAV initialization](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/gpu/drm/apple/epic/dpavservep.c#L17-L57) can reject a duplicate unit after generic allocation already consumed a slot. Later standard-service reports then arrive on unregistered channels. These are real registration failures, but do not establish the initiating FIFO cause.

DPAV supports optional EDID retrieval. [Mode enumeration](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/gpu/drm/apple/iomfb.c#L350-L381) can return firmware modes without it. The old-monitor EDID observed during temporary recovery remains a separate stale-identification problem; no fresh LG model identification is claimed.

**Leading hypothesis: poweroff crash latch.** The [poweroff path](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/gpu/drm/apple/iomfb_template.c#L876-L945) silently sets `dcp->crashed` if its clear-swap wait times out. A subsequent [atomic check](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/gpu/drm/apple/dcp.c#L330-L374) returns `-EINVAL`. Continued HPD/mode publication can coexist with that flag. The swallowed swap, missing completion and rejected modes fit this path. Other rejection paths exist, so they do not prove which branch executed.

[Open PR #582](https://github.com/AsahiLinux/linux/pull/582) removes that latch assignment and logs the timeout. Its reported validation is on M1, not this M2. The shared poweroff code also covers the internal output. This review neither installs the patch nor establishes M2 safety. It potentially addresses failed recovery, not initial cable compatibility or the initiating FIFO error.

## Capture quality and limits

Private evidence is under `lg27-rca-20260830.rbO1qYjz8d` in the persistent stage. `recurrence-snapshot.json` SHA-256 is `5ff82fb3d1c55a4ef26bf427449377f1dfbe89dbc5ada96143c605dc00c9c689`. Directory mode is 0700 and file mode is 0600. Independent saved-file QA passes for identity continuity, record counts, timing, DRM state and positive atomic-failure evidence. An initial reviewer misreading of the idle tooltip was corrected against the command source. Earlier snapshots remain unchanged. Raw boot identifiers, monitor serials and broad desktop logs are not published.

Reads used fixed DRM attributes, identity notes, filtered journal queries and the dedicated Hyprland log. No partner `usb_mode`, register access, tracing, mode request, module load, suite, build, staging or privilege ran. TIPD logging had already reached its 128-record cap before this incident; missing subsequent TIPD messages prove nothing.

A broad user-service journal exceeded the tool budget at 73,275 tokens and could not be parsed. Its mixed application scope is not retained as evidence; only failure metadata is saved. Two narrow journal patterns returned no matches/exit 1. The rolling log held only recent input diagnostics. The dedicated compositor file supplied the positive atomic-failure evidence instead. Its saved filtered excerpt is limited to the last 130 matching lines, at most 900 characters each. These captures are not a full health audit.

## Next boundary

1. Preserve this failed state and stop arbitrary reconnects or mode changes. No reboot is needed to finish this diagnosis.
2. Design one bounded diagnostic of the exact atomic rejection branch. Map it against the installed module that matches the loaded build ID. An isolated branch trace with one external-only TEST_ONLY request could distinguish the latch from other DRM rejection. It is a live diagnostic, requires fresh approval and David's sudo support, and is not released here.
3. Do not run upstream probe scripts unchanged. Their global trace clearing and compositor reload/mode actions exceed this scope. Any approved diagnostic must own only its probes and trace buffer, have a short deadline, and remove only its own changes. If those bounds cannot be met, stop and review a separate one-boot diagnostic instead.
4. If the latch is confirmed, review a contained one-boot PR #582 candidate, preserving stock/W/T1 images, boot defaults and rollback. No live Apple DRM replacement. Treat AFK service reuse and the original spontaneous loss as separate fixes/investigations; do not combine speculative patches.
5. Prepare any upstream evidence against the existing PR before proposing a duplicate. Submission remains a separate approval. USB, sustained charging, startup/sleep reliability and permanent integration remain open.
