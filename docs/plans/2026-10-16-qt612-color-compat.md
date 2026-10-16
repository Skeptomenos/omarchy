# Restore shell rendering with Qt 6.12

Goal: restore launcher labels, cards, borders, and shared desktop colors after the Qt 6.12 package update.

Scope: targeted backport of [upstream's namespace fix](https://github.com/omacom/omarchy/commit/b83d3df0840504299d3099ebf391eb8110527edd), adapted to this fork, plus staged plugin patches. On October 16, David explicitly approved deployment, the staged plugin edits, one controlled shell restart, and a repair-only waiver of the eight unchanged baseline failures.

Source: branch `fix/qt612-color-compat` in `/home/david/o/.worktrees/qt612-color-compat`, based on live commit `50dd610bc`. Never edit `/home/david/o-live` or `/usr/share/omarchy`.

## Next increments

- [x] Add a native QML regression that fails against the unchanged source.
- [x] Qualify the shell palette references without changing the singleton API.
- [x] Stage plugin patches against the actual installed QML, preserving local work.
- [x] Complete independent code review, including the corrected plugin assertions.
- [x] Complete independent full-suite QA. Targeted checks pass. The full gate fails on eight unchanged baseline failures.
- [x] Obtain approval for deployment and the repair-only baseline-test waiver.
- [x] Deploy, restart the shell once, and verify the real launcher and bar. David confirmed both are restored.
- [ ] Check persistence after David reboots. Broader panel and third-party plugin behavior remains outside the completed visual checks.

## Progress (LIVING)

The candidate qualifies 263 palette references across 55 production QML files. It includes internal `Border.qml` and `Style.qml` references and the fork's keyboard panel. Existing unqualified imports remain available for `Style`, `Border`, and `Util`.

The staged plugin bundle is `/home/david/o/.worktrees/qt612-plugin-stage/bundle-v2/`. It contains before and after snapshots of 104 QML files across 22 plugins and three affected test files, a unified `plugins.patch`, and a manifest with source and result SHA256 hashes. The generator is `../stage.py` relative to the bundle. The older `bundle/` is superseded and must not be applied. No installed plugin was edited. Some plugins contain pre-existing local changes. Those changes are included in the snapshots, not discarded.

Plugin patch SHA256: `a695c58d001d19621bab71e936d66c59691f6f7a9af08a66f71e42b80b54dc35`.

Checks performed so far:

- `bash test/shell.d/color-namespace-test.sh` failed before the fix and passed afterward. It tests the real Commons and UI modules, literal colors, singleton identity, internal lookups, bindings, and `Connections` updates. It uses isolated state and the offscreen backend, not desktop services.
- `./test/cli` passed before and after the fix with desktop environment variables unset.
- `./test/shell` reported the same eight failing test files before and after. The candidate adds one passing test. No baseline failure is waived.
- Focused bar, border-geometry, and network-profile tests passed. Command metadata and the standard command syntax checks passed.
- `git apply --check` accepted the final plugin patch against the installed source. The 107 installed source and test file hashes still matched their snapshots.
- `qmlformat --ignore-settings`, without in-place writes, parsed all 104 plugin files before and after. No syntax failures occurred. Results are in the superseded bundle's `parse-results.json`. All 104 QML snapshots are byte-identical between bundles.
- `python3 /home/david/o/.worktrees/qt612-plugin-stage/check-tests.py /home/david/o/.worktrees/qt612-plugin-stage/bundle-v2` ran the three affected plugin test files in isolated copies. All passed before the repair, failed with QML-only changes, and passed with the six corrected assertions. Results are in `bundle-v2/test-results.json`.

SWE logs: `/tmp/opencode/qt612-color-compat-evidence/`. Baseline suite logs: `/tmp/opencode/qt612-color-compat-baseline-cli.log` and `/tmp/opencode/qt612-color-compat-baseline-shell.log`. Independent QA evidence: `/tmp/opencode/qt612-independent-qa/`.

Independent review passed the staged source and final plugin bundle. It confirmed namespace-only QML changes and exactly six positive test-assertion changes. Its scoped Omamail security review found no changes to mail, credential, network, HTML, or process behavior.

Independent QA is complete. `env -u WAYLAND_DISPLAY -u HYPRLAND_INSTANCE_SIGNATURE QT_QPA_PLATFORMTHEME=basic ./test/all` exited 1. CLI passed. Eight of 342 shell test files failed, with no new failures and all eight normalized failure blocks identical to baseline. Evidence is in `/tmp/opencode/qt612-independent-qa/{all.log,all.exit,failure-comparison.json}`. Independent bundle-v2 replay, patch application, hashes, and the three affected plugin test files also passed. Production Quickshell remained PID 2968, with no probe processes left. David explicitly waived these eight unchanged failures for this repair only. The raw suite result remains FAIL.

The source repair and final plugin bundle are deployed. The running shell was restarted once. David confirmed the restored bar and app launcher, and the inspected screenshot shows the theme colors, labels, card, border, and selection highlight. Read [the deployment evidence](../evidence/qt612-color-deployment-2026-10-16.md) for commands, backups, and acceptance limits. Not every third-party plugin was tested end to end. No reboot has occurred.

The eight recorded baseline failures are `arm-channel-staging-test.sh`, `config-test.sh`, `locate-test.sh`, `network-package-test.sh`, `package-build-contract-test.sh`, `settings-package-units-test.sh`, `unowned-system-paths-test.sh`, and `zram-package-contract-test.sh`. They concern missing package recipes, the disk-backed-cache requirement, and Python bytecode read as UTF-8. Independent QA reproduced these conditions on the baseline. `locate-test.sh` passes in a clean archive and fails after bytecode caches exist.

## Deployment boundary and recovery

Before any approved apply, confirm the live checkout still matches the release base and every installed plugin file matches its manifest hash. If either has changed, regenerate and re-review the affected patch. Do not overwrite newer work.

During an approved deployment, prevent plugin hot-reload churn while applying the staged batch. Preserve the before snapshots for recovery, then start the shell once. Do not issue repeated IPC reloads into a failing shell.

Recovery must undo only this repair. The plugin snapshots preserve each file's pre-repair bytes, including existing local modifications. Restoring a snapshot requires confirming that no newer change would be lost. Live source recovery follows the release procedure rather than a reset of the running checkout.

## Decision log (LIVING)

- 2026-10-16: use namespace qualification rather than renaming the palette or downgrading Qt. Upstream already uses this approach, and it preserves the existing singleton export.
- 2026-10-16: stage plugin changes outside `~/.config`. Their QML import scopes require separate fixes, but installed edits would hot-reload the running shell and exceed the current approval.
- 2026-10-16: independent review found six source-text assertions that would fail after a QML-only plugin repair. Stage exactly those six assertion updates in three files. Preserve unrelated test guards.
- 2026-10-16: QA found no new failures. Recommend a repair-scoped waiver of the eight unchanged baseline failures rather than unrelated changes in this QML-only patch. Deployment and one controlled shell restart still require approval. Rebooting does not apply the staged repair. Verify the live desktop after deployment before using a reboot to test persistence.
- 2026-10-16: David approved the proposed deployment, shell restart, and repair-scoped waiver. Recheck source and plugin hashes before release. Live visual acceptance remains required.
- 2026-10-16: deployed source `2d7be42d8` through `origin/quattro-arm` and applied the reviewed plugin bundle with before and after hash checks. Preserved backups in the user's Omarchy state directory. The controlled shell restart succeeded, the bar and launcher are visually restored, and David confirmed the result. A reboot is now the persistence check, not the mechanism that applies this repair.
- 2026-10-16: a new Personal Linear issue could not be created because the workspace has reached its issue limit. The implementation and pending-QA handoff is recorded in [DEV-131](https://linear.app/helmus/issue/DEV-131/bug-reports#comment-e35d2f79) instead.

— drafted by David Helmus's agent
