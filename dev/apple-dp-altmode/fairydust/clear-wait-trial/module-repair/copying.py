from __future__ import annotations

import ctypes
import hashlib
import json
import os
import re
import stat
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

RELEASE = "7.1.12-dev147-fairydust1"
BOOT_TARGET = Path(f"/boot/dev147-fairydust-{RELEASE}")
MODULE_TARGET = Path(f"/usr/lib/modules/{RELEASE}")
STATE_PARENT = Path("/var/lib/dev147-fairydust-stage")
STATE_TARGET = STATE_PARENT / RELEASE
PACKAGE_LOCK = Path("/var/lib/pacman/db.lck")
ACTIVE_PINS = (
  (
    Path("/boot/efi/m1n1/boot.bin"),
    "203ab7027536c8d16f373d02c1f6346a5c34cfe095a9dafd0cfe37d2b354090c",
  ),
  (
    Path("/etc/pacman.d/hooks/05-omarchy-m2-displayport-guard.hook"),
    "469820ad7cfd015a22cff979b0aa70d62e82dcc7cc05951dca92f40cd660f2bd",
  ),
)
BOOT_FILES = ("Image", "initramfs.img", "boot.bin", "config", "t8112-j413.dtb")
RECEIPTS = ("kernel-source-config.json", "boot-bundle.json", "initramfs.json")
PROTECTED = (
  Path("/boot"),
  Path("/etc/default/grub"),
  Path("/etc/grub.d"),
  ACTIVE_PINS[1][0],
  Path("/var/lib/omarchy/m2-displayport"),
  Path("/var/lib/pacman/local"),
)
BOOT_CONFIGURATION = (
  Path("/boot/grub/grub.cfg"),
  Path("/boot/grub/grubenv"),
  Path("/boot/grub/custom.cfg"),
  Path("/etc/default/grub"),
  Path("/etc/grub.d/custom.cfg"),
  Path("/etc/grub.d/40_custom"),
  Path("/etc/grub.d/41_custom"),
)
READ_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK
DIRECTORY_FLAGS = READ_FLAGS | os.O_DIRECTORY
DELIVERY_BYTE_LIMIT = 2_300_000_000
DELIVERY_ENTRY_LIMIT = 4096
DELIVERY_DEPTH_LIMIT = 32


class StageFailure(Exception):
  pass


@dataclass(frozen=True)
class Entry:
  path: str
  sha256: str


@dataclass(frozen=True)
class Manifest:
  entries: tuple[Entry, ...]


@dataclass
class CopyBudget:
  remaining_bytes: int = DELIVERY_BYTE_LIMIT
  remaining_entries: int = DELIVERY_ENTRY_LIMIT

  def reserve_file(self, size: int) -> None:
    require(0 <= size <= self.remaining_bytes, "delivery byte budget exceeded")
    self.remaining_bytes -= size

  def reserve_entry(self) -> None:
    require(self.remaining_entries > 0, "delivery entry budget exceeded")
    self.remaining_entries -= 1


def require(condition: bool, message: str) -> None:
  if not condition:
    raise StageFailure(message)


def safe_relative(value: str) -> bool:
  return (
    bool(re.fullmatch(r"[A-Za-z0-9_.+/-]+", value))
    and not value.startswith("/")
    and all(part not in ("", ".", "..") for part in value.split("/"))
  )


def open_directory(path: Path) -> int:
  require(path.is_absolute(), "directory must be absolute")
  descriptor = os.open("/", DIRECTORY_FLAGS)
  try:
    for component in path.parts[1:]:
      require(component not in ("", ".", ".."), "invalid directory component")
      child = os.open(component, DIRECTORY_FLAGS, dir_fd=descriptor)
      os.close(descriptor)
      descriptor = child
    return descriptor
  except (OSError, StageFailure):
    os.close(descriptor)
    raise


def read_regular(path: Path) -> bytes:
  parent = open_directory(path.parent)
  try:
    descriptor = os.open(path.name, READ_FLAGS, dir_fd=parent)
    with os.fdopen(descriptor, "rb") as stream:
      require(
        stat.S_ISREG(os.fstat(stream.fileno()).st_mode), f"not a regular file: {path}"
      )
      return stream.read()
  finally:
    os.close(parent)


