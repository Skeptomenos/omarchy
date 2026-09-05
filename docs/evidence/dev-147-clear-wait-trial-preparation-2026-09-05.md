# Clear-wait diagnostic preparation — 2026-09-05

## Decision and scope

The [fixed-X8 reconnect](dev-147-fixed-x8-reconnect-timeout-2026-09-05.md) recorded a 51.749 ms clear-swap reply chain followed by the timeout warning and no shutdown tail. This justified preparing one diagnostic change: extend the existing wait from 50 to 100 ms. It does not establish a production timeout bound or prove that the rear drive caused the delay.

The user authorized continued implementation until manual support is required. The [living plan](../plans/2026-09-05-dev147-front-port-stability.md) owns remaining work. No privileged action or boot change occurred during this preparation.

## Frozen source

Trial root: `/home/david/Work/dev147-clear-wait-trial`.

- Source commit: `d2f36591abdb0db296ac24e5a2b9dade5ae40ef1`.
- Parent: `83604c8b18e4673ed91e1172aef9aebeb0af20ce`.
- Only driver delta: 50 → 100 in the clear-swap completion wait.
- Release: `7.1.12-dev147-clearwait100`.
- Config SHA-256: `f69e63e55cbc6b257a951c82b3e581ffc60d4614a5965561cbc322960767bdff`.
- Only baseline config delta: `CONFIG_LOCALVERSION`.

The source retains the AFK correction and PR582 timeout recovery behavior. The baseline source, output, installed kernel and recovery files remain separate. Compilation uses the same pinned toolchain and reduced-priority four-job recipe, with planned 280-second checkpoints.

## Checks completed at preparation

`bash dev/apple-dp-altmode/fairydust/clear-wait-trial/validate.sh` returned zero. The independent run was `checks/offline.YSuzV7Ca`; its review receipt SHA-256 is `1580dbf413b84b9c4bf8b42c90ce8c6d5947748fb9f4a2118729ebb8fcf04bc4`.

The gate checks the exact patch and extracts six Linux completion functions into a deterministic C harness. The baseline rejects a 52-tick reply; the candidate accepts it. Absent replies, late replies, precompletion and deadline-boundary controls pass their expected outcomes. Compiler warnings are errors; UBSan, Ruff, formatting, strict mypy and shell syntax checks passed.

The harness does not execute DCP poweroff, callback lifetime, RTKit, KMS or the shutdown tail. It establishes completion semantics within its time/locking model.

The isolated initramfs recipe reuses the baseline namespace builder with new release/source/config pins. Independent preparation ran 13 checks: eight shell syntax checks, module mutation controls, startup controls, wrong-release image rejection, truncated image rejection and diff checks. All passed. Receipt: `checks/initramfs-recipe-independent.al8xm25x/receipt.json`, SHA-256 `8323c018a5c918ec3886e1f47a5fc2dd9190471d7fc30aa3503ebf9e3e98f467`. The parent completion gate also passed again at `checks/offline.khr2IBtL`.

## Limits at this checkpoint

Full compilation, module staging, artifact validation, actual trial initramfs creation and independent artifact review were pending when this preparation record was written. Hardware acceptance remains open. The selected kernel remains `7.1.12-dev147-fairydust1`.

The [trial procedure](../../dev/apple-dp-altmode/fairydust/clear-wait-trial/README.md) provides commands. Subsequent build and boot results must be recorded separately or as dated addenda.

## Addendum — build and initramfs completed, 2026-09-05

The fifth compilation chunk returned zero. The first four returned the planned checkpoint status 124; a scan found no compiler-error, fatal-error or undefined-reference diagnostics. `logs/build-chunks.json` preserves that distinction. Private module installation and explicit depmod returned zero; depmod stderr was empty.

Assembly returned zero. The full `validate-build.sh` gate returned zero at `logs/full-build-gate.log`, reporting all 1,862 modules, AFK controls and J413 DP/SIO wiring PASS. Image SHA-256: `048af4bcf37e0ce365bfeb2ebb03c42c8786631cd48b94ea37e6e355975f2f84`.

The J413 DTB is byte-identical to the baseline: `9831d42f9c271ce35dd3e32b5c8298e1c13849568853aea0779f40bb67377b80`. This trial needs no ESP/m1n1 bundle replacement.

The unprivileged namespace initramfs build returned zero at `initramfs/run-001`. Image SHA-256: `a3de88afae768731a0a23bd7aaaacc02e19ac520fbed0f5df7c41ae69cf3dae9`. Actual-image validation, module and startup controls, and truncated-image rejection returned zero at `checks/initramfs.Zl3ZF15p`.

