"""Three independent RED oracles; fixture execution is not journal evidence.

The two internal engine cases use actual Python argv. The separate binding
case uses explicitly synthetic submitted journal/staging/selection bytes.
None of these inputs attests an actual staging operation or T1 boot.
"""

from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import signal
import stat
import unittest

from bounded_child import ChildCapture, _Limits, _capture_child
from capture_binding import CaptureFiles, inspect_capture_files
from fixed_t1_binding import BindingError, FixedBinding, bind_fixed_t1


FIXTURE_LABEL = "synthetic-fixed-t1-binding-not-staging-or-boot-evidence"
PREFIX_PATH = Path("/inputs/staging-prefix")
PREFIX_SHA256 = "32076acedfc5bd40b88cded89b0d37cd545caaae885d4acd29444e9fe310d03e"
IMAGE_NAME = "initramfs-linux-asahi-dpalt-tipddiag1.img"
IMAGE_SHA256 = "c72c36736cebba0d6d5b67f47b02330c35d3ef81fed9bf5b3315095b0dd765fe"
HELPER_SHA256 = "6b20d119791f4322e101a92b9e5b850ba3098d35dbf966f2d7918cb3918694f9"
BOOT = "0123456789abcdef0123456789abcdef"
BOOT_RAW = b"01234567-89ab-cdef-0123-456789abcdef\n"
BUILD_ID = "40aa54382047ba36b02c9ac0da65a213862a77ad"
NOTE = bytes.fromhex("040000001400000003000000474e5500" + BUILD_ID)
JOURNAL_ARGV = (
  "/usr/bin/journalctl", "--dmesg", "--boot=" + BOOT,
  "--all", "--output=json", "--no-pager", "--no-tail",
)
SUCCESS_ARGV = (
  "/usr/bin/python3.14", "-I", "-S", "-B", "-c",
  "import os; os.write(1, b'fixture stdout\\n'); os.write(2, b'fixture stderr\\n')",
)
CAP_ARGV = (
  "/usr/bin/python3.14", "-I", "-S", "-B", "-c",
  "import os,time; os.write(1, b'X' * 2048); time.sleep(5)",
)
COMPLETION = (
  b"STAGING ONLY PASS: /boot/initramfs-linux-asahi-dpalt-tipddiag1.img\n"
  b"Checks retained in /boot/.dev147-tipddiag-stage.A1b2C3d4E5\n"
  b"No reboot permission. Normal boot is unchanged; this T1 TIPD diagnostic image is untested at startup.\n"
)


