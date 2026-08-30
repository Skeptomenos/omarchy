# Apple DCP crash-flag observation

This diagnostic checks the external DCP's stored crash flag after the LG 27 recovery failure. It does not restore video.

## Safety boundary

The public helper is deliberately unbound and refuses live use. Only a separately reviewed private copy may be handed to David. Do not run the source helper with sudo or remove its identity guards.

The proposed live operation temporarily instruments the kernel. It creates one uniquely named probe and one private trace instance, restricts recording to its own process, then opens and closes the verified external connector's `ColorElements` file once. It never reads that file. The callback allocates a sequence-reader object; it does not call the display-data callback until a read occurs. No modeset, compositor reload, firmware command, cable action or reboot is requested.

Kernel, boot, installed-module hash, loaded module notes, expected display state and pre-existing mount/file identity must match. Missing paths or rejected probes stop the case. The helper does not mount debugfs, install dependencies, widen permissions or retry another target.

Only the crash byte and connector type are fetched. No pointer, string, stack or framebuffer payload is requested. The exact installed binary binds the probe offset and field layout. This is not a portable diagnostic for other kernels.

## Why the original atomic-test proposal changed

A separate process cannot submit an atomic TEST_ONLY request while Hyprland owns DRM master. Root does not bypass that ioctl gate. Non-master connector queries are cached and do not reach the intended Apple callback. Hyprland's output-management test handler is a success-returning stub, not a hardware test. See the [pinned DRM gate](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/gpu/drm/drm_ioctl.c) and [Hyprland handler](https://github.com/hyprwm/Hyprland/blob/5c9377c15f85c50648f35ca5a213754f95b93ca0/src/protocols/OutputManagement.cpp#L351).

The [driver-specific open callback](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/gpu/drm/apple/connector.c#L60) provides a smaller observation trigger. It checks the current flag rather than causing a new atomic rejection. No DRM ownership transfer is needed.

## Result and cleanup contract

- Exactly one matching external-connector event, the expected process, valid field layout and zero loss are required.
- A valid flag value of one establishes that the rejection guard is set. It does not establish whether the poweroff timeout or an RTKit crash set it.
- Zero, missing or invalid data does not establish a fix or authorize a retry. Numeric probe-fetch failures can resemble zero.
- Definitions are global even when recording is instance-local. The helper must append only its exact own registration and removal records. It must never truncate `kprobe_events`.
- Cleanup stops its own recording, disables its event, closes descriptors and removes only verified owned objects. Measurement has a 10-second cooperative deadline. Each cleanup operation has a separate 2-second cooperative deadline. These are not hard guarantees for an uninterruptible kernel call. A cleanup error prevents a successful completion.
- Signal handling and a short deadline cannot guarantee cleanup after SIGKILL or a system crash. The private result directory retains exact owned-object cleanup metadata before instrumentation begins, and its path is printed. This metadata is for reviewed recovery; it is not an automatically executed fallback. Never replace it with global trace clearing.

The kernel's [instance PID filter](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/kernel/trace/trace_events.c#L668) precedes fixed numeric fetches. A `common_pid` event filter alone does not provide that ordering.

## Offline development

The helper and adjacent unittest file use only Python's standard library. Dataclasses, strict parsers and unittest are the existing no-install exception to Pydantic/pytest tooling. Ruff and strict type-check results are not implied.

Run tests only through the project's reviewed private sandbox. The sandbox excludes real `/sys`, `/proc`, `/run`, home directories and display devices. Its fixtures validate parsers, refusal paths and ownership/cleanup logic; they do not emulate tracefs or prove live-kernel safety. The [main plan](../../../docs/plans/dev-147-m2-displayport.md#minimum-remaining-path-living) owns the current release decision.

See the [preparation and test record](../../../docs/evidence/dev-147-crashflag-preparation-2026-08-30.md). Keep [the failure record](../../../docs/evidence/dev-147-lg27-spontaneous-dropout-2026-08-30.md) separate from preparation and any later user-run result. [PR #582](https://github.com/AsahiLinux/linux/pull/582) remains a recovery-fix candidate, not a tested M2 fix.
