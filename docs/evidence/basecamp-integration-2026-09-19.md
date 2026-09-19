# Basecamp integration, 2026-09-19

This record covers the local Basecamp merge candidate. The orchestrator owns release, deployment, and the combined-lane QA decision.

## Inputs

| Role | Commit |
| --- | --- |
| ARM release parent | `fea5a848dd1dcefe2d08cb1a3d3e827c0df70edb` |
| Approved Basecamp parent | `8675600e9ea0c6b6011de378b0625172b9cfdd46` |

The candidate uses branch `codex/sync-2026-09-19-basecamp` in `/home/david/Work/omarchy-sync-2026-09-19-basecamp`. The merge command was `git merge --no-ff --no-commit 8675600e9ea0c6b6011de378b0625172b9cfdd46`. It returned 1 with 32 conflict paths. All conflicts were resolved before staging.

The writer fetched `origin`, `upstream`, and `omarchy`. The ARM destination and Basecamp source still matched the approved commits. `/home/david/o-live` was clean on `quattro-arm`. `/home/david/o` had existing documentation changes. Neither checkout was edited. The separate Omarchy Mac candidate was not read.

## Conflict decisions

- Preserve the public ARM README, setup script, and `Skeptomenos/omarchy-mac` clone with `--branch quattro-arm --single-branch`.
- Retain ARM package-source preparation, explicit repository targets, package filtering, and channel transactions. Use the new `omarchy-update-pacman` wrapper in the shared update, refresh, reinstall, and final staged-channel transactions. The fresh installer supplies the checkout's command path for that transaction.
- Keep the ARM keyring path and apply Basecamp's fail-fast shell settings. The separate Omarchy Mac lane owns the new keyring import.
- Keep `wf-recorder`, combined audio, 48 kHz AAC, and the shared recorder process detector. Keep Basecamp's private recording state directory. Move the ARM PulseAudio module receipt into that same directory.
- Keep the fork's terminal presentation exit-status propagation and failure message.
- Keep ARM package removal choices. Add the upstream Cursor, Muse, and OpenClaw agent behavior, menus, and tests. Keep Hermes setup in its existing shared user leaf, with its preinstall opt-out and ownership checks.
- Upgrade the verified ARM mise pin to `2026.8.15` with SHA-256 `124ea8f7c8cb9a6a3c99c763cbf37ca48c9beaa816735f011d9fd99e6cd463e9`. An ARM-only migration upgrades existing binaries that lack the Cursor registry entry. It runs before the imported Cursor wrapper migration.
- Install OpenClaw through `omarchy/openclaw` on ARM. Query installed state with its plain package name. Include installed OpenClaw in explicit update targets, and preserve its removal. Remove Claude's exact ARM provider package, `claude-desktop-extra`, with the desktop app. New Claude, OpenClaw, and T3 installers stop if the package helper skips an unavailable package.
- Keep the ARM Node tarball selection and network fallback. Add upstream's `latest` setting after an offline bundled install. Remove automatic trust of project `bin` directories.
- Keep Wi-Fi auto-connect controls and their keyboard action index. Add captive-portal state and navigation.
- Keep the transactional factory-reset inventory, sanitized replacement baseline, boot rollback, and Asahi paths. Use Basecamp's fail-fast account scrub helper and remove subordinate-ID backup files. Do not modify the retained baseline in place. The account fixture follows this transaction and redirects its live-lock path into the fixture.
- Keep the lock-screen theme denylist and add the new color-only templates.
- Preserve historical migration tests, CLI coverage, and fork migration IDs. The retained locate migration is inert because Basecamp retired its helper. Its replacement service passes fixed indexing options without rewriting administrator configuration.
- Preserve Basecamp's authentication-service isolation, privileged-file ownership repairs, Kitty remote-control repair, upgrade root-PATH separation, VM password transport, and other cleanly merged changes.

The merge keeps Asahi hardware scripts, `fnmode=1`, keyboard brightness controls, the notch layout, and ARM install/package sources. The upstream kernel migration already excludes non-x86 hosts. The imported header repair now does too. Cam Link and Xbox controller setup on ARM requires headers for the running kernel before package or device changes. Missing relay packages leave the raw camera accessible.

## Migration IDs

The maximum source IDs were `1789316115` on the ARM parent and `1789444024` on Basecamp. The final candidate retains all 150 ARM migration paths. Nineteen imported migrations receive IDs above both maxima. Two equivalent Hermes migrations retain the original ARM IDs. The sequence preserves the relative order of new Basecamp work. New ARM migration `1789444027` upgrades mise before the Cursor migration. ID `1789444028` is unused.

