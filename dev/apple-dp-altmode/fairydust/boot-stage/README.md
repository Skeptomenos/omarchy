# Stage the fairydust boot files

This handoff adds a complete, versioned candidate without selecting it. The [boot-integration plan](../../../../docs/plans/2026-09-05-dev147-fairydust-boot-integration.md) owns readiness and the remaining activation steps. The [dated evidence](../../../../docs/evidence/dev-147-fairydust-boot-preparation-2026-09-05.md) records the validation result.

## User command

After the plan records independent handoff PASS, David runs:

```bash
bash /home/david/Work/omarchy-dev147-fairydust-build/dev/apple-dp-altmode/fairydust/boot-stage/launch.sh
```

Run the launcher as the normal user. It invokes sudo for the fixed stage operation and asks for the password. The launcher verifies the exact helper bytes in the privileged process before executing those same bytes. It pins the delivery manifest to `f33054856e60d3baf5cb7630cb8d7dfc60ffa586e16456c3e7313fffe6f7c59d`.

It creates:

- `/boot/dev147-fairydust-7.1.12-dev147-fairydust1/`: Image, initramfs, m1n1 bundle, raw DTB, config and receipts.
- `/usr/lib/modules/7.1.12-dev147-fairydust1/`: the full matching module tree.
- `/var/lib/dev147-fairydust-stage/7.1.12-dev147-fairydust1/`: root-owned staging inputs and protected-state evidence.
- `/home/david/Work/dev147-fairydust-boot-20260905/stage/manual-results/`: user-private result JSON, stderr, exit status and input identities.

Allow about 5 GiB of free space for the retained staging copies and published files. The helper exclusively holds the pacman lock while it verifies and stages the files. It refuses existing destinations, package activity, altered input bytes, symlinks, hardlinks, unsafe paths and protected-state drift. A refusal can leave new isolated staging paths for inspection. Do not delete files to bypass it or rerun the launcher over its saved result directory.

Success is exit status `0` and `STAGED_UNSELECTED` in `result.json`. The command does not reboot. Its result also contains the protected GRUB configuration and hashes needed for the next review; a second privileged read is not part of the normal handoff.

## Boot and recovery boundary

The installed candidate is unselected. The active m1n1 bundle, GRUB configuration, default image, existing package guard and old integration state remain in place. Keeping the candidate unselected is the staging rollback; deleting its files is unnecessary.

The next stage must select m1n1, kernel and initramfs coherently. m1n1 prepares Apple firmware and memory properties before GRUB. Supplying the raw DT through GRUB skips that work. Once the shared m1n1 bundle changes, merely choosing an old kernel is not a proven fallback.

Activation must also handle GRUB saved/next/fallback entries and interruption between writes. `boot.bin` is on FAT EFI, but `grub.cfg` is on ext4. macOS/Recovery can restore the former directly; access to the latter needs a separately verified route. No complete activation or restore procedure is released by this staging handoff.

## Validation

The complete offline gate is:

```bash
bash /home/david/Work/omarchy-dev147-fairydust-build/dev/apple-dp-altmode/fairydust/validate-boot.sh
```

It validates the real kernel, initramfs and m1n1 bundle, external vendor firmware, the full delivery manifest, failure controls, Python formatting/types, and the exact stage entry point with the real delivery in a disposable namespace. The sandbox uses synthetic protected GRUB/state fixtures. Live protected-state collection happens only when David runs the stage command.
