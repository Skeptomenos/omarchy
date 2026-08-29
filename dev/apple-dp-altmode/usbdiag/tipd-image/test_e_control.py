"""Pinned E-control boundary fixtures, not a real-image control.

Only the orchestrator may run this file in the reviewed fresh sandbox.
The original three-test RED is preserved separately. This unexecuted GREEN
candidate retains the original 16 methods and adds active kill/reap evidence.
Setup, import, child and observation defects are errors, not semantic RED.
"""

import hashlib
import json
import os
from pathlib import Path
import signal
import stat
import sys
import time
from types import ModuleType
import unittest
import zlib


SOURCE = Path("/inputs/subject/e_control.py")
SOURCE_SHA256 = "686d59e63166df1bef1afad27998a6d58f4c28b6b4439b6ccd607b56471268ca"
CONTRACT = Path("/inputs/contract/image_contract.py")
ASSEMBLY = Path("/inputs/assembly/prepare_image.py")
PINS = {
  SOURCE: SOURCE_SHA256,
  CONTRACT: "a1eda280aa56967aa06b01a2cca0dfc70c3da6df25066f8a1e815beec719f1bf",
  ASSEMBLY: "00caceb3b7fa236dcc030fb4007d0baa75bfa08fcd1590626f85fcc8c22d5f60",
  Path("/inputs/control/verify_control.py"):
    "10b5afe6cff38df7b6ebe5619fd9a34935932a4b369f3a9ad2a51923c32932d8",
  Path("/inputs/helper/cpio_image.py"):
    "a32eddd159263d19ff87d7e9caee9d53d17ef5c350fbffe9e7eb142cb43ebf58",
}
RED_TESTS = (
  "EControlTests.test_runner_gzip_regular_stdin_roundtrip",
  "EControlTests.test_lookup_root_exact_files_and_no_replace",
  "EControlTests.test_reordered_dependency_is_rejected",
)
WORK = Path("/work/e-control-fixtures")
KERNEL = "7.1.6-1-1-ARCH"
MODULE_DIRECTORY = Path("lib/modules") / KERNEL
LOOKUP_ROOT = Path("/work/lookup-root")
CONTROL_ROOT = Path("/work/control-root")
INDEX_NAMES = (
  "modules.alias.bin", "modules.builtin.alias.bin", "modules.builtin.bin",
  "modules.dep.bin", "modules.devname", "modules.softdep", "modules.symbols.bin",
)
STDIN_BYTES = b"confined E-control stdin fixture; not an archive\n" * 512
FIXTURE_PINS: dict[Path, str] = {}
FIXTURE_STATES: dict[Path, tuple[int, ...]] = {}


def require(condition: bool, detail: str) -> None:
  if not condition:
    raise RuntimeError(detail)


def sha256(raw: bytes) -> str:
  return hashlib.sha256(raw).hexdigest()


def identity(info: os.stat_result) -> tuple[int, ...]:
  return (info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_gid,
          info.st_nlink, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def read_source(path: Path, digest: str) -> tuple[bytes, tuple[int, ...]]:
  require(path in PINS and PINS[path] == digest, "unapproved source binding")
  for parent in (Path("/"), Path("/inputs"), path.parent):
    require(stat.S_ISDIR(parent.lstat().st_mode), "source parent is not a directory")
  before = path.lstat()
  require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and
          0 < before.st_size < 128 * 1024, "source is not bounded regular single-link")
  descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC)
  with os.fdopen(descriptor, "rb") as stream:
    require(identity(os.fstat(stream.fileno())) == identity(before), "source changed on open")
    raw = stream.read(128 * 1024)
    require(identity(os.fstat(stream.fileno())) == identity(before) == identity(path.lstat()),
            "source changed while read")
  require(len(raw) == before.st_size and sha256(raw) == digest, "source pin mismatch")
  return raw, identity(before)


