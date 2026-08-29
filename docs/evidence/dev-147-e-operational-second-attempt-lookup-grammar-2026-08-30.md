# DEV-147 E second operational attempt and lookup-grammar correction evidence — 2026-08-30

**Host / scope:** `omarchy-air`; contained, unprivileged offline A2 only.
**Approval:** One gzip-corrected 424-child E-control attempt was authorized after the first fail-closed attempt and independent review.
**Repo state:** Branch `codex/dev-147-t1-image-offline`; checkpoint HEAD `80149434ee5277073d7e3f26448a8a029afc6bfe` plus the reviewed uncommitted correction.
**Holds:** Candidate-image assembly, load, stage, boot, sudo, reboot, cable, device, recovery rehearsal, sysfs, boot-file, and live-system actions stayed on HOLD.

## Outcome

Fresh toolchain-v5 probe `run-x65x28u0` passed. It authenticated the exact eight
production inputs and predicted 593 read-only mounts. The one authorized
corrected production attempt was `run-noq24xg7`. It used the reviewed launcher,
the 582-entry v5 manifest, eight inputs, and exactly 593 read-only mounts. It
ran the fixed 424-child plan once. It did not time out. All inputs stayed
unchanged.

The child directory contains exactly 1,272 files: one JSON report, stdout file,
and stderr file for each of 424 children. Every report has status `ok`, return
code zero, retained bytes equal to observed bytes, empty stderr, a positive
unique PID, `killed: false`, and `reaped: true`.

The recipe exited 1 after all children completed. Validation raised
`ControlError("LOOKUP_FORMAT")` in `e_control.ordered_lookup()`. The recipe
wrapped it as `RecipeError("E_CONTROL_OPERATIONAL_INVALID")` in
`_validate_operational_semantics()`. The first affected module was child 13,
the dependency lookup for `842`.

The fail-closed boundary worked. These files are absent:

- `/work/e-control-header.json`
- `/work/e-control-evidence.json`
- `/work/e-control-result.pending`
- `/work/e-control-result.json`

No fresh E-control proof exists. No `bwrap`, `gzip`, `cpio`, `depmod`, or
`modprobe` process from the attempt remains active. No retry ran.

## Gzip correction proved

Child 4 used exact `("/usr/bin/gzip", "-n")`. Its output is 19,181,273 bytes
at SHA-256
`375aa35be0ea57fa8d3f79f20cfa70373742ba6e2afda409462497d0d96ad724`.
Header MTIME is zero. Decompressed output is the exact 61,286,668-byte main
stream at SHA-256
`7be7b4b03367b5ce4b356fe35977edba6540af0a7df930dbff990286c9b98e28`.

Compared with first failed attempt `run-f2yoto48`, exactly one planned command
changed: child 4 changed from bare gzip to gzip `-n`. Exactly one stdout file,
child 4, changed. The other 423 stdout files are byte-identical. This proves the
narrow gzip correction. It does not create an E-control PASS.

## Byte-level lookup diagnosis

The retained production control tree has 214 files. The lookup tree has 207
files. Across the 212 dependency, alias, and symbol outputs, kmod 34.2 emitted
347 lines:

- 346 `insmod` lines end in one ASCII space followed by newline.
- The sole `builtin ecb\n` line has no trailing space.

The authenticated helper's old canonicalizer emitted `insmod <path>\n`. The
parsed path and required order were correct. The raw-byte comparison therefore
failed at the first module dependency result. This is a format-model mismatch,
not an executed-command, archive, gzip, index, containment, timeout, or input
failure.

Probe and attempt `inputs.json` are byte-identical at SHA-256
`396a210c6e302b26579891b93791da55c8803cd1e3470dfb30907aad18cb2426`.
Their `security.json` files are byte-identical at SHA-256
`eb52e8d04db7a847c19dc68e57f5b1b1331c46c45852100dc3ae19d7e9da96f2`.

## Test-first correction

The direct-helper fixture changed first to use actual kmod 34.2 grammar. The
positive oracle emitted exactly one trailing space on `insmod` lines and no
space on `builtin ecb`.

An initial outer command omitted the required explicit v5 manifest. Argparse
selected known-obsolete v4 and stopped on missing
`/usr/lib/libgcrypt.so.20.7.2`. It created no run directory or test result. This
was a command-construction failure. It is not v5 drift, containment evidence,
input evidence, or RED evidence.

