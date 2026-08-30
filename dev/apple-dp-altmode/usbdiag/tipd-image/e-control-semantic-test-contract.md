# Fixed E raw-observation semantic gate: three-method RED contract

Status: the replacement RED and first minimal GREEN below are retained history. Their subject, helper, runner, and aggregate pins are historical. The current recipe SHA is `1be81904b29c69cb24fae86208c62fb30e830eca46250978a65d8ed19db8de77`, helper SHA is `686d59e63166df1bef1afad27998a6d58f4c28b6b4439b6ccd607b56471268ca`, and semantic runner SHA is `bf6f8b271a139b4cff09bb97e02d39cfc82cbd9726efedf4a4dc85bff4785483`. Two production attempts failed closed and exposed gzip and lookup grammar. Current zero-production-child semantic run `run-trmsyl6z` passed 3/3 with 606 unchanged read-only mounts. Its aggregate remains `5f80a3cf89e2c21e9f694cb8ed47a062aa44003f554ceb18f5de3fc87ea6ebf0`. [Independent QA](../../../../docs/evidence/dev-147-e-lookup-correction-independent-qa-2026-08-30.md) repeated 3/3 in `run-_y7n3i3t`; final review passed with no blockers. The later [third operational attempt](../../../../docs/evidence/dev-147-e-operational-third-attempt-pass-2026-08-30.md), not this fixture, now supplies the fresh E-control PASS.

## Result boundary

This gate creates a real fixture tree and real fixture files. It does not run a command. It builds 424 complete stdout, stderr, and JSON report triplets. Each triplet binds its fixed stdout, stderr, and report path, raw bytes, byte count, SHA-256, all nine identity fields, mode, UID, GID, link count, report bytes, command, order, observed bytes, retained bytes, status, return code, stdin identity, elapsed value, PID, kill state, and reap state.

Every report has `status=FIXTURE_ONLY`, `executed=false`, `pid=null`, `killed=false`, `reaped=false`, and `returncode=null`. `observed_bytes` equals `retained_bytes`. The retained stdout stays at or below 67,108,864 bytes. Stderr stays empty and below 65,536 bytes. Each JSON report stays below 131,072 bytes. These records are synthetic observations. They are not successful children.

The aggregate status is `NONFRESH_FIXTURE`. These fields are all false:

- `all_records_executed`
- `structural_control_proved`
- `operational_control_proved`
- `fresh_control_proved`
- `image_created`
- `module_loaded`
- `staged`
- `booted`

The twelve historical C2 files are fixtures only. They do not prove a fresh depmod, lookup, gzip, archive-tool, image, load, stage, boot, USB-data, charging, or power-control result. No fixture input can become operational provenance. At this historical checkpoint, the real `/work/e-control-result.json` and all real control paths were absent. `operational_policy()`, `finalize_operational_result()`, and `main()` were closed with `E_CONTROL_RECIPE_UNAVAILABLE`.

## Fixed raw outputs

The independent plan has exactly 424 commands.

| Index | Family | Exact fixture stdout |
|---:|---|---|
| 0-1 | Early archive lists | Same 47 bytes, SHA `62d818f030037bc3bbfc080899def7a67770961cc81d821ab750dcd06ea974cd` |
| 2-3 | Main archive lists | Same 42,863 bytes, SHA `90e515cd5008382d737295497faf85f8fe530a19eca8bad4097cf0eb78e36633` |
| 4 | GNU gzip | Exact `E[10240:]`: 19,181,273 bytes, SHA `375aa35be0ea57fa8d3f79f20cfa70373742ba6e2afda409462497d0d96ad724` |
| 5-8 | Payloads | Exact four E module payloads |
| 9 | depmod | Empty |
| 10-11 | `--show-config` | Same historical 97,151-byte dump, SHA `c562726938a6e3d11d5b3661352508f00b74efd9cbadbb559c3680663da72c05` |
| 12-411 | 200 module pairs | Exact filename and dependency bytes |
| 412-414 | Aliases | Exact resolved dependency bytes |
| 415-423 | Symbols | Exact resolved dependency bytes |

