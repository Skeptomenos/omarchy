# DEV-147 — crash-flag preflight refusal, 2026-08-30

Scope: the [one released user command](dev-147-crashflag-manual-release-2026-08-30.md), not a hardware test result.

## Receipt and impact

David supplied this output:

```json
{"level": "error", "status": "REFUSED", "reason": "safe path open refused"}
```

The private helper SHA-256 still matches the released bytes. Source inspection and independent control-flow review agree: this exact top-level refusal occurs before instrumentation. Later measurement/cleanup failures are handled as INCOMPLETE instead. No probe/trace instance or crash-flag observation follows from this invocation. No probe rollback is indicated. The single-use release is consumed, including this refusal.

The error handling discards the underlying path and errno. That is a diagnostic limitation in our helper, not proof of a new monitor fault.

## Narrow investigation

Agent-run `namei -l -n` inspected only fixed path metadata. Installed-module, module-note and physical DRM paths contain no observed symlink or missing component. A /proc/1/mountinfo metadata check establishes path form only, not access in the exited root helper. The command exits 1 because debugfs and tracefs children are not accessible to this unprivileged process. It did not read target contents, install a probe or run the helper.

The [pinned DRM source](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/drivers/gpu/drm/drm_debugfs.c) creates the numbered minor entry as a symlink to the device-named directory. That conflicts with the helper's nofollow path walk. The fixed /dri/2 path is therefore a strong candidate, but the actual failing component and canonical path have not been observed.

## Next boundary

Ask David for one metadata-only `namei --long --nosymlinks` inspection of the exact ColorElements path, kprobe_events and instances. It reads no target contents and installs no probe. The full fixed command remains in the private receipt and user handoff.

Do not retry or edit the frozen operational helper, relax nofollow, mount anything or guess the canonical device path. A later correction must use observed path identity and improve actionable error reporting; it needs focused review before a new release. The [21-test preparation result](dev-147-crashflag-preparation-2026-08-30.md), source and all prior seals remain unchanged. No test was rerun, and no boot, cable, mode, driver/image change or upstream submission is released.

The [main plan](../plans/dev-147-m2-displayport.md#minimum-remaining-path-living) owns the next decision.
