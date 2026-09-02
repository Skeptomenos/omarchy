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

The saved boot default remains unchanged. A manual GRUB edit selects W for one boot. The active prototype DTB is not removed by an ordinary reboot. Kernel updates can invalidate the patched module, DTB, and image as a matched set. Full rollback has not been rehearsed.

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
- [x] FINAL: independent verification.
  Goal: re-derive every completed claim from repository state, saved evidence, and the final accepted hardware results.
  Validation:
  - A fresh-context verifier classifies each completed claim as VERIFIED, DISPUTED, or UNVERIFIABLE HERE and reruns the final validation gate.
  Exit criteria:
  - No unresolved disputed claim remains. Accepted unverifiable physical observations have explicit user provenance.
  Evidence: [Final independent verification](../evidence/dev-147-final-independent-verification-2026-09-02.md) classified two repository claims as VERIFIED, zero as DISPUTED, and eight Slice 3 hardware or privileged claims as UNVERIFIABLE HERE. The eight claims remain accepted with David's explicit physical and command-output provenance.

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
- 2026-09-02: FINAL independent verification PASS. A fresh-context verifier classified the two repository and upstream-handoff claims as VERIFIED, zero claims as DISPUTED, and the eight Slice 3 hardware or privileged claims as UNVERIFIABLE HERE. David's exact sudo output and physical observations remain their explicit accepted provenance. Repeated focused, metadata, syntax, and diff gates passed. The aggregate suite completed all 236 shell files and retained only the three recorded unrelated package failures. The exact legacy rollback checkout is preserved at commit `6dbcc24ad` with integration-script SHA-256 `6c93c39a97b8e0d42f5f2be262907759713e9718146f40a41e23ab4123c34a17`. Evidence: [final independent verification](../evidence/dev-147-final-independent-verification-2026-09-02.md).

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

## Follow-ups

- [ ] DEV-163: bind the existing scoped recorder to a fresh boot and capture one attended reconnect before selecting any monitor USB-data fix.
- [ ] Decide later whether sustained monitor-only charging needs a separate issue and controlled test.
- [ ] Investigate the greeter focus behavior separately from kernel display enablement.
