from __future__ import annotations

import hashlib
import json
import os
import secrets
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import copying
import protect

SOURCE = Path(__file__).parent
SERVICE = Path("/usr/lib/systemd/system/linux-modules-cleanup.service")
SERVICE_HASH = "5d947290ef8c94b33c79c531e5615f4c9bea38e7649092d34af3bf0af5b1ca24"
UNIT = SERVICE.name
DROP_DIRECTORY = Path("/etc/systemd/system/linux-modules-cleanup.service.d")
DROP_NAME = "50-dev147-candidate-modules.conf"
DROP_HASH = "661df492cfdb6cf092199ace72789b9738520a8d052d10171001d61554d4a425"
STATE = Path("/var/lib/dev147-module-repair/20260905")
MODULES = Path("/usr/lib/modules")
PRIOR_STATE = (
  Path("/var/lib/dev147-fairydust-activation"),
  Path("/var/lib/dev147-fairydust-stage"),
  Path("/var/lib/dev147-clearwait-stage"),
)


@dataclass(frozen=True)
class Delivery:
  release: str
  source: Path
  manifest_hash: str


DELIVERIES = (
  Delivery(
    "7.1.12-dev147-fairydust1",
    Path("/home/david/Work/dev147-fairydust-boot-20260905/delivery"),
    "f33054856e60d3baf5cb7630cb8d7dfc60ffa586e16456c3e7313fffe6f7c59d",
  ),
  Delivery(
    "7.1.12-dev147-clearwait100",
    Path("/home/david/Work/dev147-clear-wait-trial/delivery"),
    "a89c31f8b42c3f4f958ac8aca4c312c95a222baf2e80b8b5702dbe4549e8a857",
  ),
)


def command(argv: list[str]) -> str:
  result = subprocess.run(argv, capture_output=True, text=True, check=True, timeout=30)
  protect.require(not result.stderr, f"command diagnostics: {argv[0]}")
  return result.stdout


def effective_command(content: str) -> str:
  line = next(
    line
    for line in content.splitlines()
    if line.startswith("ExecStart=/bin/bash -exc ")
  )
  return (
    line.removeprefix("ExecStart=/bin/bash -exc '")
    .removesuffix("'")
    .replace("\\'", "'")
    .replace("%v", os.uname().release)
  )


def check_service(dropin: bool) -> dict[str, str]:
  protect.require(protect.digest(SERVICE) == SERVICE_HASH, "vendor service changed")
  output = command(
    [
      "/usr/bin/systemctl",
      "show",
      UNIT,
      "--property=FragmentPath",
      "--property=DropInPaths",
      "--property=ActiveState",
      "--property=SubState",
      "--property=ExecStart",
      "--property=Job",
    ]
  )
  fields = dict(line.split("=", 1) for line in output.splitlines())
  for key, expected in {
    "FragmentPath": str(SERVICE),
    "DropInPaths": str(DROP_DIRECTORY / DROP_NAME) if dropin else "",
    "ActiveState": "inactive",
    "SubState": "dead",
    "Job": "",
  }.items():
    protect.require(
      fields.get(key) == expected, f"cleanup service state differs: {key}"
    )
  selected = DROP_DIRECTORY / DROP_NAME if dropin else SERVICE
  expected_command = effective_command(protect.read(selected).decode())
  actual = fields.get("ExecStart", "").split("argv[]=/bin/bash -exc ", 1)
  protect.require(
    len(actual) == 2 and actual[1].split(" ; ignore_errors=", 1)[0] == expected_command,
    "effective cleanup command differs",
  )
  return fields


def pin_boot() -> None:
  for path, expected in (
    (protect.GRUB, protect.GRUB_HASH),
    (protect.BUNDLE, protect.OLD_HASH),
    (protect.GUARD, protect.GUARD_HASH),
    (protect.OLD_BACKUP, protect.OLD_HASH),
  ):
    protect.require(
      protect.digest(path) == expected, f"existing boot input changed: {path}"
    )


