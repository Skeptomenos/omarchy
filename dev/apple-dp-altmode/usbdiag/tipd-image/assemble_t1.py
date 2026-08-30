"""One fixed private E-to-T1 assembly; never an installer or module loader.

The v5 launcher authenticates this recipe and its read-only bindings. This
entry authenticates the complete E proof, T1 build proof, module and source
bytes before use. Six bounded offline children describe/compress the fixed
combination. No index is generated. The result is published last. Failures
retain their files; there is no cleanup, override, fallback or retry.
"""

from contextlib import ExitStack
from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
from types import ModuleType
from typing import Any


KERNEL = "7.1.6-1-1-ARCH"
TIPD = f"usr/lib/modules/{KERNEL}/kernel/drivers/usb/typec/tipd/tps6598x-core.ko"
T1_MODULE_SHA256 = "a0fdadc351261643545e5afd8561923be99431661c447084336c9318f5b0c02f"
T1_MODULE_BYTES = 1327920
T1_BUILD_ID = "40aa54382047ba36b02c9ac0da65a213862a77ad"
T1_SOURCE_SHA256 = "215051ed006431c73f2e402e5a1d503daaa41dc9d4b9e2bb66a82ac868892a92"
T1_BUILD_PROOF_SHA256 = "95abe335e44a5f30781a1e80f3e26efc314746b5d6baf11bae658f4484d9ada3"
E_SHA256 = "4d4f0557af57eebcc33322f004bcc7968254e644b069a11102375df0b31a52ae"
E_BYTES = 19191513
E_HEADER_SHA256 = "1665fe5a0d5d58eb3fa029faaea066da5c4b026415d19c33d644c5ec0b44f96a"
E_EVIDENCE_SHA256 = "6bbbb024d616bfa767dfe71b4a6121a1e75233bb1a1c8bc47b81b93f28628709"
E_RESULT_SHA256 = "5e08a383469bd65d402939d0b7ca9cef9c2febb77ca12de1d577454b0d2de8f2"
E_RECIPE_SHA256 = "1be81904b29c69cb24fae86208c62fb30e830eca46250978a65d8ed19db8de77"
CANDIDATE = Path("/work/initramfs-linux-asahi-dpalt-tipddiag1.img")
RESULT = Path("/work/t1-assembly-result.json")
LOOKUP_ROOT = Path("/work/t1-lookup-root")
EMPTY_CONFIG = Path("/work/t1-empty-modprobe.conf")
RECIPE = Path("/inputs/recipe")
CONTRACT = Path("/inputs/contract/image_contract.py")
ASSEMBLY = Path("/inputs/assembly/prepare_image.py")
CONTROL = Path("/inputs/control/verify_control.py")
HELPER = Path("/inputs/helper/cpio_image.py")
BASE = Path("/inputs/base")
MODULE = Path("/inputs/module")
BUILD_PROOF = Path("/inputs/build-proof")
E_PROOF = Path("/inputs/e-proof")
SOURCE_PINS = {
  CONTRACT: "a1eda280aa56967aa06b01a2cca0dfc70c3da6df25066f8a1e815beec719f1bf",
  ASSEMBLY: "00caceb3b7fa236dcc030fb4007d0baa75bfa08fcd1590626f85fcc8c22d5f60",
  CONTROL: "10b5afe6cff38df7b6ebe5619fd9a34935932a4b369f3a9ad2a51923c32932d8",
  HELPER: "a32eddd159263d19ff87d7e9caee9d53d17ef5c350fbffe9e7eb142cb43ebf58",
}
DATA_PINS = {
  BASE: (E_SHA256, E_BYTES), MODULE: (T1_MODULE_SHA256, T1_MODULE_BYTES),
  BUILD_PROOF: (T1_BUILD_PROOF_SHA256, None),
  E_PROOF / "e-control-header.json": (E_HEADER_SHA256, 1149),
  E_PROOF / "e-control-evidence.json": (E_EVIDENCE_SHA256, 965657),
  E_PROOF / "e-control-result.json": (E_RESULT_SHA256, 366381),
}
E_BINDINGS = [
  "/inputs/recipe", "/inputs/subject", "/inputs/contract", "/inputs/assembly",
  "/inputs/control", "/inputs/helper", "/inputs/base", "/inputs/index-inputs",
]
MODULE_DIRECTORY = f"lib/modules/{KERNEL}/"
ARCHIVE_PREFIX = f"usr/{MODULE_DIRECTORY}"
TIPD_RELATIVE = "kernel/drivers/usb/typec/tipd/tps6598x-core.ko"
TYPEC_RELATIVE = "kernel/drivers/usb/typec/typec.ko"
EMPTY_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
INITIAL_WORK = frozenset(("descriptor-sentinel", "probe-write", "stdout.log", "stderr.log"))


