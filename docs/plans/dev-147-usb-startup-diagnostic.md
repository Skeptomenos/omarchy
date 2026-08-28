# DEV-147 — one-boot USB startup diagnostic design

Updated: 2026-08-28, after D3 readiness confirmation. Status: offline D1 complete; D2 helper preparation complete with 38 isolated tests and independent safety review passing. The trace, archive, and assembly suites pass 59, 58, and 55 methods. Private builds, import/logging checks, exact no-change controls, and the 413-command diagnostic assembly pass. The new private image has 200 modules and exactly four archive changes. D0 remains complete. User-run D2 staging now passes; independent file metadata agrees. D3 readiness passes and the one-time handoff below is ready for David. No diagnostic boot or result is reported yet.

Current source branch: `codex/dev-147-m2-dp-altmode-public`. Its first checkpoint `c781312d1` was pushed and verified by remote readback. The [public archive](../../dev/apple-dp-altmode/usbdiag/README.md) preserves the authored drafts and fixtures, but excludes host manifests and raw logs. Public helpers have invalid machine-identity/path placeholders and must not run live. The original operational helpers and private branch remain unchanged. The [dated source checkpoint](../evidence/dev-147-public-source-checkpoint-2026-08-28.md) distinguishes historical R4 evidence from the new private RED runs.

The [main plan](dev-147-m2-displayport.md) owns overall acceptance and rollback. This subplan owns the proposed diagnostic. The [dated investigation](../research/dev-147-usb-startup-2026-08-28.md) owns the source findings and earlier evidence. Full Gate 4b remains on hold.

## Question and limit

Does this controller's first initialization call the USB2 mode API with a missing handle, then reach the actual ATC HOST setter only after DWC3 core initialization? Record failed attempts and automatic retries too. A later successful attempt can still report `PROBE_PENDING` after an earlier attempt acquired a handle.

This experiment can establish software call order. It cannot read whether the PHY latched a setting or prove why the monitor hub did not enumerate. Logging and earlier module availability can change timing. A newly working startup would not be a fix or a reliability pass.

## Progress (LIVING)

| Gate | State | Exit |
|---|---|---|
| D0 — design and independent review | Complete; design only | Measurement, image boundary, parser checks, and rollback reviewed; no implementation. |
| D1 — offline implementation and build | Complete; offline QA PASS | 59 trace, 58 archive, and 55 assembly tests pass. Private builds, import/logging checks, no-change controls, and one verified 200-module diagnostic image pass. All 413 assembly commands pass. No module load or hardware-test pass. |
| D2 — stage a distinct image | Complete; user-run staging PASS | David's final helper PASS validates image and protected post-checks. All 40 reported pin records match; independent metadata agrees. Root-private contents were not reread. No reboot implied. |
| D3 — one attended diagnostic startup | Readiness PASS; handoff ready; result pending | David confirmed physical readiness. Fresh checks pass. One user-selected boot and fixed-boot capture only; no automatic retry or completed startup claim. |

D1 included source implementation, focused fixtures, the two module builds, and private image preparation under David's explicit approval. It did not include installation, staging, a driver reload, or a reboot. David then approved D2 helper preparation. Its offline implementation and tests are complete in a fresh private continuation. David has now completed the reviewed production preflight and privileged staging. The agent did not execute either. Each later action stops for its own review and user action.

The [D2 helper record](../evidence/dev-147-usbdiag-staging-helper-2026-08-28.md) owns the retained RED runs, environment-loop and EXIT-trap defects, narrow corrections, and final independent 38-test PASS. The [public helper](../../dev/apple-dp-altmode/stage-usbdiag-initramfs.sh) has deliberately invalid constants. David used the final pinned private copy. The [D2 staging record](../evidence/dev-147-usbdiag-staging-2026-08-28.md) records the complete user PASS and independent metadata. Pending staging instructions are superseded; do not execute either the completed final command or the earlier private candidate again.

