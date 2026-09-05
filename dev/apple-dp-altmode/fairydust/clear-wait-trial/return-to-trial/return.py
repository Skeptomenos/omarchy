from __future__ import annotations

import hashlib
import json
import os
import stat
import sys
from pathlib import Path

import baseline

SOURCE = Path(__file__).parent
RELEASE = "7.1.12-dev147-clearwait100"
STAGED = Path(f"/boot/dev147-trial-{RELEASE}")
MODULES = Path(f"/usr/lib/modules/{RELEASE}")
STAGE_RESULT = Path(f"/var/lib/dev147-clearwait-stage/{RELEASE}/result.json")
RESULT_HASH = "cac1088402b6bb90d08baba8a55eda17be3b1424edc291bd8045a910145e9eb5"
MANIFEST_HASH = "a89c31f8b42c3f4f958ac8aca4c312c95a222baf2e80b8b5702dbe4549e8a857"
STATE = Path(f"/var/lib/dev147-clearwait-return/{RELEASE}")
MENU = baseline.SUPPORT / "candidate.cfg"
MENU_HASH = "2737b42aa18940d3f65e37a945df95b614b183c4ba84fe707084d0faae3dc1d6"


def verify_trial() -> None:
  document_bytes = baseline.read(STAGE_RESULT, maximum=1_048_576)
  baseline.require(
    hashlib.sha256(document_bytes).hexdigest() == RESULT_HASH,
    "trial root stage result changed",
  )
  document: object = json.loads(document_bytes)
  baseline.require(isinstance(document, dict), "invalid trial stage document")
  if not isinstance(document, dict):
    raise baseline.ActivationFailure("invalid trial stage document")
  for key, expected in {
    "status": "STAGED_UNSELECTED",
    "release": RELEASE,
    "manifest_sha256": MANIFEST_HASH,
    "boot_directory": str(STAGED),
    "module_directory": str(MODULES),
  }.items():
    baseline.require(document.get(key) == expected, f"trial receipt differs: {key}")
  content = baseline.read(STAGED / "SHA256SUMS", maximum=1_048_576)
  baseline.require(
    hashlib.sha256(content).hexdigest() == MANIFEST_HASH, "trial manifest changed"
  )
  boot_files = {"SHA256SUMS"}
  module_files: set[str] = set()
  remaining = 2_300_000_000
  for line in content.decode("ascii").splitlines():
    expected, name = line.split("  ", 1)
    baseline.require(
      len(expected) == 64
      and not name.startswith("/")
      and all(part not in ("", ".", "..") for part in name.split("/")),
      "invalid trial manifest entry",
    )
    prefix = f"root/lib/modules/{RELEASE}/"
    if name.startswith(prefix):
      relative = name.removeprefix(prefix)
      path = MODULES / relative
      module_files.add(relative)
    else:
      baseline.require(not name.startswith("root/"), "unexpected trial module root")
      path = STAGED / name
      boot_files.add(name)
    remaining -= baseline.inspect(path).st_size
    baseline.require(
      remaining >= 0 and baseline.digest(path) == expected,
      f"trial staged bytes differ: {name}",
    )
  for root, expected_files in ((STAGED, boot_files), (MODULES, module_files)):
    actual = {
      path.relative_to(root).as_posix()
      for path in root.rglob("*")
      if stat.S_ISREG(baseline.inspect(path).st_mode)
    }
    baseline.require(actual == expected_files, f"trial inventory differs: {root}")
  baseline.require(
    sum(name.endswith(".ko") for name in module_files) == 1862,
    "trial module count differs",
  )


def verify_support(menu_hash: str) -> None:
  for name in ("old.cfg", "old.sha256", "candidate.sha256"):
    baseline.require(
      baseline.digest(baseline.SUPPORT / name) == baseline.PINS[name],
      f"existing routing dependency changed: {name}",
    )
  baseline.require(baseline.digest(MENU) == menu_hash, "candidate menu changed")
  baseline.require(
    not os.path.lexists(baseline.SUPPORT / "custom.cfg"),
    "unexpected routing custom configuration",
  )


def preserved() -> dict[str, str]:
  result = baseline.preserved()
  for root in (baseline.STATE, baseline.RECOVERY, baseline.SUPPORT):
    for path in root.rglob("*"):
      if path != MENU:
        result[str(path)] = baseline.historical_identity(path)
  return result


