# Fairydust first boot — 2026-09-05

The candidate boots to the user session. `uname -r` returns `7.1.12-dev147-fairydust1`; `/proc/cmdline` names its staged Image. The [read-only snapshot](dev-147-fairydust-first-boot-2026-09-05.json) records this boot and the observed initialization state.

- SIO is enabled in the live device tree, contains `apple,sio-firmware-params`, binds `apple-sio` and reports protocol v9.
- Both DCP nodes are enabled, report firmware version/compatibility 13.5.0 and bind `apple-dcp`. Both log `DCP booted`.
- The display-audio controller binds `dcp-dp-audio`. This is not an audio playback test.
- `card2-eDP-1` reports connected/enabled. `card2-DP-1` reports disconnected/disabled.
- The sampled boot log has no `BUG:`, `Oops:`, `Call trace:` or `Direct firmware load` match. This is a bounded log check, not a claim that the boot is warning-free.

Boot warnings include repeated DCP `dp-xbar: -517` messages before the eventual successful binding, tas2764 device-tree/regulator messages, keyboard-backlight period fallback, RTKit oslog messages and Wi-Fi P2P errors. Their presence alone does not establish a regression; no old-kernel comparison or playback/backlight acceptance was performed here. Track audio and keyboard-backlight behavior during acceptance. The later DCP boot and connector registration show that the early crossbar messages did not prevent display-controller initialization.

No cable, suspend, sound playback or system configuration action was performed by the agent. External display, repeated reconnects, USB data, charging, audio, both ports/orientations and suspend remain open. Next, connect one known-working display cable and report the port used and whether the monitor shows an image. Capture the resulting connector state and logs before repeated reconnect testing.
