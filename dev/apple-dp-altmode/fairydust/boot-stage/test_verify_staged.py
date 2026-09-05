from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
  "verify_staged", Path(__file__).with_name("verify-staged.py")
)
assert SPEC is not None and SPEC.loader is not None
VERIFY = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = VERIFY
SPEC.loader.exec_module(VERIFY)


class VerifyStagedTests(unittest.TestCase):
  def setUp(self) -> None:
    self.temporary = tempfile.TemporaryDirectory(prefix="dev147-verify-stage-")
    self.root = Path(self.temporary.name)
    configuration = "menuentry 'old' {}\n"
    self.report = {
      "status": "STAGED_UNSELECTED",
      "release": VERIFY.RELEASE,
      "manifest_sha256": VERIFY.MANIFEST_HASH,
      "boot_directory": str(VERIFY.BOOT),
      "module_directory": str(VERIFY.MODULES),
      "protected_state": str(VERIFY.PROTECTED_STATE),
      "protected_identities": {
        "/boot/grub/grub.cfg": "600:0:0:file:"
        + hashlib.sha256(configuration.encode()).hexdigest()
      },
      "boot_configuration": {"/boot/grub/grub.cfg": configuration},
      "activation": VERIFY.ACTIVATION,
    }
    self.save_report()
    (self.root / "exit-status").write_text("0\n")
    (self.root / "stderr.log").write_text("")
    (self.root / "input-identities").write_text(
      f"helper_sha256={VERIFY.HELPER_HASH}\nmanifest_sha256={VERIFY.MANIFEST_HASH}\n"
    )
    for path in self.root.iterdir():
      path.chmod(0o600)

  def tearDown(self) -> None:
    self.temporary.cleanup()

  def save_report(self) -> None:
    (self.root / "result.json").write_text(json.dumps(self.report))
    (self.root / "result.json").chmod(0o600)

  def test_valid_export(self) -> None:
    report = VERIFY.verify_manual(self.root)
    self.assertEqual(report.status, "STAGED_UNSELECTED")

  def test_failed_manual_exit(self) -> None:
    (self.root / "exit-status").write_text("1\n")
    with self.assertRaises(VERIFY.VerificationFailure):
      VERIFY.verify_manual(self.root)

  def test_manual_stderr_rejected(self) -> None:
    (self.root / "stderr.log").write_text("partial stage failure\n")
    with self.assertRaises(VERIFY.VerificationFailure):
      VERIFY.verify_manual(self.root)

  def test_wrong_helper_identity(self) -> None:
    (self.root / "input-identities").write_text(
      f"helper_sha256={'0' * 64}\nmanifest_sha256={VERIFY.MANIFEST_HASH}\n"
    )
    with self.assertRaises(VERIFY.VerificationFailure):
      VERIFY.verify_manual(self.root)

  def test_saved_configuration_tamper(self) -> None:
    self.report["boot_configuration"] = {"/boot/grub/grub.cfg": "tampered config\n"}
    self.save_report()
    with self.assertRaises(VERIFY.VerificationFailure):
      VERIFY.verify_manual(self.root)

  def test_unexpected_status(self) -> None:
    self.report["status"] = "ACTIVATED"
    self.save_report()
    with self.assertRaises(VERIFY.VerificationFailure):
      VERIFY.verify_manual(self.root)

  def test_published_tree_byte_tamper(self) -> None:
    tree = self.root / "tree"
    tree.mkdir(mode=0o755)
    image = tree / "Image"
    image.write_bytes(b"original")
    expected = {"Image": hashlib.sha256(image.read_bytes()).hexdigest()}
    VERIFY.verify_tree(tree, expected, os.getuid())
    image.write_bytes(b"modified")
    with self.assertRaises(VERIFY.VerificationFailure):
      VERIFY.verify_tree(tree, expected, os.getuid())

  def test_published_symlink_rejected(self) -> None:
    tree = self.root / "tree"
    tree.mkdir(mode=0o755)
    (tree / "Image").symlink_to(self.root / "result.json")
    with self.assertRaises(VERIFY.VerificationFailure):
      VERIFY.verify_tree(tree, {"Image": "0" * 64}, os.getuid())

  def test_wrong_published_owner_rejected(self) -> None:
    tree = self.root / "tree"
    tree.mkdir(mode=0o755)
    (tree / "Image").write_bytes(b"original")
    with self.assertRaises(VERIFY.VerificationFailure):
      VERIFY.verify_tree(tree, {"Image": "0" * 64}, os.getuid() + 1)

  def test_manifest_traversal_rejected(self) -> None:
    with self.assertRaises(VERIFY.VerificationFailure):
      VERIFY.parse_manifest(f"{'0' * 64}  ../outside\n".encode())


if __name__ == "__main__":
  unittest.main()