The gzip child stdout is only the compressed tail. Prefixing it with the exact 10,240-byte early archive must reconstruct exact E: 19,191,513 bytes, SHA `4d4f0557af57eebcc33322f004bcc7968254e644b069a11102375df0b31a52ae`.

The archive lists contain newline-terminated ASCII member names in archive order. Directories have one trailing slash. The cpio and bsdtar bytes are identical for each archive.

The payload identities are:

| Payload | Bytes | SHA-256 |
|---|---:|---|
| `tps6598x-core.ko` | 1,213,760 | `bc02723db427639c6586d29eea7918e084874c741b60bf145585c6349fd07d70` |
| `tps6598x.ko` | 12,368 | `f9b9e0f01270016b72cf242178eeb2810e32888e2cd6e68cf0d6f549500e1308` |
| `phy-apple-atc.ko` | 66,512 | `fd1c3d105bd69a649a38e89e2ca0bcbe6f656200a0f211d58211e8c7b3ec944b` |
| `dwc3-apple.ko` | 20,312 | `d150400f9782c876972b2745d95617cd44e23574452f63980704911a467f7767` |

Each filename output ends with one newline. Each dependency output puts builtin rows first. Only `lrw` has `builtin ecb`. It then uses the reversed `modules.dep` row and the target. Each `insmod` row has one space before its newline. The three aliases resolve to `tps6598x`, `dwc3_apple`, and `phy_apple_atc`. All nine symbols resolve to `tps6598x_core`.

## Real fixture trees

The runner creates two distinct roots. It does not call `Commands.run()`, `subprocess`, or a mock API.

- `/work/e-control-semantic-fixture-control-root-s1` starts with 200 exact E modules and the three exact depmod inputs. `verify_control.snapshot()` captures 48 directories and 203 files. The runner adds the exact eleven historical generated outputs. A second snapshot must contain the same 48 directory identities and 214 files. Every one of the original 203 `FileState` values must be unchanged.
- `/work/e-control-semantic-fixture-lookup-root-s1` contains independent copies of the 200 exact E modules and the seven exact retained E indexes. Its before and after `TreeState` values must be identical: 48 directories and 207 files.

Directory and file identity use the exact nine-field stat tuple. `FileState` also binds SHA-256. The runner retains and tests the root identity, every directory identity, every tree file identity, all 1,272 command-file identities, and the fixed stream/config identities. It mutates all nine tuple slots for every retained identity record. Logical ordinals are not identities.

The generated index sizes are 73,869, 37,491, 12,558, 18,359, 0, 76, 31,021, 70,982, 10,998, 26,189, and 55 bytes in the fixed `HISTORICAL_BYTES` mapping. The generated `modules.symbols.bin` SHA is `5077fb001a5c48a2135ce8f651606b18578610bc660f430a59114e76be4f9437`. The retained file is a different 31,021-byte object with SHA `a3f1e745b7675daaec99c7c7ebadc7d67b318143901e063674494c210b12ace6`. The other six retained outputs are byte-identical to their generated counterparts.

## Future API and mapper boundary

The GREEN implementation must add this fixed boundary. The family validators each accept one mapped bundle. Each family reaches its matching observation validator. The observation validators provide bounded item checks for the corruption table.

```text
_map_raw_control_outputs(raw_files)
_collect_fixed_raw_files(paths)
_read_fixed_semantic_fixture_outputs()
_read_fixed_operational_outputs()
_validate_archive_family(mapped)
_validate_payload_family(mapped)
_validate_tree_family(mapped)
_validate_index_family(mapped)
_validate_module_family(mapped)
_validate_alias_family(mapped)
_validate_symbol_family(mapped)
_validate_command_family(mapped)
_validate_identity_family(mapped)
_validate_provenance_family(mapped)
_validate_archive_observation(label, raw)
_validate_payload_observation(name, raw)
_validate_tree_observation(kind, before, after)
_validate_index_observation(kind, name, raw, observation)
_validate_module_observation(name, filename_raw, dependency_raw)
_validate_alias_observation(alias, raw)
_validate_symbol_observation(symbol, raw)
_validate_command_observation(index, observation)
_validate_identity_observation(observation)
_validate_provenance_observation(provenance)
_evaluate_control_semantics()
```