def sha_file(path: Path) -> str:
  parent = open_directory(path.parent)
  try:
    descriptor = os.open(path.name, READ_FLAGS, dir_fd=parent)
    with os.fdopen(descriptor, "rb") as stream:
      require(
        stat.S_ISREG(os.fstat(stream.fileno()).st_mode), f"not a regular file: {path}"
      )
      return hashlib.file_digest(stream, "sha256").hexdigest()
  finally:
    os.close(parent)


def write_file(path: Path, content: bytes) -> None:
  with path.open("xb") as stream:
    stream.write(content)
    stream.flush()
    os.fsync(stream.fileno())


def parse_manifest(data: bytes) -> Manifest:
  entries: list[Entry] = []
  for line in data.decode("ascii").splitlines():
    match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
    require(match is not None, "invalid manifest line")
    if match is None:
      raise StageFailure("invalid manifest")
    digest, path = match.groups()
    require(safe_relative(path), "unsafe manifest path")
    entries.append(Entry(path, digest))
  paths = [entry.path for entry in entries]
  require(
    bool(paths) and len(paths) == len(set(paths)), "empty or duplicate manifest paths"
  )
  return Manifest(tuple(entries))


def copy_directory(
  source: int, destination: Path, budget: CopyBudget, depth: int = 0
) -> None:
  require(depth <= DELIVERY_DEPTH_LIMIT, "delivery depth budget exceeded")
  destination.mkdir(mode=0o700)
  names: list[str] = []
  with os.scandir(source) as entries:
    for entry in entries:
      budget.reserve_entry()
      names.append(entry.name)
  for name in sorted(names):
    require(safe_relative(name) and "/" not in name, "unsafe input filename")
    before = os.stat(name, dir_fd=source, follow_symlinks=False)
    target = destination / name
    if stat.S_ISDIR(before.st_mode):
      child = os.open(name, DIRECTORY_FLAGS, dir_fd=source)
      try:
        opened_directory = os.fstat(child)
        require(
          (opened_directory.st_dev, opened_directory.st_ino)
          == (before.st_dev, before.st_ino),
          "input directory changed during copy",
        )
        copy_directory(child, target, budget, depth + 1)
      finally:
        os.close(child)
    else:
      require(
        stat.S_ISREG(before.st_mode) and before.st_nlink == 1,
        "input contains a link or special file",
      )
      descriptor = os.open(name, READ_FLAGS, dir_fd=source)
      with os.fdopen(descriptor, "rb") as incoming:
        opened = os.fstat(incoming.fileno())
        require(
          (opened.st_dev, opened.st_ino, opened.st_nlink)
          == (before.st_dev, before.st_ino, 1),
          "input changed before copy",
        )
        budget.reserve_file(opened.st_size)
        remaining = opened.st_size
        with target.open("xb") as outgoing:
          while remaining:
            chunk = incoming.read(min(1048576, remaining))
            require(bool(chunk), "input ended early during copy")
            outgoing.write(chunk)
            remaining -= len(chunk)
          require(not incoming.read(1), "input grew during copy")
          outgoing.flush()
          os.fsync(outgoing.fileno())
        after = os.fstat(incoming.fileno())
        require(
          (opened.st_size, opened.st_mtime_ns, opened.st_ctime_ns)
          == (after.st_size, after.st_mtime_ns, after.st_ctime_ns),
          "input changed during copy",
        )
      target.chmod(0o600)


def files_in(root: Path) -> set[str]:
  files: set[str] = set()
  for path in root.rglob("*"):
    info = path.lstat()
    require(
      info.st_uid == 0 and not (info.st_mode & 0o022),
      "copied artifact is not root protected",
    )
    require(
      stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode),
      "copied artifact contains a special file",
    )
    if stat.S_ISREG(info.st_mode):
      require(info.st_nlink == 1, "copied artifact contains a hardlink")
      files.add(path.relative_to(root).as_posix())
  return files


def verify_manifest(
  root: Path, manifest: Manifest, excluded: set[str] | None = None
) -> None:
  require(
    files_in(root) - (excluded or set()) == {entry.path for entry in manifest.entries},
    "manifest inventory mismatch",
  )
  for entry in manifest.entries:
    require(
      sha_file(root / entry.path) == entry.sha256,
      f"artifact hash mismatch: {entry.path}",
    )


