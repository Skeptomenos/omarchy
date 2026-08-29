"""Fixed E-only no-change control for the reviewed offline sandbox.

The module authenticates its five-source dependency chain. The public policy
functions remain read-only. Only ``main`` can materialize the fixed roots,
execute the 424-command plan, validate the fresh evidence, and publish the
no-change result. This recipe cannot build, load, stage, or boot an image.
"""

from dataclasses import dataclass
import ctypes
import errno
from fnmatch import fnmatchcase
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
from typing import NoReturn


class RecipeError(RuntimeError):
  """A fixed E-control boundary failed; it is not a hardware verdict."""


def _require(condition: bool, code: str) -> None:
  if not condition:
    raise RecipeError(code)


FIXED_SOURCE_BYTES = 128 * 1024
FIXED_SOURCE_INPUTS = (
  ("cpio_image", "/inputs/helper/cpio_image.py", "a32eddd159263d19ff87d7e9caee9d53d17ef5c350fbffe9e7eb142cb43ebf58"),
  ("verify_control", "/inputs/control/verify_control.py", "10b5afe6cff38df7b6ebe5619fd9a34935932a4b369f3a9ad2a51923c32932d8"),
  ("prepare_image", "/inputs/assembly/prepare_image.py", "00caceb3b7fa236dcc030fb4007d0baa75bfa08fcd1590626f85fcc8c22d5f60"),
  ("t1_image_contract", "/inputs/contract/image_contract.py", "a1eda280aa56967aa06b01a2cca0dfc70c3da6df25066f8a1e815beec719f1bf"),
  ("e_control", "/inputs/subject/e_control.py", "686d59e63166df1bef1afad27998a6d58f4c28b6b4439b6ccd607b56471268ca"),
)

def _fixed_source_identity(info: os.stat_result) -> tuple[int, ...]:
  return (
    info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_gid,
    info.st_nlink, info.st_size, info.st_mtime_ns, info.st_ctime_ns,
  )

def _load_fixed_source(name: str, path: str, digest: str) -> object:
  source = Path(path)
  _require(name not in os.sys.modules, "E_CONTROL_SOURCE_INVALID")
  before = source.lstat()
  _require(stat.S_ISREG(before.st_mode), "E_CONTROL_SOURCE_INVALID")
  _require(stat.S_IMODE(before.st_mode) == 0o600, "E_CONTROL_SOURCE_INVALID")
  _require(before.st_uid == before.st_gid == 1001, "E_CONTROL_SOURCE_INVALID")
  _require(before.st_nlink == 1, "E_CONTROL_SOURCE_INVALID")
  _require(0 < before.st_size <= FIXED_SOURCE_BYTES, "E_CONTROL_SOURCE_INVALID")
  descriptor = os.open(
    source, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC,
  )
  with os.fdopen(descriptor, "rb") as stream:
    _require(
      _fixed_source_identity(before) == _fixed_source_identity(os.fstat(descriptor)),
      "E_CONTROL_SOURCE_INVALID",
    )
    raw = stream.read(FIXED_SOURCE_BYTES + 1)
    _require(
      _fixed_source_identity(before) == _fixed_source_identity(os.fstat(descriptor))
      == _fixed_source_identity(source.lstat()),
      "E_CONTROL_SOURCE_INVALID",
    )
  _require(len(raw) == before.st_size <= FIXED_SOURCE_BYTES, "E_CONTROL_SOURCE_INVALID")
  _require(hashlib.sha256(raw).hexdigest() == digest, "E_CONTROL_SOURCE_INVALID")
  module = type(os)(name)
  module.__file__ = str(source)
  os.sys.modules[name] = module
  exec(compile(raw, str(source), "exec"), module.__dict__)
  return module

def _bootstrap_fixed_sources() -> None:
  saved_path = tuple(os.sys.path)
  saved_modules = dict(os.sys.modules)
  try:
    try:
      assembly = _load_fixed_source(*FIXED_SOURCE_INPUTS[2])
      _require(
        assembly.__file__ == FIXED_SOURCE_INPUTS[2][1]
        and os.sys.modules["verify_control"].__file__ == FIXED_SOURCE_INPUTS[1][1]
        and os.sys.modules["cpio_image"].__file__ == FIXED_SOURCE_INPUTS[0][1],
        "E_CONTROL_SOURCE_INVALID",
      )
      _load_fixed_source(*FIXED_SOURCE_INPUTS[3])
      _load_fixed_source(*FIXED_SOURCE_INPUTS[4])
    except Exception:
      os.sys.modules.clear()
      os.sys.modules.update(saved_modules)
      raise
  finally:
    os.sys.path[:] = saved_path

_bootstrap_fixed_sources()

from cpio_image import Archive, parse_newc, read_regular, write_new
from prepare_image import (
  ALIASES_HEADER, SYMBOLS_HEADER, WEAKDEP_HEADER, alias_entries,
  dependency_entries, single_gzip, validate_binary_dump,
)
from verify_control import (
  FileState, Module, TreeState, module_name, regular_member, select_indexes, snapshot,
)
from e_control import Commands, ControlError, build_root, ordered_lookup


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
PAYLOAD_BYTES = {
  PREFIX + "kernel/drivers/usb/typec/tipd/tps6598x-core.ko": 1213760,
  PREFIX + "kernel/drivers/usb/typec/tipd/tps6598x.ko": 12368,
  PREFIX + "kernel/drivers/phy/apple/phy-apple-atc.ko": 66512,
  PREFIX + "kernel/drivers/usb/dwc3/dwc3-apple.ko": 20312,
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
HISTORICAL_BYTES = {
  "modules.alias.bin": 73869,
  "modules.builtin.alias.bin": 37491,
  "modules.builtin.bin": 12558,
  "modules.dep.bin": 18359,
  "modules.devname": 0,
  "modules.softdep": 76,
  "modules.symbols.bin": 31021,
  "modules.alias": 70982,
  "modules.dep": 10998,
  "modules.symbols": 26189,
  "modules.weakdep": 55,
}
DUMP_SHA256 = "c562726938a6e3d11d5b3661352508f00b74efd9cbadbb559c3680663da72c05"
DUMP_BYTES = 97151
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
  "/work/e-control-result.pending",
)
STDOUT_BYTES = 64 * 1024 * 1024
STDERR_BYTES = 65536
REPORT_BYTES = 128 * 1024
SEMANTIC_RECORDS = 424
SEMANTIC_FIXTURE_PATHS = (
  "/work/e-control-semantic-fixture-records-s1",
  "/work/e-control-semantic-fixture-control-root-s1",
  "/work/e-control-semantic-fixture-lookup-root-s1",
  "/work/e-control-semantic-fixture-empty-modprobe.conf",
  "/work/e-control-semantic-fixture-early.cpio",
  "/work/e-control-semantic-fixture-main.cpio",
)
SEMANTIC_OPERATIONAL_PATHS = (
  "/work/e-control-children-e1",
  "/work/control-root",
  "/work/lookup-root",
  "/work/empty-modprobe.conf",
  "/work/e-early.cpio",
  "/work/e-main.cpio",
)
SEMANTIC_FIXTURE_PENDING = Path("/work/e-control-semantic-fixture-pending.json")
SEMANTIC_FIXTURE_RESULT = Path("/work/e-control-semantic-fixture-result.json")
SEMANTIC_FIXTURE_WORK_MEMBERS = frozenset((
  "descriptor-sentinel",
  "e-control-semantic-fixture-control-root-s1",
  "e-control-semantic-fixture-early.cpio",
  "e-control-semantic-fixture-empty-modprobe.conf",
  "e-control-semantic-fixture-lookup-root-s1",
  "e-control-semantic-fixture-main.cpio",
  "e-control-semantic-fixture-records-s1",
  "e-control-semantic-red",
  "probe-write",
  "stderr.log",
  "stdout.log",
))
ARCHIVE_OBSERVATIONS = {
  "early-cpio": (47, "62d818f030037bc3bbfc080899def7a67770961cc81d821ab750dcd06ea974cd"),
  "early-bsdtar": (47, "62d818f030037bc3bbfc080899def7a67770961cc81d821ab750dcd06ea974cd"),
  "main-cpio": (42863, "90e515cd5008382d737295497faf85f8fe530a19eca8bad4097cf0eb78e36633"),
  "main-bsdtar": (42863, "90e515cd5008382d737295497faf85f8fe530a19eca8bad4097cf0eb78e36633"),
  "gzip": (19181273, "375aa35be0ea57fa8d3f79f20cfa70373742ba6e2afda409462497d0d96ad724"),
}
SEMANTIC_REPORT_KEYS = frozenset((
  "schema", "kind", "index", "command", "operational_command", "status",
  "returncode", "stdout", "stderr", "report", "retained_bytes",
  "observed_bytes", "stdin_sha256", "stdin_bytes", "executed",
  "elapsed_seconds", "pid", "killed", "reaped",
))
SEMANTIC_FILE_KEYS = frozenset((
  "path", "raw", "bytes", "sha256", "identity", "mode", "uid", "gid", "nlink",
))
SEMANTIC_DIRECTORY_KEYS = frozenset((
  "kind", "path", "identity", "mode", "uid", "gid",
))
SEMANTIC_TREE_FILE_KEYS = frozenset((
  "kind", "path", "identity", "mode", "uid", "gid", "nlink", "bytes", "sha256",
))
RENAME_NOREPLACE = 1
_AT_FDCWD = -100


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


@dataclass(frozen=True)
class RawControlFiles:
  paths: tuple[str, ...]
  record_state: TreeState
  records: tuple[tuple[bytes, bytes, bytes], ...]
  control_state: TreeState
  lookup_state: TreeState
  empty_config_raw: bytes
  early_raw: bytes
  main_raw: bytes


@dataclass(frozen=True)
class MappedControlOutputs:
  raw_files: RawControlFiles


@dataclass(frozen=True)
class SemanticFixtureEvaluation:
  status: str
  semantic_validated: bool
  aggregate_sha256: str
  planned_children: int
  children_executed: int
  historical_generated_files: int
  structural_control_proved: bool
  operational_control_proved: bool
  fresh_control_proved: bool
  image_created: bool
  module_loaded: bool
  staged: bool
  booted: bool


@dataclass(frozen=True)
class SemanticFixtureAcceptance:
  status: str
  semantic_validated: bool
  aggregate_sha256: str
  result_sha256: str
  pending_path: str
  result_path: str
  planned_children: int
  children_executed: int
  structural_control_proved: bool
  operational_control_proved: bool
  fresh_control_proved: bool
  image_created: bool
  module_loaded: bool
  staged: bool
  booted: bool


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
  result.append(("/usr/bin/gzip", "-n"))
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


def _collect_fixed_raw_files(paths: tuple[str, ...]) -> RawControlFiles:
  record_root, control_root, lookup_root, empty_config, early_path, main_path = paths
  record_state = snapshot(Path(record_root))
  records = tuple((
    read_regular(Path(record_root) / f"record-{index:03d}.stdout"),
    read_regular(Path(record_root) / f"record-{index:03d}.stderr"),
    read_regular(Path(record_root) / f"record-{index:03d}.json"),
  ) for index in range(SEMANTIC_RECORDS))
  control_state = snapshot(Path(control_root))
  lookup_state = snapshot(Path(lookup_root))
  empty_config_raw = read_regular(Path(empty_config))
  early_raw = read_regular(Path(early_path))
  main_raw = read_regular(Path(main_path))
  return RawControlFiles(
    paths=paths,
    record_state=record_state,
    records=records,
    control_state=control_state,
    lookup_state=lookup_state,
    empty_config_raw=empty_config_raw,
    early_raw=early_raw,
    main_raw=main_raw,
  )


def _map_raw_control_outputs(raw_files: RawControlFiles) -> MappedControlOutputs:
  return MappedControlOutputs(raw_files=raw_files)


def _read_fixed_semantic_fixture_outputs() -> MappedControlOutputs:
  return _map_raw_control_outputs(_collect_fixed_raw_files(SEMANTIC_FIXTURE_PATHS))


def _read_fixed_operational_outputs() -> MappedControlOutputs:
  return _map_raw_control_outputs(_collect_fixed_raw_files(SEMANTIC_OPERATIONAL_PATHS))


def _semantic_json(raw: bytes) -> object:
  try:
    value = json.loads(raw.decode("ascii"))
    canonical = (json.dumps(value, sort_keys=True, separators=(",", ":"),
                            allow_nan=False) + "\n").encode("ascii")
  except (UnicodeError, ValueError, TypeError, RecursionError):
    raise RecipeError("E_CONTROL_SEMANTIC_INVALID") from None
  _require(raw == canonical, "E_CONTROL_SEMANTIC_INVALID")
  return value


def _semantic_json_bytes(value: object) -> bytes:
  try:
    raw = (json.dumps(value, sort_keys=True, separators=(",", ":"),
                      allow_nan=False) + "\n").encode("ascii")
  except (UnicodeError, ValueError, TypeError, RecursionError):
    raise RecipeError("E_CONTROL_SEMANTIC_INVALID") from None
  return raw


def _semantic_module_names(main_raw: bytes) -> dict[str, str]:
  _require(type(main_raw) is bytes and len(main_raw) == MAIN_BYTES
           and _sha256(main_raw) == MAIN_SHA256, "E_CONTROL_SEMANTIC_INVALID")
  try:
    archive = parse_newc(main_raw)
  except (RuntimeError, ValueError, KeyError, TypeError):
    raise RecipeError("E_CONTROL_SEMANTIC_INVALID") from None
  names: dict[str, str] = {}
  for member in archive.members:
    filename = Path(member.name).name
    if re.search(r"\.ko(?:\.|$)", filename) is None:
      continue
    _require(member.name.startswith(PREFIX + "kernel/") and member.name.endswith(".ko"),
             "E_CONTROL_SEMANTIC_INVALID")
    try:
      regular_member(member)
      name = module_name(filename)
    except (RuntimeError, ValueError, TypeError):
      raise RecipeError("E_CONTROL_SEMANTIC_INVALID") from None
    relative = member.name.removeprefix(PREFIX)
    _require(name not in names, "E_CONTROL_SEMANTIC_INVALID")
    names[name] = relative
  try:
    validated = _validated_names(names)
  except RecipeError:
    raise RecipeError("E_CONTROL_SEMANTIC_INVALID") from None
  return validated


