# DEV-147 C3 E-only staging evidence — 2026-08-28

**Host / scope:** M2 J413/T8112, kernel `7.1.6-1-1-ARCH`; David's reviewed staging-only command and subsequent unprivileged receipt/integrity checks.
**Approval:** The C3 handoff authorized David to stage the exact E image. It did not authorize image selection or reboot.
**Repo state:** Public checkpoint `07c3f6a360767ce4615ffe3ba19edf1b9d2c2fa9`; helper sources, tests, and sealed C2/C3 artifacts remained unchanged.

## Result

**C3 user-run staging PASS; E is staged but UNBOOTED.** Independent receipt QA is a qualified PASS: the complete final report is accepted as successful user-run validation, not an independent read of root-private image bytes, logs, or completion markers. The command is consumed; do not replay staging or request another privileged read merely to duplicate it.

The [main plan](../plans/dev-147-m2-displayport.md#current-handoff--c4-readiness-hold-living) owns the next readiness hold. The [C3 preparation record](dev-147-usbearly-staging-helper-2026-08-28.md) retains the 42-test/source/private-copy review; [C2](dev-147-c2-offline-preparation-2026-08-28.md) owns image construction. No display, USB, charging, reliability, or boot-safety result was added.

## Receipt and provenance

David supplied a complete 48-line transcript of the reviewed clean-environment private helper invocation. All 41 visible hash rows match the frozen helper exactly and in order: 33 protected entries and eight sealed C2 proofs. These rows are the **initial preflight only**. The later before-copy, before-publication, and after-publication records were redirected to the root-private check directory and were not independently read.

The transcript includes the complete three-line `STAGING ONLY PASS` report and a normal prompt, with no failure text. The reviewed helper emits that report only after its repeated protected/image checks, completion-marker transition, and final sync. No separate numeric exit status was captured. Successful execution is therefore evidenced by David's complete report and normal prompt, not an independently observed numeric exit 0 or root-log read. The exact command and raw receipt remain private; no runnable staging command is repeated here.

## Independent read-only checks

| Check | Observed result and limit |
|---|---|
| `sha256sum` over readable entries in the fixed 41-row set | 37 hashes match. Four protected files are unreadable: stock initramfs, GRUB configuration, the working W image, and the retained failed-v1 image. Their repeated checks remain evidenced by David's successful validator. |
| Staged E metadata via `stat` | `/boot/initramfs-linux-asahi-dpalt-usbearly1.img` is a regular, single-link, root:root file, mode 0600, 19,191,513 bytes. Its bytes are unreadable to the agent; this is not an independent destination-hash check. |
| Retained check-directory metadata via `stat` | Root:root, mode 0700. Root-private logs and markers were not read. |
| Source image and helper identities | The private source E hash remains `4d4f0557af57eebcc33322f004bcc7968254e644b069a11102375df0b31a52ae`. Public and operational helper identities remain unchanged. |
| C3 seal verification | The full 601-file manifest, its own identity, and 16 fixed input pins pass. The final seal-report SHA-256 is `deadd035341a27da2cbf723bc55ff7bf7cca62403d65ed20f185f22ce0f95586`. No frozen artifact was changed. |
| Kernel, packages, and absence checks | Kernel remains `7.1.6-1-1-ARCH`; all seven fixed package versions match. No package lock or `/etc/default/update-m1n1` override is present. The dev-linked live checkout remains unchanged. |

The staged image's pinned target is the same 19,191,513-byte E image verified in C2. E adds packaged DWC3 and the required dependency/alias indexes; it contains no diagnostic or rebuilt control modules. ATC, the working patched TIPD core, and unrelated records remain governed by the C2 image proof. The staged destination's content validation comes from the user-run helper, not from the metadata checks above.

## Retained state and next gate

Keep the staged E image unselected, all older images, the check directory, both timestamped backups, and all private evidence. No cleanup, overwrite, retry, or privileged duplicate check is needed. Staging leaves normal boot selection unchanged. It does not restore the prototype DTB or complete full rollback; the macOS restore bundle remains untested at runtime.

At this checkpoint the current monitor connection, MagSafe connection, and downstream USB-device state are unknown. C4 is HOLD pending fresh physical/readiness confirmation and a separately reviewed one-time selection proposal with its exact recovery handoff already approved and available offline. No new reboot command or permission is supplied. B/G images remain unprepared; W/E/B/G are comparison definitions, not a boot schedule. D3 video causality remains unknown, and startup USB/full Gate 4b stays HOLD. No cable action, module load, mode change, suspend, or upstream submission occurred in this receipt reconciliation.
