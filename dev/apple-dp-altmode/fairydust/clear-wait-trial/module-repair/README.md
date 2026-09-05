# Repair and retain the two candidate module trees

This repair restores Fairydust1 and clearwait100 modules from their frozen private deliveries. The distro cleanup service removes unowned, non-running module releases. A temporary drop-in exempts exactly these two releases and keeps the original cleanup behavior for other releases. Packaging ownership remains a follow-up.

Frozen deliveries → bounded root-owned verification copies → exact-two cleanup exception and daemon reload → atomic publication of missing module directories. No rebuild, boot selection or reboot occurs.

## Run after independent review

```bash
bash /home/david/Work/omarchy-dev147-fairydust-build/dev/apple-dp-altmode/fairydust/clear-wait-trial/module-repair/launch.sh
```

Run as David. The normal-user preflight checks frozen helper hashes, service identity and inactive state, target absence, source manifest pins and readable source paths before asking for the sudo password. The privileged helper repeats full checks against its private copies.

The command installs `/etc/systemd/system/linux-modules-cleanup.service.d/50-dev147-candidate-modules.conf`, reloads systemd and verifies the effective command. It does not start or restart cleanup. It then publishes both missing module directories. It refuses existing module targets, overrides, drop-ins or repair state.

Success requires exit `0`, an empty `stderr.log`, and `MODULES_REPAIRED_NOT_SELECTED` in the exported `result.json`. The private deployment journal is `/var/lib/dev147-module-repair/20260905`. Verify the result and both published trees before using the separate [return-to-trial command](../return-to-trial/README.md).

The repair preserves all existing boot files, W modules and initramfs, `.old`, the guard and previous activation/staging state. It does not recover from `.old`; that archive is not durable. A failed partial publication can leave the exception and one repaired tree in place. Preserve the journal and inspect the completed boundaries before any retry. Do not remove locks or repair state automatically.

## Validate

```bash
bash validate.sh
```

Namespace tests use the actual frozen delivery files with synthetic current-kernel/boot/state fixtures and a mocked systemd manager. Separate tests execute the actual cleanup body with real bash, rsync and rm on disposable directories; package ownership is a fixture. Systemd checks the unit/drop-in syntax. No live privileged operation, reboot or hardware test runs in the gate.
