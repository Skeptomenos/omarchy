# DEV-147 live format-2 preparation — 2026-09-02

**Result:** PASS
**Boot:** `fa500274-a4fd-49e3-a84a-82ec4948b8e3`

David ran the accepted `b45948e12` integration script through a clean
privileged environment. It used the sealed bundle at
`/home/david/o/.dev147-stage/dev147-optin-bundle-final.iQVkvWr13p/bundle` and
reported:

```text
PREPARATION PASS: /boot/initramfs-linux-asahi-m2-displayport.img
```

The format-2 transaction verifies the 16-field state and the root-owned
mode-0700 rollback runner before it publishes the root-private `active`
directory. Normal-user access stops at the mode-0700 state parent, as designed.

The post-preparation read-only check found:

- active `boot.bin` still has accepted SHA-256
  `203ab7027536c8d16f373d02c1f6346a5c34cfe095a9dafd0cfe37d2b354090c`;
- the candidate image is root-owned, mode 0600, and 19,184,210 bytes;
- the package guard is root-owned, mode 0644, 303 bytes, and has accepted
  SHA-256 `469820ad7cfd015a22cff979b0aa70d62e82dcc7cc05951dca92f40cd660f2bd`;
- the new EFI recovery guide is
  `RECOVERY-OMARCHY-M2-DISPLAYPORT-20260902T085339Z.txt`;
- neither external USB-C controller has a partner;
- MagSafe is online, the battery is Full at 100 percent, no systemd unit
  failed, no package lock exists, and no package or initramfs job runs.

The active boot already matches the candidate. Activation should therefore
verify the complete release and change only the transaction phase. Do not
reconnect USB-C or reboot before that gate reports PASS.
