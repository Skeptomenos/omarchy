# Clear-wait diagnostic preparation — 2026-09-05

## Decision and scope

The [fixed-X8 reconnect](dev-147-fixed-x8-reconnect-timeout-2026-09-05.md) recorded a 51.749 ms clear-swap reply chain followed by the timeout warning and no shutdown tail. This justified preparing one diagnostic change: extend the existing wait from 50 to 100 ms. It does not establish a production timeout bound or prove that the rear drive caused the delay.

The user authorized continued implementation until manual support is required. The [living plan](../plans/2026-09-05-dev147-front-port-stability.md) owns remaining work. No privileged action or boot change occurred during this preparation.

## Frozen source

Trial root: `/home/david/Work/dev147-clear-wait-trial`.

- Source commit: `d2f36591abdb0db296ac24e5a2b9dade5ae40ef1`.
- Parent: `83604c8b18e4673ed91e1172aef9aebeb0af20ce`.
- Only driver delta: 50 → 100 in the clear-swap completion wait.
- Release: `7.1.12-dev147-clearwait100`.
- Config SHA-256: `f69e63e55cbc6b257a951c82b3e581ffc60d4614a5965561cbc322960767bdff`.
- Only baseline config delta: `CONFIG_LOCALVERSION`.

The source retains the AFK correction and PR582 timeout recovery behavior. The baseline source, output, installed kernel and recovery files remain separate. Compilation uses the same pinned toolchain and reduced-priority four-job recipe, with planned 280-second checkpoints.

## Checks completed at preparation

`bash dev/apple-dp-altmode/fairydust/clear-wait-trial/validate.sh` returned zero. The independent run was `checks/offline.YSuzV7Ca`; its review receipt SHA-256 is `1580dbf413b84b9c4bf8b42c90ce8c6d5947748fb9f4a2118729ebb8fcf04bc4`.

The gate checks the exact patch and extracts six Linux completion functions into a deterministic C harness. The baseline rejects a 52-tick reply; the candidate accepts it. Absent replies, late replies, precompletion and deadline-boundary controls pass their expected outcomes. Compiler warnings are errors; UBSan, Ruff, formatting, strict mypy and shell syntax checks passed.

The harness does not execute DCP poweroff, callback lifetime, RTKit, KMS or the shutdown tail. It establishes completion semantics within its time/locking model.

The isolated initramfs recipe reuses the baseline namespace builder with new release/source/config pins. Independent preparation ran 13 checks: eight shell syntax checks, module mutation controls, startup controls, wrong-release image rejection, truncated image rejection and diff checks. All passed. Receipt: `checks/initramfs-recipe-independent.al8xm25x/receipt.json`, SHA-256 `8323c018a5c918ec3886e1f47a5fc2dd9190471d7fc30aa3503ebf9e3e98f467`. The parent completion gate also passed again at `checks/offline.khr2IBtL`.

## Limits at this checkpoint

Full compilation, module staging, artifact validation, actual trial initramfs creation and independent artifact review were pending when this preparation record was written. Hardware acceptance remains open. The selected kernel remains `7.1.12-dev147-fairydust1`.

The [trial procedure](../../dev/apple-dp-altmode/fairydust/clear-wait-trial/README.md) provides commands. Subsequent build and boot results must be recorded separately or as dated addenda.

## Addendum — build and initramfs completed, 2026-09-05

The fifth compilation chunk returned zero. The first four returned the planned checkpoint status 124; a scan found no compiler-error, fatal-error or undefined-reference diagnostics. `logs/build-chunks.json` preserves that distinction. Private module installation and explicit depmod returned zero; depmod stderr was empty.

Assembly returned zero. The full `validate-build.sh` gate returned zero at `logs/full-build-gate.log`, reporting all 1,862 modules, AFK controls and J413 DP/SIO wiring PASS. Image SHA-256: `048af4bcf37e0ce365bfeb2ebb03c42c8786631cd48b94ea37e6e355975f2f84`.

The J413 DTB is byte-identical to the baseline: `9831d42f9c271ce35dd3e32b5c8298e1c13849568853aea0779f40bb67377b80`. This trial needs no ESP/m1n1 bundle replacement.

The unprivileged namespace initramfs build returned zero at `initramfs/run-001`. Image SHA-256: `a3de88afae768731a0a23bd7aaaacc02e19ac520fbed0f5df7c41ae69cf3dae9`. Actual-image validation, module and startup controls, and truncated-image rejection returned zero at `checks/initramfs.Zl3ZF15p`.

