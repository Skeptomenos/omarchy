# A3 T1 staging privacy regression — frozen RED contract

Status: authored on 2026-08-30; no privacy RED or corrected GREEN workload has run. Pre-execution review rejected the unexecuted [GREEN-v1 candidate](t1-green-review-contract.md) because its public operational guard exposed the private A2 root. Review also found that v5 lacks `/usr/bin/sync`, so the full staging suite remains on a separate runtime HOLD. The frozen `green-v1` and operational-v1 files remain unchanged as rejected, unexecuted history. No manifest repin, mock, host-tool fallback or mount widening is part of this correction.

## Exact frozen inputs

| Binding | Content and SHA-256 |
|---|---|
| `/inputs/test` | [test_stage_tipddiag_privacy_red.py](test_stage_tipddiag_privacy_red.py), `58f1eb46d5478147a015d42994f1f2dead934b7e78f0795fd24c71ca0cac4550` |
| `/inputs/helper` | Private `stage-tipddiag-incomplete.sh`, `2f0527ae984eae83a4f2ee49c6f1256bc325d0047e4ebf7dd1e8a82f9f73facc` |
| `/inputs/baseline` | Exact C3 public helper, `dbfbeac043d77ed1543274322f4f961a7622a2adbf49503bb2f54ee465d4d6fe` |
| `/inputs/proof-spec` | Unchanged independent private specification, `189cde8a58dba21374cb7231342136ab25b97fb03ee1e755cdbb2d66a9119269` |

These four individual files are frozen in private A3 `privacy-red-v1`. The subject is exact rejected GREEN-v1 plus only `d2stage_check_proof_root() { :; }` and a blank line before `d2stage_require_operational`. This is a documented missing-feature interface, not the privacy fix. No existing helper or test file changed.

The new file preserves all 52 previous method bodies and adds exactly two, for 54 total. The new methods obtain `private_root` only from the authenticated private specification. The public test contains no literal private root. The expected root-string digest is `131ee2ef09e87694dc2be3e9f2a41bca8bd5384fe48990d070d68002e02bfd09`, computed without a newline. No root path is read or normalized by the proposed predicate.

## One selected semantic RED

After root review and a fresh exact-input probe, select only:

```text
/usr/bin/python3.14 -I -S -B /inputs/test StageHelperTest.test_public_guard_hides_root_and_pins_digest_wiring StageHelperTest.test_root_predicate_accepts_only_exact_private_string
```

Expected: two tests, exactly two assertion failures, zero errors/skips, successful source/spec setup and post-input checks, outer exit 1, no timeout and unchanged inputs. The first method fails because the public helper contains the private root from the specification. It reports a fixed message without printing that root. The second calls the actual no-op predicate successfully with the exact root, then fails because the predicate also accepts the root plus `/`. A missing function, command, input or collector error is not semantic RED.

Exactly two fixture-only Bash children are expected: exact-root and nonexact-root predicate calls. Both should exit 0 with empty stdout/stderr against the deliberate no-op. The first method makes no child call. Retain exact command/stdout/stderr/result triplets, setup and post-input records. Their actual argv stays in private logs. No production preflight, staging, sync call, real image, hardware or live path is used.

The selected two-method run uses the unchanged v5 fixture runtime and four task bindings, for 589 read-only mounts. Root owns its exact outer command, fresh probe, timeout and outcome review. The full 54-method suite must not run while the separate `/usr/bin/sync` runtime issue remains unresolved. A successful privacy-only run cannot waive that hold.

## Minimal later correction, not yet implemented

The future pure `d2stage_check_proof_root` must require exactly one argument. It hashes that exact string with `printf '%s' "$1" | d2stage_clean /usr/bin/sha256sum`, then compares the complete expected digest-output string. It must not read, resolve, stat, canonicalize or normalize the argument as a path. Extra arguments, trailing slash, whitespace, newlines, case changes and other strings must fail. The static assertions freeze the digest, command and refusal wiring.

`d2stage_require_operational` must retain the root-UUID and exact source-relative checks, remove the literal private-root comparison, then call the new predicate on fixed `D2ST_PROOFS` before any production preflight. The public SOURCE/PROOFS/ROOT_UUID assignments remain deliberately invalid. The later private copy may still differ by exactly those three approved assignments and no other bytes. All T1/proof/power/transaction rules remain unchanged.

Keep the original three-assertion RED, rejected unexecuted GREEN-v1 and this privacy RED distinct. Root must accept the actual privacy RED before the correction or a new GREEN companion is authored. Every production preflight, staging, sudo, reboot, cable, device, recovery-rehearsal and live-action hold remains active. Capture preparation remains paused until this staging gate is resolved.
