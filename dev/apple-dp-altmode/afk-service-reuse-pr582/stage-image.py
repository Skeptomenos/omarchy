from __future__ import annotations

import hashlib
import json
import os
import signal
import stat
import subprocess
import sys
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterator


EXPECTED_KERNEL = "7.1.6-1-1-ARCH"
EXPECTED_PACKAGES = "\n".join(
  (
    "linux-asahi 7.1.6.asahi1-1",
    "m1n1 1.6.1-1",
    "uboot-asahi 2026.04.asahi2-1",
    "mesa 26.1.8-1",
    "mkinitcpio 41.1-1",
    "openssl 3.6.4-1",
    "coreutils 9.11-2",
    "kmod 34.2-1",
    "avd-fw 0.1-1",
  )
)
EXPECTED_MOUNT = "ext4 e24cf117-3c89-4392-a3b8-def187becda8 /"
SOURCE = Path(
  "/home/david/o/.dev147-stage/afk-pr582-combined-offline-20260904.hdfiJZaOUn/"
  "image-build/initramfs-linux-asahi-m2-displayport-afk-pr582.img"
)
SOURCE_SHA256 = "3207dd0ff346765f4514b34a137c1c7456c459082463355e51047216dedc2867"
SOURCE_SIZE = 21_599_177
DESTINATION = Path("/boot/initramfs-linux-asahi-m2-displayport-afk-pr582.img")
RESERVE_BYTES = 16_777_216
ACTIVE_STATE_RELATIVE = "var/lib/omarchy/m2-displayport/active/state.env"
EXPECTED_STATE_FIELDS = (
  ("format", "2"),
  ("timestamp", "20260902T085339Z"),
  ("kernel_release", "7.1.6-1-1-ARCH"),
  ("previous_boot_sha256", "203ab7027536c8d16f373d02c1f6346a5c34cfe095a9dafd0cfe37d2b354090c"),
  ("previous_boot_size", "6205569"),
  ("previous_boot_mode", "755"),
  ("candidate_boot_sha256", "203ab7027536c8d16f373d02c1f6346a5c34cfe095a9dafd0cfe37d2b354090c"),
  ("candidate_boot_size", "6205569"),
  ("candidate_image_sha256", "a93dd0c1b3a6c4d81bf76f2f43c7c7a2b8b7e1e0306bc487de018667f9c8c196"),
  ("candidate_image_size", "19184210"),
  ("hook_sha256", "469820ad7cfd015a22cff979b0aa70d62e82dcc7cc05951dca92f40cd660f2bd"),
  ("active_boot_changed", "0"),
  ("rollback_sha256", "3357ac75cd7a7d330d2c751bf819e342758491d71e3b34234afacf2f83264e19"),
  ("rollback_size", "42138"),
  ("efi_backup_name", "boot.bin.pre-omarchy-m2-displayport-20260902T085339Z"),
)
PROTECTED_PINS = (
  (
    Path("/boot/efi/m1n1/boot.bin"),
    "203ab7027536c8d16f373d02c1f6346a5c34cfe095a9dafd0cfe37d2b354090c",
    6_205_569,
    0,
    0,
    0o755,
  ),
  (
    Path("/boot/initramfs-linux-asahi.img"),
    "c4cffb397cfbd0158d3b1423c0512e1622053d53e0c75a17f5312986276324e0",
    18_865_707,
    0,
    0,
    0o600,
  ),
  (
    Path("/boot/grub/grub.cfg"),
    "57d839b9bc7d3488402a8cf7c9e45328dc0097731fc395b0514c467d06b7a327",
    4_129,
    0,
    0,
    0o600,
  ),
  (
    Path("/boot/initramfs-linux-asahi-m2-displayport.img"),
    "a93dd0c1b3a6c4d81bf76f2f43c7c7a2b8b7e1e0306bc487de018667f9c8c196",
    19_184_210,
    0,
    0,
    0o600,
  ),
  (
    Path("/boot/initramfs-linux-asahi-m2-displayport-afk-reuse.img"),
    "ebd383c21a35d6b0eff22ffe6f144ea7790c31d7cf058a1c3afa5e39c2375acd",
    21_598_988,
    0,
    0,
    0o600,
  ),
  (
    Path("/etc/pacman.d/hooks/05-omarchy-m2-displayport-guard.hook"),
    "469820ad7cfd015a22cff979b0aa70d62e82dcc7cc05951dca92f40cd660f2bd",
    303,
    0,
    0,
    0o644,
  ),
  (
    Path("/var/lib/omarchy/m2-displayport/active/rollback.sh"),
    "3357ac75cd7a7d330d2c751bf819e342758491d71e3b34234afacf2f83264e19",
    42_138,
    0,
    0,
    0o700,
  ),
  (
    Path("/var/lib/omarchy/m2-displayport/active/pre-install-boot.bin"),
    "203ab7027536c8d16f373d02c1f6346a5c34cfe095a9dafd0cfe37d2b354090c",
    6_205_569,
    0,
    0,
    0o600,
  ),
  (
    Path("/var/lib/omarchy/m2-displayport/active/candidate-boot.bin"),
    "203ab7027536c8d16f373d02c1f6346a5c34cfe095a9dafd0cfe37d2b354090c",
    6_205_569,
    0,
    0,
    0o600,
  ),
  (
    Path("/var/lib/omarchy/m2-displayport/active/recovery.txt"),
    "5fda712442fd860bb8c31d8441e350c66e1ecfb1c4054206f638119106dead78",
    949,
    0,
    0,
    0o600,
  ),
  (
    Path("/var/lib/omarchy/m2-displayport/active/bundle.env"),
    "f967202c3da1f31480b52c51e46ca2679e302f64596f9917edc56d0041449fb7",
    448,
    0,
    0,
    0o600,
  ),
  (
    Path("/var/lib/omarchy/m2-displayport/active/RESULT"),
    "0ebf65c7984364f0999b4b54018b582a0da08a145e4d88a228ce2438856e7b06",
    7,
    0,
    0,
    0o600,
  ),
  (
    Path(
      "/boot/efi/m1n1/"
      "boot.bin.pre-omarchy-m2-displayport-20260902T085339Z"
    ),
    "203ab7027536c8d16f373d02c1f6346a5c34cfe095a9dafd0cfe37d2b354090c",
    6_205_569,
    0,
    0,
    0o755,
  ),
  (
    Path(
      "/boot/efi/m1n1/"
      "RECOVERY-OMARCHY-M2-DISPLAYPORT-20260902T085339Z.txt"
    ),
    "5fda712442fd860bb8c31d8441e350c66e1ecfb1c4054206f638119106dead78",
    949,
    0,
    0,
    0o755,
  ),
)


