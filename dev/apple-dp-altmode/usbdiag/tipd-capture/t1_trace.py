"""Pure structural validation for the T1 TIPD sender diagnostic.

This module is pure. It does not read files, environment variables, journals,
devices, or module metadata. Structural fixture acceptance is not operational
acceptance. No reviewed T1 image/module identity is available in this draft.

No-install exception: typed dataclasses replace Pydantic for this contained
offline tool. The separate test runner uses the standard-library unittest.
"""

from dataclasses import dataclass
import json
import re
from typing import Literal


REVISION = "dev147-tipddiag1-v1"
BOARD = "j413"
TARGET = "front_lower"
COMPONENT = "tipd"
MAX_INPUT = 131072
MAX_MESSAGE = 384
MAX_ID = 2147483647
MAX_TIME = 18446744073709551615
COMMON = frozenset((
  "rev", "board", "target", "component", "seq", "gen", "worker", "event", "phase",
))
CACHED = frozenset(("plug", "usb2", "usb3", "hpd", "flip", "device", "power"))
QUEUED = CACHED | {"disconnect", "hpd_change"}
WORKER = QUEUED | {"connector", "cached_device"}
INIT_REASONS = (
  "gpio", "vid", "power_state", "mode", "patch", "mask", "status", "role",
  "psy", "port", "power_read", "data_read", "irq", "connect", "complete",
)
MUX_MODES = {
  "safe": (0,), "usb": (1,), "dp": (2, 3, 4, 5, 6, 7), "tbt": (2,), "usb4": (4,),
}


@dataclass(frozen=True)
class SyntheticBinding:
  """An external fixture oracle; never an operational artifact manifest."""

  label: str
  image_sha256: str
  image_size: int
  tipd_sha256: str
  tipd_build_id: str


@dataclass(frozen=True)
class HpdReturn:
  generation: int
  worker: int
  sequence: int


@dataclass(frozen=True)
class FailedOperation:
  generation: int
  worker: int
  event: Literal["init", "worker", "mux", "role"]
  sequence: int
  ret: int


@dataclass(frozen=True)
class TraceResult:
  status: Literal["structurally_complete", "inconclusive", "limited"]
  codes: tuple[str, ...]
  evidence: Literal["synthetic_only", "unbound"]
  record_count: int = 0
  generation_count: int = 0
  worker_count: int = 0
  connected_hpd_returns: tuple[HpdReturn, ...] = ()
  failed_operations: tuple[FailedOperation, ...] = ()
  operationally_accepted: bool = False
  negative_sender_claim: bool = False
  receiver_delivery_claim: bool = False
  usb_or_video_fix_claim: bool = False
  limitations: tuple[str, ...] = (
    "fixture_structure_is_not_boot_evidence",
    "consecutive_prefix_does_not_prove_tail",
    "core_init_entry_is_not_frontend_probe_entry",
    "hpd_return_is_not_receiver_delivery",
    "no_hardware_safety_or_usb_video_fix_claim",
  )


@dataclass(frozen=True)
class _Cached:
  plug: bool
  usb2: bool
  usb3: bool
  hpd: bool
  flip: bool
  device: bool
  power: int


@dataclass(frozen=True)
class _Queued:
  cached: _Cached
  disconnect: bool
  hpd_change: bool


@dataclass(frozen=True)
class _WorkerView:
  queued: _Queued
  connector: bool
  cached_device: bool


@dataclass(frozen=True)
class _Record:
  sequence: int
  generation: int
  worker: int
  event: str
  phase: str
  snapshot: _Cached | _Queued | _WorkerView | None = None
  ret: int | None = None
  reason: str | None = None
  kind: str | None = None
  mode: int | None = None
  which: str | None = None
  value: int | None = None


@dataclass
class _Generation:
  ended: bool = False
  pending_cache: bool = False
  queued: bool = False


@dataclass
class _Worker:
  generation: int
  view: _WorkerView
  stage: int = 0
  opened: _Record | None = None
  early_reason: str | None = None
  ended: bool = False


class _Invalid(ValueError):
  """Only a fixed diagnostic code may leave this boundary."""


def _object(value: object, keys: frozenset[str], code: str) -> dict[str, object]:
  if not isinstance(value, dict) or set(value) != keys:
    raise _Invalid(code)
  return {key: value[key] for key in keys}


def _integer(value: object, minimum: int, maximum: int, code: str) -> int:
  if not isinstance(value, int) or isinstance(value, bool) or not minimum <= value <= maximum:
    raise _Invalid(code)
  return value


def _boolean(value: object) -> bool:
  if not isinstance(value, bool):
    raise _Invalid("invalid_record")
  return value