Independent stage preparation passed 22 namespace controls at `checks/stage.SGSteyFc`. Its review receipt SHA-256 is `a3628e88e589eef05842fffbbbd79f60615a3d8521a65419e3347873c6004526`. The pending launcher refused to run before sudo. Independent assembly-procedure review passed at `checks/assembly-review-independent.kd35sec_`, receipt SHA-256 `2ee73d9590d584a79770f67d06d6b70f188558ad032c24fb2aa9d6bce3c161fd`.

The stage procedure preserves GRUB, the ESP and existing recovery inputs. The trial can later be selected by changing only its kernel/initramfs paths in a transient GRUB edit. Full delivery rehearsal and real manual staging remain pending at this addendum.

## Addendum — full delivery rehearsal, 2026-09-05

Independent full build validation returned zero at `checks/build-independent.z2lninmt`. Receipt SHA-256: `9641f033ef8e514a15311e97eb5d24c6b944a28982d0893305d7b7b95a91c97e`. Generated helper Rust bindings match the baseline; main/UAPI binding differences reflect only the release string and its length. Build warnings do not establish a new binding-layout change.

The assembled delivery manifest SHA-256 is `a89c31f8b42c3f4f958ac8aca4c312c95a222baf2e80b8b5702dbe4549e8a857`. Independent full-delivery staging ran the exact bootstrap/helper in disposable unprivileged namespaces at `checks/stage-full-independent.y9ny2ep8`. It passed in 8.966 seconds: all 1,862 modules, 1,876 module-manifest files, published boot inputs and receipts matched. All 15 protected fixture files retained their hashes.

The rehearsal used the actual delivery and readable baseline boot files. It used saved routing source for root-private GRUB fixtures. The real helper must still check those live private files during David's run. No actual staging or boot occurred.

The final launcher pins this rehearsed manifest. Launcher SHA-256: `2355fc81da26309b74e3a4fa7db29889b97c8584c173c4e394084fee32c5355f`. Helper SHA-256: `96b4ef29a03897c612ff2a978a932b5dc31d6da2cf7dfc1eded7ab08ed20ea1f`. Shell syntax and diff checks pass. The next manual action is the stage-only launcher; review its receipt before a restart or temporary trial selection.

Independent actual initramfs validation also returned zero at `checks/initramfs.w0A63RDv`. Trial capture software validation returned zero at `acceptance/checks/software.H7qELEYw`. Its explicit uname fixtures cover the trial release and reject baseline/unknown releases before trace setup. These are preboot software results, not live trial capture.

Final independent review reports no blocker to the stage-only handoff. It verified that the final launcher differs only by replacement of the pending manifest with the rehearsed hash. Actual initramfs validation covers 334 matching modules and 12 embedded firmware files; the existing ESP vendor archive remains separately verified. Final review receipts:

- `checks/initramfs.w0A63RDv/independent-review.json`: `bb0c74f2f5af41af4a01d71cc4094535837710aa7d48c920beffa0ba270e27a9`.
- `acceptance/checks/software.H7qELEYw/independent-review.json`: `ae8f780f5c960229260646ace0066f3482a5ef3252673bdf202029a85f0cbb96`.
- `checks/stage-full-independent.y9ny2ep8/final-launcher-review.json`: `cd8eef2a3633ca9f6d1ebda5061292fd874811d2353296ccb2735a9b9c41fff1`.

No actual staging, boot, tracing or trial hardware acceptance occurred. DEV-147 was updated with the stage-only dependency and commits `92c16aa0d` and `78cb3a2cd`.

## Addendum — actual stage verified, 2026-09-05

David ran the pinned stage launcher and supplied exit 0. The private receipt at `/home/david/Work/dev147-clear-wait-trial/stage/manual-results/result.json` reports `STAGED_UNSELECTED`, the exact trial release and manifest. Receipt SHA-256: `cac1088402b6bb90d08baba8a55eda17be3b1424edc291bd8045a910145e9eb5`. Stderr is empty.

Read-only verification of installed module files with `sha256sum --check --strict --status /home/david/Work/dev147-clear-wait-trial/delivery/modules.sha256` from `/usr` returned zero. Published Image, initramfs and config hashes match the accepted delivery. The new boot and module directories are root-owned, mode 755. The helper reports preserved current default, ESP and protected state. The running release remains `7.1.12-dev147-fairydust1`.

Actual staging is complete. Trial boot and hardware validation remain pending. The next attended action is a transient GRUB edit of only the linux/initrd paths, as specified in the stage guide. Preserve current cable connections for the boot observation; report release and visible internal/external display behavior before any further reconnect.

## Addendum — trial boot, 2026-09-05

