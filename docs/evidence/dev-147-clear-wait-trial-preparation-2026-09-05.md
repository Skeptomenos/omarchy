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

## Addendum — earlier-stack comparison preparation, 2026-09-05

David authorizes comparing the older working stack and reports another LG35 reconnect with no image. Snapshot `acceptance/lg35-repeat-failed.mpt6_vtg` confirms disconnected external DP on the same trial boot. No agent cable or boot action occurred.

The identified W image is `/boot/initramfs-linux-asahi-dpalt.img`, SHA-256 `ae8f1ed7f4f258f89931209cd7de6030be9f6875372d7329151b822a6ba2281f`. This matches the recent root staging receipt and the Sep1 W evidence. The old kernel hash is `ee36d989d62f2dd498b818e15c2044350c79d814a2017ffca61fdc2ad1aa95b6`; the retained old ESP bundle is `203ab7027536c8d16f373d02c1f6346a5c34cfe095a9dafd0cfe37d2b354090c`. Both readable files still match directly. The old module directory `7.1.6-1-1-ARCH` exists.

Independent restore source review finds no running-release restriction in restore mode. It verifies the saved old inputs and restores the old bundle before original GRUB. The new trial files are preserved. Frozen helper and topology hashes still match the reviewed launcher. Do not run the pre-activation gate against this activated system.

Before restore, David must freshly verify root-private W with a checksum command that stops on failure. Then use the existing restore launcher and review its result before reboot. After a full restart, W requires changing only the old GRUB initrd basename to `initramfs-linux-asahi-dpalt.img`; the old default image is different. Preserve existing kernel arguments.

The comparison plan distinguishes a recovery checkpoint from causal evidence. The current LG35 failure followed a hot swap; W after reboot has reset host state. If W works, a matched fresh-start trial result is needed before attributing the difference to the kernel stack. No new kernel patch is justified by the present observation alone.

Independent restore-only namespace verification passes ten controls on the current trial release. It exercises the existing frozen helper/bootstrap with a seeded activated fixture, including damaged route/backup rejection, old-initramfs drift rejection, broken candidate tolerance, missing/corrupt selected-bundle recovery and old-bundle-first behavior on a GRUB write failure. Synthetic W and added trial files remain unchanged. Receipt `checks/restore-independent.flly4f8g/receipt.json`, SHA-256 `feb9d9ec24fe67b30eaba60a952d58162fcb514f722af5d9b74b2cd8568cc6bf`. The fixture substitutes topology and prior-stage receipt identities; it does not establish an actual recovery boot. No handoff blocker remains for the fresh W checksum followed by the existing restore launcher.

## Addendum — old paired stack restored, 2026-09-05

David's fresh W checksum reports OK. The restore launcher returns zero with empty stderr and `RESTORED_NOT_REBOOTED`. Receipt `/home/david/Work/dev147-fairydust-boot-20260905/activation/restore-results.77wrOH2z/result.json`, SHA-256 `475a6f630f6abbd661318d24b14007aa2c82b79f0310a742b6d052ce9740b56a`, records 591 protected inputs, old bundle `203ab702…` and original GRUB `57d839b9bc7d3488402a8cf7c9e45328dc0097731fc395b0514c467d06b7a327`. Direct reading confirms the selected ESP bundle now matches the old hash; old kernel still matches `ee36d989…`.

The running kernel remains the trial until restart. The next boot must fully restart m1n1 with the restored bundle. In the restored Arch Linux entry, change only `initrd /boot/initramfs-linux-asahi.img` to `initrd /boot/initramfs-linux-asahi-dpalt.img`; preserve the kernel line and its arguments. Leave LG35/cable/rear setup unchanged. Expected release is `7.1.6-1-1-ARCH`; verify loaded W driver identities after boot and collect visible display/USB outcomes before another reconnect. This restore result alone is not a successful W comparison boot.

## Addendum — older kernel reproduces failed LG35 state, 2026-09-05

David reports rebooting the “default image,” with internal image and responsive system, LG35 blank and no cable reconnect. Read-only checks identify boot `2753fc6a-2774-4088-9cb8-784261d0bff1`, release `7.1.6-1-1-ARCH`, old ESP hash `203ab702…` and the retained kernel command line.