def _semantic_generated_relative(name: str) -> str:
  return f"lib/modules/{KERNEL}/{name}"


def _semantic_control_before(raw_files: RawControlFiles) -> TreeState:
  generated = {_semantic_generated_relative(name) for name in GENERATED_SHA256}
  files = {
    relative: value for relative, value in raw_files.control_state.files.items()
    if relative not in generated
  }
  return TreeState(raw_files.control_state.directories.copy(), files)


def _semantic_dependencies() -> dict[str, tuple[str, ...]]:
  path = (Path(SEMANTIC_FIXTURE_PATHS[1]) / "lib/modules" / KERNEL / "modules.dep")
  raw = read_regular(path)
  _require(len(raw) == HISTORICAL_BYTES["modules.dep"]
           and _sha256(raw) == GENERATED_SHA256["modules.dep"],
           "E_CONTROL_SEMANTIC_INVALID")
  try:
    lines = raw.decode("ascii").splitlines()
  except UnicodeError:
    raise RecipeError("E_CONTROL_SEMANTIC_INVALID") from None
  dependencies: dict[str, tuple[str, ...]] = {}
  for line in lines:
    parts = line.split(":")
    _require(len(parts) == 2 and parts[0] not in dependencies
             and re.fullmatch(r"kernel/(?:[A-Za-z0-9_-]+/)*[A-Za-z0-9_][A-Za-z0-9_-]*\.ko",
                              parts[0]) is not None
             and (not parts[1] or parts[1].startswith(" ")),
             "E_CONTROL_SEMANTIC_INVALID")
    values = tuple(parts[1][1:].split(" ")) if parts[1] else ()
    _require(all(re.fullmatch(
      r"kernel/(?:[A-Za-z0-9_-]+/)*[A-Za-z0-9_][A-Za-z0-9_-]*\.ko", value,
    ) is not None for value in values), "E_CONTROL_SEMANTIC_INVALID")
    dependencies[parts[0]] = values
  _require(len(dependencies) == 200, "E_CONTROL_SEMANTIC_INVALID")
  return dependencies


def _semantic_expected_module(name: str) -> tuple[bytes, bytes]:
  dependencies = _semantic_dependencies()
  names = {module_name(Path(relative).name): relative for relative in dependencies}
  _require(len(names) == 200 and type(name) is str and name in names,
           "E_CONTROL_SEMANTIC_INVALID")
  relative = names[name]
  prefix = f"{SEMANTIC_FIXTURE_PATHS[2]}/lib/modules/{KERNEL}/"
  rows: list[bytes] = []
  if name == "lrw":
    rows.append(b"builtin ecb\n")
  for dependency in dependencies[relative][::-1]:
    rows.append(f"insmod {prefix}{dependency} \n".encode("ascii"))
  rows.append(f"insmod {prefix}{relative} \n".encode("ascii"))
  filename = f"{prefix}{relative}\n".encode("ascii")
  return filename, b"".join(rows)


def _semantic_lookup_target(query: str) -> str:
  name = "modules.symbols" if query.startswith("symbol:") else "modules.alias"
  path = Path(SEMANTIC_FIXTURE_PATHS[1]) / "lib/modules" / KERNEL / name
  raw = read_regular(path)
  _require(len(raw) == HISTORICAL_BYTES[name] and _sha256(raw) == GENERATED_SHA256[name],
           "E_CONTROL_SEMANTIC_INVALID")
  try:
    lines = raw.decode("ascii").splitlines()
  except UnicodeError:
    raise RecipeError("E_CONTROL_SEMANTIC_INVALID") from None
  _require(bool(lines) and lines[0].startswith("# "), "E_CONTROL_SEMANTIC_INVALID")
  matches: list[str] = []
  for line in lines[1:]:
    parts = line.split(" ")
    _require(len(parts) == 3 and parts[0] == "alias"
             and re.fullmatch(r"[A-Za-z0-9_]{1,128}", parts[2]) is not None,
             "E_CONTROL_SEMANTIC_INVALID")
    if fnmatchcase(query, parts[1]):
      matches.append(parts[2])
  _require(len(matches) == 1, "E_CONTROL_SEMANTIC_INVALID")
  return matches[0]


def _semantic_file_observation(path: Path, raw: bytes) -> dict[str, object]:
  before = path.lstat()
  actual = read_regular(path)
  after = path.lstat()
  identity = _structural_identity(before)
  _require(actual == raw and identity == _structural_identity(after),
           "E_CONTROL_SEMANTIC_INVALID")
  return {
    "path": str(path), "raw": raw, "bytes": len(raw), "sha256": _sha256(raw),
    "identity": list(identity), "mode": stat.S_IMODE(before.st_mode),
    "uid": before.st_uid, "gid": before.st_gid, "nlink": before.st_nlink,
  }


def _semantic_stable_file(observation: dict[str, object]) -> dict[str, object]:
  return {name: observation[name] for name in (
    "path", "bytes", "sha256", "mode", "uid", "gid", "nlink",
  )}


def _semantic_stable_tree(root: Path, state: TreeState) -> dict[str, object]:
  directories = {
    relative: {
      "mode": stat.S_IMODE(value[2]), "uid": value[3], "gid": value[4],
    }
    for relative, value in sorted(state.directories.items())
  }
  files = {
    relative: {
      "mode": stat.S_IMODE(value.identity[2]), "uid": value.identity[3],
      "gid": value.identity[4], "nlink": value.identity[5],
      "bytes": value.identity[6], "sha256": value.sha256,
    }
    for relative, value in sorted(state.files.items())
  }
  return {"root": str(root), "directories": directories, "files": files}


def _semantic_tree_identity_records(
  root: Path,
  state: TreeState,
) -> tuple[dict[str, object], ...]:
  records: list[dict[str, object]] = []
  for relative in sorted(state.directories):
    value = state.directories[relative]
    path = root / relative
    actual = _structural_identity(path.lstat())
    _require(actual[:5] == value, "E_CONTROL_SEMANTIC_INVALID")
    records.append({
      "kind": "directory", "path": str(path), "identity": list(actual),
      "mode": stat.S_IMODE(actual[2]), "uid": actual[3], "gid": actual[4],
    })
  for relative in sorted(state.files):
    value = state.files[relative]
    _require(isinstance(value, FileState), "E_CONTROL_SEMANTIC_INVALID")
    records.append({
      "kind": "file", "path": str(root / relative), "identity": list(value.identity),
      "mode": stat.S_IMODE(value.identity[2]), "uid": value.identity[3],
      "gid": value.identity[4], "nlink": value.identity[5],
      "bytes": value.identity[6], "sha256": value.sha256,
    })
  return tuple(records)


def _semantic_expected_provenance() -> dict[str, object]:
  return {
    "kind": "dev147-e-control-semantic-historical-fixture-provenance-v2",
    "status": "FIXTURE_ONLY",
    "historical_generated_files": 12,
    "bindings": [
      "/inputs/g-alias-text", "/inputs/g-alias-bin", "/inputs/g-builtin-alias-bin",
      "/inputs/g-builtin-bin", "/inputs/g-dep-text", "/inputs/g-dep-bin",
      "/inputs/g-devname", "/inputs/g-softdep", "/inputs/g-symbols-text",
      "/inputs/g-symbols-bin", "/inputs/g-weakdep", "/inputs/g-dump",
    ],
    "planned_children": 424,
    "children_executed": 0,
    "all_records_executed": False,
    "fresh_control_proved": False,
    "structural_control_proved": False,
    "operational_control_proved": False,
    "image_created": False,
    "module_loaded": False,
    "staged": False,
    "booted": False,
  }


def _semantic_provenance(raw_files: RawControlFiles) -> dict[str, object]:
  _require(len(raw_files.records) == SEMANTIC_RECORDS, "E_CONTROL_SEMANTIC_INVALID")
  return _semantic_expected_provenance()


def _semantic_command_plan(
  paths: tuple[str, ...],
  names: dict[str, str],
) -> tuple[tuple[str, ...], ...]:
  _record_root, control_root, lookup_root, empty_config, early_path, main_path = paths
  result: list[tuple[str, ...]] = []
  for path in (early_path, main_path):
    result.extend((
      ("/usr/bin/cpio", "--list", "--quiet", "--file", path),
      ("/usr/bin/bsdtar", "--list", "--file", path),
    ))
  result.append(("/usr/bin/gzip", "-n"))
  for path in PAYLOAD_SHA256:
    result.append((
      "/usr/bin/bsdtar", "--extract", "--to-stdout", "--file", main_path, path,
    ))
  result.append(("/usr/bin/depmod", "-b", control_root, KERNEL))
  result.extend((
    ("/usr/bin/modprobe", "--dry-run", "--show-depends", "-d", control_root,
     "-S", KERNEL, "-C", empty_config, "--show-config"),
    ("/usr/bin/modprobe", "--dry-run", "--show-depends", "-d", lookup_root,
     "-S", KERNEL, "-C", empty_config, "--show-config"),
  ))
  for name in sorted(names):
    result.extend((
      ("/usr/bin/modinfo", "-b", lookup_root, "-k", KERNEL, "-F", "filename", name),
      ("/usr/bin/modprobe", "--dry-run", "--show-depends", "-d", lookup_root,
       "-S", KERNEL, "-C", empty_config, name),
    ))
  for alias in ALIASES:
    result.append((
      "/usr/bin/modprobe", "--dry-run", "--show-depends", "-d", lookup_root,
      "-S", KERNEL, "-C", empty_config, alias,
    ))
  for symbol in EXPORTS:
    result.append((
      "/usr/bin/modprobe", "--dry-run", "--show-depends", "-d", lookup_root,
      "-S", KERNEL, "-C", empty_config, "symbol:" + symbol,
    ))
  _require(len(result) == SEMANTIC_RECORDS, "E_CONTROL_SEMANTIC_INVALID")
  return tuple(result)


def _semantic_command_observation(
  raw_files: RawControlFiles,
  index: int,
) -> dict[str, object]:
  stdout, stderr, report_raw = raw_files.records[index]
  report = _semantic_json(report_raw)
  _require(type(report) is dict, "E_CONTROL_SEMANTIC_INVALID")
  root = Path(raw_files.paths[0])
  stdout_path = root / f"record-{index:03d}.stdout"
  stderr_path = root / f"record-{index:03d}.stderr"
  report_path = root / f"record-{index:03d}.json"
  return {
    "report": report,
    "report_raw": report_raw,
    "stdout_file": _semantic_file_observation(stdout_path, stdout),
    "stderr_file": _semantic_file_observation(stderr_path, stderr),
    "report_file": _semantic_file_observation(report_path, report_raw),
  }


def _semantic_identity_records(raw_files: RawControlFiles) -> tuple[dict[str, object], ...]:
  records: list[dict[str, object]] = []
  for index in range(SEMANTIC_RECORDS):
    observation = _semantic_command_observation(raw_files, index)
    for name in ("stdout_file", "stderr_file", "report_file"):
      value = observation[name]
      _require(type(value) is dict, "E_CONTROL_SEMANTIC_INVALID")
      records.append(value)
  control_before = _semantic_control_before(raw_files)
  for root, state in (
    (Path(raw_files.paths[1]), control_before),
    (Path(raw_files.paths[1]), raw_files.control_state),
    (Path(raw_files.paths[2]), raw_files.lookup_state),
    (Path(raw_files.paths[2]), raw_files.lookup_state),
  ):
    records.extend(_semantic_tree_identity_records(root, state))
  records.extend((
    _semantic_file_observation(Path(raw_files.paths[4]), raw_files.early_raw),
    _semantic_file_observation(Path(raw_files.paths[5]), raw_files.main_raw),
    _semantic_file_observation(Path(raw_files.paths[3]), raw_files.empty_config_raw),
  ))
  _require(len(records) == 2298, "E_CONTROL_SEMANTIC_INVALID")
  return tuple(records)


def _semantic_bound_observation(
  raw_files: RawControlFiles,
  observation: object,
) -> object:
  _require(len(raw_files.records) == SEMANTIC_RECORDS, "E_CONTROL_SEMANTIC_INVALID")
  return observation


def _semantic_archive_records(raw: bytes) -> list[dict[str, object]]:
  try:
    archive = parse_newc(raw)
  except (RuntimeError, ValueError, KeyError, TypeError):
    raise RecipeError("E_CONTROL_SEMANTIC_INVALID") from None
  records: list[dict[str, object]] = []
  for index, member in enumerate(archive.members):
    records.append({
      "index": index,
      "name": member.name,
      "raw_bytes": len(member.raw),
      "raw_sha256": _sha256(member.raw),
      "raw_name_sha256": _sha256(member.raw_name),
      "payload_bytes": len(member.payload),
      "payload_sha256": _sha256(member.payload),
      "fields": list(member.fields),
    })
  return records


