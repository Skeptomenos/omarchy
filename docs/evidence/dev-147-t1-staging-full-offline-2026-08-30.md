# DEV-147 T1 staging full offline fixtures — 2026-08-30

Scope: unprivileged offline A3 staging-helper fixtures on branch `codex/dev-147-t1-image-offline`, based on `bd704300a8f06a4a5ab5b6ee506d060563e835ad`. Status: the sole full run, independent result QA and executed-boundary safety review PASS. The full offline staging-fixture gate is accepted. This is not production staging or a complete A3/A4 package.

## Approval and exact change

David answered “approved. proceed” to the exact request to add the existing verified `/usr/bin/sync` as one read-only sandbox input and run all offline staging tests. The containing-filesystem flush effect of sync -f was disclosed. The private approval record `a3-sync-only-approval-20260830.json` has SHA `5f7b3379fa01ebdc8122ae72997c8704b1f76ab0555acf45b9c0e86f5fae58a3`.

New `toolchain-v6-sync-only.json` preserves all 582 v5 rows, their order and bytes, and appends only the approved sync row. It has 583 unique runtime targets; three harness and four task bindings give 590 read-only mounts. Sync SHA is `bf77551deae42b2d0aa5eaede07a8f9c2954409fe38ea79af2b0a238880c899c`, fingerprint `c6a7f1189a5f1f480462e3c62708fe75fc251be756abb44c99c2da4994ce38fe`. Its loader and libc already match v5. No new library, directory, writable binding, device, install or other runtime repin was introduced. V5 and the launcher remain unchanged.

The corrected public helper and all 54 test bodies remain byte-identical to the [prior subset checkpoint](dev-147-t1-staging-preparation-hold-2026-08-30.md). No operational helper was used. The test docstring and [seven-method contract](../../dev/apple-dp-altmode/usbdiag/staging/t1-privacy-green-review-contract.md) retain their earlier authorization as history; the new approval selected the existing full suite without changing those files. All earlier REDs, rejected v1, subsets, evidence and backups remain unchanged.

## Actual result

Independent manifest/source review preceded a fresh exact-input probe and one full run. The inner command was:

```text
/usr/bin/bash -c '/usr/bin/bash -n /inputs/helper && exec /usr/bin/python3.14 -I -S -B /inputs/test'
```

| Retained run | Result |
|---|---|
| Fresh probe `run-mvrkgtqy` | Outer exit 0, no timeout, unchanged inputs and 590 read-only mounts. The exact input/security records match the full run. |
| Sole full run `run-nwf2rtvo` | Bash syntax and all 54 tests passed in 2.944 seconds; zero failures/errors/skips. Outer exit 0, no timeout and unchanged inputs. Setup and post-input authentication passed. |

Root loaded and audited all 200 recorded direct fixture Bash child command/stdout/stderr/result triplets. This count does not include every descendant external helper-tool process, and no per-descendant triplet claim is made.

| Direct fixture outcome | Count |
|---|---|
| Exit 0 | 54 |
| Expected exit 1 refusal | 141 |
| Expected exit 7 injection | 4 |
| Intentional SIGTERM, return code -15 | 1 |
| Timeout | 0 |

There were 54 unique test methods, 200 unique direct-child records, no unexpected record, no successful child with stderr, no false PASS on a nonzero child and no invalid exit-7 case. The public-entry calls refused invalid configuration, an environment override and extra arguments before production preflight. Root's targeted process check found no relevant surviving workload. Independent detailed result QA and executed-boundary safety review passed without a workload rerun; only the full offline staging-fixture gate is accepted.

Independent QA matched all 590 current input fingerprints, exact commands/status/streams for the 200 direct fixture children, all 54 test-case memberships and retained current file states. It inspected 24 sentinels, 15 collision objects, 65 pin files, the expected 1,024-byte partial output and completion/failure markers. Metadata continuity was asserted inside the frozen tests. Independent QA reread retained bytes, metadata and membership, not persisted before-snapshots. Retained and fresh targeted process checks found no relevant survivor.

