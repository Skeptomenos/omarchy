"""Fixed thirteen-test GREEN runner; imports follow source authentication.

The orchestrator separately pins this runner and every read-only input.
This program has no production entry, test selection flag or live command.
"""

import hashlib
import importlib
import json
import os
from pathlib import Path
import stat
import sys
import unittest


ROOT = Path("/inputs/tests")
RUNNER = "run_fixed_capture_tests.py"
PINS = {
  "bounded_child.py": "7b2e2b0fa0e733d6956a4ba55a376a8ff708706fd3f3393d0014a78df65144fa",
  "fixed_t1_binding.py": "de49d6c97a58d417ef5ac5d48f059f1218c9aeeeea48b175b82408d6d4cdbc56",
  "fixed_t1_collector.py": "8372d6497c2f39a12aa2202e8734a2e4e889ac71e5ed19ec56a96efc810f2f6a",
  "capture_binding.py": "09a2a4d2631c64ac428d3071b4c9dabbe79b7fb4ac8b2f5682fba9506b8263ce",
  "t1_trace.py": "8c1e90a30f68c9237948e47f583038aee0d4584fa2459779e518b1630372e0fe",
  "test_fixed_capture.py": "e7e207267c18f3789a9895050d2d30f9eec6dcd6b00155bed71c12762c48d942",
  "test_capture_focus.py": "3a1de2e120668b57bb1f976a3800a76424b0f1f2aab0fe333ae0c1dbf324f0ba",
  "green-contract.md": "06500f373812b5b9faa42aee3afd31914a7840f63c0a8a1b8a3f58ce4b4ccb5d",
}
PREFIX = Path("/inputs/staging-prefix")
PREFIX_SHA256 = "32076acedfc5bd40b88cded89b0d37cd545caaae885d4acd29444e9fe310d03e"
TESTS = (
  "FixedCaptureTests.test_actual_fixture_child_retains_observed_bytes_and_argv",
  "FixedCaptureTests.test_over_cap_child_is_actively_stopped_and_reaped",
  "FixedCaptureTests.test_fixed_t1_binding_positive_and_exact_refusals",
)


class SetupError(RuntimeError):
  """Source/setup drift is never an accepted semantic RED."""


def identity(info: os.stat_result) -> tuple[int, ...]:
  return (
    info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_gid,
    info.st_nlink, info.st_size, info.st_mtime_ns, info.st_ctime_ns,
  )


def read_pinned(path: Path, expected: str | None) -> dict[str, object]:
  before = path.lstat()
  if (
    not stat.S_ISREG(before.st_mode) or stat.S_IMODE(before.st_mode) != 0o600
    or before.st_nlink != 1 or (before.st_uid, before.st_gid) != (1001, 1001)
    or not 0 < before.st_size <= 262_144
  ):
    raise SetupError("invalid_input_file")
  descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK)
  try:
    if identity(before) != identity(os.fstat(descriptor)):
      raise SetupError("input_replaced")
    raw = bytearray()
    while len(raw) <= 262_144:
      piece = os.read(descriptor, min(65_536, 262_145 - len(raw)))
      if not piece:
        break
      raw.extend(piece)
    if (
      len(raw) != before.st_size or identity(before) != identity(os.fstat(descriptor))
      or identity(before) != identity(path.lstat())
    ):
      raise SetupError("input_changed_or_oversized")
  finally:
    os.close(descriptor)
  digest = hashlib.sha256(raw).hexdigest()
  if expected is not None and digest != expected:
    raise SetupError("source_pin_mismatch")
  if path == PREFIX and (len(raw) != 5_870 or raw.count(b"\n") != 45):
    raise SetupError("staging_prefix_shape")
  return {"sha256": digest, "identity": list(identity(before))}


def input_snapshot() -> dict[str, object]:
  directory = ROOT.lstat()
  if (
    not stat.S_ISDIR(directory.st_mode) or stat.S_IMODE(directory.st_mode) != 0o700
    or (directory.st_uid, directory.st_gid) != (1001, 1001)
    or {entry.name for entry in ROOT.iterdir()} != set(PINS) | {RUNNER}
  ):
    raise SetupError("source_directory_drift")
  result: dict[str, object] = {"directory": list(identity(directory))}
  for name, expected in PINS.items():
    result[name] = read_pinned(ROOT / name, expected)
  result[RUNNER] = read_pinned(ROOT / RUNNER, None)
  result["staging-prefix"] = read_pinned(PREFIX, PREFIX_SHA256)
  result["proof"] = read_pinned(
    Path("/inputs/proof"), "9133cb64040f9df0daf9aa0caaab913c90fe7ce5c9bf59a19c71ce3e36fb0c94",
  )
  return result


