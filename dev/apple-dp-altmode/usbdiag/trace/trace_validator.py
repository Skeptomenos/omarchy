"""Pure validation of a normalized, diagnostic-only journal capture.

The input contains only DEV-147 diagnostic records with their original six
journal envelope fields. The full all-priority journal is separate evidence;
this module does not collect, filter, rewrite, sort, or query it. At most 256
records are accepted, matching the two component budgets. A declared complete
collection does not prove that the final ATC records were retained.

No-install exception: typed dataclasses and explicit validation replace
Pydantic. No runtime dependency or filesystem access is required.
"""

from dataclasses import dataclass, field
import json
import re
from typing import Literal


Component = Literal["dwc3", "atc"]
Phase = Literal["begin", "end", "skip"]
REVISION = "dev147-usbdiag2-v1"
UINT32_MAX = (1 << 32) - 1
UINT64_MAX = (1 << 64) - 1
INT32_MIN = -(1 << 31)
INT32_MAX = (1 << 31) - 1
COMMON_FIELDS = frozenset((
  "schema", "revision", "board", "component", "target", "seq",
  "generation", "event", "phase",
))
BOOLEAN_FIELDS = frozenset((
  "usb2_present", "usb2_error", "swap_lanes", "pipehandler_up",
))


@dataclass(frozen=True)
class SoftwareFinding:
  kind: Literal["early_null_then_late_host_setter"]
  dwc3_generation: int
  attempt: int
  atc_generation: int


@dataclass(frozen=True)
class FailedOperation:
  """A closed operation's nonzero return; ATC has no attempt, represented by 0."""

  component: str
  generation: int
  attempt: int
  event: str
  ret: int


@dataclass(frozen=True)
class ValidationResult:
  status: Literal["positive_software_sequence", "inconclusive"]
  findings: tuple[SoftwareFinding, ...]
  issues: tuple[str, ...]
  failed_operations: tuple[FailedOperation, ...]
  negative_late_setter_claim: bool = False
  limitations: tuple[str, ...] = (
    "software_order_only",
    "host_init_is_not_hcd_completion",
    "no_caller_attribution",
    "consecutive_prefix_does_not_prove_tail",
  )


@dataclass(frozen=True)
class _Identity:
  sha256: str
  build_id: str


@dataclass(frozen=True)
class _Record:
  index: int
  monotonic_us: int
  component: Component
  seq: int
  generation: int
  event: str
  phase: Phase
  attempt: int | None
  ret: int | None
  role: int | None
  state: int | None
  target_state: int | None
  mode: int | None
  submode: int | None
  current_mode: int | None
  target_mode: int | None
  usb2_present: bool | None
  usb2_error: bool | None
  swap_lanes: bool | None
  pipehandler_up: bool | None


@dataclass(frozen=True)
class _Pair:
  begin: _Record
  end: _Record


@dataclass
class _Stream:
  generation: int = 0
  last_seq: int = 0
  next_attempt: int = 1
  probe_result: int | None = None
  seen: set[int] = field(default_factory=set)
  opened: dict[tuple[int, str, int | None], _Record] = field(default_factory=dict)


class _Invalid(ValueError):
  """Only fixed issue codes leave the parser; never echo untrusted data."""


def _object(value: object, keys: frozenset[str], issue: str) -> dict[str, object]:
  if not isinstance(value, dict) or len(value) != len(keys) or set(value) != keys:
    raise _Invalid(issue)
  return {key: value[key] for key in keys}


def _integer(value: object, minimum: int, maximum: int, issue: str) -> int:
  if not isinstance(value, int) or isinstance(value, bool):
    raise _Invalid(issue)
  if not minimum <= value <= maximum:
    raise _Invalid(issue)
  return value


def _hex(value: object, length: int, issue: str) -> str:
  if not isinstance(value, str) or len(value) != length:
    raise _Invalid(issue)
  if re.fullmatch(r"[0-9a-f]+", value) is None:
    raise _Invalid(issue)
  return value


