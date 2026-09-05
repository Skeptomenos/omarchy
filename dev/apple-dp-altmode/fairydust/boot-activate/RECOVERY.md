# Recover the previous boot stack

This guide belongs to the experimental `7.1.12-dev147-fairydust1` activation. Keep it available in macOS before testing the candidate. The activation command copies this guide and a verified old boot bundle to the EFI partition before it changes selected boot files.

The old bundle must be restored before selecting the old kernel. m1n1 prepares the device tree before GRUB starts. Restoring a file while GRUB is already running does not replace the device tree in memory: fully restart after restoring the bundle.

## From working Linux

Run the reviewed restore launcher as the normal user:

```bash
bash /home/david/Work/omarchy-dev147-fairydust-build/dev/apple-dp-altmode/fairydust/boot-activate/restore.sh
```

It asks for sudo, restores and verifies the old EFI bundle first, then restores the original GRUB configuration. It retains the staged candidate and recovery evidence. It does not reboot. Read its result before restarting.

A killed helper can leave `/var/lib/pacman/db.lck` behind. Restore refuses an existing lock. Verify that no package operation or helper is still running before reviewing any stale-lock removal. The macOS restore below does not use this lock. The offline tests simulate failed file replacements; they do not simulate power loss.

## From macOS

Shut down, then hold the power button to open startup options. Choose the installed macOS system and open Terminal. Recovery Terminal is an alternative if the preflight below passes there. Its tools have not been tested on this machine.

