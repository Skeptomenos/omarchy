# Fixed T1 capture source

This archive contains the bounded log collector and boot/artifact consistency checks for the one accepted T1 diagnostic image. The [dated evidence](../../../../docs/evidence/dev-147-t1-capture-2026-08-30.md) owns executed results. The [plan](../../../../docs/plans/dev-147-m2-displayport.md#minimum-remaining-path-living) owns the next approval boundary.

Do not run these files live. There is no installer or live CLI. The private fixed entry is held and unrun. Reconciled 2026-08-30: [T1 user-run staging](../../../../docs/evidence/dev-147-t1-user-staging-2026-08-30.md) passes receipt review and independent QA; that release is consumed. T1 remains UNBOOTED. The [manual-package seal](../../../../docs/evidence/dev-147-t1-manual-package-2026-08-30.md) and 13-method result remain unchanged. A later attended boot and fixed capture require separate approval, fresh setup, and authenticated caller/input checks; no live capture is released.

## Contents

- `bounded_child.py`: streaming subprocess capture, active limits, signal cleanup, direct-child reaping, exclusive private files and execution-only receipts.
- `fixed_t1_collector.py`: fixed journal command and before/after boot/module samples. Maximum collection time: 30 seconds, with one second reserved for cleanup. Output limits: 8 MiB stdout and 64 KiB stderr.
- `fixed_t1_binding.py`: exact T1 image/helper identity and strict user staging/selection attestations.
- `capture_binding.py` and `t1_trace.py`: unchanged accepted pure validators.
- Two test modules, a fixed runner and the retained pre-execution GREEN contract.

The original three tests supplied the semantic RED. The added safety tests are focused regression coverage. They do not simulate monitor hardware.

## Public and private boundary

Eight exports match their frozen private source bytes. The wrapper differs in exactly one `LIVE_OUTPUT` literal. Its unchanged path-hash guard rejects the public `LOCAL_ONLY` value before any live access.

The runner intentionally retains the private wrapper pin. Its exact staging-prefix fixture and runtime manifest stay private. This checkout is not a runnable test or live-capture package. No raw journal, real boot ID, protected file, image, module binary or recovery backup is published.

A provisional result file is not completion. Later acceptance requires the complete raw records, matching readback, no parent failure, and an independently observed successful outer invocation. Staging and image selection remain user attestations. A complete-looking trace prefix cannot prove an absent later event, receiver delivery, or video/USB/charging reliability.

The typed standard-library/dataclass/unittest no-install exception remains. No dependency or general-purpose framework was added.
