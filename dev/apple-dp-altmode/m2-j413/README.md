# M2 J413 external DisplayPort experiment

This module stages one reversible external DisplayPort candidate for the M2
MacBook Air `apple,j413` / `apple,t8112`.

The current release is experimental. It supports only kernel
`7.1.6-1-1-ARCH`, package `linux-asahi 7.1.6.asahi1-1`, and the lower/front
left USB-C port.

The integrated candidate passed an internal-only startup, an LG 27UN83A-W
attachment at 3840×2160/59.997 Hz, and one same-boot hot switch to an LG 35
ultrawide at 3440×1440/99.982 Hz. The built-in panel stayed normal and Linux
stayed responsive.

Attached-display suspend is unsupported. Disconnect the external display before
suspend. A hot switch can leave the exported EDID and Hyprland monitor identity
stale even when native video works. Monitor USB hub and data behavior is outside
this module's scope and remains tracked in
[DEV-163](https://linear.app/helmus/issue/DEV-163/lg-monitor-usb-hub-disappears-while-displayport-video-remains-active).

The accepted candidate boot retained an unrelated `disablehooks=encrypt`
argument, so its live result is qualified. That argument is not part of this
feature. Do not add it or copy it from test records.

## Quick start

Prepare a sealed bundle without `sudo`:

```bash
/usr/bin/bash dev/apple-dp-altmode/m2-j413/prepare-bundle.sh \
  --boot /absolute/path/to/boot.bin.dpalt \
  --image /absolute/path/to/initramfs-linux-asahi-dpalt.img \
  --output /absolute/new/path/to/bundle
```

Inspect the bundle and recovery plan. Disconnect all USB-C devices. Keep the
MacBook on external power with at least 50 percent battery. Prepare only after
the candidate and command have been reviewed:

```bash
sudo /usr/bin/bash dev/apple-dp-altmode/m2-j413/integration.sh stage \
  --bundle /absolute/new/path/to/bundle
```

Preparation installs `/boot/initramfs-linux-asahi-m2-displayport.img`, the
package guard, backups, and rollback state. It does not change `boot.bin`,
GRUB, or its saved default. An ordinary reboot after preparation uses the exact
pre-preparation boot chain. That chain can already contain the candidate
`boot.bin`.

If preparation ends without `PREPARATION PASS`, stop. Do not retry or reboot.
Retain the reported staging evidence for review. An interrupted preparation can
leave an inactive candidate image or package guard, while the active boot file
stays unchanged.

Keep every external USB-C device disconnected. Run activation only when you
are ready for an attended reboot:

```bash
sudo /usr/bin/bash dev/apple-dp-altmode/m2-j413/integration.sh activate
```

Activation replaces `/boot/efi/m1n1/boot.bin` with the reviewed candidate when
the stock copy is active. If the candidate was already active, activation
verifies it and changes no boot bytes. Reboot immediately. Select the paired
initramfs for one boot by editing the existing Arch Linux entry in GRUB.
Change only this `initrd` line:

```text
initrd /boot/initramfs-linux-asahi-m2-displayport.img
```

Do not add `disablehooks=encrypt` or change another boot argument. Do not save
the GRUB edit. If the edit is missed, the machine uses the candidate device
tree with the default initramfs. That combination passed the earlier
internal-panel safety gate, but it does not provide the target external display
path. Reboot and select the paired image, or roll back.

Rollback works from either the prepared or activated phase. Disconnect every
external USB-C device. Keep the MacBook on external power with at least 50
percent battery:

```bash
sudo /usr/bin/bash /var/lib/omarchy/m2-displayport/active/rollback.sh rollback
```

The rollback returns `boot.bin` to its exact pre-install bytes. It removes the
candidate image and package guard. It retains the EFI backup, recovery guide,
rollback entrypoint, and rollback evidence. The preserved entrypoint is bound
to its recorded checksum, root ownership, and mode. It does not depend on the
source checkout remaining present or unchanged.

## Environment variables

The scripts accept no environment overrides. The staging command requires a
normal user to invoke it through `sudo`.

## Architecture

```text
reviewed boot.bin + reviewed initramfs
                  |
                  v
        unprivileged preparation
                  |
                  v
       checksummed private bundle
                  |
                  v
       root preparation and gate
          |                 |
          v                 v
 pre-install backups   non-default image
          |                 |
          +-------> package guard
                  |
                  v
        attended boot activation
```

The default initramfs, the accepted W image, the installed kernel module, and
GRUB stay unchanged. Preparation also leaves the active `boot.bin` unchanged.
Activation changes only `boot.bin`.

The candidate is pinned to the exact kernel, module, initramfs, m1n1, and
U-Boot identities that were reviewed. It does not follow package updates. A
pre-transaction pacman hook blocks install, upgrade, or removal of
`linux-asahi`, `m1n1`, and `uboot-asahi` while the experiment is active. Run
rollback before changing any of those packages. Rebuild and revalidate the
candidate before using it with a different kernel or boot-chain package.

Linux rollback uses the root-owned state under
`/var/lib/omarchy/m2-displayport`. A second backup and a macOS Recovery
Terminal guide stay beside `m1n1/boot.bin` on the Linux EFI partition. The
Linux rollback is the normal removal path. The retained EFI backup and Recovery
Terminal guide are the recovery boundary if Linux cannot boot.

## Validation

Run the isolated transaction tests:

```bash
/usr/bin/bash test/shell.d/apple-m2-displayport-integration-test.sh
```

The test covers the exact model and kernel gates, strict release pins,
transactional copies, preparation and activation phases, operation locking,
no-overwrite behavior, preservation of protected files, rollback from both
phases, the checkout-independent rollback entrypoint, an already active
candidate, and package-hook drift.

The [historical offline preparation evidence](../../../docs/evidence/dev-147-m2-displayport-optin-preparation-2026-09-01.md)
records the exact reconstruction and checks. The
[release evidence](../../../docs/evidence/dev-147-m2-displayport-optin-release-2026-09-02.md)
records the accepted live matrix, current limits, and release validation. The
investigation record and release decision remain in
[DEV-147](https://linear.app/helmus/issue/DEV-147/usb-c-displayport-external-monitor-unavailable-on-m2-macbook-air).