def _enum(value: object, choices: tuple[str, ...], code: str = "invalid_record") -> str:
  if not isinstance(value, str) or value not in choices:
    raise _Invalid(code)
  return value


def _hex(value: object, length: int, code: str) -> str:
  if not isinstance(value, str) or len(value) != length or re.fullmatch(r"[0-9a-f]+", value) is None:
    raise _Invalid(code)
  return value


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
  result: dict[str, object] = {}
  for key, value in pairs:
    if key in result:
      raise _Invalid("duplicate_json_key")
    result[key] = value
  return result


def _reject_constant(value: str) -> object:
  raise _Invalid("invalid_json")


def _decode(raw: str) -> object:
  try:
    return json.loads(raw, object_pairs_hook=_unique, parse_constant=_reject_constant)
  except _Invalid:
    raise
  except (ValueError, RecursionError):
    raise _Invalid("invalid_json") from None


def _timestamp(value: object) -> int:
  if not isinstance(value, str) or re.fullmatch(r"0|[1-9][0-9]{0,19}", value) is None:
    raise _Invalid("invalid_envelope")
  return _integer(int(value), 0, MAX_TIME, "invalid_envelope")


def _fields(event: str, phase: str) -> frozenset[str]:
  if event == "init" and phase == "begin":
    return frozenset()
  if event in ("init", "worker") and phase == "end":
    return frozenset(("reason", "ret"))
  if (event, phase) == ("cache", "stored"):
    return CACHED
  if (event, phase) == ("queue", "queued"):
    return QUEUED
  if (event, phase) == ("worker", "begin"):
    return WORKER
  if event == "mux" and phase in ("begin", "returned", "skip"):
    names = frozenset(("kind", "mode"))
  elif event == "role" and phase in ("begin", "returned", "skip"):
    names = frozenset(("which", "value"))
  elif event == "hpd" and phase in ("begin", "returned", "skip"):
    names = frozenset(("which",))
  elif (event, phase) == ("cap", "end"):
    return frozenset(("reason", "limit"))
  else:
    raise _Invalid("invalid_record")
  if phase == "skip":
    names |= {"reason"}
  if phase == "returned" and event != "hpd":
    names |= {"ret"}
  return names


def _snapshot(data: dict[str, object], event: str) -> _Cached | _Queued | _WorkerView:
  cached = _Cached(
    _boolean(data["plug"]), _boolean(data["usb2"]), _boolean(data["usb3"]),
    _boolean(data["hpd"]), _boolean(data["flip"]), _boolean(data["device"]),
    _integer(data["power"], 0, 3, "invalid_record"),
  )
  if event == "cache":
    return cached
  queued = _Queued(cached, _boolean(data["disconnect"]), _boolean(data["hpd_change"]))
  if event == "queue":
    return queued
  return _WorkerView(queued, _boolean(data["connector"]), _boolean(data["cached_device"]))


