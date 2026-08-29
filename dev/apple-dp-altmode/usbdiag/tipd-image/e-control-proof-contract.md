# Fixed E-only control: recipe and proof contract

Status: preserved three-assertion RED, current pure fixture GREEN, accepted raw-observation semantic GREEN, and current structural regression. No real E-control workload has run from the current source. The [bounded command/root/lookup helpers](e-control-test-contract.md) have their own retained RED and GREEN. T1 assembly remains unavailable.

## First checkpoint: three genuine assertion REDs (preserved)

The preserved subject SHA `e278c5b8346aba1963b8434747e0c990aa08ed9983e3327e5c166547ac927c44` returned `None` from its three missing pure boundaries. Its `main()` refused with `E_CONTROL_RECIPE_UNAVAILABLE`. The [runner](test_e_control_recipe.py) authenticated all sources and real input bytes before it called the subject. It did not launch a child, materialize an archive or create a module root.

The root task ran this exact first selection once in a new verified A2 sandbox:

```text
/usr/bin/python3.14 -I -S -B /inputs/test ERecipeTests.test_select_fixed_e_model ERecipeTests.test_unapproved_generated_index_is_rejected ERecipeTests.test_exact_424_command_plan
```

The retained run is `run-9fmdox3j`. Setup passed. It produced exactly the intended three assertion failures: no `ESelection` result for the actual fixed E image; no refusal when a byte was appended to the fixed generated dependency index; and no tuple for the literal 424-command plan. There were zero test errors or skips. The workload exited 1 without timeout, all inputs remained unchanged, and the test report records zero children, no fresh control, no image, no module load, no staging and no boot. Import, source drift, wrong input, archive parsing or missing-file failures would have been setup failures, not RED. The immutable `e-recipe-red-v1` snapshot retains the three files. No entire-suite RED is claimed.

The current [run_e_control.py](run_e_control.py) is the tested pure post-RED implementation. `select_e()` binds the one complete E byte string before it parses the exact streams, 200 modules, four named payloads and seven indexes. The sorted 200-entry name/path model has fixed SHA `eee8ad06a36c1537d53e0c416db998110d10638076a32bdd3fc8987f65b54bff`; a caller cannot exchange one unrelated but well-shaped module path. `validate_regeneration()` requires the fixed eleven outputs and full binary dump, checks the complete dependency model and mapping multiplicities, and preserves the one reviewed `modules.symbols.bin` distinction. `command_plan()` returns only the fixed 424 command tuples. These functions have no file, environment or subprocess API. `main()` remains unconditionally closed.

The full companion has 16 methods. It covers the exact E selector, base hash/size/type rejection, the seven original and eleven generated index identities, strict index membership/types, the one reviewed symbol-index distinction, exact dump bytes, complete dependency-model membership, exact command sequence, invalid names/placement, and closed operational/assembly gates. The current regression is `run-m64c0_of`: setup passed, 16/16 methods passed, the 605 read-only bindings remained unchanged, the workload did not time out, and it executed zero children. Its result explicitly records `fresh_control_proved=false`, `image_created=false`, `module_loaded=false`, `staged=false`, and `booted=false`. The earlier GREEN `run-7vguug70` and RED `run-9fmdox3j` remain preserved. These runs write only fixture metadata under the fresh `/work/e-recipe-fixtures` directory. Input files and identities are rechecked. This pure fixture GREEN does not claim fresh depmod, lookup, gzip, image or hardware success.

## Narrow read-only fixture bindings

Use the unchanged reviewed A2 runtime. These are 20 inputs: seven source/runner bindings, the fixed E image, and twelve individual historical files. The expected read-only mount count is 605: 582 runtime entries, three fixed sandbox files and 20 inputs. `/work` and `/tmp` are the only writable roots. The 280-second workload and 285-second outer limits remain unchanged. No manifest repin, installation, old launcher or unrestricted fallback is permitted.

| Sandbox binding | Input |
|---|---|
| `/inputs/test` | New `test_e_control_recipe.py`, pinned by the outer launcher. |
| `/inputs/recipe` | Current tested subject SHA `70f369f87942b6ca6826c808536353ae0cc400123204040b9c005995ab43c3e3`. |
| `/inputs/subject/e_control.py` | Frozen tested helper SHA `abbf59410a05fd5c789820df3d40e59d0a5c33cf1204ab93c7aeef806da7b1df`. |
| `/inputs/contract/image_contract.py` | Pure image contract SHA `a1eda280aa56967aa06b01a2cca0dfc70c3da6df25066f8a1e815beec719f1bf`. |
| `/inputs/assembly/prepare_image.py` | Pure dependency source SHA `00caceb3b7fa236dcc030fb4007d0baa75bfa08fcd1590626f85fcc8c22d5f60`. |
| `/inputs/control/verify_control.py` | Pure dependency source SHA `10b5afe6cff38df7b6ebe5619fd9a34935932a4b369f3a9ad2a51923c32932d8`. |
| `/inputs/helper/cpio_image.py` | Pure dependency source SHA `a32eddd159263d19ff87d7e9caee9d53d17ef5c350fbffe9e7eb142cb43ebf58`. |
| `/inputs/base` | Retained C2 E image: SHA `4d4f0557af57eebcc33322f004bcc7968254e644b069a11102375df0b31a52ae`, 19,191,513 bytes. |

