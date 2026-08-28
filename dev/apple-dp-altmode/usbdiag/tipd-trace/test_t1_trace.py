"""Independent structural assertions; these fixtures are not boot evidence."""

import json
import unittest

from t1_trace import SyntheticBinding, TraceResult, inspect_fixture_capture, validate_capture
from run_tests import evaluate_result
from trace_fixtures import (
  body, cached_pair, cap_capture, capture, change_body, complete_capture,
  complete_specs, entries, normal_worker, omit, payload, spec, with_entries,
)


BINDING = SyntheticBinding(
  label="synthetic-t1-no-hardware",
  image_sha256="11" * 32,
  image_size=12345,
  tipd_sha256="22" * 32,
  tipd_build_id="33" * 20,
)


def fixture_preflight() -> None:
  """Check the independent positive oracle before invoking the parser."""
  expected = (
    ("init", "begin"), ("cache", "stored"), ("queue", "queued"),
    ("worker", "begin"), ("role", "skip"), ("hpd", "skip"),
    ("mux", "begin"), ("mux", "returned"), ("role", "begin"),
    ("role", "returned"), ("hpd", "begin"), ("hpd", "returned"),
    ("worker", "end"), ("init", "end"),
  )
  original = complete_capture()
  observed = tuple((body(item)["event"], body(item)["phase"]) for item in entries(original))
  if observed != expected:
    raise ValueError("positive fixture event oracle drift")
  for document, count in (
    (original, 14), (complete_capture("after_end"), 14),
    (complete_capture("interleaved"), 14), (cap_capture(), 128),
    (cap_capture(open_worker=True), 128),
    (cap_capture(terminal_worker=True), 128),
  ):
    records = entries(document)
    if len(records) != count:
      raise ValueError("positive fixture count oracle drift")
    if tuple(body(item)["seq"] for item in records) != tuple(range(1, count + 1)):
      raise ValueError("positive fixture sequence oracle drift")
    for item in records:
      raw = item["MESSAGE"]
      if not isinstance(raw, str) or not raw.isascii() or len(raw.encode("ascii")) > 384:
        raise ValueError("positive fixture message bound drift")
  capped = entries(cap_capture())
  if (body(capped[126])["event"], body(capped[126])["phase"]) != ("init", "end"):
    raise ValueError("terminal-127 fixture oracle drift")
  if body(capped[127]) != {
    "rev": "dev147-tipddiag1-v1", "board": "j413", "target": "front_lower",
    "component": "tipd", "seq": 128, "gen": 1, "worker": 0,
    "event": "cap", "phase": "end", "limit": 128, "reason": "budget",
  }:
    raise ValueError("paired cap fixture oracle drift")


