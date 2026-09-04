# DEV-147 combined fairydust build — 2026-09-04

The complete offline kernel build passed. This is a build and artifact result. It does not establish boot, display, USB, audio, charging, suspend, or Thunderbolt behavior.

## Selected stack

The [assessment](../research/dev-147-upstream-reconciliation-2026-09-04.md) selected the complete Asahi fairydust tree at `b8810ad6442699f610984f3eceea2e3234a50b77`, followed by corrected AFK service reuse and the attributed PR582 timeout adaptation. No reduced local DT, TIPD backport, USB diagnostics, or USB4 series was added.

The combined Linux commit is `83604c8b18e4673ed91e1172aef9aebeb0af20ce`, on `codex/dev147-fairydust`. It has exactly two commits after the base, changes six files, and has a clean working tree. The source checkout has no Git object alternates.

| Item | Result |
|---|---|
| Kernel release | `7.1.12-dev147-fairydust1` |
| Image SHA-256 | `5175f41bb2d25abce49f6a844cdbe9233a4d090de34fa9aadcf6512c87590079` |
| J413 DTB SHA-256 | `9831d42f9c271ce35dd3e32b5c8298e1c13849568853aea0779f40bb67377b80` |
| Config SHA-256 | `678853acf4d664a96a4b1a69bba53d3a22ed419d9bf18bb7bcd322956ce849c6` |
| Modules | 1,862; every staged file matches its build output |
| Enabled features | Asahi GPU, Apple display, DP alt mode, SIO/display audio, 16K pages, BTF |
| Toolchain | GCC 16.1.1, Clang/LLVM 22.1.8, Rust 1.98.0, bindgen 0.72.1 |

## Commands and observed results

Commands ran from `/home/david/Work/dev147-fairydust-build`. The checked-in [gate and guide](../../dev/apple-dp-altmode/fairydust/README.md) describe the validation boundary. The [machine-readable receipt](dev-147-fairydust-build-2026-09-04.json) retains identities and supporting evidence hashes.

| Command or check | Observed result |
|---|---|
| `./build-command.sh rustavailable` | Rust available; exit 0 after private tool extraction |
| `./build-command.sh olddefconfig` | Exit 0; full delta retained |
| `./build-command.sh prepare rust/core.o rust/kernel.o apple/t8112-j413.dtb` | Exit 0 |
| `timeout --signal=INT --kill-after=15s 280s ./build-command.sh Image modules apple/t8112-j413.dtb` | Four planned resumable checkpoints, then exit 0 in chunk five; Image, all modules and DTB complete |
| `./build-command.sh INSTALL_MOD_PATH=/home/david/Work/dev147-fairydust-build/artifacts/root INSTALL_MOD_STRIP= DEPMOD=true modules_install` | Exit 0; unprivileged staging only |
| `depmod -b artifacts/root -e -F build/System.map 7.1.12-dev147-fairydust1` | Exit 0; no diagnostics |
| Complete `validate-offline.sh` gate | SWE and independent QA each exit 0; 1,862 modules, inventory/byte identity, hashes, dependency closure, Image architecture/BTF, required config and functional DT wiring pass |
| Fresh AFK extracted-function harness | Candidate exits 0; stock, unsafe reuse, unsafe send and unsafe race each exit 1 with its expected failure marker |
| Bindgen/toolchain audit | Three regenerated bindings byte-identical; C/Rust agree on 98 type layouts and 15 field offsets; signed private package archives verified |
| `dt-mk-schema` / `dt-validate` | Both exit 0, but validation emits 50 findings across 127 lines: **not a clean schema pass** |

The build wrapper pins a timestamp, local release, private Rust source/tool paths, and four reduced-priority workers. Its exact bytes are preserved in the candidate. The full make logs and initial diagnostics remain under `logs/`.

The initial bindgen run emitted extensive internal warnings under inherited `RUST_LOG=warn`. Independent tracing found that all 54,526 opaque fallback warnings refer to macro-expansion cursors. The checked layouts agree across GCC, Clang, and Rust. Known forward-enum warnings and an upstream Rust unused-import warning remain recorded. This targeted audit is not an exhaustive ABI proof.

The starting configuration came from the live kernel and matches the historical header config pin. The file named `config` in the old extracted boot bundle is an initramfs configuration and was not used. Upstream removed deprecated `EROFS_FS_ONDEMAND`; core EROFS remains. The delta discloses this removal instead of claiming full configuration equivalence.

## Retained artifacts

- Candidate: `/home/david/Work/dev147-fairydust-build/artifacts/candidate-7.1.12-dev147-fairydust1`.
- Modules: `/home/david/Work/dev147-fairydust-build/artifacts/root/lib/modules/7.1.12-dev147-fairydust1`.
- Source and build output: sibling `linux/` and `build/` directories. Keep `build/vmlinux` for later debugging.
- Evidence: `logs/source-config-receipt.json`, `logs/build-chunks.json`, `logs/staging-receipt.json`, `checks/bindgen/`, `checks/dt/`, and `checks/final-qa/` under that build root.

The candidate contains Image, J413 DTB, config, symbol/version files, two format patches, a source bundle, tool/source receipts, module hashes, and `SHA256SUMS`. Modules remain unstripped, unsigned, and uncompressed for exact byte comparison. The candidate is about 41 MiB; its separate module staging tree is about 2.0 GiB.

The thin `source.bundle` preserves the exact two local commits and **requires upstream base `b8810ad6442699f610984f3eceea2e3234a50b77`**. It is not a standalone Linux source archive. The full local checkout is self-contained. Recipe paths are specific to this workspace; recreating elsewhere requires path updates and a new receipt. No independent clean-room rebuild or bit-for-bit reproducibility claim was made.

## Remaining work

The [fresh plan](../plans/2026-09-04-dev147-fairydust-build.md) owns the next steps. Prepare a coherent initramfs/m1n1/DTB/Image/module delivery and rollback procedure, reconcile the old package guard, and verify bootloader-populated SIO firmware data. Then perform attended reconnect tests beyond the old exhaustion window, both monitors, internal-display regression checks, and video/data/audio/power tests on both ports and orientations.

The pinned DT and binding source are unchanged by the two patches. Its functional DP/SIO graph passes, but schema findings remain. Upstream's single DP route and always-on ATC workaround are not evidence for second-port DP or correct suspend/power behavior. USB4 must follow as a separate coherent upstream series with prerequisites; remaining PCIe/DP tunneling and power-state gaps must be evaluated there.

The running kernel remains `7.1.6-1-1-ARCH`; `omarchy dev status` still points to `/home/david/o-live`. No privileged install, host package installation, boot selection, or runtime-tree edit ran. Four previously recorded Omarchy suite baseline failures remain outside this kernel milestone; this report does not claim a clean whole-repository suite.
