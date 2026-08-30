# DEV-147 — LG 27 DisplayPort setup investigation — 2026-08-30

**Scope:** MacBook Air M2 J413, new LG 27-inch 4K connected by user report. Exact LG model and cable specification remain unknown.
**Authority:** David asked to reverse engineer the issue and get the monitor working after the proposed read-only snapshot. This pass performed unprivileged reads and source research. David later changed the cable himself and reported a working image. No agent changed a cable, setting, driver, privileged file or boot state.
**Repo state:** `8c91fb11b127546bbf3e3dfacc6879565031074f` before this record.

## Finding

The initial LG 27 failure is upstream of desktop output selection: the exposed external connector was disconnected, with no modes or EDID. The saved journal contains original-monitor success and new-monitor failure in the same T1 boot. This removes a different boot image as the explanation for those outcomes.

David then changed the cable and reported an LG 27 image. A second read-only snapshot confirms DP-1 connected/enabled, 16 modes and an active 3840×2160 output at 59.997 Hz. The kernel, loaded T1 note and boot identity remain unchanged. This establishes working 4K60 output after the reported cable change and rules out a general 4K limit in the current prototype. Cable compatibility is a leading explanation, not isolated causality: exact cable/port confirmation and the effect of repeated connection attempts remain open. It does not prove the rejected cable is defective on every host.

Preserve the [initial T1 evidence](../evidence/dev-147-t1-boot-capture-2026-08-30.md) and [monitor/cable correction](../evidence/dev-147-t1-monitor-identity-correction-2026-08-30.md). The later comparison below supplements them. It is not original-monitor startup acceptance or a general T1 reliability pass.

## Read-only results

| Check | Result |
|---|---|
| Kernel and loaded TIPD note | `7.1.6-1-1-ARCH`; exact T1 build ID `40aa54382047ba36b02c9ac0da65a213862a77ad` in both saved identity reads |
| External DRM `DP-1`, before / after cable change | Disconnected, disabled, no modes or EDID / connected, enabled, 16 modes and 256 EDID bytes |
| Internal DRM `eDP-1` | Connected and enabled; 2560×1664 |
| `hyprctl -j monitors all`, before / after | Only eDP-1 / eDP-1 plus active DP-1 at 3840×2160, 59.997 Hz, scale 1.6 and DPMS on |
| Bounded current-boot kernel queries | Failure snapshot: 378 matching JSON records. Post-swap projected window: 261 JSON records. Both share the original T1 boot. |
| Independent saved-file QA | PASS for both failure and working snapshots, with private-file, identity, mode, journal and EDID checks; no repeat live reads |

Commands read fixed DRM `status`, `enabled`, `modes` and `edid` files, the loaded module note, kernel/boot identity, compositor state, and a filtered kernel journal. Timeouts were 8 seconds for status reads and 15 seconds for the journal, with two-second termination bounds. The journal query used `/usr/bin/journalctl -k -b --no-pager --output=json`, selected fields, a display/Type-C/error keyword filter and a 2,500-row limit. The first spelling, `--kernel`, was rejected with exit 1 before capture; the corrected `-k` query is retained separately. No privilege or probe fallback ran.

Raw process outputs remain private under `lg27-rca-20260830.rbO1qYjz8d` in the existing persistent stage. The failure snapshot SHA-256 is `59af8e0b4bea9007cb15bf1aa4c5c28bdbc19e71b51f4e473c9c8505689594d5`; the working snapshot SHA-256 is `2754927e36cb9388128fe8310ed6a878fbc6f221839eaa3a8230fcc0f7a929b2`. Directory mode is 0700; files are 0600. The separate comparison/review record retains the agent's boot-ID `cmp` result. Raw IDs and device serials are not published.

The first post-swap orchestration received identity and external-DRM results, but its broad 79,686-token journal output exceeded the process-tool budget and gained a truncation preface. JSON parsing then stopped the cell; no compositor/EDID outcome from its concurrent calls is claimed. It did not hang or write to the system. The follow-up reacquired only the missing read-only values and projected a post-swap, 300-row-limited kernel window to five JSON fields. No consumed collector or privileged fallback ran.

## Same-boot contrast

Times are kernel-journal receipt times in seconds since boot. Monitor labels come from David's swap report; no automatic cable or physical-monitor identification occurred.