class AssemblyError(RuntimeError):
  """The fixed T1 assembly contract does not hold."""


@dataclass(frozen=True)
class AssemblyPolicy:
  bindings: tuple[str, ...]
  candidate: str
  result: str
  lookup_root: str
  commands: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class ValidatedInputs:
  base_sha256: str
  module_sha256: str
  module_bytes: int
  build_id: str
  e_result_sha256: str
  early_records: int
  main_records: int


@dataclass(frozen=True)
class _Input:
  raw: bytes
  identity: tuple[int, ...]


def _require(condition: bool, code: str) -> None:
  if not condition:
    raise AssemblyError(code)


def _sha256(raw: bytes) -> str:
  return hashlib.sha256(raw).hexdigest()


def _identity(info: os.stat_result) -> tuple[int, ...]:
  return (info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_gid,
          info.st_nlink, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def _directory_identity(info: os.stat_result) -> tuple[int, ...]:
  _require(stat.S_ISDIR(info.st_mode), "T1_INPUT_INVALID")
  return (info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_gid)


def _read(path: Path, digest: str | None, bound: int) -> _Input:
  """Walk every parent without following links; retain content and identity."""
  _require(path.is_absolute() and all(part not in (".", "..") for part in path.parts),
           "T1_INPUT_INVALID")
  with ExitStack() as stack:
    directories: list[int] = []
    states: list[tuple[int, ...]] = []
    for part in ("/", *path.parts[1:-1]):
      parent = directories[-1] if directories else None
      descriptor = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                           dir_fd=parent)
      stack.callback(os.close, descriptor)
      directories.append(descriptor)
      states.append(_directory_identity(os.fstat(descriptor)))
    parent = directories[-1]
    before = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
    _require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1
             and before.st_uid == before.st_gid == 1001 and 0 < before.st_size <= bound,
             "T1_INPUT_INVALID")
    descriptor = os.open(path.name, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC,
                         dir_fd=parent)
    stack.callback(os.close, descriptor)
    _require(_identity(os.fstat(descriptor)) == _identity(before), "T1_INPUT_CHANGED")
    chunks: list[bytes] = []
    remaining = before.st_size
    while remaining:
      chunk = os.read(descriptor, min(remaining, 1024 * 1024))
      _require(bool(chunk), "T1_INPUT_CHANGED")
      chunks.append(chunk)
      remaining -= len(chunk)
    _require(not os.read(descriptor, 1) and _identity(os.fstat(descriptor)) == _identity(before)
             == _identity(os.stat(path.name, dir_fd=parent, follow_symlinks=False)),
             "T1_INPUT_CHANGED")
    for index, directory in enumerate(directories):
      named = os.stat("/", follow_symlinks=False) if index == 0 else os.stat(
        path.parts[index], dir_fd=directories[index - 1], follow_symlinks=False)
      _require(_directory_identity(os.fstat(directory)) == states[index]
               == _directory_identity(named), "T1_INPUT_CHANGED")
    raw = b"".join(chunks)
    _require(digest is None or _sha256(raw) == digest, "T1_INPUT_IDENTITY")
    return _Input(raw, _identity(before))


def _load(name: str, path: Path, raw: bytes) -> ModuleType:
  _require(name not in sys.modules, "T1_SOURCE_PRELOADED")
  module = ModuleType(name)
  module.__file__ = str(path)
  sys.modules[name] = module
  exec(compile(raw, str(path), "exec"), module.__dict__)
  return module


