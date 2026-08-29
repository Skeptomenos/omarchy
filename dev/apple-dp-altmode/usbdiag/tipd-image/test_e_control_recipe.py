"""Fixed real-E selection/index fixtures; no real control is executed.

Only the root task may run this file in the reviewed fresh sandbox. All twelve
historical generated-index/dump files are individual read-only inputs. They
exercise pure checks and cannot stand in for fresh depmod or lookup evidence.
Setup/import/input failures are errors, not the three intended assertion REDs.
"""

import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
from types import ModuleType
import unittest


SUBJECT = Path("/inputs/recipe")
SUBJECT_SHA256 = "099be3713b7d7b40020de10ca38f0a943da3da60509acb153b2d3de390e44f1d"
ASSEMBLY = Path("/inputs/assembly/prepare_image.py")
CONTRACT = Path("/inputs/contract/image_contract.py")
COMMANDS = Path("/inputs/subject/e_control.py")
BASE = Path("/inputs/base")
E_SHA256 = "4d4f0557af57eebcc33322f004bcc7968254e644b069a11102375df0b31a52ae"
E_BYTES = 19191513
SOURCE_PINS = {
  SUBJECT: SUBJECT_SHA256,
  ASSEMBLY: "00caceb3b7fa236dcc030fb4007d0baa75bfa08fcd1590626f85fcc8c22d5f60",
  CONTRACT: "a1eda280aa56967aa06b01a2cca0dfc70c3da6df25066f8a1e815beec719f1bf",
  COMMANDS: "abbf59410a05fd5c789820df3d40e59d0a5c33cf1204ab93c7aeef806da7b1df",
  Path("/inputs/control/verify_control.py"):
    "10b5afe6cff38df7b6ebe5619fd9a34935932a4b369f3a9ad2a51923c32932d8",
  Path("/inputs/helper/cpio_image.py"):
    "a32eddd159263d19ff87d7e9caee9d53d17ef5c350fbffe9e7eb142cb43ebf58",
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
GENERATED_BINDINGS = {
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
PINS = {
  **SOURCE_PINS, BASE: E_SHA256, DUMP: DUMP_SHA256,
  **{path: GENERATED_SHA256[name] for name, path in GENERATED_BINDINGS.items()},
}
RED_TESTS = (
  "ERecipeTests.test_select_fixed_e_model",
  "ERecipeTests.test_unapproved_generated_index_is_rejected",
  "ERecipeTests.test_exact_424_command_plan",
)
WORK = Path("/work/e-recipe-fixtures")
KERNEL = "7.1.6-1-1-ARCH"
PREFIX = f"usr/lib/modules/{KERNEL}/"
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
OPERATIONAL_OUTPUTS = (
  "/work/control-root", "/work/lookup-root", "/work/empty-modprobe.conf",
  "/work/e-early.cpio", "/work/e-main.cpio", "/work/e-control-result.json",
  "/work/e-control-header.json",
)


def require(condition: bool, message: str) -> None:
  if not condition:
    raise RuntimeError(message)


def sha256(raw: bytes) -> str:
  return hashlib.sha256(raw).hexdigest()


def identity(info: os.stat_result) -> tuple[int, ...]:
  return (info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_gid,
          info.st_nlink, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def read_pinned(path: Path) -> tuple[bytes, tuple[int, ...]]:
  require(path in PINS, "unapproved input")
  for parent in path.parents:
    require(stat.S_ISDIR(parent.lstat().st_mode), "input parent is not a real directory")
  bound = E_BYTES if path == BASE else (128 * 1024 if path in SOURCE_PINS else 4 * 1024 * 1024)
  before = path.lstat()
  require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and
          0 <= before.st_size <= bound and (before.st_size > 0 or path == Path("/inputs/g-devname")),
          "input is not bounded regular single-link")
  descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC)
  with os.fdopen(descriptor, "rb") as stream:
    require(identity(os.fstat(stream.fileno())) == identity(before), "input changed on open")
    raw = stream.read(bound + 1)
    require(identity(os.fstat(stream.fileno())) == identity(before) == identity(path.lstat()),
            "input changed while read")
  require(len(raw) == before.st_size and sha256(raw) == PINS[path], "input hash mismatch")
  return raw, identity(before)


def load_source(name: str, path: Path, raw: bytes) -> ModuleType:
  require(name not in sys.modules, "source already imported")
  module = ModuleType(name)
  module.__file__ = str(path)
  sys.modules[name] = module
  exec(compile(raw, str(path), "exec"), module.__dict__)
  return module


def bootstrap() -> tuple[ModuleType, ModuleType, ModuleType, ModuleType,
                         dict[Path, bytes], dict[Path, tuple[int, ...]]]:
  require(sys.argv[1:] in ([], list(RED_TESTS)), "unapproved selected tests")
  require(sys.version_info[:2] == (3, 14) and sys.flags.isolated == 1 and
          sys.flags.no_site == 1 and sys.dont_write_bytecode, "isolated Python 3.14 required")
  require(os.getuid() == os.geteuid() == os.getgid() == 1001 and Path.cwd() == Path("/work"),
          "unexpected fixture identity or directory")
  require(Path(__file__) == Path("/inputs/test"), "unexpected runner path")
  require(not any(Path(path).exists() for path in (
    "/proc", "/sys", "/run", "/home", "/root", "/boot",
  )), "host tree visible")
  require(not any(name in sys.modules for name in (
    "cpio_image", "verify_control", "prepare_image", "t1_image_contract", "e_control", "e_recipe",
  )), "dependency already imported")
  data = {path: read_pinned(path) for path in PINS}
  assembly = load_source("prepare_image", ASSEMBLY, data[ASSEMBLY][0])
  contract = load_source("t1_image_contract", CONTRACT, data[CONTRACT][0])
  commands = load_source("e_control", COMMANDS, data[COMMANDS][0])
  subject = load_source("e_recipe", SUBJECT, data[SUBJECT][0])
  return (subject, contract, commands, assembly, {path: pair[0] for path, pair in data.items()},
          {path: pair[1] for path, pair in data.items()})


try:
  subject, contract, commands, assembly, INPUT_BYTES, INPUT_STATES = bootstrap()
  from cpio_image import parse_newc, read_regular, replace_members, write_new
except (OSError, RuntimeError, ValueError, SyntaxError, ImportError, TypeError) as error:
  print(f"SETUP FAIL: {type(error).__name__}: {error}", file=sys.stderr)
  raise SystemExit(2) from None


def save_json(path: Path, value: object) -> None:
  write_new(path, (json.dumps(value, sort_keys=True, allow_nan=False) + "\n").encode("ascii"))


def probe_command(root: str, target: str) -> tuple[str, ...]:
  return ("/usr/bin/modprobe", "--dry-run", "--show-depends", "-d", root,
          "-S", KERNEL, "-C", "/work/empty-modprobe.conf", target)


def expected_plan(names: dict[str, str]) -> tuple[tuple[str, ...], ...]:
  plan: list[tuple[str, ...]] = []
  for path in ("/work/e-early.cpio", "/work/e-main.cpio"):
    plan.extend((("/usr/bin/cpio", "--list", "--quiet", "--file", path),
                 ("/usr/bin/bsdtar", "--list", "--file", path)))
  plan.append(("/usr/bin/gzip",))
  for path in PAYLOAD_SHA256:
    plan.append(("/usr/bin/bsdtar", "--extract", "--to-stdout", "--file", "/work/e-main.cpio", path))
  plan.append(("/usr/bin/depmod", "-b", "/work/control-root", KERNEL))
  plan.extend((probe_command("/work/control-root", "--show-config"),
               probe_command("/work/lookup-root", "--show-config")))
  for name in sorted(names):
    plan.append(("/usr/bin/modinfo", "-b", "/work/lookup-root", "-k", KERNEL, "-F", "filename", name))
    plan.append(probe_command("/work/lookup-root", name))
  for alias in ("of:Nusb-pdT(null)Capple,cd321x", "of:Ndwc3T(null)Capple,t8103-dwc3",
                "of:Natc-phyT(null)Capple,t8103-atcphy"):
    plan.append(probe_command("/work/lookup-root", alias))
  for symbol in ("tipd_sn201202x_data", "tps6598x_regmap_config", "tipd_init", "tipd_cd321x_data",
                 "tipd_tps6598x_data", "tipd_tps25750_data", "tipd_remove", "tipd_suspend", "tipd_resume"):
    plan.append(probe_command("/work/lookup-root", "symbol:" + symbol))
  return tuple(plan)


def no_operational_outputs() -> None:
  require(not any(Path(path).exists() or Path(path).is_symlink() for path in OPERATIONAL_OUTPUTS),
          "operational output created during pure fixture run")
  require(not list(Path("/work").glob("e-control-children-*")), "child output created during pure fixtures")


def setup_fixtures() -> None:
  global EARLY, MAIN, INDEXES, GENERATED, NAMES, EXPECTED_DEPENDENCIES, EXPECTED_PLAN
  os.umask(0o077)
  no_operational_outputs()
  WORK.mkdir(mode=0o700)
  require(len(INPUT_BYTES[BASE]) == E_BYTES, "fixed E size differs")
  contract.validate_e_base(INPUT_BYTES[BASE])
  EARLY = parse_newc(INPUT_BYTES[BASE][:10240])
  MAIN = parse_newc(assembly.single_gzip(INPUT_BYTES[BASE][10240:], 61286668))
  require(len(EARLY.members) == 7 and len(MAIN.members) == 1163 and
          sha256(EARLY.raw) == "967bc6adcff42e59abcfb4e509f6c80fd65588e0861d8c1c3189a135f10955b4" and
          sha256(MAIN.raw) == "7be7b4b03367b5ce4b356fe35977edba6540af0a7df930dbff990286c9b98e28",
          "independent E stream oracle differs")
  require(all(b"".join(member.raw for member in archive.members) + archive.tail == archive.raw
              for archive in (EARLY, MAIN)), "independent raw-record reconstruction differs")
  by_name = {member.name: member for member in MAIN.members}
  selected = [member for member in MAIN.members if re.search(r"\.ko(?:\.|$)", Path(member.name).name)]
  require(len(selected) == 200 and all(
    member.name.startswith(PREFIX + "kernel/") and member.name.endswith(".ko") and
    stat.S_ISREG(member.fields[1]) and member.fields[4] in (0, 1) and len(member.payload) > 0
    for member in selected
  ), "independent module membership oracle differs")
  NAMES = {Path(member.name).name[:-3].replace("-", "_"): member.name.removeprefix(PREFIX)
           for member in selected}
  require(len(NAMES) == 200 and all(sha256(by_name[name].payload) == digest
                                  for name, digest in PAYLOAD_SHA256.items()),
          "independent four-payload or unique-name oracle differs")
  require(all(by_name[name].raw_name == name.encode("ascii") + b"\0" for name in PAYLOAD_SHA256),
          "fixed stdout-only archive names differ from the raw member names")
  direct_indexes = {
    member.name.removeprefix(PREFIX) for member in MAIN.members
    if member.name.startswith(PREFIX) and "/" not in member.name.removeprefix(PREFIX)
    and member.name.removeprefix(PREFIX).startswith("modules.")
  }
  require(direct_indexes == set(INDEX_SHA256), "independent original index membership differs")
  INDEXES = {name: by_name[PREFIX + name].payload for name in INDEX_SHA256}
  require(all(stat.S_ISREG(by_name[PREFIX + name].fields[1]) and
              by_name[PREFIX + name].fields[4] in (0, 1) for name in INDEX_SHA256) and
          {name: sha256(raw) for name, raw in INDEXES.items()} == INDEX_SHA256,
          "independent original seven-index oracle differs")
  GENERATED = {name: INPUT_BYTES[path] for name, path in GENERATED_BINDINGS.items()}
  require(all(GENERATED[name] == INDEXES[name] for name in INDEXES if name != "modules.symbols.bin")
          and GENERATED["modules.symbols.bin"] != INDEXES["modules.symbols.bin"],
          "historical fixture does not have the one known symbol distinction")
  rows = GENERATED["modules.dep"].decode("ascii").splitlines()
  EXPECTED_DEPENDENCIES = {}
  for row in rows:
    require(row.count(":") == 1, "dependency fixture syntax differs")
    path, values = row.split(":")
    require(path not in EXPECTED_DEPENDENCIES and path in NAMES.values() and
            (not values or values.startswith(" ")), "dependency fixture key differs")
    EXPECTED_DEPENDENCIES[path] = tuple(values[1:].split(" ")) if values else ()
  require(assembly.dependency_entries(GENERATED["modules.dep"], set(NAMES.values())) ==
          EXPECTED_DEPENDENCIES and len(EXPECTED_DEPENDENCIES) == 200,
          "pinned dependency parser disagrees with fixture oracle")
  assembly.validate_binary_dump(INPUT_BYTES[DUMP], GENERATED["modules.alias"],
                                GENERATED["modules.symbols"], INDEXES["modules.softdep"])
  require(len(GENERATED["modules.alias"].splitlines()) - 1 == 1408 and
          len(GENERATED["modules.symbols"].splitlines()) - 1 == 596,
          "full mapping multiplicity oracle differs")
  EXPECTED_PLAN = expected_plan(NAMES)
  require(len(EXPECTED_PLAN) == 424 and all(commands.approved_command(argv) for argv in EXPECTED_PLAN)
          and not any(argv[0] == "/usr/bin/python3.14" for argv in EXPECTED_PLAN),
          "literal control plan is not within the reviewed command boundary")
  save_json(WORK / "setup.json", {
    "setup": "PASS", "subject_sha256": SUBJECT_SHA256,
    "base_sha256": E_SHA256, "base_bytes": E_BYTES, "early_records": 7, "main_records": 1163,
    "module_count": 200, "original_indexes": 7, "historical_generated_files": 12,
    "alias_mappings": 1408, "symbol_mappings": 596, "planned_commands": 424,
    "children_executed": 0, "fresh_control_proved": False, "image_created": False,
  })


class ERecipeTests(unittest.TestCase):
  def test_select_fixed_e_model(self) -> None:
    selected = subject.select_e(INPUT_BYTES[BASE])
    self.assertIsInstance(selected, subject.ESelection, "missing exact E-only archive selection")
    self.assertEqual(selected.early, EARLY)
    self.assertEqual(selected.main, MAIN)
    self.assertEqual(len(selected.modules), 200)
    self.assertEqual({module.name: str(module.relative) for module in selected.modules}, NAMES)
    self.assertEqual(selected.indexes, INDEXES)
    for archive in (selected.early, selected.main):
      self.assertEqual(replace_members(archive, {}, ()), archive.raw)

  def test_e_identity_cannot_be_replaced(self) -> None:
    for raw in (INPUT_BYTES[BASE][:-1], INPUT_BYTES[BASE][:-1] + b"\x01", b"not E"):
      with self.subTest(size=len(raw)), self.assertRaisesRegex(subject.RecipeError, "^E_BASE_IDENTITY$"):
        subject.select_e(raw)

  def test_e_rejects_nonbytes(self) -> None:
    for raw in (None, False, "E", bytearray(b"E")):
      with self.subTest(kind=type(raw).__name__), self.assertRaisesRegex(subject.RecipeError,
                                                                       "^E_BASE_IDENTITY$"):
        subject.select_e(raw)

  def test_reviewed_regeneration_preserves_original_indexes(self) -> None:
    result = subject.validate_regeneration(INDEXES, GENERATED, INPUT_BYTES[DUMP], NAMES)
    self.assertIsInstance(result, subject.Regeneration)
    self.assertEqual(result.dependencies, EXPECTED_DEPENDENCIES)
    self.assertEqual((result.alias_mappings, result.symbol_mappings), (1408, 596))
    self.assertEqual(result.retained_symbol_sha256, INDEX_SHA256["modules.symbols.bin"])
    self.assertEqual(result.generated_symbol_sha256, GENERATED_SHA256["modules.symbols.bin"])
    self.assertEqual({name: sha256(raw) for name, raw in INDEXES.items()}, INDEX_SHA256)

  def test_unapproved_generated_index_is_rejected(self) -> None:
    changed = dict(GENERATED)
    changed["modules.dep.bin"] += b"\0"
    with self.assertRaisesRegex(subject.RecipeError, "^E_GENERATED_IDENTITY$"):
      subject.validate_regeneration(INDEXES, changed, INPUT_BYTES[DUMP], NAMES)

  def test_each_original_index_is_pinned(self) -> None:
    for name in INDEXES:
      changed = dict(INDEXES)
      changed[name] += b"\0"
      with self.subTest(index=name), self.assertRaisesRegex(subject.RecipeError, "^E_INDEX_IDENTITY$"):
        subject.validate_regeneration(changed, GENERATED, INPUT_BYTES[DUMP], NAMES)

  def test_each_generated_file_is_pinned(self) -> None:
    for name in GENERATED:
      changed = dict(GENERATED)
      changed[name] += b"\0"
      with self.subTest(index=name), self.assertRaisesRegex(subject.RecipeError, "^E_GENERATED_IDENTITY$"):
        subject.validate_regeneration(INDEXES, changed, INPUT_BYTES[DUMP], NAMES)

  def test_original_symbol_bytes_do_not_fake_regeneration(self) -> None:
    changed = dict(GENERATED)
    changed["modules.symbols.bin"] = INDEXES["modules.symbols.bin"]
    with self.assertRaisesRegex(subject.RecipeError, "^E_GENERATED_IDENTITY$"):
      subject.validate_regeneration(INDEXES, changed, INPUT_BYTES[DUMP], NAMES)

  def test_index_membership_is_exact(self) -> None:
    for original, generated in (({}, GENERATED), (INDEXES, {}),
                                (INDEXES | {"extra": b""}, GENERATED),
                                (INDEXES, GENERATED | {"extra": b""})):
      with self.subTest(original=len(original), generated=len(generated)), self.assertRaisesRegex(
        subject.RecipeError, "^E_INDEX_SET$",
      ):
        subject.validate_regeneration(original, generated, INPUT_BYTES[DUMP], NAMES)

  def test_index_value_types_are_strict(self) -> None:
    for value in (None, False, "index", bytearray(b"index")):
      changed = dict(GENERATED)
      changed["modules.alias.bin"] = value
      with self.subTest(kind=type(value).__name__), self.assertRaisesRegex(subject.RecipeError,
                                                                         "^E_INDEX_TYPE$"):
        subject.validate_regeneration(INDEXES, changed, INPUT_BYTES[DUMP], NAMES)

  def test_dump_requires_exact_bytes(self) -> None:
    for raw in (INPUT_BYTES[DUMP] + b"\n", INPUT_BYTES[DUMP][:-1], b"", None):
      with self.subTest(kind=type(raw).__name__), self.assertRaisesRegex(subject.RecipeError,
                                                                       "^E_DUMP_IDENTITY$"):
        subject.validate_regeneration(INDEXES, GENERATED, raw, NAMES)

  def test_dependency_model_cannot_omit_a_module(self) -> None:
    names = dict(NAMES)
    names.pop("tps6598x")
    with self.assertRaisesRegex(subject.RecipeError, "^E_MODULE_MODEL$"):
      subject.validate_regeneration(INDEXES, GENERATED, INPUT_BYTES[DUMP], names)

  def test_exact_424_command_plan(self) -> None:
    plan = subject.command_plan(NAMES)
    self.assertIsInstance(plan, tuple, "missing fixed read-only control plan")
    self.assertEqual(plan, EXPECTED_PLAN)
    self.assertEqual(len(plan), 424)
    self.assertTrue(all(commands.approved_command(argv) for argv in plan))
    self.assertEqual(sum(argv[0] == "/usr/bin/modinfo" for argv in plan), 200)
    self.assertEqual(sum(argv[0] == "/usr/bin/modprobe" for argv in plan), 214)
    self.assertFalse(any(argv[0] == "/usr/bin/python3.14" for argv in plan))

  def test_plan_rejects_count_and_placement_drift(self) -> None:
    missing = dict(NAMES)
    missing.pop("dwc3_apple")
    renamed = dict(NAMES)
    renamed["dwc3_apple"] = "kernel/fixture/dwc3-apple.ko"
    for names in (missing, renamed):
      with self.subTest(count=len(names)), self.assertRaisesRegex(subject.RecipeError, "^E_MODULE_MODEL$"):
        subject.command_plan(names)

  def test_plan_rejects_untrusted_names(self) -> None:
    changed = dict(NAMES)
    changed["tps6598x;false"] = changed.pop("tps6598x")
    for names in (None, [], changed, NAMES | {False: "kernel/false.ko"}):
      with self.subTest(kind=type(names).__name__), self.assertRaisesRegex(subject.RecipeError,
                                                                         "^E_MODULE_MODEL$"):
        subject.command_plan(names)

  def test_operational_and_assembly_gates_stay_closed(self) -> None:
    with self.assertRaisesRegex(subject.RecipeError, "^E_CONTROL_RECIPE_UNAVAILABLE$"):
      subject.main()
    with self.assertRaisesRegex(commands.ControlError, "^E_CONTROL_UNAVAILABLE$"):
      commands.main()
    with self.assertRaisesRegex(contract.ImageContractError, "^T1_ASSEMBLY_UNAVAILABLE$"):
      contract.require_operational_bindings()
    no_operational_outputs()


def main() -> int:
  try:
    setup_fixtures()
  except (OSError, RuntimeError, ValueError, KeyError, TypeError) as error:
    print(f"SETUP FAIL: {type(error).__name__}: {error}", file=sys.stderr)
    return 2
  print("SETUP PASS: fixed E bytes, 200 modules, seven original indexes, twelve historical fixtures; no child",
        flush=True)
  program = unittest.main(argv=sys.argv, verbosity=2, exit=False)
  result = program.result
  try:
    for path in PINS:
      raw, after = read_pinned(path)
      require(after == INPUT_STATES[path] and raw == INPUT_BYTES[path], "immutable input changed")
    require({name: sha256(raw) for name, raw in INDEXES.items()} == INDEX_SHA256 and
            {name: sha256(raw) for name, raw in GENERATED.items()} == GENERATED_SHA256,
            "in-memory original or fixture index collection changed")
    require(result.testsRun == (3 if sys.argv[1:] else 16), "test selection count differs")
    no_operational_outputs()
    save_json(WORK / "test-result.json", {
      "setup": "PASS", "tests": result.testsRun, "failures": len(result.failures),
      "errors": len(result.errors), "skipped": len(result.skipped),
      "failed_tests": [test.id() for test, _ in result.failures],
      "error_tests": [test.id() for test, _ in result.errors],
      "subject_sha256": SUBJECT_SHA256, "pinned_inputs": len(PINS), "inputs_unchanged": True,
      "children_executed": 0, "fresh_control_proved": False, "image_created": False,
      "module_loaded": False, "staged": False, "booted": False,
    })
  except (OSError, RuntimeError, ValueError, KeyError, TypeError) as error:
    print(f"POSTCHECK FAIL: {type(error).__name__}: {error}", file=sys.stderr)
    return 2
  if result.errors or result.skipped:
    return 2
  return 1 if result.failures else 0


if __name__ == "__main__":
  raise SystemExit(main())
