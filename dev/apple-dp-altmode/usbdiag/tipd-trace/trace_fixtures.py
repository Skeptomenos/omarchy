"""Independent synthetic T1 inputs; no producer or parser code is imported."""

from dataclasses import dataclass
import json
from typing import Literal


Scalar = str | int | bool
BOOT_ID = "0123456789abcdef0123456789abcdef"
LABEL = "synthetic-t1-no-hardware"
IMAGE_SHA256 = "11" * 32
IMAGE_SIZE = 12345
TIPD_SHA256 = "22" * 32
TIPD_BUILD_ID = "33" * 20


@dataclass(frozen=True)
class RecordSpec:
  event: str
  phase: str
  worker: int = 0
  generation: int = 1
  fields: tuple[tuple[str, Scalar], ...] = ()


def spec(
  event: str,
  phase: str,
  *,
  worker: int = 0,
  generation: int = 1,
  **fields: Scalar,
) -> RecordSpec:
  return RecordSpec(event, phase, worker, generation, tuple(fields.items()))


def cached_pair(
  *,
  generation: int = 1,
  plug: bool = True,
  hpd: bool = True,
  hpd_change: bool = False,
) -> tuple[RecordSpec, ...]:
  return (
    spec("cache", "stored", generation=generation,
         plug=plug, usb2=True, usb3=True, hpd=hpd, flip=False,
         device=False, power=3),
    spec("queue", "queued", generation=generation,
         plug=plug, usb2=True, usb3=True, hpd=hpd, flip=False,
         device=False, power=3, disconnect=False, hpd_change=hpd_change),
  )


def normal_worker(
  *,
  worker: int = 1,
  generation: int = 1,
  none_pair: bool = False,
  cached_device: bool = False,
  mux_ret: int = 0,
  role_ret: int = 0,
) -> tuple[RecordSpec, ...]:
  prefix = (spec(
    "worker", "begin", worker=worker, generation=generation,
    plug=True, usb2=True, usb3=True, hpd=True, flip=False,
    device=False, power=3, disconnect=False, hpd_change=False,
    connector=True, cached_device=cached_device,
  ),)
  if none_pair:
    transition = (
      spec("role", "begin", worker=worker, generation=generation,
           which="none", value=0),
      spec("role", "returned", worker=worker, generation=generation,
           which="none", value=0, ret=0),
    )
  else:
    transition = (spec(
      "role", "skip", worker=worker, generation=generation,
      which="none", value=0, reason="no_transition",
    ),)
  return prefix + transition + (
    spec("hpd", "skip", worker=worker, generation=generation,
         which="disconnected", reason="level_high_unchanged"),
    spec("mux", "begin", worker=worker, generation=generation,
         kind="dp", mode=4),
    spec("mux", "returned", worker=worker, generation=generation,
         kind="dp", mode=4, ret=mux_ret),
    spec("role", "begin", worker=worker, generation=generation,
         which="final", value=2 if cached_device else 1),
    spec("role", "returned", worker=worker, generation=generation,
         which="final", value=2 if cached_device else 1, ret=role_ret),
    spec("hpd", "begin", worker=worker, generation=generation,
         which="connected"),
    spec("hpd", "returned", worker=worker, generation=generation,
         which="connected"),
    spec("worker", "end", worker=worker, generation=generation,
         reason="complete", ret=0),
  )


def complete_specs(
  order: Literal["before_end", "after_end", "interleaved"] = "before_end",
  *,
  generation: int = 1,
  worker: int = 1,
  none_pair: bool = False,
  cached_device: bool = False,
  mux_ret: int = 0,
  role_ret: int = 0,
) -> tuple[RecordSpec, ...]:
  start = (spec("init", "begin", generation=generation),) + cached_pair(
    generation=generation,
  )
  end = spec("init", "end", generation=generation, reason="complete", ret=0)
  work = normal_worker(
    worker=worker, generation=generation, none_pair=none_pair,
    cached_device=cached_device, mux_ret=mux_ret, role_ret=role_ret,
  )
  if order == "before_end":
    return start + work + (end,)
  if order == "after_end":
    return start + (end,) + work
  # The init result can occur between the worker's mux begin and return.
  return start + work[:4] + (end,) + work[4:]