class StageFailure(RuntimeError):
  pass


class StageInterrupted(StageFailure):
  pass


Hook = Callable[[str], None]
HANDLED_SIGNALS = frozenset((signal.SIGHUP, signal.SIGINT, signal.SIGTERM))


@dataclass(frozen=True)
class HostFacts:
  kernel_release: str
  package_output: str
  mount_output: str


FactsProvider = Callable[[], HostFacts]


@dataclass(frozen=True)
class StageConfig:
  source: Path
  source_sha256: str
  source_size: int
  destination: Path
  transaction: Path
  system_root: Path
  trusted_root: Path
  root_owner: int
  root_group: int
  source_owner: int
  source_group: int
  protected_pins: tuple[tuple[Path, str, int, int, int, int], ...]
  kernel_release: str
  package_output: str
  mount_output: str
  copy_chunk_size: int
  reserve_bytes: int


@dataclass(frozen=True)
class FileIdentity:
  device: int
  inode: int
  links: int
  owner: int
  group: int
  mode: int
  size: int
  modified_ns: int
  changed_ns: int


@dataclass(frozen=True)
class DirectoryIdentity:
  device: int
  inode: int
  owner: int
  group: int
  mode: int


@dataclass(frozen=True)
class PinRecord:
  path: str
  sha256: str
  size: int
  identity: FileIdentity


def _identity(metadata: os.stat_result) -> FileIdentity:
  return FileIdentity(
    device=metadata.st_dev,
    inode=metadata.st_ino,
    links=metadata.st_nlink,
    owner=metadata.st_uid,
    group=metadata.st_gid,
    mode=stat.S_IMODE(metadata.st_mode),
    size=metadata.st_size,
    modified_ns=metadata.st_mtime_ns,
    changed_ns=metadata.st_ctime_ns,
  )


def _directory_identity(metadata: os.stat_result) -> DirectoryIdentity:
  return DirectoryIdentity(
    device=metadata.st_dev,
    inode=metadata.st_ino,
    owner=metadata.st_uid,
    group=metadata.st_gid,
    mode=stat.S_IMODE(metadata.st_mode),
  )


@contextmanager
def _blocked_signals() -> Iterator[None]:
  previous = signal.pthread_sigmask(signal.SIG_BLOCK, HANDLED_SIGNALS)
  try:
    yield
  finally:
    signal.pthread_sigmask(signal.SIG_SETMASK, previous)


def _validate_path(path: Path) -> tuple[str, ...]:
  raw = str(path)
  if not path.is_absolute() or "\n" in raw or "\r" in raw or "\\" in raw:
    raise StageFailure(f"invalid absolute path: {raw}")
  parts = path.parts
  if not parts or parts[0] != "/" or any(part in ("", ".", "..") for part in parts[1:]):
    raise StageFailure(f"noncanonical path: {raw}")
  return parts[1:]


