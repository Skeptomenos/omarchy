# Build the combined fairydust kernel

**Goal:** Produce a reproducible, independently checked M2/J413 kernel, module set, and device tree from upstream fairydust plus the two remaining display fixes, then use that coherent stack to close the remaining USB-C capability gaps.
**Mode:** full — kernel and boot-stack work on a daily driver.
**Branch:** `codex/dev147-fairydust-build` in the Omarchy documentation worktree; a separate Linux branch holds the kernel changes.
**Linear:** DEV-147; DEV-163 retains monitor USB-data failures.
**Started:** 2026-09-04
**Reconciled:** 2026-09-04

## Context

The [upstream assessment](../research/dev-147-upstream-reconciliation-2026-09-04.md) selected Asahi Linux fairydust `b8810ad6442699f610984f3eceea2e3234a50b77` (7.1.12), the corrected local AFK service-reuse patch, and Francisco Vargas's pending PR582 timeout fix. The six-file source composition and lifecycle harness passed independent review. No full kernel was built in that assessment.

The running host is `omarchy-air`, M2 MacBook Air J413, kernel `7.1.6-1-1-ARCH`. Omarchy is dev-linked to `/home/david/o-live`; that tree is not a build workspace. Existing images, recovery assets, historical source pins, and active package guards remain recovery/control inputs. The already-staged 7.1.6 AFK+PR582 image can be an optional bounded control; its acceptance does not block the new build.

Documentation and retained patches live in `/home/david/Work/omarchy-dev147-fairydust-build`. Linux source, output, local tools, logs, and artifacts belong under `/home/david/Work/dev147-fairydust-build`. The old complete Linux tree at `/home/david/o/.dev147-stage/dev147-integration-source.SGVnPytGQN/linux` is read-only reuse material, not an edit target.

## Approach

Build the complete pinned fairydust source with the distro's existing kernel configuration as the starting point. Apply only `dev/apple-dp-altmode/afk-service-reuse/afk-service-reuse.patch`, then `dev/apple-dp-altmode/afk-service-reuse-pr582/pr582-timeout.patch`; use upstream DT and TIPD code directly. Produce isolated, uniquely versioned artifacts before preparing any installation or boot-selection procedure.

The user authorized a fresh plan and building. This execution covers source preparation, compilation, artifact assembly, and offline checks. Privileged installation and attended hardware operations require a concrete later handoff; the agent never runs sudo on this host.

## Execution Protocol

Follow the full `self-correction-loop`. One writer owns Linux source/build output; the orchestrator owns documentation. QA and final review are read-only. Record exact commands, source/config/tool hashes, failures, and artifact identities. A source PASS cannot satisfy a build, boot, or hardware gate.

Use bounded, resumable build work with conservative parallelism to keep the desktop responsive. Save logs on every boundary. A timed chunk with ongoing compiler progress is unfinished work, not a failed build; diagnose actual compiler failures before changing source or configuration. Do not add diagnostic patches or USB4 during the initial DP build.

## Steps

- [x] Slice 1: Acquire and configure the coherent source stack.
  Goal: a full isolated Linux checkout with exactly the selected patch series and a reproducible configuration.
  Probe first: verify remote pins, patch hashes, free disk/RAM, distro configuration, compiler requirements, and required DT/audio/GPU symbols.
  Implementation: create `linux/`, `build/`, and source/config/tool receipts under the build root; select a unique local release suffix; apply only the two retained patches with original provenance.
  Validation: source Git diff and hashes agree with the assessment; existing AFK negative controls and candidate checks behave as expected; kernel configuration completes with GPU, DP, SIO/audio, and 16K-page requirements preserved.
  Exit criteria: exact source and tool identities, config delta, and dependency decisions are recorded; no silently disabled desktop feature.
  Evidence: `logs/source-config-receipt.json`, `config/live-to-fairydust.diff`, and `checks/bindgen/early-build-qa.json` under the build root. Source/config/tool checks PASS; Rust availability and small targets exit 0; all five AFK controls return the expected outcomes.
  Assumption: locally available or unprivileged extracted build tools can satisfy this kernel's compiler and Rust requirements.
  Verify: run the pinned kernel's compiler/Rust availability checks and inspect their diagnostics before compilation.
- [x] Slice 2: Compile the complete kernel, modules, and J413 DTB.
  Goal: the selected stack compiles as a complete kernel, not an out-of-tree module overlay.
  Probe first: run a small build target and confirm output paths, selected compilers, and release identity.
  Implementation: use the kernel Makefile with an out-of-tree build directory, then build Image, modules, and the J413 DTB.
  Validation: all requested make targets exit zero; verify Image architecture/release, module versions and dependency closure, DT graph/properties, and relevant GPU/display/audio modules.
  Exit criteria: complete artifacts and build log exist, with no unresolved compile/link/modpost error.
  Evidence: `logs/build-chunks.json` and `logs/build-005.log`: final make exits 0 for Image, modules, and J413 DTB after four planned checkpoints. All 1,862 modules built; whole-kernel linking, BTF, and modpost complete. `logs/staging-receipt.json` records matching module bytes and depmod exit 0 with no diagnostics.
  Assumption: fairydust supports the available toolchain and retained distro configuration.
  Verify: compiler/linker/modpost output and generated configuration reveal compatibility failures; do not mask them by disabling the GPU.