The [helper-QA record](../evidence/dev-147-offline-helper-qa-2026-08-28.md) owns initial image-helper GREEN, import/logging verification, the retained userspace linker failure, and saved-gzip validation. The later [real-control record](../evidence/dev-147-real-archive-controls-2026-08-28.md) owns the real format failure, narrow correction, 58 tests, scratch-output stop, and successful no-change archive/index control. None is a module-load or boot-safety result.

The [private-image record](../evidence/dev-147-private-diagnostic-image-2026-08-28.md) owns the later symbol-index and alias-normalization stops, their independent investigation, test-first corrections, 55 passing assembly methods, and the verified candidate. It also records that the first 30 assembly fixtures were written after their draft implementation. Do not describe those original fixtures as test-first evidence.

The [R4 evidence](../evidence/dev-147-sandbox-r4-2026-08-28.md) records the approved correction and one successful full probe, including namespace, network, write-boundary, and seven focused test checks. The [D1 hold record](../evidence/dev-147-usbdiag-d1-hold-2026-08-28.md) retains the earlier three failures; its missing errno remains unknown. The tool manifest and protection policy did not change. The [trace/build checkpoint](../evidence/dev-147-trace-and-module-builds-2026-08-28.md) records later GREEN tests, the independent review failures and correction, pahole signature/executable authentication, private builds, and remaining checks. No package was installed; builds used the verified private header tree.

The unchanged private D1 archive retains its drafts and failed attempts. The private R4 checkpoint retains the corrected sandbox and successful run. Neither frozen checkpoint was reused for outputs. A fresh private continuation passed the R4-equivalent isolation probe, then ran the trace and image stubs: 32 trace tests reported 40 NotImplementedError errors; 16 image tests reported 30. Both runs preserved all inputs and did not time out. These are genuine RED results, not implementation passes. Fifteen readable system/prototype/recovery pins still match, and the earlier 60-file D1 and 34-file R4 seals verified. No root-only image/GRUB read or live driver action occurred. The monitor is not needed for offline D1; David may unplug it while leaving MagSafe connected. That was permission, not a confirmed unplug or hardware-test result. Recheck the physical setup before D3.

## Target and source boundary

Use the existing J413/T8112 machine and kernel `7.1.6-1-1-ARCH`. Keep the current candidate DTB and working DP core. Source remains pinned to Asahi `e2e1930a9595bffafad92cec2b5504525efb9cd4`.

| Layer | Diagnostic target | Basis |
|---|---|---|
| Connector | Front/lower left USB-C, `0-003f` | Existing prototype route |
| DWC3 glue | `/soc/usb@502280000` | Saved `dwc3_1` node |
| ATC PHY | `/soc/phy@503000000` | Saved `atcphy1`; both USB PHY references point here |

The retained preprocessed DT (retained privately) supplies these links. Filter diagnostic output by J413 compatibility and the exact OF node. Print only fixed labels such as `front_lower`, `dwc3`, and `atc`. Do not use changing `portN` or PHY instance numbers to identify the monitor. The module still serves other devices; diagnostic filtering does not isolate kernel execution or make the experiment risk-free.

Only two source files may gain diagnostics: `drivers/usb/dwc3/dwc3-apple.c` and `drivers/phy/apple/atc.c`. Do not change TIPD, the HPD patch, generic PHY/USB/HCD code, DT, DCP/DRM, exported interfaces, or driver control flow. No early PHY acquisition, new error handling, reordered calls, extra hardware reads/writes, new locks, retries, delays, or work items. Leave the existing calls, hardware accesses, timeouts, and lock order intact. A local variable that records a formerly ignored return must not make that return affect execution.

## Required records

Record at existing operation boundaries, never inside register polling or delay loops. Preserve original error returns and no-op branches. Function locations are in the pinned source archive (retained privately).