def _open_directory(path: Path, owner: int | None = None, mode: int | None = None) -> int:
  parts = _validate_path(path)
  flags = os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW
  current = os.open("/", flags)
  try:
    metadata = os.fstat(current)
    if stat.S_IMODE(metadata.st_mode) & 0o022:
      raise StageFailure("group/world-writable directory: /")
    for part in parts:
      try:
        following = os.open(part, flags, dir_fd=current)
      except OSError as error:
        raise StageFailure(f"symlink or inaccessible directory: {path}") from error
      os.close(current)
      current = following
      metadata = os.fstat(current)
      if not stat.S_ISDIR(metadata.st_mode):
        raise StageFailure(f"not a directory: {path}")
      if stat.S_IMODE(metadata.st_mode) & 0o022:
        raise StageFailure(f"group/world-writable directory: {path}")
    metadata = os.fstat(current)
    if owner is not None and metadata.st_uid != owner:
      raise StageFailure(f"directory owner mismatch: {path}")
    if mode is not None and stat.S_IMODE(metadata.st_mode) != mode:
      raise StageFailure(f"directory mode mismatch: {path}")
    return current
  except Exception:
    os.close(current)
    raise


def _open_trusted_directory(
  path: Path,
  trusted_root: Path,
  owner: int,
  mode: int | None = None,
) -> int:
  _validate_path(path)
  _validate_path(trusted_root)
  try:
    relative = path.relative_to(trusted_root)
  except ValueError as error:
    raise StageFailure(f"path is outside trusted root: {path}") from error
  current = _open_directory(trusted_root, owner=owner)
  try:
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW
    for part in relative.parts:
      try:
        following = os.open(part, flags, dir_fd=current)
      except OSError as error:
        raise StageFailure(f"symlink or inaccessible trusted directory: {path}") from error
      os.close(current)
      current = following
      metadata = os.fstat(current)
      if not stat.S_ISDIR(metadata.st_mode):
        raise StageFailure(f"not a trusted directory: {path}")
      if metadata.st_uid != owner:
        raise StageFailure(f"trusted directory owner mismatch: {path}")
      if stat.S_IMODE(metadata.st_mode) & 0o022:
        raise StageFailure(f"group/world-writable trusted directory: {path}")
    metadata = os.fstat(current)
    if mode is not None and stat.S_IMODE(metadata.st_mode) != mode:
      raise StageFailure(f"trusted directory mode mismatch: {path}")
    return current
  except Exception:
    os.close(current)
    raise


def _open_regular_from_parent(path: Path, parent: int) -> tuple[int, int, FileIdentity]:
  try:
    try:
      descriptor = os.open(
        path.name,
        os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW,
        dir_fd=parent,
      )
    except OSError as error:
      raise StageFailure(f"symlink or inaccessible file: {path}") from error
    metadata = os.fstat(descriptor)
    if not stat.S_ISREG(metadata.st_mode):
      os.close(descriptor)
      raise StageFailure(f"not a regular file: {path}")
    if metadata.st_nlink != 1:
      os.close(descriptor)
      raise StageFailure(f"file is not singly linked: {path}")
    return descriptor, parent, _identity(metadata)
  except Exception:
    os.close(parent)
    raise


def _open_regular(path: Path) -> tuple[int, int, FileIdentity]:
  return _open_regular_from_parent(path, _open_directory(path.parent))


def _open_trusted_regular(
  path: Path,
  trusted_root: Path,
  owner: int,
) -> tuple[int, int, FileIdentity]:
  parent = _open_trusted_directory(path.parent, trusted_root, owner)
  return _open_regular_from_parent(path, parent)


def _hash_descriptor(descriptor: int, chunk_size: int = 1_048_576) -> tuple[str, int]:
  os.lseek(descriptor, 0, os.SEEK_SET)
  hasher = hashlib.sha256()
  size = 0
  while True:
    chunk = os.read(descriptor, chunk_size)
    if not chunk:
      break
    hasher.update(chunk)
    size += len(chunk)
  os.lseek(descriptor, 0, os.SEEK_SET)
  return hasher.hexdigest(), size


def _read_system(config: StageConfig, relative: str) -> bytes:
  descriptor, parent, _ = _open_trusted_regular(
    config.system_root / relative,
    config.trusted_root,
    config.root_owner,
  )
  try:
    result = bytearray()
    while True:
      chunk = os.read(descriptor, 4096)
      if not chunk:
        return bytes(result)
      result.extend(chunk)
      if len(result) > 4096:
        raise StageFailure(f"system input too large: {relative}")
  finally:
    os.close(descriptor)
    os.close(parent)


def _require_absent(
  path: Path,
  label: str,
  trusted_root: Path,
  owner: int,
) -> None:
  parent = _open_trusted_directory(path.parent, trusted_root, owner)
  try:
    try:
      os.stat(path.name, dir_fd=parent, follow_symlinks=False)
    except FileNotFoundError:
      return
    raise StageFailure(f"{label} already exists")
  finally:
    os.close(parent)


