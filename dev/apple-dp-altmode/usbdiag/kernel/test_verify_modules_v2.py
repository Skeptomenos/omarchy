"""Fixed-v2 GREEN contracts with real binaries/tools and separate parser cases.

Full identity negatives never rebind expected hashes. Deeper negative fixtures
transform retained real metadata/ELF bytes and call only the relevant validator;
they are not accepted binaries or hardware simulations. No build/load/image.
The frozen version-boundary RED and v1 verifier remain unchanged.
"""

from dataclasses import dataclass, replace
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import struct
import sys
from types import ModuleType
import unittest


SOURCE = Path("/inputs/subject/verify_modules_v2.py")
SOURCE_SHA256 = "be43b676d79bbc9b0dc9d182ef24ed75113e7816b02e9f6b73895bc700571f68"
SYMVERS_SHA256 = "d5eea549b9333f717fdc932683ea6633d58049c1e3f8f9e0be12e05d7610dd82"
ADDITIONS = {"_printk", "alt_cb_patch_nops", "of_machine_compatible_match", "of_find_node_opts_by_path", "of_node_put"}
NAMES = ("dwc3-apple", "phy-apple-atc")
ROLES = ("diagnostic", "control")


@dataclass(frozen=True)
class Fixture:
  name: str
  diagnostic_sha256: str
  diagnostic_build_id: str
  control_sha256: str
  control_build_id: str
  v1_sha256: str


FIXTURES = (
  Fixture(NAMES[0], "d9090119fee0252c9031185128ddd9d03bef9a0cbdfb118d8c71b7161d48b425",
          "92014543045243fb1680ac0e56b34c3ce69cc503",
          "d213e676593c1c4f9daceba1002f2381b6d390ce3eff9995043991a4d1e20975",
          "c0628ff7e26e3e3cb0dda8517bc2a34511ae85be",
          "d333ce2d82789d5da8acdc563fd04ea9cde3872472cde423ed1a51710cf38ef4"),
  Fixture(NAMES[1], "dea7e4eaee8928441a44480843795a68905e5122d435ae86dacc06fdf7b0efbe",
          "dc5bed70afdb1aa22a8cddd0a7f5ac2a2256ba49",
          "edb76a5fd6458406f6371f842a7a6a2b5f8b22b404ba622a5d081302662cc568",
          "def6d3cb64d2f7fff393c9da6fdde2e9ebbfc2c9",
          "504fc2b82e62e7497532dfe4b955228d7298a3f2c9b34d1e9623ed9188912547"),
)


def load_subject() -> ModuleType:
  for parent in SOURCE.parents:
    if not stat.S_ISDIR(parent.lstat().st_mode):
      raise RuntimeError("test subject parent is not a real directory")
  before = SOURCE.lstat()
  if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or not 0 < before.st_size < 128 * 1024:
    raise RuntimeError("invalid bounded test subject")
  descriptor = os.open(SOURCE, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC)
  with os.fdopen(descriptor, "rb") as stream:
    raw = stream.read(128 * 1024)
  if len(raw) != before.st_size or hashlib.sha256(raw).hexdigest() != SOURCE_SHA256:
    raise RuntimeError("test subject source pin mismatch")
  module = ModuleType("fixed_v2_subject")
  module.__file__ = str(SOURCE)
  if module.__name__ in sys.modules:
    raise RuntimeError("test subject already imported")
  sys.modules[module.__name__] = module
  exec(compile(raw, str(SOURCE), "exec"), module.__dict__)
  return module


subject = load_subject()


def changed_field(raw: bytes, offset: int, format_: str, value: int) -> bytes:
  result = bytearray(raw)
  struct.pack_into(format_, result, offset, value)
  return bytes(result)


