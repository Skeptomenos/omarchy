# Contained AppleDRM timeout experiment

This is an offline source archive, not an installer. Do not run these workloads on the live host. They require the existing reviewed private sandbox and pinned read-only inputs.

## Question

The external display's crash guard was observed set after LG 27 video disappeared. Its writer and the initial loss remain unknown. [Asahi Linux PR #582](https://github.com/AsahiLinux/linux/pull/582) removes one possible false writer: a 50 ms poweroff-clear-swap timeout.

Apply only the single hunk from commit `6b70d02bcb5758a625d8bcedbff340cf544a4496` to source baseline `e2e1930a9595bffafad92cec2b5504525efb9cd4`. The patch is by Francisco Vargas (haripako); retain its credit, Signed-off-by and source licenses. Do not copy the PR parent's unrelated plane-order change.

The timeout still returns immediately. Later poweroff steps remain skipped in that case. Genuine RTKit crash handling stays intact. The patch affects shared internal/external display code and cannot clear the flag in the current boot.

## Comparison

Build an unmodified control and patched AppleDRM with the same headers, tools and virtual build path. Package each into the same retained T1 base by replacing only `appledrm.ko`. Keep the TIPD, ATC, DWC3, all indexes and every other archive record unchanged.

Offline checks establish artifact identity and the intended code change. They cannot prove hardware recovery. A later attended test must identify the loaded module, verify both displays and responsiveness, and observe recovery after the relevant timeout. Startup success alone is insufficient.

## Boundary

The [offline evidence](../../../docs/evidence/dev-147-pr582-offline-2026-08-30.md) records the paired builds, 14 focused tests, binary review and private image results. `build-appledrm.sh` and `build_support.py` are exact workload copies. `image_pr582.py` is the tested archival version with an intentionally unbound module manifest. `test_image_pr582.py` exercises its pure contracts. The private bound version changes that one constant only.

The [main plan](../../../docs/plans/dev-147-m2-displayport.md#pr-582-offline-preparation-living) owns current permission and next steps. The [existing diagnostic export passed review](../../../docs/evidence/dev-147-crashflag-export-2026-08-31.md); it is preserved before any planned reboot. The [minimal staging handoff](../../../docs/evidence/dev-147-pr582-staging-preparation-2026-08-31.md) uses a private wrapper around the retained file operations. Staging and boot remain separate manual steps. This archive grants no sudo, driver operation, display setting, cable/device change, suspend, reboot, recovery rehearsal or upstream submission. Keep the packaged files, stock/W/T1 images, defaults and old evidence unchanged.