def load_source(name: str, path: Path, raw: bytes) -> ModuleType:
  require(name not in sys.modules, "source already imported")
  module = ModuleType(name)
  module.__file__ = str(path)
  sys.modules[name] = module
  exec(compile(raw, str(path), "exec"), module.__dict__)
  return module


def bootstrap() -> tuple[ModuleType, ModuleType, ModuleType, dict[Path, tuple[int, ...]]]:
  require(sys.argv[1:] in ([], list(RED_TESTS)), "unapproved selected tests")
  require(sys.version_info[:2] == (3, 14) and sys.flags.isolated == 1 and
          sys.flags.no_site == 1 and sys.dont_write_bytecode, "isolated Python 3.14 required")
  require(os.getuid() == os.geteuid() == os.getgid() == 1001 and Path.cwd() == Path("/work"),
          "unexpected test identity or directory")
  require(Path(__file__) == Path("/inputs/test"), "unexpected runner path")
  require(not any(Path(name).exists() for name in (
    "/proc", "/sys", "/run", "/home", "/root", "/boot",
  )), "host tree visible")
  require(not any(name in sys.modules for name in (
    "cpio_image", "verify_control", "prepare_image", "t1_image_contract", "e_control",
  )), "dependency already imported")
  sources = {path: read_source(path, digest) for path, digest in PINS.items()}
  # The pinned assembler imports only its authenticated pure control/cpio chain.
  assembly = load_source("prepare_image", ASSEMBLY, sources[ASSEMBLY][0])
  contract = load_source("t1_image_contract", CONTRACT, sources[CONTRACT][0])
  subject = load_source("e_control", SOURCE, sources[SOURCE][0])
  for name in ("gzip", "cpio", "bsdtar", "depmod", "modprobe", "modinfo", "python3.14"):
    path = Path("/usr/bin") / name
    require(stat.S_ISREG(path.lstat().st_mode) and os.access(path, os.X_OK),
            "pinned runtime executable absent")
  return subject, contract, assembly, {path: value[1] for path, value in sources.items()}


try:
  subject, contract, assembly, SOURCE_STATES = bootstrap()
  from cpio_image import read_regular, write_new
  from verify_control import TreeState
except (OSError, RuntimeError, ValueError, SyntaxError, ImportError, TypeError) as error:
  print(f"SETUP FAIL: {type(error).__name__}: {error}", file=sys.stderr)
  raise SystemExit(2) from None


NAMES = {
  "typec": "kernel/drivers/usb/typec/typec.ko",
  "tps6598x_core": "kernel/drivers/usb/typec/tipd/tps6598x-core.ko",
  "tps6598x": "kernel/drivers/usb/typec/tipd/tps6598x.ko",
  "lrw": "kernel/crypto/lrw.ko",
  "other": "kernel/fixture/other.ko",
}
DEPENDENCIES = {
  NAMES["typec"]: (),
  NAMES["tps6598x_core"]: (NAMES["typec"],),
  NAMES["tps6598x"]: (NAMES["tps6598x_core"], NAMES["typec"]),
  NAMES["lrw"]: (),
  NAMES["other"]: (),
}
MODULES = {
  relative: ("ASCII fixture only: " + relative + "\n").encode("ascii")
  for relative in (
    *NAMES.values(), "kernel/drivers/phy/apple/phy-apple-atc.ko",
    "kernel/drivers/usb/dwc3/dwc3-apple.ko",
    *(f"kernel/fixture/filler_{index:03d}.ko" for index in range(193)),
  )
}
INDEXES = {name: ("fixture index: " + name + "\n").encode("ascii") for name in INDEX_NAMES}
INDEX_INPUTS = {name: b"fixture input; not real depmod data\n" for name in (
  "modules.order", "modules.builtin", "modules.builtin.modinfo",
)}


def filename(name: str) -> str:
  return str(LOOKUP_ROOT / MODULE_DIRECTORY / NAMES[name])


def dependency_bytes(*names: str, builtin: str | None = None) -> bytes:
  prefix = "" if builtin is None else f"builtin {builtin}\n"
  return (prefix + "".join(f"insmod {filename(name)} \n" for name in names)).encode("ascii")


