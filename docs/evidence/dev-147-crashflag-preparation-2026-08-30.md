# DEV-147 — crash-flag diagnostic preparation, 2026-08-30

## Outcome and boundary

A diagnostic is prepared for the [LG 27 recovery failure](dev-147-lg27-spontaneous-dropout-2026-08-30.md). It asks whether the external DCP's stored crash guard is set. It does not identify the writer or explain the initial FIFO/link loss. This record covers offline preparation only. No live probe, target open, sudo command, display change, driver load, boot-file write, reconnect or reboot ran.

## Why the trigger changed

A separate atomic TEST_ONLY ioctl requires DRM master; root does not bypass the gate while Hyprland owns it. A non-master connector query does not force the driver callback. The pinned Hyprland output-management test handler returns success without performing a DRM hardware test. Do not treat it as an acceptance result.

The selected trigger is one O_RDONLY open-close of the external connector's ColorElements debugfs file, with no read. Pinned source shows that open calls single_open; the display-data callback runs only on a read. Metadata preflight uses O_PATH and does not invoke this callback. No compositor, firmware or mode-setting operation is requested.

Source and matched installed-module disassembly bind the probe to appledrm:chunk_color_open+0x1c. The loaded-module GNU note and installed-module SHA match the saved boot. The probe reads only the crash byte and connector type through the reviewed binary layout. Global readback renders the offset as +28. The u8 trace field prints decimal. Numeric fields are packed at offsets 16 and 17. The profile lists the unique event name without its group. These exact source rules correct the fixtures; they are not live tracefs observations.

## Containment and interpretation

The public helper contains an invalid boot binding. The private copy must differ only in that literal and must refuse kernel, boot, installed-module, loaded-note or display-state drift. Existing tracefs/debugfs mounts and target eligibility remain unverified until a separately approved user-run preflight. Missing paths, rejected registration or unexpected readback stop the diagnostic; there is no fallback probe or mount.

One unique probe and one new trace instance are used. The instance PID filter is set before event enable and precedes fixed numeric fetches. Only owned registration/removal records may be appended to global kprobe_events; truncation is forbidden. The buffer request is 16 KiB per CPU, with readback and CPU bounds.

One event, the expected PID, external connector type, valid numeric layout and zero loss are required. A value of one establishes the current guard. It does not distinguish a poweroff timeout from another writer. Zero does not establish a clear flag: numeric fetch failures can resemble zero.

Measurement has a 10-second cooperative deadline. Cleanup keeps signal handling active and gives each operation a separate 2-second cooperative deadline. It attempts other eligible owned operations after a failure. It verifies removal before reporting success. SIGKILL, power loss and uninterruptible kernel calls defeat any guarantee; exact owned-object recovery metadata is saved and its path printed before mutation. Never clear global tracing state or blindly rerun.

## Offline checks

The preserved RED used an intentionally unimplemented stub. Fresh probe `run-iur25tiz` passed. RED `run-m0t4__60` exited 1: 14 methods, 12 expected “not implemented” errors and two negative-case passes. Independent saved-result QA accepted this as missing-feature evidence, not validated rejection logic.

The sole GREEN `run-hypwc72z` ran a fresh internal isolation probe, then:

```text
/usr/bin/python3.14 -I -S -B /inputs/crashflag/test_crashflag.py
```

Result: 21 tests passed in 2.004 seconds; outer and workload exit 0; no timeout; all 587 read-only bindings unchanged. This includes the unchanged 583-entry runtime. Independent retained-result QA and pre-execution source/safety review passed without a rerun.

Frozen helper SHA-256: `60cc9f3f3ebd233931500ebd7049dd8f5a09fef4089e0addb65325e9d8ef638f`. Tests: `cf0238d57ddee596cc548471abf3146e67f23dd2436d725cebb70234f1f4e767`. Coverage includes strict identity/format parsing, bounded nofollow access, exact append/ownership/collision guards, one-open ordering, partial cleanup, a real cooperative SIGALRM and trace redaction. The 14 RED method names remain, but some assertions changed; they are not byte-unchanged.

A private operational copy changes only the boot-hash literal. Independent final review verified that exact single-literal delta and its saved-boot binding, and found no blocker to a conditional manual handoff. It remains unexecuted and unreleased pending fresh readiness. The public source remains unbound. Private source/result files are regular, single-link and mode 0600 in mode 0700 directories. The saved trace would contain a raw-byte fingerprint plus clearly labelled sanitized text, not raw probe-site addresses.

The reviewed sandbox excludes real proc, sys, run, home, boot and display devices. Only private work/tmp are writable. Tests use real temporary files plus strict parsers; they do not emulate a live kernel or prove probe registration and cleanup. The unchanged launcher is 3544e55bd504019344b6358e1829686759abecc5f9f4c8534901290df963851e. The unchanged v6 runtime manifest is 6f999183c660b49c3ba665a9bc9b22d316beca81cf01a9b4a403f5c1435a9391. No dependencies were added or repinned.

Pre-execution review corrected a nofollow-incompatible /proc/self path, global canonical/profile/packed-format assumptions, the zero-reading overclaim and signal-ignoring cleanup logic. The retained RED is a stub result, not failing hardware. Later added tests are regression coverage, not separately observed RED. No old image or accepted suite was rebuilt or repeated. The historical aggregate-suite real-home write hold remains.

## Next decision

Stop at the manual boundary. Reconfirm internal-screen health, failed external setup, saved work, open lid, MagSafe, battery above 50%, empty monitor USB ports and attendance. Review one exact user-run command and its cleanup limit; no automatic retry follows. If the crash guard is established, review a contained candidate based on existing PR #582. That needs separate build/boot review and cannot be claimed as a fix for spontaneous loss or cable compatibility.

The [helper contract](../../dev/apple-dp-altmode/crashflag/README.md) and [main plan](../plans/dev-147-m2-displayport.md#minimum-remaining-path-living) own use and approval. Prior failure and success records remain unchanged. No upstream submission is authorized.

## Primary source references

- [Driver open callback](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/gpu/drm/apple/connector.c#L60) and [sequence-reader open](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/fs/seq_file.c#L573).
- [DRM ioctl master gate](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/gpu/drm/drm_ioctl.c) and [Hyprland test handler](https://github.com/hyprwm/Hyprland/blob/5c9377c15f85c50648f35ca5a213754f95b93ca0/src/protocols/OutputManagement.cpp#L351).
- [Probe canonical/profile serialization](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/kernel/trace/trace_kprobe.c#L1300), [numeric types and packed fields](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/kernel/trace/trace_probe.c), and [instance PID filter](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/kernel/trace/trace_events.c#L668).
- [Existing recovery-fix PR #582](https://github.com/AsahiLinux/linux/pull/582).
