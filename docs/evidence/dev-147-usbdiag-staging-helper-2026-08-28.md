# DEV-147 diagnostic staging-helper evidence — 2026-08-28

Host / scope: J413/T8112, kernel `7.1.6-1-1-ARCH`. Offline D2 helper preparation and review only. No privileged preflight, staging, driver action, or reboot occurred.

Approval: David said “ok, update the plan if necessary and proceed” after the D2-preparation recommendation. David alone runs the reviewed staging command. D3 remains a separately approved attended boot.

Repo state: prepared on `codex/dev-147-m2-dp-altmode-public`, after pushed checkpoint `c6dcdacccecbc383f0a8fbd37ffefab68c8f5be2`. The original private history, old helpers, and sealed D1 evidence remain unchanged.

## What changed

The new [staging helper](../../dev/apple-dp-altmode/stage-usbdiag-initramfs.sh) accepts no arguments or environment overrides. Public source and machine constants are deliberately invalid. A separately pinned private copy changes exactly three readonly assignments: source, proof root, and root UUID. All function bodies and the header match. Neither private copy was executed.

The source image remains 19,647,739 bytes, SHA-256 `a11bf3a2bac1f105aa57b08ce9fad338c68882851247f7524d09f4b7c94188ca`. The only proposed destination is `/boot/initramfs-linux-asahi-dpalt-usbdiag1.img`. An existing file, directory, or symlink is a stop, not permission to replace it.

The helper checks kernel and seven package versions, the existing J413 front-port DT route, battery above 50%, the pinned ext4 root, package-transaction state, and a 16 MiB free-space reserve. It checks the candidate's hash, size, owner, mode, and single-link status. Thirty-two protected stock, working-image, recovery, tool, and original-helper files plus eight D1 proof records are checked before copying, before publication, and after publication.

Copying uses a bounded real `dd` into a new root-private directory. Publication uses same-filesystem atomic no-replace `mv`. Hash, size, link count, permissions, sync, and identical protected-check logs must pass. An exclusive INCOMPLETE marker precedes copying. `RESULT.txt` is provisional; completion requires final marker sync, console PASS, and exit 0. Failures retain all partial or final files. There is no cleanup, overwrite, boot-entry change, automatic retry, module load, or reboot option.

## Retained failures and corrections

All runs below are retained privately. Each passed the actual isolation probe before its workload, preserved read-only inputs, and did not time out.

| Run | Result |
|---|---|
| `run-oan706l5` | Initial genuine RED: 36 methods, 47 expected failures against interface stubs. |
| `run-8nn8vpv1` | First implementation: two failures. Its environment loop required `/dev/fd`, which is absent in the sandbox. |
| `run-91daxhtn` | Guarded capture and here-string correction: Bash syntax and all 36 methods pass. |
| `run-aoa0m0pr` | Independent 36-method QA passes, with 123 expected child results. |
| `run-v7wna_pi` | Independent Bash syntax, Python AST, and hash checks pass for that revision. |
| `run-laitgvag` | A separate real Bash-language probe exposes an EXIT-trap scope defect. Failed subshells and nonzero returns lose the local directory variable, changing status 7 to 1. The existing INCOMPLETE marker survives. |
| `run-y37ug8dt` | Two new regression methods produce four expected RED failures against a trap-interface stub. The original 36 methods still pass. |
| `run-4_84j4ds` | The trap now binds an escaped literal path at installation. Bash syntax and all 38 methods pass in 1.264 seconds. |
| `run-52bjj33t` | Final independent QA: 38 methods pass in 1.209 seconds; all 130 child outcomes are expected. |
| `run-k9tp9muw` | Final independent Bash syntax, Python AST, and source hashes pass. |

The original 36 fixture bodies remain unchanged. The two added methods test failed subshells, explicit nonzero returns, direct refusal, silent success, and paths with spaces and quotes. Failure statuses 7, 7, and 1 are preserved. The RED and final GREEN fixture files are byte-identical. The initial private operational copy remains retained but superseded; only the final reviewed copy is eligible for the handoff.

## Containment and final review

The fresh D2 launcher differs from the sealed D1 launcher only in its fixed output root. The old 582-entry tool manifest remains intact. A new 583-entry manifest adds only the pinned `/usr/bin/sync`; its loader and C library were already present. Namespace, network, descriptor, capability, keyring, read-only input, and write-boundary rules remain unchanged. The actual probe and seven stdlib smoke tests pass before every workload. No host `/boot`, `/home`, `/proc`, `/sys`, or `/run` is exposed to the fixtures.

The [38 fixtures](../../dev/apple-dp-altmode/usbdiag/staging/test_stage_helper.py) use real copy, rename, stat, hash, and sync commands against synthetic files under `/work`. They cover source drift, links and special files, existing destinations, bounded copy failure, validation records, interrupted operation, and completion ordering. They do not mock commands or substitute production constants. The test entry point inside the reviewed sandbox is `python3.14 -I -S -B /inputs/staging/test_stage_helper.py`; both Bash sources also pass `bash -n`.

Final public helper SHA-256: `485a68e30c3b94f430e375286756204f7332446c7878393e40ad22bb8a9ebaff`. Final fixture SHA-256: `e06452f8c05c02121e6b47451b4c80ddfa4fa5e30f1b9183da8393baa7836177`. Final private helper SHA-256: `aaedcffd6f614864406055e63a9e3f88e885c44d9ef74e48469c3b3aadfc8c51`.

Independent QA and static safety review found no remaining blocker. The root separately reviewed the complete implementation, the trap correction, and the private-copy comparison. The private file is canonical, UID 1001, mode 0600, one link, under a mode-0700 directory. Its fixed root identity matches the current filesystem without disclosure. The three-assignment comparison and private syntax check pass; this is not execution of its production preflight.

The frozen 4,528-file D1 manifest passes a fresh `sha256sum --check --quiet`. All 15 readable integrity pins passed the preparation baseline. Kernel and package versions still match. The proposed diagnostic destination and package lock remain absent. Root-only staged/stock images and GRUB were not freshly read; the user-run helper must check them before copying.

## Rollback and next boundary

No live rollback is needed for this offline checkpoint. After successful staging, the distinct image remains unselected. Leaving it unselected preserves the normal boot choice. Keep the working DP image, old helpers, both backups, and recovery bundle. Do not delete or overwrite files to repeat staging. An unedited boot still uses the pre-existing experimental DTB; it does not restore the original DTB.

David's exact private staging command is in the local handoff, not in the public archive. Save work, keep the internal screen usable, keep MagSafe connected, and avoid package updates during staging. Paste the complete result. Stop on any refusal or incomplete result. Even `STAGING ONLY PASS` does not authorize reboot; D3 needs a fresh review of the actual cable/device setup and one-time GRUB selection.

## Open limits

Verdict: PASS for D2 offline helper preparation only. Production collection, root staging, startup, USB enumeration, hardware causation, reliability, and recovery execution remain unproved. Source inode continuity brackets the copy operation only; later preflights recheck bytes and metadata. A file-size limit is not disk exhaustion, and a missing-path sync error is not storage-device failure. No power-loss durability claim is made.

The aggregate suite's five recorded baseline failures and credential-writing fixture remain unresolved; it was not rerun unrestricted. Missing lint/type tools were not installed or claimed as passing. Full Gate 4b, Gate 5, rollback acceptance, release, deployment, and upstream submission remain separate. The [living diagnostic plan](../plans/dev-147-usb-startup-diagnostic.md) owns the next action.
