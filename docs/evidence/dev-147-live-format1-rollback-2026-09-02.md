# DEV-147 live format-1 rollback — 2026-09-02

**Result:** PASS
**Boot:** `fa500274-a4fd-49e3-a84a-82ec4948b8e3`

David disconnected every USB-C cable and kept MagSafe connected. He then ran
the exact legacy integration script from detached commit `6dbcc24ad` with a
clean privileged environment. It reported:

```text
ROLLBACK PASS: /var/lib/omarchy/m2-displayport/rolled-back-20260901T215143Z
```

The script SHA-256 was
`6c93c39a97b8e0d42f5f2be262907759713e9718146f40a41e23ab4123c34a17`.

The post-rollback read-only check found:

- `/boot/efi/m1n1/boot.bin` still matches the accepted candidate SHA-256
  `203ab7027536c8d16f373d02c1f6346a5c34cfe095a9dafd0cfe37d2b354090c`;
- `/boot/initramfs-linux-asahi-m2-displayport.img` is absent;
- `/etc/pacman.d/hooks/05-omarchy-m2-displayport-guard.hook` is absent;
- no partner exists on the two external USB-C controllers at `0-0038` and
  `0-003f`;
- the remaining `port0-partner` resolves through `0-003a`, the MagSafe path
  that the integration safety check intentionally excludes;
- external power is online, the battery is Full at 100 percent, no systemd
  unit failed, no package lock exists, and no package or initramfs job runs.

The running kernel already loaded the removed image into memory. Do not reboot
before the reviewed format-2 preparation restores the accepted image path.