Loaded ELF GNU notes match the earlier successful W driver identities: AppleDRM `dd5e291114047bb4d7c83a529cddb4f4ac9292d7`, TIPD `8fd9e3d39ee211f439471a812fb5eaa2622f7585`. The current old-kernel port numbering differs: front controller 0-003f is port2, rear 0-0038 is port1. Front reports device/sink; DP is disconnected/disabled, eDP connected/enabled, and USB inventory contains only two root hubs. External DCP boots then reports disconnected with no modes; the journal records only a DPTX disconnect after startup.

This shows the failed LG35 state can occur with the older kernel and earlier working driver identities, so the newer Fairydust patches are not necessary to reproduce this observation. It does not rule out other regressions. Exact initramfs selection remains unresolved: David's “default” description could mean the unchanged default image rather than the requested dpalt image. Loaded driver notes alone do not authenticate the whole initramfs or module-load ordering. Ask the exact selection before accepting a matched W comparison. No new cable action or reboot is requested yet.

David explicitly confirms adding `-dpalt` to the initrd filename. Together with the fresh preboot checksum, old bundle and loaded driver notes, this establishes the intended W boot provenance. W also fails to show LG35 in the current setup. This is evidence against a failure requiring the new code to be running, not proof that earlier software could not leave persistent controller/monitor state or that Fairydust has no regression. Next verify the LG35 input menu selects USB-C while retaining cable connections. No more kernel changes or blind reboots are justified at this point.

## Addendum — powered LG35 baseline verified, 2026-09-05

David reports turning on LG35 restored its image without a reported cable change. Read-only verification on the same W boot confirms internal 2560×1664/60 Hz and external 3440×1440/99.982 Hz, both enabled and DPMS on. Front Type-C role is now host/PD sink. LG35 hub 0bda:5411 is enumerated at 480 Mbps; controls 043e:9a39 at 12 Mbps. USB enumeration is not a functional peripheral or throughput test.

The kernel logs hub/controls discovery at 279.339113/279.720025 seconds, external HPD at 280.869595 and modeset request at 280.965226. No USB enumeration errors appear in the inspected boot. These observations support monitor power/wake state as an important variable in the prior blank result. They do not retrospectively establish the monitor's state during every Fairydust test.

Private working-baseline record: `comparison/w-powered-on.6zVYHkiV`, with release, boot ID, command line, filtered driver journal, compositor modes, USB IDs/speeds and bundle hash. Current user authorization is to return to Fairydust while retaining powered monitor and cable setup.

Prepare a guarded return that reuses the retained activation state without overwriting its original backups. Preserve old-bundle recovery and validate the staged trial inputs. A clearly labelled trial menu entry should avoid manual long-path edits. No source-kernel change is part of this transition. The next cold trial startup and this W power-on-after-startup are different sequences; account for that distinction before declaring a regression if the trial remains blank.

## Addendum — guarded return software gate, 2026-09-05

The new `clear-wait-trial/return-to-trial` helper retains the original activation state, backup bundle, GRUB backup and recovery guide. It verifies both complete staged kernel inventories and the trial's original root-stage receipt. A separate root-private return journal saves the prior candidate menu. Ordered replacements publish the new menu, unchanged dispatcher, then the pinned Fairydust bundle. The named default is `DEV-147 fairydust 7.1.12 - test1 (100 ms)`; Fairydust1 remains the second entry. W stays on its separate old-bundle recovery path.

Frozen SHA-256 identities:

- `return.py`: `b68113720f9c23af4325bb6ad284c26c30b4cbe130601b62c70dfa7af027825c`.
- `launch.sh`: `76aad7ee86ed34e913a04814f74a8766e897bc328561d4646faee0e42cc6a839`.
- `candidate.cfg`: `2737b42aa18940d3f65e37a945df95b614b183c4ba84fe707084d0faae3dc1d6`.
- `baseline.py`, `topology.py` and `dispatcher.cfg` are byte-identical copies of the original reviewed activation inputs.

