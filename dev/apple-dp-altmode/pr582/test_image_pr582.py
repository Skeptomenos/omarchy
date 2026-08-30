"""Focused pure-contract tests; run only in the pinned offline sandbox.

The launcher must bind this file at /inputs/tests and the frozen subject directory
at /inputs/recipe. These tests do not invoke the operational entry or children.
Stdlib unittest is the existing no-install exception; no hardware is simulated.
"""

import json
import os
from pathlib import Path
import stat
import sys
import unittest
import zlib


if (os.getuid() != 1001 or os.getgid() != 1001 or Path.cwd() != Path("/work")
    or not sys.flags.isolated or not sys.flags.no_site or not sys.dont_write_bytecode
    or any(Path(path).exists() for path in ("/proc", "/sys", "/home", "/run", "/boot"))):
  raise SystemExit("REFUSED: tests require the reviewed offline sandbox")
sys.path.insert(0, "/inputs/recipe")
import image_pr582 as subject


def record(name: str, payload: bytes = b"", mode: int = stat.S_IFREG | 0o644,
           links: int = 0, inode: int = 1) -> bytes:
  encoded = name.encode("ascii") + b"\0"
  fields = (inode, mode, 0, 0, links, 123, len(payload), 0, 0, 0, 0, len(encoded), 0)
  raw = b"070701" + b"".join(f"{value:08X}".encode() for value in fields) + encoded
  return raw + b"\0" * (-len(raw) % 4) + payload + b"\0" * (-len(payload) % 4)


def fixture() -> bytes:
  files = {subject.TARGET: b"old module", "etc/keep": b"keep",
           **{subject.PREFIX + name: name.encode() for name in subject.INDEXES}}
  parents = {str(parent) for name in files for parent in Path(name).parents
             if parent != Path(".")}
  raw = b"".join(record(name + "/", mode=stat.S_IFDIR | 0o755, inode=index)
                 for index, name in enumerate(sorted(parents, key=lambda x: (x.count("/"), x)), 2))
  raw += b"".join(record(name, data, inode=index)
                  for index, (name, data) in enumerate(files.items(), 100))
  return raw + record("TRAILER!!!", mode=0, links=1, inode=0) + b"\0" * 12


def manifest() -> dict[str, object]:
  return {"schema": "dev147-pr582-images-v1", "source_commit": subject.SOURCE_COMMIT,
          "patch_commit": subject.PATCH_COMMIT, "depends": "drm,drm_kms_helper",
          "closure": ["kernel/drivers/gpu/drm/drm.ko", subject.RELATIVE],
          "control": {"sha256": "1" * 64, "bytes": 100, "build_id": "1" * 40},
          "candidate": {"sha256": "2" * 64, "bytes": 101, "build_id": "2" * 40}}


