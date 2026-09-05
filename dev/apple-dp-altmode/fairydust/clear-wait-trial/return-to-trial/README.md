# Return to the Fairydust trial

This guarded return selects the existing 100 ms trial from the restored original boot stack. It preserves the original activation state and recovery backups. The [trial guide](../README.md) links the living plan and evidence.

Validated staged kernels → saved previous menu and deployment journal → trial menu → existing dispatcher → matching Fairydust ESP bundle. The default entry is `DEV-147 fairydust 7.1.12 - test1 (100 ms)`. The second entry boots Fairydust1. Both use the same device tree. The older W configuration is not an entry under this bundle.

## Run after review

Run as the normal user when the new helper and its checks have passed independent review:

```bash
bash /home/david/Work/omarchy-dev147-fairydust-build/dev/apple-dp-altmode/fairydust/clear-wait-trial/return-to-trial/launch.sh
```

The command asks for the sudo password and does not reboot. It requires the original `7.1.6-1-1-ARCH` kernel, restored boot hashes, intact existing backups and routing files, and both complete staged module inventories. No environment keys or command arguments are required.

The installed module cleanup service can archive unowned, inactive test kernels during boot. If either candidate module directory is absent, complete the separately reviewed [module repair](../module-repair/README.md) first. A prior stage receipt alone does not prove that the active module paths still exist.

Send the printed result path for verification. Success requires exit `0`, an empty `stderr.log`, and `RETURNED_TO_TRIAL_NOT_REBOOTED` in `result.json`. The helper stores the previous candidate menu and each completed write boundary under `/var/lib/dev147-clearwait-return/7.1.12-dev147-clearwait100`.

After verification, restart manually. The trial entry is the default; no path editing is needed. Before any comparison trace, verify `uname -r` prints `7.1.12-dev147-clearwait100`.

## Recovery and limits

A failure can leave the new menu, dispatcher, or bundle selected. Preserve the result and deployment journal. Do not rerun an interrupted attempt: the existing return-state directory causes refusal.

The unchanged [restore command](../../boot-activate/README.md) remains the recovery route from working Linux. It replaces the older bundle first, then the original GRUB configuration. It does not automatically select the W test initramfs; W still needs the separate manual initramfs edit. For an unbootable system, the existing [macOS recovery guide](../../boot-activate/RECOVERY.md) applies. A stale package lock requires manual assessment.

The namespace checks substitute topology discovery and the synthetic original-stage receipt identity. They use the real frozen Fairydust and trial artifacts. They do not prove physical FAT atomicity, power-loss behavior, display recovery or hardware acceptance. No reboot or live privileged mutation runs in the software gate.