def _identities(value: object, issue: str) -> tuple[_Identity, _Identity]:
  components = _object(value, frozenset(("dwc3", "atc")), issue)
  result: list[_Identity] = []
  for component in ("dwc3", "atc"):
    data = _object(components[component], frozenset(("sha256", "build_id")), issue)
    result.append(_Identity(
      _hex(data["sha256"], 64, issue), _hex(data["build_id"], 40, issue),
    ))
  return result[0], result[1]


def _timestamp(value: object) -> int:
  if not isinstance(value, str) or re.fullmatch(r"0|[1-9][0-9]{0,19}", value) is None:
    raise _Invalid("invalid_envelope")
  return _integer(int(value), 0, UINT64_MAX, "invalid_envelope")


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
  result: dict[str, object] = {}
  for key, value in pairs:
    if key in result:
      raise _Invalid("duplicate_json_key")
    result[key] = value
  return result


def _reject_constant(value: str) -> object:
  raise _Invalid("invalid_json")


def _variant(component: Component, event: str, phase: Phase) -> frozenset[str]:
  """Mirror the fixed revision's event fields, not a general JSON-schema engine."""
  names: tuple[str, ...]
  if event == "capture_capped" and phase == "end":
    names = ()
  elif component == "dwc3":
    if event == "probe" and phase in ("begin", "end"):
      names = ()
    elif event == "role":
      names = ("role", "state")
    elif event == "init" and phase in ("begin", "end"):
      names = ("state", "target_state")
    elif event == "early_usb2" and phase in ("begin", "end"):
      names = ("mode", "usb2_present", "usb2_error")
    elif event in ("reset_deassert", "reset_assert", "host_init", "gadget_init") and phase in ("begin", "end"):
      names = ()
    elif event == "core_init" and phase == "begin":
      names = ("state",)
    elif event == "core_init" and phase == "end":
      names = ("state", "usb2_present", "usb2_error")
    else:
      raise _Invalid("invalid_record")
  elif event in ("probe", "finalize") and phase in ("begin", "end"):
    names = ()
  elif event == "mux":
    names = ("current_mode", "target_mode", "swap_lanes", "pipehandler_up")
  elif event in ("usb2_power_on", "usb2_power_off") and phase in ("begin", "end"):
    names = ()
  elif event == "usb2_set_mode" and phase in ("begin", "end"):
    names = ("mode", "submode")
  else:
    raise _Invalid("invalid_record")
  if phase in ("end", "skip") and event not in (
    "capture_capped", "usb2_power_on", "usb2_power_off",
  ):
    names += ("ret",)
  return frozenset(names)


def _number(body: dict[str, object], name: str) -> int | None:
  if name not in body:
    return None
  return _integer(body[name], INT32_MIN, INT32_MAX, "invalid_record")


def _boolean(body: dict[str, object], name: str) -> bool | None:
  if name not in body:
    return None
  value = body[name]
  if not isinstance(value, bool):
    raise _Invalid("invalid_record")
  return value