def capture(
  records: tuple[RecordSpec, ...],
  *,
  arrival_order: tuple[int, ...] | None = None,
) -> str:
  if arrival_order is None:
    arrival_order = tuple(range(len(records)))
  if sorted(arrival_order) != list(range(len(records))):
    raise ValueError("fixture arrival order must be a permutation")
  messages: list[str] = []
  for sequence, record in enumerate(records, 1):
    body: dict[str, object] = {
      "rev": "dev147-tipddiag1-v1", "board": "j413",
      "target": "front_lower", "component": "tipd", "seq": sequence,
      "gen": record.generation, "worker": record.worker,
      "event": record.event, "phase": record.phase,
    }
    body.update(record.fields)
    messages.append(json.dumps(body, separators=(",", ":")) + "\n")
  envelopes: list[dict[str, object]] = []
  for arrival, index in enumerate(arrival_order, 1):
    envelopes.append({
      "_BOOT_ID": BOOT_ID, "PRIORITY": "6", "__CURSOR": f"fixture:{arrival}",
      "__MONOTONIC_TIMESTAMP": str(arrival),
      "__REALTIME_TIMESTAMP": str(1_800_000_000_000_000 + arrival),
      "MESSAGE": messages[index],
    })
  return json.dumps({
    "schema": "dev147-tipd-capture1", "kind": "synthetic_fixture",
    "fixture_label": LABEL, "boot_id": BOOT_ID,
    "collection_start_monotonic_us": 0,
    "collection_end_monotonic_us": len(records) + 100,
    "collection_complete": True, "all_priorities": True,
    "artifacts": {
      "image_sha256": IMAGE_SHA256, "image_size": IMAGE_SIZE,
      "tipd_sha256": TIPD_SHA256, "tipd_build_id": TIPD_BUILD_ID,
    },
    "records": envelopes,
  }, separators=(",", ":"))


def complete_capture(
  order: Literal["before_end", "after_end", "interleaved"] = "before_end",
) -> str:
  return capture(complete_specs(order))


def cap_capture(*, open_worker: bool = False, terminal_worker: bool = False) -> str:
  if open_worker:
    prefix = complete_specs() + cached_pair() * 56
    record127 = normal_worker(worker=2)[0]
  else:
    order: Literal["before_end", "after_end"] = "before_end"
    if terminal_worker:
      order = "after_end"
    base = complete_specs(order, none_pair=True)
    prefix = base[:3] + cached_pair() * 56 + base[3:-1]
    record127 = base[-1]
  records = prefix + (record127, spec(
    "cap", "end", worker=record127.worker, generation=record127.generation,
    limit=128, reason="budget",
  ))
  if len(records) != 128:
    raise ValueError("fixture cap shape must contain exactly 128 records")
  return capture(records)


def payload(document: str) -> dict[str, object]:
  result: object = json.loads(document)
  if not isinstance(result, dict) or not all(isinstance(key, str) for key in result):
    raise ValueError("fixture capture must be an object")
  return dict(result)


def entries(document: str) -> list[dict[str, object]]:
  value = payload(document).get("records")
  if not isinstance(value, list):
    raise ValueError("fixture records must be a list")
  result: list[dict[str, object]] = []
  for item in value:
    if not isinstance(item, dict) or not all(isinstance(key, str) for key in item):
      raise ValueError("fixture envelope must be an object")
    result.append(dict(item))
  return result


def body(entry: dict[str, object]) -> dict[str, object]:
  raw = entry.get("MESSAGE")
  if not isinstance(raw, str):
    raise ValueError("fixture message must be a string")
  result: object = json.loads(raw)
  if not isinstance(result, dict) or not all(isinstance(key, str) for key in result):
    raise ValueError("fixture message must be an object")
  return dict(result)


def with_entries(document: str, records: list[dict[str, object]]) -> str:
  value = payload(document)
  value["records"] = records
  return json.dumps(value, separators=(",", ":"))


def change_body(document: str, index: int, **changes: object) -> str:
  records = entries(document)
  value = body(records[index])
  value.update(changes)
  records[index]["MESSAGE"] = json.dumps(value, separators=(",", ":")) + "\n"
  return with_entries(document, records)


def omit(document: str, index: int, *, renumber: bool = False) -> str:
  records = entries(document)
  del records[index]
  if renumber:
    for sequence, entry in enumerate(records, 1):
      value = body(entry)
      value["seq"] = sequence
      entry["MESSAGE"] = json.dumps(value, separators=(",", ":")) + "\n"
  return with_entries(document, records)