Independent stage preparation passed 22 namespace controls at `checks/stage.SGSteyFc`. Its review receipt SHA-256 is `a3628e88e589eef05842fffbbbd79f60615a3d8521a65419e3347873c6004526`. The pending launcher refused to run before sudo. Independent assembly-procedure review passed at `checks/assembly-review-independent.kd35sec_`, receipt SHA-256 `2ee73d9590d584a79770f67d06d6b70f188558ad032c24fb2aa9d6bce3c161fd`.

The stage procedure preserves GRUB, the ESP and existing recovery inputs. The trial can later be selected by changing only its kernel/initramfs paths in a transient GRUB edit. Full delivery rehearsal and real manual staging remain pending at this addendum.

## Addendum — full delivery rehearsal, 2026-09-05

Independent full build validation returned zero at `checks/build-independent.z2lninmt`. Receipt SHA-256: `9641f033ef8e514a15311e97eb5d24c6b944a28982d0893305d7b7b95a91c97e`. Generated helper Rust bindings match the baseline; main/UAPI binding differences reflect only the release string and its length. Build warnings do not establish a new binding-layout change.

The assembled delivery manifest SHA-256 is `a89c31f8b42c3f4f958ac8aca4c312c95a222baf2e80b8b5702dbe4549e8a857`. Independent full-delivery staging ran the exact bootstrap/helper in disposable unprivileged namespaces at `checks/stage-full-independent.y9ny2ep8`. It passed in 8.966 seconds: all 1,862 modules, 1,876 module-manifest files, published boot inputs and receipts matched. All 15 protected fixture files retained their hashes.

The rehearsal used the actual delivery and readable baseline boot files. It used saved routing source for root-private GRUB fixtures. The real helper must still check those live private files during David's run. No actual staging or boot occurred.

The final launcher pins this rehearsed manifest. Launcher SHA-256: `2355fc81da26309b74e3a4fa7db29889b97c8584c173c4e394084fee32c5355f`. Helper SHA-256: `96b4ef29a03897c612ff2a978a932b5dc31d6da2cf7dfc1eded7ab08ed20ea1f`. Shell syntax and diff checks pass. The next manual action is the stage-only launcher; review its receipt before a restart or temporary trial selection.

Independent actual initramfs validation also returned zero at `checks/initramfs.w0A63RDv`. Trial capture software validation returned zero at `acceptance/checks/software.H7qELEYw`. Its explicit uname fixtures cover the trial release and reject baseline/unknown releases before trace setup. These are preboot software results, not live trial capture.

Final independent review reports no blocker to the stage-only handoff. It verified that the final launcher differs only by replacement of the pending manifest with the rehearsed hash. Actual initramfs validation covers 334 matching modules and 12 embedded firmware files; the existing ESP vendor archive remains separately verified. Final review receipts:

- `checks/initramfs.w0A63RDv/independent-review.json`: `bb0c74f2f5af41af4a01d71cc4094535837710aa7d48c920beffa0ba270e27a9`.
- `acceptance/checks/software.H7qELEYw/independent-review.json`: `ae8f780f5c960229260646ace0066f3482a5ef3252673bdf202029a85f0cbb96`.
- `checks/stage-full-independent.y9ny2ep8/final-launcher-review.json`: `cd8eef2a3633ca9f6d1ebda5061292fd874811d2353296ccb2735a9b9c41fff1`.

No actual staging, boot, tracing or trial hardware acceptance occurred. DEV-147 was updated with the stage-only dependency and commits `92c16aa0d` and `78cb3a2cd`.

## Addendum — actual stage verified, 2026-09-05

David ran the pinned stage launcher and supplied exit 0. The private receipt at `/home/david/Work/dev147-clear-wait-trial/stage/manual-results/result.json` reports `STAGED_UNSELECTED`, the exact trial release and manifest. Receipt SHA-256: `cac1088402b6bb90d08baba8a55eda17be3b1424edc291bd8045a910145e9eb5`. Stderr is empty.

Read-only verification of installed module files with `sha256sum --check --strict --status /home/david/Work/dev147-clear-wait-trial/delivery/modules.sha256` from `/usr` returned zero. Published Image, initramfs and config hashes match the accepted delivery. The new boot and module directories are root-owned, mode 755. The helper reports preserved current default, ESP and protected state. The running release remains `7.1.12-dev147-fairydust1`.

Actual staging is complete. Trial boot and hardware validation remain pending. The next attended action is a transient GRUB edit of only the linux/initrd paths, as specified in the stage guide. Preserve current cable connections for the boot observation; report release and visible internal/external display behavior before any further reconnect.
