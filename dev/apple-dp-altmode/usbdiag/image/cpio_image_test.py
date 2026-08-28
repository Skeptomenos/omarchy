"""Focused pure-format and real-filesystem guards; no hardware model."""
from dataclasses import replace
import hashlib
from pathlib import Path
from tempfile import mkdtemp
import os
import resource
import signal
import stat
import unittest

from cpio_image import (
  MAX_ARCHIVE_BYTES, MAX_MEMBERS, MAX_NAME_BYTES, ArchiveError,
  parse_newc, read_regular, replace_members, write_new,
)


def member(name: str, payload: bytes = b"", *, mode: int = stat.S_IFREG | 0o644,
           ino: int = 1, nlink: int = 1) -> bytes:
    encoded = name.encode("ascii") + b"\0"
    fields = (ino, mode, 0, 0, nlink, 0, len(payload), 0, 0, 0, 0, len(encoded), 0)
    raw = b"070701" + b"".join(f"{value:08x}".encode() for value in fields) + encoded
    raw += b"\0" * (-len(raw) % 4)
    return raw + payload + b"\0" * (-len(payload) % 4)


def archive(*records: bytes) -> bytes:
    raw = b"".join(records) + member("TRAILER!!!", mode=0, ino=0)
    return raw + b"\0" * (-len(raw) % 512)


class ArchiveTests(unittest.TestCase):
    def test_unmodified_roundtrip_is_byte_identical(self) -> None:
        raw = archive(member("usr", mode=stat.S_IFDIR | 0o755),
                      member("usr/a", b"payload", ino=2))
        parsed = parse_newc(raw)
        self.assertEqual(replace_members(parsed, {}, ()), raw)
        self.assertEqual([record.name for record in parsed.members], ["usr", "usr/a"])
        self.assertEqual(parsed.members[1].payload, b"payload")

    def test_replacement_preserves_all_other_raw_records(self) -> None:
        raw = archive(member("usr", mode=stat.S_IFDIR | 0o755),
                      member("usr/a", b"old", ino=2), member("usr/b", b"keep", ino=3))
        before = parse_newc(raw)
        after = parse_newc(replace_members(before, {"usr/a": b"new longer"}, ()))
        self.assertEqual(after.members[0].raw, before.members[0].raw)
        self.assertEqual(after.members[2].raw, before.members[2].raw)
        self.assertEqual(after.members[1].payload, b"new longer")
        for index in range(13):
            if index != 6:
                self.assertEqual(after.members[1].fields[index], before.members[1].fields[index])

    def test_addition_is_unique_with_existing_directory_parent(self) -> None:
        parsed = parse_newc(archive(member("usr", mode=stat.S_IFDIR | 0o755),
                                    member("usr/a", b"a", ino=2)))
        changed = parse_newc(replace_members(parsed, {}, (("usr/b", b"b"),)))
        self.assertEqual([entry.name for entry in changed.members], ["usr", "usr/a", "usr/b"])
        self.assertEqual(changed.members[-1].fields[0], 3)
        self.assertEqual(changed.members[-1].fields[1], stat.S_IFREG | 0o644)
        self.assertEqual(changed.members[-1].fields[2:5], (0, 0, 1))

    def test_unsafe_names_are_rejected(self) -> None:
        for name in ("/root", "../root", "usr/../root", "", "usr//a", "././a", "usr/a\nb"):
            with self.subTest(name=name), self.assertRaises(ArchiveError):
                parse_newc(archive(member(name)))

    def test_initial_dot_prefix_is_canonical_and_preserved(self) -> None:
        parsed = parse_newc(archive(member("./a", b"x")))
        self.assertEqual(parsed.members[0].name, "a")
        self.assertEqual(parsed.members[0].raw_name, b"./a\0")

    def test_duplicate_members_fail_closed(self) -> None:
        with self.assertRaises(ArchiveError):
            parse_newc(archive(member("a"), member("./a", ino=2)))

    def test_bad_magic_and_truncation_fail_closed(self) -> None:
        good = archive(member("a", b"payload"))
        for bad in (b"", b"070701", b"070702" + good[6:], good[:111],
                    good[:115], good[:-512], good + b"unexpected"):
            with self.subTest(length=len(bad)), self.assertRaises(ArchiveError):
                parse_newc(bad)

    def test_unterminated_name_and_nonzero_padding_rejected(self) -> None:
        raw = bytearray(archive(member("a", b"payload")))
        raw[111] = ord("x")
        with self.assertRaises(ArchiveError):
            parse_newc(bytes(raw))
        raw = bytearray(archive(member("aa", b"x")))
        raw[113] = 1
        with self.assertRaises(ArchiveError):
            parse_newc(bytes(raw))

    def test_special_files_and_nonempty_directories_rejected(self) -> None:
        for mode, data in ((stat.S_IFCHR | 0o600, b""), (stat.S_IFIFO | 0o600, b""),
                           (stat.S_IFDIR | 0o755, b"not empty")):
            with self.subTest(mode=mode), self.assertRaises(ArchiveError):
                parse_newc(archive(member("a", data, mode=mode)))

    def test_symlink_payload_is_preserved_but_not_replaceable(self) -> None:
        parsed = parse_newc(archive(member("lib", b"usr/lib", mode=stat.S_IFLNK | 0o777)))
        self.assertEqual(replace_members(parsed, {}, ()), parsed.raw)
        with self.assertRaises(ArchiveError):
            replace_members(parsed, {"lib": b"/other"}, ())
        with self.assertRaises(ArchiveError):
            replace_members(parsed, {}, (("lib/escape", b"x"),))

    def test_hardlink_groups_are_preserved_not_rewritten(self) -> None:
        parsed = parse_newc(archive(member("a", b"", ino=7, nlink=2),
                                    member("b", b"data", ino=7, nlink=2)))
        self.assertEqual(replace_members(parsed, {}, ()), parsed.raw)
        with self.assertRaises(ArchiveError):
            replace_members(parsed, {"b": b"new"}, ())

    def test_unknown_replacement_and_duplicate_addition_fail(self) -> None:
        parsed = parse_newc(archive(member("a", b"a")))
        with self.assertRaises(ArchiveError):
            replace_members(parsed, {"missing": b"x"}, ())
        with self.assertRaises(ArchiveError):
            replace_members(parsed, {}, (("a", b"x"),))
        with self.assertRaises(ArchiveError):
            replace_members(parsed, {}, (("b", b"x"), ("b", b"y")))


class FilesystemTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(mkdtemp(prefix="image-test-", dir="/work"))

    def test_existing_output_is_preserved(self) -> None:
        target = self.root / "existing"
        target.write_bytes(b"keep")
        with self.assertRaises(ArchiveError):
            write_new(target, b"replace")
        self.assertEqual(target.read_bytes(), b"keep")

    def test_output_symlink_and_symlinked_parent_rejected(self) -> None:
        source = self.root / "source"
        source.write_bytes(b"keep")
        link = self.root / "link"
        link.symlink_to(source)
        with self.assertRaises(ArchiveError):
            write_new(link, b"replace")
        directory = self.root / "directory"
        directory.mkdir()
        alias = self.root / "alias"
        alias.symlink_to(directory, target_is_directory=True)
        with self.assertRaises(ArchiveError):
            write_new(alias / "new", b"no")
        self.assertFalse((directory / "new").exists())

    def test_input_symlink_hardlink_and_hash_drift_rejected(self) -> None:
        source = self.root / "input"
        source.write_bytes(b"input")
        link = self.root / "symlink"
        link.symlink_to(source)
        with self.assertRaises(ArchiveError):
            read_regular(link)
        hard = self.root / "hard"
        os.link(source, hard)
        with self.assertRaises(ArchiveError):
            read_regular(source)
        other = self.root / "other"
        other.write_bytes(b"input")
        with self.assertRaises(ArchiveError):
            read_regular(other, "0" * 64)

    def test_new_output_is_private_and_complete(self) -> None:
        target = self.root / "new"
        write_new(target, b"complete")
        self.assertEqual(read_regular(target), b"complete")
        self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o600)
        self.assertEqual(target.stat().st_nlink, 1)


