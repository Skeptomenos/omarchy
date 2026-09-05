# Fairydust staging verified — 2026-09-05

David ran the reviewed launcher successfully. The candidate `7.1.12-dev147-fairydust1` is installed and unselected. The running kernel remains `7.1.6-1-1-ARCH`. No activation or reboot occurred during this verification.

The [bounded JSON receipt](dev-147-fairydust-staged-2026-09-05.json) binds the manual result, checks and independently reviewed source hashes. Full protected configuration and state inventories remain private under `/home/david/Work/dev147-fairydust-boot-20260905`.

## Apply and checks

The user ran `bash /home/david/Work/omarchy-dev147-fairydust-build/dev/apple-dp-altmode/fairydust/boot-stage/launch.sh`. Saved exit status is `0`, stderr is empty, and `result.json` reports `STAGED_UNSELECTED`. The helper and launcher retain their reviewed hashes.

`bash /home/david/Work/omarchy-dev147-fairydust-build/dev/apple-dp-altmode/fairydust/validate-staged.sh` exits 0 for both the author and independent QA. Their retained runs are `checks/staged-gate.XdDL0sq9` and `checks/staged-gate.OMOzM8fN`. The gate includes the complete offline boot rehearsal, ten new verifier controls, and actual-publication checks.

| Check | Observed result |
|---|---|
| Published files | All 1,885 manifest entries match, plus the copied manifest itself |
| Boot directory | 10 exact files |
| Module directory | 1,876 exact files, including all 1,862 modules |
| File properties | Regular, root-owned, single-link, no group/other write access; no extra files |
| Readable protected state | 4,522 matches, zero mismatches |
| Root-private protected state | 68 paths not independently readable; stage receipt only |
| Saved boot configuration | All five exported strings match the protected receipt hashes |
| GRUB export | `grub-script-check` exits 0; two old kernel/initramfs entries; empty GRUB environment |
| Active inputs | Existing boot bundle, package guard and external vendor firmware hashes match |
| Independent review | No blocking finding; staged-publication claim supported |

The new verifier controls cover failed manual execution, diagnostics, wrong helper identity, changed configuration, wrong stage status, modified published bytes, symlinks, wrong ownership and unsafe manifest paths. The unchanged kernel, initramfs and staging checks retain their earlier negative controls. This is a focused milestone PASS. The unrelated Omarchy suite limitations remain recorded in the [preparation evidence](dev-147-fairydust-boot-preparation-2026-09-05.md).

## Recovery and remaining work

Keeping the candidate unselected preserves the old boot. Restaging or deleting the new files is unnecessary. The [paired activation plan](../plans/2026-09-05-dev147-paired-activation.md) owns the next work: exact kernel/DT selection, complete recovery, a reviewed user-run activation command and attended hardware acceptance.

The active GRUB configuration is still root-private. Its exported contents were verified against the stage receipt; a future privileged helper must verify the live file again before any selected-boot write. Static checks and staging success do not establish candidate boot, display, USB, audio, charging or suspend behavior.