def _record(raw: object, index: int, monotonic_us: int) -> _Record:
  if not isinstance(raw, str):
    raise _Invalid("invalid_record")
  # A stripped journal newline still occupies one byte in the source limit.
  if len(raw) + (0 if raw.endswith("\n") else 1) > 384:
    raise _Invalid("record_too_long")
  if not raw.isascii() or "\n" in raw.removesuffix("\n") or "\r" in raw:
    raise _Invalid("invalid_record")
  try:
    decoded: object = json.loads(
      raw, object_pairs_hook=_unique_object, parse_constant=_reject_constant,
    )
  except (json.JSONDecodeError, RecursionError):
    raise _Invalid("invalid_json") from None
  if not isinstance(decoded, dict):
    raise _Invalid("invalid_record")
  component_value = decoded.get("component")
  if component_value == "dwc3":
    component: Component = "dwc3"
  elif component_value == "atc":
    component = "atc"
  else:
    raise _Invalid("invalid_record")
  event = decoded.get("event")
  phase_value = decoded.get("phase")
  if not isinstance(event, str):
    raise _Invalid("invalid_record")
  if phase_value == "begin":
    phase: Phase = "begin"
  elif phase_value == "end":
    phase = "end"
  elif phase_value == "skip":
    phase = "skip"
  else:
    raise _Invalid("invalid_record")
  extras = _variant(component, event, phase)
  names = COMMON_FIELDS | extras
  if component == "dwc3":
    names |= frozenset(("attempt",))
  body = _object(decoded, names, "invalid_record")
  if (
    _integer(body["schema"], 1, 1, "invalid_record") != 1
    or body["revision"] != REVISION or body["board"] != "j413"
    or body["target"] != "front_lower"
  ):
    raise _Invalid("invalid_record")
  seq = _integer(body["seq"], 1, 128, "invalid_record")
  if (event == "capture_capped") != (seq == 128):
    raise _Invalid("invalid_record")
  generation = _integer(body["generation"], 1, UINT32_MAX, "invalid_record")
  attempt: int | None = None
  if component == "dwc3":
    minimum, maximum = 1, UINT32_MAX
    if event in ("probe", "role"):
      minimum, maximum = 0, 0
    elif event == "capture_capped":
      minimum = 0
    attempt = _integer(body["attempt"], minimum, maximum, "invalid_record")
  for name in extras:
    if name in BOOLEAN_FIELDS:
      _boolean(body, name)
    else:
      _number(body, name)
  if phase == "skip" and body["ret"] != 0:
    raise _Invalid("invalid_record")
  if body.get("usb2_error") is True and body.get("usb2_present") is not True:
    raise _Invalid("invalid_record")
  return _Record(
    index, monotonic_us, component, seq, generation, event, phase, attempt,
    _number(body, "ret"), _number(body, "role"), _number(body, "state"),
    _number(body, "target_state"), _number(body, "mode"), _number(body, "submode"),
    _number(body, "current_mode"), _number(body, "target_mode"),
    _boolean(body, "usb2_present"), _boolean(body, "usb2_error"),
    _boolean(body, "swap_lanes"), _boolean(body, "pipehandler_up"),
  )


def _capture(payload: object, manifest: object) -> tuple[_Record, ...]:
  expected = _object(manifest, frozenset(("revision", "components")), "invalid_manifest")
  if expected["revision"] != REVISION:
    raise _Invalid("invalid_manifest")
  identities = _identities(expected["components"], "invalid_manifest")
  data = _object(payload, frozenset((
    "schema", "boot_id", "collection_start_monotonic_us",
    "collection_end_monotonic_us", "collection_complete", "identities", "records",
  )), "invalid_capture")
  _integer(data["schema"], 1, 1, "invalid_capture")
  boot_id = _hex(data["boot_id"], 32, "invalid_capture")
  if _identities(data["identities"], "identity_mismatch") != identities:
    raise _Invalid("identity_mismatch")
  _integer(data["collection_start_monotonic_us"], 0, 0, "collection_boundary")
  end = _integer(data["collection_end_monotonic_us"], 1, UINT64_MAX, "collection_boundary")
  if data["collection_complete"] is not True:
    raise _Invalid("collection_boundary")
  entries = data["records"]
  if not isinstance(entries, list):
    raise _Invalid("invalid_capture")
  if len(entries) > 256:
    raise _Invalid("record_limit")
  if not entries:
    raise _Invalid("missing_start")
  result: list[_Record] = []
  cursors: set[str] = set()
  previous_time = 0
  for index, item in enumerate(entries):
    envelope = _object(item, frozenset((
      "_BOOT_ID", "PRIORITY", "__CURSOR", "__MONOTONIC_TIMESTAMP",
      "__REALTIME_TIMESTAMP", "MESSAGE",
    )), "invalid_envelope")
    if envelope["_BOOT_ID"] != boot_id or envelope["PRIORITY"] != "6":
      raise _Invalid("invalid_envelope")
    cursor = envelope["__CURSOR"]
    if (
      not isinstance(cursor, str) or not 1 <= len(cursor) <= 512
      or not cursor.isascii() or any(ord(char) <= 32 or ord(char) == 127 for char in cursor)
      or cursor in cursors
    ):
      raise _Invalid("invalid_envelope")
    cursors.add(cursor)
    monotonic_us = _timestamp(envelope["__MONOTONIC_TIMESTAMP"])
    _timestamp(envelope["__REALTIME_TIMESTAMP"])
    if monotonic_us > end:
      raise _Invalid("collection_boundary")
    if monotonic_us < previous_time:
      raise _Invalid("invalid_envelope")
    previous_time = monotonic_us
    result.append(_record(envelope["MESSAGE"], index, monotonic_us))
  return tuple(result)


