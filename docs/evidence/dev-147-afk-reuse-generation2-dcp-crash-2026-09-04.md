# DEV-147 AFK reuse generation-2 DCP crash evidence

**Date:** 2026-09-04
**Host / scope:** `omarchy-air`, one attended LG27 reconnect on the non-default AFK reuse candidate
**Approval:** David authorized the attended generations 2 through 10 gate
**Kernel:** `7.1.6-1-1-ARCH`
**Boot ID:** `d91d49a5-025e-43f6-9bb4-72ec84622e64`
**AppleDRM build ID:** `1ca52ad1cea00559d5fdfd32177e4d1e694994e1`

## Provenance

The attended gate transcript is:

- path: `/home/david/.codex/attachments/14963024-b5ac-4456-af07-a17ee6b43365/pasted-text.txt`;
- SHA-256: `6c97634a3d8295d13c96086071f7499fe7a6d036a1c9ad9d86faeab0c9752ff7`;
- relevant lines: 995 through 1216.

Those lines contain the second gate start, generation-2 tokens, automatic state, 38-event trace, kernel journal, AFK channels, and final `HOLD`. Lines 855 through 993 retain the first no-generation timeout. The commands below ran later on the same boot and before any reboot. This document is their normalized durable receipt.

## What happened

Generation 1 passed on this fresh candidate boot. LG27 showed an image at its native 3840×2160 mode. The internal display and Linux were healthy. Endpoint `0x28` announced `DCPDP13Service` on channels 1 and 3.

The first generations 2 through 10 gate run timed out while it waited for the generation-2 disconnect token. It performed no cable generation. Its final state still had the generation-1 image, two AFK services, and zero AFK capacity or announcement errors.

The second gate run performed exactly generation 2. David disconnected LG27 once, the gate verified the complete disconnected state and enforced its five-second wait, and David reconnected the same cable to the same port. The disconnect-to-reconnect sequence took 35.8 seconds. David supplied the physical blank token. The internal display stayed healthy, and Linux stayed responsive.

The loss-free TIPD trace retained 38 of 38 events. Twenty-four events were attributable to controller `0-003f`. The loss counters were zero. The reconnect completed these stages:

1. Type-C partner and host data role
2. DisplayPort pin assignment C
3. HPD
4. The xHCI child below `/sys/devices/platform/soc/502280000.usb`
5. DPTX connection
6. `DCPDP13Service` announcements on channels 5 and 7

This run did not fail in Type-C or AFK service allocation. It reached the display pipeline and then failed to enable the external output.

## Display failure boundary

DRM reported `DP-1` as connected and disabled. It reported `eDP-1` as connected and enabled. The external connector retained an EDID, 16 modes, and assignment to CRTC 58. Its link status was `Bad`, and DPMS was `Off`.

The Hyprland log contains exactly 80 failed atomic `TEST_ONLY` operations with `EINVAL`. It also contains one failed real `PAGE_FLIP` commit with `EINVAL`. The failures started after the generation-2 reconnect and prevented the compositor from enabling the external output.

During disconnect, DCP reported swallowed swap ID 733 twice. The two records were for power state and timings. The retained journal has no `dcp_poweroff() done` record and no `DCP has crashed` log.

## Same-boot read-only receipts

The bounded compositor state read was:

```bash
/usr/bin/timeout --kill-after=2s 10s /usr/bin/hyprctl monitors all -j | /usr/bin/jq -c '.[] | {name,description,width,height,disabled}'
```

Its exact compact output was:

```text
{"name":"eDP-1","description":"","width":2560,"height":1664,"disabled":false}
{"name":"DP-1","description":"LG Electronics LG HDR 4K 0x00065802","width":0,"height":0,"disabled":false}
```

The bounded DRM state read was:

```bash
/usr/bin/timeout --kill-after=2s 10s /usr/bin/modetest -M apple -c -p
```

Its relevant values were:

```text
connector=60 name=DP-1 status=connected modes=16 encoder=0
DPMS=3 link-status=1
CRTC=58 fb=0 size=0x0
```

