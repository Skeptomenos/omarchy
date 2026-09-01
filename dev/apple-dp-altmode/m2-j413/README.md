# M2 J413 external DisplayPort experiment

This module stages one reversible external DisplayPort candidate for the M2
MacBook Air `apple,j413` / `apple,t8112`.

The current release is experimental. It supports only `linux-asahi
7.1.6-1-1-ARCH` and the lower/front left USB-C port. Attached-display suspend
is unsafe. Disconnect the external display before suspend. Monitor USB data is
outside this module's scope.

The accepted prototype produced native video on an LG 27UN83A-W and an LG 35
ultrawide. Attached startup, attach after login, and one hot reconnect passed.
The integrated candidate still needs its own boot test.

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
GRUB, or its saved default. An ordinary reboot after preparation uses the
unchanged stock boot chain.

If preparation ends without `PREPARATION PASS`, stop. Do not retry or reboot.
Retain the reported staging evidence for review. An interrupted preparation can
leave an inactive candidate image or package guard, while the active boot file
stays unchanged.

Run activation only when you are ready for an attended reboot:

```bash
sudo /usr/bin/bash dev/apple-dp-altmode/m2-j413/integration.sh activate
```

Activation replaces `/boot/efi/m1n1/boot.bin` with the reviewed candidate when
the stock copy is active. If the candidate was already active, activation
verifies it and changes no boot bytes. Reboot immediately. Select the paired
initramfs for one boot by editing the existing Arch Linux entry in GRUB:

```text
initrd /boot/initramfs-linux-asahi-m2-displayport.img
```

Do not save the GRUB edit. If the edit is missed, the machine uses the
candidate device tree with the default initramfs. That combination passed the
earlier internal-panel safety gate, but it does not provide the target external
display path. Reboot and select the paired image, or roll back.

Rollback works from either the prepared or activated phase. It requires the
same power and cable conditions:

```bash
sudo /usr/bin/bash dev/apple-dp-altmode/m2-j413/integration.sh rollback
```

The rollback returns `boot.bin` to its exact pre-install bytes. It removes the
candidate image and package guard. It retains the EFI backup, recovery guide,
and rollback evidence.

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
Activation changes only `boot.bin`. A pre-transaction pacman hook blocks
changes to `linux-asahi`, `m1n1`, and `uboot-asahi` while the experiment is
active. Run rollback before updating those packages.

Linux rollback uses the root-owned state under
`/var/lib/omarchy/m2-displayport`. A second backup and a macOS Recovery
Terminal guide stay beside `m1n1/boot.bin` on the Linux EFI partition.

## Validation

Run the isolated transaction tests:

```bash
/usr/bin/bash test/shell.d/apple-m2-displayport-integration-test.sh
```

The test covers the exact model and kernel gates, strict release pins,
transactional copies, preparation and activation phases, operation locking,
no-overwrite behavior, preservation of protected files, rollback from both
phases, an already active candidate, and package-hook drift.

The [offline preparation evidence](../../../docs/evidence/dev-147-m2-displayport-optin-preparation-2026-09-01.md)
records the exact reconstruction and checks. The investigation record and
release decision remain in
[DEV-147](https://linear.app/helmus/issue/DEV-147/usb-c-displayport-external-monitor-unavailable-on-m2-macbook-air).
