# DEV-147 T1 offline foundation — 2026-08-29

Checkpoint sequence: source tests and control evidence first; later parser and private-build results are appended below. The [living subplan](../plans/dev-147-usb-startup-diagnostic.md#a2-foundation--continued-offline-preparation-living) owns current progress. The [main goal](../plans/dev-147-m2-displayport.md#autonomous-offline-goal--next-test-package-living) still ends before the first manual review/staging boundary.

## First source/control checkpoint

The selected sender-only diagnostic passes 22 focused production-source methods. This is not a boot, kernel-concurrency, hardware-safety, or USB/video fix result. A fresh private build of the unchanged working-HPD control also passed scoped checks. Actual candidate ABI acceptance remains separate.

| Check | Actual result | Limit |
|---|---|---|
| Fresh sandbox | Isolation and seven import-smoke tests pass; fixed 582-entry runtime retained | No unrestricted fallback or install. Kernel defects/resource exhaustion are not ruled out. |
| Driver baseline | Two selected missing-entry assertions RED; full run has 11 PASS plus the same two RED, no errors | Both subjects were the unchanged control; setup and 308 children passed. |
| T1 source | 22 methods PASS, no failures/errors/skips; 552 children exit 0 without timeout or stderr | 214 paired original-operation observations, 120 diagnostic cases, two compiles, two ELF dependency checks. No module load. |
| Pure image contract | Two genuine RED assertions, then all 15 methods PASS | Synthetic archive/header checks. No image assembly; operational gate disabled. |
| T1 trace contract | Two genuine RED assertions, no errors/skips | Preserved stub lacks complete-trace recognition and missing-worker-end classification. GREEN and real-artifact acceptance remain later gates. |

Every workload used fresh output and read-only fixed inputs. T1 source, image-contract, and trace runs had 592, 590, and 586 read-only bindings. Input readbacks matched; none timed out. Independent pre-execution review preceded each run. Raw commands, snapshots, output, and child results remain private. The ongoing A2 directory is not a completed sealed package.

The source GREEN run preserves all original 13 test bodies and all three independent operation models. New checks cover exact source scope, 23 real-FDT cases across five allocation variants, balanced OF references, retries/two instances, record decisions, terminal-cap behavior, eight-thread reservation/arrival, and exhausted-counter operation preservation. Userspace type shims are not kernel-layout evidence. Ignored mux/role returns and original call ledgers remain unchanged in these fixtures.

## Control, type, and frontend evidence

The fresh control module is SHA-256 `a695d4cd222406938240079860ee63db7d548950066ed758b410f5ca070f6848`, build ID `11405e07a2b83267dfbb432350dcc69d963d29b4`. It does not replace the known-working module `bc02723db427639c6586d29eea7918e084874c741b60bf145585c6349fd07d70`. Their 94 imports and basic metadata match. Metadata equality and zero version CRCs are not ABI proof.

Preserve the failed observations and narrow resolutions:

- Default type inspection returned exit 0 with a missing SN type and nonempty stderr. That is not a type PASS.
- Full-vmlinux BTF inspection produced DECL_TAG warnings. The noisy output remains retained.
- Each module's own extracted `.BTF.base` yields clean matching BTF for `tps6598x`, `cd321x`, and `tipd_data`. DWARF independently agrees on their 384-, 680-, and 120-byte layouts. SN still has no production debug entry.
- A separate type-only object, with the identical control compiler invocation, gives clean 784-byte SN DWARF: a 680-byte CD prefix, three 32-byte completions, and the final pointer. Both actual module tables encode that 784-byte allocation. This is a scoped witness, not a production SN debug record.
- The exact packaged I2C frontend reads allocation size at table offset 16 before allocation. Its common-prefix offsets match working/control layouts; its Apple OF binding selects the CD table. This checks actual packaged bytes, not only source.

Independent reviews accepted those scopes. No type check loaded a module or read hardware.

## Frozen identities and next boundary

The first T1 source is `215051ed006431c73f2e402e5a1d503daaa41dc9d4b9e2bb66a82ac868892a92`; its tested runner is `b8f4bd0c9e4aa200910bb0a2517aa26219583114623e2dbbb17a94b790440727`. Shared headers and trace sources stay unchanged. Only the selected core gains logging and the CD allocation tail.

The pure image subject is `a1eda280aa56967aa06b01a2cca0dfc70c3da6df25066f8a1e815beec719f1bf`; its tested runner is `744a874b6c5657aec5894cb998374a2bff9649f617fe5e5e7c2d41bb930c1283`. It requires exact E bytes, unchanged raw records outside the core, and all seven original indexes. Caller-supplied identity cannot enable assembly.

The trace RED subject is `1dff12fda070f8712e77c2631ba92afa3631af889eae7b95b8e0fbe857cd9086`; its runner is `f67b9ebb465759f8a9349346af7c062ae80a459a6f943764b3298dd499a3a55c`. Synthetic fixtures cannot prove artifact acceptance, receiver delivery, or a negative sender claim. Normal 127 must have same-owner cap 128; losing it is incomplete even after a terminal record.

Next are parser GREEN, actual candidate build/layout/import/export checks, fresh E reconstruction and full index controls, the single T1 image, then A3/A4 staging/recovery/review/sealing. This checkpoint releases no privileged command or boot.

E/D3 failures, recoveries, stock files, backups, and sealed checkpoints remain unchanged. Root-private bytes retain user-validator provenance. USB-C charging is user-attested, not controlled power evidence or present-cabling proof. Automatic monitor USB and full Gate 4b remain HOLD. No live system, greeter, device, or boot change occurred.

## Later A2 checkpoint: parser and private build

The strict trace parser now passes all 31 methods after the retained two-assertion RED. The run reports 0.072 seconds, no errors/skips or unexpected outcomes, zero workload children, unchanged inputs, and 586 read-only bindings. Independent pre-execution and output reviews pass. Parser SHA-256 is `8c1e90a30f68c9237948e47f583038aee0d4584fa2459779e518b1630372e0fe`. The original 27 test bodies and independent fixtures remain unchanged. Operational capture acceptance stays closed until reviewed fixed artifact binding; this is synthetic structural evidence only.

The first private T1 module compiled, then its exact-import check stopped: it predicted 98 imports but found 99. The extra `alt_cb_patch_nops` is generated by the pinned ARM64 atomic comparison helpers. Both callback relocations belong to the new diagnostic counters. The fixed kernel exports it from `vmlinux`; `depends=typec` is unchanged. Preserve that failed check. Independent source/relocation review accepted the narrow expectation correction, not a dependency installation or source/tool change.

A second fresh build passes the corrected 99-import check and produces identical bytes: SHA-256 `a0fdadc351261643545e5afd8561923be99431661c447084336c9318f5b0c02f`, build ID `40aa54382047ba36b02c9ac0da65a213862a77ad`. Basic metadata, nine export names, and all three shared DWARF/BTF layouts match the working/control module. The new wrapper is 688 bytes: unchanged 680-byte CD prefix, then two four-byte atomic fields. Full independent table/export-binding acceptance remains pending; a successful build is not kernel or hardware acceptance.

The new E-control boundary also has three genuine RED assertions after valid setup, with no test errors/skips, children, reduced roots, or image output. Its 200 module payloads and seven indexes are labelled synthetic fixtures. Before GREEN acceptance, strengthen independent proof that output caps and deadlines kill and reap a running child. The real 424-child E reconstruction/index control remains a separate unexecuted gate.

Next: accept the binary table/export review, implement and verify E-control boundaries, then run the real no-change E control and assemble only T1. Bind the operational capture validator to reviewed artifacts, finish A3/A4, and release only the first manual staging/review boundary. No live state changed.

## Later A2 checkpoint: scoped binary and E-boundary acceptance

Independent review now accepts the actual candidate's scoped interface evidence. All four 120-byte data tables retain all 46 callback bindings. Only the selected CD allocation changes, from 680 to 688 bytes. The other allocation sizes, table bytes and padding match. All nine exports retain their actual names, empty namespaces, GPL flags and relative bindings. The 99 imports comprise the original 94 plus the five reviewed kernel exports. The two builds are byte-identical; the module is 1,327,920 bytes. The shared DWARF/BTF layouts and tail offsets agree. This does not establish kernel lifetime/concurrency safety or hardware acceptance. The missing production SN debug entry and zero version CRC limits remain.

The fresh E-control fixture run `run-0z8qsjmd` passes all 18 methods in 1.244 seconds after the preserved three-assertion RED. It retains the original 16 test bodies and adds independent active-limit checks. Eleven harmless child records match the expected commands. Both long-lived overflow cases kill and reap the waiting child in under 0.007 seconds; the two active deadlines complete in under 0.204 seconds. Independent process checks confirm reaping. Setup, postchecks, seven sandbox smokes, exit status and all 591 read-only input fingerprints pass. Independent output review passes. No real image or module was an input. These are runner/root/lookup boundary results, not the planned 424-child E image control.

Next: complete the real E no-change/index control and private T1 image, then bind the capture package to the accepted artifact. Structural parsing is complete; operational provenance remains qualified and separate. A3/A4, recovery, final seals and the first manual staging/review handoff remain unfinished. No privileged command, live preflight, device query, display change or reboot occurred.

## Later A2 checkpoint: pure E recipe and bounded capture package

The pure E-control recipe passes all 16 methods in a fresh sandbox. Setup and postchecks pass; all inputs remain unchanged; 605 read-only bindings are present; no timeout or workload child occurs. The recipe authenticates retained E as 19,191,513 bytes with seven early records, 1,163 main records, 200 modules, seven original indexes, the fixed module model, and an exact 424-command plan. Historical generated bytes are fixtures. No depmod, lookup, compression, image assembly, staging, module load, or boot ran. Independent pre-execution and output reviews pass.

The retained capture review RED has exactly two intended assertion failures: duplicate JSON keys could hide an escaped T1 revision during family classification, and boot/build-note samples were hashed before explicit size bounds. The corrected final package then passes all 21 methods with 586 read-only bindings, unchanged inputs, no timeout, and zero children. Independent static and actual-output reviews pass. It records candidate module SHA-256 `a0fdadc351261643545e5afd8561923be99431661c447084336c9318f5b0c02f` and enforces build ID `40aa54382047ba36b02c9ac0da65a213862a77ad` through exact before/after note samples. Full module-SHA/image provenance remains closed.

These 21 methods accept only bounded submitted bytes and internal consistency. They require the exact all-priority journal command, complete original envelopes, receipt hashes, one boot/kernel transport, and before/after module-note agreement. They do not read a journal, device, sysfs, or live module. The active collector and operational artifact/image binding remain closed. No selected initramfs, earliest-startup attribution, receiver delivery, negative sender result, USB behavior, charging behavior, display result, or hardware acceptance follows.

Next: execute and independently review the real 424-child E control. Then assemble one T1 image with the accepted binary while retaining all seven E indexes, activate the fixed capture provenance only against that accepted image, and finish A3/A4. Old images, helpers, seals, backups, and `/home/david/o-live` remain unchanged. No manual action is ready.
