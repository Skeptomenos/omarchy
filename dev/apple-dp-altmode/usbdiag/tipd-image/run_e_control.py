"""Pure boundaries for a new, fixed E-only no-change control.

The runner authenticates the pure dependency chain before importing this
module. Historical C2 index bytes are test inputs only, never a completed
fresh-control proof. These functions read no file and launch no command.

The operational entry point and T1 assembly remain unavailable. Two fixed-path
functions expose only a distinct zero-child structural policy and result.
"""

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import stat
from typing import NoReturn

from cpio_image import Archive, parse_newc, write_new
from prepare_image import (
  ALIASES_HEADER, SYMBOLS_HEADER, WEAKDEP_HEADER, alias_entries,
  dependency_entries, single_gzip, validate_binary_dump,
)
from verify_control import Module, module_name, regular_member, select_indexes


KERNEL = "7.1.6-1-1-ARCH"
PREFIX = f"usr/lib/modules/{KERNEL}/"
E_SHA256 = "4d4f0557af57eebcc33322f004bcc7968254e644b069a11102375df0b31a52ae"
E_BYTES = 19191513
EARLY_SHA256 = "967bc6adcff42e59abcfb4e509f6c80fd65588e0861d8c1c3189a135f10955b4"
MAIN_SHA256 = "7be7b4b03367b5ce4b356fe35977edba6540af0a7df930dbff990286c9b98e28"
EARLY_BYTES = 10240
MAIN_BYTES = 61286668
PAYLOAD_SHA256 = {
  PREFIX + "kernel/drivers/usb/typec/tipd/tps6598x-core.ko":
    "bc02723db427639c6586d29eea7918e084874c741b60bf145585c6349fd07d70",
  PREFIX + "kernel/drivers/usb/typec/tipd/tps6598x.ko":
    "f9b9e0f01270016b72cf242178eeb2810e32888e2cd6e68cf0d6f549500e1308",
  PREFIX + "kernel/drivers/phy/apple/phy-apple-atc.ko":
    "fd1c3d105bd69a649a38e89e2ca0bcbe6f656200a0f211d58211e8c7b3ec944b",
  PREFIX + "kernel/drivers/usb/dwc3/dwc3-apple.ko":
    "d150400f9782c876972b2745d95617cd44e23574452f63980704911a467f7767",
}
INDEX_SHA256 = {
  "modules.alias.bin": "ca6ca7be95509eb294c2e67090bfa84dcbab855fb0489e504804593a257c4ea9",
  "modules.builtin.alias.bin": "9635eaa0d8c3d2f89c98789adce44dfd047f8cb11c7c9d0aa60199defc2ad962",
  "modules.builtin.bin": "edf2e707c121431f4f77b842ffd0a37fad5c0a6df198296fd6ef0b7f3227ac74",
  "modules.dep.bin": "436095f4779ccbd9f0c44b90febef13b62be50c9518dd499c151843fdf1feb3d",
  "modules.devname": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "modules.softdep": "6a8f2009d87deba7a2de46e3d0c46b114fe388d188b00b9a382fc2156aabb676",
  "modules.symbols.bin": "a3f1e745b7675daaec99c7c7ebadc7d67b318143901e063674494c210b12ace6",
}
GENERATED_SHA256 = {
  **INDEX_SHA256,
  "modules.symbols.bin": "5077fb001a5c48a2135ce8f651606b18578610bc660f430a59114e76be4f9437",
  "modules.alias": "9ea85f8fd754e394a63c6de9a93f9d8445ad3ebaf3d75eb8101a460dcf4127ac",
  "modules.dep": "48b6e5f5befe58918639ae27e3271984629ade44d7de8f46fa46e92c7b9150fe",
  "modules.symbols": "91299d9a80705a17c92068869293aa32c86985f751a5e6ea84024cb511ca539a",
  "modules.weakdep": "a1fffe1059d8150b5d402b3f284f507025a8d4b5881810cb17b3fda8b8ab9304",
}
DUMP_SHA256 = "c562726938a6e3d11d5b3661352508f00b74efd9cbadbb559c3680663da72c05"
INDEX_INPUT_SHA256 = {
  "modules.order": "497c8546d3131d01191f7a66b68047abce5e5235ae982890180007f55c51a927",
  "modules.builtin": "74de5bab05fe70496f7702d83974adf8816ea826f1d8579f3b3f4b28a3890d2b",
  "modules.builtin.modinfo": "702d4cabaa9bdc1b282d0e419ba091f64dc06ba737fe7319928bb3003adeea4b",
}
ALIASES = (
  "of:Nusb-pdT(null)Capple,cd321x", "of:Ndwc3T(null)Capple,t8103-dwc3",
  "of:Natc-phyT(null)Capple,t8103-atcphy",
)
EXPORTS = (
  "tipd_sn201202x_data", "tps6598x_regmap_config", "tipd_init", "tipd_cd321x_data",
  "tipd_tps6598x_data", "tipd_tps25750_data", "tipd_remove", "tipd_suspend", "tipd_resume",
)
CONTROL_ROOT = "/work/control-root"
LOOKUP_ROOT = "/work/lookup-root"
EMPTY_CONFIG = "/work/empty-modprobe.conf"
EARLY_PATH = "/work/e-early.cpio"
MAIN_PATH = "/work/e-main.cpio"
MAX_INDEX_BYTES = 64 * 1024 * 1024
MODULE_MODEL_SHA256 = "eee8ad06a36c1537d53e0c416db998110d10638076a32bdd3fc8987f65b54bff"
STRUCTURAL_BINDINGS = (
  "/inputs/recipe", "/inputs/subject", "/inputs/contract", "/inputs/assembly",
  "/inputs/control", "/inputs/helper", "/inputs/base", "/inputs/index-inputs",
)
STRUCTURAL_RECORD_ROOT = "/work/e-control-structural-records-e1"
STRUCTURAL_ARTIFACTS = (
  "/work/e-control-structural-header.json",
  "/work/e-control-structural-evidence.json",
  "/work/e-control-structural-result.json",
)
REAL_OPERATIONAL_ARTIFACTS = (
  "/work/e-control-header.json", "/work/e-control-evidence.json", "/work/e-control-result.json",
)
STDOUT_BYTES = 64 * 1024 * 1024
STDERR_BYTES = 65536
REPORT_BYTES = 128 * 1024


