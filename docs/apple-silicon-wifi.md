# Apple Silicon Wi-Fi: missing firmware and authentication timeouts

This documents two separate Wi-Fi failures observed while installing Omarchy
Mac on an Apple M2 MacBook Air running Asahi Alarm. The tested system used the
`linux-asahi` 7.1.6 kernel and a Broadcom BCM4387/7 adapter.

The fixes below are specific to Apple Silicon and `brcmfmac`. Do not apply the
authentication setting indiscriminately to Intel Macs: disabling Broadcom's
firmware supplicant can still be the correct workaround for older adapters.

## Symptoms

The first failure happens immediately after boot:

- NetworkManager has no usable Wi-Fi interface.
- The graphical Wi-Fi control may ask for an administrator password.
- `mkinitcpio -P` succeeds, but its hook list does not contain `asahi`.

After restoring the firmware, a second failure can appear:

- Scanning works and access points are listed.
- Association ends with `Authentication with <BSSID> timed out`.
- NetworkManager asks for the password again even when it is correct.
- The adapter then stops scanning and the kernel repeatedly reports
  `brcmf_msgbuf_query_dcmd: Timeout on response for query command` and scan
  error `-5`.
- Reloading only `brcmfmac` fails with `Module brcmfmac is in use`.

## Cause 1: Omarchy replaces the Asahi initramfs hook list

Asahi places Apple-provided, machine-specific firmware in a vendor-firmware
CPIO. Its `asahi` mkinitcpio hook must load that firmware before `udev` probes
the hardware. Omarchy's `omarchy_hooks.conf` assigns a new `HOOKS` array and
can omit `asahi`, overriding the Asahi distribution default.

Confirm the problem with:

```bash
sudo mkinitcpio -P
```

The generated hook order must contain the following sequence:

```text
[base]
[asahi]
[udev]
```

### Repair an installed system

Create `/etc/mkinitcpio.conf.d/zz-asahi-vendorfw.conf`:

```bash
# Omarchy's hook list replaces the Asahi default. Restore vendor firmware
# before udev without duplicating the hook if Omarchy later adds it itself.
if [[ " ${HOOKS[*]} " != *" asahi "* ]]; then
  HOOKS=(base asahi "${HOOKS[@]:1}")
fi
```

Rebuild the image and reboot:

```bash
sudo mkinitcpio -P
sudo reboot
```

Warnings about `xhci_pci`, unsupported aarch64 microcode, a console font, or
`drm_privacy_screen_register` did not prevent the tested image from booting.
The important results are the `base -> asahi -> udev` order and the final
`Initcpio image generation successful` message.

After reboot, verify that the adapter and vendor firmware loaded:

```bash
nmcli device status
journalctl -b -k --no-pager | grep -E 'brcmfmac|firmware'
```

On the tested BCM4387, the log included `TxCap blob found`, calibration loading,
and a firmware version line.

## Cause 2: the Intel Broadcom workaround breaks BCM4387 authentication

Omarchy's Apple Broadcom workaround writes:

```text
options brcmfmac feature_disable=0x82000
```

The mask disables the firmware supplicant (`FWSUP`, `0x2000`) and firmware
authenticator (`FWAUTH`, `0x80000`). That is useful on some older Broadcom
adapters whose WPA offload is broken. On the tested Apple Silicon BCM4387,
however, the host-side authentication path timed out before the WPA handshake
and left the firmware unresponsive.

Keeping firmware authentication enabled fixed the connection:

```text
# Apple BCM4387: keep firmware authentication enabled. Disabling FWSUP/FWAUTH
# makes association time out and wedges this firmware.
options brcmfmac p2pon=0 roamoff=1 feature_disable=0
```

Save that as `/etc/modprobe.d/brcmfmac.conf`.

### Recover without rebooting

`brcmfmac_wcc` depends on and holds `brcmfmac`, so unload both modules in this
order. `-C /dev/null` deliberately ignores the existing modprobe configuration
during the test load.

```bash
sudo modprobe -r brcmfmac_wcc brcmfmac
sudo modprobe -C /dev/null brcmfmac p2pon=0 roamoff=1 feature_disable=0
sudo modprobe brcmfmac_wcc
nmcli radio wifi on
```

Then connect through NetworkManager without placing the Wi-Fi password in shell
history:

```bash
nmcli device wifi list
nmcli --ask device wifi connect "SSID" ifname "WIFI_INTERFACE"
```

If testing with an iPhone hotspot, enabling **Settings > Personal Hotspot >
Maximize Compatibility** makes it advertise 2.4 GHz with WPA2. This can improve
discoverability, but it does not replace the driver fix.

## Verification

```bash
nmcli -f DEVICE,TYPE,STATE,CONNECTION device status
ip -4 address show dev "WIFI_INTERFACE"
ping -c 2 1.1.1.1
journalctl -b -k --no-pager | grep -E 'brcmf|scan error|Timeout on response'
```

A successful result has a connected Wi-Fi device, a DHCP address, working
network traffic, and no new Broadcom command timeouts.

## Recommended integration in this fork

The permanent fix should have two parts:

1. In `etc/mkinitcpio.conf.d/omarchy_hooks.conf`, add `asahi` immediately after
   `base` when `/usr/lib/initcpio/install/asahi` exists and the hook is not
   already present.
2. In `install/hardware/apple/fix-brcmfmac-supplicant.sh`, distinguish Apple
   Silicon from Intel Macs. Keep `feature_disable=0x82000` only for adapters
   known to need software WPA handling; write the BCM4387 settings above for
   Apple Silicon instead.

This avoids regressing Intel Mac support while making a fresh Apple Silicon
installation boot with its vendor firmware and connect without manual repair.

## References

- [Asahi Linux open OS interoperability: vendor firmware](https://asahilinux.org/docs/platform/open-os-interop/)
- [Linux `brcmfmac` feature detection and `feature_disable`](https://github.com/torvalds/linux/blob/master/drivers/net/wireless/broadcom/brcm80211/brcmfmac/feature.c)
- [Apple Platform Security: Personal Hotspot compatibility](https://support.apple.com/guide/security/secfd166f620/web)
