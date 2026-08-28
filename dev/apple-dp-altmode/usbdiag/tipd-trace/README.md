# T1 sender trace contract

This directory defines a strict, pure parser for the selected TIPD sender diagnostic. The [A1 plan](../../../../docs/plans/dev-147-usb-startup-diagnostic.md#a1-selection--t1-tipd-sender-diagnostic-living) owns scope and approval. The parser has passed the scoped synthetic-fixture tests. It is not a boot instruction or operational validator.

## Test-first boundary

The original `parser_not_implemented` subject and two genuine assertion failures were retained before implementation. The current fixture parser passes the same two tests plus the full structural matrix after independent pre-execution review, a fresh sandbox run, and independent output review. Source-pin, import, fixture, and execution errors are setup failures, not semantic RED. The runner requires exactly 2 selected tests or all 31 methods. It returns 2 for setup errors, test exceptions, skips, expected failures, unexpected successes, or a count mismatch; 1 for ordinary assertion failures; and 0 only when every selected test passes.

`trace_fixtures.py` does not import the parser or driver. It contains independent literal event sequences and labelled synthetic artifact identities. `test_t1_trace.py` supplies expected results separately. The [record schema](t1-record.schema.json) documents exact JSON payload fields. Tests exercise the parser, not a second schema validator that supplies its expected answers.

No dependency is installed. This contained tool uses standard-library `unittest`, typed dataclasses, and explicit validation instead of pytest/Pydantic. Native kernel INFO/JSON remains the producer format; no application logging library is added. Ruff/mypy and kernel behavior are separate unclaimed gates.

## Entry points and evidence levels

- `inspect_fixture_capture(document, binding)` takes one bounded JSON string and an external `SyntheticBinding`. It accepts only the exact `synthetic_fixture` kind and the same label in the binding and capture. The label matches `synthetic-[a-z0-9_-]{1,48}`. Its strongest possible result is `structurally_complete` with `evidence="synthetic_only"` and `operationally_accepted=False`.
- `validate_capture(document)` has no caller-supplied manifest, expected hash, or environment override. It always returns `artifact_binding_unavailable` in this draft. Real T1 image size/hash and TIPD hash/build ID do not yet exist as reviewed fixed parser inputs. Later activation needs a distinct reviewed source change and tests; a fixture binding can never activate it.

The parser does not collect or filter logs, inspect files, access a device, read environment variables, or modify its input. Existing v1/v2 validators stay unchanged. No output may echo an untrusted message, artifact identity, cursor, or arbitrary string. Results expose only fixed codes, bounded counts, and typed sender observations.

## Capture envelope

The fixture capture has exactly these keys: `schema`, `kind`, `fixture_label`, `boot_id`, `collection_start_monotonic_us`, `collection_end_monotonic_us`, `collection_complete`, `all_priorities`, `artifacts`, and `records`.

- Schema is `dev147-tipd-capture1`; kind is `synthetic_fixture`. The label must equal the independent synthetic binding. `boot_id` is 32 lowercase hex characters.
- Start is integer zero. End is an integer from 1 through `2**64-1`. Both collection flags are the Boolean `true`. These are collection declarations, not independent evidence that a journal retained every message.
- `artifacts` has exactly `image_sha256`, `image_size`, `tipd_sha256`, and `tipd_build_id`. Hashes are 64 lowercase hex characters, build ID is 40, and image size is a positive integer. All four values must match the external fixture binding. No Boolean can substitute for an integer.
- `records` is a list of 1–128 original diagnostic-only journal envelopes. Each envelope has exactly `_BOOT_ID`, `PRIORITY`, `__CURSOR`, `__MONOTONIC_TIMESTAMP`, `__REALTIME_TIMESTAMP`, and `MESSAGE`. Boot IDs match; priority is the string `6`; cursors are unique ASCII strings of 1–512 bytes without control characters. Timestamps are unsigned decimal strings in `uint64` range. Monotonic arrival timestamps are nondecreasing and lie within the declared collection interval. Realtime values are retained, but clock adjustments must not invalidate otherwise ordered monotonic evidence.
- The whole input is bounded to 131,072 UTF-8 bytes. Each message is ASCII, contains no CR or embedded newline, and has zero or one final newline. A stripped final newline still counts as one byte toward the producer's 384-byte limit. Blank or unrelated messages are rejected, not silently filtered.

Reject duplicate JSON keys at every nesting level, nonstandard JSON constants, wrong types, unknown keys, bad ranges, malformed JSON, extra records, or mismatched identities. A Boolean or float cannot substitute for an integer, even when numerically equal. Unknown fields are rejected rather than stripped: this deliberate security-skill refinement prevents accepting a different diagnostic contract.

## Payload grammar

Every record has exactly `rev`, `board`, `target`, `component`, `seq`, `gen`, `worker`, `event`, `phase`, plus the event fields below. Fixed values are `dev147-tipddiag1-v1`, `j413`, `front_lower`, and `tipd`. Sequence is 1–128, generation is 1–2,147,483,647, and worker is 0–2,147,483,647. Initialization/cache/queue use worker zero. Worker/mux/role/HPD use a positive worker ID.

The cached fields are `plug`, `usb2`, `usb3`, `hpd`, `flip`, and `device` as Booleans, plus `power` in 0–3. Queued fields add Boolean `disconnect` and `hpd_change`. Worker entry adds Boolean `connector` and `cached_device`. `disconnect` is the accumulated plug-status change bit, not an independent physical-cable observation. These are recorded facts, not hardware queries.

| Event / phase | Exact additional fields |
|---|---|
| `init / begin` | None |
| `init / end` | `ret` as int32; `reason` in `gpio`, `vid`, `power_state`, `mode`, `patch`, `mask`, `status`, `role`, `psy`, `port`, `power_read`, `data_read`, `irq`, `connect`, `complete`. `complete` iff ret is zero. |
| `cache / stored` | Cached fields |
| `queue / queued` | Queued fields |
| `worker / begin` | Queued fields plus `connector`, `cached_device` |
| `worker / end` | `reason` is `disconnected`, `partner_error`, or `complete`; `ret` is zero except `partner_error`, which requires an actual `PTR_ERR` value from -4095 through -1. |
| `mux / begin` or `returned` | `kind`, `mode`; `returned` also has int32 `ret`. Valid pairs: safe/0, usb/1, dp/2–7, tbt/2, usb4/4. |
| `mux / skip` | Valid kind/mode plus `reason="unchanged"`; or dp/-1 with `invalid_dp_pin`; or none/-1 with `disconnected` or `partner_error`. |
| `role / begin` or `returned` | `which` is `none` or `final`; `value` is 0 for none, 0–2 for final; `returned` also has int32 `ret`. |
| `role / skip` | none/0 with `reason="no_transition"`; or final/0–2 with `disconnected` or `partner_error`. |
| `hpd / begin` or `returned` | `which` is `disconnected` or `connected`. There is no return value, delivery, accepted, or status field. |
| `hpd / skip` | Disconnected: `no_connector` or `level_high_unchanged`. Connected: `no_connector`, `level_low`, `disconnected`, or `partner_error`. |
| `cap / end` | `limit=128`, `reason="budget"`; sequence 128 and the same generation/worker as normal record 127. |

## Ordering and completeness

Sequence reservation precedes emission. Preserve arrival order and timestamps, but check causal record order by unique sequence number. Accept reordered arrival without rewriting the evidence. Require a consecutive sequence prefix starting at one. Generation and worker IDs are globally unique within their respective namespaces; their numeric values need not increase with sequence order because ID reservation can be preempted before sequence reservation.

Each generation has exactly one positive init entry before its records, and one init terminal unless the budget was exhausted. Every worker has a globally unique begin, belongs to its entry generation, and closes once. Init/end can occur before, during, or after worker records. An error returned by init does not prove that previously queued work was canceled; the pinned source has a retained lifetime limitation. The parser must not invent cleanup or hardware-safety claims.

Each actual queue-status call emits a cache/stored then queue/queued pair with worker zero. Detached or early-failed init can emit neither. Later IRQ/polling can emit more pairs after init/end. Pair order matters, but records from other contexts may intervene. A worker needs a prior queue record in its generation. There is no one-queue/one-worker rule: existing cancellation, requeue, and coalescing stay outside the parser's evidence.

For each worker, require this order:

`begin → none-role pair/skip → disconnected-HPD pair/skip → mux pair/skip → final-role pair/skip → connected-HPD pair/skip → end`

Early disconnected/partner-error termination requires explicit not-reached mux, final-role, and connected-HPD skips with the same terminal reason. The normal path still runs the final role and connected-HPD decision after a mux error or invalid pin skip. Pair fields must agree; a failed int32 return closes the operation and remains in `failed_operations`. HPD is a void API: a returned pair is only a sender-call return.

Final role uses queued USB2/USB3 presence but **worker `cached_device`**, not queued `device`. This value is computed independently of `plug`; the disconnected early skip can therefore record a nonzero final role value. Disconnected and connected HPD decisions must agree with worker `connector`, `hpd`, `hpd_change`, and any early terminal reason. The old role is not recorded, so the parser cannot independently prove why the none-role call was needed. Data-connection bits and pin/mode history are also absent; a legal mux skip is not independent proof of hardware mode.

Reservations 1–126 are normal. Reservation 127 atomically reserves both 127 and 128. The same invocation emits normal 127 and then cap 128; later reservations emit nothing. Any 127 without 128 is `missing_cap`, even if 127 is an init or worker terminal. A valid cap is always `limited` / `capture_capped`, never structurally complete or negative evidence. A cap may close a truncated prefix with open operations; it does not fabricate their outcomes. Dropping 127 while retaining 128 is a sequence gap. Losing an entire closed suffix below the cap cannot be detected from consecutive records alone.

## Results and fixed error codes

`structurally_complete` means the supplied synthetic sequence has its required entries, pairs, and terminals. It does not establish that all source executions were captured. `limited` means the valid budget marker was reached. Every invalid or incomplete capture is `inconclusive`. All results keep `operationally_accepted`, `negative_sender_claim`, `receiver_delivery_claim`, and `usb_or_video_fix_claim` false.

Validation precedence is input/JSON, envelope/binding, record fields/identity, duplicate/gap/cap checks, then source-order checks. The first fixed issue code is returned. Focused malformed fixtures introduce one fault at that layer. Intended codes include `input_too_large`, `invalid_json`, `duplicate_json_key`, `invalid_capture`, `invalid_collection`, `incomplete_collection`, `fixture_binding_mismatch`, `artifact_mismatch`, `invalid_envelope`, `boot_mismatch`, `record_too_long`, `invalid_record`, `record_identity_mismatch`, `duplicate_sequence`, `sequence_gap`, `missing_cap`, `invalid_cap`, `missing_init_begin`, `duplicate_init`, `unknown_generation`, `missing_init_end`, `missing_queue`, `worker_without_queue`, `unknown_worker`, `duplicate_worker`, `operation_order`, `missing_operation_begin`, `missing_operation_return`, `operation_pair_mismatch`, `decision_mismatch`, and `missing_worker_end`. The cap code is `capture_capped`.

## Reviewed sandbox execution, not a host command

Mount only a frozen copy of this directory as `/inputs/tests` in the already verified new sandbox. The source-pinned runner authenticates its three local Python dependencies and the schema. The tests also import the runner's pure result-classification helper; the runner itself and this contract remain pinned by the outer sandbox input fingerprint. Importing the runner cannot execute its guarded main. It has no subprocess, network, device, filesystem-write, old-helper, or environment-override path.

Retained semantic RED argv inside that sandbox:

```text
/usr/bin/python3.14 -I -S -B /inputs/tests/run_tests.py red
```

The `all` mode adds the full structural matrix and operational refusal checks. Its four new methods cover the kernel errno range, cap ownership/reserved slot, serialized bounds, and real unittest result classification. The original 27 method bodies and fixture source remain unchanged. Each run requires the root's reviewed launcher, fresh private output, fixed tool pins, isolation/smoke checks, and existing outer deadline.

On 2026-08-29, `/usr/bin/python3.14 -I -S -B /inputs/tests/run_tests.py all` passed all 31 methods in a reported 0.072 seconds. There were zero failures, errors, skips, expected failures, or unexpected successes. The run exited 0 without timeout and launched zero workload child processes. Isolation and seven import-smoke tests passed; all 586 read-only bindings stayed unchanged. Independent pre-execution and actual-output reviews passed.

The tested parser SHA-256 is `8c1e90a30f68c9237948e47f583038aee0d4584fa2459779e518b1630372e0fe`. The original RED and tested six-file GREEN snapshots and raw results remain private and unchanged. This later README update is not part of the executed snapshot. Acceptance covers synthetic structural parsing only. `validate_capture` still unconditionally refuses operational acceptance; the run proves no boot identity, complete driver trace, receiver delivery, hardware safety, USB function, or video fix.
