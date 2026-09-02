# DEV-147 live format-2 activation — 2026-09-02

**Result:** PASS
**Boot:** `fa500274-a4fd-49e3-a84a-82ec4948b8e3`

David ran activation through the preserved root-owned entrypoint:

```text
/var/lib/omarchy/m2-displayport/active/rollback.sh activate
ACTIVATION PASS: /boot/efi/m1n1/boot.bin
```

Before it changes the transaction phase, activation verifies the strict
format-2 state, pre-install and candidate boot copies, root-owned mode-0700
rollback runner and its bound checksum and size, EFI backup, recovery guide,
candidate image, package guard, package lock, live host identity, power, and
external Type-C safety. It then verifies and syncs the active boot bytes.

The public post-activation check found:

- active `boot.bin` still has accepted SHA-256
  `203ab7027536c8d16f373d02c1f6346a5c34cfe095a9dafd0cfe37d2b354090c`;
- the candidate image remains root-owned, mode 0600, and 19,184,210 bytes;
- the package guard retains accepted SHA-256
  `469820ad7cfd015a22cff979b0aa70d62e82dcc7cc05951dca92f40cd660f2bd`;
- the matching EFI recovery guide remains present;
- neither external USB-C controller has a partner;
- the internal output remains enabled at 2560×1664/60 Hz with DPMS on;
- MagSafe is online, the battery is Full at 100 percent, no systemd unit
  failed, no package lock exists, no package or initramfs job runs, and the
  bounded kernel scan found no fatal display pattern.

No reboot is required for the migration itself. The active boot and image are
the exact bytes already validated on both monitors. Format 2 changes the
transaction state and rollback durability, not the running display payload.