class ImageContractTests(unittest.TestCase):
  def setUp(self) -> None:
    self.before = fixture()
    self.module = b"different fixture module, not an ELF"
    self.after = subject.replace_members(subject.parse_newc(self.before),
                                         {subject.TARGET: self.module}, ())

  def test_exact_one_payload_is_accepted(self) -> None:
    self.assertEqual(subject.archive_delta(self.before, self.after, self.module), 1)

  def test_unchanged_control_can_be_explicitly_accepted(self) -> None:
    self.assertEqual(subject.archive_delta(self.before, self.before, b"old module", True), 0)
    with self.assertRaises(subject.ImageError):
      subject.archive_delta(self.before, self.before, b"old module")

  def test_wrong_payload_is_rejected(self) -> None:
    with self.assertRaises(subject.ImageError):
      subject.archive_delta(self.before, self.after, b"wrong")

  def test_unrelated_record_is_rejected(self) -> None:
    changed = subject.replace_members(subject.parse_newc(self.after), {"etc/keep": b"changed"}, ())
    with self.assertRaises(subject.ImageError):
      subject.archive_delta(self.before, changed, self.module)

  def test_index_change_is_rejected(self) -> None:
    changed = subject.replace_members(subject.parse_newc(self.after),
                                      {subject.PREFIX + "modules.dep.bin": b"changed"}, ())
    with self.assertRaises(subject.ImageError):
      subject.archive_delta(self.before, changed, self.module)

  def test_changed_tail_is_rejected(self) -> None:
    with self.assertRaises(subject.ImageError):
      subject.archive_delta(self.before, self.after + b"\0", self.module)

  def test_changed_target_metadata_is_rejected(self) -> None:
    archive = subject.parse_newc(self.after)
    rows = []
    for member in archive.members:
      raw = member.raw
      if member.name == subject.TARGET:
        raw = raw[:14] + b"00008180" + raw[22:]  # regular mode 0600, not original 0644
      rows.append(raw)
    with self.assertRaises(subject.ImageError):
      subject.archive_delta(self.before, b"".join(rows) + archive.tail, self.module)

  def test_missing_target_is_rejected(self) -> None:
    archive = subject.parse_newc(self.before)
    missing = b"".join(item.raw for item in archive.members if item.name != subject.TARGET) + archive.tail
    with self.assertRaises(subject.ImageError):
      subject.archive_delta(missing, missing, self.module)

  def test_manifest_is_strict(self) -> None:
    value = manifest()
    self.assertEqual(subject.parse_manifest(json.dumps(value).encode()).candidate.size, 101)
    for key, replacement in (("schema", "wrong"), ("source_commit", "0" * 40),
                             ("patch_commit", "0" * 40), ("depends", "drm\ninsmod bad"),
                             ("closure", ["../escape.ko", subject.RELATIVE])):
      changed = dict(value, **{key: replacement})
      with self.subTest(key=key), self.assertRaises(subject.ImageError):
        subject.parse_manifest(json.dumps(changed).encode())
    with self.assertRaises(subject.ImageError):
      subject.parse_manifest(json.dumps(dict(value, extra=True)).encode())

  def test_duplicate_json_and_boolean_size_are_rejected(self) -> None:
    with self.assertRaises(subject.ImageError):
      subject.parse_manifest(b'{"schema":1,"schema":1}')
    value = manifest()
    value["control"] = {"sha256": "1" * 64, "bytes": True, "build_id": "1" * 40}
    with self.assertRaises(subject.ImageError):
      subject.parse_manifest(json.dumps(value).encode())

  def test_identical_pair_is_rejected(self) -> None:
    value = manifest()
    value["candidate"] = value["control"]
    with self.assertRaises(subject.ImageError):
      subject.parse_manifest(json.dumps(value).encode())

  def test_unbound_manifest_is_rejected(self) -> None:
    with self.assertRaises(subject.ImageError):
      subject.manifest_binding(None)
    with self.assertRaises(subject.ImageError):
      subject.manifest_binding("unbound")
    self.assertEqual(subject.manifest_binding("a" * 64), "a" * 64)

  def test_dependency_output_is_exact_and_never_executed(self) -> None:
    closure = ("kernel/drivers/gpu/drm/drm.ko", subject.RELATIVE)
    root = Path("/work/control-lookup")
    expected = b"".join(f"insmod {root}/lib/modules/{subject.KERNEL}/{path} \n".encode()
                        for path in closure)
    subject.check_closure(expected, root, closure)
    for wrong in (expected.replace(b" \n", b"\n"), expected + b"insmod /host/a.ko \n",
                  b"\n".join(reversed(expected.splitlines())) + b"\n"):
      with self.assertRaises(subject.ImageError):
        subject.check_closure(wrong, root, closure)

  def test_gzip_trailing_and_truncated_streams_are_rejected(self) -> None:
    encoder = zlib.compressobj(wbits=16 + zlib.MAX_WBITS)
    compressed = encoder.compress(self.before) + encoder.flush()
    self.assertEqual(subject.assembly.single_gzip(compressed, len(self.before)), self.before)
    for wrong in (compressed[:-1], compressed + compressed, compressed + b"x"):
      with self.assertRaises((RuntimeError, zlib.error)):
        subject.assembly.single_gzip(wrong, len(self.before))


if __name__ == "__main__":
  unittest.main()
