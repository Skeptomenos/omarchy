"""Test-only T1 raw-contract runner; execute only in the reviewed sandbox.

Source authentication and real fixture setup precede every test assertion.
The selected RED tests exercise missing behavior, not an import or setup
error. These synthetic payloads never stand in for accepted kernel binaries.
No old main, subprocess, depmod, general extraction, or assembler is invoked.
"""

from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
from types import ModuleType
import unittest
import zlib


SOURCE = Path("/inputs/subject/image_contract.py")
SOURCE_SHA256 = "a1eda280aa56967aa06b01a2cca0dfc70c3da6df25066f8a1e815beec719f1bf"
ASSEMBLY = Path("/inputs/assembly/prepare_image.py")
PINS = {
  SOURCE: SOURCE_SHA256,
  ASSEMBLY: "00caceb3b7fa236dcc030fb4007d0baa75bfa08fcd1590626f85fcc8c22d5f60",
  Path("/inputs/control/verify_control.py"):
    "10b5afe6cff38df7b6ebe5619fd9a34935932a4b369f3a9ad2a51923c32932d8",
  Path("/inputs/helper/cpio_image.py"):
    "a32eddd159263d19ff87d7e9caee9d53d17ef5c350fbffe9e7eb142cb43ebf58",
}
WORK = Path("/work/t1-image-fixtures")


def require(condition: bool, detail: str) -> None:
  if not condition:
    raise RuntimeError(detail)


def identity(info: os.stat_result) -> tuple[int, ...]:
  return (info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_gid,
          info.st_nlink, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def read_source(path: Path, digest: str) -> tuple[bytes, tuple[int, ...]]:
  require(path in PINS and PINS[path] == digest, "unapproved source binding")
  for parent in (Path("/"), Path("/inputs"), path.parent):
    require(stat.S_ISDIR(parent.lstat().st_mode), "source parent is not a real directory")
  before = path.lstat()
  require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1
          and 0 < before.st_size < 128 * 1024, "source is not bounded regular single-link")
  descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC)
  with os.fdopen(descriptor, "rb") as stream:
    require(identity(os.fstat(stream.fileno())) == identity(before), "source changed on open")
    raw = stream.read(128 * 1024)
    require(identity(os.fstat(stream.fileno())) == identity(before) == identity(path.lstat()),
            "source changed during read")
  require(len(raw) == before.st_size and hashlib.sha256(raw).hexdigest() == digest,
          "source pin mismatch")
  return raw, identity(before)


def load_source(name: str, path: Path, raw: bytes) -> ModuleType:
  require(name not in sys.modules, "module already imported")
  module = ModuleType(name)
  module.__file__ = str(path)
  sys.modules[name] = module
  exec(compile(raw, str(path), "exec"), module.__dict__)
  return module


def bootstrap() -> tuple[ModuleType, dict[Path, tuple[int, ...]]]:
  require(os.getuid() == os.getgid() == 1001 and Path.cwd() == Path("/work"),
          "unexpected test identity or directory")
  require(sys.flags.isolated == 1 and sys.flags.no_site == 1 and sys.dont_write_bytecode,
          "isolated Python flags required")
  require(not any(Path(name).exists() for name in ("/proc", "/sys", "/run", "/home", "/boot")),
          "host tree visible")
  require(not any(name in sys.modules for name in ("cpio_image", "verify_control", "prepare_image")),
          "legacy dependency already imported")
  sources = {path: read_source(path, digest) for path, digest in PINS.items()}
  # Its top level authenticates the fixed control/cpio chain. No main runs.
  load_source("prepare_image", ASSEMBLY, sources[ASSEMBLY][0])
  subject = load_source("t1_image_contract", SOURCE, sources[SOURCE][0])
  return subject, {path: value[1] for path, value in sources.items()}


try:
  subject, SOURCE_STATES = bootstrap()
  from cpio_image import Archive, ArchiveError, parse_newc, replace_members
except (OSError, RuntimeError, ValueError, SyntaxError, ImportError) as error:
  print(f"SETUP FAIL: {type(error).__name__}: {error}", file=sys.stderr)
  raise SystemExit(2) from None


