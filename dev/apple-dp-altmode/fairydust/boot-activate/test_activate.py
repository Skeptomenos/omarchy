from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import activate

SOURCE = Path(__file__).parent
ROOT = Path("/home/david/Work/dev147-fairydust-boot-20260905")
OUTPUT = ROOT / "activation/namespace-tests"


def sha(path: Path) -> str:
  return hashlib.sha256(path.read_bytes()).hexdigest()


class ActivationTests(unittest.TestCase):
  shared: tempfile.TemporaryDirectory[str]
  base: Path

  @classmethod
  def setUpClass(cls) -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    cls.shared = tempfile.TemporaryDirectory(prefix="payload.", dir=OUTPUT)
    cls.base = Path(cls.shared.name)
    shutil.copytree(
      ROOT / "delivery/root/lib/modules" / activate.RELEASE, cls.base / "modules"
    )
    (cls.base / "boot").mkdir()
    for path in (ROOT / "delivery").iterdir():
      if path.is_file():
        shutil.copyfile(path, cls.base / "boot" / path.name)
    shutil.copytree(ROOT / "delivery/receipts", cls.base / "boot/receipts")

  @classmethod
  def tearDownClass(cls) -> None:
    cls.shared.cleanup()

  def setUp(self) -> None:
    self.temporary = tempfile.TemporaryDirectory(prefix="case.", dir=OUTPUT)
    self.root = Path(self.temporary.name)
    for directory in (
      "boot/grub",
      "boot/efi/m1n1",
      f"boot/dev147-fairydust-{activate.RELEASE}",
      "etc/default",
      "etc/grub.d",
      "etc/pacman.d/hooks",
      "var/lib/pacman",
      f"var/lib/dev147-fairydust-stage/{activate.RELEASE}",
      "var/lib/omarchy/m2-displayport",
    ):
      (self.root / directory).mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SOURCE / "old.cfg", self.root / "boot/grub/grub.cfg")
    shutil.copyfile("/boot/efi/m1n1/boot.bin", self.root / "boot/efi/m1n1/boot.bin")
    shutil.copyfile(
      ROOT / "stage/manual-results/result.json",
      self.root / "var/lib/dev147-fairydust-stage" / activate.RELEASE / "result.json",
    )
    shutil.copyfile(activate.GUARD, self.root / str(activate.GUARD).lstrip("/"))
    for name in ("etc/default/grub", "boot/grub/grubenv"):
      shutil.copyfile(Path("/") / name, self.root / name)
    (self.root / "var/lib/omarchy/m2-displayport/keep").write_text(
      "preserve old state\n"
    )
    (self.root / "boot/vmlinuz-linux-asahi").write_bytes(b"synthetic original kernel")
    (self.root / "boot/initramfs-linux-asahi.img").write_bytes(
      b"synthetic private original initramfs"
    )
    identities = {}
    for parent in (
      self.root / "boot",
      self.root / "etc",
      self.root / "var/lib/omarchy",
    ):
      for path in parent.rglob("*"):
        info = path.lstat()
        relative = "/" + str(path.relative_to(self.root))
        metadata = f"{info.st_mode & 0o777:o}:0:0:"
        identities[relative] = metadata + (
          "file:" + sha(path) if path.is_file() else "directory"
        )
    report = (
      self.root / "var/lib/dev147-fairydust-stage" / activate.RELEASE / "result.json"
    )
    report.write_text(json.dumps({"protected_identities": identities}))
    self.fixture_hash = sha(report)
    (self.root / "usr/lib/modules").mkdir(parents=True)
    for entry in Path("/usr/lib").iterdir():
      if entry.name != "modules":
        (self.root / "usr/lib" / entry.name).symlink_to("/runtime/lib/" + entry.name)
    (self.root / "usr/bin").symlink_to("/runtime/bin")

  def tearDown(self) -> None:
    self.temporary.cleanup()

  def command(
    self,
    action: str,
    overrides: tuple[tuple[Path, str], ...] = (),
    fixture_identity: bool = True,
  ) -> list[str]:
    launcher = (
      SOURCE / ("launch.sh" if action == "activate" else "restore.sh")
    ).read_text()
    bootstrap = launcher.split("<<'DEV147_ACTIVATION_BOOTSTRAP'\n", 1)[1].split(
      "\nDEV147_ACTIVATION_BOOTSTRAP", 1
    )[0]
    self.assertEqual(bootstrap.count('validated = topology["discover"]()'), 1)
    bootstrap = bootstrap.replace(
      'validated = topology["discover"]()',
      'validated = {path: os.stat(path).st_dev for path in ("/boot", "/boot/grub", "/boot/efi", "/boot/efi/m1n1")}',
    )
    if fixture_identity:
      bootstrap = bootstrap.replace(
        'exec(compile(code, helper, "exec"), globals())',
        'globals()["__name__"] = "dev147_fixture"\nexec(compile(code, helper, "exec"), globals())\nglobals()["RESULT_HASH"] = '
        + repr(self.fixture_hash)
        + "\nsys.exit(main())",
      )
    helper_hash = launcher.split("helper_hash=", 1)[1].splitlines()[0]
    topology_hash = launcher.split("topology_hash=", 1)[1].splitlines()[0]
    command = [
      "/usr/bin/bwrap",
      "--die-with-parent",
      "--unshare-user",
      "--uid",
      "0",
      "--gid",
      "0",
      "--tmpfs",
      "/",
      "--ro-bind",
      "/usr",
      "/runtime",
      "--bind",
      str(self.root / "usr"),
      "/usr",
      "--symlink",
      "usr/bin",
      "/bin",
      "--symlink",
      "usr/lib",
      "/lib",
      "--dev-bind",
      "/dev",
      "/dev",
      "--proc",
      "/proc",
      "--ro-bind",
      str(SOURCE),
      str(SOURCE),
    ]
    for relative in ("boot", "etc", "var/lib"):
      command += ["--bind", str(self.root / relative), "/" + relative]
    command += [
      "--ro-bind",
      str(self.base / "modules"),
      str(activate.MODULES),
      "--ro-bind",
      str(self.base / "boot"),
      str(activate.STAGED),
    ]
    for source, target in overrides:
      command += ["--ro-bind", str(source), target]
    command += [
      "--chdir",
      "/",
      "/usr/bin/env",
      "-i",
      "PATH=/usr/bin:/bin",
      "/usr/bin/python3",
      "-I",
      "-c",
      bootstrap,
      str(SOURCE / "activate.py"),
      helper_hash,
      str(SOURCE / "topology.py"),
      topology_hash,
      action,
    ]
    return command

  def run_action(
    self, action: str, expected: int = 0, overrides: tuple[tuple[Path, str], ...] = ()
  ) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
      self.command(action, overrides),
      capture_output=True,
      text=True,
      check=False,
      timeout=120,
    )
    self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
    self.assertEqual(
      sha(self.root / str(activate.GUARD).lstrip("/")), activate.GUARD_HASH
    )
    self.assertEqual(
      (self.root / "var/lib/omarchy/m2-displayport/keep").read_text(),
      "preserve old state\n",
    )
    self.assertFalse((self.root / "var/lib/pacman/db.lck").exists())
    return result

  def pair(self) -> tuple[str, str]:
    return sha(self.root / "boot/grub/grub.cfg"), sha(
      self.root / "boot/efi/m1n1/boot.bin"
    )

  def test_activate_and_restore(self) -> None:
    self.run_action("activate")
    self.assertEqual(self.pair(), (activate.DISPATCHER_HASH, activate.NEW_HASH))
    self.run_action("restore")
    self.assertEqual(self.pair(), (activate.GRUB_HASH, activate.OLD_HASH))

  def test_real_receipt_pin_rejects_fixture(self) -> None:
    self.assertEqual(
      activate.RESULT_HASH,
      "56e8c20d25806e1ced05515aede08dfe2147163c99f4e1ce766724f539a70ae6",
    )
    result = subprocess.run(
      self.command("activate", fixture_identity=False),
      check=False,
      capture_output=True,
      text=True,
      timeout=120,
    )
    self.assertEqual(result.returncode, 1)
    self.assertIn("root stage result changed", result.stderr)

  def test_original_input_drift(self) -> None:
    (self.root / "etc/default/grub").write_text("changed since stage\n")
    result = self.run_action("activate", 1)
    self.assertIn("original input drift since stage", result.stderr)
    self.assertEqual(self.pair(), (activate.GRUB_HASH, activate.OLD_HASH))

  def test_existing_package_lock(self) -> None:
    lock = self.root / "var/lib/pacman/db.lck"
    lock.write_text("other package transaction")
    result = subprocess.run(
      self.command("activate"), capture_output=True, text=True, check=False, timeout=120
    )
    self.assertEqual(result.returncode, 1)
    self.assertEqual(lock.read_text(), "other package transaction")
    self.assertEqual(self.pair(), (activate.GRUB_HASH, activate.OLD_HASH))

  def test_restore_accepts_changed_efi_variables_and_unrelated_state(self) -> None:
    self.run_action("activate")
    (self.root / "boot/efi/ubootefi.var").write_bytes(b"new boot variables")
    (self.root / "etc/default/grub").write_text("unrelated later setting")
    self.run_action("restore")
    self.assertEqual(
      (self.root / "boot/efi/ubootefi.var").read_bytes(), b"new boot variables"
    )

  def test_restore_rejects_original_initramfs_drift(self) -> None:
    self.run_action("activate")
    (self.root / "boot/initramfs-linux-asahi.img").write_bytes(b"corrupt")
    self.run_action("restore", 1)
    self.assertEqual(self.pair(), (activate.DISPATCHER_HASH, activate.NEW_HASH))

  def test_restore_ignores_broken_candidate_and_payload(self) -> None:
    self.run_action("activate")
    invalid = self.root / "bad-candidate"
    invalid.write_text("invalid")
    self.run_action(
      "restore",
      overrides=(
        (invalid, str(activate.STAGED / "boot.bin")),
        (invalid, str(SOURCE / "candidate.cfg")),
      ),
    )
    self.assertEqual(self.pair(), (activate.GRUB_HASH, activate.OLD_HASH))

  def test_restore_rejects_damaged_route_before_selected_write(self) -> None:
    self.run_action("activate")
    (self.root / str(activate.SUPPORT).lstrip("/") / "candidate.sha256").write_text(
      "broken"
    )
    result = self.run_action("restore", 1)
    self.assertIn("old routing dependency changed", result.stderr)
    self.assertEqual(self.pair(), (activate.DISPATCHER_HASH, activate.NEW_HASH))

  def test_restore_bundle_failure_preserves_candidate_pair(self) -> None:
    self.run_action("activate")
    selected = self.root / "boot/efi/m1n1/boot.bin"
    self.run_action("restore", 1, ((selected, str(activate.BUNDLE)),))
    self.assertEqual(self.pair(), (activate.DISPATCHER_HASH, activate.NEW_HASH))
    self.run_action("restore")
    self.assertEqual(self.pair(), (activate.GRUB_HASH, activate.OLD_HASH))

  def test_restore_rejects_symlink_bundle(self) -> None:
    self.run_action("activate")
    selected = self.root / "boot/efi/m1n1/boot.bin"
    selected.unlink()
    selected.symlink_to("dev147-recovery/boot.bin.old-203ab702")
    self.run_action("restore", 1)
    self.assertTrue(selected.is_symlink())

  def test_restore_rejects_corrupt_backup(self) -> None:
    self.run_action("activate")
    (self.root / str(activate.OLD_BACKUP).lstrip("/")).write_bytes(b"bad backup")
    self.run_action("restore", 1)
    self.assertEqual(self.pair(), (activate.DISPATCHER_HASH, activate.NEW_HASH))

  def test_bootstrap_rejects_tampered_helper_bytes(self) -> None:
    bad = self.root / "bad-helper.py"
    bad.write_text("raise SystemExit(0)")
    result = self.run_action("activate", 1, ((bad, str(SOURCE / "activate.py")),))
    self.assertIn("frozen code hash or identity mismatch", result.stderr)
    self.assertEqual(self.pair(), (activate.GRUB_HASH, activate.OLD_HASH))

  def test_new_custom_configuration_rejected(self) -> None:
    (self.root / "boot/grub/custom.cfg").write_text("unexpected menu")
    self.run_action("activate", 1)
    self.assertEqual(self.pair(), (activate.GRUB_HASH, activate.OLD_HASH))

  def test_unprotected_parent_rejected(self) -> None:
    (self.root / "boot/grub").chmod(0o777)
    self.run_action("activate", 1)
    self.assertEqual(self.pair(), (activate.GRUB_HASH, activate.OLD_HASH))

  def test_root_stage_tamper(self) -> None:
    (
      self.root / "var/lib/dev147-fairydust-stage" / activate.RELEASE / "result.json"
    ).write_text("{}\n")
    self.run_action("activate", 1)
    self.assertEqual(self.pair(), (activate.GRUB_HASH, activate.OLD_HASH))

  def test_existing_activation_state(self) -> None:
    (self.root / "var/lib/dev147-fairydust-activation" / activate.RELEASE).mkdir(
      parents=True
    )
    self.run_action("activate", 1)
    self.assertEqual(self.pair(), (activate.GRUB_HASH, activate.OLD_HASH))

  def test_routing_payload_tamper(self) -> None:
    bad = self.root / "bad.cfg"
    bad.write_text("invalid\n")
    self.run_action("activate", 1, ((bad, str(SOURCE / "candidate.cfg")),))
    self.assertEqual(self.pair(), (activate.GRUB_HASH, activate.OLD_HASH))

  def test_dispatcher_replace_failure_preserves_original_pair(self) -> None:
    original = self.root / "boot/grub/grub.cfg"
    self.run_action("activate", 1, ((original, str(activate.GRUB)),))
    self.assertEqual(self.pair(), (activate.GRUB_HASH, activate.OLD_HASH))
    self.assertEqual(
      sha(self.root / str(activate.OLD_BACKUP).lstrip("/")), activate.OLD_HASH
    )

  def test_bundle_replace_failure_leaves_dispatcher_old_pair(self) -> None:
    original = self.root / "boot/efi/m1n1/boot.bin"
    self.run_action("activate", 1, ((original, str(activate.BUNDLE)),))
    self.assertEqual(self.pair(), (activate.DISPATCHER_HASH, activate.OLD_HASH))
    self.run_action("restore")
    self.assertEqual(self.pair(), (activate.GRUB_HASH, activate.OLD_HASH))

  def test_restore_grub_failure_keeps_old_bundle_first(self) -> None:
    self.run_action("activate")
    selected = self.root / "boot/grub/grub.cfg"
    self.run_action("restore", 1, ((selected, str(activate.GRUB)),))
    self.assertEqual(self.pair(), (activate.DISPATCHER_HASH, activate.OLD_HASH))

  def test_restore_missing_bundle(self) -> None:
    self.run_action("activate")
    (self.root / "boot/efi/m1n1/boot.bin").unlink()
    result = self.run_action("restore")
    self.assertEqual(json.loads(result.stdout)["previous_bundle_identity"], "missing")
    self.assertEqual(self.pair(), (activate.GRUB_HASH, activate.OLD_HASH))

  def test_restore_corrupted_regular_bundle(self) -> None:
    self.run_action("activate")
    (self.root / "boot/efi/m1n1/boot.bin").write_bytes(
      b"corrupted partial FAT publication"
    )
    self.run_action("restore")
    self.assertEqual(self.pair(), (activate.GRUB_HASH, activate.OLD_HASH))


if __name__ == "__main__":
  unittest.main()