def _requests_match(begin: _Record, end: _Record) -> bool:
  if begin.event == "role":
    return begin.role == end.role and (end.phase != "skip" or begin.state == end.state)
  if begin.event == "init":
    return begin.target_state == end.target_state
  if begin.event == "early_usb2":
    return (
      begin.mode == end.mode and begin.usb2_present == end.usb2_present
      and begin.usb2_error == end.usb2_error
    )
  if begin.event == "usb2_set_mode":
    return begin.mode == end.mode and begin.submode == end.submode
  if begin.event == "mux":
    return begin.target_mode == end.target_mode and (
      end.phase != "skip" or (
        begin.current_mode == end.current_mode == begin.target_mode
        and begin.swap_lanes == end.swap_lanes
        and begin.pipehandler_up == end.pipehandler_up
      )
    )
  return True


def _pairs(records: tuple[_Record, ...]) -> tuple[tuple[_Pair, ...], tuple[str, ...]]:
  streams: dict[Component, _Stream] = {"dwc3": _Stream(), "atc": _Stream()}
  pairs: list[_Pair] = []
  issues: list[str] = []
  for record in records:
    stream = streams[record.component]
    if not stream.seen and (
      record.seq != 1 or record.generation != 1
      or record.event != "probe" or record.phase != "begin"
    ):
      issues.append("missing_start")
    if record.seq in stream.seen:
      issues.append("sequence_duplicate")
    elif record.seq < stream.last_seq:
      issues.append("sequence_reordered")
    if record.seq != stream.last_seq + 1:
      issues.append("sequence_gap")
    stream.seen.add(record.seq)
    stream.last_seq = record.seq
    if record.event == "probe" and record.phase == "begin":
      if record.generation != stream.generation + 1:
        issues.append("generation_order")
      if stream.opened:
        issues.append("unclosed_pair")
      stream.generation = record.generation
      stream.next_attempt = 1
      stream.probe_result = None
    elif record.generation != stream.generation:
      issues.append("generation_order")
    elif stream.probe_result not in (None, 0):
      issues.append("failed_generation")
    if record.event == "capture_capped":
      issues.append("capture_capped")
      continue
    key = record.generation, record.event, record.attempt
    if record.component == "dwc3" and record.attempt:
      init_key = record.generation, "init", record.attempt
      if record.event == "init" and record.phase == "begin":
        if record.attempt != stream.next_attempt or any(
          opened.event == "init" for opened in stream.opened.values()
        ):
          issues.append("attempt_order")
        stream.next_attempt = record.attempt + 1
      elif init_key not in stream.opened:
        issues.append("attempt_order")
    if record.phase == "begin":
      if key in stream.opened:
        issues.append("pair_mismatch")
      stream.opened[key] = record
      continue
    begin = stream.opened.pop(key, None)
    if begin is None:
      issues.append("unclosed_pair")
      continue
    if not _requests_match(begin, record):
      issues.append("pair_mismatch")
    if record.event == "init" and any(
      opened.attempt == record.attempt for opened in stream.opened.values()
    ):
      issues.append("unclosed_pair")
    if record.event == "probe":
      stream.probe_result = record.ret
    pairs.append(_Pair(begin, record))
  for stream in streams.values():
    if not stream.seen:
      issues.append("missing_start")
    if stream.opened:
      issues.append("unclosed_pair")
  return tuple(pairs), tuple(dict.fromkeys(issues))