PREFIX = "usr/lib/modules/7.1.6-1-1-ARCH/"
TIPD = PREFIX + "kernel/drivers/usb/typec/tipd/tps6598x-core.ko"
FRONTEND = PREFIX + "kernel/drivers/usb/typec/tipd/tps6598x.ko"
ATC = PREFIX + "kernel/drivers/phy/apple/phy-apple-atc.ko"
DWC = PREFIX + "kernel/drivers/usb/dwc3/dwc3-apple.ko"
KEEP = PREFIX + "kernel/drivers/fixture/keep.ko"
OLD_TIPD = b"fixture-only original TIPD; not an ELF module"
NEW_TIPD = b"fixture-only changed TIPD; not an ELF module; different length"
INDEXES = frozenset(("modules.alias.bin", "modules.builtin.alias.bin", "modules.builtin.bin",
                     "modules.dep.bin", "modules.devname", "modules.softdep", "modules.symbols.bin"))
FIXED_INDEX_HASHES = {
  "modules.alias.bin": "ca6ca7be95509eb294c2e67090bfa84dcbab855fb0489e504804593a257c4ea9",
  "modules.builtin.alias.bin": "9635eaa0d8c3d2f89c98789adce44dfd047f8cb11c7c9d0aa60199defc2ad962",
  "modules.builtin.bin": "edf2e707c121431f4f77b842ffd0a37fad5c0a6df198296fd6ef0b7f3227ac74",
  "modules.dep.bin": "436095f4779ccbd9f0c44b90febef13b62be50c9518dd499c151843fdf1feb3d",
  "modules.devname": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "modules.softdep": "6a8f2009d87deba7a2de46e3d0c46b114fe388d188b00b9a382fc2156aabb676",
  "modules.symbols.bin": "a3f1e745b7675daaec99c7c7ebadc7d67b318143901e063674494c210b12ace6",
}
BEFORE: Archive
GOOD: Archive
FIXTURE_PINS: dict[Path, str] = {}
FIXTURE_STATES: dict[Path, tuple[int, ...]] = {}


def sha256(raw: bytes) -> str:
  return hashlib.sha256(raw).hexdigest()


def json_bytes(value: object) -> bytes:
  return (json.dumps(value, sort_keys=True, allow_nan=False) + "\n").encode("ascii")


def write_json(name: str, value: object) -> None:
  subject.write_new(WORK / name, json_bytes(value))


def record(name: str, payload: bytes = b"", *, inode: int = 1,
           mode: int = stat.S_IFREG | 0o644, links: int = 0) -> bytes:
  encoded = name.encode("ascii") + b"\0"
  fields = (inode, mode, 0, 0, links, 0xABCDEF, len(payload), 0, 0, 0, 0, len(encoded), 0)
  raw = b"070701" + b"".join(f"{value:08X}".encode("ascii") for value in fields) + encoded
  return raw + b"\0" * (-len(raw) % 4) + payload + b"\0" * (-len(payload) % 4)


def fixture_archive() -> Archive:
  files = {
    TIPD: OLD_TIPD, FRONTEND: b"fixture unchanged I2C frontend",
    ATC: b"fixture unchanged ATC", DWC: b"fixture unchanged packaged DWC",
    KEEP: b"fixture unrelated module", "etc/fixture": b"unchanged config",
    **{PREFIX + name: ("unchanged " + name).encode("ascii") for name in sorted(INDEXES)},
  }
  parents = {str(parent) for name in files for parent in Path(name).parents if parent != Path(".")}
  records = [record("./", mode=stat.S_IFDIR | 0o755, links=2)]
  records.extend(record("./" + name + "/", inode=index, mode=stat.S_IFDIR | 0o755)
                 for index, name in enumerate(sorted(parents, key=lambda name: (name.count("/"), name)), 2))
  records.extend(record("./" + name, payload, inode=index)
                 for index, (name, payload) in enumerate(files.items(), len(records) + 1))
  records.extend((record("lib", b"/usr/lib", inode=700, mode=stat.S_IFLNK | 0o777),
                  record("etc/hard-a", b"linked fixture", inode=777, links=2),
                  record("etc/hard-b", inode=777, links=2)))
  raw = b"".join(records) + record("TRAILER!!!", inode=0, mode=0, links=1)
  return parse_newc(raw + b"\0" * (-len(raw) % 512))


def index_payloads(archive: Archive) -> dict[str, bytes]:
  return {member.name[len(PREFIX):]: member.payload for member in archive.members
          if member.name in {PREFIX + name for name in INDEXES}}