class T1TraceTests(unittest.TestCase):
  def result(self, document: str) -> TraceResult:
    result = inspect_fixture_capture(document, BINDING)
    self.assertIsInstance(result, TraceResult)
    self.assertIs(result.operationally_accepted, False)
    self.assertIs(result.negative_sender_claim, False)
    self.assertIs(result.receiver_delivery_claim, False)
    self.assertIs(result.usb_or_video_fix_claim, False)
    self.assertEqual(result.evidence, "synthetic_only")
    return result

  def expect_code(self, document: str, code: str) -> None:
    result = self.result(document)
    self.assertEqual(result.status, "inconclusive")
    self.assertEqual(result.codes, (code,))

  def test_complete_reordered_and_interleaved_capture(self) -> None:
    documents = [
      complete_capture(), complete_capture("after_end"),
      complete_capture("interleaved"),
      capture(complete_specs("after_end"), arrival_order=(
        0, 1, 2, 4, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13,
      )),
    ]
    for document in documents:
      result = self.result(document)
      self.assertEqual(result.status, "structurally_complete")
      self.assertEqual(result.codes, ())
      self.assertEqual((result.record_count, result.generation_count, result.worker_count), (14, 1, 1))
      self.assertEqual(len(result.connected_hpd_returns), 1)
      self.assertEqual(result.failed_operations, ())

  def test_missing_mandatory_tail_and_terminal_cap(self) -> None:
    self.expect_code(omit(complete_capture("after_end"), -1), "missing_worker_end")
    self.expect_code(omit(complete_capture(), -1), "missing_init_end")
    self.expect_code(omit(cap_capture(), -1), "missing_cap")
    self.expect_code(omit(cap_capture(terminal_worker=True), -1), "missing_cap")

  def test_operational_entry_is_unconditionally_unbound(self) -> None:
    for document in (complete_capture(), "not JSON", cap_capture()):
      result = validate_capture(document)
      self.assertEqual(result.status, "inconclusive")
      self.assertEqual(result.codes, ("artifact_binding_unavailable",))
      self.assertEqual(result.evidence, "unbound")
      self.assertFalse(result.operationally_accepted)
      self.assertFalse(result.negative_sender_claim)
      self.assertFalse(result.receiver_delivery_claim)
      self.assertFalse(result.usb_or_video_fix_claim)

  def test_init_retry_and_queued_worker_before_failed_init_end(self) -> None:
    retry = (
      spec("init", "begin"), spec("init", "end", reason="vid", ret=-19),
    ) + complete_specs(generation=2)
    result = self.result(capture(retry))
    self.assertEqual(result.status, "structurally_complete")
    self.assertEqual((result.generation_count, result.worker_count), (2, 1))
    self.assertEqual(tuple(item.ret for item in result.failed_operations), (-19,))
    failed_end = change_body(complete_capture(), -1, reason="irq", ret=-16)
    result = self.result(failed_end)
    self.assertEqual(result.status, "structurally_complete")
    self.assertEqual(tuple(item.ret for item in result.failed_operations), (-16,))

  def test_numeric_ids_need_not_follow_reservation_order(self) -> None:
    records = (
      spec("init", "begin", generation=2),
      spec("init", "end", generation=2, reason="vid", ret=-19),
    ) + complete_specs(generation=1, worker=7)
    result = self.result(capture(records))
    self.assertEqual(result.status, "structurally_complete")
    self.assertEqual((result.generation_count, result.worker_count), (2, 1))

  def test_detached_init_and_coalesced_queues(self) -> None:
    detached = capture((spec("init", "begin"), spec("init", "end", reason="complete", ret=0)))
    result = self.result(detached)
    self.assertEqual(result.status, "structurally_complete")
    self.assertEqual((result.worker_count, result.connected_hpd_returns), (0, ()))
    base = complete_specs("after_end")
    result = self.result(capture(base[:3] + cached_pair() + base[3:] + cached_pair()))
    self.assertEqual(result.status, "structurally_complete")
    self.assertEqual(result.worker_count, 1)

  def test_failed_operations_are_closed_not_missing(self) -> None:
    result = self.result(capture(complete_specs(mux_ret=-5, role_ret=-22)))
    self.assertEqual(result.status, "structurally_complete")
    self.assertEqual(tuple((item.event, item.ret) for item in result.failed_operations), (
      ("mux", -5), ("role", -22),
    ))
    self.assertEqual(len(result.connected_hpd_returns), 1)

  def test_final_role_uses_current_cached_not_queued_device(self) -> None:
    document = capture(complete_specs(cached_device=True))
    self.assertEqual(self.result(document).status, "structurally_complete")
    wrong = change_body(change_body(document, 8, value=1), 9, value=1)
    self.expect_code(wrong, "decision_mismatch")

  def test_explicit_early_terminal_skips(self) -> None:
    for reason, ret, plug in (("disconnected", 0, False), ("partner_error", -12, True)):
      initial = (spec("init", "begin"),) + cached_pair(plug=plug)
      worker = normal_worker()
      entry = spec("worker", "begin", worker=1,
                   plug=plug, usb2=True, usb3=True, hpd=True, flip=False,
                   device=False, power=3, disconnect=False, hpd_change=False,
                   connector=True, cached_device=False)
      records = initial + (entry,) + worker[1:3] + (
        spec("mux", "skip", worker=1, kind="none", mode=-1, reason=reason),
        spec("role", "skip", worker=1, which="final", value=1, reason=reason),
        spec("hpd", "skip", worker=1, which="connected", reason=reason),
        spec("worker", "end", worker=1, reason=reason, ret=ret),
        spec("init", "end", reason="complete", ret=0),
      )
      result = self.result(capture(records))
      self.assertEqual(result.status, "structurally_complete")
      self.assertEqual(result.connected_hpd_returns, ())

  def test_invalid_dp_pin_skip_keeps_later_operations(self) -> None:
    records = complete_specs()
    changed = records[:6] + (spec(
      "mux", "skip", worker=1, kind="dp", mode=-1, reason="invalid_dp_pin",
    ),) + records[8:]
    result = self.result(capture(changed))
    self.assertEqual(result.status, "structurally_complete")
    self.assertEqual(len(result.connected_hpd_returns), 1)

  def test_mux_modes_calls_and_unchanged_skips(self) -> None:
    for kind, mode in (("safe", 0), ("usb", 1), ("dp", 2), ("dp", 7), ("tbt", 2), ("usb4", 4)):
      text = change_body(change_body(complete_capture(), 6, kind=kind, mode=mode), 7, kind=kind, mode=mode)
      self.assertEqual(self.result(text).status, "structurally_complete")
      records = complete_specs()
      skipped = records[:6] + (spec(
        "mux", "skip", worker=1, kind=kind, mode=mode, reason="unchanged",
      ),) + records[8:]
      self.assertEqual(self.result(capture(skipped)).status, "structurally_complete")
    self.assertEqual(self.result(capture(complete_specs(none_pair=True))).status, "structurally_complete")

  def test_hpd_no_connector_low_and_changed_high_decisions(self) -> None:
    base = complete_specs()
    for connector, hpd, changed in ((False, True, False), (True, False, False), (True, True, True)):
      entry = spec("worker", "begin", worker=1,
                   plug=True, usb2=True, usb3=True, hpd=hpd, flip=False,
                   device=False, power=3, disconnect=False, hpd_change=changed,
                   connector=connector, cached_device=False)
      if connector and (not hpd or changed):
        disconnected = (
          spec("hpd", "begin", worker=1, which="disconnected"),
          spec("hpd", "returned", worker=1, which="disconnected"),
        )
      else:
        disconnected = (spec("hpd", "skip", worker=1, which="disconnected", reason="no_connector"),)
      if connector and hpd:
        connected = base[10:12]
      else:
        connected = (spec(
          "hpd", "skip", worker=1, which="connected",
          reason="level_low" if connector else "no_connector",
        ),)
      initial = (spec("init", "begin"),) + cached_pair(hpd=hpd, hpd_change=changed)
      records = initial + (entry, base[4]) + disconnected + base[6:10] + connected + base[12:]
      result = self.result(capture(records))
      self.assertEqual(result.status, "structurally_complete")
      self.assertEqual(len(result.connected_hpd_returns), 1 if connector and hpd else 0)

  def test_cache_queue_allows_unrelated_init_terminal(self) -> None:
    pair = cached_pair()
    records = (spec("init", "begin"),) + pair + pair[:1] + (
      spec("init", "end", reason="complete", ret=0),
    ) + pair[1:] + normal_worker()
    self.assertEqual(self.result(capture(records)).status, "structurally_complete")

  def test_budget_marker_is_always_limited(self) -> None:
    for document in (cap_capture(), cap_capture(open_worker=True), cap_capture(terminal_worker=True)):
      result = self.result(document)
      self.assertEqual(result.status, "limited")
      self.assertEqual(result.codes, ("capture_capped",))
      self.assertEqual(result.record_count, 128)

  def test_cap_requires_record127_same_owner_and_fixed_limit(self) -> None:
    self.expect_code(omit(cap_capture(), 126), "sequence_gap")
    self.expect_code(change_body(cap_capture(), 127, worker=1), "invalid_cap")
    self.expect_code(change_body(cap_capture(), 127, gen=2), "invalid_cap")
    self.expect_code(change_body(cap_capture(), 127, limit=127), "invalid_record")
    premature = entries(cap_capture())[:126]
    premature[-1] = entries(cap_capture())[-1]
    value = body(premature[-1])
    value["seq"] = 126
    premature[-1]["MESSAGE"] = json.dumps(value, separators=(",", ":")) + "\n"
    self.expect_code(with_entries(cap_capture(), premature), "invalid_cap")

  def test_json_malformed_duplicate_and_nonstandard(self) -> None:
    self.expect_code("not JSON", "invalid_json")
    text = complete_capture()
    self.expect_code(text.replace('"schema":', '"schema":0,"schema":', 1), "duplicate_json_key")
    for message, code in (
      ('{"seq":1,"seq":2}\n', "duplicate_json_key"),
      ('{"seq":NaN}\n', "invalid_json"),
      ("{not JSON}\n", "invalid_json"),
    ):
      records = entries(text)
      records[0]["MESSAGE"] = message
      self.expect_code(with_entries(text, records), code)

  def test_message_encoding_and_complete_byte_limit(self) -> None:
    text = complete_capture()
    for message, code in (
      ("é\n", "invalid_record"), ("{}\r\n", "invalid_record"),
      ("{}\n{}\n", "invalid_record"), (" " * 385, "record_too_long"),
    ):
      records = entries(text)
      records[0]["MESSAGE"] = message
      self.expect_code(with_entries(text, records), code)

  def test_integer_boolean_separation_and_ranges(self) -> None:
    text = complete_capture()
    for index, field, value in (
      (0, "seq", True), (0, "gen", False), (0, "worker", True),
      (0, "seq", 1.0), (1, "power", 3.0), (7, "ret", 0.0),
      (0, "seq", 0), (0, "seq", 129), (0, "gen", 0),
      (0, "gen", 2_147_483_648), (3, "worker", 2_147_483_648),
      (1, "power", True), (1, "power", 4), (1, "plug", 1),
      (3, "connector", 0), (6, "mode", True), (8, "value", True),
      (7, "ret", False), (7, "ret", -2_147_483_649),
    ):
      with self.subTest(index=index, field=field, value=value):
        self.expect_code(change_body(text, index, **{field: value}), "invalid_record")

  def test_record_keys_and_mixed_identity(self) -> None:
    text = complete_capture()
    self.expect_code(change_body(text, 0, extra="not allowed"), "invalid_record")
    for field, value in (
      ("rev", "dev147-usbdiag1-v1"), ("rev", "dev147-usbdiag2-v1"),
      ("board", "apple,j413"), ("target", "/soc/i2c@235010000/usb-pd@3f"),
      ("component", "atc"),
    ):
      self.expect_code(change_body(text, 7, **{field: value}), "record_identity_mismatch")
    self.expect_code(change_body(text, 11, ret=0), "invalid_record")
    self.expect_code(change_body(text, 11, delivered=True), "invalid_record")

  def test_duplicate_sequence_gap_and_missing_first_entry(self) -> None:
    text = complete_capture()
    self.expect_code(change_body(text, 1, seq=1), "duplicate_sequence")
    self.expect_code(omit(text, 5), "sequence_gap")
    self.expect_code(omit(text, 0, renumber=True), "missing_init_begin")

  def test_wrong_generation_worker_and_duplicate_ownership(self) -> None:
    text = complete_capture()
    self.expect_code(change_body(text, 7, gen=2), "unknown_generation")
    self.expect_code(change_body(text, 7, worker=2), "unknown_worker")
    records = complete_specs() + cached_pair() + normal_worker(worker=1)
    self.expect_code(capture(records), "duplicate_worker")
    self.expect_code(capture(complete_specs() + (spec("init", "begin"),)), "duplicate_init")

  def test_required_operation_pairs_and_order(self) -> None:
    text = complete_capture()
    self.expect_code(omit(text, 6, renumber=True), "missing_operation_begin")
    self.expect_code(omit(text, 7, renumber=True), "missing_operation_return")
    self.expect_code(change_body(text, 7, mode=5), "operation_pair_mismatch")
    records = complete_specs()
    swapped = records[:6] + records[8:10] + records[6:8] + records[10:]
    self.expect_code(capture(swapped), "operation_order")

  def test_queue_requirements_without_cardinality_assumption(self) -> None:
    text = complete_capture()
    self.expect_code(omit(text, 2, renumber=True), "missing_queue")
    records = complete_specs()
    self.expect_code(capture(records[:1] + records[3:]), "worker_without_queue")

  def test_hpd_snapshot_and_terminal_reason_consistency(self) -> None:
    self.expect_code(change_body(complete_capture(), 3, connector=False), "decision_mismatch")
    self.expect_code(change_body(complete_capture(), 12, reason="partner_error", ret=0), "invalid_record")
    self.expect_code(change_body(complete_capture(), 13, reason="complete", ret=-5), "invalid_record")

  def test_exact_external_artifact_binding(self) -> None:
    text = complete_capture()
    value = payload(text)
    value["fixture_label"] = "another-synthetic-case"
    self.expect_code(json.dumps(value), "fixture_binding_mismatch")
    for field, replacement in (
      ("image_sha256", "44" * 32), ("image_size", 12346),
      ("tipd_sha256", "55" * 32), ("tipd_build_id", "66" * 20),
    ):
      value = payload(text)
      artifacts = value["artifacts"]
      if not isinstance(artifacts, dict):
        raise ValueError("fixture artifact object missing")
      artifacts[field] = replacement
      self.expect_code(json.dumps(value), "artifact_mismatch")
    value = payload(text)
    value["kind"] = "operational"
    self.expect_code(json.dumps(value), "fixture_binding_mismatch")

  def test_journal_envelope_and_collection_boundary(self) -> None:
    text = complete_capture()
    for field, replacement, code in (
      ("_BOOT_ID", "fedcba9876543210fedcba9876543210", "boot_mismatch"),
      ("PRIORITY", "7", "invalid_envelope"),
      ("__MONOTONIC_TIMESTAMP", "-1", "invalid_envelope"),
      ("__REALTIME_TIMESTAMP", "18446744073709551616", "invalid_envelope"),
      ("__CURSOR", "fixture:1", "invalid_envelope"),
    ):
      records = entries(text)
      records[1][field] = replacement
      self.expect_code(with_entries(text, records), code)
    for field in ("collection_complete", "all_priorities"):
      value = payload(text)
      value[field] = False
      self.expect_code(json.dumps(value), "incomplete_collection")
    value = payload(text)
    value["collection_start_monotonic_us"] = 1
    self.expect_code(json.dumps(value), "invalid_collection")

  def test_missing_records_and_input_bound(self) -> None:
    value = payload(complete_capture())
    value["records"] = []
    self.expect_code(json.dumps(value), "missing_init_begin")
    self.expect_code(" " * 131_073, "input_too_large")

  def test_partner_error_requires_kernel_errno_range(self) -> None:
    base = (spec("init", "begin"),) + cached_pair() + normal_worker()[:3]
    for ret in (-4095, -1, -4096, -2147483648, 1, 2147483647, True):
      records = base + (
        spec("mux", "skip", worker=1, kind="none", mode=-1, reason="partner_error"),
        spec("role", "skip", worker=1, which="final", value=1, reason="partner_error"),
        spec("hpd", "skip", worker=1, which="connected", reason="partner_error"),
        spec("worker", "end", worker=1, reason="partner_error", ret=ret),
        spec("init", "end", reason="complete", ret=0),
      )
      if ret in (-4095, -1):
        result = self.result(capture(records))
        self.assertEqual(result.status, "structurally_complete")
        self.assertEqual(tuple(item.ret for item in result.failed_operations), (ret,))
      else:
        self.expect_code(capture(records), "invalid_record")

  def test_cap_ownership_and_reserved_slot_are_exact(self) -> None:
    self.expect_code(change_body(cap_capture(terminal_worker=True), -1, worker=0), "invalid_cap")
    self.expect_code(change_body(cap_capture(open_worker=True), -1, worker=1), "invalid_cap")
    text = cap_capture()
    records = entries(text)
    second_cap = body(records[-1])
    second_cap["seq"] = 127
    records[-2]["MESSAGE"] = json.dumps(second_cap, separators=(",", ":")) + "\n"
    self.expect_code(with_entries(text, records), "invalid_cap")
    without_cap = entries(text)
    value = body(without_cap[-2])
    value["seq"] = 128
    without_cap[-1]["MESSAGE"] = json.dumps(value, separators=(",", ":")) + "\n"
    self.expect_code(with_entries(text, without_cap), "invalid_cap")

  def test_serialized_bounds_include_stripped_newline(self) -> None:
    text = complete_capture()
    records = entries(text)
    raw = records[0]["MESSAGE"]
    if not isinstance(raw, str):
      raise ValueError("fixture message must be text")
    prefix = raw.removesuffix("\n")
    exact = prefix + " " * (383 - len(prefix))
    for message in (exact, exact + "\n"):
      records[0]["MESSAGE"] = message
      self.assertEqual(self.result(with_entries(text, records)).status, "structurally_complete")
    records[0]["MESSAGE"] = exact + " "
    self.expect_code(with_entries(text, records), "record_too_long")
    bounded = text + " " * (131072 - len(text.encode("utf-8")))
    self.assertEqual(self.result(bounded).status, "structurally_complete")
    self.expect_code(bounded + " ", "input_too_large")

  def test_runner_refuses_skips_errors_and_count_mismatch(self) -> None:
    def succeeds() -> None:
      return None

    def fails() -> None:
      raise AssertionError("synthetic failure")

    def skips() -> None:
      raise unittest.SkipTest("synthetic skip")

    def errors() -> None:
      raise ValueError("synthetic exception")

    for callback, expected_status, expected_exit in (
      (succeeds, "pass", 0), (fails, "assertion_red", 1),
      (skips, "test_incomplete", 2), (errors, "test_error", 2),
    ):
      result = unittest.TestResult()
      unittest.FunctionTestCase(callback).run(result)
      outcome = evaluate_result(result, expected_tests=1)
      self.assertEqual((outcome.status, outcome.exit_code), (expected_status, expected_exit))
      mismatch = evaluate_result(result, expected_tests=2)
      self.assertEqual(mismatch.exit_code, 2)

    class ExpectedFailure(unittest.TestCase):
      @unittest.expectedFailure
      def runTest(self) -> None:
        self.fail("synthetic expected failure")

    class UnexpectedSuccess(unittest.TestCase):
      @unittest.expectedFailure
      def runTest(self) -> None:
        return None

    for case in (ExpectedFailure(), UnexpectedSuccess()):
      result = unittest.TestResult()
      case.run(result)
      self.assertEqual(evaluate_result(result, expected_tests=1).exit_code, 2)