Author command `bash dev/apple-dp-altmode/fairydust/clear-wait-trial/return-to-trial/validate.sh` exits 0. Private gate `return-to-trial/checks/software.1oblqoyF` records eight tests in 28.401 seconds, lint, formatting, strict type checks and shell/GRUB syntax checks. It tests successful return and unchanged restore, all three interrupted replacement boundaries, existing state, altered routing, changed receipts, damaged trial Image and changed helper bytes. Synthetic W remains unchanged across return and restore. Both full real kernel/module deliveries and the real trial receipt are used; topology and original-stage receipt identity are substituted inside the isolated namespace.

Two real GRUB emulator cases execute the menu against a disposable ext4 image. They verify the default trial and selectable Fairydust1 entry, exact kernel/initrd arguments and cleared stale selection variables. Kernel/initrd commands are recording wrappers; this does not load a kernel or execute EFI firmware. Direct live read-only execution of the exact launcher preflight also exits 0 with `READ_ONLY_TOPOLOGY_PASS`.

No selected boot file, kernel source or running system changed. Hardware recovery, physical power-loss behavior and FAT atomicity remain outside these software checks. Independent final review and the user's password-assisted apply remain the next boundaries.

Independent rerun `return-to-trial/checks/software.RdgFx8UI` exits 0: eight tests in 21.378 seconds and both GRUB cases pass. Its source inventory SHA-256 is `95032743aac88759532c9e19711c648c5b5da4bb39a21b3b48b152c81991f36e`; GRUB receipt SHA-256 is `40cf9de47352d97084d3911778f739965e24090e3b98fd1c5b6e88e8ec0eca04`. Root rechecks every frozen code/menu hash against the author inventory and runs `git diff --check`; both exit 0.

Independent final review returns `VERDICT: PASS` with no blocking finding. The handoff is ready for David's normal-user `return-to-trial/launch.sh` run. Review its private receipt before a manual reboot. Keep LG35 on and cables fixed; the default named trial removes the earlier long-path editing step. Hardware comparison and release acceptance remain open.

## Addendum — return refused missing modules, 2026-09-05

David's run `return-to-trial/return-results.jYflVlnm` exits 1 with empty result output and `No such file or directory: '/usr/lib/modules/7.1.12-dev147-fairydust1'`. Stderr SHA-256: `8a40d8ea48298720e684525bbfd0de09a9e78efdfac5bab20395afe60bae546f`. The failure occurs in staged-input verification before return-state creation or any menu/GRUB/bundle replacement. `/var/lib/dev147-clearwait-return` and the package lock are absent. Selected ESP still hashes to the original `203ab702…`; W remains running.

Only the packaged W module directory remains active. The trial module tree is under `/usr/lib/modules/.old`. Both original private deliveries remain available. The installed `linux-modules-cleanup.service` skips the running release and package-owned directories, then moves other module trees with rsync and removes their original paths. Service SHA-256: `5d947290ef8c94b33c79c531e5615f4c9bea38e7649092d34af3bf0af5b1ca24`. No service drop-ins exist; it is enabled and currently inactive.

The previous boot's unit journal records Fairydust1 archival at 5.480726 seconds and removal at 10.285978 seconds. The current W boot records clearwait100 archival at 4.388547 and removal at 9.025067 seconds. These logs identify an installed cleanup policy, not a display-driver regression. The earlier gate supplied full module fixtures and therefore did not establish that live module paths survived reboot. Its software PASS did not justify readiness without that prerequisite.

Prepare a separate guarded module repair from pinned deliveries and a narrow cleanup exception for the two test releases. Preserve W, boot selection and recovery. No kernel rebuild or reboot is required for repair. Review its receipt before retrying the unchanged return helper.

Independent diagnosis verifies both pinned top-level manifests and all 1,876 module-manifest files per delivery, including 1,862 `.ko` files each. Receipt `checks/module-retention-independent.h81d3bx6/diagnosis.json`, SHA-256 `38eb89545a128640697a353690333325d65595a400687768d0f6cbf8a42c1fd4`, confirms intact repair inputs. Unit journals are also retained under `module-repair/diagnosis`. The absent older archive is consistent with the installed boot-time tmpfiles `R!` removal rule; no per-path deletion log proves that inference. Repair uses verified deliveries, not the archive.

