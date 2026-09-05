from __future__ import annotations

import hashlib
import json
import os
import secrets
import stat
import sys
from pathlib import Path

RELEASE = "7.1.12-dev147-fairydust1"
SOURCE = Path(__file__).parent
STAGED = Path(f"/boot/dev147-fairydust-{RELEASE}")
MODULES = Path(f"/usr/lib/modules/{RELEASE}")
STAGE_RESULT = Path(f"/var/lib/dev147-fairydust-stage/{RELEASE}/result.json")
STATE = Path(f"/var/lib/dev147-fairydust-activation/{RELEASE}")
SUPPORT = Path(f"/boot/grub/dev147-paired-{RELEASE}")
RECOVERY = Path("/boot/efi/m1n1/dev147-recovery")
GRUB = Path("/boot/grub/grub.cfg")
BUNDLE = Path("/boot/efi/m1n1/boot.bin")
OLD_BACKUP = RECOVERY / "boot.bin.old-203ab702"
GRUB_BACKUP = STATE / "grub.cfg.original"
LOCK = Path("/var/lib/pacman/db.lck")
OLD_HASH = "203ab7027536c8d16f373d02c1f6346a5c34cfe095a9dafd0cfe37d2b354090c"
NEW_HASH = "1ae29a2bfadb309562c205520d8c28e2a8df2283bc88bbfb52474e54333c3dff"
GRUB_HASH = "57d839b9bc7d3488402a8cf7c9e45328dc0097731fc395b0514c467d06b7a327"
DISPATCHER_HASH = "58fd5692f3e28013ce54df8de255c552117c1786a7d027e2da21b7fc8a63a9d2"
MANIFEST_HASH = "f33054856e60d3baf5cb7630cb8d7dfc60ffa586e16456c3e7313fffe6f7c59d"
RESULT_HASH = "56e8c20d25806e1ced05515aede08dfe2147163c99f4e1ce766724f539a70ae6"
GUIDE_HASH = "cd96a4d02ef1e9ac728a604a2ab377794b4bc5f944bd133cd11cae40b401178c"
PINS = {
  "dispatcher.cfg": DISPATCHER_HASH,
  "old.cfg": GRUB_HASH,
  "candidate.cfg": "d4082978c51d96419e98218e472b76653ca52bf1c357fc12ba50786f671efcf6",
  "old.sha256": "b0e5899dfc01b9ddd29a91c5b9ae5dd16f5de9986375470766b30ebf215747a9",
  "candidate.sha256": "4b29319c900ddf4cdfd275c25c31eb7be42be22104b653914f56f6ec90895202",
  "RECOVERY.md": GUIDE_HASH,
}
GUARD = Path("/etc/pacman.d/hooks/05-omarchy-m2-displayport-guard.hook")
GUARD_HASH = "469820ad7cfd015a22cff979b0aa70d62e82dcc7cc05951dca92f40cd660f2bd"
READ_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
DEVICE_PATHS = ("/boot", "/boot/grub", "/boot/efi", "/boot/efi/m1n1")


class ActivationFailure(Exception):
  pass


def require(condition: bool, message: str) -> None:
  if not condition:
    raise ActivationFailure(message)


def inspect(path: Path, owned: bool = True) -> os.stat_result:
  for parent in reversed((path, *path.parents)):
    parent_info = parent.lstat()
    require(not stat.S_ISLNK(parent_info.st_mode), f"symlink path: {parent}")
    require(
      not owned or (parent_info.st_uid == 0 and not parent_info.st_mode & 0o022),
      f"unprotected ancestor: {parent}",
    )
  info = path.lstat()
  require(
    stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode), f"special path: {path}"
  )
  require(
    not owned or (info.st_uid == 0 and not info.st_mode & 0o022),
    f"unprotected path: {path}",
  )
  if stat.S_ISREG(info.st_mode):
    require(info.st_nlink == 1, f"hardlinked path: {path}")
  return info


