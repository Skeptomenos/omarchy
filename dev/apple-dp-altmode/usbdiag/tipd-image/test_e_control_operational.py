"""Three zero-child checks for the fixed E-control structural boundary.

Only the root task may run this file in the reviewed fresh sandbox. Setup
authenticates the final eight task inputs plus this runner, then writes
distinct structural records under /work. It never starts a subprocess. These
records cannot produce real PASS, fresh control, image, module, stage or boot.
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


TEST = Path("/inputs/test")
SUBJECT = Path("/inputs/recipe")
SUBJECT_SHA256 = "57d35a30de9b351bcbaf0b78a1be186c8c44a2fbfb378d8f0b801e6e9256a7a9"
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
  COMMANDS: "16016875e731e88d047eb805c7c6d03045300abdb262361b18010a952adb7b80",
  CONTROL: "10b5afe6cff38df7b6ebe5619fd9a34935932a4b369f3a9ad2a51923c32932d8",
  HELPER: "a32eddd159263d19ff87d7e9caee9d53d17ef5c350fbffe9e7eb142cb43ebf58",
}
PINS = {
  **SOURCE_PINS, BASE: E_SHA256,
  PROOF: "9133cb64040f9df0daf9aa0caaab913c90fe7ce5c9bf59a19c71ce3e36fb0c94",
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
EXPECTED_BINDINGS = (
  "/inputs/recipe", "/inputs/subject", "/inputs/contract", "/inputs/assembly",
  "/inputs/control", "/inputs/helper", "/inputs/base", "/inputs/index-inputs",
)
EXPECTED_TOP = frozenset((
  "test", "recipe", "subject", "contract", "assembly", "control", "helper", "base",
  "index-inputs", "proof",
))
SOURCE_LAYOUT = {
  Path("/inputs/subject"): "e_control.py",
  Path("/inputs/contract"): "image_contract.py",
  Path("/inputs/assembly"): "prepare_image.py",
  Path("/inputs/control"): "verify_control.py",
  Path("/inputs/helper"): "cpio_image.py",
}
SELECTED_TESTS = (
  "EOperationalRedTests.test_a_exact_eight_binding_and_424_structural_policy",
  "EOperationalRedTests.test_b_distinct_zero_child_structural_acceptance",
  "EOperationalRedTests.test_c_missing_or_failed_record_refuses_without_structural_result",
)
KERNEL = "7.1.6-1-1-ARCH"
PREFIX = f"usr/lib/modules/{KERNEL}/"
PAYLOADS = (
  PREFIX + "kernel/drivers/usb/typec/tipd/tps6598x-core.ko",
  PREFIX + "kernel/drivers/usb/typec/tipd/tps6598x.ko",
  PREFIX + "kernel/drivers/phy/apple/phy-apple-atc.ko",
  PREFIX + "kernel/drivers/usb/dwc3/dwc3-apple.ko",
)
ALIASES = (
  "of:Nusb-pdT(null)Capple,cd321x", "of:Ndwc3T(null)Capple,t8103-dwc3",
  "of:Natc-phyT(null)Capple,t8103-atcphy",
)
EXPORTS = (
  "tipd_sn201202x_data", "tps6598x_regmap_config", "tipd_init", "tipd_cd321x_data",
  "tipd_tps6598x_data", "tipd_tps25750_data", "tipd_remove", "tipd_suspend", "tipd_resume",
)
META = Path("/work/e-control-structural-check")
RECORD_ROOT = Path("/work/e-control-structural-records-e1")
HEADER = Path("/work/e-control-structural-header.json")
EVIDENCE = Path("/work/e-control-structural-evidence.json")
RESULT = Path("/work/e-control-structural-result.json")
FORBIDDEN_REAL_OUTPUTS = (
  Path("/work/control-root"), Path("/work/lookup-root"), Path("/work/empty-modprobe.conf"),
  Path("/work/e-early.cpio"), Path("/work/e-main.cpio"),
  Path("/work/e-control-children-e1"), Path("/work/e-control-header.json"),
  Path("/work/e-control-evidence.json"), Path("/work/e-control-result.pending"),
  Path("/work/e-control-result.json"),
)


def require(condition: bool, message: str) -> None:
  if not condition:
    raise RuntimeError(message)


def sha256(raw: bytes) -> str:
  return hashlib.sha256(raw).hexdigest()


def identity(info: os.stat_result) -> tuple[int, ...]:
  return (info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_gid,
          info.st_nlink, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def canonical_json(value: object) -> bytes:
  return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")


def read_pinned(path: Path) -> tuple[bytes, tuple[int, ...]]:
  require(path in PINS, "unapproved input")
  for parent in path.parents:
    require(stat.S_ISDIR(parent.lstat().st_mode), "input parent is not a real directory")
  before = path.lstat()
  expected_size = E_BYTES if path == BASE else before.st_size
  expected_mode = 0o644 if path == SUBJECT else 0o600
  bound = E_BYTES if path == BASE else 128 * 1024
  require(stat.S_ISREG(before.st_mode) and stat.S_IMODE(before.st_mode) == expected_mode and
          before.st_uid == before.st_gid == 1001 and before.st_nlink == 1 and
          0 < before.st_size <= bound and before.st_size == expected_size, "input metadata differs")
  descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC)
  with os.fdopen(descriptor, "rb") as stream:
    require(identity(os.fstat(stream.fileno())) == identity(before), "input changed on open")
    raw = stream.read(bound + 1)
    require(identity(os.fstat(stream.fileno())) == identity(before) == identity(path.lstat()),
            "input changed while read")
  require(len(raw) == before.st_size and sha256(raw) == PINS[path], "input hash mismatch")
  return raw, identity(before)


def read_index_directory() -> tuple[dict[str, bytes], tuple[int, ...], dict[str, tuple[int, ...]]]:
  before = INDEX_DIRECTORY.lstat()
  require(stat.S_ISDIR(before.st_mode) and stat.S_IMODE(before.st_mode) == 0o700 and
          before.st_uid == before.st_gid == 1001 and before.st_nlink == 2,
          "index directory metadata differs")
  require({path.name for path in INDEX_DIRECTORY.iterdir()} == set(INDEX_INPUTS),
          "index directory membership differs")
  raw_files: dict[str, bytes] = {}
  states: dict[str, tuple[int, ...]] = {}
  for name, (size, digest) in INDEX_INPUTS.items():
    path = INDEX_DIRECTORY / name
    info = path.lstat()
    require(stat.S_ISREG(info.st_mode) and stat.S_IMODE(info.st_mode) == 0o644 and
            info.st_uid == info.st_gid == 1001 and info.st_nlink == 1 and info.st_size == size,
            "index input metadata differs")
    descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC)
    with os.fdopen(descriptor, "rb") as stream:
      require(identity(os.fstat(stream.fileno())) == identity(info), "index input changed on open")
      raw = stream.read(size + 1)
      require(identity(os.fstat(stream.fileno())) == identity(info) == identity(path.lstat()),
              "index input changed while read")
    require(len(raw) == size and sha256(raw) == digest, "index input hash mismatch")
    raw_files[name] = raw
    states[name] = identity(info)
  require(identity(INDEX_DIRECTORY.lstat()) == identity(before), "index directory changed")
  return raw_files, identity(before), states


def validate_binding_tree() -> None:
  inputs = Path("/inputs")
  require(stat.S_ISDIR(inputs.lstat().st_mode) and
          {path.name for path in inputs.iterdir()} == EXPECTED_TOP,
          "task input membership differs")
  test_info = TEST.lstat()
  require(stat.S_ISREG(test_info.st_mode) and stat.S_IMODE(test_info.st_mode) == 0o644 and
          test_info.st_uid == test_info.st_gid == 1001 and test_info.st_nlink == 1 and
          0 < test_info.st_size < 128 * 1024, "runner metadata differs")
  for directory, filename in SOURCE_LAYOUT.items():
    info = directory.lstat()
    require(stat.S_ISDIR(info.st_mode) and stat.S_IMODE(info.st_mode) == 0o700 and
            info.st_uid == info.st_gid == 1001 and info.st_nlink == 2 and
            {path.name for path in directory.iterdir()} == {filename},
            "source binding membership or metadata differs")


def load_source(name: str, path: Path, raw: bytes) -> ModuleType:
  require(name not in sys.modules, "source already imported")
  module = ModuleType(name)
  module.__file__ = str(path)
  sys.modules[name] = module
  exec(compile(raw, str(path), "exec"), module.__dict__)
  return module


def bootstrap() -> tuple[ModuleType, ModuleType, ModuleType, ModuleType,
                         dict[Path, bytes], dict[Path, tuple[int, ...]], dict[str, bytes],
                         tuple[int, ...], dict[str, tuple[int, ...]]]:
  require(sys.argv[1:] in ([], list(SELECTED_TESTS)), "unapproved selected tests")
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
  validate_binding_tree()
  data = {path: read_pinned(path) for path in PINS}
  indexes, index_state, index_file_states = read_index_directory()
  subject = load_source("e_recipe", SUBJECT, data[SUBJECT][0])
  assembly = sys.modules.get("prepare_image")
  contract = sys.modules.get("t1_image_contract")
  commands = sys.modules.get("e_control")
  require(
    isinstance(assembly, ModuleType) and assembly.__file__ == str(ASSEMBLY) and
    isinstance(contract, ModuleType) and contract.__file__ == str(CONTRACT) and
    isinstance(commands, ModuleType) and commands.__file__ == str(COMMANDS) and
    isinstance(sys.modules.get("verify_control"), ModuleType) and
    sys.modules["verify_control"].__file__ == str(CONTROL) and
    isinstance(sys.modules.get("cpio_image"), ModuleType) and
    sys.modules["cpio_image"].__file__ == str(HELPER),
    "authenticated subject bootstrap source files differ",
  )
  return (subject, contract, commands, assembly, {path: pair[0] for path, pair in data.items()},
          {path: pair[1] for path, pair in data.items()}, indexes, index_state, index_file_states)


try:
  (subject, contract, commands, assembly, INPUT_BYTES, INPUT_STATES, INDEX_BYTES,
   INDEX_STATE, INDEX_FILE_STATES) = bootstrap()
  from cpio_image import parse_newc, read_regular, write_new
except (OSError, RuntimeError, ValueError, SyntaxError, ImportError, TypeError) as error:
  print(f"SETUP FAIL: {type(error).__name__}: {error}", file=sys.stderr)
  raise SystemExit(2) from None


def probe_command(root: str, target: str) -> tuple[str, ...]:
  return ("/usr/bin/modprobe", "--dry-run", "--show-depends", "-d", root,
          "-S", KERNEL, "-C", "/work/empty-modprobe.conf", target)


def expected_plan(names: dict[str, str]) -> tuple[tuple[str, ...], ...]:
  plan: list[tuple[str, ...]] = []
  for path in ("/work/e-early.cpio", "/work/e-main.cpio"):
    plan.extend((("/usr/bin/cpio", "--list", "--quiet", "--file", path),
                 ("/usr/bin/bsdtar", "--list", "--file", path)))
  plan.append(("/usr/bin/gzip", "-n"))
  for path in PAYLOADS:
    plan.append(("/usr/bin/bsdtar", "--extract", "--to-stdout", "--file",
                 "/work/e-main.cpio", path))
  plan.append(("/usr/bin/depmod", "-b", "/work/control-root", KERNEL))
  plan.extend((probe_command("/work/control-root", "--show-config"),
               probe_command("/work/lookup-root", "--show-config")))
  for name in sorted(names):
    plan.append(("/usr/bin/modinfo", "-b", "/work/lookup-root", "-k", KERNEL,
                 "-F", "filename", name))
    plan.append(probe_command("/work/lookup-root", name))
  plan.extend(probe_command("/work/lookup-root", alias) for alias in ALIASES)
  plan.extend(probe_command("/work/lookup-root", "symbol:" + symbol) for symbol in EXPORTS)
  return tuple(plan)


def file_record(path: Path) -> dict[str, str | int]:
  info = path.lstat()
  raw = read_regular(path)
  require(stat.S_ISREG(info.st_mode) and stat.S_IMODE(info.st_mode) == 0o600 and
          info.st_uid == info.st_gid == 1001 and info.st_nlink == 1 and
          identity(path.lstat()) == identity(info), "synthetic output metadata differs")
  return {
    "path": str(path), "bytes": len(raw), "sha256": sha256(raw),
    "mode": stat.S_IMODE(info.st_mode), "uid": info.st_uid, "gid": info.st_gid,
    "nlink": info.st_nlink,
  }


def structural_report(index: int, command: tuple[str, ...]) -> bytes:
  return canonical_json({
    "schema": 1, "kind": "dev147-e-control-structural-record-v1",
    "command": list(command), "status": "STRUCTURAL_ONLY", "returncode": None,
    "stdout": f"record-{index:03d}.stdout", "stderr": f"record-{index:03d}.stderr",
    "retained_bytes": [0, 0], "observed_bytes": [0, 0],
    "planned_stdin_sha256": "7be7b4b03367b5ce4b356fe35977edba6540af0a7df930dbff990286c9b98e28"
    if command == ("/usr/bin/gzip", "-n") else None,
    "planned_stdin_bytes": 61286668 if command == ("/usr/bin/gzip", "-n") else 0,
    "executed": False, "elapsed_seconds": 0.0, "pid": None,
    "killed": False, "reaped": False,
  })


def build_structural_artifacts(plan: tuple[tuple[str, ...], ...]) -> tuple[bytes, bytes, bytes]:
  RECORD_ROOT.mkdir(mode=0o700)
  record_files: list[dict[str, object]] = []
  for index, command in enumerate(plan):
    paths = tuple(RECORD_ROOT / f"record-{index:03d}.{suffix}"
                  for suffix in ("stdout", "stderr", "json"))
    raw_files = (b"", b"", structural_report(index, command))
    for path, raw in zip(paths, raw_files, strict=True):
      write_new(path, raw)
    record_files.append({
      "index": index, "command": list(command),
      "stdout": file_record(paths[0]), "stderr": file_record(paths[1]),
      "record": file_record(paths[2]),
    })
  header = canonical_json({
    "schema": 1, "kind": "dev147-e-control-structural-header-v1",
    "status": "STRUCTURAL_ONLY",
    "base_sha256": E_SHA256, "base_bytes": E_BYTES,
    "early_records": 7, "early_bytes": 10240,
    "early_sha256": "967bc6adcff42e59abcfb4e509f6c80fd65588e0861d8c1c3189a135f10955b4",
    "main_records": 1163, "main_bytes": 61286668,
    "main_sha256": "7be7b4b03367b5ce4b356fe35977edba6540af0a7df930dbff990286c9b98e28",
    "module_count": 200, "expected_no_change_archive": True,
    "expected_gzip_exact": True, "expected_binary_only_lookup": True,
    "module_loaded": False, "image_staged": False,
    "indexes": {
      "modules.alias.bin": "ca6ca7be95509eb294c2e67090bfa84dcbab855fb0489e504804593a257c4ea9",
      "modules.builtin.alias.bin": "9635eaa0d8c3d2f89c98789adce44dfd047f8cb11c7c9d0aa60199defc2ad962",
      "modules.builtin.bin": "edf2e707c121431f4f77b842ffd0a37fad5c0a6df198296fd6ef0b7f3227ac74",
      "modules.dep.bin": "436095f4779ccbd9f0c44b90febef13b62be50c9518dd499c151843fdf1feb3d",
      "modules.devname": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "modules.softdep": "6a8f2009d87deba7a2de46e3d0c46b114fe388d188b00b9a382fc2156aabb676",
      "modules.symbols.bin": "a3f1e745b7675daaec99c7c7ebadc7d67b318143901e063674494c210b12ace6",
    },
    "planned_children": 424, "structural_records": 424,
    "children_executed": 0, "fresh_control_proved": False,
  })
  write_new(HEADER, header)
  evidence = canonical_json({
    "schema": 1, "kind": "dev147-e-control-structural-evidence-v1",
    "status": "STRUCTURAL_ONLY",
    "bindings": list(EXPECTED_BINDINGS), "base_sha256": E_SHA256, "base_bytes": E_BYTES,
    "index_inputs": {name: digest for name, (_, digest) in INDEX_INPUTS.items()},
    "planned_commands": [list(command) for command in plan],
    "fixture_commands": [list(command) for command in plan],
    "record_root": str(RECORD_ROOT), "structural_records": 424,
    "record_files": record_files, "children_executed": 0, "fresh_control_proved": False,
    "image_created": False, "module_loaded": False, "staged": False, "booted": False,
  })
  write_new(EVIDENCE, evidence)
  result = canonical_json({
    "schema": 1, "kind": "dev147-e-control-structural-result-v1",
    "status": "STRUCTURAL_PASS", "bindings": list(EXPECTED_BINDINGS),
    "planned_children": 424, "structural_records": 424, "children_executed": 0,
    "record_files": 1272, "record_root": str(RECORD_ROOT),
    "header": file_record(HEADER), "evidence": file_record(EVIDENCE),
    "structural_validated": True, "fresh_control_proved": False,
    "image_created": False, "module_loaded": False,
    "staged": False, "booted": False,
  })
  return header, evidence, result


def write_json(path: Path, value: object) -> None:
  write_new(path, canonical_json(value))


def setup_fixtures() -> None:
  global NAMES, EXPECTED_PLAN, HEADER_BYTES, EVIDENCE_BYTES, RESULT_BYTES
  os.umask(0o077)
  require(not any(path.exists() or path.is_symlink() for path in (
    *FORBIDDEN_REAL_OUTPUTS, RECORD_ROOT, HEADER, EVIDENCE, RESULT, META,
  )), "structural output already exists")
  META.mkdir(mode=0o700)
  contract.validate_e_base(INPUT_BYTES[BASE])
  early = parse_newc(INPUT_BYTES[BASE][:10240])
  main = parse_newc(assembly.single_gzip(INPUT_BYTES[BASE][10240:], 61286668))
  require(len(early.members) == 7 and len(main.members) == 1163 and
          sha256(early.raw) == "967bc6adcff42e59abcfb4e509f6c80fd65588e0861d8c1c3189a135f10955b4" and
          sha256(main.raw) == "7be7b4b03367b5ce4b356fe35977edba6540af0a7df930dbff990286c9b98e28" and
          all(b"".join(member.raw for member in archive.members) + archive.tail == archive.raw
              for archive in (early, main)), "independent E stream model differs")
  module_members = [member for member in main.members
                    if re.search(r"\.ko(?:\.|$)", Path(member.name).name)]
  require(len(module_members) == 200 and all(
    member.name.startswith(PREFIX + "kernel/") and member.name.endswith(".ko") and
    stat.S_ISREG(member.fields[1]) and member.fields[4] in (0, 1) and len(member.payload) > 0
    for member in module_members
  ), "independent E module membership differs")
  NAMES = {Path(member.name).name[:-3].replace("-", "_"): member.name.removeprefix(PREFIX)
           for member in module_members}
  selected = subject.select_e(INPUT_BYTES[BASE])
  require(len(NAMES) == 200 and
          {module.name: str(module.relative) for module in selected.modules} == NAMES,
          "fixed E module model differs")
  require({name: sha256(raw) for name, raw in INDEX_BYTES.items()} ==
          {name: digest for name, (_, digest) in INDEX_INPUTS.items()},
          "index input model differs")
  EXPECTED_PLAN = expected_plan(NAMES)
  require(len(EXPECTED_PLAN) == 424 and all(commands.approved_command(argv) for argv in EXPECTED_PLAN)
          and not commands.approved_command(("/usr/bin/gzip",))
          and not any(argv[0] == "/usr/bin/python3.14" for argv in EXPECTED_PLAN),
          "literal operational plan differs")
  HEADER_BYTES, EVIDENCE_BYTES, RESULT_BYTES = build_structural_artifacts(EXPECTED_PLAN)
  require(not RESULT.exists(), "structural result exists before acceptance")
  write_json(META / "setup.json", {
    "setup": "PASS", "subject_sha256": SUBJECT_SHA256, "task_inputs": 9,
    "structural_bindings": 8, "planned_commands": 424, "structural_record_files": 1272,
    "children_executed": 0, "fresh_control_proved": False, "image_created": False,
    "module_loaded": False, "staged": False, "booted": False,
  })


class EOperationalRedTests(unittest.TestCase):
  def test_a_exact_eight_binding_and_424_structural_policy(self) -> None:
    policy = subject.structural_policy()
    self.assertIsInstance(policy, subject.StructuralPolicy, "fixed structural policy is missing")
    self.assertEqual(policy.bindings, EXPECTED_BINDINGS)
    self.assertEqual(policy.commands, EXPECTED_PLAN)
    self.assertEqual(policy.record_root, str(RECORD_ROOT))
    self.assertEqual(policy.artifacts, (str(HEADER), str(EVIDENCE), str(RESULT)))
    self.assertNotIn("/work/e-control-result.json", policy.artifacts)
    execution = subject.operational_execution_policy()
    self.assertEqual(len(execution.task_bindings), 8)
    self.assertEqual(execution.read_only_mounts, 593)
    self.assertEqual(execution.planned_children, 424)
    self.assertIn("_run_operational_control", subject.main.__code__.co_names)
    with self.assertRaisesRegex(
      subject.RecipeError, "^E_CONTROL_DIRECT_FINALIZE_UNAVAILABLE$",
    ):
      subject.finalize_operational_result()

  def test_b_distinct_zero_child_structural_acceptance(self) -> None:
    accepted = subject.finalize_structural_result()
    self.assertIsInstance(accepted, subject.StructuralAcceptance,
                          "complete fixed-path structural acceptance is missing")
    result_raw = read_regular(RESULT)
    self.assertEqual(result_raw, RESULT_BYTES)
    result_value = json.loads(result_raw.decode("ascii"))
    evidence_value = json.loads(EVIDENCE_BYTES.decode("ascii"))
    self.assertEqual(result_value["kind"], "dev147-e-control-structural-result-v1")
    self.assertEqual(result_value["status"], "STRUCTURAL_PASS")
    self.assertEqual(result_value["children_executed"], 0)
    self.assertFalse(result_value["fresh_control_proved"])
    self.assertEqual(evidence_value["kind"], "dev147-e-control-structural-evidence-v1")
    self.assertEqual(evidence_value["status"], "STRUCTURAL_ONLY")
    self.assertEqual(evidence_value["children_executed"], 0)
    self.assertFalse(evidence_value["fresh_control_proved"])
    self.assertEqual(accepted, subject.StructuralAcceptance(
      424, 0, sha256(HEADER_BYTES), sha256(EVIDENCE_BYTES), sha256(RESULT_BYTES),
      "STRUCTURAL_PASS", True, False, False, False, False, False,
    ))
    self.assertFalse(Path("/work/e-control-result.json").exists())

  def test_c_missing_or_failed_record_refuses_without_structural_result(self) -> None:
    report = RECORD_ROOT / "record-423.json"
    held = META / "held-record-423.json"
    if RESULT.exists() or RESULT.is_symlink():
      RESULT.unlink()
    report.rename(held)
    try:
      with self.assertRaisesRegex(subject.RecipeError, "^E_CONTROL_INCOMPLETE$"):
        subject.finalize_structural_result()
      self.assertFalse(RESULT.exists() or RESULT.is_symlink())
    finally:
      if RESULT.exists() or RESULT.is_symlink():
        RESULT.unlink()
      held.rename(report)

    original = read_regular(report)
    value = json.loads(original.decode("ascii"))
    require(type(value) is dict, "structural record model differs")
    value["status"] = "STRUCTURAL_FAILED"
    value["returncode"] = 7
    report.rename(held)
    write_new(report, canonical_json(value))
    try:
      with self.assertRaisesRegex(subject.RecipeError, "^E_CONTROL_INCOMPLETE$"):
        subject.finalize_structural_result()
      self.assertFalse(RESULT.exists() or RESULT.is_symlink())
    finally:
      if RESULT.exists() or RESULT.is_symlink():
        RESULT.unlink()
      report.unlink()
      held.rename(report)
    self.assertEqual(read_regular(report), original)


def main() -> int:
  try:
    setup_fixtures()
  except (OSError, RuntimeError, ValueError, KeyError, TypeError) as error:
    print(f"SETUP FAIL: {type(error).__name__}: {error}", file=sys.stderr)
    return 2
  print("SETUP PASS: exact nine inputs, real E/index-inputs, 424 structural records; zero children",
        flush=True)
  program = unittest.main(argv=sys.argv, verbosity=2, exit=False)
  result = program.result
  try:
    validate_binding_tree()
    for path in PINS:
      raw, after = read_pinned(path)
      require(raw == INPUT_BYTES[path] and after == INPUT_STATES[path], "immutable input changed")
    indexes, directory_state, file_states = read_index_directory()
    require(indexes == INDEX_BYTES and directory_state == INDEX_STATE and
            file_states == INDEX_FILE_STATES, "index input directory changed")
    require(result.testsRun == 3, "test selection count differs")
    require(not any(path.exists() or path.is_symlink() for path in FORBIDDEN_REAL_OUTPUTS),
            "real operational output created")
    require(len(list(RECORD_ROOT.iterdir())) == 1272 and
            all(stat.S_ISREG(path.lstat().st_mode) for path in RECORD_ROOT.iterdir()),
            "structural record membership differs")
    write_json(META / "test-result.json", {
      "setup": "PASS", "tests": result.testsRun, "failures": len(result.failures),
      "errors": len(result.errors), "skipped": len(result.skipped),
      "failed_tests": [test.id() for test, _ in result.failures],
      "error_tests": [test.id() for test, _ in result.errors],
      "subject_sha256": SUBJECT_SHA256, "task_inputs": 9, "read_only_mounts": 594,
      "inputs_unchanged": True, "planned_commands": 424, "structural_record_files": 1272,
      "children_executed": 0, "structural_result_present": RESULT.exists(),
      "real_result_present": Path("/work/e-control-result.json").exists(),
      "fresh_control_proved": False, "image_created": False, "module_loaded": False,
      "staged": False, "booted": False,
    })
  except (OSError, RuntimeError, ValueError, KeyError, TypeError) as error:
    print(f"POSTCHECK FAIL: {type(error).__name__}: {error}", file=sys.stderr)
    return 2
  if result.errors or result.skipped:
    return 2
  return 1 if result.failures else 0


if __name__ == "__main__":
  raise SystemExit(main())