`pacman -Qo /usr/lib/systemd/system/linux-modules-cleanup.service` identifies its owner as `kernel-modules-hook 0.1.7-3`. The repair preserves that vendor unit and limits its local exception to the two exact diagnostic releases.

## Addendum — module repair preparation, 2026-09-05

The separate `clear-wait-trial/module-repair` helper verifies private copies of both complete frozen deliveries. It prepares root-owned module directories, publishes a drop-in that exempts exactly the two test releases, reloads systemd without starting cleanup, and verifies the effective service command before publishing either module directory. Publication refuses existing targets. A separate repair journal retains completed boundaries for interrupted attempts. Existing boot files, W modules/initramfs, `.old`, the guard and original activation/staging records are covered by preservation checks.

The normal-user launcher preflight authenticates helper bytes, verifies the live inactive service, checks target absence, manifest pins and readable source paths before requesting the password. Full copied-content and root-private checks remain in the privileged phase. It does not select a kernel or reboot.

Frozen SHA-256 identities:

- `repair.py`: `713a0534da1bf9ffafef7c2490d885d57162651fb8fa882140a160bbfbc506cd`.
- `launch.sh`: `d7386149d6e409a2f33a4e29c52d71526827983e907ac8afdce31e160fa23d32`.
- `50-dev147-candidate-modules.conf`: `661df492cfdb6cf092199ace72789b9738520a8d052d10171001d61554d4a425`.

Author command `bash dev/apple-dp-altmode/fairydust/clear-wait-trial/module-repair/validate.sh` exits 0. Private run `module-repair/checks/software.lfdouGKP` passes seven namespace tests in 42.363 seconds, systemd syntax, actual cleanup-body execution, lint, formatting, strict types and shell syntax. Controls cover full deliveries, preservation, existing modules/drop-ins, changed vendor service, damaged or missing delivery content and interrupted second-module publication. Cleanup retains both candidates, the current release and package-owned kernels while archiving an unrelated unowned release.

Initial tests hit ENOSPC in a RAM-backed temporary fixture; disk-backed fixtures corrected that test setup. Earlier gate logs also retain test-only lint/type failures. No production repair behavior changed for those corrections. Namespace repair uses synthetic existing boot/state and a mocked systemd manager; cleanup-body tests decode the pinned unit's variable expansion and substitute package ownership. Real bash, rsync and rm operate only on disposable trees. Exact launcher read-only preflight passes on the live machine. Final independent review and manual apply remain pending at this checkpoint.

Independent final gate `module-repair/checks/software.aXsPPo1G` exits 0: seven namespace tests in 44.221 seconds, cleanup behavior, systemd syntax, lint, types and shell syntax pass. Exact normal-user bootstrap preflight also passes. Review returns `VERDICT: PASS` with no blocker. Receipt `independent-review.json` SHA-256: `8b4fe055f5d6f6130b301c1d1a4708652a029d4ae8d6f8165060cd712834188f`. Root rechecks the frozen source inventory and `git diff --check`; both pass. The manual module-repair handoff is ready. Inspect its receipt and both live module trees before the separate return command; no live repair or reboot occurred during preparation.

## Addendum — module repair applied and verified, 2026-09-05

David's `module-repair/repair-results.YFb3sL5J` exits 0 with empty stderr and `MODULES_REPAIRED_NOT_SELECTED`. Receipt SHA-256: `360bcb07009ccda204c313825263edf809db324d729ebd59bbb0149fbb5c2656`. It records both module releases, the pinned cleanup exception, successful daemon reload and no cleanup restart or boot selection.

Read-only post-apply verification independently hashes every staged artifact and all 1,876 module files per release, including 1,862 `.ko` files each. Both inventories match. Systemd reports the exact frozen exception command, expected vendor fragment and drop-in path, inactive/dead state and no queued job. The vendor unit hash is unchanged. The drop-in directory is root-private because its creation used umask 077; direct normal-user hashing is unavailable. Its installed hash is supported by the privileged receipt, while the effective loaded command is independently readable and verified. No permission change is needed.

