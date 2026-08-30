# A3 T1 staging privacy correction — GREEN-v2 review

Status: authored on 2026-08-30 after root and independent QA accepted privacy RED `run-l7r97oh1`, following fresh probe `run-pd9_sz89`. No GREEN-v2 helper, test, probe, preflight or operational entry has run during this authoring pass. This is a candidate for a seven-method sync-free subset, not a full staging GREEN or a ready manual package. The full 54-method suite remains UNRUN/HOLD.

## Retained boundary and inputs

The [privacy RED contract](t1-privacy-red-contract.md) and its frozen inputs remain unchanged. Its actual run had exactly two intended assertion failures, zero errors/skips, two fixture Bash children with exit 0 and empty stdout/stderr, successful setup/post-input checks, outer exit 1, no timeout, unchanged inputs and 589 read-only mounts. Independent QA accepted the retained evidence and found no remaining workload. The original three-assertion RED `run-qlfjssz8` remains separate history. The [GREEN-v1 checkpoint](t1-green-review-contract.md) and private operational-v1 copy remain rejected, unexecuted history.

| Binding | SHA-256 |
|---|---|
| `/inputs/helper`: [public T1 helper](../../stage-tipddiag-initramfs.sh) | `91553641af7e6676c8c032cb3432406fec3958959674ec5917a759726714c71e` |
| `/inputs/test`: [privacy GREEN companion](test_stage_tipddiag_privacy_green.py) | `af28433894b92728a7a1892b543e10b59e2d0ff6c5e359a8ba390ec62f9563b0` |
| `/inputs/baseline`: unchanged C3 public helper | `dbfbeac043d77ed1543274322f4f961a7622a2adbf49503bb2f54ee465d4d6fe` |
| `/inputs/proof-spec`: unchanged private eleven-proof specification | `189cde8a58dba21374cb7231342136ab25b97fb03ee1e755cdbb2d66a9119269` |

The four files are frozen separately in private A3 `green-v2`. The new companion differs from [privacy RED](test_stage_tipddiag_privacy_red.py) only in its leading docstring and helper SHA literal. All 54 method bodies are unchanged. None of the test bindings contains a real image, operational helper, boot tree or hardware tree.

The v5 manifest stays `5886d68d263c773990f2c7c5675f63e05debf5c78cdf693440339fddfca947c0`, with 582 runtime files. The four task bindings and three harness bindings total 589 read-only mounts. No runtime repin, mock, host fallback or mount expansion is authorized. Root must review the exact source/command and run a fresh exact-input v5 probe before the subset.

## Minimal correction

The helper now defines one pure `d2stage_check_proof_root` predicate. It requires exactly one argument, hashes the exact string with `printf '%s' "$1" | d2stage_clean /usr/bin/sha256sum`, and compares the complete output to `131ee2ef09e87694dc2be3e9f2a41bca8bd5384fe48990d070d68002e02bfd09  -`. It does not read, stat, resolve, canonicalize or normalize the argument as a path. The public helper no longer contains the private root literal.

The operational guard retains its root-UUID and exact source-relative checks, then calls the predicate on fixed `D2ST_PROOFS` before preflight. SOURCE, PROOFS and ROOT_UUID remain invalid public assignments. No other helper logic changed from rejected GREEN-v1. In particular, the T1 image identity, 34 protected records, eleven proof records, power checks and C3 file-transaction algorithms remain unchanged.

Private operational-v2 SHA is `6b20d119791f4322e101a92b9e5b850ba3098d35dbf966f2d7918cb3918694f9`. Its only byte differences from the public source are the three SOURCE, PROOFS and ROOT_UUID assignment lines. The UUID comes from the retained private C3 copy, not a live read. Both new private directories are 0700 and all their files are 0600. Public source files remain 0644. These comparisons are authoring checks, not execution or permission for live use.

## Exact proposed sync-free subset

After separate review and the fresh exact-input probe, root may run exactly:

```text
/usr/bin/bash -c '/usr/bin/bash -n /inputs/helper && exec /usr/bin/python3.14 -I -S -B /inputs/test StageHelperTest.test_public_guard_hides_root_and_pins_digest_wiring StageHelperTest.test_root_predicate_accepts_only_exact_private_string StageHelperTest.test_t1_image_identity_and_staging_names StageHelperTest.test_protected_records_preserve_c3_33_and_add_retained_e StageHelperTest.test_exact_accepted_a2_proof_records StageHelperTest.test_external_power_requires_both_online StageHelperTest.test_exact_power_reader_and_preflight_wiring'
```

The shell first checks helper syntax without sourcing it. Then the seven selected unittest methods run. Expected result: seven tests, zero failures/errors/skips, outer exit 0, no timeout, successful setup/post-input authentication and unchanged outer inputs. Keep the existing 280-second launcher deadline and 285-second outer cap.

| Selected coverage | Expected direct fixture Bash children |
|---|---|
| Public privacy and digest/operational wiring | 0; static source assertions |
| Exact root-string predicate | 13: one success and twelve refusals |
| T1 constants and output names | 1 successful producer |
| Old 33 protected rows plus staged E | 2 successful producers |
| Exact eleven A2 proofs and 45 unique total paths | 2 successful producers |
| Strict two-value power validator | 19: one success and eighteen refusals |
| Fixed power reader/preflight wiring | 0; static source assertions |
| Total | 37: seven exit 0 and thirty exit 1 |

All 37 child triplets must be retained and independently checked. The successful predicate calls have empty stdout/stderr. The five successful producer calls emit only their exact asserted constants or records, with empty stderr. The twelve root refusals have empty stdout and the fixed argument-count or changed-string refusal; the eighteen power refusals have empty stdout and the fixed two-value refusal. None may time out. Setup, post-input records, exact child argv, outer invariance and absence of remaining workload must be checked. No selected method calls sync, a production reader, preflight or staging.

## Holds and unproved behavior

A subset PASS cannot establish full transaction correctness. The full 54-method suite is UNRUN/HOLD because v5 lacks `/usr/bin/sync`. Adding it needs separate user approval and runtime review. Its `-f` operation flushes the containing filesystem, not only a fixture file, so the missing tool must not be replaced or silently mocked.

The two software online values are not physical MagSafe, active-charge or isolated-charge proof. The synthetic validator rejects nonliteral values, but shell command substitution removes trailing newlines; the static reader test does not prove raw-file newline rejection. No power attribute has been read.

The complete private-file transaction tests, production preflight, storage failure behavior, boot safety, hardware behavior and recovery rehearsal are not established by this subset. The unsafe aggregate-test hold also remains. All live-action, staging, sudo, reboot, cable, device and recovery-rehearsal holds stay active. The fixed-profile capture/binding prerequisite remains unimplemented and held. No full manual test package is ready.
