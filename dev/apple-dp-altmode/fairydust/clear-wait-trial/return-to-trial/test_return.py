from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import baseline as activate

HERE = Path(__file__).parent
SOURCE = HERE.parents[1] / "boot-activate"
TRIAL_ROOT = Path("/home/david/Work/dev147-clear-wait-trial")
TRIAL_RELEASE = "7.1.12-dev147-clearwait100"
TRIAL_STAGED = Path(f"/boot/dev147-trial-{TRIAL_RELEASE}")
TRIAL_MODULES = Path(f"/usr/lib/modules/{TRIAL_RELEASE}")
ROOT = Path("/home/david/Work/dev147-fairydust-boot-20260905")
OUTPUT = TRIAL_ROOT / "return-to-trial/namespace-tests"


def sha(path: Path) -> str:
  return hashlib.sha256(path.read_bytes()).hexdigest()


class ReturnTests(unittest.TestCase):
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

    shutil.copytree(
      TRIAL_ROOT / "delivery/root/lib/modules" / TRIAL_RELEASE,
      cls.base / "trial-modules",
    )
    (cls.base / "trial-boot").mkdir()
    for path in (TRIAL_ROOT / "delivery").iterdir():
      if path.is_file():
        shutil.copyfile(path, cls.base / "trial-boot" / path.name)
    shutil.copytree(TRIAL_ROOT / "delivery/receipts", cls.base / "trial-boot/receipts")

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
    (self.root / "boot/initramfs-linux-asahi-dpalt.img").write_bytes(
      b"synthetic W comparison initramfs"
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

    for relative in (
      str(activate.STATE),
      str(activate.SUPPORT),
      str(activate.RECOVERY),
      str(TRIAL_STAGED),
      str(TRIAL_MODULES),
      f"/var/lib/dev147-clearwait-stage/{TRIAL_RELEASE}",
    ):
      (self.root / relative.lstrip("/")).mkdir(parents=True, exist_ok=True)
    for name in ("old.cfg", "candidate.cfg", "old.sha256", "candidate.sha256"):
      shutil.copyfile(
        SOURCE / name, self.root / str(activate.SUPPORT).lstrip("/") / name
      )
    shutil.copyfile(
      SOURCE / "old.cfg", self.root / str(activate.GRUB_BACKUP).lstrip("/")
    )
    shutil.copyfile(
      "/boot/efi/m1n1/dev147-recovery/boot.bin.old-203ab702",
      self.root / str(activate.OLD_BACKUP).lstrip("/"),
    )
    shutil.copyfile(
      SOURCE / "RECOVERY.md",
      self.root / str(activate.RECOVERY).lstrip("/") / "RECOVERY.md",
    )
    shutil.copyfile(
      TRIAL_ROOT / "stage/manual-results/result.json",
      self.root / f"var/lib/dev147-clearwait-stage/{TRIAL_RELEASE}/result.json",
    )
    self.original_state = {
      str(path.relative_to(self.root)): sha(path)
      for parent in (activate.STATE, activate.RECOVERY)
      for path in (self.root / str(parent).lstrip("/")).rglob("*")
      if path.is_file()
    }

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

  def return_command(
    self, boundary: int = 0, fixture_identity: bool = True, override: str = ""
  ) -> list[str]:
    launcher = (HERE / "launch.sh").read_text()
    bootstrap = launcher.split("<<'DEV147_ACTIVATION_BOOTSTRAP'\n", 1)[1].split(
      "\nDEV147_ACTIVATION_BOOTSTRAP", 1
    )[0]
    bootstrap = bootstrap.replace(
      'validated = topology["discover"]()',
      'validated = {path: os.stat(path).st_dev for path in ("/boot", "/boot/grub", "/boot/efi", "/boot/efi/m1n1")}',
    )
    replacement = 'globals()["__name__"] = "return_fixture"\nexec(compile(code, helper, "exec"), globals())\n'
    if fixture_identity:
      replacement += f"baseline.RESULT_HASH = {self.fixture_hash!r}\n"
    replacement += override
    if boundary:
      replacement += (
        "original_replace = baseline.replace_selected\nwrite_count = 0\n"
        "def interrupted_replace(*args):\n"
        "  global write_count\n  write_count += 1\n"
        f"  if write_count == {boundary}: raise OSError('injected boundary interruption')\n"
        "  original_replace(*args)\n"
        "baseline.replace_selected = interrupted_replace\n"
      )
    replacement += "sys.exit(main())"
    bootstrap = bootstrap.replace(
      'exec(compile(code, helper, "exec"), globals())', replacement
    )
    command = self.command("restore")
    cut = command.index("--chdir")
    command[cut:cut] = [
      "--ro-bind",
      str(HERE),
      str(HERE),
      "--ro-bind",
      str(self.base / "trial-boot"),
      str(TRIAL_STAGED),
      "--ro-bind",
      str(self.base / "trial-modules"),
      str(TRIAL_MODULES),
    ]
    cut = command.index("-c") + 1
    command[cut:] = [
      bootstrap,
      str(HERE / "return.py"),
      launcher.split("helper_hash=", 1)[1].splitlines()[0],
      str(HERE / "topology.py"),
      launcher.split("topology_hash=", 1)[1].splitlines()[0],
      str(HERE / "baseline.py"),
      launcher.split("baseline_hash=", 1)[1].splitlines()[0],
      "return",
    ]
    return command

  def run_return(self, expected: int = 0, boundary: int = 0) -> str:
    result = subprocess.run(
      self.return_command(boundary),
      capture_output=True,
      text=True,
      check=False,
      timeout=120,
    )
    self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
    for name, expected_hash in self.original_state.items():
      self.assertEqual(sha(self.root / name), expected_hash)
    self.assertFalse((self.root / "var/lib/pacman/db.lck").exists())
    self.assertEqual(
      (self.root / "boot/initramfs-linux-asahi-dpalt.img").read_bytes(),
      b"synthetic W comparison initramfs",
    )
    return result.stdout + result.stderr

  def pair(self) -> tuple[str, str]:
    return sha(self.root / "boot/grub/grub.cfg"), sha(
      self.root / "boot/efi/m1n1/boot.bin"
    )

  def restore(self) -> None:
    result = subprocess.run(
      self.command("restore"), capture_output=True, text=True, check=False, timeout=120
    )
    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
    self.assertEqual(self.pair(), (activate.GRUB_HASH, activate.OLD_HASH))
    self.assertEqual(
      (self.root / "boot/initramfs-linux-asahi-dpalt.img").read_bytes(),
      b"synthetic W comparison initramfs",
    )

  def test_success_and_unchanged_restore(self) -> None:
    result = self.run_return()
    self.assertIn("RETURNED_TO_TRIAL_NOT_REBOOTED", result)
    self.assertEqual(self.pair(), (activate.DISPATCHER_HASH, activate.NEW_HASH))
    self.assertEqual(
      (self.root / str(activate.SUPPORT).lstrip("/") / "candidate.cfg").read_bytes(),
      (HERE / "candidate.cfg").read_bytes(),
    )
    self.restore()

  def test_each_interrupted_replacement_still_restores(self) -> None:
    for boundary in (1, 2, 3):
      if boundary > 1:
        self.tearDown()
        self.setUp()
      with self.subTest(boundary=boundary):
        self.assertIn("injected boundary interruption", self.run_return(1, boundary))
        self.assertEqual(
          self.pair(),
          (
            activate.DISPATCHER_HASH if boundary == 3 else activate.GRUB_HASH,
            activate.OLD_HASH,
          ),
        )
        self.restore()

  def test_existing_attempt_is_refused(self) -> None:
    state = self.root / f"var/lib/dev147-clearwait-return/{TRIAL_RELEASE}"
    state.mkdir(parents=True)
    self.assertIn("return state exists", self.run_return(1))
    self.assertEqual(self.pair(), (activate.GRUB_HASH, activate.OLD_HASH))

  def test_modified_route_is_refused(self) -> None:
    (self.root / str(activate.SUPPORT).lstrip("/") / "old.sha256").write_text("changed")
    self.assertIn("routing dependency changed", self.run_return(1))
    self.assertEqual(self.pair(), (activate.GRUB_HASH, activate.OLD_HASH))

  def test_modified_trial_receipt_is_refused(self) -> None:
    (
      self.root / f"var/lib/dev147-clearwait-stage/{TRIAL_RELEASE}/result.json"
    ).write_text("{}")
    self.assertIn("trial root stage result changed", self.run_return(1))
    self.assertEqual(self.pair(), (activate.GRUB_HASH, activate.OLD_HASH))

  def test_corrupted_trial_image_is_refused(self) -> None:
    bad = self.root / "corrupt-Image"
    bad.write_text("corrupted staged trial Image")
    command = self.return_command()
    cut = command.index("--chdir")
    command[cut:cut] = ["--ro-bind", str(bad), str(TRIAL_STAGED / "Image")]
    result = subprocess.run(
      command, capture_output=True, text=True, check=False, timeout=120
    )
    self.assertEqual(result.returncode, 1)
    self.assertIn("trial staged bytes differ: Image", result.stderr)
    self.assertEqual(self.pair(), (activate.GRUB_HASH, activate.OLD_HASH))
    self.assertEqual(
      (self.root / str(activate.SUPPORT).lstrip("/") / "candidate.cfg").read_bytes(),
      (SOURCE / "candidate.cfg").read_bytes(),
    )

  def test_real_prior_receipt_pin_rejects_fixture(self) -> None:
    self.assertEqual(
      activate.RESULT_HASH,
      "56e8c20d25806e1ced05515aede08dfe2147163c99f4e1ce766724f539a70ae6",
    )
    result = subprocess.run(
      self.return_command(fixture_identity=False),
      capture_output=True,
      text=True,
      check=False,
      timeout=120,
    )
    self.assertEqual(result.returncode, 1)
    self.assertIn("root stage result changed", result.stderr)

  def test_changed_helper_bootstrap_is_refused(self) -> None:
    command = self.return_command()
    command[-6] = "0" * 64
    result = subprocess.run(
      command, capture_output=True, text=True, check=False, timeout=120
    )
    self.assertEqual(result.returncode, 1)
    self.assertIn("frozen code hash", result.stderr)


if __name__ == "__main__":
  unittest.main()