def _semantic_aggregate(raw_files: RawControlFiles) -> dict[str, object]:
  control_before = _semantic_control_before(raw_files)
  commands: list[dict[str, object]] = []
  for index in range(SEMANTIC_RECORDS):
    observation = _semantic_command_observation(raw_files, index)
    report = observation["report"]
    stdout = observation["stdout_file"]
    stderr = observation["stderr_file"]
    report_file = observation["report_file"]
    _require(type(report) is dict and type(stdout) is dict and type(stderr) is dict
             and type(report_file) is dict, "E_CONTROL_SEMANTIC_INVALID")
    commands.append({
      "report": report,
      "stdout": _semantic_stable_file(stdout),
      "stderr": _semantic_stable_file(stderr),
      "report_file": _semantic_stable_file(report_file),
    })
  generated_indexes = {
    name: raw_files.control_state.files[_semantic_generated_relative(name)].sha256
    for name in sorted(GENERATED_SHA256)
  }
  retained_indexes = {
    name: raw_files.lookup_state.files[_semantic_generated_relative(name)].sha256
    for name in sorted(INDEX_SHA256)
  }
  dump = raw_files.records[10][0]
  result = {
    "schema": 2,
    "kind": "dev147-e-control-semantic-raw-fixture-v2",
    "status": "FIXTURE_ONLY",
    "base_sha256": E_SHA256,
    "base_bytes": E_BYTES,
    "early_records": _semantic_archive_records(raw_files.early_raw),
    "main_records": _semantic_archive_records(raw_files.main_raw),
    "commands": commands,
    "control_before": _semantic_stable_tree(Path(raw_files.paths[1]), control_before),
    "control_after": _semantic_stable_tree(
      Path(raw_files.paths[1]), raw_files.control_state,
    ),
    "lookup_before": _semantic_stable_tree(
      Path(raw_files.paths[2]), raw_files.lookup_state,
    ),
    "lookup_after": _semantic_stable_tree(
      Path(raw_files.paths[2]), raw_files.lookup_state,
    ),
    "generated_indexes": generated_indexes,
    "retained_indexes": retained_indexes,
    "historical_dump": {"bytes": len(dump), "sha256": _sha256(dump)},
    "provenance": _semantic_provenance(raw_files),
  }
  return result


def _validate_file_metadata(
  observation: object,
  expected_path: str,
  maximum: int,
) -> None:
  _require(type(observation) is dict and set(observation) == SEMANTIC_FILE_KEYS,
           "E_CONTROL_SEMANTIC_INVALID")
  path = observation["path"]
  raw = observation["raw"]
  size = observation["bytes"]
  digest = observation["sha256"]
  identity = observation["identity"]
  mode = observation["mode"]
  uid = observation["uid"]
  gid = observation["gid"]
  nlink = observation["nlink"]
  _require(type(path) is str and path == expected_path and Path(path).is_absolute()
           and type(raw) is bytes and type(size) is int and 0 <= size <= maximum
           and len(raw) == size and type(digest) is str and len(digest) == 64
           and type(identity) is list and len(identity) == 9
           and all(type(value) is int for value in identity)
           and type(mode) is int and type(uid) is int and type(gid) is int
           and type(nlink) is int and mode == identity[2] & 0o7777
           and uid == identity[3] and gid == identity[4] and nlink == identity[5]
           and mode == 0o600 and uid == gid == 1001 and nlink == 1,
           "E_CONTROL_SEMANTIC_INVALID")
  info = Path(path).lstat()
  _require(stat.S_ISREG(info.st_mode)
           and tuple(identity) == _structural_identity(info),
           "E_CONTROL_SEMANTIC_INVALID")


def _validate_file_content(observation: dict[str, object]) -> None:
  raw = observation["raw"]
  path = observation["path"]
  digest = observation["sha256"]
  _require(type(raw) is bytes and type(path) is str and type(digest) is str
           and _sha256(raw) == digest, "E_CONTROL_SEMANTIC_INVALID")
  actual = read_regular(Path(path))
  _require(actual == raw, "E_CONTROL_SEMANTIC_INVALID")


def _validate_command_shape(
  index: int,
  command: object,
  operational_command: object,
) -> None:
  _require(type(command) is list and type(operational_command) is list
           and all(type(value) is str for value in command)
           and all(type(value) is str for value in operational_command),
           "E_CONTROL_SEMANTIC_INVALID")
  if index == 0:
    _require(command == [
      "/usr/bin/cpio", "--list", "--quiet", "--file", SEMANTIC_FIXTURE_PATHS[4],
    ] and operational_command == [
      "/usr/bin/cpio", "--list", "--quiet", "--file", SEMANTIC_OPERATIONAL_PATHS[4],
    ], "E_CONTROL_SEMANTIC_INVALID")
  elif index == 1:
    _require(command == [
      "/usr/bin/bsdtar", "--list", "--file", SEMANTIC_FIXTURE_PATHS[4],
    ] and operational_command == [
      "/usr/bin/bsdtar", "--list", "--file", SEMANTIC_OPERATIONAL_PATHS[4],
    ], "E_CONTROL_SEMANTIC_INVALID")
  elif index == 2:
    _require(command == [
      "/usr/bin/cpio", "--list", "--quiet", "--file", SEMANTIC_FIXTURE_PATHS[5],
    ] and operational_command == [
      "/usr/bin/cpio", "--list", "--quiet", "--file", SEMANTIC_OPERATIONAL_PATHS[5],
    ], "E_CONTROL_SEMANTIC_INVALID")
  elif index == 3:
    _require(command == [
      "/usr/bin/bsdtar", "--list", "--file", SEMANTIC_FIXTURE_PATHS[5],
    ] and operational_command == [
      "/usr/bin/bsdtar", "--list", "--file", SEMANTIC_OPERATIONAL_PATHS[5],
    ], "E_CONTROL_SEMANTIC_INVALID")
  elif index == 4:
    _require(command == ["/usr/bin/gzip", "-n"] and
             operational_command == ["/usr/bin/gzip", "-n"],
             "E_CONTROL_SEMANTIC_INVALID")
  elif 5 <= index <= 8:
    payload = tuple(PAYLOAD_SHA256)[index - 5]
    _require(command == [
      "/usr/bin/bsdtar", "--extract", "--to-stdout", "--file",
      SEMANTIC_FIXTURE_PATHS[5], payload,
    ] and operational_command == [
      "/usr/bin/bsdtar", "--extract", "--to-stdout", "--file",
      SEMANTIC_OPERATIONAL_PATHS[5], payload,
    ], "E_CONTROL_SEMANTIC_INVALID")
  elif index == 9:
    _require(command == [
      "/usr/bin/depmod", "-b", SEMANTIC_FIXTURE_PATHS[1], KERNEL,
    ] and operational_command == [
      "/usr/bin/depmod", "-b", SEMANTIC_OPERATIONAL_PATHS[1], KERNEL,
    ], "E_CONTROL_SEMANTIC_INVALID")
  elif index in (10, 11):
    root_index = 1 if index == 10 else 2
    _require(command == [
      "/usr/bin/modprobe", "--dry-run", "--show-depends", "-d",
      SEMANTIC_FIXTURE_PATHS[root_index], "-S", KERNEL, "-C",
      SEMANTIC_FIXTURE_PATHS[3], "--show-config",
    ] and operational_command == [
      "/usr/bin/modprobe", "--dry-run", "--show-depends", "-d",
      SEMANTIC_OPERATIONAL_PATHS[root_index], "-S", KERNEL, "-C",
      SEMANTIC_OPERATIONAL_PATHS[3], "--show-config",
    ], "E_CONTROL_SEMANTIC_INVALID")
  elif 12 <= index <= 411 and index % 2 == 0:
    _require(len(command) == len(operational_command) == 8
             and command[:2] == operational_command[:2] == ["/usr/bin/modinfo", "-b"]
             and command[2] == SEMANTIC_FIXTURE_PATHS[2]
             and operational_command[2] == SEMANTIC_OPERATIONAL_PATHS[2]
             and command[3:7] == operational_command[3:7] == [
               "-k", KERNEL, "-F", "filename",
             ] and command[7] == operational_command[7]
             and re.fullmatch(r"[A-Za-z0-9_]{1,128}", command[7]) is not None,
             "E_CONTROL_SEMANTIC_INVALID")
  elif 12 <= index <= 411:
    _require(len(command) == len(operational_command) == 10
             and command[:4] == operational_command[:4] == [
               "/usr/bin/modprobe", "--dry-run", "--show-depends", "-d",
             ] and command[4] == SEMANTIC_FIXTURE_PATHS[2]
             and operational_command[4] == SEMANTIC_OPERATIONAL_PATHS[2]
             and command[5:8] == operational_command[5:8] == ["-S", KERNEL, "-C"]
             and command[8] == SEMANTIC_FIXTURE_PATHS[3]
             and operational_command[8] == SEMANTIC_OPERATIONAL_PATHS[3]
             and command[9] == operational_command[9]
             and re.fullmatch(r"[A-Za-z0-9_]{1,128}", command[9]) is not None,
             "E_CONTROL_SEMANTIC_INVALID")
  elif 412 <= index <= 414:
    alias = ALIASES[index - 412]
    _require(command == [
      "/usr/bin/modprobe", "--dry-run", "--show-depends", "-d",
      SEMANTIC_FIXTURE_PATHS[2], "-S", KERNEL, "-C", SEMANTIC_FIXTURE_PATHS[3], alias,
    ] and operational_command == [
      "/usr/bin/modprobe", "--dry-run", "--show-depends", "-d",
      SEMANTIC_OPERATIONAL_PATHS[2], "-S", KERNEL, "-C",
      SEMANTIC_OPERATIONAL_PATHS[3], alias,
    ], "E_CONTROL_SEMANTIC_INVALID")
  else:
    symbol = EXPORTS[index - 415]
    _require(415 <= index <= 423 and command == [
      "/usr/bin/modprobe", "--dry-run", "--show-depends", "-d",
      SEMANTIC_FIXTURE_PATHS[2], "-S", KERNEL, "-C", SEMANTIC_FIXTURE_PATHS[3],
      "symbol:" + symbol,
    ] and operational_command == [
      "/usr/bin/modprobe", "--dry-run", "--show-depends", "-d",
      SEMANTIC_OPERATIONAL_PATHS[2], "-S", KERNEL, "-C",
      SEMANTIC_OPERATIONAL_PATHS[3], "symbol:" + symbol,
    ], "E_CONTROL_SEMANTIC_INVALID")


def _validate_archive_observation(label: str, raw: bytes) -> None:
  _require(type(label) is str and label in ARCHIVE_OBSERVATIONS and type(raw) is bytes,
           "E_CONTROL_SEMANTIC_INVALID")
  expected = ARCHIVE_OBSERVATIONS[label]
  _require(len(raw) == expected[0] and _sha256(raw) == expected[1],
           "E_CONTROL_SEMANTIC_INVALID")


def _validate_payload_observation(name: str, raw: bytes) -> None:
  _require(type(name) is str and name in PAYLOAD_SHA256 and type(raw) is bytes
           and len(raw) == PAYLOAD_BYTES[name] and _sha256(raw) == PAYLOAD_SHA256[name],
           "E_CONTROL_SEMANTIC_INVALID")


def _validate_tree_observation(kind: str, before: TreeState, after: TreeState) -> None:
  _require(type(kind) is str and kind in ("control", "lookup")
           and isinstance(before, TreeState) and isinstance(after, TreeState),
           "E_CONTROL_SEMANTIC_INVALID")
  if kind == "control":
    expected = {_semantic_generated_relative(name) for name in GENERATED_SHA256}
    _require(len(before.directories) == len(after.directories) == 48
             and before.directories == after.directories
             and len(before.files) == 203 and len(after.files) == 214
             and set(after.files) == set(before.files) | expected
             and all(after.files.get(name) == value for name, value in before.files.items()),
             "E_CONTROL_SEMANTIC_INVALID")
  else:
    _require(before == after and len(before.directories) == 48
             and len(before.files) == 207, "E_CONTROL_SEMANTIC_INVALID")


def _validate_index_observation(
  kind: str,
  name: str,
  raw: bytes,
  observation: dict[str, object],
) -> None:
  _require(type(kind) is str and kind in ("generated", "retained")
           and type(name) is str and type(raw) is bytes,
           "E_CONTROL_SEMANTIC_INVALID")
  digests = GENERATED_SHA256 if kind == "generated" else INDEX_SHA256
  root = SEMANTIC_FIXTURE_PATHS[1] if kind == "generated" else SEMANTIC_FIXTURE_PATHS[2]
  _require(name in digests and name in HISTORICAL_BYTES
           and len(raw) == HISTORICAL_BYTES[name] and _sha256(raw) == digests[name],
           "E_CONTROL_SEMANTIC_INVALID")
  _validate_file_metadata(
    observation, f"{root}/lib/modules/{KERNEL}/{name}", MAX_INDEX_BYTES,
  )
  _require(observation["raw"] == raw, "E_CONTROL_SEMANTIC_INVALID")
  _validate_file_content(observation)


def _validate_module_observation(
  name: str,
  filename_raw: bytes,
  dependency_raw: bytes,
) -> None:
  _require(type(name) is str and type(filename_raw) is bytes and type(dependency_raw) is bytes,
           "E_CONTROL_SEMANTIC_INVALID")
  expected_filename, expected_dependency = _semantic_expected_module(name)
  _require(filename_raw == expected_filename and dependency_raw == expected_dependency,
           "E_CONTROL_SEMANTIC_INVALID")


def _validate_alias_observation(alias: str, raw: bytes) -> None:
  _require(type(alias) is str and alias in ALIASES and type(raw) is bytes,
           "E_CONTROL_SEMANTIC_INVALID")
  target = _semantic_lookup_target(alias)
  _expected_filename, expected = _semantic_expected_module(target)
  _require(raw == expected, "E_CONTROL_SEMANTIC_INVALID")


def _validate_symbol_observation(symbol: str, raw: bytes) -> None:
  _require(type(symbol) is str and symbol in EXPORTS and type(raw) is bytes,
           "E_CONTROL_SEMANTIC_INVALID")
  target = _semantic_lookup_target("symbol:" + symbol)
  _expected_filename, expected = _semantic_expected_module(target)
  _require(raw == expected, "E_CONTROL_SEMANTIC_INVALID")