def read(path: Path, maximum: int = 16_777_216, owned: bool = True) -> bytes:
  before = inspect(path, owned)
  require(
    stat.S_ISREG(before.st_mode) and before.st_size <= maximum,
    f"invalid file size/type: {path}",
  )
  descriptor = os.open(path, READ_FLAGS)
  with os.fdopen(descriptor, "rb") as stream:
    require(os.fstat(stream.fileno()) == before, "source changed before read")
    content = stream.read(before.st_size + 1)
    after = os.fstat(stream.fileno())
    require(
      len(content) == before.st_size
      and (after.st_size, after.st_mtime_ns, after.st_ctime_ns)
      == (before.st_size, before.st_mtime_ns, before.st_ctime_ns),
      f"source changed during read: {path}",
    )
    return content


def digest(path: Path, maximum: int = 2_300_000_000) -> str:
  before = inspect(path)
  require(
    stat.S_ISREG(before.st_mode) and before.st_size <= maximum,
    f"invalid file size/type: {path}",
  )
  checksum = hashlib.sha256()
  descriptor = os.open(path, READ_FLAGS)
  with os.fdopen(descriptor, "rb") as stream:
    require(os.fstat(stream.fileno()) == before, "source changed before hash")
    remaining = before.st_size
    while remaining:
      chunk = stream.read(min(1_048_576, remaining))
      require(bool(chunk), "source ended during hash")
      checksum.update(chunk)
      remaining -= len(chunk)
    require(not stream.read(1), "source grew during hash")
    after = os.fstat(stream.fileno())
    require(
      (after.st_size, after.st_mtime_ns, after.st_ctime_ns)
      == (before.st_size, before.st_mtime_ns, before.st_ctime_ns),
      "source drift during hash",
    )
  return checksum.hexdigest()


def identity(path: Path) -> str:
  if not os.path.lexists(path):
    return "missing"
  return digest(path)


def devices() -> dict[str, int]:
  value: object = globals().get("validated_directory_devices")
  require(
    isinstance(value, dict) and set(value) == set(DEVICE_PATHS),
    "use the frozen launcher with privileged topology preflight",
  )
  if not isinstance(value, dict):
    raise ActivationFailure("missing topology")
  require(all(type(item) is int for item in value.values()), "invalid topology record")
  return {str(name): int(number) for name, number in value.items()}


def recheck_devices(expected: dict[str, int]) -> None:
  for name, device in expected.items():
    require(inspect(Path(name)).st_dev == device, f"mount device changed: {name}")


def sync_directory(path: Path) -> None:
  descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
  try:
    os.fsync(descriptor)
  finally:
    os.close(descriptor)


def write_new(path: Path, content: bytes, mode: int = 0o600) -> None:
  inspect(path.parent)
  descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
  with os.fdopen(descriptor, "wb") as stream:
    stream.write(content)
    stream.flush()
    os.fsync(stream.fileno())
  sync_directory(path.parent)
  require(
    digest(path) == hashlib.sha256(content).hexdigest(),
    f"new file verification failed: {path}",
  )


def replace_selected(
  path: Path,
  content: bytes,
  previous: str,
  expected_devices: dict[str, int],
  lock_identity: tuple[int, int],
  mode: int,
) -> None:
  temporary = path.with_name(f".{path.name}.dev147-{secrets.token_hex(12)}")
  write_new(temporary, content, mode)
  recheck_devices(expected_devices)
  require(
    (inspect(LOCK).st_dev, inspect(LOCK).st_ino) == lock_identity,
    "package lock changed",
  )
  require(identity(path) == previous, f"selected file drift: {path}")
  os.replace(temporary, path)
  sync_directory(path.parent)
  require(
    digest(path) == hashlib.sha256(content).hexdigest(),
    f"selected file verification failed: {path}",
  )


def frozen_payload() -> dict[str, bytes]:
  result: dict[str, bytes] = {}
  for name, expected in PINS.items():
    content = read(SOURCE / name, owned=False)
    require(
      hashlib.sha256(content).hexdigest() == expected, f"frozen payload changed: {name}"
    )
    result[name] = content
  return result


