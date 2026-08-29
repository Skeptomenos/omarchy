# DEV-147 E first operational attempt and gzip correction evidence — 2026-08-29

**Host / scope:** `omarchy-air`; contained, unprivileged offline A2 only.
**Approval:** The fixed offline control was authorized after independent review. All candidate-image, load, stage, boot, sudo, reboot, cable, device, recovery-rehearsal, and live-system holds stayed active.
**Repo state:** Branch `codex/dev-147-t1-image-offline`; pre-checkpoint HEAD `26c2fdc9560d946bff4755244da63f81e6e0fb06` plus the reviewed uncommitted candidate.

## Outcome

Fresh toolchain-v5 probe `run-8xph_o58` passed. The one and only production
attempt was `run-f2yoto48`. It used the reviewed launcher, the 582-entry v5
manifest, eight task inputs, and exactly 593 read-only mounts. It ran the fixed
424-child plan once. It did not time out. All inputs stayed unchanged.

All 424 child JSON reports exist. The retained child directory contains exactly
1,272 files: one JSON report, stdout file, and stderr file for each child. Every
report has status `ok`, return code zero, retained bytes equal to observed
bytes, empty stderr, a positive PID, `killed: false`, and `reaped: true`.

The recipe exited 1 after the children completed. It raised
`RecipeError("E_CONTROL_SEMANTIC_INVALID")` at
`_validate_archive_observation()` for child 4. The stop occurred before result
publication. These production artifacts are absent:

- `/work/e-control-header.json`
- `/work/e-control-evidence.json`
- `/work/e-control-result.pending`
- `/work/e-control-result.json`

No fresh E-control proof exists. No process from `run-f2yoto48` remains active.
No production retry ran.

## Byte-level diagnosis

Child 4 used `("/usr/bin/gzip",)`. Its input was the exact 61,286,668-byte main
stream at SHA-256
`7be7b4b03367b5ce4b356fe35977edba6540af0a7df930dbff990286c9b98e28`.
The expected and observed gzip outputs were both 19,181,273 bytes.

| Observation | Expected retained E | Observed child 4 |
|---|---|---|
| SHA-256 | `375aa35be0ea57fa8d3f79f20cfa70373742ba6e2afda409462497d0d96ad724` | `35ae12e147f556cd6fa5fadb7749acc69e8e60bf91593669c18e527b75070e8d` |
| Header bytes 5-8, one-based | `00 00 00 00` | `07 11 93 6a` |
| Decoded modification time | zero | `2026-08-29T17:04:07Z` |
| Trailer | `d0 e5 7a c4 0c 29 a7 03` | `d0 e5 7a c4 0c 29 a7 03` |
| Decompressed SHA-256 | `7be7b4b03367b5ce4b356fe35977edba6540af0a7df930dbff990286c9b98e28` | same |

Only gzip bytes 5-8 differed. The compressed payload and trailer were
byte-identical. The observed timestamp matched the main-stream file modification
time. The retained local gzip help states that `-n` or `--no-name` does not save
the original name or timestamp.

## Fail-closed correction

The fixed command plan now uses `("/usr/bin/gzip", "-n")`. The helper accepts
that exact tuple and rejects bare `("/usr/bin/gzip",)`. The recipe planner,
semantic planner, semantic command validator, structural report condition, and
all four focused runner oracles use the same exact tuple. There is no flag,
environment override, fallback, retry, or alternate plan.

The helper `e_control.py` SHA-256 is
`16016875e731e88d047eb805c7c6d03045300abdb262361b18010a952adb7b80`.
The corrected recipe `run_e_control.py` SHA-256 is
`57d35a30de9b351bcbaf0b78a1be186c8c44a2fbfb378d8f0b801e6e9256a7a9`.

The semantic fixture comparison used accepted run `run-b7wklmzu` and failed-pin
setup run `run-ost1uw06`. Of their common fixture files, only
`e-control-semantic-fixture-records-s1/record-004.json` changed. Its size changed
from 648 to 658 bytes. Its SHA-256 changed from
`75fec501f6e0ef237715a107ce81bfbca3064b6d11944ad9b768751785fd7c6b` to
`7d7060b4d09adeee70fa3b0eccacf75225912cb1289391a2722a705bed597642`.
The record changed only the fixture and operational command arrays from bare
gzip to gzip with `-n`.

The directly derived fixed aggregate SHA-256 changed from
`68dd45eeeb9239b873c293b81cbbb5b7403d4ff0d5d1b5a32f3e27c14c92d44e` to
`5f80a3cf89e2c21e9f694cb8ed47a062aa44003f554ceb18f5de3fc87ea6ebf0`.
Derivation run `run-ibhaue4t` used the normal exact three-method semantic
command with only that literal pin temporarily unset. Setup published the new
candidate. The expected literal-pin assertion failed. The other two methods
passed. It ran zero workload children. Inputs stayed unchanged and no timeout
occurred. The final source contains the new literal. It does not contain the
temporary `None` value.

## Corrective zero-child results

All four final corrective runs used the reviewed launcher at SHA-256
`62d3c8224cdf2add93a96195f2d35da232086b7074911c92346cd3200beee827`
and the 582-entry toolchain-v5 manifest at SHA-256
`5886d68d263c773990f2c7c5675f63e05debf5c78cdf693440339fddfca947c0`.
Each containment probe passed. Every run reported unchanged inputs, no timeout,
zero executed workload children, and no production output.

