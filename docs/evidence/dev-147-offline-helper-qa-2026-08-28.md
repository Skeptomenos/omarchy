# DEV-147 offline helper QA — 2026-08-28

Status: diagnostic import/logging checks and 48 archive-helper tests PASS. Real no-change archive/index controls and a diagnostic image remain pending at this cutoff. No live driver, boot, package, or cable action occurred. The [diagnostic plan](../plans/dev-147-usb-startup-diagnostic.md) owns the next gate.

This follows the [trace/module checkpoint](dev-147-trace-and-module-builds-2026-08-28.md). That source checkpoint was pushed as `d28fbc16975c337856d4e7e07a3a7dece2f98a96`; remote readback matched. Trace QA remains 59 PASS. Earlier RED, review, authentication, and metadata failures remain recorded, not rewritten.

## Diagnostic modules

`run-5o9oq1wf` ran the [module verifier](../../dev/apple-dp-altmode/usbdiag/kernel/verify_modules.py) after the actual isolation probe. Both modules passed pinned control/diagnostic hashes, build IDs, BTF section presence, and unchanged names, vermagic, dependencies, and aliases. Each has exactly four added undefined imports and no removed import:

| Added import | Source basis |
|---|---|
| `_printk` | Fixed native INFO records. |
| `strcmp` | Exact controller OF-path filter. |
| `of_machine_compatible_match` | The pinned `of_machine_is_compatible` inline calls it. |
| `alt_cb_patch_nops` | The pinned AArch64 atomic path uses `alternative_has_cap_likely`, whose alternative callback names it. |

All four are exported by vmlinux in the pinned Module.symvers. No new module dependency is introduced. This verifies import names and BTF presence, not semantic BTF/CRC compatibility or actual loader acceptance. Nothing was loaded. Independent source review found no blocking issue in this narrow verifier.

## Log formats and reservation cap

The [logging verifier](../../dev/apple-dp-altmode/usbdiag/kernel/verify_logging.py) extracts the exact pinned producer prefixes, reservation bodies, and macros. It substitutes C11 atomic and stdio primitives only. It compiles that userspace harness with `-std=gnu11 -O2 -Wall -Wextra -Werror -pthread`. This is not a Linux atomic, printk-scheduling, or hardware test.

The first run, `run-3e2rsoie`, compiled the C source but failed to link: the sandbox lacked GCC's `libgcc_s_asneeded.so` and `libatomic_asneeded.so` linker scripts. The compiler/linker output and failed inputs remain private. No producer code or sandbox policy was changed.

The second run supplied exact hash-checked private copies of those two installed scripts and libatomic as read-only inputs. It checked ELF dependencies and used only a process-local library path. The 582-entry tool manifest stayed unchanged. Nothing was installed or copied into a host library directory.

`run-ibqv1jmi` passed:

- All 57 actual log call sites use fixed literals and at most seven scalar conversions. Worst-width signed, unsigned, and Boolean arguments produced valid ASCII JSON. The largest record was 277 bytes including newline, below the 384-byte bound.
- Ten runs with eight threads each produced exactly 128 records per component: 127 ordinary records and one final cap marker. Reservations cover 1–128 without duplicates. Further calls leave the counter saturated and emit nothing. Generation zero consumes no reservation.
- The check compares reservation sets, not journal insertion order. It does not sort or repair captured evidence. Independent review confirmed that all producer `%s` arguments use the Boolean macros and that the test does not make a kernel-concurrency claim.

The extra linker-script hashes are `10bc094393cfacd92e7683eff066803c7c5bfd51ac8ee8eb7b57847a4c9b3ebb` and `7006f9f3ea0a199cca99d3646c3a7ebd5aa0fea2d45894c205cdb6eab4b4a7de`. The copied libatomic hash is `e4e026a2b4d66f9d57c08645dea91ae9d36ebcbea55b34cf2357f312a8682495`. These are build-test inputs, not new live dependencies of the diagnostic modules.

## Strict archive helper

The [helper](../../dev/apple-dp-altmode/usbdiag/image/cpio_image.py) now implements bounded single-stream `070701` parsing and non-extracting regular-file transformations. It preserves untouched raw records, metadata, hardlink groups, opaque symlink targets, trailer, and exact zero tail. Only regular single-link replacements and additions with existing real directory ancestors are allowed. It rejects duplicate or unsafe names, malformed metadata, nonzero padding/tail, concatenated archives, special files, forged models, and path shadowing.

Filesystem operations use no-follow descriptor-relative walks, regular single-link and identity checks, bounded reads, optional source hashes, exclusive mode-0600 creation, readback verification, and file/parent fsync. Failed writes leave partial output for inspection. The separate sandbox supplies write containment; the helper is not itself a sandbox or a live staging command.

`run-zpj9pfai` passed all 48 [fixture tests](../../dev/apple-dp-altmode/usbdiag/image/cpio_image_test.py), including the original 16 unchanged tests and 32 additions. The real filesystem cases cover symlinks, hardlinks, existing outputs, FIFO/directory rejection, hash drift, sparse oversize inputs, permissions, and a retained partial write under a temporary file-size limit. The fixture restores that limit and signal handler. No mock hardware or unrestricted test runner was used.

The workload command was `python3.14 -I -S -B -m unittest discover -s /inputs/image -p 'cpio_image_test.py'`. Source review found no blocking issue. Ruff and strict type checks remain unavailable; no pass is claimed for them or the unsafe aggregate suite.

The [saved-image inspection source](../../dev/apple-dp-altmode/usbdiag/image/inspect-base-image.sh) passed in `run-dumx63wn`: the working image hash remains `ae8f1ed7f4f258f89931209cd7de6030be9f6875372d7329151b822a6ba2281f`, size 19,184,103 bytes. At the recorded offset 10,240, gzip validation passed and reported a 19,173,863-byte stream with 61,265,920 uncompressed bytes. This fits the helper's 256 MiB bound. It does not yet prove real newc parsing, round-trip preservation, or index equivalence.

## Integrity and next step

All four successful workload results above report exit 0, unchanged inputs, no timeout, and empty stderr except unittest's normal progress output. The actual probe and seven smoke tests precede every workload. Fifteen readable system/prototype/recovery pins still match. The old sealed checkpoints, operational helpers, working image, backups, and recovery bundle remain unchanged. Raw child outputs and failed runs stay private.

Next: run real no-change archive/compression and reduced-index controls. Only after those pass may D1 construct a separate private diagnostic image. Keep the seven original early records, 1,162 main records, 199 original module paths, both builtin indexes, and all unrelated payloads/metadata intact. A diagnostic candidate would add DWC3 glue and replace ATC, not install either. D2 staging and D3 attended startup remain unauthorized. Full Gate 4b stays HOLD; Gates 5 and 6 remain open.
