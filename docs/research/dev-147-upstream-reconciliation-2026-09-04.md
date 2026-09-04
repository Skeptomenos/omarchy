# DEV-147: reuse upstream USB-C work

**Assessed:** 2026-09-04. **Machine:** M2 MacBook Air, J413/T8112. **Scope:** source assessment, not a kernel release or hardware acceptance.

Use the complete, pinned Asahi `fairydust` kernel as the next DisplayPort prototype. Carry the corrected local AFK service-reuse patch and the pending upstream PR582 timeout fix. Replace our reduced device tree and TIPD hotplug backports with their upstream implementations. Keep the current 7.1.6 recovery assets and evidence.

The proposed two-patch stack applies cleanly to the six affected files from `fairydust`. The existing extracted-function lifecycle harness passes, with all four negative controls failing as intended. This does **not** establish a complete kernel build, module compatibility, a bootable image, or working hardware. The [machine-readable source receipt](../evidence/dev-147-upstream-reconciliation-2026-09-04.json) records pins, hashes, patch order, outputs, and limits. The [plan](../plans/2026-09-04-dev147-upstream-reconciliation.md) owns follow-up decisions.

## Choose the baseline

Here, upstream includes Asahi development branches and submitted patches. It does not mean all work is in mainline Linux or an Arch package.

| Pinned Asahi Linux branch | Version | Relevant state | Decision |
|---|---|---|---|
| `asahi` at `77cb8f24c2381a8abb7272d7bbdec548d6426a8a` | 7.1.9 | Lacks fairydust DP enablement. Retains both investigated AFK/timeout behaviors. | Release reference. |
| `asahi-wip` at `ca9a850f237f98949996eefb8980371a5d58c886` | 7.1.12 | Exact ancestor of the pinned fairydust tip. | Alternative base only if maintaining a separate DP backport is necessary. |
| `fairydust` at `b8810ad6442699f610984f3eceea2e3234a50b77` | 7.1.12 | Adds J413 DP setup and HPD forwarding. Asahi GPU is not gated as broken. | Preferred next DP prototype, still experimental. |
| `asahi-wip-7.2` at `236788cd2602a24c703fe7bdaddaf73ef77d2027` | 7.2.2 | Has Apple USB4 development work, lacks the fairydust DP wiring, and gates the Asahi GPU driver with `depends on BROKEN`. | USB4 donor/reference; unsuitable as the immediate Omarchy desktop baseline. |