def preflight() -> dict[str, object]:
  if sys.argv != [str(ROOT / RUNNER)]:
    raise SetupError("unexpected_argv")
  if sys.version_info[:2] != (3, 14) or sys.executable != "/usr/bin/python3.14":
    raise SetupError("wrong_python")
  if not (sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode):
    raise SetupError("missing_python_isolation")
  if (os.getuid(), os.geteuid(), os.getgid(), os.getegid()) != (1001, 1001, 1001, 1001):
    raise SetupError("wrong_identity")
  if Path.cwd() != Path("/work") or Path(__file__) != ROOT / RUNNER:
    raise SetupError("wrong_sandbox_paths")
  if {entry.name for entry in Path("/inputs").iterdir()} != {"proof", "tests", "staging-prefix"}:
    raise SetupError("unexpected_binding")
  for forbidden in ("/home", "/root", "/boot", "/sys", "/proc", "/run", "/usr/lib/modules"):
    if os.path.lexists(forbidden):
      raise SetupError("host_tree_visible")
  harness_files = {"descriptor-sentinel", "stdout.log", "stderr.log", "probe-write"}
  if {entry.name for entry in Path("/work").iterdir()} != harness_files:
    raise SetupError("unexpected_initial_work_files")
  for name in harness_files:
    info = (Path("/work") / name).lstat()
    if (
      not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o600
      or (info.st_uid, info.st_gid, info.st_nlink) != (1001, 1001, 1)
      or not 0 <= info.st_size <= 262_144
    ):
      raise SetupError("invalid_harness_file")
  if (Path("/work") / "descriptor-sentinel").stat().st_size != 0:
    raise SetupError("changed_descriptor_sentinel")
  if (Path("/work") / "probe-write").read_bytes() != b"private sandbox write\n":
    raise SetupError("changed_probe_write")
  for descriptor, name in ((1, "stdout.log"), (2, "stderr.log")):
    actual = os.fstat(descriptor)
    expected = (Path("/work") / name).lstat()
    if (actual.st_dev, actual.st_ino) != (expected.st_dev, expected.st_ino):
      raise SetupError("wrong_harness_output_descriptor")
  return input_snapshot()


def save(name: str, value: object) -> None:
  raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("ascii") + b"\n"
  descriptor = os.open(
    Path("/work") / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
    0o600,
  )
  with os.fdopen(descriptor, "wb") as stream:
    if stream.write(raw) != len(raw):
      raise SetupError("short_evidence_write")


def report(status: str, result: unittest.TestResult | None = None) -> None:
  print(json.dumps({
    "status": status,
    "tests": 0 if result is None else result.testsRun,
    "failures": 0 if result is None else len(result.failures),
    "errors": 0 if result is None else len(result.errors),
    "skipped": 0 if result is None else len(result.skipped),
    "planned_fixture_child_invocations": 21,
    "expected_valid_execution_receipts": 19,
    "expected_partial_fixture_cases": ["child-json-collision", "same-inode-tamper"],
    "live_entry_invoked": False, "hardware_evidence": False,
    "operational_acceptance": False,
  }, separators=(",", ":")))


def main() -> int:
  try:
    before = preflight()
    sys.path.insert(0, str(ROOT))
    test_module = importlib.import_module("test_fixed_capture")
    test_module.fixture_preflight()
    focus_module = importlib.import_module("test_capture_focus")
    suite = unittest.TestSuite((
      unittest.defaultTestLoader.loadTestsFromNames(TESTS, test_module),
      unittest.defaultTestLoader.loadTestsFromModule(focus_module),
    ))
    if suite.countTestCases() != 13:
      raise SetupError("wrong_test_count")
    save("setup.json", {"status": "pass", "inputs": before, "original_tests": list(TESTS), "focused_methods": 10, "total_methods": 13})
  except Exception:
    report("setup_error")
    return 2
  try:
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    after = input_snapshot()
    if before != after:
      raise SetupError("post_input_drift")
    save("after.json", {"status": "pass", "inputs_unchanged": True, "inputs": after})
  except Exception:
    report("execution_or_postcheck_error")
    return 2
  if (
    result.testsRun != 13 or result.errors or result.skipped
    or result.expectedFailures or result.unexpectedSuccesses
  ):
    report("test_error_or_incomplete", result)
    return 2
  if result.failures:
    report("assertion_failure", result)
    return 1
  report("pass", result)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
