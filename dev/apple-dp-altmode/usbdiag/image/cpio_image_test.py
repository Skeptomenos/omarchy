"""Focused pure-format and real-filesystem guards; no hardware model."""
from pathlib import Path
from tempfile import mkdtemp
import os
import stat
import unittest

from cpio_image import ArchiveError, parse_newc, read_regular, replace_members, write_new


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


if __name__ == "__main__":
    unittest.main()
