"""Three zero-child RED checks for the fixed E raw-observation boundary.

Only the root task may run this file in the reviewed fresh sandbox. It creates
distinct fixture trees and complete raw output records for all 424 planned
commands. Nothing executes. Historical bytes and synthetic records cannot
prove a fresh depmod, lookup, gzip, image, load, stage, boot or hardware result.
"""

import ast
import copy
from fnmatch import fnmatchcase
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
from types import ModuleType
import unittest


TEST = Path("/inputs/test")
SUBJECT = Path("/inputs/recipe")
SUBJECT_SHA256 = "099be3713b7d7b40020de10ca38f0a943da3da60509acb153b2d3de390e44f1d"
ASSEMBLY = Path("/inputs/assembly/prepare_image.py")
CONTRACT = Path("/inputs/contract/image_contract.py")
COMMANDS = Path("/inputs/subject/e_control.py")
CONTROL = Path("/inputs/control/verify_control.py")
HELPER = Path("/inputs/helper/cpio_image.py")
BASE = Path("/inputs/base")
INDEX_DIRECTORY = Path("/inputs/index-inputs")
PROOF = Path("/inputs/proof")
E_SHA256 = "4d4f0557af57eebcc33322f004bcc7968254e644b069a11102375df0b31a52ae"
E_BYTES = 19191513
SOURCE_PINS = {
  SUBJECT: SUBJECT_SHA256,
  ASSEMBLY: "00caceb3b7fa236dcc030fb4007d0baa75bfa08fcd1590626f85fcc8c22d5f60",
  CONTRACT: "a1eda280aa56967aa06b01a2cca0dfc70c3da6df25066f8a1e815beec719f1bf",
  COMMANDS: "abbf59410a05fd5c789820df3d40e59d0a5c33cf1204ab93c7aeef806da7b1df",
  CONTROL: "10b5afe6cff38df7b6ebe5619fd9a34935932a4b369f3a9ad2a51923c32932d8",
  HELPER: "a32eddd159263d19ff87d7e9caee9d53d17ef5c350fbffe9e7eb142cb43ebf58",
}
INDEX_INPUTS = {
  "modules.order": (
    73113, "497c8546d3131d01191f7a66b68047abce5e5235ae982890180007f55c51a927",
  ),
  "modules.builtin": (
    10592, "74de5bab05fe70496f7702d83974adf8816ea826f1d8579f3b3f4b28a3890d2b",
  ),
  "modules.builtin.modinfo": (
    106640, "702d4cabaa9bdc1b282d0e419ba091f64dc06ba737fe7319928bb3003adeea4b",
  ),
}
RETAINED_INDEX_SHA256 = {
  "modules.alias.bin": "ca6ca7be95509eb294c2e67090bfa84dcbab855fb0489e504804593a257c4ea9",
  "modules.builtin.alias.bin": "9635eaa0d8c3d2f89c98789adce44dfd047f8cb11c7c9d0aa60199defc2ad962",
  "modules.builtin.bin": "edf2e707c121431f4f77b842ffd0a37fad5c0a6df198296fd6ef0b7f3227ac74",
  "modules.dep.bin": "436095f4779ccbd9f0c44b90febef13b62be50c9518dd499c151843fdf1feb3d",
  "modules.devname": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "modules.softdep": "6a8f2009d87deba7a2de46e3d0c46b114fe388d188b00b9a382fc2156aabb676",
  "modules.symbols.bin": "a3f1e745b7675daaec99c7c7ebadc7d67b318143901e063674494c210b12ace6",
}
HISTORICAL_SHA256 = {
  **RETAINED_INDEX_SHA256,
  "modules.symbols.bin": "5077fb001a5c48a2135ce8f651606b18578610bc660f430a59114e76be4f9437",
  "modules.alias": "9ea85f8fd754e394a63c6de9a93f9d8445ad3ebaf3d75eb8101a460dcf4127ac",
  "modules.dep": "48b6e5f5befe58918639ae27e3271984629ade44d7de8f46fa46e92c7b9150fe",
  "modules.symbols": "91299d9a80705a17c92068869293aa32c86985f751a5e6ea84024cb511ca539a",
  "modules.weakdep": "a1fffe1059d8150b5d402b3f284f507025a8d4b5881810cb17b3fda8b8ab9304",
}
HISTORICAL_BYTES = {
  "modules.alias.bin": 73869, "modules.builtin.alias.bin": 37491,
  "modules.builtin.bin": 12558, "modules.dep.bin": 18359,
  "modules.devname": 0, "modules.softdep": 76, "modules.symbols.bin": 31021,
  "modules.alias": 70982, "modules.dep": 10998, "modules.symbols": 26189,
  "modules.weakdep": 55,
}
HISTORICAL_BINDINGS = {
  "modules.alias.bin": Path("/inputs/g-alias-bin"),
  "modules.builtin.alias.bin": Path("/inputs/g-builtin-alias-bin"),
  "modules.builtin.bin": Path("/inputs/g-builtin-bin"),
  "modules.dep.bin": Path("/inputs/g-dep-bin"),
  "modules.devname": Path("/inputs/g-devname"),
  "modules.softdep": Path("/inputs/g-softdep"),
  "modules.symbols.bin": Path("/inputs/g-symbols-bin"),
  "modules.alias": Path("/inputs/g-alias-text"),
  "modules.dep": Path("/inputs/g-dep-text"),
  "modules.symbols": Path("/inputs/g-symbols-text"),
  "modules.weakdep": Path("/inputs/g-weakdep"),
}
DUMP = Path("/inputs/g-dump")
DUMP_SHA256 = "c562726938a6e3d11d5b3661352508f00b74efd9cbadbb559c3680663da72c05"
DUMP_BYTES = 97151
PINS = {
  **SOURCE_PINS,
  BASE: E_SHA256,
  PROOF: "9133cb64040f9df0daf9aa0caaab913c90fe7ce5c9bf59a19c71ce3e36fb0c94",
  DUMP: DUMP_SHA256,
  **{path: HISTORICAL_SHA256[name] for name, path in HISTORICAL_BINDINGS.items()},
}
EXPECTED_TOP = frozenset((
  "test", "recipe", "subject", "contract", "assembly", "control", "helper", "base",
  "index-inputs", "proof", "g-alias-bin", "g-builtin-alias-bin", "g-builtin-bin",
  "g-dep-bin", "g-devname", "g-softdep", "g-symbols-bin", "g-alias-text",
  "g-dep-text", "g-symbols-text", "g-weakdep", "g-dump",
))
SOURCE_LAYOUT = {
  Path("/inputs/subject"): "e_control.py",
  Path("/inputs/contract"): "image_contract.py",
  Path("/inputs/assembly"): "prepare_image.py",
  Path("/inputs/control"): "verify_control.py",
  Path("/inputs/helper"): "cpio_image.py",
}
SELECTED_TESTS = (
  "EControlSemanticRedTests.test_a_full_fixed_e_historical_vector_is_nonfresh",
  "EControlSemanticRedTests.test_b_each_semantic_corruption_refuses_without_publication",
  "EControlSemanticRedTests.test_c_fixture_publication_is_no_replace_rename_last_and_fail_closed",
)
KERNEL = "7.1.6-1-1-ARCH"
PREFIX = f"usr/lib/modules/{KERNEL}/"
MODULE_MODEL_SHA256 = "eee8ad06a36c1537d53e0c416db998110d10638076a32bdd3fc8987f65b54bff"
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
ALIASES = (
  "of:Nusb-pdT(null)Capple,cd321x", "of:Ndwc3T(null)Capple,t8103-dwc3",
  "of:Natc-phyT(null)Capple,t8103-atcphy",
)
EXPORTS = (
  "tipd_sn201202x_data", "tps6598x_regmap_config", "tipd_init", "tipd_cd321x_data",
  "tipd_tps6598x_data", "tipd_tps25750_data", "tipd_remove", "tipd_suspend", "tipd_resume",
)
META = Path("/work/e-control-semantic-red")
FIXTURE_RECORD_ROOT = "/work/e-control-semantic-fixture-records-s1"
FIXTURE_CONTROL_ROOT = "/work/e-control-semantic-fixture-control-root-s1"
FIXTURE_LOOKUP_ROOT = "/work/e-control-semantic-fixture-lookup-root-s1"
FIXTURE_EMPTY_CONFIG = "/work/e-control-semantic-fixture-empty-modprobe.conf"
FIXTURE_EARLY_PATH = "/work/e-control-semantic-fixture-early.cpio"
FIXTURE_MAIN_PATH = "/work/e-control-semantic-fixture-main.cpio"
PENDING = Path("/work/e-control-semantic-fixture-pending.json")
FINAL = Path("/work/e-control-semantic-fixture-result.json")
REAL_OUTPUTS = (
  Path("/work/control-root"), Path("/work/lookup-root"), Path("/work/empty-modprobe.conf"),
  Path("/work/e-early.cpio"), Path("/work/e-main.cpio"),
  Path("/work/e-control-children-e1"), Path("/work/e-control-header.json"),
  Path("/work/e-control-evidence.json"), Path("/work/e-control-result.json"),
  Path("/work/e-control-structural-records-e1"),
  Path("/work/e-control-structural-header.json"),
  Path("/work/e-control-structural-evidence.json"),
  Path("/work/e-control-structural-result.json"),
)
STDOUT_BYTES = 64 * 1024 * 1024
STDERR_BYTES = 65536
REPORT_BYTES = 128 * 1024
CHILD_SECONDS = 30
CONTROL_SECONDS = 270
WORKLOAD_SECONDS = 280
OUTER_SECONDS = 285
GZIP_TAIL_BYTES = 19181273
GZIP_TAIL_SHA256 = "375aa35be0ea57fa8d3f79f20cfa70373742ba6e2afda409462497d0d96ad724"
EARLY_LIST_BYTES = 47
EARLY_LIST_SHA256 = "62d818f030037bc3bbfc080899def7a67770961cc81d821ab750dcd06ea974cd"
MAIN_LIST_BYTES = 42863
MAIN_LIST_SHA256 = "90e515cd5008382d737295497faf85f8fe530a19eca8bad4097cf0eb78e36633"
EXPECTED_AGGREGATE_SHA256: str | None = "68dd45eeeb9239b873c293b81cbbb5b7403d4ff0d5d1b5a32f3e27c14c92d44e"
INITIAL_WORK_MEMBERS = frozenset((
  "descriptor-sentinel", "probe-write", "stdout.log", "stderr.log",
))
FIXTURE_PATH_POLICY = (
  FIXTURE_RECORD_ROOT, FIXTURE_CONTROL_ROOT, FIXTURE_LOOKUP_ROOT,
  FIXTURE_EMPTY_CONFIG, FIXTURE_EARLY_PATH, FIXTURE_MAIN_PATH,
)
OPERATIONAL_PATH_POLICY = (
  "/work/e-control-children-e1", "/work/control-root", "/work/lookup-root",
  "/work/empty-modprobe.conf", "/work/e-early.cpio", "/work/e-main.cpio",
)
FAMILY_VALIDATORS = (
  "_validate_archive_family", "_validate_payload_family", "_validate_tree_family",
  "_validate_index_family", "_validate_module_family", "_validate_alias_family",
  "_validate_symbol_family", "_validate_command_family", "_validate_identity_family",
  "_validate_provenance_family",
)
OBSERVATION_VALIDATORS = (
  "_validate_archive_observation", "_validate_payload_observation",
  "_validate_tree_observation", "_validate_index_observation",
  "_validate_module_observation", "_validate_alias_observation",
  "_validate_symbol_observation", "_validate_command_observation",
  "_validate_identity_observation", "_validate_provenance_observation",
)
FAMILY_APIS = (
  "RawControlFiles", "MappedControlOutputs", "SemanticFixtureEvaluation",
  "_map_raw_control_outputs",
  "SEMANTIC_FIXTURE_PATHS", "SEMANTIC_OPERATIONAL_PATHS", "SEMANTIC_RECORDS",
  "_collect_fixed_raw_files",
  "_read_fixed_semantic_fixture_outputs", "_read_fixed_operational_outputs",
  *FAMILY_VALIDATORS, *OBSERVATION_VALIDATORS, "_evaluate_control_semantics",
)
SUBJECT_EXACT_IMPORTS = {
  "Archive": ("cpio_image", "Archive"),
  "FileState": ("verify_control", "FileState"),
  "Module": ("verify_control", "Module"),
  "Path": ("pathlib", "Path"),
  "TreeState": ("verify_control", "TreeState"),
  "alias_entries": ("prepare_image", "alias_entries"),
  "ctypes": (None, "ctypes"),
  "dataclass": ("dataclasses", "dataclass"),
  "dependency_entries": ("prepare_image", "dependency_entries"),
  "errno": (None, "errno"),
  "fnmatchcase": ("fnmatch", "fnmatchcase"),
  "hashlib": (None, "hashlib"),
  "json": (None, "json"),
  "module_name": ("verify_control", "module_name"),
  "os": (None, "os"),
  "parse_newc": ("cpio_image", "parse_newc"),
  "read_regular": ("cpio_image", "read_regular"),
  "re": (None, "re"),
  "regular_member": ("verify_control", "regular_member"),
  "select_indexes": ("verify_control", "select_indexes"),
  "single_gzip": ("prepare_image", "single_gzip"),
  "snapshot": ("verify_control", "snapshot"),
  "stat": (None, "stat"),
  "validate_binary_dump": ("prepare_image", "validate_binary_dump"),
  "write_new": ("cpio_image", "write_new"),
}
SUBJECT_REQUIRED_IMPORTS = frozenset((
  "Archive", "Module", "Path", "alias_entries", "dataclass", "dependency_entries",
  "hashlib", "json", "module_name", "os", "parse_newc", "re", "regular_member",
  "select_indexes", "single_gzip", "stat", "validate_binary_dump", "write_new",
))
SUBJECT_CRITICAL_BUILTINS = frozenset((
  "RuntimeError", "all", "any", "bool", "bytes", "dict", "enumerate", "float",
  "frozenset", "int", "isinstance", "len", "list", "map", "max", "min", "object",
  "range", "set", "sorted", "str", "sum", "tuple", "type", "zip",
))
SUBJECT_REQUIRED_LOCAL_FUNCTIONS = frozenset((
  "_probe", "_require", "_sha256", "_validated_names", "command_plan",
  "finalize_operational_result", "operational_policy", "select_e",
  "validate_regeneration",
))
SUBJECT_FUTURE_LOCAL_FUNCTIONS = frozenset((
  "_map_raw_control_outputs", "_collect_fixed_raw_files",
  "_read_fixed_semantic_fixture_outputs", "_read_fixed_operational_outputs",
  "_evaluate_control_semantics", "_rename_noreplace_errcheck", "_rename_noreplace",
  "_semantic_fixture_work_membership", "_semantic_fixture_result_bytes",
  "publish_semantic_fixture_result", *FAMILY_VALIDATORS, *OBSERVATION_VALIDATORS,
))
SUBJECT_REQUIRED_LOCAL_CLASSES = frozenset(("ESelection", "RecipeError", "Regeneration"))
SUBJECT_FUTURE_LOCAL_CLASSES = frozenset((
  "MappedControlOutputs", "RawControlFiles", "SemanticFixtureAcceptance",
  "SemanticFixtureEvaluation",
))


def require(condition: bool, message: str) -> None:
  if not condition:
    raise RuntimeError(message)


def sha256(raw: bytes) -> str:
  return hashlib.sha256(raw).hexdigest()


def identity(info: os.stat_result) -> tuple[int, ...]:
  return (info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_gid,
          info.st_nlink, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def canonical_json(value: object) -> bytes:
  return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                     allow_nan=False) + "\n").encode("ascii")


def corrupted_raw(raw: bytes) -> bytes:
  return bytes((raw[0] ^ 1,)) + raw[1:] if raw else b"x"


def read_regular_bound(path: Path, maximum: int, *, allow_empty: bool = False) -> tuple[bytes, tuple[int, ...]]:
  for parent in path.parents:
    require(stat.S_ISDIR(parent.lstat().st_mode), "input parent is not a real directory")
  before = path.lstat()
  require(stat.S_ISREG(before.st_mode) and before.st_uid == before.st_gid == 1001 and
          before.st_nlink == 1 and 0 <= before.st_size <= maximum and
          (allow_empty or before.st_size > 0), "input metadata differs")
  descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC)
  with os.fdopen(descriptor, "rb") as stream:
    require(identity(os.fstat(stream.fileno())) == identity(before), "input changed on open")
    raw = stream.read(maximum + 1)
    require(identity(os.fstat(stream.fileno())) == identity(before) == identity(path.lstat()),
            "input changed while read")
  require(len(raw) == before.st_size, "input size differs")
  return raw, identity(before)


def read_pinned(path: Path) -> tuple[bytes, tuple[int, ...]]:
  require(path in PINS, "unapproved input")
  maximum = E_BYTES if path == BASE else (128 * 1024 if path in SOURCE_PINS or path == PROOF
                                          else 4 * 1024 * 1024)
  raw, state = read_regular_bound(
    path, maximum, allow_empty=path == HISTORICAL_BINDINGS["modules.devname"],
  )
  require(sha256(raw) == PINS[path] and (path != BASE or len(raw) == E_BYTES),
          "input hash or size differs")
  return raw, state