def historical_identity(path: Path) -> str:
  if not os.path.lexists(path):
    return "absent"
  info = path.lstat()
  metadata = f"{stat.S_IMODE(info.st_mode):o}:{info.st_uid}:{info.st_gid}:"
  if stat.S_ISLNK(info.st_mode):
    return metadata + "symlink:" + os.readlink(path)
  if stat.S_ISREG(info.st_mode):
    return metadata + "file:" + digest(path)
  require(stat.S_ISDIR(info.st_mode), f"unexpected original path type: {path}")
  return metadata + "directory"


def verify_original(action: str) -> None:
  result = read(STAGE_RESULT, maximum=1_048_576)
  require(
    hashlib.sha256(result).hexdigest() == RESULT_HASH, "root stage result changed"
  )
  document: object = json.loads(result)
  require(isinstance(document, dict), "invalid stage document")
  if not isinstance(document, dict):
    raise ActivationFailure("invalid stage document")
  values: object = document.get("protected_identities")
  require(isinstance(values, dict), "missing original identities")
  if not isinstance(values, dict):
    raise ActivationFailure("invalid original identities")
  for custom in (Path("/boot/grub/custom.cfg"), Path("/etc/grub.d/custom.cfg")):
    require(
      historical_identity(custom) == values.get(str(custom), "absent"),
      f"custom GRUB configuration drift: {custom}",
    )
  require(
    not os.path.lexists(SUPPORT / "custom.cfg"),
    "unexpected routing custom configuration",
  )
  for name, expected in values.items():
    require(
      isinstance(name, str) and name.startswith("/") and isinstance(expected, str),
      "invalid original identity",
    )
    path = Path(name)
    if action == "restore" and not (
      name
      in (
        "/boot/vmlinuz-linux-asahi",
        "/boot/initramfs-linux-asahi.img",
        "/boot/efi/EFI/BOOT/BOOTAA64.EFI",
        str(GUARD),
      )
      or name.startswith("/boot/grub/arm64-efi/")
    ):
      continue
    require(
      historical_identity(path) == expected, f"original input drift since stage: {path}"
    )
  require(digest(GUARD) == GUARD_HASH, "existing package guard changed")


def verify_stage() -> None:
  content = read(STAGED / "SHA256SUMS", maximum=1_048_576)
  require(
    hashlib.sha256(content).hexdigest() == MANIFEST_HASH, "staged manifest changed"
  )
  boot_files = {"SHA256SUMS"}
  module_files: set[str] = set()
  remaining = 2_300_000_000
  for line in content.decode("ascii").splitlines():
    expected, name = line.split("  ", 1)
    require(
      len(expected) == 64
      and not name.startswith("/")
      and all(part not in ("", ".", "..") for part in name.split("/")),
      "invalid fixed manifest entry",
    )
    prefix = f"root/lib/modules/{RELEASE}/"
    if name.startswith(prefix):
      relative = name.removeprefix(prefix)
      path = MODULES / relative
      module_files.add(relative)
    else:
      require(not name.startswith("root/"), "unexpected module root")
      path = STAGED / name
      boot_files.add(name)
    remaining -= inspect(path).st_size
    require(remaining >= 0 and digest(path) == expected, f"staged bytes differ: {name}")
  for root, expected_files in ((STAGED, boot_files), (MODULES, module_files)):
    actual: set[str] = set()
    for path in root.rglob("*"):
      info = inspect(path)
      if stat.S_ISREG(info.st_mode):
        actual.add(path.relative_to(root).as_posix())
    require(actual == expected_files, f"staged inventory differs: {root}")
  require(
    sum(name.endswith(".ko") for name in module_files) == 1862,
    "staged module count differs",
  )
  require(digest(GUARD) == GUARD_HASH, "existing package guard changed")


