# DEV-147 C2 offline preparation evidence — 2026-08-28

**Host / scope:** M2 J413/T8112, kernel `7.1.6-1-1-ARCH`; fresh private, unprivileged build/test outputs only.
**Approval:** David asked to update the docs and plan, then proceed until monitor connection, a privileged command, or reboot needs his support. The reviewed C2 scope was two fresh module pairs and the E image only.
**Repo state:** Public source checkpoint before export: `051a3a6358a8387a541e62796f9e2a888ff3b4e9`. C1 producer sources and all historical v1 files stayed unchanged.

## Result

Fresh unmodified controls, corrected-v2 diagnostic modules, and the E image passed their offline checks and independent review. Focused GREEN suites passed 3 metadata, 13 E-image, and 15 v2-verifier methods. The actual E assembly passed 414 child commands; the v2-verifier run passed its 55-command contract. No new module was loaded, image staged, boot selected, or hardware action performed. Full Gate 4b remains HOLD.

The [diagnostic subplan](../plans/dev-147-usb-startup-diagnostic.md#c2-result--offline-artifacts-living) owns the next gate. [C1](dev-147-usbdiag-c1-correction-2026-08-28.md), [D3 failure](dev-147-usbdiag-startup-failure-2026-08-28.md), and [working-image recovery](dev-147-dp-recovery-2026-08-28.md) remain separate records. These C2 results do not establish the external-video cause or repair startup USB enumeration.

## Executed checks and retained failures

The commands below describe completed workloads inside fresh reviewed sandboxes. They are not live-use instructions. Each `/inputs/test` or `/inputs/builder` was a single pinned source binding for that row. The private launcher, host paths, manifests, raw outputs, and binaries are not published. Every workload passed the actual isolation probe, retained unchanged inputs, and avoided an outer timeout. Expected child failures and the short runner-timeout fixture remain distinguishable from workload failure.

| Check | Inner workload / subject | Observed result |
|---|---|---|
| Metadata RED | `/usr/bin/python3.14 -I -S -B /inputs/test ControlMetadataTests.test_dwc3_existing_packaged_file_is_accepted ControlMetadataTests.test_atc_existing_packaged_file_is_accepted ControlMetadataTests.test_source_pin_and_extraction_drift_fail_closed`; [frozen fixture](../../dev/apple-dp-altmode/usbdiag/build/test_control_metadata_red.py) | Exit 1: exactly two expected assertions fail in the old production metadata block; the drift test passes. All 16 real proper-`.ko` metadata prechecks and dual-name byte checks pass. Existing extensionless paths are rejected by `modinfo` name resolution, not by absent inputs. |
| Metadata GREEN | `/usr/bin/python3.14 -I -S -B /inputs/test`; [companion](../../dev/apple-dp-altmode/usbdiag/build/test_control_metadata_green.py) against the new C2 builder | Exit 0; 3 methods pass with the same real prechecks. The new builder uses `/inputs/stock/$module.ko`; the old builder is unchanged. |
| Fresh control build | `/usr/bin/bash /inputs/builder`; [C2 control source](../../dev/apple-dp-altmode/usbdiag/build/build-controls-c2.sh) | Exit 0; both unmodified modules link with BTF. Twelve fixed inputs pass. Complete metadata and exact imports match the packaged modules. |
| Fresh v2 build | `/usr/bin/bash /inputs/builder`; [bound v2 builder](../../dev/apple-dp-altmode/usbdiag/build/build-diagnostics-v2.sh) | Exit 0; both modules link with BTF. The builder was bound to the independently reviewed fresh control hashes before execution. Basic metadata passes; actual binary review and the separate verifier establish the exact import/identity result below. |
| E delta RED | `/usr/bin/python3.14 -I -S -B /inputs/test EArchiveTests.test_packaged_dwc_only_delta_is_accepted`; [frozen fixture](../../dev/apple-dp-altmode/usbdiag/image/test_e_image_red.py) | Exit 1; one expected assertion fails with `unapproved archive replacement set`. Real module pins and valid small-newc/no-change setup pass. The old diagnostic gate requires ATC replacement; E must preserve ATC. |
| E delta GREEN | `/usr/bin/python3.14 -I -S -B /inputs/test`; [E fixtures](../../dev/apple-dp-altmode/usbdiag/image/test_e_image_green.py) | Exit 0; 13 methods pass. This checks delta/path/identity contracts, not real dependency resolution or hardware. |
| Actual E assembly | `/usr/bin/python3.14 -I -S -B /inputs/e-helper/prepare_e_image.py`; [E-only helper](../../dev/apple-dp-altmode/usbdiag/image/prepare_e_image.py) | Exit 0; all 414 real child commands exit 0 with empty stderr. Independent image/index/lookup QA passes. |
| V2 version-boundary RED | `/usr/bin/python3.14 -I -S -B /inputs/test V2VerifierBoundaryTests.test_real_v2_pair_is_accepted`; [frozen fixture](../../dev/apple-dp-altmode/usbdiag/kernel/test_verifier_v2_red.py) | Exit 1; one expected assertion fails with `diagnostic drift`. All 20 real setup commands and seven pins pass. The old verifier runs zero children. This is correct v1 exclusion of v2, not a legacy-verifier defect. |
| Strict v2 GREEN | `/usr/bin/python3.14 -I -S -B /inputs/test`; [v2 tests](../../dev/apple-dp-altmode/usbdiag/kernel/test_verify_modules_v2.py) and [new verifier](../../dev/apple-dp-altmode/usbdiag/kernel/verify_modules_v2.py) | Exit 0; 15 methods pass in 1.528 seconds and the exact pair result is PASS. Independent QA verifies 24 fixture + 24 production + 7 runner commands, all 14 pre/post/legacy pins, and each expected negative runner outcome. |

The RED runs preceded each corresponding correction or new verifier. There was no retry to hide a setup failure. The diagnostic build's `diff` exit 1 records expected import differences; it is not a failed build. Source/test static reviews and independent saved-run QA passed. The actual E suite has 13 methods, not the earlier informal estimate of 14. QA also corrected its own readers for kmod trailing whitespace and an empty TSV namespace. Those reader corrections changed no helper, artifact, pin, or workload and required no replay.

## Actual module identities

All four modules are ELF64 little-endian AArch64 ET_REL with the exact build IDs below and nonempty `.BTF` plus `.BTF.base`. Name, vermagic, dependencies, and complete aliases match the packaged modules. Fresh controls reproduce the prior unmodified controls, not packaged binary bytes.

| Module | SHA-256 | Build ID |
|---|---|---|
| DWC3 control | `d213e676593c1c4f9daceba1002f2381b6d390ce3eff9995043991a4d1e20975` | `c0628ff7e26e3e3cb0dda8517bc2a34511ae85be` |
| ATC control | `edb76a5fd6458406f6371f842a7a6a2b5f8b22b404ba622a5d081302662cc568` | `def6d3cb64d2f7fff393c9da6fdde2e9ebbfc2c9` |
| DWC3 v2 diagnostic | `d9090119fee0252c9031185128ddd9d03bef9a0cbdfb118d8c71b7161d48b425` | `92014543045243fb1680ac0e56b34c3ce69cc503` |
| ATC v2 diagnostic | `dea7e4eaee8928441a44480843795a68905e5122d435ae86dacc06fdf7b0efbe` | `dc5bed70afdb1aa22a8cddd0a7f5ac2a2256ba49` |

Controls retain exactly 33 DWC3 and 29 ATC undefined imports. Each diagnostic adds exactly five strong undefined (`U`) symbols: `_printk`, `alt_cb_patch_nops`, `of_machine_compatible_match`, `of_find_node_opts_by_path`, and `of_node_put`. No import or binding is removed or changed; `strcmp` is not added. The pinned export table supplies the required `vmlinux` / `EXPORT_SYMBOL` entries with empty namespaces.

The binaries contain 20 DWC3 and 14 ATC complete `dev147-usbdiag2-v1` format strings for the fixed component, J413 board, and front/lower target. No v1 or wrong-component marker is present. Controls and packaged modules contain no diagnostic markers. The verifier rejects full v1/mixed/swapped/altered identities separately from deeper parser fixtures. Its bounded input, ELF/BTF, export/import, metadata, revision, output, and child-failure checks pass. These are binary inspections, not executed kernel probe results.

## E-only archive result

The private E image is `initramfs-linux-asahi-dpalt-usbearly1.img`, **19,191,513 bytes**, SHA-256 `4d4f0557af57eebcc33322f004bcc7968254e644b069a11102375df0b31a52ae`. A fresh no-change gzip control reproduces W exactly before E is assembled.

E adds only the exact packaged DWC3 module, SHA-256 `d150400f9782c876972b2745d95617cd44e23574452f63980704911a467f7767`. It replaces only `modules.dep.bin` and `modules.alias.bin`. Original ATC bytes (`fd1c3d105bd69a649a38e89e2ca0bcbe6f656200a0f211d58211e8c7b3ec944b`), the working patched TIPD core, all 199 old modules, and all 1,160 unrelated original main raw records remain unchanged. All seven early records, trailer/zero tail, and five static indexes remain unchanged. Metadata for the two replaced indexes is preserved except for payload size. No v2 or rebuilt control module is included.

Independent checks find 1,163 main records, 200 modules, and no duplicate paths. All 200 filename and 200 no-load dependency lookups and both concrete OF aliases pass; all 199 old dependency results remain identical. GNU cpio and bsdtar agree on membership. Three stdout-only payload hashes match. All 207 lookup files and 21 input/tool pins pass post-checks. The generated symbol binary and mapping dump match the unchanged strict pins; no normalization or permissive fallback was added.

E can change module availability and probe timing. Byte/index correctness does not establish boot safety, call order, display behavior, USB enumeration, or charging. B/G images were not prepared. W/E/B/G remain comparison definitions, not a scheduled boot ladder.

## Source archive and trust limits

The 11 new public sources below match their frozen reviewed private bytes. The [build](../../dev/apple-dp-altmode/usbdiag/build/README.md), [image](../../dev/apple-dp-altmode/usbdiag/image/README.md), and [archive README](../../dev/apple-dp-altmode/usbdiag/README.md) supply navigation. The retained verifier contract is a preimplementation handoff; its original pending wording is historical, not this result. Existing v1 helpers, schemas, patches, failed images, tests, and earlier evidence stay unchanged.

| New source | SHA-256 |
|---|---|
| `build/build-controls-c2.sh` | `37376bfdd59efe9a760e3391da591a4114e199f82c1f4557ec6c8e159949506a` |
| `build/build-diagnostics-v2.sh` | `ad07c5e11bd57612bf813fd595243f29a876120e26890fd82f04fe0844f868ea` |
| `build/test_control_metadata_red.py` | `de0f0fd5885e2850402e8add3f95bceb997328d9ff06eabb82f0a563ee474289` |
| `build/test_control_metadata_green.py` | `69a80cab0d90cebb0e11ee4a3f4b1494f7f60bfd2fa2749043ad5979a74ce2fd` |
| `image/prepare_e_image.py` | `5168df187f1460b8d916b05be6d075b17b7ae9a10a59d6d8bb9d4644bcc33c49` |
| `image/test_e_image_red.py` | `ed664f644f97e074531c26ee6bc8e580369a8aa9e80d088d5ed50e5e4fd9a538` |
| `image/test_e_image_green.py` | `a142143f313d5329223deb1ab1c813616c4d43dd4222699170f6d5717ec38706` |
| `kernel/verify_modules_v2.py` | `be43b676d79bbc9b0dc9d182ef24ed75113e7816b02e9f6b73895bc700571f68` |
| `kernel/test_verifier_v2_red.py` | `b017711aaabad21d4c60766291314e219f63956b5bbcf8ec67c1dd0bb1cafb2e` |
| `kernel/test_verify_modules_v2.py` | `d844ac181eebc1bf7246fbdf5d1192d58e1c3383599117a1bb0d0fe5935050ad` |
| `kernel/verifier-v2-test-contracts.md` | `0a2e1c1703e6f90cee90c7cc942bd0cea69125fb9176b1432468acd25a09569c` |

The public files require exact private `/inputs` bindings and the reviewed private sandbox. They are not installation or staging commands. No host manifest, raw log, boot identifier, device serial, module, image, or recovery file is exported. Typed stdlib/unittest remains the no-install exception; Ruff, Pydantic, pytest, and strict type-check tooling were not run or claimed as passing. The unrestricted aggregate suite was not rerun; its earlier failures remain recorded.

## Rollback and open gates

No system rollback is needed for this offline checkpoint: it did not change installed modules, boot files, GRUB, the live checkout, or device state. Retain all private outputs and failures; do not delete or overwrite them. This does not complete the separate full-DTB rollback proof or test the macOS restore bundle.

After the C2 checkpoint is reviewed and sealed, prepare and test a new **E-only C3 staging helper** and exact manual handoff. David must run any reviewed privileged staging command. Staging must not select or boot the image. Before any later C4 selection, review fresh readiness and the exact recovery handoff, and make that handoff available offline. No automatic boot, retry, reconnect, USB-device test, mode change, suspend, live swap, release, or external submission follows from C2. Permitted monitor disconnection is not a confirmed action or test.
