# DEV-147 — T1 boot identity and startup capture — 2026-08-30

**Host / scope:** MacBook Air M2 J413, front/lower USB-C path; kernel `7.1.6-1-1-ARCH`.
**Approval:** David approved one attended connection, exact T1 boot, and fixed bounded capture. He then reported completing all five boot steps, a working internal screen, a responsive device, and no external image. He confirmed adding `-dpalt-tipddiag1` to the prescribed initrd filename and asked to validate the boot.
**Repo state:** `eaf7543346c5819f17f72f0027912034dec11088` before this result update.

This is a completed, consumed diagnostic case. Video FAIL is David's physical observation. Loaded-code identity and retained capture checks PASS with the qualifications below. No further boot, capture, reconnect, or recovery is released.

## What happened

The prior [staging result](dev-147-t1-user-staging-2026-08-30.md) and [sealed manual package](dev-147-t1-manual-package-2026-08-30.md) remained unchanged. The new user report refers to `initramfs-linux-asahi-dpalt-tipddiag1.img`. That selection is user-attested; it is not a measurement of the archive that GRUB read.

Before collection, the main agent authenticated the exact nine-file private collector inventory, its metadata and pins, the accepted fingerprint helper/manifest, eight bootstrap runtime identities, and 281 affected runtime entries. The journalctl binary matched its separate fixed hash, size, owner, mode and single-link constraint. The output directory was absent. The accepted source, runtime and tool identities remained unchanged across collection. No package, image, helper, runtime or pin changed.

The existing process tool invoked the reviewed fixed `collect_fixed_t1()` command once through clean `env -i`, isolated `python3.14 -I -S -B`, and `timeout --signal=TERM --kill-after=5s 40s`. The collector's own bound was 30 seconds, with one second reserved for cleanup, 8 MiB stdout and 64 KiB stderr limits. This collected retained startup messages; it was not an extra 30-second hardware exercise. No test suite or old helper was replayed.

The outer tool returned numeric exit 0 with empty combined output, not separately observed outer stdout/stderr. It exposed no outer PID or session ID. The separate actual journal child used the fixed boot-ID-scoped, all-priority kernel-journal JSON command. It exited 0, reached both stream EOFs and was reaped without a kill. No timeout, escalation, disconnection, retry or parent-failure record occurred. The collector's recorded monotonic span was 30,299 microseconds; the journal child span was 27,648 microseconds.

The raw recordings stay private in the existing one-use capture directory. The separate manual-output directory retains `capture-preflight.json`, `capture-observer.json`, `selection-attestation.json`, `capture-binding.json` and `capture-raw-checksums.txt`. Raw journal rows contain host and audit details; they are not exported here. Existing staging attestations and sealed inputs were not overwritten.

## Result

| Check | Observed result |
|---|---|
| Kernel | `7.1.6-1-1-ARCH`, as required |
| Loaded TIPD GNU build ID | `40aa54382047ba36b02c9ac0da65a213862a77ad`, exact T1 match in both saved samples |
| Boot identity | Same before/after samples and all journal envelopes; raw ID remains private |
| Journal child | Exit 0; 811,980 stdout bytes; empty stderr; both EOFs; direct child reaped |
| Raw stdout SHA-256 | `ed7d65f876a041d254a508a703d954a6d5bf4217e2b5f32b202033ae7bbd95b3` |
| Raw stderr SHA-256 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| Journal and diagnostic records | 1,106 same-boot kernel envelopes; 39 T1 records, sequences 1–39 |
| Pure `bind_fixed_t1()` | Exit 0; `consistent_user_attestation`; no codes; structurally complete supplied trace |
| Independent saved-file QA | PASS for raw hashes, stable private metadata, receipts, identity, bounds and qualified provenance; no live reads or duplicate capture |

The pure binding used the actual unmodified journal/sample files, original staging stdout/stderr, accepted staging attestation and David's same-boot selection attestation. It was run after capture, not used as a substitute execution receipt. Its explicit `initrd_boot_proven`, `earliest_load_proven`, `receiver_delivery_claim` and `hardware_acceptance` fields remain false.

Together, the user selection report, matching kernel, exact loaded T1 note and matching startup revision establish strong evidence that the intended diagnostic ran in this boot. They do not prove every byte of the initramfs GRUB consumed or independently exclude a later reload. Root-private staging checks retain David's pinned privileged-helper provenance.

### What the T1 trace establishes

| Saved sequence | Positive observation |
|---|---|
| 1–2 | First initialization returns `-517` for the role prerequisite. The pinned kernel header defines 517 as `EPROBE_DEFER`; this is a probe retry request, not by itself a fatal error. |
| 3–16 | Generation 2 initializes. Worker 1 sees cached HPD low, applies DP mux mode 4 with return 0 and final role value 1 with return 0, then skips connected HPD for `level_low`. |
| 17–28 | Cached HPD becomes high. Worker 2 calls disconnected HPD, retains the unchanged DP mux, gets final-role return 0, then enters and returns from connected HPD at sequences 26–27. The worker completes. |
| 29–39 | Worker 3 again sees cached HPD high and returns from connected HPD at sequences 37–38. The worker completes. |

These are two observed closed connected-HPD call pairs. They contradict “TIPD never attempted the connected-HPD call” for this case. They do not establish receiver delivery, successful link training or visible video. Nearby saved DCP messages include `dcp_dptx_connect(port=0)` and drive-setting activity; timing proximity alone is not a root-cause proof.

The saved snapshot has no matches for the checked explicit kernel WARN/BUG/panic or DART/IOMMU fault signatures. Other startup diagnostics remain in the raw journal. This narrow search is not a full health check. The physical external-display result remains FAIL; no live DRM, USB-hub or power survey was added.

## Rollback and retained limits

No agent ran sudo, changed a driver, touched boot defaults, reconnected a cable or rebooted. The user-selected GRUB edit was one-use. All images, timestamped backups, sealed inputs and raw results remain retained.

The previously working W image is preserved, but a W recovery boot requires new explicit approval. It is not an automatic second test. An unedited normal boot and W still retain the prototype DTB, so neither is full stock rollback. The exact Mac guide remains the recovery reference; its restore execution is untested.

## Open

- Treat the hardware case as external-video FAIL with useful diagnostic evidence, not a display fix or a cause proven.
- Next investigation should compare saved W/T1 downstream DCP, routing and link-establishment evidence. Do not infer a specific faulty component from these sender records alone.
- If David wants external video restored now, seek approval for one attended selection of the previously working W image before another live action.
- USB enumeration, sustained USB-C charging, reliability, greeter focus, full rollback and upstream-ready implementation remain unvalidated or separate work.
- A structurally complete supplied trace cannot exclude an entirely absent closed suffix. Journal timestamps are receipt times, not exact callback times.