def raw_field(raw: bytes, index: int, value: bytes) -> bytes:
  if len(value) != 8:
    raise ValueError("fixture field must be eight bytes")
  offset = 6 + index * 8
  return raw[:offset] + value + raw[offset + 8:]


class ArchiveSafetyTests(unittest.TestCase):
  def test_empty_archive_and_explicit_root_are_preserved(self) -> None:
    for raw in (archive(), archive(member(".", mode=stat.S_IFDIR | 0o755)),
                archive(member("./", mode=stat.S_IFDIR | 0o755))):
      with self.subTest(raw=raw[:32]):
        parsed = parse_newc(raw)
        self.assertEqual(replace_members(parsed, {}, ()), raw)
    root = parse_newc(archive(member("./", mode=stat.S_IFDIR | 0o755)))
    self.assertEqual(root.members[0].name, ".")
    self.assertEqual(parse_newc(replace_members(root, {}, (("a", b"x"),))).members[-1].name, "a")

  def test_root_alias_duplicates_and_non_directory_roots_fail(self) -> None:
    for raw in (archive(member(".")), archive(member("./")),
                archive(member(".", mode=stat.S_IFDIR), member("./", mode=stat.S_IFDIR))):
      with self.subTest(raw=raw[:32]), self.assertRaises(ArchiveError):
        parse_newc(raw)

  def test_absolute_symlink_target_is_opaque_and_unchanged(self) -> None:
    parsed = parse_newc(archive(member("vendor", b"/vendorfw/current", mode=stat.S_IFLNK | 0o777),
                                member("a", b"old", ino=2)))
    changed = parse_newc(replace_members(parsed, {"a": b"new"}, ()))
    self.assertEqual(changed.members[0].raw, parsed.members[0].raw)
    self.assertEqual(changed.members[0].payload, b"/vendorfw/current")

  def test_embedded_nul_non_ascii_and_control_names_fail(self) -> None:
    non_ascii = bytearray(archive(member("a")))
    non_ascii[110] = 255
    for raw in (archive(member("a\0b")), archive(member("a\tb")),
                archive(member("a\x7fb")), bytes(non_ascii)):
      with self.subTest(raw=raw[:32]), self.assertRaises(ArchiveError):
        parse_newc(raw)

  def test_invalid_numeric_fields_and_checksum_fail(self) -> None:
    good = archive(member("a"))
    for field in (b"+0000001", b"-0000001", b" 0000001", b"0000000g"):
      with self.subTest(field=field), self.assertRaises(ArchiveError):
        parse_newc(raw_field(good, 0, field))
    with self.assertRaises(ArchiveError):
      parse_newc(raw_field(good, 12, b"00000001"))

  def test_nonzero_payload_padding_fails(self) -> None:
    first = member("a", b"x")
    raw = bytearray(archive(first))
    raw[len(first) - 1] = 1
    with self.assertRaises(ArchiveError):
      parse_newc(bytes(raw))

  def test_trailer_is_required_and_is_the_only_archive_boundary(self) -> None:
    for raw in (member("a"), member("TRAILER!!!", b"x", mode=0),
                member("TRAILER!!!"), member("./TRAILER!!!", mode=0),
                archive(member("a")) + archive(member("b"))):
      with self.subTest(raw=raw[:32]), self.assertRaises(ArchiveError):
        parse_newc(raw)

  def test_invalid_modes_links_and_symlink_payloads_fail(self) -> None:
    bad = [archive(member("a", mode=mode)) for mode in
           (stat.S_IFBLK | 0o600, stat.S_IFSOCK | 0o600, 0o644, stat.S_IFREG | (1 << 16))]
    bad.append(archive(member("a", nlink=0)))
    bad.extend(archive(member("a", target, mode=stat.S_IFLNK | 0o777))
               for target in (b"", b"a\0b", b"x" * MAX_NAME_BYTES))
    for raw in bad:
      with self.subTest(raw=raw[:32]), self.assertRaises(ArchiveError):
        parse_newc(raw)

  def test_declared_size_and_name_bounds_fail_before_truncation(self) -> None:
    good = archive(member("a"))
    for index, value in ((6, MAX_ARCHIVE_BYTES + 1), (11, MAX_NAME_BYTES + 1)):
      with self.subTest(index=index), self.assertRaisesRegex(ArchiveError, "bound"):
        parse_newc(raw_field(good, index, f"{value:08x}".encode("ascii")))

  def test_component_and_depth_bounds_fail(self) -> None:
    for name in ("x" * 256, "/".join(["x"] * 129), "/".join(["x" * 255] * 17)):
      with self.subTest(length=len(name)), self.assertRaises(ArchiveError):
        parse_newc(archive(member(name)))

  def test_member_count_bound_and_addition_overflow(self) -> None:
    records = tuple(member(f"a{index}", ino=index + 1) for index in range(MAX_MEMBERS))
    parsed = parse_newc(archive(*records))
    self.assertEqual(len(parsed.members), MAX_MEMBERS)
    with self.assertRaisesRegex(ArchiveError, "bound"):
      parse_newc(archive(*records, member("extra", ino=MAX_MEMBERS + 1)))
    with self.assertRaisesRegex(ArchiveError, "bound"):
      replace_members(parsed, {}, (("extra", b"x"),))

  def test_all_header_bytes_except_size_are_preserved(self) -> None:
    record = member("./a", b"old", mode=stat.S_IFREG | 0o4755, ino=0xabc)
    for index, value in ((2, 0x123), (3, 0x456), (5, 0xabcdef), (7, 0x12), (8, 0x34)):
      record = raw_field(record, index, f"{value:08X}".encode("ascii"))
    record = record[:110].upper() + record[110:]
    before = parse_newc(archive(record))
    after = parse_newc(replace_members(before, {"a": b"changed payload"}, ()))
    self.assertEqual(after.members[0].raw[:54], before.members[0].raw[:54])
    self.assertEqual(after.members[0].raw[62:116], before.members[0].raw[62:116])
    self.assertEqual(after.members[0].raw_name, b"./a\0")
    self.assertEqual(after.members[0].fields[:6], before.members[0].fields[:6])
    self.assertEqual(after.members[0].fields[7:], before.members[0].fields[7:])

  def test_equal_replacement_is_exact_with_original_dot_name(self) -> None:
    record = member("./a", b"x" * 15)
    record = record[:110].upper() + record[110:]
    raw = archive(record) + b"\0" * 7
    self.assertEqual(replace_members(parse_newc(raw), {"a": b"x" * 15}, ()), raw)

  def test_missing_or_non_directory_parents_block_all_mutation(self) -> None:
    for records in ((member("a/b", b"x"),),
                    (member("a", b"file"), member("a/b", b"x", ino=2))):
      parsed = parse_newc(archive(*records))
      self.assertEqual(replace_members(parsed, {}, ()), parsed.raw)
      with self.assertRaises(ArchiveError):
        replace_members(parsed, {"a/b": b"new"}, ())
      with self.assertRaises(ArchiveError):
        replace_members(parsed, {}, (("a/c", b"new"),))

  def test_ancestor_symlink_is_never_resolved(self) -> None:
    parsed = parse_newc(archive(member("real", mode=stat.S_IFDIR | 0o755),
                                member("alias", b"real", mode=stat.S_IFLNK | 0o777, ino=2),
                                member("alias/child", b"old", ino=3)))
    with self.assertRaises(ArchiveError):
      replace_members(parsed, {"alias/child": b"new"}, ())
    with self.assertRaises(ArchiveError):
      replace_members(parsed, {}, (("alias/new", b"new"),))

  def test_regular_mutation_must_not_shadow_existing_descendants(self) -> None:
    parsed = parse_newc(archive(member("a/b", b"kept")))
    with self.assertRaises(ArchiveError):
      replace_members(parsed, {}, (("a", b"new parent"),))
    parsed = parse_newc(archive(member("a", b"old"), member("a/b", b"kept", ino=2)))
    with self.assertRaises(ArchiveError):
      replace_members(parsed, {"a": b"new parent"}, ())

  def test_mutation_names_must_be_canonical(self) -> None:
    parsed = parse_newc(archive(member("a", b"x")))
    for name in ("./a", "../a", "/a", "a/../b", "TRAILER!!!", "."):
      with self.subTest(name=name):
        with self.assertRaises(ArchiveError):
          replace_members(parsed, {name: b"new"}, ())
        with self.assertRaises(ArchiveError):
          replace_members(parsed, {}, ((name, b"new"),))

  def test_hardlinks_stay_raw_when_other_members_change(self) -> None:
    parsed = parse_newc(archive(member("a", ino=7, nlink=2),
                                member("b", b"linked", ino=7, nlink=2),
                                member("c", b"old", ino=9)))
    changed = parse_newc(replace_members(parsed, {"c": b"new"}, (("d", b"added"),)))
    self.assertEqual(tuple(entry.raw for entry in changed.members[:2]),
                     tuple(entry.raw for entry in parsed.members[:2]))
    self.assertEqual(changed.members[-1].fields[0], 10)

  def test_addition_inode_cannot_wrap(self) -> None:
    parsed = parse_newc(archive(member("a", b"old", ino=0xffffffff)))
    with self.assertRaisesRegex(ArchiveError, "inode"):
      replace_members(parsed, {}, (("b", b"new"),))
    self.assertEqual(parse_newc(replace_members(parsed, {"a": b"new"}, ())).members[0].fields[0],
                     0xffffffff)

  def test_forged_archive_models_fail(self) -> None:
    parsed = parse_newc(archive(member("a", b"x")))
    for forged in (replace(parsed, tail=b""), replace(parsed, members=()),
                   replace(parsed, members=(replace(parsed.members[0], payload=b"forged"),))):
      with self.subTest(forged=type(forged).__name__), self.assertRaises(ArchiveError):
        replace_members(forged, {}, ())

  def test_mutation_contract_rejects_wrong_types(self) -> None:
    parsed = parse_newc(archive(member("a")))
    with self.assertRaises(ArchiveError):
      parse_newc(bytearray(parsed.raw))  # type: ignore[arg-type]
    with self.assertRaises(ArchiveError):
      replace_members(parsed, {"a": bytearray(b"x")}, ())  # type: ignore[dict-item]
    with self.assertRaises(ArchiveError):
      replace_members(parsed, {}, [("b", b"x")])  # type: ignore[arg-type]
    with self.assertRaises(ArchiveError):
      replace_members(parsed, {}, (("b",),))  # type: ignore[arg-type]

  def test_tail_is_retained_for_size_changing_and_added_members(self) -> None:
    before = parse_newc(archive(member("a", b"old")) + b"\0" * 7)
    after = parse_newc(replace_members(before, {"a": b"longer replacement"}, (("b", b"new"),)))
    self.assertEqual(after.tail, before.tail)
    self.assertEqual(after.members[-1].fields[1:6], (stat.S_IFREG | 0o644, 0, 0, 1, 0))