| Component / site | Required observation |
|---|---|
| DWC3 probe | Target probe generation, begin, ready or original failure. |
| DWC3 role callback | Requested role, existing state, and same-role skip, under its existing lock. |
| `dwc3_apple_init` | Attempt ID and state; early USB2 call begin/end and return; reset result; core-init begin/end; host/gadget-init begin/end; original exit result. |
| ATC probe/finalize | Generation and begin before initialization operations; ready or original failure. |
| ATC mux | Current/target mode, cached lane orientation and pipe-handler state, no-op or configure result. |
| ATC USB2 power-on/off | Begin before first existing write; end after last existing write. These mark execution, not measured electrical state. |
| ATC USB2 mode setter | Entry after its existing lock; requested mode/submode; exit and unchanged return, including HOST_SS rejection and HOST fallback. |

At the early USB2 call and core-init return, record `usb2_present` and `usb2_error` as separate booleans. A non-null error pointer is not a usable handle. Do not dereference or print that pointer, add a validity guard, or introduce a WARN. Keep the early setter unmoved and preserve its currently ignored return semantics.

Use a module-wide sequence that survives probe retries, a component-local probe generation, and a DWC3 initialization-attempt ID within each generation. ATC and DWC3 generation numbers are independent. Failed probes and deferred attempts must remain visible. Do not join the streams by matching generation numbers or treat the first successful attempt as the first attempt.

Use native `pr_info()` / KERN_INFO with one fixed, newline-terminated JSON payload per record. Include schema version, a fixed diagnostic revision token, fixed component/target, sequence/generation/attempt where applicable, event/phase, and only the cached values needed above. The initial token is `dev147-usbdiag1-v1`; bind it to the reviewed source/patch manifest and both binary hashes/build IDs, and change it for a changed diagnostic implementation. Both earliest probe markers must carry that token. A schema version or a later loaded build ID alone cannot identify the code that handled the first probe. Retain boot identity, priority, message, cursor, and original timestamps in the journal envelope. No application logging library, raw pointers, MMIO values, register dumps, serial numbers, arbitrary strings, or backtraces. An absent field must be explicit or specified by the event schema; never substitute a plausible value.

Limit each component to 128 records per module load, including one reserved `capture_capped` marker, with at most 384 bytes per record. Saturate the counter and stop diagnostics after the cap; driver execution must continue unchanged. The implementation must be race-safe across target probe retries without changing the existing lock order. Do not use rate-limited logging that silently drops selected calls. No dynamic-debug, tracefs, BPF, console-level, or kernel-command-line changes.