`RawControlFiles`, `MappedControlOutputs`, and `SemanticFixtureEvaluation` are required types. `MappedControlOutputs` has one field, `raw_files`. The mapper has one return statement: `MappedControlOutputs(raw_files=raw_files)`. It retains the exact complete `RawControlFiles` object by identity. It cannot reduce the input to a hash, flag, token, selected record, or caller assertion. `SEMANTIC_RECORDS` is literal `424`. `SEMANTIC_FIXTURE_PATHS` and `SEMANTIC_OPERATIONAL_PATHS` are literal six-item policies. The fixture policy names the distinct record, control, lookup, empty-config, early, and main fixture paths. The operational policy names the corresponding fixed real paths.

The two readers accept no argument. Each directly calls `_collect_fixed_raw_files()` with its one literal policy. It passes the returned bytes directly to `_map_raw_control_outputs()`. The collector unpacks all six policy slots once and in order. It snapshots the record root. Its reachable generator iterates exactly `range(SEMANTIC_RECORDS)`. For each index, it calls `read_regular()` on exactly `record-NNN.stdout`, `record-NNN.stderr`, and `record-NNN.json` below the record root. It separately snapshots the control and lookup roots. It reads the empty-config, early, and main files. Its final `RawControlFiles` binds the policy, three snapshots, all 424 raw triplets, and all three fixed stream reads. No token-only, one-read, hard-coded, dead-branch, or path-only return can satisfy this shape. The mapper accepts only `raw_files`. Its return derives from that argument. The later operational reader has the same fixed raw-reader and mapper shape, but this fixture RED never calls it. No reader accepts a caller-built result, path, proof, identity, environment override, trust flag, or alternate root.

The aggregate accepts no argument. Its first statement reads the fixture output. It then calls every family validator once, in the listed order, as reachable top-level statements. Every family passes data from `mapped.raw_files` to its matching observation validator. The aggregate return derives from the same data. Nested, duplicate, dead, aliased, or unresolved validator calls are invalid. The reachable reader, collector, mapper, family, observation, evaluator, existing plan, E-selection, and regeneration closure is transitively read-only. It permits only a closed set of authenticated constructors, validators, hashes, fixed reads, and snapshots. It rejects imports, nested functions, dynamic attribute lookup, deletes, arbitrary calls, subprocesses, and all file mutations. A digest-only shortcut is invalid.

The command observation validator first checks exact schemas, keys, types, bounds, paths, commands, status, execution metadata, and identities. It then recomputes byte counts and hashes from raw bytes. It validates every stdout, stderr, and report identity. Every record requires exact equality between observed and retained bytes. For any later successful child, it must also require `status=ok`, `executed=true`, a non-null PID, `reaped=true`, `killed=false`, return code zero, empty stderr, and equality under the fixed caps. The fixture family remains separate and cannot satisfy that rule by changing its flags. Metadata rejection must not repeatedly copy or hash the 19,181,273-byte gzip fixture.

The runner records a deterministic aggregate digest candidate. It excludes volatile device, inode, and time numbers from the digest. The identity family still validates those exact captured values separately. After independent QA accepts the RED, a reviewer must replace `EXPECTED_AGGREGATE_SHA256 = None` with the exact reviewed literal candidate. This pin must happen before any subject implementation or GREEN run. A setup-derived value is not an accepted GREEN pin.

## Exact three-method RED

The runner contains exactly these methods:

