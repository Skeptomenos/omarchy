# DEV-147 E third operational attempt PASS evidence — 2026-08-30

**Host / scope:** `omarchy-air`; contained, unprivileged, offline A2 only.
**Approval:** David's `GO` authorized exactly one third 424-child E-control attempt after the two retained fail-closed attempts.
**Repo state:** Branch `codex/dev-147-t1-image-offline`; reviewed checkpoint `e7adf149fce1e656a030f9557d2531333179f34b`.
**Holds:** T1 assembly, candidate-image creation, load, stage, boot, sudo, reboot, cable, device, recovery rehearsal, sysfs, boot-file, and live-system actions stayed on HOLD.

## What happened

The preflight authenticated the reviewed checkpoint and a clean worktree. The
local and remote branch heads matched. No earlier control process or package
lock was present. The eight production inputs had their reviewed identities,
metadata, and exact directory membership. The private source and retained E
inputs remained single-link files owned by UID/GID 1001.

The approved launcher had SHA-256
`62d3c8224cdf2add93a96195f2d35da232086b7074911c92346cd3200beee827`.
The 582-entry toolchain-v5 manifest had SHA-256
`5886d68d263c773990f2c7c5675f63e05debf5c78cdf693440339fddfca947c0`.
The recipe had SHA-256
`1be81904b29c69cb24fae86208c62fb30e830eca46250978a65d8ed19db8de77`.
The helper and its private staged copy were byte-identical at SHA-256
`686d59e63166df1bef1afad27998a6d58f4c28b6b4439b6ccd607b56471268ca`.

Fresh probe `run-y3xcwg2_` exited 0 without timeout. It used exactly 593 unique
read-only mounts. It exposed only the fixed proof target and eight task inputs.
Its containment checks passed. UID/GID were 1001. The capability and bounding
sets were empty. `NoNewPrivs` was active. Seccomp filtering was active. No
network route or host `/proc`, `/sys`, `/run`, `/home`, or `/boot` was visible.
Only `/work` and `/tmp` were writable. All seven lazy-import smoke checks
passed. Stderr was empty and every input stayed unchanged.

The one authorized production entry was `run-988kuwr1`. It used the same
launcher, manifest, ordered eight inputs, and 593 read-only mounts. Its
`inputs.json` and `security.json` files are byte-identical to the probe files.
It exited 0 without timeout. Every input stayed unchanged. No retry ran.

## Result

The production result is a fresh operational no-change PASS:

| Check | Result |
|---|---|
| Mode | `E_NO_CHANGE_OFFLINE` |
| Fresh and operational proof | Both `true` |
| Planned / observed commands | 424 / 424, exact and ordered |
| Child processes | 424 completed; 424 unique positive PIDs |
| Child files | 424 JSON, 424 stdout, 424 stderr; 1,272 total |
| Child state | Every status `ok`, return code 0, retained bytes equal observed bytes, empty stderr, `killed: false`, `reaped: true` |
| Lookups | 200 modules, 3 aliases, and 9 symbols |
| Mappings | 1,408 aliases and 596 symbols |
| Candidate bound | `false` |
| Image / load / stage / boot | All `false` |

Every child file is mode `0600`, owned by UID/GID 1001, and single-link. Every
child record, stdout, and stderr SHA matches its descriptor in the published
evidence. The 424 commands and 424 stdout/stderr streams are byte-identical to
the corresponding completed children in the second fail-closed attempt
`run-noq24xg7`. This comparison confirms that only the validator correction
changed the outcome.

Child 4 used exact `/usr/bin/gzip -n`. Its output SHA-256 is
`375aa35be0ea57fa8d3f79f20cfa70373742ba6e2afda409462497d0d96ad724`.
The ten-byte gzip header is `1f 8b 08 00 00 00 00 00 00 03`. Decompression
produces the exact 61,286,668-byte main stream at SHA-256
`7be7b4b03367b5ce4b356fe35977edba6540af0a7df930dbff990286c9b98e28`.

The generated lookup root is unchanged before and after observation. Six of
the seven retained final indexes match fresh generation. The one reviewed
exception is `modules.symbols.bin`: retained SHA-256
`a3f1e745b7675daaec99c7c7ebadc7d67b318143901e063674494c210b12ace6`
and generated SHA-256
`5077fb001a5c48a2135ce8f651606b18578610bc660f430a59114e76be4f9437`.
The control root changes as expected because `depmod` creates generated index
names. This is the exact reviewed no-change model. It does not replace the
seven retained final index bytes.

The published proof files are:

| File | Bytes | SHA-256 |
|---|---:|---|
| `e-control-header.json` | 1,149 | `1665fe5a0d5d58eb3fa029faaea066da5c4b026415d19c33d644c5ec0b44f96a` |
| `e-control-evidence.json` | 965,657 | `6bbbb024d616bfa767dfe71b4a6121a1e75233bb1a1c8bc47b81b93f28628709` |
| `e-control-result.json` | 366,381 | `5e08a383469bd65d402939d0b7ca9cef9c2febb77ca12de1d577454b0d2de8f2` |
| `e-early.cpio` | 10,240 | `967bc6adcff42e59abcfb4e509f6c80fd65588e0861d8c1c3189a135f10955b4` |
| `e-main.cpio` | 61,286,668 | `7be7b4b03367b5ce4b356fe35977edba6540af0a7df930dbff990286c9b98e28` |

The header binds retained E SHA-256
`4d4f0557af57eebcc33322f004bcc7968254e644b069a11102375df0b31a52ae`,
19,191,513 bytes, 7 early records, 1,163 main records, 200 modules, all seven
retained index hashes, exact gzip, binary-only lookup, and no-change archive.

Probe and production input manifests both have SHA-256
`64176462e8b84b0876df6da966beb7795a7376250c68206c2c6e212f620a0456`.
Their security records both have SHA-256
`eb52e8d04db7a847c19dc68e57f5b1b1331c46c45852100dc3ae19d7e9da96f2`.
No pending result or image exists. No control child or tool process remains.

## Review

Independent QA and final documentation review were pending when this immutable
run record was written. The living plans own their later verdicts.

## Rollback

No rollback is needed. This operation wrote only to a fresh private sandbox
run directory. It changed no installed package, boot file, module, image,
device, cable state, or live process.

## Open

This is the first fresh E no-change control PASS. It is not a T1 assembly,
candidate image, startup, driver-load, display, USB, charging, or hardware
result. The accepted private T1 source and module remain unbound. T1 assembly
is the next separate offline review gate. It requires new explicit authority.
All live and manual holds remain active.