def _write_all(descriptor: int, data: bytes) -> None:
  offset = 0
  while offset < len(data):
    written = os.write(descriptor, data[offset:])
    if written <= 0:
      raise StageFailure("short write")
    offset += written


def _write_new(directory: int, name: str, data: bytes, mode: int = 0o600) -> None:
  try:
    descriptor = os.open(
      name,
      os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
      mode,
      dir_fd=directory,
    )
  except FileExistsError as error:
    raise StageFailure(f"transaction record already exists: {name}") from error
  try:
    _write_all(descriptor, data)
    os.fchmod(descriptor, mode)
    os.fsync(descriptor)
  finally:
    os.close(descriptor)


def _write_json(directory: int, name: str, value: object) -> None:
  data = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
  _write_new(directory, name, data)


def _verify_pins(
  pins: tuple[tuple[Path, str, int, int, int, int], ...],
  hook: Hook,
  trusted_root: Path,
  owner: int,
) -> tuple[PinRecord, ...]:
  records: list[PinRecord] = []
  seen: set[Path] = set()
  for path, expected, expected_size, expected_owner, expected_group, expected_mode in pins:
    if (
      path in seen
      or not re_full_sha256(expected)
      or expected_size <= 0
      or expected_owner < 0
      or expected_group < 0
      or expected_mode <= 0
      or expected_mode > 0o7777
      or expected_mode & 0o022
    ):
      raise StageFailure("invalid protected pin contract")
    seen.add(path)
    descriptor, parent, identity = _open_trusted_regular(path, trusted_root, owner)
    if (
      identity.owner != expected_owner
      or identity.group != expected_group
      or identity.mode != expected_mode
      or identity.size != expected_size
    ):
      os.close(descriptor)
      os.close(parent)
      raise StageFailure(f"protected pin metadata mismatch: {path}")
    try:
      os.lseek(descriptor, 0, os.SEEK_SET)
      hasher = hashlib.sha256()
      size = 0
      while True:
        chunk = os.read(descriptor, 1_048_576)
        if not chunk:
          break
        hasher.update(chunk)
        size += len(chunk)
        hook("pin_hash_chunk")
      actual = hasher.hexdigest()
      if _identity(os.fstat(descriptor)) != identity:
        raise StageFailure(f"protected pin identity changed: {path}")
      path_metadata = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
      if _identity(path_metadata) != identity:
        raise StageFailure(f"protected pin path changed: {path}")
      fresh_descriptor, fresh_parent, fresh_identity = _open_trusted_regular(
        path,
        trusted_root,
        owner,
      )
      try:
        fresh_path_metadata = os.stat(
          path.name,
          dir_fd=fresh_parent,
          follow_symlinks=False,
        )
        if fresh_identity != identity or _identity(fresh_path_metadata) != identity:
          raise StageFailure(f"protected pin canonical path changed: {path}")
      finally:
        os.close(fresh_descriptor)
        os.close(fresh_parent)
    finally:
      os.close(descriptor)
      os.close(parent)
    if actual != expected or size != expected_size:
      raise StageFailure(f"protected pin hash or size mismatch: {path}")
    records.append(PinRecord(str(path), actual, size, identity))
  if not records:
    raise StageFailure("protected pin set is empty")
  return tuple(records)


def _verify_active_state(config: StageConfig) -> PinRecord:
  path = _system_path(config, ACTIVE_STATE_RELATIVE)
  descriptor, parent, identity = _open_trusted_regular(
    path,
    config.trusted_root,
    config.root_owner,
  )
  try:
    if (
      identity.owner != config.root_owner
      or identity.group != config.root_group
      or identity.mode != 0o600
      or identity.size <= 0
      or identity.size > 4096
    ):
      raise StageFailure("active format-2 state metadata mismatch")
    data = bytearray()
    while True:
      chunk = os.read(descriptor, 4096)
      if not chunk:
        break
      data.extend(chunk)
      if len(data) > 4096:
        raise StageFailure("active format-2 state is too large")
    if not data.endswith(b"\n"):
      raise StageFailure("active format-2 state is not line complete")
    try:
      lines = bytes(data).decode("ascii").splitlines()
    except UnicodeDecodeError as error:
      raise StageFailure("active format-2 state is not ASCII") from error
    fields: list[tuple[str, str]] = []
    for line in lines:
      if line.count("=") != 1:
        raise StageFailure("active format-2 state field is invalid")
      key, value = line.split("=", 1)
      fields.append((key, value))
    if len(fields) != 16 or len({key for key, _ in fields}) != 16:
      raise StageFailure("active format-2 state field set is invalid")
    if fields[11][0] != "hook_parent_created" or fields[11][1] not in ("0", "1"):
      raise StageFailure("active format-2 hook state is invalid")
    expected_fields = (
      *EXPECTED_STATE_FIELDS[:11],
      ("hook_parent_created", fields[11][1]),
      *EXPECTED_STATE_FIELDS[11:],
    )
    if tuple(fields) != expected_fields:
      raise StageFailure("active format-2 state differs from the accepted release")
    current = _identity(os.fstat(descriptor))
    path_metadata = _identity(os.stat(path.name, dir_fd=parent, follow_symlinks=False))
    if current != identity or path_metadata != identity:
      raise StageFailure("active format-2 state identity changed")
    fresh_descriptor, fresh_parent, fresh_identity = _open_trusted_regular(
      path,
      config.trusted_root,
      config.root_owner,
    )
    try:
      fresh_path = _identity(
        os.stat(path.name, dir_fd=fresh_parent, follow_symlinks=False)
      )
      if fresh_identity != identity or fresh_path != identity:
        raise StageFailure("active format-2 state canonical path changed")
    finally:
      os.close(fresh_descriptor)
      os.close(fresh_parent)
    return PinRecord(
      str(path),
      hashlib.sha256(data).hexdigest(),
      len(data),
      identity,
    )
  finally:
    os.close(descriptor)
    os.close(parent)


