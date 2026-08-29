"""Source-pinned, zero-child runner for the new synthetic capture tests.

The orchestrator must authenticate this runner and its frozen directory
before launch. Local source imports happen only after the fixed preflight.
No receipt or fixture can change the operationally closed result.
"""

from dataclasses import dataclass
import hashlib
import importlib
import json
import os
from pathlib import Path
import stat
import sys
import unittest
from typing import Literal


ROOT = Path("/inputs/tests")
PINS = {
  "capture_binding.py": "09a2a4d2631c64ac428d3071b4c9dabbe79b7fb4ac8b2f5682fba9506b8263ce",
  "collector_recipe.py": "911aeeb2c464b3514280f74a78961f190fe4d7d86122e2a014343b4f1604a40e",
  "test_capture_binding.py": "2237cb697530556f811eae873e044edcc72f35bfc58e3ce247d20c911343c400",
  "capture-contract.md": "34137a59ac44f1790d6ab18809a4a71eaa2b6e1e40724a38bc1e5c4a3fdca87e",
  "t1_trace.py": "8c1e90a30f68c9237948e47f583038aee0d4584fa2459779e518b1630372e0fe",
}
RED_TESTS = (
  "CaptureBindingTests.test_complete_full_boot_projection",
  "CaptureBindingTests.test_receipt_hash_and_boot_mismatch",
  "CaptureBindingTests.test_collector_plan_is_exact_all_priority",
)
REVIEW_TESTS = (
  "CaptureBindingTests.test_malformed_and_mixed_t1_family_is_not_filtered_out",
  "CaptureBindingTests.test_boot_samples_and_module_note_are_exact",
)
EXPECTED_COUNTS = {"red": 3, "review": 2, "all": 21}


@dataclass(frozen=True)
class RunOutcome:
  status: Literal["pass", "assertion_red", "test_error", "test_incomplete"]
  exit_code: int


def evaluate_result(result: unittest.TestResult, *, expected_tests: int) -> RunOutcome:
  if result.errors:
    return RunOutcome("test_error", 2)
  if (
    result.testsRun != expected_tests or result.skipped
    or result.expectedFailures or result.unexpectedSuccesses
  ):
    return RunOutcome("test_incomplete", 2)
  if result.failures:
    return RunOutcome("assertion_red", 1)
  return RunOutcome("pass", 0)


class SetupError(RuntimeError):
  """A setup defect is not semantic assertion RED."""


def preflight() -> str:
  if sys.argv[1:] not in (["red"], ["review"], ["all"]):
    raise SetupError("invalid_mode")
  if sys.version_info[:2] != (3, 14):
    raise SetupError("wrong_python")
  if not (sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode):
    raise SetupError("missing_python_isolation")
  if Path.cwd() != Path("/work") or Path(__file__) != ROOT / "run_capture_tests.py":
    raise SetupError("wrong_sandbox_paths")
  if os.getuid() == 0 or os.geteuid() != os.getuid():
    raise SetupError("privileged_process")
  for forbidden in ("/home", "/root", "/boot", "/sys", "/proc", "/run"):
    if Path(forbidden).exists():
      raise SetupError("host_tree_visible")
  if {path.name for path in ROOT.iterdir()} != set(PINS) | {"run_capture_tests.py"}:
    raise SetupError("unexpected_input_file")
  for name, expected in PINS.items():
    path = ROOT / name
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or not 0 < info.st_size <= 262_144:
      raise SetupError("invalid_pinned_source")
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
      raise SetupError("source_pin_mismatch")
  return sys.argv[1]


def report(
  status: str, *, tests: int = 0, failures: int = 0, errors: int = 0,
  skipped: int = 0, expected_failures: int = 0, unexpected_successes: int = 0,
) -> None:
  print(json.dumps({
    "status": status, "tests": tests, "failures": failures, "errors": errors,
    "skipped": skipped, "expected_failures": expected_failures,
    "unexpected_successes": unexpected_successes,
    "hardware_evidence": False, "operational_acceptance": False,
    "workload_children": 0,
  }, separators=(",", ":")))


def main() -> int:
  try:
    mode = preflight()
    sys.path.insert(0, str(ROOT))
    test_module = importlib.import_module("test_capture_binding")
    test_module.fixture_preflight()
    if mode in ("red", "review"):
      names = RED_TESTS if mode == "red" else REVIEW_TESTS
      suite = unittest.defaultTestLoader.loadTestsFromNames(names, test_module)
    else:
      suite = unittest.defaultTestLoader.loadTestsFromModule(test_module)
    if suite.countTestCases() != EXPECTED_COUNTS[mode]:
      raise SetupError("wrong_test_count")
  except Exception:
    report("setup_error", errors=1)
    return 2
  try:
    result = unittest.TextTestRunner(verbosity=2).run(suite)
  except Exception:
    report("execution_error", errors=1)
    return 2
  outcome = evaluate_result(result, expected_tests=EXPECTED_COUNTS[mode])
  report(
    outcome.status, tests=result.testsRun, failures=len(result.failures),
    errors=len(result.errors), skipped=len(result.skipped),
    expected_failures=len(result.expectedFailures),
    unexpected_successes=len(result.unexpectedSuccesses),
  )
  return outcome.exit_code


if __name__ == "__main__":
  raise SystemExit(main())