def change_field(archive: Archive, name: str, field: int, value: int) -> Archive:
  rows: list[bytes] = []
  found = False
  for member in archive.members:
    raw = member.raw
    if member.name == name:
      found = True
      start = 6 + field * 8
      raw = raw[:start] + f"{value:08x}".encode("ascii") + raw[start + 8:]
    rows.append(raw)
  require(found, "fixture metadata target missing")
  return parse_newc(b"".join(rows) + archive.tail)


def e_header() -> dict[str, object]:
  return {
    "schema": 1, "kind": "dev147-t1-e-control-v1",
    "base_sha256": "4d4f0557af57eebcc33322f004bcc7968254e644b069a11102375df0b31a52ae",
    "base_bytes": 19191513, "early_records": 7, "early_bytes": 10240,
    "early_sha256": "967bc6adcff42e59abcfb4e509f6c80fd65588e0861d8c1c3189a135f10955b4",
    "main_records": 1163, "main_bytes": 61286668,
    "main_sha256": "7be7b4b03367b5ce4b356fe35977edba6540af0a7df930dbff990286c9b98e28",
    "module_count": 200, "indexes": dict(FIXED_INDEX_HASHES),
    "no_change_archive": True, "gzip_exact": True, "binary_only_lookup": True,
    "module_loaded": False, "image_staged": False,
  }


def setup_fixtures() -> None:
  global BEFORE, GOOD
  os.umask(0o077)
  WORK.mkdir(mode=0o700)
  require(subject.TIPD == TIPD and subject.FRONTEND == FRONTEND
          and subject.ATC == ATC and subject.DWC == DWC, "subject target constants drift")
  require(subject.INDEX_SHA256 == FIXED_INDEX_HASHES, "subject index pins drift")
  BEFORE = fixture_archive()
  GOOD = parse_newc(replace_members(BEFORE, {TIPD: NEW_TIPD}, ()))
  require(replace_members(BEFORE, {}, ()) == BEFORE.raw, "fixture raw no-op failed")
  require(tuple(member.name for member in BEFORE.members) ==
          tuple(member.name for member in GOOD.members), "fixture changed membership")
  changed = [(old, new) for old, new in zip(BEFORE.members, GOOD.members, strict=True)
             if old.raw != new.raw]
  require(len(changed) == 1 and changed[0][0].name == TIPD
          and changed[0][0].payload == OLD_TIPD and changed[0][1].payload == NEW_TIPD,
          "fixture is not exactly the intended TIPD delta")
  require(BEFORE.tail == GOOD.tail and index_payloads(BEFORE) == index_payloads(GOOD)
          and set(index_payloads(BEFORE)) == INDEXES, "fixture indexes or tail changed")
  for name, raw in (("e-shaped.cpio", BEFORE.raw), ("tipd-only.cpio", GOOD.raw)):
    path = WORK / name
    subject.write_new(path, raw)
    FIXTURE_PINS[path] = sha256(raw)
    FIXTURE_STATES[path] = identity(path.lstat())
  write_json("fixture-setup.json", {
    "verdict": "PASS", "scope": "synthetic raw structure only; not a real E or T1 image",
    "source_sha256": SOURCE_SHA256, "base_records": len(BEFORE.members),
    "changed_records": 1, "indexes_unchanged": 7, "raw_noop": True,
    "base_sha256": sha256(BEFORE.raw), "candidate_sha256": sha256(GOOD.raw),
    "t1_binary_bound": False, "subprocesses": 0,
  })


