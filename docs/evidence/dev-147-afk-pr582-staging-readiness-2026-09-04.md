# DEV-147 combined AFK reuse plus PR582 staging readiness

Date: 2026-09-04

Status: PASS. The publisher implementation, 26-test gate, independent functional QA, and final adversarial security review pass. The destination remains absent. A separate manual staging handoff is next. Sudo, staging, reboot, and cable actions remain held until that handoff. Nothing was written to `/boot` or `/var`, and no live driver, boot, display, cable, or recovery state changed.

## Scope

This slice creates a new publisher and literal authenticated root handoff for the combined AFK reuse plus PR582 image. It does not alter the accepted AFK-only publisher or any prior artifact. The publisher can create only `/boot/initramfs-linux-asahi-m2-displayport-afk-pr582.img`, and it refuses if that path already exists.

Input artifact:

- Path: `/home/david/o/.dev147-stage/afk-pr582-combined-offline-20260904.hdfiJZaOUn/image-build/initramfs-linux-asahi-m2-displayport-afk-pr582.img`
- Size: 21,599,177 bytes
- SHA-256: `3207dd0ff346765f4514b34a137c1c7456c459082463355e51047216dedc2867`
- Current public metadata: owner/group `1001:1001`, mode `0600`, one link

Publisher artifacts:

- `dev/apple-dp-altmode/afk-service-reuse-pr582/stage-image.py`: 36,672 bytes, SHA-256 `7b14544aacee7a88ca164de7c0a6b2cd901dd1f791752c18af41e3e3eea8939d`
- `dev/apple-dp-altmode/afk-service-reuse-pr582/stage-image-bootstrap.txt`: 52,855 bytes, SHA-256 `668f123098252bfd849d66630ec8ec08a808cc9a70d6a9a3520c07cbd55177c5`
- `dev/apple-dp-altmode/afk-service-reuse-pr582/test-stage-image.py`: 42,206 bytes, SHA-256 `5bdf48b6f6ae670162e37f1977be02e7ace80a5ee26cc0af2240c4fe4d3809f9`

## Protected baseline

The publisher checks these exact accepted bytes, sizes, owners, groups, and modes before the copy, after the copy, and after publication:

| Path | SHA-256 | Bytes | Metadata |
|---|---|---:|---|
| `/boot/efi/m1n1/boot.bin` | `203ab7027536c8d16f373d02c1f6346a5c34cfe095a9dafd0cfe37d2b354090c` | 6,205,569 | `0:0 0755` |
| `/boot/initramfs-linux-asahi.img` | `c4cffb397cfbd0158d3b1423c0512e1622053d53e0c75a17f5312986276324e0` | 18,865,707 | `0:0 0600` |
| `/boot/grub/grub.cfg` | `57d839b9bc7d3488402a8cf7c9e45328dc0097731fc395b0514c467d06b7a327` | 4,129 | `0:0 0600` |
| `/boot/initramfs-linux-asahi-m2-displayport.img` | `a93dd0c1b3a6c4d81bf76f2f43c7c7a2b8b7e1e0306bc487de018667f9c8c196` | 19,184,210 | `0:0 0600` |
| `/boot/initramfs-linux-asahi-m2-displayport-afk-reuse.img` | `ebd383c21a35d6b0eff22ffe6f144ea7790c31d7cf058a1c3afa5e39c2375acd` | 21,598,988 | `0:0 0600` |
| `/etc/pacman.d/hooks/05-omarchy-m2-displayport-guard.hook` | `469820ad7cfd015a22cff979b0aa70d62e82dcc7cc05951dca92f40cd660f2bd` | 303 | `0:0 0644` |
| `/var/lib/omarchy/m2-displayport/active/rollback.sh` | `3357ac75cd7a7d330d2c751bf819e342758491d71e3b34234afacf2f83264e19` | 42,138 | `0:0 0700` |
| `/var/lib/omarchy/m2-displayport/active/pre-install-boot.bin` | `203ab7027536c8d16f373d02c1f6346a5c34cfe095a9dafd0cfe37d2b354090c` | 6,205,569 | `0:0 0600` |
| `/var/lib/omarchy/m2-displayport/active/candidate-boot.bin` | `203ab7027536c8d16f373d02c1f6346a5c34cfe095a9dafd0cfe37d2b354090c` | 6,205,569 | `0:0 0600` |
| `/var/lib/omarchy/m2-displayport/active/recovery.txt` | `5fda712442fd860bb8c31d8441e350c66e1ecfb1c4054206f638119106dead78` | 949 | `0:0 0600` |
| `/var/lib/omarchy/m2-displayport/active/bundle.env` | `f967202c3da1f31480b52c51e46ca2679e302f64596f9917edc56d0041449fb7` | 448 | `0:0 0600` |
| `/var/lib/omarchy/m2-displayport/active/RESULT` | `0ebf65c7984364f0999b4b54018b582a0da08a145e4d88a228ce2438856e7b06` | 7 | `0:0 0600` |
| `/boot/efi/m1n1/boot.bin.pre-omarchy-m2-displayport-20260902T085339Z` | `203ab7027536c8d16f373d02c1f6346a5c34cfe095a9dafd0cfe37d2b354090c` | 6,205,569 | `0:0 0755` |
| `/boot/efi/m1n1/RECOVERY-OMARCHY-M2-DISPLAYPORT-20260902T085339Z.txt` | `5fda712442fd860bb8c31d8441e350c66e1ecfb1c4054206f638119106dead78` | 949 | `0:0 0755` |