def _validate_command_observation(index: int, observation: dict[str, object]) -> None:
  _require(type(index) is int and 0 <= index < SEMANTIC_RECORDS
           and type(observation) is dict and set(observation) == {
             "report", "report_raw", "stdout_file", "stderr_file", "report_file",
           }, "E_CONTROL_SEMANTIC_INVALID")
  report = observation["report"]
  report_raw = observation["report_raw"]
  stdout = observation["stdout_file"]
  stderr = observation["stderr_file"]
  report_file = observation["report_file"]
  _require(type(report) is dict and set(report) == SEMANTIC_REPORT_KEYS
           and type(report_raw) is bytes and type(stdout) is dict
           and type(stderr) is dict and type(report_file) is dict,
           "E_CONTROL_SEMANTIC_INVALID")
  retained = report["retained_bytes"]
  observed = report["observed_bytes"]
  _require(type(report["schema"]) is int and report["schema"] == 1
           and type(report["kind"]) is str
           and report["kind"] == "dev147-e-control-semantic-fixture-record-v2"
           and type(report["index"]) is int and report["index"] == index
           and type(report["status"]) is str and report["status"] == "FIXTURE_ONLY"
           and report["returncode"] is None
           and type(report["stdout"]) is str and type(report["stderr"]) is str
           and type(report["report"]) is str
           and type(retained) is list and len(retained) == 2
           and all(type(value) is int and value >= 0 for value in retained)
           and type(observed) is list and len(observed) == 2
           and all(type(value) is int and value >= 0 for value in observed)
           and observed == retained
           and type(report["stdin_bytes"]) is int
           and type(report["executed"]) is bool and report["executed"] is False
           and type(report["elapsed_seconds"]) is float and report["elapsed_seconds"] == 0.0
           and report["pid"] is None
           and type(report["killed"]) is bool and report["killed"] is False
           and type(report["reaped"]) is bool and report["reaped"] is False,
           "E_CONTROL_SEMANTIC_INVALID")
  _validate_command_shape(index, report["command"], report["operational_command"])
  root = SEMANTIC_FIXTURE_PATHS[0]
  stdout_path = f"{root}/record-{index:03d}.stdout"
  stderr_path = f"{root}/record-{index:03d}.stderr"
  report_path = f"{root}/record-{index:03d}.json"
  _require(report["stdout"] == stdout_path and report["stderr"] == stderr_path
           and report["report"] == report_path, "E_CONTROL_SEMANTIC_INVALID")
  if index == 4:
    _require(type(report["stdin_sha256"]) is str
             and report["stdin_sha256"] == MAIN_SHA256
             and report["stdin_bytes"] == MAIN_BYTES, "E_CONTROL_SEMANTIC_INVALID")
  else:
    _require(report["stdin_sha256"] is None and report["stdin_bytes"] == 0,
             "E_CONTROL_SEMANTIC_INVALID")
  _validate_file_metadata(stdout, stdout_path, STDOUT_BYTES)
  _validate_file_metadata(stderr, stderr_path, STDERR_BYTES)
  _validate_file_metadata(report_file, report_path, REPORT_BYTES)
  _require(retained == [stdout["bytes"], stderr["bytes"]]
           and stderr["bytes"] == 0 and stderr["raw"] == b""
           and report_file["bytes"] == len(report_raw)
           and report_file["raw"] == report_raw
           and report_raw == _semantic_json_bytes(report),
           "E_CONTROL_SEMANTIC_INVALID")
  _validate_file_content(stdout)
  _validate_file_content(stderr)
  _validate_file_content(report_file)


def _validate_identity_observation(observation: dict[str, object]) -> None:
  _require(type(observation) is dict, "E_CONTROL_SEMANTIC_INVALID")
  keys = set(observation)
  if keys == SEMANTIC_FILE_KEYS:
    path = observation["path"]
    _require(type(path) is str, "E_CONTROL_SEMANTIC_INVALID")
    _validate_file_metadata(observation, path, MAX_INDEX_BYTES)
    _validate_file_content(observation)
  elif keys == SEMANTIC_DIRECTORY_KEYS:
    path = observation["path"]
    identity = observation["identity"]
    _require(observation["kind"] == "directory" and type(path) is str
             and Path(path).is_absolute() and type(identity) is list and len(identity) == 9
             and all(type(value) is int for value in identity)
             and type(observation["mode"]) is int
             and observation["mode"] == identity[2] & 0o7777
             and type(observation["uid"]) is int and observation["uid"] == identity[3]
             and type(observation["gid"]) is int and observation["gid"] == identity[4]
             and observation["mode"] == 0o700
             and observation["uid"] == observation["gid"] == 1001,
             "E_CONTROL_SEMANTIC_INVALID")
    info = Path(path).lstat()
    _require(stat.S_ISDIR(info.st_mode)
             and tuple(identity) == _structural_identity(info),
             "E_CONTROL_SEMANTIC_INVALID")
  else:
    _require(keys == SEMANTIC_TREE_FILE_KEYS, "E_CONTROL_SEMANTIC_INVALID")
    path = observation["path"]
    identity = observation["identity"]
    _require(observation["kind"] == "file" and type(path) is str
             and Path(path).is_absolute() and type(identity) is list and len(identity) == 9
             and all(type(value) is int for value in identity)
             and type(observation["mode"]) is int
             and observation["mode"] == identity[2] & 0o7777
             and type(observation["uid"]) is int and observation["uid"] == identity[3]
             and type(observation["gid"]) is int and observation["gid"] == identity[4]
             and type(observation["nlink"]) is int and observation["nlink"] == identity[5]
             and type(observation["bytes"]) is int and observation["bytes"] == identity[6]
             and type(observation["sha256"]) is str and len(observation["sha256"]) == 64
             and observation["mode"] == 0o600
             and observation["uid"] == observation["gid"] == 1001
             and observation["nlink"] == 1,
             "E_CONTROL_SEMANTIC_INVALID")
    info = Path(path).lstat()
    _require(stat.S_ISREG(info.st_mode)
             and tuple(identity) == _structural_identity(info),
             "E_CONTROL_SEMANTIC_INVALID")
    raw = read_regular(Path(path))
    _require(len(raw) == observation["bytes"]
             and _sha256(raw) == observation["sha256"],
             "E_CONTROL_SEMANTIC_INVALID")


def _validate_provenance_observation(provenance: dict[str, object]) -> None:
  _require(type(provenance) is dict and provenance == _semantic_expected_provenance(),
           "E_CONTROL_SEMANTIC_INVALID")


def _validate_archive_family(mapped: MappedControlOutputs) -> None:
  cases = (
    ("early-cpio", 0), ("early-bsdtar", 1), ("main-cpio", 2),
    ("main-bsdtar", 3), ("gzip", 4),
  )
  for label, index in cases:
    _validate_archive_observation(label, mapped.raw_files.records[index][0])
  _require(len(mapped.raw_files.early_raw) == EARLY_BYTES
           and _sha256(mapped.raw_files.early_raw) == EARLY_SHA256
           and len(mapped.raw_files.main_raw) == MAIN_BYTES
           and _sha256(mapped.raw_files.main_raw) == MAIN_SHA256
           and len(mapped.raw_files.early_raw + mapped.raw_files.records[4][0]) == E_BYTES
           and _sha256(mapped.raw_files.early_raw + mapped.raw_files.records[4][0]) == E_SHA256,
           "E_CONTROL_SEMANTIC_INVALID")


def _validate_payload_family(mapped: MappedControlOutputs) -> None:
  for index, name in enumerate(PAYLOAD_SHA256, start=5):
    _validate_payload_observation(name, mapped.raw_files.records[index][0])


def _validate_tree_family(mapped: MappedControlOutputs) -> None:
  control_before = _semantic_control_before(mapped.raw_files)
  cases = (
    ("control", control_before, mapped.raw_files.control_state),
    ("lookup", mapped.raw_files.lookup_state, mapped.raw_files.lookup_state),
  )
  for kind, before, after in cases:
    _validate_tree_observation(
      kind, before, _semantic_bound_observation(mapped.raw_files, after),
    )


def _validate_index_family(mapped: MappedControlOutputs) -> None:
  control_root = Path(mapped.raw_files.paths[1]) / "lib/modules" / KERNEL
  lookup_root = Path(mapped.raw_files.paths[2]) / "lib/modules" / KERNEL
  cases = tuple(
    ("generated", name, control_root / name) for name in sorted(GENERATED_SHA256)
  ) + tuple(
    ("retained", name, lookup_root / name) for name in sorted(INDEX_SHA256)
  )
  for kind, name, path in cases:
    raw = read_regular(path)
    observation = _semantic_file_observation(path, raw)
    _validate_index_observation(
      kind, name, raw, _semantic_bound_observation(mapped.raw_files, observation),
    )


def _validate_module_family(mapped: MappedControlOutputs) -> None:
  names = _semantic_module_names(mapped.raw_files.main_raw)
  for ordinal, name in enumerate(sorted(names)):
    _validate_module_observation(
      name, mapped.raw_files.records[12 + ordinal * 2][0],
      mapped.raw_files.records[13 + ordinal * 2][0],
    )


def _validate_alias_family(mapped: MappedControlOutputs) -> None:
  for ordinal, alias in enumerate(ALIASES):
    _validate_alias_observation(alias, mapped.raw_files.records[412 + ordinal][0])


def _validate_symbol_family(mapped: MappedControlOutputs) -> None:
  for ordinal, symbol in enumerate(EXPORTS):
    _validate_symbol_observation(symbol, mapped.raw_files.records[415 + ordinal][0])


def _validate_command_family(mapped: MappedControlOutputs) -> None:
  names = _semantic_module_names(mapped.raw_files.main_raw)
  fixture_plan = _semantic_command_plan(mapped.raw_files.paths, names)
  operational_plan = command_plan(names)
  _require(len(mapped.raw_files.record_state.directories) == 1
           and len(mapped.raw_files.record_state.files) == SEMANTIC_RECORDS * 3
           and mapped.raw_files.empty_config_raw == b"",
           "E_CONTROL_SEMANTIC_INVALID")
  for index in range(SEMANTIC_RECORDS):
    observation = _semantic_command_observation(mapped.raw_files, index)
    report = observation["report"]
    _require(type(report) is dict
             and report.get("command") == list(fixture_plan[index])
             and report.get("operational_command") == list(operational_plan[index]),
             "E_CONTROL_SEMANTIC_INVALID")
    _validate_command_observation(
      index, _semantic_bound_observation(mapped.raw_files, observation),
    )


def _validate_identity_family(mapped: MappedControlOutputs) -> None:
  for observation in _semantic_identity_records(mapped.raw_files):
    _validate_identity_observation(
      _semantic_bound_observation(mapped.raw_files, observation),
    )


def _validate_provenance_family(mapped: MappedControlOutputs) -> None:
  _validate_provenance_observation(_semantic_provenance(mapped.raw_files))


def _evaluate_control_semantics() -> SemanticFixtureEvaluation:
  mapped = _read_fixed_semantic_fixture_outputs()
  _validate_archive_family(mapped)
  _validate_payload_family(mapped)
  _validate_tree_family(mapped)
  _validate_index_family(mapped)
  _validate_module_family(mapped)
  _validate_alias_family(mapped)
  _validate_symbol_family(mapped)
  _validate_command_family(mapped)
  _validate_identity_family(mapped)
  _validate_provenance_family(mapped)
  aggregate = _semantic_aggregate(mapped.raw_files)
  aggregate_sha256 = _sha256(_semantic_json_bytes(aggregate))
  return SemanticFixtureEvaluation(
    status="NONFRESH_FIXTURE",
    semantic_validated=True,
    aggregate_sha256=aggregate_sha256,
    planned_children=SEMANTIC_RECORDS,
    children_executed=0,
    historical_generated_files=12,
    structural_control_proved=False,
    operational_control_proved=False,
    fresh_control_proved=False,
    image_created=False,
    module_loaded=False,
    staged=False,
    booted=False,
  )


def _rename_noreplace_errcheck(result, function, arguments):
  if result != 0:
    error = ctypes.get_errno()
    if error == errno.EEXIST:
      raise RecipeError("E_CONTROL_SEMANTIC_EXISTS")
    raise RecipeError("E_CONTROL_SEMANTIC_INVALID")
  return result


_SEMANTIC_LIBC = ctypes.CDLL(None, use_errno=True)
_SEMANTIC_LIBC.renameat2.argtypes = [
  ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint,
]
_SEMANTIC_LIBC.renameat2.restype = ctypes.c_int
_SEMANTIC_LIBC.renameat2.errcheck = _rename_noreplace_errcheck


def _rename_noreplace(source: Path, target: Path) -> None:
  _SEMANTIC_LIBC.renameat2(
    _AT_FDCWD, os.fsencode(source), _AT_FDCWD, os.fsencode(target),
    RENAME_NOREPLACE,
  )


def _semantic_fixture_work_membership() -> frozenset[str]:
  return frozenset(path.name for path in Path("/work").iterdir())


def _semantic_fixture_result_bytes(evaluation: SemanticFixtureEvaluation) -> bytes:
  result = {
    "schema": 2,
    "kind": "dev147-e-control-semantic-fixture-result-v2",
    "status": evaluation.status,
    "semantic_validated": evaluation.semantic_validated,
    "aggregate_sha256": evaluation.aggregate_sha256,
    "planned_children": evaluation.planned_children,
    "children_executed": evaluation.children_executed,
    "historical_generated_files": evaluation.historical_generated_files,
    "structural_control_proved": evaluation.structural_control_proved,
    "operational_control_proved": evaluation.operational_control_proved,
    "fresh_control_proved": evaluation.fresh_control_proved,
    "image_created": evaluation.image_created,
    "module_loaded": evaluation.module_loaded,
    "staged": evaluation.staged,
    "booted": evaluation.booted,
  }
  serialized = json.dumps(
    result, sort_keys=True, separators=(",", ":"), allow_nan=False,
  ) + "\n"
  return serialized.encode("ascii")


