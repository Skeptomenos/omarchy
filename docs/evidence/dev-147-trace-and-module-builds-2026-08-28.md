# DEV-147 trace validator and private module builds — 2026-08-28

Status: trace fixtures and private module compilation passed. D1 is still incomplete. No archive/index control or diagnostic image exists at this cutoff. No module was installed or loaded. The [diagnostic plan](../plans/dev-147-usb-startup-diagnostic.md) owns remaining work and authority.

This follows the [public-source checkpoint](dev-147-public-source-checkpoint-2026-08-28.md). Its initial RED results and the earlier failed sandbox rounds remain historical facts. Source work continues on `codex/dev-147-m2-dp-altmode-public`; raw evidence, packages, modules, and manifests remain private.

## Isolation and inputs

Every workload below ran after the actual reviewed isolation probe and seven smoke tests in the fresh private continuation. The 582 pinned tool/runtime mounts and protection policy stayed unchanged. Only private work and temporary directories were writable. No host network, boot tree, live device/sysfs tree, or privileged action was exposed to a workload. Each result reports unchanged inputs and no timeout.

The installed kernel is `7.1.6-1-1-ARCH`. The installed package query did not find `linux-asahi-headers`. Builds used the previously verified private header tree, not a newly installed package. Read-only header inputs included its Makefile, Module.symvers, configuration, and vmlinux. Kbuild ran from a private writable output directory with `M` set there; it did not run in or rewrite the header tree.

All 15 readable system/prototype/recovery pins still matched after the diagnostic build. Protected stock initramfs/GRUB and staged image contents were not freshly read. The original 60-file D1 and 34-file R4 seals passed earlier in this continuation. No old checkpoint was reused for output.

## Trace validation and independent review

The [validator](../../dev/apple-dp-altmode/usbdiag/trace/trace_validator.py) accepts only bounded diagnostic records with their six original journal envelope fields. It checks the fixed revision, two module identities, exact field types, record limits, independent generations, sequences, attempts, matched operations, and successful initialization order. It keeps closed nonzero returns as evidence. It does not collect, filter, sort, repair, or discard journal records.

| Run | Result | Meaning |
|---|---|---|
| `run-48sknd7o` | 32 tests, 40 NotImplementedError errors | Original frozen stub RED; retained unchanged. |
| `run-6okbfkww` | 49 tests PASS | First implementation passed its then-current fixtures. |
| `run-975cxeoi` | 3 independent tests FAIL | Review found false positives for missing, failed, or misordered ATC finalize records. |
| `run-2eiudru2` | 59 tests PASS; exit 0 | Corrected implementation, 56 permanent tests, and all 3 independent regressions. |

The correction requires a successful ATC probe to contain one matching finalize and its mandatory USB2 power-off pair. Finalize and probe returns must agree. A genuine early failed probe can omit finalize only if it has no other operation. Tests cover those failures, missing or misordered power-off, and valid failure/retry paths. The original 32 tests remain present. The independent [review regressions](../../dev/apple-dp-altmode/usbdiag/trace/test_review_trace.py) are published too.

The accepted result can report only a positive software sequence. It cannot identify the HCD caller, prove PHY latching or a hardware cause, or prove that no late setter occurred. A declared complete capture cannot prove that its final suffix was retained. Capped, partial, malformed, or inconsistent evidence remains inconclusive. These are synthetic contract tests, not hardware simulations or a USB fix.

The test command inside the sandbox was `python3.14 -I -S -B -m unittest discover -s /inputs/trace -p 'test*.py'`. No package was installed. Ruff, strict type checking, pytest, and Pydantic remain unavailable and are not reported as passing. The unsafe aggregate suite was not rerun.

## Build-tool authentication

The retained pahole package SHA-256 is `d9aa45da6e009f655a528faca1bcd9eab4e1ab521a9e467476aae8d32bbc087b`. Its detached signature SHA-256 is `43b2dd8fac5bfa9e4e456f5f432601210c5ac603b9ccc0b930ba709421e2f2f1`.

