# E-only control boundary: tested GREEN

This is the narrow runner, reduced-root and ordered-lookup contract for the [T1 image boundary](README.md). The original three-test RED is preserved below. On 2026-08-29, the full GREEN run passed 18 methods and 11 harmless children. Its operational entry still raises `E_CONTROL_UNAVAILABLE`. The existing T1 assembler gate also remains closed.

Only the root task may execute the reviewed files in a fresh verified unprivileged sandbox. These fixtures do not accept real E, a real module, a saved W proof or a candidate identity. The 200 fixture module payloads are labelled ASCII text. The seven index payloads are also synthetic. They cannot prove ELF, index semantics, ABI, hardware behaviour or a usable image.

## Narrow boundaries

| Boundary | Fixture requirement |
|---|---|
| Child input and output | A real GNU gzip stdin roundtrip through a checked regular, single-link, hash-bound file. Keep raw stdout, stderr and a separate result record in exclusive-create files. Reject symlinks, hardlinks, missing/wrong inputs and paths outside fresh `/work`. |
| Active limits | Drain both pipes under active byte caps. Retain at most the cap; observe one extra byte to prove overflow, then kill and reap. Reject nonzero exit or nonempty stderr. Apply per-child and cumulative monotonic deadlines, not only a post-exit size check. No retry. |
| Runner scope | Accept only the six fixed control tools and exact reviewed argument forms. No shell, load operation, inherited command text or arbitrary Python. The five original literal Python cases in `SELF_CHECKS` remain unchanged. Two added literals write nine bytes to stdout or stderr, then wait five seconds. These harmless fixtures test active caps; the real E workload must not use any of them. |
| Runner bounds | At most 424 children per runner, 270 seconds cumulatively, 30 seconds per child, 64 MiB stdout and 64 KiB stderr. The outer workload remains limited to 280 seconds, with a 285-second outer timeout. The count-limit fixture seeds the counter at 424; it does not run 424 children. |
| Fresh roots | Only `/work/control-root` and `/work/lookup-root`. Require exactly 200 unique safe module paths with bytes payloads. The first root receives exactly the three depmod text inputs. The second receives exactly seven binary-image index files, with no text-index fallback. Refuse any existing root; do not overwrite, remove or repair it. |
| Root proof | Return the real pinned `TreeState` snapshot. Require exact file membership, payload hashes and single-link metadata. A later snapshot must match. Deliberate mutation affects only a disposable fixture output and must be rejected. |
| Ordered lookup | Parse real bounded dry-run text through the authenticated pure dependency parser. Require the exact reverse of the ordered `modules.dep` closure followed by the target. Reject missing, extra, duplicate, reordered, unsafe or malformed records. Only `lrw` may produce the single builtin `ecb`; no other builtin is permitted. |
| Operational gate | These fixture helpers do not reconstruct E or assemble T1. `main()` must continue to refuse. Actual orchestration needs a separate reviewed entry, fixed inputs, proof contract and command list. Do not turn the fixture gate into a configurable bypass. |

The full suite has 18 methods: all 16 original method bodies and two added active-limit methods. The setup first authenticates the source chain, real file guards, a zlib single-gzip roundtrip and the five literal dependency entries. It also checks the intended correct lookup against the pinned parser independently of the new subject. Setup launches no child. No old main, archive/index workload, global rebinding or import-time inspection script is used.

The new method tests stdout and stderr separately. Each child writes nine bytes and stays alive for five seconds. With an eight-byte cap, the runner must return `CHILD_OUTPUT_LIMIT` in less than two seconds, before either the four-second timeout or normal child exit. The test requires eight retained bytes, a SIGKILL exit, and independent `waitpid`/signal-zero checks that the child was reaped and no longer exists. It saves the independently measured duration and observations in two `long-cap-*.json` files. A post-exit truncation implementation cannot satisfy these checks.

The second added method uses the unchanged one-second wait command. It tests a 0.2-second per-child deadline and a 0.2-second cumulative deadline. Both must kill and reap the child in less than 0.8 seconds, with SIGKILL and the same independent process checks. The cumulative case must also refuse a second child without incrementing the count or creating its result. Two separate observation files retain the independently measured durations and checks. Pre-execution review added these cap/deadline cases before the first GREEN run. They are coverage refinements, not a failed GREEN or another RED.

The original control helper's `TreeState`, snapshot model and pure parsers are dependencies only. Its W identity, 199-module main, old subprocess runner, old root builder and proof acceptance are not authority for E. The later runner must preserve the fixed tool environment and source/input pre/post checks. The existing typed-stdlib/dataclasses/unittest no-install exception applies. This document does not claim lint, type-check or full-repository test results.

## First RED: retained three assertion failures (historical)

The root task ran this exact selection against the preserved incomplete subject. Do not replay the current implementation as RED evidence:

```text
/usr/bin/python3.14 -I -S -B /inputs/test EControlTests.test_runner_gzip_regular_stdin_roundtrip EControlTests.test_lookup_root_exact_files_and_no_replace EControlTests.test_reordered_dependency_is_rejected
```

The three intended failures were:

1. `None` is not a bounded gzip `bytes` result.
2. `None` is not a real `TreeState` for the lookup root.
3. The reordered lookup does not raise the required `LOOKUP_ORDER` refusal.