def verify_delivery(root: Path, expected_digest: str) -> Manifest:
  data = read_regular(root / "SHA256SUMS")
  require(
    hashlib.sha256(data).hexdigest() == expected_digest, "frozen manifest hash mismatch"
  )
  manifest = parse_manifest(data)
  paths = {entry.path for entry in manifest.entries}
  mandatory = (
    set(BOOT_FILES) | {f"receipts/{name}" for name in RECEIPTS} | {"modules.sha256"}
  )
  require(mandatory <= paths, "mandatory delivery artifact missing")
  module_prefix = f"root/lib/modules/{RELEASE}/"
  require(
    all(
      path in mandatory or path.startswith(("receipts/", module_prefix))
      for path in paths
    ),
    "unexpected delivery path",
  )
  verify_manifest(root, manifest, {"SHA256SUMS"})
  modules = parse_manifest(read_regular(root / "modules.sha256"))
  require(
    all(entry.path.startswith(f"lib/modules/{RELEASE}/") for entry in modules.entries),
    "unexpected module release",
  )
  require(
    any(entry.path.endswith(".ko") for entry in modules.entries), "empty module tree"
  )
  verify_manifest(root / "root", modules)
  return manifest


def secure_parent(path: Path) -> None:
  descriptor = open_directory(path)
  try:
    info = os.fstat(descriptor)
    require(
      info.st_uid == 0 and not (info.st_mode & 0o022),
      f"unprotected target parent: {path}",
    )
  finally:
    os.close(descriptor)


def check_absent(path: Path) -> None:
  require(not os.path.lexists(path), f"target already exists: {path}")


def identity(path: Path) -> str:
  try:
    info = path.lstat()
  except FileNotFoundError:
    return "absent"
  metadata = f"{stat.S_IMODE(info.st_mode):o}:{info.st_uid}:{info.st_gid}:"
  if stat.S_ISREG(info.st_mode):
    return metadata + "file:" + sha_file(path)
  if stat.S_ISLNK(info.st_mode):
    return metadata + "symlink:" + os.readlink(path)
  require(stat.S_ISDIR(info.st_mode), f"unexpected protected file type: {path}")
  return metadata + "directory"


def protected_snapshot() -> dict[str, str]:
  values: dict[str, str] = {}
  for root in PROTECTED:
    values[str(root)] = identity(root)
    if root.is_dir() and not root.is_symlink():
      for path in sorted(root.rglob("*")):
        if (
          path == BOOT_TARGET
          or BOOT_TARGET in path.parents
          or path.name.startswith(".dev147-stage-")
          or any(parent.name.startswith(".dev147-stage-") for parent in path.parents)
        ):
          continue
        values[str(path)] = identity(path)
  return values


def pin_active() -> None:
  for path, expected in ACTIVE_PINS:
    require(sha_file(path) == expected, f"active input drift: {path}")


def check_lock(expected: os.stat_result) -> None:
  current = PACKAGE_LOCK.lstat()
  require(
    (current.st_dev, current.st_ino, current.st_uid, current.st_nlink)
    == (expected.st_dev, expected.st_ino, 0, 1),
    "package lock changed during staging",
  )


def publish(source: Path, destination: Path) -> None:
  library = ctypes.CDLL(None, use_errno=True)
  rename = library.renameat2
  rename.argtypes = [
    ctypes.c_int,
    ctypes.c_char_p,
    ctypes.c_int,
    ctypes.c_char_p,
    ctypes.c_uint,
  ]
  rename.restype = ctypes.c_int
  if rename(-100, os.fsencode(source), -100, os.fsencode(destination), 1) != 0:
    code = ctypes.get_errno()
    raise OSError(code, os.strerror(code), str(destination))
  parent = open_directory(destination.parent)
  try:
    os.fsync(parent)
  finally:
    os.close(parent)


def make_public(root: Path) -> None:
  for path in root.rglob("*"):
    path.chmod(0o755 if path.is_dir() else 0o644)
  root.chmod(0o755)


