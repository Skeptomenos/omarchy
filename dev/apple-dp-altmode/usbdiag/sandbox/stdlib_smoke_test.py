"""Check the retained stdlib and fail-closed namespace-denial validation."""

from dataclasses import dataclass
import errno
import hashlib
from pathlib import Path
import struct
import unittest
import zlib

from isolation_probe import CLONE_NEWNS, CLONE_NEWUSER, namespace_denied


@dataclass(frozen=True, slots=True)
class Payload:
  value: bytes


class StandardLibrarySmoke(unittest.TestCase):
  def test_archive_fixture_dependencies(self) -> None:
    payload = Payload(struct.pack("<I", 147))
    self.assertEqual(zlib.decompress(zlib.compress(payload.value)), payload.value)
    self.assertEqual(struct.unpack("<I", payload.value), (147,))
    self.assertRegex(hashlib.sha256(payload.value).hexdigest(), r"^[0-9a-f]{64}$")
    self.assertEqual(Path("/work/output").parent, Path("/work"))


class NamespaceDenialValidation(unittest.TestCase):
  def test_documented_denials_are_accepted(self) -> None:
    for flag, error_number in (
      (CLONE_NEWUSER, errno.EPERM),
      (CLONE_NEWUSER, errno.ENOSPC),
      (CLONE_NEWNS, errno.EPERM),
    ):
      with self.subTest(flag=flag, error_number=error_number):
        self.assertTrue(namespace_denied(flag, -1, error_number))

  def test_success_is_rejected_even_with_stale_errno(self) -> None:
    for flag in (CLONE_NEWUSER, CLONE_NEWNS):
      for error_number in (0, errno.EPERM, errno.ENOSPC):
        with self.subTest(flag=flag, error_number=error_number):
          self.assertFalse(namespace_denied(flag, 0, error_number))

  def test_unknown_or_combined_flags_are_rejected(self) -> None:
    for flag in (0, 1, CLONE_NEWUSER | CLONE_NEWNS, CLONE_NEWUSER | 1):
      for error_number in (errno.EPERM, errno.ENOSPC):
        with self.subTest(flag=flag, error_number=error_number):
          self.assertFalse(namespace_denied(flag, -1, error_number))

  def test_unexpected_errors_are_rejected(self) -> None:
    for flag in (CLONE_NEWUSER, CLONE_NEWNS):
      for error_number in (0, errno.EINVAL, errno.ENOMEM):
        with self.subTest(flag=flag, error_number=error_number):
          self.assertFalse(namespace_denied(flag, -1, error_number))

  def test_mount_namespace_enospc_is_rejected(self) -> None:
    self.assertFalse(namespace_denied(CLONE_NEWNS, -1, errno.ENOSPC))

  def test_other_return_values_are_rejected(self) -> None:
    for flag in (CLONE_NEWUSER, CLONE_NEWNS):
      for return_value in (1, -2):
        for error_number in (errno.EPERM, errno.ENOSPC):
          with self.subTest(flag=flag, return_value=return_value, error_number=error_number):
            self.assertFalse(namespace_denied(flag, return_value, error_number))