def publish_semantic_fixture_result() -> SemanticFixtureAcceptance:
  membership_before = _semantic_fixture_work_membership()
  _require(SEMANTIC_FIXTURE_PENDING.name not in membership_before and SEMANTIC_FIXTURE_RESULT.name not in membership_before, "E_CONTROL_SEMANTIC_EXISTS")
  _require(membership_before == SEMANTIC_FIXTURE_WORK_MEMBERS, "E_CONTROL_SEMANTIC_INVALID")
  evaluation = _evaluate_control_semantics()
  result_raw = _semantic_fixture_result_bytes(evaluation)
  acceptance = SemanticFixtureAcceptance(
    status=evaluation.status,
    semantic_validated=evaluation.semantic_validated,
    aggregate_sha256=evaluation.aggregate_sha256,
    result_sha256=_sha256(result_raw),
    pending_path=str(SEMANTIC_FIXTURE_PENDING),
    result_path=str(SEMANTIC_FIXTURE_RESULT),
    planned_children=evaluation.planned_children,
    children_executed=evaluation.children_executed,
    structural_control_proved=evaluation.structural_control_proved,
    operational_control_proved=evaluation.operational_control_proved,
    fresh_control_proved=evaluation.fresh_control_proved,
    image_created=evaluation.image_created,
    module_loaded=evaluation.module_loaded,
    staged=evaluation.staged,
    booted=evaluation.booted,
  )
  membership_after = _semantic_fixture_work_membership()
  _require(membership_after == membership_before == SEMANTIC_FIXTURE_WORK_MEMBERS, "E_CONTROL_SEMANTIC_INVALID")
  write_new(SEMANTIC_FIXTURE_PENDING, result_raw)
  _rename_noreplace(SEMANTIC_FIXTURE_PENDING, SEMANTIC_FIXTURE_RESULT)
  return acceptance


@dataclass(frozen=True)
class ExecutionPolicy:
  command: tuple[str, ...]
  environment: tuple[tuple[str, str], ...]
  task_bindings: tuple[str, ...]
  uid: int
  gid: int
  cwd: str
  umask: int
  runtime_mounts: int
  fixed_sandbox_mounts: int
  task_inputs: int
  read_only_mounts: int
  planned_children: int
  control_seconds: float
  child_seconds: float
  workload_seconds: int
  outer_seconds: int
  mode: str


@dataclass(frozen=True)
class OperationalPolicy:
  execution: ExecutionPolicy
  commands: tuple[tuple[str, ...], ...]
  record_root: str
  control_root: str
  lookup_root: str
  empty_config: str
  early_stream: str
  main_stream: str
  artifacts: tuple[str, ...]


@dataclass(frozen=True)
class OperationalAcceptance:
  status: str
  mode: str
  header_sha256: str
  evidence_sha256: str
  result_sha256: str
  planned_children: int
  children_executed: int
  operational_control_proved: bool
  fresh_control_proved: bool
  image_created: bool
  module_loaded: bool
  staged: bool
  booted: bool


@dataclass(frozen=True)
class OperationalInputSnapshot:
  files: tuple[tuple[str, bytes, tuple[int, ...]], ...]
  directories: tuple[tuple[str, tuple[int, ...], tuple[str, ...]], ...]


@dataclass(frozen=True)
class OperationalContext:
  policy: OperationalPolicy
  inputs: OperationalInputSnapshot
  selection: ESelection
  names: dict[str, str]
  builtins: set[str]
  control_before: TreeState
  lookup_before: TreeState
  materialized_files: tuple[tuple[str, bytes, tuple[int, ...]], ...]


@dataclass(frozen=True)
class OperationalEvaluation:
  records: tuple[dict[str, object], ...]
  generated: dict[str, bytes]
  regeneration: Regeneration
  module_lookups: tuple[dict[str, object], ...]
  alias_lookups: tuple[dict[str, object], ...]
  symbol_lookups: tuple[dict[str, object], ...]

EXECUTION_COMMAND = ("/usr/bin/python3.14", "-I", "-S", "-B", "/inputs/recipe")
EXECUTION_ENVIRONMENT = (
  ("PATH", "/usr/bin:/bin"),
  ("LC_ALL", "C"),
  ("TMPDIR", "/tmp"),
  ("PYTHONDONTWRITEBYTECODE", "1"),
)
EXECUTION_TASK_BINDINGS = (
  "/inputs/recipe", "/inputs/subject", "/inputs/contract", "/inputs/assembly",
  "/inputs/control", "/inputs/helper", "/inputs/base", "/inputs/index-inputs",
)
EXECUTION_UID = 1001
EXECUTION_GID = 1001
EXECUTION_CWD = "/work"
EXECUTION_UMASK = 0o077
EXECUTION_RUNTIME_MOUNTS = 582
EXECUTION_FIXED_SANDBOX_MOUNTS = 3
EXECUTION_TASK_INPUTS = 8
EXECUTION_READ_ONLY_MOUNTS = 593
EXECUTION_PLANNED_CHILDREN = 424
EXECUTION_CONTROL_SECONDS = 270.0
EXECUTION_CHILD_SECONDS = 30.0
EXECUTION_WORKLOAD_SECONDS = 280
EXECUTION_OUTER_SECONDS = 285
EXECUTION_MODE = "E_NO_CHANGE_OFFLINE"
OPERATIONAL_RECORD_ROOT = "/work/e-control-children-e1"
OPERATIONAL_ARTIFACTS = (
  "/work/e-control-header.json",
  "/work/e-control-evidence.json",
  "/work/e-control-result.json",
)
OPERATIONAL_RESULT_PENDING = "/work/e-control-result.pending"
OPERATIONAL_PROOF_PATH = "/inputs/proof"
OPERATIONAL_PROOF_SHA256 = "9133cb64040f9df0daf9aa0caaab913c90fe7ce5c9bf59a19c71ce3e36fb0c94"
OPERATIONAL_RECIPE_LIMIT = 128 * 1024
OPERATIONAL_HEADER_LIMIT = 2 * 1024 * 1024
OPERATIONAL_EVIDENCE_LIMIT = 16 * 1024 * 1024
OPERATIONAL_INDEX_INPUTS = {
  "modules.order": (73113, "497c8546d3131d01191f7a66b68047abce5e5235ae982890180007f55c51a927"),
  "modules.builtin": (10592, "74de5bab05fe70496f7702d83974adf8816ea826f1d8579f3b3f4b28a3890d2b"),
  "modules.builtin.modinfo": (106640, "702d4cabaa9bdc1b282d0e419ba091f64dc06ba737fe7319928bb3003adeea4b"),
}
OPERATIONAL_INPUT_MEMBERS = frozenset((
  "recipe", "subject", "contract", "assembly", "control", "helper",
  "base", "index-inputs", "proof",
))
OPERATIONAL_INITIAL_WORK_MEMBERS = frozenset((
  "descriptor-sentinel", "probe-write", "stdout.log", "stderr.log",
))
OPERATIONAL_REPORT_KEYS = frozenset((
  "command", "status", "returncode", "stdout", "stderr", "retained_bytes",
  "observed_bytes", "stdin_sha256", "stdin_bytes", "elapsed_seconds", "pid",
  "killed", "reaped",
))
OPERATIONAL_STDOUT_LIMITS = (
  1024, 1024, 65536, 65536, E_BYTES - 10240,
  1213760, 12368, 66512, 20312, 1, 128 * 1024, 128 * 1024,
  *((4096, 65536) * 200),
  *((65536,) * 12),
)
OPERATIONAL_STDERR_LIMIT = 1
OPERATIONAL_REPORT_LIMIT = 128 * 1024
OPERATIONAL_EMPTY_CONFIG_LIMIT = 1
OPERATIONAL_EARLY_STREAM_LIMIT = 10240
OPERATIONAL_MAIN_STREAM_LIMIT = 61286668
OPERATIONAL_RECORD_FILES = 1272
OPERATIONAL_CONTROL_TREE_FILES = 214
OPERATIONAL_LOOKUP_TREE_FILES = 207
OPERATIONAL_TREE_DIRECTORIES = 48
OPERATIONAL_TREE_MAX_DEPTH = 16
OPERATIONAL_TREE_FILE_LIMIT = 2 * 1024 * 1024
OPERATIONAL_TREE_AGGREGATE_LIMIT = 64 * 1024 * 1024

def operational_execution_policy() -> ExecutionPolicy:
  return ExecutionPolicy(
    command=EXECUTION_COMMAND,
    environment=EXECUTION_ENVIRONMENT,
    task_bindings=EXECUTION_TASK_BINDINGS,
    uid=EXECUTION_UID,
    gid=EXECUTION_GID,
    cwd=EXECUTION_CWD,
    umask=EXECUTION_UMASK,
    runtime_mounts=EXECUTION_RUNTIME_MOUNTS,
    fixed_sandbox_mounts=EXECUTION_FIXED_SANDBOX_MOUNTS,
    task_inputs=EXECUTION_TASK_INPUTS,
    read_only_mounts=EXECUTION_READ_ONLY_MOUNTS,
    planned_children=EXECUTION_PLANNED_CHILDREN,
    control_seconds=EXECUTION_CONTROL_SECONDS,
    child_seconds=EXECUTION_CHILD_SECONDS,
    workload_seconds=EXECUTION_WORKLOAD_SECONDS,
    outer_seconds=EXECUTION_OUTER_SECONDS,
    mode=EXECUTION_MODE,
  )

def _read_bounded_operational_file(path: Path, limit: int) -> bytes:
  _require(path.is_absolute(), "E_CONTROL_OPERATIONAL_INVALID")
  _require(type(limit) is int, "E_CONTROL_OPERATIONAL_INVALID")
  _require(0 < limit <= OPERATIONAL_TREE_AGGREGATE_LIMIT, "E_CONTROL_OPERATIONAL_INVALID")
  before = path.lstat()
  _require(stat.S_ISREG(before.st_mode), "E_CONTROL_OPERATIONAL_INVALID")
  _require(stat.S_IMODE(before.st_mode) == 0o600, "E_CONTROL_OPERATIONAL_INVALID")
  _require(before.st_uid == before.st_gid == 1001, "E_CONTROL_OPERATIONAL_INVALID")
  _require(before.st_nlink == 1, "E_CONTROL_OPERATIONAL_INVALID")
  _require(0 <= before.st_size <= limit, "E_CONTROL_OPERATIONAL_INVALID")
  descriptor = os.open(
    path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC,
  )
  with os.fdopen(descriptor, "rb") as stream:
    _require(
      _structural_identity(before) == _structural_identity(os.fstat(descriptor)),
      "E_CONTROL_OPERATIONAL_INVALID",
    )
    raw = stream.read(limit + 1)
    _require(
      _structural_identity(before) == _structural_identity(os.fstat(descriptor))
      == _structural_identity(path.lstat()),
      "E_CONTROL_OPERATIONAL_INVALID",
    )
  _require(len(raw) == before.st_size <= limit, "E_CONTROL_OPERATIONAL_INVALID")
  return raw

def _operational_record_path(index: int, suffix: str) -> Path:
  _require(type(index) is int and 0 <= index < SEMANTIC_RECORDS,
           "E_CONTROL_OPERATIONAL_INVALID")
  _require(type(suffix) is str and suffix in ("stdout", "stderr", "json"),
           "E_CONTROL_OPERATIONAL_INVALID")
  return Path(OPERATIONAL_RECORD_ROOT) / f"child-{index:03d}.{suffix}"

def _validate_operational_record_root() -> TreeState:
  root = Path(OPERATIONAL_RECORD_ROOT)
  _require(root.is_absolute(), "E_CONTROL_OPERATIONAL_INVALID")
  before = root.lstat()
  _require(stat.S_ISDIR(before.st_mode), "E_CONTROL_OPERATIONAL_INVALID")
  _require(stat.S_IMODE(before.st_mode) == 0o700, "E_CONTROL_OPERATIONAL_INVALID")
  _require(before.st_uid == before.st_gid == 1001, "E_CONTROL_OPERATIONAL_INVALID")
  _require(before.st_nlink == 2, "E_CONTROL_OPERATIONAL_INVALID")
  expected = {
    f"child-{index:03d}.{suffix}"
    for index in range(SEMANTIC_RECORDS)
    for suffix in ("stdout", "stderr", "json")
  }
  observed = {}
  descriptor = os.open(
    root, os.O_RDONLY | os.O_DIRECTORY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC,
  )
  try:
    _require(_structural_identity(before) == _structural_identity(os.fstat(descriptor)),
             "E_CONTROL_OPERATIONAL_INVALID")
    with os.scandir(descriptor) as entries:
      for entry in entries:
        info = entry.stat(follow_symlinks=False)
        _require(stat.S_ISREG(info.st_mode), "E_CONTROL_OPERATIONAL_INVALID")
        _require(stat.S_IMODE(info.st_mode) == 0o600, "E_CONTROL_OPERATIONAL_INVALID")
        _require(info.st_uid == info.st_gid == 1001, "E_CONTROL_OPERATIONAL_INVALID")
        _require(info.st_nlink == 1, "E_CONTROL_OPERATIONAL_INVALID")
        observed[entry.name] = info
        _require(len(observed) <= OPERATIONAL_RECORD_FILES,
                 "E_CONTROL_OPERATIONAL_INVALID")
    _require(
      _structural_identity(before) == _structural_identity(os.fstat(descriptor))
      == _structural_identity(root.lstat()),
      "E_CONTROL_OPERATIONAL_INVALID",
    )
  finally:
    os.close(descriptor)
  _require(set(observed) == expected, "E_CONTROL_OPERATIONAL_INVALID")
  _require(len(observed) == OPERATIONAL_RECORD_FILES, "E_CONTROL_OPERATIONAL_INVALID")
  files = {}
  for index in range(SEMANTIC_RECORDS):
    for suffix, limit in (
      ("stdout", OPERATIONAL_STDOUT_LIMITS[index]),
      ("stderr", OPERATIONAL_STDERR_LIMIT),
      ("json", OPERATIONAL_REPORT_LIMIT),
    ):
      path = _operational_record_path(index, suffix)
      raw = _read_bounded_operational_file(path, limit)
      _require(_structural_identity(observed[path.name]) == _structural_identity(path.lstat()),
               "E_CONTROL_OPERATIONAL_INVALID")
      files[path.name] = FileState(_structural_identity(observed[path.name]), _sha256(raw))
  _require(_structural_identity(before) == _structural_identity(root.lstat()),
           "E_CONTROL_OPERATIONAL_INVALID")
  return TreeState({".": _structural_identity(before)[:5]}, files)

