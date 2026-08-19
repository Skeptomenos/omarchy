# Apple Silicon trackpad: boot race, detection, and the settings panel

This documents a trackpad failure observed while running Omarchy Mac on an
Apple M2 MacBook Air (J413) on Asahi Alarm with the `linux-asahi` 7.1.6
kernel, and the trackpad settings UI added alongside the fix.

## Symptoms

On some boots the trackpad is completely dead for the whole session, while an
external mouse and the internal keyboard keep working:

- The kernel sees the device: `/proc/bus/input/devices` lists
  `Apple MTP multi-touch` with a `mouse`/`event` handler.
- udev tags it correctly (`ID_INPUT_TOUCHPAD=1`).
- `hyprctl devices` does not list it at all.
- The Hyprland log (under `$XDG_RUNTIME_DIR/hypr/*/hyprland.log`) contains,
  from startup:

  ```
  ERR from aquamarine ]: [libseat] [libseat/backend/logind.c:121] Could not take device: No such file or directory
  ERR from aquamarine ]: libseat: Couldn't open device at /dev/input/eventN
  ```

A reboot fixes it — or breaks it again. The failure is a race, so it only
lands on unlucky boots.

## Cause: HID driver rebinding races logind startup

On Apple Silicon the internal keyboard and trackpad are HID devices provided
by `dockchannel-hid`. When they first register, the trackpad binds to the
generic `hid-generic` driver (as a plain mouse). A moment later
`hid_magicmouse` finishes loading and the kernel destroys and re-creates the
device under the proper driver; the keyboard does the same dance with
`hid_apple`.

That churn re-registers the input devices and reshuffles the
`/dev/input/eventN` minor numbers at the same moment udev, systemd-logind,
and the compositor are starting. On unlucky boots logind's `TakeDevice`
answers `ENOENT` for the trackpad node when Hyprland enumerates input
devices, and libinput never retries a failed open unless a new udev event
arrives for the node — so the trackpad stays dead for the session.

## Fix: load the Apple HID drivers from the initramfs

`install/hardware/apple/fix-asahi-hid-race.sh` writes
`/etc/mkinitcpio.conf.d/apple_hid_modules.conf`:

```
MODULES+=(hid_apple hid_magicmouse)
```

With both drivers already registered when `dockchannel-hid` creates its HID
devices, they bind correctly on first registration: no rebind, no device
churn, no race. Apply it to an existing install with:

```
echo 'MODULES+=(hid_apple hid_magicmouse)' | sudo tee /etc/mkinitcpio.conf.d/apple_hid_modules.conf
sudo mkinitcpio -P
```

### Recovering a live session without rebooting

Make udev emit a fresh add event for the node so libinput retries the open:

```
sudo udevadm trigger --action=add /dev/input/eventN
```

Find `eventN` in `/proc/bus/input/devices` under `Apple MTP multi-touch`.

## Detection: the trackpad is named "multi-touch", not "touchpad"

Hyprland names the device after its MTP HID interface —
`apple-mtp-multi-touch`. `omarchy-hw-touchpad` used to match only
`touchpad|trackpad`, so every touchpad-guarded menu entry was hidden on
Apple Silicon. The pattern now also matches `multi-touch`.

## Trackpad settings panel

`omarchy-trackpad-settings` backs a settings UI for the trackpad:

- **Omarchy menu**: Setup > Trackpad — natural scrolling and workspace
  gesture toggles, plus "Sliders…" which summons the panel.
- **Slider panel**: `omarchy-shell shell summon omarchy.trackpad` — draggable
  sliders for scroll speed, pointer speed, and workspace swipe speed, plus
  the two toggles. Scroll and pointer speed apply live while dragging.
- **CLI**: `omarchy trackpad settings get|toggle|set <key> [value]` with keys
  `natural_scroll`, `scroll_factor`, `sensitivity`, `gestures`,
  `swipe_speed`.

Settings persist to `~/.config/hypr/trackpad-ui.lua`, which
`config/hypr/hyprland.lua` requires right after `hypr/input.lua` so the
panel's values override manual input settings. The file is regenerated on
every change — put manual input tweaks in `hypr/input.lua` instead.

## Mac-style gestures

`trackpad-ui.lua` ships with four-finger gestures enabled (Hyprland ≥ 0.55
Lua gestures):

- horizontal swipe: 1:1 workspace switch, like macOS Spaces. The panel's
  "Swipe speed" slider sets the gesture `scale`.
- swipe up: fullscreen the active window.
- swipe down: toggle the `scratchpad` special workspace.

The "Workspace Gestures" toggle removes all three. More gestures (pinch
cursor zoom, three-finger swipes) can be added per user in
`~/.config/hypr/input.lua`; see
<https://wiki.hypr.land/Configuring/Advanced-and-Cool/Gestures/>.