def read_index_directory() -> tuple[dict[str, bytes], tuple[int, ...], dict[str, tuple[int, ...]]]:
  before = INDEX_DIRECTORY.lstat()
  require(stat.S_ISDIR(before.st_mode) and stat.S_IMODE(before.st_mode) == 0o700 and
          before.st_uid == before.st_gid == 1001 and before.st_nlink == 2 and
          {path.name for path in INDEX_DIRECTORY.iterdir()} == set(INDEX_INPUTS),
          "index directory differs")
  raw_files: dict[str, bytes] = {}
  states: dict[str, tuple[int, ...]] = {}
  for name, (size, digest) in INDEX_INPUTS.items():
    path = INDEX_DIRECTORY / name
    raw, state = read_regular_bound(path, size)
    info = path.lstat()
    require(stat.S_IMODE(info.st_mode) == 0o644 and len(raw) == size and sha256(raw) == digest,
            "index input differs")
    raw_files[name] = raw
    states[name] = state
  require(identity(INDEX_DIRECTORY.lstat()) == identity(before), "index directory changed")
  return raw_files, identity(before), states


def validate_binding_tree() -> tuple[bytes, tuple[int, ...]]:
  inputs = Path("/inputs")
  require(stat.S_ISDIR(inputs.lstat().st_mode) and
          {path.name for path in inputs.iterdir()} == EXPECTED_TOP,
          "task input membership differs")
  test_raw, test_state = read_regular_bound(TEST, 256 * 1024)
  for directory, filename in SOURCE_LAYOUT.items():
    info = directory.lstat()
    require(stat.S_ISDIR(info.st_mode) and info.st_uid == info.st_gid == 1001 and
            info.st_nlink == 2 and {path.name for path in directory.iterdir()} == {filename},
            "source binding membership differs")
  return test_raw, test_state


def load_source(name: str, path: Path, raw: bytes) -> ModuleType:
  require(name not in sys.modules, "source already imported")
  module = ModuleType(name)
  module.__file__ = str(path)
  sys.modules[name] = module
  exec(compile(raw, str(path), "exec"), module.__dict__)
  return module


def preexec_subject_source_shape(raw: bytes) -> None:
  try:
    tree = ast.parse(raw.decode("utf-8"), filename=str(SUBJECT))
  except (SyntaxError, UnicodeError):
    raise RuntimeError("subject source is not parseable UTF-8 Python") from None
  allowed_imports = {
    "ctypes", "dataclasses", "errno", "fnmatch", "hashlib", "json", "os", "pathlib",
    "re", "stat", "typing", "cpio_image", "prepare_image", "verify_control",
  }
  allowed_assignment_calls = {"Path", "ctypes.CDLL", "frozenset"}
  allowed_attribute_targets = {
    "_SEMANTIC_LIBC.renameat2.argtypes", "_SEMANTIC_LIBC.renameat2.restype",
    "_SEMANTIC_LIBC.renameat2.errcheck",
  }
  forbidden_attributes = {
    "Popen", "call", "check_call", "check_output", "compile", "exec", "fork", "getattr",
    "link", "mkdir", "open", "remove", "rename", "renameat2", "replace", "rmdir", "rmtree",
    "run", "setattr", "spawn", "symlink", "system", "touch", "unlink", "write",
    "write_bytes", "write_text",
  }
  def dotted(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
      return node.id
    if isinstance(node, ast.Attribute):
      parent = dotted(node.value)
      return f"{parent}.{node.attr}" if parent is not None else None
    return None

  def calls(node: ast.AST) -> set[str | None]:
    return {
      dotted(item.func) for item in ast.walk(node)
      if isinstance(item, ast.Call)
    }

  top_level_ids = {id(node) for node in tree.body}
  imports: list[tuple[str, str | None, str, str | None, bool]] = []
  for node in ast.walk(tree):
    if isinstance(node, ast.Import):
      imports.extend((alias.asname or alias.name.split(".")[0], None, alias.name,
                      alias.asname, id(node) in top_level_ids) for alias in node.names)
    elif isinstance(node, ast.ImportFrom):
      imports.extend((alias.asname or alias.name, node.module, alias.name,
                      alias.asname, id(node) in top_level_ids) for alias in node.names)
  for binding, expected in SUBJECT_EXACT_IMPORTS.items():
    rows = [row for row in imports if row[0] == binding]
    required = binding in SUBJECT_REQUIRED_IMPORTS
    require(len(rows) == (1 if required else min(len(rows), 1)) and all(
      module == expected[0] and name == expected[1] and alias is None and top_level
      for _binding, module, name, alias, top_level in rows
    ), f"subject critical import binding differs: {binding}")
  protected_imports = set(SUBJECT_EXACT_IMPORTS)
  protected_functions = SUBJECT_REQUIRED_LOCAL_FUNCTIONS | SUBJECT_FUTURE_LOCAL_FUNCTIONS
  protected_classes = SUBJECT_REQUIRED_LOCAL_CLASSES | SUBJECT_FUTURE_LOCAL_CLASSES
  protected_bindings = (protected_imports | SUBJECT_CRITICAL_BUILTINS |
                        protected_functions | protected_classes)
  require(not any(binding in (SUBJECT_CRITICAL_BUILTINS | protected_functions |
                              protected_classes) for binding, *_rest in imports),
          "subject imports over a critical builtin or local binding")
  require(not any(
    (isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store) and
     node.id in protected_bindings) or
    (isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Store) and
     dotted(node) is not None and dotted(node).split(".")[0] in protected_bindings) or
    (isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and
     node.name in (protected_imports | SUBJECT_CRITICAL_BUILTINS | protected_classes)) or
    (isinstance(node, ast.ClassDef) and
     node.name in (protected_imports | SUBJECT_CRITICAL_BUILTINS | protected_functions)) or
    (isinstance(node, (ast.ExceptHandler, ast.MatchAs, ast.MatchStar)) and
     node.name in protected_bindings) or
    (isinstance(node, ast.MatchMapping) and node.rest in protected_bindings) or
    (isinstance(node, ast.arg) and node.arg in protected_bindings) or
    (isinstance(node, (ast.Global, ast.Nonlocal)) and
     bool(set(node.names) & protected_bindings)) or
    isinstance(node, ast.Delete)
    for node in ast.walk(tree)
  ), "subject shadows, captures, or deletes a critical binding")
  for name in protected_functions:
    definitions = [node for node in ast.walk(tree)
                   if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and
                   node.name == name]
    required = name in SUBJECT_REQUIRED_LOCAL_FUNCTIONS
    require(len(definitions) == (1 if required else min(len(definitions), 1)) and
            all(isinstance(node, ast.FunctionDef) and id(node) in top_level_ids
                for node in definitions) and
            not any(isinstance(node, ast.ClassDef) and node.name == name
                    for node in ast.walk(tree)),
            f"subject critical function binding differs: {name}")
  for name in protected_classes:
    definitions = [node for node in ast.walk(tree)
                   if isinstance(node, ast.ClassDef) and node.name == name]
    required = name in SUBJECT_REQUIRED_LOCAL_CLASSES
    require(len(definitions) == (1 if required else min(len(definitions), 1)) and
            all(id(node) in top_level_ids for node in definitions) and
            not any(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and
                    node.name == name for node in ast.walk(tree)),
            f"subject critical class binding differs: {name}")

  for node in tree.body:
    if isinstance(node, ast.Import):
      require(all(alias.name in allowed_imports and alias.asname is None for alias in node.names),
              "subject top-level import differs")
    elif isinstance(node, ast.ImportFrom):
      require(node.module in allowed_imports and node.level == 0 and
              all(alias.asname is None and alias.name != "*" for alias in node.names),
              "subject top-level import differs")
    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
      signature_nodes: list[ast.AST] = [*node.args.defaults]
      signature_nodes.extend(value for value in node.args.kw_defaults if value is not None)
      signature_nodes.extend(
        argument.annotation for argument in (
          *node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs,
        ) if argument.annotation is not None
      )
      if node.args.vararg is not None and node.args.vararg.annotation is not None:
        signature_nodes.append(node.args.vararg.annotation)
      if node.args.kwarg is not None and node.args.kwarg.annotation is not None:
        signature_nodes.append(node.args.kwarg.annotation)
      if node.returns is not None:
        signature_nodes.append(node.returns)
      require(not node.decorator_list and all(not calls(value) for value in signature_nodes),
              "subject function signature would execute a call during import")
    elif isinstance(node, ast.ClassDef):
      require(not node.keywords and
              all(isinstance(base, ast.Name) and base.id == "RuntimeError"
                  for base in node.bases) and
              all(isinstance(decorator, ast.Call) and dotted(decorator.func) == "dataclass" and
                  not decorator.args and len(decorator.keywords) == 1 and
                  decorator.keywords[0].arg == "frozen" and
                  isinstance(decorator.keywords[0].value, ast.Constant) and
                  decorator.keywords[0].value.value is True
                  for decorator in node.decorator_list),
              "subject class definition differs")
      require(all(
        (isinstance(item, ast.Expr) and isinstance(item.value, ast.Constant) and
         type(item.value.value) is str) or
        (isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name) and
         item.value is None and not calls(item.annotation))
        for item in node.body
      ), "subject class body has an import-time side effect")
    elif isinstance(node, (ast.Assign, ast.AnnAssign)):
      value = node.value
      require(value is not None and calls(value) <= allowed_assignment_calls,
              "subject assignment has an unapproved import-time call")
      for call in (item for item in ast.walk(value) if isinstance(item, ast.Call)):
        name = dotted(call.func)
        if name == "ctypes.CDLL":
          require(len(call.args) == 1 and isinstance(call.args[0], ast.Constant) and
                  call.args[0].value is None and len(call.keywords) == 1 and
                  call.keywords[0].arg == "use_errno" and
                  isinstance(call.keywords[0].value, ast.Constant) and
                  call.keywords[0].value.value is True,
                  "subject libc binding would execute an unapproved load")
        elif name == "Path":
          require(len(call.args) == 1 and not call.keywords and
                  isinstance(call.args[0], ast.Constant) and
                  type(call.args[0].value) is str,
                  "subject import-time Path argument differs")
        elif name == "frozenset":
          require(len(call.args) == 1 and not call.keywords and
                  isinstance(call.args[0], (ast.Tuple, ast.List)) and
                  all(isinstance(item, ast.Constant) and type(item.value) is str
                      for item in call.args[0].elts),
                  "subject import-time frozenset argument differs")
      require(not any(isinstance(item, ast.Attribute) and item.attr in forbidden_attributes
                      for item in ast.walk(value)),
              "subject assignment aliases an unsafe operation")
      require(not ({item.id for item in ast.walk(value) if isinstance(item, ast.Name) and
                    isinstance(item.ctx, ast.Load)} & {"delattr", "getattr", "setattr"}),
              "subject assignment aliases dynamic attribute access")
      targets = node.targets if isinstance(node, ast.Assign) else [node.target]
      require(all(dotted(target) is not None and
                  (isinstance(target, ast.Name) or dotted(target) in allowed_attribute_targets)
                  for target in targets), "subject assignment target differs")
    elif isinstance(node, ast.If):
      require(
        isinstance(node.test, ast.Compare) and len(node.test.ops) == 1 and
        isinstance(node.test.ops[0], ast.Eq) and len(node.test.comparators) == 1 and
        isinstance(node.test.left, ast.Name) and node.test.left.id == "__name__" and
        isinstance(node.test.comparators[0], ast.Constant) and
        node.test.comparators[0].value == "__main__" and not node.orelse and
        len(node.body) == 1 and isinstance(node.body[0], ast.Expr) and
        isinstance(node.body[0].value, ast.Call) and
        dotted(node.body[0].value.func) == "main" and not node.body[0].value.args and
        not node.body[0].value.keywords and calls(node) == {"main"},
        "subject import-time branch differs",
      )
    elif isinstance(node, ast.Expr):
      require(isinstance(node.value, ast.Constant) and type(node.value.value) is str,
              "subject has an executable top-level expression")
    else:
      raise RuntimeError("subject has an unapproved import-time statement")


def bootstrap() -> tuple[ModuleType, ModuleType, ModuleType, ModuleType, ModuleType,
                         dict[Path, bytes], dict[Path, tuple[int, ...]], bytes,
                         tuple[int, ...], dict[str, bytes], tuple[int, ...],
                         dict[str, tuple[int, ...]]]:
  require(sys.argv[1:] == list(SELECTED_TESTS), "exact three-test selection required")
  require(sys.version_info[:2] == (3, 14) and sys.flags.isolated == 1 and
          sys.flags.no_site == 1 and sys.dont_write_bytecode, "isolated Python 3.14 required")
  require(os.getuid() == os.geteuid() == os.getgid() == 1001 and Path.cwd() == Path("/work"),
          "unexpected fixture identity or directory")
  require(Path(__file__) == TEST, "unexpected runner path")
  require(not any(Path(path).exists() for path in (
    "/proc", "/sys", "/run", "/home", "/root", "/boot",
  )), "host tree visible")
  require(not any(name in sys.modules for name in (
    "cpio_image", "verify_control", "prepare_image", "t1_image_contract", "e_control", "e_recipe",
  )), "dependency already imported")
  test_raw, test_state = validate_binding_tree()
  data = {path: read_pinned(path) for path in PINS}
  indexes, index_state, index_file_states = read_index_directory()
  assembly = load_source("prepare_image", ASSEMBLY, data[ASSEMBLY][0])
  control = sys.modules.get("verify_control")
  require(isinstance(control, ModuleType) and control.__file__ == str(CONTROL),
          "frozen control helper was not imported")
  contract = load_source("t1_image_contract", CONTRACT, data[CONTRACT][0])
  commands = load_source("e_control", COMMANDS, data[COMMANDS][0])
  preexec_subject_source_shape(data[SUBJECT][0])
  subject = load_source("e_recipe", SUBJECT, data[SUBJECT][0])
  return (
    subject, contract, commands, assembly, control,
    {path: pair[0] for path, pair in data.items()},
    {path: pair[1] for path, pair in data.items()}, test_raw, test_state, indexes,
    index_state, index_file_states,
  )


try:
  (subject, contract, commands, assembly, control, INPUT_BYTES, INPUT_STATES, TEST_BYTES, TEST_STATE,
   INDEX_BYTES, INDEX_STATE, INDEX_FILE_STATES) = bootstrap()
  from cpio_image import parse_newc, read_regular, write_new
except (OSError, RuntimeError, ValueError, SyntaxError, ImportError, TypeError) as error:
  print(f"SETUP FAIL: {type(error).__name__}: {error}", file=sys.stderr)
  raise SystemExit(2) from None


def save_json(path: Path, value: object) -> None:
  write_new(path, canonical_json(value))


def object_map(value: object) -> dict[str, object]:
  require(type(value) is dict, "semantic fixture map differs")
  return value


def object_list(value: object) -> list[object]:
  require(type(value) is list, "semantic fixture list differs")
  return value


def shallow_observation(value: object) -> dict[str, object]:
  source = object_map(value)
  result = dict(source)
  report = dict(object_map(source["report"]))
  for key in ("command", "operational_command", "retained_bytes", "observed_bytes"):
    report[key] = list(object_list(report[key]))
  result["report"] = report
  for key in ("stdout_file", "stderr_file", "report_file"):
    record = dict(object_map(source[key]))
    record["identity"] = list(object_list(record["identity"]))
    result[key] = record
  return result


def changed_value(value: object) -> object:
  if type(value) is bool:
    return not value
  if value is None:
    return 1
  if type(value) is int:
    return value + 1
  if type(value) is float:
    return value + 0.25
  if type(value) is str:
    return value + "-wrong"
  if type(value) is bytes:
    return corrupted_raw(value)
  if type(value) is list:
    return [*value, "wrong"]
  raise RuntimeError("unsupported semantic mutation value")


def probe_command(root: str, target: str, config: str) -> tuple[str, ...]:
  return ("/usr/bin/modprobe", "--dry-run", "--show-depends", "-d", root,
          "-S", KERNEL, "-C", config, target)