def _children(init: _Pair, pairs: tuple[_Pair, ...]) -> tuple[_Pair, ...]:
  return tuple(pair for pair in pairs if (
    pair.begin.component == "dwc3" and pair.begin.event not in ("probe", "role", "init")
    and pair.begin.generation == init.begin.generation
    and pair.begin.attempt == init.begin.attempt
  ))


def _successful_init(init: _Pair, pairs: tuple[_Pair, ...]) -> bool:
  children = _children(init, pairs)
  expected = (
    "early_usb2", "reset_deassert", "core_init",
    "host_init" if init.begin.target_state == 2 else "gadget_init",
  )
  if tuple(pair.begin.event for pair in children) != expected:
    return False
  if any(pair.end.ret != 0 for pair in children[1:]):
    return False
  previous_end = init.begin.index
  for pair in children:
    if not previous_end < pair.begin.index < pair.end.index < init.end.index:
      return False
    previous_end = pair.end.index
  return init.begin.target_state in (2, 3) and init.end.state == init.begin.target_state


def _atc_probes_complete(pairs: tuple[_Pair, ...]) -> bool:
  """A ready probe must include its one finalize call and mandatory power-off."""
  probes = tuple(pair for pair in pairs if (
    pair.begin.component == "atc" and pair.begin.event == "probe"
  ))
  finalizes = tuple(pair for pair in pairs if (
    pair.begin.component == "atc" and pair.begin.event == "finalize"
  ))
  for finalize in finalizes:
    if sum(probe.begin.generation == finalize.begin.generation for probe in probes) != 1:
      return False
  for probe in probes:
    related = tuple(finalize for finalize in finalizes if (
      finalize.begin.generation == probe.begin.generation
    ))
    if not related:
      # Allocation, resource mapping, or tunables can fail before finalize.
      # Any other operation in that generation would contradict that early exit.
      if probe.end.ret == 0 or any(
        pair.begin.component == "atc" and pair.begin.generation == probe.begin.generation
        and pair.begin.event != "probe" for pair in pairs
      ):
        return False
      continue
    if len(related) != 1:
      return False
    finalize = related[0]
    if not (
      probe.begin.index < finalize.begin.index < finalize.end.index < probe.end.index
      and finalize.end.ret == probe.end.ret
    ):
      return False
    power_off = tuple(pair for pair in pairs if (
      pair.begin.component == "atc" and pair.begin.event == "usb2_power_off"
      and pair.begin.generation == probe.begin.generation
      and finalize.begin.index < pair.begin.index < pair.end.index < finalize.end.index
    ))
    if len(power_off) != 1:
      return False
  return True


