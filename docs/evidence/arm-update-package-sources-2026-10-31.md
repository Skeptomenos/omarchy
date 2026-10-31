# ARM update package-source repair — 2026-10-31

## Scope and approval

David approved implementation and then proceeding with delivery after `omarchy update` failed on omarchy-air. The live dev-linked checkout was clean at `f8c5fca4d`. Development used the feature branch `fix/arm-hypr-package-source`; no live checkout files were edited directly and no privileged commands were run by the agent.

Tracker: [DEV-432](https://linear.app/helmus/issue/DEV-432/repair-arm-updater-package-sources-and-recovery-delivery).

## Findings and changes

- `pacman -Si omarchy/hyprtoolkit omarchy/hyprland-guiutils` reproduced both missing targets. Unqualified queries found both packages in `extra`.
- The shared ARM helper now explicitly selects `omarchy/hyprland`, `extra/hyprtoolkit`, and `extra/hyprland-guiutils`. Full-system transactions, signature checks, and explicit-target upgrade protection remain in place.
- Standalone recovery no longer sources a potentially stale installed helper. It uses its adjacent checkout helper or fetches from `Skeptomenos/omarchy` branch `quattro-arm`; failure to fetch stops recovery. Documented recovery script URLs use the same repository and branch.
- Real pacman selection tests reproduce the missing-package scenario with neither toolkit nor GUI utilities in the synthetic Omarchy repository. Conflict-retry and recovery tests cover the revised policy.

## Mirror diagnosis and user-run repair

`curl -ILsS` reproduced HTTP 403 from `http://de.mirror.archlinuxarm.org/aarch64/extra/extra.db`. Denmark and France returned HTTP 200. Denmark returned 200 for all four configured distribution databases: `core`, `extra`, `alarm`, and `aur`. A fresh download of Denmark's `extra.db` listed `hyprtoolkit` `0.6.0-1` and `hyprland-guiutils` `0.2.2-4` for aarch64. HTTPS probes of the German and generic mirror names failed hostname verification; TLS verification was not disabled.

The agent prepared `/tmp/opencode/omarchy-update-repair.sh` for David to run in his own terminal. It verifies Denmark's databases, moves the existing Denmark mirror entry first without removing other entries, takes a timestamped backup, installs the reordered mirror list with sudo, and invokes the normal `omarchy update` path. `bash -n` passed. A bubblewrap test with a disposable mirror directory and stubbed sudo, curl, and update commands verified ordering, backup preservation, fallback retention, and update dispatch. The script was not executed against the host.

The normal dev-linked updater performs `git pull --ff-only` before package updates, so publication to `origin/quattro-arm` delivers the corrected helper without a direct live edit.

## Verification and remaining limits

Focused package-source, real-pacman selection, recovery, and conflict tests passed: 50 checks across six test files. Recovery passed all ten checks, including the download-route assertions. Review found no blocking defects. The native contained channel transaction was skipped because the contained root runner was unavailable.

The final `./test/all` completed in a read-only filesystem sandbox with isolated `/tmp`, `/run`, and networking. CLI passed. Shell reported 333 passing and nine failing files out of 342; some passing files contained skips. The log is `/tmp/opencode/arm-update-final-qa.log`. Baseline replay used an archive of parent `f8c5fca4d`; its log is `/tmp/opencode/arm-update-baseline-qa.log`.

- Six unchanged recipe tests failed because `omarchy-pkgs` was absent or unversioned: `config-test.sh`, `network-package-test.sh`, `package-build-contract-test.sh`, `settings-package-units-test.sh`, `unowned-system-paths-test.sh`, and `zram-package-contract-test.sh`. All six reproduced at the parent.
- `network-profile-sequence-test.sh` could not open display `:0` in the isolated runtime sandbox. It reproduced at the parent.
- `network-sysctl-migration-test.sh` failed its apply-operation assertion under network isolation. It reproduced at the parent and passed separately on the host.
- Unchanged `locate-test.sh` encountered existing `bin/__pycache__/*.pyc` bytes in the worktree. It passed against both the clean parent archive and a clean archive of the final feature commit. Existing bytecode was not deleted.

David explicitly approved publication if final QA confirmed only unchanged environment-related failures. The results above satisfy that conditional waiver; the aggregate verdict remains FAIL, not a fully passing suite. Native contained package installation and live runtime acceptance remain unverified.

`bin/omarchy commands --check` passed for 488 commands. Shebang-selected syntax checks and `git diff --check` passed. `hyprctl configerrors`, `hyprctl reload`, and a second `hyprctl configerrors` completed successfully with no configuration errors.

Package installation, migrations, logout/login, and graphical runtime acceptance remain pending David's privileged update. Metadata resolution does not establish compositor runtime compatibility. No automatic package rollback is claimed. The mirror-only repair can be reversed by restoring its printed backup.

— drafted by David Helmus's agent
