from __future__ import annotations

import ast
import hashlib
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DELIVERY = ROOT / "stage-image-delivery.txt"
BOOTSTRAP = ROOT / "stage-image-bootstrap.txt"
EXPECTED_BOOTSTRAP_PATH = str(BOOTSTRAP)
EXPECTED_BOOTSTRAP_SHA256 = "668f123098252bfd849d66630ec8ec08a808cc9a70d6a9a3520c07cbd55177c5"
EXPECTED_BOOTSTRAP_SIZE = 52_855
EXPECTED_PREFIX = (
  "/usr/bin/env -i PATH=/usr/bin:/bin LANG=C.UTF-8 "
  "/usr/bin/python3.14 -I -S -B -c '\n"
)
EXPECTED_SUFFIX = "'\n"


def digest(data: bytes) -> str:
  return hashlib.sha256(data).hexdigest()


def delivery_source(text: str) -> str:
  if not text.startswith(EXPECTED_PREFIX) or not text.endswith(EXPECTED_SUFFIX):
    raise AssertionError("delivery shell boundary changed")
  return text[len(EXPECTED_PREFIX) : -len(EXPECTED_SUFFIX)]


def fake_sudo(path: Path) -> Path:
  script = path / "sudo"
  script.write_text(
    "#!/bin/bash\n"
    "printf '%s\\n' reached > /tmp/sudo-called\n"
    "printf '%s\\n' 'REFUSED: downstream fixture' >&2\n"
    "exit 73\n",
    encoding="utf-8",
  )
  script.chmod(0o755)
  return script


def run_delivery(
  text: str,
  base: Path,
  bootstrap_overlay: Path | None = None,
) -> subprocess.CompletedProcess[bytes]:
  boot = base / "boot"
  marker = base / "marker"
  boot.mkdir()
  marker.mkdir()
  command = [
    "/usr/bin/bwrap",
    "--die-with-parent",
    "--unshare-user",
    "--uid",
    "1001",
    "--gid",
    "1001",
    "--ro-bind",
    "/",
    "/",
    "--dev-bind",
    "/dev",
    "/dev",
    "--proc",
    "/proc",
    "--bind",
    str(boot),
    "/boot",
    "--bind",
    str(marker),
    "/tmp",
    "--ro-bind",
    str(fake_sudo(base)),
    "/usr/bin/sudo",
  ]
  if bootstrap_overlay is not None:
    destination = str(BOOTSTRAP.parent) if bootstrap_overlay.is_dir() else EXPECTED_BOOTSTRAP_PATH
    command.extend(("--ro-bind", str(bootstrap_overlay), destination))
  command.extend(("--chdir", "/", "/usr/bin/bash", "-s"))
  return subprocess.run(
    command,
    input=text.encode(),
    check=False,
    capture_output=True,
    timeout=30,
  )