def _bootstrap() -> tuple[ModuleType, ModuleType, ModuleType, ModuleType]:
  _require(sys.version_info[:2] == (3, 14) and sys.flags.isolated == 1
           and sys.flags.no_site == 1 and sys.dont_write_bytecode,
           "T1_ISOLATION_REQUIRED")
  _require(os.getuid() == os.geteuid() == os.getgid() == 1001 and Path.cwd() == Path("/work"),
           "T1_ISOLATION_REQUIRED")
  _require(not any(Path(path).exists() for path in ("/proc", "/sys", "/run", "/home", "/root", "/boot")),
           "T1_ISOLATION_REQUIRED")
  # All source bytes authenticate before the first source executes. The old
  # assembly module's import then independently authenticates control/helper.
  inputs = {path: _read(path, digest, 256 * 1024) for path, digest in SOURCE_PINS.items()}
  for path in SOURCE_PINS:
    _require({entry.name for entry in path.parent.iterdir()} == {path.name}, "T1_SOURCE_LAYOUT")
  before_modules = dict(sys.modules)
  before_path = sys.path[:]
  try:
    prepared = _load("prepare_image", ASSEMBLY, inputs[ASSEMBLY].raw)
    image = _load("image_contract", CONTRACT, inputs[CONTRACT].raw)
    checked = sys.modules["verify_control"]
    cpio = sys.modules["cpio_image"]
    _require(checked.__file__ == str(CONTROL) and cpio.__file__ == str(HELPER), "T1_SOURCE_LAYOUT")
    for path, value in inputs.items():
      _require(_read(path, SOURCE_PINS[path], 256 * 1024) == value, "T1_INPUT_CHANGED")
    return cpio, checked, prepared, image
  except BaseException:
    sys.modules.clear()
    sys.modules.update(before_modules)
    raise
  finally:
    sys.path[:] = before_path


helper, control, assembly, contract = _bootstrap()


def assembly_policy() -> AssemblyPolicy:
  """The only operational bindings, outputs and child commands."""
  return AssemblyPolicy((
    "/inputs/recipe", "/inputs/contract", "/inputs/assembly", "/inputs/control",
    "/inputs/helper", "/inputs/base", "/inputs/module", "/inputs/build-proof", "/inputs/e-proof",
  ), str(CANDIDATE), str(RESULT), str(LOOKUP_ROOT), (
    ("/usr/bin/gzip", "-n"),
    ("/usr/bin/readelf", "-n", "/inputs/module"),
    ("/usr/bin/modinfo", "-b", "/work/t1-lookup-root", "-k", KERNEL, "-F", "filename", "tps6598x_core"),
    ("/usr/bin/modinfo", "-b", "/work/t1-lookup-root", "-k", KERNEL, "-F", "name", "tps6598x_core"),
    ("/usr/bin/modinfo", "-b", "/work/t1-lookup-root", "-k", KERNEL, "-F", "depends", "tps6598x_core"),
    ("/usr/bin/modprobe", "--dry-run", "--show-depends", "-d", "/work/t1-lookup-root",
     "-S", KERNEL, "-C", "/work/t1-empty-modprobe.conf", "tps6598x_core"),
  ))


def _json(raw: bytes, code: str) -> dict[str, Any]:
  _require(type(raw) is bytes and 0 < len(raw) <= 2 * 1024 * 1024, code)
  def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
      _require(key not in result, code)
      result[key] = value
    return result
  def invalid(value: str) -> None:
    raise AssemblyError(code)
  try:
    value = json.loads(raw.decode("ascii"), object_pairs_hook=unique, parse_constant=invalid)
  except (ValueError, RecursionError):
    raise AssemblyError(code) from None
  _require(type(value) is dict, code)
  return value


def _same(actual: object, expected: object, code: str) -> None:
  _require(json.dumps(actual, sort_keys=True, allow_nan=False) ==
           json.dumps(expected, sort_keys=True, allow_nan=False), code)


