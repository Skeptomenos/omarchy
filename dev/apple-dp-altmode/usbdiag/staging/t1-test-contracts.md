# A3 T1 staging helper — frozen RED contract

Status: authored on 2026-08-30; no RED workload or GREEN implementation has run. This is a source/fixture handoff for independent pre-execution review. All production preflight, staging, sudo, reboot, cable, device, recovery-rehearsal and live-action holds remain active. The [accepted private T1 image](../../../../docs/evidence/dev-147-t1-private-image-2026-08-30.md) is not rebuilt, copied or mounted by these tests.

## Exact frozen inputs

Four individual read-only files are required. The unchanged v5 manifest has 582 runtime entries; the relocated harness adds its three fixed bindings, for 589 read-only mounts. The root task owns the one-literal launcher relocation review, fresh isolation probe and exact launch approval. No runtime repin, host tree, whole source directory, real image or operational helper is permitted.

| Binding | Frozen content and SHA-256 |
|---|---|
| `/inputs/test` | [test_stage_tipddiag_red.py](test_stage_tipddiag_red.py), `00272539e96843e9b0085a7729db4f10d27c682edca307f08c3d3bbc711ed644` |
| `/inputs/helper` | Private `stage-tipddiag-incomplete.sh`, `d7cdd558519cc984ea7209aacfb0d9fb3be6a5eafb544374fd1d20885554dadd` |
| `/inputs/baseline` | Exact unchanged C3 [public helper](../../stage-usbearly-initramfs.sh), `dbfbeac043d77ed1543274322f4f961a7622a2adbf49503bb2f54ee465d4d6fe` |
| `/inputs/proof-spec` | Independent private `t1-proof-spec.json`, `189cde8a58dba21374cb7231342136ab25b97fb03ee1e755cdbb2d66a9119269` |

The incomplete subject is exactly the C3 baseline plus the two-line insertion `d2stage_check_external_power() { :; }` and a blank line before `d2stage_preflight`. This deliberate no-op is the missing-feature interface, not a production implementation. No old C3 file changed. Private snapshots live in the new A3 `red-v1` directory; host-path manifests stay private.

Setup authenticates the helper, baseline and specification before sourcing Bash. It requires unprivileged UID 1001, `/work`, absent host trees, bounded no-follow single-link inputs, and the specification's exact independent constants. It saves `a3-staging-setup.json`. Teardown reauthenticates inputs and writes `a3-staging-inputs-after.json`. The outer launcher separately owns input invariance and containment checks. Setup, source, collector, decoding or timeout errors are not RED.

## One selected semantic RED

Run only this exact three-method command after root approval and a fresh successful probe:

```text
/usr/bin/python3.14 -I -S -B /inputs/test StageHelperTest.test_t1_image_identity_and_staging_names StageHelperTest.test_exact_accepted_a2_proof_records StageHelperTest.test_external_power_requires_both_online
```

Expected: three tests, exactly three assertion failures, zero errors/skips, outer exit 1, no timeout, unchanged inputs. The image collector succeeds but returns C3/E identities instead of T1. The proof collector succeeds but returns eight C2 rows instead of eleven accepted A2 rows. The no-op accepts `1,1`, then incorrectly accepts `0,1`; that first refusal assertion is the sole power RED. No missing-function or command error substitutes for it.

Exactly four direct fixture Bash children are expected for this selection: image collector, proof collector, online-power call and offline-power call. Each should exit 0 with empty stderr. Preserve their exact commands, stdout, stderr and result triplets, plus the setup and post-input records. They execute no production preflight, staging, assembler, gzip, module, device or recovery operation. The fixture-only `stage-case-*` files under `/work` are not T1 image outputs. The root task must validate the retained child outcomes, outer invariance and absence of remaining workload processes.

## Later GREEN coverage, not permission to run

The new file has 52 methods. All 38 historical real-file test method sources remain unchanged. Four C3-specific methods now specify fixed T1 identities, the old 33 protected rows plus staged E, the eleven A2 proof rows, and diagnostic/no-reboot wording. Ten additional methods cover the two-input power validator, static reader wiring, a complete private transaction, exit 7 after copy and after publication, closed stdout after marker transition, three collision matrices and duplicate/excessive pin records.

The full private transaction calls the real start, protected-file hash, copy, pre-publication hash, no-replace publication, post-publication hash and finish functions. Synthetic stock/W/E/configuration/boot-chain/recovery sentinels and the source must keep their bytes and metadata. Deterministic failures must retain `INCOMPLETE` and partial or unaccepted final outputs. A failed final console write must restore `INCOMPLETE` even if the final marker and provisional result exist. Temporary, result and final-marker collisions include files, symlinks, dangling links, directories and hardlinks; existing entries and targets must remain unchanged.

These are real private-file tests using the retained helper functions and existing runtime tools, not mocked file transactions or production-constant overrides. Synthetic kernel, package, mount, battery and power records do not certify the present machine. Typed stdlib/unittest remains the approved no-install exception. No unrestricted aggregate, graphical, lint-tool, hardware or root-preflight result is claimed. The historical aggregate safety hold remains active.

## Fixed future production boundary

The separately reviewed GREEN helper will stage only `initramfs-linux-asahi-dpalt-tipddiag1.img`, 19,209,545 bytes, SHA `c72c36736cebba0d6d5b67f47b02330c35d3ef81fed9bf5b3315095b0dd765fe`, to that distinct `/boot` name. It will preserve all 33 C3 protected rows and add staged E, for 34. Eleven proof rows bind accepted T1 source, module and build evidence; the three accepted E JSON proofs from `run-988kuwr1`; and the T1 assembly result plus its command/input/security/outer-result records from `run-mvqmtbw_`. There are exactly 45 unique combined paths, below the existing 64-row limit. These are fixed source expectations, not identities inferred from test output. No future A4 seal is a helper input, so no self-referential seal cycle exists.

The future public/private helper comparison permits exactly three literal assignment changes: SOURCE, PROOFS and ROOT_UUID. Every other byte must match. The public copy remains nonoperational; the private source/proof paths reference the retained A2 artifacts directly. Any difference invalidates the comparison. No private operational helper or GREEN companion exists at this RED-authoring checkpoint.

Retained records identify `/sys/class/power_supply/macsmc-ac/online` and `/sys/class/power_supply/tps6598x-source-psy-0-003a/online`. The future reader will pass both values to a validator requiring exact `1`, in addition to battery strictly above 50%. The static test freezes both read commands and their placement before `/boot` checks. Pure synthetic validator tests reject multiline strings, but Bash command substitution strips trailing newlines: these tests do not claim raw-file trailing-newline rejection. A value of `1` is not proof of physical MagSafe, active charging or isolated USB-C charging. Fresh physical confirmation remains a later user gate.

After accepted RED, the root task must approve the minimal GREEN implementation and exact next workload. Keep RED inputs unchanged. Staging-helper GREEN alone will not make the full manual test package ready: the separate fixed-profile capture/binding prerequisite still needs its own offline design, tests and review. No live instruction is released by this contract.