def stage(source: Path, manifest_digest: str) -> None:
  require(os.geteuid() == 0, "run the reviewed entrypoint as root")
  require(
    bool(re.fullmatch(r"[0-9a-f]{64}", manifest_digest)),
    "invalid frozen manifest digest",
  )
  os.umask(0o077)
  for path in (
    BOOT_TARGET.parent,
    MODULE_TARGET.parent,
    Path("/var/lib/pacman"),
    Path("/var/lib"),
  ):
    secure_parent(path)
  for path in (BOOT_TARGET, MODULE_TARGET, STATE_TARGET):
    check_absent(path)
  pin_active()
  lock = os.open(
    PACKAGE_LOCK, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
  )
  lock_identity = os.fstat(lock)
  try:
    pin_active()
    before = protected_snapshot()
    boot_configuration = {
      str(path): read_regular(path).decode("utf-8")
      for path in BOOT_CONFIGURATION
      if path.exists()
    }
    STATE_PARENT.mkdir(mode=0o700, exist_ok=True)
    secure_parent(STATE_PARENT)
    STATE_TARGET.mkdir(mode=0o700)
    copied = STATE_TARGET / "input"
    descriptor = open_directory(source)
    try:
      copy_directory(descriptor, copied, CopyBudget())
    finally:
      os.close(descriptor)
    manifest = verify_delivery(copied, manifest_digest)
    write_file(
      STATE_TARGET / "protected-before.json",
      (json.dumps(before, indent=2) + "\n").encode(),
    )
    write_file(
      STATE_TARGET / "boot-configuration.json",
      (json.dumps(boot_configuration, indent=2) + "\n").encode(),
    )
    require(protected_snapshot() == before, "protected input changed during staging")
    boot_pending = BOOT_TARGET.parent / f".dev147-stage-{RELEASE}-{os.getpid()}"
    module_pending = MODULE_TARGET.parent / f".dev147-stage-{RELEASE}-{os.getpid()}"
    boot_pending.mkdir(mode=0o700)
    for name in (*BOOT_FILES, "SHA256SUMS", "modules.sha256"):
      write_file(boot_pending / name, read_regular(copied / name))
    descriptor = open_directory(copied / "receipts")
    try:
      copy_directory(descriptor, boot_pending / "receipts", CopyBudget())
    finally:
      os.close(descriptor)
    descriptor = open_directory(copied / "root/lib/modules" / RELEASE)
    try:
      copy_directory(descriptor, module_pending, CopyBudget())
    finally:
      os.close(descriptor)
    for entry in manifest.entries:
      if entry.path.startswith(f"root/lib/modules/{RELEASE}/"):
        path = module_pending / PurePosixPath(entry.path).relative_to(
          f"root/lib/modules/{RELEASE}"
        )
      elif (
        entry.path == "modules.sha256"
        or entry.path in BOOT_FILES
        or entry.path.startswith("receipts/")
      ):
        path = boot_pending / entry.path
      else:
        continue
      require(sha_file(path) == entry.sha256, "publication copy mismatch")
    require(
      protected_snapshot() == before, "protected input changed before publication"
    )
    pin_active()
    check_lock(lock_identity)
    for path in (BOOT_TARGET, MODULE_TARGET):
      check_absent(path)
    make_public(boot_pending)
    make_public(module_pending)
    publish(module_pending, MODULE_TARGET)
    publish(boot_pending, BOOT_TARGET)
    check_lock(lock_identity)
    require(
      protected_snapshot() == before,
      "protected input changed after publication; candidate remains unselected",
    )
    report = {
      "status": "STAGED_UNSELECTED",
      "release": RELEASE,
      "manifest_sha256": manifest_digest,
      "boot_directory": str(BOOT_TARGET),
      "module_directory": str(MODULE_TARGET),
      "protected_state": str(STATE_TARGET),
      "protected_identities": before,
      "boot_configuration": boot_configuration,
      "activation": "not performed; paired m1n1 and GRUB activation requires separate review",
    }
    write_file(
      STATE_TARGET / "result.json", (json.dumps(report, indent=2) + "\n").encode()
    )
    print(json.dumps(report, indent=2))
  finally:
    os.close(lock)
    try:
      current = PACKAGE_LOCK.lstat()
      if (current.st_dev, current.st_ino) == (
        lock_identity.st_dev,
        lock_identity.st_ino,
      ):
        PACKAGE_LOCK.unlink()
    except FileNotFoundError:
      pass


def main(arguments: list[str]) -> int:
  try:
    require(
      len(arguments) == 2, "usage: stage.py DELIVERY_DIRECTORY FROZEN_MANIFEST_SHA256"
    )
    stage(Path(arguments[0]), arguments[1])
    return 0
  except (OSError, StageFailure, UnicodeError) as error:
    print(f"FAIL: {error}", file=sys.stderr)
    print(
      f"New staging paths may remain at {STATE_TARGET}, {BOOT_TARGET}, or {MODULE_TARGET}; nothing was selected. Preserve evidence before any reviewed retry.",
      file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
  sys.exit(main(sys.argv[1:]))