class RecipeError(RuntimeError):
  """A fixed E-control boundary failed; it is not a hardware verdict."""


@dataclass(frozen=True)
class ESelection:
  early: Archive
  main: Archive
  modules: tuple[Module, ...]
  indexes: dict[str, bytes]


@dataclass(frozen=True)
class Regeneration:
  dependencies: dict[str, tuple[str, ...]]
  alias_mappings: int
  symbol_mappings: int
  retained_symbol_sha256: str
  generated_symbol_sha256: str


@dataclass(frozen=True)
class StructuralPolicy:
  """The fixed input, plan and distinct output policy for a zero-child check."""

  bindings: tuple[str, ...]
  commands: tuple[tuple[str, ...], ...]
  record_root: str
  artifacts: tuple[str, ...]


@dataclass(frozen=True)
class StructuralAcceptance:
  """A complete zero-child structure result, never fresh-control proof."""

  records: int
  children_executed: int
  header_sha256: str
  evidence_sha256: str
  result_sha256: str
  status: str
  structural_validated: bool
  fresh_control_proved: bool
  image_created: bool
  module_loaded: bool
  staged: bool
  booted: bool


def _require(condition: bool, code: str) -> None:
  if not condition:
    raise RecipeError(code)


def _sha256(raw: bytes) -> str:
  return hashlib.sha256(raw).hexdigest()


def _validated_names(value: dict[str, str]) -> dict[str, str]:
  _require(type(value) is dict and len(value) == 200, "E_MODULE_MODEL")
  _require(all(
    type(name) is str and re.fullmatch(r"[A-Za-z0-9_]{1,128}", name) is not None
    and type(relative) is str and re.fullmatch(
      r"kernel/(?:[A-Za-z0-9_-]+/)*[A-Za-z0-9_][A-Za-z0-9_-]*\.ko", relative,
    ) is not None
    for name, relative in value.items()
  ), "E_MODULE_MODEL")
  try:
    _require(all(module_name(Path(relative).name) == name for name, relative in value.items()),
             "E_MODULE_MODEL")
  except (RuntimeError, ValueError, TypeError):
    raise RecipeError("E_MODULE_MODEL") from None
  _require(len(set(value.values())) == 200, "E_MODULE_MODEL")
  serialized = "".join(f"{name}={value[name]}\n" for name in sorted(value)).encode("ascii")
  _require(_sha256(serialized) == MODULE_MODEL_SHA256, "E_MODULE_MODEL")
  expected = {
    module_name(Path(path).name): path.removeprefix(PREFIX)
    for path in PAYLOAD_SHA256
  }
  _require(all(value.get(name) == relative for name, relative in expected.items()) and
           "lrw" in value, "E_MODULE_MODEL")
  return dict(value)