class ArchiveContractTests(unittest.TestCase):
  def test_tipd_only_zero_index_delta_is_accepted(self) -> None:
    actual = subject.archive_delta(BEFORE, GOOD, NEW_TIPD)
    write_json("positive-delta-observation.json", {
      "returned_type": type(actual).__name__,
      "returned_none": actual is None, "source_sha256": SOURCE_SHA256,
    })
    self.assertIsInstance(actual, subject.ArchiveDelta, "valid TIPD-only structural delta was not recognized")
    self.assertEqual(actual, subject.ArchiveDelta(TIPD, sha256(OLD_TIPD), sha256(NEW_TIPD),
                                                len(BEFORE.members) - 1, 7))
    subject.validate_zero_index_delta(index_payloads(BEFORE), index_payloads(GOOD))

  def test_each_index_change_is_rejected(self) -> None:
    before = index_payloads(BEFORE)
    rejected: list[str] = []
    for name in sorted(INDEXES):
      after = before | {name: before[name] + b"\n"}
      try:
        subject.validate_zero_index_delta(before, after)
      except subject.ImageContractError as error:
        self.assertEqual(str(error), "INDEX_BYTES")
        rejected.append(name)
    write_json("index-change-observation.json", {"attempted": sorted(INDEXES), "rejected": rejected})
    self.assertEqual(rejected, sorted(INDEXES), "every changed index must be rejected")

  def test_indexes_cannot_change_inside_the_archive(self) -> None:
    for name in sorted(INDEXES):
      bad = parse_newc(replace_members(GOOD, {PREFIX + name: b"forbidden index bytes"}, ()))
      with self.subTest(index=name), self.assertRaisesRegex(subject.ImageContractError, "^ARCHIVE_RAW_RECORD$"):
        subject.archive_delta(BEFORE, bad, NEW_TIPD)

  def test_unrelated_modules_config_and_links_stay_raw(self) -> None:
    for name in (ATC, DWC, FRONTEND, KEEP, "etc/fixture"):
      bad = parse_newc(replace_members(GOOD, {name: b"forbidden unrelated payload"}, ()))
      with self.subTest(member=name), self.assertRaisesRegex(subject.ImageContractError, "^ARCHIVE_RAW_RECORD$"):
        subject.archive_delta(BEFORE, bad, NEW_TIPD)
    for name, field, value in (("lib", 3, 1), ("etc/hard-a", 4, 1), ("etc/hard-b", 0, 778)):
      bad = change_field(GOOD, name, field, value)
      with self.subTest(member=name), self.assertRaisesRegex(subject.ImageContractError, "^ARCHIVE_RAW_RECORD$"):
        subject.archive_delta(BEFORE, bad, NEW_TIPD)

  def test_missing_extra_reordered_members_and_tail_are_rejected(self) -> None:
    missing = parse_newc(b"".join(member.raw for member in GOOD.members if member.name != KEEP) + GOOD.tail)
    reordered = parse_newc(b"".join(member.raw for member in reversed(GOOD.members)) + GOOD.tail)
    added = [parse_newc(replace_members(GOOD, {}, ((name, b"forbidden extra"),)))
             for name in (PREFIX + "modules.dep", PREFIX + "kernel/extra.ko")]
    for bad in (missing, reordered, *added):
      with self.subTest(shape=sha256(bad.raw)), self.assertRaisesRegex(subject.ImageContractError, "^ARCHIVE_MEMBERS$"):
        subject.archive_delta(BEFORE, bad, NEW_TIPD)
    with self.assertRaisesRegex(subject.ImageContractError, "^ARCHIVE_TAIL$"):
      subject.archive_delta(BEFORE, parse_newc(GOOD.raw + b"\0" * 4), NEW_TIPD)

  def test_tipd_metadata_and_raw_header_spelling_are_preserved(self) -> None:
    old = next(member for member in GOOD.members if member.name == TIPD)
    for field, value in ((0, old.fields[0] + 1), (1, stat.S_IFREG | 0o600), (2, 1),
                         (3, 1), (4, 1), (5, old.fields[5] + 1), (7, 1), (8, 1), (9, 1), (10, 1)):
      with self.subTest(field=field), self.assertRaisesRegex(subject.ImageContractError, "^TIPD_METADATA$"):
        subject.archive_delta(BEFORE, change_field(GOOD, TIPD, field, value), NEW_TIPD)
    renamed = b"".join(record(TIPD, NEW_TIPD, inode=old.fields[0], mode=old.fields[1], links=old.fields[4])
                       if member.name == TIPD else member.raw for member in GOOD.members)
    with self.assertRaisesRegex(subject.ImageContractError, "^TIPD_METADATA$"):
      subject.archive_delta(BEFORE, parse_newc(renamed + GOOD.tail), NEW_TIPD)
    with self.assertRaisesRegex(subject.ImageContractError, "^TIPD_RAW_HEADER$"):
      subject.archive_delta(BEFORE, change_field(GOOD, TIPD, 5, old.fields[5]), NEW_TIPD)

  def test_wrong_expected_noop_and_forged_models_are_rejected(self) -> None:
    with self.assertRaisesRegex(subject.ImageContractError, "^TIPD_EXPECTED_PAYLOAD$"):
      subject.archive_delta(BEFORE, GOOD, b"not the actual candidate payload")
    with self.assertRaisesRegex(subject.ImageContractError, "^TIPD_NO_CHANGE$"):
      subject.archive_delta(BEFORE, BEFORE, OLD_TIPD)
    forged = replace(GOOD, members=BEFORE.members)
    with self.assertRaisesRegex(subject.ImageContractError, "^ARCHIVE_MODEL$"):
      subject.archive_delta(BEFORE, forged, NEW_TIPD)
    with self.assertRaisesRegex(subject.ImageContractError, "^ARCHIVE_MODEL$"):
      subject.archive_delta(replace(BEFORE, raw=GOOD.raw), GOOD, NEW_TIPD)

  def test_index_set_types_and_equal_copy(self) -> None:
    before = index_payloads(BEFORE)
    subject.validate_zero_index_delta(before, dict(before))
    for after in ({}, {key: value for key, value in before.items() if key != "modules.dep.bin"},
                  before | {"modules.dep": b"forbidden"}):
      with self.subTest(keys=sorted(after)), self.assertRaisesRegex(subject.ImageContractError, "^INDEX_SET$"):
        subject.validate_zero_index_delta(before, after)
    malformed: dict[str, object] = dict(before)
    malformed["modules.alias.bin"] = bytearray(before["modules.alias.bin"])
    with self.assertRaisesRegex(subject.ImageContractError, "^INDEX_PAYLOAD_TYPE$"):
      subject.validate_zero_index_delta(before, malformed)


