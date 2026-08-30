"""Zero-child semantic contract for the fixed offline T1 assembler.

The suite authenticates every real fixed input before it imports the subject.
It never calls the assembler entry, launches a child, or creates an image.
"""

from dataclasses import asdict
import ast
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
from types import ModuleType
import unittest


TEST = Path("/inputs/test")
SUBJECT = Path("/inputs/recipe")
CONTRACT = Path("/inputs/contract/image_contract.py")
ASSEMBLY = Path("/inputs/assembly/prepare_image.py")
CONTROL = Path("/inputs/control/verify_control.py")
HELPER = Path("/inputs/helper/cpio_image.py")
BASE = Path("/inputs/base")
MODULE = Path("/inputs/module")
BUILD_PROOF = Path("/inputs/build-proof")
E_PROOF = Path("/inputs/e-proof")
SOURCE_PINS = {
  SUBJECT: "0facf27332e698bb24826a63b617e899d18bd591f399d869c5c91f12bb2f5552",
  CONTRACT: "a1eda280aa56967aa06b01a2cca0dfc70c3da6df25066f8a1e815beec719f1bf",
  ASSEMBLY: "00caceb3b7fa236dcc030fb4007d0baa75bfa08fcd1590626f85fcc8c22d5f60",
  CONTROL: "10b5afe6cff38df7b6ebe5619fd9a34935932a4b369f3a9ad2a51923c32932d8",
  HELPER: "a32eddd159263d19ff87d7e9caee9d53d17ef5c350fbffe9e7eb142cb43ebf58",
}
DATA_PINS = {
  BASE: ("4d4f0557af57eebcc33322f004bcc7968254e644b069a11102375df0b31a52ae", 19191513),
  MODULE: ("a0fdadc351261643545e5afd8561923be99431661c447084336c9318f5b0c02f", 1327920),
  BUILD_PROOF: ("95abe335e44a5f30781a1e80f3e26efc314746b5d6baf11bae658f4484d9ada3", None),
  E_PROOF / "e-control-header.json":
    ("1665fe5a0d5d58eb3fa029faaea066da5c4b026415d19c33d644c5ec0b44f96a", 1149),
  E_PROOF / "e-control-evidence.json":
    ("6bbbb024d616bfa767dfe71b4a6121a1e75233bb1a1c8bc47b81b93f28628709", 965657),
  E_PROOF / "e-control-result.json":
    ("5e08a383469bd65d402939d0b7ca9cef9c2febb77ca12de1d577454b0d2de8f2", None),
}
FIXTURE_ROOT = Path("/work/t1-assembly-fixtures")
CANDIDATE = Path("/work/initramfs-linux-asahi-dpalt-tipddiag1.img")
RESULT = Path("/work/t1-assembly-result.json")
CHILD_PREFIX = "child-"


def sha256(raw: bytes) -> str:
  return hashlib.sha256(raw).hexdigest()


def identity(info: os.stat_result) -> tuple[int, ...]:
  return (info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_gid,
          info.st_nlink, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def read_pinned(path: Path, digest: str, maximum: int) -> bytes:
  before = path.lstat()
  if not (stat.S_ISREG(before.st_mode) and before.st_nlink == 1
          and 0 < before.st_size <= maximum):
    raise RuntimeError(f"unsafe fixed input: {path}")
  descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC)
  try:
    if identity(os.fstat(descriptor)) != identity(before):
      raise RuntimeError(f"input changed while opening: {path}")
    chunks: list[bytes] = []
    remaining = before.st_size
    while remaining:
      chunk = os.read(descriptor, min(remaining, 1024 * 1024))
      if not chunk:
        raise RuntimeError(f"input shortened: {path}")
      chunks.append(chunk)
      remaining -= len(chunk)
    if os.read(descriptor, 1) or identity(os.fstat(descriptor)) != identity(before):
      raise RuntimeError(f"input changed while reading: {path}")
  finally:
    os.close(descriptor)
  if identity(path.lstat()) != identity(before):
    raise RuntimeError(f"input name changed: {path}")
  raw = b"".join(chunks)
  if sha256(raw) != digest:
    raise RuntimeError(f"input digest differs: {path}")
  return raw


def input_bytes() -> dict[Path, bytes]:
  result = {path: read_pinned(path, digest, 256 * 1024)
            for path, digest in SOURCE_PINS.items()}
  for path, (digest, size) in DATA_PINS.items():
    maximum = 32 * 1024 * 1024 if path in (BASE, MODULE) else 2 * 1024 * 1024
    raw = read_pinned(path, digest, maximum)
    if size is not None and len(raw) != size:
      raise RuntimeError(f"input size differs: {path}")
    result[path] = raw
  return result


def load_subject(raw: bytes) -> ModuleType:
  module = ModuleType("assemble_t1")
  module.__file__ = str(SUBJECT)
  previous = sys.modules.get(module.__name__)
  sys.modules[module.__name__] = module
  try:
    exec(compile(raw, str(SUBJECT), "exec"), module.__dict__)
  except BaseException:
    if previous is None:
      del sys.modules[module.__name__]
    else:
      sys.modules[module.__name__] = previous
    raise
  return module