The EFI partition is identified by GPT UUID `190f2e7d-4e97-4f75-975b-8bd6aa85174f`. Do not substitute a Linux partition number or assume a macOS disk number. diskutil accepts the GPT UUID directly. [Apple diskutil manual](https://keith.github.io/xcode-man-pages/diskutil.8.html), [Apple startup and Recovery guide](https://support.apple.com/en-lamr/guide/mac-help/mchl82829c17/26/mac/26).

First paste this whole read-only preflight. It checks the partition identity and tools without mounting or changing a volume. Success prints `READ-ONLY PREFLIGHT PASS`.

```sh
(
  set -eu
  for tool in /usr/sbin/diskutil /usr/bin/plutil /usr/bin/shasum /usr/bin/tr /usr/bin/id /usr/bin/mktemp /bin/cp /bin/mv /bin/sync; do
    [ -x "$tool" ] || exit 1
  done
  partuuid=190f2e7d-4e97-4f75-975b-8bd6aa85174f
  actual=$(/usr/sbin/diskutil info -plist "$partuuid" | /usr/bin/plutil -extract DiskUUID raw -expect string -o - -)
  actual=$(printf '%s' "$actual" | /usr/bin/tr 'A-F' 'a-f')
  [ "$actual" = "$partuuid" ]
  digest=$(printf abc | /usr/bin/shasum -a 256)
  [ "${digest%% *}" = ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad ]
  /usr/sbin/diskutil info "$partuuid"
  printf '%s\n' 'READ-ONLY PREFLIGHT PASS'
)
```

Apple documents `shasum -a 256` on macOS. The preflight also tests its runtime dependencies. The plist extraction requires macOS 12 or later. If these checks fail in Recovery, use installed macOS. [Apple checksum instructions](https://support.apple.com/en-qa/guide/business/axm8e397e77d/web), [Apple plutil manual](https://keith.github.io/xcode-man-pages/plutil.1.html).

In installed macOS, enter a root shell with `sudo /bin/sh`. Recovery Terminal normally already runs as root; the restore block checks this. Paste the complete block below. It requires the backup that the activation command created at `/m1n1/dev147-recovery/boot.bin.old-203ab702` on the EFI partition.

```sh
(
  set -eu
  [ "$(/usr/bin/id -u)" = 0 ]
  partuuid=190f2e7d-4e97-4f75-975b-8bd6aa85174f
  oldhash=203ab7027536c8d16f373d02c1f6346a5c34cfe095a9dafd0cfe37d2b354090c
  actual=$(/usr/sbin/diskutil info -plist "$partuuid" | /usr/bin/plutil -extract DiskUUID raw -expect string -o - -)
  actual=$(printf '%s' "$actual" | /usr/bin/tr 'A-F' 'a-f')
  [ "$actual" = "$partuuid" ]
  /usr/sbin/diskutil mount "$partuuid"
  esp=$(/usr/sbin/diskutil info -plist "$partuuid" | /usr/bin/plutil -extract MountPoint raw -expect string -o - -)
  [ -n "$esp" ]
  [ "$esp" != / ]
  [ -d "$esp/m1n1" ]
  mounted=$(/usr/sbin/diskutil info -plist "$esp" | /usr/bin/plutil -extract DiskUUID raw -expect string -o - -)
  mounted=$(printf '%s' "$mounted" | /usr/bin/tr 'A-F' 'a-f')
  [ "$mounted" = "$partuuid" ]
  backup="$esp/m1n1/dev147-recovery/boot.bin.old-203ab702"
  [ -f "$backup" ]
  [ ! -L "$backup" ]
  digest=$(/usr/bin/shasum -a 256 "$backup")
  [ "${digest%% *}" = "$oldhash" ]
  [ ! -d "$esp/m1n1/boot.bin" ]
  [ ! -L "$esp/m1n1/boot.bin" ]
  temp=$(/usr/bin/mktemp "$esp/m1n1/boot.bin.restore.XXXXXX")
  /bin/cp "$backup" "$temp"
  digest=$(/usr/bin/shasum -a 256 "$temp")
  [ "${digest%% *}" = "$oldhash" ]
  /bin/sync
  /bin/mv -f "$temp" "$esp/m1n1/boot.bin"
  /bin/sync
  digest=$(/usr/bin/shasum -a 256 "$esp/m1n1/boot.bin")
  [ "${digest%% *}" = "$oldhash" ]
  cd /
  /usr/sbin/diskutil unmount "$partuuid"
  /usr/sbin/diskutil mount readOnly "$partuuid"
  esp=$(/usr/sbin/diskutil info -plist "$partuuid" | /usr/bin/plutil -extract MountPoint raw -expect string -o - -)
  [ -n "$esp" ]
  [ "$esp" != / ]
  digest=$(/usr/bin/shasum -a 256 "$esp/m1n1/boot.bin")
  [ "${digest%% *}" = "$oldhash" ]
  /usr/sbin/diskutil unmount "$partuuid"
  printf '%s\n' 'OLD BOOT.BIN RESTORED AND VERIFIED'
)
```

Success prints `OLD BOOT.BIN RESTORED AND VERIFIED`. Fully restart and choose the Linux installation. The retained GRUB selector recognizes the restored bundle and selects the old kernel. Once Linux works, the Linux restore launcher can also restore the original GRUB configuration.

A failed check stops the procedure. Preserve any temporary file for inspection. Do not use forced unmount or replace the expected hash. The script copies to a unique temporary file, verifies it, renames it, syncs, then verifies after an unmount and read-only remount. This does not guarantee power-loss atomicity on FAT.

## If the GRUB selector still stops

Use this only after the old bundle was restored and the machine fully restarted. At the GRUB command prompt, or after pressing `c` at its menu, load the preserved old configuration:

```text
search --no-floppy --fs-uuid --set=root e24cf117-3c89-4392-a3b8-def187becda8
normal ($root)/boot/grub/dev147-paired-7.1.12-dev147-fairydust1/old.cfg
```

These commands bypass the selector. They do not check the device tree, which is why restoration and a full restart must come first. Do not use them to boot an old kernel under the candidate bundle. Arbitrary damage to ext4 or GRUB itself requires separate Linux recovery; this procedure restores the EFI bundle and uses preserved GRUB files.

## Verification limits

Real GRUB disk-image probes establish selection and configuration behavior. Local shell tests establish guard behavior, including missing backups and directory/symlink targets. The macOS/Recovery commands and an actual recovery boot have not been executed on this machine. The activation plan records these hardware and recovery acceptance steps separately.
