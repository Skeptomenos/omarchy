# Stage and select the diagnostic kernel

This recipe stages the clear-wait trial without changing the saved Fairydust boot selection. The [trial guide](../README.md) links the plan and build evidence.

Validated kernel and initramfs → private delivery → root-owned staging copy → temporary GRUB edit. No additional environment keys are required.

## Prepare and stage

After the build and initramfs gates finish, assemble their exact outputs. The build log needs a sibling file named `BUILD_GATE_LOG.exit-status` containing `0`.

```bash
bash assemble-delivery.sh INITRAMFS_RUN INITRAMFS_GATE_DIRECTORY BUILD_GATE_LOG
bash validate.sh
```

The assembler checks source/config pins, all modules, the initramfs receipt and gate image hash, and exact DT equality with Fairydust1. It preserves check receipts and text logs in the delivery. It omits extracted image trees and large module fixtures. It does not rebuild the ESP bundle.

The launcher deliberately rejects an unset delivery pin. Finalize the manifest pin only after the completed delivery passes independent review and a full namespace rehearsal. Then run as the normal user:

```bash
bash /home/david/Work/omarchy-dev147-fairydust-build/dev/apple-dp-altmode/fairydust/clear-wait-trial/stage/launch.sh
```

David enters the sudo password. The helper stages `/boot/dev147-trial-7.1.12-dev147-clearwait100` and `/usr/lib/modules/7.1.12-dev147-clearwait100`. It checks the current selected boot and recovery hashes. It writes private receipts under `/var/lib/dev147-clearwait-stage/7.1.12-dev147-clearwait100` and exports the result to the launcher's private result directory. Verify `STAGED_UNSELECTED`, exit `0`, and the published files before restarting.

## Select once

At the existing Fairydust GRUB menu, highlight `DEV-147 fairydust 7.1.12` and press **e**. Change only these two paths:

```text
linux /boot/dev147-trial-7.1.12-dev147-clearwait100/Image root=UUID=e24cf117-3c89-4392-a3b8-def187becda8 rw loglevel=3 quiet disablehooks=encrypt
initrd /boot/dev147-trial-7.1.12-dev147-clearwait100/initramfs.img
```

Keep the other lines unchanged. Press **Ctrl-X** to boot this edit. Press **Esc** before booting to discard it. After Linux starts, `uname -r` must print `7.1.12-dev147-clearwait100` before a trial trace is accepted.

This edit is temporary. An ordinary subsequent boot still selects Fairydust1. If the trial does not start, return to the GRUB menu and boot the unchanged Fairydust entry. Do not use `grub-reboot`: the current candidate configuration clears saved and next-entry values.

## Recovery scope

Staging changes neither `/boot/grub` nor the ESP. It preserves the Fairydust1 files, existing module release, guard and prior recovery state. The current ESP bundle remains paired with both kernels only because the trial DT is byte-identical.

The existing [paired recovery guide](../../boot-activate/RECOVERY.md) restores the older pre-Fairydust stack. That is separate from returning from this trial to the unchanged Fairydust default. Do not replace only GRUB or only the ESP bundle for that older recovery route.

Offline checks do not establish trial boot, display recovery, USB behavior or endurance.