def output_members() -> set[str]:
  return {entry.name for entry in Path("/work").iterdir()}


def no_assembly_outputs() -> None:
  members = output_members()
  if (CANDIDATE.exists() or RESULT.exists() or "t1-lookup-root" in members
      or "t1-empty-modprobe.conf" in members or any(name.startswith(CHILD_PREFIX) for name in members)
      or any(path.suffix == ".img" for path in Path("/work").rglob("*"))):
    raise RuntimeError("assembler output or child record exists in zero-child fixture")


INPUTS = input_bytes()
no_assembly_outputs()
subject = load_subject(INPUTS[SUBJECT])


class T1AssemblyTests(unittest.TestCase):
  def test_a_fixed_policy_is_bound_without_execution(self) -> None:
    policy = subject.assembly_policy()
    self.assertIsInstance(policy, subject.AssemblyPolicy)
    self.assertEqual(asdict(policy), {
      "bindings": (
        "/inputs/recipe", "/inputs/contract", "/inputs/assembly", "/inputs/control",
        "/inputs/helper", "/inputs/base", "/inputs/module", "/inputs/build-proof",
        "/inputs/e-proof",
      ),
      "candidate": str(CANDIDATE), "result": str(RESULT),
      "lookup_root": "/work/t1-lookup-root",
      "commands": (
        ("/usr/bin/gzip", "-n"),
        ("/usr/bin/readelf", "-n", "/inputs/module"),
        ("/usr/bin/modinfo", "-b", "/work/t1-lookup-root", "-k", subject.KERNEL,
         "-F", "filename", "tps6598x_core"),
        ("/usr/bin/modinfo", "-b", "/work/t1-lookup-root", "-k", subject.KERNEL,
         "-F", "name", "tps6598x_core"),
        ("/usr/bin/modinfo", "-b", "/work/t1-lookup-root", "-k", subject.KERNEL,
         "-F", "depends", "tps6598x_core"),
        ("/usr/bin/modprobe", "--dry-run", "--show-depends", "-d",
         "/work/t1-lookup-root", "-S", subject.KERNEL, "-C",
         "/work/t1-empty-modprobe.conf", "tps6598x_core"),
      ),
    })
    self.assertEqual(subject._validate_build_id_output(
      b"Displaying notes found in: .note.gnu.build-id\n"
      b"  Owner                Data size \tDescription\n"
      b"  GNU                  0x00000014\tNT_GNU_BUILD_ID (unique build ID bitstring)\n"
      b"    Build ID: 40aa54382047ba36b02c9ac0da65a213862a77ad\n"
    ), subject.T1_BUILD_ID)
    for malformed in (b"Build ID: 00\n", b"Build ID: " + subject.T1_BUILD_ID.encode() + b" extra\n"):
      with self.assertRaisesRegex(subject.AssemblyError, "^T1_BUILD_ID_INVALID$"):
        subject._validate_build_id_output(malformed)
    valid_line = b"    Build ID: 40aa54382047ba36b02c9ac0da65a213862a77ad\n"
    for malformed in (b"", valid_line * 2, valid_line + b"\x00", valid_line * 2000,
                      valid_line.replace(b"40aa", b"40AA"), valid_line.rstrip(b"\n") + b" \n"):
      with self.subTest(build_id_output=malformed[:70]):
        with self.assertRaisesRegex(subject.AssemblyError, "^T1_BUILD_ID_INVALID$"):
          subject._validate_build_id_output(malformed)
    tipd = b"/work/t1-lookup-root/lib/modules/7.1.6-1-1-ARCH/kernel/drivers/usb/typec/tipd/tps6598x-core.ko"
    typec = b"/work/t1-lookup-root/lib/modules/7.1.6-1-1-ARCH/kernel/drivers/usb/typec/typec.ko"
    expected = (tipd + b"\n", b"tps6598x_core\n", b"typec\n",
                b"insmod " + typec + b" \ninsmod " + tipd + b" \n")
    subject._validate_lookup_outputs(expected)
    for field, malformed in (
      (0, tipd + b".other\n"), (1, b"tps6598x\n"), (2, b"\n"),
      (3, expected[3].replace(b" \n", b"\n")),
      (3, expected[3].replace(b" \n", b"  \n")),
      (3, b"insmod " + tipd + b" \ninsmod " + typec + b" \n"),
      (3, expected[3] + b"builtin ecb\n"),
    ):
      output = list(expected)
      output[field] = malformed
      with self.subTest(lookup_field=field, malformed=malformed):
        with self.assertRaisesRegex(subject.AssemblyError, "^T1_LOOKUP_INVALID$"):
          subject._validate_lookup_outputs(tuple(output))
    no_assembly_outputs()

  def test_b_real_fixed_inputs_validate_without_assembly(self) -> None:
    validated = subject.validate_fixed_inputs()
    self.assertIsInstance(validated, subject.ValidatedInputs)
    self.assertEqual(asdict(validated), {
      "base_sha256": DATA_PINS[BASE][0], "module_sha256": DATA_PINS[MODULE][0],
      "module_bytes": 1327920, "build_id": "40aa54382047ba36b02c9ac0da65a213862a77ad",
      "e_result_sha256": DATA_PINS[E_PROOF / "e-control-result.json"][0],
      "early_records": 7, "main_records": 1163,
    })
    build = json.loads(INPUTS[BUILD_PROOF])
    for field, replacement in (("module_sha256", "0" * 64), ("module_size", 1327919),
                               ("source_sha256", "0" * 64), ("build_id", "0" * 40)):
      changed = dict(build)
      changed[field] = replacement
      with self.subTest(build_field=field):
        with self.assertRaisesRegex(subject.AssemblyError, "^T1_BUILD_PROOF_INVALID$"):
          subject._validate_build_proof(json.dumps(changed).encode("ascii"))
    proofs = tuple(INPUTS[E_PROOF / name] for name in (
      "e-control-header.json", "e-control-evidence.json", "e-control-result.json",
    ))
    for index in range(3):
      changed = list(proofs)
      changed[index] += b"\n"
      with self.subTest(proof_bytes=index):
        with self.assertRaisesRegex(subject.AssemblyError, "^T1_E_PROOF_INVALID$"):
          subject._validate_e_proof(*changed)
    descriptor = json.loads(proofs[2])["header"]
    subject._validate_descriptor(descriptor, "/work/e-control-header.json", DATA_PINS[E_PROOF / "e-control-header.json"][0], 1149)
    for field, replacement in (("mode", 0o644), ("uid", 0), ("nlink", 2), ("bytes", True),
                               ("path", "/work/other.json"), ("sha256", "0" * 64)):
      changed = dict(descriptor)
      changed[field] = replacement
      with self.subTest(descriptor_field=field):
        with self.assertRaisesRegex(subject.AssemblyError, "^T1_E_PROOF_INVALID$"):
          subject._validate_descriptor(changed, "/work/e-control-header.json", DATA_PINS[E_PROOF / "e-control-header.json"][0], 1149)
    no_assembly_outputs()

  def test_c_fixed_private_entry_and_refusal_surface(self) -> None:
    self.assertEqual(subject.main.__code__.co_argcount, 0)
    self.assertIn("_run_fixed_assembly", subject.main.__code__.co_names)
    self.assertNotIn("getenv", INPUTS[SUBJECT].decode("utf-8"))
    self.assertNotIn("argparse", INPUTS[SUBJECT].decode("utf-8"))
    self.assertEqual(subject._publication_plan(), (str(CANDIDATE), str(RESULT)))
    tree = ast.parse(INPUTS[SUBJECT])
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    production = functions["_run_fixed_assembly"]
    self.assertEqual(ast.unparse(production.body[-1].value.func), "helper.write_new")
    self.assertEqual(ast.unparse(production.body[-1].value.args[0]), "RESULT")
    writes = [node for node in ast.walk(production) if isinstance(node, ast.Call)
              and ast.unparse(node.func) == "helper.write_new"]
    self.assertEqual([ast.unparse(node.args[0]) for node in writes], ["CANDIDATE", "RESULT"])
    calls = {ast.unparse(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)}
    self.assertFalse(calls & {"os.system", "subprocess.run", "os.unlink", "os.remove", "shutil.rmtree"})
    self.assertNotIn("/usr/bin/depmod", INPUTS[SUBJECT].decode("utf-8"))
    guards = [node for node in tree.body if isinstance(node, ast.If)]
    self.assertEqual(len(guards), 1)
    self.assertIs(tree.body[-1], guards[0])
    self.assertEqual(ast.unparse(guards[0].test), "__name__ == '__main__'")
    no_assembly_outputs()