def re_full_sha256(value: str) -> bool:
  return len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def _system_path(config: StageConfig, relative: str) -> Path:
  return config.system_root / relative


def _preflight(
  config: StageConfig,
  facts_provider: FactsProvider,
  hook: Hook,
) -> tuple[PinRecord, ...]:
  facts = facts_provider()
  if facts.kernel_release != config.kernel_release:
    raise StageFailure("running kernel changed")
  if facts.package_output != config.package_output:
    raise StageFailure("installed package versions changed")
  if facts.mount_output != config.mount_output:
    raise StageFailure("boot mount identity changed")
  if not re_full_sha256(config.source_sha256) or config.source_size <= 0:
    raise StageFailure("candidate input contract is invalid")
  if config.copy_chunk_size <= 0 or config.reserve_bytes < 0:
    raise StageFailure("copy contract is invalid")
  _require_absent(
    _system_path(config, "var/lib/pacman/db.lck"),
    "package transaction",
    config.trusted_root,
    config.root_owner,
  )
  _require_absent(
    _system_path(config, "etc/default/update-m1n1"),
    "persistent boot override",
    config.trusted_root,
    config.root_owner,
  )
  compatible = _read_system(config, "sys/firmware/devicetree/base/compatible").split(b"\0")
  if b"apple,j413" not in compatible or b"apple,t8112" not in compatible:
    raise StageFailure("platform identity changed")
  status = _read_system(
    config,
    "sys/firmware/devicetree/base/soc/dcp@271c00000/status",
  ).rstrip(b"\0")
  alias = _read_system(
    config,
    "sys/firmware/devicetree/base/aliases/dcpext",
  ).rstrip(b"\0")
  if status != b"okay" or alias != b"/soc/dcp@271c00000":
    raise StageFailure("external DCP route changed")
  dcp_phandle = _read_system(
    config,
    "sys/firmware/devicetree/base/soc/dcp@271c00000/phandle",
  )
  port_phandle = _read_system(
    config,
    "sys/firmware/devicetree/base/soc/i2c@235010000/usb-pd@3f/connector/displayport",
  )
  if dcp_phandle != port_phandle:
    raise StageFailure("front display route changed")
  _require_absent(
    _system_path(
      config,
      "sys/firmware/devicetree/base/soc/i2c@235010000/usb-pd@38/connector/displayport",
    ),
    "rear display route",
    config.trusted_root,
    config.root_owner,
  )
  capacity_raw = _read_system(
    config,
    "sys/devices/platform/soc/23e400000.smc/macsmc-power/power_supply/"
    "macsmc-battery/capacity",
  ).strip()
  try:
    capacity = int(capacity_raw)
  except ValueError as error:
    raise StageFailure("battery capacity is invalid") from error
  if capacity <= 50 or capacity > 100:
    raise StageFailure("battery must be above 50 percent")
  external_power = _read_system(
    config,
    "sys/devices/platform/soc/23e400000.smc/macsmc-power/power_supply/"
    "macsmc-ac/online",
  ).strip()
  if external_power != b"1":
    raise StageFailure("external power is required")
  pins = _verify_pins(
    config.protected_pins,
    hook,
    config.trusted_root,
    config.root_owner,
  )
  return (*pins, _verify_active_state(config))