def _record(raw: object) -> _Record:
  if not isinstance(raw, str):
    raise _Invalid("invalid_record")
  if len(raw) + (0 if raw.endswith("\n") else 1) > MAX_MESSAGE:
    raise _Invalid("record_too_long")
  if not raw.isascii() or "\r" in raw or "\n" in raw.removesuffix("\n"):
    raise _Invalid("invalid_record")
  decoded = _decode(raw)
  if not isinstance(decoded, dict) or not COMMON.issubset(decoded):
    raise _Invalid("invalid_record")
  for name, value in (("rev", REVISION), ("board", BOARD), ("target", TARGET), ("component", COMPONENT)):
    if decoded[name] != value:
      raise _Invalid("record_identity_mismatch")
  event = _enum(decoded["event"], ("init", "cache", "queue", "worker", "mux", "role", "hpd", "cap"))
  phase = _enum(decoded["phase"], ("begin", "end", "stored", "queued", "returned", "skip"))
  data = _object(decoded, COMMON | _fields(event, phase), "invalid_record")
  sequence = _integer(data["seq"], 1, 128, "invalid_record")
  generation = _integer(data["gen"], 1, MAX_ID, "invalid_record")
  worker = _integer(data["worker"], 0, MAX_ID, "invalid_record")
  if event in ("init", "cache", "queue") and worker != 0:
    raise _Invalid("invalid_record")
  if event in ("worker", "mux", "role", "hpd") and worker == 0:
    raise _Invalid("invalid_record")
  ret = _integer(data["ret"], -2147483648, MAX_ID, "invalid_record") if "ret" in data else None
  reason: str | None = None
  kind: str | None = None
  mode: int | None = None
  which: str | None = None
  value: int | None = None
  snapshot: _Cached | _Queued | _WorkerView | None = None
  if event == "init" and phase == "end":
    reason = _enum(data["reason"], INIT_REASONS)
    if (reason == "complete") != (ret == 0):
      raise _Invalid("invalid_record")
  elif event == "worker" and phase == "end":
    reason = _enum(data["reason"], ("complete", "disconnected", "partner_error"))
    if reason == "partner_error":
      _integer(ret, -4095, -1, "invalid_record")
    elif ret != 0:
      raise _Invalid("invalid_record")
  elif event in ("cache", "queue", "worker"):
    snapshot = _snapshot(data, event)
  elif event == "mux":
    kind = _enum(data["kind"], ("safe", "usb", "dp", "tbt", "usb4", "none"))
    mode = _integer(data["mode"], -1, 7, "invalid_record")
    if phase == "skip":
      reason = _enum(data["reason"], ("unchanged", "invalid_dp_pin", "disconnected", "partner_error"))
    if reason == "invalid_dp_pin":
      valid = kind == "dp" and mode == -1
    elif reason in ("disconnected", "partner_error"):
      valid = kind == "none" and mode == -1
    else:
      valid = mode in MUX_MODES.get(kind, ())
    if not valid:
      raise _Invalid("invalid_record")
  elif event == "role":
    which = _enum(data["which"], ("none", "final"))
    value = _integer(data["value"], 0, 2, "invalid_record")
    if which == "none" and value != 0:
      raise _Invalid("invalid_record")
    if phase == "skip":
      reasons = ("no_transition",) if which == "none" else ("disconnected", "partner_error")
      reason = _enum(data["reason"], reasons)
  elif event == "hpd":
    which = _enum(data["which"], ("disconnected", "connected"))
    if phase == "skip":
      reasons = ("no_connector", "level_high_unchanged") if which == "disconnected" else (
        "no_connector", "level_low", "disconnected", "partner_error",
      )
      reason = _enum(data["reason"], reasons)
  elif event == "cap":
    reason = _enum(data["reason"], ("budget",))
    _integer(data["limit"], 128, 128, "invalid_record")
  return _Record(
    sequence, generation, worker, event, phase, snapshot, ret,
    reason, kind, mode, which, value,
  )


def _capture(document: str, binding: SyntheticBinding) -> tuple[_Record, ...]:
  if not isinstance(document, str):
    raise _Invalid("invalid_capture")
  if len(document) > MAX_INPUT:
    raise _Invalid("input_too_large")
  try:
    encoded_size = len(document.encode("utf-8"))
  except UnicodeError:
    raise _Invalid("invalid_json") from None
  if encoded_size > MAX_INPUT:
    raise _Invalid("input_too_large")
  data = _object(_decode(document), frozenset((
    "schema", "kind", "fixture_label", "boot_id", "collection_start_monotonic_us",
    "collection_end_monotonic_us", "collection_complete", "all_priorities",
    "artifacts", "records",
  )), "invalid_capture")
  if data["schema"] != "dev147-tipd-capture1":
    raise _Invalid("invalid_capture")
  if not isinstance(binding, SyntheticBinding):
    raise _Invalid("fixture_binding_mismatch")
  if (
    not isinstance(binding.label, str)
    or re.fullmatch(r"synthetic-[a-z0-9_-]{1,48}", binding.label) is None
    or data["kind"] != "synthetic_fixture" or data["fixture_label"] != binding.label
  ):
    raise _Invalid("fixture_binding_mismatch")
  boot = _hex(data["boot_id"], 32, "invalid_capture")
  _integer(data["collection_start_monotonic_us"], 0, 0, "invalid_collection")
  end = _integer(data["collection_end_monotonic_us"], 1, MAX_TIME, "invalid_collection")
  for flag in ("collection_complete", "all_priorities"):
    if not isinstance(data[flag], bool):
      raise _Invalid("invalid_collection")
    if not data[flag]:
      raise _Invalid("incomplete_collection")
  artifact_keys = frozenset(("image_sha256", "image_size", "tipd_sha256", "tipd_build_id"))
  artifacts = _object(data["artifacts"], artifact_keys, "artifact_mismatch")
  for name, expected, length in (
    ("image_sha256", binding.image_sha256, 64),
    ("tipd_sha256", binding.tipd_sha256, 64),
    ("tipd_build_id", binding.tipd_build_id, 40),
  ):
    if _hex(artifacts[name], length, "artifact_mismatch") != _hex(expected, length, "artifact_mismatch"):
      raise _Invalid("artifact_mismatch")
  size = _integer(artifacts["image_size"], 1, MAX_TIME, "artifact_mismatch")
  if size != _integer(binding.image_size, 1, MAX_TIME, "artifact_mismatch"):
    raise _Invalid("artifact_mismatch")
  raw_records = data["records"]
  if not isinstance(raw_records, list) or len(raw_records) > 128:
    raise _Invalid("invalid_capture")
  envelope_keys = frozenset((
    "_BOOT_ID", "PRIORITY", "__CURSOR", "__MONOTONIC_TIMESTAMP",
    "__REALTIME_TIMESTAMP", "MESSAGE",
  ))
  cursors: set[str] = set()
  previous_time = 0
  messages: list[object] = []
  for raw in raw_records:
    envelope = _object(raw, envelope_keys, "invalid_envelope")
    if envelope["_BOOT_ID"] != boot:
      raise _Invalid("boot_mismatch")
    if envelope["PRIORITY"] != "6":
      raise _Invalid("invalid_envelope")
    cursor = envelope["__CURSOR"]
    if (
      not isinstance(cursor, str) or not 1 <= len(cursor) <= 512
      or not cursor.isascii() or any(ord(char) < 32 or ord(char) == 127 for char in cursor)
      or cursor in cursors
    ):
      raise _Invalid("invalid_envelope")
    cursors.add(cursor)
    stamp = _timestamp(envelope["__MONOTONIC_TIMESTAMP"])
    _timestamp(envelope["__REALTIME_TIMESTAMP"])
    if not previous_time <= stamp <= end:
      raise _Invalid("invalid_envelope")
    previous_time = stamp
    messages.append(envelope["MESSAGE"])
  return tuple(_record(message) for message in messages)