The full suite covers the actual synthetic start/protected-hash/copy/recheck/no-replace-publication/recheck/finish sequence. It checks preserved sentinel bytes/metadata, failure after copy and publication, closed completion stdout, exit-trap behavior, collisions, source identity/hash/size guards, exact 34 protected plus eleven proof producers, strict power-value validation and static fixed-reader wiring. These are private-file and parser/guard tests, not a read of actual protected boot files or power attributes.

## Fixed pins and retained records

| Source or record | SHA-256 |
|---|---|
| [Unchanged public helper](../../dev/apple-dp-altmode/stage-tipddiag-initramfs.sh) | `91553641af7e6676c8c032cb3432406fec3958959674ec5917a759726714c71e` |
| [Unchanged 54-method suite](../../dev/apple-dp-altmode/usbdiag/staging/test_stage_tipddiag_privacy_green.py) | `af28433894b92728a7a1892b543e10b59e2d0ff6c5e359a8ba390ec62f9563b0` |
| Frozen C3 baseline | `dbfbeac043d77ed1543274322f4f961a7622a2adbf49503bb2f54ee465d4d6fe` |
| Independent private proof specification | `189cde8a58dba21374cb7231342136ab25b97fb03ee1e755cdbb2d66a9119269` |
| New v6 sync-only manifest | `6f999183c660b49c3ba665a9bc9b22d316beca81cf01a9b4a403f5c1435a9391` |
| Preserved v5 manifest | `5886d68d263c773990f2c7c5675f63e05debf5c78cdf693440339fddfca947c0` |
| Preserved private launcher | `3544e55bd504019344b6358e1829686759abecc5f9f4c8534901290df963851e` |
| Shared probe/full `inputs.json` | `c0f6c66bd4ccd1a37c5b8491c0199880a1737e8561ee540d3bc76455451be143` |
| Full `command.json` | `2cf25e6c2348dc38b056eb7afa0bbb0081b3193cde1188adf907b2b6c1ce01cc` |
| Shared successful outer `result.json` | `995626ca50174bc34f03fdf59825ddb8c485ffcb59d62d20116b394620ac3a1f` |
| Full unittest `stderr.log` | `bafc459bf5c8b68594abb2fe3008ba9db5f0475f0d2efff30581de9c7c1aeff9` |
| Private `a3-staging-full-root-evidence.json` | `ec90ebcb9baac02ff9cb9f66fb4c4f9e3acce50e96662c411d13d2b2d3e8b072` |
| Later private `a3-staging-full-independent-qa.json` | `19038d5cbe273b58d632c3cfb10df8c7ac86521ceee2d1772336d7559b1a6ca1` |

The root evidence was authored with independent result review still pending and stays unchanged. It retains exact commands, isolation results, input invariance, direct-child audit and the no-survivor observation. The separate later QA record documents independent PASS and the metadata-continuity qualification above. Its observer-only inspection corrections did not change or rerun the workload and were not workload failures. Raw records and machine paths stay private.

## Limits and next gate

The approved sync -f calls flush cached writes for the containing filesystem, not only the named fixture file. The missing-path sync refusal checks error propagation; it is not an injected physical disk failure. Neither that test nor the other synthetic failures proves storage power-loss safety or recovery correctness.

The [accepted private T1 image](dev-147-t1-private-image-2026-08-30.md) remains unchanged, unstaged and unbooted. No real image input, operational-helper execution, production preflight, live sampling, cable/device action, sudo, reboot, recovery rehearsal or hardware acceptance occurred. There is no current power or display-state claim. No rollback or cleanup ran; retain all outputs and historical artifacts.

With this fixture result independently accepted, the remaining software prerequisite is the real fixed-T1 bounded collector and artifact binding. The accepted 21 pure capture tests are not an actual collector; the operational collection/binding entry remains closed and the new implementation is missing. Reviewed private capture, one-case and recovery drafts remain drafts. A3/A4 is incomplete and unsealed; A4 review/seal follows the capture implementation and its tests. The unsafe aggregate-test hold and every live/manual hold remain active. This fixture result does not complete the overall goal.