def write_json(path: Path, value: object) -> None:
  path.parent.mkdir(mode=0o700, exist_ok=False)
  descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                       0o600)
  try:
    raw = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")
    if os.write(descriptor, raw) != len(raw):
      raise RuntimeError("short fixture-result write")
  finally:
    os.close(descriptor)


def main() -> int:
  if sys.argv[1:]:
    raise RuntimeError("this runner accepts only its complete fixed suite")
  program = unittest.main(argv=[sys.argv[0]], verbosity=2, exit=False)
  result = program.result
  no_assembly_outputs()
  unchanged = input_bytes() == INPUTS
  payload = {
    "setup": "PASS", "tests": result.testsRun, "failures": len(result.failures),
    "errors": len(result.errors), "skipped": len(result.skipped),
    "failed_tests": [test.id() for test, _trace in result.failures],
    "error_tests": [test.id() for test, _trace in result.errors],
    "inputs_unchanged": unchanged, "children_executed": 0, "image_created": False,
    "result_created": False, "module_loaded": False, "staged": False,
    "rebooted": False, "boot_tested": False, "subject_sha256": SOURCE_PINS[SUBJECT],
  }
  write_json(FIXTURE_ROOT / "test-result.json", payload)
  if result.errors or result.skipped or not unchanged:
    return 2
  return 1 if result.failures else 0


if __name__ == "__main__":
  raise SystemExit(main())