def _source_descriptor(config: StageConfig) -> tuple[int, int, FileIdentity]:
  descriptor, parent, identity = _open_regular(config.source)
  if identity.owner != config.source_owner or identity.group != config.source_group:
    os.close(descriptor)
    os.close(parent)
    raise StageFailure("candidate ownership changed")
  if identity.mode != 0o600 or identity.size != config.source_size:
    os.close(descriptor)
    os.close(parent)
    raise StageFailure("candidate mode or size changed")
  actual, size = _hash_descriptor(descriptor)
  current = _identity(os.fstat(descriptor))
  path_metadata = os.stat(config.source.name, dir_fd=parent, follow_symlinks=False)
  if current != identity or _identity(path_metadata) != identity:
    os.close(descriptor)
    os.close(parent)
    raise StageFailure("source identity changed during verification")
  if actual != config.source_sha256 or size != config.source_size:
    os.close(descriptor)
    os.close(parent)
    raise StageFailure("candidate hash or size changed")
  return descriptor, parent, identity


def _same_source_path(config: StageConfig, expected: FileIdentity) -> None:
  descriptor, parent, identity = _open_regular(config.source)
  try:
    if identity != expected:
      raise StageFailure("source identity changed during staging")
  finally:
    os.close(descriptor)
    os.close(parent)


def _unlink_if_present(directory: int, name: str) -> None:
  try:
    os.unlink(name, dir_fd=directory)
  except FileNotFoundError:
    return


def _restore_incomplete(directory: int) -> None:
  try:
    os.stat("INCOMPLETE", dir_fd=directory, follow_symlinks=False)
    return
  except FileNotFoundError:
    pass
  try:
    _write_new(
      directory,
      "INCOMPLETE",
      b"INCOMPLETE staging. Retain this transaction. Do not reboot.\n",
    )
  except StageFailure:
    return


def _record_failure(directory: int, error: Exception) -> None:
  try:
    _write_json(
      directory,
      "failure.json",
      {"status": "INCOMPLETE", "error": type(error).__name__, "message": str(error)},
    )
    os.fsync(directory)
  except (OSError, StageFailure):
    return


def _published_identity(directory: int, name: str) -> FileIdentity | None:
  try:
    metadata = os.stat(name, dir_fd=directory, follow_symlinks=False)
  except FileNotFoundError:
    return None
  return _identity(metadata)


def _require_directory_identity(
  path: Path,
  expected: DirectoryIdentity,
  trusted_root: Path,
) -> None:
  descriptor = _open_trusted_directory(path, trusted_root, expected.owner)
  try:
    if _directory_identity(os.fstat(descriptor)) != expected:
      raise StageFailure(f"directory identity changed: {path}")
  finally:
    os.close(descriptor)


def _verify_destination(
  parent: int,
  name: str,
  expected: FileIdentity,
  expected_hash: str,
  expected_size: int,
  owner: int,
  group: int,
) -> FileIdentity:
  try:
    descriptor = os.open(
      name,
      os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW,
      dir_fd=parent,
    )
  except OSError as error:
    raise StageFailure("published destination is inaccessible or a symlink") from error
  try:
    before = _identity(os.fstat(descriptor))
    if before.device != expected.device or before.inode != expected.inode:
      raise StageFailure("published destination inode changed")
    if before.links != 1 or before.owner != owner or before.group != group:
      raise StageFailure("published destination metadata changed")
    if before.mode != 0o600 or before.size != expected_size:
      raise StageFailure("published destination mode or size changed")
    actual_hash, actual_size = _hash_descriptor(descriptor)
    after = _identity(os.fstat(descriptor))
    path_after = _published_identity(parent, name)
    if after != before or path_after != before:
      raise StageFailure("published destination identity changed during hashing")
    if actual_hash != expected_hash or actual_size != expected_size:
      raise StageFailure("published destination hash or size mismatch")
    os.fsync(descriptor)
    return after
  finally:
    os.close(descriptor)


def _cleanup_failed_publication(
  transaction: int,
  destination_parent: int,
  temporary_name: str,
  destination_name: str,
  published: FileIdentity | None,
) -> None:
  _unlink_if_present(transaction, temporary_name)
  if published is not None:
    current = _published_identity(destination_parent, destination_name)
    if current is not None and current.device == published.device and current.inode == published.inode:
      _unlink_if_present(destination_parent, destination_name)
      os.fsync(destination_parent)
  _unlink_if_present(transaction, "COMPLETE")
  _restore_incomplete(transaction)
  os.fsync(transaction)


def _copy_source(
  source: int,
  target: int,
  config: StageConfig,
  hook: Hook,
) -> tuple[str, int]:
  os.lseek(source, 0, os.SEEK_SET)
  hasher = hashlib.sha256()
  size = 0
  while True:
    chunk = os.read(source, config.copy_chunk_size)
    if not chunk:
      break
    _write_all(target, chunk)
    hasher.update(chunk)
    size += len(chunk)
    hook("copy_chunk")
  os.fchmod(target, 0o600)
  os.fsync(target)
  return hasher.hexdigest(), size