def expected_plan(names: dict[str, str], *, fixture: bool) -> tuple[tuple[str, ...], ...]:
  control_root = FIXTURE_CONTROL_ROOT if fixture else "/work/control-root"
  lookup_root = FIXTURE_LOOKUP_ROOT if fixture else "/work/lookup-root"
  empty_config = FIXTURE_EMPTY_CONFIG if fixture else "/work/empty-modprobe.conf"
  early_path = FIXTURE_EARLY_PATH if fixture else "/work/e-early.cpio"
  main_path = FIXTURE_MAIN_PATH if fixture else "/work/e-main.cpio"
  plan: list[tuple[str, ...]] = []
  for path in (early_path, main_path):
    plan.extend((("/usr/bin/cpio", "--list", "--quiet", "--file", path),
                 ("/usr/bin/bsdtar", "--list", "--file", path)))
  plan.append(("/usr/bin/gzip",))
  for path in PAYLOAD_SHA256:
    plan.append(("/usr/bin/bsdtar", "--extract", "--to-stdout", "--file", main_path, path))
  plan.append(("/usr/bin/depmod", "-b", control_root, KERNEL))
  plan.extend((probe_command(control_root, "--show-config", empty_config),
               probe_command(lookup_root, "--show-config", empty_config)))
  for name in sorted(names):
    plan.append(("/usr/bin/modinfo", "-b", lookup_root, "-k", KERNEL,
                 "-F", "filename", name))
    plan.append(probe_command(lookup_root, name, empty_config))
  plan.extend(probe_command(lookup_root, alias, empty_config) for alias in ALIASES)
  plan.extend(probe_command(lookup_root, "symbol:" + symbol, empty_config) for symbol in EXPORTS)
  return tuple(plan)


def alias_rows(raw: bytes) -> tuple[tuple[str, str], ...]:
  try:
    lines = raw.decode("ascii").splitlines()
  except UnicodeError:
    raise RuntimeError("historical alias fixture is not ASCII") from None
  require(bool(lines) and lines[0].startswith("# "), "historical alias header differs")
  rows: list[tuple[str, str]] = []
  for line in lines[1:]:
    parts = line.split(" ")
    require(len(parts) == 3 and parts[0] == "alias" and
            re.fullmatch(r"[A-Za-z0-9_]{1,128}", parts[2]) is not None,
            "historical alias row differs")
    rows.append((parts[1], parts[2]))
  return tuple(rows)


def archive_record(member: object, index: int) -> dict[str, object]:
  raw = getattr(member, "raw")
  raw_name = getattr(member, "raw_name")
  payload = getattr(member, "payload")
  fields = getattr(member, "fields")
  name = getattr(member, "name")
  require(type(raw) is bytes and type(raw_name) is bytes and type(payload) is bytes and
          type(fields) is tuple and all(type(value) is int for value in fields) and
          type(name) is str, "archive member model differs")
  return {
    "index": index, "name": name, "raw_bytes": len(raw), "raw_sha256": sha256(raw),
    "raw_name_sha256": sha256(raw_name), "payload_bytes": len(payload),
    "payload_sha256": sha256(payload), "fields": list(fields),
  }


def matching_target(query: str, rows: tuple[tuple[str, str], ...]) -> str:
  matches = [module for pattern, module in rows if fnmatchcase(query, pattern)]
  require(len(matches) == 1, "fixture lookup target is not unique")
  return matches[0]


def work_members() -> frozenset[str]:
  return frozenset(path.name for path in Path("/work").iterdir())


def expected_fixture_members(*extra: str) -> frozenset[str]:
  return INITIAL_WORK_MEMBERS | frozenset((
    META.name, Path(FIXTURE_RECORD_ROOT).name, Path(FIXTURE_CONTROL_ROOT).name,
    Path(FIXTURE_LOOKUP_ROOT).name, Path(FIXTURE_EMPTY_CONFIG).name,
    Path(FIXTURE_EARLY_PATH).name, Path(FIXTURE_MAIN_PATH).name, *extra,
  ))


def archive_listing(archive: object) -> bytes:
  lines: list[str] = []
  for member in getattr(archive, "members"):
    name = getattr(member, "name")
    fields = getattr(member, "fields")
    require(type(name) is str and type(fields) is tuple, "archive list model differs")
    if stat.S_ISDIR(fields[1]) and not name.endswith("/"):
      name += "/"
    lines.append(name)
  return ("\n".join(lines) + "\n").encode("ascii")


def lookup_output(name: str) -> bytes:
  relative = NAMES[name]
  prefix = f"{FIXTURE_LOOKUP_ROOT}/lib/modules/{KERNEL}/"
  builtins = ("ecb",) if name == "lrw" else ()
  insmod = tuple(prefix + path for path in reversed(DEPENDENCIES[relative])) + (prefix + relative,)
  return ("".join(f"builtin {item}\n" for item in builtins) +
          "".join(f"insmod {item} \n" for item in insmod)).encode("ascii")


def file_observation(path: Path, expected: bytes) -> dict[str, object]:
  before = path.lstat()
  actual = read_regular(path)
  after = path.lstat()
  require(actual == expected and identity(before) == identity(after), "fixture file changed")
  return {
    "path": str(path), "raw": actual, "bytes": len(actual), "sha256": sha256(actual),
    "identity": list(identity(before)), "mode": stat.S_IMODE(before.st_mode),
    "uid": before.st_uid, "gid": before.st_gid, "nlink": before.st_nlink,
  }


def tree_records(root: Path, state: object) -> tuple[dict[str, object], ...]:
  records: list[dict[str, object]] = []
  directories = getattr(state, "directories")
  files = getattr(state, "files")
  for relative in sorted(directories):
    value = directories[relative]
    actual = identity((root / relative).lstat())
    require(actual[:5] == value, "fixture directory identity differs")
    value = actual
    records.append({
      "kind": "directory", "path": str(root / relative), "identity": list(value),
      "mode": stat.S_IMODE(value[2]), "uid": value[3], "gid": value[4],
    })
  for relative in sorted(files):
    value = files[relative]
    records.append({
      "kind": "file", "path": str(root / relative), "identity": list(value.identity),
      "mode": stat.S_IMODE(value.identity[2]), "uid": value.identity[3],
      "gid": value.identity[4], "nlink": value.identity[5], "bytes": value.identity[6],
      "sha256": value.sha256,
    })
  return tuple(records)


def make_module_tree(root: Path, indexes: dict[str, bytes]) -> object:
  root.mkdir(mode=0o700)
  version = root / "lib/modules" / KERNEL
  version.mkdir(mode=0o700, parents=True)
  for relative in sorted(MODULE_PAYLOADS):
    path = version / relative
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    write_new(path, MODULE_PAYLOADS[relative])
  for name in sorted(indexes):
    write_new(version / name, indexes[name])
  return control.snapshot(root)


def raw_command_outputs() -> tuple[bytes, ...]:
  outputs: list[bytes] = [
    archive_listing(EARLY), archive_listing(EARLY),
    archive_listing(MAIN), archive_listing(MAIN), INPUT_BYTES[BASE][10240:],
  ]
  outputs.extend(BY_NAME[path].payload for path in PAYLOAD_SHA256)
  outputs.extend((b"", INPUT_BYTES[DUMP], INPUT_BYTES[DUMP]))
  for name in sorted(NAMES):
    outputs.extend((
      (f"{FIXTURE_LOOKUP_ROOT}/lib/modules/{KERNEL}/{NAMES[name]}\n").encode("ascii"),
      lookup_output(name),
    ))
  outputs.extend(lookup_output(matching_target(alias, ALIAS_ROWS)) for alias in ALIASES)
  outputs.extend(lookup_output(matching_target("symbol:" + symbol, SYMBOL_ROWS))
                 for symbol in EXPORTS)
  require(len(outputs) == 424 and
          len(outputs[0]) == len(outputs[1]) == EARLY_LIST_BYTES and
          sha256(outputs[0]) == sha256(outputs[1]) == EARLY_LIST_SHA256 and
          len(outputs[2]) == len(outputs[3]) == MAIN_LIST_BYTES and
          sha256(outputs[2]) == sha256(outputs[3]) == MAIN_LIST_SHA256 and
          len(outputs[4]) == GZIP_TAIL_BYTES and
          sha256(outputs[4]) == GZIP_TAIL_SHA256 and
          EARLY.raw + outputs[4] == INPUT_BYTES[BASE], "raw command output model differs")
  return tuple(outputs)


def write_command_observation(index: int, stdout: bytes) -> dict[str, object]:
  base = Path(FIXTURE_RECORD_ROOT) / f"record-{index:03d}"
  stdout_path = base.with_suffix(".stdout")
  stderr_path = base.with_suffix(".stderr")
  report_path = base.with_suffix(".json")
  report = {
    "schema": 1, "kind": "dev147-e-control-semantic-fixture-record-v2",
    "index": index, "command": list(EXPECTED_FIXTURE_PLAN[index]),
    "operational_command": list(EXPECTED_OPERATIONAL_PLAN[index]),
    "status": "FIXTURE_ONLY", "returncode": None,
    "stdout": str(stdout_path), "stderr": str(stderr_path), "report": str(report_path),
    "retained_bytes": [len(stdout), 0], "observed_bytes": [len(stdout), 0],
    "stdin_sha256": "7be7b4b03367b5ce4b356fe35977edba6540af0a7df930dbff990286c9b98e28"
      if index == 4 else None,
    "stdin_bytes": 61286668 if index == 4 else 0,
    "executed": False, "elapsed_seconds": 0.0, "pid": None,
    "killed": False, "reaped": False,
  }
  report_raw = canonical_json(report)
  require(len(stdout) <= STDOUT_BYTES and len(report_raw) <= REPORT_BYTES,
          "fixture record exceeds retained limit")
  write_new(stdout_path, stdout)
  write_new(stderr_path, b"")
  write_new(report_path, report_raw)
  return {
    "report": report, "report_raw": report_raw,
    "stdout_file": file_observation(stdout_path, stdout),
    "stderr_file": file_observation(stderr_path, b""),
    "report_file": file_observation(report_path, report_raw),
  }


def stable_file(value: dict[str, object]) -> dict[str, object]:
  return {key: value[key] for key in (
    "path", "bytes", "sha256", "mode", "uid", "gid", "nlink",
  )}


def stable_tree(root: Path, state: object) -> dict[str, object]:
  directories = getattr(state, "directories")
  files = getattr(state, "files")
  return {
    "root": str(root),
    "directories": {
      relative: {"mode": stat.S_IMODE(value[2]), "uid": value[3], "gid": value[4]}
      for relative, value in sorted(directories.items())
    },
    "files": {
      relative: {
        "mode": stat.S_IMODE(value.identity[2]), "uid": value.identity[3],
        "gid": value.identity[4], "nlink": value.identity[5],
        "bytes": value.identity[6], "sha256": value.sha256,
      }
      for relative, value in sorted(files.items())
    },
  }


def build_aggregate_model() -> dict[str, object]:
  return {
    "schema": 2, "kind": "dev147-e-control-semantic-raw-fixture-v2",
    "status": "FIXTURE_ONLY", "base_sha256": E_SHA256, "base_bytes": E_BYTES,
    "early_records": [archive_record(member, index)
                      for index, member in enumerate(EARLY.members)],
    "main_records": [archive_record(member, index)
                     for index, member in enumerate(MAIN.members)],
    "commands": [
      {
        "report": value["report"],
        "stdout": stable_file(object_map(value["stdout_file"])),
        "stderr": stable_file(object_map(value["stderr_file"])),
        "report_file": stable_file(object_map(value["report_file"])),
      }
      for value in COMMAND_OBSERVATIONS
    ],
    "control_before": stable_tree(Path(FIXTURE_CONTROL_ROOT), CONTROL_BEFORE),
    "control_after": stable_tree(Path(FIXTURE_CONTROL_ROOT), CONTROL_AFTER),
    "lookup_before": stable_tree(Path(FIXTURE_LOOKUP_ROOT), LOOKUP_BEFORE),
    "lookup_after": stable_tree(Path(FIXTURE_LOOKUP_ROOT), LOOKUP_AFTER),
    "generated_indexes": {name: sha256(raw) for name, raw in sorted(HISTORICAL.items())},
    "retained_indexes": {name: sha256(raw) for name, raw in sorted(RETAINED_INDEXES.items())},
    "historical_dump": {"bytes": len(INPUT_BYTES[DUMP]), "sha256": DUMP_SHA256},
    "provenance": PROVENANCE,
  }


def expected_result_bytes() -> bytes:
  return canonical_json({
    "schema": 2, "kind": "dev147-e-control-semantic-fixture-result-v2",
    "status": "NONFRESH_FIXTURE", "semantic_validated": True,
    "aggregate_sha256": AGGREGATE_SHA256_CANDIDATE, "planned_children": 424,
    "children_executed": 0, "historical_generated_files": 12,
    "structural_control_proved": False, "operational_control_proved": False,
    "fresh_control_proved": False, "image_created": False,
    "module_loaded": False, "staged": False, "booted": False,
  })


def recheck_fixture_state() -> None:
  require(control.snapshot(Path(FIXTURE_CONTROL_ROOT)) == CONTROL_AFTER and
          control.snapshot(Path(FIXTURE_LOOKUP_ROOT)) == LOOKUP_AFTER,
          "fixture root identity or membership changed")
  for observation in COMMAND_OBSERVATIONS:
    for key in ("stdout_file", "stderr_file", "report_file"):
      record = object_map(observation[key])
      raw = record["raw"]
      path = record["path"]
      require(type(raw) is bytes and type(path) is str and
              file_observation(Path(path), raw) == record,
              "fixture command leaf identity changed")
  require(work_members() in (
    expected_fixture_members(), expected_fixture_members(FINAL.name),
  ), "fixture top-level membership changed")


def no_real_outputs() -> None:
  require(not any(path.exists() or path.is_symlink() for path in REAL_OUTPUTS),
          "real or structural control output exists")


def no_publication() -> None:
  require(not (PENDING.exists() or PENDING.is_symlink() or FINAL.exists() or FINAL.is_symlink()),
          "semantic fixture publication exists")
  no_real_outputs()


def call_name(call: ast.Call) -> str | None:
  if isinstance(call.func, ast.Name):
    return call.func.id
  if isinstance(call.func, ast.Attribute) and isinstance(call.func.value, ast.Name):
    return f"{call.func.value.id}.{call.func.attr}"
  return None


def assigned_value(tree: ast.Module, name: str) -> ast.expr | None:
  for node in tree.body:
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and \
       isinstance(node.targets[0], ast.Name) and node.targets[0].id == name:
      return node.value
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and \
       node.target.id == name:
      return node.value
  return None


def fixed_path_call(value: ast.expr | None, expected: str) -> bool:
  return bool(
    isinstance(value, ast.Call) and isinstance(value.func, ast.Name) and
    value.func.id == "Path" and len(value.args) == 1 and not value.keywords and
    isinstance(value.args[0], ast.Constant) and value.args[0].value == expected
  )


def function_statements(function: ast.FunctionDef) -> list[ast.stmt]:
  body = list(function.body)
  if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and \
     type(body[0].value.value) is str:
    body.pop(0)
  return body


def statement_call(statement: ast.stmt) -> ast.Call | None:
  value: ast.expr | None = None
  if isinstance(statement, ast.Expr):
    value = statement.value
  elif isinstance(statement, ast.Assign) and len(statement.targets) == 1:
    value = statement.value
  elif isinstance(statement, ast.AnnAssign):
    value = statement.value
  return value if isinstance(value, ast.Call) else None


def assignment_name(statement: ast.stmt) -> str | None:
  if isinstance(statement, ast.Assign) and len(statement.targets) == 1 and \
     isinstance(statement.targets[0], ast.Name):
    return statement.targets[0].id
  if isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
    return statement.target.id
  return None


def assignment_names(statement: ast.stmt) -> set[str]:
  targets: list[ast.expr] = []
  if isinstance(statement, ast.Assign):
    targets.extend(statement.targets)
  elif isinstance(statement, ast.AnnAssign):
    targets.append(statement.target)
  return {
    item.id for target in targets for item in ast.walk(target)
    if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Store)
  }


def loaded_names(node: ast.AST) -> set[str]:
  return {
    item.id for item in ast.walk(node)
    if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Load)
  }


def target_path(node: ast.expr) -> str | None:
  if isinstance(node, ast.Name):
    return node.id
  if isinstance(node, ast.Attribute):
    parent = target_path(node.value)
    return f"{parent}.{node.attr}" if parent is not None else None
  return None


def stored_paths(tree: ast.Module) -> list[tuple[str, ast.expr, int]]:
  result: list[tuple[str, ast.expr, int]] = []
  for node in ast.walk(tree):
    pairs: list[tuple[ast.expr, ast.expr]] = []
    if isinstance(node, ast.Assign):
      pairs.extend((target, node.value) for target in node.targets)
    elif isinstance(node, ast.AnnAssign) and node.value is not None:
      pairs.append((node.target, node.value))
    elif isinstance(node, ast.AugAssign):
      pairs.append((node.target, node.value))
    elif isinstance(node, ast.NamedExpr):
      pairs.append((node.target, node.value))
    for target, value in pairs:
      name = target_path(target)
      if name is not None:
        result.append((name, value, getattr(node, "lineno", -1)))
  return result


def exact_reader(function: ast.FunctionDef, policy: str) -> bool:
  body = function_statements(function)
  if function.args.posonlyargs or function.args.args or function.args.kwonlyargs or \
     function.args.vararg is not None or function.args.kwarg is not None or len(body) != 1:
    return False
  returned = body[0]
  if not (isinstance(returned, ast.Return) and isinstance(returned.value, ast.Call) and
          call_name(returned.value) == "_map_raw_control_outputs" and
          len(returned.value.args) == 1 and not returned.value.keywords):
    return False
  collector = returned.value.args[0]
  return bool(
    isinstance(collector, ast.Call) and call_name(collector) == "_collect_fixed_raw_files" and
    len(collector.args) == 1 and not collector.keywords and
    isinstance(collector.args[0], ast.Name) and collector.args[0].id == policy
  )