class V2VerifierTests(unittest.TestCase):
  raw: dict[tuple[str, str], bytes]
  v1: dict[str, bytes]
  elf: dict[tuple[str, str], bytes]
  imports: dict[tuple[str, str], bytes]
  metadata: dict[tuple[str, str], subject.Metadata]
  symvers: bytes

  @classmethod
  def setUpClass(cls) -> None:
    os.umask(0o077)
    cls.raw, cls.v1, cls.elf, cls.imports, cls.metadata = {}, {}, {}, {}, {}
    cls.symvers = subject.read_fixed(Path("/inputs/symvers"), SYMVERS_SHA256)
    commands = subject.Commands(Path("/work/v2-fixture-metadata"))
    for fixture in FIXTURES:
      cls.v1[fixture.name] = subject.read_fixed(Path("/inputs/v1") / f"{fixture.name}.ko", fixture.v1_sha256)
      for role, digest in (("diagnostic", fixture.diagnostic_sha256), ("control", fixture.control_sha256)):
        key = (fixture.name, role)
        path = Path("/inputs") / role / f"{fixture.name}.ko"
        cls.raw[key] = subject.read_fixed(path, digest)
        cls.metadata[key] = subject.Metadata(*(commands.run(("/usr/bin/modinfo", "-F", field, str(path)))
                                              for field in ("name", "vermagic", "depends", "alias")))
        cls.imports[key] = commands.run(("/usr/bin/nm", "-u", str(path)))
        cls.elf[key] = commands.run(("/usr/bin/readelf", "-h", "-n", "-SW", str(path)))
    subject.require(commands.count == 24, "fixture real-tool coverage differs")

  def test_actual_fixed_v2_pair_main_passes(self) -> None:
    subject.main()
    result = json.loads(subject.guard.read_regular(Path("/work/v2-module-checks/RESULT.json")))
    self.assertEqual(result["verdict"], "PASS")
    self.assertEqual(result["commands"], 24)
    self.assertEqual([item["module"] for item in result["modules"]], list(NAMES))
    self.assertEqual([item["marker_count"] for item in result["modules"]], [20, 14])
    self.assertFalse(result["module_loaded"])
    self.assertFalse(result["image_changed"])

  def test_fixed_identities_roles_and_actual_inputs(self) -> None:
    for fixture in FIXTURES:
      for role, digest, build_id in (("diagnostic", fixture.diagnostic_sha256, fixture.diagnostic_build_id),
                                     ("control", fixture.control_sha256, fixture.control_build_id)):
        with self.subTest(module=fixture.name, role=role):
          self.assertEqual(subject.expected(fixture.name, subject.Role(role)), (digest, build_id))
          subject.validate_identity(fixture.name, subject.Role(role), self.raw[(fixture.name, role)])
    for name in ("dwc3", "unknown", "../dwc3-apple", "phy-apple-atc.ko"):
      with self.subTest(name=name), self.assertRaisesRegex(subject.VerificationError, "unknown module identity"):
        subject.identity_for(name)
    with self.assertRaisesRegex(subject.VerificationError, "unknown module role"):
      subject.expected(NAMES[0], "diagnostic")

  def test_full_identity_gate_rejects_v1_mixed_swapped_and_altered_pairs(self) -> None:
    good = {name: self.raw[(name, "diagnostic")] for name in NAMES}
    cases = (("both-v1", dict(self.v1), set(NAMES)),
             ("old-dwc", good | {NAMES[0]: self.v1[NAMES[0]]}, {NAMES[0]}),
             ("old-atc", good | {NAMES[1]: self.v1[NAMES[1]]}, {NAMES[1]}),
             ("swapped", {NAMES[0]: good[NAMES[1]], NAMES[1]: good[NAMES[0]]}, set(NAMES)),
             ("controls", {name: self.raw[(name, "control")] for name in NAMES}, set(NAMES)),
             ("altered-dwc", good | {NAMES[0]: good[NAMES[0]] + b"drift"}, {NAMES[0]}),
             ("altered-atc", good | {NAMES[1]: good[NAMES[1]][:-1]}, {NAMES[1]}))
    for label, pair, rejected in cases:
      for name in NAMES:
        with self.subTest(case=label, module=name):
          if name in rejected:
            with self.assertRaisesRegex(subject.VerificationError, "module identity mismatch"):
              subject.validate_identity(name, subject.Role.DIAGNOSTIC, pair[name])
          else:
            subject.validate_identity(name, subject.Role.DIAGNOSTIC, pair[name])
    for name in NAMES:
      with self.subTest(diagnostic_as_control=name), self.assertRaisesRegex(subject.VerificationError, "module identity mismatch"):
        subject.validate_identity(name, subject.Role.CONTROL, good[name])

  def test_binding_aware_imports_accept_actual_and_reject_each_delta_change(self) -> None:
    self.assertEqual(subject.ADDITIONS, ADDITIONS)
    for name in NAMES:
      raw = self.imports[(name, "diagnostic")]
      baseline_raw = self.imports[(name, "control")]
      actual, baseline = subject.parse_imports(raw), subject.parse_imports(baseline_raw)
      subject.validate_import_delta(name, actual, baseline)
      first = baseline[0].name.encode("ascii")
      changes = (raw + b"                 U unexpected_symbol\n",
                 raw.replace(b" U " + first + b"\n", b" w " + first + b"\n", 1),
                 raw.replace(b" U of_node_put\n", b" w of_node_put\n", 1),
                 raw.replace(b" U of_node_put\n", b" U strcmp\n", 1),
                 b"\n".join(line for line in raw.splitlines() if not line.endswith(b" " + first)) + b"\n")
      for bad in changes:
        with self.subTest(module=name, mutation=bad[-80:]):
          self.assertNotEqual(bad, raw)
          with self.assertRaises(subject.VerificationError):
            subject.validate_import_delta(name, subject.parse_imports(bad), baseline)
      weak_control = baseline_raw.replace(b" U " + first + b"\n", b" w " + first + b"\n", 1)
      with self.subTest(control_binding=name), self.assertRaisesRegex(subject.VerificationError, "control import binding"):
        subject.validate_import_delta(name, actual, subject.parse_imports(weak_control))

  def test_import_parser_rejects_malformed_duplicate_and_ambiguous_entries(self) -> None:
    for raw in (b"", b" U foo", b" T foo\n", b" U foo\n U foo\n", b" U foo\n w foo\n",
                b" U bad symbol\n", b" U " + b"x" * 257 + b"\n", b" U foo\r\n", b" U \xff\n"):
      with self.subTest(raw=raw[:40]), self.assertRaises(subject.VerificationError):
        subject.parse_imports(raw)

  def test_required_exports_preserve_owner_type_namespace_and_uniqueness(self) -> None:
    subject.validate_exports(self.symvers)
    lines = tuple(line for line in self.symvers.splitlines(keepends=True)
                  if len(line.split(b"\t")) >= 2 and line.split(b"\t")[1].decode("ascii") in ADDITIONS)
    self.assertEqual(len(lines), 5)
    selected = b"".join(lines)
    subject.validate_exports(selected)
    cases = (selected.replace(b"\tvmlinux\t", b"\tother/module\t", 1),
             selected.replace(b"\tEXPORT_SYMBOL\t", b"\tEXPORT_SYMBOL_GPL\t", 1),
             selected.replace(b"\tEXPORT_SYMBOL\t\n", b"\tEXPORT_SYMBOL\tPRIVATE\n", 1),
             selected + lines[0], b"".join(lines[1:]), selected.replace(b"0x00000000", b"bad-crc", 1))
    for raw in cases:
      with self.subTest(raw=raw[:100]), self.assertRaises(subject.VerificationError):
        subject.validate_exports(raw)

  def test_complete_prefixes_require_v2_component_board_port_and_control_absence(self) -> None:
    for name, component in zip(NAMES, ("dwc3", "atc"), strict=True):
      raw = self.raw[(name, "diagnostic")]
      subject.validate_markers(name, subject.Role.DIAGNOSTIC, raw)
      control = self.raw[(name, "control")]
      subject.validate_markers(name, subject.Role.CONTROL, control)
      cases = (raw.replace(b"dev147-usbdiag2-v1", b"dev147-usbdiag1-v1", 1),
               raw + b"dev147-usbdiag1-v1", raw.replace(b'"board":"j413"', b'"board":"j313"', 1),
               raw.replace(f'"component":"{component}"'.encode(), b'"component":"other"', 1),
               raw.replace(b'"target":"front_lower"', b'"target":"rear_upper"', 1),
               raw[:raw.index(b"dev147-usbdiag2-v1") + 8], b"no-markers")
      for bad in cases:
        with self.subTest(module=name, digest=hashlib.sha256(bad).hexdigest()), self.assertRaises(subject.VerificationError):
          subject.validate_markers(name, subject.Role.DIAGNOSTIC, bad)
      for marker in (b"dev147-usbdiag1-v1", b"dev147-usbdiag2-v1"):
        with self.subTest(control=name, marker=marker), self.assertRaisesRegex(subject.VerificationError, "control contains"):
          subject.validate_markers(name, subject.Role.CONTROL, control + marker)

  def test_actual_raw_elf_and_real_readelf_agree(self) -> None:
    for key, raw in self.raw.items():
      name, role = key
      with self.subTest(module=name, role=role):
        subject.validate_elf(name, subject.Role(role), raw, self.elf[key])

  def test_raw_elf_header_table_and_payload_bounds_are_independent_gates(self) -> None:
    key = (NAMES[0], "diagnostic")
    raw, elf = self.raw[key], self.elf[key]
    cases = (raw[:63], changed_field(raw, 4, "<B", 1), changed_field(raw, 5, "<B", 2),
             changed_field(raw, 16, "<H", 2), changed_field(raw, 18, "<H", 62),
             changed_field(raw, 40, "<Q", len(raw) + 8), changed_field(raw, 58, "<H", 0),
             changed_field(raw, 60, "<H", 0), changed_field(raw, 60, "<H", 4097),
             changed_field(raw, 62, "<H", 65535), raw[:-128])
    for bad in cases:
      with self.subTest(digest=hashlib.sha256(bad).hexdigest()), self.assertRaises(subject.VerificationError):
        subject.validate_elf(key[0], subject.Role.DIAGNOSTIC, bad, elf)
    table = struct.unpack_from("<Q", raw, 40)[0]
    sections = subject.sections(raw)
    index = next(index for index, section in enumerate(sections) if section.name == ".BTF")
    header = table + index * 64
    for offset, format_, value in ((0, "<I", 2**32 - 1), (4, "<I", 8), (24, "<Q", len(raw) + 1),
                                    (32, "<Q", 0), (32, "<Q", len(raw) + 1)):
      bad = changed_field(raw, header + offset, format_, value)
      with self.subTest(section_field=offset, value=value), self.assertRaises(subject.VerificationError):
        subject.validate_elf(key[0], subject.Role.DIAGNOSTIC, bad, elf)

  def test_raw_btf_and_build_note_identity_cannot_be_hidden_by_readelf_text(self) -> None:
    key = (NAMES[1], "diagnostic")
    raw, elf = self.raw[key], self.elf[key]
    table = struct.unpack_from("<Q", raw, 40)[0]
    sections = subject.sections(raw)
    btf_index = next(index for index, section in enumerate(sections) if section.name == ".BTF")
    note_index = next(index for index, section in enumerate(sections) if section.name == ".note.gnu.build-id")
    other_index = next(index for index, section in enumerate(sections) if section.name == ".BTF.base")
    btf_name = struct.unpack_from("<I", raw, table + btf_index * 64)[0]
    note_name = struct.unpack_from("<I", raw, table + note_index * 64)[0]
    note = sections[note_index]
    cases = (changed_field(raw, table + other_index * 64, "<I", btf_name),
             changed_field(raw, table + other_index * 64, "<I", note_name),
             changed_field(raw, table + note_index * 64 + 4, "<I", 1),
             changed_field(raw, table + note_index * 64 + 32, "<Q", 0),
             changed_field(raw, note.offset, "<I", 5),
             changed_field(raw, note.offset + 16, "<B", raw[note.offset + 16] ^ 1))
    for bad in cases:
      with self.subTest(digest=hashlib.sha256(bad).hexdigest()), self.assertRaises(subject.VerificationError):
        subject.validate_elf(key[0], subject.Role.DIAGNOSTIC, bad, elf)

  def test_transformed_readelf_header_note_and_btf_metadata_are_rejected(self) -> None:
    key = (NAMES[0], "diagnostic")
    raw, elf = self.raw[key], self.elf[key]
    btf_line = next(line for line in elf.splitlines(keepends=True) if re.search(rb"\s\.BTF\s+PROGBITS", line))
    build_id = FIXTURES[0].diagnostic_build_id.encode("ascii")
    cases = (elf.replace(b"AArch64", b"x86-64", 1), elf.replace(b"ELF64", b"ELF32", 1),
             elf.replace(b"REL (Relocatable file)", b"EXEC (Executable file)", 1),
             elf.replace(build_id, b"0" * 40, 1), elf + b"Build ID: " + build_id + b"\n",
             elf.replace(b"Build ID:", b"Absent ID:", 1), elf.replace(btf_line, b"", 1), elf + btf_line,
             re.sub(rb"(\s\.BTF\s+)PROGBITS", rb"\1NOBITS", elf, count=1),
             elf.replace(btf_line, re.sub(rb"(PROGBITS\s+[0-9a-f]+\s+)[0-9a-f]+", rb"\1ffffff", btf_line), 1))
    for bad in cases:
      with self.subTest(digest=hashlib.sha256(bad).hexdigest()):
        self.assertNotEqual(bad, elf)
        with self.assertRaises(subject.VerificationError):
          subject.validate_elf(key[0], subject.Role.DIAGNOSTIC, raw, bad)

  def test_module_metadata_fields_and_encoding_remain_strict(self) -> None:
    for name in NAMES:
      diagnostic, control = self.metadata[(name, "diagnostic")], self.metadata[(name, "control")]
      subject.validate_metadata(name, diagnostic, control)
      for field in ("name", "vermagic", "depends", "alias"):
        bad = replace(diagnostic, **{field: b"changed\n"})
        with self.subTest(module=name, field=field), self.assertRaises(subject.VerificationError):
          subject.validate_metadata(name, bad, control)
      bad = replace(diagnostic, alias=b"\xff")
      with self.assertRaisesRegex(subject.VerificationError, "invalid metadata text"):
        subject.validate_metadata(name, bad, bad)

  def test_input_guards_and_existing_outputs_fail_closed(self) -> None:
    root = Path("/work/v2-file-fixtures")
    root.mkdir(mode=0o700)
    good = root / "good"
    payload = b"bounded fixture"
    digest = hashlib.sha256(payload).hexdigest()
    subject.guard.write_new(good, payload)
    self.assertEqual(subject.read_fixed(good, digest), payload)
    exceptions = (subject.VerificationError, subject.guard.ArchiveError)
    for path in (root / "missing", Path("relative"), root / ".." / "escape"):
      with self.subTest(path=str(path)), self.assertRaises(exceptions):
        subject.read_fixed(path, digest)
    with self.assertRaises(subject.guard.ArchiveError):
      subject.guard.write_new(good, b"overwrite")
    self.assertEqual(good.read_bytes(), payload)
    leaf = root / "leaf-link"
    leaf.symlink_to(good)
    with self.assertRaises(exceptions):
      subject.read_fixed(leaf, digest)
    parent = root / "parent-link"
    parent.symlink_to(root, target_is_directory=True)
    with self.assertRaises(exceptions):
      subject.read_fixed(parent / "good", digest)
    oversized = root / "oversized"
    with oversized.open("xb") as stream:
      stream.truncate(subject.MAX_INPUT + 1)
    with self.assertRaisesRegex(subject.VerificationError, "input size bound"):
      subject.read_fixed(oversized, digest)
    changed = root / "changed"
    subject.guard.write_new(changed, payload + b"drift")
    with self.assertRaisesRegex(subject.VerificationError, "input digest mismatch"):
      subject.read_fixed(changed, digest)
    hard = root / "hard-link"
    os.link(good, hard)
    with self.assertRaises(subject.guard.ArchiveError):
      subject.read_fixed(hard, digest)

  def test_real_child_failures_are_bounded_retained_and_not_passes(self) -> None:
    cases = (("success", "import os; os.write(1, b'ok\\n')", "", 5, 128),
             ("nonzero", "import sys; sys.exit(7)", "child nonzero exit", 5, 128),
             ("stderr", "import os; os.write(2, b'problem\\n')", "child wrote stderr", 5, 128),
             ("invalid", "import os; os.write(1, bytes([255]))", "invalid metadata text", 5, 128),
             ("overflow", "import os; os.write(1, b'x' * 8192)", "child output_overflow", 5, 128),
             ("stderr-overflow", "import os; os.write(2, b'x' * 8192)", "child output_overflow", 5, 128),
             ("timeout", "import os,time; os.write(1, b'partial\\n'); time.sleep(2)", "child timeout", 1, 128))
    for label, code, message, timeout, bound in cases:
      with self.subTest(case=label):
        root = Path("/work") / f"v2-child-{label}"
        commands = subject.Commands(root)
        argv = ("/usr/bin/python3.14", "-I", "-S", "-B", "-c", code)
        if message:
          with self.assertRaisesRegex(subject.VerificationError, message):
            commands.run(argv, timeout=timeout, bound=bound)
        else:
          self.assertEqual(commands.run(argv, timeout=timeout, bound=bound), b"ok\n")
        result = json.loads(subject.guard.read_regular(root / "child-000.json"))
        self.assertLessEqual((root / "child-000.stdout").stat().st_size, bound)
        self.assertLessEqual((root / "child-000.stderr").stat().st_size, bound)
        self.assertEqual(result["stream_bound"], bound)
        if label == "timeout":
          self.assertEqual(result["status"], "timeout")
          self.assertEqual((root / "child-000.stdout").read_bytes(), b"partial\n")
        if "overflow" in label:
          self.assertEqual(result["status"], "output_overflow")
          self.assertIn(bound + 1, result["observed_bytes"])
        if label == "nonzero":
          self.assertEqual(result["returncode"], 7)
        if label == "invalid":
          self.assertEqual((root / "child-000.stdout").read_bytes(), bytes([255]))
        self.assertFalse((root / "RESULT.json").exists())
        with self.assertRaises(FileExistsError):
          subject.Commands(root)

  def test_source_and_production_input_pins_remain_unchanged(self) -> None:
    subject.read_fixed(SOURCE, SOURCE_SHA256)
    subject.read_fixed(Path("/inputs/symvers"), SYMVERS_SHA256)
    for fixture in FIXTURES:
      for role, digest in (("diagnostic", fixture.diagnostic_sha256), ("control", fixture.control_sha256)):
        with self.subTest(module=fixture.name, role=role):
          self.assertEqual(subject.read_fixed(Path("/inputs") / role / f"{fixture.name}.ko", digest),
                           self.raw[(fixture.name, role)])


if __name__ == "__main__":
  unittest.main(verbosity=2)