1. `test_a_full_fixed_e_historical_vector_is_nonfresh` first asserts that the mapper, fixed collector, both fixed readers, every family and observation validator, `SemanticFixtureEvaluation`, and the aggregate exist. The pre-GREEN subject at commit `2ccf53be13220539e1f3f6d30f688d8adbaaa56e` must stop at this assertion. After GREEN, it compares both literal path policies and the independent plan, checks reachable aggregate data flow and the closed read-only call graph, requires the literal aggregate pin, and calls the collector. It compares the returned paths, record-tree snapshot, all 424 raw triplets, both fixture-tree snapshots, empty config, exact early archive, and exact main archive. It requires the mapper to retain that same complete object by identity. It then validates the exact nonfresh evaluation and checks that the three operational APIs remain closed.
2. `test_b_each_semantic_corruption_refuses_without_publication` first asserts the same missing boundary and then rechecks the closed source shape before any subject validator call. After GREEN, it checks all 424 raw command records. For every record it mutates and removes every report field, both retained and observed byte slots, every stdout, stderr, and report-file field, each of the nine identity slots in each file, report raw bytes, every top-level key, and unknown keys. Record 4 binds the exact main-archive stdin hash and 61,286,668 bytes. Every other record binds null stdin hash and zero stdin bytes. It also checks all 200 module mappings, four payloads, eleven generated indexes, seven retained indexes, three aliases, nine symbols, all nine identity fields in every captured identity record, and every provenance field. Every corruption raises exactly `E_CONTROL_SEMANTIC_INVALID`. It uses shallow copies and bounded observation calls. It does not repeat an aggregate evaluation or copy the 19 MiB gzip fixture for metadata mutations.
3. `test_c_fixture_publication_is_no_replace_rename_last_and_fail_closed` first asserts the missing publisher boundary. After GREEN, it checks the exact ctypes binding. A direct missing-source rename raises `E_CONTROL_SEMANTIC_INVALID`. A direct existing-target rename raises `E_CONTROL_SEMANTIC_EXISTS` and preserves both full `FileState` identities. An unexpected `/work` member refuses before evaluation. Independent stale pending and stale final files each preserve their full identity and refuse. One valid call writes the distinct nonfresh fixture result. A second call preserves the full final identity and creates no pending file.

At clean commit `2ccf53be13220539e1f3f6d30f688d8adbaaa56e`, the named APIs are absent. With valid setup, the first run must have exactly three controlled assertion failures, zero errors, and zero skips. Setup, import, authentication, identity, fixture, postcheck, or syntax failure is not accepted RED.

The exact inner command is:

```text
/usr/bin/python3.14 -I -S -B /inputs/test EControlSemanticRedTests.test_a_full_fixed_e_historical_vector_is_nonfresh EControlSemanticRedTests.test_b_each_semantic_corruption_refuses_without_publication EControlSemanticRedTests.test_c_fixture_publication_is_no_replace_rename_last_and_fail_closed
```

## No-replace publication contract

The only pending path is `/work/e-control-semantic-fixture-pending.json`. The only final path is `/work/e-control-semantic-fixture-result.json`. The result kind is `dev147-e-control-semantic-fixture-result-v2`. Its status is `NONFRESH_FIXTURE`. It contains no real `PASS` and no true structural, operational, fresh, image, load, stage, or boot claim.

`RENAME_NOREPLACE` must be literal integer `1`. `_AT_FDCWD` must be literal `-100`. The module imports `ctypes`, `errno`, and `os` directly and once. `_SEMANTIC_LIBC` binds `ctypes.CDLL(None, use_errno=True)` directly after the error callback. The exact binding is:

```text
_SEMANTIC_LIBC.renameat2.argtypes = [
  ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint,
]
_SEMANTIC_LIBC.renameat2.restype = ctypes.c_int
_SEMANTIC_LIBC.renameat2.errcheck = _rename_noreplace_errcheck
```

The three-argument error callback calls `ctypes.get_errno()` exactly once after a nonzero result. `errno.EEXIST` raises exactly `E_CONTROL_SEMANTIC_EXISTS`. Every other nonzero result raises exactly `E_CONTROL_SEMANTIC_INVALID`. A zero result returns the original result. `_rename_noreplace(source, target)` has one statement. It directly calls `_SEMANTIC_LIBC.renameat2(_AT_FDCWD, os.fsencode(source), _AT_FDCWD, os.fsencode(target), RENAME_NOREPLACE)`. That real libc call is the helper's last operation. The module cannot later rebind or delete the imports, libc object, function, constants, ABI attributes, fixed paths, semantic APIs, or publication functions. The source check rejects direct aliases, callable values hidden in containers or subscripts, indirect call targets, import aliases, exception-handler names, match-capture names, and argument shadowing. It also rejects a shim, `getattr`, `setattr`, `delattr`, `Path.unlink`, overwrite helper, link helper, or subprocess path.