def _validate_build_proof(raw: bytes) -> None:
  code = "T1_BUILD_PROOF_INVALID"
  _require(type(raw) is bytes and _sha256(raw) == T1_BUILD_PROOF_SHA256, code)
  value = _json(raw, code)
  _require(set(value) == set((
    "build_id", "command", "date", "export_sections", "first_run", "module_btf_base_sha256",
    "module_sha256", "module_size", "output_pins", "recipe_sha256", "result", "reviews",
    "run", "schema", "scope", "seal", "source_sha256", "table_review",
  )), code)
  for name, expected in {
    "schema": "dev147-t1-private-build1", "source_sha256": T1_SOURCE_SHA256,
    "module_sha256": T1_MODULE_SHA256, "module_size": T1_MODULE_BYTES, "build_id": T1_BUILD_ID,
    "recipe_sha256": "53eaf3cd984d9a45ae007649f2070e579fdcde65de789e270ce7b9886190bad0",
  }.items():
    _same(value[name], expected, code)
  result = value["result"]
  _require(type(result) is dict and set(result) == set((
    "exit_code", "timed_out", "inputs_unchanged", "stderr_bytes", "readonly_bindings", "smokes",
    "isolated", "reproducibility", "original_strong_imports", "candidate_strong_imports",
    "added_imports", "added_import_origin", "depends", "common_dwarf_btf_layouts", "wrapper",
  )), code)
  for name, expected in {
    "exit_code": 0, "timed_out": False, "inputs_unchanged": True, "stderr_bytes": 0,
    "readonly_bindings": 592, "smokes": 7, "isolated": True, "original_strong_imports": 94,
    "candidate_strong_imports": 99, "depends": "typec",
    "added_imports": ["_printk", "of_machine_compatible_match", "of_find_node_opts_by_path",
                      "of_node_put", "alt_cb_patch_nops"],
    "common_dwarf_btf_layouts": {"tps6598x": 384, "cd321x": 680, "tipd_data": 120},
    "wrapper": {"size": 688, "cd321x": {"offset": 0, "size": 680},
                "generation": {"offset": 680, "size": 4}, "worker": {"offset": 684, "size": 4}},
  }.items():
    _same(result[name], expected, code)
  review = value["table_review"]
  _require(review["export_bindings_equal"] is True and review["export_relocation_rows"] == 27
           and [row["name"] for row in review["tables"]] == [
             "tipd_cd321x_data", "tipd_sn201202x_data", "tipd_tps25750_data", "tipd_tps6598x_data",
           ] and all(row["bindings_equal"] is True for row in review["tables"]), code)


def _validate_descriptor(value: object, path: str, digest: str | None = None,
                         size: int | None = None) -> None:
  code = "T1_E_PROOF_INVALID"
  _require(type(value) is dict and set(value) ==
           {"bytes", "gid", "identity", "mode", "nlink", "path", "sha256", "uid"}, code)
  _require(value["path"] == path and type(value["bytes"]) is int and 0 <= value["bytes"] <= 32 * 1024 * 1024
           and type(value["sha256"]) is str and re.fullmatch(r"[0-9a-f]{64}", value["sha256"]) is not None,
           code)
  for key, expected in {"mode": 0o600, "uid": 1001, "gid": 1001, "nlink": 1}.items():
    _same(value[key], expected, code)
  identity = value["identity"]
  _require(type(identity) is list and len(identity) == 9 and all(type(item) is int for item in identity)
           and identity[0] > 0 and identity[1] > 0 and identity[2:7] ==
           [stat.S_IFREG | 0o600, 1001, 1001, 1, value["bytes"]], code)
  _require((digest is None or value["sha256"] == digest) and (size is None or value["bytes"] == size), code)