The corrected RED invocation supplied the exact v5 manifest. `run-mnmz924l`
used 591 read-only mounts. It ran 18 methods in 1.181 seconds. Exactly one
assertion failed: the current helper rejected actual grammar with
`LOOKUP_FORMAT`. There were zero errors or skips. It retained the expected 11
bounded fixture child records. Inputs stayed unchanged. No timeout occurred.

The minimal helper correction changes only the canonical raw `insmod` suffix
from newline to one space plus newline. It keeps `builtin` lines unchanged. The
fixture also requires strict refusal of missing or doubled `insmod` spaces, a
spaced builtin, altered paths, reordering, duplicates, missing records, and
extras. It adds no option, override, fallback, or retry.

`run-2f6yexwm` used 591 read-only mounts and passed 18/18 methods in 1.174
seconds. It retained exactly 11 bounded fixture child records. These are the
existing harmless gzip, cap, exit, stderr, kill, reap, and deadline fixtures.
They are not the 424-child production workload. It created only synthetic ASCII
fixture trees at `/work/control-root` and `/work/lookup-root`. It created no
E-derived production tree, stream, `/work/e-control-children-e1`, header,
evidence, pending result, or final result.

## Zero-production-child GREEN results

All final runs used reviewed launcher SHA-256
`62d3c8224cdf2add93a96195f2d35da232086b7074911c92346cd3200beee827`
and toolchain-v5 manifest SHA-256
`5886d68d263c773990f2c7c5675f63e05debf5c78cdf693440339fddfca947c0`.
Each containment probe passed. Every run exited 0 with unchanged inputs, no
timeout, zero production children, and no production result files.

| Run directory / ID | Suite | Read-only mounts | Result |
|---|---|---:|---|
| `run-rte0vj2a` | Pure recipe | 605 | 16/16 passed in 0.311 seconds. |
| `run-hgr5p8p1` | Structural | 594 | 3/3 passed in 1.038 seconds. |
| `run-trmsyl6z` | Semantic | 606 | 3/3 passed in 13.352 seconds. |
| `run-lsiwy1ye` | Execution | 594 | 3/3 passed in 1.255 seconds. |

The focused aggregate is 25/25 with zero failures, errors, or skips. The
semantic fixture aggregate stayed exactly
`5f80a3cf89e2c21e9f694cb8ed47a062aa44003f554ceb18f5de3fc87ea6ebf0`.
The command plan did not change.

## Current identities

| Artifact | SHA-256 |
|---|---|
| Helper `e_control.py` | `686d59e63166df1bef1afad27998a6d58f4c28b6b4439b6ccd607b56471268ca` |
| Private staged helper copy | `686d59e63166df1bef1afad27998a6d58f4c28b6b4439b6ccd607b56471268ca` |
| Recipe `run_e_control.py` | `1be81904b29c69cb24fae86208c62fb30e830eca46250978a65d8ed19db8de77` |
| Direct-helper runner | `4e4638c9579af4c56b46f207d806f3fc2caf3b5ad346683065660b0159f1814c` |
| Pure recipe runner | `170b27788135ae7d78e0355570ed5ee20ccd33c8ada11912b5cd15ffaf053751` |
| Structural runner | `31ccbb035e6e92fab6328b203b090c77138d1abdd8f76e1cab430367fb8783b9` |
| Semantic runner | `bf6f8b271a139b4cff09bb97e02d39cfc82cbd9726efedf4a4dc85bff4785483` |
| Execution runner | `50ba54c6dcbe8304890908ac976ee0bf07e00e0ba34c5433043a9ee6efa491b3` |

Production attempt `run-noq24xg7` used the reviewed pre-correction helper SHA
`16016875e731e88d047eb805c7c6d03045300abdb262361b18010a952adb7b80`
and recipe SHA
`57d35a30de9b351bcbaf0b78a1be186c8c44a2fbfb378d8f0b801e6e9256a7a9`.
Those identities are retained incident history, not current source pins.

## Holds and next gate

No candidate image was assembled. No module was loaded. No staging, boot,
sudo, reboot, cable, device, recovery-rehearsal, sysfs, boot-file, or live-system
action occurred during the correction. The private T1 source and module remain
unbound. There is no T1 image or fresh E-control PASS.

Independent QA and final review of the exact lookup-grammar correction are the
next gates. Any third production attempt needs a separate GO and a new
successful toolchain-v5 probe. A failure cannot trigger an automatic retry,
image build, stage, or manual action.