David booted `7.1.12-dev147-clearwait100`. He reports a working internal screen and responsive system, but no external image. Read-only capture `acceptance/trial-boot.uxa1108a` confirms boot `c9cfab56-d624-48e8-a7a4-04ae5a763fbe`, external DP disconnected/disabled and internal eDP connected/enabled. Snapshot SHA-256: `833331819d62b79173c3ed7879d7fbea0ee83c654388b6d51e479af9022e9099`.

The collector returned SNAPSHOT_CAPTURED_WITH_ERRORS: 22 classified journal records, no collection issues. The boot log contains repeated external-DCP probe deferrals before it binds and boots; the record count is not a count of distinct new defects. Both physical Type-C ports have partners; the front reports host data role and PD sink. The external DCP reports connected=0 at initialization, with no external display service generation. No clear-swap or setPowerState timeout was found in this boot's journal. ESP/recovery/guard pins still match.

The blank attached-at-boot display remains an open startup result. It does not test the trial's disconnect wait. Next capture one front reconnect with the rear cable left untouched, to establish image recovery and retain negotiation evidence. If the image returns, assess that trace before a later connected-to-connected teardown test.

David also reports that the paired Fairydust GRUB menu is harder to scan. The current saved configuration has one Fairydust entry. He requests future trial names keep the installed baseline name and append a short suffix, instead of replacing multiple name segments. This preference is recorded in the living plan. The running trial's release, module directory and pinned artifacts were not renamed.

## Addendum — first trial reconnect restores video, 2026-09-05

David reports an external image after about 11 seconds. Capture `acceptance/trace-capture.mwAFJQZb` spans uptime 895.83–940.83 on the same trial boot. It contains 2,118/2,118 records and 24 zero loss counters, exit 0, empty stderr and successful instance cleanup.

There are no A407/A408 clear-swap calls or A467/A457/A472 shutdown-tail calls in this capture. The initial external connector was already disconnected. This result establishes image recovery from the failed startup state, not acceptance of the larger timeout.

Front Type-C data returns at 904.739158; DP pin C appears at 905.566423, HPD at 905.891205. DCP hotplug callbacks occur at 908.519933, then disconnect at 910.513102 and reconnect at 910.748036. The journal records a 3840×2160 modeset at 910.760142. These software timestamps do not replace David's insertion-to-visible-image estimate. Four external endpoint 0x28 service announcements occur during the one physical reconnect; do not equate announcement pairs with two user actions.

USB remains faulty. Front bus usb3 resolves to controller `502280000.usb`. The hub enumerates, resets and returns, then disconnects at 913.292014. Four descriptor-read errors and two address errors report -71; enumeration finally fails at 915.816583. The final USB inventory contains only root hubs. Snapshot `acceptance/first-reconnect.v7gkw1ak` confirms both DRM connectors enabled, two classified journal errors and no collection issues; its driver filter excludes these USB failures. This is a video recovery with USB faults, not a clean interval.

Next perform one scoped front-only reconnect from the now-active display, keeping the rear cable untouched. This tests the actual clear-wait and shutdown tail. Inspect its result before any further cycle; do not start an endurance batch. DEV-163 retains ownership of the hub fault.

### Correction — method names versus numeric tags, 2026-09-05

Independent review corrected the preceding blanket absence claim. `iomfb_push` prints method names, not numeric A-tags. The trace contains power-state and normal frame swap calls after reconnection: `dcpep_set_power_state` at 910.759211 and `dcpep_swap_start`/`dcpep_swap_submit` from 910.983686/910.983734. These map to A472/A407/A408. Searching only numeric tags incorrectly reported their absence.

The narrower conclusion remains: there are no method pushes during the initial unplug period, before reconnection and display power-on, and no abort-swaps/last-client-close shutdown chain. This capture does not exercise the poweroff clear-swap wait. Subsequent analysis must classify method names by timing and caller sequence, not numeric text searches or an undifferentiated swap-call count.

## Addendum — longer clear-wait exercised, 2026-09-05

Active-display reconnect capture `acceptance/trace-capture.H6RTWN8n` retains 1,338/1,338 records with 24 zero loss counters, exit 0, empty stderr and removed trace instance. Window: uptime 1251.82–1296.82, same trial boot. Report SHA-256: `63234b15f50025ab67e15345474d1ce00439e9c75e641b5313698c28eabcfe2e`.

The actual context-2 clear-swap and shutdown sequence is present. Times below are monotonic seconds; ACK refers to the matched transport reply, not a directly traced completion cookie.

| Method | Push | ACK |
|---|---:|---:|
| dcpep_swap_start | 1253.838714 | 1253.891787 |
| dcpep_swap_submit | 1253.891799 | 1253.891935 |
| iomfbep_abort_swaps_dcp | 1253.891961 | 1253.892030 |
| iomfbep_last_client_close | 1253.892031 | 1253.892301 |
| dcpep_set_power_state | 1253.892302 | 1253.892351 |

