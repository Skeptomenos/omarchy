"""GREEN companion for the exact new E-only helper after genuine legacy RED.

The frozen RED runner and old helpers stay unchanged. The archive fixtures and
expected E contract are unchanged. The subject is now the fixed E helper; text
index tests still call its authenticated prior validators without patching them.
No assembly main, compression, depmod, module build/load, or device test runs.
The approved no-install unittest/typed-stdlib exception remains in force.
"""

from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
from types import ModuleType
import unittest


SOURCE = Path("/inputs/e-helper/prepare_e_image.py")
SOURCE_SHA256 = "5168df187f1460b8d916b05be6d075b17b7ae9a10a59d6d8bb9d4644bcc33c49"
STOCK_DWC_SHA256 = "d150400f9782c876972b2745d95617cd44e23574452f63980704911a467f7767"
STOCK_ATC_SHA256 = "fd1c3d105bd69a649a38e89e2ca0bcbe6f656200a0f211d58211e8c7b3ec944b"
OLD_CONTROL_DWC_SHA256 = "d213e676593c1c4f9daceba1002f2381b6d390ce3eff9995043991a4d1e20975"
OLD_DIAGNOSTIC_DWC_SHA256 = "d333ce2d82789d5da8acdc563fd04ea9cde3872472cde423ed1a51710cf38ef4"
WORK = Path("/work/e-fixtures")


def require(condition: bool, detail: str) -> None:
  if not condition:
    raise RuntimeError(detail)