def select_e(base: bytes) -> ESelection:
  """Select the one authenticated E image without using the old W selector."""
  _require(type(base) is bytes and len(base) == E_BYTES and _sha256(base) == E_SHA256,
           "E_BASE_IDENTITY")
  try:
    early = parse_newc(base[:EARLY_BYTES])
    main_raw = single_gzip(base[EARLY_BYTES:], MAIN_BYTES)
    main = parse_newc(main_raw)
  except (RuntimeError, ValueError, KeyError, TypeError):
    raise RecipeError("E_ARCHIVE_MODEL") from None
  _require(
    len(early.members) == 7 and len(early.raw) == EARLY_BYTES
    and _sha256(early.raw) == EARLY_SHA256
    and len(main.members) == 1163 and len(main.raw) == MAIN_BYTES
    and _sha256(main.raw) == MAIN_SHA256,
    "E_ARCHIVE_MODEL",
  )
  _require(all(
    b"".join(member.raw for member in archive.members) + archive.tail == archive.raw
    for archive in (early, main)
  ), "E_ARCHIVE_MODEL")

  modules: list[Module] = []
  names: set[str] = set()
  try:
    for member in main.members:
      filename = Path(member.name).name
      if re.search(r"\.ko(?:\.|$)", filename) is None:
        continue
      _require(member.name.startswith(PREFIX + "kernel/") and member.name.endswith(".ko"),
               "E_MODULE_MODEL")
      regular_member(member)
      relative = Path(member.name.removeprefix(PREFIX))
      _require(relative.parts[0] == "kernel" and not any(
        part in ("", ".", "..") or any(char.isspace() for char in part)
        for part in relative.parts
      ), "E_MODULE_MODEL")
      name = module_name(filename)
      _require(name not in names, "E_MODULE_MODEL")
      names.add(name)
      modules.append(Module(name, relative, member))
  except (RuntimeError, ValueError, KeyError, TypeError, IndexError):
    raise RecipeError("E_MODULE_MODEL") from None
  _require(len(modules) == len(names) == 200, "E_MODULE_MODEL")
  by_path = {member.name: member for member in main.members}
  _require(all(path in by_path and _sha256(by_path[path].payload) == digest
               for path, digest in PAYLOAD_SHA256.items()), "E_MODULE_MODEL")
  _validated_names({module.name: str(module.relative) for module in modules})

  try:
    indexes = select_indexes(main)
  except (RuntimeError, ValueError, KeyError, TypeError):
    raise RecipeError("E_INDEX_SET") from None
  _require({name: _sha256(raw) for name, raw in indexes.items()} == INDEX_SHA256,
           "E_INDEX_IDENTITY")
  return ESelection(early, main, tuple(modules), dict(indexes))