def stage_image(
  config: StageConfig,
  facts_provider: FactsProvider,
  hook: Hook = lambda event: None,
) -> Path:
  transaction = _open_trusted_directory(
    config.transaction,
    config.trusted_root,
    config.root_owner,
    mode=0o700,
  )
  destination_parent = _open_trusted_directory(
    config.destination.parent,
    config.trusted_root,
    config.root_owner,
  )
  source = -1
  source_parent = -1
  temporary = -1
  temporary_name = ".candidate.partial"
  published: FileIdentity | None = None
  committed = False
  destination_directory_identity = _directory_identity(os.fstat(destination_parent))
  try:
    marker = os.stat("INCOMPLETE", dir_fd=transaction, follow_symlinks=False)
    if (
      not stat.S_ISREG(marker.st_mode)
      or marker.st_uid != config.root_owner
      or marker.st_gid != config.root_group
      or stat.S_IMODE(marker.st_mode) != 0o600
      or marker.st_nlink != 1
    ):
      raise StageFailure("transaction INCOMPLETE marker is invalid")
    _require_absent(
      config.destination,
      "destination",
      config.trusted_root,
      config.root_owner,
    )
    if os.fstat(transaction).st_dev != os.fstat(destination_parent).st_dev:
      raise StageFailure("transaction and destination are on different filesystems")
    available = os.fstatvfs(transaction)
    if available.f_bavail * available.f_frsize < config.source_size + config.reserve_bytes:
      raise StageFailure("insufficient staging space")
    before = _preflight(config, facts_provider, hook)
    _write_json(
      transaction,
      "before.json",
      [asdict(record) for record in before],
    )
    _write_new(
      transaction,
      "REMOVE.txt",
      (
        f"Remove only {config.destination} after its SHA-256 is verified as "
        f"{config.source_sha256}. Do not alter boot.bin, GRUB, or another image.\n"
      ).encode(),
    )
    source, source_parent, source_identity = _source_descriptor(config)
    hook("source_verified")
    temporary = os.open(
      temporary_name,
      os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
      0o600,
      dir_fd=transaction,
    )
    copied_hash, copied_size = _copy_source(source, temporary, config, hook)
    temporary_identity = _identity(os.fstat(temporary))
    os.close(temporary)
    temporary = -1
    if copied_hash != config.source_sha256 or copied_size != config.source_size:
      raise StageFailure("copied candidate hash or size mismatch")
    if (
      temporary_identity.owner != config.root_owner
      or temporary_identity.group != config.root_group
      or temporary_identity.mode != 0o600
      or temporary_identity.links != 1
      or temporary_identity.size != config.source_size
    ):
      raise StageFailure("temporary candidate metadata mismatch")
    _same_source_path(config, source_identity)
    if _identity(os.fstat(source)) != source_identity:
      raise StageFailure("source identity changed during staging")
    hook("copy_complete")
    after_copy = _preflight(config, facts_provider, hook)
    if after_copy != before:
      raise StageFailure("protected pin identity changed")
    _require_directory_identity(
      config.destination.parent,
      destination_directory_identity,
      config.trusted_root,
    )
    with _blocked_signals():
      try:
        hook("link")
        published = temporary_identity
        try:
          os.link(
            temporary_name,
            config.destination.name,
            src_dir_fd=transaction,
            dst_dir_fd=destination_parent,
            follow_symlinks=False,
          )
        except FileExistsError as error:
          raise StageFailure("destination already exists") from error
        hook("destination_parent_fsync")
        os.fsync(destination_parent)
        hook("temp_unlink")
        os.unlink(temporary_name, dir_fd=transaction)
        os.fsync(transaction)
        _require_directory_identity(
          config.destination.parent,
          destination_directory_identity,
          config.trusted_root,
        )
        hook("destination_verify")
        destination_identity = _verify_destination(
          destination_parent,
          config.destination.name,
          temporary_identity,
          config.source_sha256,
          config.source_size,
          config.root_owner,
          config.root_group,
        )
        hook("final_pin_check")
        after_publish = _preflight(config, facts_provider, hook)
        if after_publish != before:
          raise StageFailure("protected pin identity changed after publication")
        _require_directory_identity(
          config.destination.parent,
          destination_directory_identity,
          config.trusted_root,
        )
        hook("record_write")
        _write_json(
          transaction,
          "transaction.json",
          {
            "status": "READY_TO_COMMIT",
            "commit_point": "atomic INCOMPLETE-to-COMPLETE rename",
            "source": str(config.source),
            "destination": str(config.destination),
            "sha256": config.source_sha256,
            "size": config.source_size,
            "identity": asdict(destination_identity),
            "protected": [asdict(record) for record in after_publish],
            "rollback": str(config.transaction / "REMOVE.txt"),
          },
        )
        os.fsync(transaction)
        hook("commit_pin_check")
        commit_check = _preflight(config, facts_provider, hook)
        if commit_check != before:
          raise StageFailure("protected pin identity changed before commit")
        try:
          os.stat("COMPLETE", dir_fd=transaction, follow_symlinks=False)
        except FileNotFoundError:
          pass
        else:
          raise StageFailure("COMPLETE marker already exists")
        hook("marker_rename")
        os.rename(
          "INCOMPLETE",
          "COMPLETE",
          src_dir_fd=transaction,
          dst_dir_fd=transaction,
        )
        hook("marker_dir_fsync")
        os.fsync(transaction)
        committed = True
      except Exception as error:
        if not committed:
          _cleanup_failed_publication(
            transaction,
            destination_parent,
            temporary_name,
            config.destination.name,
            published,
          )
          _record_failure(transaction, error)
        raise
    return config.destination
  except Exception as error:
    if not committed:
      with _blocked_signals():
        if temporary >= 0:
          os.close(temporary)
          temporary = -1
        _cleanup_failed_publication(
          transaction,
          destination_parent,
          temporary_name,
          config.destination.name,
          published,
        )
        _record_failure(transaction, error)
    raise
  finally:
    if source >= 0:
      os.close(source)
    if source_parent >= 0:
      os.close(source_parent)
    os.close(destination_parent)
    os.close(transaction)