Authentication round 1 (`run-cdv6z7y0`) passed the package/signature hashes, then failed because gpgv could not read the installed ASCII-armored public keyring as a binary keyring. Nothing was extracted or executed. Round 2 (`run-27rwb2ee`) verified the exact pinned public-keyring bytes, strictly decoded the armor into a new private file, and used gpgv to check the same signature. It reported a good Arch Linux ARM Build System signature from fingerprint `68B3537F39A313B3E574D06777193F152BDBE6A6`.

`run-ck85xyae` repeated authentication and extracted only pahole plus its selected library entries into private output. The executable hash is `6720f51a6a3b0f439e5d74fb07acfcd75bed599fd333c819eb3b1ced441f56ed`. ELF dependencies were inspected. The one additional installed runtime file, libdw, was copied into a private read-only input after its hash was checked. It was not added to the sandbox tool manifest. Subsequent builds reported pahole `v1.31`. No package, host library, or global environment changed.

## Control and diagnostic builds

Both sources derive from Asahi commit `e2e1930a9595bffafad92cec2b5504525efb9cd4`. The unmodified control used the pinned original DWC3 and ATC files. The diagnostic build used the unchanged, published draft files and patch. Both builds used the same private headers, GCC, binutils, make, and authenticated pahole inputs.

| Build / run | Result |
|---|---|
| Unmodified controls, `run-t533wqyw` | Both modules compiled with BTF and no compiler warning. The wrapper then failed a metadata command because a stock input filename lacked `.ko`; it did not rebuild or load anything. |
| Separate control QA, `run-oy0m8pr9` | PASS, exit 0, empty stderr. Correctly named copies of the existing outputs passed name, vermagic, dependency, alias, undefined-import, and BTF checks against stock. |
| Diagnostic build, `run-tvwolbkw` | PASS, exit 0, empty stderr. Both modules compiled with BTF and no compiler warning. Name, vermagic, dependencies, and aliases match the controls. |

| Module | Control SHA-256 / build ID | Diagnostic SHA-256 / build ID |
|---|---|---|
| DWC3 glue | `d213e676593c1c4f9daceba1002f2381b6d390ce3eff9995043991a4d1e20975` / `c0628ff7e26e3e3cb0dda8517bc2a34511ae85be` | `d333ce2d82789d5da8acdc563fd04ea9cde3872472cde423ed1a51710cf38ef4` / `4e3a8536657283ecc0ac9d5c49e19990a32150db` |
| ATC PHY | `edb76a5fd6458406f6371f842a7a6a2b5f8b22b404ba622a5d081302662cc568` / `def6d3cb64d2f7fff393c9da6fdde2e9ebbfc2c9` | `504fc2b82e62e7497532dfe4b955228d7298a3f2c9b34d1e9623ed9188912547` / `5e40dcc39aef0914b9fcba1a779b237f99a39f48` |

The unmodified control is not byte-identical to the packaged module. Its hash and build ID differ; metadata/import agreement is not a reproducible-build claim. The four diagnostic-only imports in each module are `_printk`, `alt_cb_patch_nops`, `of_machine_compatible_match`, and `strcmp`. Review of this exact delta and cap/concurrency/format checks remain pending at this cutoff. Compilation alone is not module-load or runtime compatibility proof.

## Remaining gate and rollback

Next: finish diagnostic import and logging-bound QA; implement and test the strict newc helper; then run real no-change archive/index controls before constructing a separate private diagnostic image. Preserve all old modules, images, helpers, backups, and recovery files. No destination under `/boot` was created or selected. D2 staging and D3 attended boot remain unauthorized.

The monitor is not needed for this offline work. No physical unplug is inferred. Full Gate 4b remains HOLD; Gates 5 and 6 remain open. This work needs no live rollback: leave the private outputs unused. Actual macOS restore execution remains untested.