class IdentityContractTests(unittest.TestCase):
  def test_correct_synthetic_e_header_is_parsed_not_operational_proof(self) -> None:
    actual = subject.validate_e_control_header(json_bytes(e_header()))
    self.assertIsInstance(actual, subject.EControlHeader)
    self.assertEqual(actual, subject.EControlHeader(
      "4d4f0557af57eebcc33322f004bcc7968254e644b069a11102375df0b31a52ae",
      19191513, 1163, 200, tuple(sorted(FIXED_INDEX_HASHES.items()))))

  def test_w_identity_stale_counts_and_wrong_indexes_are_rejected(self) -> None:
    changes: tuple[tuple[str, object], ...] = (
      ("base_sha256", "ae8f1ed7f4f258f89931209cd7de6030be9f6875372d7329151b822a6ba2281f"),
      ("base_bytes", 19184103), ("main_records", 1162), ("main_bytes", 61265920),
      ("module_count", 199), ("early_records", 8), ("early_bytes", 10241),
      ("early_sha256", "0" * 64), ("main_sha256", "1" * 64),
      ("kind", "no_change_archive_and_indexes"),
      ("indexes", FIXED_INDEX_HASHES | {"modules.symbols.bin":
        "5077fb001a5c48a2135ce8f651606b18578610bc660f430a59114e76be4f9437"}),
      ("indexes", {name: value for name, value in FIXED_INDEX_HASHES.items() if name != "modules.dep.bin"}),
    )
    for key, value in changes:
      with self.subTest(field=key), self.assertRaisesRegex(subject.ImageContractError, "^E_PROOF_"):
        subject.validate_e_control_header(json_bytes(e_header() | {key: value}))

  def test_schema_json_and_bool_integer_coercions_are_rejected(self) -> None:
    correct = e_header()
    malformed = (
      b"[]", b"null", b'{"x":NaN}', b'{"x":Infinity}',
      json_bytes(correct).replace(b'"schema": 1', b'"schema": 1, "schema": 1'),
      json_bytes(correct | {"extra": True}), json_bytes({key: value for key, value in correct.items() if key != "kind"}),
      json_bytes(correct) + b" " * (2 * 1024 * 1024),
    )
    for raw in malformed:
      with self.subTest(raw=sha256(raw)), self.assertRaisesRegex(subject.ImageContractError, "^E_PROOF_"):
        subject.validate_e_control_header(raw)
    for key, value in (("schema", True), ("module_count", True), ("base_bytes", "19191513"),
                       ("no_change_archive", 1), ("gzip_exact", False), ("binary_only_lookup", 1),
                       ("module_loaded", 0), ("module_loaded", True), ("image_staged", 0)):
      with self.subTest(field=key, value=value), self.assertRaisesRegex(subject.ImageContractError, "^E_PROOF_"):
        subject.validate_e_control_header(json_bytes(correct | {key: value}))

  def test_wrong_complete_base_bytes_never_satisfy_fixed_e_identity(self) -> None:
    for payload in (b"", BEFORE.raw, GOOD.raw, b"\0" * 19191513,
                    b"4d4f0557af57eebcc33322f004bcc7968254e644b069a11102375df0b31a52ae"):
      with self.subTest(payload=sha256(payload)), self.assertRaisesRegex(subject.ImageContractError, "^E_BASE_IDENTITY$"):
        subject.validate_e_base(payload)

  def test_unbound_operational_identity_cannot_be_supplied_by_the_caller(self) -> None:
    self.assertIsNone(subject.T1_MODULE_SHA256)
    self.assertIsNone(subject.T1_BUILD_ID)
    self.assertIsNone(subject.E_CONTROL_PROOF_SHA256)
    with self.assertRaisesRegex(subject.ImageContractError, "^T1_ASSEMBLY_UNAVAILABLE$"):
      subject.require_operational_bindings()
    with self.assertRaises(TypeError):
      subject.require_operational_bindings(sha256=sha256(NEW_TIPD))


