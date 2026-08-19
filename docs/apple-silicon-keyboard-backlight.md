# Apple Silicon keyboard backlight

This documents the keyboard backlight behavior diagnosed on an Apple M2
MacBook Air 13-inch (2022, J413) running Omarchy Mac with the `linux-asahi`
7.1.6 kernel.

## Symptom and diagnosis

The keyboard started completely dark and the desktop offered no obvious
keyboard-backlight control. This looked like missing hardware support, but the
kernel device was already present:

```text
/sys/class/leds/kbd_backlight
```

It reported a maximum brightness of 255, and `omarchy-brightness-keyboard`
could change it successfully. The initial brightness was simply zero. No
kernel, firmware, or initramfs repair was needed for this case.

The M2 MacBook Air has no dedicated keyboard-backlight keys. Its F1/F2 keys
emit display-brightness media events, so this fork maps:

- **Shift+F1** — keyboard backlight down
- **Shift+F2** — keyboard backlight up

Those bindings are in `default/hypr/bindings/media.lua`. The installer writes
`options hid_apple fnmode=1` to `/etc/modprobe.d/hid_apple.conf`, making the top
row act as media keys without Fn. This is required for plain F1/F2 to control
the display and Shift+F1/F2 to reach the keyboard-backlight bindings.

## Settings panel

Open **Setup > Keyboard > Backlight…** in the Omarchy menu. The entry appears
only when a `*kbd_backlight*` LED exists. The panel reads the current percentage
and offers a 0–100% slider; changes are applied when the slider is released.
It can also be opened directly:

```bash
omarchy-shell shell summon omarchy.keyboard
```

The first-party plugin lives at `shell/plugins/panels/keyboard/`. The same
Keyboard submenu also exposes the existing Input config and Keybindings
editors; their original Setup menu entries remain available.

## Diagnostics

Confirm that the kernel exposed a keyboard-backlight LED:

```bash
find /sys/class/leds -maxdepth 1 -name '*kbd_backlight*' -printf '%f\n'
```

Read its raw range and current value:

```bash
device=$(basename /sys/class/leds/*kbd_backlight*)
brightnessctl -d "$device" max
brightnessctl -d "$device" get
```

Confirm the media-key mode and inspect the relevant Hyprland bindings:

```bash
cat /sys/module/hid_apple/parameters/fnmode
cat /etc/modprobe.d/hid_apple.conf
omarchy menu keybindings --print | grep 'Keyboard brightness'
```

An `fnmode` value of `1` is expected. If the LED device is absent, this is not
the zero-brightness case documented here; inspect `dmesg` for `hid_apple` and
verify that the correct Asahi kernel and device tree are booted.

## Direct commands

The helper discovers the first `*kbd_backlight*` LED automatically:

```bash
# Machine-readable integer percentage
omarchy brightness keyboard get

# Set an exact percentage (validated from 0 through 100)
omarchy brightness keyboard set 50

# Existing controls
omarchy brightness keyboard up
omarchy brightness keyboard down
omarchy brightness keyboard cycle
omarchy brightness keyboard off
omarchy brightness keyboard restore
```

Use `--no-osd` before the action when scripting, for example
`omarchy brightness keyboard --no-osd set 50`. The `get` action never displays
an OSD.

For low-level confirmation, the equivalent direct command is:

```bash
brightnessctl -d kbd_backlight set 50%
```

## Asahi support status

Asahi's M2 feature matrix lists keyboard-backlight support for the 13-inch M2
MacBook Air as available since kernel 6.4. See the upstream
[M2 Series Feature Support](https://github.com/AsahiLinux/docs/blob/main/docs/platform/feature-support/m2.md)
page for the current per-model status.
