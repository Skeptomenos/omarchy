"""Pure T1 capture consistency checks implemented after preserved RED.

No function reads files, environment variables, journals, or devices. The
operational entry stays closed. Matching submitted bytes is not provenance.
The six earlier structural-parser files remain unchanged.
"""

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Literal, NoReturn

from t1_trace import (
  MAX_INPUT as MAX_PROJECTION, FailedOperation, HpdReturn, _Invalid,
  _ordered, _record, _source_order,
)


KERNEL_RELEASE = "7.1.6-1-1-ARCH"
TIPD_SHA256 = "a0fdadc351261643545e5afd8561923be99431661c447084336c9318f5b0c02f"
TIPD_BUILD_ID = "40aa54382047ba36b02c9ac0da65a213862a77ad"
MAX_STDOUT = 8_388_608
MAX_STDERR = 65_536
MAX_ROWS = 16_384
MAX_ROW = 262_144
MAX_RECEIPT = 16_384
MAX_DURATION_US = 30_000_000


@dataclass(frozen=True)
class CaptureFiles:
  """Untrusted raw inputs, supplied by the caller without a trust flag."""

  stdout: bytes
  stderr: bytes
  receipt: bytes
  before_boot_id: bytes
  before_tipd_note: bytes
  after_boot_id: bytes
  after_tipd_note: bytes


@dataclass(frozen=True)
class JournalRecord:
  """Original envelope values after the kernel-transport check."""

  boot_id: str
  priority: str
  cursor: str
  monotonic_timestamp: str
  realtime_timestamp: str
  message: str


@dataclass(frozen=True)
class CaptureFacts:
  """Consistency and structural facts only; never an image-boot receipt."""

  boot_id: str
  kernel_release: str
  tipd_note_build_id: str
  journal_record_count: int
  records: tuple[JournalRecord, ...]
  last_returned_cursor: str | None
  structural_status: Literal["structurally_complete", "inconclusive", "limited"]
  structural_codes: tuple[str, ...]
  connected_hpd_returns: tuple[HpdReturn, ...] = ()
  failed_operations: tuple[FailedOperation, ...] = ()
  evidence: Literal["internally_consistent_only"] = "internally_consistent_only"
  operationally_accepted: Literal[False] = False
  negative_sender_claim: Literal[False] = False
  receiver_delivery_claim: Literal[False] = False
  usb_or_video_fix_claim: Literal[False] = False


@dataclass(frozen=True)
class BindingDecision:
  status: Literal["inconclusive"] = "inconclusive"
  codes: tuple[str, ...] = ("artifact_binding_unavailable",)
  evidence: Literal["unbound"] = "unbound"
  operationally_accepted: Literal[False] = False


class CaptureError(ValueError):
  """The consistency boundary raises only fixed, non-sensitive codes."""


class _DuplicateKey(ValueError):
  """Internal duplicate-key sentinel."""


@dataclass(frozen=True)
class _PairObject:
  """A duplicate-preserving JSON object used only for family detection."""

  pairs: tuple[tuple[str, object], ...]


RECEIPT_KEYS = frozenset((
  "schema", "argv", "kernel_release", "start_monotonic_us",
  "end_monotonic_us", "exit_code", "timed_out", "stdout_limit_exceeded",
  "stderr_limit_exceeded", "stdout_bytes", "stderr_bytes", "stdout_sha256",
  "stderr_sha256", "before", "after",
))
SAMPLE_KEYS = frozenset(("boot_id_sha256", "tipd_note_sha256"))
ENVELOPE_FIELDS = (
  "_BOOT_ID", "_TRANSPORT", "PRIORITY", "__CURSOR",
  "__MONOTONIC_TIMESTAMP", "__REALTIME_TIMESTAMP", "MESSAGE",
)


def _fail(code: str) -> NoReturn:
  raise CaptureError(code)


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
  result: dict[str, object] = {}
  for key, value in pairs:
    if key in result:
      raise _DuplicateKey
    result[key] = value
  return result


def _reject_constant(value: str) -> NoReturn:
  raise ValueError


def _decode(raw: bytes | str, code: str) -> object:
  try:
    if isinstance(raw, bytes):
      raw = raw.decode("utf-8", errors="strict")
    return json.loads(raw, object_pairs_hook=_unique, parse_constant=_reject_constant)
  except _DuplicateKey:
    _fail("duplicate_json_key")
  except (UnicodeError, ValueError, RecursionError, TypeError):
    _fail(code)


def _object(value: object, keys: frozenset[str], code: str) -> dict[str, object]:
  if not isinstance(value, dict) or set(value) != keys:
    _fail(code)
  return value


def _integer(value: object, minimum: int, maximum: int, code: str) -> int:
  if not isinstance(value, int) or isinstance(value, bool) or not minimum <= value <= maximum:
    _fail(code)
  return value


def _text(value: object, code: str) -> str:
  if not isinstance(value, str):
    _fail(code)
  return value


def _hash(value: object, code: str) -> str:
  text = _text(value, code)
  if re.fullmatch(r"[0-9a-f]{64}", text) is None:
    _fail(code)
  return text