| External DCP phase | New monitor at startup | Original monitor after reconnect | New monitor before cable change | New monitor after cable change |
|---|---|---|---|---|
| Connection window | 12.978–15.688 s | 4258.267–4260.850 s | 4476.186–4478.921 s | Multiple attempts after 6001 s; productive events at 6039 and 6062 s |
| Drive-setting pattern | 28 before no publication | 4: two before publication, two during modeset | 28 before no publication | Several 28-message attempts; later publication succeeds |
| Interface published / connected modes | Not observed | Published; 14 modes | Not observed | Published; 16 modes twice |
| Native modeset completed | Not observed | 3440×1440, about 100 Hz at 4260.814 s | Not observed | 3840×2160, 60 Hz at 6039.627 and 6062.557 s |

The original monitor's same-boot mode record has a 543.5 MHz pixel clock and 10-bit color. The new working mode record has a 533.25 MHz pixel clock. This directly rejects a simple “4K unsupported” conclusion.

The working snapshot still exposes `LG Electronics / LG HDR WQHD`. Its 256-byte EDID SHA-256 is `a7c65e10b79718d46379d7c46e4239283ea2ab09e897f6467e3ad5d22d9809e6`, byte-identical to the prior original-monitor EDID. Treat the name and product code as stale cached metadata, not the LG 27 model. This matches the class of identification-after-swap behavior in [Asahi #474](https://github.com/AsahiLinux/linux/issues/474), but is separate from the solved visible-video state.

The journal was returned in reverse chronological order; analysis sorts timestamps without rewriting raw output. It is keyword-filtered, not a full-journal or overall-health check. Its original 39 T1 messages and timestamps match the initial capture. Later TIPD records reach the explicit 128-record budget cap at 4472.928277 s, before the final new-monitor connection attempt. Missing subsequent TIPD records prove nothing about sender behavior. Ordinary DCP logs continue after the cap.

## Pinned-source interpretation

Source is Asahi commit `e2e1930a9595bffafad92cec2b5504525efb9cd4`, the existing kernel source reference. This is source inspection, not new binary equivalence or hardware acceptance.

- [IOMFB modes and EDID](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/gpu/drm/apple/iomfb.c#L346): Linux exposes firmware-derived modes and attempts the firmware EDID-copy service only when modes exist. Empty exposed EDID therefore does not isolate an AUX/EDID failure. Mode validation requires a matching firmware timing; forcing an arbitrary desktop resolution is not a justified first treatment. Its connected-but-no-valid-mode path can deliberately mark link status BAD to prompt a userspace flush, so that property alone would not prove an electrical fault.
- [Drive-setting callback](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/gpu/drm/apple/dptxep.c#L210): the seven printed values are fields named `unk1` through `unk7`. The handler acknowledges and caches settings; it does not program PHY voltage there. The separate getter's lane-count comment concerns an unprinted field. Do not interpret printed `4`/`2` as proven lane fallback or increasing values as link rates.
- [DCP connection](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/gpu/drm/apple/dcp.c#L376): connection state and callback return do not establish displayed pixels. Several service-call results are ignored; a repeated connect may return on its already-connected flag. These are measurement gaps, not a demonstrated cause or a selected fix.

The failed setup diverges during display/link setup, before interface publication and usable modes. After the reported cable change, the same boot and driver reach publication, 16 modes and 4K60 output. Cable compatibility is a leading explanation, but physical-setup and repeated-attempt effects are not independently isolated. The exact electrical/protocol cause remains unknown. No delay, forced EDID, voltage change or crash-latch patch is selected.

## Upstream check and next boundary

A bounded primary-source search found no confirmed fix matching this signature. [Asahi #579](https://github.com/AsahiLinux/linux/issues/579#issuecomment-5459790089) contains a maintainer request for a full-featured non-Thunderbolt USB-C cable, but concerns a different display/signature. [LG report #481](https://github.com/AsahiLinux/linux/issues/481) names LG 27UQ850V-W on M1 with an ATC warning and supplies no demonstrated fix; it does not identify David's model. [haripako's status](https://github.com/haripako/dp-altmode/blob/7fd43775668f340cb84353801be6ce88833f383e/STATUS.md) concerns M1 and a different post-unplug problem. None is authority to apply a patch here.

The cable change is now a functional workaround: keep the working cable and current configuration unchanged. Obtain the exact LG model, both cable specifications, same-port confirmation and physical internal-screen result before wider claims. No new image, reboot or compositor change is needed to retain the current result. A later attended restart with this exact working setup is the next reliability gate, not an immediate requirement. If the project needs support for the rejected cable too, first reproduce it in a separately approved case and add the minimum missing link-rate/lane/PHY result instrumentation; do not guess a behavior patch.

No agent changed a driver, boot file, live checkout, configuration, cable, monitor setting or power state. David performed the reported cable change. No build, suite, old collector, staging helper or recovery ran. External 4K60 video now works; cable independence, restart reliability, accurate monitor metadata, USB hub behavior and root cause remain open.
