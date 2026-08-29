# T1 capture support — test-first contract

Status: post-GREEN publication-only refinement. The initial RED, review RED, and tested GREEN snapshots remain immutable. The pure capture-consistency suite is GREEN. The 31-test structural parser and its six files remain unchanged. Its historical unbound entry remains closed. This package does not release a live collector, operational artifact binding, staging command, image profile, reboot, or test case.

The known T1 module is SHA-256 `a0fdadc351261643545e5afd8561923be99431661c447084336c9318f5b0c02f`, build ID `40aa54382047ba36b02c9ac0da65a213862a77ad`, for `7.1.6-1-1-ARCH`. The accepted T1 image name, SHA-256, and size are not yet available. There is no expected-image argument, environment override, external accepted-profile file, or trusted JSON flag.

## Boundary and result

`inspect_capture_files()` is a pure consistency check over seven submitted byte strings: journal stdout, stderr, receipt, and before/after boot-ID and TIPD build-ID-note samples. Its preserved initial RED subject returned `None`. The current candidate validates these inputs and calls only the existing `_record`, `_ordered`, and `_source_order` structural primitives. It does not create a `SyntheticBinding`, call the fixture capture API, or promote the old result's `synthetic_only` evidence field.

`CaptureFacts` copies only structural facts and the original T1 envelopes. It reports `internally_consistent_only`, not an authentic capture or selected image. Raw-byte consistency does not prove who ran a command or what booted. All operational, negative-sender, receiver-delivery, and USB/video claims stay false. Invalid input raises `CaptureError` with a fixed code, without raw log content. Structural absence or incompleteness instead returns the existing inconclusive code. A valid cap returns `limited`.

`validate_bound_capture()` always returns `artifact_binding_unavailable`. `collect_capture()` always raises the same closed-gate code. Both stops apply even if supplied notes match the known module and a receipt says `trusted`.

## Exact receipt

Receipt JSON is UTF-8 and has these exact top-level keys:

- `schema`: `dev147-t1-collector-receipt1`.
- `argv`: the exact argument list from the collector recipe below.
- `kernel_release`: the fixed release above.
- `start_monotonic_us`, `end_monotonic_us`: non-boolean uint64 integers.
- `exit_code`: non-boolean int32; clean completion requires zero.
- `timed_out`, `stdout_limit_exceeded`, `stderr_limit_exceeded`: booleans; clean completion requires all false.
- `stdout_bytes`, `stderr_bytes`: non-boolean uint64 byte counts.
- `stdout_sha256`, `stderr_sha256`: lowercase 64-digit hashes.
- `before`, `after`: exact objects with `boot_id_sha256` and `tipd_note_sha256`, each a lowercase 64-digit hash.

Reject duplicate JSON keys, non-standard numeric constants, extra/missing keys, wrong types, unknown schema, wrong kernel, or a different argument list. Check fixed byte bounds first. Check all counts and hashes before interpreting the submitted samples or command outcome. A mismatch is `receipt_mismatch`; the validator never updates a mismatched receipt.

Before hashing, reject a before or after boot sample longer than 37 bytes and a before or after note sample longer than 36 bytes as `capture_bound_exceeded`. Within-bound altered samples with stale receipt hashes remain `receipt_mismatch`. Before/after raw boot IDs must each be one canonical lowercase UUID plus newline, and must agree. Each note must be exactly the 36-byte little-endian GNU build-ID note: namesz 4, descsz 20, type 3, owner `GNU\0`, then the known 20-byte ID. A malformed note is `invalid_note`; a different ID is `module_mismatch`. A malformed boot sample is `invalid_boot_sample`; two different valid boot IDs are `boot_mismatch`.

Require `0 <= start <= end`, at most 30,000,000 elapsed microseconds, zero exit status, empty stderr, and no timeout or exceeded-limit flag. Bad clock shape is `invalid_receipt`; an unsuccessful collection is `collection_failed`. Fixed limits are 8,388,608 stdout bytes, 65,536 stderr bytes, 16,384 receipt bytes, 16,384 journal rows, and 262,144 bytes per raw row including newline. Exceeding a bound is `capture_bound_exceeded`. These receipt checks do not prove an active deadline or output-cap implementation.

## Full raw journal and strict projection

