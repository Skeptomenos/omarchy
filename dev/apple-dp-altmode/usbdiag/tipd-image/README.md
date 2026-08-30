# T1 image contract and private assembly boundary

This directory defines the narrow archive boundary for the [selected T1 diagnostic](../../../../docs/plans/dev-147-usb-startup-diagnostic.md#a1-selection--t1-tipd-sender-diagnostic-living). The unchanged pure contract passed all 15 focused methods after the recorded semantic RED below, with independent QA and root review. The [fixed private assembler](t1-assembly-contract.md) produced one private T1 image after source/fixture GREEN and independent pre-execution review. Neither entry is a staging command or hardware result.

Reconciled: 2026-08-30. The [sole private T1 assembly and independent result QA](../../../../docs/evidence/dev-147-t1-private-image-2026-08-30.md) passed. Fresh exact-nine-input probe `run-vpqm7rk3` preceded assembly `run-mvqmtbw_`; both exited 0 without timeout or input change, with 594 read-only mounts. The private image is 19,209,545 bytes, SHA `c72c36736cebba0d6d5b67f47b02330c35d3ef81fed9bf5b3315095b0dd765fe`. Six offline children passed; exactly the TIPD payload changed and all seven indexes stayed identical. Complete result validation and independent candidate/readback audit passed; final-file presence alone is never PASS. The later [manual-boundary package](../../../../docs/evidence/dev-147-t1-manual-package-2026-08-30.md) reuses this image and the accepted 54-method staging and 13-method collector results. Independent handoff, manifest, safety, and final checksum review passed. The package is integrity-sealed and ready only for first manual staging/review. T1 remains unstaged/unbooted; the live collector is unrun. All live/manual holds remain active.

The [retained pre-execution RED `run-od4kokms` and GREEN `run-_6v39awz`](../../../../docs/evidence/dev-147-t1-assembly-preexecution-2026-08-30.md) each executed zero children. GREEN and independent QA `run-zbpyg548` passed 3/3 with unchanged inputs and no image/result. Assembler SHA remains `0facf27332e698bb24826a63b617e899d18bd591f399d869c5c91f12bb2f5552`; test SHA remains `03c5a8c0d1526d27c6cb78dfd739e878104850f25d33d6078d7723feb0877fc6`. These tests are separate from the later actual assembly.

## Scope and trust boundary

The T1 image starts from exact retained E: SHA-256 `4d4f0557af57eebcc33322f004bcc7968254e644b069a11102375df0b31a52ae`, 19,191,513 bytes. Only `usr/lib/modules/7.1.6-1-1-ARCH/kernel/drivers/usb/typec/tipd/tps6598x-core.ko` may change. All seven E index payloads must remain byte-identical. An unexpected dependency, alias, symbol, or index difference means HOLD; it does not widen this contract.

The [T1 private-candidate evidence](../../../../docs/evidence/dev-147-t1-private-candidate-2026-08-29.md) records retained source and two byte-identical contained module builds. The accepted private module SHA-256 is `a0fdadc351261643545e5afd8561923be99431661c447084336c9318f5b0c02f`. It was never an E-control input. The [third operational attempt](../../../../docs/evidence/dev-147-e-operational-third-attempt-pass-2026-08-30.md) supplies the required fresh E no-change proof. The dedicated assembler binds both exact identities. Its separately recorded private image passed independent result QA. No T1 load, stage, boot or hardware result exists.

The pure archive fixtures use labelled ASCII payloads, not ELF modules. Their raw delta check proves structure and an explicitly expected payload only. It does not authenticate T1. The new assembler separately authenticates the accepted real module and fresh E-control result SHA-256 `5e08a383469bd65d402939d0b7ca9cef9c2febb77ca12de1d577454b0d2de8f2`. Two fixed E production attempts ran all 424 children and failed closed before publication. The first exposed a gzip timestamp mismatch. The second proved `/usr/bin/gzip -n` and exposed kmod 34.2's exact trailing-space grammar. The third passed and published the proof. No argument, environment variable, fake identity, or fixture mode enables an alternate assembly.

These tests use the real, pinned newc parser/replacer and file guards. They also use the pinned pure single-gzip validator through its authenticated source chain. No dependency is mocked, and no historical main or import-time inspection workload is called. The existing no-install exception applies: typed stdlib/dataclasses, explicit validation and unittest replace Pydantic/pytest here. No Ruff, mypy or full-suite result is implied.

The current [E-control structural boundary](e-control-operational-red-contract.md) separates the accepted zero-child RED, the rejected first GREEN and the accepted corrected structural GREEN. The current structural regression `run-f0tjlamv` passes 3/3 after two retained repository-mode setup stops. Structural output is distinct and always states zero control-workload children and no fresh-control proof. The later operational entry, not this structural fixture, published the fresh proof on its third attempt.

The [E-control raw-observation semantic gate](e-control-semantic-test-contract.md) is accepted. Replacement RED `run-nqnr8soj` failed on the exact three missing boundaries. GREEN `run-vfbn_07m` passes 3/3, validates 424 complete fixture triplets, and publishes only a `NONFRESH_FIXTURE` result. The current pure recipe regression `run-m64c0_of` passes 16/16. Both execute zero workload children and cannot publish real control evidence.

The [fixed E execution boundary](e-control-execution-red-contract.md) preserves two fail-closed production attempts. `run-f2yoto48` exposed gzip MTIME drift. `run-noq24xg7` proved exact gzip `-n` and exposed kmod 34.2's one-space `insmod` grammar. The correction then passed its controlled RED, fixture GREEN, independent QA, and final review. Fresh probe `run-y3xcwg2_` and the one authorized third attempt `run-988kuwr1` passed with identical input and security manifests. The third attempt completed all 424 children, retained all 1,272 child files, proved exact E reconstruction and lookups, and published the [fresh no-change proof](../../../../docs/evidence/dev-147-e-operational-third-attempt-pass-2026-08-30.md). Independent read-only result QA found zero failures. Final documentation review found no blocker. Current recipe SHA is `1be81904b29c69cb24fae86208c62fb30e830eca46250978a65d8ed19db8de77`; helper SHA is `686d59e63166df1bef1afad27998a6d58f4c28b6b4439b6ccd607b56471268ca`. The [first-attempt evidence](../../../../docs/evidence/dev-147-e-operational-first-attempt-gzip-determinism-2026-08-29.md), [second-attempt evidence](../../../../docs/evidence/dev-147-e-operational-second-attempt-lookup-grammar-2026-08-30.md), [lookup-correction QA](../../../../docs/evidence/dev-147-e-lookup-correction-independent-qa-2026-08-30.md), [round-3 pre-execution evidence](../../../../docs/evidence/dev-147-e-operational-preexecution-gate-2026-08-29.md), and earlier [execution-boundary evidence](../../../../docs/evidence/dev-147-e-execution-boundary-2026-08-29.md) remain retained history. That E checkpoint created no T1 image. The later [private T1 assembly](../../../../docs/evidence/dev-147-t1-private-image-2026-08-30.md) is a separate accepted offline result. Every live/manual boundary remains on HOLD.

## Focused fixture contract

| Boundary | Required assertion |
|---|---|
| Allowed delta | Exactly one TIPD replacement, with the expected changed payload and every other raw record unchanged. |
| TIPD metadata | Raw name and header spelling, inode, mode, ownership, links, timestamps and device fields remain unchanged; only payload size and its alignment padding may change. |
| Indexes | Exactly the seven expected names; every payload remains bytes and byte-identical. This includes equivalent-looking or otherwise harmless changes. |
| Other records | ATC, packaged DWC3, I2C frontend, other modules, configuration, absolute symlink data and hardlink relationships remain unchanged. |
| Archive shape | No addition, removal, reordering, trailer/tail change or caller-crafted `Archive` model that disagrees with its raw bytes. |
| Payload identity | A no-op replacement or an expected payload that differs from the candidate is rejected. Structural fixture bytes cannot satisfy operational binary identity. |
| E binding | Wrong complete base bytes are rejected by the fixed E hash/size gate. The third operational attempt supplies the positive complete-image proof. The dedicated assembler authenticates and binds that exact proof. |
| E control header | Strict JSON with exact types, keys, E identity, 7/1,163 records, 200 modules, seven fixed index hashes and exact no-change/no-load flags. Reject W/199-module records, duplicates, booleans used as counts, non-finite values and changed index identities. This header alone is not a complete or authenticated control proof. |
| Existing dependencies | Real gzip roundtrip and malformed/truncated/concatenated/oversized failures; real single-link file hash checks and exclusive-create refusal. |
| Historical unbound pure operation | `image_contract.py` remains unchanged, with its unknown operational identities unset. Only the distinct fixed `assemble_t1.py` binds accepted real inputs. |

The expected new error classes/codes are `ImageContractError` with `ARCHIVE_MODEL`, `ARCHIVE_MEMBERS`, `ARCHIVE_TAIL`, `ARCHIVE_RAW_RECORD`, `TIPD_METADATA`, `TIPD_RAW_HEADER`, `TIPD_EXPECTED_PAYLOAD`, `TIPD_NO_CHANGE`, `INDEX_SET`, `INDEX_BYTES`, `INDEX_PAYLOAD_TYPE`, `E_BASE_IDENTITY`, or `E_PROOF_*`. Reused cpio and gzip dependencies retain their original exceptions. A dependency/setup failure is not a substitute for the selected contract assertion failures.

## Test-first handoff

Only the orchestrator may execute the reviewed runner in a fresh verified unprivileged sandbox. Do not run these files on the host. It uses four narrow source bindings and one test binding:

| Sandbox path | Read-only input |
|---|---|
| `/inputs/test` | This frozen `test_image_contract.py` file. |
| `/inputs/subject/image_contract.py` | The reviewed frozen subject for that run; no other files from its directory are required. |
| `/inputs/assembly/prepare_image.py` | Existing pinned `../image/prepare_image.py`, SHA `00caceb3b7fa236dcc030fb4007d0baa75bfa08fcd1590626f85fcc8c22d5f60`. |
| `/inputs/control/verify_control.py` | Existing pinned `../image/verify_control.py`, SHA `10b5afe6cff38df7b6ebe5619fd9a34935932a4b369f3a9ad2a51923c32932d8`. |
| `/inputs/helper/cpio_image.py` | Existing pinned `../image/cpio_image.py`, SHA `a32eddd159263d19ff87d7e9caee9d53d17ef5c350fbffe9e7eb142cb43ebf58`. |

The historical first RED command used the preserved incomplete subject. Do not replay it against the new implementation as RED evidence:

```text
/usr/bin/python3.14 -I -S -B /inputs/test ArchiveContractTests.test_tipd_only_zero_index_delta_is_accepted ArchiveContractTests.test_each_index_change_is_rejected
```

The sandbox supplies `/work` and `/tmp` as the only writable roots, the unchanged pinned runtime tools, and no host `/proc`, `/sys`, `/run`, `/boot` or `/home`. The runner authenticates all source bytes before execution. It then proves real fixture parsing, raw no-op reconstruction and the exact intended synthetic delta. Only then does it invoke unittest assertions against the selected subject. Sources and fixtures are rechecked afterwards. A setup/pin/import error exits 2, not semantic RED. Test errors also exit 2. Assertion failures with valid setup exit 1. The separate logs and JSON stay in `/work/t1-image-fixtures`; no candidate `.img`, module, depmod root or system file is written.

No test ran when the original drafts were authored. On 2026-08-29, the root task recorded RED in `run-ocsbbs4e`: setup PASS, the two specified assertion failures, zero errors, and unchanged sources/fixtures. The subject SHA was `b59d2d53c0bb8fd9394d7e01936cb00211547a11f83d81891bae117c98db946e`. The original source/runner snapshot remains preserved separately. This was a synthetic contract result, not an image or module result.

The reviewed full GREEN command ran all 15 existing methods with only the runner's subject SHA pin changed, in a fresh verified sandbox:

```text
/usr/bin/python3.14 -I -S -B /inputs/test
```

On 2026-08-29, `run-6nt0q6sz` passed all 15 methods in 0.060 seconds, with zero failures, errors or skips. Setup passed, source/fixture/input checks stayed unchanged, and the workload did not time out. Independent QA and root review passed. The exact five input bindings gave 590 read-only bindings with the unchanged runtime. The runner launched zero subprocesses and created no candidate image. Tested source SHA: `a1eda280aa56967aa06b01a2cca0dfc70c3da6df25066f8a1e815beec719f1bf`; runner SHA: `744a874b6c5657aec5894cb998374a2bff9649f617fe5e5e7c2d41bb930c1283`. The original two-test RED remains separate and is not coverage of the whole matrix.

## Gates not supplied by these fixtures

A later real control must reconstruct complete E exactly, not W and not an image containing the fresh rebuilt TIPD control. It must check 200 modules, 1,163 main records and the original early stream/tail. The saved E main stream is 61,286,668 bytes with SHA `7be7b4b03367b5ce4b356fe35977edba6540af0a7df930dbff990286c9b98e28`; its early stream is 10,240 bytes with SHA `967bc6adcff42e59abcfb4e509f6c80fd65588e0861d8c1c3189a135f10955b4`.

The real reduced-root depmod outputs, all 200 binary-only filename/dependency lookups, complete alias/symbol mappings, concrete frontend/DWC3/ATC aliases, TIPD export resolution and unchanged inputs need separate evidence. Preserve the existing exact generated-symbol versus retained-symbol exception; do not copy generated indexes into T1. The accepted binary must separately prove ELF/BTF, source-derived imports/exports, unchanged frontend/shared layouts and the wrapper allocation contract. A strict header and metadata equality cannot replace these checks.

The pure fixtures do not supply final image assembly, compression, output naming, candidate hash/size, proof authentication, no-replace staging, manual handoff, recovery or hardware acceptance. The distinct [fixed assembler contract](t1-assembly-contract.md) defines the private assembly and proof boundary. The [actual image result](../../../../docs/evidence/dev-147-t1-private-image-2026-08-30.md) is separate evidence. No staging or live/manual step is released. Preserve all prior helpers, images, proofs and seals. The root task owns later plan/evidence publication.