- [x] Slice 3: Assemble and verify an offline delivery bundle.
  Goal: a versioned, inspectable artifact directory or package ready for a separate boot-integration review.
  Probe first: inspect the existing opt-in guard, distro packaging, firmware and boot-bundle requirements without executing their installers.
  Implementation: install modules only into an unprivileged staging root; retain Image, DTB, config, System.map, provenance, checksums, and a clear boot-integration dependency list.
  Validation: check module dependency generation, artifact identities, DT dependencies, file inventory, and absence of host-path writes. Evaluate DT schema tooling and record any unavailable check precisely.
  Exit criteria: bundle and repeatable offline validation command pass independent QA. Installation, initramfs and m1n1 bundle preparation remain explicitly separate if their exact recipe is not yet validated.
  Evidence: `checks/final-qa/final-qa.json`: full gate exit 0, all 1,862 staged modules match, no depmod diagnostics, source bundle verifies with its pinned base prerequisite. DT graph passes; 50 inherited schema findings remain explicitly open.
  Assumption: a complete module tree can be staged without root.
  Verify: use `INSTALL_MOD_PATH` under the owned build root and inspect all resulting paths.
- [x] FINAL: independent verification of the build milestone.
  Goal: a reviewer who did not write the build or plan re-derives every checked claim.
  Validation: rerun the documented offline gate; inspect source/config deltas, logs, artifact hashes, module/DT relationships, and remaining limitations.
  Exit criteria: no disputed build claim; unavailable hardware checks remain open below. Protocol: `self-correction-loop/references/verify-plan-prompt.md`.
  Evidence: independent reviewer verdict PASS at 2026-09-04T21:29:40Z, `checks/final-qa/final-qa.json`. Reviewer reran the full gate and schema validator, verified source/config/tool/artifact evidence, and reviewed plan, report and guide. No disputed offline-build claim remains.

## Validation

The [dated build evidence](../evidence/dev-147-fairydust-build-2026-09-04.md) and its machine-readable receipt retain this run’s commands, identities, and limitations.

The milestone gate is `bash /home/david/Work/omarchy-dev147-fairydust-build/dev/apple-dp-altmode/fairydust/validate-offline.sh /home/david/Work/dev147-fairydust-build`. It covers source/configuration pins, a fresh executable from the pinned extracted-function AFK harness, incremental make completion for Image/modules/J413 DTB, complete module inventory and byte identity, dependency resolution, artifact hashes, and functional DT relationships. The [build guide](../../dev/apple-dp-altmode/fairydust/README.md) documents the artifact boundary. Missing later-stage outputs fail; they are never silently skipped.

Documentation links and `git diff --check` must pass at handoff. The preceding assessment already recorded four baseline Omarchy suite failures: three missing package-checkout tests and one desktop IPC smoke mismatch. This build does not change Omarchy runtime code; kernel/build validation is the acceptance gate for this milestone.

## Progress (LIVING)

