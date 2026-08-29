"""Independent synthetic capture oracles; no journal or device is accessed."""

from dataclasses import replace
import hashlib
import json
import unittest

from capture_binding import (
  CaptureError, CaptureFacts, CaptureFiles, inspect_capture_files,
  validate_bound_capture,
)
from collector_recipe import CollectorClosed, CollectorPlan, collect_capture, collector_plan
from run_capture_tests import evaluate_result


FIXTURE_LABEL = "synthetic-t1-capture-consistency-not-boot-evidence"
BOOT = "0123456789abcdef0123456789abcdef"
BOOT_RAW = b"01234567-89ab-cdef-0123-456789abcdef\n"
OTHER_BOOT_RAW = b"11234567-89ab-cdef-0123-456789abcdef\n"
BUILD_ID = "40aa54382047ba36b02c9ac0da65a213862a77ad"
NOTE = bytes.fromhex("040000001400000003000000474e5500" + BUILD_ID)
ARGV = (
  "/usr/bin/journalctl", "--dmesg", "--boot=" + BOOT,
  "--all", "--output=json", "--no-pager", "--no-tail",
)


def encoded(value: object) -> bytes:
  return json.dumps(value, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def digest(value: bytes) -> str:
  return hashlib.sha256(value).hexdigest()


def messages() -> list[str]:
  """Literal source-order oracle, with init/end inside a mux call pair."""
  cached = dict(plug=True, usb2=True, usb3=True, hpd=True, flip=False, device=False, power=3)
  queued = dict(cached, disconnect=False, hpd_change=False)
  specs = (
    ("init", "begin", 0, {}), ("cache", "stored", 0, cached),
    ("queue", "queued", 0, queued),
    ("worker", "begin", 7, dict(queued, connector=True, cached_device=False)),
    ("role", "skip", 7, dict(which="none", value=0, reason="no_transition")),
    ("hpd", "skip", 7, dict(which="disconnected", reason="level_high_unchanged")),
    ("mux", "begin", 7, dict(kind="dp", mode=4)),
    ("init", "end", 0, dict(reason="complete", ret=0)),
    ("mux", "returned", 7, dict(kind="dp", mode=4, ret=0)),
    ("role", "begin", 7, dict(which="final", value=1)),
    ("role", "returned", 7, dict(which="final", value=1, ret=0)),
    ("hpd", "begin", 7, dict(which="connected")),
    ("hpd", "returned", 7, dict(which="connected")),
    ("worker", "end", 7, dict(reason="complete", ret=0)),
  )
  result = []
  for seq, (event, phase, worker, fields) in enumerate(specs, 1):
    record = dict(
      rev="dev147-tipddiag1-v1", board="j413", target="front_lower",
      component="tipd", seq=seq, gen=1, worker=worker, event=event, phase=phase,
    )
    record.update(fields)
    result.append(encoded(record).decode("ascii") + "\n")
  return result


def rows(source: list[str] | None = None) -> list[dict[str, object]]:
  source = messages() if source is None else source
  ordinary = [("fixture ordinary error", "0"), ("fixture ordinary debug", "7")]
  payloads = [ordinary[0]] + [(message, "6") for message in source] + [ordinary[1]]
  return [dict(
    _BOOT_ID=BOOT, _TRANSPORT="kernel", PRIORITY=priority,
    __CURSOR=f"synthetic-cursor:{index}", __MONOTONIC_TIMESTAMP=str(index),
    __REALTIME_TIMESTAMP=str(1_800_000_000_000_000 + index), MESSAGE=message,
    _EXTRA_SYNTHETIC_FIELD="raw-only",
  ) for index, (message, priority) in enumerate(payloads, 1)]


def fixture(
  records: list[dict[str, object]] | None = None, *, stdout: bytes | None = None,
  stderr: bytes = b"", before_boot: bytes = BOOT_RAW, after_boot: bytes = BOOT_RAW,
  before_note: bytes = NOTE, after_note: bytes = NOTE,
  receipt_changes: dict[str, object] | None = None,
) -> CaptureFiles:
  if stdout is None:
    stdout = b"".join(encoded(record) + b"\n" for record in (rows() if records is None else records))
  receipt: dict[str, object] = dict(
    schema="dev147-t1-collector-receipt1", argv=list(ARGV),
    kernel_release="7.1.6-1-1-ARCH", start_monotonic_us=100,
    end_monotonic_us=200, exit_code=0, timed_out=False,
    stdout_limit_exceeded=False, stderr_limit_exceeded=False,
    stdout_bytes=len(stdout), stderr_bytes=len(stderr),
    stdout_sha256=digest(stdout), stderr_sha256=digest(stderr),
    before=dict(boot_id_sha256=digest(before_boot), tipd_note_sha256=digest(before_note)),
    after=dict(boot_id_sha256=digest(after_boot), tipd_note_sha256=digest(after_note)),
  )
  receipt.update({} if receipt_changes is None else receipt_changes)
  return CaptureFiles(stdout, stderr, encoded(receipt), before_boot, before_note, after_boot, after_note)


def cap_messages() -> list[str]:
  result = []
  for seq in range(1, 129):
    generation = (seq + 1) // 2
    record = dict(
      rev="dev147-tipddiag1-v1", board="j413", target="front_lower",
      component="tipd", seq=seq, gen=generation, worker=0,
      event="init", phase="begin" if seq % 2 else "end",
    )
    if seq == 128:
      record.update(event="cap", phase="end", limit=128, reason="budget")
    elif seq % 2 == 0:
      record.update(reason="vid", ret=-19)
    result.append(encoded(record).decode("ascii") + "\n")
  return result


def fixture_preflight() -> None:
  """Check independent fixtures before any subject function is called."""
  expected = (
    ("init", "begin"), ("cache", "stored"), ("queue", "queued"),
    ("worker", "begin"), ("role", "skip"), ("hpd", "skip"),
    ("mux", "begin"), ("init", "end"), ("mux", "returned"),
    ("role", "begin"), ("role", "returned"), ("hpd", "begin"),
    ("hpd", "returned"), ("worker", "end"),
  )
  source = [json.loads(message) for message in messages()]
  if tuple((record["event"], record["phase"]) for record in source) != expected:
    raise ValueError("fixture_event_oracle_drift")
  if tuple(record["seq"] for record in source) != tuple(range(1, 15)):
    raise ValueError("fixture_sequence_oracle_drift")
  if len(rows()) != 16 or any(len(message.encode("ascii")) > 384 for message in messages()):
    raise ValueError("fixture_size_oracle_drift")
  caps = [json.loads(message) for message in cap_messages()]
  if len(caps) != 128 or (caps[126]["gen"], caps[127]["gen"], caps[127]["event"]) != (64, 64, "cap"):
    raise ValueError("fixture_cap_oracle_drift")
  sample = fixture()
  receipt = json.loads(sample.receipt)
  if receipt["stdout_sha256"] != digest(sample.stdout) or len(NOTE) != 36 or len(BOOT_RAW) != 37:
    raise ValueError("fixture_receipt_oracle_drift")


class CaptureBindingTests(unittest.TestCase):
  def facts(self, sample: CaptureFiles) -> CaptureFacts:
    result = inspect_capture_files(sample)
    self.assertIsInstance(result, CaptureFacts)
    assert isinstance(result, CaptureFacts)
    self.assertEqual(result.evidence, "internally_consistent_only")
    self.assertFalse(result.operationally_accepted)
    self.assertFalse(result.negative_sender_claim)
    self.assertFalse(result.receiver_delivery_claim)
    self.assertFalse(result.usb_or_video_fix_claim)
    return result

  def refuses(self, sample: CaptureFiles, code: str) -> None:
    with self.assertRaises(CaptureError) as raised:
      inspect_capture_files(sample)
    self.assertEqual(str(raised.exception), code)

  def test_complete_full_boot_projection(self) -> None:
    original = messages()
    reordered = original[:6] + [original[7], original[6]] + original[8:]
    result = self.facts(fixture(rows(reordered)))
    self.assertEqual((result.boot_id, result.kernel_release, result.tipd_note_build_id), (
      BOOT, "7.1.6-1-1-ARCH", BUILD_ID,
    ))
    self.assertEqual((result.journal_record_count, len(result.records)), (16, 14))
    self.assertEqual((result.structural_status, result.structural_codes), ("structurally_complete", ()))
    self.assertEqual(tuple(record.message for record in result.records), tuple(reordered))
    self.assertEqual(result.last_returned_cursor, "synthetic-cursor:16")
    self.assertEqual(tuple((item.generation, item.worker, item.sequence) for item in result.connected_hpd_returns), ((1, 7, 13),))

  def test_receipt_hash_and_boot_mismatch(self) -> None:
    self.refuses(fixture(receipt_changes={"stdout_sha256": "0" * 64}), "receipt_mismatch")
    self.refuses(fixture(after_boot=OTHER_BOOT_RAW), "boot_mismatch")

  def test_collector_plan_is_exact_all_priority(self) -> None:
    plan = collector_plan(BOOT)
    self.assertIsInstance(plan, CollectorPlan)
    assert isinstance(plan, CollectorPlan)
    self.assertEqual(plan.argv, ARGV)
    self.assertEqual((plan.deadline_us, plan.stdout_limit, plan.stderr_limit), (30_000_000, 8_388_608, 65_536))
    self.assertEqual(plan.boot_id_path, "/proc/sys/kernel/random/boot_id")
    self.assertEqual(plan.tipd_note_path, "/sys/module/tps6598x_core/notes/.note.gnu.build-id")

  def test_receipt_schema_and_types_are_strict(self) -> None:
    for changes in (
      {"schema": "old"}, {"trusted": True}, {"stdout_bytes": True},
      {"exit_code": False}, {"timed_out": 0}, {"stdout_sha256": "X" * 64},
      {"end_monotonic_us": 200.0}, {"kernel_release": "other"},
    ):
      self.refuses(fixture(receipt_changes=changes), "invalid_receipt")
    receipt = json.loads(fixture().receipt)
    del receipt["before"]
    self.refuses(replace(fixture(), receipt=encoded(receipt)), "invalid_receipt")

  def test_receipt_binds_every_raw_input(self) -> None:
    sample = fixture()
    for name in ("stdout", "stderr", "before_boot_id", "after_boot_id", "before_tipd_note", "after_tipd_note"):
      changed = getattr(sample, name)
      if name not in ("stdout", "stderr"):
        changed = bytes((changed[0] ^ 1,)) + changed[1:]
      else:
        changed += b"x"
      self.refuses(replace(sample, **{name: changed}), "receipt_mismatch")
    self.refuses(fixture(receipt_changes={"stdout_bytes": 1}), "receipt_mismatch")

  def test_collection_completion_and_fixed_bounds(self) -> None:
    for changes in (
      {"exit_code": 1}, {"timed_out": True}, {"stdout_limit_exceeded": True},
      {"stderr_limit_exceeded": True}, {"end_monotonic_us": 30_000_101},
    ):
      self.refuses(fixture(receipt_changes=changes), "collection_failed")
    self.refuses(fixture(stderr=b"journal access warning\n"), "collection_failed")
    self.refuses(fixture(receipt_changes={"start_monotonic_us": 201}), "invalid_receipt")
    self.refuses(fixture(stdout=b" " * 8_388_609), "capture_bound_exceeded")
    self.refuses(fixture(stderr=b" " * 65_537), "capture_bound_exceeded")
    self.refuses(replace(fixture(), receipt=b" " * 16_385), "capture_bound_exceeded")

  def test_boot_samples_and_module_note_are_exact(self) -> None:
    self.refuses(fixture(before_boot=BOOT.encode("ascii")), "invalid_boot_sample")
    self.refuses(fixture(before_note=NOTE[:-1]), "invalid_note")
    self.refuses(fixture(before_note=b"\x05" + NOTE[1:]), "invalid_note")
    wrong = NOTE[:-1] + bytes((NOTE[-1] ^ 1,))
    self.refuses(fixture(before_note=wrong, after_note=wrong), "module_mismatch")
    self.refuses(fixture(after_note=wrong), "module_mismatch")
    observed = []
    for sample in (
      fixture(before_boot=BOOT_RAW + b"x"),
      fixture(after_boot=BOOT_RAW + b"x"),
      fixture(before_note=NOTE + b"x"),
      fixture(after_note=NOTE + b"x"),
    ):
      with self.assertRaises(CaptureError) as raised:
        inspect_capture_files(sample)
      observed.append(str(raised.exception))
    self.assertEqual(tuple(observed), (
      "capture_bound_exceeded", "capture_bound_exceeded",
      "capture_bound_exceeded", "capture_bound_exceeded",
    ))

  def test_query_shape_cannot_silently_filter_or_tail(self) -> None:
    for argv in (list(ARGV) + ["--priority=info"], list(ARGV) + ["--quiet"], list(ARGV[:-1]), list(ARGV) + ["--since=now"]):
      self.refuses(fixture(receipt_changes={"argv": argv}), "invalid_receipt")

  def test_raw_rows_require_complete_bounded_json(self) -> None:
    self.refuses(fixture(stdout=fixture().stdout[:-1]), "invalid_journal")
    self.refuses(fixture(stdout=b"{\n"), "invalid_journal")
    self.refuses(fixture(stdout=b"\xff\n"), "invalid_journal")
    self.refuses(fixture(stdout=b" " * 262_145 + b"\n"), "capture_bound_exceeded")
    self.refuses(fixture(stdout=b"{}\n" * 16_385), "capture_bound_exceeded")
    self.refuses(fixture(rows(cap_messages() + [messages()[0]])), "capture_bound_exceeded")
    padded = [message.removesuffix("\n").ljust(383) + "\n" for message in cap_messages()]
    large_projection = rows(padded)
    for index, record in enumerate(large_projection):
      record["__CURSOR"] = str(index).ljust(512, "x")
    self.refuses(fixture(large_projection), "capture_bound_exceeded")

  def test_duplicate_json_keys_are_refused(self) -> None:
    sample = fixture()
    duplicate_receipt = sample.receipt.replace(b'"exit_code":0', b'"exit_code":0,"exit_code":0', 1)
    self.refuses(replace(sample, receipt=duplicate_receipt), "duplicate_json_key")
    duplicate_row = sample.stdout.replace(b'"PRIORITY":"0"', b'"PRIORITY":"0","PRIORITY":"0"', 1)
    self.refuses(fixture(stdout=duplicate_row), "duplicate_json_key")
    changed = rows()
    changed[1]["MESSAGE"] = messages()[0].replace('"seq":1', '"seq":1,"seq":1')
    self.refuses(fixture(changed), "malformed_t1_family")

  def test_required_journal_fields_have_scalar_types(self) -> None:
    for field in ("_BOOT_ID", "_TRANSPORT", "PRIORITY", "__CURSOR", "__MONOTONIC_TIMESTAMP", "__REALTIME_TIMESTAMP", "MESSAGE"):
      for value in (None, ["6"], True):
        changed = rows()
        changed[0][field] = value
        self.refuses(fixture(changed), "invalid_envelope")
      changed = rows()
      del changed[0][field]
      self.refuses(fixture(changed), "invalid_envelope")

  def test_all_rows_must_match_boot_and_kernel_transport(self) -> None:
    changed = rows()
    changed[0]["_BOOT_ID"] = "1" + BOOT[1:]
    self.refuses(fixture(changed), "boot_mismatch")
    changed = rows()
    changed[-1]["_TRANSPORT"] = "stdout"
    self.refuses(fixture(changed), "invalid_envelope")

  def test_cursor_and_monotonic_envelopes_remain_original(self) -> None:
    for field, value in (("__CURSOR", "synthetic-cursor:1"), ("__MONOTONIC_TIMESTAMP", "0"), ("__MONOTONIC_TIMESTAMP", "020"), ("__MONOTONIC_TIMESTAMP", "201")):
      changed = rows()
      changed[1][field] = value
      self.refuses(fixture(changed), "invalid_envelope")
    changed = rows()
    changed[3]["__REALTIME_TIMESTAMP"] = "1"
    result = self.facts(fixture(changed))
    self.assertEqual(result.records[2].realtime_timestamp, "1")

  def test_all_priorities_are_retained_but_t1_requires_info(self) -> None:
    result = self.facts(fixture())
    self.assertEqual(result.journal_record_count, 16)
    self.assertTrue(all(record.priority == "6" for record in result.records))
    changed = rows()
    changed[1]["PRIORITY"] = "7"
    self.refuses(fixture(changed), "diagnostic_priority")

  def test_malformed_and_mixed_t1_family_is_not_filtered_out(self) -> None:
    for message in (
      '{"rev":"dev147-tipddiag1-v1",',
      messages()[0].replace("dev147-tipddiag1-v1", "dev147-tipddiag1-v2"),
      messages()[0].replace("dev147-tipddiag1-v1", "dev147-usbdiag2-v1"),
      messages()[0].replace('"component":"tipd"', '"component":"dwc3"'),
      messages()[0].replace('"seq":1', '"seq":true'),
      'prefix {"rev":"dev147-tipddiag1-v1"}',
    ):
      changed = rows()
      changed[1]["MESSAGE"] = message
      self.refuses(fixture(changed), "malformed_t1_family")
    source = messages()
    source[0] = source[0].replace("dev147-tipd", "dev147-\\u0074ipd")
    self.assertEqual(self.facts(fixture(rows(source))).structural_status, "structurally_complete")
    changed = rows()
    changed[1]["MESSAGE"] = (
      '{"rev":"dev147-\\u0074ipddiag1-v1","rev":"benign","component":"not-tipd"}'
    )
    self.refuses(fixture(changed), "malformed_t1_family")

  def test_missing_tail_gaps_and_cap_keep_original_structural_codes(self) -> None:
    for source, code in ((messages()[:-1], "missing_worker_end"), (messages()[1:], "sequence_gap"), (cap_messages()[:-1], "missing_cap"), ([], "missing_init_begin")):
      result = self.facts(fixture(rows(source)))
      self.assertEqual((result.structural_status, result.structural_codes), ("inconclusive", (code,)))
    result = self.facts(fixture(rows(cap_messages())))
    self.assertEqual((result.structural_status, result.structural_codes), ("limited", ("capture_capped",)))
    self.assertEqual(result.connected_hpd_returns, ())

  def test_failed_operation_does_not_become_hpd_delivery(self) -> None:
    source = messages()
    record = json.loads(source[8])
    record["ret"] = -5
    source[8] = encoded(record).decode("ascii") + "\n"
    result = self.facts(fixture(rows(source)))
    self.assertEqual(result.structural_status, "structurally_complete")
    self.assertEqual(tuple((item.event, item.ret) for item in result.failed_operations), (("mux", -5),))
    self.assertEqual(tuple(item.sequence for item in result.connected_hpd_returns), (13,))

  def test_receiver_only_message_cannot_supply_sender_evidence(self) -> None:
    changed = rows([])
    changed[0]["MESSAGE"] = "synthetic receiver-only hotplug marker"
    result = self.facts(fixture(changed))
    self.assertEqual((result.structural_status, result.structural_codes), ("inconclusive", ("missing_init_begin",)))
    self.assertEqual(result.connected_hpd_returns, ())

  def test_operational_gate_ignores_forged_receipts_and_selection(self) -> None:
    for receipt, selection in (
      (b"", ""),
      (encoded(dict(trusted=True, image_sha256="1" * 64, image_size=12345, tipd_build_id=BUILD_ID)), "synthetic-t1.img"),
    ):
      result = validate_bound_capture(fixture(), staging_receipt=receipt, selected_initrd=selection)
      self.assertEqual((result.status, result.codes, result.evidence), ("inconclusive", ("artifact_binding_unavailable",), "unbound"))
      self.assertFalse(result.operationally_accepted)

  def test_collector_rejects_noncanonical_boot_ids_and_stays_closed(self) -> None:
    for boot in ("", BOOT.upper(), BOOT + "\n", "--since=now", BOOT_RAW.decode("ascii")):
      with self.assertRaisesRegex(ValueError, "^invalid_boot_id$"):
        collector_plan(boot)
    with self.assertRaisesRegex(CollectorClosed, "^artifact_binding_unavailable$"):
      collect_capture()

  def test_runner_refuses_errors_skips_and_wrong_counts(self) -> None:
    empty = unittest.TestResult()
    self.assertEqual(evaluate_result(empty, expected_tests=3).exit_code, 2)
    for name in ("errors", "skipped", "expectedFailures", "unexpectedSuccesses"):
      result = unittest.TestResult()
      result.testsRun = 3
      getattr(result, name).append("synthetic runner sentinel")
      self.assertEqual(evaluate_result(result, expected_tests=3).exit_code, 2)
    result = unittest.TestResult()
    result.testsRun = 3
    result.failures.append("synthetic assertion sentinel")
    self.assertEqual((evaluate_result(result, expected_tests=3).status, evaluate_result(result, expected_tests=3).exit_code), ("assertion_red", 1))
