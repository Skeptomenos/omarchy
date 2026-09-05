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