def _bounded_operational_tree(
  root: Path,
  *,
  expected_files: int,
  expected_directories: int,
  max_depth: int,
  per_file_limit: int,
  aggregate_limit: int,
) -> TreeState:
  _require(isinstance(root, Path) and root.is_absolute(), "E_CONTROL_OPERATIONAL_INVALID")
  _require(type(expected_files) is int and 0 <= expected_files <= 4096,
           "E_CONTROL_OPERATIONAL_INVALID")
  _require(type(expected_directories) is int and 1 <= expected_directories <= 512,
           "E_CONTROL_OPERATIONAL_INVALID")
  _require(type(max_depth) is int and 0 <= max_depth <= OPERATIONAL_TREE_MAX_DEPTH,
           "E_CONTROL_OPERATIONAL_INVALID")
  _require(type(per_file_limit) is int and 0 < per_file_limit <= OPERATIONAL_TREE_FILE_LIMIT,
           "E_CONTROL_OPERATIONAL_INVALID")
  _require(type(aggregate_limit) is int and 0 < aggregate_limit <= OPERATIONAL_TREE_AGGREGATE_LIMIT,
           "E_CONTROL_OPERATIONAL_INVALID")
  root_before = root.lstat()
  pending = [(root, 0, _structural_identity(root_before))]
  directories = {}
  files = {}
  aggregate = 0
  while pending:
    directory, depth, expected_identity = pending.pop()
    _require(depth <= max_depth, "E_CONTROL_OPERATIONAL_INVALID")
    before = directory.lstat()
    _require(_structural_identity(before) == expected_identity,
             "E_CONTROL_OPERATIONAL_INVALID")
    _require(stat.S_ISDIR(before.st_mode), "E_CONTROL_OPERATIONAL_INVALID")
    _require(stat.S_IMODE(before.st_mode) == 0o700, "E_CONTROL_OPERATIONAL_INVALID")
    _require(before.st_uid == before.st_gid == 1001, "E_CONTROL_OPERATIONAL_INVALID")
    relative_directory = "." if directory == root else str(directory.relative_to(root))
    directories[relative_directory] = _structural_identity(before)[:5]
    _require(len(directories) <= expected_directories, "E_CONTROL_OPERATIONAL_INVALID")
    descriptor = os.open(
      directory,
      os.O_RDONLY | os.O_DIRECTORY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC,
    )
    try:
      _require(_structural_identity(before) == _structural_identity(os.fstat(descriptor)),
               "E_CONTROL_OPERATIONAL_INVALID")
      with os.scandir(descriptor) as entries:
        for entry in entries:
          info = entry.stat(follow_symlinks=False)
          path = directory / entry.name
          if stat.S_ISDIR(info.st_mode):
            _require(stat.S_IMODE(info.st_mode) == 0o700, "E_CONTROL_OPERATIONAL_INVALID")
            _require(info.st_uid == info.st_gid == 1001, "E_CONTROL_OPERATIONAL_INVALID")
            pending.append((path, depth + 1, _structural_identity(info)))
            _require(len(directories) + len(pending) <= expected_directories,
                     "E_CONTROL_OPERATIONAL_INVALID")
          else:
            _require(stat.S_ISREG(info.st_mode), "E_CONTROL_OPERATIONAL_INVALID")
            _require(stat.S_IMODE(info.st_mode) == 0o600, "E_CONTROL_OPERATIONAL_INVALID")
            _require(info.st_uid == info.st_gid == 1001, "E_CONTROL_OPERATIONAL_INVALID")
            _require(info.st_nlink == 1, "E_CONTROL_OPERATIONAL_INVALID")
            raw = _read_bounded_operational_file(path, per_file_limit)
            _require(_structural_identity(info) == _structural_identity(path.lstat()),
                     "E_CONTROL_OPERATIONAL_INVALID")
            aggregate += len(raw)
            _require(aggregate <= aggregate_limit, "E_CONTROL_OPERATIONAL_INVALID")
            relative_file = str(path.relative_to(root))
            files[relative_file] = FileState(_structural_identity(info), _sha256(raw))
            _require(len(files) <= expected_files, "E_CONTROL_OPERATIONAL_INVALID")
      _require(
        _structural_identity(before) == _structural_identity(os.fstat(descriptor))
        == _structural_identity(directory.lstat()),
        "E_CONTROL_OPERATIONAL_INVALID",
      )
    finally:
      os.close(descriptor)
  _require(len(files) == expected_files, "E_CONTROL_OPERATIONAL_INVALID")
  _require(len(directories) == expected_directories, "E_CONTROL_OPERATIONAL_INVALID")
  return TreeState(directories, files)

def _collect_operational_outputs() -> RawControlFiles:
  record_state = _validate_operational_record_root()
  records = []
  for index in range(SEMANTIC_RECORDS):
    stdout = _read_bounded_operational_file(
      _operational_record_path(index, "stdout"), OPERATIONAL_STDOUT_LIMITS[index],
    )
    stderr = _read_bounded_operational_file(
      _operational_record_path(index, "stderr"), OPERATIONAL_STDERR_LIMIT,
    )
    report = _read_bounded_operational_file(
      _operational_record_path(index, "json"), OPERATIONAL_REPORT_LIMIT,
    )
    records.append((stdout, stderr, report))
  control_state = _bounded_operational_tree(
    Path(CONTROL_ROOT),
    expected_files=OPERATIONAL_CONTROL_TREE_FILES,
    expected_directories=OPERATIONAL_TREE_DIRECTORIES,
    max_depth=OPERATIONAL_TREE_MAX_DEPTH,
    per_file_limit=OPERATIONAL_TREE_FILE_LIMIT,
    aggregate_limit=OPERATIONAL_TREE_AGGREGATE_LIMIT,
  )
  lookup_state = _bounded_operational_tree(
    Path(LOOKUP_ROOT),
    expected_files=OPERATIONAL_LOOKUP_TREE_FILES,
    expected_directories=OPERATIONAL_TREE_DIRECTORIES,
    max_depth=OPERATIONAL_TREE_MAX_DEPTH,
    per_file_limit=OPERATIONAL_TREE_FILE_LIMIT,
    aggregate_limit=OPERATIONAL_TREE_AGGREGATE_LIMIT,
  )
  empty_config_raw = _read_bounded_operational_file(
    Path(EMPTY_CONFIG), OPERATIONAL_EMPTY_CONFIG_LIMIT,
  )
  early_raw = _read_bounded_operational_file(Path(EARLY_PATH), OPERATIONAL_EARLY_STREAM_LIMIT)
  main_raw = _read_bounded_operational_file(Path(MAIN_PATH), OPERATIONAL_MAIN_STREAM_LIMIT)
  return RawControlFiles(
    paths=SEMANTIC_OPERATIONAL_PATHS,
    record_state=record_state,
    records=tuple(records),
    control_state=control_state,
    lookup_state=lookup_state,
    empty_config_raw=empty_config_raw,
    early_raw=early_raw,
    main_raw=main_raw,
  )


def _read_exact_operational_input(
  path: Path,
  *,
  maximum: int,
  mode: int,
  size: int | None,
  digest: str | None,
) -> tuple[bytes, tuple[int, ...]]:
  _require(path.is_absolute() and path.is_relative_to("/inputs"), "E_CONTROL_INPUT_INVALID")
  _require(type(maximum) is int and 0 < maximum <= E_BYTES, "E_CONTROL_INPUT_INVALID")
  _require(type(mode) is int and mode in (0o600, 0o644), "E_CONTROL_INPUT_INVALID")
  _require(size is None or type(size) is int and 0 <= size <= maximum,
           "E_CONTROL_INPUT_INVALID")
  _require(digest is None or type(digest) is str
           and re.fullmatch(r"[0-9a-f]{64}", digest) is not None,
           "E_CONTROL_INPUT_INVALID")
  try:
    before = path.lstat()
    _require(stat.S_ISREG(before.st_mode), "E_CONTROL_INPUT_INVALID")
    _require(stat.S_IMODE(before.st_mode) == mode, "E_CONTROL_INPUT_INVALID")
    _require(before.st_uid == before.st_gid == 1001, "E_CONTROL_INPUT_INVALID")
    _require(before.st_nlink == 1, "E_CONTROL_INPUT_INVALID")
    _require(0 < before.st_size <= maximum, "E_CONTROL_INPUT_INVALID")
    _require(size is None or before.st_size == size, "E_CONTROL_INPUT_INVALID")
    descriptor = os.open(
      path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC,
    )
    with os.fdopen(descriptor, "rb") as stream:
      _require(_structural_identity(before) == _structural_identity(os.fstat(descriptor)),
               "E_CONTROL_INPUT_INVALID")
      raw = stream.read(maximum + 1)
      _require(
        _structural_identity(before) == _structural_identity(os.fstat(descriptor))
        == _structural_identity(path.lstat()),
        "E_CONTROL_INPUT_INVALID",
      )
    _require(len(raw) == before.st_size <= maximum, "E_CONTROL_INPUT_INVALID")
    _require(digest is None or _sha256(raw) == digest, "E_CONTROL_INPUT_INVALID")
    return raw, _structural_identity(before)
  except RecipeError:
    raise
  except (OSError, RuntimeError, ValueError, TypeError, OverflowError):
    raise RecipeError("E_CONTROL_INPUT_INVALID") from None


def _capture_operational_input_directory(
  path: Path,
  members: frozenset[str],
) -> tuple[str, tuple[int, ...], tuple[str, ...]]:
  try:
    before = path.lstat()
    _require(stat.S_ISDIR(before.st_mode), "E_CONTROL_INPUT_INVALID")
    _require(stat.S_IMODE(before.st_mode) == 0o700, "E_CONTROL_INPUT_INVALID")
    _require(before.st_uid == before.st_gid == 1001, "E_CONTROL_INPUT_INVALID")
    _require(before.st_nlink == 2, "E_CONTROL_INPUT_INVALID")
    observed = tuple(sorted(item.name for item in path.iterdir()))
    _require(frozenset(observed) == members and len(observed) == len(members),
             "E_CONTROL_INPUT_INVALID")
    _require(_structural_identity(path.lstat()) == _structural_identity(before),
             "E_CONTROL_INPUT_INVALID")
    return str(path), _structural_identity(before), observed
  except RecipeError:
    raise
  except (OSError, RuntimeError, ValueError, TypeError):
    raise RecipeError("E_CONTROL_INPUT_INVALID") from None


def _capture_operational_inputs() -> OperationalInputSnapshot:
  inputs = Path("/inputs")
  try:
    _require(stat.S_ISDIR(inputs.lstat().st_mode), "E_CONTROL_INPUT_INVALID")
    _require(frozenset(path.name for path in inputs.iterdir()) == OPERATIONAL_INPUT_MEMBERS,
             "E_CONTROL_INPUT_INVALID")
  except RecipeError:
    raise
  except OSError:
    raise RecipeError("E_CONTROL_INPUT_INVALID") from None

  files: list[tuple[str, bytes, tuple[int, ...]]] = []

  def capture(
    path: Path,
    *,
    maximum: int,
    mode: int,
    size: int | None,
    digest: str | None,
  ) -> None:
    raw, identity = _read_exact_operational_input(
      path, maximum=maximum, mode=mode, size=size, digest=digest,
    )
    files.append((str(path), raw, identity))

  capture(
    Path("/inputs/recipe"), maximum=OPERATIONAL_RECIPE_LIMIT, mode=0o644,
    size=None, digest=None,
  )
  capture(
    Path(OPERATIONAL_PROOF_PATH), maximum=128 * 1024, mode=0o600,
    size=None, digest=OPERATIONAL_PROOF_SHA256,
  )
  for _name, path, digest in FIXED_SOURCE_INPUTS:
    capture(
      Path(path), maximum=FIXED_SOURCE_BYTES, mode=0o600, size=None, digest=digest,
    )
  capture(
    Path("/inputs/base"), maximum=E_BYTES, mode=0o600, size=E_BYTES,
    digest=E_SHA256,
  )
  for name, (size, digest) in sorted(OPERATIONAL_INDEX_INPUTS.items()):
    capture(
      Path("/inputs/index-inputs") / name, maximum=size, mode=0o644,
      size=size, digest=digest,
    )

  source_members = tuple(
    (Path(path).parent, frozenset((Path(path).name,)))
    for _name, path, _digest in FIXED_SOURCE_INPUTS
  )
  directories = tuple(
    _capture_operational_input_directory(path, members)
    for path, members in (*source_members, (
      Path("/inputs/index-inputs"), frozenset(OPERATIONAL_INDEX_INPUTS),
    ))
  )
  return OperationalInputSnapshot(tuple(files), directories)


def _operational_input_bytes(
  snapshot_value: OperationalInputSnapshot,
  path: str,
) -> bytes:
  matches = tuple(raw for name, raw, _identity in snapshot_value.files if name == path)
  _require(len(matches) == 1, "E_CONTROL_INPUT_INVALID")
  return matches[0]


def _operational_builtins(raw: bytes) -> set[str]:
  try:
    lines = raw.decode("ascii").splitlines()
    values = {
      module_name(Path(line).name)
      for line in lines
      if line
    }
  except (UnicodeError, RuntimeError, ValueError, TypeError):
    raise RecipeError("E_CONTROL_INPUT_INVALID") from None
  _require(len(values) == len(lines) and 0 < len(values) <= 8192
           and "ecb" in values, "E_CONTROL_INPUT_INVALID")
  return values