def _validate_e_proof(header_raw: bytes, evidence_raw: bytes, result_raw: bytes) -> None:
  code = "T1_E_PROOF_INVALID"
  _require(all(type(raw) is bytes and _sha256(raw) == digest for raw, digest in (
    (header_raw, E_HEADER_SHA256), (evidence_raw, E_EVIDENCE_SHA256), (result_raw, E_RESULT_SHA256),
  )), code)
  contract.validate_e_control_header(header_raw)
  evidence, result = _json(evidence_raw, code), _json(result_raw, code)
  common = {
    "schema": 2, "status": "PASS", "mode": "E_NO_CHANGE_OFFLINE", "bindings": E_BINDINGS,
    "children_executed": 424, "planned_children": 424, "record_files": 1272,
    "read_only_mounts": 593, "historical_generated_inputs": [],
    "children_root": "/work/e-control-children-e1", "offline_no_change": True,
    "operational_control_proved": True, "fresh_control_proved": True, "image_created": False,
    "candidate_module_bound": False, "module_loaded": False, "staged": False, "booted": False,
  }
  _require(set(result) == set(common) | {"kind", "children", "header", "evidence"}, code)
  _require(set(evidence) == set(common) | {
    "kind", "recipe_sha256", "inputs", "planned_commands", "observed_commands", "records",
    "module_lookups", "alias_lookups", "symbol_lookups", "alias_mappings", "symbol_mappings",
    "retained_indexes", "generated_indexes", "retained_symbol_sha256", "generated_symbol_sha256",
    "control_before", "control_after", "lookup_before", "lookup_after",
  }, code)
  for value, kind in ((result, "dev147-e-control-result-v2"),
                       (evidence, "dev147-e-control-operational-evidence-v2")):
    _same(value["kind"], kind, code)
    for name, expected in common.items():
      _same(value[name], expected, code)
  _validate_descriptor(result["header"], "/work/e-control-header.json", E_HEADER_SHA256, len(header_raw))
  _validate_descriptor(result["evidence"], "/work/e-control-evidence.json", E_EVIDENCE_SHA256, len(evidence_raw))
  _require(evidence["recipe_sha256"] == E_RECIPE_SHA256 and evidence["alias_mappings"] == 1408
           and evidence["symbol_mappings"] == 596, code)
  for name, count in (("module_lookups", 200), ("alias_lookups", 3), ("symbol_lookups", 9),
                      ("planned_commands", 424), ("observed_commands", 424), ("records", 424), ("inputs", 17)):
    _require(type(evidence[name]) is list and len(evidence[name]) == count, code)
  _require(evidence["planned_commands"] == evidence["observed_commands"]
           and evidence["planned_commands"][4] == ["/usr/bin/gzip", "-n"]
           and type(result["children"]) is list and len(result["children"]) == 424, code)
  pids: set[int] = set()
  for index, (record, child, command) in enumerate(zip(
      evidence["records"], result["children"], evidence["planned_commands"], strict=True)):
    _require(type(record) is dict and set(record) == {"index", "command", "report", "record", "stdout", "stderr"}
             and type(child) is dict and set(child) == {"index", "record", "stdout", "stderr"}
             and record["index"] == child["index"] == index and record["command"] == command, code)
    for field, suffix in (("record", "json"), ("stdout", "stdout"), ("stderr", "stderr")):
      _same(record[field], child[field], code)
      _validate_descriptor(record[field], f"/work/e-control-children-e1/child-{index:03d}.{suffix}",
                           EMPTY_SHA256 if field == "stderr" else None, 0 if field == "stderr" else None)
    report = record["report"]
    _require(type(report) is dict and set(report) == {
      "command", "elapsed_seconds", "killed", "observed_bytes", "pid", "reaped", "retained_bytes",
      "returncode", "status", "stderr", "stdin_bytes", "stdin_sha256", "stdout",
    }, code)
    _require(report["command"] == command and report["status"] == "ok"
             and type(report["returncode"]) is int and report["returncode"] == 0
             and report["killed"] is False and report["reaped"] is True
             and type(report["pid"]) is int and report["pid"] > 0 and report["pid"] not in pids
             and report["observed_bytes"] == report["retained_bytes"] == [record["stdout"]["bytes"], 0]
             and report["stdout"] == f"child-{index:03d}.stdout"
             and report["stderr"] == f"child-{index:03d}.stderr", code)
    pids.add(report["pid"])
  _require(evidence["lookup_before"] == evidence["lookup_after"], code)
  _require(len(evidence["lookup_after"]["files"]) == 207
           and len(evidence["control_after"]["files"]) == 214, code)
  _require(set(evidence["retained_indexes"]) == set(contract.INDEX_SHA256), code)
  for name, digest in contract.INDEX_SHA256.items():
    value = evidence["retained_indexes"][name]
    _require(set(value) == {"bytes", "sha256"} and value["sha256"] == digest, code)
  _require(evidence["retained_symbol_sha256"] == contract.INDEX_SHA256["modules.symbols.bin"]
           and evidence["generated_symbol_sha256"] ==
           "5077fb001a5c48a2135ce8f651606b18578610bc660f430a59114e76be4f9437", code)


