"""Held, no-CLI collector for one fixed T1 capture.

Importing this module performs no collection or live reads. Invocation is
not authorized by offline tests. Only the reviewed fixed function can join
actual execution, before/after samples and consistency publication.
"""

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import stat
import time

from bounded_child import (
  ChildCapture, CollectionError, _Limits, _capture_child, _identity,
  _new_directory, _private_directory, _read_back, _write_new,
)
from capture_binding import (
  CaptureError, CaptureFiles, _boot, _note, inspect_capture_files,
)


LIVE_OUTPUT = Path("/LOCAL_ONLY_DEV147_T1_CAPTURE")
LIVE_OUTPUT_SHA256 = "7d3325571eded2507427d7637cefda75beb91d21a50dbf9a33c1eca3ce761ec9"
BOOT_PATH = Path("/proc/sys/kernel/random/boot_id")
NOTE_PATH = Path("/sys/module/tps6598x_core/notes/.note.gnu.build-id")
JOURNAL_PATH = Path("/usr/bin/journalctl")
JOURNAL_SHA256 = "c7de3d70a567a1e9f7f09cd67c8d626c96d14f53149728d3b86ded4a323cda22"
JOURNAL_BYTES = 138_296
KERNEL_RELEASE = "7.1.6-1-1-ARCH"
TIPD_BUILD_ID = "40aa54382047ba36b02c9ac0da65a213862a77ad"
DURATION_US = 30_000_000
STDOUT_LIMIT = 8_388_608
STDERR_LIMIT = 65_536
CLEANUP_US = 1_000_000


def _require_local_output() -> None:
  """The public one-literal LOCAL_ONLY copy stops before any live access."""
  if hashlib.sha256(os.fsencode(LIVE_OUTPUT)).hexdigest() != LIVE_OUTPUT_SHA256:
    raise CollectionError("local_only_output")


@dataclass(frozen=True)
class _SamplePair:
  boot: bytes
  note: bytes
  boot_identity: tuple[int, ...]
  note_identity: tuple[int, ...]