class FilesystemSafetyTests(unittest.TestCase):
  def setUp(self) -> None:
    self.root = Path(mkdtemp(prefix="image-safety-test-", dir="/work"))

  def test_empty_and_nested_files_roundtrip_with_hash(self) -> None:
    directory = self.root / "one" / "two"
    directory.mkdir(parents=True)
    for name, payload in (("empty", b""), ("data", b"verified content")):
      target = directory / name
      write_new(target, payload)
      self.assertEqual(read_regular(target, hashlib.sha256(payload).hexdigest()), payload)

  def test_invalid_digest_is_rejected(self) -> None:
    source = self.root / "input"
    source.write_bytes(b"x")
    for digest in ("", "0" * 63, "G" * 64, "A" * 64, "0" * 65):
      with self.subTest(digest=digest[:8]), self.assertRaises(ArchiveError):
        read_regular(source, digest)

  def test_input_parent_symlink_and_missing_parent_fail(self) -> None:
    directory = self.root / "directory"
    directory.mkdir()
    (directory / "input").write_bytes(b"x")
    (self.root / "alias").symlink_to(directory, target_is_directory=True)
    with self.assertRaises(ArchiveError):
      read_regular(self.root / "alias" / "input")
    with self.assertRaises(ArchiveError):
      write_new(self.root / "missing" / "output", b"x")
    self.assertFalse((self.root / "missing").exists())

  def test_input_directory_fifo_and_oversized_sparse_file_fail(self) -> None:
    fifo = self.root / "fifo"
    os.mkfifo(fifo, 0o600)
    oversized = self.root / "oversized"
    # A sparse fixture checks the stat bound without allocating a large payload.
    with oversized.open("xb") as output:
      output.truncate(MAX_ARCHIVE_BYTES + 1)
    for source in (self.root, fifo, oversized):
      with self.subTest(name=source.name), self.assertRaises(ArchiveError):
        read_regular(source)

  def test_unsafe_filesystem_paths_fail_before_access(self) -> None:
    for path in (Path("relative"), Path("/"), Path("//work/invalid"), self.root / ".." / "escape",
                 self.root / "line\nbreak", self.root / "nul\0name", self.root / "\ud800"):
      with self.subTest(name=path.name):
        with self.assertRaises(ArchiveError):
          read_regular(path)
        with self.assertRaises(ArchiveError):
          write_new(path, b"x")

  def test_invalid_output_payload_does_not_create_a_file(self) -> None:
    target = self.root / "output"
    with self.assertRaises(ArchiveError):
      write_new(target, bytearray(b"x"))  # type: ignore[arg-type]
    self.assertFalse(target.exists())

  def test_existing_output_hardlink_and_directory_are_preserved(self) -> None:
    source = self.root / "source"
    source.write_bytes(b"keep")
    linked = self.root / "linked"
    os.link(source, linked)
    directory = self.root / "directory"
    directory.mkdir()
    for target in (linked, directory):
      before = target.stat()
      with self.assertRaises(ArchiveError):
        write_new(target, b"replace")
      self.assertEqual((target.stat().st_dev, target.stat().st_ino), (before.st_dev, before.st_ino))
    self.assertEqual(source.read_bytes(), b"keep")
    self.assertEqual(source.stat().st_nlink, 2)

  def test_restrictive_umask_still_produces_exact_private_mode(self) -> None:
    target = self.root / "output"
    previous = os.umask(0o777)
    try:
      write_new(target, b"x")
    finally:
      os.umask(previous)
    self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o600)
    self.assertEqual(read_regular(target), b"x")

  def test_real_write_limit_failure_retains_partial_output(self) -> None:
    target = self.root / "partial"
    previous_limit = resource.getrlimit(resource.RLIMIT_FSIZE)
    previous_signal = signal.signal(signal.SIGXFSZ, signal.SIG_IGN)
    try:
      resource.setrlimit(resource.RLIMIT_FSIZE, (3, previous_limit[1]))
      with self.assertRaises(ArchiveError):
        write_new(target, b"01234567")
    finally:
      resource.setrlimit(resource.RLIMIT_FSIZE, previous_limit)
      signal.signal(signal.SIGXFSZ, previous_signal)
    self.assertEqual(target.read_bytes(), b"012")
    self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o600)
    with self.assertRaises(ArchiveError):
      write_new(target, b"retry")
    self.assertEqual(target.read_bytes(), b"012")

  def test_unwritable_parent_does_not_create_output(self) -> None:
    directory = self.root / "readonly"
    directory.mkdir(mode=0o500)
    try:
      with self.assertRaises(ArchiveError):
        write_new(directory / "output", b"x")
      self.assertFalse((directory / "output").exists())
    finally:
      directory.chmod(0o700)


if __name__ == "__main__":
    unittest.main()
