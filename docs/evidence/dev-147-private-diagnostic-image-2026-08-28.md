# DEV-147 private diagnostic image — 2026-08-28

Status: offline D1 PASS. One private diagnostic image passed assembly, exact-delta checks, and all 200 binary-only module lookups. It is not staged or boot-tested. D2 staging and D3 startup remain unauthorized. No live module, package, boot file, or operational helper changed.

This follows the [real no-change controls](dev-147-real-archive-controls-2026-08-28.md). That checkpoint was pushed as `dd44427104bbad65a2eb9e6903ac73b75a8c8424`; remote readback matched. The earlier source, trace, helper, and control checkpoints remain in the public feature branch. Raw evidence, generated modules, images, and machine manifests remain private.

## Retained assembly stops

The first assembly draft passed 30 focused fixtures in `run-170z1mtc`. These fixtures were written after the draft implementation. This missed the required test-first sequence. It is not a RED-to-GREEN claim. The draft, test source, and review record remain retained.

The real execution, `run-8di2p39b`, stopped before image creation. The generated `modules.symbols.bin` differed from the original, although the generated symbol text was byte-identical. Both builtin indexes, soft dependencies, and device-name metadata stayed unchanged. Dependency and alias text deltas passed before the stop. No final assembly result or candidate image was created.

A separate read-only inspection, `run-npbone19`, exposed a second validator defect. The baseline kmod binary dump returned success with empty stderr, but the comparator rejected 125 alias keys whose hyphens had become underscores. It expected raw text-index spelling. The generated-root inspection did not run in that failed attempt.

## Independent index investigation