The Hyprland log was `/run/user/1001/hypr/5c9377c15f85c50648f35ca5a213754f95b93ca0_1788523186_569531777/hyprland.log`. This bounded exact-pattern count ran:

```bash
/usr/bin/timeout --kill-after=2s 10s /usr/bin/awk '/failed to commit: Invalid argument, flags: ATOMIC_ALLOW_MODESET ATOMIC_TEST_ONLY / { test_only++ } /failed to commit: Invalid argument, flags: ATOMIC_ALLOW_MODESET PAGE_FLIP_EVENT / { page_flip++ } END { printf "test_only_einval=%d page_flip_einval=%d\n", test_only, page_flip }' /run/user/1001/hypr/5c9377c15f85c50648f35ca5a213754f95b93ca0_1788523186_569531777/hyprland.log
```

Its exact output was:

```text
test_only_einval=80 page_flip_einval=1
```

The bounded exact-predicate kernel count ran:

```bash
/usr/bin/timeout --kill-after=2s 10s /usr/bin/bash -c '/usr/bin/journalctl -b --no-pager -o cat | /usr/bin/awk '\''/swallowed swap ID 733/ { swallowed++ } /dcp_poweroff\(\) done/ { poweroff_done++ } /DCP has crashed/ { crash_log++ } END { printf "swallowed_swap_733=%d dcp_poweroff_done=%d dcp_crash_log=%d\n", swallowed, poweroff_done, crash_log }'\'''
```

Its exact output was:

```text
swallowed_swap_733=2 dcp_poweroff_done=0 dcp_crash_log=0
```

The current boot-bound crash-flag probe then observed:

- external connector type `10`;
- `crashed=1`;
- one probe hit and zero misses;
- zero trace-loss counters;
- no probe failure;
- no cleanup failure.

The first protected crash-probe wrapper used an unsupported GNU `cp --preserve=none` option. It refused before the helper or trace ran and cleaned its transaction. The corrected wrapper used `install`, authenticated the protected helper, and produced the observation above. Neither wrapper changed the boot, display mode, cable, or module.

## Result

The current boot has the permanent atomic-rejection mechanism set for its external DCP connector. This explains the repeated `EINVAL` results and why the compositor cannot enable `DP-1` on this boot.

The evidence does not identify the exact write that set the crash flag. The strongest writer candidate is the earlier 50 ms clear-swap timeout in the DCP power-off path. The disconnect swallowed the expected swap twice, the completion log is absent, and the loaded AFK candidate still uses the pre-PR582 timeout semantics. The onset and writer were not traced directly.

The loaded AFK reuse candidate omitted the [PR582 timeout change](../../dev/apple-dp-altmode/pr582/pr582-upstream.patch). Its AFK reuse implementation reached new channels 5 and 7. This result does not establish that AFK reuse caused the DCP crash.

The generations 2 through 10 gate is consumed with `HOLD` at generation 2. It is not a pass. Do not perform another cable cycle on this latched boot.

## Saved evidence

The root evidence was exported without changing `/run`:

- archive: `/home/david/o/.dev147-stage/crashflag-export-current-20260904.YqKydE77sE/capture.tar`;
- size: 40,960 bytes;
- SHA-256: `862a7bae63a97292db46fa01dc34f05704fb98c6b112ac1dbc73a0777b016609`;
- export exit: `0`.

The archive contains 14 regular JSON records. Its result records the observation and exact owned cleanup operations.

## Rollback

No boot or system file changed during the generation gate, probe, or export. No rollback action ran.

Keep the current internal-only system state. Reboot only after the exact-source combined AFK reuse and PR582 candidate is built, staged as a separate non-default image, and reviewed.

## Open

Build one exact-source candidate that combines the accepted AFK reuse patch with the PR582 timeout semantics. Run offline RED/GREEN lifecycle, build, ABI, and image-delta gates. After review and staging, start a fresh attended boot and restart the ten-generation acceptance from generation 1.