All three occurred inside unittest assertions after valid setup. They were not import, pin, missing-file, executable, compile or test errors. On 2026-08-29, `run-m1rni4vb` recorded setup PASS, three assertion failures and zero errors. The root task and independent QA accepted this RED. The incomplete subject launched zero children and created no reduced root or image. The original three files are preserved at commit `ae4821ccdc0d12e54a67fbfe0d5578f9b26e7ffa`: subject SHA `a91506e45d5d024deb2b389f8a85092faa1685fabdf92b88c7b61b2f51510d7a`, runner SHA `eafbc0414482ed6d340900b278114445840ca8169ad346ea04933b210762c49a`, and contract SHA `0614fa1ae54393ac7b41aa90b971761ec261bbd97b04b13a3cd66c1d00368ca2`. No entire-suite RED was claimed.

## Full GREEN: executed 2026-08-29

After independent source review, the root task ran the complete fixture suite in a fresh verified sandbox:

```text
/usr/bin/python3.14 -I -S -B /inputs/test
```

The runner accepts only the historical three-test selection or this complete 18-method suite. It writes `setup.json` and `test-result.json` below `/work/e-control-fixtures`. It rechecks all pinned source identities and immutable fixture bytes after the assertions. Setup, postcheck, test errors or skips exit 2. Assertion failures with valid setup exit 1. A complete GREEN requires 18 methods, zero failures/errors/skips, 11 harmless child records and unchanged inputs. The 11 children are one gzip, two short overflow cases, exit 7, nonempty stderr, the two original deadline cases, two long-lived overflow cases and two added active-deadline cases. No archive tool, depmod, modprobe or modinfo workload is part of this fixture run.

| Read-only sandbox path | Frozen input |
|---|---|
| `/inputs/test` | This `test_e_control.py`; the outer launcher pins its exact bytes. |
| `/inputs/subject/e_control.py` | Tested GREEN subject SHA `abbf59410a05fd5c789820df3d40e59d0a5c33cf1204ab93c7aeef806da7b1df`. |
| `/inputs/contract/image_contract.py` | Existing pure T1 contract SHA `a1eda280aa56967aa06b01a2cca0dfc70c3da6df25066f8a1e815beec719f1bf`. |
| `/inputs/assembly/prepare_image.py` | Authenticated pure source SHA `00caceb3b7fa236dcc030fb4007d0baa75bfa08fcd1590626f85fcc8c22d5f60`. |
| `/inputs/control/verify_control.py` | Authenticated pure source SHA `10b5afe6cff38df7b6ebe5619fd9a34935932a4b369f3a9ad2a51923c32932d8`. |
| `/inputs/helper/cpio_image.py` | Authenticated pure source SHA `a32eddd159263d19ff87d7e9caee9d53d17ef5c350fbffe9e7eb142cb43ebf58`. |

Use only these six inputs with the already reviewed fixed runtime. Single-file source mounts or source-only directories are sufficient; do not bind old run directories. The expected read-only mount count is 591: 582 runtime entries, three fixed sandbox files and six inputs. `/work` and `/tmp` are the only writable roots. No host `/proc`, `/sys`, `/run`, `/home`, `/root` or `/boot` is visible. No dependency installation or tool-manifest repin is allowed.

The retained run is `run-0z8qsjmd`: setup and postchecks pass, 18 methods pass in 1.244 seconds, and all 11 expected child records exist. There are no failures, errors or skips. The outer workload exits 0 without timeout; all 591 read-only input fingerprints match. Both long-lived overflow children were killed and reaped in under 0.007 seconds. The active per-child and cumulative deadline cases completed in under 0.204 seconds. Each independent process check observed ECHILD and ESRCH. These are fixture observations, not a live-system safety guarantee.

Runner SHA is `23eb117db32fe651a2a9574782c47afce5ced99c4e0c4267a168a6786d1caa9e`. The private pre-execution contract remains unchanged at SHA `323891076c027b5932924d27b2c2d10c801ba2f44f5599b8e86039210587a7cf`; this public document adds the later result. The original RED, source/test bytes, and outputs are retained. The test runner's pre-execution wording is historical, not a second run.

## Later real E control: separate evidence gate

This fixture GREEN covers these boundaries only. The actual E control remains a separate unexecuted gate. It must independently authenticate the exact E image: SHA `4d4f0557af57eebcc33322f004bcc7968254e644b069a11102375df0b31a52ae`, 19,191,513 bytes. It must retain the original TIPD payload, not the fresh rebuilt control. It must prove the exact early/main archive streams, all 200 module identities, raw no-op reconstruction and byte-exact GNU gzip output. The [image contract](README.md#gates-not-supplied-by-these-fixtures) retains the fixed stream hashes and limitations.

The planned real workload has exactly 424 fixed children:

| Observation | Children |
|---|---:|
| Early/main list with GNU cpio and bsdtar | 4 |
| No-option GNU gzip with checked regular-file stdin | 1 |
| Four selected module payload reads to stdout only | 4 |
| Fresh reduced-root depmod | 1 |
| Generated and retained binary index dumps | 2 |
| Filename and exact ordered dependency lookup for all 200 modules | 400 |
| Front CD321x frontend, DWC3 and ATC alias lookups | 3 |
| Nine TIPD exported-symbol lookups | 9 |

Before execution, a separate review must confirm every path, tool/source/input pin, complete alias/symbol normalization and multiplicity check, result schema and immutable-root readback. Preserve the exact previously reviewed generated-symbol-index exception. It does not permit replacement of any of the seven final E index bytes. Unexpected command count, output, ordering, index or source drift means HOLD. It never permits adaptive retries, repinning, text fallback, a broader delta or automatic T1 assembly.

The final complete control proof must bind the actual raw archive, module, index, lookup, child and before/after root records. Write the final result only after all checks pass. The existing strict header alone cannot satisfy this gate. Accepted T1 binary identity and the complete fresh E-control proof remain unbound operational inputs. No candidate image, staging helper, privileged preflight, module load, cable action or boot is authorized by this fixture draft.