def critical_callable_load_source_shape(tree: ast.Module) -> tuple[bool, str]:
  module_bindings = {"ctypes", "errno", "hashlib", "json", "os", "re", "stat"}
  guarded = (
    (set(SUBJECT_EXACT_IMPORTS) - module_bindings) | set(SUBJECT_CRITICAL_BUILTINS) |
    set(SUBJECT_REQUIRED_LOCAL_FUNCTIONS) | set(SUBJECT_FUTURE_LOCAL_FUNCTIONS) |
    set(SUBJECT_REQUIRED_LOCAL_CLASSES) | set(SUBJECT_FUTURE_LOCAL_CLASSES)
  )
  allowed: set[int] = set()

  def allow_subtree(root: ast.AST | None) -> None:
    if root is not None:
      allowed.update(id(node) for node in ast.walk(root)
                     if isinstance(node, ast.Name) and node.id in guarded)

  for node in ast.walk(tree):
    if isinstance(node, ast.Call):
      if isinstance(node.func, ast.Name) and node.func.id in guarded:
        allowed.add(id(node.func))
      name = target_path(node.func)
      if name == "map" and node.args:
        allow_subtree(node.args[0])
      elif name == "isinstance" and len(node.args) >= 2:
        for value in node.args[1:]:
          allow_subtree(value)
    elif isinstance(node, ast.Compare):
      values = (node.left, *node.comparators)
      for position, operator in enumerate(node.ops):
        left, right = values[position], values[position + 1]
        if isinstance(operator, (ast.Is, ast.IsNot)):
          if isinstance(left, ast.Name) and left.id in guarded and \
             isinstance(right, ast.Call) and target_path(right.func) == "type":
            allow_subtree(left)
          if isinstance(right, ast.Name) and right.id in guarded and \
             isinstance(left, ast.Call) and target_path(left.func) == "type":
            allow_subtree(right)
    elif isinstance(node, ast.ExceptHandler):
      allow_subtree(node.type)
    elif isinstance(node, ast.ClassDef):
      for value in (*node.bases, *node.decorator_list):
        allow_subtree(value)
    elif isinstance(node, ast.FunctionDef):
      for argument in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs):
        allow_subtree(argument.annotation)
      if node.args.vararg is not None:
        allow_subtree(node.args.vararg.annotation)
      if node.args.kwarg is not None:
        allow_subtree(node.args.kwarg.annotation)
      allow_subtree(node.returns)
    elif isinstance(node, ast.AnnAssign):
      allow_subtree(node.annotation)
  errcheck = [value for stored, value, _line in stored_paths(tree)
              if stored == "_SEMANTIC_LIBC.renameat2.errcheck"]
  if len(errcheck) == 1 and isinstance(errcheck[0], ast.Name) and \
     errcheck[0].id == "_rename_noreplace_errcheck":
    allowed.add(id(errcheck[0]))
  rejected = [
    node.id for node in ast.walk(tree)
    if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and
    node.id in guarded and id(node) not in allowed
  ]
  if rejected:
    return False, f"critical callable is aliased or loaded outside a reviewed site: {rejected[0]}"
  return True, "critical callable loads are direct and reviewed"


def semantic_readonly_source_shape(
  tree: ast.Module,
  functions: dict[str, ast.FunctionDef],
) -> tuple[bool, str]:
  roots = {
    "_evaluate_control_semantics", "_read_fixed_semantic_fixture_outputs",
    "_read_fixed_operational_outputs", "_collect_fixed_raw_files",
    "_map_raw_control_outputs", "_probe", "_require", "_sha256", "_validated_names",
    "command_plan", "select_e", "validate_regeneration", *FAMILY_VALIDATORS,
    *OBSERVATION_VALIDATORS,
  }
  terminal_local: set[str] = set()
  forbidden = {
    "Popen", "call", "check_call", "check_output", "compile", "delattr", "eval", "exec",
    "fork", "getattr", "link", "mkdir", "open", "remove", "rename", "replace", "rmdir",
    "run", "setattr", "spawn", "system", "touch", "unlink", "write", "write_bytes",
    "write_new", "write_text",
  }
  allowed_exact = {
    "ESelection", "FileState", "MappedControlOutputs", "Module", "Path", "RawControlFiles",
    "RecipeError", "Regeneration", "SemanticFixtureEvaluation", "TreeState", "alias_entries",
    "all", "any", "bool", "bytes", "dependency_entries", "dict", "enumerate", "float",
    "fnmatchcase", "frozenset", "hashlib.sha256", "int", "isinstance", "json.dumps",
    "json.loads", "len", "list", "map", "max", "min", "module_name", "object",
    "parse_newc", "range", "read_regular", "re.fullmatch", "re.search", "regular_member",
    "select_indexes", "set", "single_gzip", "snapshot", "sorted", "stat.S_IMODE",
    "stat.S_ISDIR", "stat.S_ISREG", "str", "sum", "tuple", "type",
    "validate_binary_dump", "zip",
  }
  allowed_tails = {
    "add", "append", "copy", "decode", "encode", "endswith", "extend", "get",
    "hexdigest", "hex", "is_absolute", "is_symlink", "isspace", "items", "iterdir",
    "join", "keys", "lstat", "name", "relative_to", "removeprefix", "split",
    "splitlines", "startswith", "values",
  }
  family_items = dict(zip(FAMILY_VALIDATORS, OBSERVATION_VALIDATORS, strict=True))
  observation_arguments = {
    "_validate_archive_observation": ["label", "raw"],
    "_validate_payload_observation": ["name", "raw"],
    "_validate_tree_observation": ["kind", "before", "after"],
    "_validate_index_observation": ["kind", "name", "raw", "observation"],
    "_validate_module_observation": ["name", "filename_raw", "dependency_raw"],
    "_validate_alias_observation": ["alias", "raw"],
    "_validate_symbol_observation": ["symbol", "raw"],
    "_validate_command_observation": ["index", "observation"],
    "_validate_identity_observation": ["observation"],
    "_validate_provenance_observation": ["provenance"],
  }
  for family, item in family_items.items():
    function = functions.get(family)
    observation = functions.get(item)
    if function is None or observation is None:
      return False, f"unresolved semantic family validator: {family}"
    if ([argument.arg for argument in (*function.args.posonlyargs, *function.args.args)] !=
        ["mapped"] or function.args.kwonlyargs or function.args.vararg is not None or
        function.args.kwarg is not None or function.args.defaults or
        function.args.kw_defaults or
        [argument.arg for argument in (*observation.args.posonlyargs,
                                       *observation.args.args)] != observation_arguments[item] or
        observation.args.kwonlyargs or observation.args.vararg is not None or
        observation.args.kwarg is not None or observation.args.defaults or
        observation.args.kw_defaults):
      return False, f"{family} or {item} signature differs"
    calls = [node for node in ast.walk(function) if isinstance(node, ast.Call) and
             call_name(node) == item]
    if len(calls) != 1 or not any(
      argument.arg in loaded_names(calls[0])
      for argument in (*function.args.posonlyargs, *function.args.args,
                       *function.args.kwonlyargs)
    ) or not any(
      isinstance(node, ast.Attribute) and target_path(node) == "mapped.raw_files"
      for node in ast.walk(calls[0])
    ):
      return False, f"{family} does not reach and consume its observation validator exactly once"

  visited: set[str] = set()
  pending = list(roots)
  while pending:
    name = pending.pop()
    if name in visited or name in terminal_local:
      continue
    function = functions.get(name)
    if function is None:
      return False, f"unresolved semantic helper: {name}"
    visited.add(name)
    statements = function_statements(function)
    if any(isinstance(node, (ast.Global, ast.Nonlocal, ast.Delete, ast.Import, ast.ImportFrom,
                             ast.AsyncFunctionDef, ast.Lambda)) or
           (isinstance(node, ast.FunctionDef) and node is not function)
           for node in ast.walk(function)):
      return False, f"{name} contains mutable scope, import, delete, or nested code"
    returns = [node for node in ast.walk(function) if isinstance(node, ast.Return)]
    if returns and (len(returns) != 1 or not statements or returns[0] is not statements[-1]):
      return False, f"{name} has an early or dead return"
    if any(isinstance(node, ast.If) and isinstance(node.test, ast.Constant)
           for node in ast.walk(function)):
      return False, f"{name} contains a constant dead branch"
    called_local_functions = {
      call_name(node) for node in ast.walk(function)
      if isinstance(node, ast.Call) and call_name(node) in functions
    }
    callable_names = roots | called_local_functions | terminal_local | allowed_exact | {
      "hashlib", "json", "os", "re", "stat",
    }
    if any((isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store) and
            node.id in callable_names) or
           (isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Store))
           for node in ast.walk(function)):
      return False, f"{name} shadows or rebinds an allowed callable"
    for stored, value, _line in stored_paths(ast.Module(body=function.body, type_ignores=[])):
      value_path = target_path(value)
      value_tail = value_path.split(".")[-1] if value_path is not None else None
      if value_path in functions or value_path in allowed_exact or \
         value_path in {"hashlib", "json", "os", "re", "stat"} or value_tail in forbidden:
        return False, f"{name} aliases callable or unsafe behavior through {stored}"
    for node in ast.walk(function):
      if not isinstance(node, ast.Call):
        continue
      called = call_name(node)
      tail = node.func.attr if isinstance(node.func, ast.Attribute) else called
      if called in forbidden or tail in forbidden:
        return False, f"{name} reaches unsafe call {called or tail}"
      if called in functions:
        pending.append(called)
      elif called in terminal_local or called in allowed_exact or tail in allowed_tails:
        continue
      else:
        return False, f"{name} reaches unresolved or unapproved call {called or tail}"
  if not ((roots - terminal_local) <= visited):
    return False, "semantic read-only call graph is incomplete"
  return True, "semantic evaluator closure is transitively read-only"


def aggregate_source_shape() -> tuple[bool, str]:
  try:
    tree = ast.parse(INPUT_BYTES[SUBJECT].decode("utf-8"), filename=str(SUBJECT))
    binding_ok, binding_message = critical_callable_load_source_shape(tree)
    if not binding_ok:
      return False, binding_message
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    for name in ("operational_policy", "finalize_operational_result", "main"):
      function = functions[name]
      top_level_rebound = any(
        isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)) and any(
          isinstance(value, ast.Name) and isinstance(value.ctx, ast.Store) and value.id == name
          for target in (node.targets if isinstance(node, ast.Assign) else [node.target])
          for value in ast.walk(target)
        )
        for node in tree.body
      )
      imported = any(
        (alias.asname or alias.name.split(".")[-1]) == name
        for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
      )
      closed = function_statements(function)
      raised = closed[0] if len(closed) == 1 else None
      error = raised.exc if isinstance(raised, ast.Raise) else None
      if (sum(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name
              for node in ast.walk(tree)) != 1 or
          any(isinstance(node, ast.ClassDef) and node.name == name for node in ast.walk(tree)) or
          top_level_rebound or imported or function.args.posonlyargs or function.args.args or
          function.args.kwonlyargs or
          function.args.vararg is not None or function.args.kwarg is not None or
          not isinstance(error, ast.Call) or call_name(error) != "RecipeError" or
          len(error.args) != 1 or error.keywords or
          not isinstance(error.args[0], ast.Constant) or
          error.args[0].value != "E_CONTROL_RECIPE_UNAVAILABLE" or
          raised.cause is not None):
        return False, f"closed operational function differs: {name}"
    semantic_functions = {
      "_map_raw_control_outputs", "_collect_fixed_raw_files",
      "_read_fixed_semantic_fixture_outputs", "_read_fixed_operational_outputs",
      "_evaluate_control_semantics", *FAMILY_VALIDATORS, *OBSERVATION_VALIDATORS,
    }
    semantic_types = {"RawControlFiles", "MappedControlOutputs", "SemanticFixtureEvaluation"}
    semantic_bindings = semantic_functions | semantic_types
    string_bindings = {
      value
      for node in ast.walk(tree)
      for value in (
        (node.name if isinstance(node, (ast.ExceptHandler, ast.MatchAs, ast.MatchStar)) else
         node.rest if isinstance(node, ast.MatchMapping) else
         node.arg if isinstance(node, ast.arg) else None),
      )
      if type(value) is str
    }
    if any(sum(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name
               for node in ast.walk(tree)) != 1 for name in semantic_functions) or any(
      sum(isinstance(node, ast.ClassDef) and node.name == name for node in ast.walk(tree)) != 1
      for name in semantic_types
    ) or any(
      isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store) and
      node.id in semantic_bindings for node in ast.walk(tree)
    ) or bool(string_bindings & semantic_bindings) or any(
      isinstance(node, (ast.Global, ast.Nonlocal)) and
      bool(set(node.names) & semantic_bindings) for node in ast.walk(tree)
    ) or any(
      isinstance(node, ast.Delete) and any(target_path(target) in semantic_bindings
                                           for target in node.targets)
      for node in ast.walk(tree)
    ) or any(
      isinstance(node, (ast.Import, ast.ImportFrom)) and any(
        (alias.asname or alias.name.split(".")[-1]) in semantic_bindings
        for alias in node.names
      ) for node in ast.walk(tree)
    ):
      return False, "semantic type or function is duplicated, aliased, shadowed, or rebound"
    mapped_classes = [node for node in tree.body
                      if isinstance(node, ast.ClassDef) and node.name == "MappedControlOutputs"]
    if len(mapped_classes) != 1:
      return False, "MappedControlOutputs is not one top-level class"
    mapped_class = mapped_classes[0]
    mapped_fields = [node for node in mapped_class.body if not (
      isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and
      type(node.value.value) is str
    )]
    if not (len(mapped_fields) == 1 and isinstance(mapped_fields[0], ast.AnnAssign) and
            isinstance(mapped_fields[0].target, ast.Name) and
            mapped_fields[0].target.id == "raw_files" and mapped_fields[0].value is None and
            isinstance(mapped_fields[0].annotation, ast.Name) and
            mapped_fields[0].annotation.id == "RawControlFiles"):
      return False, "MappedControlOutputs must retain only the exact RawControlFiles object"
    aggregate = functions["_evaluate_control_semantics"]
    mapper = functions["_map_raw_control_outputs"]
    collector = functions["_collect_fixed_raw_files"]
    fixture_reader = functions["_read_fixed_semantic_fixture_outputs"]
    operational_reader = functions["_read_fixed_operational_outputs"]
    if not exact_reader(fixture_reader, "SEMANTIC_FIXTURE_PATHS") or \
       not exact_reader(operational_reader, "SEMANTIC_OPERATIONAL_PATHS"):
      return False, "fixed readers do not feed the exact fixed collector bytes to the mapper"
    if [item.arg for item in collector.args.args] != ["paths"] or collector.args.posonlyargs or \
       collector.args.kwonlyargs or collector.args.vararg is not None or \
       collector.args.kwarg is not None or collector.args.defaults or \
       collector.args.kw_defaults:
      return False, "fixed raw collector signature differs"
    collector_body = function_statements(collector)
    policy_names = (
      "record_root", "control_root", "lookup_root", "empty_config", "early_path", "main_path",
    )
    unpack = collector_body[0] if collector_body else None
    if not (len(collector_body) == 9 and isinstance(unpack, ast.Assign) and
            len(unpack.targets) == 1 and isinstance(unpack.targets[0], (ast.Tuple, ast.List)) and
            tuple(item.id for item in unpack.targets[0].elts if isinstance(item, ast.Name)) ==
            policy_names and len(unpack.targets[0].elts) == len(policy_names) and
            isinstance(unpack.value, ast.Name) and unpack.value.id == "paths"):
      return False, "collector does not unpack every fixed policy slot once in exact order"

    def exact_path_argument(value: ast.expr, name: str) -> bool:
      return bool(isinstance(value, ast.Call) and call_name(value) == "Path" and
                  len(value.args) == 1 and not value.keywords and
                  isinstance(value.args[0], ast.Name) and value.args[0].id == name)

    def exact_bound_read(statement: ast.stmt, target: str, called: str,
                         path_name: str) -> bool:
      call = statement_call(statement)
      return bool(assignment_name(statement) == target and call is not None and
                  call_name(call) == called and len(call.args) == 1 and not call.keywords and
                  exact_path_argument(call.args[0], path_name))

    records_call = statement_call(collector_body[2])
    if not (exact_bound_read(collector_body[1], "record_state", "snapshot", "record_root") and
            assignment_name(collector_body[2]) == "records" and records_call is not None and
            call_name(records_call) == "tuple" and len(records_call.args) == 1 and
            not records_call.keywords and isinstance(records_call.args[0], ast.GeneratorExp)):
      return False, "collector does not capture the exact record tree and record generator"
    generator = records_call.args[0]
    if not (len(generator.generators) == 1 and
            isinstance(generator.generators[0].target, ast.Name) and
            generator.generators[0].target.id == "index" and
            not generator.generators[0].ifs and generator.generators[0].is_async == 0 and
            isinstance(generator.generators[0].iter, ast.Call) and
            call_name(generator.generators[0].iter) == "range" and
            len(generator.generators[0].iter.args) == 1 and
            not generator.generators[0].iter.keywords and
            isinstance(generator.generators[0].iter.args[0], ast.Name) and
            generator.generators[0].iter.args[0].id == "SEMANTIC_RECORDS" and
            isinstance(generator.elt, (ast.Tuple, ast.List)) and len(generator.elt.elts) == 3):
      return False, "collector record generator does not iterate exact range(SEMANTIC_RECORDS)"

    def exact_record_read(value: ast.expr, suffix: str) -> bool:
      if not (isinstance(value, ast.Call) and call_name(value) == "read_regular" and
              len(value.args) == 1 and not value.keywords and
              isinstance(value.args[0], ast.BinOp) and isinstance(value.args[0].op, ast.Div) and
              exact_path_argument(value.args[0].left, "record_root") and
              isinstance(value.args[0].right, ast.JoinedStr)):
        return False
      pieces = value.args[0].right.values
      return bool(
        len(pieces) == 3 and isinstance(pieces[0], ast.Constant) and
        pieces[0].value == "record-" and isinstance(pieces[1], ast.FormattedValue) and
        isinstance(pieces[1].value, ast.Name) and pieces[1].value.id == "index" and
        pieces[1].conversion == -1 and isinstance(pieces[1].format_spec, ast.JoinedStr) and
        len(pieces[1].format_spec.values) == 1 and
        isinstance(pieces[1].format_spec.values[0], ast.Constant) and
        pieces[1].format_spec.values[0].value == "03d" and
        isinstance(pieces[2], ast.Constant) and pieces[2].value == suffix
      )

    if not all(exact_record_read(value, suffix) for value, suffix in zip(
      generator.elt.elts, (".stdout", ".stderr", ".json"), strict=True,
    )):
      return False, "collector does not read each exact stdout, stderr and report path"
    fixed_reads = (
      (3, "control_state", "snapshot", "control_root"),
      (4, "lookup_state", "snapshot", "lookup_root"),
      (5, "empty_config_raw", "read_regular", "empty_config"),
      (6, "early_raw", "read_regular", "early_path"),
      (7, "main_raw", "read_regular", "main_path"),
    )
    if not all(exact_bound_read(collector_body[position], target, called, path_name)
               for position, target, called, path_name in fixed_reads):
      return False, "collector does not read or snapshot every fixed non-record policy slot"
    returned = collector_body[8]
    result_call = returned.value if isinstance(returned, ast.Return) else None
    returned_names = (
      "paths", "record_state", "records", "control_state", "lookup_state",
      "empty_config_raw", "early_raw", "main_raw",
    )
    if not (isinstance(result_call, ast.Call) and call_name(result_call) == "RawControlFiles" and
            not result_call.args and [keyword.arg for keyword in result_call.keywords] ==
            list(returned_names) and all(isinstance(keyword.value, ast.Name) and
                                         keyword.value.id == keyword.arg
                                         for keyword in result_call.keywords)):
      return False, "collector return does not bind every fixed read into RawControlFiles"
    mapper_arguments = (*mapper.args.posonlyargs, *mapper.args.args, *mapper.args.kwonlyargs)
    if (mapper.args.vararg is not None or mapper.args.kwarg is not None or
        len(mapper_arguments) != 1 or mapper_arguments[0].arg != "raw_files" or
        mapper.args.defaults or mapper.args.kw_defaults):
      return False, "raw mapper must accept only the raw_files bundle"
    mapper_body = function_statements(mapper)
    mapper_return = mapper_body[0] if len(mapper_body) == 1 else None
    mapper_call = mapper_return.value if isinstance(mapper_return, ast.Return) else None
    if not (isinstance(mapper_call, ast.Call) and
            call_name(mapper_call) == "MappedControlOutputs" and not mapper_call.args and
            len(mapper_call.keywords) == 1 and mapper_call.keywords[0].arg == "raw_files" and
            isinstance(mapper_call.keywords[0].value, ast.Name) and
            mapper_call.keywords[0].value.id == "raw_files"):
      return False, "raw mapper does not retain the exact complete RawControlFiles bundle"

    body = function_statements(aggregate)
    first_call = statement_call(body[0]) if body else None
    if not body or assignment_name(body[0]) != "mapped" or first_call is None or \
       call_name(first_call) != "_read_fixed_semantic_fixture_outputs":
      return False, "aggregate does not start from the fixed fixture reader"
    if any(isinstance(statement, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try,
                                  ast.With, ast.AsyncWith, ast.Match, ast.Raise))
           for statement in body):
      return False, "aggregate is not straight-line reachable code"
    positions: list[int] = []
    tainted = {"mapped"}
    for position, statement in enumerate(body[1:-1], start=1):
      name = assignment_name(statement)
      if name is not None and loaded_names(statement) & tainted:
        tainted.add(name)
      call = statement_call(statement)
      called = call_name(call) if call is not None else None
      if called in FAMILY_VALIDATORS:
        if call is None or len(call.args) != 1 or call.keywords or \
           not (loaded_names(call.args[0]) & tainted):
          return False, "family validator does not consume mapped raw data"
        positions.append(position)
    family_order = [call_name(statement_call(body[position])) for position in positions]
    if family_order != list(FAMILY_VALIDATORS):
      return False, "aggregate does not call every family validator once in fixed order"
    all_family_calls = [node for node in ast.walk(aggregate) if isinstance(node, ast.Call) and
                        call_name(node) in FAMILY_VALIDATORS]
    direct_family_calls = [statement_call(body[position]) for position in positions]
    if len(all_family_calls) != len(FAMILY_VALIDATORS) or any(
      call is not direct for call, direct in zip(all_family_calls, direct_family_calls, strict=True)
    ):
      return False, "aggregate contains a nested, duplicate, or dead family validator call"
    final = body[-1]
    if not isinstance(final, ast.Return) or not (loaded_names(final) & tainted):
      return False, "aggregate result is not derived from its mapped raw model"
    if any(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)) and
           node is not aggregate for node in ast.walk(aggregate)):
      return False, "aggregate contains a nested or dead callable"
    readonly_ok, readonly_message = semantic_readonly_source_shape(tree, functions)
    if not readonly_ok:
      return False, readonly_message
    return True, "fixed readers, mapper and aggregate have reachable read-only raw data flow"
  except (KeyError, SyntaxError, UnicodeError, TypeError, ValueError) as error:
    return False, f"aggregate source inspection failed: {type(error).__name__}"