def perform() -> None:
  baseline.require(
    os.geteuid() == 0 and os.uname().release == "7.1.6-1-1-ARCH",
    "return requires root and the restored original running kernel",
  )
  os.umask(0o077)
  expected_devices = baseline.devices()
  baseline.recheck_devices(expected_devices)
  baseline.require(
    not os.path.lexists(STATE), "return state exists; inspect or restore"
  )
  baseline.inspect(STATE.parent.parent)
  baseline.inspect(baseline.LOCK.parent)
  lock = os.open(
    baseline.LOCK, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
  )
  lock_info = os.fstat(lock)
  try:
    baseline.require(
      baseline.digest(baseline.GRUB) == baseline.GRUB_HASH
      and baseline.digest(baseline.BUNDLE) == baseline.OLD_HASH,
      "selected pair is not restored original",
    )
    baseline.verify_original("restore")
    baseline.verify_stage()
    verify_trial()
    baseline.require(
      baseline.digest(baseline.GRUB_BACKUP) == baseline.GRUB_HASH
      and baseline.digest(baseline.OLD_BACKUP) == baseline.OLD_HASH
      and baseline.digest(baseline.RECOVERY / "RECOVERY.md") == baseline.GUIDE_HASH,
      "existing recovery input changed",
    )
    verify_support(baseline.PINS["candidate.cfg"])
    old_menu = baseline.read(MENU)
    new_menu = baseline.read(SOURCE / "candidate.cfg", owned=False)
    dispatcher = baseline.read(SOURCE / "dispatcher.cfg", owned=False)
    bundle = baseline.read(baseline.STAGED / "boot.bin")
    for content, expected in (
      (old_menu, baseline.PINS["candidate.cfg"]),
      (new_menu, MENU_HASH),
      (dispatcher, baseline.DISPATCHER_HASH),
      (bundle, baseline.NEW_HASH),
    ):
      baseline.require(
        hashlib.sha256(content).hexdigest() == expected, "captured payload changed"
      )
    before = preserved()
    STATE.parent.mkdir(mode=0o700, exist_ok=True)
    baseline.inspect(STATE.parent)
    STATE.mkdir(mode=0o700)
    baseline.sync_directory(STATE.parent)
    baseline.write_new(STATE / "candidate.cfg.previous", old_menu)
    baseline.write_new(
      STATE / "protected-before.json", (json.dumps(before, indent=2) + "\n").encode()
    )
    baseline.write_new(STATE / "candidate.cfg.new", new_menu)
    replacements = (
      (MENU, new_menu, baseline.PINS["candidate.cfg"], 0o600),
      (baseline.GRUB, dispatcher, baseline.GRUB_HASH, 0o600),
      (baseline.BUNDLE, bundle, baseline.OLD_HASH, 0o755),
    )
    menu_hash = baseline.PINS["candidate.cfg"]
    for index, (path, content, previous, mode) in enumerate(replacements, 1):
      verify_support(menu_hash)
      expected_grub = baseline.GRUB_HASH if index < 3 else baseline.DISPATCHER_HASH
      baseline.require(
        baseline.digest(baseline.GRUB) == expected_grub
        and baseline.digest(baseline.BUNDLE) == baseline.OLD_HASH,
        "selected pair drift before replacement",
      )
      baseline.require(preserved() == before, "protected inputs changed before write")
      baseline.write_new(
        STATE / f"boundary-{index}-before.json",
        (
          json.dumps({"target": str(path), "previous_sha256": previous}) + "\n"
        ).encode(),
      )
      baseline.replace_selected(
        path,
        content,
        previous,
        expected_devices,
        (lock_info.st_dev, lock_info.st_ino),
        mode,
      )
      if path == MENU:
        menu_hash = MENU_HASH
      os.sync()
      verify_support(menu_hash)
      baseline.require(
        baseline.digest(baseline.GRUB)
        == (baseline.GRUB_HASH if index == 1 else baseline.DISPATCHER_HASH)
        and baseline.digest(baseline.BUNDLE)
        == (baseline.NEW_HASH if index == 3 else baseline.OLD_HASH),
        "selected pair drift after replacement",
      )
      baseline.require(preserved() == before, "protected inputs changed after write")
      baseline.write_new(
        STATE / f"boundary-{index}-complete.json",
        (
          json.dumps({"target": str(path), "sha256": baseline.digest(path)}) + "\n"
        ).encode(),
      )
    baseline.recheck_devices(expected_devices)
    baseline.require(
      (baseline.inspect(baseline.LOCK).st_dev, baseline.inspect(baseline.LOCK).st_ino)
      == (lock_info.st_dev, lock_info.st_ino),
      "package lock changed after selection",
    )
    baseline.require(
      baseline.digest(baseline.GRUB) == baseline.DISPATCHER_HASH
      and baseline.digest(baseline.BUNDLE) == baseline.NEW_HASH,
      "final selected pair differs",
    )
    report = {
      "status": "RETURNED_TO_TRIAL_NOT_REBOOTED",
      "release": RELEASE,
      "trial_manifest_sha256": MANIFEST_HASH,
      "trial_stage_result_sha256": RESULT_HASH,
      "menu_sha256": MENU_HASH,
      "grub_sha256": baseline.DISPATCHER_HASH,
      "bundle_sha256": baseline.NEW_HASH,
      "original_menu_backup": str(STATE / "candidate.cfg.previous"),
      "state": str(STATE),
      "limitations": "No reboot or hardware test. Existing restore retains its original default; W still needs its manual initrd edit. FAT power-loss atomicity is not guaranteed.",
    }
    baseline.write_new(
      STATE / "result.json", (json.dumps(report, indent=2) + "\n").encode()
    )
    print(json.dumps(report, indent=2))
  finally:
    os.close(lock)
    if os.path.lexists(baseline.LOCK) and (
      baseline.LOCK.lstat().st_dev,
      baseline.LOCK.lstat().st_ino,
    ) == (lock_info.st_dev, lock_info.st_ino):
      baseline.LOCK.unlink()


def main() -> int:
  try:
    baseline.require(
      len(sys.argv) == 2 and sys.argv[1] == "return", "use frozen launcher"
    )
    perform()
    return 0
  except (OSError, baseline.ActivationFailure, UnicodeError, ValueError) as error:
    print(
      f"FAIL: {error}\nNo reboot requested. Preserve return receipts; use the unchanged reviewed restore command after inspection.",
      file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
  sys.exit(main())