def _timestamp(value: object) -> int:
  text = _text(value, "invalid_envelope")
  if re.fullmatch(r"0|[1-9][0-9]{0,19}", text) is None:
    _fail("invalid_envelope")
  return _integer(int(text), 0, 18_446_744_073_709_551_615, "invalid_envelope")


def _receipt(files: CaptureFiles) -> tuple[dict[str, object], str, int]:
  value = _object(_decode(files.receipt, "invalid_receipt"), RECEIPT_KEYS, "invalid_receipt")
  if value["schema"] != "dev147-t1-collector-receipt1" or value["kernel_release"] != KERNEL_RELEASE:
    _fail("invalid_receipt")
  argv = value["argv"]
  if not isinstance(argv, list) or len(argv) != 7 or not all(isinstance(item, str) for item in argv):
    _fail("invalid_receipt")
  if argv[:2] != ["/usr/bin/journalctl", "--dmesg"] or argv[3:] != [
    "--all", "--output=json", "--no-pager", "--no-tail",
  ]:
    _fail("invalid_receipt")
  boot_option = argv[2]
  if re.fullmatch(r"--boot=[0-9a-f]{32}", boot_option) is None:
    _fail("invalid_receipt")
  start = _integer(value["start_monotonic_us"], 0, 18_446_744_073_709_551_615, "invalid_receipt")
  end = _integer(value["end_monotonic_us"], 0, 18_446_744_073_709_551_615, "invalid_receipt")
  if start > end:
    _fail("invalid_receipt")
  exit_code = _integer(value["exit_code"], -2_147_483_648, 2_147_483_647, "invalid_receipt")
  flags = tuple(value[name] for name in (
    "timed_out", "stdout_limit_exceeded", "stderr_limit_exceeded",
  ))
  if any(not isinstance(flag, bool) for flag in flags):
    _fail("invalid_receipt")
  stdout_bytes = _integer(value["stdout_bytes"], 0, 18_446_744_073_709_551_615, "invalid_receipt")
  stderr_bytes = _integer(value["stderr_bytes"], 0, 18_446_744_073_709_551_615, "invalid_receipt")
  expected = (
    (stdout_bytes, len(files.stdout)), (stderr_bytes, len(files.stderr)),
    (_hash(value["stdout_sha256"], "invalid_receipt"), hashlib.sha256(files.stdout).hexdigest()),
    (_hash(value["stderr_sha256"], "invalid_receipt"), hashlib.sha256(files.stderr).hexdigest()),
  )
  for side, boot_raw, note_raw in (
    ("before", files.before_boot_id, files.before_tipd_note),
    ("after", files.after_boot_id, files.after_tipd_note),
  ):
    sample = _object(value[side], SAMPLE_KEYS, "invalid_receipt")
    expected += (
      (_hash(sample["boot_id_sha256"], "invalid_receipt"), hashlib.sha256(boot_raw).hexdigest()),
      (_hash(sample["tipd_note_sha256"], "invalid_receipt"), hashlib.sha256(note_raw).hexdigest()),
    )
  if any(actual != submitted for actual, submitted in expected):
    _fail("receipt_mismatch")
  if exit_code != 0 or any(flags) or files.stderr or end - start > MAX_DURATION_US:
    _fail("collection_failed")
  return value, boot_option.removeprefix("--boot="), end


def _boot(raw: bytes) -> str:
  if re.fullmatch(rb"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\n", raw) is None:
    _fail("invalid_boot_sample")
  return raw[:-1].replace(b"-", b"").decode("ascii")


def _note(raw: bytes) -> str:
  if len(raw) != 36 or raw[:16] != bytes.fromhex("040000001400000003000000474e5500"):
    _fail("invalid_note")
  return raw[16:].hex()


def _family(message: str) -> bool:
  marker = "dev147-tipd" in message or "dev147-usbdiag" in message
  stripped = message.lstrip()
  if not stripped.startswith("{"):
    return marker
  try:
    decoded = json.loads(
      message,
      object_pairs_hook=lambda pairs: _PairObject(tuple(pairs)),
    )
  except (ValueError, RecursionError):
    return marker or any(key in message for key in ('"rev"', '"revision"', '"component"'))
  if not isinstance(decoded, _PairObject):
    return marker
  for key, value in decoded.pairs:
    if key in ("rev", "revision") and isinstance(value, str) and value.startswith("dev147-"):
      return True
    if key == "component" and value == "tipd":
      return True
  return marker


def _projection_size(records: list[JournalRecord]) -> int:
  value = [{
    "_BOOT_ID": item.boot_id, "PRIORITY": item.priority,
    "__CURSOR": item.cursor, "__MONOTONIC_TIMESTAMP": item.monotonic_timestamp,
    "__REALTIME_TIMESTAMP": item.realtime_timestamp, "MESSAGE": item.message,
  } for item in records]
  return len(json.dumps(value, ensure_ascii=True, separators=(",", ":")).encode("ascii"))


