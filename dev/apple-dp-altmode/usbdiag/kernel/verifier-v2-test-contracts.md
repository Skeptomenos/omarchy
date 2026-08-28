# C2 strict v2 module verifier — test contracts

Status: tests/design only. No new verifier is implemented. This is a private review handoff, not hardware evidence. The existing v1 verifier and frozen source/tests remain unchanged.

## First RED

Run `test_verifier_v2_red.py` with the unchanged, SHA-pinned v1 verifier and the real fresh v2/control modules. Setup authenticates all inputs and checks real `.ko` metadata, build IDs, AArch64 ET_REL, nonempty BTF, component/revision prefixes, and uninstrumented controls. It retains bounded real-tool output. The selected acceptance assertion must fail specifically because the old verifier raises `diagnostic drift`; its child count must remain zero. A setup, source, tool, export, timeout, or missing-file error is not valid RED. This is an expected version boundary, not a defect in the old verifier.

Exact sandbox command:

```text
/usr/bin/python3.14 -I -S -B /inputs/test V2VerifierBoundaryTests.test_real_v2_pair_is_accepted
```

Read-only bindings: test file at `/inputs/test`; old verifier at `/inputs/verifier`; fixed `Module.symvers` at `/inputs/symvers`; fresh diagnostic and control directories at `/inputs/diagnostic` and `/inputs/control`. Each directory contains `dwc3-apple.ko` and `phy-apple-atc.ko`. The outer launcher independently pins all mounts and owns the deadline. Only `/work` and `/tmp` are writable.

## Fixed identities

| Component | Diagnostic SHA-256 | Diagnostic build ID |
|---|---|---|
| DWC3 | `d9090119fee0252c9031185128ddd9d03bef9a0cbdfb118d8c71b7161d48b425` | `92014543045243fb1680ac0e56b34c3ce69cc503` |
| ATC | `dea7e4eaee8928441a44480843795a68905e5122d435ae86dacc06fdf7b0efbe` | `dc5bed70afdb1aa22a8cddd0a7f5ac2a2256ba49` |

Controls retain exact independently reviewed hashes/build IDs in the RED fixture. Module names, component roles, source revision `dev147-usbdiag2-v1`, board `j413`, target `front_lower`, and kernel metadata remain fixed. No CLI, environment, manifest, or test may replace expected identities with the identity under test. New output identities require a later explicit source/pin review.

## Required GREEN contracts

1. Accept the actual fresh v2 pair and exact controls using real `modinfo`, `nm`, and `readelf`. Check both modules before final pair PASS. Retain all raw tool output and bounded structured results; no module load or image mutation.
2. At the full identity gate, reject both v1 modules, either direction of a v1/v2 pair, swapped components, control-as-diagnostic, diagnostic-as-control, and altered bytes. Read actual frozen v1/control inputs or deliberate private copies. Do not change expected hashes to let bad inputs reach later checks.
3. Test parsed metadata contracts separately with transformations of retained real tool output. These are parser tests, not accepted binaries. This distinction prevents a hash failure from masquerading as deeper ELF, import, or revision coverage.
4. Preserve symbol bindings. The exact added `(binding, name)` entries are `U _printk`, `U alt_cb_patch_nops`, `U of_machine_compatible_match`, `U of_find_node_opts_by_path`, and `U of_node_put`. No removals or other additions, including `strcmp`, are allowed. Every original name and binding must remain unchanged. Reject duplicates, malformed lines, missing/extra symbols, and weak/strong binding substitutions. Do not reduce entries to names alone.
5. Require the fixed symvers hash and each added symbol's exact `vmlinux` / `EXPORT_SYMBOL` ownership, type, and empty namespace. Test missing, duplicate, wrong-owner, GPL/type, and namespace cases in the parsed export contract. No permissive superset or silently learned imports.
6. Require ELF64 little-endian AArch64 ET_REL and exact single build ID for each diagnostic and control. Require a nonempty `.BTF` PROGBITS section with bounded placement. Reject wrong machine/type/class, missing/duplicate/wrong notes, missing/empty/wrong-type BTF, truncation, malformed counts/offsets, and out-of-bounds sections in the relevant parser seam.
7. Require v2-only complete diagnostic prefixes for the correct component, board, and target; controls must contain no diagnostic prefix. Reject v1, mixed revision, wrong component/board/port, missing/truncated prefixes, and diagnostic markers in controls. Do not infer versions or broaden accepted versions.
8. Bound all input paths, regular-file sizes, reads, and output files. Reject missing files, parent/leaf symlinks, hardlinks, unsafe paths, source/metadata drift, existing output names, and partial output reuse. Inputs stay read-only. Fresh output roots retain failure evidence; no cleanup or automatic retry.
9. Exercise the real bounded child runner with harmless fixed commands: success, nonzero exit, stderr, invalid text, output overflow, and short timeout. Retain stdout/stderr/status before rejection. No unbounded capture, shell command interpolation, unrestricted fallback, or false PASS after child failure.

Use small frozen dataclasses and stdlib/unittest under the approved no-install exception. Keep subject parsers and immutable identity tables distinct from test inputs. Do not add a generic plugin, version-selection, or identity-rebinding framework. Actual implementation and run commands need review after the recorded RED.

## Scope and count correction

The separate E-image GREEN suite executed **13 methods**, not the earlier informal estimate of 14. That count correction does not add a test or image result. Verifier results remain pending. Controls are uninstrumented; diagnostic build success is not module-verifier PASS, C2 completion, staging, or hardware acceptance.
