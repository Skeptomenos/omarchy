"""Pure E-to-T1 contract; no operational assembler or accepted binary binding.

The runner authenticates cpio_image and prepare_image before importing this
module. Their pure functions retain their original source pins. No old main
or image orchestration runs here. Structural and header validation cannot
authenticate a module or complete control proof. Assembly remains unavailable
without separate real-binary, fresh-control, containment and orchestration
reviews.
"""

from dataclasses import dataclass
import hashlib
import json
import stat
from typing import NoReturn

from cpio_image import Archive, ArchiveError, MAX_ARCHIVE_BYTES, MAX_MEMBERS, Member
from cpio_image import parse_newc, read_regular, replace_members, write_new
from prepare_image import single_gzip
from verify_control import select_indexes


KERNEL = "7.1.6-1-1-ARCH"
PREFIX = f"usr/lib/modules/{KERNEL}/"
TIPD = PREFIX + "kernel/drivers/usb/typec/tipd/tps6598x-core.ko"
FRONTEND = PREFIX + "kernel/drivers/usb/typec/tipd/tps6598x.ko"
ATC = PREFIX + "kernel/drivers/phy/apple/phy-apple-atc.ko"
DWC = PREFIX + "kernel/drivers/usb/dwc3/dwc3-apple.ko"
REVISION = "dev147-tipddiag1-v1"
E_SHA256 = "4d4f0557af57eebcc33322f004bcc7968254e644b069a11102375df0b31a52ae"
E_BYTES = 19191513
EARLY_SHA256 = "967bc6adcff42e59abcfb4e509f6c80fd65588e0861d8c1c3189a135f10955b4"
EARLY_BYTES = 10240
MAIN_SHA256 = "7be7b4b03367b5ce4b356fe35977edba6540af0a7df930dbff990286c9b98e28"
MAIN_BYTES = 61286668
INDEX_SHA256 = {
  "modules.alias.bin": "ca6ca7be95509eb294c2e67090bfa84dcbab855fb0489e504804593a257c4ea9",
  "modules.builtin.alias.bin": "9635eaa0d8c3d2f89c98789adce44dfd047f8cb11c7c9d0aa60199defc2ad962",
  "modules.builtin.bin": "edf2e707c121431f4f77b842ffd0a37fad5c0a6df198296fd6ef0b7f3227ac74",
  "modules.dep.bin": "436095f4779ccbd9f0c44b90febef13b62be50c9518dd499c151843fdf1feb3d",
  "modules.devname": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "modules.softdep": "6a8f2009d87deba7a2de46e3d0c46b114fe388d188b00b9a382fc2156aabb676",
  "modules.symbols.bin": "a3f1e745b7675daaec99c7c7ebadc7d67b318143901e063674494c210b12ace6",
}

# Unknown identities cannot be supplied by an argument, environment, or fixture.
T1_MODULE_SHA256: str | None = None
T1_BUILD_ID: str | None = None
E_CONTROL_PROOF_SHA256: str | None = None


class ImageContractError(RuntimeError):
  """A T1-specific contract does not hold."""


@dataclass(frozen=True)
class ArchiveDelta:
  path: str
  old_sha256: str
  new_sha256: str
  preserved_raw_records: int
  unchanged_indexes: int


@dataclass(frozen=True)
class EControlHeader:
  """Validated header only; not authentication or complete control evidence."""

  base_sha256: str
  base_bytes: int
  main_records: int
  module_count: int
  indexes: tuple[tuple[str, str], ...]


def _require(condition: bool, code: str) -> None:
  if not condition:
    raise ImageContractError(code)


def _validated_archive(value: Archive) -> Archive:
  """Compare the supplied model with a fresh parse, then use the parsed model."""
  _require(type(value) is Archive, "ARCHIVE_MODEL")
  _require(type(value.raw) is bytes and type(value.tail) is bytes
           and type(value.members) is tuple and len(value.members) <= MAX_MEMBERS, "ARCHIVE_MODEL")
  for member in value.members:
    _require(type(member) is Member, "ARCHIVE_MODEL")
    _require(type(member.name) is str and type(member.raw_name) is bytes
             and type(member.payload) is bytes and type(member.raw) is bytes
             and type(member.fields) is tuple and len(member.fields) == 13
             and all(type(field) is int for field in member.fields), "ARCHIVE_MODEL")
  try:
    parsed = parse_newc(value.raw)
  except ArchiveError:
    raise ImageContractError("ARCHIVE_MODEL") from None
  _require(value == parsed, "ARCHIVE_MODEL")
  return parsed


