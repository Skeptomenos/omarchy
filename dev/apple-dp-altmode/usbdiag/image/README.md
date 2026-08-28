# Offline image source archive

These are reviewed source checkpoints, not live-use commands. They require exact private inputs and the reviewed private R4 sandbox. The public sandbox has invalid paths and omits the host tool manifest. Do not run these files unrestricted or add a fallback to host tools or files.

The [diagnostic plan](../../../../docs/plans/dev-147-usb-startup-diagnostic.md) owns current status and authority. The [real-control evidence](../../../../docs/evidence/dev-147-real-archive-controls-2026-08-28.md) and [diagnostic-image evidence](../../../../docs/evidence/dev-147-private-diagnostic-image-2026-08-28.md) distinguish fixture results, real-tool checks, retained failures, and untested startup behavior.

Reconciled: 2026-08-28. The sealed [C2 evidence](../../../../docs/evidence/dev-147-c2-offline-preparation-2026-08-28.md), [C3 helper preparation](../../../../docs/evidence/dev-147-usbearly-staging-helper-2026-08-28.md), [user-run staging PASS](../../../../docs/evidence/dev-147-usbearly-staging-2026-08-28.md), and [C4 readiness record](../../../../docs/evidence/dev-147-usbearly-boot-readiness-2026-08-28.md) remain separate from the [post-reboot display loss](../../../../docs/evidence/dev-147-post-c4-display-loss-2026-08-28.md). The [selection addendum](../../../../docs/evidence/dev-147-c4-selection-confirmation-2026-08-28.md) now establishes E external-display FAIL from user confirmation and saved capture, not shared IDs alone. The [current plan](../../../../docs/plans/dev-147-m2-displayport.md#current-recovery-handoff--working-image-w-living) prepares one reviewed W recovery for final release; it has not been performed. Staging and E are consumed. B/G images remain unprepared. See the [staging archive](../staging/README.md); no live-use command or boot permission is supplied here.

## Historical D1 sources

| Source | Scope and dependencies |
|---|---|
| `cpio_image.py`, `cpio_image_test.py`, `test_review_archive.py` | Bounded raw-record reader/writer and real filesystem guards. 58 focused tests pass. |
| `verify_control.py` | Passed no-change image/index control with 199 binary-only module lookups. Exact saved image and three private text inputs are required. |
| `prepare_image.py`, `test_prepare_image.py`, `test_alias_normalization.py`, `test_symbol_retention.py` | Corrected private assembly source and 55 passing fixture methods. Tests require the pinned control proofs and three actual index-review inputs. They never call assembly main. |
| `inspect_indexes.py` | Historical read-only two-root comparison. It intentionally pins the retained private **first** assembly draft; that draft is not the current `prepare_image.py` in this directory. |
| `inspect_priorities.py` | Independent read-only comparison of the two exact pinned symbol binaries. It proves that only 335 priority fields differ. It does not write an index. |

At the D1 export, all six assembly/inspection files were byte-identical to their reviewed private sources. Raw proof JSON, symbol binaries, generated dumps, modules, images, and host manifests stay private. The earlier failed drafts and RED checkpoints stay in the private evidence archive. No missing private input is permission to invent a replacement or bypass a hash check.

The historical diagnostic assembly permits three replacements: ATC, `modules.dep.bin`, and `modules.alias.bin`. It adds DWC3 glue. It retains the original symbol index after verifying the regenerated scratch index and its complete binary mapping dump. Both builtin indexes and every unrelated archive record remain unchanged. The final result is written last; an absent result means incomplete output. D3 later failed its external-display criterion; preserve that image and evidence unchanged.

## Distinct C2 E-only sources

| Source | Scope |
|---|---|
| [test_e_image_red.py](test_e_image_red.py) | Frozen legitimate-E acceptance case against the old assembly gate. Setup passes; the expected rejection is `unapproved archive replacement set`. |
| [prepare_e_image.py](prepare_e_image.py) | New E-only gate and assembly using authenticated old utilities without changing their globals or strict index pins. Adds exact packaged DWC3 and replaces only dependency/alias binary indexes; raw ATC/TIPD/unrelated records remain unchanged. |
| [test_e_image_green.py](test_e_image_green.py) | 13 passing delta, identity, path, and preservation methods. Actual index/dependency proof is the separate 414-command assembly result, not these fixtures. |

All three C2 files match their frozen reviewed private bytes. The [dated result](../../../../docs/evidence/dev-147-c2-offline-preparation-2026-08-28.md#e-only-archive-result) owns E's exact hash/size, fresh no-change control, raw-record delta, independent archive listings, and complete no-load resolution. E contains no diagnostic or rebuilt control module. Correct bytes and indexes do not prove safe probe timing or USB/display behavior.

No helper here stages into `/boot`, loads a module, selects a boot entry, or reboots. The separate C3 staging command is complete, and the old D2/D3 handoffs remain consumed. Do not replay staging or E. Only the current main W handoff can release its one recovery; there is no retry or new test sequence. W/E/B/G is not a boot schedule.