def _operational_policy_from_inputs(
  inputs: OperationalInputSnapshot,
) -> tuple[OperationalPolicy, ESelection, dict[str, str], set[str]]:
  selection = select_e(_operational_input_bytes(inputs, "/inputs/base"))
  names = {module.name: str(module.relative) for module in selection.modules}
  commands = command_plan(names)
  _require(len(commands) == EXECUTION_PLANNED_CHILDREN, "E_COMMAND_PLAN")
  policy = OperationalPolicy(
    execution=operational_execution_policy(),
    commands=commands,
    record_root=OPERATIONAL_RECORD_ROOT,
    control_root=CONTROL_ROOT,
    lookup_root=LOOKUP_ROOT,
    empty_config=EMPTY_CONFIG,
    early_stream=EARLY_PATH,
    main_stream=MAIN_PATH,
    artifacts=OPERATIONAL_ARTIFACTS,
  )
  builtins = _operational_builtins(
    _operational_input_bytes(inputs, "/inputs/index-inputs/modules.builtin"),
  )
  return policy, selection, names, builtins


def _operational_work_membership() -> frozenset[str]:
  try:
    return frozenset(path.name for path in Path("/work").iterdir())
  except OSError:
    raise RecipeError("E_CONTROL_WORK_INVALID") from None


def _capture_operational_materialized_file(
  path: Path,
  expected: bytes,
) -> tuple[str, bytes, tuple[int, ...]]:
  before = path.lstat()
  raw = _read_bounded_operational_file(path, max(1, len(expected)))
  _require(raw == expected and _structural_identity(path.lstat()) == _structural_identity(before),
           "E_CONTROL_WORK_INVALID")
  return str(path), raw, _structural_identity(before)


def _materialize_operational_context() -> OperationalContext:
  _require(_operational_work_membership() == OPERATIONAL_INITIAL_WORK_MEMBERS,
           "E_CONTROL_WORK_INVALID")
  inputs = _capture_operational_inputs()
  policy, selection, names, builtins = _operational_policy_from_inputs(inputs)
  _require(not any(Path(path).exists() or Path(path).is_symlink() for path in (
    OPERATIONAL_RECORD_ROOT, CONTROL_ROOT, LOOKUP_ROOT, EMPTY_CONFIG,
    EARLY_PATH, MAIN_PATH, OPERATIONAL_RESULT_PENDING, *OPERATIONAL_ARTIFACTS,
  )), "E_CONTROL_OUTPUT_EXISTS")

  write_new(Path(EARLY_PATH), selection.early.raw)
  write_new(Path(MAIN_PATH), selection.main.raw)
  write_new(Path(EMPTY_CONFIG), b"")
  modules = {str(module.relative): module.member.payload for module in selection.modules}
  index_inputs = {
    name: _operational_input_bytes(inputs, f"/inputs/index-inputs/{name}")
    for name in OPERATIONAL_INDEX_INPUTS
  }
  try:
    control_before = build_root(Path(CONTROL_ROOT), modules, index_inputs)
    lookup_before = build_root(Path(LOOKUP_ROOT), modules, selection.indexes)
  except ControlError as error:
    raise RecipeError("E_CONTROL_ROOT_INVALID") from error
  _require(len(control_before.directories) == len(lookup_before.directories) == 48
           and len(control_before.files) == 203 and len(lookup_before.files) == 207,
           "E_CONTROL_ROOT_INVALID")
  materialized_files = (
    _capture_operational_materialized_file(Path(EARLY_PATH), selection.early.raw),
    _capture_operational_materialized_file(Path(MAIN_PATH), selection.main.raw),
    _capture_operational_materialized_file(Path(EMPTY_CONFIG), b""),
  )
  expected = OPERATIONAL_INITIAL_WORK_MEMBERS | frozenset((
    Path(EARLY_PATH).name, Path(MAIN_PATH).name, Path(EMPTY_CONFIG).name,
    Path(CONTROL_ROOT).name, Path(LOOKUP_ROOT).name,
  ))
  _require(_operational_work_membership() == expected, "E_CONTROL_WORK_INVALID")
  return OperationalContext(
    policy, inputs, selection, names, builtins, control_before, lookup_before,
    materialized_files,
  )


def _run_operational_commands(context: OperationalContext) -> RawControlFiles:
  try:
    runner = Commands(
      Path(context.policy.record_root),
      budget_seconds=context.policy.execution.control_seconds,
    )
    for index, command in enumerate(context.policy.commands):
      if index == 4:
        runner.run(
          command,
          stdin=Path(MAIN_PATH),
          stdin_sha256=MAIN_SHA256,
          timeout=context.policy.execution.child_seconds,
          stdout_limit=OPERATIONAL_STDOUT_LIMITS[index],
          stderr_limit=OPERATIONAL_STDERR_LIMIT,
        )
      else:
        runner.run(
          command,
          timeout=context.policy.execution.child_seconds,
          stdout_limit=OPERATIONAL_STDOUT_LIMITS[index],
          stderr_limit=OPERATIONAL_STDERR_LIMIT,
        )
    _require(runner.count == EXECUTION_PLANNED_CHILDREN, "E_CONTROL_EXECUTION_INVALID")
  except RecipeError:
    raise
  except ControlError as error:
    raise RecipeError("E_CONTROL_EXECUTION_INVALID") from error
  return _collect_operational_outputs()


def _operational_json(raw: bytes) -> object:
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
    value = json.loads(
      raw.decode("ascii"), object_pairs_hook=unique_object,
      parse_constant=reject_constant,
    )
    canonical = (json.dumps(value, sort_keys=True, allow_nan=False) + "\n").encode("ascii")
  except (UnicodeError, ValueError, TypeError, RecursionError):
    raise RecipeError("E_CONTROL_OPERATIONAL_INVALID") from None
  _require(raw == canonical, "E_CONTROL_OPERATIONAL_INVALID")
  return value


def _operational_tree_file_record(
  root: Path,
  name: str,
  state: TreeState,
  raw: bytes,
) -> dict[str, object]:
  _require(type(name) is str and name in state.files, "E_CONTROL_OPERATIONAL_INVALID")
  value = state.files[name]
  _require(isinstance(value, FileState), "E_CONTROL_OPERATIONAL_INVALID")
  path = root / name
  _require(len(raw) == value.identity[6] and _sha256(raw) == value.sha256
           and _structural_identity(path.lstat()) == value.identity,
           "E_CONTROL_OPERATIONAL_INVALID")
  return {
    "path": str(path), "bytes": len(raw), "sha256": value.sha256,
    "identity": list(value.identity), "mode": stat.S_IMODE(value.identity[2]),
    "uid": value.identity[3], "gid": value.identity[4], "nlink": value.identity[5],
  }


def _validate_operational_records(
  context: OperationalContext,
  raw_files: RawControlFiles,
) -> tuple[dict[str, object], ...]:
  _require(raw_files.paths == SEMANTIC_OPERATIONAL_PATHS
           and len(raw_files.records) == EXECUTION_PLANNED_CHILDREN,
           "E_CONTROL_OPERATIONAL_INVALID")
  root = Path(OPERATIONAL_RECORD_ROOT)
  records: list[dict[str, object]] = []
  for index, command in enumerate(context.policy.commands):
    stdout, stderr, report_raw = raw_files.records[index]
    report = _operational_json(report_raw)
    _require(type(report) is dict and set(report) == OPERATIONAL_REPORT_KEYS,
             "E_CONTROL_OPERATIONAL_INVALID")
    retained = report["retained_bytes"]
    observed = report["observed_bytes"]
    _require(type(report["command"]) is list and report["command"] == list(command)
             and type(report["status"]) is str and report["status"] == "ok"
             and type(report["returncode"]) is int and report["returncode"] == 0
             and type(report["stdout"]) is str
             and report["stdout"] == f"child-{index:03d}.stdout"
             and type(report["stderr"]) is str
             and report["stderr"] == f"child-{index:03d}.stderr"
             and type(retained) is list and len(retained) == 2
             and all(type(value) is int and value >= 0 for value in retained)
             and type(observed) is list and observed == retained
             and retained == [len(stdout), len(stderr)]
             and len(stdout) <= OPERATIONAL_STDOUT_LIMITS[index]
             and len(stderr) == 0 and stderr == b""
             and type(report["elapsed_seconds"]) is float
             and math.isfinite(report["elapsed_seconds"])
             and 0 <= report["elapsed_seconds"] <= EXECUTION_CHILD_SECONDS
             and type(report["pid"]) is int and report["pid"] > 0
             and type(report["killed"]) is bool and report["killed"] is False
             and type(report["reaped"]) is bool and report["reaped"] is True,
             "E_CONTROL_OPERATIONAL_INVALID")
    if index == 4:
      _require(report["stdin_sha256"] == MAIN_SHA256
               and type(report["stdin_sha256"]) is str
               and type(report["stdin_bytes"]) is int
               and report["stdin_bytes"] == MAIN_BYTES,
               "E_CONTROL_OPERATIONAL_INVALID")
    else:
      _require(report["stdin_sha256"] is None
               and type(report["stdin_bytes"]) is int
               and report["stdin_bytes"] == 0,
               "E_CONTROL_OPERATIONAL_INVALID")
    stdout_name = f"child-{index:03d}.stdout"
    stderr_name = f"child-{index:03d}.stderr"
    report_name = f"child-{index:03d}.json"
    records.append({
      "index": index,
      "command": list(command),
      "report": report,
      "stdout": _operational_tree_file_record(
        root, stdout_name, raw_files.record_state, stdout,
      ),
      "stderr": _operational_tree_file_record(
        root, stderr_name, raw_files.record_state, stderr,
      ),
      "record": _operational_tree_file_record(
        root, report_name, raw_files.record_state, report_raw,
      ),
    })
  _require(len(records) == EXECUTION_PLANNED_CHILDREN,
           "E_CONTROL_OPERATIONAL_INVALID")
  return tuple(records)


def _read_operational_generated_indexes(raw_files: RawControlFiles) -> dict[str, bytes]:
  root = Path(CONTROL_ROOT) / "lib/modules" / KERNEL
  generated: dict[str, bytes] = {}
  for name in sorted(GENERATED_SHA256):
    path = root / name
    expected_size = HISTORICAL_BYTES[name]
    raw = _read_bounded_operational_file(path, max(1, expected_size))
    _require(len(raw) == expected_size and _sha256(raw) == GENERATED_SHA256[name]
             and raw_files.control_state.files[str(path.relative_to(CONTROL_ROOT))].sha256
             == GENERATED_SHA256[name], "E_CONTROL_OPERATIONAL_INVALID")
    generated[name] = raw
  return generated


def _validate_operational_roots(
  context: OperationalContext,
  raw_files: RawControlFiles,
) -> None:
  generated_names = {
    f"lib/modules/{KERNEL}/{name}" for name in GENERATED_SHA256
  }
  _require(context.control_before.directories == raw_files.control_state.directories
           and len(context.control_before.files) == 203
           and len(raw_files.control_state.files) == OPERATIONAL_CONTROL_TREE_FILES
           and set(raw_files.control_state.files)
           == set(context.control_before.files) | generated_names
           and all(raw_files.control_state.files.get(name) == value
                   for name, value in context.control_before.files.items()),
           "E_CONTROL_OPERATIONAL_INVALID")
  _require(raw_files.lookup_state == context.lookup_before
           and len(raw_files.lookup_state.files) == OPERATIONAL_LOOKUP_TREE_FILES,
           "E_CONTROL_OPERATIONAL_INVALID")


def _operational_lookup_target(raw: bytes, query: str) -> str:
  try:
    lines = raw.decode("ascii").splitlines()
  except UnicodeError:
    raise RecipeError("E_CONTROL_OPERATIONAL_INVALID") from None
  _require(bool(lines) and lines[0].startswith("# "), "E_CONTROL_OPERATIONAL_INVALID")
  matches: list[str] = []
  for line in lines[1:]:
    parts = line.split(" ")
    _require(len(parts) == 3 and parts[0] == "alias"
             and re.fullmatch(r"[A-Za-z0-9_]{1,128}", parts[2]) is not None,
             "E_CONTROL_OPERATIONAL_INVALID")
    if fnmatchcase(query, parts[1]):
      matches.append(parts[2])
  _require(len(matches) == 1, "E_CONTROL_OPERATIONAL_INVALID")
  return matches[0]


