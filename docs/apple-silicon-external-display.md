# Apple Silicon external display prototype

> Public source archive: do not run these public helpers on a live machine. The machine UUIDs and sandbox paths use deliberately invalid `LOCAL_ONLY_*` placeholders. The operational, machine-pinned originals remain private. The edited public copies are not byte-identical to the helpers used in the historical tests. See the [export boundary and draft source](../dev/apple-dp-altmode/usbdiag/README.md).

> [!WARNING]
> This DEV-147 prototype remains experimental work in progress. All candidate boots are on safety HOLD after an unattended, monitor-powered candidate session lost net external charging, reached 2%, entered `s2idle`, and was followed by an unclean next boot on 2026-08-29. MagSafe had been disconnected. The exact monitor/PD interruption cause is unresolved. Native external video and one reconnect worked earlier, but power safety, automatic USB enumeration, reliability, full rollback, and permanent installation are not proved. Keep the default stock-core boot and MagSafe charging. Do not use a candidate on this or another machine.

Reconciled: 2026-08-29, after the immutable [battery-depletion incident](evidence/dev-147-battery-depletion-2026-08-29.md) and its later [physical-power and safety addendum](evidence/dev-147-battery-depletion-addendum-2026-08-29.md). The [living execution plan](plans/dev-147-m2-displayport.md) supersedes this guide's former gate/status instructions. Read it before any next action. The [visible recovery card](plans/dev-147-visible-recovery-card.md) has passed offline documentation and safety review; do not use it until the exact committed card and pinned guide are available outside Linux and the normal-shutdown stock-selection and Recovery-access rehearsals are complete. The [dated history](evidence/dev-147-prototype-history-2026-08-27.md) preserves the earlier attempts, holds, corrections, and display success. The old “output is not confirmed” checkpoint remains on the retained private branch at `8db5ef5b` and in the original private issue history; it described the pre-Gate-3 state.

## Target and containment

The prototype targets one configuration:

- Apple MacBook Air M2 J413 with T8112.
- `linux-asahi` kernel `7.1.6-1-1-ARCH`.
- The front/lower left USB-C port, controller `0-003f` / `usb-pd@3f`.

The upper/back port is `0-0038` / `usb-pd@38`. It has no DisplayPort route in this prototype. MagSafe is Type-C partner `0-003a`.

The minimal candidate enables the M2 video route and generic CD321x hotplug forwarding. It excludes the full fairydust kernel, suspend always-on, SIO, audio, and `appledrm` changes. The packaged kernel module, stock initramfs, GRUB configuration, and `update-m1n1` configuration remain protected.

The public [build-helper archive](../bin/omarchy-dev-dp-altmode) and [pinned patch files](../dev/apple-dp-altmode/) retain the original build method. The private helper created artifacts and non-executable gate scripts, not an installation. Its preconditions require a stock starting state and an empty persistent output directory. Do not rerun it on the active prototype or regenerate the existing stage. The old `/tmp` source/cache command is historical; those paths did not survive reboot. This feature helper must not be assumed to exist in the live Omarchy command set.

## Completed gates and next work

Gates 0–3 have reached the states recorded in the plan. Do not replay them. In particular, do not repeat the live module swap after the successful image.

The corrected Gate 3 rule was to unplug MagSafe AND every USB-C cable before the swap, then attach only the front/lower monitor at the patched-core prompt. The first invocation stopped at that guard before changing a driver. One later swap succeeded. Keep this distinction when reading earlier notes.

Gate 4a is complete: David's reviewed helper staged `/boot/initramfs-linux-asahi-dpalt.img` and reached final PASS after protected post-checks and image verification. He then selected it through the one-time GRUB edit and rebooted. The candidate build ID, early startup log, native display states, and his physical-image confirmation establish display startup success. Independent checks confirmed the staged file's unchanged size and private permissions; the agent did not re-read root-only contents or logs. Keep the [staging checkpoint](evidence/dev-147-one-boot-staging-2026-08-27.md) and [new startup evidence](evidence/dev-147-one-boot-startup-2026-08-27.md). Do not rerun staging.

The module set differs only in the intended Type-C core, but the whole image also contains recorded configuration, OpenSSL, and permission differences. The [preparation evidence](evidence/dev-147-one-boot-preparation-2026-08-27.md) retains the build, differences, warnings, and five remaining aggregate test failures. One successful startup does not clear those qualifications.

[Gate 4b](plans/dev-147-m2-displayport.md#gate-4b--user-selected-one-time-startup-test) remains partial. The monitor's USB hub and LG controls did not enumerate at startup. The completed [USB-1 reconnect](evidence/dev-147-usb-reconnect-2026-08-27.md) restored them and both native displays. David reports an external image after about 5 seconds and an internal screen that stayed usable. Automatic USB enumeration at attached startup remains unproved. An earlier stock-driver boot also began with only root hubs, so a candidate-specific regression is not established.

The reconnect log retains one unplug-time FIFO error and the known firmware diagnostics; no new kernel WARN or fatal-pattern/USB-error match was found in that window. Our earlier partner `usb_mode` read triggered a separate WARN; do not repeat that status read or USB-1. The [dated USB startup investigation](research/dev-147-usb-startup-2026-08-28.md) is complete. It found a stock USB-glue first-probe ordering defect, but did not prove its hardware effect or test a fix.

Historical D1 checkpoint: the [one-boot diagnostic plan](plans/dev-147-usb-startup-diagnostic.md) passed design review, and its offline trace, archive, and assembly suites passed. Later D2/C3 staging and D3/E/W boot records supersede that checkpoint. Their handoffs are consumed. The battery incident now pauses all T1 and candidate work. No staging helper, image selection, build, or offline continuation is currently next or authorized.

The working DP image, stock files, and private operational helpers stay unchanged. Adding the missing DWC3 glue can change startup timing, so this is an observation experiment, not a matched A/B test. Staging and an attended startup remain separately gated. Do not start mode, repeated hotplug, or suspend tests. Full rollback and permanent integration remain later work. A normal unedited boot selects the stock driver, not the original DTB. Do not repeat the live swap.

## Rollback and offline macOS recovery

The [plan's rollback gate](plans/dev-147-m2-displayport.md#gate-6--prove-full-rollback-then-retain-the-evidence) has the exact Linux commands and proof requirements. A normal reboot restores the stock driver, not the original DTB. Reboot after the DTB rollback script only when it reports PASS. Keep both timestamped backups and all evidence; cleanup needs separate approval.

Normal macOS Terminal or Recovery Terminal can use the saved EFI bundle if Linux cannot boot. Follow the offline recovery guide (retained privately). Gate 2 copied and verified that guide and its restore script beside the stock backup on `EFI - OMARC`. They need no Linux filesystem, editor, or network.

The helper defaults to `--check`. Explicit `--restore` requires root and verifies the partition identity and stock backup. It syncs and verifies a temporary stock copy before renaming it, and never reboots. Follow the guide's mount/unmount sequence and restart only after RESTORE PASS and successful unmount. Rename and sync reduce risk; FAT is not power-loss-proof.

David attested that macOS boots and Recovery is available, and chose not to rehearse recovery. Static checks and EFI integrity passed. The helper's actual macOS execution remains untested.