def publication_source_shape() -> tuple[bool, str]:
  try:
    tree = ast.parse(INPUT_BYTES[SUBJECT].decode("utf-8"), filename=str(SUBJECT))
    binding_ok, binding_message = critical_callable_load_source_shape(tree)
    if not binding_ok:
      return False, binding_message
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    required_functions = {
      "_rename_noreplace_errcheck", "_rename_noreplace",
      "_semantic_fixture_work_membership", "_semantic_fixture_result_bytes",
      "publish_semantic_fixture_result",
    }
    semantic_functions = {
      "_map_raw_control_outputs", "_collect_fixed_raw_files",
      "_read_fixed_semantic_fixture_outputs", "_read_fixed_operational_outputs",
      "_evaluate_control_semantics", *FAMILY_VALIDATORS, *OBSERVATION_VALIDATORS,
    }
    if any(sum(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name
               for node in ast.walk(tree)) != 1
           for name in required_functions):
      return False, "publication function is missing, duplicated, or rebound"
    publisher = functions["publish_semantic_fixture_result"]
    rename_helper = functions["_rename_noreplace"]
    errcheck = functions["_rename_noreplace_errcheck"]
    membership = functions["_semantic_fixture_work_membership"]
    result_helper = functions["_semantic_fixture_result_bytes"]

    imports = [(alias.name, alias.asname) for node in tree.body if isinstance(node, ast.Import)
               for alias in node.names]
    if any(imports.count((name, None)) != 1 for name in ("ctypes", "errno", "os")) or any(
      isinstance(node, ast.ImportFrom) and node.module in {"ctypes", "errno", "os"}
      for node in tree.body
    ):
      return False, "ctypes, errno and os must each be imported once and never imported by alias"

    stores = stored_paths(tree)

    def sole_value(name: str) -> ast.expr | None:
      values = [value for stored, value, _line in stores if stored == name]
      return values[0] if len(values) == 1 else None

    def sole_line(name: str) -> int:
      lines = [line for stored, _value, line in stores if stored == name]
      return lines[0] if len(lines) == 1 else -1

    def literal_string_tuple(value: ast.expr | None, expected: tuple[str, ...]) -> bool:
      return bool(isinstance(value, (ast.Tuple, ast.List)) and
                  all(isinstance(item, ast.Constant) and type(item.value) is str
                      for item in value.elts) and
                  tuple(item.value for item in value.elts) == expected)

    def exact_name(value: ast.expr, name: str) -> bool:
      return isinstance(value, ast.Name) and value.id == name

    def exact_require(statement: ast.stmt, code: str) -> ast.expr | None:
      call = statement_call(statement)
      if not (isinstance(statement, ast.Expr) and call is not None and
              call_name(call) == "_require" and len(call.args) == 2 and not call.keywords and
              isinstance(call.args[1], ast.Constant) and call.args[1].value == code):
        return None
      return call.args[0]

    if not (isinstance(sole_value("RENAME_NOREPLACE"), ast.Constant) and
            sole_value("RENAME_NOREPLACE").value == 1 and
            isinstance(sole_value("_AT_FDCWD"), ast.UnaryOp) and
            isinstance(sole_value("_AT_FDCWD").op, ast.USub) and
            isinstance(sole_value("_AT_FDCWD").operand, ast.Constant) and
            sole_value("_AT_FDCWD").operand.value == 100):
      return False, "renameat2 constants are not exact literal 1 and -100"
    if not fixed_path_call(sole_value("SEMANTIC_FIXTURE_PENDING"), str(PENDING)) or \
       not fixed_path_call(sole_value("SEMANTIC_FIXTURE_RESULT"), str(FINAL)):
      return False, "fixture pending or result constant is not the exact fixed Path"
    if not literal_string_tuple(sole_value("SEMANTIC_FIXTURE_PATHS"), FIXTURE_PATH_POLICY) or \
       not literal_string_tuple(sole_value("SEMANTIC_OPERATIONAL_PATHS"), OPERATIONAL_PATH_POLICY) or \
       not (isinstance(sole_value("SEMANTIC_RECORDS"), ast.Constant) and
            sole_value("SEMANTIC_RECORDS").value == 424):
      return False, "semantic record count or fixed path policy differs"
    work_value = sole_value("SEMANTIC_FIXTURE_WORK_MEMBERS")
    if not (isinstance(work_value, ast.Call) and call_name(work_value) == "frozenset" and
            len(work_value.args) == 1 and not work_value.keywords and
            literal_string_tuple(work_value.args[0], tuple(sorted(expected_fixture_members())))):
      return False, "fixed fixture work membership constant differs"

    libc = sole_value("_SEMANTIC_LIBC")
    if not (isinstance(libc, ast.Call) and call_name(libc) == "ctypes.CDLL" and
            len(libc.args) == 1 and isinstance(libc.args[0], ast.Constant) and
            libc.args[0].value is None and len(libc.keywords) == 1 and
            libc.keywords[0].arg == "use_errno" and
            isinstance(libc.keywords[0].value, ast.Constant) and
            libc.keywords[0].value.value is True):
      return False, "publisher does not bind the real libc directly"
    argtypes = sole_value("_SEMANTIC_LIBC.renameat2.argtypes")
    expected_argtypes = (
      "ctypes.c_int", "ctypes.c_char_p", "ctypes.c_int", "ctypes.c_char_p",
      "ctypes.c_uint",
    )
    if not (isinstance(argtypes, ast.List) and len(argtypes.elts) == 5 and
            tuple(target_path(item) for item in argtypes.elts) == expected_argtypes and
            target_path(sole_value("_SEMANTIC_LIBC.renameat2.restype")) == "ctypes.c_int" and
            exact_name(sole_value("_SEMANTIC_LIBC.renameat2.errcheck"),
                       "_rename_noreplace_errcheck") and
            errcheck.lineno < sole_line("_SEMANTIC_LIBC") <
            sole_line("_SEMANTIC_LIBC.renameat2.argtypes") <
            sole_line("_SEMANTIC_LIBC.renameat2.restype") <
            sole_line("_SEMANTIC_LIBC.renameat2.errcheck")):
      return False, "renameat2 ctypes argtypes, restype, errcheck, or binding order differs"

    protected = {
      "ctypes", "errno", "os", "ctypes.CDLL", "ctypes.get_errno", "errno.EEXIST",
      "os.fsencode", "RENAME_NOREPLACE", "_AT_FDCWD", "_SEMANTIC_LIBC",
      "_SEMANTIC_LIBC.renameat2",
      "_SEMANTIC_LIBC.renameat2.argtypes", "_SEMANTIC_LIBC.renameat2.restype",
      "_SEMANTIC_LIBC.renameat2.errcheck", "SEMANTIC_FIXTURE_PATHS",
      "SEMANTIC_OPERATIONAL_PATHS", "SEMANTIC_RECORDS", "SEMANTIC_FIXTURE_WORK_MEMBERS",
      "SEMANTIC_FIXTURE_PENDING", "SEMANTIC_FIXTURE_RESULT",
      "_rename_noreplace_errcheck", "_rename_noreplace",
      "_semantic_fixture_work_membership", "_semantic_fixture_result_bytes",
      "publish_semantic_fixture_result", *semantic_functions,
    }
    zero_store_names = {
      "ctypes", "errno", "os", "ctypes.CDLL", "ctypes.get_errno", "errno.EEXIST",
      "os.fsencode", "_SEMANTIC_LIBC.renameat2", "_rename_noreplace_errcheck", "_rename_noreplace",
      "_semantic_fixture_work_membership", "_semantic_fixture_result_bytes",
      "publish_semantic_fixture_result", *semantic_functions,
    }
    expected_store_counts = {
      name: 0 if name in zero_store_names else 1 for name in protected
    }
    protected_simple = {name for name in protected if "." not in name}
    string_bindings = {
      value
      for node in ast.walk(tree)
      for value in (
        (node.name if isinstance(node, (ast.ExceptHandler, ast.MatchAs, ast.MatchStar)) else
         node.rest if isinstance(node, ast.MatchMapping) else
         node.arg if isinstance(node, ast.arg) else None),
      )
      if type(value) is str
    }
    allowed_direct_imports = {
      id(alias) for node in tree.body if isinstance(node, ast.Import) for alias in node.names
      if alias.asname is None and alias.name in {"ctypes", "errno", "os"}
    }
    if any(sum(stored == name for stored, _value, _line in stores) != count
           for name, count in expected_store_counts.items()) or any(
      sum(isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store) and node.id == name
          for node in ast.walk(tree)) != count
      for name, count in expected_store_counts.items() if "." not in name
    ) or any(
      sum(isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Store) and
          target_path(node) == name for node in ast.walk(tree)) != count
      for name, count in expected_store_counts.items() if "." in name
    ) or any(
      isinstance(node, (ast.Global, ast.Nonlocal)) and
      bool(set(getattr(node, "names", ())) & protected)
      for node in ast.walk(tree)
    ) or any(
      target_path(target) in protected
      for node in ast.walk(tree) if isinstance(node, ast.Delete) for target in node.targets
    ) or any(
      isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and
      node.name in (protected - required_functions - semantic_functions)
      for node in ast.walk(tree)
    ) or any(
      isinstance(node, ast.ImportFrom) and any(
        (alias.asname or alias.name) in protected for alias in node.names
      )
      for node in ast.walk(tree)
    ) or bool(string_bindings & protected_simple) or any(
      (alias.asname or alias.name.split(".")[0]) in protected_simple and
      id(alias) not in allowed_direct_imports
      for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names
    ):
      return False, "publication constant, binding, or function is later rebound or deleted"

    unsafe_tails = {
      "Popen", "call", "check_call", "check_output", "delattr", "getattr", "link",
      "remove", "rename", "replace", "rmdir", "rmtree", "run", "setattr", "spawn",
      "symlink", "system", "unlink",
    }
    for stored, value, _line in stores:
      value_path = target_path(value)
      value_tail = value_path.split(".")[-1] if value_path is not None else None
      if stored not in {
        "_SEMANTIC_LIBC.renameat2.argtypes", "_SEMANTIC_LIBC.renameat2.restype",
        "_SEMANTIC_LIBC.renameat2.errcheck",
      } and (value_path in protected or value_tail in unsafe_tails | {"renameat2"}):
        return False, "module aliases a protected or unsafe callable"
    whole_allowed_exact = {
      "FileState", "Module", "Path", "RecipeError", "RuntimeError", "TreeState",
      "ValueError", "alias_entries", "all", "any", "bool", "bytes", "dataclass",
      "dependency_entries", "dict", "enumerate", "float", "fnmatchcase", "frozenset",
      "hashlib.sha256", "int", "isinstance", "json.dumps", "json.loads", "len", "list",
      "map", "max", "min", "module_name", "object", "os.close", "os.fsencode",
      "os.fstat", "os.open", "os.read", "parse_newc", "range", "read_regular",
      "re.fullmatch", "re.search", "regular_member", "select_indexes", "set", "single_gzip",
      "snapshot", "sorted", "stat.S_IMODE", "stat.S_ISDIR", "stat.S_ISREG", "str", "sum",
      "tuple", "type", "validate_binary_dump", "write_new", "zip", "ctypes.CDLL",
      "ctypes.get_errno", "_SEMANTIC_LIBC.renameat2",
    } | {
      node.name for node in ast.walk(tree)
      if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
    }
    whole_allowed_tails = {
      "add", "append", "copy", "decode", "encode", "endswith", "exists", "extend", "get",
      "hexdigest", "hex", "is_absolute", "is_symlink", "isspace", "items", "iterdir",
      "join", "keys", "lstat", "relative_to", "removeprefix", "split", "splitlines",
      "startswith", "update", "values",
    }
    rename_calls_whole = []
    for node in ast.walk(tree):
      if not isinstance(node, ast.Call):
        continue
      called = target_path(node.func)
      tail = node.func.attr if isinstance(node.func, ast.Attribute) else called
      if called in {"getattr", "setattr", "delattr"} or tail in unsafe_tails or \
         (called not in whole_allowed_exact and tail not in whole_allowed_tails):
        return False, "module contains unresolved, dynamic, overwrite, unlink, or subprocess call"
      if tail == "renameat2":
        rename_calls_whole.append(node)

    err_body = function_statements(errcheck)
    if ([argument.arg for argument in (*errcheck.args.posonlyargs, *errcheck.args.args)] !=
        ["result", "function", "arguments"] or errcheck.args.kwonlyargs or
        errcheck.args.vararg is not None or errcheck.args.kwarg is not None or
        len(err_body) != 2 or not isinstance(err_body[0], ast.If) or err_body[0].orelse or
        len(err_body[0].body) != 3 or not isinstance(err_body[1], ast.Return) or
        not exact_name(err_body[1].value, "result")):
      return False, "renameat2 errcheck signature or straight-line result handling differs"
    outer = err_body[0]
    error_assignment, exists_branch, invalid_raise = outer.body
    error_call = statement_call(error_assignment)
    if not (isinstance(outer.test, ast.Compare) and exact_name(outer.test.left, "result") and
            len(outer.test.ops) == len(outer.test.comparators) == 1 and
            isinstance(outer.test.ops[0], ast.NotEq) and
            isinstance(outer.test.comparators[0], ast.Constant) and
            outer.test.comparators[0].value == 0 and assignment_name(error_assignment) == "error" and
            error_call is not None and target_path(error_call.func) == "ctypes.get_errno" and
            not error_call.args and not error_call.keywords and isinstance(exists_branch, ast.If) and
            not exists_branch.orelse and len(exists_branch.body) == 1 and
            isinstance(exists_branch.test, ast.Compare) and exact_name(exists_branch.test.left, "error") and
            len(exists_branch.test.ops) == len(exists_branch.test.comparators) == 1 and
            isinstance(exists_branch.test.ops[0], ast.Eq) and
            target_path(exists_branch.test.comparators[0]) == "errno.EEXIST"):
      return False, "renameat2 errcheck does not inspect the exact errno once"

    def exact_recipe_raise(statement: ast.stmt, code: str) -> bool:
      return bool(isinstance(statement, ast.Raise) and isinstance(statement.exc, ast.Call) and
                  call_name(statement.exc) == "RecipeError" and len(statement.exc.args) == 1 and
                  not statement.exc.keywords and isinstance(statement.exc.args[0], ast.Constant) and
                  statement.exc.args[0].value == code and statement.cause is None)

    if not exact_recipe_raise(exists_branch.body[0], "E_CONTROL_SEMANTIC_EXISTS") or \
       not exact_recipe_raise(invalid_raise, "E_CONTROL_SEMANTIC_INVALID") or \
       sum(isinstance(node, ast.Call) and target_path(node.func) == "ctypes.get_errno"
           for node in ast.walk(errcheck)) != 1:
      return False, "renameat2 errcheck error translation differs"

    rename_body = function_statements(rename_helper)
    rename_args = (*rename_helper.args.posonlyargs, *rename_helper.args.args)
    if ([argument.arg for argument in rename_args] != ["source", "target"] or
        rename_helper.args.kwonlyargs or rename_helper.args.vararg is not None or
        rename_helper.args.kwarg is not None or len(rename_body) != 1 or
        not isinstance(rename_body[0], ast.Expr) or not isinstance(rename_body[0].value, ast.Call)):
      return False, "no-replace helper signature or straight-line body differs"
    rename_call = rename_body[0].value

    def exact_fsencode(value: ast.expr, name: str) -> bool:
      return bool(isinstance(value, ast.Call) and target_path(value.func) == "os.fsencode" and
                  len(value.args) == 1 and not value.keywords and exact_name(value.args[0], name))

    if not (target_path(rename_call.func) == "_SEMANTIC_LIBC.renameat2" and
            len(rename_call.args) == 5 and not rename_call.keywords and
            exact_name(rename_call.args[0], "_AT_FDCWD") and
            exact_fsencode(rename_call.args[1], "source") and
            exact_name(rename_call.args[2], "_AT_FDCWD") and
            exact_fsencode(rename_call.args[3], "target") and
            exact_name(rename_call.args[4], "RENAME_NOREPLACE") and
            rename_calls_whole == [rename_call]):
      return False, "helper does not make the one direct fixed-argument libc renameat2 call"

    member_body = function_statements(membership)
    if (membership.args.posonlyargs or membership.args.args or membership.args.kwonlyargs or
        membership.args.vararg is not None or membership.args.kwarg is not None or
        len(member_body) != 1 or not isinstance(member_body[0], ast.Return) or
        not isinstance(member_body[0].value, ast.Call) or
        call_name(member_body[0].value) != "frozenset" or len(member_body[0].value.args) != 1 or
        member_body[0].value.keywords):
      return False, "membership helper does not return the exact /work set"
    generator = member_body[0].value.args[0]
    if not (isinstance(generator, ast.GeneratorExp) and
            isinstance(generator.elt, ast.Attribute) and generator.elt.attr == "name" and
            exact_name(generator.elt.value, "path") and len(generator.generators) == 1 and
            exact_name(generator.generators[0].target, "path") and
            not generator.generators[0].ifs and generator.generators[0].is_async == 0 and
            isinstance(generator.generators[0].iter, ast.Call) and
            isinstance(generator.generators[0].iter.func, ast.Attribute) and
            generator.generators[0].iter.func.attr == "iterdir" and
            not generator.generators[0].iter.args and
            not generator.generators[0].iter.keywords and
            isinstance(generator.generators[0].iter.func.value, ast.Call) and
            call_name(generator.generators[0].iter.func.value) == "Path" and
            len(generator.generators[0].iter.func.value.args) == 1 and
            isinstance(generator.generators[0].iter.func.value.args[0], ast.Constant) and
            generator.generators[0].iter.func.value.args[0].value == "/work" and
            not generator.generators[0].iter.func.value.keywords):
      return False, "membership helper does not compute exact Path('/work').iterdir() names"

    result_args = (*result_helper.args.posonlyargs, *result_helper.args.args)
    result_body = function_statements(result_helper)
    result_tainted = {"evaluation"}
    for statement in result_body[:-1]:
      if loaded_names(statement) & result_tainted:
        result_tainted.update(assignment_names(statement))
    if ([argument.arg for argument in result_args] != ["evaluation"] or
        result_helper.args.kwonlyargs or result_helper.args.vararg is not None or
        result_helper.args.kwarg is not None or not result_body or
        not isinstance(result_body[-1], ast.Return) or
        not (loaded_names(result_body[-1]) & result_tainted)):
      return False, "result-byte helper does not consume the prepared evaluation"

    body = function_statements(publisher)
    if (publisher.args.posonlyargs or publisher.args.args or publisher.args.kwonlyargs or
        publisher.args.vararg is not None or publisher.args.kwarg is not None or len(body) != 11):
      return False, "fixture publisher must be the exact no-argument eleven-statement sequence"

    def assigned_exact_call(statement: ast.stmt, target: str, called: str,
                            arguments: tuple[str, ...] = ()) -> bool:
      call = statement_call(statement)
      return bool(assignment_name(statement) == target and call is not None and
                  target_path(call.func) == called and not call.keywords and
                  len(call.args) == len(arguments) and
                  all(exact_name(value, name) for value, name in zip(call.args, arguments,
                                                                      strict=True)))

    before_exists = exact_require(body[1], "E_CONTROL_SEMANTIC_EXISTS")
    before_exact = exact_require(body[2], "E_CONTROL_SEMANTIC_INVALID")
    after_exact = exact_require(body[7], "E_CONTROL_SEMANTIC_INVALID")
    acceptance_call = statement_call(body[5])
    if not assigned_exact_call(body[0], "membership_before",
                               "_semantic_fixture_work_membership") or \
       before_exists is None or before_exact is None or \
       not assigned_exact_call(body[3], "evaluation", "_evaluate_control_semantics") or \
       not assigned_exact_call(body[4], "result_raw", "_semantic_fixture_result_bytes",
                               ("evaluation",)) or \
       assignment_name(body[5]) != "acceptance" or acceptance_call is None or \
       target_path(acceptance_call.func) != "SemanticFixtureAcceptance" or \
       not {"evaluation", "result_raw"} <= loaded_names(body[5]) or \
       not assigned_exact_call(body[6], "membership_after",
                               "_semantic_fixture_work_membership") or after_exact is None:
      return False, "publisher preparation and membership-check statement order differs"
    if not (isinstance(before_exists, ast.BoolOp) and isinstance(before_exists.op, ast.And) and
            len(before_exists.values) == 2 and all(
              isinstance(value, ast.Compare) and len(value.ops) == len(value.comparators) == 1 and
              isinstance(value.ops[0], ast.NotIn) and exact_name(value.comparators[0],
                                                                "membership_before")
              for value in before_exists.values
            ) and loaded_names(before_exists) == {
              "SEMANTIC_FIXTURE_PENDING", "SEMANTIC_FIXTURE_RESULT", "membership_before",
            }):
      return False, "publisher does not consume the first membership for both stale paths"
    if not (isinstance(before_exact, ast.Compare) and len(before_exact.ops) == 1 and
            isinstance(before_exact.ops[0], ast.Eq) and
            loaded_names(before_exact) == {"membership_before", "SEMANTIC_FIXTURE_WORK_MEMBERS"}):
      return False, "publisher does not check exact /work membership before evaluation"
    if not (isinstance(after_exact, ast.Compare) and len(after_exact.ops) == 2 and
            all(isinstance(operator, ast.Eq) for operator in after_exact.ops) and
            loaded_names(after_exact) == {
              "membership_after", "membership_before", "SEMANTIC_FIXTURE_WORK_MEMBERS",
            }):
      return False, "publisher does not recheck and consume unchanged exact membership"
    write_call = statement_call(body[8])
    publish_call = statement_call(body[9])
    returned = body[10]
    if not (isinstance(body[8], ast.Expr) and write_call is not None and
            target_path(write_call.func) == "write_new" and not write_call.keywords and
            len(write_call.args) == 2 and exact_name(write_call.args[0],
                                                    "SEMANTIC_FIXTURE_PENDING") and
            exact_name(write_call.args[1], "result_raw") and isinstance(body[9], ast.Expr) and
            publish_call is not None and target_path(publish_call.func) == "_rename_noreplace" and
            not publish_call.keywords and len(publish_call.args) == 2 and
            exact_name(publish_call.args[0], "SEMANTIC_FIXTURE_PENDING") and
            exact_name(publish_call.args[1], "SEMANTIC_FIXTURE_RESULT") and
            isinstance(returned, ast.Return) and exact_name(returned.value, "acceptance")):
      return False, "exclusive pending write, final no-replace rename, or precomputed return differs"
    publisher_calls = [target_path(node.func) for node in ast.walk(publisher)
                       if isinstance(node, ast.Call)]
    allowed_publisher = {
      "_semantic_fixture_work_membership", "_evaluate_control_semantics",
      "_semantic_fixture_result_bytes", "_sha256", "_require", "write_new",
      "_rename_noreplace", "SemanticFixtureAcceptance", "str",
    }
    if any(name not in allowed_publisher for name in publisher_calls) or \
       publisher_calls.count("_evaluate_control_semantics") != 1 or \
       publisher_calls.count("_semantic_fixture_work_membership") != 2 or \
       publisher_calls.count("_semantic_fixture_result_bytes") != 1 or \
       publisher_calls.count("_require") != 3 or \
       publisher_calls.count("_sha256") != 1 or \
       publisher_calls.count("SemanticFixtureAcceptance") != 1 or \
       publisher_calls.count("write_new") != 1 or \
       publisher_calls.count("_rename_noreplace") != 1:
      return False, "publisher direct calls are not the exact closed allowlist"
    hash_calls = [node for node in ast.walk(publisher) if isinstance(node, ast.Call) and
                  target_path(node.func) == "_sha256"]
    if not (len(hash_calls) == 1 and len(hash_calls[0].args) == 1 and
            not hash_calls[0].keywords and exact_name(hash_calls[0].args[0], "result_raw")):
      return False, "publisher does not precompute the result hash from result_raw"

    abi_targets = [
      node for node in ast.walk(tree) if isinstance(node, ast.Attribute) and
      isinstance(node.ctx, ast.Store) and target_path(node) in {
        "_SEMANTIC_LIBC.renameat2.argtypes", "_SEMANTIC_LIBC.renameat2.restype",
        "_SEMANTIC_LIBC.renameat2.errcheck",
      }
    ]
    allowed_protected_nodes: set[int] = {
      id(libc.func), id(error_call.func), id(exists_branch.test.comparators[0]),
      id(rename_call.func), id(rename_call.args[1].func), id(rename_call.args[3].func),
      id(sole_value("_SEMANTIC_LIBC.renameat2.errcheck")),
    }
    for target in abi_targets:
      allowed_protected_nodes.update(
        id(node) for node in ast.walk(target) if isinstance(node, (ast.Attribute, ast.Name))
      )
    allowed_protected_nodes.update(
      id(node) for root in (
        libc.func, error_call.func, exists_branch.test.comparators[0], rename_call.func,
        rename_call.args[1].func, rename_call.args[3].func,
      ) for node in ast.walk(root) if isinstance(node, (ast.Attribute, ast.Name))
    )
    guarded_callables = {
      "_SEMANTIC_LIBC", "_evaluate_control_semantics", "_rename_noreplace",
      "_rename_noreplace_errcheck", "_semantic_fixture_result_bytes",
      "_semantic_fixture_work_membership", "publish_semantic_fixture_result", "write_new",
      "__import__", "delattr", "eval", "exec", "getattr", "open", "setattr",
    } | semantic_functions
    allowed_guarded_names = {
      id(call.func) for call in ast.walk(publisher)
      if isinstance(call, ast.Call) and isinstance(call.func, ast.Name) and
      call.func.id in guarded_callables
    } | {
      id(call.func) for call in ast.walk(tree)
      if isinstance(call, ast.Call) and isinstance(call.func, ast.Name) and
      call.func.id == "write_new"
    } | {
      id(call.func) for name in semantic_functions for call in ast.walk(functions[name])
      if isinstance(call, ast.Call) and isinstance(call.func, ast.Name) and
      call.func.id in semantic_functions
    } | {
      id(sole_value("_SEMANTIC_LIBC.renameat2.errcheck")),
    }
    protected_attributes = {
      "ctypes.CDLL", "ctypes.get_errno", "errno.EEXIST", "os.fsencode",
      "_SEMANTIC_LIBC.renameat2", "_SEMANTIC_LIBC.renameat2.argtypes",
      "_SEMANTIC_LIBC.renameat2.restype", "_SEMANTIC_LIBC.renameat2.errcheck",
    }
    for node in ast.walk(tree):
      if isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load):
        path = target_path(node)
        if (path in protected_attributes or node.attr in unsafe_tails) and \
           id(node) not in allowed_protected_nodes:
          return False, "protected or unsafe callable attribute is aliased or loaded indirectly"
      if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and \
         node.id in guarded_callables and id(node) not in allowed_guarded_names and \
         id(node) not in allowed_protected_nodes:
        return False, "protected callable is aliased, captured, or invoked outside its fixed site"

    readonly_ok, readonly_message = semantic_readonly_source_shape(tree, functions)
    if not readonly_ok:
      return False, readonly_message
    publication_terminals = {
      "_require", "_sha256", "bytes", "dict", "hashlib.sha256", "int", "isinstance",
      "json.dumps", "len", "list", "sorted", "str", "tuple", "type",
    }
    publication_tails = {"decode", "encode", "hexdigest", "items", "keys", "values"}
    visited: set[str] = set()
    pending = ["_semantic_fixture_result_bytes"]
    while pending:
      name = pending.pop()
      if name in visited:
        continue
      function = functions.get(name)
      if function is None:
        return False, f"unresolved publication helper: {name}"
      visited.add(name)
      statements = function_statements(function)
      if any(isinstance(node, (ast.Global, ast.Nonlocal, ast.Delete, ast.Import,
                               ast.ImportFrom, ast.AsyncFunctionDef, ast.Lambda)) or
             (isinstance(node, ast.FunctionDef) and node is not function)
             for node in ast.walk(function)):
        return False, "publication helper contains mutable scope, import, delete, or nested code"
      returns = [node for node in ast.walk(function) if isinstance(node, ast.Return)]
      if len(returns) != 1 or not statements or returns[0] is not statements[-1]:
        return False, "publication helper contains an early or dead return"
      for call in (node for node in ast.walk(function) if isinstance(node, ast.Call)):
        called = target_path(call.func)
        tail = call.func.attr if isinstance(call.func, ast.Attribute) else called
        if called is None or called in {"_evaluate_control_semantics", "getattr", "setattr",
                                        "delattr"} or tail in unsafe_tails:
          return False, "publication helper reaches dynamic, evaluator, overwrite, or subprocess code"
        if called in functions and called not in publication_terminals:
          pending.append(called)
        elif called in publication_terminals or tail in publication_tails:
          continue
        else:
          return False, f"publication helper reaches unresolved call {called}"
    return True, "publication source shape is fixed"
  except (KeyError, SyntaxError, UnicodeError, TypeError, ValueError) as error:
    return False, f"publication source inspection failed: {type(error).__name__}"