`SEMANTIC_FIXTURE_WORK_MEMBERS` is the exact sorted baseline fixture membership. `_semantic_fixture_work_membership()` has no argument. It directly returns the `frozenset` of `path.name` from `Path("/work").iterdir()`.

The no-argument publisher has exactly eleven reachable statements. It first captures membership. It checks both stale paths and exact membership before evaluation. It then prepares the shared evaluation, result bytes, all acceptance fields, and every hash. It captures membership again and consumes an exact equality with both the first value and fixed membership. It exclusive-writes only the fixed pending path. Its penultimate statement is exactly `_rename_noreplace(SEMANTIC_FIXTURE_PENDING, SEMANTIC_FIXTURE_RESULT)`. Its final statement returns the precomputed acceptance. No read, hash, stat, cleanup, validation, or other fallible operation occurs after final creation. The result-byte helper consumes the prepared evaluation. Its transitive call graph is closed and read-only. It cannot call the evaluator again.

Before the runner executes `run_e_control.py`, it parses the authenticated source. The import-time shape allows only reviewed direct imports, pure constants, exact frozen dataclasses, safe annotations and defaults, the exact libc binding, function definitions, and the exact `__main__` guard. A binding ledger authenticates every critical imported callable, builtin, existing helper, future semantic helper, and result type. It rejects assignment, annotation assignment, augmented assignment, named-expression binding, import replacement, argument shadowing, exception or match capture, global or nonlocal declaration, delete, duplicate definition, wrong definition scope, attribute mutation, and later rebinding. Critical callable values can occur only at direct calls, annotations, exact type checks, reviewed higher-order calls, class bases or decorators, exception types, and the one exact `errcheck` binding. Composite containers, subscripts, aliases, and indirect call targets are invalid. The source check also rejects executable top-level expressions, dynamic attributes, child-process APIs, and file mutations. The pre-GREEN subject at commit `2ccf53be13220539e1f3f6d30f688d8adbaaa56e` must therefore reach the three missing-API assertions without a setup error.

## Authentication and limits

The sandbox has 21 task inputs. With the unchanged 582-entry runtime manifest, `/inputs/proof`, and two fixed `/sandbox` inputs, the predicted read-only total is 606. The task inputs are the test, recipe, five frozen source files, exact E, the one three-file index directory, and the same twelve historical `g-*` files. `/work` initially contains only `descriptor-sentinel`, `probe-write`, `stdout.log`, and `stderr.log`. The runner checks exact membership after setup and after every publication case.

The accepted source pins are:

- recipe: `70f369f87942b6ca6826c808536353ae0cc400123204040b9c005995ab43c3e3`
- `e_control.py`: `abbf59410a05fd5c789820df3d40e59d0a5c33cf1204ab93c7aeef806da7b1df`
- `image_contract.py`: `a1eda280aa56967aa06b01a2cca0dfc70c3da6df25066f8a1e815beec719f1bf`
- `prepare_image.py`: `00caceb3b7fa236dcc030fb4007d0baa75bfa08fcd1590626f85fcc8c22d5f60`
- `verify_control.py`: `10b5afe6cff38df7b6ebe5619fd9a34935932a4b369f3a9ad2a51923c32932d8`
- `cpio_image.py`: `a32eddd159263d19ff87d7e9caee9d53d17ef5c350fbffe9e7eb142cb43ebf58`

The runner requires isolated Python 3.14, UID/GID 1001, exact input membership, unchanged full input identities, no visible host tree, zero workload children, and no real result. The retained limits are 30 seconds per future child, 270 seconds internal control, 280 seconds workload, and 285 seconds outer timeout.

## Checkpoint history

### Accepted original operational RED