def inspect_capture_files(files: CaptureFiles) -> CaptureFacts:
  """Validate submitted bytes without promoting consistency to provenance."""
  if not isinstance(files, CaptureFiles) or any(
    not isinstance(value, bytes) for value in (
      files.stdout, files.stderr, files.receipt, files.before_boot_id,
      files.before_tipd_note, files.after_boot_id, files.after_tipd_note,
    )
  ):
    _fail("invalid_capture_input")
  if (
    len(files.stdout) > MAX_STDOUT or len(files.stderr) > MAX_STDERR
    or len(files.receipt) > MAX_RECEIPT
  ):
    _fail("capture_bound_exceeded")
  if (
    len(files.before_boot_id) > 37 or len(files.after_boot_id) > 37
    or len(files.before_tipd_note) > 36 or len(files.after_tipd_note) > 36
  ):
    _fail("capture_bound_exceeded")
  receipt, receipt_boot, end = _receipt(files)
  before_boot = _boot(files.before_boot_id)
  after_boot = _boot(files.after_boot_id)
  if before_boot != after_boot or before_boot != receipt_boot:
    _fail("boot_mismatch")
  before_note = _note(files.before_tipd_note)
  after_note = _note(files.after_tipd_note)
  if before_note != TIPD_BUILD_ID or after_note != TIPD_BUILD_ID:
    _fail("module_mismatch")

  if files.stdout and not files.stdout.endswith(b"\n"):
    _fail("invalid_journal")
  raw_rows = files.stdout.splitlines(keepends=True)
  if len(raw_rows) > MAX_ROWS or any(len(row) > MAX_ROW for row in raw_rows):
    _fail("capture_bound_exceeded")
  if any(not row.endswith(b"\n") or row.endswith(b"\r\n") for row in raw_rows):
    _fail("invalid_journal")

  cursors: set[str] = set()
  previous = -1
  projected: list[JournalRecord] = []
  parsed = []
  last_cursor: str | None = None
  for raw_row in raw_rows:
    row = _decode(raw_row[:-1], "invalid_journal")
    if not isinstance(row, dict) or any(
      field not in row or not isinstance(row[field], str) for field in ENVELOPE_FIELDS
    ):
      _fail("invalid_envelope")
    boot = _text(row["_BOOT_ID"], "invalid_envelope")
    if re.fullmatch(r"[0-9a-f]{32}", boot) is None:
      _fail("invalid_envelope")
    if boot != before_boot:
      _fail("boot_mismatch")
    if row["_TRANSPORT"] != "kernel":
      _fail("invalid_envelope")
    priority = _text(row["PRIORITY"], "invalid_envelope")
    if re.fullmatch(r"[0-7]", priority) is None:
      _fail("invalid_envelope")
    cursor = _text(row["__CURSOR"], "invalid_envelope")
    if (
      not 1 <= len(cursor) <= 512 or not cursor.isascii()
      or any(ord(char) < 32 or ord(char) == 127 for char in cursor)
      or cursor in cursors
    ):
      _fail("invalid_envelope")
    monotonic_text = _text(row["__MONOTONIC_TIMESTAMP"], "invalid_envelope")
    monotonic = _timestamp(monotonic_text)
    realtime_text = _text(row["__REALTIME_TIMESTAMP"], "invalid_envelope")
    _timestamp(realtime_text)
    if monotonic < previous or monotonic > end:
      _fail("invalid_envelope")
    cursors.add(cursor)
    previous = monotonic
    last_cursor = cursor
    message = _text(row["MESSAGE"], "invalid_envelope")
    if not _family(message):
      continue
    if priority != "6":
      _fail("diagnostic_priority")
    try:
      parsed.append(_record(message))
    except _Invalid:
      _fail("malformed_t1_family")
    projected.append(JournalRecord(
      boot, priority, cursor, monotonic_text, realtime_text, message,
    ))
    if len(projected) > 128:
      _fail("capture_bound_exceeded")
  if _projection_size(projected) > MAX_PROJECTION:
    _fail("capture_bound_exceeded")
  try:
    ordered, limited = _ordered(tuple(parsed))
    structural = _source_order(ordered, limited)
  except _Invalid as error:
    return CaptureFacts(
      before_boot, _text(receipt["kernel_release"], "invalid_receipt"), before_note,
      len(raw_rows), tuple(projected), last_cursor, "inconclusive", (str(error),),
    )
  return CaptureFacts(
    before_boot, _text(receipt["kernel_release"], "invalid_receipt"), before_note,
    len(raw_rows), tuple(projected), last_cursor, structural.status, structural.codes,
    structural.connected_hpd_returns, structural.failed_operations,
  )


def validate_bound_capture(
  files: CaptureFiles, *, staging_receipt: bytes, selected_initrd: str,
) -> BindingDecision:
  """Refuse operation until an accepted image and collector are reviewed.

  There is no image hash/size constant, expected-profile argument, trusted
  metadata flag, environment lookup, or implicit fallback in this draft.
  A known module note does not prove the selected image or startup order.
  """
  return BindingDecision()
