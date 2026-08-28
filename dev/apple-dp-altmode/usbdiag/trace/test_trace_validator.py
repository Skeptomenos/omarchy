"""Synthetic parser cases, not evidence about USB or display hardware."""

from copy import deepcopy
import json
import unittest

from trace_validator import ValidationResult, validate_capture

REVISION = "dev147-usbdiag1-v1"
BOOT_ID = "0123456789abcdef0123456789abcdef"
MANIFEST: dict[str, object] = {
    "revision": REVISION,
    "components": {
        "dwc3": {"sha256": "d" * 64, "build_id": "1" * 40},
        "atc": {"sha256": "a" * 64, "build_id": "2" * 40},
    },
}


class Trace:
    def __init__(self) -> None:
        self.records: list[dict[str, object]] = []
        self.sequence = {"dwc3": 0, "atc": 0}
        self.now = 0

    def add(
        self,
        component: str,
        event: str,
        phase: str,
        *,
        generation: int = 1,
        attempt: int = 0,
        **fields: object,
    ) -> dict[str, object]:
        self.now += 1
        self.sequence[component] += 1
        body: dict[str, object] = {
            "schema": 1,
            "revision": REVISION,
            "board": "j413",
            "component": component,
            "target": "front_lower",
            "seq": self.sequence[component],
            "generation": generation,
            "event": event,
            "phase": phase,
        }
        if component == "dwc3":
            body["attempt"] = attempt
        body.update(fields)
        entry: dict[str, object] = {
            "_BOOT_ID": BOOT_ID,
            "PRIORITY": "6",
            "__CURSOR": f"fixture:{self.now}",
            "__MONOTONIC_TIMESTAMP": str(self.now),
            "__REALTIME_TIMESTAMP": str(1_800_000_000_000_000 + self.now),
            "MESSAGE": json.dumps(body, separators=(",", ":")) + "\n",
        }
        self.records.append(entry)
        return entry

    def capture(self) -> dict[str, object]:
        return {
            "schema": 1,
            "boot_id": BOOT_ID,
            "collection_start_monotonic_us": 0,
            "collection_end_monotonic_us": self.now + 100,
            "collection_complete": True,
            "identities": deepcopy(MANIFEST["components"]),
            "records": deepcopy(self.records),
        }


def message(entry: dict[str, object]) -> dict[str, object]:
    raw = entry["MESSAGE"]
    if not isinstance(raw, str):
        raise TypeError("fixture message must be a string")
    body: object = json.loads(raw)
    if not isinstance(body, dict) or not all(isinstance(key, str) for key in body):
        raise TypeError("fixture message must be an object")
    return dict(body)


def replace_message(entry: dict[str, object], **fields: object) -> None:
    body = message(entry)
    body.update(fields)
    entry["MESSAGE"] = json.dumps(body, separators=(",", ":")) + "\n"


def records(capture: dict[str, object]) -> list[dict[str, object]]:
    value = capture["records"]
    if not isinstance(value, list):
        raise TypeError("fixture records must be a list")
    if not all(isinstance(entry, dict) for entry in value):
        raise TypeError("fixture records must contain objects")
    return value


def select(
    capture: dict[str, object],
    component: str,
    event: str,
    phase: str,
    *,
    mode: int | None = None,
) -> dict[str, object]:
    for entry in records(capture):
        body = message(entry)
        if (
            body["component"] == component
            and body["event"] == event
            and body["phase"] == phase
            and (mode is None or body.get("mode") == mode)
        ):
            return entry
    raise LookupError("fixture event missing")


def renumber(capture: dict[str, object], component: str) -> None:
    sequence = 0
    for entry in records(capture):
        if message(entry)["component"] == component:
            sequence += 1
            replace_message(entry, seq=sequence)


