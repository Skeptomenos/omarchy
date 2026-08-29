# DEV-147 E operational pre-execution gate evidence — 2026-08-29

**Host / scope:** `omarchy-air`; contained, unprivileged offline A2 zero-child validation only.
**Approval:** “Proceed with contained, unprivileged offline A2–A4 only. Keep all live-action, candidate boot, staging, sudo, reboot, cable, device, and recovery-rehearsal holds active.”
**Repo state:** Branch `codex/dev-147-t1-image-offline`; pre-checkpoint HEAD `26c2fdc9560d946bff4755244da63f81e6e0fb06` plus the reviewed uncommitted round-3 candidate.

## What happened

The final round-3 candidate ran in four fresh test sandboxes. The retained run root is `/home/david/o/.dev147-stage/tipddiag-a2-20260829.5ShNpUnxf5/sandbox-tools`. Each sandbox used the reviewed launcher and 582-entry toolchain-v5 manifest. Each run reported the containment probe PASS before its test runner started.

| Run directory / ID | Zero-child suite | Inner command | Result |
|---|---|---|---|
| `run-3nddgb4n` | Pure recipe regression | `/usr/bin/python3.14 -I -S -B /inputs/test` | Exit 0; 16/16 passed in 0.307 seconds. |
| `run-u2mzcf5x` | Distinct structural fixture | `/usr/bin/python3.14 -I -S -B /inputs/test EOperationalRedTests.test_a_exact_eight_binding_and_424_structural_policy EOperationalRedTests.test_b_distinct_zero_child_structural_acceptance EOperationalRedTests.test_c_missing_or_failed_record_refuses_without_structural_result` | Exit 0; 3/3 passed in 1.038 seconds. |
| `run-b7wklmzu` | Semantic fixture and pre-import/publication safety | `/usr/bin/python3.14 -I -S -B /inputs/test EControlSemanticRedTests.test_a_full_fixed_e_historical_vector_is_nonfresh EControlSemanticRedTests.test_b_each_semantic_corruption_refuses_without_publication EControlSemanticRedTests.test_c_fixture_publication_is_no_replace_rename_last_and_fail_closed` | Exit 0; 3/3 passed in 13.311 seconds. |
| `run-okhq8uv6` | Fixed execution and collector contract | `/usr/bin/python3.14 -I -S -B /inputs/test EExecutionRedTests.test_a_fixed_self_bootstrap_is_missing EExecutionRedTests.test_b_exact_execution_policy_is_missing EExecutionRedTests.test_c_bounded_operational_collector_is_missing` | Exit 0; 3/3 passed in 1.247 seconds. |

The aggregate result was 25 tests, zero failures, zero errors, and zero skips. Every outer result reported `inputs_unchanged: true` and `timed_out: false`. Every runner reported zero executed workload children, no fresh or operational control proof, no image creation, no module load, no staging, and no boot.

## Exact identities

| Input | SHA-256 |
|---|---|
| Candidate `run_e_control.py` | `4f0475f4aca0e0378096ddb1a164371cb307d44da5d7859ce19fd0602009ec83` |
| Recipe runner | `e334173e984c0bbea1acb2506a0d91a6ac107c6a0e98577419257d84ce7f9714` |
| Structural runner | `65e4da974bd2718e1818805908e1c7a1a6bf5dff2f645eb573572600eb85bd37` |
| Semantic runner | `1ef9f98f1365bcb158a8935ce1cb643a8bf6dbf1544e9cc7d7fc378f372fc316` |
| Execution runner | `3c7452ffb91dbcc26850035bda6fb3f94013d0d34b0e8d704d50ffe6a5b5b17e` |
| Reviewed `sandbox.py` launcher | `62d3c8224cdf2add93a96195f2d35da232086b7074911c92346cd3200beee827` |
| 582-entry toolchain-v5 manifest | `5886d68d263c773990f2c7c5675f63e05debf5c78cdf693440339fddfca947c0` |
| Fixed proof input | `9133cb64040f9df0daf9aa0caaab913c90fe7ce5c9bf59a19c71ce3e36fb0c94` |