For the twelve rows below, use individual read-only file mounts. Do not copy a binary fixture directory or bind the old root/run directory. The eleven `modules.*` files come from retained C2 `sandbox-tools/run-affn1zit/work/control-root/lib/modules/7.1.6-1-1-ARCH/`. The dump is that same run's `work/child-002.stdout`. The runner owns the literal raw SHA-256 pins for every row; they are not caller parameters.

| Sandbox binding | Historical file |
|---|---|
| `/inputs/g-alias-bin` | `modules.alias.bin` |
| `/inputs/g-builtin-alias-bin` | `modules.builtin.alias.bin` |
| `/inputs/g-builtin-bin` | `modules.builtin.bin` |
| `/inputs/g-dep-bin` | `modules.dep.bin` |
| `/inputs/g-devname` | `modules.devname` — the sole allowed empty input. |
| `/inputs/g-softdep` | `modules.softdep` |
| `/inputs/g-symbols-bin` | `modules.symbols.bin` |
| `/inputs/g-alias-text` | `modules.alias` |
| `/inputs/g-dep-text` | `modules.dep` |
| `/inputs/g-symbols-text` | `modules.symbols` |
| `/inputs/g-weakdep` | `modules.weakdep` |
| `/inputs/g-dump` | `child-002.stdout` |

Setup independently checks the whole E identity, both parsed stream hashes and record counts, raw-record concatenation, all 200 module paths, the four fixed module payloads, seven original index hashes, the exact generated-symbol distinction, all 200 ordered dependency lists, 1,408 alias mappings and 596 symbol mappings. It uses the authenticated pure parser for the complete normalized binary dump comparison. It also checks every literal planned command against the separately tested allowlist. The old W-only 199-module selector, W proof validators, old subprocess runner, old mains and import-time inspection scripts are not called or rebound.

These historical files are valid test fixtures only. A pure-fixture PASS cannot become a fresh-control proof. The future operational command must omit all twelve historical fixture mounts.

## Later real E control: exact no-change case

The later operational entry needs a separate implementation and full pre-execution review after the pure boundary RED/GREEN. Its eight read-only inputs are the recipe, the five frozen pure/helper sources, the fixed E image, and a directory containing only the three pinned original depmod inputs. No caller-supplied identities, fixture mode, alternate base, old proof, candidate module or command override is allowed. The recipe's source pin is enforced by the outer launcher and retained in the evidence. No accepted T1 module or image is bound by this contract.

| Boundary | Required fresh evidence |
|---|---|
| E identity | Whole image SHA/size above; early stream 10,240 bytes, seven records, SHA `967bc6adcff42e59abcfb4e509f6c80fd65588e0861d8c1c3189a135f10955b4`; main stream 61,286,668 bytes, 1,163 records, SHA `7be7b4b03367b5ce4b356fe35977edba6540af0a7df930dbff990286c9b98e28`. Exactly 200 uncompressed regular non-hardlinked archive modules with unique normalized names. |
| Four payloads | Keep the original working TIPD core SHA `bc02723db427639c6586d29eea7918e084874c741b60bf145585c6349fd07d70`, frontend SHA `f9b9e0f01270016b72cf242178eeb2810e32888e2cd6e68cf0d6f549500e1308`, ATC SHA `fd1c3d105bd69a649a38e89e2ca0bcbe6f656200a0f211d58211e8c7b3ec944b`, and packaged DWC3 SHA `d150400f9782c876972b2745d95617cd44e23574452f63980704911a467f7767`. Do not substitute a fresh rebuilt control or the T1 candidate. |
| Raw reconstruction | Preserve every early/main raw record and both trailer/tail byte sequences. Write only the two exclusive scratch cpio files. Compare both independent tool lists with parser order. No general extraction occurs. Read the four selected regular payloads to stdout only and compare exact bytes. |
| GNU gzip | One no-option `gzip` child with the checked regular main-stream file as stdin. Require the exact reconstructed E bytes, not only a successful decompression. Do not retry another flag, compressor or input layout. The retained child stdout is sufficient; no `.img` output is needed. |
| Regeneration root | Fresh `/work/control-root`: only the 200 E module bytes and pinned `modules.order`, `modules.builtin`, `modules.builtin.modinfo`. The three fixed hashes are in the subject. One depmod run may add exactly eleven approved index outputs. All 203 input files and the directory identities must stay unchanged. Final membership is 214 files. |
| Index policy | Six generated final-index files must equal E. The sole symbol exception is original SHA `a3f1e745b7675daaec99c7c7ebadc7d67b318143901e063674494c210b12ace6` versus generated SHA `5077fb001a5c48a2135ce8f651606b18578610bc660f430a59114e76be4f9437`, with binary dump SHA `c562726938a6e3d11d5b3661352508f00b74efd9cbadbb559c3680663da72c05`. All four generated text files also have fixed expected hashes. Check the complete normalized alias and literal symbol mappings with multiplicity, not a few sample lookups. Preserve all seven original E index payloads; never install the generated symbol index into E. |
| Binary lookup root | Fresh `/work/lookup-root`: exactly the same 200 E modules and the seven original E indexes, 207 files. No text dependency/alias inputs or fallback. Use only the exclusive empty config at `/work/empty-modprobe.conf`; its identity and bytes must remain unchanged. |
| Every module | For all 200 normalized names, require the exact filename and full ordered dry-run dependency list: reverse of the generated `modules.dep` closure, then the target. Only `lrw` may report builtin `ecb`; all other builtin lists are empty. This must be fresh evidence for all 200 names. |
| Driver routes | CD321x OF alias must resolve to the packaged `tps6598x` frontend and its core dependency chain. DWC3 and ATC aliases must match their exact normal module lookups. All nine TIPD exported-symbol lookups must match the core's complete ordered result. No returned `insmod` description is executed. |