def python_child(source: str) -> tuple[str, ...]:
  return ("/usr/bin/python3.14", "-I", "-S", "-B", "-c", source)


def child_root(label: str) -> Path:
  return Path("/work") / f"e-control-children-{label}"


def save_json(path: Path, value: object) -> None:
  write_new(path, (json.dumps(value, sort_keys=True, allow_nan=False) + "\n").encode("ascii"))


def child_report(root: Path) -> dict[str, object]:
  raw: object = json.loads(read_regular(root / "child-000.json"))
  require(type(raw) is dict and all(type(key) is str for key in raw), "child result object")
  if not isinstance(raw, dict):
    raise RuntimeError("child result object")
  return raw


def setup_fixtures() -> None:
  os.umask(0o077)
  WORK.mkdir(mode=0o700)
  require(len(MODULES) == 200 and len(INDEXES) == 7, "fixture membership oracle")
  normalized = [Path(name).name.removesuffix(".ko").replace("-", "_") for name in MODULES]
  require(len(normalized) == len(set(normalized)), "fixture module names are ambiguous")
  require(all(raw.startswith(b"ASCII fixture only: ") for raw in MODULES.values()),
          "fixture payload unexpectedly looks operational")
  source = WORK / "stdin.fixture"
  write_new(source, STDIN_BYTES)
  require(read_regular(source, sha256(STDIN_BYTES)) == STDIN_BYTES, "fixture file precheck")
  packed = zlib.compress(STDIN_BYTES, wbits=31)
  require(assembly.single_gzip(packed, len(STDIN_BYTES)) == STDIN_BYTES, "real gzip dependency precheck")
  text = "".join(relative + ":" + (" " + " ".join(deps) if deps else "") + "\n"
                 for relative, deps in DEPENDENCIES.items()).encode("ascii")
  require(assembly.dependency_entries(text, set(NAMES.values())) == DEPENDENCIES,
          "independent dependency fixture oracle")
  known = assembly.dependency_output(
    dependency_bytes("typec", "tps6598x_core", "tps6598x"), "tps6598x", NAMES, {"ecb"},
  )
  require(known["insmod"] == [filename(name) for name in ("typec", "tps6598x_core", "tps6598x")]
          and known["builtin"] == [], "literal lookup fixture oracle")
  save_json(WORK / "setup.json", {
    "setup": "PASS", "subject_sha256": SOURCE_SHA256, "synthetic_modules": 200,
    "synthetic_indexes": 7, "literal_dependency_records": 5,
    "real_image_or_module_input": False, "setup_children": 0,
  })
  for path in (source, WORK / "setup.json"):
    FIXTURE_PINS[path] = sha256(read_regular(path))
    FIXTURE_STATES[path] = identity(path.lstat())


