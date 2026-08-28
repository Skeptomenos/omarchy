# C3 E-only staging — test-first contract

Status: RED fixture authored; no helper correction or workload executed by SWE. C2 is sealed and must not change. Root owns the real sandbox probe and every later execution. A passing probe and independent source/command review must precede the selected RED run.

## Inputs and fixed expectations

The four bindings are individual read-only files, not directories:

| Sandbox path | Input |
|---|---|
| `/inputs/test` | `test_stage_usbearly_red.py` from this draft |
| `/inputs/helper` | Exact historical public D2 helper, SHA-256 `485a68e30c3b94f430e375286756204f7332446c7878393e40ad22bb8a9ebaff` |
| `/inputs/baseline` | The same exact historical helper bytes, independently bound for the old protected-record producer |
| `/inputs/proof-spec` | Root's fixed sealed-C2 specification, SHA-256 `1ef19e97ff21836091b569a9168a1802f6173f549999a56d12fd20321d3b37aa` |

The specification records the already reviewed E image and eight actual proof hashes. The tests fix those values in source; they do not infer accepted identities from the helper under test. The specification is authenticated as a review input. Do not bind the whole C2 tree, a real boot directory, the operational staging helper, or a hardware tree. No protected/proof file is opened by the test producer calls: those functions only print their fixed records.

The test setup checks unprivileged `/work` isolation and bounds/authenticates all three data inputs before any shell source operation. It writes a distinct setup record. The old public helper remains nonoperational. Collector source errors, stderr, malformed output, source-pin mismatch, missing input, or timeout are setup failures, not accepted RED. The outer launcher pins all inputs, retains output, and owns the deadline.

## Genuine RED before correction

Run exactly the two selected methods, in this order:

```text
/usr/bin/python3.14 -I -S -B /inputs/test StageHelperTest.test_e_image_identity_and_staging_names StageHelperTest.test_exact_sealed_c2_proof_records
```

Setup must pass. Both actual old production collectors must exit 0 with empty stderr. The two assertions must fail specifically because the old image constants select the diagnostic image and the old proof records select D1. Preserve the setup record, stdout, stderr, child results, and overall expected exit 1. This is a missing E-only contract, not evidence that the old D2 image/helper was intended to satisfy C3.

## GREEN after accepted RED

Keep this RED file frozen. After the minimal helper correction and independent review, create a GREEN companion whose only semantic fixture change is the exact subject-helper SHA pin. The expected E/spec/baseline values and all test bodies remain unchanged. Bind the corrected public helper at the same `/inputs/helper` path and run the whole file. No corrected helper, pin update, or GREEN run is authorized before accepted RED.

The suite preserves all 38 historical method bodies and adds exactly four methods:

1. Read the real readonly image fields; require exact E SHA, size, destination, public source suffix/proof root, exclusive temporary basename, and staging directory label.
2. Call both real protected-record producers; require the old 32 rows byte-for-byte plus exactly one retained D3 image pin, for 33 unique protected paths.
3. Call the real proof producer; require the fixed eight sealed-C2 path/hash pairs, including the actual `e-assembly-result.json` and `e-image-delta.json` names. Combined preflight records must contain 41 unique paths. No old D1 proof set or aliases.
4. Use real synthetic-file completion operations under `/work`; require uninstrumented early-availability wording and no reboot permission, with no diagnostic-image claim.

The old 38 bodies still cover copy/hash/size, paths/links, collision refusal, bounded failure, sync, completion, environment and synthetic host validation, and the exit-trap correction. They do not establish production root preflight, actual current power/mount state, storage power-loss behavior, staging, boot safety, or hardware acceptance. No source constants or system commands are mocked or overridden.

## Required separate private-copy QA

The public helper's SOURCE, PROOFS, and ROOT_UUID remain deliberately invalid. Only the later independently reviewed operational copy may contain the machine values. QA must record both actual file hashes and prove exactly the three approved literal assignment replacements, with every other byte equal to the 42-tested public source. Validate private values against sealed C2 and the approved root identity. Do not use a permissive line filter. Any change to either file invalidates that comparison and requires renewed review. No additional fixture method substitutes for this gate.

The minimal later helper diff is limited to E source/hash/size/destination/temp/directory labels, the one retained-D3 protected row, the eight fixed C2 proof rows, and uninstrumented wording. Preserve `D2ST_`/`d2stage_` names and all copy, no-replace publication, sync, trap, environment, package/kernel, battery, and root checks. David must run any later reviewed privileged staging command. No runtime preflight, staging, image selection, reboot, cleanup, or retry follows from these test contracts.
