# DEV-147 D1 preparation hold — 2026-08-28

> Public archival copy, prepared 2026-08-28. Actual boot IDs are redacted where present. Local evidence links are marked as private. Commit references identify the retained private branch unless they name upstream source. Recorded hashes and past QA results describe the private originals, not this edited export. Commands below are historical records, not instructions to run the public helpers.

**Host / scope:** Personal-owned omarchy-air; private offline preparation only.
**Approval:** David said “yes, proceed” after the D1 implementation, focused QA, and private build handoff. D2 staging and D3 boot were excluded.
**Repository:** `codex/dev-147-m2-dp-altmode`, starting at `dcaf9925c64d73811207944ea3ec820752d02fc1`.

## Result

D1 is incomplete and paused after three sandbox QA failures. No diagnostic driver was compiled, installed, or loaded. No initramfs extraction, index generation, repack, staging, boot-file write, or reboot ran. The earlier display/reconnect results and full Gate 4b hold are unchanged.

The [main plan](../plans/dev-147-m2-displayport.md) owns acceptance and rollback. The [diagnostic subplan](../plans/dev-147-usb-startup-diagnostic.md) owns D1. The complete private checkpoint is usbdiag-d1-20260828.fnwvoL5PPt (retained privately). Drafts are saved there, not promoted as tested repository code.

## Completed preparation

- `omarchy dev status` confirmed the live checkout is `/home/david/o-live`; it was not edited. The running kernel remains `7.1.6-1-1-ARCH`.
- GitHub metadata and `git hash-object` verified both saved driver sources and the recovered `glue.h` / `core.h` against Asahi commit `e2e1930a9595bffafad92cec2b5504525efb9cd4`. The quoted-header closure is complete. Source provenance (retained privately) retains URLs, sizes, and hashes.
- The private header Makefile, config, and Module.symvers match their retained pins. GCC 16.1.1 and binutils 2.46 match the recorded compiler versions. This is not a completed reproducible build.
- The recovered `pahole 1:1.31-2` package matches the package database SHA-256 `d9aa45da6e009f655a528faca1bcd9eab4e1ab521a9e467476aae8d32bbc087b`. It came from the official Aachen mirror with TLS verification enabled. Signature verification, extraction, and the old executable-hash check remain unrun. Nothing was installed.
- Private mode-0600, single-link copies of the two installed USB modules retain their exact hashes. They are comparison inputs only.
- A minimal Bash-only sandbox bootstrap passed its limited checks. This is distinct from the incomplete production sandbox proof below.

## Sandbox QA and stop

The proposed boundary uses explicit namespaces, UID/GID 1001, a read-only root and inputs, fresh private work/temp directories, no home/boot/sysfs/procfs access, null-only devices, closed descriptors, and a fixed environment. A narrow seccomp filter denies keyring calls. The approved runtime excludes third-party Python packages and the unused Tk extension, whose host library is absent. No dependency or host setting changed.

| Round | Recorded result |
|---|---|
| 1 | FAIL before launch: a tool RUNPATH produced a non-canonical manifest path. |
| 2 | FAIL during Python startup: the runtime allowlist lacked a lazily imported ctypes file. Inputs stayed unchanged. |
| 3 | FAIL at the assertion for blocking further namespaces. Inputs stayed unchanged; no requested job ran. |

The sandbox handoff (retained privately) retains commands, logs, hashes, and the earlier checks reached. The last result is `exit_code: 1`, `inputs_unchanged: true`, `timed_out: false` in run-cwttf033 (retained privately).

The assertion requires both a failed `unshare()` call and errno `EPERM`. It did not record the actual return, errno, or failing namespace flag. Its message, “namespace recreation was permitted,” therefore does **not** establish that creation succeeded. The installed bubblewrap manual describes a namespace-count limit; Linux also documents `ENOSPC` for that limit. This is a plausible explanation, not the observed result. [Linux unshare manual](https://man7.org/linux/man-pages/man2/unshare.2.html).

The third run did not reach network-route checks, write-boundary canaries, tool version checks, or the unittest smoke. No complete containment PASS is claimed. The repository's [three-round QA rule](../../AGENTS.md) required a user checkpoint. The failed probe was frozen, not repaired or run again.

## Drafts and unrun work

The kernel draft handoff (retained privately) pins the two instrumented copies, patch, 23-variant schema, and trace fixtures. The validator remains an unimplemented RED stub. The [image-format fixtures](../../dev/apple-dp-altmode/usbdiag/image/cpio_image_test.py) also have an unimplemented helper. Neither suite ran. No concurrent cap test, compiler/ABI check, no-change image control, or independent driver/image QA pass exists.

Native kernel INFO/JSON logging follows the design's logging exception. Python uses typed standard-library models and unittest as an explicit no-install tooling exception. Pydantic, pytest, Ruff, and strict type-check gates were unavailable and are not claimed as passed. These exceptions do not waive the failed isolation gate.

The original working image, candidate DP core, old gate helpers, and both backups remain required inputs. Readable before/after checks are retained in the private checkpoint. Root-only stock initramfs/GRUB and the staged image were not freshly read with privilege.

## Next gate and rollback

Ask David before one additional bounded isolation correction and QA round. First retain the namespace flag, return, and errno, and accept only documented denial results for that specific call. A successful namespace creation must still fail. Require the full isolation proof and runtime smoke before any other job. Then resume signature verification, RED/GREEN work, unmodified control builds, diagnostic builds, and image containment checks. D2 and D3 stay unauthorized.

David asked whether the monitor could be unplugged. D1 does not need it; he was told he could unplug it and keep MagSafe connected. An unplug was not confirmed or treated as a test. Recheck the physical setup before any future attended case.

Rollback is to leave these private drafts unused. Do not delete evidence or select a new boot image. This checkpoint did not undo the earlier candidate DTB: a normal boot still selects the stock driver image, not a full DTB rollback. Keep the existing working DP image, both timestamped backups, and the macOS bundle. Full rollback and actual macOS restore execution remain unproved.
