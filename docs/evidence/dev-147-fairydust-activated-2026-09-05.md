# Fairydust activated, awaiting reboot — 2026-09-05

David ran the reviewed activation launcher. It exited 0 with empty stderr and status `ACTIVATED_NOT_REBOOTED`. The selected pair is prepared for `7.1.12-dev147-fairydust1`; the running release remains `7.1.6-1-1-ARCH`. No reboot or hardware test occurred.

The saved result directory is `/home/david/Work/dev147-fairydust-boot-20260905/activation/activate-results.iUG81ebY`. Its `result.json` SHA-256 is `a004059958c11531a74625a8de04e458b8783a02bb2b0a0ef53d05be7a5468b5`. The launcher's helper and topology identities match the [reviewed preparation evidence](dev-147-fairydust-activation-preparation-2026-09-05.json).

## Verified result

| Input | SHA-256 / result | Evidence boundary |
|---|---|---|
| Active EFI bundle | `1ae29a2bfadb309562c205520d8c28e2a8df2283bc88bbfb52474e54333c3dff` | Direct live read |
| Old recovery bundle | `203ab7027536c8d16f373d02c1f6346a5c34cfe095a9dafd0cfe37d2b354090c` | Direct live read |
| Copied recovery guide | `cd96a4d02ef1e9ac728a604a2ab377794b4bc5f944bd133cd11cae40b401178c` | Direct live read |
| Package guard | `469820ad7cfd015a22cff979b0aa70d62e82dcc7cc05951dca92f40cd660f2bd` | Direct live read |
| Selected GRUB dispatcher | `58fd5692f3e28013ce54df8de255c552117c1786a7d027e2da21b7fc8a63a9d2` | Privileged helper final check and receipt |
| Historical original inputs | All captured original inputs checked | Privileged helper and receipt |
| Preserved activation-time inputs | 533 unchanged | Privileged helper before/after check |
| Package lock | Absent after completion | Direct live check |
| Omarchy dev link | Still `/home/david/o-live` | `omarchy dev status` |

The 533 activation-time preservation entries are a narrower inventory than the earlier stage's historical inventory. These counts are not interchangeable. The helper checks historical original inputs separately before activation. Current GRUB, support files and root-side backup/receipt files are root-private. The unprivileged verification does not claim a second direct read of them.

The command `sha256sum` verifies the four readable live inputs above. `uname -r` returns the old release. The activation receipt records the new pair only after hashing both selected files and checking preserved state. No agent used sudo.

Independent read-only QA repeats the receipt and live-pin checks with PASS. A fresh topology check also returns the recorded root and EFI device identities. All 13 frozen executable/payload inputs still match the completed offline gate. `git diff --check` exits 0. No pre-activation gate was rerun.

## Next acceptance step

Keep the [recovery guide](../../dev/apple-dp-altmode/fairydust/boot-activate/RECOVERY.md) accessible from macOS. Save work, restart normally, and select Linux. Run `uname -r` after login; expected output is `7.1.12-dev147-fairydust1`. Return that result before cable/reconnect or suspend testing. If Linux cannot boot, use the recovery guide to restore the old bundle before selecting the old kernel.

Do not rerun the activation launcher or pre-activation gates against the changed selected state. The [living plan](../plans/2026-09-05-dev147-paired-activation.md) tracks attended boot, SIO/firmware checks, display, USB, audio, charging and later suspend/USB4 work. Activation success does not establish hardware support or physical power-loss recovery.