Fairydust is exactly 11 commits ahead of the pinned `asahi-wip`, with zero commits behind it. Four additions serve J413: [CD321x data-status tracking](https://github.com/AsahiLinux/linux/commit/9b65351d9cf850ec8273f138f04480dc1e93f15a), [DRM hotplug forwarding](https://github.com/AsahiLinux/linux/commit/d02d57a6c830ed5f2934490aa6bb35df0db4d376), [M2 DT enablement](https://github.com/AsahiLinux/linux/commit/f216a6e787f89b7545e28494f624e0ce997900ea), and the [ATC1 power-domain workaround](https://github.com/AsahiLinux/linux/commit/1069f56d6225fbd16cea99d5e9988163465f207b). The remaining additions target other boards. Taking the full branch avoids another stripped backport, but its HPD and DT commits remain experimental. [Pinned comparison](https://github.com/AsahiLinux/linux/compare/ca9a850f237f98949996eefb8980371a5d58c886...b8810ad6442699f610984f3eceea2e3234a50b77).

The GPU gate in 7.2 is deliberate: [Kconfig](https://github.com/AsahiLinux/linux/blob/236788cd2602a24c703fe7bdaddaf73ef77d2027/drivers/gpu/drm/asahi/Kconfig#L19), [introducing commit](https://github.com/AsahiLinux/linux/commit/97b22d1355086a88447a048fc78212769ca5f41c). Removing that gate without resolving its cause is not a desktop integration strategy.

## Every local patch

Paths below are relative to `dev/apple-dp-altmode/`. The receipt contains full SHA-256 values. “Drop” means exclude from the new runtime stack; retain the historical files and evidence.

| Patch | Decision | Reason and reuse |
|---|---|---|
| `t8112-j413-dp-altmode.patch` | **Replace** | Reduced fairydust backport. Use the pinned upstream M2 DT, which also includes SIO/audio and the ATC power workaround. Build it with its matching kernel. |
| `tipd-cd321x-hpd.patch` | **Replace** | Both data-status tracking and DRM hotplug forwarding already exist in fairydust. Do not apply a second copy. |
| `afk-service-reuse/afk-service-reuse.patch` | **Keep, experimental** | Novel local correction remains absent from all inspected branches. Retain the corrected quiescent-retirement implementation and its lifecycle harness. Hardware acceptance remains open. |
| `afk-service-reuse-pr582/pr582-timeout.patch` | **Keep one application** | Adapted form of Francisco Vargas's pending PR582. Upstream branches still latch the crash flag on a poweroff timeout. Preserve attribution; this is borrowed work, not a local invention. |
| `pr582/pr582-upstream.patch` | **Keep provenance; drop duplicate application** | Original upstream format patch for the same timeout change. Keep the author and commit record. Apply only the adapted patch above in this proposed stack. |
| `usbdiag/kernel/usbdiag1.patch` | **Drop from new stack** | Superseded instrumentation with a faulty target-name/path guard. It is neither a USB fix nor a valid new diagnostic baseline. |
| `usbdiag/kernel/usbdiag2.patch` | **Defer** | Corrected DWC3/ATC diagnostic guard. Useful only for a specific unresolved USB question; keep outside the normal kernel and refresh against the selected source if needed. |
| `contributions/pr289-partner-absence.patch` | **Defer to Omarchy diagnostics** | Corrects an interpretation: absent Type-C partner state does not prove a cable is physically absent. It is a userspace diagnostic change, not port enablement. Review against the current command before applying. |

The AFK allocator and teardown files are byte-identical across `asahi`, `asahi-wip`, `fairydust`, `asahi-wip-7.2`, and `bits/200-dcp` at `52f0b76aaae7b9a1cc2100f4a9b33257b450d5c0`. Allocation still increments a fixed-capacity counter. Teardown retains channels to handle late replies, so reclaiming every disabled channel is unsafe. The local patch adds controlled reuse, including pending-command, owner, and debugfs lifetime handling. [Pinned allocator](https://github.com/AsahiLinux/linux/blob/b8810ad6442699f610984f3eceea2e3234a50b77/drivers/gpu/drm/apple/afk.c#L262), [local safety correction](../evidence/dev-147-afk-reuse-safety-correction-2026-09-02.md).

All five source views also retain the 50 ms poweroff-timeout crash assignment. PR582 removes that assignment, adds a warning, and keeps the wait and return behavior. It does not disable the real RTKit crash path. PR582 was open with no reviews at this assessment. [Pinned timeout code](https://github.com/AsahiLinux/linux/blob/b8810ad6442699f610984f3eceea2e3234a50b77/drivers/gpu/drm/apple/iomfb_template.c#L929), [PR582](https://github.com/AsahiLinux/linux/pull/582).

## Every local branch and supporting component

These are Omarchy research or delivery branches. Their commits cannot be wholesale rebased onto the Linux kernel repository. Rebase the small **kernel patch series**; selectively retain the separate Omarchy delivery work.

| Branch at assessment | Keep | Exclude or replace |
|---|---|---|
| `codex/dev-147-m2-dp-altmode` at `bb5750c8e74fcea6bfd3dc5027f0b3b6a54b6f73` | Initial hardware discovery and recovery history. | Replace its two backports with fairydust. Do not merge the whole prototype branch. |
| `codex/dev-147-m2-dp-altmode-public` at `77ef92e394905ff60f6bde82d81ea4ca670be59d` | Public source/provenance archive. | Duplicated backports and obsolete diagnostic variants. Its `LOCAL_ONLY` placeholders are intentional; it is not an executable deployment recipe. |
| `codex/dev-147-t1-trace-offline` at `e670225b74e0c3115cc0ada93396c88c53b47527` | Trace interpretation and instrumented experiment records. | No additional proven functional fix to carry. Keep trace-only module/image variants out of the new baseline. |
| `codex/dev-147-t1-image-offline` at `cfcc45d92661a7539c0290babe3220f87ac14e31` | The corrected AFK patch, one PR582 patch, their tests, and failure evidence. This assessment branches from this snapshot. | Do not carry every historic image builder and staged candidate into the new runtime. |
| `codex/dev-147-m2-displayport-opt-in` at `b45948e129a5197d7174aa2c4c870134b03fdff6` | Separate-image delivery, integrity checks, rollback design, and tests as requirements. | Replace the fixed 7.1.6 package/image/boot-bundle assumptions. Review and adapt its update guard before changing the package stack. |

The remaining local files fall into these operational groups:

| Component | Treatment |
|---|---|
| Original `bin/omarchy-dev-dp-altmode`, standalone TIPD module build, copied one-boot mkinitcpio config | Archive the old recipe. Do not replay fixed package identities, EFI placeholders, or copied hooks on a new full kernel. |
| AFK and PR582 exact-source build, module, initramfs, staging checks | Keep their invariants and regression evidence. Adapt deliberately to the new complete kernel package; do not silently relax historical source pins. |
| D/E/T1 early-USB and TIPD diagnostic images | Archive as controlled experiments. Early driver-loading changes affect timing; they are not established fixes. |
| Crash-flag probe, USB event capture, PM recorder, TIPD trace parser | Retain the diagnostic methods and tested parsing, including dynamic controller mapping. Rebind source/build/boot identities before reuse. Enable instrumentation only to answer a named question. |
| Candidate-specific delivery wrappers | Reuse required backup, authentication, non-default image, and rollback properties. Prefer one tested manifest-driven path when implementing the next package. Avoid another set of copied per-candidate wrappers. |

The opt-in integration guard blocks changes to `linux-asahi`, `m1n1`, and `uboot-asahi`. Its current logic is tied to the existing custom boot stack. A new kernel requires a coherent Image, modules, DTBs, initramfs, and m1n1 stage-2 boot bundle. Replacing only the initramfs or dropping a fairydust DTB onto the old kernel does not perform this migration.

## What the full device tree adds

The upstream M2 DT enables the external DCP path, its IOMMU/DART and mailbox, the selected DP PHY/crossbar, and display audio through SIO. Our reduced backport omitted some of that work. Use the upstream definitions together. [Pinned M2 DT](https://github.com/AsahiLinux/linux/blob/b8810ad6442699f610984f3eceea2e3234a50b77/arch/arm64/boot/dts/apple/t8112-jxxx.dtsi#L125).

Audio still needs verification. `dpaudio1` uses SIO DMA channel `0x66`. The kernel requires bootloader-supplied `apple,sio-firmware-params`. Upstream m1n1 v1.6.1 already prepares those mappings and enables SIO after successful setup; the installed package reports 1.6.1-1. Verify the actual booted DT, firmware preparation, `CONFIG_APPLE_SIO`, and `CONFIG_DRM_APPLE_AUDIO`. A package version alone does not prove the loaded boot bundle or firmware state. [SIO reader](https://github.com/AsahiLinux/linux/blob/b8810ad6442699f610984f3eceea2e3234a50b77/drivers/dma/apple-sio.c#L744), [m1n1 setup](https://github.com/AsahiLinux/m1n1/blob/06a4601a351ebfd1abb6abba9a44c34e40d94776/src/kboot.c#L2189).

The `apple,always-on` property keeps the ATC1 common power domain powered. It is a workaround for incomplete PHY suspend handling, not proof of working suspend or acceptable battery use. SIO also retains incomplete sleep-state handling. Measure both. The DP wiring still selects the lower/front port through `usb-pd@3f` and PHY1; this is not both-port DP routing. [Power-domain implementation](https://github.com/AsahiLinux/linux/blob/b8810ad6442699f610984f3eceea2e3234a50b77/drivers/pmdomain/apple/pmgr-pwrstate.c#L284).

## Preserve the useful local evidence

The original task made useful progress. It established native external video and separated failures at different protocol layers. The next task should use those boundaries:

- [AFK exhaustion](../evidence/dev-147-afk-service-exhaustion-2026-09-02.md): reconnects consume the fixed service capacity. The local lifetime fix still addresses a real unmerged gap.
- [Pre-DP reconnect failure](../evidence/dev-147-tipd-failed-reconnect-2026-09-04.md) and [host-role rejection](../evidence/dev-147-tipd-host-role-rejection-2026-09-04.md): a failure can occur before HPD or AFK allocation. Neither display patch claims to fix this.
- [Generation-2 display failure](../evidence/dev-147-afk-reuse-generation2-dcp-crash-2026-09-04.md): Type-C, DP, HPD, xHCI, and new AFK channels succeeded, but the external DCP had `crashed=1` and atomic commits returned `EINVAL`. The timeout is the leading writer candidate; the write itself was not traced.
- [Combined offline candidate](../evidence/dev-147-afk-pr582-combined-offline-2026-09-04.md): retain it as a 7.1.6 control. The user later reported image staging PASS in the original task. This is not a successful boot or reconnect acceptance result.

An independent J413 report describes fairydust link bouncing with a multiport adapter and eventual AFK capacity errors. This supports the relevance of the exhaustion investigation. It does not identify the cause of the first link drop. [Asahi issue 571](https://github.com/AsahiLinux/linux/issues/571).

## Integration sequence and remaining work

The already-staged 7.1.6 AFK+PR582 candidate can supply one bounded, attended control run while the full fairydust build is prepared. That run is optional for attribution; it should not block source integration or start another series of old-baseline image iterations. Fairydust changes the DT, audio, power handling, and kernel patch level, so the retained control can help separate regressions later.

1. **Build the minimal combined DP stack.** Start a Linux integration branch at pinned fairydust and apply AFK reuse followed by PR582. Use the distro kernel configuration as input, check new dependencies, and build the kernel, modules, and J413 DTB. Run DT checks and verify the desktop GPU configuration. Produce a versioned package and coherent boot assets. Preserve the current recovery/control package. Source composition is complete; this full build is still open.
2. **Prove stable external video before broadening the stack.** Use a new boot and the existing bounded reconnect procedure. Exceed the old service-exhaustion window, vary cold/hot attach, test both existing monitors, and retain the first failing layer when a run fails. Check AFK lifetime, timeout events, atomic commits, internal-display health, and recovery. A fairydust-only control is useful if the combined result needs attribution; do not repeat already answered diagnostic experiments without a new question.
3. **Close the ordinary USB-C gaps.** Validate USB2/USB3 data and charging separately, including simultaneous video/data/power. DEV-163 owns the monitor-hub data-loss case. Check DP audio/SIO, both cable orientations and both ports. The second-port DP path needs routing work or a newer upstream implementation; the current static DT does not supply it. Test suspend/resume and measure power drain with devices connected and disconnected.
4. **Add USB4 from the existing upstream series.** Assess the complete series and prerequisites against the GPU-capable baseline. Use a separate experimental integration branch. If the dependency cost becomes a broad kernel port, prefer a later integrated Asahi base over creating a second maintenance project. Re-run the DP/USB/power regression matrix when USB4 is combined.
5. **Reverse engineer only the remaining gaps.** Use targeted firmware traces or a known-good macOS comparison for a demonstrated unresolved boundary. Candidates include initial role/DP entry failures, both-port routing, unsupported tunnel types, and power-state transitions. Do not reimplement the existing controller or repeat broad register discovery.

Sven Peter's August 30 USB4 series already supplies Apple ACIO support. It needs the CIO reset controller, ATC USB3-over-USB4 support, DART aperture handling, the CD321x Thunderbolt VDO correction, and Thunderbolt capability-read fixes. Porting only `drivers/thunderbolt/apple.c` or the DT nodes omits that dependency chain. The stated scope is inter-host connections and USB3 tunneling. PCIe and DP tunneling remain unfinished. [Original 19-patch cover letter](https://lwn.net/Articles/1091412/).

The inspected USB4 driver refuses suspend with active connections. Treat suspend as an explicit unresolved capability, not a test that this branch is expected to pass. [Pinned suspend guard](https://github.com/AsahiLinux/linux/blob/236788cd2602a24c703fe7bdaddaf73ef77d2027/drivers/thunderbolt/apple.c#L970).

DP Alt Mode and DP tunneling through a Thunderbolt/USB4 dock are different paths. Success with a direct USB-C display proves only the former. The machine's hardware target is also bounded: Apple specifies one native external display up to 6K at 60 Hz, two Thunderbolt/USB4 ports, and USB 3.1 Gen 2. Use those limits for acceptance. [Apple specifications](https://support.apple.com/en-us/111867).

## Verification receipt

The source assessment used `git ls-remote`, local Git branch and patch inventories, immutable raw source downloads, and the pinned GitHub comparison. Sources and scratch compositions are retained at `/home/david/o/.dev147-stage/upstream-assessment-20260904/`. The accepted full 7.1.6 source tree and both original worktrees were left unchanged.

The [DEV-147 handoff](https://linear.app/helmus/issue/DEV-147/usb-c-displayport-external-monitor-unavailable-on-m2-macbook-air#comment-7683faf1) records this recommendation without closing the issue. Recheck moving upstream heads when implementation starts; retain these immutable pins to reproduce the assessment.

For both fairydust and the alternative 7.2 source, sequential `git apply --check` and application succeeded. Each composition changes six files, with 215 insertions and 47 deletions. The alternate test establishes patch portability only; it does not override the 7.2 baseline objection.

The existing AFK test module extracted functions from the new pinned files and rendered its existing C harness. It compiled with `cc -std=c11 -Wall -Wextra -Werror -Wno-unused-parameter`. The historical test entry point's 7.1.6 source pin was preserved; its full entry point was not claimed to pass on a different source tree.

| Harness mode, on both sources | Exit | Result |
|---|---|---|
| `stock` | 1, expected | Fixed service capacity reached at synthetic generation 8. |
| `unsafe` | 1, expected | Detects erasure of a disabled slot with pending work. |
| `unsafe-send` | 1, expected | Detects stranded retirement after a post-teardown command. |
| `unsafe-race` | 1, expected | Detects teardown between reserve and send. |
| `candidate` | 0 | Opted-in quiescent service reuse passes. |

The harness uses extracted functions and kernel stand-ins. It cannot prove real scheduler/locking behavior, firmware compatibility, module ABI, or hardware correctness. Full kernel/DTB builds and new hardware tests were not performed in this assessment. No boot, package, or live Omarchy configuration changed.

Repository checks: command metadata passed for 455 commands, and the shebang-aware script syntax sweep passed. `./test/all` returned 1. Four of 235 shell test files failed: `config-test.sh`, `unowned-system-paths-test.sh`, and `zram-package-contract-test.sh` could not find the external `omarchy-pkgs` checkout; `runtime-smoke-test.sh` observed three IPC registrations for two screens. The CLI suite passed. These failures concern the existing checkout/environment; this assessment changes documentation and a source receipt only. The full repository gate is not green. Logs are retained in the scratch evidence directory, and the receipt records the log hash.

Independent verification returned **PASS for the source assessment**, with no blocking findings. Fresh downloads reproduced both compositions and every lifecycle outcome. The reviewer verified inventory, pins, source dependencies, links, and the disclosed QA failures, and reran metadata and syntax checks. Independent results and their hash are retained in the source receipt. This verdict does not cover a complete kernel build or hardware acceptance.
