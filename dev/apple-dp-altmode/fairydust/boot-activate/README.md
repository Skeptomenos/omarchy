# Select the paired fairydust boot stack

The activation and recovery handoff passed independent offline QA on 2026-09-05. David then ran activation successfully: `ACTIVATED_NOT_REBOOTED`. The [living plan](../../../../docs/plans/2026-09-05-dev147-paired-activation.md) owns execution status; [preparation evidence](../../../../docs/evidence/dev-147-fairydust-activation-preparation-2026-09-05.md) records offline checks and [activation evidence](../../../../docs/evidence/dev-147-fairydust-activated-2026-09-05.md) records the apply. Candidate boot remains open.

The candidate kernel and modules are already staged. Activation preserves the old configuration and EFI bundle, installs the verified GRUB selector while the old bundle remains active, then replaces the EFI bundle. The selector requires exactly one bundle hash to match before it loads the paired kernel configuration.

## Activate

The command below has already been applied. Do not run it again. Its saved result is `/home/david/Work/dev147-fairydust-boot-20260905/activation/activate-results.iUG81ebY`.

Keep the [recovery guide](RECOVERY.md) available in macOS before the first candidate boot. Recorded command, already executed:

```bash
bash /home/david/Work/omarchy-dev147-fairydust-build/dev/apple-dp-altmode/fairydust/boot-activate/launch.sh
```

It asks for the sudo password. It does not reboot. Its checks bind the helper, payload, existing stage and live boot inputs. Read its saved result before restarting; a failed command is not evidence that selected boot stayed unchanged.

Success reports `activate exit: 0`. The printed private result directory contains `result.json` with status `ACTIVATED_NOT_REBOOTED`, plus `exit-status`, diagnostics and input identities. Send the result path for verification before the first candidate restart. The launcher does not print the root receipt itself.

## Restore

From working Linux:

```bash
bash /home/david/Work/omarchy-dev147-fairydust-build/dev/apple-dp-altmode/fairydust/boot-activate/restore.sh
```

Restore verifies and replaces the old EFI bundle first, then restores original GRUB. It preserves the candidate and evidence. If Linux cannot start, follow the UUID-based macOS instructions in the recovery guide. Restoring only the old GRUB configuration could select an old kernel under the candidate device tree.

Successful Linux restore records `RESTORED_NOT_REBOOTED` in its private result directory. A stale package lock requires manual assessment; the recovery guide explains the separate macOS route.

## Validate

This is the pre-activation gate. It expects the old selected boot state and must not be rerun against the activated system. Preserve its completed evidence; use the activation receipt and post-boot checks for the next milestone.

```bash
bash /home/david/Work/omarchy-dev147-fairydust-build/dev/apple-dp-altmode/fairydust/validate-activation.sh
```

The complete activation gate passed for both the author and independent QA. It chains the staging and full boot preparation gates, then runs 22 namespace controls, four topology checks, 19 real GRUB probes, 14 recovery guard cases, exact launcher read-only preflights, shell syntax, Ruff and strict mypy.

Namespace fixtures substitute topology discovery and the expected prior-stage receipt identity. They do not perform a physical FAT transaction. Replacement failures are injected at selected-file boundaries; SIGKILL, fsync faults and power loss are not simulated. macOS recovery commands have not run on this machine. Offline PASS does not establish candidate boot or USB/display behavior.