def complete_trace(
    *,
    order: str = "late",
    atc_generation: int = 1,
    first_failure: bool = False,
) -> Trace:
    trace = Trace()
    if atc_generation == 2:
        trace.add("atc", "probe", "begin")
        trace.add("atc", "probe", "end", ret=-517)
    trace.add("atc", "probe", "begin", generation=atc_generation)
    trace.add("atc", "finalize", "begin", generation=atc_generation)
    trace.add("atc", "usb2_power_off", "begin", generation=atc_generation)
    trace.add("atc", "usb2_power_off", "end", generation=atc_generation)
    trace.add("atc", "finalize", "end", generation=atc_generation, ret=0)
    trace.add("atc", "probe", "end", generation=atc_generation, ret=0)
    trace.add("dwc3", "probe", "begin")
    trace.add("atc", "usb2_power_off", "begin", generation=atc_generation)
    trace.add("atc", "usb2_power_off", "end", generation=atc_generation)
    trace.add("dwc3", "probe", "end", ret=0)
    mux_fields: dict[str, object] = {
        "current_mode": 0,
        "target_mode": 6,
        "swap_lanes": False,
        "pipehandler_up": False,
    }
    trace.add("atc", "mux", "begin", generation=atc_generation, **mux_fields)
    trace.add("atc", "usb2_power_on", "begin", generation=atc_generation)
    trace.add("atc", "usb2_power_on", "end", generation=atc_generation)
    mux_fields["current_mode"] = 6
    trace.add("atc", "mux", "end", generation=atc_generation, ret=0, **mux_fields)
    attempts = (1, 2) if first_failure else (1,)
    for attempt in attempts:
        trace.add("dwc3", "role", "begin", role=1, state=0)
        trace.add("dwc3", "init", "begin", attempt=attempt, state=0, target_state=2)
        present = first_failure and attempt == 2
        trace.add(
            "dwc3", "early_usb2", "begin", attempt=attempt,
            mode=1, usb2_present=present, usb2_error=False,
        )
        trace.add(
            "dwc3", "early_usb2", "end", attempt=attempt,
            mode=1, ret=0, usb2_present=present, usb2_error=False,
        )
        trace.add("dwc3", "reset_deassert", "begin", attempt=attempt)
        trace.add("dwc3", "reset_deassert", "end", attempt=attempt, ret=0)
        trace.add("dwc3", "core_init", "begin", attempt=attempt, state=0)
        if first_failure and attempt == 1:
            trace.add(
                "dwc3", "core_init", "end", attempt=attempt,
                state=0, ret=-517, usb2_present=True, usb2_error=False,
            )
            trace.add("dwc3", "reset_assert", "begin", attempt=attempt)
            trace.add("dwc3", "reset_assert", "end", attempt=attempt, ret=0)
            trace.add(
                "dwc3", "init", "end", attempt=attempt,
                state=0, target_state=2, ret=-517,
            )
            trace.add("dwc3", "role", "end", role=1, state=0, ret=-517)
            continue
        if order == "overlap":
            trace.add(
                "atc", "usb2_set_mode", "begin", generation=atc_generation,
                mode=1, submode=0,
            )
        core_end = trace.add(
            "dwc3", "core_init", "end", attempt=attempt,
            state=1, ret=0, usb2_present=True, usb2_error=False,
        )
        if order in ("overlap", "touching"):
            if order == "touching":
                begin = trace.add(
                    "atc", "usb2_set_mode", "begin", generation=atc_generation,
                    mode=1, submode=0,
                )
                begin["__MONOTONIC_TIMESTAMP"] = core_end["__MONOTONIC_TIMESTAMP"]
            trace.add(
                "atc", "usb2_set_mode", "end", generation=atc_generation,
                mode=1, submode=0, ret=0,
            )
        trace.add("dwc3", "host_init", "begin", attempt=attempt)
        if order == "async":
            trace.add("dwc3", "host_init", "end", attempt=attempt, ret=0)
            trace.add(
                "dwc3", "init", "end", attempt=attempt,
                state=2, target_state=2, ret=0,
            )
            trace.add("dwc3", "role", "end", role=1, state=2, ret=0)
        if order in ("late", "async"):
            trace.add(
                "atc", "usb2_set_mode", "begin", generation=atc_generation,
                mode=5, submode=0,
            )
            trace.add(
                "atc", "usb2_set_mode", "end", generation=atc_generation,
                mode=5, submode=0, ret=-22,
            )
            trace.add(
                "atc", "usb2_set_mode", "begin", generation=atc_generation,
                mode=1, submode=0,
            )
            trace.add(
                "atc", "usb2_set_mode", "end", generation=atc_generation,
                mode=1, submode=0, ret=0,
            )
        if order != "async":
            trace.add("dwc3", "host_init", "end", attempt=attempt, ret=0)
            trace.add(
                "dwc3", "init", "end", attempt=attempt,
                state=2, target_state=2, ret=0,
            )
            trace.add("dwc3", "role", "end", role=1, state=2, ret=0)
    return trace


