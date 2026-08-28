"""Independent regressions for the saved mkinitcpio archive's observed format."""

from pathlib import Path
from tempfile import mkdtemp
import os
import stat
import unittest

from cpio_image import ArchiveError, parse_newc, read_regular, replace_members, write_new
from cpio_image_test import archive, member, raw_field


class ObservedArchiveTests(unittest.TestCase):
  def test_zero_link_directory_records_and_replacement_preserve_raw_metadata(self) -> None:
    raw = archive(
      member("bin", b"usr/bin", mode=stat.S_IFLNK | 0o777, ino=1, nlink=0),
      member("usr/", mode=stat.S_IFDIR | 0o755, ino=2, nlink=0),
      member("usr/lib/", mode=stat.S_IFDIR | 0o755, ino=3, nlink=0),
      raw_field(member("usr/lib/a.ko", b"old", ino=4, nlink=0), 1, b"000081A4"),
    )
    before = parse_newc(raw)
    self.assertEqual([item.name for item in before.members], ["bin", "usr", "usr/lib", "usr/lib/a.ko"])
    self.assertEqual(replace_members(before, {}, ()), raw)
    changed = parse_newc(replace_members(before, {"usr/lib/a.ko": b"new module bytes"},
                                        (("usr/lib/b.ko", b"added module"),)))
    self.assertEqual(changed.tail, before.tail)
    for old, new in zip(before.members[:3], changed.members[:3], strict=True):
      self.assertEqual(new.raw, old.raw)
    old, new = before.members[3], changed.members[3]
    self.assertEqual(new.raw_name, old.raw_name)
    self.assertEqual(new.raw[:54], old.raw[:54])
    self.assertEqual(new.raw[62:110], old.raw[62:110])
    self.assertEqual(new.fields[4], 0)
    self.assertEqual(new.payload, b"new module bytes")
    self.assertEqual(changed.members[4].fields[4], 1)
    self.assertEqual(changed.members[4].payload, b"added module")

  def test_directory_slash_support_does_not_accept_alias_or_traversal(self) -> None:
    for name in ("/", "a//", ".//", "././a/", "a/../b/", "a/./b/", "a//b/"):
      with self.subTest(name=name), self.assertRaises(ArchiveError):
        parse_newc(archive(member(name, mode=stat.S_IFDIR | 0o755, nlink=0)))
    for spelling in ("a", "./a", "a/", "./a/"):
      with self.subTest(spelling=spelling), self.assertRaises(ArchiveError):
        parse_newc(archive(member("a/", mode=stat.S_IFDIR | 0o755, ino=1, nlink=0),
                           member(spelling, mode=stat.S_IFDIR | 0o755, ino=2, nlink=0)))
    for mode in (stat.S_IFREG | 0o644, stat.S_IFLNK | 0o777):
      with self.subTest(mode=mode), self.assertRaises(ArchiveError):
        parse_newc(archive(member("a/", b"payload", mode=mode, nlink=0)))

  def test_zero_archive_links_do_not_relax_physical_hardlink_guard(self) -> None:
    parsed = parse_newc(archive(member("module.ko", b"module", nlink=0)))
    self.assertEqual(replace_members(parsed, {}, ()), parsed.raw)
    root = Path(mkdtemp(prefix="archive-review-", dir="/work"))
    source, second_link = root / "source", root / "second-link"
    write_new(source, parsed.members[0].payload)
    os.link(source, second_link)
    with self.assertRaises(ArchiveError):
      read_regular(source)
    self.assertEqual(source.stat().st_nlink, 2)


if __name__ == "__main__":
  unittest.main()