- 2026-09-04: User authorized the fresh plan and build. Created the isolated documentation worktree from assessment commit `8863ee615`. Live dev-link still points to `/home/david/o-live`. Remote fairydust and both comparison heads are unchanged. Initial read-only probe found 160 GiB disk available and about 11 GiB available RAM on an eight-core host.
- 2026-09-04: The SWE acquired the complete pinned source into `linux/`, applied the two patches (+215/-47 across six files), and reproduced the AFK candidate PASS with four expected negative controls. The checkout has no remaining Git object alternates, so it does not depend on the old tree's continued existence.
- 2026-09-04: Extracted signed Arch ARM bc, dtc, pahole, rust-bindgen, and matching Rust 1.98 source into `tools/root`. Every archive matched the local sync database SHA-256 and passed `gpgv` against the installed Arch ARM keyring. Tool probes pass. Receipt: `/home/david/Work/dev147-fairydust-build/tools/receipt.json`. No host package installation ran.
- 2026-09-04: Linked the active build plan and initial status from the [DEV-147 build handoff](https://linear.app/helmus/issue/DEV-147/usb-c-displayport-external-monitor-unavailable-on-m2-macbook-air#comment-8d2ca90c).
- 2026-09-04: `rustavailable`, `olddefconfig`, and `prepare rust/core.o rust/kernel.o apple/t8112-j413.dtb` completed successfully. Candidate config SHA-256 is `678853acf4d664a96a4b1a69bba53d3a22ed419d9bf18bb7bcd322956ce849c6`; release is `7.1.12-dev147-fairydust1`. Full Image/modules compilation used four nice-priority workers and planned resumable chunks.
- 2026-09-04: Installed dtschema 2026.6 in an isolated uv environment. Schema preprocessing returned zero with no diagnostics. Static J413 DT validation emitted 50 findings across 127 log lines despite returning zero. These are not a schema PASS; the DT and binding sources are unchanged from pinned fairydust. Retain the diagnostics and inspect the functional DP/SIO graph separately.
- 2026-09-04: The real Asahi GPU object and combined Apple display driver compiled successfully. The later full build completed whole-kernel linking, BTF, and modpost.
- 2026-09-04: Independent gate review identified that version checks alone could accept a missing or mixed module. The corrected gate compares the exact module inventory, installation order, every module's bytes, and builtin metadata. Positive, missing, changed-content, and extra-module regression fixtures pass. Independent review also rejected reordered and symlinked fixtures. Syntax and gate review PASS. The later SWE run of the complete artifact gate exits 0; final independent execution also exits 0.

- 2026-09-04: Complete `Image modules apple/t8112-j413.dtb` build exits 0. Staged 1,862 modules without root, stripping, signing, or compression; every module matches its build output. `depmod` exits 0 with no diagnostics. The candidate contains a thin source bundle with the exact two commits, format patches, checksums, build recipe, and source/config/tool receipts. SWE and independent final offline gates PASS.
- 2026-09-04: Early independent source/config/toolchain QA PASS. Preserved its receipt and 16 hash-verified supporting artifacts in `checks/bindgen/`. The functional DT check passes 11 assertions; 50 inherited schema findings remain open.

- 2026-09-04: Independent FINAL verification PASS. Full gate exits 0; source bundle verifies; repeated DT validation reproduces the same 50 findings. The [dated evidence](../evidence/dev-147-fairydust-build-2026-09-04.md) records the completed offline milestone. Boot integration and all hardware follow-ups remain open. Shell syntax, four module-tree regression fixtures, 32 local documentation links, and `git diff --check` pass.

## Discoveries (LIVING)

- The live distro config is readable at `/proc/config.gz`. The old full source tree has no `.config`, and the installed module build symlink is absent. Existing extracted package/header material may supply provenance and build tools; verify before reuse.
- Host tools report GCC 16.1.1, Clang 22.1.8, and Rust 1.98.0. `bindgen`, `pahole`, `bc`, and `dtc` were not found by the initial PATH probe. A kernel build may need isolated tool extraction rather than host installation.
- The extracted bundle's file named `config` is an initramfs configuration, not a kernel configuration. Use the saved live kernel config at `/home/david/Work/dev147-fairydust-build/config/live-7.1.6.config`, SHA-256 `701d1270a36cb57047558ab78e7d825900cc76935e42fd96003c319d1b9050e4`, which agrees with the historical kernel-header config pin.
- The mirror alias rejects HTTPS due to its certificate hostname. The configured official mirror uses HTTP. Package acquisition used that configured transport and verified both the signed package and database checksum before extraction; TLS checks were not disabled.
- The inherited `RUST_LOG=warn` exposes extensive internal bindgen warnings. Independent review reproduced all three emitted binding files byte-for-byte. All 54,526 opaque fallback warnings refer to macro-expansion cursors, not C structure fields. GCC, Clang, and Rust agree on the 98 checked type sizes/alignments and 15 field offsets. These probes support using the current toolchain; they do not prove every ABI or runtime path. Known forward-enum warnings and one upstream Rust unused-import warning remain recorded.
- `dt-validate` returns zero even with schema findings. Its output must be inspected. The unchanged upstream DT uses undocumented `displayport` wiring and other Apple properties that current schemas reject; this is an explicit prototype limitation, not a locally introduced DT change.
- Upstream removed deprecated `CONFIG_EROFS_FS_ONDEMAND`; olddefconfig did not accidentally disable it. Required desktop/GPU/DP/SIO/16K settings and core EROFS remain. This build does not claim that every historical configuration capability still exists upstream.

## Decision Log (LIVING)

- 2026-09-04: Adopt the assessed immutable fairydust pin and exactly two patches. This replaces the reduced local DT/TIPD backports and avoids the GPU-broken 7.2 branch.
- 2026-09-04: Treat this as an offline build milestone. Keep boot selection, package guard migration, initramfs/m1n1 assembly, and hardware acceptance distinct from successful compilation.
- 2026-09-04: Preserve existing source/config evidence and recovery assets. Use a separate Linux checkout and output directory; do not change historical helper pins to make them accept a new kernel.

## Follow-ups

- [ ] Prepare and review coherent Image/modules/DTB/initramfs/m1n1 delivery and rollback, including the existing package guard. Any privileged action is a user-run command.
- [ ] Attended reconnect acceptance beyond the old exhaustion window, both known monitors, cold/hot attach, and healthy internal display.
- [ ] Validate SIO/display audio, USB2/USB3 data, charging, simultaneous video/data/power, both orientations, and both ports. DEV-163 owns monitor-hub data loss.
- [ ] Resolve second-port DP routing, suspend/resume, and power drain with measured evidence.
- [ ] Reconcile inherited device-tree schema findings with upstream bindings and bootloader-populated properties before claiming complete DT schema compliance.
- [ ] Integrate the complete upstream USB4 series and prerequisites on a separate experimental branch; preserve the GPU-capable baseline.
- [ ] Investigate only remaining unsupported role/routing, PCIe/DP tunneling, and power-state behavior after upstream integration.