class TraceValidatorTests(unittest.TestCase):
    def assert_inconclusive(self, capture: object, reason: str | None = None) -> ValidationResult:
        result = validate_capture(capture, MANIFEST)
        self.assertEqual(result.status, "inconclusive")
        self.assertFalse(result.negative_late_setter_claim)
        if reason is not None:
            self.assertIn(reason, result.issues)
        return result

    def test_closed_first_null_call_then_strict_late_host_pair(self) -> None:
        result = validate_capture(complete_trace().capture(), MANIFEST)
        self.assertEqual(result.status, "positive_software_sequence")
        self.assertEqual(len(result.findings), 1)
        self.assertEqual(result.findings[0].attempt, 1)
        self.assertEqual(result.findings[0].dwc3_generation, 1)
        self.assertFalse(result.negative_late_setter_claim)
        self.assertIn("software_order_only", result.limitations)
        self.assertIn("no_caller_attribution", result.limitations)

    def test_host_ss_rejection_and_host_fallback_remain_separate(self) -> None:
        result = validate_capture(complete_trace().capture(), MANIFEST)
        self.assertTrue(any(
            failure.component == "atc" and failure.event == "usb2_set_mode"
            and failure.ret == -22 for failure in result.failed_operations
        ))
        self.assertEqual(result.status, "positive_software_sequence")

    def test_error_handle_is_not_null_or_usable(self) -> None:
        capture = complete_trace().capture()
        for phase in ("begin", "end"):
            replace_message(
                select(capture, "dwc3", "early_usb2", phase),
                usb2_present=True, usb2_error=True,
            )
        result = self.assert_inconclusive(capture)
        self.assertEqual(result.findings, ())

    def test_impossible_null_error_combination_is_rejected(self) -> None:
        capture = complete_trace().capture()
        replace_message(
            select(capture, "dwc3", "early_usb2", "begin"),
            usb2_present=False, usb2_error=True,
        )
        self.assert_inconclusive(capture, "invalid_record")

    def test_first_failed_attempt_is_retained_before_handle_bearing_retry(self) -> None:
        result = self.assert_inconclusive(complete_trace(first_failure=True).capture())
        self.assertTrue(any(
            failure.component == "dwc3" and failure.event == "init"
            and failure.attempt == 1 and failure.ret == -517
            for failure in result.failed_operations
        ))
        self.assertFalse(any(finding.attempt == 1 for finding in result.findings))

    def test_component_generations_are_independent(self) -> None:
        result = validate_capture(complete_trace(atc_generation=2).capture(), MANIFEST)
        self.assertEqual(result.status, "positive_software_sequence")
        self.assertEqual(result.findings[0].dwc3_generation, 1)
        self.assertEqual(result.findings[0].atc_generation, 2)

    def test_overlapping_setter_is_not_strict_late_evidence(self) -> None:
        self.assert_inconclusive(complete_trace(order="overlap").capture())

    def test_equal_timestamps_are_not_strict_late_evidence(self) -> None:
        self.assert_inconclusive(complete_trace(order="touching").capture())

    def test_async_child_after_host_return_has_no_hcd_completion_claim(self) -> None:
        result = validate_capture(complete_trace(order="async").capture(), MANIFEST)
        self.assertEqual(result.status, "positive_software_sequence")
        self.assertIn("host_init_is_not_hcd_completion", result.limitations)
        self.assertIn("no_caller_attribution", result.limitations)

    def test_no_observed_host_setter_is_inconclusive_not_negative(self) -> None:
        self.assert_inconclusive(complete_trace(order="absent").capture())

    def test_lost_final_complete_atc_setter_pair_leaves_consecutive_prefix(self) -> None:
        capture = complete_trace().capture()
        entries = records(capture)
        capture["records"] = [
            entry for entry in entries
            if not (
                message(entry)["component"] == "atc"
                and message(entry)["event"] == "usb2_set_mode"
                and message(entry).get("mode") == 1
            )
        ]
        self.assert_inconclusive(capture)

    def test_cap_and_lost_final_cap_are_both_inconclusive(self) -> None:
        trace = complete_trace()
        fields: dict[str, object] = {
            "current_mode": 6, "target_mode": 6,
            "swap_lanes": False, "pipehandler_up": False,
        }
        while trace.sequence["atc"] < 126:
            trace.add("atc", "mux", "begin", **fields)
            trace.add("atc", "mux", "skip", ret=0, **fields)
        trace.add("atc", "mux", "begin", **fields)
        trace.add("atc", "capture_capped", "end")
        capture = trace.capture()
        self.assert_inconclusive(capture, "capture_capped")
        records(capture).pop()
        self.assert_inconclusive(capture)

    def test_missing_start_is_not_a_successful_suffix(self) -> None:
        capture = complete_trace().capture()
        entries = records(capture)
        entries.remove(select(capture, "atc", "probe", "begin"))
        self.assert_inconclusive(capture)

    def test_missing_tail_operation_end_is_inconclusive(self) -> None:
        capture = complete_trace().capture()
        entries = records(capture)
        entries.remove(select(capture, "dwc3", "host_init", "end"))
        renumber(capture, "dwc3")
        self.assert_inconclusive(capture, "unclosed_pair")

    def test_sequence_gap(self) -> None:
        capture = complete_trace().capture()
        records(capture).remove(select(capture, "atc", "usb2_power_off", "end"))
        self.assert_inconclusive(capture, "sequence_gap")

    def test_duplicate_sequence(self) -> None:
        capture = complete_trace().capture()
        replace_message(select(capture, "atc", "finalize", "begin"), seq=1)
        self.assert_inconclusive(capture, "sequence_duplicate")

    def test_reservation_insertion_reordering_is_not_silently_sorted(self) -> None:
        capture = complete_trace().capture()
        first = select(capture, "atc", "usb2_power_off", "begin")
        second = select(capture, "atc", "usb2_power_off", "end")
        first["MESSAGE"], second["MESSAGE"] = second["MESSAGE"], first["MESSAGE"]
        self.assert_inconclusive(capture, "sequence_reordered")

    def test_generation_restart_is_rejected(self) -> None:
        trace = complete_trace()
        trace.add("atc", "probe", "begin", generation=1)
        trace.add("atc", "probe", "end", generation=1, ret=-517)
        self.assert_inconclusive(trace.capture(), "generation_order")

    def test_initial_attempt_two_is_not_first_attempt(self) -> None:
        capture = complete_trace().capture()
        for entry in records(capture):
            body = message(entry)
            if body["component"] == "dwc3" and body.get("attempt") == 1:
                replace_message(entry, attempt=2)
        self.assert_inconclusive(capture, "attempt_order")

    def test_malformed_json(self) -> None:
        capture = complete_trace().capture()
        records(capture)[0]["MESSAGE"] = '{"schema":1,"revision":'
        self.assert_inconclusive(capture, "invalid_json")

    def test_duplicate_json_keys_are_rejected(self) -> None:
        capture = complete_trace().capture()
        entry = records(capture)[0]
        raw = entry["MESSAGE"]
        if not isinstance(raw, str):
            raise TypeError("fixture message must be a string")
        entry["MESSAGE"] = raw.replace('{"schema":1,', '{"schema":1,"schema":1,', 1)
        self.assert_inconclusive(capture, "duplicate_json_key")

    def test_journal_may_strip_source_newline(self) -> None:
        capture = complete_trace().capture()
        for entry in records(capture):
            raw = entry["MESSAGE"]
            if not isinstance(raw, str):
                raise TypeError("fixture message must be a string")
            entry["MESSAGE"] = raw.removesuffix("\n")
        result = validate_capture(capture, MANIFEST)
        self.assertEqual(result.status, "positive_software_sequence")

    def test_wrong_revision_target_board_and_unknown_field(self) -> None:
        for fields in (
            {"revision": "dev147-usbdiag1-v0"},
            {"target": "rear_upper"},
            {"board": "j293"},
            {"serial": "must-not-be-accepted"},
        ):
            with self.subTest(fields=fields):
                capture = complete_trace().capture()
                replace_message(records(capture)[0], **fields)
                self.assert_inconclusive(capture, "invalid_record")

    def test_wrong_observed_build_identity(self) -> None:
        capture = complete_trace().capture()
        capture["identities"] = {
            "dwc3": {"sha256": "d" * 64, "build_id": "f" * 40},
            "atc": {"sha256": "a" * 64, "build_id": "2" * 40},
        }
        self.assert_inconclusive(capture, "identity_mismatch")

    def test_wrong_manifest_revision(self) -> None:
        manifest = deepcopy(MANIFEST)
        manifest["revision"] = "different"
        result = validate_capture(complete_trace().capture(), manifest)
        self.assertEqual(result.status, "inconclusive")
        self.assertIn("invalid_manifest", result.issues)

    def test_mixed_boot_priority_and_missing_envelope(self) -> None:
        for key, value in (("_BOOT_ID", "f" * 32), ("PRIORITY", "4"), ("__CURSOR", "")):
            with self.subTest(key=key):
                capture = complete_trace().capture()
                records(capture)[0][key] = value
                self.assert_inconclusive(capture, "invalid_envelope")

    def test_duplicate_cursor(self) -> None:
        capture = complete_trace().capture()
        records(capture)[1]["__CURSOR"] = records(capture)[0]["__CURSOR"]
        self.assert_inconclusive(capture, "invalid_envelope")

    def test_collection_boundary_must_be_declared_and_complete(self) -> None:
        for key, value in (
            ("collection_complete", False),
            ("collection_end_monotonic_us", 1),
            ("collection_start_monotonic_us", 1),
        ):
            with self.subTest(key=key):
                capture = complete_trace().capture()
                capture[key] = value
                self.assert_inconclusive(capture, "collection_boundary")

    def test_oversized_record(self) -> None:
        capture = complete_trace().capture()
        records(capture)[0]["MESSAGE"] = " " * 385
        self.assert_inconclusive(capture, "record_too_long")

    def test_bool_and_fractional_sequence_are_not_integer_evidence(self) -> None:
        for value in (True, 1.5):
            with self.subTest(value=value):
                capture = complete_trace().capture()
                replace_message(records(capture)[0], seq=value)
                self.assert_inconclusive(capture, "invalid_record")

    def test_explicit_failed_host_call_is_not_a_successful_reproduction(self) -> None:
        capture = complete_trace().capture()
        replace_message(select(capture, "dwc3", "host_init", "end"), ret=-5)
        replace_message(select(capture, "dwc3", "init", "end"), ret=-5, state=1)
        replace_message(select(capture, "dwc3", "role", "end"), ret=-5, state=1)
        result = self.assert_inconclusive(capture)
        self.assertTrue(any(
            failure.event == "host_init" and failure.ret == -5
            for failure in result.failed_operations
        ))

    def test_pair_request_changes_are_rejected(self) -> None:
        capture = complete_trace().capture()
        replace_message(select(capture, "atc", "usb2_set_mode", "end", mode=1), submode=9)
        self.assert_inconclusive(capture, "pair_mismatch")


if __name__ == "__main__":
    unittest.main()