def preserved() -> dict[str, str]:
  roots = (
    Path("/boot"),
    Path("/etc/default/grub"),
    Path("/etc/grub.d"),
    GUARD,
    Path("/var/lib/omarchy/m2-displayport"),
  )
  skipped = (STAGED, SUPPORT, RECOVERY)
  result: dict[str, str] = {}
  for root in roots:
    if not os.path.lexists(root):
      result[str(root)] = "missing"
      continue
    paths = root.rglob("*") if root.is_dir() else (root,)
    for path in paths:
      if (
        path in (GRUB, BUNDLE)
        or any(path == directory or directory in path.parents for directory in skipped)
        or path.name.startswith(".")
        and ".dev147-" in path.name
      ):
        continue
      info = path.lstat()
      if stat.S_ISLNK(info.st_mode):
        result[str(path)] = "symlink:" + os.readlink(path)
      elif stat.S_ISREG(info.st_mode):
        result[str(path)] = digest(path)
  return result


def prepare(payload: dict[str, bytes], old_grub: bytes, old_bundle: bytes) -> None:
  require(
    hashlib.sha256(old_grub).hexdigest() == GRUB_HASH
    and hashlib.sha256(old_bundle).hexdigest() == OLD_HASH,
    "original backup bytes drifted",
  )
  require(
    not os.path.lexists(STATE), "activation state already exists; inspect or restore it"
  )
  require(
    not os.path.lexists(SUPPORT) and not os.path.lexists(RECOVERY),
    "routing or recovery destination already exists",
  )
  inspect(STATE.parent.parent)
  inspect(SUPPORT.parent)
  inspect(RECOVERY.parent)
  STATE.parent.mkdir(mode=0o700, exist_ok=True)
  inspect(STATE.parent)
  STATE.mkdir(mode=0o700)
  sync_directory(STATE.parent)
  write_new(GRUB_BACKUP, old_grub)
  RECOVERY.mkdir(mode=0o700)
  sync_directory(RECOVERY.parent)
  write_new(OLD_BACKUP, old_bundle, 0o644)
  write_new(RECOVERY / "RECOVERY.md", payload["RECOVERY.md"], 0o644)
  SUPPORT.mkdir(mode=0o700)
  sync_directory(SUPPORT.parent)
  for name in ("old.cfg", "candidate.cfg", "old.sha256", "candidate.sha256"):
    write_new(SUPPORT / name, payload[name])
  require(
    not os.path.lexists(SUPPORT / "custom.cfg"),
    "unexpected routing custom configuration",
  )
  os.sync()