The clear-swap reply chain takes 53.221 ms. The following abort/close/power-state calls demonstrate that the waiter passed into the shutdown tail. The journal records poweroff done at 1253.894680 with neither clear-wait nor power-state timeout. This directly supports the larger diagnostic budget for a reply beyond the old nominal 50 ms. It does not establish a worst-case bound, exact scheduler counterfactual for the baseline, or general stability.

The external connector returns and the journal requests a 4K modeset at 1262.981889. Snapshot `acceptance/active-reconnect.x46n0sqo` confirms both DRM connectors enabled. User-visible image return and timing are pending.

USB remains a separate blocker: front hub repeatedly disconnects and logs descriptor/configuration/address -71 errors during this window. The current downstream USB inventory is empty. Some USB disruption precedes the monitor teardown, so not all of it can be attributed to that unplug. Five snapshot-classified errors do not include the complete USB journal. Retain the trial for analysis, pause stress cycles, and prioritize USB fault isolation before endurance qualification. Do not mark release acceptance complete.

Independent review verifies all five endpoint 0x37/context-2 ACK pairs, distinguishing interleaved context-0/3 callbacks. It confirms the 53.221 ms clear sequence and completed tail. Exact wait entry is untraced; retain the stated counterfactual and stability limits.

## Addendum — visual confirmation and USB isolation, 2026-09-05

David confirms H6RTWN8n restored the external image in roughly 5–7 seconds. Combined with the independently checked 53.221 ms clear-swap chain and completed shutdown tail, this is one successful attended teardown/recovery on the diagnostic kernel. Retain the 100 ms trial for further qualification; no production-bound or endurance claim follows from one result.

The front Type-C trace last reports unchanged DP pin C, USB2 and HPD at 1262.711295. Subsequent USB hub failures continue through 1273.192784 without another recorded Type-C data-status change in the capture. This narrows the observed failure to USB behavior while DP remains active; it does not identify a defective cable, hub or driver. The hub remains absent after the capture.

Clarification of the prior timing note: USB disruption before DCP teardown is not proof that it preceded the user's physical unplug. No physical-action timestamp was recorded. Do not infer which early USB event was spontaneous from kernel ordering alone.

The next discriminator depends on equipment David already has: another cable known to carry both USB-C video and USB data, or another USB-C monitor. Ask availability before prescribing the one-variable comparison. Keep the current kernel and rear connection fixed; do not begin another endurance batch or make a speculative USB patch.

David confirms a second USB-C monitor, LG35, is available. Select a one-monitor comparison: retain the same USB-C cable, front port, plug orientation and rear connection on the current trial boot. Power the LG35 on beforehand. During one attended trace, disconnect the front cable, move its monitor end to LG35, and reconnect the front once after at least five seconds. The default 45-second capture is adequate only if this can be completed inside its READY window. Record visible image/time and inspect USB enumeration; a different monitor's timing does not isolate resolution or monitor implementation effects.

## Addendum — LG35 comparison fails negotiation, 2026-09-05

David reports no image on LG35. Capture `acceptance/trace-capture.uhjc27vs` spans uptime 2135.68–2180.68, with 125/125 records, 24 zero loss counters, exit 0, empty stderr and removed instance. Report SHA-256: `8d44a531ecdfbc71dc8ab495df63a02107f79e4b6764e392ab459d961a2fca4d`.

Front data-status events at 2160.132248 and 2160.175299 contain USB_DATA_ROLE and DATA_UPSIDE_DOWN; the second adds USB2/USB3 flags. Neither contains DP_CONNECTION or HPD. Snapshot `acceptance/lg35-attach.jlw1y2k9` reports front device data role/PD sink, external DRM disconnected/disabled and internal eDP enabled. Only rear USB root buses remain. The pinned CD321x source maps USB_DATA_ROLE to USB_ROLE_DEVICE. No display mode negotiation occurred for the new monitor.

The old display's shutdown still completes: clear start 2161.060060, submit ACK 2161.108280, a 48.220 ms chain; abort/last-close/power-state follow, poweroff done at 2161.110462. No clear-wait timeout. This failure occurs before a new DP connection and does not refute the previously observed larger-wait benefit.

The working trace did not report DATA_UPSIDE_DOWN, so the comparison has a reported orientation difference as well as the monitor change. This does not establish how the user handled the cable. Ask whether LG35 selected USB-C input and whether the same cable/front port and Mac-end orientation were retained. Stop physical testing pending those facts; no repeated SWDF role write or speculative driver patch.