The production model stayed fixed at eight task inputs and 593 read-only mounts. The structural and execution test harnesses used nine task inputs and 594 read-only mounts because `/inputs/test` was an additional test binding. The semantic fixture harness used 21 task inputs and 606 read-only mounts because it also bound twelve historical fixture inputs. None of those additional test inputs exist in the production model.

## Fixture and production output boundary

The structural run created only its distinct `/work/e-control-structural-*` record, header, evidence, and check namespace. The semantic run created only the distinct `/work/e-control-semantic-fixture-*` control root, lookup root, early stream, main stream, empty configuration, records, and `NONFRESH_FIXTURE` result, plus its test metadata. These are synthetic zero-child observations. They are not a fresh depmod or lookup result.

The recipe and execution runs created only their test metadata below `/work/e-recipe-fixtures` and `/work/e-control-execution-red`. A retained top-level membership audit of all four run work directories found no production `/work/control-root`, `/work/lookup-root`, `/work/e-early.cpio`, `/work/e-main.cpio`, `/work/empty-modprobe.conf`, `/work/e-control-children-e1`, `/work/e-control-header.json`, `/work/e-control-evidence.json`, `/work/e-control-result.pending`, or `/work/e-control-result.json`.

No production operational recipe ran. No `main()` production entry ran. No one launched the fixed 424-command workload.

## Containment result

All four probes reported UID/GID 1001, empty capabilities and bounding set, `no_new_privs`, filter-mode seccomp, absent IPv4/IPv6 routes, no host `/proc`, `/sys`, `/run`, `/home`, or `/boot`, and only `/work` and `/tmp` as writable storage. All four retained `security.json` files have SHA-256 `eb52e8d04db7a847c19dc68e57f5b1b1331c46c45852100dc3ae19d7e9da96f2` and record keyring denial filter SHA-256 `67aad0d97b5162fe2a4daa6ea9669e42a5b2b9e4aae3e204315787cba8327298`.

## Retained failed round-1 semantic history

`run-zjm97cz4` remains retained as the failed first semantic hardening run. Setup passed. Inputs stayed unchanged. It executed zero workload children and timed out nowhere. Two methods passed. `test_c_fixture_publication_is_no_replace_rename_last_and_fail_closed` failed because the first publication source scan treated a legitimate call in the separately authenticated operational suffix as unresolved. The run exited 1 with one assertion failure and no errors or skips. Its semantic runner SHA-256 was `fc9977b19b0fe91c356e9d8c212d40f301814833b5051927cd91fe39d9aa1ef7`. This was a runner-boundary defect, not production operational evidence, and it is not accepted as GREEN.

The final runner separates the complete semantic prefix scan from the independently authenticated 83-node operational suffix. It also requires the sole fixed bootstrap definitions and call, sole exact `ctypes` bindings, sole final `__main__` guard, immediate pre-import gate before subject loading, and exact prefix sites for `os.open`, `write_new`, and `os.sys.modules.update`. Its negative mutations for `runner.run`, `os.environ.update`, and a decoy `write_new` call are rejected before subject execution and by the publication scan.

## Holds

Candidate-image creation, T1 assembly, load, staging, sudo, reboot, cable action, device access, recovery rehearsal, live-system access, sysfs access, boot-file access, and candidate boot all remained on HOLD. This evidence changes none of those holds.

## Rollback

The completed runs changed no host or live-system state. Their outputs are retained private sandbox evidence. No rollback is required.

## Open

This checkpoint proves only that the fixed candidate and four zero-child runners passed their pre-execution contracts in reviewed v5 containment. It does not prove a fresh E no-change control, image correctness, T1 correctness, DisplayPort causality, USB behavior, charging behavior, startup behavior, or hardware acceptance.

The next gate is conditional. An independent review must first return GO for these exact source, runner, launcher, manifest, eight-input, 593-mount, command-plan, cap, timeout, resweep, and result-last identities. A fresh toolchain-v5 containment probe must then pass. Only after both conditions pass can one fixed 424-child offline E no-change attempt run. Any difference or failure stops the gate. It does not authorize a retry, image build, staging step, sudo command, reboot, cable action, device action, or recovery rehearsal.