class EControlTests(unittest.TestCase):
  def test_runner_gzip_regular_stdin_roundtrip(self) -> None:
    root = child_root("gzip")
    commands = subject.Commands(root)
    raw = commands.run(("/usr/bin/gzip", "-n"), stdin=WORK / "stdin.fixture",
                       stdin_sha256=sha256(STDIN_BYTES), stdout_limit=65536)
    self.assertIsInstance(raw, bytes, "missing actively bounded child result")
    self.assertEqual(assembly.single_gzip(raw, len(STDIN_BYTES)), STDIN_BYTES)
    self.assertEqual(read_regular(root / "child-000.stdout"), raw)
    self.assertEqual(read_regular(root / "child-000.stderr"), b"")
    report = child_report(root)
    self.assertEqual((report["status"], report["returncode"]), ("ok", 0))
    self.assertEqual(report["command"], ["/usr/bin/gzip", "-n"])
    self.assertEqual(report["stdin_sha256"], sha256(STDIN_BYTES))
    self.assertEqual(commands.count, 1)
    self.assertEqual(identity((WORK / "stdin.fixture").lstat()), FIXTURE_STATES[WORK / "stdin.fixture"])

  def test_active_stdout_and_stderr_caps(self) -> None:
    for label, code, stream in (
      ("stdout-limit", "import sys; sys.stdout.buffer.write(b'x' * 65537)", "stdout"),
      ("stderr-limit", "import sys; sys.stderr.buffer.write(b'e' * 65537)", "stderr"),
    ):
      with self.subTest(stream=stream):
        root = child_root(label)
        commands = subject.Commands(root)
        with self.assertRaisesRegex(subject.ControlError, "^CHILD_OUTPUT_LIMIT$"):
          commands.run(python_child(code), stdout_limit=8, stderr_limit=8)
        self.assertEqual(len(read_regular(root / f"child-000.{stream}")), 8)
        report = child_report(root)
        self.assertEqual(report["status"], "CHILD_OUTPUT_LIMIT")
        self.assertEqual(report["retained_bytes"][0 if stream == "stdout" else 1], 8)
        self.assertEqual(report["observed_bytes"][0 if stream == "stdout" else 1], 9)

  def test_nonzero_exit_and_nonempty_stderr_cannot_pass(self) -> None:
    for label, code, expected, status in (
      ("exit", "raise SystemExit(7)", 7, "CHILD_EXIT"),
      ("stderr", "import sys; sys.stderr.write('fixture stderr\\n')", 0, "CHILD_STDERR"),
    ):
      with self.subTest(status=status):
        root = child_root(label)
        commands = subject.Commands(root)
        with self.assertRaisesRegex(subject.ControlError, f"^{status}$"):
          commands.run(python_child(code))
        self.assertEqual((child_report(root)["status"], child_report(root)["returncode"]), (status, expected))

  def test_per_child_and_cumulative_deadlines(self) -> None:
    for label, budget, timeout, expected in (
      ("child-time", 30.0, 0.2, "CHILD_TIMEOUT"),
      ("total-time", 0.2, 30.0, "CONTROL_DEADLINE"),
    ):
      with self.subTest(status=expected):
        root = child_root(label)
        commands = subject.Commands(root, budget_seconds=budget)
        with self.assertRaisesRegex(subject.ControlError, f"^{expected}$"):
          commands.run(python_child("import time; time.sleep(1)"), timeout=timeout)
        self.assertEqual(child_report(root)["status"], expected)
        self.assertIsInstance(child_report(root)["returncode"], int)
        self.assertEqual(commands.count, 1)
        if expected == "CONTROL_DEADLINE":
          with self.assertRaisesRegex(subject.ControlError, "^CONTROL_DEADLINE$"):
            commands.run(python_child("raise SystemExit(7)"))
          self.assertEqual(commands.count, 1, "expired control must not start another child")

  def test_unapproved_commands_and_limits_refuse_before_children(self) -> None:
    commands = subject.Commands(child_root("arguments"))
    for command in (
      ("/usr/bin/bash", "-c", "true"), ("/usr/bin/gzip",), ("/usr/bin/gzip", "-f"),
      ("/usr/bin/python3.14", "-c", "print(1)"),
      python_child("print('not a whitelisted fixture')"),
      ("/usr/bin/modprobe", "tps6598x_core"),
      ("/usr/bin/depmod", "-b", "/", KERNEL),
    ):
      with self.subTest(command=command), self.assertRaisesRegex(subject.ControlError, "^CHILD_ARGS$"):
        commands.run(command)
    for options in (
      {"stdout_limit": True}, {"stdout_limit": 0}, {"stdout_limit": 64 * 1024 * 1024 + 1},
      {"stderr_limit": 0}, {"stderr_limit": 65537},
      {"timeout": True}, {"timeout": 0}, {"timeout": 31.0},
      {"timeout": float("nan")}, {"timeout": float("inf")},
    ):
      with self.subTest(options=options), self.assertRaisesRegex(subject.ControlError, "^CHILD_ARGS$"):
        commands.run(python_child("raise SystemExit(7)"), **options)
    self.assertEqual(commands.count, 0)
    self.assertEqual(subject.MAX_COMMANDS, 424)
    commands.count = 424
    with self.assertRaisesRegex(subject.ControlError, "^CONTROL_CHILD_LIMIT$"):
      commands.run(python_child("raise SystemExit(7)"))
    self.assertEqual(commands.count, 424, "limit fixture must not start a 425th child")

  def test_command_root_and_budget_are_bounded(self) -> None:
    for root in (Path("/work"), Path("/tmp/children"), Path("/inputs/children"),
                 Path("/work/e-control-children-x/child")):
      with self.subTest(root=str(root)), self.assertRaisesRegex(subject.ControlError, "^CHILD_ARGS$"):
        subject.Commands(root)
    for index, budget in enumerate((0, True, 271.0, float("nan"), float("inf"))):
      with self.subTest(budget=budget), self.assertRaisesRegex(subject.ControlError, "^CHILD_ARGS$"):
        subject.Commands(child_root(f"budget-{index}"), budget_seconds=budget)

  def test_stdin_hash_symlink_hardlink_and_scope_refusals(self) -> None:
    linked = WORK / "link-target.fixture"
    write_new(linked, b"separate linked fixture\n")
    hardlink = WORK / "hardlink.fixture"
    hardlink.hardlink_to(linked)
    symlink = WORK / "symlink.fixture"
    symlink.symlink_to("stdin.fixture")
    commands = subject.Commands(child_root("stdin-errors"))
    for path, digest in (
      (WORK / "stdin.fixture", "0" * 64), (symlink, sha256(STDIN_BYTES)),
      (hardlink, sha256(b"separate linked fixture\n")), (Path("/inputs/proof"), "0" * 64),
      (WORK / "absent.fixture", "0" * 64),
    ):
      with self.subTest(path=path.name), self.assertRaisesRegex(subject.ControlError, "^CHILD_INPUT$"):
        commands.run(("/usr/bin/gzip", "-n"), stdin=path, stdin_sha256=digest)
    self.assertEqual(commands.count, 0)

  def test_child_outputs_are_never_replaced(self) -> None:
    root = child_root("existing")
    commands = subject.Commands(root)
    write_new(root / "child-000.stdout", b"retain this fixture\n")
    with self.assertRaisesRegex(subject.ControlError, "^CHILD_OUTPUT_EXISTS$"):
      commands.run(python_child("raise SystemExit(7)"))
    self.assertEqual(read_regular(root / "child-000.stdout"), b"retain this fixture\n")
    with self.assertRaisesRegex(subject.ControlError, "^CHILD_OUTPUT_EXISTS$"):
      subject.Commands(root)

  def test_lookup_root_exact_files_and_no_replace(self) -> None:
    proof = subject.build_root(LOOKUP_ROOT, MODULES, INDEXES)
    self.assertIsInstance(proof, TreeState, "missing exact binary-only root proof")
    expected = {str(MODULE_DIRECTORY / name): sha256(raw) for name, raw in (MODULES | INDEXES).items()}
    self.assertEqual({name: state.sha256 for name, state in proof.files.items()}, expected)
    self.assertEqual(len(proof.files), 207)
    self.assertTrue(subject.unchanged_root(LOOKUP_ROOT, proof))
    with self.assertRaisesRegex(subject.ControlError, "^ROOT_EXISTS$"):
      subject.build_root(LOOKUP_ROOT, MODULES, INDEXES)
    self.assertTrue(subject.unchanged_root(LOOKUP_ROOT, proof))
    # Mutate only this disposable output, never an input or retained image.
    target = LOOKUP_ROOT / MODULE_DIRECTORY / NAMES["other"]
    with target.open("ab") as stream:
      stream.write(b"deliberate output drift\n")
    with self.assertRaisesRegex(subject.ControlError, "^ROOT_CHANGED$"):
      subject.unchanged_root(LOOKUP_ROOT, proof)

  def test_control_root_uses_only_three_index_inputs(self) -> None:
    proof = subject.build_root(CONTROL_ROOT, MODULES, INDEX_INPUTS)
    self.assertIsInstance(proof, TreeState)
    self.assertEqual(len(proof.files), 203)
    self.assertEqual(set(proof.files), {str(MODULE_DIRECTORY / name) for name in MODULES | INDEX_INPUTS})
    self.assertTrue(subject.unchanged_root(CONTROL_ROOT, proof))

  def test_invalid_root_module_and_metadata_shapes(self) -> None:
    with self.assertRaisesRegex(subject.ControlError, "^ROOT_PATH$"):
      subject.build_root(Path("/work/another-root"), MODULES, INDEXES)
    for metadata in (INDEX_INPUTS, INDEXES | {"modules.dep": b"text forbidden"},
                     {name: raw for name, raw in INDEXES.items() if name != "modules.dep.bin"}):
      with self.subTest(metadata=tuple(metadata)), self.assertRaisesRegex(subject.ControlError, "^ROOT_METADATA$"):
        subject.build_root(LOOKUP_ROOT, MODULES, metadata)
    first = next(iter(MODULES))
    remainder = {name: raw for name, raw in MODULES.items() if name != first}
    for changed in (
      remainder, remainder | {"/kernel/absolute.ko": b"fixture"},
      remainder | {"kernel/../escape.ko": b"fixture"},
      remainder | {"kernel/space name.ko": b"fixture"},
      remainder | {"kernel/other/tps6598x-core.ko": b"ambiguous basename"},
      remainder | {first: bytearray(b"not bytes")},
    ):
      with self.subTest(keys=len(changed)), self.assertRaisesRegex(subject.ControlError, "^ROOT_MODULES$"):
        subject.build_root(LOOKUP_ROOT, changed, INDEXES)

  def test_ordered_dependency_result_matches_literal_oracle(self) -> None:
    raw = dependency_bytes("typec", "tps6598x_core", "tps6598x")
    try:
      actual = subject.ordered_lookup(raw, "tps6598x", NAMES, DEPENDENCIES, {"ecb"})
    except subject.ControlError as error:
      self.fail(f"actual kmod 34.2 lookup grammar was rejected: {error}")
    self.assertEqual(actual, subject.Lookup(
      "tps6598x", filename("tps6598x"),
      (filename("typec"), filename("tps6598x_core"), filename("tps6598x")), (),
    ))
    lrw = subject.ordered_lookup(dependency_bytes("lrw", builtin="ecb"), "lrw", NAMES, DEPENDENCIES, {"ecb"})
    self.assertEqual(lrw, subject.Lookup("lrw", filename("lrw"), (filename("lrw"),), ("ecb",)))
    for malformed in (raw.replace(b" \n", b"\n"), raw.replace(b" \n", b"  \n")):
      with self.subTest(malformed=sha256(malformed)), self.assertRaisesRegex(
        subject.ControlError, "^LOOKUP_FORMAT$",
      ):
        subject.ordered_lookup(malformed, "tps6598x", NAMES, DEPENDENCIES, {"ecb"})

  def test_reordered_dependency_is_rejected(self) -> None:
    raw = dependency_bytes("tps6598x_core", "typec", "tps6598x")
    with self.assertRaisesRegex(subject.ControlError, "^LOOKUP_ORDER$"):
      subject.ordered_lookup(raw, "tps6598x", NAMES, DEPENDENCIES, {"ecb"})

  def test_missing_extra_duplicate_and_unsafe_lookup_records(self) -> None:
    correct = dependency_bytes("typec", "tps6598x_core", "tps6598x")
    for raw in (
      dependency_bytes("tps6598x"), dependency_bytes("typec", "tps6598x_core", "other", "tps6598x"),
      correct + dependency_bytes("tps6598x"), correct.replace(b"/work/lookup-root/", b"/boot/"),
      b"install arbitrary\n", correct[:-1], correct + b"\n", b"x" * (1024 * 1024 + 1),
    ):
      with self.subTest(raw=sha256(raw)), self.assertRaisesRegex(subject.ControlError, "^LOOKUP_"):
        subject.ordered_lookup(raw, "tps6598x", NAMES, DEPENDENCIES, {"ecb"})

  def test_only_lrw_may_resolve_the_expected_ecb_builtin(self) -> None:
    for raw, name, builtins in (
      (dependency_bytes("typec", builtin="ecb"), "typec", {"ecb"}),
      (dependency_bytes("lrw"), "lrw", {"ecb"}),
      (dependency_bytes("lrw", builtin="unexpected"), "lrw", {"ecb", "unexpected"}),
      (dependency_bytes("lrw", builtin="ecb"), "lrw", set()),
      (dependency_bytes("lrw", builtin="ecb").replace(b"builtin ecb\n", b"builtin ecb \n"),
       "lrw", {"ecb"}),
    ):
      with self.subTest(name=name), self.assertRaisesRegex(subject.ControlError, "^LOOKUP_"):
        subject.ordered_lookup(raw, name, NAMES, DEPENDENCIES, builtins)

  def test_operational_control_and_t1_assembly_remain_closed(self) -> None:
    with self.assertRaisesRegex(subject.ControlError, "^E_CONTROL_UNAVAILABLE$"):
      subject.main()
    self.assertIsNone(contract.T1_MODULE_SHA256)
    self.assertIsNone(contract.T1_BUILD_ID)
    self.assertIsNone(contract.E_CONTROL_PROOF_SHA256)
    with self.assertRaisesRegex(contract.ImageContractError, "^T1_ASSEMBLY_UNAVAILABLE$"):
      contract.require_operational_bindings()

  def test_active_caps_kill_and_reap_long_lived_children(self) -> None:
    for label, code, stream, expected in (
      ("long-stdout", "import os, time; os.write(1, b'x' * 9); time.sleep(5)", "stdout", b"x" * 8),
      ("long-stderr", "import os, time; os.write(2, b'e' * 9); time.sleep(5)", "stderr", b"e" * 8),
    ):
      with self.subTest(stream=stream):
        root = child_root(label)
        commands = subject.Commands(root)
        started = time.monotonic()
        with self.assertRaisesRegex(subject.ControlError, "^CHILD_OUTPUT_LIMIT$"):
          commands.run(python_child(code), timeout=4.0, stdout_limit=8, stderr_limit=8)
        elapsed = time.monotonic() - started
        self.assertLess(elapsed, 2.0, "post-exit truncation or the four-second timeout is not an active cap")
        self.assertEqual(read_regular(root / f"child-000.{stream}"), expected)
        report = child_report(root)
        self.assertEqual((report["status"], report["returncode"]), ("CHILD_OUTPUT_LIMIT", -signal.SIGKILL))
        self.assertIs(report["killed"], True)
        self.assertIs(report["reaped"], True)
        pid = report["pid"]
        self.assertIs(type(pid), int)
        if not isinstance(pid, int):
          self.fail("child pid is not an integer")
        self.assertGreater(pid, 1)
        self.assertNotEqual(pid, os.getpid())
        with self.assertRaises(ChildProcessError):
          os.waitpid(pid, os.WNOHANG)
        with self.assertRaises(ProcessLookupError):
          os.kill(pid, 0)
        self.assertEqual(commands.count, 1)
        save_json(WORK / f"long-cap-{stream}.json", {
          "command": list(python_child(code)), "measured_elapsed_seconds": elapsed,
          "returncode": report["returncode"], "output_sha256": sha256(expected),
          "waitpid_after_runner": "ECHILD", "kill_zero_after_runner": "ESRCH",
          "active_cap_before_four_second_timeout_and_five_second_exit": True,
        })

  def test_active_deadlines_kill_and_reap_before_normal_exit(self) -> None:
    command = python_child("import time; time.sleep(1)")
    for label, budget, timeout, expected in (
      ("active-child-time", 30.0, 0.2, "CHILD_TIMEOUT"),
      ("active-total-time", 0.2, 30.0, "CONTROL_DEADLINE"),
    ):
      with self.subTest(status=expected):
        root = child_root(label)
        commands = subject.Commands(root, budget_seconds=budget)
        started = time.monotonic()
        with self.assertRaisesRegex(subject.ControlError, f"^{expected}$"):
          commands.run(command, timeout=timeout)
        elapsed = time.monotonic() - started
        self.assertLess(elapsed, 0.8, "post-exit timeout classification is not an active deadline")
        report = child_report(root)
        self.assertEqual((report["status"], report["returncode"]), (expected, -signal.SIGKILL))
        self.assertIs(report["killed"], True)
        self.assertIs(report["reaped"], True)
        pid = report["pid"]
        self.assertIs(type(pid), int)
        if not isinstance(pid, int):
          self.fail("child pid is not an integer")
        self.assertGreater(pid, 1)
        self.assertNotEqual(pid, os.getpid())
        with self.assertRaises(ChildProcessError):
          os.waitpid(pid, os.WNOHANG)
        with self.assertRaises(ProcessLookupError):
          os.kill(pid, 0)
        self.assertEqual(commands.count, 1)
        if expected == "CONTROL_DEADLINE":
          with self.assertRaisesRegex(subject.ControlError, "^CONTROL_DEADLINE$"):
            commands.run(command)
          self.assertEqual(commands.count, 1)
          self.assertFalse((root / "child-001.json").exists())
        save_json(WORK / f"{label}.json", {
          "command": list(command), "measured_elapsed_seconds": elapsed,
          "status": expected, "returncode": report["returncode"],
          "waitpid_after_runner": "ECHILD", "kill_zero_after_runner": "ESRCH",
          "active_deadline_before_one_second_exit": True,
          "cumulative_second_child_refusal_checked": expected == "CONTROL_DEADLINE",
        })