The raw stream is retained privately without rewriting, trimming, filtering, or sorting. It must be complete UTF-8 newline-delimited JSON; empty stdout is permitted but supplies no positive T1 entry. A missing final newline or bad raw JSON is `invalid_journal`. Check total row count and row lengths before interpreting envelopes. Duplicate JSON keys are `duplicate_json_key`.

Each row must contain scalar string `_BOOT_ID`, `_TRANSPORT`, `PRIORITY`, `__CURSOR`, `__MONOTONIC_TIMESTAMP`, `__REALTIME_TIMESTAMP`, and `MESSAGE`. Unknown journald fields stay in the raw stream and are not copied into the projection. `_BOOT_ID` must be the sampled 32-digit boot ID; a different valid ID is `boot_mismatch`. `_TRANSPORT` must be `kernel`. Priority is one decimal digit 0 through 7. T1 priority must be 6 or the result is `diagnostic_priority`. Do not coerce arrays, byte arrays, nulls, or booleans. Missing/wrong envelope fields are `invalid_envelope`.

Timestamps use the existing canonical uint64-decimal grammar. Monotonic timestamps must not decrease in journal arrival order and cannot exceed the collection end. Realtime can move backwards. Cursors must be unique, printable ASCII, nonempty, and at most 512 bytes. Do not parse their opaque contents. Preserve each projected record's six original fields after the transport check. `last_returned_cursor` is the last raw row's cursor, not a scan-end cursor, source-event boundary, or proof of a complete tail.

T1-family detection examines both literal diagnostic markers and every duplicate-preserving top-level JSON pair, so escaping a revision or adding a later benign duplicate cannot make an earlier diagnostic revision/component disappear. A message with a `dev147-tipd` or `dev147-usbdiag` marker, any decoded diagnostic revision, or any `component: tipd` pair must pass the exact T1 record grammar. A malformed, prefixed, duplicate-key, old/mixed-revision, wrong-target, wrong-component, oversize, or wrong-type family record is `malformed_t1_family`. Do not turn it into an ordinary ignored row. Entirely erased markers cannot be detected from text alone; absence is not evidence that a sender did not run.

Serialize the projected six-field envelope list as ASCII JSON with compact comma/colon separators. It retains the existing 131,072-byte budget and at most 128 records; a larger projection is `capture_bound_exceeded`. Reordered sequence reservations remain legal. Preserve all existing sequence, generation/worker, operation-pair, return, terminal, and cap checks. Missing seq 128 after normal 127 remains inconclusive, even if 127 is terminal. A cap is never negative evidence.

## Collector recipe, not a released command

`collector_plan()` accepts only a lowercase 32-digit boot ID. Its preserved initial RED subject returned `None`; the current pure implementation returns the fixed plan without executing it. The independent oracle fixes this argument order: `/usr/bin/journalctl`, `--dmesg`, `--boot=<sampled ID>`, `--all`, `--output=json`, `--no-pager`, `--no-tail`.