def _fixed_inputs() -> dict[Path, _Input]:
  result = {RECIPE: _read(RECIPE, None, 256 * 1024)}
  result.update({path: _read(path, digest, 256 * 1024) for path, digest in SOURCE_PINS.items()})
  for path, (digest, size) in DATA_PINS.items():
    value = _read(path, digest, 32 * 1024 * 1024 if path == BASE else 2 * 1024 * 1024)
    _require(size is None or len(value.raw) == size, "T1_INPUT_IDENTITY")
    result[path] = value
  return result


def _validated_archives(inputs: dict[Path, _Input]) -> tuple[Any, Any]:
  _validate_build_proof(inputs[BUILD_PROOF].raw)
  _validate_e_proof(*(inputs[E_PROOF / name].raw for name in (
    "e-control-header.json", "e-control-evidence.json", "e-control-result.json",
  )))
  base, module = inputs[BASE].raw, inputs[MODULE].raw
  contract.validate_e_base(base)
  _require(len(module) == T1_MODULE_BYTES and _sha256(module) == T1_MODULE_SHA256, "T1_MODULE_IDENTITY")
  early_raw = base[:contract.EARLY_BYTES]
  main_raw = assembly.single_gzip(base[contract.EARLY_BYTES:], contract.MAIN_BYTES)
  _require(_sha256(early_raw) == contract.EARLY_SHA256 and _sha256(main_raw) == contract.MAIN_SHA256,
           "T1_E_ARCHIVE_INVALID")
  early, main = helper.parse_newc(early_raw), helper.parse_newc(main_raw)
  _require(len(early.members) == 7 and len(main.members) == 1163, "T1_E_ARCHIVE_INVALID")
  indexes = control.select_indexes(main)
  _require({name: _sha256(raw) for name, raw in indexes.items()} == contract.INDEX_SHA256,
           "T1_E_ARCHIVE_INVALID")
  return early, main


def validate_fixed_inputs() -> ValidatedInputs:
  """Read and validate fixed real inputs without a child, output or assembly."""
  inputs = _fixed_inputs()
  early, main = _validated_archives(inputs)
  _require(_fixed_inputs() == inputs, "T1_INPUT_CHANGED")
  return ValidatedInputs(E_SHA256, T1_MODULE_SHA256, T1_MODULE_BYTES, T1_BUILD_ID,
                         E_RESULT_SHA256, len(early.members), len(main.members))


def _validate_build_id_output(raw: bytes) -> str:
  code = "T1_BUILD_ID_INVALID"
  _require(type(raw) is bytes and 0 < len(raw) <= 65536
           and raw.endswith(b"\n")
           and all(char in (9, 10) or 32 <= char <= 126 for char in raw), code)
  lines = [line for line in raw.splitlines() if b"Build ID:" in line]
  _require(lines == [b"    Build ID: " + T1_BUILD_ID.encode("ascii")], code)
  return T1_BUILD_ID