def _ordered(records: tuple[_Record, ...]) -> tuple[tuple[_Record, ...], bool]:
  if not records:
    raise _Invalid("missing_init_begin")
  if len({record.sequence for record in records}) != len(records):
    raise _Invalid("duplicate_sequence")
  ordered = tuple(sorted(records, key=lambda record: record.sequence))
  if tuple(record.sequence for record in ordered) != tuple(range(1, len(records) + 1)):
    raise _Invalid("sequence_gap")
  caps = tuple(record for record in ordered if record.event == "cap")
  if not caps and len(ordered) == 127:
    raise _Invalid("missing_cap")
  if caps or len(ordered) == 128:
    if len(caps) != 1 or len(ordered) != 128 or ordered[-1].event != "cap":
      raise _Invalid("invalid_cap")
    before, cap = ordered[-2:]
    if (before.generation, before.worker) != (cap.generation, cap.worker):
      raise _Invalid("invalid_cap")
    return ordered[:-1], True
  return ordered, False


def _role(view: _WorkerView) -> int:
  if view.queued.cached.usb2 or view.queued.cached.usb3:
    return 2 if view.cached_device else 1
  return 0


def _decision(record: _Record, worker: _Worker) -> None:
  view = worker.view
  state = view.queued.cached
  if worker.stage == 0:
    # The old role is not recorded. Both a call and no-transition skip fit.
    return
  if worker.stage == 1:
    called = view.connector and (not state.hpd or view.queued.hpd_change)
    reason = "no_connector" if not view.connector else "level_high_unchanged"
  elif worker.stage == 2:
    if not state.plug:
      if record.phase != "skip" or record.reason != "disconnected":
        raise _Invalid("decision_mismatch")
      worker.early_reason = "disconnected"
    elif record.reason in ("disconnected", "partner_error"):
      if record.reason != "partner_error":
        raise _Invalid("decision_mismatch")
      worker.early_reason = "partner_error"
    return
  elif worker.stage == 3:
    if record.value != _role(view):
      raise _Invalid("decision_mismatch")
    called = worker.early_reason is None
    reason = worker.early_reason
  else:
    called = worker.early_reason is None and view.connector and state.hpd
    if worker.early_reason is not None:
      reason = worker.early_reason
    else:
      reason = "no_connector" if not view.connector else "level_low"
  if called:
    if record.phase != "begin":
      raise _Invalid("decision_mismatch")
  elif record.phase != "skip" or record.reason != reason:
    raise _Invalid("decision_mismatch")


def _failure(
  record: _Record, event: Literal["init", "worker", "mux", "role"],
) -> FailedOperation | None:
  if record.ret is None or record.ret == 0:
    return None
  return FailedOperation(record.generation, record.worker, event, record.sequence, record.ret)