def snapshot(excluded: tuple[Path, ...]) -> dict[str, str]:
  values: dict[str, str] = {}
  for root in (
    Path("/boot"),
    MODULES,
    Path("/var/lib/omarchy/m2-displayport"),
    protect.GUARD,
    *PRIOR_STATE,
  ):
    for path in (root, *root.rglob("*")) if root.is_dir() else (root,):
      if any(path == item or item in path.parents for item in excluded):
        continue
      values[str(path)] = protect.historical_identity(path)
  return values


def preflight() -> None:
  protect.require(os.uname().release == "7.1.6-1-1-ARCH", "unexpected running kernel")
  check_service(False)
  for path in (DROP_DIRECTORY, *(MODULES / item.release for item in DELIVERIES)):
    copying.check_absent(path)
  for delivery in DELIVERIES:
    content = protect.read(
      delivery.source / "SHA256SUMS", maximum=1_048_576, owned=False
    )
    protect.require(
      hashlib.sha256(content).hexdigest() == delivery.manifest_hash,
      "source manifest changed",
    )
    for entry in copying.parse_manifest(content).entries:
      protect.inspect(delivery.source / entry.path, owned=False)
  for path in (protect.BUNDLE, protect.GUARD, protect.OLD_BACKUP):
    expected = protect.GUARD_HASH if path == protect.GUARD else protect.OLD_HASH
    protect.require(
      protect.digest(path) == expected, f"readable boot input changed: {path}"
    )
  print(
    json.dumps(
      {
        "status": "READ_ONLY_REPAIR_PREFLIGHT_PASS",
        "privileged_checks_pending": "Root-private boot/state reads, complete copied artifact hashes and publication checks repeat under root.",
      }
    )
  )


def verify_copy(root: Path, delivery: Delivery) -> copying.Manifest:
  content = protect.read(root / "SHA256SUMS", maximum=1_048_576)
  protect.require(
    hashlib.sha256(content).hexdigest() == delivery.manifest_hash,
    "delivery manifest changed",
  )
  copying.verify_manifest(root, copying.parse_manifest(content), {"SHA256SUMS"})
  modules = copying.parse_manifest(
    protect.read(root / "modules.sha256", maximum=1_048_576)
  )
  protect.require(
    all(
      entry.path.startswith(f"lib/modules/{delivery.release}/")
      for entry in modules.entries
    ),
    "unexpected module release",
  )
  protect.require(
    sum(entry.path.endswith(".ko") for entry in modules.entries) == 1862,
    "module count differs",
  )
  copying.verify_manifest(root / "root", modules)
  return modules