This is an all-priority, oldest-available, exact-boot kernel query. It has no priority, grep, time-window, output-field, namespace, follow, or cursor-file filter. Do not use `--quiet`: access warnings must remain visible and cause refusal. No `--show-cursor` footer is requested. The systemd documentation defines `--dmesg` as the kernel filter, `--no-tail` as all stored lines, and `--all` as disabling field-length elision. JSON may still represent unusual or repeated fields as arrays. [Official journalctl documentation](https://raw.githubusercontent.com/systemd/systemd/main/man/journalctl.xml)

The future reviewed collector may sample only `/proc/sys/kernel/random/boot_id` and `/sys/module/tps6598x_core/notes/.note.gnu.build-id`, before and after the query. It also records the kernel release and monotonic collection bounds. It needs one bounded child, a fixed clean environment, retained stdout and stderr, active cap/deadline enforcement, and an exact exit/termination receipt. No retries, journal sync, privilege escalation, dynamic debug, tracefs/BPF, console changes, hardware probes, or partner `usb_mode` reads. The currently disabled recipe performs none of these reads or launches.

Journal timestamps are receipt metadata, not callback execution times. Pair monotonic values with the boot ID. [Official journal field documentation](https://raw.githubusercontent.com/systemd/systemd/main/man/systemd.journal-fields.xml)

## Later operational gate and interpretation

After actual image acceptance, separately review a literal fixed image profile, exact manual initrd-selection confirmation, and the new helper's staging receipt against its exact source/artifact pins. Preserve the qualification where staging validation was user-run and root-private bytes were not independently read. Do not treat a human receipt as an agent read or fabricate a numeric exit status. Keep before/after boot and note samples with the real collector execution record. Add genuine refusal/positive tests for this bound entry and active collector limits before a manual handoff. These later steps are not implemented or accepted by this draft.

A matching loaded note alone does not identify the initrd, prove the module ran at earliest startup, or exclude an earlier reload. A complete observed trace cannot detect an entirely absent closed suffix. INFO at the sender records a call/void return, not receiver delivery. Only an independently correlated positive receiver marker supports receiver entry; its absence is unknown and its timestamp does not prove connector-registration order. No parser result proves USB enumeration, physical display behavior, charging negotiation, hardware safety, or the cause of the earlier E failure.

## Retained test history

Only the orchestrator may run the reviewed package in a fresh verified sandbox. Proposed single read-only binding: a frozen six-file directory at `/inputs/tests` with the five new files and unchanged `t1_trace.py`. The outer launcher pins every file, including the runner. The runner checks the other five hashes before importing any local module, checks exact input membership, isolated Python 3.14, `/work`, non-root identity, and absent host trees. No workload child is launched.

The internal test invocation is `python3 -I -S -B /inputs/tests/run_capture_tests.py red`; this is not a live capture command. The selected methods are valid full-boot projection, receipt/hash refusal, and exact collector plan. Each should reach one assertion failure, not an import/setup failure. Expect 3 tests, 3 failures, 0 errors, and exit 1. `all` selects exactly 21 methods. Skips, errors, expected failures, unexpected successes, wrong counts, or setup faults return 2. The fixtures are labelled synthetic by the test oracle, outside the operational inputs. No successful fixture can enable the operational entry.

The preserved initial RED result is `run-cshy9zwb`: exactly 3 intended assertion failures, 0 errors, 586 read-only bindings, no timeout, no workload children, unchanged inputs, and no live input. This line records that immutable result; it does not relabel this later publication refinement as tested.

Pre-execution review rejected the first GREEN candidate before it ran. It could filter an escaped first T1 revision when a later duplicate revision decoded as benign, and it checked boot/note sample grammar before explicit 37-byte and 36-byte maximums. The regression draft adds both cases to the existing malformed-family and boot/note methods without changing the 21-method total. The duplicate message is valid JSON whose first escaped `rev` decodes to `dev147-tipddiag1-v1`; a later benign duplicate and non-TIPD component must not hide it. Four independently regenerated receipts bind an oversized before-boot, after-boot, before-note, or after-note sample. Each 38-byte boot or 37-byte GNU-note sample must fail as `capture_bound_exceeded` before grammar or identity interpretation.

The regression-only invocation is `python3 -I -S -B /inputs/tests/run_capture_tests.py review`. It selects exactly those 2 existing methods. The accepted retained result is `run-emqla_gz`, recorded in `a2-capture-review-red-evidence.json`, with both intended regression assertions RED. `validate_bound_capture()` and `collect_capture()` remain unconditionally closed.

The accepted GREEN result is `run-0dpnhbbf`. Root and independent output review agree: all 21 of 21 methods pass, with 586 read-only bindings, zero workload children, unchanged inputs, no timeout, and both hardware evidence and operational acceptance false. This validates only the frozen pure parser, receipt-consistency checks, command plan, and closed gates. It does not validate a live collector, selected initrd, accepted T1 image profile, earliest startup identity, receiver delivery, USB/video behavior, charging behavior, or hardware safety.

Preserve each run, its source/input pins, sandbox proof, actual stdout/stderr, exit/timeout record, and post-run unchanged-input checks. The initial RED, review RED, and GREEN snapshots remain immutable. Future operational work still requires a separately reviewed fixed image name/hash/size, exact staging and manual-selection qualification, a bounded real collector with active cap/deadline tests, retained raw bytes and receipts, and a new positive/refusal gate before any manual handoff. Before commit, one final zero-child pin-integration run must authenticate this publication revision together with the unchanged accepted code and tests.