def _step(record: _Record, worker: _Worker) -> None:
  if worker.ended:
    raise _Invalid("operation_order")
  if worker.opened is not None:
    first = worker.opened
    if record.event != first.event or record.phase != "returned":
      raise _Invalid("missing_operation_return")
    if (record.which, record.kind, record.mode, record.value) != (
      first.which, first.kind, first.mode, first.value,
    ):
      raise _Invalid("operation_pair_mismatch")
    worker.opened = None
    worker.stage += 1
    return
  if record.phase == "returned":
    raise _Invalid("missing_operation_begin")
  expected = (
    ("role", "none"), ("hpd", "disconnected"), ("mux", None),
    ("role", "final"), ("hpd", "connected"), ("worker", None),
  )
  if (record.event, record.which) != expected[worker.stage]:
    raise _Invalid("operation_order")
  if worker.stage == 5:
    if record.phase != "end":
      raise _Invalid("operation_order")
    expected_reason = worker.early_reason if worker.early_reason is not None else "complete"
    if record.reason != expected_reason:
      raise _Invalid("decision_mismatch")
    worker.ended = True
    return
  _decision(record, worker)
  if record.phase == "begin":
    worker.opened = record
  elif record.phase == "skip":
    worker.stage += 1
  else:
    raise _Invalid("operation_order")


def _source_order(records: tuple[_Record, ...], limited: bool) -> TraceResult:
  if (records[0].event, records[0].phase) != ("init", "begin"):
    raise _Invalid("missing_init_begin")
  generations: dict[int, _Generation] = {}
  workers: dict[int, _Worker] = {}
  returns: list[HpdReturn] = []
  failures: list[FailedOperation] = []
  for record in records:
    if (record.event, record.phase) == ("init", "begin"):
      if record.generation in generations:
        raise _Invalid("duplicate_init")
      generations[record.generation] = _Generation()
      continue
    if record.generation not in generations:
      raise _Invalid("unknown_generation")
    generation = generations[record.generation]
    if record.event == "init":
      if generation.ended:
        raise _Invalid("duplicate_init")
      generation.ended = True
      failure = _failure(record, "init")
    elif record.event == "cache":
      if generation.pending_cache:
        raise _Invalid("operation_order")
      generation.pending_cache = True
      continue
    elif record.event == "queue":
      if not generation.pending_cache:
        raise _Invalid("missing_queue")
      generation.pending_cache = False
      generation.queued = True
      continue
    elif (record.event, record.phase) == ("worker", "begin"):
      if record.worker in workers:
        raise _Invalid("duplicate_worker")
      if not generation.queued:
        raise _Invalid("missing_queue" if generation.pending_cache else "worker_without_queue")
      if not isinstance(record.snapshot, _WorkerView):
        raise _Invalid("invalid_record")
      workers[record.worker] = _Worker(record.generation, record.snapshot)
      continue
    else:
      worker = workers.get(record.worker)
      if worker is None or worker.generation != record.generation:
        raise _Invalid("unknown_worker")
      _step(record, worker)
      failure = None
      if record.event == "worker":
        failure = _failure(record, "worker")
      elif record.event == "mux":
        failure = _failure(record, "mux")
      elif record.event == "role":
        failure = _failure(record, "role")
      elif record.phase == "returned" and record.which == "connected":
        returns.append(HpdReturn(record.generation, record.worker, record.sequence))
    if failure is not None:
      failures.append(failure)
  if not limited:
    if any(worker.opened is not None for worker in workers.values()):
      raise _Invalid("missing_operation_return")
    if any(not worker.ended for worker in workers.values()):
      raise _Invalid("missing_worker_end")
    if any(generation.pending_cache for generation in generations.values()):
      raise _Invalid("missing_queue")
    if any(not generation.ended for generation in generations.values()):
      raise _Invalid("missing_init_end")
  return TraceResult(
    status="limited" if limited else "structurally_complete",
    codes=("capture_capped",) if limited else (), evidence="synthetic_only",
    record_count=len(records) + int(limited), generation_count=len(generations),
    worker_count=len(workers), connected_hpd_returns=tuple(returns),
    failed_operations=tuple(failures),
  )


def inspect_fixture_capture(document: str, binding: SyntheticBinding) -> TraceResult:
  """Validate a synthetic trace without promoting it to operational evidence."""
  try:
    records, limited = _ordered(_capture(document, binding))
    return _source_order(records, limited)
  except _Invalid as error:
    return TraceResult("inconclusive", (str(error),), "synthetic_only")


def validate_capture(document: str) -> TraceResult:
  """Refuse operational use without a later reviewed fixed artifact binding.

  There is intentionally no manifest, expected hash, environment, or caller
  override. A synthetic binding cannot enable this entry point.
  """
  return TraceResult(
    status="inconclusive",
    codes=("artifact_binding_unavailable",),
    evidence="unbound",
  )
