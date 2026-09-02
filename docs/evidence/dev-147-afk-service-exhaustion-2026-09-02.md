# DEV-147 AFK service-slot exhaustion

**Date:** 2026-09-02
**Host:** `omarchy-air`
**Kernel:** `7.1.6-1-1-ARCH`
**Candidate:** `/boot/initramfs-linux-asahi-m2-displayport.img`

## Approval and scope

David attached both tested external monitors after the format-2 state migration. Neither external monitor showed an image. The internal display stayed healthy and Linux stayed responsive. This record uses read-only system state and retained journal data. No driver, boot file, package, or live configuration changed during diagnosis.

## Failed boot

Boot `fa500274-a4fd-49e3-a84a-82ec4948b8e3` accumulated 21 external DPTX connect calls and 26 disconnect calls. Endpoint `0x28` accepted exactly 16 services on channels `1,3,5,7,9,11,13,15,17,19,21,23,25,27,29,31`. Later link generations produced 14 `too many enabled services!` errors and 32 `expected announce` errors. The rejected service channels continued from 33 through 59.

The failure occurred without a new kernel boot, driver reload, or display-payload change after format-2 activation. The migration changed protected transaction state and rollback ownership only. It did not change the running kernel.

The installed Asahi source at commit `e2e1930a9595bffafad92cec2b5504525efb9cd4` explains the limit:

- `drivers/gpu/drm/apple/afk.h` defines `AFK_MAX_CHANNEL` as 16 and stores services in a fixed array.
- `afk_recv_handle_init()` appends with `ep->num_channels++`.
- `afk_recv_handle_teardown()` marks a service torn down.
- Endpoint-specific teardown can disable a service, but generic allocation does not reuse disabled entries or reduce the high-water mark.

This is a bounded runtime service-slot leak. It is not persistent disk damage. A physical connect is not the only trigger. Link resets, retries, monitor switches, and reconnects can each create another generation.

## Recovery and confirmation

David disconnected both external monitors, kept MagSafe connected, rebooted the same candidate with no external display, waited for a healthy internal session, and attached LG27 to the lower/front left USB-C port.

Fresh boot `d930e28c-4a73-4de0-be0b-7bbfae3ceafe` produced:

```text
connect=2 disconnect=2 new_service=2 channels=1,3 too_many=0 expected_announce=0 lg27_modeset=1
```

The kernel completed a native LG27 mode set:

```text
set_digital_out_mode(color:74 timing:45) "3840x2160": 60
set_digital_out_mode finished:8271
```

David confirms that LG27 shows an image, the internal display shows an image, and Linux is responsive. DRM reports both `DP-1` and `eDP-1` connected.

## Result

The reboot reset the endpoint service table and recovered external video. The format-2 migration remains accepted. DEV-147 is not complete because repeated link generations can still exhaust endpoint `0x28` and require a reboot.

## Safety boundary

Do not test repeated physical hot-plug on the accepted image again. First build an offline lifecycle probe and a separate non-default candidate. A safe fix must reuse only disabled service entries. It must preserve late command replies for services that remain enabled after teardown. Suspend remains unsupported, and monitor USB data remains in DEV-163.
