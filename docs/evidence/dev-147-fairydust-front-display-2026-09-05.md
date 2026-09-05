# Front-port display: reconnect succeeds, boot detection fails

On the first `7.1.12-dev147-fairydust1` boot, David reports that the monitor was connected throughout on the lower/front USB-C port. It showed no image after boot. Reconnecting the cable produced an image. This corrects any inference that the first-boot `disconnected` DRM status meant the cable was physically absent.

The [same-boot snapshot](dev-147-fairydust-front-display-2026-09-05.json) records the kernel evidence. External DCP booted at about 5.359 seconds, then reported `connected:0`. The first logged DPTX connect appears at about 1403.439 seconds after logged disconnect activity. Firmware services appear, HPD reports connected with 16 modes, and modesetting selects 3840×2160 at nominal 60 Hz. Firmware later labels this 59 Hz. Current `card2-DP-1` reports connected/enabled; the internal panel remains connected/enabled. David confirms the visible image.

This is one successful reconnect observation and one failure to detect an already attached display at boot. It does not establish repeated reconnect reliability, the other port, audio, USB data, charging, suspend or Thunderbolt/USB4 tunneling. Physical front-port naming comes from David; firmware `port=0` is not assumed to map directly to the physical connector.

The evidence narrows the failure to establishing the display connection at startup, before a successful hot-plug transition. It does not identify the cause. Type-C state replay, mux/PHY readiness and DCP initialization order remain hypotheses. Early crossbar deferral messages are not proof of causation. Firmware also logs a clock-frequency warning during the successful modeset; do not treat the image as a warning-free result.

Next, preserve this working baseline and test controlled reconnects before changing code. Track boot-time attached-display detection as a separate open defect. Do not read the Type-C partner `usb_mode` attribute; prior work records that it can trigger a kernel warning.