def main() -> int:
  try:
    setup_fixtures()
  except (OSError, RuntimeError, ValueError, KeyError, TypeError) as error:
    print(f"SETUP FAIL: {type(error).__name__}: {error}", file=sys.stderr)
    return 2
  print("SETUP PASS: pinned sources, real confined files, 200 ASCII fixtures and literal dependency oracle",
        flush=True)
  program = unittest.main(argv=sys.argv, verbosity=2, exit=False)
  result = program.result
  try:
    for path, digest in PINS.items():
      _, after = read_source(path, digest)
      require(after == SOURCE_STATES[path], "source identity changed")
    for path, digest in FIXTURE_PINS.items():
      read_regular(path, digest)
      require(identity(path.lstat()) == FIXTURE_STATES[path], "immutable fixture changed")
    expected_count = 3 if sys.argv[1:] else 18
    require(result.testsRun == expected_count, "test selection count differs")
    child_records = sorted(Path("/work").glob("e-control-children-*/child-*.json"))
    if result.wasSuccessful() and not result.skipped and not sys.argv[1:]:
      require(len(child_records) == 11, "full fixture child count differs")
    save_json(WORK / "test-result.json", {
      "setup": "PASS", "tests": result.testsRun, "failures": len(result.failures),
      "errors": len(result.errors), "skipped": len(result.skipped),
      "failed_tests": [test.id() for test, _ in result.failures],
      "error_tests": [test.id() for test, _ in result.errors],
      "sources_unchanged": True, "immutable_fixtures_unchanged": True,
      "subject_sha256": SOURCE_SHA256, "real_image_or_module_input": False,
      "fixture_child_records": len(child_records),
      "candidate_image_created": False, "module_loaded": False,
    })
  except (OSError, RuntimeError, ValueError, KeyError, TypeError) as error:
    print(f"POSTCHECK FAIL: {type(error).__name__}: {error}", file=sys.stderr)
    return 2
  if result.errors or result.skipped:
    return 2
  if result.failures:
    return 1
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
