"""Independent producer-consistency regression checks. No hardware model."""

import unittest

from test_trace_validator import MANIFEST, complete_trace, message, records, renumber, replace_message, select
from trace_validator import validate_capture


class ProbeFinalizeReview(unittest.TestCase):
  def require_inconclusive(self, capture: object) -> None:
    result = validate_capture(capture, MANIFEST)
    self.assertEqual(result.status, "inconclusive")
    self.assertEqual(result.findings, ())
    self.assertIn("incomplete_probe", result.issues)
    self.assertFalse(result.negative_late_setter_claim)

  def test_atc_success_without_finalize_pair(self) -> None:
    capture = complete_trace().capture()
    capture["records"] = [entry for entry in records(capture) if not (
      message(entry)["component"] == "atc" and message(entry)["event"] == "finalize"
    )]
    renumber(capture, "atc")
    self.require_inconclusive(capture)

  def test_atc_failed_finalize_cannot_have_successful_probe(self) -> None:
    capture = complete_trace().capture()
    replace_message(select(capture, "atc", "finalize", "end"), ret=-517)
    self.require_inconclusive(capture)

  def test_atc_finalize_cannot_finish_after_probe(self) -> None:
    capture = complete_trace().capture()
    probe_end = select(capture, "atc", "probe", "end")
    finalize_end = select(capture, "atc", "finalize", "end")
    probe_end["MESSAGE"], finalize_end["MESSAGE"] = finalize_end["MESSAGE"], probe_end["MESSAGE"]
    renumber(capture, "atc")
    self.require_inconclusive(capture)
