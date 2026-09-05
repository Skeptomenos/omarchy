# Fairydust activation handoff verified — 2026-09-05

The paired activation and recovery handoff passes author and independent offline QA. The candidate remains staged and unselected. The running kernel is `7.1.6-1-1-ARCH`; no agent ran sudo, changed selected boot files or rebooted.

The [bounded JSON receipt](dev-147-fairydust-activation-preparation-2026-09-05.json) binds the checked code and private proof files. The [living plan](../plans/2026-09-05-dev147-paired-activation.md) owns execution status. The [handoff](../../dev/apple-dp-altmode/fairydust/boot-activate/README.md) gives the exact user-run activation and restore commands.

## Behavior

Activation verifies the frozen staged candidate, historical protected state, package guard and actual root/EFI mount identities. It saves original GRUB, the old EFI bundle and the recovery guide before selected-file writes. It installs a GRUB dispatcher while the old bundle remains active, then replaces the bundle with the verified candidate bytes. The dispatcher requires exactly one old/new bundle hash match before loading its paired kernel configuration.

Linux restore verifies the old dependencies and backups, restores the old bundle first, then restores original GRUB. It can recover without intact candidate files or unchanged unrelated EFI-variable/package metadata. It refuses damaged old support files or an existing package lock. A killed helper can leave a stale lock that needs manual assessment.

The [recovery guide](../../dev/apple-dp-altmode/fairydust/boot-activate/RECOVERY.md) provides a macOS route that restores the old bundle on the EFI partition by GPT UUID. After a full restart, the retained dispatcher selects the old kernel. This does not require macOS to write ext4. A GRUB console bypass is restricted to a fully restarted machine with the restored old bundle. Arbitrary ext4/GRUB damage is outside this recovery route.

## Checks

Both executions of `bash dev/apple-dp-altmode/fairydust/validate-activation.sh` exited 0. Author evidence is `checks/activation-gate.H3xj4U2r`; independent evidence is `checks/activation-gate.xMLQu9Tn`, under `/home/david/Work/dev147-fairydust-boot-20260905`.

| Check | Result |
|---|---|
| Full preparation and actual staging gates | PASS, chained in both activation runs |
| Activation/restore namespace controls | 22 PASS |
| Topology parsing/rejection controls | 4 PASS |
| Real GRUB disk-image runtime cases | 19 PASS |
| macOS shell guard cases under Linux | 14 PASS |
| Exact activation and restore bootstrap | Live read-only preflight PASS |
| Python formatting, Ruff, strict mypy; shell syntax | PASS |
| Installed GRUB dependencies | 37 module hashes match package and protected stage inventory |
| Independent source review | No remaining blocking finding |

The GRUB cases cover old, candidate and restored selection; missing commands; wrong identity; invalid, empty or missing inputs; returning configuration; and stale saved/next-entry state. Candidate instrumentation replaces Linux/initrd command names and timeout, with one pre-menu environment echo. It checks exact boot arguments and environment resets without executing Linux. The emulator has built-in modules; dynamic EFI module loading remains a separate source/inventory check.

An earlier gate correctly failed after recovery prose changed during execution. The guide, helper and launchers were repinned before both final PASS runs. The corrected shell blocks were unchanged by that prose edit.

## Limits and next step

Namespace tests substitute topology discovery and the expected prior-stage receipt identity. They first prove that the synthetic fixture fails with the production identity. Production has no fixture override. This is not an unmodified privileged bootstrap end-to-end run. The real helper must still recheck root-private live state before writing.

Tests inject selected-file replacement failures and source review checks preparation/flush ordering. They do not inject fsync faults, SIGKILL or physical power loss. Actual FAT publication and macOS/Recovery execution remain untested. Bundle hashing assumes the on-disk file does not change between m1n1 loading it and GRUB checking it; this is not an attestation of the in-memory device tree.

The focused handoff gate passed. The unrelated Omarchy suite limitations remain in the [boot preparation evidence](dev-147-fairydust-boot-preparation-2026-09-05.md). No candidate boot, USB4 completeness, display, audio, USB, charging or suspend success is claimed.

Next, David runs the activation launcher and returns its result path. Verify `ACTIVATED_NOT_REBOOTED` and selected-file identities before the attended candidate boot. Keep the recovery guide available in macOS. The plan retains hardware acceptance and the later coherent upstream USB4 integration as open work.

## Source basis

The private GRUB design receipt records source inspection, executable probes and the installed module inventory. Recovery commands use the [diskutil contract](https://keith.github.io/xcode-man-pages/diskutil.8.html), [plutil contract](https://keith.github.io/xcode-man-pages/plutil.1.html), [Apple startup and Recovery instructions](https://support.apple.com/en-lamr/guide/mac-help/mchl82829c17/26/mac/26) and [Apple checksum instructions](https://support.apple.com/en-qa/guide/business/axm8e397e77d/web). Mutable EFI-variable handling follows [U-Boot's EFI variable storage API](https://docs.u-boot.org/en/v2026.01/api/efi.html).