def validate_regeneration(
  original: dict[str, bytes],
  generated: dict[str, bytes],
  dump: bytes,
  names: dict[str, str],
) -> Regeneration:
  """Validate exact fresh depmod outputs and the one symbol-bin exception."""
  _require(type(original) is dict and len(original) == len(INDEX_SHA256)
           and set(original) == set(INDEX_SHA256)
           and type(generated) is dict and len(generated) == len(GENERATED_SHA256)
           and set(generated) == set(GENERATED_SHA256), "E_INDEX_SET")
  _require(all(type(name) is str and type(raw) is bytes for name, raw in original.items())
           and all(type(name) is str and type(raw) is bytes for name, raw in generated.items())
           and sum(map(len, original.values())) <= MAX_INDEX_BYTES
           and sum(map(len, generated.values())) <= MAX_INDEX_BYTES, "E_INDEX_TYPE")
  _require({name: _sha256(raw) for name, raw in original.items()} == INDEX_SHA256,
           "E_INDEX_IDENTITY")
  _require({name: _sha256(raw) for name, raw in generated.items()} == GENERATED_SHA256,
           "E_GENERATED_IDENTITY")
  _require(type(dump) is bytes and len(dump) <= MAX_INDEX_BYTES and _sha256(dump) == DUMP_SHA256,
           "E_DUMP_IDENTITY")
  model = _validated_names(names)
  _require(all(generated[name] == original[name] for name in INDEX_SHA256
               if name != "modules.symbols.bin")
           and generated["modules.symbols.bin"] != original["modules.symbols.bin"],
           "E_GENERATED_IDENTITY")
  try:
    dependencies = dependency_entries(generated["modules.dep"], set(model.values()))
    aliases = alias_entries(generated["modules.alias"], ALIASES_HEADER)
    symbols = alias_entries(generated["modules.symbols"], SYMBOLS_HEADER)
    _require(generated["modules.weakdep"] == WEAKDEP_HEADER, "E_GENERATED_FORMAT")
    validate_binary_dump(dump, generated["modules.alias"], generated["modules.symbols"],
                         original["modules.softdep"])
  except RecipeError:
    raise
  except (RuntimeError, ValueError, KeyError, TypeError):
    raise RecipeError("E_GENERATED_FORMAT") from None
  _require(len(dependencies) == 200 and sum(aliases.values()) == 1408
           and sum(symbols.values()) == 596, "E_GENERATED_FORMAT")
  return Regeneration(
    dict(dependencies), 1408, 596, INDEX_SHA256["modules.symbols.bin"],
    GENERATED_SHA256["modules.symbols.bin"],
  )


def _probe(root: str, target: str) -> tuple[str, ...]:
  return (
    "/usr/bin/modprobe", "--dry-run", "--show-depends", "-d", root,
    "-S", KERNEL, "-C", EMPTY_CONFIG, target,
  )


def command_plan(names: dict[str, str]) -> tuple[tuple[str, ...], ...]:
  """Return the fixed read-only plan; this function launches no subprocess."""
  model = _validated_names(names)
  result: list[tuple[str, ...]] = []
  for path in (EARLY_PATH, MAIN_PATH):
    result.extend((
      ("/usr/bin/cpio", "--list", "--quiet", "--file", path),
      ("/usr/bin/bsdtar", "--list", "--file", path),
    ))
  result.append(("/usr/bin/gzip",))
  for path in PAYLOAD_SHA256:
    result.append((
      "/usr/bin/bsdtar", "--extract", "--to-stdout", "--file", MAIN_PATH, path,
    ))
  result.append(("/usr/bin/depmod", "-b", CONTROL_ROOT, KERNEL))
  result.extend((_probe(CONTROL_ROOT, "--show-config"), _probe(LOOKUP_ROOT, "--show-config")))
  for name in sorted(model):
    result.extend((
      ("/usr/bin/modinfo", "-b", LOOKUP_ROOT, "-k", KERNEL, "-F", "filename", name),
      _probe(LOOKUP_ROOT, name),
    ))
  result.extend(_probe(LOOKUP_ROOT, alias) for alias in ALIASES)
  result.extend(_probe(LOOKUP_ROOT, "symbol:" + symbol) for symbol in EXPORTS)
  _require(len(result) == 424, "E_COMMAND_PLAN")
  return tuple(result)