def setup_fixtures() -> None:
  global EARLY, MAIN, BY_NAME, NAMES, MODULE_PAYLOADS, RETAINED_INDEXES, HISTORICAL
  global DEPENDENCIES, ALIAS_ROWS, SYMBOL_ROWS, EXPECTED_OPERATIONAL_PLAN
  global EXPECTED_FIXTURE_PLAN, RAW_OUTPUTS, COMMAND_OBSERVATIONS
  global CONTROL_BEFORE, CONTROL_AFTER, LOOKUP_BEFORE, LOOKUP_AFTER
  global GENERATED_OBSERVATIONS, RETAINED_OBSERVATIONS, TREE_IDENTITY_RECORDS
  global ALL_IDENTITY_RECORDS, PROVENANCE, AGGREGATE_MODEL, AGGREGATE_SHA256_CANDIDATE
  global RESULT_BYTES
  os.umask(0o077)
  require(work_members() == INITIAL_WORK_MEMBERS, "initial work membership differs")
  no_publication()
  META.mkdir(mode=0o700)
  contract.validate_e_base(INPUT_BYTES[BASE])
  EARLY = parse_newc(INPUT_BYTES[BASE][:10240])
  MAIN = parse_newc(assembly.single_gzip(INPUT_BYTES[BASE][10240:], 61286668))
  require(len(EARLY.members) == 7 and len(MAIN.members) == 1163 and
          sha256(EARLY.raw) == "967bc6adcff42e59abcfb4e509f6c80fd65588e0861d8c1c3189a135f10955b4" and
          sha256(MAIN.raw) == "7be7b4b03367b5ce4b356fe35977edba6540af0a7df930dbff990286c9b98e28" and
          all(b"".join(member.raw for member in archive.members) + archive.tail == archive.raw
              for archive in (EARLY, MAIN)), "independent E archive model differs")
  BY_NAME = {member.name: member for member in MAIN.members}
  modules = [member for member in MAIN.members
             if re.search(r"\.ko(?:\.|$)", Path(member.name).name)]
  require(len(modules) == 200 and all(
    member.name.startswith(PREFIX + "kernel/") and member.name.endswith(".ko") and
    stat.S_ISREG(member.fields[1]) and member.fields[4] in (0, 1) and len(member.payload) > 0
    for member in modules
  ), "independent module membership differs")
  NAMES = {Path(member.name).name[:-3].replace("-", "_"): member.name.removeprefix(PREFIX)
           for member in modules}
  serialized = "".join(f"{name}={NAMES[name]}\n" for name in sorted(NAMES)).encode("ascii")
  require(len(NAMES) == 200 and sha256(serialized) == MODULE_MODEL_SHA256,
          "independent module model differs")
  MODULE_PAYLOADS = {member.name.removeprefix(PREFIX): member.payload for member in modules}
  require(all(path in BY_NAME and len(BY_NAME[path].payload) == PAYLOAD_BYTES[path] and
              sha256(BY_NAME[path].payload) == digest
              for path, digest in PAYLOAD_SHA256.items()), "four payload identities differ")
  direct_indexes = {
    member.name.removeprefix(PREFIX): member.payload for member in MAIN.members
    if member.name.startswith(PREFIX) and "/" not in member.name.removeprefix(PREFIX)
    and member.name.removeprefix(PREFIX).startswith("modules.")
  }
  RETAINED_INDEXES = direct_indexes
  require({name: sha256(raw) for name, raw in RETAINED_INDEXES.items()} == RETAINED_INDEX_SHA256,
          "retained E index model differs")
  HISTORICAL = {name: INPUT_BYTES[path] for name, path in HISTORICAL_BINDINGS.items()}
  require({name: sha256(raw) for name, raw in HISTORICAL.items()} == HISTORICAL_SHA256 and
          {name: len(raw) for name, raw in HISTORICAL.items()} == HISTORICAL_BYTES and
          len(INPUT_BYTES[DUMP]) == DUMP_BYTES and sha256(INPUT_BYTES[DUMP]) == DUMP_SHA256 and
          all(HISTORICAL[name] == RETAINED_INDEXES[name]
              for name in RETAINED_INDEX_SHA256 if name != "modules.symbols.bin") and
          HISTORICAL["modules.symbols.bin"] != RETAINED_INDEXES["modules.symbols.bin"],
          "historical generated fixture identities differ")
  DEPENDENCIES = {}
  for row in HISTORICAL["modules.dep"].decode("ascii").splitlines():
    require(row.count(":") == 1, "historical dependency row differs")
    path, values = row.split(":")
    require(path not in DEPENDENCIES and path in NAMES.values() and
            (not values or values.startswith(" ")), "historical dependency key differs")
    DEPENDENCIES[path] = tuple(values[1:].split(" ")) if values else ()
  require(len(DEPENDENCIES) == 200 and
          assembly.dependency_entries(HISTORICAL["modules.dep"], set(NAMES.values())) == DEPENDENCIES,
          "independent dependency model differs")
  ALIAS_ROWS = alias_rows(HISTORICAL["modules.alias"])
  SYMBOL_ROWS = alias_rows(HISTORICAL["modules.symbols"])
  require(len(ALIAS_ROWS) == 1408 and len(SYMBOL_ROWS) == 596 and
          all(matching_target(alias, ALIAS_ROWS) in NAMES for alias in ALIASES) and
          all(matching_target("symbol:" + symbol, SYMBOL_ROWS) in NAMES for symbol in EXPORTS),
          "complete alias or symbol fixture differs")
  assembly.validate_binary_dump(
    INPUT_BYTES[DUMP], HISTORICAL["modules.alias"], HISTORICAL["modules.symbols"],
    RETAINED_INDEXES["modules.softdep"],
  )
  EXPECTED_OPERATIONAL_PLAN = expected_plan(NAMES, fixture=False)
  EXPECTED_FIXTURE_PLAN = expected_plan(NAMES, fixture=True)
  require(len(EXPECTED_OPERATIONAL_PLAN) == len(EXPECTED_FIXTURE_PLAN) == 424 and
          all(commands.approved_command(argv) for argv in EXPECTED_OPERATIONAL_PLAN) and
          not any(argv[0] == "/usr/bin/python3.14" for argv in EXPECTED_OPERATIONAL_PLAN) and
          EXPECTED_OPERATIONAL_PLAN != EXPECTED_FIXTURE_PLAN,
          "independent operational and fixture plans differ")

  write_new(Path(FIXTURE_EARLY_PATH), EARLY.raw)
  write_new(Path(FIXTURE_MAIN_PATH), MAIN.raw)
  write_new(Path(FIXTURE_EMPTY_CONFIG), b"")
  Path(FIXTURE_RECORD_ROOT).mkdir(mode=0o700)
  CONTROL_BEFORE = make_module_tree(Path(FIXTURE_CONTROL_ROOT), INDEX_BYTES)
  control_version = Path(FIXTURE_CONTROL_ROOT) / "lib/modules" / KERNEL
  for name in sorted(HISTORICAL):
    write_new(control_version / name, HISTORICAL[name])
  CONTROL_AFTER = control.snapshot(Path(FIXTURE_CONTROL_ROOT))
  require(len(CONTROL_BEFORE.files) == 203 and len(CONTROL_AFTER.files) == 214 and
          len(CONTROL_BEFORE.directories) == len(CONTROL_AFTER.directories) == 48 and
          CONTROL_BEFORE.directories == CONTROL_AFTER.directories and
          all(CONTROL_AFTER.files[name] == value
              for name, value in CONTROL_BEFORE.files.items()) and
          set(CONTROL_AFTER.files) == set(CONTROL_BEFORE.files) |
          {f"lib/modules/{KERNEL}/{name}" for name in HISTORICAL},
          "control fixture tree does not prove exact 203-to-214 preservation")
  LOOKUP_BEFORE = make_module_tree(Path(FIXTURE_LOOKUP_ROOT), RETAINED_INDEXES)
  LOOKUP_AFTER = control.snapshot(Path(FIXTURE_LOOKUP_ROOT))
  require(len(LOOKUP_BEFORE.files) == 207 and len(LOOKUP_BEFORE.directories) == 48 and
          LOOKUP_AFTER == LOOKUP_BEFORE,
          "lookup fixture tree does not preserve all 207 files")

  RAW_OUTPUTS = raw_command_outputs()
  COMMAND_OBSERVATIONS = tuple(
    write_command_observation(index, raw) for index, raw in enumerate(RAW_OUTPUTS)
  )
  GENERATED_OBSERVATIONS = {
    name: file_observation(control_version / name, raw)
    for name, raw in sorted(HISTORICAL.items())
  }
  lookup_version = Path(FIXTURE_LOOKUP_ROOT) / "lib/modules" / KERNEL
  RETAINED_OBSERVATIONS = {
    name: file_observation(lookup_version / name, raw)
    for name, raw in sorted(RETAINED_INDEXES.items())
  }
  TREE_IDENTITY_RECORDS = (
    *tree_records(Path(FIXTURE_CONTROL_ROOT), CONTROL_BEFORE),
    *tree_records(Path(FIXTURE_CONTROL_ROOT), CONTROL_AFTER),
    *tree_records(Path(FIXTURE_LOOKUP_ROOT), LOOKUP_BEFORE),
    *tree_records(Path(FIXTURE_LOOKUP_ROOT), LOOKUP_AFTER),
  )
  command_identity_records = tuple(
    object_map(observation[key]) for observation in COMMAND_OBSERVATIONS
    for key in ("stdout_file", "stderr_file", "report_file")
  )
  fixed_identity_records = (
    file_observation(Path(FIXTURE_EARLY_PATH), EARLY.raw),
    file_observation(Path(FIXTURE_MAIN_PATH), MAIN.raw),
    file_observation(Path(FIXTURE_EMPTY_CONFIG), b""),
  )
  ALL_IDENTITY_RECORDS = (*command_identity_records, *TREE_IDENTITY_RECORDS,
                          *fixed_identity_records)
  PROVENANCE = {
    "kind": "dev147-e-control-semantic-historical-fixture-provenance-v2",
    "status": "FIXTURE_ONLY", "historical_generated_files": 12,
    "bindings": [str(HISTORICAL_BINDINGS[name]) for name in sorted(HISTORICAL_BINDINGS)] +
                [str(DUMP)],
    "planned_children": 424, "children_executed": 0,
    "all_records_executed": False, "fresh_control_proved": False,
    "structural_control_proved": False, "operational_control_proved": False,
    "image_created": False, "module_loaded": False, "staged": False, "booted": False,
  }
  AGGREGATE_MODEL = build_aggregate_model()
  AGGREGATE_SHA256_CANDIDATE = sha256(canonical_json(AGGREGATE_MODEL))
  require(EXPECTED_AGGREGATE_SHA256 is None or
          EXPECTED_AGGREGATE_SHA256 == AGGREGATE_SHA256_CANDIDATE,
          "literal aggregate digest differs from the fixed raw fixture")
  RESULT_BYTES = expected_result_bytes()
  require(work_members() == expected_fixture_members(), "fixture work membership differs")
  save_json(META / "setup.json", {
    "setup": "PASS", "runner_sha256": sha256(TEST_BYTES), "subject_sha256": SUBJECT_SHA256,
    "task_inputs": 21, "expected_read_only_mounts": 606, "base_sha256": E_SHA256,
    "early_records": 7, "main_records": 1163, "modules": 200,
    "index_inputs": 3, "historical_generated_files": 12,
    "alias_mappings": 1408, "symbol_mappings": 596, "planned_commands": 424,
    "raw_output_files": 424, "raw_stderr_files": 424, "raw_report_files": 424,
    "control_files_before": 203, "control_files_after": 214, "lookup_files": 207,
    "aggregate_sha256_candidate": AGGREGATE_SHA256_CANDIDATE,
    "children_executed": 0, "fresh_control_proved": False,
    "image_created": False, "module_loaded": False, "staged": False, "booted": False,
  })


