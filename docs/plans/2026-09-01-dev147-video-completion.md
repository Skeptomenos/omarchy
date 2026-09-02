# Complete M2 external DisplayPort support

**Goal:** Install reversible, opt-in external DisplayPort support for the M2 MacBook Air from the known-good W configuration, with repeatable video acceptance on both tested LG monitors.
**Mode:** full
**Research branch:** `codex/dev-147-t1-image-offline`
**Integration branch:** `codex/dev-147-m2-displayport-opt-in`
**Linear:** `DEV-147`
**Started:** 2026-09-01
**Reconciled:** 2026-09-02

---

## Context

The preserved `/boot/initramfs-linux-asahi-dpalt.img` image, called W, has produced native external video on an LG 27UN83A-W and an LG 35 ultrawide while the internal display stayed usable. One controlled hot reconnect restored video in about ten seconds. W uses the packaged AppleDRM driver, the patched TIPD core, and the active M2/J413 device-tree prototype. These results establish a working prototype, not a repeatable installation or reliability guarantee.

The earlier [prototype plan](dev-147-m2-displayport.md) retains the complete investigation and is superseded for active execution by this plan. Monitor downstream USB-data loss is separate from video. [DEV-163](https://linear.app/helmus/issue/DEV-163/lg-monitor-usb-hub-disappears-while-displayport-video-remains-active) and the [USB PM plan](2026-08-31-dev147-usb-pm-recurrence.md) own that follow-up. USB hub enumeration, a mouse through the monitor, and USB control-transfer tracing do not block DEV-147.

The saved boot default remains unchanged. A manual GRUB edit selects W for one boot. The active prototype DTB is not removed by an ordinary reboot. Kernel updates can invalidate the patched module, DTB, and image as a matched set. The format-1 rollback and format-2 activation paths have passed once. The accepted format-2 rollback remains prepared but has not been invoked.

Repeated external link generations expose a second reliability limit. Endpoint `0x28` stores at most 16 AFK services. The current allocator never reuses disabled entries, so eight two-service display generations can exhaust the table and leave a detected monitor blank until reboot. [AFK service-slot exhaustion](../evidence/dev-147-afk-service-exhaustion-2026-09-02.md) owns the failed-boot and recovery evidence.

## Approach

First, run one compact attended video matrix against the exact W image. Keep MagSafe connected and keep the monitor USB ports empty so video is the only acceptance target. Then design the smallest M2/J413-specific fork integration that reproduces the accepted bytes, refuses kernel drift, preserves stock files, and has an explicit uninstall and rollback path. Stage it as a non-default option before any release decision.

The first local release can remain experimental if suspend/resume is a documented limitation. Attached startup, attach after startup, one hot reconnect, both tested monitors, internal-display safety, and system responsiveness are mandatory.

## Execution Protocol

Execution uses the full `self-correction-loop`. Work on one slice at a time. Run the complete slice gate before a checkbox changes. Record every manual result with the exact boot image, physical setup, observed time to image, both display states, system responsiveness, and recovery action. Stop after the same failure twice or three fix cycles in one slice.

## Steps

- [x] Slice 1: complete the compact W video acceptance matrix.
  Goal: establish whether the known-good prototype is reliable enough to package as an opt-in M2 feature.
  Probe first:
  - Record the current boot, loaded module identities, active DTB status, DRM state, power state, kernel/package versions, W metadata, and saved rollback assets before the first physical action.
  Implementation:
  - [x] Case A: boot exact W with one known-good monitor attached to the lower/front left USB-C port. Evidence: [identified W/LG27 startup](../evidence/dev-147-w-lg27-startup-2026-08-31.md) records David's exact W line, both physical images, responsive Linux, and 4K at 59.997 Hz.
  - [x] Case B: boot exact W without a monitor, then attach the monitor after login. Evidence: [W attach-after-login](../evidence/dev-147-w-attach-after-login-2026-09-01.md) records exact W user provenance, healthy internal-only startup, later LG27 4K60, both physical images, responsive Linux, and the temporary `disablehooks=encrypt` qualification.
  - [x] Case C: on the working boot, disconnect once, wait five seconds, reconnect once, and allow up to 15 seconds for video. Evidence: [LG27 reconnect](../evidence/dev-147-lg27-reconnect-usb-loss-2026-08-31.md) records David's five-second disconnect and external-image return after about ten seconds on the same identified W boot.
  - [x] Case D: verify the second tested LG monitor at its native mode. Evidence: [W/LG35 attached startup](../evidence/dev-147-w-lg35-startup-2026-09-01.md) records exact W user provenance, both physical images, responsive Linux, and LG35 at 3440×1440/99.982 Hz. The coordinated reboot superseded the planned live switch; Case C already supplies the required hot-reconnect result.
  - [x] Case E: suspend and resume once, last. Result: FAIL with safe recovery after external cable removal. Evidence: [W suspend/resume failure](../evidence/dev-147-w-suspend-resume-failure-2026-09-01.md) records failed external link preparation and modeset, an unusable internal lock screen until recovery, and the resulting opt-in-only limitation. Do not repeat.
  Validation:
  - Each mandatory case records an external image, a healthy internal display, responsive Linux, and a native advertised external mode.
  - Capture bounded kernel, DRM, compositor, Type-C, and power state after each case without reading partner `usb_mode`.
  Exit criteria:
  - Cases A through D pass without driver replacement, live module swap, boot-file mutation, or repeated recovery.
  - Case E has one recorded result. A recoverable failure becomes an explicit experimental limitation and blocks default-on release, but it does not block opt-in packaging.
  Assumption: W remains compatible with installed kernel `7.1.6-1-1-ARCH` and the current active prototype DTB.
  Verify: compare the running kernel, package version, loaded TIPD and AppleDRM build IDs, DTB status, W metadata, and retained recovery-file metadata before release of the first reboot.
- [x] Slice 2: design and test reversible M2/J413 integration.
  Goal: reproduce W through a small opt-in fork workflow instead of a one-off manual artifact.
  Probe first:
  - Inventory the fork's current install, hardware-detection, update, initramfs, m1n1, and uninstall patterns. Identify the exact files and package hooks that a kernel update can change.
  Implementation:
  - Add only the M2/J413 hardware path that acceptance proves.
  - Require an exact supported kernel and model before staging.
  - Preserve stock image, module, DTB, m1n1 bundle, GRUB, and recovery assets.
  - Build a distinct non-default image and provide an explicit uninstall and rollback procedure.
  - Refuse input drift, existing conflicting outputs, and unsupported kernel versions.
  Validation:
  - Focused isolated tests cover model/kernel refusal, exact inputs, no-overwrite behavior, rollback manifests, and package-hook drift.
  - The relevant repository gate and independent review pass.
  Exit criteria:
  - A reviewed staging package can create a fresh candidate without changing the saved default or overwriting W.
  Assumption: the known-good W ingredients can be reconstructed from reviewed source and current package inputs without importing the M1-specific installer.
  Verify: compare the reconstructed archive, module indexes, DTB delta, build IDs, configuration, and firmware routing with W before staging.
- [x] Slice 3: stage and validate the integrated candidate.
  Goal: prove the fork workflow, not only the hand-built W artifact.
  Probe first:
  - Recheck protected inputs and exact rollback paths in one user-run staging preflight.
  Implementation:
  - [x] David runs the reviewed sudo preparation command with MagSafe connected and every external USB-C device disconnected.
  - [x] Verify the prepared image, package guard, backups, recovery guide, and root-owned state while the active `boot.bin` remains unchanged.
  - [x] David runs the separate activation command only immediately before the attended reboot.
  - [x] Boot `/boot/initramfs-linux-asahi-m2-displayport.img` once with the external monitor disconnected.
  - [x] Verify the internal panel and system first, then attach LG27 and verify native video. Evidence: [integrated candidate LG27](../evidence/dev-147-integrated-candidate-lg27-2026-09-02.md) records David's physical image after about five to six seconds and native 4K60 state.
  - [x] Switch once from LG27 to LG35 and verify native video. Evidence: [integrated candidate LG35 switch](../evidence/dev-147-integrated-candidate-lg35-switch-2026-09-02.md) records David's physical image after about five seconds and native 3440×1440/99.982 Hz state.
  - [x] Confirm that the internal panel physically shows a normal image after the LG35 switch. Evidence: [integrated candidate internal confirmation](../evidence/dev-147-integrated-candidate-internal-confirmation-2026-09-02.md) records David's normal physical panel and responsive system plus the same-boot dual-output snapshot.
  Validation:
  - Candidate identity is distinct and complete. Both displays and Linux remain healthy. Stock, W, defaults, backups, and recovery files remain unchanged.
  Exit criteria:
  - Candidate reproduces mandatory W video acceptance and its rollback is ready.
  Evidence: Candidate boot `fa500274-a4fd-49e3-a84a-82ec4948b8e3` passed internal-only startup, LG27 attach at 4K60, LG35 switch at 3440×1440/99.982 Hz, physical internal-panel health, and system responsiveness. The three dated integrated-candidate evidence records retain the exact observations and software state.
  Assumption: staging does not trigger unrelated package hooks or rebuild the saved default image.
  Verify: capture protected pre/post hashes and package logs around the exact staging transaction.
- [x] Slice 4: integrate the accepted opt-in path into `quattro-arm`.
  Goal: make the tested feature available from the Apple Silicon fork with clear limits and recovery instructions.
  Validation:
  - Focused tests, `./test/all`, `bin/omarchy commands --check`, entrypoint syntax checks, diff hygiene, and independent review pass, or pre-existing unrelated failures are recorded precisely.
  - The release documentation states supported model/kernel, experimental status, suspend result, update behavior, install, uninstall, rollback, and recovery boundaries.
  Exit criteria:
  - The atomic fork change is reviewed, pushed, and ready for David's release decision. Deployment remains separate until approved.
  Evidence: Commit [`b45948e12`](https://github.com/Skeptomenos/omarchy-mac/commit/b45948e129a5197d7174aa2c4c870134b03fdff6) is pushed on `codex/dev-147-m2-displayport-opt-in`. The focused integration test, 454-command metadata gate, entrypoint syntax, documentation links, whitespace, and no-code-comments checks passed. Independent review passed. Boundary QA found no DEV-147 failure; the aggregate suite remains red only for three precisely recorded unrelated package tests.
- [x] Slice 5: prepare the upstream handoff.
  Goal: share tested M2 replication evidence without duplicating or misrepresenting upstream work.
  Validation:
  - Recheck existing Omarchy Mac PR #289, repository license and contribution terms, and recipient policy.
  - Keep AI provenance, original authorship, successful cases, failures, and untested limits explicit.
  Exit criteria:
  - A small submission-ready evidence update exists. Sending it still requires David's approval.
  Evidence: [Upstream handoff](../research/dev-147-upstream-handoff-2026-09-02.md) records current Omarchy Mac PR #289, the repository license and contribution-guide check, Asahi's prohibitive AI policy, the recommended maintainer-first route, and the exact unsent comment draft. Local draft PR [#1](https://github.com/Skeptomenos/omarchy-mac/pull/1) remains unmerged.
- [x] Release gate: independent verification.
  Goal: re-derive every completed claim from repository state, saved evidence, and the final accepted hardware results.
  Validation:
  - A fresh-context verifier classifies each completed claim as VERIFIED, DISPUTED, or UNVERIFIABLE HERE and reruns the final validation gate.
  Exit criteria:
  - No unresolved disputed claim remains. Accepted unverifiable physical observations have explicit user provenance.
  Evidence: [Release independent verification](../evidence/dev-147-final-independent-verification-2026-09-02.md) classified two repository claims as VERIFIED, zero as DISPUTED, and eight Slice 3 hardware or privileged claims as UNVERIFIABLE HERE. The eight claims remain accepted with David's explicit physical and command-output provenance.
- [x] Slice 6: migrate the live installation from format 1 to format 2.
  Goal: replace the legacy mutable-checkout rollback dependency with the accepted root-owned rollback entrypoint without changing the tested display bytes.
  Probe first:
  - Confirm exact legacy and accepted script identities, J413/T8112, kernel `7.1.6-1-1-ARCH`, MagSafe power, at least 50 percent battery, no package operation, and the accepted image and boot identities.
  Implementation:
  - [x] David disconnects every USB-C cable while MagSafe stays connected. Evidence: both external Type-C controller paths have no partner; the remaining `0-003a` partner is the MagSafe path intentionally excluded by the safety gate.
  - [x] Roll back format 1 with the exact detached `6dbcc24ad` implementation. Do not reboot between rollback and the reviewed format-2 preparation. Evidence: the user-run command reported `ROLLBACK PASS` and retained `rolled-back-20260901T215143Z`.
  - [x] Verify the legacy image and guard are absent, the exact pre-preparation boot is restored, and rollback evidence is retained. Evidence: [live format-1 rollback](../evidence/dev-147-live-format1-rollback-2026-09-02.md) records the absent image and guard, accepted boot SHA-256, external Type-C state, power, and host health.
  - [x] Stage the accepted format-2 release from the sealed bundle at `b45948e12`. Evidence: the user-run clean-environment command reported `PREPARATION PASS` for the accepted image path.
  - [x] Verify the root-owned mode-0700 rollback entrypoint, strict 16-field state, image, guard, recovery assets, and unchanged protected boot inputs. Evidence: [live format-2 preparation](../evidence/dev-147-live-format2-preparation-2026-09-02.md) records the transaction's protected-state verification and the independent public post-check.
  - [x] Activate through the preserved runner. Reconnect the monitor only after the activation result is reviewed. Evidence: the user-run root-owned entrypoint reported `ACTIVATION PASS`; [live format-2 activation](../evidence/dev-147-live-format2-activation-2026-09-02.md) records the script contract and public post-check.
  Validation:
  - Legacy rollback, format-2 preparation, and activation must each report PASS once. Stop after any other result.
  - Candidate boot and image hashes must match the already tested bytes. GRUB, the default image, W, and the installed module must remain unchanged.
  Exit criteria:
  - The accepted image remains available, the active boot remains the accepted candidate, and rollback no longer depends on a developer checkout.
  Evidence: Format-2 preparation and activation both passed. The accepted candidate image and boot identity remain installed. The bound root-owned entrypoint now owns future rollback.
  Assumption: The current format-1 state still matches the accepted `6dbcc24ad` release and has not drifted.
  Verify: Let the exact legacy script validate the protected state before it changes any file. Do not attempt conversion with the format-2 parser.
- [ ] Slice 7: keep DisplayPort usable across repeated AFK service generations.
  Goal: let one supported external monitor reconnect for more than eight link generations without exhausting endpoint `0x28` or requiring a reboot.
  Probe first:
  - [x] Add an offline lifecycle harness that drives at least ten two-service announce and teardown generations against the service allocator.
  - [x] Confirm that the unmodified allocator rejects generation nine after 16 slots.
  - [x] Reject the first disabled-slot candidate when a disabled service still owns a pending command.
  - [x] Reject post-teardown command admission and teardown between command reservation and send.
  Implementation:
  - [x] Limit reuse to the two opted-in endpoint `0x28` service operations.
  - [x] Keep torn-down services enabled until teardown is requested, the command bitmap is empty, the owner cookie is clear, no transient external user remains, and no debugfs state exists.
  - [x] Protect DCP AV owner acquisition and teardown with a nonblocking lock and transient user count. Preserve a newer owner during stale teardown.
  - [x] Serialize command admission, reservation, record setup, and AFK send against teardown. Release the bitmap before unlock when send fails.
  - [x] Reset all per-service state only after the complete retirement boundary.
  - [x] Keep the accepted image and active boot unchanged. Build fresh control and candidate AppleDRM modules from the exact accepted source and inputs. Prepare a separate non-default candidate image from the accepted image.
  - [x] Prepare a literal root bootstrap that authenticates a root-owned image publisher before execution and leaves the saved boot selection unchanged. Evidence: [AFK reuse staging readiness](../evidence/dev-147-afk-reuse-staging-readiness-2026-09-02.md) records the rejected first design, final hashes, 20-test gate, independent QA, and security review.
  Validation:
  - [x] The lifecycle probe fails on the accepted source, rejects three unsafe candidate boundaries, and passes with explicit quiescent retirement and serialized send.
  - [x] The Apple DRM driver builds from the sealed source, and control/candidate inspection proves that only the reviewed AFK change differs.
  - [x] The image-only staging path publishes the exact production candidate in an isolated sandbox, rejects mutable-code and protected-path races, and passes independent QA and security review.
  - After an attended candidate reboot, one supported monitor completes at least ten controlled reconnect generations. Every generation must regain native video, retain a healthy internal display, and leave Linux responsive with zero service-capacity errors.
  Exit criteria:
  - The offline probe, build, artifact comparison, independent review, and attended generation test pass. Recovery assets remain unchanged and ready.
  Assumption: the two opted-in endpoint `0x28` services are the only records consumed by each external link generation, and the DCP DP member has no external command caller in the accepted source.
  Verify: build the exact patched Apple DRM module, inspect its imports and layouts against a control, then exceed the stock eight-generation limit in one attended boot.
  Evidence in progress: [AFK reuse safety correction](../evidence/dev-147-afk-reuse-safety-correction-2026-09-02.md) rejects disabled-only reuse and records the corrected retirement contract and exact-code gate. [AFK reuse offline build](../evidence/dev-147-afk-reuse-build-2026-09-02.md) records the independent patch review, reproducible module pair, interface inspection, and one-member candidate image. [AFK reuse staging readiness](../evidence/dev-147-afk-reuse-staging-readiness-2026-09-02.md) records the authenticated root handoff and confirms that no live staging occurred.
- [ ] FINAL: verify the migrated live state and reliable reconnect boundary, then reconcile DEV-147.
  Goal: prove that the hardened rollback path owns the live experiment and that one supported monitor no longer exhausts AFK service slots.
  Validation:
  - Review the three user-run PASS results, run a bounded read-only system check, and confirm the accepted candidate bytes and limitations remain unchanged.
  Exit criteria:
  - Format-2 state is active, the machine remains healthy, Slice 7 passes, the plan and DEV-147 contain the migration and reliability results, and no open DEV-147 action remains.
  Evidence in progress: [Live format-2 independent verification](../evidence/dev-147-live-format2-independent-verification-2026-09-02.md) reports one VERIFIED claim, zero DISPUTED claims, and six UNVERIFIABLE HERE claims accepted with explicit user provenance. The later AFK exhaustion result reopens reliability work as Slice 7.

## Validation

Slice 1 uses a fresh private evidence directory. It records commands and outputs but does not install software or mutate boot files. Manual actions occur only after a reviewed handoff. The mandatory acceptance threshold is:

- exact W selected for each W boot;
- external image appears within 15 seconds after login or attach;
- internal display remains usable;
- Linux remains responsive;
- native external mode is present;
- one hot reconnect succeeds;
- both LG monitors succeed.

Suspend/resume is recorded last. Its failure blocks default-on support. It does not erase successful opt-in video results if recovery is safe and documented.

Monitor USB data, monitor-only overnight charging, greeter focus, and automatic-standby behavior are excluded from this validation. Keep MagSafe connected during the matrix.

## Progress (LIVING)

- 2026-09-01: Re-scoped DEV-147 to external video acceptance and reversible fork integration. Created related DEV-163 for monitor USB-hub/data loss. Preserved the earlier main and USB plans as historical owners. No hardware action or system mutation occurred in this update.
- 2026-09-01 17:55Z: accepted existing Case A and Case C evidence instead of repeating them. Fresh read-only preflight finds M2/J413, running and installed kernel `7.1.6-1-1-ARCH`, patched TIPD ID `8fd9e3d39ee211f439471a812fb5eaa2622f7585`, packaged AppleDRM ID `dd5e291114047bb4d7c83a529cddb4f4ac9292d7`, and external DCP status `okay`. W remains a root-owned 19,184,103-byte regular file. Both m1n1 backups and both recovery bundles are present. The external connector is disconnected; the internal output is healthy. MagSafe and aggregate AC are online; battery is Full/100%. No systemd job or pacman lock is active. Current command line does not identify the initramfs, so the next case requires a fresh exact W selection. Protected W and boot hashes remain a user-run pre-reboot check.
- 2026-09-01 18:59Z: David's user-run protected check reports W SHA-256 `ae8f1ed7f4f258f89931209cd7de6030be9f6875372d7329151b822a6ba2281f`, matching the accepted image. Fresh same-boot checks retain kernel `7.1.6-1-1-ARCH`, disconnected external DP, connected internal display, MagSafe and aggregate AC online, Full/100% battery, no systemd jobs, no pacman lock, and a clean branch pushed at `1a0f676b1`. Release one exact W reboot with every external monitor disconnected. After login, stop before attaching LG27 so the new boot can be identified first.
- 2026-09-01 19:25Z: Case B PASS. David booted exact W without the monitor, logged in with a healthy internal display, then attached LG27 and woke or powered it. He reports both physical images and responsive Linux. Same-boot capture verifies LG27 at 3840×2160/59.997 Hz, eDP-1 at 2560×1664/60 Hz, both DPMS on, accepted module IDs, active M2 external DCP, both power sources online, Full/100% battery, no failed units, and no fatal display pattern. The combined boot carried temporary `disablehooks=encrypt`; accept the functional video result with that qualification and require intended production arguments for the later integrated-candidate test. Next manual case is one LG27-to-LG35 switch, not another reboot or reconnect loop.
- 2026-09-01 20:17Z: Case D PASS on fresh exact W boot `261ba5db-68fc-4044-8cd8-09687a5fcba3`. The coordinated boot-cleanup reboot started with LG35 attached. David reports both images and responsive Linux. Same-boot capture verifies LG35 at 3440×1440/99.982 Hz, eDP-1 at 2560×1664/60 Hz, both DPMS on, accepted module IDs, both DCP nodes active, MagSafe and monitor power online, Full/100% battery, no failed units, and no fatal display pattern. The display remains active after 460 seconds. Accept this attached-startup result for second-monitor compatibility instead of repeating the superseded live switch. One suspend/resume classification remains last.
- 2026-09-01 20:31Z: Slice 1 complete with Case E FAIL. The system slept for about 20.7 seconds of wall time. Resume attempted the LG35 native mode, but external `prepareLink()` failed with `0xe00002ed`; the modeset failed, the pipe stayed disabled, and swaps were discarded. David saw only an unusable internal lock screen until he disconnected LG35 and woke the machine again. The same W boot recovered to a responsive internal-only session with MagSafe online, Full/100% battery, no failed units, and no fatal display pattern. Do not repeat suspend. The first integration remains reversible and opt-in only; attached-display suspend is unsupported.
- 2026-09-02: Slice 2 complete. Official Asahi tag `asahi-7.1.6-1` resolved to commit `e2e1930a9595bffafad92cec2b5504525efb9cd4`. Rebuilt stock `boot.bin` matched the preserved stock backup. The patched J413 DTB and candidate boot matched the accepted prototype byte for byte. The rebuilt TIPD module was runtime-equivalent after debug and build-ID normalization. The fresh integrated image is 19,184,210 bytes with SHA-256 `a93dd0c1b3a6c4d81bf76f2f43c7c7a2b8b7e1e0306bc487de018667f9c8c196`.
- 2026-09-02: The reversible integration now separates unprivileged bundle preparation, privileged preparation, and privileged boot activation. Preparation leaves `boot.bin`, GRUB, the default image, W, and the stock module unchanged. The package guard pins `linux-asahi`, `m1n1`, and `uboot-asahi`. Offline preparation, activation, and rollback restored the exact stock boot and preserved all protected sentinel hashes. Final bundle: `/home/david/o/.dev147-stage/dev147-optin-bundle-final.iQVkvWr13p/bundle`. Final simulation: `/home/david/o/.dev147-stage/dev147-optin-simulation-final.n40ajXo9lR`.
- 2026-09-02: Independent QA and review passed. The focused integration suite, 454-command metadata gate, Bash syntax, whitespace, documentation links, bundle validation, and 14-field rollback-state verification passed. The repository-wide suite reached all 236 shell test files. DEV-147 passed; three unrelated package-coverage tests failed only because this isolated worktree has no `omarchy-pkgs` checkout. Commit `6dbcc24adbf7bfe435b1c64b0ec5c6ff5eed0f09` is pushed to `Skeptomenos/omarchy-mac:codex/dev-147-m2-displayport-opt-in`.
- 2026-09-01 21:51Z: Slice 3 preparation PASS. David ran the reviewed clean-environment sudo command with only MagSafe attached. `/boot/initramfs-linux-asahi-m2-displayport.img` is root-owned, mode 0600, and exactly 19,184,210 bytes. The package guard is root-owned, mode 0644, and matches SHA-256 `469820ad7cfd015a22cff979b0aa70d62e82dcc7cc05951dca92f40cd660f2bd`. Active `boot.bin` stayed unchanged at the accepted candidate SHA-256 `203ab7027536c8d16f373d02c1f6346a5c34cfe095a9dafd0cfe37d2b354090c`. The EFI backup matches it exactly, and the recovery guide is present. Candidate destinations were absent before preparation. Afterward, no package lock, systemd job, failed unit, or external USB-C partner was present; MagSafe remained online and the battery Full/100%. The root-private state is intentionally unreadable without privilege and will be revalidated by activation. Do not reboot before the separate activation gate.
- 2026-09-02: Integrated-candidate LG27 video PASS on boot `fa500274-a4fd-49e3-a84a-82ec4948b8e3`. David selected `/boot/initramfs-linux-asahi-m2-displayport.img`; loaded TIPD build ID `50ee94a5f8dbae780c676a73b611a7ad5197e47a` proves the new image. Internal-only startup was healthy. David attached LG27 and reported an image after about five to six seconds. Read-only state confirms LG27 at 3840×2160/59.997 Hz and eDP-1 at 2560×1664/60 Hz, both DPMS on. One autonomous xHCI/DCP reset removed HPD at 509.696 seconds and restored the 4K modeset by 519.330 seconds. Video remained active afterward. The LG USB hub did not return and belongs to DEV-163. No fatal pattern occurred. The retained `disablehooks=encrypt` command-line token qualifies this result but does not change candidate identity. Evidence: [integrated candidate LG27](../evidence/dev-147-integrated-candidate-lg27-2026-09-02.md).
- 2026-09-02: Integrated-candidate LG35 switch video PASS on the same identified boot. David disconnected LG27, connected LG35, and reported an image after about five seconds. The kernel completed the new native 3440×1440/99.982 Hz modeset about 2.5 seconds after link setup began. The internal output remains active at 2560×1664/60 Hz, Linux is responsive, power remains healthy, zero units failed, and no fatal kernel pattern appeared. Physical internal-panel confirmation remains the final Slice 3 input. Evidence: [integrated candidate LG35 switch](../evidence/dev-147-integrated-candidate-lg35-switch-2026-09-02.md).
- 2026-09-02: Slice 3 complete. David confirms that the physical built-in screen works normally after the LG35 switch and that Linux remains responsive. A same-boot snapshot at 1,575 seconds retains eDP-1 at 2560×1664/60 Hz and DP-1 at 3440×1440/99.982 Hz, both connected, enabled, and DPMS on, with zero failed units and zero fatal patterns. The candidate now reproduces the mandatory W video cases on both tested monitors. Suspend, stale hot-switch identity, USB data, and the retained boot argument remain explicit limitations. Evidence: [integrated candidate internal confirmation](../evidence/dev-147-integrated-candidate-internal-confirmation-2026-09-02.md).
- 2026-09-02: Slice 4 complete at `b45948e129a5197d7174aa2c4c870134b03fdff6`. Release hardening stores the exact integration script as a root-owned mode-0700 rollback entrypoint, binds its checksum and size in strict 16-field format-2 state, and verifies it before activation or rollback. A red probe showed that the earlier workflow lost rollback when the source checkout disappeared; the fixed test changes and removes the source copy and then passes rollback from preserved state. The feature guide now owns the accepted hardware matrix and explicit suspend, stale-identity, USB-data, boot-argument, package-update, rollback, and Recovery Terminal limits. The focused test and all feature gates pass. Boundary QA found no DEV-147 regression. The aggregate suite exits 1 for three unrelated package tests; independent review passes with no blocker. The branch is pushed and ready for a draft release decision.
- 2026-09-02: Local draft PR [Skeptomenos/omarchy-mac#1](https://github.com/Skeptomenos/omarchy-mac/pull/1) now targets `quattro-arm`. It discloses material AI assistance and preserves the experimental boundary. No merge or deployment occurred.
- 2026-09-02: Slice 5 complete without upstream communication. Omarchy Mac PR #289 remains open with changes requested and does not enable DisplayPort. The repository has no detected contribution guide and uses MIT. The prepared handoff recommends one factual maintainer-first comment before any code PR. Asahi Linux's current policy expressly forbids materially LLM-assisted contributions, so no Asahi code, documentation, comment, issue, or patch submission can come from this work. The exact Omarchy Mac draft comment is saved but unsent. Evidence: [upstream handoff](../research/dev-147-upstream-handoff-2026-09-02.md).
- 2026-09-02: Release independent verification PASS. A fresh-context verifier classified the two repository and upstream-handoff claims as VERIFIED, zero claims as DISPUTED, and the eight Slice 3 hardware or privileged claims as UNVERIFIABLE HERE. David's exact sudo output and physical observations remain their explicit accepted provenance. Repeated focused, metadata, syntax, and diff gates passed. The aggregate suite completed all 236 shell files and retained only the three recorded unrelated package failures. The exact legacy rollback checkout is preserved at commit `6dbcc24ad` with integration-script SHA-256 `6c93c39a97b8e0d42f5f2be262907759713e9718146f40a41e23ab4123c34a17`. This closes the release gate, not the pending live format-2 migration. Evidence: [release independent verification](../evidence/dev-147-final-independent-verification-2026-09-02.md).
- 2026-09-02: Slice 6 legacy rollback PASS. David disconnected all external USB-C cables, kept MagSafe connected, and ran the exact format-1 rollback implementation once. The script retained `rolled-back-20260901T215143Z`. A read-only check finds the legacy candidate image and guard absent while active `boot.bin` remains the accepted candidate bytes. The external Type-C controller paths are clear. MagSafe is online, the battery is Full/100%, and no failed unit, package lock, or package job exists. Do not reboot before format-2 preparation. Evidence: [live format-1 rollback](../evidence/dev-147-live-format1-rollback-2026-09-02.md).
- 2026-09-02: Slice 6 format-2 preparation PASS. David ran the accepted hardened integration with the sealed bundle. The transaction verified and published strict format-2 state plus its root-owned checksummed rollback runner. Public checks confirm the accepted boot SHA, candidate image metadata, package-guard hash, new EFI recovery guide, clear external Type-C paths, Full/100% battery, external power, and no failed unit or package operation. Keep USB-C disconnected and do not reboot before activation through the preserved runner. Evidence: [live format-2 preparation](../evidence/dev-147-live-format2-preparation-2026-09-02.md).
- 2026-09-02: Slice 6 complete. Activation through the preserved root-owned entrypoint reported PASS. Its pre-mutation checks validated the strict state, runner checksum and mode, backups, recovery guide, image, guard, boot identity, host, power, and external-port safety. The public post-check retains accepted boot and image metadata, a healthy internal output, Full/100% battery, no failed unit or package operation, and no fatal display pattern. No migration reboot is needed because the display payload bytes did not change. Evidence: [live format-2 activation](../evidence/dev-147-live-format2-activation-2026-09-02.md).
- 2026-09-02: Final format-2 independent verification PASS. A fresh-context verifier classified one external-port safety claim as VERIFIED, zero claims as DISPUTED, and six historical privileged or root-private claims as UNVERIFIABLE HERE. David's exact three PASS outputs remain their explicit provenance. Focused integration, 454-command metadata, parser-selective syntax, changed-script syntax, and diff gates passed. The aggregate suite retained only the three known unrelated package failures across all 236 shell files. No item re-enters the plan. Evidence: [live format-2 independent verification](../evidence/dev-147-live-format2-independent-verification-2026-09-02.md).
- 2026-09-02 13:49Z: A later same-boot two-monitor attempt exposed AFK service-slot exhaustion and reopened DEV-147 reliability work. Boot `fa500274-a4fd-49e3-a84a-82ec4948b8e3` reached all 16 endpoint `0x28` slots on channels 1 through 31, then logged 14 capacity errors and 32 failed announcements while both tested monitors stayed blank. David safely recovered by disconnecting both displays and booting the same accepted candidate. Fresh boot `d930e28c-4a73-4de0-be0b-7bbfae3ceafe` has two services on channels 1 and 3, zero capacity or announcement errors, and a completed LG27 3840x2160 mode set. David confirms both displays and Linux are healthy. The format-2 migration remains accepted; only final reliability closure is reopened. Evidence: [AFK service-slot exhaustion](../evidence/dev-147-afk-service-exhaustion-2026-09-02.md).
- 2026-09-02 13:55Z: Documentation boundary validation passed every DEV-147 test, command metadata for 455 commands, all selected Bash and Python syntax checks, local links, and diff hygiene. The aggregate suite reached all 235 shell files and remained red for three known package-checkout tests plus an unrelated Quickshell runtime assertion that counted three widget handlers for two screens. The same runtime assertion repeated once, so no further retry or out-of-scope fix was attempted.
- 2026-09-02 14:45Z: Slice 7 reached its final implementation cycle after two review rejections. Stock fails at generation nine. Disabled-only reuse erases a pending command. A second candidate admits a command after teardown. A third boundary lets teardown enter between reservation and send. The final five-file prototype adds endpoint-scoped retirement, protected owner lifetime, command admission, and a service-lock span through AFK send. All four negative controls and the full exact-code lifecycle gate pass. Fresh cycle-3 QA passed the exact patch, AST, patch application, checkpatch, path inventory, hash, and accepted-source checks. Final independent review passed with no blocking bug. No accepted source, package, boot file, or live-system mutation occurred. Evidence: [AFK reuse safety correction](../evidence/dev-147-afk-reuse-safety-correction-2026-09-02.md).
- 2026-09-02 15:45Z: The fresh offline AppleDRM control and candidate builds pass. The control is byte-identical to the earlier control. The candidate keeps the stock name, vermagic, dependencies, aliases, and empty export set. It adds only the expected `_raw_spin_lock` and `_raw_spin_unlock` kernel imports, which exist in the pinned `Module.symvers`. AArch64, DWARF, BTF, and `.BTF.base` checks pass. Independent build QA reports PASS. The reviewed image builder replaces only `appledrm.ko` in the accepted image and retains the early archive plus all other 1,161 main records byte-for-byte. The separate image is 21,598,988 bytes with SHA-256 `ebd383c21a35d6b0eff22ffe6f144ea7790c31d7cf058a1c3afa5e39c2375acd`. It is not staged or booted. Evidence: [AFK reuse offline build](../evidence/dev-147-afk-reuse-build-2026-09-02.md).
- 2026-09-02 16:00Z: The first image-only staging wrapper passed isolated functional QA but failed the required root-path review. It hashed a user-owned library by pathname and then sourced that pathname as root. A same-user replacement between those operations could execute unverified code as root. The wrapper is rejected and removed from the branch. No live staging occurred. The replacement must copy the wrapper and library into a new root-owned, non-writable directory, verify those copied bytes, and execute only the authenticated root-owned copy.
- 2026-09-02 17:32Z: The replacement staging handoff is ready for manual execution. The literal bootstrap embeds the publisher as data, creates a fresh root-owned mode-0700 transaction on `/boot`, verifies the root-owned publisher before isolated Python execution, and keeps `INCOMPLETE` until exact no-replace publication and all final checks are durable. The focused gate passes 20 tests. It includes the real 21,598,988-byte candidate, mutable source and protected-path races, publication and completion fault boundaries, exact bwrap bootstrap controls, and collision preservation. Independent QA and security review PASS. The candidate remains unstaged. The accepted image, default image, `boot.bin`, GRUB, packages, modules, and live destination remain unchanged. Evidence: [AFK reuse staging readiness](../evidence/dev-147-afk-reuse-staging-readiness-2026-09-02.md).
- 2026-09-02 17:36Z: Fresh-context milestone verification PASS with zero disputed claims and no item to reopen. The verifier reran the exact lifecycle and 20-test staging gates, independently spot-checked the protected ancestor attack and real candidate copy, verified all three staging hashes and the embedded payload, and found the live candidate and matching transactions absent. Historical negative-action and root-private claims remain accepted with David's approval and prior command or physical provenance. The final attended reboot and ten-generation hardware result remain open.
- 2026-09-02 17:38Z: Final branch boundary validation completed all 235 shell test files. DEV-147 passed. Three unrelated package-ownership tests failed because this isolated worktree has no `omarchy-pkgs` checkout. The earlier transient Quickshell failure did not recur. Command metadata passed 455 commands. Entrypoint syntax passed 5 Python and 453 Bash files. The focused staging gate, documentation gate, and diff hygiene pass.

## Discoveries (LIVING)

- **Finding:** The working video path and unreliable monitor USB-data path have different outcomes and evidence.
  **Evidence:** W produced native video on both LG monitors even when only USB root hubs remained. The later reconnect restored video before the monitor hub disappeared again.
- **Finding:** The PR #582 candidate is not the local video solution.
  **Evidence:** Both LG monitors failed to detect a device on that candidate. The later W boot restored video.
- **Finding:** `linux-asahi-headers` is not installed in the current package inventory.
  **Evidence:** `pacman -Q linux-asahi-headers` reports that the package is not found, while `linux-asahi 7.1.6.asahi1-1` is installed. This does not block W acceptance. Resolve the build dependency before Slice 2.
- **Finding:** LG27 attach-after-login works on W even when the boot starts with no external partner.
  **Evidence:** The accepted boot begins with only eDP-1. After the later attach and monitor wake/power action, DP-1 publishes 16 modes and runs at 4K60 without a driver reload or reboot.
- **Finding:** LG35 attached startup works on W at its native high-refresh mode.
  **Evidence:** Fresh boot `261ba5db-68fc-4044-8cd8-09687a5fcba3` publishes 14 LG HDR WQHD modes and remains active at 3440×1440/99.982 Hz after 460 seconds.
- **Finding:** W does not recover the external display across suspend with LG35 attached.
  **Evidence:** Resume reaches external `dcp_dptx_connect`, then `prepareLink()` fails with `0xe00002ed`; the native modeset returns `80000104` with the pipe disabled. Cable removal is required before the internal login becomes usable again.
- **Finding:** The accepted prototype can be reconstructed from the official Asahi source and retained matching build inputs.
  **Evidence:** Stock boot reconstruction is byte-identical. The patched DTB and candidate boot are byte-identical to the prototype. The rebuilt TIPD module has identical runtime content after removing debug data and the build-ID note.
- **Finding:** The integrated candidate supports a same-boot switch between both accepted LG monitors at their native modes.
  **Evidence:** LG27 ran at 3840×2160/59.997 Hz. After one physical switch, LG35 produced a visible image in about five seconds and ran at 3440×1440/99.982 Hz. The internal DRM output stayed enabled and Linux stayed responsive.
- **Finding:** A physical monitor switch re-enumerated the LG USB hub after the earlier autonomous reset did not.
  **Evidence:** The LG35 switch identified the `0bda:5411` hub and `043e:9a39` USB Controls before HPD asserted. This difference belongs to DEV-163 and does not block video acceptance.
- **Finding:** Native mode selection changes correctly during the integrated-candidate monitor switch, but exported monitor identity stays stale.
  **Evidence:** DCP and DRM changed to the LG35's 14-mode set and 3440×1440/99.982 Hz output. The exported EDID and Hyprland description still identify the prior LG27 4K display. This repeats a known prototype metadata limitation and does not invalidate the physically confirmed LG35 image.
- **Finding:** The first integration left Linux rollback dependent on the mutable source checkout.
  **Evidence:** Independent review showed that an Omarchy update or removed worktree could make the format-1 rollback script unavailable. The format-2 fix preserves and binds the exact rollback implementation under root-owned state, and the regression test passes after the source copy changes and disappears.
- **Finding:** The accepted live installation still uses legacy format-1 state.
  **Evidence:** It was prepared and activated before the format-2 rollback fix. The new strict parser correctly refuses the old 14-field state. The live installation must use the exact `6dbcc24ad` implementation for rollback before any fresh format-2 preparation.
- **Finding:** Repeated external link generations exhaust the fixed endpoint `0x28` AFK service table.
  **Evidence:** The failed boot allocated 16 services on channels 1 through 31. Later generations produced `too many enabled services!` and rejected channel announcements through 59. A fresh reboot reset the table to channels 1 and 3 and restored native LG27 video.
- **Finding:** `enabled=false` is not a safe AFK service reuse boundary.
  **Evidence:** Endpoint `0x28` teardown can disable a service while its command bitmap remains populated. The first candidate erased that pending state. The corrected prototype keeps the old channel routable until explicit quiescence. Evidence: [AFK reuse safety correction](../evidence/dev-147-afk-reuse-safety-correction-2026-09-02.md).
- **Finding:** The exact Apple DRM build inputs remain available without installing the live headers package.
  **Evidence:** The retained private header root contains the matching `.config`, `Module.symvers`, `vmlinux`, generated headers, and prior contained build toolchain for `7.1.6-1-1-ARCH`.
- **Finding:** Hashing user-owned code before a later root import does not authenticate the executed bytes.
  **Evidence:** The rejected wrapper allowed pathname replacement between `sha256sum` and `source`. The accepted handoff writes embedded data into a root-owned private directory, verifies that destination, and only then executes it.

## Decision Log (LIVING)

- **Decision:** Remove monitor USB-hub enumeration from DEV-147's completion criteria.
  **Rationale:** Video works independently. Keeping USB tracing on the critical path delays a usable external-display release without testing the display fix.
  **Date:** 2026-09-01
- **Decision:** Treat suspend/resume as a classification gate for the first opt-in release and as a blocker for default-on release.
  **Rationale:** The reference path has an unresolved reconnect-after-suspend limitation. One safe result is useful; repeated risky loops are not.
  **Date:** 2026-09-01
- **Decision:** Keep MagSafe connected during video acceptance.
  **Rationale:** A prior unattended monitor-only session lost net charging. Power-source endurance is a separate question.
  **Date:** 2026-09-01
- **Decision:** Reuse the identified attached-startup and hot-reconnect results.
  **Rationale:** Both have exact W user provenance and independently checked saved evidence. Repeating them adds risk and time without closing a new gap.
  **Date:** 2026-09-01
- **Decision:** Accept Case B with the temporary `disablehooks=encrypt` qualification.
  **Rationale:** The token skips an unused initramfs hook. It did not change W, the kernel, DTB, display modules, or display configuration. Repeating the hardware case would add risk without isolating a display variable. The later integrated candidate must still pass with its intended production arguments.
  **Date:** 2026-09-01
- **Decision:** Accept the fresh LG35 attached-startup result as Case D instead of repeating the superseded live monitor switch.
  **Rationale:** The case exists to prove second-monitor compatibility at native mode. Exact W now proves that result, while Case C already proves one controlled hot reconnect. Another physical action would add risk without closing the remaining suspend/resume gap.
  **Date:** 2026-09-01
- **Decision:** Complete Slice 1 with attached-display suspend unsupported and block default-on release.
  **Rationale:** Case E failed at external link preparation and modeset and required cable removal for a usable internal login. The predeclared exit criteria permit this one classified failure for reversible opt-in packaging. Repetition would add recovery risk without changing the release boundary.
  **Date:** 2026-09-01
- **Decision:** Separate preparation from boot activation.
  **Rationale:** Preparation can publish the image, recovery assets, state, and update guard while leaving the active boot chain unchanged. A short, separate activation gate limits the time in a mixed boot state before the attended reboot.
  **Date:** 2026-09-02
- **Decision:** Accept the integrated candidate for opt-in fork integration with explicit limitations.
  **Rationale:** Internal-only startup, both tested monitors, one same-boot switch, the internal panel, and Linux responsiveness passed. The known suspend failure blocks default-on release, while stale monitor identity, USB data, and the retained boot argument do not invalidate the accepted video path.
  **Date:** 2026-09-02
- **Decision:** Preserve the exact rollback implementation in root-owned state for every new preparation.
  **Rationale:** Package hooks can block boot-package drift, but they cannot ensure that a developer checkout survives an Omarchy source update. A checksummed state-local entrypoint keeps rollback available and fail-closed.
  **Date:** 2026-09-02
- **Decision:** Do not parse or migrate the active format-1 state with the new format-2 script.
  **Rationale:** Strict refusal is safer than an in-place privileged state conversion. Use the exact legacy implementation to roll back first, then perform a fresh preparation with the accepted release.
  **Date:** 2026-09-02
- **Decision:** Ask Omarchy Mac maintainers whether they want enablement before opening an upstream code PR.
  **Rationale:** Their existing diagnostics PR is still under requested changes and explicitly excludes enablement. A small factual hardware-evidence comment gives maintainers a low-cost scope decision before a large experimental workflow enters review.
  **Date:** 2026-09-02
- **Decision:** Do not contribute this work to Asahi Linux.
  **Rationale:** Asahi's current policy expressly forbids materially LLM-assisted code, documentation, and engineering decisions in any project contribution. This session falls inside that boundary.
  **Date:** 2026-09-02
- **Decision:** Accept the eight independently unrepeatable Slice 3 claims with explicit user provenance.
  **Rationale:** They require root-only state or physical display actions. The fresh-context verifier found no dispute, the saved outputs identify the tested boot and native modes, and David supplied each physical result. Repeating the accepted hardware matrix would add risk without closing an evidence gap.
  **Date:** 2026-09-02
- **Decision:** Do not reboot only to verify the format-2 migration.
  **Rationale:** The active boot and candidate image remain the exact bytes already tested on both monitors. The migration changes protected transaction state and rollback durability. Its executable coverage is the integration test plus one live preparation and activation, not another identical display boot.
  **Date:** 2026-09-02
- **Decision:** Accept the six independently unrepeatable Slice 6 claims with explicit user provenance.
  **Rationale:** They are past sudo transactions or live root-private state. The user supplied each exact PASS result. The accepted scripts verify the protected inputs before mutation, the public results match, and the fresh-context verifier found no contradiction or item to reopen.
  **Date:** 2026-09-02
- **Decision:** Reopen DEV-147 for AFK service-slot reliability and keep the format-2 migration accepted.
  **Rationale:** The failure is a live service-lifecycle defect in the unchanged Apple DCP driver. The migration did not change the running kernel or tested payload. A reboot cleared the failure, which isolates the regression from the installation-state change.
  **Date:** 2026-09-02
- **Decision:** Test slot reuse offline before another display reboot.
  **Rationale:** A torn-down service can still have a late command reply or external owner. The first disabled-only design failed QA. Require explicit endpoint-scoped retirement and exact-code lifecycle validation before this machine boots a candidate.
  **Date:** 2026-09-02
- **Decision:** Deliver the staging publisher as an authenticated literal root bootstrap.
  **Rationale:** Root must not execute or import a mutable user-owned pathname. The literal writes fixed payload bytes into a new root-owned private transaction and authenticates that copy before execution.
  **Date:** 2026-09-02
- **Decision:** Accept the staging verifier's historical and root-private claims with explicit user provenance.
  **Rationale:** The fresh verifier found no contradiction and current state matches the recorded boundary. Repeating past negative actions is impossible. Privileged staging and the physical reboot remain separate future evidence gates.
  **Date:** 2026-09-02

## Follow-ups

- [ ] DEV-163: bind the existing scoped recorder to a fresh boot and capture one attended reconnect before selecting any monitor USB-data fix.
- [ ] Decide later whether sustained monitor-only charging needs a separate issue and controlled test.
- [ ] Investigate the greeter focus behavior separately from kernel display enablement.