Kmod 34.2 normalizes hyphens in alias keys, except inside a bracket section. It copies each opening bracket through the first closing bracket unchanged, and rejects unmatched brackets. This is not a nested-bracket or escape-aware parser. The bounded Python rule rejects empty, non-printable/non-ASCII, and overlength inputs instead of copying C truncation behavior. Only alias keys are normalized; symbol keys and owner module names are not. [Normalization source](https://github.com/kmod-project/kmod/blob/v34.2/shared/util.c#L65), [distinct alias and symbol writers](https://github.com/kmod-project/kmod/blob/v34.2/tools/depmod.c#L2120).

The corrected independent inspection, `run-bs1gvfgo`, passed both read-only binary dumps:

- Baseline: 1,406 alias mappings and 596 symbol mappings. Exactly 125 alias keys need normalization.
- Generated: 1,408 alias mappings and the same 596 symbol mappings. Exactly 127 alias keys need normalization. The only added mappings are the two approved DWC3 glue aliases.
- Both input roots stayed unchanged. Each child returned zero with empty stderr. No module loaded and no image was created.

The original symbol index is `a3f1e745b7675daaec99c7c7ebadc7d67b318143901e063674494c210b12ace6`. The regenerated index is `5077fb001a5c48a2135ce8f651606b18578610bc660f430a59114e76be4f9437`. Each is 31,021 bytes.

A separate byte/field inspection, `run-jqb824lf`, parsed every byte using the documented kmod index layout. All 596 mapping identities and field positions match. Exactly 335 priority fields increase by one, across 12 owner modules. All other bytes are identical. These values order matches within an index; they are not cross-index module identifiers. Preserve the original symbol index in the final image and keep the regenerated one only as scratch evidence. [Index layout and priority semantics](https://github.com/kmod-project/kmod/blob/v34.2/libkmod/libkmod-index.c#L51), [writer stores the module name and priority separately](https://github.com/kmod-project/kmod/blob/v34.2/tools/depmod.c#L2249).

## Correction checkpoint

Fourteen new normalization fixture methods ran against the frozen correction interface and unchanged binary-dump comparator in `run-m_dvzx37`. Together with the unchanged original 30 methods, 44 ran. The expected RED result contains 17 assertion failures and 20 errors, including four direct regressions against the existing comparator. These cover real hyphenated keys, preserved bracket ranges, normalization collisions, and untouched symbol keys. The new helper interface remained unimplemented at this point.

The normalization correction passed all 44 methods in `run-axf7r6k0`. The only earlier fixture edit corrected the two fabricated binary DWC alias keys from hyphens to underscores; its assertions stayed unchanged. Eleven new retained-symbol tests then used the actual pinned symbol binaries and generated dump. Ten methods reached the unimplemented selector and produced the expected RED result: 19 assertion failures and two errors across 55 total methods. The existing static-index guard test passed. No digest function was replaced or mocked.

The final [assembly source](../../dev/apple-dp-altmode/usbdiag/image/prepare_image.py), SHA-256 `00caceb3b7fa236dcc030fb4007d0baa75bfa08fcd1590626f85fcc8c22d5f60`, preserves the exact original symbol index. It requires both symbol binary hashes, the complete generated dump hash, unchanged symbol text, semantic mapping equality, and all prior static-index guards. It returns a new index collection without replacing the generated scratch file. The empty private modprobe configuration is created once; its bytes and identity are checked throughout.

All 55 fixture methods passed in `run-9chiropy`, in 0.175 seconds. The three fixture files were byte-identical to the prior correction checkpoint. Independent source review found no blocking issue. The two independent index inspectors also passed separate read-only review. Their physical read-only claims rely on the authenticated R4 mounts and launcher evidence, not just their Python code.

## Verified private image

The real assembly passed in `run-r2vtw6ym`. The final file is `initramfs-linux-asahi-dpalt-usbdiag1.img`, retained privately. Its size is 19,647,739 bytes. Its SHA-256 is `a11bf3a2bac1f105aa57b08ce9fad338c68882851247f7524d09f4b7c94188ca`. Independent file-stat and hash checks confirm a regular, single-link file with mode `0600`.

- All seven early records and the byte-10,240 gzip boundary are unchanged. The main archive has 1,163 records and 200 modules. All 1,159 unrelated original main records, the trailer, and the zero tail remain byte-identical.
- Only three original payloads change: ATC (`504fc2b8…`), `modules.dep.bin` (`436095f4…`), and `modules.alias.bin` (`ca6ca7be…`). Their metadata is preserved except for payload size. One new DWC3 glue module (`d333ce2d…`) is added with the exact reviewed metadata.
- The original symbol index, both builtin indexes, soft dependencies, and device-name metadata stay byte-identical. The working DP core remains `bc02723d…`. No extra input, text index, hook, preload, firmware, configuration, library, or symlink enters or changes in the image.
- A fresh binary-only lookup root passes filename and dry-run dependency resolution for all 200 modules. The original 199 results are unchanged. Both concrete target OF aliases resolve to their intended modules and dependency order. A separate JSON comparison confirms equality of all 199 baseline records.
- GNU cpio and bsdtar agree on both archive listings. Independent stdout-only extraction matches ATC, DWC3 glue, and the unchanged DP core. GNU gzip output round-trips exactly; the complete candidate is re-read and its delta checked again.

All 413 child commands returned zero with empty stderr: 200 modinfo calls, 204 guarded modprobe calls, five bsdtar calls, two cpio calls, one depmod call, and one gzip call. A separate command-record audit verifies every modprobe guard. No returned `insmod` description was executed. The passed 406-command no-change control was reused as pinned evidence, not rerun.

Every run above passed the actual isolation probe and seven stdlib smoke tests before its workload. All reported unchanged inputs and no timeout. The 582-entry runtime manifest and sandbox policy were unchanged. The failed inputs and outputs remain retained; no frozen run was edited or reused.

## Acceptance and next boundary

QA verdict: PASS for offline D1 only. Current focused suites have 59 trace, 58 archive, and 55 assembly methods passing. The earlier aggregate suite still has five recorded baseline failures and an unsafe credential-writing fixture; it was not rerun unrestricted. Unavailable lint/type tools were not installed or reported as passing.

Fifteen readable system/prototype/recovery pins and the original D1/R4 seals still match. The root-only stock/staged images and GRUB were not freshly read. No package installation, live driver action, device action, or reboot occurred.

Next, obtain approval for D2: a separately reviewed, fixed-target staging-only helper that David runs. The proposed `/boot/initramfs-linux-asahi-dpalt-usbdiag1.img` destination has not been created or selected by this work. Staging does not authorize D3. Startup, hardware causality, reliability, recovery execution, full Gate 4b, and permanent integration remain unproved. Adding DWC3 glue changes early availability; even a later successful diagnostic startup would not be a timing-matched A/B result or a tested fix.