class EControlSemanticRedTests(unittest.TestCase):
  def test_a_full_fixed_e_historical_vector_is_nonfresh(self) -> None:
    self.assertTrue(
      all(hasattr(subject, name) for name in FAMILY_APIS),
      "missing raw mapper, fixed readers, family validators, or aggregate evaluator",
    )
    self.assertEqual(subject.SEMANTIC_RECORDS, 424)
    self.assertEqual(subject.SEMANTIC_FIXTURE_PATHS, FIXTURE_PATH_POLICY)
    self.assertEqual(subject.SEMANTIC_OPERATIONAL_PATHS, OPERATIONAL_PATH_POLICY)
    self.assertIsNotNone(EXPECTED_AGGREGATE_SHA256,
                         "accepted RED must freeze the reviewed literal aggregate digest")
    self.assertEqual(EXPECTED_AGGREGATE_SHA256, AGGREGATE_SHA256_CANDIDATE)
    shape_ok, shape_message = aggregate_source_shape()
    self.assertTrue(shape_ok, shape_message)
    self.assertEqual(subject.command_plan(NAMES), EXPECTED_OPERATIONAL_PLAN)
    raw_files = subject._collect_fixed_raw_files(subject.SEMANTIC_FIXTURE_PATHS)
    self.assertIsInstance(raw_files, subject.RawControlFiles)
    expected_records = tuple(
      (
        object_map(observation["stdout_file"])["raw"],
        object_map(observation["stderr_file"])["raw"],
        observation["report_raw"],
      )
      for observation in COMMAND_OBSERVATIONS
    )
    self.assertEqual(raw_files.paths, FIXTURE_PATH_POLICY)
    self.assertEqual(raw_files.record_state, control.snapshot(Path(FIXTURE_RECORD_ROOT)))
    self.assertEqual(raw_files.records, expected_records)
    self.assertEqual(raw_files.control_state, CONTROL_AFTER)
    self.assertEqual(raw_files.lookup_state, LOOKUP_AFTER)
    self.assertEqual(raw_files.empty_config_raw, b"")
    self.assertEqual(raw_files.early_raw, EARLY.raw)
    self.assertEqual(raw_files.main_raw, MAIN.raw)
    mapped = subject._map_raw_control_outputs(raw_files)
    self.assertIsInstance(mapped, subject.MappedControlOutputs)
    self.assertIs(mapped.raw_files, raw_files)
    evaluation = subject._evaluate_control_semantics()
    self.assertIsInstance(evaluation, subject.SemanticFixtureEvaluation)
    self.assertEqual(evaluation, subject.SemanticFixtureEvaluation(
      status="NONFRESH_FIXTURE", semantic_validated=True,
      aggregate_sha256=AGGREGATE_SHA256_CANDIDATE, planned_children=424,
      children_executed=0, historical_generated_files=12,
      structural_control_proved=False, operational_control_proved=False,
      fresh_control_proved=False, image_created=False, module_loaded=False,
      staged=False, booted=False,
    ))
    for name in ("operational_policy", "finalize_operational_result", "main"):
      with self.assertRaisesRegex(subject.RecipeError, "^E_CONTROL_RECIPE_UNAVAILABLE$"):
        getattr(subject, name)()
    no_publication()
    self.assertEqual(work_members(), expected_fixture_members())

  def test_b_each_semantic_corruption_refuses_without_publication(self) -> None:
    self.assertTrue(
      all(hasattr(subject, name) for name in FAMILY_APIS),
      "missing raw mapper or one of the required semantic family validators",
    )
    shape_ok, shape_message = aggregate_source_shape()
    self.assertTrue(shape_ok, shape_message)
    def refuses(function: object, *arguments: object) -> None:
      with self.assertRaisesRegex(subject.RecipeError, "^E_CONTROL_SEMANTIC_INVALID$"):
        function(*arguments)
      no_publication()

    archive_cases = (
      ("early-cpio", RAW_OUTPUTS[0]), ("early-bsdtar", RAW_OUTPUTS[1]),
      ("main-cpio", RAW_OUTPUTS[2]), ("main-bsdtar", RAW_OUTPUTS[3]),
      ("gzip", RAW_OUTPUTS[4]),
    )
    for label, raw in archive_cases:
      with self.subTest(family="archive", label=label):
        self.assertIsNone(subject._validate_archive_observation(label, raw))
        refuses(subject._validate_archive_observation, label, corrupted_raw(raw))

    for offset, path in enumerate(PAYLOAD_SHA256, start=5):
      with self.subTest(family="payload", path=path):
        self.assertIsNone(subject._validate_payload_observation(path, RAW_OUTPUTS[offset]))
        refuses(subject._validate_payload_observation, path, corrupted_raw(RAW_OUTPUTS[offset]))

    for label, before, after in (
      ("control", CONTROL_BEFORE, CONTROL_AFTER),
      ("lookup", LOOKUP_BEFORE, LOOKUP_AFTER),
    ):
      with self.subTest(family="tree", label=label):
        self.assertIsNone(subject._validate_tree_observation(label, before, after))
        corrupt = copy.deepcopy(after)
        corrupt.files.pop(next(iter(corrupt.files)))
        refuses(subject._validate_tree_observation, label, before, corrupt)

    for kind, raw_values, observations in (
      ("generated", HISTORICAL, GENERATED_OBSERVATIONS),
      ("retained", RETAINED_INDEXES, RETAINED_OBSERVATIONS),
    ):
      for name in sorted(raw_values):
        raw = raw_values[name]
        observation = observations[name]
        with self.subTest(family="index", kind=kind, name=name):
          self.assertIsNone(subject._validate_index_observation(kind, name, raw, observation))
          refuses(subject._validate_index_observation, kind, name, corrupted_raw(raw), observation)

    for ordinal, name in enumerate(sorted(NAMES)):
      filename_raw = RAW_OUTPUTS[12 + ordinal * 2]
      dependency_raw = RAW_OUTPUTS[13 + ordinal * 2]
      with self.subTest(family="module", name=name):
        self.assertIsNone(subject._validate_module_observation(name, filename_raw, dependency_raw))
        refuses(subject._validate_module_observation, name, b"/wrong\n", dependency_raw)
        refuses(subject._validate_module_observation, name, filename_raw,
                dependency_raw + b"insmod /wrong.ko \n")

    for ordinal, alias in enumerate(ALIASES):
      raw = RAW_OUTPUTS[412 + ordinal]
      with self.subTest(family="alias", alias=alias):
        self.assertIsNone(subject._validate_alias_observation(alias, raw))
        refuses(subject._validate_alias_observation, alias, raw + b"x")
    for ordinal, symbol in enumerate(EXPORTS):
      raw = RAW_OUTPUTS[415 + ordinal]
      with self.subTest(family="symbol", symbol=symbol):
        self.assertIsNone(subject._validate_symbol_observation(symbol, raw))
        refuses(subject._validate_symbol_observation, symbol, raw + b"x")

    for index, observation in enumerate(COMMAND_OBSERVATIONS):
      with self.subTest(family="command", index=index):
        self.assertIsNone(subject._validate_command_observation(index, observation))
      report = object_map(observation["report"])
      for field, original in report.items():
        with self.subTest(family="command-report-mutate", index=index, field=field):
          corrupt = shallow_observation(observation)
          object_map(corrupt["report"])[field] = changed_value(original)
          refuses(subject._validate_command_observation, index, corrupt)
        with self.subTest(family="command-report-remove", index=index, field=field):
          corrupt = shallow_observation(observation)
          object_map(corrupt["report"]).pop(field)
          refuses(subject._validate_command_observation, index, corrupt)
      for field in ("retained_bytes", "observed_bytes"):
        for slot in range(2):
          with self.subTest(family="command-byte-vector", index=index,
                            field=field, slot=slot):
            corrupt = shallow_observation(observation)
            values = object_list(object_map(corrupt["report"])[field])
            values[slot] = int(values[slot]) + 1
            refuses(subject._validate_command_observation, index, corrupt)
      corrupt = shallow_observation(observation)
      object_map(corrupt["report"])["unexpected"] = "wrong"
      with self.subTest(family="command-report-extra", index=index):
        refuses(subject._validate_command_observation, index, corrupt)

      for file_key in ("stdout_file", "stderr_file", "report_file"):
        file_record = object_map(observation[file_key])
        for field, original in file_record.items():
          with self.subTest(family="command-file-mutate", index=index,
                            file=file_key, field=field):
            corrupt = shallow_observation(observation)
            object_map(corrupt[file_key])[field] = changed_value(original)
            refuses(subject._validate_command_observation, index, corrupt)
          with self.subTest(family="command-file-remove", index=index,
                            file=file_key, field=field):
            corrupt = shallow_observation(observation)
            object_map(corrupt[file_key]).pop(field)
            refuses(subject._validate_command_observation, index, corrupt)
        for slot in range(9):
          with self.subTest(family="command-file-identity", index=index,
                            file=file_key, slot=slot):
            corrupt = shallow_observation(observation)
            values = object_list(object_map(corrupt[file_key])["identity"])
            values[slot] = int(values[slot]) + 1
            refuses(subject._validate_command_observation, index, corrupt)
        corrupt = shallow_observation(observation)
        object_map(corrupt[file_key])["unexpected"] = "wrong"
        with self.subTest(family="command-file-extra", index=index, file=file_key):
          refuses(subject._validate_command_observation, index, corrupt)

      report_raw = observation["report_raw"]
      require(type(report_raw) is bytes, "raw report fixture differs")
      corrupt = shallow_observation(observation)
      corrupt["report_raw"] = corrupted_raw(report_raw)
      with self.subTest(family="command-report-raw", index=index):
        refuses(subject._validate_command_observation, index, corrupt)
      for field in tuple(observation):
        corrupt = shallow_observation(observation)
        corrupt.pop(field)
        with self.subTest(family="command-observation-remove", index=index, field=field):
          refuses(subject._validate_command_observation, index, corrupt)
      corrupt = shallow_observation(observation)
      corrupt["unexpected"] = "wrong"
      with self.subTest(family="command-observation-extra", index=index):
        refuses(subject._validate_command_observation, index, corrupt)

    for ordinal, record in enumerate(ALL_IDENTITY_RECORDS):
      with self.subTest(family="identity", ordinal=ordinal):
        self.assertIsNone(subject._validate_identity_observation(record))
      for slot in range(9):
        corrupt = dict(record)
        corrupt["identity"] = list(object_list(record["identity"]))
        values = object_list(corrupt["identity"])
        values[slot] = int(values[slot]) + 1
        with self.subTest(family="identity-field", ordinal=ordinal, slot=slot):
          refuses(subject._validate_identity_observation, corrupt)

    for field, original in PROVENANCE.items():
      corrupt = copy.deepcopy(PROVENANCE)
      if type(original) is bool:
        corrupt[field] = not original
      elif type(original) is int:
        corrupt[field] = original + 1
      elif type(original) is str:
        corrupt[field] = original + "-wrong"
      elif type(original) is list:
        corrupt[field] = original[:-1]
      else:
        raise RuntimeError("unsupported provenance fixture field")
      with self.subTest(family="provenance", field=field):
        self.assertIsNone(subject._validate_provenance_observation(PROVENANCE))
        refuses(subject._validate_provenance_observation, corrupt)
      missing = dict(PROVENANCE)
      missing.pop(field)
      with self.subTest(family="provenance-remove", field=field):
        refuses(subject._validate_provenance_observation, missing)
    extra_provenance = dict(PROVENANCE)
    extra_provenance["unexpected"] = "wrong"
    refuses(subject._validate_provenance_observation, extra_provenance)
    self.assertEqual(work_members(), expected_fixture_members())

  def test_c_fixture_publication_is_no_replace_rename_last_and_fail_closed(self) -> None:
    self.assertTrue(
      all(hasattr(subject, name) for name in (
        "SemanticFixtureAcceptance", "_evaluate_control_semantics",
        "publish_semantic_fixture_result", "_rename_noreplace",
        "_rename_noreplace_errcheck", "_SEMANTIC_LIBC", "_AT_FDCWD",
        "SEMANTIC_FIXTURE_PENDING", "SEMANTIC_FIXTURE_RESULT", "RENAME_NOREPLACE",
        "SEMANTIC_FIXTURE_PATHS", "SEMANTIC_OPERATIONAL_PATHS", "SEMANTIC_RECORDS",
        "SEMANTIC_FIXTURE_WORK_MEMBERS",
      )),
      "missing fixture publisher, shared evaluator, acceptance, or no-replace helper",
    )
    self.assertEqual(
      (subject.SEMANTIC_FIXTURE_PENDING, subject.SEMANTIC_FIXTURE_RESULT),
      (PENDING, FINAL),
    )
    self.assertEqual(subject.RENAME_NOREPLACE, 1)
    self.assertEqual(subject._AT_FDCWD, -100)
    self.assertEqual(subject.SEMANTIC_FIXTURE_PATHS, FIXTURE_PATH_POLICY)
    self.assertEqual(subject.SEMANTIC_OPERATIONAL_PATHS, OPERATIONAL_PATH_POLICY)
    self.assertEqual(subject.SEMANTIC_RECORDS, 424)
    self.assertEqual(subject.SEMANTIC_FIXTURE_WORK_MEMBERS, expected_fixture_members())
    self.assertIs(subject._SEMANTIC_LIBC.renameat2.errcheck,
                  subject._rename_noreplace_errcheck)
    shape_ok, shape_message = publication_source_shape()
    self.assertTrue(shape_ok, shape_message)

    missing_source = Path("/work/e-control-semantic-missing-source")
    missing_target = Path("/work/e-control-semantic-missing-target")
    before_missing = work_members()
    with self.assertRaisesRegex(subject.RecipeError, "^E_CONTROL_SEMANTIC_INVALID$"):
      subject._rename_noreplace(missing_source, missing_target)
    self.assertFalse(missing_source.exists() or missing_source.is_symlink() or
                     missing_target.exists() or missing_target.is_symlink())
    self.assertEqual(work_members(), before_missing)

    blocked_source = Path("/work/e-control-semantic-blocked-source")
    blocked_target = Path("/work/e-control-semantic-blocked-target")
    write_new(blocked_source, b"rename source fixture\n")
    write_new(blocked_target, b"rename target fixture\n")
    blocked_source_state = file_observation(blocked_source, b"rename source fixture\n")
    blocked_target_state = file_observation(blocked_target, b"rename target fixture\n")
    blocked_members = work_members()
    with self.assertRaisesRegex(subject.RecipeError, "^E_CONTROL_SEMANTIC_EXISTS$"):
      subject._rename_noreplace(blocked_source, blocked_target)
    self.assertEqual(file_observation(blocked_source, b"rename source fixture\n"),
                     blocked_source_state)
    self.assertEqual(file_observation(blocked_target, b"rename target fixture\n"),
                     blocked_target_state)
    self.assertEqual(work_members(), blocked_members)
    blocked_source.unlink()
    blocked_target.unlink()
    self.assertEqual(work_members(), expected_fixture_members())

    unexpected = Path("/work/e-control-semantic-unapproved")
    write_new(unexpected, b"unapproved\n")
    unexpected_state = file_observation(unexpected, b"unapproved\n")
    with self.assertRaisesRegex(subject.RecipeError, "^E_CONTROL_SEMANTIC_INVALID$"):
      subject.publish_semantic_fixture_result()
    self.assertEqual(file_observation(unexpected, b"unapproved\n"), unexpected_state)
    self.assertFalse(PENDING.exists() or FINAL.exists())
    unexpected.unlink()
    self.assertEqual(work_members(), expected_fixture_members())

    stale = b"stale semantic fixture pending\n"
    write_new(PENDING, stale)
    pending_state = file_observation(PENDING, stale)
    with self.assertRaisesRegex(subject.RecipeError, "^E_CONTROL_SEMANTIC_EXISTS$"):
      subject.publish_semantic_fixture_result()
    self.assertEqual(file_observation(PENDING, stale), pending_state)
    self.assertFalse(FINAL.exists() or FINAL.is_symlink())
    self.assertEqual(work_members(), expected_fixture_members(PENDING.name))
    PENDING.unlink()

    stale_final = b"stale semantic fixture final\n"
    write_new(FINAL, stale_final)
    final_state = file_observation(FINAL, stale_final)
    with self.assertRaisesRegex(subject.RecipeError, "^E_CONTROL_SEMANTIC_EXISTS$"):
      subject.publish_semantic_fixture_result()
    self.assertEqual(file_observation(FINAL, stale_final), final_state)
    self.assertFalse(PENDING.exists() or PENDING.is_symlink())
    self.assertEqual(work_members(), expected_fixture_members(FINAL.name))
    FINAL.unlink()
    self.assertEqual(work_members(), expected_fixture_members())

    recheck_fixture_state()
    accepted = subject.publish_semantic_fixture_result()
    self.assertIsInstance(accepted, subject.SemanticFixtureAcceptance)
    self.assertEqual(read_regular(FINAL), RESULT_BYTES)
    self.assertFalse(PENDING.exists() or PENDING.is_symlink())
    self.assertEqual(accepted, subject.SemanticFixtureAcceptance(
      status="NONFRESH_FIXTURE", semantic_validated=True,
      aggregate_sha256=AGGREGATE_SHA256_CANDIDATE, result_sha256=sha256(RESULT_BYTES),
      pending_path=str(PENDING), result_path=str(FINAL), planned_children=424,
      children_executed=0, structural_control_proved=False,
      operational_control_proved=False, fresh_control_proved=False, image_created=False,
      module_loaded=False, staged=False, booted=False,
    ))
    self.assertEqual(work_members(), expected_fixture_members(FINAL.name))
    original = file_observation(FINAL, RESULT_BYTES)
    with self.assertRaisesRegex(subject.RecipeError, "^E_CONTROL_SEMANTIC_EXISTS$"):
      subject.publish_semantic_fixture_result()
    self.assertEqual(file_observation(FINAL, RESULT_BYTES), original)
    self.assertFalse(PENDING.exists() or PENDING.is_symlink())
    no_real_outputs()
    self.assertEqual(work_members(), expected_fixture_members(FINAL.name))


