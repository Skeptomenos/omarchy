# Fixed E-only structural boundary before operational control

Status: the corrected zero-child structural GREEN and its original pins below are retained history. The current corrected recipe SHA is `57d35a30de9b351bcbaf0b78a1be186c8c44a2fbfb378d8f0b801e6e9256a7a9`, the helper SHA is `16016875e731e88d047eb805c7c6d03045300abdb262361b18010a952adb7b80`, and the structural runner SHA is `f4419eeab9d713f9f42c2467aecb8c2eb582e5f4271669c9833aab5e997ca72c`. Independent QA `run-qv63ivbi` passed 3/3 with 594 unchanged read-only mounts and zero workload children. One later production attempt failed closed. The corrected production entry has not run, so there is no fresh E-control PASS. Nothing in this structural checkpoint creates a real control result, constructs an image, stages, boots, or changes hardware.

## Provenance history

### Accepted RED

`run-z0i8_dzw` accepted the original three-test RED. Setup passed. The three selected assertions failed as intended. All 594 read-only inputs stayed unchanged. No control-workload subprocess started.

| Artifact | SHA-256 |
|---|---|
| Incomplete subject | `7dc80a121f563d3ffda9a876b2871fff294d8a911c4ea7176a85b2b5054a17b8` |
| Unchanged 16-method pure runner with RED pin | `5c791970e9bfd06165a142f71d99b933aad530b0d7b38e42b13c6ffde99771c7` |
| Original three-method operational runner | `3cdde469e0e2a3a0b02bc6eda2ed898ee3555aa5139f35f6b33ba4fe5b065330` |
| Original RED contract | `21370877fa19a577749c183336de3739b2590166199c2cdb2fbf7376a2cbf53e` |

The pure E recipe remains GREEN at `run-7vguug70`. Its historical assertion RED remains `run-9fmdox3j`.

### Rejected first GREEN candidate

The preserved `e-operational-green-rejected-v1` snapshot was rejected before execution. It incorrectly let zero-child synthetic files mint `/work/e-control-result.json`, status `PASS` and `fresh_control_proved=true`. It also lacked the required final identity sweep, accepted observed bytes larger than retained bytes and performed fallible validation after result creation.

| Artifact | SHA-256 |
|---|---|
| Rejected subject | `0c13329bace1967cb8123fea02802f3b40eab345ddad7e179b69df02f488e4e6` |
| Rejected pure-runner pin | `cbd130d28edef9063303b5ebeeda616df3360260cd2a85de1f2e68899eecdcd8` |
| Rejected three-method runner | `44f98f10a1596b80a1b1d68c219a45ef2f41a8a921b40003d34318814aa58625` |
| Rejected contract | `f089ea7ba6888d16c022de769619a10a7d2ed279c2e02a2c90cee55cabe061ad` |
| Rejected README | `735b297f2641537d0bb31b1adb2a247cdbd4bd6d40573efb81e358bc4f7cd38c` |

No result from this rejected snapshot is evidence.

### Accepted corrected structural GREEN

| Artifact | SHA-256 |
|---|---|
| Corrected subject | `099be3713b7d7b40020de10ca38f0a943da3da60509acb153b2d3de390e44f1d` |
| Unchanged 16-method pure runner with corrected pin | `3409276733c14061cc89b88cbc3f14fddf27f3f089c260e1e1f7ed3721605d52` |
| Corrected three-method structural runner | `46c1a963549721aa9e03357c91019db73420dde972a74630f6c4bafb153c7d11` |

This document is not self-pinned. Record its final hash in external evidence after review.

Retained run `run-elj0pbjn` passed 3/3 with no timeout. Its complete 424-record and 1,272-file structural graph stayed structural-only. Test B created and exact-verified the positive structural result. Test C then removed it before both negative cases and intentionally left it absent. No real control path or result existed. The containment probe runs its own version and standard-library smoke subprocesses, so zero children means zero of the 424 control-workload commands.

## Corrected zero-child boundary (historical)

At this checkpoint, [run_e_control.py](run_e_control.py) kept `operational_policy()`, `finalize_operational_result()` and `main()` closed with `E_CONTROL_RECIPE_UNAVAILABLE`. Real status `PASS`, `fresh_control_proved=true`, real child evidence and `/work/e-control-result.json` stayed reserved for the later executed 424-command workload.

The corrected candidate exposes only:

- `structural_policy()`, which returns the exact eight input bindings, independently derived 424-command plan, `/work/e-control-structural-records-e1` and three distinct structural artifact paths.
- `finalize_structural_result()`, which can create only `/work/e-control-structural-result.json` with kind `dev147-e-control-structural-result-v1`, status `STRUCTURAL_PASS`, `children_executed=0` and `fresh_control_proved=false`.

The structural header, evidence, record kind, record filenames and paths are also distinct. Each record says `status=STRUCTURAL_ONLY`, `executed=false`, `returncode=null`, `pid=null` and `reaped=false`. It cannot be reused as a real `Commands.run()` report.

The finalizer requires exactly 424 ordered structural records and 1,272 fixed leaf files. It binds every leaf path, hash and metadata record. Retained and observed byte counts must be exactly equal. The explicit existing caps are 64 MiB for stdout, 65,536 bytes for stderr and 128 KiB for a JSON record. Successful structural stderr is empty.

The finalizer retains the full root identity and all 1,272 full leaf identities. Immediately before publication it rechecks the exact root identity, exact membership and every leaf identity. It also rereads and rechecks the structural header and evidence. It prepares the result bytes, hashes and frozen return value before this final sweep. It then exclusive-creates the structural result as its last operation and returns without a later validation step.

