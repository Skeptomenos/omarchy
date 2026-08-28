"""Run only authenticated T1 fixture tests inside the new offline sandbox.

The outer launcher authenticates this runner and the read-only directory.
This runner checks every locally imported source before importing it. It does
not start subprocesses, write files, read environment variables, or collect
hardware data. Test exceptions are never reported as semantic assertion RED.
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
  "t1_trace.py": "8c1e90a30f68c9237948e47f583038aee0d4584fa2459779e518b1630372e0fe",
  "trace_fixtures.py": "1831f4f01ff2286840d78c0f658ffeba1850468e05d4958d8982391ce667cd55",
  "test_t1_trace.py": "592a067adfa939634008a039bd51f698cb620d216e7e9396a49dfb8731f9ec1b",
  "t1-record.schema.json": "27218551534feaaf0e1cd812c3f302ad25f00769d0e536a570d354f716102f01",
}
RED_TESTS = (
  "T1TraceTests.test_complete_reordered_and_interleaved_capture",
  "T1TraceTests.test_missing_mandatory_tail_and_terminal_cap",
)
EXPECTED_COUNTS = {"red": 2, "all": 31}


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
  """A fixed setup failure, not an assertion against missing behavior."""


def preflight() -> str:
  if sys.argv[1:] not in (["red"], ["all"]):
    raise SetupError("invalid_mode")
  if sys.version_info[:2] != (3, 14):
    raise SetupError("wrong_python")
  if not (sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode):
    raise SetupError("missing_python_isolation")
  if Path.cwd() != Path("/work") or Path(__file__) != ROOT / "run_tests.py":
    raise SetupError("wrong_sandbox_paths")
  if os.getuid() == 0 or os.geteuid() != os.getuid():
    raise SetupError("privileged_process")
  for forbidden in ("/home", "/root", "/boot", "/sys", "/proc", "/run"):
    if Path(forbidden).exists():
      raise SetupError("host_tree_visible")
  if {path.name for path in ROOT.iterdir()} != set(PINS) | {"README.md", "run_tests.py"}:
    raise SetupError("unexpected_input_file")
  for name, expected in PINS.items():
    path = ROOT / name
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or not 0 < info.st_size <= 262_144:
      raise SetupError("invalid_pinned_source")
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
      raise SetupError("source_pin_mismatch")
  schema: object = json.loads((ROOT / "t1-record.schema.json").read_text(encoding="ascii"))
  if not isinstance(schema, dict) or schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
    raise SetupError("invalid_schema_document")
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
  }, separators=(",", ":")))


def main() -> int:
  # A process-level exception boundary is deliberate: any setup/import defect
  # must exit 2, including a defect not anticipated by this initial draft.
  try:
    mode = preflight()
    sys.path.insert(0, str(ROOT))
    test_module = importlib.import_module("test_t1_trace")
    test_module.fixture_preflight()
    if mode == "red":
      suite = unittest.defaultTestLoader.loadTestsFromNames(RED_TESTS, test_module)
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
