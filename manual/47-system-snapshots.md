# System snapshots

Omarchy checks automatic rollback before each update. A configured Btrfs root can store the pre-update snapshot, but automatic rollback also needs a supported restore backend. Run `omarchy snapshot check` to test the current system. The check does not change the system or ask for `sudo`.

### Support matrix

| Root and boot setup | Status |
| --- | --- |
| Btrfs with a Snapper root config for `/`, Limine, and active Limine snapshot sync | Supported. Updates create a snapshot, and Limine can boot and restore it. |
| Btrfs with GRUB on Apple Silicon or Asahi | Automatic restore is unavailable in this release. Snapper can store snapshots when configured, but an update cannot promise automatic rollback. |
| LVM thin provisioning | Not implemented. |
| Plain ext4 | Unsupported. Ext4 cannot provide the Btrfs snapshots that this feature uses. |

When the readiness check fails, an interactive update shows a warning and asks for a second confirmation. The update asks for the same confirmation before package changes if readiness passed but snapshot creation later fails. An unattended `omarchy update -y` logs the warning and continues.

### Create and restore a supported snapshot

Use `omarchy snapshot create` to create a snapshot outside an update.

On a supported Limine system, restart and select the snapshot by its date and Omarchy version. If the machine normally boots directly to the Omarchy decryption screen, select Limine from the firmware boot menu first.

![snapshots-bootloader](images/snapshots-bootloader.webp)

After the snapshot boots, select the notification to restore it. You can also run `omarchy snapshot restore`.

![snapshots-restore](images/snapshots-restore.webp)

The snapshot restores the root filesystem. It does not restore `/home`, including `~/.config`. A snapshot can reverse a broken system update, but it cannot recover lost personal files. Configuration written in a newer application format can also need manual repair after a rollback.

### Recovery without automatic rollback

Make a current external backup before an update when `omarchy snapshot check` reports that automatic rollback is unavailable.

If the system still boots, `omarchy reinstall` can reinstall the default packages and configuration and return the system to stable package versions. It is a repair operation, not a rollback. It does not restore the exact earlier system state or recover personal files. It also overwrites changes to the default Omarchy configuration.

If the system does not boot, use installation or recovery media to repair or reinstall Omarchy, then restore personal files and other required state from the external backup.

### Skipping the boot menu

If you never use the boot menu and want the machine to go straight to the decryption screen, run _Setup > Direct Boot_ in the Omarchy menu. This adds an EFI entry that points directly at Omarchy.

With direct boot enabled, select Limine from the firmware boot menu when you need a snapshot. Run _Setup > Direct Boot_ again to remove the entry and return to Limine. The setup refuses to run on American Megatrends and Apple firmware because some firmware does not handle custom EFI entries safely.
