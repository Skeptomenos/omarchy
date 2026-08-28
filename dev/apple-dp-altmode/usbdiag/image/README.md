# Offline image source archive

These are reviewed source checkpoints, not live-use commands. They require exact private inputs and the reviewed private R4 sandbox. The public sandbox has invalid paths and omits the host tool manifest. Do not run these files unrestricted or add a fallback to host tools or files.

The [diagnostic plan](../../../../docs/plans/dev-147-usb-startup-diagnostic.md) owns current status and authority. The [real-control evidence](../../../../docs/evidence/dev-147-real-archive-controls-2026-08-28.md) and [diagnostic-image evidence](../../../../docs/evidence/dev-147-private-diagnostic-image-2026-08-28.md) distinguish fixture results, real-tool checks, retained failures, and untested startup behavior.

| Source | Scope and dependencies |
|---|---|
| `cpio_image.py`, `cpio_image_test.py`, `test_review_archive.py` | Bounded raw-record reader/writer and real filesystem guards. 58 focused tests pass. |
| `verify_control.py` | Passed no-change image/index control with 199 binary-only module lookups. Exact saved image and three private text inputs are required. |
| `prepare_image.py`, `test_prepare_image.py`, `test_alias_normalization.py`, `test_symbol_retention.py` | Corrected private assembly source and 55 passing fixture methods. Tests require the pinned control proofs and three actual index-review inputs. They never call assembly main. |
| `inspect_indexes.py` | Historical read-only two-root comparison. It intentionally pins the retained private **first** assembly draft; that draft is not the current `prepare_image.py` in this directory. |
| `inspect_priorities.py` | Independent read-only comparison of the two exact pinned symbol binaries. It proves that only 335 priority fields differ. It does not write an index. |

All six newly exported assembly/inspection files are byte-identical to their reviewed private sources. Raw proof JSON, symbol binaries, generated dumps, modules, images, and host manifests stay private. The earlier failed drafts and RED checkpoints stay in the private evidence archive. No missing private input is permission to invent a replacement or bypass a hash check.

The assembly permits three replacements: ATC, `modules.dep.bin`, and `modules.alias.bin`. It adds DWC3 glue. It retains the original symbol index after verifying the regenerated scratch index and its complete binary mapping dump. Both builtin indexes and every unrelated archive record remain unchanged. The final result is written last; an absent result means incomplete output.

No helper here stages into `/boot`, loads a module, selects a boot entry, or reboots. D2 staging and D3 attended startup require separate review and user action.