| Basecamp ID | Imported ID | Effect |
| --- | --- | --- |
| 1786609204 | 1789444025 | Video wallpaper dependencies |
| 1787215483 | 1789444026 | Disable mise upgrade pruning |
| 1787760281 | 1787760281, retained | Hermes CLI setup |
| 1787843905 | 1787843905, retained | Hermes skill links |
| New ARM repair | 1789444027 | Verified mise upgrade for Cursor registry support |
| 1788577553 | 1789444029 | Cursor CLI wrapper |
| 1788595060 | 1789444030 | Brave Origin native messaging |
| 1788596255 | 1789444031 | vi package |
| 1788619462 | 1789444032 | Hermes Desktop skin |
| 1788662350 | 1789444033 | Privileged sleep-hook ownership repair |
| 1788724825 | 1789444034 | Muse wrapper |
| 1788745941 | 1789444035 | Kitty remote-control repair |
| 1788848726 | 1789444036 | Retire the known legacy icon font |
| 1788862626 | 1789444037 | Cam Link relay |
| 1788941927 | 1789444038 | Basecamp CLI wrapper |
| 1789091250 | 1789444039 | T3 Code theme |
| 1789095456 | 1789444040 | Remove automatic project-bin PATH trust |
| 1789130779 | 1789444041 | KEF USB sink suspend setting |
| 1789294350 | 1789444042 | BBR and fq defaults |
| 1789310715 | 1789444043 | Cloudflare CLI wrapper |
| 1789325478 | 1789444044 | x86 Omarchy kernel |
| 1789444024 | 1789444045 | x86 kernel headers |

The original ARM files `1787760281.sh` and `1787843905.sh` remain byte-for-byte unchanged, including their modes. Read-only inspection found both live completion markers. There are no duplicate imports of those effects. This preserves user changes made after the original migrations. The earlier draft allocated duplicate IDs with marker guards. The orchestrator relayed the assessor's equivalence finding, which replaced that draft before commit. This attribution was corrected on 2026-09-19.

The system-sleep repair keeps its existing root quarantine and retry-marker names. The x86 kernel migration keeps its machine completion marker. Those names identify prior machine-wide work and prevent a new per-user filename from repeating it. Test references to imported files use the new IDs. Historical-marker tests retain their original marker names deliberately.

## Verification

Focused tests ran in Bubblewrap with a read-only host filesystem, private home, private `/run`, isolated processes and network, and writable scratch space. The real `sudo` and `pkexec` executables were replaced by `false` inside the sandbox. No live migration or installer ran.

Command records and actual exit statuses are in `/tmp/opencode/basecamp-2026-09-19-commands.log`. Each focused test also has `/tmp/opencode/basecamp-<test-name>.log`. The local runner is `/tmp/opencode/basecamp-focused.py`.

The focused package, channel, Hermes, agent, menu, network, recording, theme, update, kernel, DKMS, and factory-reset tests passed. Security repair fixtures passed for Kitty, project PATH trust, system-sleep ownership, and legacy font retirement. CLI, retained historical migrations, systemd, provisioning, preinstall removal, and Hyprland binding-conflict checks also passed.

