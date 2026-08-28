# DEV-147 C3 E-only staging-helper evidence — 2026-08-28

**Host / scope:** M2 J413/T8112, kernel `7.1.6-1-1-ARCH`; offline helper preparation and contained real-file fixtures only.
**Approval:** Continue the reviewed E-only preparation until a manual action is needed. David runs any later privileged staging command; boot selection remains a separate gate.
**Repo state:** C2 checkpoint `b1414e3f3fecd4dadcaea32070cac29cde8e2b0b` was pushed and read back clean. Its sealed 2,270-file manifest passed. C2 artifacts and all historical helpers/tests/evidence remain unchanged.

## Result

The new E-only helper passes Bash syntax checking and all 42 focused tests in 1.377 seconds. The two genuine RED assertions were retained before the minimal helper change. Independent saved-run QA, helper review, and exact private-copy review pass. E remains **unstaged and unbooted**. No production preflight or hardware action ran.

The [main plan](../plans/dev-147-m2-displayport.md#current-handoff--c3-staging-only-living) owns the manual boundary. The [diagnostic subplan](../plans/dev-147-usb-startup-diagnostic.md#c3-result--offline-staging-preparation-living) owns current C3 status. [C2 artifact checks](dev-147-c2-offline-preparation-2026-08-28.md), [D3 failure](dev-147-usbdiag-startup-failure-2026-08-28.md), and [working-image recovery](dev-147-dp-recovery-2026-08-28.md) remain separate. No new display, USB, charging, or reliability result follows; full Gate 4b stays HOLD.

## Executed checks and retained RED

These are completed sandbox workloads, not live-use commands. Each run bound four individual read-only files at `/inputs/test`, `/inputs/helper`, `/inputs/baseline`, and `/inputs/proof-spec`. The baseline was the frozen old public D2 helper; the authenticated specification fixed the sealed C2 identities. No whole C2 tree, boot directory, operational helper, or hardware tree was mounted. The root UUID, raw host manifests, private launcher, and raw logs remain private. The archived helper retains its exact guard/protected source-path literals.

| Check | Exact inner workload | Observed result |
|---|---|---|
| E-identity/proof RED | `/usr/bin/python3.14 -I -S -B /inputs/test StageHelperTest.test_e_image_identity_and_staging_names StageHelperTest.test_exact_sealed_c2_proof_records` | Exit 1; exactly two expected assertion failures and zero errors. Setup passed. Both real old collectors exited 0 with empty stderr. The failures were old image/proof values, not missing inputs, source drift, or setup failure. |
| Syntax-gated GREEN | `/usr/bin/bash -c '/usr/bin/bash -n /inputs/helper && exec /usr/bin/python3.14 -I -S -B /inputs/test'` | Exit 0; syntax check, setup, and all 42 methods passed. The run retained 137 fixture-child records. |

Both runs passed the actual isolation probe, retained unchanged inputs, and avoided a workload timeout. Independent RED QA verified all eight pre/post input pins, 1,836 sandbox-command arguments, 590 read-only mounts, and exactly four task bindings. Final GREEN QA verifies 1,832 sandbox-command arguments, the same 590 read-only mounts, nine stable post-pins, seven passing smoke checks, and all 137 expected child outcomes: 41 successes, 93 refusals, two exit-7 trap cases, and one SIGTERM case. Each workload ran once; no replay hid a failed setup.

The old D2 helper was not intended to satisfy this new E contract. These expected fixture failures do not invalidate its historical D2 staging result. The GREEN companion changes only the subject-helper SHA and explanatory docstring from the frozen RED file. All 42 bodies and fixed expectations are identical. All 38 old method bodies remain unchanged; four new methods test E identity/names, the old protected rows plus the retained failed image, the exact eight C2 proof records, and uninstrumented completion wording.

The fixture collectors execute the real fixed-record producers. They do not read the protected or proof files. Thus **33 protected + 8 proof records** is a tested 41-path producer contract, not a fresh root preflight or a current-machine hash result. Synthetic host/power/mount inputs and real temporary-file failures do not establish live power state, root execution, storage power-loss safety, or kernel behavior.

## Exact source and image boundary

The four exports match their frozen reviewed private bytes:

| Source | SHA-256 |
|---|---|
| [E-only helper](../../dev/apple-dp-altmode/stage-usbearly-initramfs.sh) | `dbfbeac043d77ed1543274322f4f961a7622a2adbf49503bb2f54ee465d4d6fe` |
| [Frozen RED fixture](../../dev/apple-dp-altmode/usbdiag/staging/test_stage_usbearly_red.py) | `35cb1c4c4695b70524dd1e0bc321779d0dbb026e13e42b929273a90a3f9af46c` |
| [GREEN companion](../../dev/apple-dp-altmode/usbdiag/staging/test_stage_usbearly_green.py) | `1907acd3ae9562b768ec72d460b093df39a9c748e7303789379b830079bf433b` |
| [Retained test-first contract](../../dev/apple-dp-altmode/usbdiag/staging/c3-test-contracts.md) | `4a46656694871b2202a087f88a77b346a43d34649e2da2ba4e44d5dac2234c64` |

The helper pins `initramfs-linux-asahi-dpalt-usbearly1.img`, 19,191,513 bytes, SHA-256 `4d4f0557af57eebcc33322f004bcc7968254e644b069a11102375df0b31a52ae`, for the distinct `/boot` destination. E contains the packaged DWC3 addition and required dependency/alias indexes, not diagnostic or rebuilt control modules. ATC, the working patched TIPD core, and unrelated records remain as verified in C2. B/G images are unprepared.

Only the fixed E identities, exact operational-path guards, staging names, retained failed-v1 image pin, eight C2 proof rows, and completion wording changed from the old helper. All 32 old protected rows remain byte-for-byte. `D2ST_`/`d2stage_` names and the copy, no-replace publication, sync, trap, environment, package/kernel, battery, root, and reserve checks remain unchanged. Two initially proposed proof filenames were corrected to the existing `e-assembly-result.json` and `e-image-delta.json` during static review, before binding or execution. No artifact was renamed.

The public helper's source, proof root, and root UUID remain deliberately invalid. Independent review proves that the private copy changes exactly those three literal assignments; every other byte equals the tested public helper. Its actual hash and comparison record remain private. The image's actual hash/size, owner/mode and single-link identity, all eight canonical proof paths/hashes, and the root identity match the approved inputs. The private directory is mode 0700 and the helper is mode 0600. Any change to either copy requires renewed comparison and review. Neither copy's production preflight has run.

## Manual boundary and limits

With offline QA and private-copy review complete, the next manual action is David's exact **staging-only** command. It must clear the environment before Bash starts. No monitor connection is required for staging; keep the current cable state unchanged. David must be present, save work, keep the lid open and internal screen usable, keep MagSafe connected, and have battery strictly above 50%. Stop on package/kernel drift or any refusal; no cleanup, guard bypass, or automatic retry.

Review David's complete output and exit status before any C4 proposal. The helper must validate all protected/proof records before and after publication, the exact final image identity and metadata, completion marker, final sync, console PASS, and exit 0. `RESULT.txt` alone is provisional; `INCOMPLETE`, a nonzero exit, or missing evidence means HOLD. Preserve all outputs and both timestamped recovery backups.

Leaving E unselected keeps normal boot selection unchanged; it does not restore the prototype DTB. No reboot follows staging. Any later C4 image selection needs fresh readiness and an exact recovery handoff already reviewed, approved, and available offline. The macOS restore bundle remains untested at runtime. No full-suite, privileged-preflight, staging, boot-safety, hardware, permanent-integration, or upstream-submission PASS is claimed. Typed stdlib/unittest remains the no-install exception. No new package, driver operation, cable action, mode change, suspend, or live checkout change occurred.
