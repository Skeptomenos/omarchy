# Qt 6.12 rendering repair deployment, 2026-10-16

David approved deployment, one controlled shell restart, and a repair-only waiver of eight unchanged baseline test failures. He subsequently confirmed that the menu bar and app launcher were restored and supplied a screenshot showing the launcher icons, labels, bordered card, and selection highlight.

## Applied changes

- Source commit `2d7be42d8`, pushed to `origin/quattro-arm` and applied to `/home/david/o-live` by fast-forward from `50dd610bc`.
- Reviewed plugin bundle `bundle-v2` from `/home/david/o/.worktrees/qt612-plugin-stage/`. It updates 104 QML files across 22 plugins and six assertions in three test files.
- Patch SHA256: `a695c58d001d19621bab71e936d66c59691f6f7a9af08a66f71e42b80b54dc35`.
- Verified all 59 tested source and test hashes before committing. Verified all 107 installed plugin file hashes and modes before application, then verified all 107 result hashes and modes afterward. Existing local plugin work was preserved.

The deployment script is `/tmp/opencode/deploy-qt612-color.sh`. Persistent backups are `/home/david/.local/state/omarchy/repairs/qt612-color-2026-10-16/`. The backup contains before and after snapshots, the patch, manifest, source commit IDs, and restart timestamp. Recovery must preserve any work done after this deployment and must not reset the live checkout.

## Application and verification

The deployment refused a locked session and required a clean live checkout and matching plugin hashes. It stopped only the original Omarchy launcher PID 2954 and its child PID 2968. The launcher forwarded TERM and both exited before source and plugin application. The separate Voxtype Quickshell process was not stopped. `omarchy restart shell` then started one replacement launcher and shell, with shell PID 618656. No IPC-driven restart or plugin hot-reload batch was used.

| Command or check | Result |
|---|---|
| `bash test/shell.d/color-namespace-test.sh` immediately before release | PASS |
| `git push origin HEAD:refs/heads/quattro-arm` | Fast-forward push succeeded |
| `bash /tmp/opencode/deploy-qt612-color.sh` | Exit 0, live source and all plugin result hashes matched |
| `omarchy shell shell ping` | `ok` |
| `hyprctl reload` | `ok` |
| `hyprctl configerrors` | Empty |
| `systemctl --failed --no-pager` | Zero failed units |
| `systemctl --user --failed --no-pager` | Zero failed units |
| Post-restart journal search for palette errors and crash indicators | Zero matches in the captured log |
| `hyprctl -j binds` | SUPER+SPACE has the `App launcher` binding |
| Real launcher screenshot and David's confirmation | Bar and launcher restored |

Visual evidence inspected: `/home/david/Pictures/screenshot-2026-10-16_23-05-51.png`. It shows readable launcher labels, the theme-colored card and border, selection highlight, and restored bar. David's subsequent screenshot also shows the application icons. The post-restart journal snapshot is `/tmp/opencode/qt612-live-after-deploy.log`.

## Limits

The aggregate suite's raw result remains FAIL. David waived only the eight unchanged baseline failures for this repair. Native and affected-plugin checks passed, and independent review passed the source and staged plugin repair.

The shell still emits unrelated plugin warnings, including a next-event integer assignment, Omaconnect null lookups, and a startup burst of duplicate IPC targets. These are not claimed fixed. The captured log contains no recurrence of the palette failure or crash indicators.

Cua could not capture the layer-shell desktop through its current X11 backend. No keyboard injection or Cua configuration change was attempted. The compositor binding and launcher route were checked, but this record does not claim an automated physical CMD+SPACE test. A panel summon returned `ok`, but the screenshot did not show the panel, so panel visual acceptance is not claimed. Not every third-party plugin was exercised end to end, and the selected theme was not changed during acceptance.

No reboot was performed. The deployed QML and plugin files persist across reboot. The next boot remains the test of post-login persistence and any separate boot symptom. This repair does not establish that every boot problem is resolved.

— drafted by David Helmus's agent