W remains running at `7.1.6-1-1-ARCH`; old ESP hash `203ab702…` is unchanged. Return state and package lock are absent. The return helper and launcher retain hashes `b6811372…` and `76aad7ee…`. Root result `repair-results.YFb3sL5J/live-verification.json` records these checks. Independent verification returns PASS for retrying the unchanged return launcher. Inspect the next return receipt before reboot; this repair does not establish display acceptance.

## Addendum — trial return selected, 2026-09-05

David's retry `return-to-trial/return-results.fBVDEKz2` exits 0 with empty stderr and `RETURNED_TO_TRIAL_NOT_REBOOTED`. Receipt SHA-256: `76c9fd8794865161588a97f1bfb94f8a4d92e18277e686e49402fcbc68f708e3`. The privileged result records menu `2737b42a…`, dispatcher `58fd5692…`, paired Fairydust bundle `1ae29a2b…`, trial manifest `a89c31f8…` and trial stage receipt `cac10884…`. Direct ESP hashing confirms the selected bundle. GRUB/menu identities are supported by the privileged receipt.

Both restored module directories remain present with root ownership and mode 0755. The cleanup exception remains loaded and inactive; no package lock remains. W is still running until a full restart. The frozen menu defaults to `DEV-147 fairydust 7.1.12 - test1 (100 ms)`, using the clearwait100 Image/initramfs pair without manual edits. The next attended boot keeps LG35 powered on and all cables fixed. Record release, internal/external image and responsiveness before any reconnect; this selection receipt alone does not establish hardware success.

Independent read-only verification returns PASS for the full manual restart. It confirms receipt and frozen pins, direct ESP identity, both live module trees and absent package lock. Expected post-boot release is `7.1.12-dev147-clearwait100`.

## Addendum — returned trial boot observed, 2026-09-05

David reports `7.1.12-dev147-clearwait100`. Read-only checks confirm boot `ee6d8621-18d4-4821-9052-bb54b58f9ccb` and ESP `1ae29a2b…`. Snapshot `acceptance/lg35-powered-reboot.qbb7lvao` records internal eDP connected/enabled at 2560×1664/60 Hz and external DP disconnected/disabled with no modes. Its exit 1 means `SNAPSHOT_CAPTURED_WITH_ERRORS`: 20 classified journal records, zero collection issues. This is not a hardware acceptance PASS or a count of new faults.

Front controller 0-003f maps to port1 and reports host data role / PD sink. Both USB host controllers initialize, but the inspected boot journal has no downstream USB discovery. External DCP boots at 5.041548 seconds and reports disconnected with zero modes at 5.041817. This differs from the earlier device-role failure; it does not establish the exact point of startup notification loss.

Both test module directories survive this boot. The cleanup unit journal shows both exact-release exemptions taking effect and retains packaged W. This verifies the repair across a boot. User confirmation of visible LG35 output and unchanged powered-on cable setup is pending. Leave cables fixed; do not assign a regression or request another reconnect until the physical state is confirmed.

## Addendum — LG35 power-on restores trial image, 2026-09-05

David confirms no initial LG35 image, then reports that manually powering on the monitor restores it. Snapshot `acceptance/lg35-power-on-recovered.pk7h6zde` on the same trial boot confirms external 3440×1440/99.982 Hz and internal 2560×1664/60 Hz, both enabled with DPMS on. External HPD is asserted at 485.414916 seconds, followed by modeset at 485.508520. The snapshot records 22 classified driver records and zero collection issues; endurance remains unaccepted.

This reproduces W's observed recovery after manual monitor power-on. LG35 video is therefore demonstrated on both stacks under that sequence; the earlier blank result does not establish a Fairydust video regression. Automatic monitor wake remains unresolved. This observation does not distinguish monitor power/input settings, standby behavior or host startup handling.

USB differs: current trial inventory contains only four root hubs, with no LG35 hub or controls, while powered-on W enumerated both. The inspected trial journal contains no downstream USB discovery or enumeration-error messages. Preserve this as an unresolved USB comparison, not proof of a particular cause.

David asks to return to LG27. Keep the current trial and use powered-on LG27 for the next single traced front-port attachment, retaining cable, Mac-end orientation and rear setup. Keep LG35 as secondary coverage for later wake/USB checks; no further LG35 reboot is needed now.