class PinnedDependencyTests(unittest.TestCase):
  def test_real_single_gzip_and_drift_rejections(self) -> None:
    raw = b"bounded fixture gzip content"
    packed = zlib.compress(raw, wbits=31)
    self.assertEqual(subject.single_gzip(packed, len(raw)), raw)
    for candidate, size in ((packed[:-1], len(raw)), (packed + b"trailing", len(raw)),
                            (packed + packed, len(raw) * 2), (packed, len(raw) - 1),
                            (packed, len(raw) + 1), (packed, 0)):
      with self.subTest(size=size, sha256=sha256(candidate)), self.assertRaises(RuntimeError):
        subject.single_gzip(candidate, size)

  def test_existing_output_symlink_and_wrong_file_hash_fail_closed(self) -> None:
    path = WORK / "existing-output.fixture"
    payload = b"unchanged real-file fixture"
    subject.write_new(path, payload)
    with self.assertRaises(ArchiveError):
      subject.write_new(path, b"must not replace")
    with self.assertRaises(ArchiveError):
      subject.read_regular(path, "0" * 64)
    link = WORK / "existing-symlink.fixture"
    link.symlink_to(path.name)
    with self.assertRaises(ArchiveError):
      subject.write_new(link, b"must not follow")
    self.assertEqual(subject.read_regular(path, sha256(payload)), payload)
    self.assertTrue(link.is_symlink())


def main() -> int:
  try:
    setup_fixtures()
  except (OSError, RuntimeError, ValueError, KeyError, TypeError) as error:
    print(f"SETUP FAIL: {type(error).__name__}: {error}", file=sys.stderr)
    return 2
  print("SETUP PASS: pinned sources, real newc fixtures, raw no-op and TIPD-only delta", flush=True)
  program = unittest.main(argv=sys.argv, verbosity=2, exit=False)
  result = program.result
  try:
    for path, digest in PINS.items():
      _, after = read_source(path, digest)
      require(after == SOURCE_STATES[path], "source identity changed during tests")
    for path, digest in FIXTURE_PINS.items():
      subject.read_regular(path, digest)
      require(identity(path.lstat()) == FIXTURE_STATES[path], "fixture identity changed during tests")
    report = {
      "setup": "PASS", "tests": result.testsRun, "failures": len(result.failures),
      "errors": len(result.errors), "skipped": len(result.skipped),
      "failed_tests": [test.id() for test, _ in result.failures],
      "error_tests": [test.id() for test, _ in result.errors],
      "sources_unchanged": True, "fixtures_unchanged": True,
      "source_sha256": SOURCE_SHA256, "subprocesses": 0, "candidate_image_created": False,
    }
    write_json("test-result.json", report)
  except (OSError, RuntimeError, ValueError) as error:
    print(f"POSTCHECK FAIL: {type(error).__name__}: {error}", file=sys.stderr)
    return 2
  if result.errors or result.skipped or result.testsRun == 0:
    return 2
  if result.failures:
    return 1
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