def encoded(value: object) -> bytes:
  return json.dumps(value, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def digest(raw: bytes) -> str:
  return hashlib.sha256(raw).hexdigest()


def synthetic_capture() -> CaptureFiles:
  """A closed two-record prefix; wholly absent later events stay unknowable."""
  rows: list[dict[str, str]] = []
  for sequence, phase in ((1, "begin"), (2, "end")):
    message: dict[str, object] = dict(
      rev="dev147-tipddiag1-v1", board="j413", target="front_lower",
      component="tipd", seq=sequence, gen=1, worker=0, event="init", phase=phase,
    )
    if phase == "end":
      message.update(reason="vid", ret=-19)
    rows.append(dict(
      _BOOT_ID=BOOT, _TRANSPORT="kernel", PRIORITY="6",
      __CURSOR=f"synthetic-fixed-binding:{sequence}",
      __MONOTONIC_TIMESTAMP=str(sequence), __REALTIME_TIMESTAMP=str(100 + sequence),
      MESSAGE=encoded(message).decode("ascii") + "\n",
    ))
  stdout = b"".join(encoded(row) + b"\n" for row in rows)
  sample = dict(boot_id_sha256=digest(BOOT_RAW), tipd_note_sha256=digest(NOTE))
  receipt = encoded(dict(
    schema="dev147-t1-collector-receipt1", argv=list(JOURNAL_ARGV),
    kernel_release="7.1.6-1-1-ARCH", start_monotonic_us=100, end_monotonic_us=200,
    exit_code=0, timed_out=False, stdout_limit_exceeded=False, stderr_limit_exceeded=False,
    stdout_bytes=len(stdout), stderr_bytes=0, stdout_sha256=digest(stdout),
    stderr_sha256=digest(b""), before=sample, after=sample,
  ))
  return CaptureFiles(stdout, b"", receipt, BOOT_RAW, NOTE, BOOT_RAW, NOTE)


def staging_stdout() -> bytes:
  return PREFIX_PATH.read_bytes() + COMPLETION


def staging_attestation(
  stdout: bytes, stderr: bytes = b"", changes: dict[str, object] | None = None,
) -> bytes:
  value: dict[str, object] = dict(
    schema="dev147-t1-staging-attestation1", helper_sha256=HELPER_SHA256,
    image_sha256=IMAGE_SHA256, image_bytes=19_209_545,
    stdout_sha256=digest(stdout), stderr_sha256=digest(stderr), reported_exit_code=0,
  )
  value.update({} if changes is None else changes)
  return encoded(value)


def selection_attestation(changes: dict[str, object] | None = None) -> bytes:
  value: dict[str, object] = dict(
    schema="dev147-t1-selection-attestation1", selected_initrd=IMAGE_NAME, boot_id=BOOT,
  )
  value.update({} if changes is None else changes)
  return encoded(value)


def fixture_preflight() -> None:
  prefix = PREFIX_PATH.read_bytes()
  if len(prefix) != 5_870 or prefix.count(b"\n") != 45 or digest(prefix) != PREFIX_SHA256:
    raise ValueError("staging_prefix_fixture_drift")
  if COMPLETION.count(b"\n") != 3 or len(BOOT_RAW) != 37 or len(NOTE) != 36:
    raise ValueError("fixture_literal_drift")
  sample = synthetic_capture()
  facts = inspect_capture_files(sample)
  if (
    facts.boot_id != BOOT or facts.tipd_note_build_id != BUILD_ID
    or facts.structural_status != "structurally_complete"
    or len(facts.records) != 2 or facts.operationally_accepted
  ):
    raise ValueError("synthetic_consistency_fixture_drift")
  if SUCCESS_ARGV[:5] != CAP_ARGV[:5] or SUCCESS_ARGV[0] == JOURNAL_ARGV[0]:
    raise ValueError("fixture_command_identity_drift")


class FixedCaptureTests(unittest.TestCase):
  def assert_private_files(self, directory: Path, result: ChildCapture) -> None:
    self.assertEqual({path.name for path in directory.iterdir()}, {"stdout.bin", "stderr.bin", "child.json"})
    directory_info = directory.lstat()
    self.assertEqual(stat.S_IMODE(directory_info.st_mode), 0o700)
    self.assertEqual((directory_info.st_uid, directory_info.st_gid), (1001, 1001))
    for name in ("stdout.bin", "stderr.bin", "child.json"):
      info = (directory / name).lstat()
      self.assertTrue(stat.S_ISREG(info.st_mode))
      self.assertEqual((stat.S_IMODE(info.st_mode), info.st_uid, info.st_gid, info.st_nlink), (0o600, 1001, 1001, 1))
    stdout = (directory / "stdout.bin").read_bytes()
    stderr = (directory / "stderr.bin").read_bytes()
    receipt = json.loads((directory / "child.json").read_bytes())
    self.assertEqual(receipt["argv"], list(result.argv))
    self.assertEqual(receipt["status"], result.status)
    self.assertEqual(receipt["pid"], result.pid)
    self.assertEqual(receipt["process_group"], result.process_group)
    self.assertEqual(receipt["exit_code"], result.exit_code)
    self.assertEqual(receipt["killed"], result.killed)
    self.assertEqual(receipt["reaped"], result.reaped)
    self.assertEqual((receipt["stdout_retained"], receipt["stderr_retained"]), (len(stdout), len(stderr)))
    self.assertEqual((receipt["stdout_sha256"], receipt["stderr_sha256"]), (digest(stdout), digest(stderr)))
    self.assertFalse(receipt["overall_capture_accepted"])
    self.assertFalse(receipt["emitted_bytes_known"])
    self.assertEqual((result.stdout_sha256, result.stderr_sha256), (digest(stdout), digest(stderr)))
    self.assertGreater(result.pid, 0)
    self.assertEqual(result.process_group, result.pid)
    self.assertNotEqual(result.process_group, os.getpgrp())
    self.assertTrue(result.reaped)
    with self.assertRaises(ProcessLookupError):
      os.kill(result.pid, 0)
    self.assertFalse(result.overall_capture_accepted)
    self.assertFalse(result.emitted_bytes_known)

  def test_actual_fixture_child_retains_observed_bytes_and_argv(self) -> None:
    directory = Path("/work/success")
    result = _capture_child(SUCCESS_ARGV, directory, _Limits(2_000_000, 1_024, 1_024, 250_000))
    self.assertIsInstance(result, ChildCapture, "active fixture execution is unimplemented")
    assert isinstance(result, ChildCapture)
    self.assertEqual(result.argv, SUCCESS_ARGV)
    self.assertNotEqual(result.argv, JOURNAL_ARGV)
    self.assertEqual((result.status, result.exit_code, result.killed), ("ok", 0, False))
    self.assertEqual((result.stdout_observed, result.stdout_retained), (15, 15))
    self.assertEqual((result.stderr_observed, result.stderr_retained), (15, 15))
    self.assertTrue(result.stdout_eof and result.stderr_eof)
    self.assertLessEqual(result.end_monotonic_us - result.start_monotonic_us, 2_000_000)
    self.assertEqual((directory / "stdout.bin").read_bytes(), b"fixture stdout\n")
    self.assertEqual((directory / "stderr.bin").read_bytes(), b"fixture stderr\n")
    self.assert_private_files(directory, result)

  def test_over_cap_child_is_actively_stopped_and_reaped(self) -> None:
    directory = Path("/work/over-cap")
    result = _capture_child(CAP_ARGV, directory, _Limits(2_000_000, 1_024, 1_024, 250_000))
    self.assertIsInstance(result, ChildCapture, "active size-limit enforcement is unimplemented")
    assert isinstance(result, ChildCapture)
    self.assertEqual(result.argv, CAP_ARGV)
    self.assertEqual((result.status, result.exit_code), ("stdout_limit", -signal.SIGKILL))
    self.assertTrue(result.killed and result.reaped)
    self.assertGreater(result.stdout_observed, 1_024)
    self.assertLessEqual(result.stdout_observed, 2_048)
    self.assertEqual((result.stdout_retained, result.stderr_retained), (1_024, 0))
    self.assertEqual((directory / "stdout.bin").read_bytes(), b"X" * 1_024)
    self.assertEqual((directory / "stderr.bin").read_bytes(), b"")
    self.assertLessEqual(result.end_monotonic_us - result.start_monotonic_us, 2_000_000)
    self.assert_private_files(directory, result)

  def test_fixed_t1_binding_positive_and_exact_refusals(self) -> None:
    sample = synthetic_capture()
    stdout = staging_stdout()
    supplied = dict(
      staging_attestation=staging_attestation(stdout), staging_stdout=stdout,
      staging_stderr=b"", selection_attestation=selection_attestation(),
    )
    result = bind_fixed_t1(sample, **supplied)
    self.assertIsInstance(result, FixedBinding, "exact fixed-T1 binding is unimplemented")
    assert isinstance(result, FixedBinding)
    self.assertEqual((result.status, result.codes), ("consistent_user_attestation", ()))
    self.assertEqual((result.selected_initrd, result.image_sha256, result.image_bytes), (IMAGE_NAME, IMAGE_SHA256, 19_209_545))
    self.assertEqual(result.expected_tipd_sha256, "a0fdadc351261643545e5afd8561923be99431661c447084336c9318f5b0c02f")
    self.assertEqual((result.facts.boot_id, result.facts.tipd_note_build_id), (BOOT, BUILD_ID))
    self.assertEqual(result.reported_staging_exit_code, 0)
    self.assertEqual(result.staging_evidence, "user_attested_only")
    self.assertEqual(result.selection_evidence, "user_attested_only")
    self.assertEqual(result.collection_evidence, "submitted_bytes_consistency_only")
    for field in (
      "operationally_accepted", "initrd_boot_proven", "earliest_load_proven",
      "negative_sender_claim", "receiver_delivery_claim", "hardware_acceptance",
    ):
      self.assertFalse(getattr(result, field))

    unknown = bind_fixed_t1(sample, **dict(
      supplied, staging_attestation=staging_attestation(stdout, changes={"reported_exit_code": None}),
    ))
    self.assertIsInstance(unknown, FixedBinding)
    assert isinstance(unknown, FixedBinding)
    self.assertEqual((unknown.status, unknown.codes, unknown.reported_staging_exit_code), (
      "inconclusive", ("staging_exit_unobserved",), None,
    ))
    mutations: tuple[tuple[dict[str, bytes], str], ...] = (
      ({"staging_attestation": staging_attestation(stdout, changes={"image_sha256": "0" * 64})}, "staging_identity_mismatch"),
      ({"staging_attestation": staging_attestation(stdout, changes={"helper_sha256": "0" * 64})}, "staging_identity_mismatch"),
      ({"staging_attestation": staging_attestation(stdout, changes={"image_bytes": 19_209_544})}, "staging_identity_mismatch"),
      ({"staging_attestation": staging_attestation(stdout, changes={"image_bytes": True})}, "invalid_staging_attestation"),
      ({"staging_attestation": staging_attestation(stdout, changes={"reported_exit_code": True})}, "invalid_staging_attestation"),
      ({"staging_attestation": staging_attestation(stdout, changes={"reported_exit_code": 1})}, "staging_not_successful"),
      ({"staging_attestation": staging_attestation(stdout, changes={"trusted": True})}, "invalid_staging_attestation"),
      ({"selection_attestation": selection_attestation({"selected_initrd": "initramfs-linux-asahi-dpalt.img"})}, "selection_mismatch"),
      ({"selection_attestation": selection_attestation({"boot_id": "1" + BOOT[1:]})}, "selection_mismatch"),
      ({"selection_attestation": selection_attestation({"trusted": True})}, "invalid_selection_attestation"),
    )
    for changed, expected in mutations:
      with self.assertRaises(BindingError) as raised:
        bind_fixed_t1(sample, **dict(supplied, **changed))
      self.assertEqual(str(raised.exception), expected)
    for changed in (
      stdout[:-1], stdout + b"extra\n", b"0" + stdout[1:],
      stdout.replace(b"A1b2C3d4E5", b"../invalid"),
      b"PROVISIONAL staging record. Default boot unchanged. No reboot permission.\n",
    ):
      with self.assertRaises(BindingError) as raised:
        bind_fixed_t1(sample, **dict(
          supplied, staging_stdout=changed, staging_attestation=staging_attestation(changed),
        ))
      self.assertEqual(str(raised.exception), "staging_output_mismatch")
    with self.assertRaises(BindingError) as raised:
      bind_fixed_t1(sample, **dict(
        supplied, staging_stderr=b"warning\n",
        staging_attestation=staging_attestation(stdout, b"warning\n"),
      ))
    self.assertEqual(str(raised.exception), "staging_not_successful")
    with self.assertRaises(BindingError) as raised:
      bind_fixed_t1(replace(sample, after_boot_id=b"11234567-89ab-cdef-0123-456789abcdef\n"), **supplied)
    self.assertEqual(str(raised.exception), "receipt_mismatch")