def _findings(records: tuple[_Record, ...], pairs: tuple[_Pair, ...]) -> tuple[SoftwareFinding, ...]:
  findings: list[SoftwareFinding] = []
  probes = tuple(pair for pair in pairs if pair.begin.event == "probe")
  setters = tuple(pair for pair in pairs if (
    pair.begin.component == "atc" and pair.begin.event == "usb2_set_mode"
    and pair.begin.mode == 1 and pair.begin.submode == 0 and pair.end.ret == 0
  ))
  for init in pairs:
    if (
      init.begin.component != "dwc3" or init.begin.event != "init"
      or init.begin.state != 0 or init.begin.target_state != 2 or init.end.ret != 0
      or init.begin.attempt is None or not _successful_init(init, pairs)
    ):
      continue
    children = _children(init, pairs)
    early, _, core, _ = children
    if (
      early.begin.mode != 1 or early.end.ret != 0
      or early.begin.usb2_present is not False or early.begin.usb2_error is not False
      or core.begin.state != 0 or core.end.state != 1
      or core.end.usb2_present is not True or core.end.usb2_error is not False
    ):
      continue
    if not any(
      probe.begin.component == "dwc3" and probe.begin.generation == init.begin.generation
      and probe.end.ret == 0 for probe in probes
    ):
      continue
    if not any(
      role.begin.component == "dwc3" and role.begin.event == "role"
      and role.begin.generation == init.begin.generation
      and role.begin.role == 1 and role.end.ret == 0 and role.end.state == 2
      and role.begin.index < init.begin.index < init.end.index < role.end.index
      for role in pairs
    ):
      continue
    # A new role request, retry, or reprobe closes this observation interval.
    next_init = min((record.index for record in records if (
      record.component == "dwc3" and record.phase == "begin"
      and record.event in ("init", "probe", "role") and record.index > init.begin.index
    )), default=len(records))
    for setter in setters:
      if not (
        core.end.monotonic_us < setter.begin.monotonic_us
        and setter.end.index < next_init
      ):
        continue
      atc_probe = next((probe for probe in probes if (
        probe.begin.component == "atc" and probe.begin.generation == setter.begin.generation
        and probe.end.ret == 0 and probe.begin.index < init.begin.index
        and probe.end.index < setter.begin.index
      )), None)
      if atc_probe is None:
        continue
      if any(
        record.component == "atc" and record.event == "probe" and record.phase == "begin"
        and atc_probe.begin.index < record.index <= setter.end.index
        for record in records
      ):
        continue
      findings.append(SoftwareFinding(
        "early_null_then_late_host_setter", init.begin.generation,
        init.begin.attempt, setter.begin.generation,
      ))
      break
  return tuple(findings)


def validate_capture(payload: object, expected_manifest: object) -> ValidationResult:
  """Validate diagnostic-only saved envelopes without modifying the input.

  The caller supplies the fixed revision's reviewed two-binary manifest and
  matching observed identities. Unknown fields, malformed data, reordered or
  missing sequences, incomplete pairs, and capped captures fail closed. Inputs
  must be ordinary decoded JSON values. Non-diagnostic journal records belong
  in the separately retained full capture, not this normalized packet.
  ATC probe results must match a nested finalize and its mandatory power-off
  pair; only an earlier failed probe can omit those initialization records.

  Positive findings require a closed successful HOST attempt and strict
  core-end/setter-begin non-overlap within the same observed ATC lifetime and
  before another DWC3 role request, attempt, or probe. They identify software
  order only, never a caller
  or hardware cause. A collection boundary cannot prove that no later setter
  or cap marker was lost. This API never makes a negative late-setter claim.
  """
  try:
    records = _capture(payload, expected_manifest)
  except _Invalid as error:
    return ValidationResult("inconclusive", (), (str(error),), ())
  pairs, issues = _pairs(records)
  failures = tuple(FailedOperation(
    pair.begin.component, pair.begin.generation, pair.begin.attempt or 0,
    pair.begin.event, pair.end.ret,
  ) for pair in pairs if pair.end.ret is not None and pair.end.ret != 0)
  if any(
    pair.begin.component == "dwc3" and pair.begin.event == "init" and pair.end.ret == 0
    and not _successful_init(pair, pairs) for pair in pairs
  ):
    issues = tuple(dict.fromkeys((*issues, "incomplete_attempt")))
  if not _atc_probes_complete(pairs):
    issues = tuple(dict.fromkeys((*issues, "incomplete_probe")))
  if issues:
    return ValidationResult("inconclusive", (), issues, failures)
  findings = _findings(records, pairs)
  if findings:
    return ValidationResult("positive_software_sequence", findings, (), failures)
  return ValidationResult("inconclusive", (), ("no_positive_sequence",), failures)
