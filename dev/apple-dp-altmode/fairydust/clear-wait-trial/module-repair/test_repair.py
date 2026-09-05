from __future__ import annotations

import hashlib
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import protect
import repair

SOURCE = Path(__file__).parent
BOOT_SOURCE = SOURCE.parents[1] / "boot-activate"


def sha(path: Path) -> str:
  return hashlib.sha256(path.read_bytes()).hexdigest()


class RepairTests(unittest.TestCase):
  def setUp(self) -> None:
    fixture_parent = Path(
      "/home/david/Work/dev147-clear-wait-trial/module-repair/fixtures"
    )
    fixture_parent.mkdir(parents=True, exist_ok=True)
    self.temporary = tempfile.TemporaryDirectory(
      prefix="dev147-module-repair.", dir=fixture_parent
    )
    self.root = Path(self.temporary.name)
    for name in (
      "usr/lib/modules/7.1.6-1-1-ARCH",
      "usr/lib/modules/.old/archive",
      "usr/lib/systemd/system",
      "boot/efi/m1n1/dev147-recovery",
      "boot/grub",
      "etc/systemd/system",
      "etc/pacman.d/hooks",
      "var/lib/pacman",
      "var/lib/omarchy/m2-displayport",
      "run/systemd/system",
    ):
      (self.root / name).mkdir(parents=True, exist_ok=True)
    for entry in Path("/usr/lib").iterdir():
      if entry.name not in ("modules", "systemd"):
        (self.root / "usr/lib" / entry.name).symlink_to("/runtime/lib/" + entry.name)
    (self.root / "usr/bin").symlink_to("/runtime/bin")
    shutil.copyfile(SOURCE / repair.UNIT, self.root / str(repair.SERVICE).lstrip("/"))
    shutil.copyfile(BOOT_SOURCE / "old.cfg", self.root / "boot/grub/grub.cfg")
    for target in (
      "boot/efi/m1n1/boot.bin",
      "boot/efi/m1n1/dev147-recovery/boot.bin.old-203ab702",
    ):
      shutil.copyfile(
        "/boot/efi/m1n1/dev147-recovery/boot.bin.old-203ab702", self.root / target
      )
    shutil.copyfile(protect.GUARD, self.root / str(protect.GUARD).lstrip("/"))
    for target in (
      "boot/initramfs-linux-asahi-dpalt.img",
      "usr/lib/modules/7.1.6-1-1-ARCH/preserved.ko",
      "usr/lib/modules/.old/archive/preserved",
      "var/lib/omarchy/m2-displayport/preserved",
    ):
      (self.root / target).write_text("preserve " + target)
    self.before = {
      str(path.relative_to(self.root)): sha(path)
      for parent in ("boot", "usr/lib/modules", "var/lib/omarchy", "etc/pacman.d")
      for path in (self.root / parent).rglob("*")
      if path.is_file()
    }
    for prior in repair.PRIOR_STATE[:2]:
      prior_target = self.root / str(prior).lstrip("/")
      prior_target.mkdir()
      (prior_target / "preserved.json").write_text("prior protected receipt")
      self.before[str((prior_target / "preserved.json").relative_to(self.root))] = sha(
        prior_target / "preserved.json"
      )
    systemctl = self.root / "systemctl"
    systemctl.write_text("""#!/usr/bin/python3
import pathlib,sys
unit="linux-modules-cleanup.service"
drop=pathlib.Path("/etc/systemd/system/"+unit+".d/50-dev147-candidate-modules.conf")
vendor=pathlib.Path("/usr/lib/systemd/system/"+unit)
if sys.argv[1:]==["daemon-reload"]:
 pathlib.Path("/run/reloaded").write_text("yes")
 raise SystemExit(0)
assert sys.argv[1]=="show"
loaded=drop.exists() and pathlib.Path("/run/reloaded").exists()
text=(drop if loaded else vendor).read_text()
line=next(line for line in text.splitlines() if line.startswith("ExecStart=/bin/bash -exc "))
body=line.removeprefix("ExecStart=/bin/bash -exc '").removesuffix("'").replace("\\\\'", "'").replace("%v","7.1.6-1-1-ARCH")
print("FragmentPath="+str(vendor))
print("DropInPaths="+(str(drop) if loaded else ""))
print("ActiveState=inactive\\nSubState=dead\\nJob=")
print("ExecStart={ path=/bin/bash ; argv[]=/bin/bash -exc "+body+" ; ignore_errors=no }")
""")
    systemctl.chmod(0o700)

  def tearDown(self) -> None:
    self.temporary.cleanup()

  def command(self, fail_publication: int = 0) -> list[str]:
    launcher = (SOURCE / "launch.sh").read_text()
    bootstrap = launcher.split("<<'DEV147_MODULE_REPAIR_BOOTSTRAP'\n", 1)[1].split(
      "\nDEV147_MODULE_REPAIR_BOOTSTRAP", 1
    )[0]
    if fail_publication:
      bootstrap = bootstrap.replace(
        'exec(compile(content, path, "exec"), globals())',
        """module = types.ModuleType("repair_fixture")
module.__file__ = path
sys.modules["repair_fixture"] = module
exec(compile(content, path, "exec"), module.__dict__)
original_publish = module.copying.publish
count = 0
def interrupted_publish(*args):
  global count
  count += 1
  if count == """
        + str(fail_publication)
        + """: raise OSError("injected publication interruption")
  return original_publish(*args)
module.copying.publish = interrupted_publish
sys.exit(module.main())""",
      )
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
    for relative in ("boot", "etc", "var/lib", "run"):
      command += ["--bind", str(self.root / relative), "/" + relative]
    for delivery in repair.DELIVERIES:
      command += ["--ro-bind", str(delivery.source), str(delivery.source)]
    command += [
      "--ro-bind",
      str(self.root / "systemctl"),
      "/usr/bin/systemctl",
      "--chdir",
      "/",
      "/usr/bin/env",
      "-i",
      "PATH=/usr/bin:/bin",
      "/usr/bin/python3",
      "-I",
      "-c",
      bootstrap,
      str(SOURCE),
      launcher.split("helper_hash=", 1)[1].splitlines()[0],
      "repair",
    ]
    return command

  def run_case(
    self,
    expected: int = 0,
    fail_publication: int = 0,
    override: tuple[Path, Path] | None = None,
  ) -> str:
    command = self.command(fail_publication)
    if override:
      cut = command.index("--chdir")
      command[cut:cut] = ["--ro-bind", str(override[0]), str(override[1])]
    result = subprocess.run(
      command, capture_output=True, text=True, check=False, timeout=240
    )
    self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
    for name, expected_hash in self.before.items():
      self.assertEqual(sha(self.root / name), expected_hash)
    self.assertFalse((self.root / "var/lib/pacman/db.lck").exists())
    return result.stdout + result.stderr

  def test_full_artifacts_repaired_and_cleanup_reloaded_only(self) -> None:
    self.assertIn("MODULES_REPAIRED_NOT_SELECTED", self.run_case())
    self.assertEqual((self.root / "run/reloaded").read_text(), "yes")
    for delivery in repair.DELIVERIES:
      published = self.root / "usr/lib/modules" / delivery.release
      self.assertEqual(len(list(published.rglob("*.ko"))), 1862)
      for path in published.rglob("*"):
        if path.is_file():
          self.assertEqual(
            sha(path),
            sha(
              delivery.source
              / "root/lib/modules"
              / delivery.release
              / path.relative_to(published)
            ),
          )

  def test_existing_release_refused_without_overwrite(self) -> None:
    (self.root / "usr/lib/modules" / repair.DELIVERIES[0].release).mkdir()
    self.assertIn("target already exists", self.run_case(1))

  def test_existing_dropin_refused(self) -> None:
    (self.root / str(repair.DROP_DIRECTORY).lstrip("/")).mkdir()
    self.assertIn("target already exists", self.run_case(1))

  def test_vendor_change_refused(self) -> None:
    (self.root / str(repair.SERVICE).lstrip("/")).write_text("changed service")
    self.assertIn("vendor service changed", self.run_case(1))

  def test_corrupt_delivery_file_refused(self) -> None:
    bad = self.root / "bad-image"
    bad.write_text("corrupted source")
    self.assertIn(
      "artifact hash mismatch",
      self.run_case(1, override=(bad, repair.DELIVERIES[0].source / "Image")),
    )
    self.assertFalse((self.root / str(repair.DROP_DIRECTORY).lstrip("/")).exists())

  def test_missing_delivery_module_refused(self) -> None:
    empty = self.root / "empty-modules"
    empty.mkdir()
    self.assertIn(
      "manifest inventory mismatch",
      self.run_case(
        1,
        override=(
          empty,
          repair.DELIVERIES[0].source
          / "root/lib/modules"
          / repair.DELIVERIES[0].release,
        ),
      ),
    )

  def test_partial_module_publication_retains_exemption(self) -> None:
    self.assertIn(
      "injected publication interruption", self.run_case(1, fail_publication=3)
    )
    self.assertTrue(
      (self.root / str(repair.DROP_DIRECTORY / repair.DROP_NAME).lstrip("/")).is_file()
    )
    self.assertTrue(
      (self.root / "usr/lib/modules" / repair.DELIVERIES[0].release).is_dir()
    )
    self.assertFalse(
      (self.root / "usr/lib/modules" / repair.DELIVERIES[1].release).exists()
    )


if __name__ == "__main__":
  unittest.main()
