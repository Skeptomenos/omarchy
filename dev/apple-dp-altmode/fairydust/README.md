# Combined fairydust build

This directory validates an offline M2/J413 kernel build. The [living plan](../../../docs/plans/2026-09-04-dev147-fairydust-build.md) owns execution status; the [assessment](../../../docs/research/dev-147-upstream-reconciliation-2026-09-04.md) explains the source selection. These scripts do not install a kernel or prepare a boot selection.

## Pinned inputs

- Upstream: Asahi fairydust `b8810ad6442699f610984f3eceea2e3234a50b77`.
- Combined Linux commit: `83604c8b18e4673ed91e1172aef9aebeb0af20ce`, branch `codex/dev147-fairydust`.
- Patches: [corrected AFK reuse](../afk-service-reuse/afk-service-reuse.patch), then [PR582 timeout semantics](../afk-service-reuse-pr582/pr582-timeout.patch). PR582 is Francisco Vargas's upstream proposal; its original patch remains in [the provenance archive](../pr582/pr582-upstream.patch).
- Release: `7.1.12-dev147-fairydust1`.
- Input kernel config SHA-256: `701d1270a36cb57047558ab78e7d825900cc76935e42fd96003c319d1b9050e4`.
- Candidate config SHA-256: `678853acf4d664a96a4b1a69bba53d3a22ed419d9bf18bb7bcd322956ce849c6`.

The source checkout is `/home/david/Work/dev147-fairydust-build/linux`. Its out-of-tree output is the sibling `build/` directory. The sibling `build-command.sh` records GCC/Rust build environment, private tools, fixed build timestamp, local release, and four reduced-priority jobs. `tools/receipt.json` records signed Arch ARM build-tool archives; `config/live-to-fairydust.diff` records the full configuration delta.

GPU, DP, display audio, SIO, 16K pages, and BTF remain enabled. The new upstream source removes deprecated EROFS on-demand blob support; this is disclosed in the config delta. The remaining core EROFS support is retained.

## Build and validation

The recorded compile command is:

```bash
/home/david/Work/dev147-fairydust-build/build-command.sh Image modules apple/t8112-j413.dtb
```

Long compilation runs use resumable 280-second chunks. `logs/build-chunks.json` distinguishes planned timeout checkpoints from compiler failures. Successful compilation requires a final zero exit, including whole-kernel linking and modpost.

After module staging and candidate assembly, run the complete offline gate:

```bash
bash /home/david/Work/omarchy-dev147-fairydust-build/dev/apple-dp-altmode/fairydust/validate-offline.sh /home/david/Work/dev147-fairydust-build
```

The gate reruns incremental compilation and verifies source/config pins, candidate hashes, build-output equality, AArch64 Image format, BTF, required kernel features, and the complete staged module tree. Module contents must match their corresponding build outputs byte-for-byte; this candidate does not strip, sign, or compress modules. It checks dependency resolution and regenerates the AFK harness executable from its pinned source before running positive and negative controls. DT checks cover J413 identity, the external display connection, enabled DCP/SIO/audio nodes, and the audio DMA relationship.

The module-tree regression tests can run before the full build finishes:

```bash
bash /home/david/Work/omarchy-dev147-fairydust-build/dev/apple-dp-altmode/fairydust/test-module-tree.sh
```

They reject a missing leaf module, an extra module, and changed module contents even when the version marker is unchanged. The whole gate also refuses an incomplete candidate before attempting make.

## Artifact boundary

The expected candidate directory is `/home/david/Work/dev147-fairydust-build/artifacts/candidate-7.1.12-dev147-fairydust1`. It contains Image, J413 DTB, configuration, symbol/version files, patch provenance, and checksums. Modules are staged separately under `artifacts/root/lib/modules/7.1.12-dev147-fairydust1`. The [dated build evidence](../../../docs/evidence/dev-147-fairydust-build-2026-09-04.md) records the completed outputs and checks.

The source bundle preserves the exact two local commits and requires the pinned upstream base. Reapplying the patches with different commit metadata can reproduce source bytes but changes the Git identity that this gate intentionally pins. Build recipes contain paths for this workspace; recreating it elsewhere requires explicit path updates and a new receipt.

Static DT schema validation is separate from the functional graph checks. The pinned fairydust DT produces inherited schema diagnostics, including its experimental `displayport` property; the validator's zero exit does not mean those diagnostics passed. Bootloader-populated firmware parameters, initramfs/m1n1 assembly, package-guard migration, boot selection, suspend, and device behavior require later checks. An offline PASS is not a boot or hardware PASS.

## Boot integration

The [boot-integration continuation](../../../docs/plans/2026-09-05-dev147-fairydust-boot-integration.md) prepares the complete initramfs and m1n1 inputs. The [staging handoff](boot-stage/README.md) and [paired activation handoff](boot-activate/README.md) have been applied. The activation receipt reports `ACTIVATED_NOT_REBOOTED`; the first candidate boot now succeeds; hardware acceptance remains open. The full kernel build above remains the frozen baseline.

## Clear-swap diagnostic

The separate [100 ms clear-wait trial](clear-wait-trial/README.md) tests the late reply observed during front-port acceptance. It retains this directory's frozen baseline and uses its own source, release, output and validation gates.