def _lookup_payloads(main: Any) -> dict[str, bytes]:
  modules = {member.name[len(ARCHIVE_PREFIX):]: member.payload for member in main.members
             if member.name.startswith(ARCHIVE_PREFIX) and member.name.endswith(".ko")
             and stat.S_ISREG(member.fields[1]) and member.fields[4] in (0, 1)}
  _require(len(modules) == 200 and TIPD_RELATIVE in modules and TYPEC_RELATIVE in modules
           and modules[TIPD_RELATIVE] and _sha256(modules[TIPD_RELATIVE]) == T1_MODULE_SHA256,
           "T1_LOOKUP_INVALID")
  indexes = control.select_indexes(main)
  _require({name: _sha256(raw) for name, raw in indexes.items()} == contract.INDEX_SHA256,
           "T1_LOOKUP_INVALID")
  return {MODULE_DIRECTORY + name: raw for name, raw in (modules | indexes).items()}


def _lookup_expected() -> tuple[bytes, bytes, bytes, bytes]:
  tipd = str(LOOKUP_ROOT / MODULE_DIRECTORY / TIPD_RELATIVE)
  typec = str(LOOKUP_ROOT / MODULE_DIRECTORY / TYPEC_RELATIVE)
  return ((tipd + "\n").encode("ascii"), b"tps6598x_core\n", b"typec\n",
          (f"insmod {typec} \ninsmod {tipd} \n").encode("ascii"))


def _validate_lookup_outputs(outputs: tuple[bytes, ...]) -> None:
  _require(type(outputs) is tuple and outputs == _lookup_expected()
           and all(type(raw) is bytes for raw in outputs), "T1_LOOKUP_INVALID")


def _private_lookup(main: Any) -> dict[str, _Input]:
  payloads = _lookup_payloads(main)
  LOOKUP_ROOT.mkdir(mode=0o700, exist_ok=False)
  for relative, raw in sorted(payloads.items()):
    path = LOOKUP_ROOT / relative
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    helper.write_new(path, raw)
  helper.write_new(EMPTY_CONFIG, b"")
  return _check_lookup(payloads)


def _check_lookup(payloads: dict[str, bytes]) -> dict[str, _Input]:
  expected_dirs = {"."}
  for relative in payloads:
    expected_dirs.update(str(parent) for parent in Path(relative).parents)
  files: dict[str, _Input] = {}
  directories: set[str] = set()
  for path in (LOOKUP_ROOT, *sorted(LOOKUP_ROOT.rglob("*"))):
    relative = str(path.relative_to(LOOKUP_ROOT))
    info = path.lstat()
    _require(info.st_uid == info.st_gid == 1001, "T1_LOOKUP_INVALID")
    if stat.S_ISDIR(info.st_mode):
      _require(stat.S_IMODE(info.st_mode) == 0o700, "T1_LOOKUP_INVALID")
      directories.add(relative)
    else:
      _require(relative in payloads and stat.S_IMODE(info.st_mode) == 0o600,
               "T1_LOOKUP_INVALID")
      raw = helper.read_regular(path, _sha256(payloads[relative]))
      _require(raw == payloads[relative], "T1_LOOKUP_INVALID")
      files[relative] = _Input(raw, _identity(info))
  _require(set(files) == set(payloads) and directories == expected_dirs, "T1_LOOKUP_INVALID")
  config = EMPTY_CONFIG.lstat()
  _require(config.st_mode == stat.S_IFREG | 0o600 and config.st_uid == config.st_gid == 1001
           and config.st_nlink == 1 and config.st_size == 0
           and helper.read_regular(EMPTY_CONFIG) == b""
           and _identity(EMPTY_CONFIG.lstat()) == _identity(config), "T1_LOOKUP_INVALID")
  files["@empty-config"] = _Input(b"", _identity(config))
  return files


def _publication_plan() -> tuple[str, ...]:
  """The exclusive image precedes the exclusive final result; no pending file."""
  return (str(CANDIDATE), str(RESULT))


