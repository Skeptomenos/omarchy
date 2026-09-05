from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

RELEASE = "7.1.12-dev147-clearwait100"
HELPER = Path(__file__).with_name("stage.py")
BOOT_CONFIG = HELPER.parents[2] / "boot-activate"


def digest(path: Path) -> str:
  return hashlib.sha256(path.read_bytes()).hexdigest()


class StageTests(unittest.TestCase):
  def setUp(self) -> None:
    self.temporary = tempfile.TemporaryDirectory(prefix="dev147-stage-test-")
    self.root = Path(self.temporary.name)
    for directory in (
      "boot/efi/m1n1",
      "boot/grub",
      "etc/default",
      "etc/grub.d",
      "etc/pacman.d/hooks",
      "var/lib/pacman/local",
      "var/lib/omarchy/m2-displayport",
      "modules/current",
      "run/lock",
      "delivery/receipts",
      f"delivery/root/lib/modules/{RELEASE}/kernel/drivers",
    ):
      (self.root / directory).mkdir(parents=True, exist_ok=True)
    shutil.copyfile("/boot/efi/m1n1/boot.bin", self.root / "boot/efi/m1n1/boot.bin")
    shutil.copyfile(
      "/etc/pacman.d/hooks/05-omarchy-m2-displayport-guard.hook",
      self.root / "etc/pacman.d/hooks/05-omarchy-m2-displayport-guard.hook",
    )
    shutil.copyfile(BOOT_CONFIG / "dispatcher.cfg", self.root / "boot/grub/grub.cfg")
    support = self.root / "boot/grub/dev147-paired-7.1.12-dev147-fairydust1"
    support.mkdir()
    for name in ("candidate.cfg", "old.cfg", "old.sha256", "candidate.sha256"):
      shutil.copyfile(BOOT_CONFIG / name, support / name)
    for name in (
      "boot/efi/m1n1/dev147-recovery/boot.bin.old-203ab702",
      "boot/dev147-fairydust-7.1.12-dev147-fairydust1/Image",
      "boot/dev147-fairydust-7.1.12-dev147-fairydust1/initramfs.img",
      "boot/dev147-fairydust-7.1.12-dev147-fairydust1/t8112-j413.dtb",
    ):
      target = self.root / name
      target.parent.mkdir(parents=True, exist_ok=True)
      shutil.copyfile(Path("/") / name, target)
    (self.root / "boot/grub/grubenv").write_text(
      "# GRUB Environment Block\nsaved_entry=original\n"
    )
    (self.root / "etc/default/grub").write_text("GRUB_DEFAULT=0\n")
    (self.root / "modules/current/preserved").write_text("current modules\n")
    (self.root / "var/lib/omarchy/m2-displayport/state.env").write_text(
      "existing private state\n"
    )
    for name in ("Image", "initramfs.img", "config"):
      (self.root / "delivery" / name).write_text(f"candidate {name}\n")
    for name in ("kernel-source-config.json", "initramfs.json"):
      (self.root / "delivery/receipts" / name).write_text("{}\n")
    module = self.root / f"delivery/root/lib/modules/{RELEASE}/kernel/drivers/apple.ko"
    module.write_text("candidate module\n")
    (self.root / "delivery/modules.sha256").write_text(
      f"{digest(module)}  lib/modules/{RELEASE}/kernel/drivers/apple.ko\n"
    )
    self.manifest = self.freeze()
    self.before = self.protected()

  def tearDown(self) -> None:
    self.temporary.cleanup()

  def freeze(self) -> str:
    source = self.root / "delivery"
    files = sorted(
      path for path in source.rglob("*") if path.is_file() and path.name != "SHA256SUMS"
    )
    manifest = source / "SHA256SUMS"
    manifest.write_text(
      "".join(f"{digest(path)}  {path.relative_to(source)}\n" for path in files)
    )
    return digest(manifest)

  def protected(self) -> dict[str, str]:
    return {
      str(path.relative_to(self.root)): digest(path)
      for parent in ("boot", "etc", "modules/current", "var/lib/omarchy")
      for path in (self.root / parent).rglob("*")
      if path.is_file()
    }

  def command(self) -> list[str]:
    command = [
      "/usr/bin/bwrap",
      "--die-with-parent",
      "--unshare-user",
      "--uid",
      "0",
      "--gid",
      "0",
      "--ro-bind",
      "/",
      "/",
      "--dev-bind",
      "/dev",
      "/dev",
      "--proc",
      "/proc",
    ]
    for source, destination in (
      ("boot", "/boot"),
      ("etc", "/etc"),
      ("var/lib", "/var/lib"),
      ("modules", "/usr/lib/modules"),
      ("run/lock", "/run/lock"),
    ):
      command += ["--bind", str(self.root / source), destination]
    command += [
      "--chdir",
      "/",
      "/usr/bin/env",
      "-i",
      "PATH=/usr/bin:/bin",
      "/usr/bin/python3",
      "-I",
      str(HELPER),
      str(self.root / "delivery"),
      self.manifest,
    ]
    return command

  def run_stage(
    self, expected: int = 0, existing_lock: bool = False
  ) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
      self.command(), text=True, capture_output=True, timeout=90, check=False
    )
    self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
    for path, expected_digest in self.before.items():
      self.assertEqual(digest(self.root / path), expected_digest, path)
    self.assertEqual((self.root / "var/lib/pacman/db.lck").exists(), existing_lock)
    return result

  def test_stage_preserves_active_system(self) -> None:
    result = self.run_stage()
    report = json.loads(result.stdout)
    self.assertEqual(report["status"], "STAGED_UNSELECTED")
    self.assertEqual(
      (self.root / f"boot/dev147-trial-{RELEASE}/Image").read_bytes(),
      (self.root / "delivery/Image").read_bytes(),
    )
    self.assertEqual(
      report["boot_configuration"]["/boot/grub/grub.cfg"],
      (BOOT_CONFIG / "dispatcher.cfg").read_text(),
    )
    self.assertEqual(
      report["boot_configuration"]["/boot/grub/grubenv"],
      "# GRUB Environment Block\nsaved_entry=original\n",
    )

  def test_frozen_launcher_bootstrap(self) -> None:
    launcher = HELPER.with_name("launch.sh").read_text()
    bootstrap = launcher.split("<<'DEV147_STAGE_BOOTSTRAP'\n", 1)[1].split(
      "\nDEV147_STAGE_BOOTSTRAP", 1
    )[0]
    helper_hash = launcher.split("helper_hash=", 1)[1].splitlines()[0]
    self.assertEqual(digest(HELPER), helper_hash)
    command = self.command()[:-3] + [
      "-c",
      bootstrap,
      str(HELPER),
      helper_hash,
      str(self.root / "delivery"),
      self.manifest,
    ]
    result = subprocess.run(
      command, text=True, capture_output=True, timeout=90, check=False
    )
    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
    self.assertEqual(json.loads(result.stdout)["status"], "STAGED_UNSELECTED")

  def test_launcher_rejects_changed_helper(self) -> None:
    launcher = HELPER.with_name("launch.sh").read_text()
    bootstrap = launcher.split("<<'DEV147_STAGE_BOOTSTRAP'\n", 1)[1].split(
      "\nDEV147_STAGE_BOOTSTRAP", 1
    )[0]
    command = self.command()[:-3] + [
      "-c",
      bootstrap,
      str(HELPER),
      "0" * 64,
      str(self.root / "delivery"),
      self.manifest,
    ]
    result = subprocess.run(
      command, text=True, capture_output=True, timeout=90, check=False
    )
    self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
    self.assertIn("frozen helper hash mismatch", result.stderr)
    self.assertFalse((self.root / f"modules/{RELEASE}").exists())

  def test_tampered_input(self) -> None:
    (self.root / "delivery/Image").write_text("tampered\n")
    self.run_stage(1)
    self.assertFalse((self.root / f"modules/{RELEASE}").exists())

  def test_esp_artifact_is_rejected(self) -> None:
    (self.root / "delivery/boot.bin").write_text("unexpected ESP payload\n")
    self.manifest = self.freeze()
    result = self.run_stage(1)
    self.assertIn("unexpected delivery path", result.stderr)
    self.assertFalse((self.root / f"modules/{RELEASE}").exists())

  def test_selected_grub_drift_is_rejected(self) -> None:
    (self.root / "boot/grub/grub.cfg").write_text("changed selector\n")
    self.before = self.protected()
    result = self.run_stage(1)
    self.assertIn("active input drift", result.stderr)
    self.assertFalse((self.root / f"modules/{RELEASE}").exists())

  def test_existing_target(self) -> None:
    (self.root / f"modules/{RELEASE}").mkdir()
    self.run_stage(1)

  def test_symlink_input(self) -> None:
    image = self.root / "delivery/Image"
    image.unlink()
    image.symlink_to("boot.bin")
    self.run_stage(1)

  def test_symlink_target(self) -> None:
    (self.root / f"boot/dev147-trial-{RELEASE}").symlink_to("grub")
    self.run_stage(1)

  def test_hardlink_input(self) -> None:
    image = self.root / "delivery/Image"
    (self.root / "delivery/Image.alias").hardlink_to(image)
    self.run_stage(1)

  def test_active_guard_drift(self) -> None:
    guard = self.root / "etc/pacman.d/hooks/05-omarchy-m2-displayport-guard.hook"
    guard.write_text("changed guard\n")
    self.before = self.protected()
    self.run_stage(1)

  def test_package_lock_preserved(self) -> None:
    lock = self.root / "var/lib/pacman/db.lck"
    lock.write_text("another package transaction\n")
    self.run_stage(1, existing_lock=True)
    self.assertEqual(lock.read_text(), "another package transaction\n")

  def test_manifest_traversal(self) -> None:
    manifest = self.root / "delivery/SHA256SUMS"
    manifest.write_text(f"{'0' * 64}  ../escape\n")
    self.manifest = digest(manifest)
    self.run_stage(1)

  def test_missing_receipt(self) -> None:
    (self.root / "delivery/receipts/initramfs.json").unlink()
    self.manifest = self.freeze()
    self.run_stage(1)

  def test_module_inner_manifest_tamper(self) -> None:
    (
      self.root / f"delivery/root/lib/modules/{RELEASE}/kernel/drivers/apple.ko"
    ).write_text("changed module\n")
    self.manifest = self.freeze()
    self.run_stage(1)

  def test_fifo_input_rejected(self) -> None:
    import os

    image = self.root / "delivery/Image"
    image.unlink()
    os.mkfifo(image)
    self.run_stage(1)

  def test_protected_drift_during_copy(self) -> None:
    (self.root / "delivery/Image").write_bytes(b"x" * (128 * 1024 * 1024))
    self.manifest = self.freeze()
    process = subprocess.Popen(
      self.command(), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    copied = self.root / f"var/lib/dev147-clearwait-stage/{RELEASE}/input/Image"
    deadline = time.monotonic() + 10
    while (
      not copied.exists() and process.poll() is None and time.monotonic() < deadline
    ):
      time.sleep(0.001)
    self.assertTrue(copied.exists(), "copy boundary was not reached")
    (self.root / "etc/default/grub").write_text("GRUB_DEFAULT=changed\n")
    stdout, stderr = process.communicate(timeout=90)
    self.assertEqual(process.returncode, 1, stdout + stderr)
    self.assertIn("protected input changed", stderr)
    self.assertFalse((self.root / f"modules/{RELEASE}").exists())
    self.assertFalse((self.root / f"boot/dev147-trial-{RELEASE}").exists())

  def test_oversized_input_refused_before_content_copy(self) -> None:
    with (self.root / "delivery/Image").open("wb") as stream:
      stream.truncate(2_300_000_001)
    result = self.run_stage(1)
    self.assertIn("delivery byte budget exceeded", result.stderr)
    self.assertFalse(
      (self.root / f"var/lib/dev147-clearwait-stage/{RELEASE}/input/Image").exists()
    )

  def test_oversized_unlisted_input_refused_before_content_copy(self) -> None:
    with (self.root / "delivery/000-unlisted").open("wb") as stream:
      stream.truncate(2_300_000_001)
    result = self.run_stage(1)
    self.assertIn("delivery byte budget exceeded", result.stderr)
    self.assertFalse(
      (
        self.root / f"var/lib/dev147-clearwait-stage/{RELEASE}/input/000-unlisted"
      ).exists()
    )

  def test_unlisted_entry_flood_is_bounded(self) -> None:
    for index in range(4097):
      (self.root / f"delivery/unlisted-{index}").mkdir()
    result = self.run_stage(1)
    self.assertIn("delivery entry budget exceeded", result.stderr)

  def test_growing_input_copy_is_bounded(self) -> None:
    initial_size = 128 * 1024 * 1024
    image = self.root / "delivery/Image"
    with image.open("wb") as stream:
      stream.truncate(initial_size)
    process = subprocess.Popen(
      self.command(), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    copied = self.root / f"var/lib/dev147-clearwait-stage/{RELEASE}/input/Image"
    deadline = time.monotonic() + 10
    while (
      not copied.exists() and process.poll() is None and time.monotonic() < deadline
    ):
      time.sleep(0.001)
    self.assertTrue(copied.exists(), "copy boundary was not reached")
    with image.open("r+b") as stream:
      stream.truncate(2_300_000_001)
    stdout, stderr = process.communicate(timeout=90)
    self.assertEqual(process.returncode, 1, stdout + stderr)
    self.assertIn("input grew during copy", stderr)
    self.assertLessEqual(copied.stat().st_size, initial_size)
    self.assertFalse((self.root / f"modules/{RELEASE}").exists())

  def test_recursive_file_budget_is_shared(self) -> None:
    for name in ("Image", "receipts/oversized-extra"):
      with (self.root / "delivery" / name).open("wb") as stream:
        stream.truncate(1_200_000_000)
    result = self.run_stage(1)
    self.assertIn("delivery byte budget exceeded", result.stderr)
    copied = self.root / f"var/lib/dev147-clearwait-stage/{RELEASE}/input"
    self.assertEqual((copied / "Image").stat().st_size, 1_200_000_000)
    self.assertFalse((copied / "receipts/oversized-extra").exists())


if __name__ == "__main__":
  unittest.main()
