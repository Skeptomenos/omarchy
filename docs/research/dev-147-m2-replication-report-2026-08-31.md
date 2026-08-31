# M2 USB-C DisplayPort replication report — 2026-08-31

Status: UNSENT draft for haripako/Omarchy Mac, subject to recipient terms and submission approval. This replaces the dated hardware summary in the [2026-08-28 draft](dev-147-upstream-contribution-draft-2026-08-28.md), not its history. It is not an installation guide or a reliability claim.

Material AI assistance was used in the investigation, engineering decisions, source, tests and writing. David performed physical actions and reported visible results. [Asahi's policy](https://asahilinux.org/slop/) excludes this work as a compliant contribution to that project. Do not hide this provenance or route it elsewhere to bypass that policy.

## Scope and credit

One MacBook Air M2, J413/T8112, running `linux-asahi 7.1.6.asahi1-1` / `7.1.6-1-1-ARCH`. One external monitor at a time, on the front/lower left USB-C connector: controller `0-003f`, ATC PHY1, display mux index 2. The other USB-C port was not enabled or validated by this prototype.

The working setup combines the packaged kernel/AppleDRM with an M2 device-tree subset and backported CD321x HPD forwarding. Credit belongs to the Asahi/fairydust authors, including Janne Grunau and Sven Peter, and to [haripako's M1 investigation](https://github.com/haripako/dp-altmode). This is M2 replication, not a claim to have invented the route or forwarding:

- M2 device-tree source: `ad272ad5d6742869cdd13320e43f9ed01bd1fb33`.
- HPD source: `3d28209d04c77904e9909b6ab52046910c585a55` and `1aab123a6d57feae519268f55119c82e52e4adac`.
- The M1 installer/DTB and full fairydust kernel were not installed. Original attribution and per-file licenses remain intact. [Source history](../evidence/dev-147-prototype-history-2026-08-27.md#historical-stock-baseline-and-initial-research).

## Observed results

| Case | Result | Limit |
|---|---|---|
| [Working-image startup](../evidence/dev-147-one-boot-startup-2026-08-27.md) | LG35 at 3440×1440/99.982 Hz; internal 2560×1664/60 Hz; both visible | Monitor hub/controls did not enumerate at attached startup |
| [Identified W/LG27 startup, 2026-08-31](../evidence/dev-147-w-lg27-startup-2026-08-31.md) | Exact W filename confirmed; LG27 at 3840×2160/59.997 Hz and internal panel at 60 Hz; monitor hub and LG controls enumerate within about five seconds of boot | One successful startup, not a repair of earlier USB failures, a downstream-mouse test, USB3 throughput or reliability proof |
| [Later USB-only loss on that W boot](../evidence/dev-147-lg27-usb-data-loss-2026-08-31.md) | Hub/controls disconnect twice; first recovery succeeds, second fails with descriptor/address `-71`; David confirms no changes and both images still working; snapshots retain both native outputs/PD | Active controllers/ports have zero recorded runtime-suspend residency. Missing-child PM is unknown; the built-in usbcore setting mismatch does not establish cause. Mouse test held |
| [LG27 attended reconnect after that loss](../evidence/dev-147-lg27-reconnect-usb-loss-2026-08-31.md) | Video returns; hub/controls enumerate transiently, then fail again about 32 seconds after bus recreation and 15.5 seconds after the restored 4K modeset | Root-only snapshot misses child PM. Video recovery is not USB reliability; cable-warning wording is not a cable diagnosis |
| [One attended reconnect](../evidence/dev-147-usb-reconnect-2026-08-27.md) | Video returned in about five seconds by user report; USB2 hub and LG controls enumerated | One case, not repeated-hotplug reliability |
| [LG27 cable comparison](dev-147-lg27-link-investigation-2026-08-30.md) | LG27 reached 3840×2160/59.997 Hz with the other cable | The rejected cable works on other devices; it is not established as defective |
| [LG27 recovery failure](../evidence/dev-147-crashflag-export-2026-08-31.md) | A later observation confirmed external `crashed=1`; earlier logs retained modes and rejected commits | The writer and initiating loss were not identified; not proof of the PR582 timeout path |
| [PR582 candidate and W comparison](dev-147-w-candidate-comparison-2026-08-31.md) | Candidate had low cached HPD/no modes; return to working drivers restored LG35, then LG27 | W and candidate differ in five archive entries; matched control remains unbooted |
| [LG27 overnight loss and recovery](../evidence/dev-147-lg27-watch-link-loss-2026-08-31.md#addendum--joystick-recovery-and-confirmed-timer-2026-08-31) | Sixteen samples retained the working state; link loss came about 3h59m42s after link-up; a joystick click restored video, partner and PD without a cable change | LG 27UN83A-W has user-confirmed Automatic Standby 4H. Standby is the accepted working explanation; timer-Off validation is parked |

These cases must remain separate. Video, USB data and USB-PD can have different outcomes. The failed candidate's low-HPD startup is not the earlier modes-present/crash-guard failure. A FIFO message also appears during a successful manual disconnect/reconnect; it is not sufficient to identify the initiating cause.

Known PMU, clock and calibration-data firmware diagnostics remain. A previous partner `usb_mode` read caused a kernel WARN; that read was not repeated. There is no clean-firmware claim, general M2 support claim, sustained monitor-only charging result, or validated suspend/cold-start/repeated-hotplug result. Recent working module notes do not independently identify every byte of the selected initramfs. Default-on installation and kernel-update handling remain out of scope.

## Narrow diagnostic proposal

[Omarchy Mac PR #289](https://github.com/omarchy-mac/omarchy-mac/pull/289), checked open at head `273e93970635e9f2bfeaec47185f93bb1b696d17`, already owns the diagnostic/documentation work. Its [partner-absence branch](https://github.com/haripako/omarchy-mac/blob/273e93970635e9f2bfeaec47185f93bb1b696d17/bin/omarchy-debug-dp-altmode#L88) infers that no cable is plugged in. Our unchanged-cable observation supports a narrower statement: no USB-C partner was detected; check cable connection and monitor power/standby.

The [prepared patch](../../dev/apple-dp-altmode/contributions/pr289-partner-absence.patch) changes one output line to two neutral lines and adds one three-case fixture test. It does not diagnose a timer from sysfs, detect physical insertion, or enable DisplayPort. The real command fails the new absent-partner assertion before the change and passes after it. Connected-port and wrong-port outputs remain byte-identical. All fixture paths are private; this is not a hardware test. The [preparation evidence](../evidence/dev-147-contribution-and-w-handoff-2026-08-31.md) owns source pins, QA and handoff limits.

Before sending: ask the recipient whether materially AI-assisted reports/patches are accepted, confirm contribution terms, and coordinate with PR #289 rather than opening duplicate enablement work. The next local action and submission authority belong to the [living plan](../plans/dev-147-m2-displayport.md#fork-integration-and-upstream-contribution).