The fixed command plan is ordered as follows. There are no help/probe children, literal Python self-checks or adaptive retries in this workload.

| Zero-based children | Work | Count |
|---|---|---:|
| 0–3 | Early then main: GNU cpio list, then bsdtar list. | 4 |
| 4 | GNU gzip, checked regular-file stdin. | 1 |
| 5–8 | TIPD core, frontend, ATC and DWC3 stdout-only payload reads. | 4 |
| 9 | Fresh reduced-root depmod. | 1 |
| 10–11 | Generated then retained binary index dump. | 2 |
| 12–411 | Sorted module names: filename then dependency lookup for each. | 400 |
| 412–414 | CD321x frontend, DWC3 and ATC OF alias lookups. | 3 |
| 415–423 | Nine TIPD symbol lookups, in the subject's fixed order. | 9 |

Use only the tested `Commands` active output caps, kill/reap behavior, exact environment and cumulative deadline. Retain the 270-second internal control budget within the unchanged 280/285-second outer limits. Each child has at most 30 seconds and a tighter output bound suitable for its exact result. Gzip stdout is bounded by the known compressed size; payload stdout is bounded by the exact expected payload size. Read-only lookups have bounded text outputs. Nonzero exits, any stderr, drift, extra children, timeout or output overflow mean HOLD, not repair. No partial run is accepted or automatically resumed.

The tested root builder copies module files in sorted path order. The historical builder used input order. The fixed regenerated indexes and full binary dump must still match. If this order difference changes any bytes outside the exact known exception, stop for review. It does not authorize sorting away differences, changing priorities or repinning an observed result.

## Complete proof and refusal boundary

Before the first child, authenticate all fixed sources and inputs, require all fixed outputs absent, and record the source/input identities. Maintain exact before/after snapshots for the regeneration and binary-only roots, both raw stream files, the empty config and every immutable input. The only new files are confined to the fresh `/work` output tree and `/tmp`; no live host paths are visible. Preserve partial outputs on failure.

The proposed complete proof has three fixed new JSON files plus the runner's raw child files. `e-control-evidence.json` retains archive metadata/raw hashes, all module/index identities, full lookup results, before/after snapshots, and the complete planned/observed command ledger with raw-output hashes. `e-control-header.json` uses the existing strict fixed E header schema. `e-control-result.json` is written last and binds both JSON files and all 424 actual child result/stdout/stderr files by their read-back identities and hashes. The final check requires complete exact membership, all statuses/return codes, empty stderr, no kill/timeout, every expected command, and unchanged inputs/roots. A caller-supplied dictionary of hashes or a header alone cannot substitute for actual files. No full-control result may be written by the fixture runner.

Write the final result only after every archive, index, lookup, command and postcheck gate passes within the deadline. The result must state that it is an offline no-change E control, that the twelve historical test files were not operational inputs, and that no candidate image, module load, staging, reboot or hardware acceptance occurred. Later T1 assembly still needs the independently accepted real T1 binary identity, this complete fresh control proof, a new exact single-payload assembly review and its own evidence. No unknown identity is configurable and no failed W/E/D3 hardware case is replayed here.