The [kernel logging guidance](https://docs.kernel.org/core-api/printk-basics.html) warns that logging can delay execution. The pinned header exposes `printk_deferred`, but the retained `Module.symvers` does not export `_printk_deferred`; do not add an export or use that route. The [format guidance](https://www.kernel.org/doc/html/latest/core-api/printk-formats.html) also requires correct integer formats. Native kernel logging is the explicit exception to the application-logger recommendation in the logging skill; JSON records and levels remain required.

## Image containment and timing change

The known working image is the private Gate 4 image (retained privately), SHA-256 `ae8f1ed7f4f258f89931209cd7de6030be9f6875372d7329151b822a6ba2281f`, 19,184,103 bytes. Its root-private staged copy is `/boot/initramfs-linux-asahi-dpalt.img`. Preserve both unchanged. The private source is available for offline work; no extra privileged read is needed during design.

The saved working archive contains 199 modules, including `phy-apple-atc`, `dwc3`, `udc-core`, and the xHCI modules. It does not contain `dwc3-apple`. Its direct dependency closure is already present. The verified diagnostic image replaces ATC, adds DWC3 glue, and replaces only `modules.dep.bin` and `modules.alias.bin`. It has 200 modules. The original symbol index, both builtin indexes, and DP core remain byte-identical.

The private candidate is 19,647,739 bytes, SHA-256 `a11bf3a2bac1f105aa57b08ce9fad338c68882851247f7524d09f4b7c94188ca`. It has seven unchanged early records and 1,163 main records. All 1,159 unrelated original main records and the archive tail are unchanged. All 200 binary-only filename/dependency checks and both target OF aliases pass. The original 199 dependency results are identical. The same candidate is now staged at `/boot/initramfs-linux-asahi-dpalt-usbdiag1.img` but has not been selected or boot-tested.

Adding the glue permits earlier automatic probing, even without an explicit preload. Record this as a separate timing variable. This boot cannot be compared with the old image as a timing-matched A/B test. If a later causal comparison is needed, its control must match this packaging and logging policy; that is not part of D3.

Verified preparation route: preserve raw records from the saved archive and write a new private image. Generate indexes in a separate reduced module root. The saved image has 199 dependency records and seven indexes; the full private tree has 1,861 dependency records. The image lacks `modules.order`, `modules.builtin`, and `modules.builtin.modinfo`. Use those exact pinned inputs only in the generation root; do not run bare `depmod` over an extracted archive. Keep these inputs and extra generated outputs out of the image. The generated symbol binary changes only ordering priorities; its exact bytes and complete mapping dump are pinned. Retain the original symbol binary in the final index set. All five static indexes must remain byte-identical. Only the dependency and alias binary indexes may change, with full final binary-only resolution checked.

The unmodified control now passes index regeneration, lossless raw-record serialization, and gzip reconstruction. Independent GNU cpio and bsdtar listings agree; complete reconstructed image bytes are identical. No general archive extraction was needed. The saved image has seven early members, 1,162 main members, and gzip starting at byte 10,240. Preserve that split, record placement, payloads, type, permissions, UID/GID, link targets, and hardlink relationships in the diagnostic image. Independent stdout-only extraction of its selected module payloads must also match. No archive-member path may escape a private directory. Keep embedded `buildconfig` unchanged as base-image provenance; retain new build/repack provenance externally.

The private operational core-only preparation/staging helpers are fixed to the completed experiment and must stay unchanged. Their public archival copies have deliberate identity redactions and are not live-use helpers. Do not rerun, parameterize, or weaken the operational guards. A new bounded helper needs its own tests and review. It must reject an existing or symlinked output, private-tree hardlinks to system files, source/image drift, an active package transaction, and missing build isolation. It must never fall back to an unrestricted build. Keep all incomplete artifacts for inspection; no cleanup or automatic retry.

D1 requires a real unprivileged build sandbox with only a fresh persistent build directory and its temporary area writable. Source snapshots, exact headers/`Module.symvers`, toolchain, and required inputs are read-only. No access to credentials, network during compilation, host package writes, or live device interfaces. The current unrestricted execution tool is not itself a build sandbox. If containment cannot be established, stop and report it. Each command has the existing five-minute limit; retain logs and ask before retrying a timeout.

Before release for D2, require all of these checks:

- Exact kernel/config/header/toolchain provenance, module ABI/imports/dependencies/aliases, distinct diagnostic build IDs, and no new unreviewed warnings. Build and inspect unmodified source as an offline control if needed to resolve build-method differences; do not load it.
- The working image/source, candidate DP core, all original stage artifacts, old gate scripts, and backups remain unchanged. Recheck actual host drift before execution; a dated design check is not a fresh preflight.
- The new archive retains all 199 original module paths, replaces ATC, and adds only DWC3 glue: 200 modules total. Only reviewed non-builtin index differences may accompany that delta; no extra depmod inputs or outputs enter the archive. Both builtin indexes remain identical. All other original payloads, metadata, link relationships, and archive placement match, including DP core, DT-related content, firmware, `init`, hooks, keyboard/disk unlock support, configuration, OpenSSL, and symlinks. No new preload, custom boot hook, persistent entry, or runtime service.
- Independent extraction and dependency/index resolution show that the intended diagnostic modules are available for the first probe. A later loaded build ID alone does not prove which code handled the first event. D3 requires their earliest probe markers and diagnostic identities too.
- The new image's exact hash, size, member/delta manifest, and source/patch/build records are pinned. The fixed destination is `/boot/initramfs-linux-asahi-dpalt-usbdiag1.img`; David has now created it through the reviewed helper, without selecting it. The pre-staging absence guard passed in that run. Its presence now forbids rerunning or overwriting.

D2 helper preparation is complete. The new reviewed, fixed-source/fixed-destination staging-only helper preserves atomic no-replace publication, repeated protected hashes, permissions, sync, and incomplete-result rules. It protects the working DP image and both installed USB modules. It rechecks source-image hash/size, kernel and package versions, package-transaction state, free space, recovery copies, and protected stock/working files before any copy. Public source retains invalid host identifiers. The final private copy completed staging; retain it without rerunning it. Preserve the old helper and all frozen D1/D2 preparation outputs.

The 38 focused failure-path and real-tool tests pass in isolation with synthetic boot/source files. They cover existing destinations and links, source/protected-file drift, synthetic host/kernel/package records, package lock, space validation, bounded copy failure, interruption, and final success-marker ordering. A missing-path sync error checks propagation, not storage-device failure. Independent QA and safety review pass. Never run the helper against live `/boot` for QA. Preserve partial results on failure; do not add an overwrite or automatic cleanup option. David's complete final PASS now supplies the user-run result. Its root-private check directory is `/boot/.dev147-usbdiag-stage.ESqzIgLr8I`; the agent checked only directory/file metadata. The paste has no separate numeric exit-status capture. Do not repeat a completed gate or treat staging success as permission to reboot.

## D3 — attended diagnostic case

### Current D3 handoff — one user-selected restart

Read these steps before restarting and keep a copy available on another device. David confirmed no other active work, both physical screens normal, MagSafe and the front/lower USB-C monitor connected, and no device attached to the monitor's USB ports. Keep the lid open and the cable orientation, HDMI cable, and input settings unchanged. The fresh readiness checks are in the [dated record](../evidence/dev-147-usbdiag-boot-readiness-2026-08-28.md). This handoff permits one attended diagnostic selection, not a repeated test or permanent change.

1. When ready to leave this Linux session, run only `sudo reboot` in the desktop Terminal.
2. At the visible GRUB menu, press an arrow key to stop the countdown. Highlight `Arch Linux`, then press `e`. Do not send blind key presses through other boot screens.
3. Find the existing `initrd` line. Replace only the filename `initramfs-linux-asahi.img` with `initramfs-linux-asahi-dpalt-usbdiag1.img`. Keep the existing `/boot/` prefix and any other entry contents. The expected line is shown below; it is not a Terminal command.
4. Leave the `linux /boot/vmlinuz-linux-asahi ...` line and every kernel argument unchanged. Press Ctrl-x once to boot the edited entry. Esc cancels the edit. These keys follow the [GRUB menu-editor reference](https://www.gnu.org/software/grub/manual/grub/html_node/Menu-entry-editor.html).
5. After login, report whether each physical screen shows an image. Keep all cables, input settings, modes, and lid position unchanged. Allow one 30-second observation before the fixed-boot log capture described below. Do not reconnect, retry, change modes, or suspend.

```text
initrd /boot/initramfs-linux-asahi-dpalt-usbdiag1.img
```

If the menu, expected stock filename, or path differs, press Esc and stop this case. If startup passes the menu and reaches login without the edit, report that missed selection; do not start another test boot or use a Terminal `initrd` command. A failed test has only the reviewed recovery route below, not an automatic retry. If a safety-stop event occurs, stop immediately; do not wait 30 seconds just to collect more data.

The edit changes only this boot's in-memory entry. A normal unedited boot selects the stock driver image but leaves the candidate DTB installed and can lose external video. It is not full rollback. Keep the working DP image and both timestamped backups. Before restarting, make the existing private macOS recovery guide available without relying on Linux; no Recovery visit or rehearsal is required now. Its restore execution remains untested.

Save work. Confirm healthy internal display, matching kernel/packages, intact backups/recovery bundle, battery strictly above 50%, and David's attendance. Recheck that no downstream storage or other new USB device was added to the monitor. If its contents are unknown, hold; software absence does not clear that physical check.

Keep the lid open, same front/lower cable/port/orientation, MagSafe, HDMI, and monitor input settings. No mouse or storage test. Use one user-selected restart with the separately staged diagnostic image and unchanged kernel arguments. The GRUB menu-editor procedure applies only after D2 and readiness review. That handoff must name the newly verified diagnostic image; the old reference names the working DP image instead. No desktop `initrd` command and no blind menu input. This is a restart, not a cold-start test.

After login, first report whether both screens show an image. Leave cables and modes unchanged. Capture one fixed boot-ID, all-priority kernel-journal window from boot through a declared end after a 30-second observation. Preserve original fields/cursors and validate capture completeness; do not use warning-only filtering. Collect only reviewed identity/build-ID, USB enumeration, DRM/compositor, and power attributes. Never read partner `usb_mode` or sweep arbitrary sysfs files. Do not change tracing or logging settings to fill a missing capture.

Require the actual monitor hub `0bda:5411` and LG controls `043e:9a39` under the target USB controller for an enumeration success. Root hubs alone do not pass. Record display modes and both power sources, without claiming that a full battery proves isolated USB-C charging. Preserve full firmware diagnostics and the new boot's taint baseline; do not carry the old boot's taint value forward as a fresh result.

There is no physical reconnect, second boot, automatic correction, mode change, suspend, or live module swap in this case. Missing USB enumeration with otherwise healthy screens is the diagnostic question, not permission to retry. A new internal-screen failure, unexpected persistent external loss, charging regression, WARN/BUG/panic, coprocessor/IOMMU fault, or repeated timeout stops the case. Save evidence only if the machine remains responsive, then use the reviewed recovery route.

## Interpretation and acceptance

Assess capture validity separately from hardware behavior. Require both component start markers, verified diagnostic identities/target mapping, consecutive sequences, all earlier probe/initialization attempts, closed critical operation pairs, and a known collection boundary. Missing starts/tail, gaps, duplicate/restarted sequences, a cap marker, unmatched operations, or only a successful suffix make the capture inconclusive. A closed attempt with an explicit error is useful failure evidence, not a successful reproduction.

Consecutive sequence numbers detect interior loss, not a lost final suffix. Do not infer an absent late setter from a clean-looking prefix. A negative claim requires a later verified ATC record that closes the relevant ATC interval; otherwise, keep only positive closed-pair findings and classify missing late-setter evidence as inconclusive. A declared journal end alone does not supply that component-level closure. Do not add a device action or synthetic callback to obtain it.

For a late actual setter, require strict non-overlap: `core_init.end → ATC HOST setter.begin → ATC HOST setter.end(ret=0)`. If intervals overlap, do not infer the order. `dwc3_host_init()` can create a child whose probe completes later; its return alone is not an HCD-completion marker. Use target-scoped pairs and the complete sequence, not timestamp proximity alone to label a caller.

| Observation | Conclusion / next boundary |
|---|---|
| First early call has no handle and returns 0; a later observed HOST setter follows core init | Positive software sequence confirmed. Hardware latching and causal effect remain unproved. |
| Same sequence, but hub/controls appear | Startup behavior varies or instrumentation/packaging changed timing. Not a fix. |
| Valid handle appears only after an earlier failed attempt | Attribute it to the retry; do not relabel it the original first attempt. |
| Unexpected order in positive closed pairs, or no late setter within a separately closed ATC interval | Review actual return/deferred-probe paths; do not add a fix automatically. Without ATC tail closure, a missing late setter is inconclusive. |
| Missing/invalid trace or wrong module identity | Inconclusive; preserve evidence and redesign before another boot. |
| New safety-stop event | Test failure; stop and recover. Do not continue for more data. |

Even complete traces plus both screens and USB are only one diagnostic result. Full Gate 4b, firmware review, Gate 5 reliability, rollback proof, and permanent integration remain separate. No `appledrm` workaround is justified by the existing FIFO observation.

## Offline QA before any boot approval

Review the source diff against the exact pinned base. Check that every original hardware operation, call count/order, lock boundary, error/no-op path, and return behavior remains intact. Logging must not make a formerly ignored failure actionable. Verify all print formats and record-length bounds; no raw data is permitted.

Use parser fixtures for null and error handles, first-attempt failure followed by retry, independent probe generations, late and overlapping setters, asynchronous child probing, missing starts/tails, sequence gaps/duplicates, caps, malformed JSON, wrong controller/revision/build ID, and explicit failed operations. Include fixtures that remove the final complete ATC setter pair or final cap marker while leaving prior sequences consecutive; neither may support a negative late-setter claim. Fixture results do not simulate or prove hardware behavior. Check the cap under concurrent emission without changing driver synchronization.

The new image helper needs real archive-tool round-trip/delta checks, including the no-change reduced-index control and early/main archive boundaries, plus real dependency resolution. Add failure fixtures for unsafe paths, symlinks/hardlinks, existing outputs, drift, missing index inputs/dependencies, unexpected files/configuration, and incomplete builds. Keep real-tool failures distinct from parser fixtures. No hardware mocking may be used as evidence of display or USB safety.

Run focused tests only inside the reviewed sandbox. The earlier aggregate suite has five recorded failures and includes a fixture that attempted a credentials-path write. Do not rerun it unrestricted or call this a release/full-suite pass. New failures block release unless explicitly waived; existing failures remain visible. Use the repo's SWE → QA → Review loop, with at most three correction rounds.

## Rollback and retained state

Before staging, rollback is simply not selecting the private experiment. After staging but before boot, leave the new image unselected. Neither state changes normal startup. Do not delete evidence to undo preparation.

After a diagnostic boot, a normal unedited restart selects the stock driver image; it does not restore the original DTB and may leave external video unavailable. The known working DP image remains a separate one-time selection option after review; never compensate with a live swap. The main plan's [full rollback gate](dev-147-m2-displayport.md#gate-6--prove-full-rollback-then-retain-the-evidence) restores the original DTB and verifies a stock boot. Keep both timestamped backups and the offline macOS bundle. macOS restore execution remains untested. No cleanup, package install, persistent boot change, or live checkout edit is part of this design.

## Decision Log (LIVING)

- 2026-08-28: David cleared the physical readiness hold: MagSafe/front-lower monitor connected, no other active work, both screens normal, and no downstream USB device. Fresh preflight passes, with protected root-only bytes still evidenced by his D2 validator. Save one explicit desktop-to-GRUB handoff using `initramfs-linux-asahi-dpalt-usbdiag1.img`; keep kernel arguments, normal boot, cables, and modes unchanged. One attended restart only. No diagnostic startup or USB result has occurred at this checkpoint.

- 2026-08-28: D2 user-run staging PASS. The complete transcript matches all 32 protected and eight proof records. The root-owned mode-0600 diagnostic image is 19,647,739 bytes; the check directory is root-owned mode 0700. Accept the helper's protected post-checks from David's validated execution, not an independent root-log or image-byte read. Preserve sealed evidence and the unselected image. D3 requires fresh physical readiness and explicit approval; no boot is authorized.

- 2026-08-28: D2 preparation passes final independent review and all 38 isolated tests. Preserve genuine RED, the missing-`/dev/fd` correction, and the EXIT-trap local-scope defect and regressions. The final private copy differs in exactly three fixed assignments; its production preflight has not run. Hand off staging only, preserve all existing images and evidence, and keep D3 separately gated.
- 2026-08-28: David approved plan reconciliation and the recommended D2 preparation. Implement and test a new staging-only helper without changing the image, old operational helpers, live checkout, boot files, packages, or drivers. Preserve the frozen D1 archive and use fresh private outputs. Stage only through David's reviewed command; keep D3 and all release/upstream actions separate.

- 2026-08-28: Design observations in the two device drivers, not a behavior correction. Reason: source order is established, but this boot's actual sequence and hardware causality are not.
- 2026-08-28: Record all first-probe and automatic retry generations, plus null/error booleans. Reason: a later `PROBE_PENDING` attempt can already hold a PHY or error pointer.
- 2026-08-28: Retain bounded native INFO/JSON logging without deferred printk or live tracing controls. Reason: the exact module export boundary and observer timing must remain explicit.
- 2026-08-28: Propose adding the missing DWC3 glue only to a distinct diagnostic image, with no explicit preload or runtime hook. Reason: both drivers must be observable at first probe; earlier availability is a known timing confound. Whole-image and round-trip review must pass before staging.
- 2026-08-28: Require a separate reduced index-generation root with pinned missing inputs and a no-change control. Preserve builtin indexes and archive boundaries. Reason: the working archive is not a complete depmod input tree; bare regeneration could alter unrelated boot content.
- 2026-08-28: Complete D0 after independent source/measurement, image/rollback, and safety review. Require an implementation revision at first probe and explicit handling of missing final records. Reason: a later module identity or consecutive prefix does not prove capture completeness. D1 remains subject to separate approval; D2 and D3 remain separate gates.
- 2026-08-28: David approved D1 with “yes, proceed” after the explicit offline implementation/build handoff. Start with pinned-input and actual sandbox checks. Keep all outputs in a fresh private directory. No installation, staging, live driver action, or reboot is authorized.
- 2026-08-28: Pause D1 after three production-sandbox QA failures. Retain the namespace assertion's incomplete evidence; do not call it either an escape or a pass. Save all source/fixture drafts, input pins, and failed runs. Ask before a narrow correction and one further isolation round. Do not build, stage, or boot while containment is unproved. The monitor may be disconnected during this offline hold; its current physical state was not asserted.
- 2026-08-28: David approved one narrow correction and one additional isolation QA round with “yes, go ahead!”. R4 passed after recording actual namespace results and accepting only the reviewed denial codes. Preserve the earlier three failures and their unknown errno. Resume the already approved offline D1 scope in fresh private outputs; implementation/build/image gates remain unfinished. This R4 run made no driver, image, or hardware change. D2 and D3 remain separately gated.
- 2026-08-28: Prepare the public source checkpoint on a clean branch, while preserving the original private branch and both frozen checkpoints. Publish authored drafts and fixtures with explicit unimplemented/unbuilt labels. Keep raw device/Linear records, tool manifests, package binaries, images, and backups private; public machine placeholders cannot substitute for the tested operational originals.
- 2026-08-28: The fresh private continuation passed the same isolation checks, then ran the frozen trace/image stubs once to establish RED. All reported errors are NotImplementedError; inputs stayed unchanged and neither run timed out. Proceed to implementation and independent QA, not staging or hardware testing. R4's historical result remains a separate record.
- 2026-08-28: Complete the source/build, import/logging, and real no-change controls. Preserve the newly observed archive format without normalizing its raw bytes. Allow only the verified header-only weakdep scratch file outside the image. The base image and seven indexes reproduce exactly; all 199 binary-only lookups pass. Use raw-record preservation and stdout-only selected extraction instead of general archive extraction. Proceed to private diagnostic assembly and delta QA. D2/D3 remain unauthorized.
- 2026-08-28: Complete offline D1. Retain the failed assembly and baseline alias-dump check. Prove that symbol-index drift is limited to ordering priorities, and preserve the original symbol bytes. Correct only kmod alias-key normalization; keep raw symbol keys and multiplicities. All 55 assembly fixtures and the real 413-command candidate run pass. The private image has exactly the approved four changes and all 200 binary-only lookups pass. Preserve the original fixture-order miss and genuine later RED runs. Next requires approval for D2 staging preparation; no staging, live load, reboot, or hardware acceptance is implied.