Missing, failed, reordered, extra, changed or unbound structural records raise exactly `E_CONTROL_INCOMPLETE`. The structural result remains absent. All real operational paths must also remain absent.

The existing `select_e()`, `validate_regeneration()`, `command_plan()` and closed `main()` bodies are unchanged. The existing 16 pure test method bodies and semantics are byte-for-byte unchanged. Only their literal subject pin changed.

## Corrected three-test contract

[test_e_control_operational.py](test_e_control_operational.py) still has exactly three methods:

1. `test_a_exact_eight_binding_and_424_structural_policy` requires the exact bindings, plan, record root and distinct structural paths. It also requires both real operational APIs to remain closed with `E_CONTROL_RECIPE_UNAVAILABLE`.
2. `test_b_distinct_zero_child_structural_acceptance` requires the exact structural result and acceptance object. It explicitly checks the structural kinds and statuses, `children_executed=0`, `fresh_control_proved=false` and absence of `/work/e-control-result.json`.
3. `test_c_missing_or_failed_record_refuses_without_structural_result` first removes one disposable record and then substitutes one fixed failed record. Both cases must raise `E_CONTROL_INCOMPLETE` with no structural result. The runner restores its own fixture.

The exact corrected inner command is:

```text
/usr/bin/python3.14 -I -S -B /inputs/test EOperationalRedTests.test_a_exact_eight_binding_and_424_structural_policy EOperationalRedTests.test_b_distinct_zero_child_structural_acceptance EOperationalRedTests.test_c_missing_or_failed_record_refuses_without_structural_result
```

The accepted GREEN has three passes, zero failures, zero errors and zero skips. Setup and containment passed. The run has zero executed control-workload commands, 594 unchanged read-only fingerprints, no timeout and no real control root, stream, result, image, stage or boot output.

## Exact input boundary

The corrected test has nine task bindings: the future eight operational inputs plus `/inputs/test`. The unchanged A2 launcher also supplies `/inputs/proof` and two `/sandbox` files. The expected read-only total remains 594. The later real workload returns to 593 because it omits `/inputs/test`.

| Sandbox target | Frozen input and guard |
|---|---|
| `/inputs/test` | Historical tracked runner; exact mode `0644`, UID/GID 1001, single-link and under 128 KiB. |
| `/inputs/recipe` | Historical tracked subject; exact mode `0644`, UID/GID 1001 and single-link. |
| `/inputs/subject/e_control.py` | SHA `abbf59410a05fd5c789820df3d40e59d0a5c33cf1204ab93c7aeef806da7b1df`; sole file in a private source directory. |
| `/inputs/contract/image_contract.py` | SHA `a1eda280aa56967aa06b01a2cca0dfc70c3da6df25066f8a1e815beec719f1bf`; sole file in a private source directory. |
| `/inputs/assembly/prepare_image.py` | SHA `00caceb3b7fa236dcc030fb4007d0baa75bfa08fcd1590626f85fcc8c22d5f60`; sole file in a private source directory. |
| `/inputs/control/verify_control.py` | SHA `10b5afe6cff38df7b6ebe5619fd9a34935932a4b369f3a9ad2a51923c32932d8`; sole file in a private source directory. |
| `/inputs/helper/cpio_image.py` | SHA `a32eddd159263d19ff87d7e9caee9d53d17ef5c350fbffe9e7eb142cb43ebf58`; sole file in a private source directory. |
| `/inputs/base` | Retained E SHA `4d4f0557af57eebcc33322f004bcc7968254e644b069a11102375df0b31a52ae`; exactly 19,191,513 bytes, mode `0600`, UID/GID 1001 and single-link. |
| `/inputs/index-inputs` | Exact retained three-file directory described below. |

The retained index input directory contains only:

| File | Bytes | SHA-256 |
|---|---:|---|
| `modules.order` | 73,113 | `497c8546d3131d01191f7a66b68047abce5e5235ae982890180007f55c51a927` |
| `modules.builtin` | 10,592 | `74de5bab05fe70496f7702d83974adf8816ea826f1d8579f3b3f4b28a3890d2b` |
| `modules.builtin.modinfo` | 106,640 | `702d4cabaa9bdc1b282d0e419ba091f64dc06ba737fe7319928bb3003adeea4b` |

The runner requires exact `/inputs` membership and fixed `/inputs/proof` SHA `9133cb64040f9df0daf9aa0caaab913c90fe7ce5c9bf59a19c71ce3e36fb0c94`. It records full input identities before import, uses `O_NOFOLLOW` reads and rechecks every input after the assertions.

## Retained limits and next gate (historical)

This checkpoint did not implement direct self-authentication in `main()`, root construction, `Commands.run()`, archive-tool execution, gzip, depmod, lookup execution, real evidence production, or real result finalization. Its next implementation had to preserve the reviewed 424-command order, active child caps and reaping, 270-second internal budget, 280/285-second outer limits, exclusive outputs, complete input/root readback, all 200 lookups, exact alias/symbol checks, the known `modules.symbols.bin` exception, and all seven retained E indexes. The superseding current status is at the top of this document.

The first current-source rerun, `run-urf729h4`, stopped before setup because the runner still expected its old private-snapshot mode. `run-b_gwjn23` stopped next because the subject still expected its old private-snapshot mode. Both retained unchanged inputs, passed isolation, ran no tests or workload children, and created no control artifact. The two corrections are exact: only the test and `/inputs/recipe` modes changed to `0644`; all other pinned private inputs remain `0600`. `run-f0tjlamv` then passed 3/3. Independent QA and safety review passed.

Only the later executed workload may claim a fresh control. T1 assembly, image creation, staging, module load and hardware testing remain separate and unavailable.