def _sample_identity(info: os.stat_result) -> tuple[int, ...]:
  return _identity(info) + (info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def _bounded_read(path: Path, limit: int, owner: int) -> tuple[bytes, tuple[int, ...]]:
  """Internal synthetic-file seam; the held wrapper supplies fixed paths."""
  descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
  try:
    before = os.fstat(descriptor)
    if (
      not stat.S_ISREG(before.st_mode) or before.st_nlink != 1
      or before.st_uid != owner or before.st_gid != owner
      or stat.S_IMODE(before.st_mode) & 0o022 or before.st_size > limit
    ):
      raise CollectionError("invalid_sample_file")
    raw = bytearray()
    while len(raw) <= limit:
      chunk = os.read(descriptor, min(4_096, limit + 1 - len(raw)))
      if not chunk:
        break
      raw.extend(chunk)
    after = os.fstat(descriptor)
    if (
      len(raw) > limit or _sample_identity(before) != _sample_identity(after)
      or _sample_identity(after) != _sample_identity(path.lstat())
    ):
      raise CollectionError("sample_changed_or_oversized")
    return bytes(raw), _sample_identity(after)
  finally:
    os.close(descriptor)


def _sample_pair(boot_path: Path, note_path: Path, owner: int) -> _SamplePair:
  boot, boot_identity = _bounded_read(boot_path, 37, owner)
  note, note_identity = _bounded_read(note_path, 36, owner)
  try:
    _boot(boot)
    build_id = _note(note)
  except CaptureError as error:
    raise CollectionError(str(error)) from None
  if build_id != TIPD_BUILD_ID:
    raise CollectionError("module_mismatch")
  return _SamplePair(boot, note, boot_identity, note_identity)


def _same_samples(before: _SamplePair, after: _SamplePair) -> None:
  if before != after:
    raise CollectionError("boot_or_module_sample_changed")


def _journal_plan(boot_id: str) -> tuple[str, ...]:
  if len(boot_id) != 32 or any(char not in "0123456789abcdef" for char in boot_id):
    raise CollectionError("invalid_boot_id")
  return (
    "/usr/bin/journalctl", "--dmesg", "--boot=" + boot_id,
    "--all", "--output=json", "--no-pager", "--no-tail",
  )


def _authenticate_journal() -> tuple[int, ...]:
  raw, identity = _bounded_read(JOURNAL_PATH, JOURNAL_BYTES, 0)
  if (
    len(raw) != JOURNAL_BYTES or hashlib.sha256(raw).hexdigest() != JOURNAL_SHA256
    or stat.S_IMODE(identity[2]) != 0o755
  ):
    raise CollectionError("journal_tool_mismatch")
  return identity


def _capture_files(
  before: _SamplePair, after: _SamplePair, child: ChildCapture,
  stdout: bytes, stderr: bytes, start_us: int, end_us: int,
) -> CaptureFiles:
  """Derive the old format only from a matching actual-command outcome.

  In particular, an actual Python fixture result cannot become journalctl
  execution evidence through this function.
  """
  _same_samples(before, after)
  if child.argv != _journal_plan(_boot(before.boot)):
    raise CollectionError("nonjournal_execution")
  if (
    child.status != "ok" or child.exit_code != 0 or child.killed or not child.reaped
    or child.pid <= 0 or child.process_group != child.pid
    or not child.stdout_eof or not child.stderr_eof
    or child.stdout_observed != child.stdout_retained or child.stderr_observed != child.stderr_retained
    or child.stdout_retained != len(stdout) or child.stderr_retained != len(stderr)
    or child.stdout_sha256 != hashlib.sha256(stdout).hexdigest()
    or child.stderr_sha256 != hashlib.sha256(stderr).hexdigest()
    or not start_us <= child.start_monotonic_us <= child.end_monotonic_us <= end_us
    or not 0 <= end_us - start_us <= DURATION_US
  ):
    raise CollectionError("incomplete_child_capture")
  receipt = {
    "schema": "dev147-t1-collector-receipt1", "argv": list(child.argv),
    "kernel_release": KERNEL_RELEASE, "start_monotonic_us": start_us,
    "end_monotonic_us": end_us, "exit_code": child.exit_code,
    "timed_out": False, "stdout_limit_exceeded": False, "stderr_limit_exceeded": False,
    "stdout_bytes": len(stdout), "stderr_bytes": len(stderr),
    "stdout_sha256": child.stdout_sha256, "stderr_sha256": child.stderr_sha256,
    "before": {"boot_id_sha256": hashlib.sha256(before.boot).hexdigest(), "tipd_note_sha256": hashlib.sha256(before.note).hexdigest()},
    "after": {"boot_id_sha256": hashlib.sha256(after.boot).hexdigest(), "tipd_note_sha256": hashlib.sha256(after.note).hexdigest()},
  }
  files = CaptureFiles(
    stdout, stderr, json.dumps(receipt, separators=(",", ":")).encode("ascii"),
    before.boot, before.note, after.boot, after.note,
  )
  try:
    inspect_capture_files(files)
  except CaptureError as error:
    raise CollectionError(str(error)) from None
  return files


def _publish_consistency(directory: int, files: CaptureFiles) -> None:
  """Publish consistency last; pathname presence alone is never acceptance."""
  facts = inspect_capture_files(files)
  _write_new(directory, "journal.receipt.json", files.receipt)
  result = {
    "schema": "dev147-t1-capture-consistency1", "boot_id": facts.boot_id,
    "publication_status": "provisional_requires_observed_exit0_and_raw_audit",
    "evidence": "internally_consistent_only", "structural_status": facts.structural_status,
    "structural_codes": list(facts.structural_codes), "record_count": len(facts.records),
    "stdout_sha256": hashlib.sha256(files.stdout).hexdigest(),
    "stderr_sha256": hashlib.sha256(files.stderr).hexdigest(),
    "receipt_sha256": hashlib.sha256(files.receipt).hexdigest(),
    "staging_attested": False, "selection_attested": False,
    "operationally_accepted": False, "initrd_boot_proven": False,
    "earliest_load_proven": False, "negative_sender_claim": False,
    "receiver_delivery_claim": False, "hardware_acceptance": False,
  }
  _write_new(directory, "capture-result.json", json.dumps(result, separators=(",", ":")).encode("ascii") + b"\n")


def collect_fixed_t1() -> CaptureFiles:
  """HELD: fixed one-use live entry; offline tests never invoke it."""
  _require_local_output()
  start = time.monotonic_ns() // 1_000
  deadline = start + DURATION_US
  if (os.getuid(), os.geteuid(), os.getgid(), os.getegid()) != (1001, 1001, 1001, 1001):
    raise CollectionError("wrong_identity")
  directory = _new_directory(LIVE_OUTPUT)
  try:
    _write_new(directory, "STARTED.json", json.dumps({
      "schema": "dev147-t1-capture-start1", "start_monotonic_us": start,
      "status": "incomplete_until_validated_exit", "operationally_accepted": False,
    }, separators=(",", ":")).encode("ascii") + b"\n")
    if os.uname().release != KERNEL_RELEASE:
      raise CollectionError("kernel_mismatch")
    tool_before = _authenticate_journal()
    before = _sample_pair(BOOT_PATH, NOTE_PATH, 0)
    _write_new(directory, "before.boot-id", before.boot)
    _write_new(directory, "before.tipd-note", before.note)
    child = _capture_child(
      _journal_plan(_boot(before.boot)), LIVE_OUTPUT / "child",
      _Limits(DURATION_US, STDOUT_LIMIT, STDERR_LIMIT, CLEANUP_US), _deadline_us=deadline,
    )
    after = _sample_pair(BOOT_PATH, NOTE_PATH, 0)
    _write_new(directory, "after.boot-id", after.boot)
    _write_new(directory, "after.tipd-note", after.note)
    if _authenticate_journal() != tool_before or os.uname().release != KERNEL_RELEASE:
      raise CollectionError("immutable_live_input_changed")
    child_directory = _private_directory(LIVE_OUTPUT / "child")
    try:
      stdout = _read_back(child_directory, "stdout.bin", STDOUT_LIMIT)
      stderr = _read_back(child_directory, "stderr.bin", STDERR_LIMIT)
    finally:
      os.close(child_directory)
    end = time.monotonic_ns() // 1_000
    files = _capture_files(before, after, child, stdout, stderr, start, end)
    _publish_consistency(directory, files)
    if time.monotonic_ns() // 1_000 > deadline:
      raise CollectionError("collection_deadline")
    return files
  except BaseException as error:
    code = str(error) if isinstance(error, (CollectionError, CaptureError)) else "wrapper_failure"
    try:
      _write_new(directory, "parent-failure.json", json.dumps({
        "schema": "dev147-t1-capture-failure1", "status": "incomplete", "code": code,
        "operationally_accepted": False, "retain_all_files": True,
      }, separators=(",", ":")).encode("ascii") + b"\n")
    except (OSError, CollectionError):
      pass
    raise
  finally:
    os.close(directory)