def _validate_operational_semantics(
  context: OperationalContext,
  raw_files: RawControlFiles,
  records: tuple[dict[str, object], ...],
) -> OperationalEvaluation:
  _validate_operational_roots(context, raw_files)
  for label, index in (
    ("early-cpio", 0), ("early-bsdtar", 1),
    ("main-cpio", 2), ("main-bsdtar", 3), ("gzip", 4),
  ):
    _validate_archive_observation(label, raw_files.records[index][0])
  _require(len(raw_files.early_raw + raw_files.records[4][0]) == E_BYTES
           and _sha256(raw_files.early_raw + raw_files.records[4][0]) == E_SHA256,
           "E_CONTROL_OPERATIONAL_INVALID")
  for index, name in enumerate(PAYLOAD_SHA256, start=5):
    _validate_payload_observation(name, raw_files.records[index][0])
  _require(raw_files.records[9][0] == b""
           and all(len(raw_files.records[index][1]) == 0 for index in range(424)),
           "E_CONTROL_OPERATIONAL_INVALID")

  generated = _read_operational_generated_indexes(raw_files)
  regeneration = validate_regeneration(
    context.selection.indexes, generated, raw_files.records[10][0], context.names,
  )
  _require(len(raw_files.records[10][0]) == len(raw_files.records[11][0]) == DUMP_BYTES
           and _sha256(raw_files.records[10][0]) == DUMP_SHA256
           and _sha256(raw_files.records[11][0]) == DUMP_SHA256,
           "E_CONTROL_OPERATIONAL_INVALID")

  module_lookups: list[dict[str, object]] = []
  dependency_outputs: dict[str, bytes] = {}
  for ordinal, name in enumerate(sorted(context.names)):
    filename_raw = raw_files.records[12 + ordinal * 2][0]
    dependency_raw = raw_files.records[13 + ordinal * 2][0]
    try:
      lookup = ordered_lookup(
        dependency_raw, name, context.names, regeneration.dependencies,
        context.builtins,
      )
    except ControlError as error:
      raise RecipeError("E_CONTROL_OPERATIONAL_INVALID") from error
    _require(filename_raw == (lookup.filename + "\n").encode("ascii"),
             "E_CONTROL_OPERATIONAL_INVALID")
    dependency_outputs[name] = dependency_raw
    module_lookups.append({
      "name": name,
      "filename_sha256": _sha256(filename_raw),
      "dependency_sha256": _sha256(dependency_raw),
      "filename": lookup.filename,
      "insmod": list(lookup.insmod),
      "builtin": list(lookup.builtin),
    })

  alias_lookups: list[dict[str, object]] = []
  for ordinal, alias in enumerate(ALIASES):
    target = _operational_lookup_target(generated["modules.alias"], alias)
    raw = raw_files.records[412 + ordinal][0]
    _require(raw == dependency_outputs[target], "E_CONTROL_OPERATIONAL_INVALID")
    alias_lookups.append({
      "query": alias, "target": target, "sha256": _sha256(raw),
    })

  symbol_lookups: list[dict[str, object]] = []
  for ordinal, symbol in enumerate(EXPORTS):
    query = "symbol:" + symbol
    target = _operational_lookup_target(generated["modules.symbols"], query)
    raw = raw_files.records[415 + ordinal][0]
    _require(raw == dependency_outputs[target], "E_CONTROL_OPERATIONAL_INVALID")
    symbol_lookups.append({
      "query": query, "target": target, "sha256": _sha256(raw),
    })
  _require(len(module_lookups) == 200 and len(alias_lookups) == 3
           and len(symbol_lookups) == 9 and len(records) == 424,
           "E_CONTROL_OPERATIONAL_INVALID")
  return OperationalEvaluation(
    records, generated, regeneration, tuple(module_lookups),
    tuple(alias_lookups), tuple(symbol_lookups),
  )


def _operational_input_records(
  inputs: OperationalInputSnapshot,
) -> tuple[dict[str, object], ...]:
  records: list[dict[str, object]] = []
  for path, raw, identity in inputs.files:
    records.append({
      "kind": "file", "path": path, "bytes": len(raw), "sha256": _sha256(raw),
      "identity": list(identity), "mode": stat.S_IMODE(identity[2]),
      "uid": identity[3], "gid": identity[4], "nlink": identity[5],
    })
  for path, identity, members in inputs.directories:
    records.append({
      "kind": "directory", "path": path, "identity": list(identity),
      "mode": stat.S_IMODE(identity[2]), "uid": identity[3], "gid": identity[4],
      "members": list(members),
    })
  return tuple(records)


def _operational_full_tree_identities(
  root: Path,
  state: TreeState,
) -> tuple[tuple[str, tuple[int, ...]], ...]:
  records: list[tuple[str, tuple[int, ...]]] = []
  for relative in sorted(state.directories):
    path = root if relative == "." else root / relative
    identity = _structural_identity(path.lstat())
    expected = state.directories[relative]
    _require(identity[:5] == expected, "E_CONTROL_OPERATIONAL_INVALID")
    records.append((str(path), identity))
  for relative in sorted(state.files):
    path = root / relative
    value = state.files[relative]
    _require(isinstance(value, FileState)
             and _structural_identity(path.lstat()) == value.identity,
             "E_CONTROL_OPERATIONAL_INVALID")
    records.append((str(path), value.identity))
  return tuple(records)


def _operational_header_bytes() -> bytes:
  value = {
    "schema": 1,
    "kind": "dev147-t1-e-control-v1",
    "base_sha256": E_SHA256,
    "base_bytes": E_BYTES,
    "early_records": 7,
    "early_bytes": EARLY_BYTES,
    "early_sha256": EARLY_SHA256,
    "main_records": 1163,
    "main_bytes": MAIN_BYTES,
    "main_sha256": MAIN_SHA256,
    "module_count": 200,
    "no_change_archive": True,
    "gzip_exact": True,
    "binary_only_lookup": True,
    "module_loaded": False,
    "image_staged": False,
    "indexes": INDEX_SHA256,
  }
  return _semantic_json_bytes(value)


def _operational_evidence_bytes(
  context: OperationalContext,
  raw_files: RawControlFiles,
  evaluation: OperationalEvaluation,
) -> bytes:
  value = {
    "schema": 2,
    "kind": "dev147-e-control-operational-evidence-v2",
    "status": "PASS",
    "mode": EXECUTION_MODE,
    "offline_no_change": True,
    "bindings": list(EXECUTION_TASK_BINDINGS),
    "read_only_mounts": EXECUTION_READ_ONLY_MOUNTS,
    "recipe_sha256": _sha256(
      _operational_input_bytes(context.inputs, "/inputs/recipe"),
    ),
    "inputs": list(_operational_input_records(context.inputs)),
    "planned_commands": [list(command) for command in context.policy.commands],
    "observed_commands": [record["command"] for record in evaluation.records],
    "children_root": OPERATIONAL_RECORD_ROOT,
    "planned_children": EXECUTION_PLANNED_CHILDREN,
    "children_executed": EXECUTION_PLANNED_CHILDREN,
    "record_files": OPERATIONAL_RECORD_FILES,
    "records": list(evaluation.records),
    "control_before": _semantic_stable_tree(Path(CONTROL_ROOT), context.control_before),
    "control_after": _semantic_stable_tree(Path(CONTROL_ROOT), raw_files.control_state),
    "lookup_before": _semantic_stable_tree(Path(LOOKUP_ROOT), context.lookup_before),
    "lookup_after": _semantic_stable_tree(Path(LOOKUP_ROOT), raw_files.lookup_state),
    "generated_indexes": {
      name: {"bytes": len(raw), "sha256": _sha256(raw)}
      for name, raw in sorted(evaluation.generated.items())
    },
    "retained_indexes": {
      name: {"bytes": len(raw), "sha256": _sha256(raw)}
      for name, raw in sorted(context.selection.indexes.items())
    },
    "retained_symbol_sha256": evaluation.regeneration.retained_symbol_sha256,
    "generated_symbol_sha256": evaluation.regeneration.generated_symbol_sha256,
    "alias_mappings": evaluation.regeneration.alias_mappings,
    "symbol_mappings": evaluation.regeneration.symbol_mappings,
    "module_lookups": list(evaluation.module_lookups),
    "alias_lookups": list(evaluation.alias_lookups),
    "symbol_lookups": list(evaluation.symbol_lookups),
    "historical_generated_inputs": [],
    "candidate_module_bound": False,
    "operational_control_proved": True,
    "fresh_control_proved": True,
    "image_created": False,
    "module_loaded": False,
    "staged": False,
    "booted": False,
  }
  raw = _semantic_json_bytes(value)
  _require(len(raw) <= OPERATIONAL_EVIDENCE_LIMIT, "E_CONTROL_OPERATIONAL_INVALID")
  return raw


def _operational_result_bytes(
  header_record: tuple[str, bytes, tuple[int, ...]],
  evidence_record: tuple[str, bytes, tuple[int, ...]],
  evaluation: OperationalEvaluation,
) -> bytes:
  def file_record(value: tuple[str, bytes, tuple[int, ...]]) -> dict[str, object]:
    path, raw, identity = value
    return {
      "path": path, "bytes": len(raw), "sha256": _sha256(raw),
      "identity": list(identity), "mode": stat.S_IMODE(identity[2]),
      "uid": identity[3], "gid": identity[4], "nlink": identity[5],
    }

  children = tuple({
    "index": record["index"],
    "stdout": record["stdout"],
    "stderr": record["stderr"],
    "record": record["record"],
  } for record in evaluation.records)
  value = {
    "schema": 2,
    "kind": "dev147-e-control-result-v2",
    "status": "PASS",
    "mode": EXECUTION_MODE,
    "offline_no_change": True,
    "bindings": list(EXECUTION_TASK_BINDINGS),
    "read_only_mounts": EXECUTION_READ_ONLY_MOUNTS,
    "planned_children": EXECUTION_PLANNED_CHILDREN,
    "children_executed": EXECUTION_PLANNED_CHILDREN,
    "record_files": OPERATIONAL_RECORD_FILES,
    "children_root": OPERATIONAL_RECORD_ROOT,
    "children": list(children),
    "header": file_record(header_record),
    "evidence": file_record(evidence_record),
    "historical_generated_inputs": [],
    "candidate_module_bound": False,
    "operational_control_proved": True,
    "fresh_control_proved": True,
    "image_created": False,
    "module_loaded": False,
    "staged": False,
    "booted": False,
  }
  raw = _semantic_json_bytes(value)
  _require(len(raw) <= OPERATIONAL_EVIDENCE_LIMIT, "E_CONTROL_OPERATIONAL_INVALID")
  return raw


def _finalize_executed_operational_result(
  context: OperationalContext,
  raw_files: RawControlFiles,
  evaluation: OperationalEvaluation,
) -> OperationalAcceptance:
  header_path, evidence_path, result_path = map(Path, OPERATIONAL_ARTIFACTS)
  pending_path = Path(OPERATIONAL_RESULT_PENDING)
  _require(not any(path.exists() or path.is_symlink()
                   for path in (header_path, evidence_path, pending_path, result_path)),
           "E_CONTROL_OUTPUT_EXISTS")
  header_raw = _operational_header_bytes()
  evidence_raw = _operational_evidence_bytes(context, raw_files, evaluation)
  write_new(header_path, header_raw)
  write_new(evidence_path, evidence_raw)
  header_record = _capture_operational_materialized_file(header_path, header_raw)
  evidence_record = _capture_operational_materialized_file(evidence_path, evidence_raw)

  tree_identities = (
    _operational_full_tree_identities(Path(OPERATIONAL_RECORD_ROOT), raw_files.record_state),
    _operational_full_tree_identities(Path(CONTROL_ROOT), raw_files.control_state),
    _operational_full_tree_identities(Path(LOOKUP_ROOT), raw_files.lookup_state),
  )
  _require(_capture_operational_inputs() == context.inputs, "E_CONTROL_INPUT_CHANGED")
  for path, expected, identity in context.materialized_files:
    _require(_capture_operational_materialized_file(Path(path), expected)
             == (path, expected, identity), "E_CONTROL_WORK_CHANGED")
  final_raw_files = _collect_operational_outputs()
  _require(final_raw_files == raw_files, "E_CONTROL_WORK_CHANGED")
  _require((
    _operational_full_tree_identities(
      Path(OPERATIONAL_RECORD_ROOT), final_raw_files.record_state,
    ),
    _operational_full_tree_identities(Path(CONTROL_ROOT), final_raw_files.control_state),
    _operational_full_tree_identities(Path(LOOKUP_ROOT), final_raw_files.lookup_state),
  ) == tree_identities, "E_CONTROL_WORK_CHANGED")
  expected_work = OPERATIONAL_INITIAL_WORK_MEMBERS | frozenset((
    Path(OPERATIONAL_RECORD_ROOT).name, Path(CONTROL_ROOT).name, Path(LOOKUP_ROOT).name,
    Path(EMPTY_CONFIG).name, Path(EARLY_PATH).name, Path(MAIN_PATH).name,
    header_path.name, evidence_path.name,
  ))
  _require(_operational_work_membership() == expected_work
           and not any(path.exists() or path.is_symlink()
                       for path in (pending_path, result_path)),
           "E_CONTROL_WORK_CHANGED")
  _require(_capture_operational_materialized_file(header_path, header_raw) == header_record
           and _capture_operational_materialized_file(evidence_path, evidence_raw)
           == evidence_record, "E_CONTROL_WORK_CHANGED")

  result_raw = _operational_result_bytes(header_record, evidence_record, evaluation)
  acceptance = OperationalAcceptance(
    status="PASS",
    mode=EXECUTION_MODE,
    header_sha256=_sha256(header_raw),
    evidence_sha256=_sha256(evidence_raw),
    result_sha256=_sha256(result_raw),
    planned_children=EXECUTION_PLANNED_CHILDREN,
    children_executed=EXECUTION_PLANNED_CHILDREN,
    operational_control_proved=True,
    fresh_control_proved=True,
    image_created=False,
    module_loaded=False,
    staged=False,
    booted=False,
  )
  write_new(pending_path, result_raw)
  _require(
    _capture_operational_materialized_file(pending_path, result_raw)
    == (str(pending_path), result_raw, _structural_identity(pending_path.lstat()))
    and not (result_path.exists() or result_path.is_symlink()),
    "E_CONTROL_WORK_CHANGED",
  )
  _rename_noreplace(pending_path, result_path)
  return acceptance


def _run_operational_control() -> OperationalAcceptance:
  context = _materialize_operational_context()
  raw_files = _run_operational_commands(context)
  records = _validate_operational_records(context, raw_files)
  evaluation = _validate_operational_semantics(context, raw_files, records)
  return _finalize_executed_operational_result(context, raw_files, evaluation)


def operational_policy() -> OperationalPolicy:
  """Return the sole authenticated eight-input operational policy; run nothing."""
  inputs = _capture_operational_inputs()
  policy, _selection, _names, _builtins = _operational_policy_from_inputs(inputs)
  return policy


def finalize_operational_result() -> NoReturn:
  """Refuse direct publication outside the fixed execute-and-validate sequence."""
  raise RecipeError("E_CONTROL_DIRECT_FINALIZE_UNAVAILABLE")


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
      if command == ("/usr/bin/gzip", "-n"):
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


def main() -> None:
  """Run the one fixed offline E no-change control in the reviewed sandbox."""
  _run_operational_control()


if __name__ == "__main__":
  main()