def main() -> int:
  try:
    setup_fixtures()
  except (OSError, RuntimeError, ValueError, KeyError, TypeError) as error:
    print(f"SETUP FAIL: {type(error).__name__}: {error}", file=sys.stderr)
    return 2
  print("SETUP PASS: exact E, three index inputs and twelve historical fixture files; zero children",
        flush=True)
  program = unittest.main(argv=sys.argv, verbosity=2, exit=False)
  result = program.result
  try:
    validate_binding_tree()
    test_after, test_state_after = read_regular_bound(TEST, 256 * 1024)
    require(test_after == TEST_BYTES and test_state_after == TEST_STATE, "runner changed")
    for path in PINS:
      raw, after = read_pinned(path)
      require(raw == INPUT_BYTES[path] and after == INPUT_STATES[path], "pinned input changed")
    indexes, index_state, index_file_states = read_index_directory()
    require(indexes == INDEX_BYTES and index_state == INDEX_STATE and
            index_file_states == INDEX_FILE_STATES, "index input directory changed")
    require(result.testsRun == 3, "test selection count differs")
    require(not (PENDING.exists() or PENDING.is_symlink()), "pending fixture result remains")
    if FINAL.exists() or FINAL.is_symlink():
      require(read_regular(FINAL) == RESULT_BYTES, "fixture result bytes differ")
    recheck_fixture_state()
    no_real_outputs()
    save_json(META / "test-result.json", {
      "setup": "PASS", "tests": result.testsRun, "failures": len(result.failures),
      "errors": len(result.errors), "skipped": len(result.skipped),
      "failed_tests": [test.id() for test, _ in result.failures],
      "error_tests": [test.id() for test, _ in result.errors],
      "runner_sha256": sha256(TEST_BYTES), "subject_sha256": SUBJECT_SHA256,
      "task_inputs": 21, "read_only_mounts": 606, "inputs_unchanged": True,
      "semantic_fixture_result_present": FINAL.exists(), "real_result_present": False,
      "children_executed": 0, "fresh_control_proved": False,
      "image_created": False, "module_loaded": False, "staged": False, "booted": False,
    })
  except (OSError, RuntimeError, ValueError, KeyError, TypeError) as error:
    print(f"POSTCHECK FAIL: {type(error).__name__}: {error}", file=sys.stderr)
    return 2
  if result.errors or result.skipped:
    return 2
  return 1 if result.failures else 0


if __name__ == "__main__":
  raise SystemExit(main())