def validate_root_environment(environment: dict[str, str]) -> None:
  if environment != {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"}:
    raise StageFailure("root environment is not the reviewed empty environment")


def _run_fact(command: tuple[str, ...]) -> str:
  result = subprocess.run(
    command,
    check=False,
    capture_output=True,
    text=True,
    timeout=30,
    env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"},
  )
  if result.returncode != 0 or result.stderr:
    raise StageFailure(f"host fact command failed: {command[0]}")
  return result.stdout.rstrip("\n")


def collect_host_facts() -> HostFacts:
  packages = _run_fact(
    (
      "/usr/bin/pacman",
      "-Q",
      "linux-asahi",
      "m1n1",
      "uboot-asahi",
      "mesa",
      "mkinitcpio",
      "openssl",
      "coreutils",
      "kmod",
      "avd-fw",
    )
  )
  mount = _run_fact(
    (
      "/usr/bin/findmnt",
      "-n",
      "-o",
      "FSTYPE,UUID,TARGET",
      "-T",
      "/boot",
    )
  )
  return HostFacts(os.uname().release, packages, mount)


def production_config(transaction: Path) -> StageConfig:
  return StageConfig(
    source=SOURCE,
    source_sha256=SOURCE_SHA256,
    source_size=SOURCE_SIZE,
    destination=DESTINATION,
    transaction=transaction,
    system_root=Path("/"),
    trusted_root=Path("/"),
    root_owner=0,
    root_group=0,
    source_owner=1001,
    source_group=1001,
    protected_pins=PROTECTED_PINS,
    kernel_release=EXPECTED_KERNEL,
    package_output=EXPECTED_PACKAGES,
    mount_output=EXPECTED_MOUNT,
    copy_chunk_size=1_048_576,
    reserve_bytes=RESERVE_BYTES,
  )


def _signal_abort(signum: int, frame: object) -> None:
  raise StageInterrupted(f"signal {signum}")


def _validate_root_wrapper(path: Path) -> None:
  descriptor, parent, identity = _open_trusted_regular(path, Path("/"), 0)
  os.close(descriptor)
  os.close(parent)
  if identity.owner != 0 or identity.group != 0 or identity.mode != 0o500:
    raise StageFailure("authenticated root wrapper metadata changed")
  transaction = path.parent
  transaction_descriptor = _open_trusted_directory(
    transaction,
    Path("/"),
    0,
    mode=0o700,
  )
  os.close(transaction_descriptor)


def main() -> int:
  try:
    if len(sys.argv) != 1:
      raise StageFailure("no arguments or path overrides are accepted")
    if os.geteuid() != 0:
      raise StageFailure("root is required")
    if sys.version_info[:2] != (3, 14):
      raise StageFailure("Python runtime changed")
    validate_root_environment(dict(os.environ))
    wrapper = Path(__file__)
    _validate_root_wrapper(wrapper)
    for number in (signal.SIGHUP, signal.SIGINT, signal.SIGTERM):
      signal.signal(number, _signal_abort)
    destination = stage_image(production_config(wrapper.parent), collect_host_facts)
    print("AFK PR582 IMAGE STAGING PASS")
    print(f"Candidate: {destination}")
    print(f"Checks retained in {wrapper.parent}")
    print("Default boot, boot selection, boot.bin, GRUB, packages, and modules are unchanged.")
    print("No reboot permission.")
    return 0
  except (OSError, StageFailure, subprocess.SubprocessError) as error:
    print(f"REFUSED: {error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
  raise SystemExit(main())