def archive_delta(before: Archive, after: Archive, expected_tipd: bytes) -> ArchiveDelta:
  """Recognize one structural TIPD replacement, not an accepted T1 binary."""
  before, after = _validated_archive(before), _validated_archive(after)
  _require(tuple(member.name for member in before.members) ==
           tuple(member.name for member in after.members), "ARCHIVE_MEMBERS")
  _require(before.tail == after.tail, "ARCHIVE_TAIL")
  _require(type(expected_tipd) is bytes and 0 < len(expected_tipd) <= MAX_ARCHIVE_BYTES,
           "TIPD_EXPECTED_PAYLOAD")
  delta: ArchiveDelta | None = None
  for old, new in zip(before.members, after.members, strict=True):
    if old.name != TIPD:
      _require(old.raw == new.raw, "ARCHIVE_RAW_RECORD")
    else:
      _require(new.payload == expected_tipd, "TIPD_EXPECTED_PAYLOAD")
      _require(new.payload != old.payload, "TIPD_NO_CHANGE")
      _require(stat.S_ISREG(old.fields[1]) and old.fields[4] in (0, 1)
               and old.raw_name == new.raw_name
               and all(old.fields[index] == new.fields[index] for index in range(13) if index != 6),
               "TIPD_METADATA")
      payload_start = (110 + len(old.raw_name) + 3) & ~3
      _require(old.raw[:54] == new.raw[:54] and old.raw[62:payload_start] == new.raw[62:payload_start],
               "TIPD_RAW_HEADER")
      delta = ArchiveDelta(TIPD, hashlib.sha256(old.payload).hexdigest(),
                           hashlib.sha256(new.payload).hexdigest(), len(before.members) - 1, 7)
  if delta is None:
    raise ImageContractError("ARCHIVE_MEMBERS")
  try:
    before_indexes, after_indexes = select_indexes(before), select_indexes(after)
  except RuntimeError:
    raise ImageContractError("INDEX_SET") from None
  validate_zero_index_delta(before_indexes, after_indexes)
  # The pinned replacement also checks parents, descendants and hardlink rules.
  try:
    expected_raw = replace_members(before, {TIPD: expected_tipd}, ())
  except ArchiveError:
    raise ImageContractError("TIPD_METADATA") from None
  _require(expected_raw == after.raw, "TIPD_RAW_HEADER")
  return delta


def validate_zero_index_delta(before: dict[str, bytes], after: dict[str, bytes]) -> None:
  """Require exactly the seven original index payloads, byte for byte."""
  for indexes in (before, after):
    _require(type(indexes) is dict and all(type(name) is str for name in indexes)
             and set(indexes) == set(INDEX_SHA256), "INDEX_SET")
    _require(all(type(payload) is bytes for payload in indexes.values()), "INDEX_PAYLOAD_TYPE")
    _require(sum(len(payload) for payload in indexes.values()) <= MAX_ARCHIVE_BYTES,
             "INDEX_PAYLOAD_TYPE")
  _require(all(before[name] == after[name] for name in INDEX_SHA256), "INDEX_BYTES")


def validate_e_base(payload: bytes) -> None:
  """Bind complete input bytes to the fixed E hash and byte count."""
  _require(type(payload) is bytes and len(payload) == E_BYTES
           and hashlib.sha256(payload).hexdigest() == E_SHA256, "E_BASE_IDENTITY")


def _unique_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
  result: dict[str, object] = {}
  for key, value in pairs:
    _require(type(key) is str and key not in result, "E_PROOF_SCHEMA")
    result[key] = value
  return result


def _reject_json_constant(value: str) -> NoReturn:
  raise ImageContractError("E_PROOF_SCHEMA")


def validate_e_control_header(raw: bytes) -> EControlHeader:
  """Parse an E-only header; authentication and complete controls stay separate."""
  _require(type(raw) is bytes and 0 < len(raw) <= 2 * 1024 * 1024, "E_PROOF_SCHEMA")
  try:
    value: object = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_json_object,
                               parse_constant=_reject_json_constant)
  except (ValueError, RecursionError):
    raise ImageContractError("E_PROOF_SCHEMA") from None
  if type(value) is not dict:
    raise ImageContractError("E_PROOF_SCHEMA")
  expected: dict[str, str | int | bool] = {
    "schema": 1, "kind": "dev147-t1-e-control-v1",
    "base_sha256": E_SHA256, "base_bytes": E_BYTES,
    "early_records": 7, "early_bytes": EARLY_BYTES, "early_sha256": EARLY_SHA256,
    "main_records": 1163, "main_bytes": MAIN_BYTES, "main_sha256": MAIN_SHA256,
    "module_count": 200, "no_change_archive": True, "gzip_exact": True,
    "binary_only_lookup": True, "module_loaded": False, "image_staged": False,
  }
  _require(set(value) == set(expected) | {"indexes"}, "E_PROOF_SCHEMA")
  for name, required in expected.items():
    actual = value[name]
    _require(type(actual) is type(required), "E_PROOF_SCHEMA")
    _require(actual == required, "E_PROOF_IDENTITY")
  indexes = value["indexes"]
  if type(indexes) is not dict:
    raise ImageContractError("E_PROOF_INDEXES")
  _require(set(indexes) == set(INDEX_SHA256)
           and all(type(name) is str and type(digest) is str for name, digest in indexes.items())
           and indexes == INDEX_SHA256, "E_PROOF_INDEXES")
  return EControlHeader(E_SHA256, E_BYTES, 1163, 200, tuple(sorted(INDEX_SHA256.items())))


def require_operational_bindings() -> NoReturn:
  """No assembler exists at this test-first checkpoint, even with fake pins."""
  raise ImageContractError("T1_ASSEMBLY_UNAVAILABLE")


if __name__ == "__main__":
  require_operational_bindings()