def perform() -> None:
  protect.require(
    os.geteuid() == 0 and os.uname().release == "7.1.6-1-1-ARCH",
    "repair requires original running kernel and root",
  )
  os.umask(0o077)
  protect.inspect(MODULES)
  protect.inspect(DROP_DIRECTORY.parent)
  protect.inspect(STATE.parent.parent)
  for path in (
    STATE,
    DROP_DIRECTORY,
    Path("/run/systemd/system") / f"{UNIT}.d",
    Path("/usr/lib/systemd/system") / f"{UNIT}.d",
    Path("/etc/systemd/system") / UNIT,
    Path("/run/systemd/system") / UNIT,
    *(MODULES / item.release for item in DELIVERIES),
  ):
    copying.check_absent(path)
  pin_boot()
  check_service(False)
  drop = protect.read(SOURCE / DROP_NAME, owned=False)
  protect.require(
    hashlib.sha256(drop).hexdigest() == DROP_HASH, "drop-in payload changed"
  )
  pending = tuple(
    MODULES / f".dev147-module-repair-{item.release}-{secrets.token_hex(8)}"
    for item in DELIVERIES
  )
  excluded = tuple(MODULES / item.release for item in DELIVERIES) + pending
  protect.inspect(protect.LOCK.parent)
  lock = os.open(
    protect.LOCK, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
  )
  lock_info = os.fstat(lock)
  try:
    before = snapshot(excluded)
    STATE.parent.mkdir(mode=0o700, exist_ok=True)
    protect.inspect(STATE.parent)
    STATE.mkdir(mode=0o700)
    protect.sync_directory(STATE.parent)
    protect.write_new(
      STATE / "protected-before.json", (json.dumps(before, indent=2) + "\n").encode()
    )
    for delivery, destination in zip(DELIVERIES, pending, strict=True):
      copied = STATE / delivery.release
      descriptor = copying.open_directory(delivery.source)
      try:
        copying.copy_directory(descriptor, copied, copying.CopyBudget())
      finally:
        os.close(descriptor)
      modules = verify_copy(copied, delivery)
      descriptor = copying.open_directory(
        copied / "root/lib/modules" / delivery.release
      )
      try:
        copying.copy_directory(descriptor, destination, copying.CopyBudget())
      finally:
        os.close(descriptor)
      stripped = copying.Manifest(
        tuple(
          copying.Entry(
            entry.path.removeprefix(f"lib/modules/{delivery.release}/"), entry.sha256
          )
          for entry in modules.entries
        )
      )
      copying.verify_manifest(destination, stripped)
      copying.make_public(destination)
    protect.require(snapshot(excluded) == before, "preserved input drift during copy")
    pin_boot()
    check_service(False)
    copying.check_lock(lock_info)
    drop_pending = (
      DROP_DIRECTORY.parent / f".dev147-module-repair-{secrets.token_hex(8)}"
    )
    drop_pending.mkdir(mode=0o755)
    protect.write_new(drop_pending / DROP_NAME, drop, 0o644)
    copying.publish(drop_pending, DROP_DIRECTORY)
    protect.write_new(
      STATE / "drop-in-published.json",
      (
        json.dumps({"path": str(DROP_DIRECTORY / DROP_NAME), "sha256": DROP_HASH})
        + "\n"
      ).encode(),
    )
    command(["/usr/bin/systemctl", "daemon-reload"])
    loaded = check_service(True)
    protect.write_new(
      STATE / "loaded-service.json", (json.dumps(loaded, indent=2) + "\n").encode()
    )
    for index, (delivery, source) in enumerate(
      zip(DELIVERIES, pending, strict=True), 1
    ):
      copying.check_lock(lock_info)
      check_service(True)
      pin_boot()
      protect.require(
        snapshot(excluded) == before, "preserved input drift before module publication"
      )
      copying.publish(source, MODULES / delivery.release)
      protect.write_new(
        STATE / f"modules-{index}-published.json",
        (
          json.dumps(
            {"release": delivery.release, "manifest_sha256": delivery.manifest_hash}
          )
          + "\n"
        ).encode(),
      )
    protect.require(snapshot(excluded) == before, "preserved input drift after repair")
    copying.check_lock(lock_info)
    check_service(True)
    pin_boot()
    report = {
      "status": "MODULES_REPAIRED_NOT_SELECTED",
      "releases": [item.release for item in DELIVERIES],
      "module_count_per_release": 1862,
      "delivery_manifests": {item.release: item.manifest_hash for item in DELIVERIES},
      "dropin": str(DROP_DIRECTORY / DROP_NAME),
      "dropin_sha256": DROP_HASH,
      "vendor_service_sha256": SERVICE_HASH,
      "state": str(STATE),
      "cleanup_reloaded": True,
      "cleanup_restarted": False,
      "boot_selected": False,
      "limitations": "Temporary exact-two-release cleanup exemption. Packaging ownership remains follow-up. No reboot or hardware validation.",
    }
    protect.write_new(
      STATE / "result.json", (json.dumps(report, indent=2) + "\n").encode()
    )
    print(json.dumps(report, indent=2))
  finally:
    os.close(lock)
    if os.path.lexists(protect.LOCK) and (
      protect.LOCK.lstat().st_dev,
      protect.LOCK.lstat().st_ino,
    ) == (lock_info.st_dev, lock_info.st_ino):
      protect.LOCK.unlink()


def main() -> int:
  try:
    protect.require(
      len(sys.argv) == 1 or sys.argv[1:] == ["preflight"], "use frozen repair launcher"
    )
    if sys.argv[1:] == ["preflight"]:
      preflight()
    else:
      perform()
    return 0
  except (
    OSError,
    ValueError,
    UnicodeError,
    copying.StageFailure,
    protect.ActivationFailure,
    subprocess.SubprocessError,
  ) as error:
    print(
      f"FAIL: {error}\nNo boot selection or reboot requested. Preserve {STATE}, any new drop-in and module directories; inspect completed boundary receipts before retry.",
      file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
  sys.exit(main())