| Run directory / ID | Suite | Result |
|---|---|---|
| `run-voc0ceb9` | Pure recipe | Exit 0; 16/16 passed in 0.309 seconds. |
| `run-q_c6c496` | Structural | Exit 0; 3/3 passed in 1.044 seconds. |
| `run-ng6qerzs` | Semantic | Exit 0; 3/3 passed in 13.364 seconds. |
| `run-z2rki6ms` | Execution | Exit 0; 3/3 passed in 1.254 seconds. |

The aggregate result is 25 tests, zero failures, zero errors, and zero skips.
The focused runner SHA-256 values are:

| Runner | SHA-256 |
|---|---|
| Recipe | `4ea75667497821f3f0dbbdebe00d16a8f86c5a6cdf18fe48c1b1c522b510fcd0` |
| Structural | `f4419eeab9d713f9f42c2467aecb8c2eb582e5f4271669c9833aab5e997ca72c` |
| Semantic | `fc2a34f573013d01ff24b18cf964ef236a1c22808fcb364724c05157cab602b6` |
| Execution | `641388e6c8e73cd4aebc245789fd273fecc4a49a5c3bb940365dd89200005b6d` |

## Holds and next gate

No candidate image was assembled. No module was loaded. No staging, boot,
sudo, reboot, cable, device, recovery-rehearsal, sysfs, boot-file, or live-system
action occurred. The production attempt and all correction checks were offline.
All holds remain active.

The next gate is independent QA and review of the exact correction. A second
production attempt requires a separate GO and a new successful toolchain-v5
containment probe. A failure cannot trigger a retry, image build, stage, or
manual action.

## Independent QA addendum — 2026-08-29

Independent QA repeated the four corrected zero-child suites with the same
reviewed launcher and toolchain-v5 manifest. All containment probes passed.
Every run exited 0 with unchanged inputs and no timeout.

| Run directory / ID | Suite | Read-only mounts | Result |
|---|---|---:|---|
| `run-wdid9vqb` | Pure recipe | 605 | 16/16 passed in 0.309 seconds; zero workload children. |
| `run-qv63ivbi` | Structural | 594 | 3/3 passed in 1.041 seconds; zero workload children. |
| `run-3sjaril5` | Semantic | 606 | 3/3 passed in 13.348 seconds; zero workload children. |
| `run-r24xtx2w` | Execution | 594 | 3/3 passed in 1.257 seconds; zero workload children. |

The independent focused result is 25/25 with zero failures, errors, or skips.
No run created a production control root, child-record root, header, evidence,
pending result, final result, candidate image, module load, stage, or boot
output.

Independent QA then invoked the direct helper suite once. This was its first
and only invocation for the corrected helper. `run-kyar_nn2` used 591 read-only
mounts. It passed 18/18 methods in 1.199 seconds. It retained exactly 11 bounded
fixture child records. These children cover the gzip roundtrip and the fixed
cap, exit, stderr, kill, reap, and deadline cases. They are not the 424-child
production workload.

The helper gzip child used exactly `("/usr/bin/gzip", "-n")`. Its ten-byte
header starts `1f 8b 08 00 00 00 00 00 00 03`, so its MTIME field is zero.
The unapproved-command test proved that bare `("/usr/bin/gzip",)` is refused
before a child starts. The run created no production control output, candidate
image, module load, stage, or boot output. Its inputs and sources stayed
unchanged, and it did not time out.

The independently tested identities are:

| Artifact | SHA-256 |
|---|---|
| Corrected recipe | `57d35a30de9b351bcbaf0b78a1be186c8c44a2fbfb378d8f0b801e6e9256a7a9` |
| Corrected helper | `16016875e731e88d047eb805c7c6d03045300abdb262361b18010a952adb7b80` |
| Direct helper runner | `e1d1e39bb0782962a225d1f9f25f29f91025ce3bad59e8c8030fec80f3398045` |
| Recipe runner | `4ea75667497821f3f0dbbdebe00d16a8f86c5a6cdf18fe48c1b1c522b510fcd0` |
| Structural runner | `f4419eeab9d713f9f42c2467aecb8c2eb582e5f4271669c9833aab5e997ca72c` |
| Semantic runner | `fc2a34f573013d01ff24b18cf964ef236a1c22808fcb364724c05157cab602b6` |
| Execution runner | `641388e6c8e73cd4aebc245789fd273fecc4a49a5c3bb940365dd89200005b6d` |

Independent QA is complete. Independent final review remains open. These
results do not create a fresh E-control PASS and do not authorize a second
production attempt. A separate GO and a fresh v5 probe remain mandatory.

## Helper-root clarification — 2026-08-29

The earlier phrase "no production control root" means that no E-derived
production tree existed. Direct-helper run `run-kyar_nn2` did create synthetic
ASCII fixture trees at the exact names `/work/control-root` and
`/work/lookup-root`. It created no E-derived production tree, `/work/e-early.cpio`,
`/work/e-main.cpio`, `/work/e-control-children-e1`, header, evidence, pending
result, or final result. This clarification does not change the run result.