def _structural_identity(info: os.stat_result) -> tuple[int, ...]:
  return (info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_gid,
          info.st_nlink, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def _structural_read(
  path: Path,
  maximum: int,
  *,
  empty: bool = False,
) -> tuple[bytes, dict[str, str | int], tuple[int, ...]]:
  _require(path.is_absolute() and type(maximum) is int and 0 < maximum <= 64 * 1024 * 1024,
           "E_CONTROL_INCOMPLETE")
  try:
    for parent in path.parents:
      _require(stat.S_ISDIR(parent.lstat().st_mode), "E_CONTROL_INCOMPLETE")
    before = path.lstat()
    _require(stat.S_ISREG(before.st_mode) and stat.S_IMODE(before.st_mode) == 0o600
             and before.st_uid == before.st_gid == 1001 and before.st_nlink == 1
             and 0 <= before.st_size <= maximum and (empty or before.st_size > 0),
             "E_CONTROL_INCOMPLETE")
    descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
      expected = _structural_identity(before)
      _require(_structural_identity(os.fstat(descriptor)) == expected,
               "E_CONTROL_INCOMPLETE")
      chunks: list[bytes] = []
      remaining = before.st_size
      while remaining:
        raw = os.read(descriptor, min(remaining, 1024 * 1024))
        _require(bool(raw), "E_CONTROL_INCOMPLETE")
        chunks.append(raw)
        remaining -= len(raw)
      _require(not os.read(descriptor, 1)
               and _structural_identity(os.fstat(descriptor)) == expected
               and _structural_identity(path.lstat()) == expected,
               "E_CONTROL_INCOMPLETE")
    finally:
      os.close(descriptor)
  except (OSError, ValueError, TypeError):
    raise RecipeError("E_CONTROL_INCOMPLETE") from None
  payload = b"".join(chunks)
  return payload, {
    "path": str(path), "bytes": len(payload), "sha256": _sha256(payload),
    "mode": stat.S_IMODE(before.st_mode), "uid": before.st_uid, "gid": before.st_gid,
    "nlink": before.st_nlink,
  }, expected


def _structural_json(raw: bytes) -> object:
  def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for name, item in pairs:
      if type(name) is not str or name in value:
        raise ValueError("duplicate or invalid JSON key")
      value[name] = item
    return value

  def reject_constant(_: str) -> NoReturn:
    raise ValueError("non-finite JSON number")

  try:
    value = json.loads(raw.decode("ascii"), object_pairs_hook=unique_object,
                       parse_constant=reject_constant)
    compact = (json.dumps(value, sort_keys=True, separators=(",", ":"),
                          allow_nan=False) + "\n").encode("ascii")
  except (UnicodeError, ValueError, TypeError, RecursionError):
    raise RecipeError("E_CONTROL_INCOMPLETE") from None
  _require(raw == compact, "E_CONTROL_INCOMPLETE")
  return value


def _structural_record(value: object, expected: dict[str, str | int]) -> None:
  _require(type(value) is dict and set(value) == set(expected), "E_CONTROL_INCOMPLETE")
  for name, required in expected.items():
    actual = value[name]
    _require(type(actual) is type(required) and actual == required, "E_CONTROL_INCOMPLETE")


def _structural_commands() -> tuple[tuple[str, ...], ...]:
  base, _, _ = _structural_read(Path("/inputs/base"), E_BYTES)
  selected = select_e(base)
  names = {module.name: str(module.relative) for module in selected.modules}
  return command_plan(names)


def structural_policy() -> StructuralPolicy:
  """Return the exact zero-child structural policy; launch nothing."""
  return StructuralPolicy(
    STRUCTURAL_BINDINGS, _structural_commands(), STRUCTURAL_RECORD_ROOT,
    STRUCTURAL_ARTIFACTS,
  )


def operational_policy() -> NoReturn:
  """Reserve the real executed-control policy for the later semantic workload."""
  raise RecipeError("E_CONTROL_RECIPE_UNAVAILABLE")


def finalize_operational_result() -> NoReturn:
  """Reserve the real PASS result and fresh provenance for an executed control."""
  raise RecipeError("E_CONTROL_RECIPE_UNAVAILABLE")


def finalize_structural_result() -> StructuralAcceptance:
  """Validate a zero-child fixture graph and write its distinct result last."""
  header_path, evidence_path, result_path = map(Path, STRUCTURAL_ARTIFACTS)
  record_root = Path(STRUCTURAL_RECORD_ROOT)
  real_paths = tuple(map(Path, REAL_OPERATIONAL_ARTIFACTS))
  try:
    _require(not any(path.exists() or path.is_symlink()
                     for path in (result_path, *real_paths)), "E_CONTROL_INCOMPLETE")
    commands = _structural_commands()
    _require(len(commands) == 424, "E_CONTROL_INCOMPLETE")

    header_raw, header_record, header_identity = _structural_read(
      header_path, 2 * 1024 * 1024,
    )
    header = {
      "schema": 1, "kind": "dev147-e-control-structural-header-v1",
      "status": "STRUCTURAL_ONLY",
      "base_sha256": E_SHA256, "base_bytes": E_BYTES,
      "early_records": 7, "early_bytes": EARLY_BYTES, "early_sha256": EARLY_SHA256,
      "main_records": 1163, "main_bytes": MAIN_BYTES, "main_sha256": MAIN_SHA256,
      "module_count": 200, "expected_no_change_archive": True,
      "expected_gzip_exact": True, "expected_binary_only_lookup": True,
      "module_loaded": False, "image_staged": False,
      "indexes": INDEX_SHA256, "planned_children": 424, "structural_records": 424,
      "children_executed": 0, "fresh_control_proved": False,
    }
    _structural_json(header_raw)
    expected_header = (json.dumps(header, sort_keys=True, separators=(",", ":"),
                                  allow_nan=False) + "\n").encode("ascii")
    _require(header_raw == expected_header, "E_CONTROL_INCOMPLETE")

    evidence_raw, evidence_record, evidence_identity = _structural_read(
      evidence_path, 16 * 1024 * 1024,
    )
    evidence = _structural_json(evidence_raw)
    evidence_keys = {
      "schema", "kind", "status", "bindings", "base_sha256", "base_bytes",
      "index_inputs", "planned_commands", "fixture_commands", "record_root",
      "structural_records", "record_files", "children_executed", "fresh_control_proved",
      "image_created", "module_loaded", "staged", "booted",
    }
    _require(type(evidence) is dict and set(evidence) == evidence_keys,
             "E_CONTROL_INCOMPLETE")
    expected_commands = [list(command) for command in commands]
    fixed_evidence: dict[str, object] = {
      "schema": 1, "kind": "dev147-e-control-structural-evidence-v1",
      "status": "STRUCTURAL_ONLY", "bindings": list(STRUCTURAL_BINDINGS),
      "base_sha256": E_SHA256,
      "base_bytes": E_BYTES, "index_inputs": INDEX_INPUT_SHA256,
      "planned_commands": expected_commands, "fixture_commands": expected_commands,
      "record_root": STRUCTURAL_RECORD_ROOT, "structural_records": 424,
      "children_executed": 0, "fresh_control_proved": False,
      "image_created": False, "module_loaded": False,
      "staged": False, "booted": False,
    }
    for name, required in fixed_evidence.items():
      actual = evidence[name]
      _require(type(actual) is type(required) and actual == required,
               "E_CONTROL_INCOMPLETE")

    root_info = record_root.lstat()
    _require(stat.S_ISDIR(root_info.st_mode) and stat.S_IMODE(root_info.st_mode) == 0o700
             and root_info.st_uid == root_info.st_gid == 1001 and root_info.st_nlink == 2,
             "E_CONTROL_INCOMPLETE")
    root_identity = _structural_identity(root_info)
    expected_names = {
      f"record-{index:03d}.{suffix}"
      for index in range(424) for suffix in ("stdout", "stderr", "json")
    }
    _require({path.name for path in record_root.iterdir()} == expected_names,
             "E_CONTROL_INCOMPLETE")

    records = evidence["record_files"]
    _require(type(records) is list and len(records) == 424, "E_CONTROL_INCOMPLETE")
    leaf_identities: dict[Path, tuple[int, ...]] = {}
    for index, (command, record) in enumerate(zip(commands, records, strict=True)):
      _require(type(record) is dict and set(record) == {
        "index", "command", "stdout", "stderr", "record",
      } and type(record["index"]) is int and record["index"] == index
        and type(record["command"]) is list and record["command"] == list(command),
        "E_CONTROL_INCOMPLETE")
      paths = tuple(record_root / f"record-{index:03d}.{suffix}"
                    for suffix in ("stdout", "stderr", "json"))
      stdout, stdout_record, stdout_identity = _structural_read(
        paths[0], STDOUT_BYTES, empty=True,
      )
      stderr, stderr_record, stderr_identity = _structural_read(
        paths[1], STDERR_BYTES, empty=True,
      )
      report_raw, report_record, report_identity = _structural_read(paths[2], REPORT_BYTES)
      leaf_identities.update(zip(paths, (stdout_identity, stderr_identity, report_identity), strict=True))
      _structural_record(record["stdout"], stdout_record)
      _structural_record(record["stderr"], stderr_record)
      _structural_record(record["record"], report_record)

      report = _structural_json(report_raw)
      _require(type(report) is dict and set(report) == {
        "schema", "kind", "command", "status", "returncode", "stdout", "stderr",
        "retained_bytes", "observed_bytes", "planned_stdin_sha256",
        "planned_stdin_bytes", "executed", "elapsed_seconds", "pid", "killed", "reaped",
      }, "E_CONTROL_INCOMPLETE")
      _require(type(report["schema"]) is int and report["schema"] == 1
               and type(report["kind"]) is str
               and report["kind"] == "dev147-e-control-structural-record-v1"
               and type(report["command"]) is list and report["command"] == list(command)
               and type(report["status"]) is str and report["status"] == "STRUCTURAL_ONLY"
               and report["returncode"] is None
               and type(report["stdout"]) is str and report["stdout"] == paths[0].name
               and type(report["stderr"]) is str and report["stderr"] == paths[1].name
               and type(report["retained_bytes"]) is list
               and len(report["retained_bytes"]) == 2
               and all(type(value) is int and value >= 0 for value in report["retained_bytes"])
               and report["retained_bytes"] == [len(stdout), len(stderr)]
               and len(stdout) <= STDOUT_BYTES and len(stderr) <= STDERR_BYTES
               and type(report["observed_bytes"]) is list
               and len(report["observed_bytes"]) == 2
               and all(type(value) is int and value >= 0 for value in report["observed_bytes"])
               and report["observed_bytes"] == report["retained_bytes"]
               and len(stderr) == 0
               and type(report["executed"]) is bool and report["executed"] is False
               and type(report["elapsed_seconds"]) is float and report["elapsed_seconds"] == 0.0
               and report["pid"] is None
               and type(report["killed"]) is bool and report["killed"] is False
               and type(report["reaped"]) is bool and report["reaped"] is False,
               "E_CONTROL_INCOMPLETE")
      if command == ("/usr/bin/gzip",):
        _require(report["planned_stdin_sha256"] == MAIN_SHA256
                 and type(report["planned_stdin_sha256"]) is str
                 and type(report["planned_stdin_bytes"]) is int
                 and report["planned_stdin_bytes"] == MAIN_BYTES,
                 "E_CONTROL_INCOMPLETE")
      else:
        _require(report["planned_stdin_sha256"] is None
                 and type(report["planned_stdin_bytes"]) is int
                 and report["planned_stdin_bytes"] == 0,
                 "E_CONTROL_INCOMPLETE")

    result = {
      "schema": 1, "kind": "dev147-e-control-structural-result-v1",
      "status": "STRUCTURAL_PASS", "bindings": list(STRUCTURAL_BINDINGS),
      "planned_children": 424, "structural_records": 424, "children_executed": 0,
      "record_files": 1272, "record_root": STRUCTURAL_RECORD_ROOT,
      "header": header_record, "evidence": evidence_record,
      "structural_validated": True, "fresh_control_proved": False,
      "image_created": False, "module_loaded": False, "staged": False, "booted": False,
    }
    result_raw = (json.dumps(result, sort_keys=True, separators=(",", ":"),
                             allow_nan=False) + "\n").encode("ascii")
    acceptance = StructuralAcceptance(
      424, 0, _sha256(header_raw), _sha256(evidence_raw), _sha256(result_raw),
      "STRUCTURAL_PASS", True, False, False, False, False, False,
    )

    header_after, _, header_identity_after = _structural_read(header_path, 2 * 1024 * 1024)
    evidence_after, _, evidence_identity_after = _structural_read(
      evidence_path, 16 * 1024 * 1024,
    )
    _require(header_after == header_raw and header_identity_after == header_identity
             and evidence_after == evidence_raw and evidence_identity_after == evidence_identity,
             "E_CONTROL_INCOMPLETE")
    _require(_structural_identity(record_root.lstat()) == root_identity
             and {path.name for path in record_root.iterdir()} == expected_names
             and len(leaf_identities) == 1272
             and all(_structural_identity(path.lstat()) == identity
                     for path, identity in leaf_identities.items())
             and not any(path.exists() or path.is_symlink()
                         for path in (result_path, *real_paths)),
             "E_CONTROL_INCOMPLETE")
  except RecipeError:
    raise
  except (OSError, RuntimeError, ValueError, KeyError, TypeError, OverflowError):
    raise RecipeError("E_CONTROL_INCOMPLETE") from None

  write_new(result_path, result_raw)
  return acceptance


def main() -> NoReturn:
  """Neither a fixture nor a header can unlock an operational workload."""
  raise RecipeError("E_CONTROL_RECIPE_UNAVAILABLE")


if __name__ == "__main__":
  main()