The active `state.env` has no separately retained root-only hash that this offline slice can authenticate without privilege. The publisher therefore requires the exact ordered 16-field format-2 semantic contract, root ownership, mode `0600`, one link, ASCII and line-complete syntax. It records the file descriptor identity and transaction-local SHA-256 on the first preflight, then requires the exact record again after the copy, after publication, and immediately before commit. Only the accepted `hook_parent_created` values `0` and `1` are allowed. This does not invent a historical state hash.

Every ancestor of each protected pin, active-state path, system input, destination, transaction, publisher, and recovery path must have the configured root owner. Production sets the trusted traversal root to `/` and the expected owner to UID 0. Only the exact source uses the safe generic traversal that permits its required UID-1001 ancestry. The source file itself still requires UID/GID `1001:1001`, mode `0600`, one link, the exact size, and the exact hash.

Fresh unprivileged `stat -c '%n|%u:%g|%a|%h|%s|%F'` checks confirmed the public metadata for `boot.bin`, the default, accepted base, and AFK-only images, GRUB, the package guard, both current EFI recovery files, and the input image. The `/var/lib/omarchy/m2-displayport/active` directory refused unprivileged traversal. Its file hashes and metadata therefore reuse the accepted authenticated format-2 activation records instead of a new privileged read. A fresh existence check reported `destination=absent`.

The host contract also pins kernel `7.1.6-1-1-ARCH`, the nine exact package versions, the `/boot` filesystem identity `ext4 e24cf117-3c89-4392-a3b8-def187becda8 /`, M2 J413 and T8112 identity, the external DCP route to controller `0-003f`, external power online, battery above 50 percent, and absent package transaction and persistent boot override.

## RED and GREEN

The retained first run occurred after the test was added but before the new publisher and bootstrap existed:

```text
python3.14 -I -S -B dev/apple-dp-altmode/afk-service-reuse-pr582/test-stage-image.py
exit 1 because the new publisher and bootstrap were absent
```

The later bootstrap-boundary run found the expected missing bootstrap and retained the failure before correction:

```text
Ran 23 tests in 0.253s
FAILED (failures=1, errors=3)
```

The exact GREEN command and result are:

```text
/usr/bin/python3.14 -I -S -B dev/apple-dp-altmode/afk-service-reuse-pr582/test-stage-image.py
Ran 26 tests
OK
```

The gate covers exact production pins and the real candidate. It also covers source replacement and file-descriptor mutation, wrong owner/group/mode/hash/size, hard links, symlinks, unsafe ancestors, non-root-owned protected ancestors at modes `0700` and `0755`, destination collision, protected-file and ancestor replacement, an ancestor swap after the prior final check, the immediate pre-commit recheck, active-state semantic and mid-copy drift, fresh kernel/package/mount drift, partial-copy signals, every publication and commit boundary, retained `INCOMPLETE` semantics, embedded-payload identity, tampering, bootstrap collision, and bootstrap signal handling.

Additional offline checks at this checkpoint:

```text
/usr/bin/python3.14 -I -S -B -c 'import ast, pathlib; [ast.parse(pathlib.Path(path).read_text(encoding="utf-8"), filename=path) for path in ("dev/apple-dp-altmode/afk-service-reuse-pr582/stage-image.py", "dev/apple-dp-altmode/afk-service-reuse-pr582/test-stage-image.py")]'
exit 0

/usr/bin/env -i PATH=/usr/bin:/bin LANG=C.UTF-8 /usr/bin/python3.14 -I -S -B dev/apple-dp-altmode/afk-service-reuse-pr582/stage-image.py
REFUSED: root is required
exit 1
```

## Result and hold

The implementation keeps the mutable user-owned source behind a file-descriptor identity check, copies it into a root-owned private transaction, verifies the protected copy and publication, and uses a durable `INCOMPLETE` to `COMPLETE` commit boundary. A failed operation removes only its owned partial publication, restores `INCOMPLETE`, and never replaces an existing destination. It retains the exact failed transaction for review.

The first independent security review rejected the 24-test version because it did not require root ownership for every protected-path ancestor. The corrected version adds that barrier, the two negative ancestor modes, and the immediate pre-commit protected recheck. The final adversarial security review accepted the corrected implementation.

Independent functional QA accepted all 26 focused tests. Final adversarial security review accepted the exact publisher, embedded payload, pins, path handling, signal behavior, and durability boundaries. The reviewed publisher is 36,672 bytes with SHA-256 `7b14544aacee7a88ca164de7c0a6b2cd901dd1f791752c18af41e3e3eea8939d`. The reviewed literal bootstrap is 52,855 bytes with SHA-256 `668f123098252bfd849d66630ec8ec08a808cc9a70d6a9a3520c07cbd55177c5`. The reviewed test is 42,206 bytes with SHA-256 `5bdf48b6f6ae670162e37f1977be02e7ace80a5ee26cc0af2240c4fe4d3809f9`. The destination remains absent. The next action is a separate manual staging handoff. Sudo, staging, reboot, and cable actions remain held until that handoff. Any result other than the exact staging PASS requires inspection of the retained transaction. This includes a signal delivered after the durable commit point, where `COMPLETE` can exist despite a non-PASS terminal result. Do not retry, select, or boot the candidate until that transaction is reviewed.
