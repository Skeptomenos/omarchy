# DEV-147 E lookup-correction independent QA — 2026-08-30

**Host / scope:** `omarchy-air`; contained, unprivileged, zero-production-child QA only.
**Candidate:** Branch `codex/dev-147-t1-image-offline`; base HEAD `80149434ee5277073d7e3f26448a8a029afc6bfe` plus the uncommitted lookup-grammar correction.
**Holds:** Production E control, T1 assembly, image creation, load, stage, boot, sudo, reboot, cable, device, recovery rehearsal, sysfs, boot-file, and live-system actions stayed on HOLD.

## Verdict

Independent QA passed. It first verified fresh probe `run-x65x28u0` and the
fail-closed second production attempt `run-noq24xg7`. It then invoked each
corrected v5 fixture or boundary suite once. Every QA run exited 0, kept its
inputs unchanged, and did not time out.

| Suite | Run | Read-only mounts | Result | `test-result.json` SHA-256 |
|---|---|---:|---|---|
| Direct helper | `run-i_x5ec4n` | 591 | 18/18; 11 bounded fixture children | `60dcf7dad9478ebf28adab6ed96fb3bfdbcc84be59efd770d85c349e4066e514` |
| Pure recipe | `run-ks9kn889` | 605 | 16/16; zero production children | `9659c6f9d06d271f86df114f3833b19e7128fc8eb8f6bddf5c24fdf31fb5a4a6` |
| Structural | `run-81ol5s2v` | 594 | 3/3; zero production children | `95acf3b5469ff1b075dfb5717ef8a9fba6fc6ca6ec88ce2ee4c788622ffc6df7` |
| Semantic | `run-_y7n3i3t` | 606 | 3/3; zero production children | `7b6d6082412ac4b286200573bb1dba193774e1315c28e8637b42199d74864392` |
| Execution | `run-bam09x3u` | 594 | 3/3; zero production children | `bd842b6b47b8a33f2b839b159429f8bc003167833791e9b17af44cfa4b38b114` |

The shared outer `result.json` SHA-256 is
`995626ca50174bc34f03fdf59825ddb8c485ffcb59d62d20116b394620ac3a1f`.
The shared `security.json` SHA-256 is
`eb52e8d04db7a847c19dc68e57f5b1b1331c46c45852100dc3ae19d7e9da96f2`.

## Checked boundary

The direct-helper QA accepted exactly one trailing ASCII space before newline
on each `insmod` line. It accepted no trailing space on `builtin ecb`. The
missing-space, doubled-space, spaced-builtin, reordered, unsafe-path, missing,
extra, and duplicate cases all remained refusals.

The current helper and private helper copy were byte-identical at SHA-256
`686d59e63166df1bef1afad27998a6d58f4c28b6b4439b6ccd607b56471268ca`.
The recipe SHA-256 was
`1be81904b29c69cb24fae86208c62fb30e830eca46250978a65d8ed19db8de77`.
The direct-helper, recipe, structural, semantic, and execution runner hashes
were, in that order:

- `4e4638c9579af4c56b46f207d806f3fc2caf3b5ad346683065660b0159f1814c`
- `170b27788135ae7d78e0355570ed5ee20ccd33c8ada11912b5cd15ffaf053751`
- `31ccbb035e6e92fab6328b203b090c77138d1abdd8f76e1cab430367fb8783b9`
- `bf6f8b271a139b4cff09bb97e02d39cfc82cbd9726efedf4a4dc85bff4785483`
- `50ba54c6dcbe8304890908ac976ee0bf07e00e0ba34c5433043a9ee6efa491b3`

QA also verified all 424 retained child triplets from `run-noq24xg7`, exact
gzip `-n`, zero MTIME, the 346 spaced `insmod` lines and one unspaced builtin,
the `LOOKUP_FORMAT` stop, and absence of header, evidence, pending result,
final result, and fresh proof. The obsolete-v4 command-construction stop had no
run directory and was not treated as test evidence.

No active sandbox or workload process remained. No production E artifact or
T1 image was created. This QA result does not authorize a third production
attempt. A third attempt still needs final review, a separate GO, exact
preflight, and a new successful toolchain-v5 containment probe.