Retained run `run-z0i8_dzw` accepted the original three-failure operational RED. These pins remain historical evidence. This semantic checkpoint does not replace them.

| Artifact | SHA-256 |
|---|---|
| Incomplete subject | `7dc80a121f563d3ffda9a876b2871fff294d8a911c4ea7176a85b2b5054a17b8` |
| Unchanged 16-method runner with RED pin | `5c791970e9bfd06165a142f71d99b933aad530b0d7b38e42b13c6ffde99771c7` |
| Original three-method operational runner | `3cdde469e0e2a3a0b02bc6eda2ed898ee3555aa5139f35f6b33ba4fe5b065330` |
| Original operational RED contract | `21370877fa19a577749c183336de3739b2590166199c2cdb2fbf7376a2cbf53e` |

### Rejected model-only semantic candidate

The private `e-semantic-red-rejected-v1` snapshot was rejected before execution. It used modeled files and logical identities instead of complete raw observations and real fixture trees. No result from it is evidence.

| Artifact | SHA-256 |
|---|---|
| Rejected semantic runner | `c66b7df25b3eefe08ca5d16100b31ccc707011df1941a89f825500a7b0f3baf0` |
| Rejected semantic contract | `e3af74799a0a08ab7a4b65a18e3e526c57f2ddf698b9ff2989c478cf577fb360` |
| Rejected README | `0072ea7776d9caea75c1370eb4dc84825cac9932c7531d71178f5a2ae93d6ad6` |

### Rejected raw-observation candidate v2

The private `e-semantic-red-rejected-v2` snapshot was rejected before execution. It added real fixture trees and raw observations, but its ctypes binding, publisher data flow, fixed-reader reachability, mutation coverage, and stale-file identity checks were not strict enough. No result from it is evidence.

| Artifact | SHA-256 |
|---|---|
| Rejected-v2 semantic runner | `a19d1ab4ff514672169492bc76daa850207fe2eb0d5e6b37ac71795e3ac803f8` |
| Rejected-v2 semantic contract | `26a4d618bafe91104ad1e928ecc30b6f7fe4a1f5ceaae8accda245d46118040c` |
| Rejected-v2 README | `c5753c9c7eed7b83e65eda6c381aca61a7af896ff0e726ad3989c501586a6ece` |

### Accepted corrected raw-observation RED and GREEN

`run-nqnr8soj` is the accepted replacement RED. Setup passed. It produced exactly three expected assertion failures, zero errors/skips, zero workload children, and no result. Its runner is preserved in commit `af2f2d6c137e39930415e86f6cb663f6eb5d8c7b`.

`run-vfbn_07m` is the accepted GREEN. It passed 3/3, checked all 424 triplets, and produced the pinned aggregate `68dd45eeeb9239b873c293b81cbbb5b7403d4ff0d5d1b5a32f3e27c14c92d44e`. The only result was `NONFRESH_FIXTURE`; every operational, fresh, image, load, stage and boot field was false. Independent QA and safety review passed.

`run-6swsqrwz` and `run-flf195ba` are retained fail-closed GREEN attempts. The first exposed an AST-runner field error. The second exposed a publication-helper source-shape error. Neither ran a workload child or produced a real result.

| Artifact | SHA-256 |
|---|---|
| Accepted subject | `70f369f87942b6ca6826c808536353ae0cc400123204040b9c005995ab43c3e3` |
| Historical 16-method runner | `ab7e297f9b80f787a8137876df4d056208e2b74d237db71e2aefba3f7c3e956f` |
| Historical structural runner | `8816d63874b1590c24b5ac468d38a644896836a6dc76dcc7df4aaf6b5d2b2c70` |
| Accepted semantic runner | `4c14f023d719dd4e709e424812d53f96ab535fdeb7de2461e5b1c63a813099b2` |

The structural regression `run-f0tjlamv` and pure recipe regression `run-m64c0_of` also pass after independent QA and safety review. Do not overwrite the accepted operational RED history.

That checkpoint's next gate was a new zero-child execution RED and exact eight-input launch contract. The current status and next gate are in the superseding note at the top of this document.