def load_subject() -> ModuleType:
  require(os.getuid() == os.getgid() == 1001 and Path.cwd() == Path("/work"),
          "unexpected test identity/directory")
  require(sys.flags.isolated == 1 and sys.flags.no_site == 1 and sys.dont_write_bytecode,
          "isolated Python flags required")
  require(not any(Path(name).exists() for name in ("/proc", "/sys", "/run", "/home", "/boot")),
          "host tree visible")
  for parent in (Path("/inputs"), SOURCE.parent):
    require(stat.S_ISDIR(parent.lstat().st_mode), "source parent is not a real directory")
  before = SOURCE.lstat()
  require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and 0 < before.st_size < 128 * 1024,
          "source is not bounded regular single-link input")
  descriptor = os.open(SOURCE, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC)
  def identity(info: os.stat_result) -> tuple[int, ...]:
    return (info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_gid,
            info.st_nlink, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
  with os.fdopen(descriptor, "rb") as stream:
    require(identity(os.fstat(stream.fileno())) == identity(before), "source changed on open")
    raw = stream.read(128 * 1024)
    require(identity(os.fstat(stream.fileno())) == identity(before) == identity(SOURCE.lstat()),
            "source changed while reading")
  require(len(raw) == before.st_size and hashlib.sha256(raw).hexdigest() == SOURCE_SHA256,
          "assembler source pin mismatch")
  name = "e_image_subject"
  require(name not in sys.modules, "subject already imported")
  module = ModuleType(name)
  module.__file__ = str(SOURCE)
  sys.modules[name] = module
  # This executes the exact old import/authentication path, never its main().
  exec(compile(raw, str(SOURCE), "exec"), module.__dict__)
  return module


subject = load_subject()
from cpio_image import Archive, ArchiveError, parse_newc, read_regular, replace_members, write_new


PREFIX = subject.PREFIX
ATC, DWC, TIPD, DWC_CORE = subject.ATC, subject.DWC, subject.TIPD, subject.DWC_CORE
KEEP_MODULE = "kernel/drivers/fixture/keep.ko"
INDEXES = frozenset(("modules.alias.bin", "modules.builtin.alias.bin", "modules.builtin.bin",
                     "modules.dep.bin", "modules.devname", "modules.softdep", "modules.symbols.bin"))
CHANGED = frozenset(("modules.dep.bin", "modules.alias.bin"))


def record(name: str, payload: bytes = b"", *, inode: int = 1,
           mode: int = stat.S_IFREG | 0o644, links: int = 0) -> bytes:
  encoded = name.encode("ascii") + b"\0"
  fields = (inode, mode, 0, 0, links, 0xABCDEF, len(payload), 0, 0, 0, 0, len(encoded), 0)
  raw = b"070701" + b"".join(f"{value:08X}".encode("ascii") for value in fields) + encoded
  return raw + b"\0" * (-len(raw) % 4) + payload + b"\0" * (-len(payload) % 4)


def fixture_archive(atc: bytes) -> Archive:
  files = {
    PREFIX + ATC: atc, PREFIX + TIPD: b"fixture-working-tipd-unchanged",
    PREFIX + DWC_CORE: b"fixture-dwc-core-unchanged",
    PREFIX + KEEP_MODULE: b"fixture-unrelated-module", "etc/fixture": b"keep-config",
    **{PREFIX + name: ("old-" + name).encode("ascii") for name in sorted(INDEXES)},
  }
  parents = {str(parent) for name in files for parent in Path(name).parents if parent != Path(".")}
  records = [record("./", mode=stat.S_IFDIR | 0o755, links=2)]
  records.extend(record("./" + name + "/", inode=index, mode=stat.S_IFDIR | 0o755)
                 for index, name in enumerate(sorted(parents, key=lambda name: (name.count("/"), name)), 2))
  records.extend(record("./" + name, payload, inode=index)
                 for index, (name, payload) in enumerate(files.items(), len(records) + 1))
  records.extend((record("lib", b"/usr/lib", inode=700, mode=stat.S_IFLNK | 0o777),
                  record("etc/hard-a", b"hardlink-data", inode=777, links=2),
                  record("etc/hard-b", inode=777, links=2)))
  raw = b"".join(records) + record("TRAILER!!!", mode=0, inode=0, links=1)
  return parse_newc(raw + b"\0" * (-len(raw) % 512))


def replacements() -> dict[str, bytes]:
  return {PREFIX + name: ("new-" + name).encode("ascii") for name in sorted(CHANGED)}


def transform(before: Archive, dwc: bytes, updates: dict[str, bytes] | None = None,
              extra: tuple[tuple[str, bytes], ...] = ()) -> Archive:
  selected = replacements() if updates is None else updates
  return parse_newc(replace_members(before, selected, ((PREFIX + DWC, dwc),) + extra))


def altered_field(archive: Archive, name: str, field: int, value: int) -> Archive:
  records: list[bytes] = []
  found = False
  for member in archive.members:
    raw = member.raw
    if member.name == name:
      found = True
      offset = 6 + field * 8
      raw = raw[:offset] + f"{value:08x}".encode("ascii") + raw[offset + 8:]
    records.append(raw)
  require(found, "fixture mutation target missing")
  return parse_newc(b"".join(records) + archive.tail)


class EArchiveTests(unittest.TestCase):
  before: Archive
  good: Archive
  dwc: bytes
  old_control: bytes
  old_diagnostic: bytes

  @classmethod
  def setUpClass(cls) -> None:
    os.umask(0o077)
    WORK.mkdir(mode=0o700)
    cls.dwc = read_regular(Path("/inputs/stock/dwc3-apple.ko"), STOCK_DWC_SHA256)
    atc = read_regular(Path("/inputs/stock/phy-apple-atc.ko"), STOCK_ATC_SHA256)
    cls.old_control = read_regular(Path("/inputs/control-modules/dwc3-apple.ko"), OLD_CONTROL_DWC_SHA256)
    cls.old_diagnostic = read_regular(Path("/inputs/diagnostic-modules/dwc3-apple.ko"), OLD_DIAGNOSTIC_DWC_SHA256)
    require(cls.old_control != cls.dwc and cls.old_diagnostic != cls.dwc,
            "provenance-negative modules do not differ")
    require(subject.CHANGED_INDEXES == CHANGED and subject.control.INDEX_NAMES == INDEXES,
            "fixed index contract drift")
    cls.before = fixture_archive(atc)
    cls.good = transform(cls.before, cls.dwc)
    require(replace_members(cls.before, {}, ()) == cls.before.raw, "fixture no-op roundtrip failed")
    require(tuple(member.name for member in cls.good.members) ==
            tuple(member.name for member in cls.before.members) + (PREFIX + DWC,),
            "fixture E membership differs")
    require(all(old.raw == new.raw for old, new in zip(cls.before.members, cls.good.members[:-1], strict=True)
                if old.name not in replacements()), "fixture changed an unrelated record")
    write_new(WORK / "baseline.cpio", cls.before.raw)
    write_new(WORK / "legitimate-e.cpio", cls.good.raw)
    write_new(WORK / "setup.json", b'{"parse_noop_raw_membership":"PASS","module_pins":"PASS"}\n')

  def test_packaged_dwc_only_delta_is_accepted(self) -> None:
    rejection: str | None = None
    changes: object = None
    try:
      changes = subject.archive_delta(self.before, self.good, replacements(), self.dwc)
    except RuntimeError as error:
      rejection = str(error)
    write_new(WORK / "positive-observation.json", (json.dumps({
      "rejection": rejection, "changes": changes, "source_sha256": SOURCE_SHA256,
      "before_sha256": hashlib.sha256(self.before.raw).hexdigest(),
      "after_sha256": hashlib.sha256(self.good.raw).hexdigest(),
      "packaged_dwc_sha256": STOCK_DWC_SHA256, "replacement_paths": sorted(replacements()),
    }, sort_keys=True) + "\n").encode("ascii"))
    self.assertIsNone(rejection, "legitimate E delta rejected by actual production archive gate")
    if not isinstance(changes, list):
      self.fail("production archive delta did not return its change list")
    self.assertEqual(len(changes), 3)

  def test_atc_replacement_is_not_an_e_delta(self) -> None:
    updates = replacements() | {PREFIX + ATC: b"replacement-atc-is-forbidden"}
    bad = transform(self.before, self.dwc, updates)
    with self.assertRaisesRegex(RuntimeError, "unapproved archive replacement set"):
      subject.archive_delta(self.before, bad, updates, self.dwc)

  def test_atc_tipd_other_modules_config_and_static_indexes_stay_raw(self) -> None:
    names = (PREFIX + ATC, PREFIX + TIPD, PREFIX + DWC_CORE, PREFIX + KEEP_MODULE,
             "etc/fixture", *(PREFIX + name for name in sorted(INDEXES - CHANGED)))
    for name in names:
      bad = transform(self.before, self.dwc, replacements() | {name: b"unauthorized-change"})
      with self.subTest(name=name), self.assertRaisesRegex(RuntimeError, "unrelated raw archive record changed"):
        subject.archive_delta(self.before, bad, replacements(), self.dwc)

  def test_extra_module_and_index_are_rejected(self) -> None:
    for name in (PREFIX + "kernel/drivers/fixture/extra.ko", PREFIX + "modules.dep"):
      bad = transform(self.before, self.dwc, extra=((name, b"extra"),))
      with self.subTest(name=name), self.assertRaisesRegex(RuntimeError, "membership/order differs"):
        subject.archive_delta(self.before, bad, replacements(), self.dwc)

  def test_old_control_diagnostic_and_corrupted_dwc_bytes_are_rejected(self) -> None:
    for label, raw in (("old-control", self.old_control), ("old-diagnostic", self.old_diagnostic),
                       ("corrupted-stock", self.dwc + b"drift")):
      bad = transform(self.before, raw)
      with self.subTest(provenance=label), self.assertRaisesRegex(RuntimeError, "new DWC member payload/metadata differs"):
        subject.archive_delta(self.before, bad, replacements(), self.dwc)

  def test_expected_dwc_argument_cannot_rebind_the_packaged_identity(self) -> None:
    for raw in (self.old_control, self.old_diagnostic, self.dwc + b"drift"):
      bad = transform(self.before, raw)
      with self.subTest(digest=hashlib.sha256(raw).hexdigest()), self.assertRaisesRegex(RuntimeError, "unapproved packaged DWC payload"):
        subject.archive_delta(self.before, bad, replacements(), raw)

  def test_fixed_e_inputs_exclude_diagnostic_modules_and_output_is_distinct(self) -> None:
    pins = subject.pinned_inputs()
    self.assertEqual(pins[Path("/inputs/stock/dwc3-apple.ko")], STOCK_DWC_SHA256)
    self.assertEqual(pins[Path("/inputs/stock/phy-apple-atc.ko")], STOCK_ATC_SHA256)
    self.assertFalse(any("diagnostic" in str(path) for path in pins))
    self.assertEqual(subject.CANDIDATE, Path("/work/initramfs-linux-asahi-dpalt-usbearly1.img"))
    self.assertNotEqual(subject.CANDIDATE, subject.prior.CANDIDATE)

  def test_changed_record_metadata_and_raw_header_case_are_rejected(self) -> None:
    name = PREFIX + "modules.dep.bin"
    original = next(member for member in self.good.members if member.name == name)
    for field, value in ((0, 999), (1, stat.S_IFREG | 0o600), (2, 1), (3, 1), (4, 1),
                         (5, 1), (7, 1), (8, 1), (9, 1), (10, 1), (5, original.fields[5])):
      # The final case changes uppercase hex to lowercase, not its numeric value.
      bad = altered_field(self.good, name, field, value)
      with self.subTest(field=field, value=value), self.assertRaisesRegex(RuntimeError, "metadata changed|header/name bytes"):
        subject.archive_delta(self.before, bad, replacements(), self.dwc)

  def test_unchanged_atc_metadata_and_symlink_payload_are_rejected(self) -> None:
    bad = altered_field(self.good, PREFIX + ATC, 5, 1)
    with self.assertRaisesRegex(RuntimeError, "unrelated raw archive record changed"):
      subject.archive_delta(self.before, bad, replacements(), self.dwc)
    records = [member.raw if member.name != "lib" else record("lib", b"/other", inode=700,
               mode=stat.S_IFLNK | 0o777) for member in self.good.members]
    bad = parse_newc(b"".join(records) + self.good.tail)
    with self.assertRaisesRegex(RuntimeError, "unrelated raw archive record changed"):
      subject.archive_delta(self.before, bad, replacements(), self.dwc)

  def test_new_dwc_metadata_and_archive_tail_are_rejected(self) -> None:
    for field, value in ((0, 9999), (1, stat.S_IFREG | 0o600), (2, 1), (3, 1), (4, 2),
                         (5, 1), (7, 1), (8, 1), (9, 1), (10, 1)):
      bad = altered_field(self.good, PREFIX + DWC, field, value)
      with self.subTest(field=field), self.assertRaisesRegex(RuntimeError, "new DWC member payload/metadata differs"):
        subject.archive_delta(self.before, bad, replacements(), self.dwc)
    with self.assertRaisesRegex(RuntimeError, "trailer or zero tail changed"):
      subject.archive_delta(self.before, parse_newc(self.good.raw + b"\0" * 4), replacements(), self.dwc)

  def test_noop_required_index_missing_extra_or_unsafe_replacement_is_rejected(self) -> None:
    before = {member.name: member.payload for member in self.before.members}
    for name in sorted(CHANGED):
      key = PREFIX + name
      updates = replacements() | {key: before[key]}
      bad = transform(self.before, self.dwc, updates)
      with self.subTest(index=name), self.assertRaisesRegex(RuntimeError, "wrong replacement payload"):
        subject.archive_delta(self.before, bad, updates, self.dwc)
    for updates in ({}, replacements() | {PREFIX + "modules.symbols.bin": b"bad"}):
      bad = transform(self.before, self.dwc, updates)
      with self.subTest(updates=sorted(updates)), self.assertRaisesRegex(RuntimeError, "unapproved archive replacement set"):
        subject.archive_delta(self.before, bad, updates, self.dwc)
    for name in ("../escape", PREFIX + "../escape", "etc/hard-a"):
      with self.subTest(path=name), self.assertRaises(ArchiveError):
        replace_members(self.before, {name: b"bad"}, ())
    with self.assertRaisesRegex(ArchiveError, "parent is not an existing directory"):
      replace_members(self.before, {}, (("lib/escape", b"bad"),))

  def test_source_pin_drift_and_output_path_hazards_fail_closed(self) -> None:
    drift = WORK / "drifted-assembler.py"
    write_new(drift, read_regular(SOURCE, SOURCE_SHA256) + b"\n# fixture drift\n")
    with self.assertRaisesRegex(ArchiveError, "source SHA-256 mismatch"):
      read_regular(drift, SOURCE_SHA256)
    target = WORK / "existing"
    write_new(target, b"preserve")
    with self.assertRaises(ArchiveError):
      write_new(target, b"overwrite")
    self.assertEqual(read_regular(target), b"preserve")
    leaf = WORK / "leaf-link"
    leaf.symlink_to(target)
    with self.assertRaises(ArchiveError):
      write_new(leaf, b"overwrite")
    actual = WORK / "actual-parent"
    actual.mkdir(mode=0o700)
    parent = WORK / "parent-link"
    parent.symlink_to(actual, target_is_directory=True)
    with self.assertRaises(ArchiveError):
      write_new(parent / "new", b"no-follow")
    self.assertFalse((actual / "new").exists())
    hard = WORK / "hard-link"
    os.link(target, hard)
    with self.assertRaises(ArchiveError):
      read_regular(hard)


class IndexSemanticTests(unittest.TestCase):
  def test_real_dependency_and_alias_validators_accept_only_the_e_delta(self) -> None:
    original = {ATC, TIPD, DWC_CORE, KEEP_MODULE}
    before = "".join(f"{name}:\n" for name in sorted(original)).encode("ascii")
    after = before + f"{DWC}: {DWC_CORE}\n".encode("ascii")
    subject.prior.validate_dependency_delta(before, after, original)
    aliases = subject.prior.ALIASES_HEADER + b"alias of:N*T*Cfixture,existing phy_apple_atc\n"
    added = ("\n".join(sorted(subject.prior.DWC_ALIASES)) + "\n").encode("ascii")
    subject.prior.validate_alias_delta(aliases, aliases + added)
    self.assertEqual(Counter(subject.prior.alias_entries(aliases + added, subject.prior.ALIASES_HEADER)),
                     Counter(subject.prior.alias_entries(aliases, subject.prior.ALIASES_HEADER)) + subject.prior.DWC_ALIASES)
    for bad in (after.replace(f"{ATC}:\n".encode(), f"{ATC}: {TIPD}\n".encode()),
                before, after + f"{DWC}: {DWC_CORE}\n".encode()):
      with self.subTest(dependency=bad[-100:]), self.assertRaises(RuntimeError):
        subject.prior.validate_dependency_delta(before, bad, original)
    for bad in (aliases, aliases + added + added, aliases + added + b"alias unexpected other\n"):
      with self.subTest(alias=bad[-100:]), self.assertRaises(RuntimeError):
        subject.prior.validate_alias_delta(aliases, bad)


if __name__ == "__main__":
  unittest.main(verbosity=2)