class DeliveryContractTests(unittest.TestCase):
  def test_01_exact_static_contract_and_syntax(self) -> None:
    text = DELIVERY.read_text(encoding="utf-8")
    source = delivery_source(text)
    tree = ast.parse(source)
    self.assertEqual(digest(BOOTSTRAP.read_bytes()), EXPECTED_BOOTSTRAP_SHA256)
    self.assertEqual(BOOTSTRAP.stat().st_size, EXPECTED_BOOTSTRAP_SIZE)
    self.assertIn(f'bootstrap_path = "{EXPECTED_BOOTSTRAP_PATH}"', source)
    self.assertIn(f'expected_size = {EXPECTED_BOOTSTRAP_SIZE}', source)
    self.assertIn(f'expected_sha256 = "{EXPECTED_BOOTSTRAP_SHA256}"', source)
    self.assertIn("os.O_NOFOLLOW", source)
    self.assertIn("os.O_CLOEXEC", source)
    self.assertEqual(source.count("os.open("), 1)
    self.assertEqual(source.count("os.read("), 1)
    self.assertEqual(source.count("os.lstat("), 1)
    self.assertIn("os.lstat(bootstrap_path)", source)
    self.assertIn("expected_size + 1 - len(payload)", source)
    self.assertIn("before.st_uid != 1001 or before.st_gid != 1001", source)
    self.assertIn("stat.S_IMODE(before.st_mode) != 0o644", source)
    self.assertIn("before.st_nlink != 1", source)
    self.assertIn("immutable_bootstrap = bytes(payload)", source)
    self.assertIn('subprocess.run(["/usr/bin/bash", "-s"]', source)
    self.assertNotIn("shell=True", source)
    self.assertNotIn("read_bytes", source)
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
    run_calls = [
      node
      for node in calls
      if isinstance(node.func, ast.Attribute)
      and isinstance(node.func.value, ast.Name)
      and node.func.value.id == "subprocess"
      and node.func.attr == "run"
    ]
    self.assertEqual(len(run_calls), 1)
    self.assertEqual(
      ast.literal_eval(run_calls[0].args[0]),
      ["/usr/bin/bash", "-s"],
    )
    self.assertEqual(
      {keyword.arg for keyword in run_calls[0].keywords},
      {"check", "input"},
    )
    syntax = subprocess.run(
      ["/usr/bin/bash", "-n", str(DELIVERY)],
      check=False,
      capture_output=True,
      text=True,
      timeout=10,
    )
    self.assertEqual(syntax.returncode, 0, syntax.stderr)

  @unittest.skipUnless(Path("/usr/bin/bwrap").is_file(), "bwrap is unavailable")
  def test_02_clean_delivery_reaches_bootstrap_and_preserves_exit(self) -> None:
    text = DELIVERY.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix=".delivery-clean-", dir=ROOT) as temporary:
      base = Path(temporary)
      result = run_delivery(text, base)
      self.assertEqual(result.returncode, 73)
      self.assertEqual((base / "marker/sudo-called").read_text(), "reached\n")
      self.assertIn(b"REFUSED: downstream fixture", result.stderr)
      self.assertFalse(tuple((base / "boot").glob(".dev147-afk-pr582-stage.*")))

  @unittest.skipUnless(Path("/usr/bin/bwrap").is_file(), "bwrap is unavailable")
  def test_03_tampered_bootstrap_refuses_before_sudo(self) -> None:
    text = DELIVERY.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix=".delivery-tamper-", dir=ROOT) as temporary:
      base = Path(temporary)
      tampered = base / "tampered-bootstrap.txt"
      payload = bytearray(BOOTSTRAP.read_bytes())
      payload[len(payload) // 2] ^= 1
      tampered.write_bytes(payload)
      tampered.chmod(0o644)
      result = run_delivery(text, base, tampered)
      self.assertEqual(result.returncode, 1)
      self.assertIn(b"REFUSED: bootstrap SHA-256 mismatch", result.stderr)
      self.assertFalse((base / "marker/sudo-called").exists())
      self.assertFalse(tuple((base / "boot").glob(".dev147-afk-pr582-stage.*")))

  @unittest.skipUnless(Path("/usr/bin/bwrap").is_file(), "bwrap is unavailable")
  def test_04_symlink_rebound_refuses_before_sudo(self) -> None:
    text = DELIVERY.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix=".delivery-rebound-", dir=ROOT) as temporary:
      base = Path(temporary)
      rebound = base / "rebound"
      rebound.mkdir()
      (rebound / BOOTSTRAP.name).symlink_to(BOOTSTRAP)
      result = run_delivery(text, base, rebound)
      self.assertEqual(result.returncode, 1)
      self.assertIn(b"REFUSED: cannot open bootstrap safely", result.stderr)
      self.assertFalse((base / "marker/sudo-called").exists())
      self.assertFalse(tuple((base / "boot").glob(".dev147-afk-pr582-stage.*")))


if __name__ == "__main__":
  unittest.main(verbosity=2)