def _run_fixed_assembly() -> None:
  _require(not sys.argv[1:] and Path(__file__) == RECIPE, "T1_FIXED_ENTRY_REQUIRED")
  policy = assembly_policy()
  _require({entry.name for entry in Path("/inputs").iterdir()} ==
           {Path(path).name for path in policy.bindings} | {"proof"}, "T1_FIXED_BINDINGS_REQUIRED")
  _require({entry.name for entry in Path("/work").iterdir()} == INITIAL_WORK, "T1_FRESH_WORK_REQUIRED")
  os.umask(0o077)
  inputs = _fixed_inputs()
  early, original = _validated_archives(inputs)
  module = inputs[MODULE].raw
  main_raw = helper.replace_members(original, {TIPD: module}, ())
  final_main = helper.parse_newc(main_raw)
  delta = contract.archive_delta(original, final_main, module)
  commands = control.Commands()
  compressed = commands.run(policy.commands[0], payload=main_raw, output_bound=32 * 1024 * 1024)
  _require(compressed[:8] == b"\x1f\x8b\x08\x00\x00\x00\x00\x00"
           and assembly.single_gzip(compressed, len(main_raw)) == main_raw, "T1_GZIP_INVALID")
  _validate_build_id_output(commands.run(policy.commands[1], output_bound=65536))
  lookup_before = _private_lookup(final_main)
  outputs = tuple(commands.run(command, output_bound=65536) for command in policy.commands[2:])
  _validate_lookup_outputs(outputs)
  _require(commands.count == 6 and _check_lookup(_lookup_payloads(final_main)) == lookup_before,
           "T1_LOOKUP_CHANGED")
  candidate = early.raw + compressed
  helper.write_new(CANDIDATE, candidate)
  readback = helper.read_regular(CANDIDATE, _sha256(candidate))
  _require(readback[:contract.EARLY_BYTES] == early.raw and helper.parse_newc(
    readback[:contract.EARLY_BYTES]) == early, "T1_READBACK_INVALID")
  readback_main = helper.parse_newc(assembly.single_gzip(readback[contract.EARLY_BYTES:], len(main_raw)))
  _require(readback_main.raw == main_raw and contract.archive_delta(original, readback_main, module) == delta,
           "T1_READBACK_INVALID")
  _require(_check_lookup(_lookup_payloads(readback_main)) == lookup_before, "T1_LOOKUP_CHANGED")
  _require(_fixed_inputs() == inputs, "T1_INPUT_CHANGED")
  expected_work = INITIAL_WORK | {CANDIDATE.name, LOOKUP_ROOT.name, EMPTY_CONFIG.name}
  expected_work |= {f"child-{index:03d}.{suffix}" for index in range(6)
                    for suffix in ("stdout", "stderr", "result.json")}
  _require({entry.name for entry in Path("/work").iterdir()} == expected_work, "T1_OUTPUT_MEMBERSHIP")
  result = {
    "schema": 1, "kind": "dev147-t1-assembly-result-v1", "status": "PASS", "offline": True,
    "image_created": True, "staged": False, "module_loaded": False, "rebooted": False,
    "boot_tested": False, "inputs_unchanged": True, "children_executed": 6,
    "bindings": policy.bindings, "commands": policy.commands, "archive_delta": asdict(delta),
    "early_records": 7, "main_records": 1163, "unchanged_indexes": contract.INDEX_SHA256,
    "lookup_files": 207, "lookup_outputs": [raw.decode("ascii") for raw in outputs],
    "build_id": T1_BUILD_ID, "build_proof_sha256": T1_BUILD_PROOF_SHA256,
    "e_header_sha256": E_HEADER_SHA256, "e_evidence_sha256": E_EVIDENCE_SHA256,
    "e_result_sha256": E_RESULT_SHA256, "e_recipe_sha256": E_RECIPE_SHA256,
    "inputs": {str(path): {"sha256": _sha256(value.raw), "bytes": len(value.raw),
                           "identity": value.identity} for path, value in inputs.items()},
    "candidate": {"path": str(CANDIDATE), "bytes": len(readback), "sha256": _sha256(readback),
                  "identity": _identity(CANDIDATE.lstat())},
  }
  # Exclusive publication is the last operation. Its absence is INCOMPLETE.
  helper.write_new(RESULT, (json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("ascii"))


def main() -> None:
  """No arguments, environment overrides or alternate assembly mode exist."""
  _run_fixed_assembly()


if __name__ == "__main__":
  main()