def perform(action: str) -> None:
  require(
    os.geteuid() == 0 and action in ("activate", "restore"),
    "use a frozen activate or restore launcher",
  )
  os.umask(0o077)
  expected_devices = devices()
  recheck_devices(expected_devices)
  inspect(LOCK.parent)
  lock = os.open(LOCK, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
  lock_info = os.fstat(lock)
  try:
    verify_original(action)
    if action == "activate":
      payload = frozen_payload()
      verify_stage()
    before = preserved()
    grub_before = identity(GRUB)
    bundle_before = identity(BUNDLE)
    if action == "activate":
      require(
        os.uname().release == "7.1.6-1-1-ARCH",
        "activation requires the original running kernel",
      )
      require(
        grub_before == GRUB_HASH and bundle_before == OLD_HASH,
        "selected boot inputs changed",
      )
      candidate_bundle = read(STAGED / "boot.bin")
      require(
        hashlib.sha256(candidate_bundle).hexdigest() == NEW_HASH,
        "candidate bundle drift before publication",
      )
      prepare(payload, read(GRUB), read(BUNDLE))
      require(preserved() == before, "protected input drift during preparation")
      replace_selected(
        GRUB,
        payload["dispatcher.cfg"],
        GRUB_HASH,
        expected_devices,
        (lock_info.st_dev, lock_info.st_ino),
        0o600,
      )
      os.sync()
      require(preserved() == before, "protected input drift before bundle activation")
      replace_selected(
        BUNDLE,
        candidate_bundle,
        OLD_HASH,
        expected_devices,
        (lock_info.st_dev, lock_info.st_ino),
        0o755,
      )
      expected_grub, expected_bundle, status = (
        DISPATCHER_HASH,
        NEW_HASH,
        "ACTIVATED_NOT_REBOOTED",
      )
    else:
      require(
        grub_before in (GRUB_HASH, DISPATCHER_HASH),
        "GRUB is neither original nor exact dispatcher",
      )
      if grub_before == DISPATCHER_HASH:
        for name in ("old.cfg", "old.sha256", "candidate.sha256"):
          require(
            digest(SUPPORT / name) == PINS[name],
            f"old routing dependency changed: {name}",
          )
      require(
        digest(GRUB_BACKUP) == GRUB_HASH and digest(OLD_BACKUP) == OLD_HASH,
        "recovery backup changed or missing",
      )
      require(digest(RECOVERY / "RECOVERY.md") == GUIDE_HASH, "recovery guide changed")
      write_new(
        STATE / f"restore-before-{secrets.token_hex(12)}.json",
        (
          json.dumps({"grub_sha256": grub_before, "bundle_identity": bundle_before})
          + "\n"
        ).encode(),
      )
      old_bundle = read(OLD_BACKUP)
      old_grub = read(GRUB_BACKUP)
      require(
        hashlib.sha256(old_bundle).hexdigest() == OLD_HASH
        and hashlib.sha256(old_grub).hexdigest() == GRUB_HASH,
        "recovery captured bytes changed",
      )
      if bundle_before != OLD_HASH:
        replace_selected(
          BUNDLE,
          old_bundle,
          bundle_before,
          expected_devices,
          (lock_info.st_dev, lock_info.st_ino),
          0o755,
        )
      require(digest(BUNDLE) == OLD_HASH, "old bundle was not restored")
      os.sync()
      if grub_before != GRUB_HASH:
        replace_selected(
          GRUB,
          old_grub,
          grub_before,
          expected_devices,
          (lock_info.st_dev, lock_info.st_ino),
          0o600,
        )
      expected_grub, expected_bundle, status = (
        GRUB_HASH,
        OLD_HASH,
        "RESTORED_NOT_REBOOTED",
      )
    recheck_devices(expected_devices)
    require(
      (inspect(LOCK).st_dev, inspect(LOCK).st_ino)
      == (lock_info.st_dev, lock_info.st_ino),
      "package lock changed",
    )
    require(
      digest(GRUB) == expected_grub and digest(BUNDLE) == expected_bundle,
      "final boot pair differs",
    )
    require(preserved() == before, "protected input drift after selected writes")
    receipt = {
      "status": status,
      "action": action,
      "release": RELEASE,
      "grub_sha256": expected_grub,
      "bundle_sha256": expected_bundle,
      "previous_bundle_identity": bundle_before,
      "directory_devices": expected_devices,
      "protected_input_count": len(before),
      "historical_scope": "all captured original inputs"
      if action == "activate"
      else "old kernel/initramfs, installed GRUB components and guard",
      "root_stage_result_sha256": RESULT_HASH,
      "state": str(STATE),
      "recovery_backup": str(OLD_BACKUP),
      "limitations": "No reboot or hardware test; FAT power-loss atomicity is not guaranteed.",
    }
    write_new(
      STATE / f"{action}-result-{secrets.token_hex(12)}.json",
      (json.dumps(receipt, indent=2) + "\n").encode(),
    )
    print(json.dumps(receipt, indent=2))
  finally:
    os.close(lock)
    if os.path.lexists(LOCK) and (LOCK.lstat().st_dev, LOCK.lstat().st_ino) == (
      lock_info.st_dev,
      lock_info.st_ino,
    ):
      LOCK.unlink()


def main() -> int:
  try:
    require(len(sys.argv) == 2, "usage: frozen launcher activate or restore")
    perform(sys.argv[1])
    return 0
  except (OSError, ActivationFailure, UnicodeError, ValueError) as error:
    print(
      f"FAIL: {error}\nNo reboot was requested. Preserve backups and temporary files; use the reviewed restore path.",
      file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
  sys.exit(main())