- `arm-dkms-gates-test.sh` proves the architecture and missing-dependency gates.
- `arm-ai-packages-test.sh` proves qualified OpenClaw installation, plain-name installed queries, repeat-run behavior, and installer failure after skipped packages.
- `arm-package-transaction-test.sh` uses real pacman against synthetic databases. It proves OpenClaw stays on its explicit source while installed and stays removed afterward.
- `aarch64-mise-migration-test.sh` covers an old Cursor-less registry, checksum rejection, the upgrade, repeated runs, and the x86 no-op.
- `arm-channel-apply-test.sh` runs the prepared transaction and real wrapper with mocked system commands. Success, package failure, and hook failure pass both with and without a systemd boot marker. It checks the frozen config path, exact targets, locale, update authorization, and final configuration state.
- `update-pacman-test.sh`, `update-file-conflict-test.sh`, and `update-package-conflict-test.sh` also pass with the systemd scope branch selected and its execution mocked.
- `config-test.sh` returned 0 with `OMARCHY_PKGS_PATH=/tmp/opencode/omarchy-pkgs-pinned-20260919`, verified at recipe commit `19ef4b560ffd6f26df67665400394278065cf437`.
- The downloaded mise binary matched the ARM asset digest in the [v2026.8.15 release](https://github.com/jdx/mise/releases/tag/v2026.8.15). In an isolated offline home it returned `2026.8.15 linux-arm64` and resolved `mise registry cursor-agent` to `http:cursor-agent`, both with exit 0.

Initial fixture failures were corrected by exposing the real update wrapper to the ARM reinstaller test, mocking package metadata queries in kernel tests, and resolving mise from its actual executable directory. The corresponding reruns returned 0.

- `bin/omarchy commands --check` returned 0: 488 commands.
- `python3 /tmp/opencode/basecamp-syntax.py` returned 0: 1,109 Bash and Python parser checks, zero failures. Per-file statuses are in `/tmp/opencode/basecamp-syntax.log`.
- `python3 /tmp/opencode/basecamp-final-check.py` returned 0. It checked the exact parents, retained migration paths, new IDs and modes, original Hermes bytes and modes, unchanged upstream migration contents except the header guard, and the downloaded mise binary.
- `git diff --cached --check` returned 0.
- `git diff --name-only --diff-filter=U` returned 0 with no paths.

## Remaining gates

The initial config failure was an input-path failure and is resolved by the pinned recipe checkout above. The contained native ARM channel transaction test skipped because it requires its dedicated root and disk-backed test runner. The prepared-transaction fixture does not replace that native test. Captive-portal and authentication-boundary static checks passed; their runtime checks skipped without a compositor. Full-suite QA and review remain required after the finalized Omarchy Mac lane is merged into this candidate.

The orchestrator owns the enabled personal-plugin compatibility work, graphical and hardware acceptance, and delivery of the qualified `omarchy` and `omarchy-settings` package pair. A source fast-forward alone does not install the new fixed-path Kitty defaults, tmpfiles rule, udev rule, sysctl defaults, or font. This lane made no live configuration, package, plugin, deployment, or privileged changes.

## Fixture follow-up, 2026-09-19

Independent QA on `790ceaccc0c786c2c56d5834d8d3fdd7d08d7133` found two fixture defects. This follow-up starts from assembled commit `65e259cad1525cde379fd27280633ec656c4887a`. The QA report is `/tmp/opencode/omarchy-sync-20260919-basecamp-qa/SUMMARY.md`.

- The sleep-hook test selected the first quarantined symlink, which could belong to an earlier case. It now selects the current case's target and retains the existing content and target assertions.
- The optional wf-recorder test reached the host's mise and an unmocked download. Its conditional subshell suppressed `errexit`, so it reported success after the bootstrap failed. It now supplies a mise fixture for both `--version` and `registry cursor-agent`, rejects downloads and elevation, and runs in a separate Bash process with `errexit` enabled.
- The new failure case runs the unchanged production `main` and package-install function bodies with the real mise helper. Other upgrade steps are mocked. A refused download returns status 1 through that chain, stops before `wire_system_paths`, and never reports upgrade completion. The swallowed failure was limited to the former conditional test context. No production failure-handling change was needed.

`python3 /tmp/opencode/basecamp-fixture-check.py before system-sleep-ownership-migration upgrade-to-quattro-mac` reproduced both defects. The sleep test exited 1. The upgrade test exited 0 despite an unexpected curl call, which made the runner fail. The matching `after` command returned 0 for both complete test files, including all sleep cases after the former failure. No external download or elevation guard was reached after the correction.

The tests ran with disk-backed scratch bound at `/tmp`, `/usr/local/bin` on PATH, a private home and runtime, and isolated network and process namespaces. Logs are in `/tmp/opencode/basecamp-fixture-followup-20260919/`. The command and exit-status record remains `/tmp/opencode/basecamp-2026-09-19-commands.log`. Full assembled-candidate QA remains a separate gate.

## Package-source follow-up, 2026-09-19

Independent review of `790ceac` found that Perplexity and the Cam Link relay lacked explicit ARM source selection. With `Usage = Sync`, a bare `pacman -Si` lookup succeeds, but a bare install cannot select either package. Installed copies also lacked explicit update targets. The review is `/tmp/opencode/omarchy-sync-20260919/basecamp-review-790ceac-2026-09-19.md`, finding B1.

This correction follows fixture commit `2cad97e04`. The package helper now maps `perplexity` and `v4l2-relayd` to `omarchy/<package>` on ARM, like OpenClaw. The shared update policy includes each package only while installed. `Usage = Sync`, signature policy, and intentionally removed packages remain preserved.

The extended `arm-package-transaction-test.sh` failed before the source fix because installed optional packages lost their explicit source. After the fix, real pacman against disposable databases proves all of these outcomes for OpenClaw, Perplexity, and `v4l2-relayd`:

- Explicit selection survives unchanged versions, upgrades, and downgrades while ordinary packages still update.
- Removed packages stay removed.
- Bare metadata lookup succeeds but bare install resolution fails in the Sync-only repository.
- The real package helper selects the qualified source for a fresh install, passes its installed-state check, and skips a second transaction on repeat invocation. Its transaction shim uses pacman's print-only resolver and records only fixture metadata. It does not install packages on the host.

`python3 /tmp/opencode/basecamp-fixture-check.py package-after arm-package-transaction arm-package-sources arm-ai-packages arm-dkms-gates update-package-conflict` returned 0 for all five files. No external guards were reached. The `package-before` and `package-after` logs are in `/tmp/opencode/basecamp-fixture-followup-20260919/`.

`bin/omarchy commands --check` passed for 488 commands. `python3 /tmp/opencode/basecamp-syntax.py` passed all 1,116 Bash and Python parser checks on the assembled tree. Full-suite QA and the separate host plugin changes remain with the orchestrator.

## Elsewhen candidate addendum, 2026-09-19

The orchestrator approved an isolated feature candidate from released ARM commit `dd25a66d988d3c53b101aa22a40b3830c0346045`, with exact Basecamp merge source `60663faf8764253646f1d6166e864b608d4a0fa1`. The branch is `codex/sync-2026-09-19-elsewhen` in `/home/david/Work/omarchy-sync-2026-09-19-elsewhen`. Release qualification remains separate. Basecamp PR 12157 includes regression tests, but the orchestrator found no published GitHub CI checks for its merge.

`git merge --no-ff --no-commit 60663faf8764253646f1d6166e864b608d4a0fa1` returned 1 with one conflict in `test/shell.d/config-test.sh`. The resolution checks Elsewhen immediately before the clock on the ARM right-side bar. The empty center and clock date format remain intact.

The migration maxima were ARM `1789444045` and Basecamp `1789581661`. The imported migration is `1789581662.sh`. All 171 migration paths from the ARM parent retain their contents and modes. The candidate adds no duplicate migration under the upstream ID.

### Package source and failure handling

The host's `pacman -Si elsewhen` returned 1. The package agent then fetched the actual remote databases into `/tmp/opencode/omarchy-sync-20260919/elsewhen-package/repository-databases/`. Its `availability.json` records the observation at `2026-09-19T10:10:24.084377+00:00`.

The writer independently checked the saved `https://pkgs.omarchy.org/edge/aarch64/omarchy.db` bytes against SHA-256 `991d64e4a65f7062676b4939a2b3a98cc8148073855210348c251774e3df1930` and extracted `elsewhen-1.0.0-1/desc`. The entry names `elsewhen-1.0.0-1-any.pkg.tar.zst`, with package SHA-256 `49f1a692b979487cb3adec0b0b063fbade56a6522776d7292e2b0872eeb75e01`. This confirms the configured upstream ARM repository contains the package. The decision does not depend on an installed copy or an x86 repository entry.

The candidate maps Elsewhen to `omarchy/elsewhen` in both the package helper and the fresh-install default loop. Explicit updates include Elsewhen only while it is installed. The existing `Usage = Sync`, signature policy, repository lanes, and other package targets retain their behavior.

The original migration could complete after the ARM helper skipped an unavailable package with status 0. The new migration checks the installed package and its packaged manifest before it creates a link or sends shell IPC. A missing package or payload now fails the migration and leaves its completion marker absent. Existing plugin checkouts and symlinks retain their contents and targets. The migration uses the upstream preserving `bar put` operation and leaves the shell restart to the update flow.

### Focused verification

The runner `/tmp/opencode/elsewhen-check.py` uses Bubblewrap with a read-only host, a private home and `/run`, isolated processes and network, and disk-backed scratch mounted at `/tmp`. The PATH includes `/usr/local/bin`. The package recipes stay at exact pin `19ef4b560ffd6f26df67665400394278065cf437`, without a custom-recipe override. No external guard fired. The command log is `/tmp/opencode/elsewhen-20260919-commands.log`; per-test logs are in `/tmp/opencode/elsewhen-20260919/`.

| Command or log prefix | Result |
| --- | --- |
| `elsewhen-check.py upstream elsewhen-default-migration config settings-package-units` | All three files returned 0 before ARM hardening. |
| `elsewhen-check.py guard-before elsewhen-default-migration` | Returned 1 and reproduced false completion after an unavailable ARM package. |
| `elsewhen-check.py guard-after elsewhen-default-migration config settings-package-units arm-package-sources arm-package-transaction arm-ai-packages migrate bar bar-notch` | Eight existing files returned 0. The nonexistent `migrate-test.sh` returned 127, a runner selection error. |
| `elsewhen-check.py migration-gates migrate-wrapper migrate-scope` | Both correct migration-runner files returned 0. |
| `elsewhen-check.py mapping-before arm-package-sources arm-package-transaction` | Both files returned 1 and reproduced the unqualified fresh-install target and wrong update source. |
| `elsewhen-check.py mapping-after arm-package-sources arm-package-transaction arm-ai-packages elsewhen-default-migration arm-channel-apply` | All five files returned 0. |
| `elsewhen-check.py final-cli cli package-build-contract` | Both files returned 0. The build-contract test intentionally exercises custom-recipe warnings in its negative and opt-in cases. |
| `elsewhen-check.py final-migration elsewhen-default-migration` | Returned 0 after the final fixture style corrections. |
| `bin/omarchy commands --check` | Returned 0 for 488 commands. |
| Parser-aware Bash and Python checks | All 1,119 checks returned 0. The runner reused `/tmp/opencode/basecamp-syntax.py` with its output redirected to `/tmp/opencode/elsewhen-20260919/syntax.log`. |

The real-pacman fixture covers fresh qualified installation, installed-state checks, repeat installation, unchanged versions, upgrades, downgrades, and deliberate removal of Elsewhen. The real migration runner proves package and payload failures cannot write a completion marker. It also covers scan and placement failures, successful completion, and skipping a completed migration. Shell IPC responses are stubbed. The custom-config assertion proves the migration does not directly rewrite a custom bar, clock anchor, existing placement, or plugin settings; it is not runtime UI qualification.

The settings-package fixture executes the pinned stable and development recipes for both architectures. It checks the Elsewhen link under `/etc/skel/.config` and `/usr/share/omarchy/config`, including staging when the absolute package target does not exist on the host.

`git diff --cached --check` returned 0. The index audit confirmed the exact merge parents, all 171 preserved ARM migration blobs and modes, the single new migration with mode `0644`, and no unresolved conflicts.

Independent full-suite QA, review, package delivery, and graphical acceptance remain with the orchestrator. No privileged command, dev-status call, live change, push, or release occurred in this feature worktree.

### Tracked-symlink QA correction, 2026-09-19

The orchestrator reported that full QA on `b88c99316aa4e051cc91e9c432abe6e7ed47130a` failed only `tracked-symlinks-test.sh`. The other 338 files, independent source review, and package QA passed. The writer reproduced the failure with `elsewhen-check.py symlink-before tracked-symlinks`, which returned 1.

The test now recognizes exactly `config/omarchy/plugins/omacom.elsewhen` with target `/usr/share/omarchy/plugins/omacom.elsewhen`. This upstream user default points to the installed Elsewhen package, not a source-checkout file. The exception also requires `elsewhen` in `install/omarchy-base.packages`. The existing package-staging test checks this link in both package seed locations. Every other tracked link retains the relative-target, shell-expansion, repository-boundary, and target-existence checks. Production files and the absolute default link are unchanged.

The retained test uses a disposable Git repository and indexed symlink mutations. It accepts the legitimate package link and an ordinary relative link. It rejects a wrong Elsewhen target, the correct absolute target at another tracked path, a missing package default, an escaping relative target, a dangling relative target, and a target that needs shell expansion.

`python3 /tmp/opencode/elsewhen-check.py symlink-after tracked-symlinks config settings-package-units` returned 0 for all three files. The package fixture used exact recipe pin `19ef4b560ffd6f26df67665400394278065cf437`. No external guard fired. `bash -n test/shell.d/tracked-symlinks-test.sh` and `git diff --check` both returned 0. Logs use the `symlink-before` and `symlink-after` prefixes in `/tmp/opencode/elsewhen-20260919/`. The orchestrator owns full-QA round two and retargeting the package build and apply script to the follow-up commit.
