"""Bounded, non-extracting operations on one uncompressed 070701 archive.

This is an offline helper, not a collector, extractor, image builder, or sandbox.
Filesystem calls require the separately reviewed sandbox and absolute paths.
They do not grant authority to access a host path. No CLI or live fallback exists.

Names are printable ASCII, with at most one initial ``./``. A root-directory
record may use ``.`` or ``./``. Symlink targets stay opaque and may be absolute;
this module never follows an archive link or materializes archive members.
Mutation keys must use canonical names. Parents must be directory records in
the original archive. Only regular, single-link members may be changed or added.

Untouched records, the trailer, and its exact zero tail remain byte-identical.
Changed payloads receive four-byte alignment; no new 512-byte blocking is added.
An unchanged transformation returns the original bytes. Compression, split
early/main archives, index regeneration, and real-tool controls belong elsewhere.
"""
from bisect import bisect_left
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import stat


MAX_ARCHIVE_BYTES = 256 * 1024 * 1024
MAX_MEMBERS = 8192
MAX_NAME_BYTES = 4096  # Includes the final NUL in an archive name.
_MAX_DEPTH = 128
_MAX_COMPONENT_BYTES = 255
_IO_CHUNK_BYTES = 1024 * 1024
_HEADER_BYTES = 110
_UINT32_MAX = (1 << 32) - 1
_HEX_DIGITS = b"0123456789abcdefABCDEF"
_DIRECTORY_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC


class ArchiveError(ValueError):
  """Input or filesystem safety gate failed; no output is removed on failure."""


@dataclass(frozen=True)
class Member:
  name: str
  raw_name: bytes
  fields: tuple[int, ...]
  payload: bytes
  raw: bytes


@dataclass(frozen=True)
class Archive:
  raw: bytes
  members: tuple[Member, ...]
  tail: bytes  # Original trailer record, followed by the original zero padding.


def _require(condition: bool, message: str) -> None:
  if not condition:
    raise ArchiveError(message)


def _aligned(size: int) -> int:
  return (size + 3) & ~3


def _name(value: str, *, allow_root: bool = False) -> str:
  _require(type(value) is str, "member name must be a string")
  _require(0 < len(value) < MAX_NAME_BYTES, "member name exceeds bound")
  _require(all(32 <= ord(char) <= 126 for char in value), "invalid member name bytes")
  if value in (".", "./"):
    _require(allow_root, "root is not a mutation target")
    return "."
  canonical = value[2:] if value.startswith("./") else value
  parts = canonical.split("/")
  _require(len(parts) <= _MAX_DEPTH, "member path exceeds depth bound")
  _require(all(part not in ("", ".", "..") and len(part) <= _MAX_COMPONENT_BYTES
               for part in parts), "unsafe member path")
  _require(canonical != "TRAILER!!!", "reserved member name")
  return canonical


def _payload(value: bytes) -> None:
  _require(type(value) is bytes, "payload must be immutable bytes")
  _require(len(value) <= MAX_ARCHIVE_BYTES, "payload exceeds bound")


def parse_newc(raw: bytes) -> Archive:
  """Validate one bounded newc stream without extracting or resolving names."""
  _payload(raw)
  members: list[Member] = []
  names: set[str] = set()
  offset = 0
  while offset < len(raw):
    start = offset
    header_end = start + _HEADER_BYTES
    _require(header_end <= len(raw), "truncated newc header")
    _require(raw[start:start + 6] == b"070701", "unsupported newc magic")
    header = raw[start + 6:header_end]
    _require(all(byte in _HEX_DIGITS for byte in header), "invalid newc numeric field")
    fields = tuple(int(header[index:index + 8], 16) for index in range(0, 104, 8))
    name_size, file_size = fields[11], fields[6]
    _require(1 <= name_size <= MAX_NAME_BYTES, "member name exceeds bound")
    _require(file_size <= MAX_ARCHIVE_BYTES, "archive member exceeds bound")
    _require(fields[12] == 0, "070701 checksum must be zero")
    name_end = header_end + name_size
    payload_start = _aligned(name_end)
    payload_end = payload_start + file_size
    offset = _aligned(payload_end)
    _require(offset <= len(raw), "truncated newc member")
    raw_name = raw[header_end:name_end]
    _require(raw_name[-1:] == b"\0" and b"\0" not in raw_name[:-1],
             "invalid newc name terminator")
    _require(not any(raw[name_end:payload_start]) and not any(raw[payload_end:offset]),
             "nonzero newc alignment padding")
    if raw_name == b"TRAILER!!!\0":
      _require(file_size == 0 and fields[1] == 0, "invalid newc trailer")
      _require(raw.count(b"\0", offset) == len(raw) - offset,
               "data follows the newc trailer")
      return Archive(raw, tuple(members), raw[start:])
    _require(len(members) < MAX_MEMBERS, "archive member count exceeds bound")
    try:
      name = _name(raw_name[:-1].decode("ascii"), allow_root=True)
    except UnicodeDecodeError:
      raise ArchiveError("invalid member name bytes") from None
    _require(name not in names, "duplicate canonical member name")
    mode = fields[1]
    file_type = stat.S_IFMT(mode)
    _require(mode <= 0xffff and file_type in (stat.S_IFREG, stat.S_IFDIR, stat.S_IFLNK),
             "unsupported archive member type")
    _require(fields[4] > 0, "zero archive link count")
    _require(name != "." or file_type == stat.S_IFDIR, "root member is not a directory")
    _require(file_type != stat.S_IFDIR or file_size == 0, "nonempty archive directory")
    payload = raw[payload_start:payload_end]
    if file_type == stat.S_IFLNK:
      _require(0 < file_size < MAX_NAME_BYTES and b"\0" not in payload,
               "invalid archive symlink payload")
    names.add(name)
    members.append(Member(name, raw_name, fields, payload, raw[start:offset]))
  raise ArchiveError("missing newc trailer")


def _mutation_name(value: str) -> str:
  canonical = _name(value)
  _require(value == canonical, "mutation name must be canonical")
  return canonical


def _mutation_path(name: str, members: Mapping[str, Member], ordered_names: tuple[str, ...]) -> None:
  parts = name.split("/")
  for depth in range(1, len(parts)):
    parent = members.get("/".join(parts[:depth]))
    _require(parent is not None and stat.S_ISDIR(parent.fields[1]),
             "mutation parent is not an existing directory")
  # A new regular file must not shadow an existing implicit directory either.
  prefix = name + "/"
  index = bisect_left(ordered_names, prefix)
  _require(index == len(ordered_names) or not ordered_names[index].startswith(prefix),
           "mutation target has archive descendants")


def _replace_record(member: Member, payload: bytes) -> bytes:
  if member.payload == payload:
    return member.raw
  payload_start = _aligned(_HEADER_BYTES + len(member.raw_name))
  # Keep even numeric-field casing and the original name/alignment bytes.
  header = member.raw[:54] + f"{len(payload):08x}".encode("ascii") + member.raw[62:payload_start]
  return header + payload + b"\0" * (-len(payload) % 4)


def _new_record(name: str, payload: bytes, inode: int) -> bytes:
  raw_name = name.encode("ascii") + b"\0"
  fields = (inode, stat.S_IFREG | 0o644, 0, 0, 1, 0, len(payload), 0, 0, 0, 0,
            len(raw_name), 0)
  header = b"070701" + b"".join(f"{field:08x}".encode("ascii") for field in fields) + raw_name
  return header + b"\0" * (-len(header) % 4) + payload + b"\0" * (-len(payload) % 4)


def replace_members(original: Archive, replacements: Mapping[str, bytes],
                    additions: tuple[tuple[str, bytes], ...]) -> bytes:
  """Return a bounded stream with only the requested regular-file changes.

  A caller-created Archive cannot bypass validation. Additions are appended in
  supplied order with fresh inode numbers, root UID/GID, mode 0644, and mtime zero.
  Existing hardlink groups are preserved, never expanded or rewritten.
  """
  _require(type(original) is Archive, "expected a parsed archive")
  validated = parse_newc(original.raw)
  _require(original == validated, "archive model does not match its raw bytes")
  _require(isinstance(replacements, Mapping), "replacements must be a mapping")
  _require(len(replacements) <= MAX_MEMBERS, "replacement count exceeds bound")
  _require(type(additions) is tuple, "additions must be an ordered tuple")
  _require(len(validated.members) + len(additions) <= MAX_MEMBERS,
           "archive member count exceeds bound")
  by_name = {member.name: member for member in validated.members}
  ordered_names = tuple(sorted(by_name))
  updates: dict[str, bytes] = {}
  output_size = len(validated.raw)
  for name, payload in replacements.items():
    _require(len(updates) < MAX_MEMBERS, "replacement count exceeds bound")
    name = _mutation_name(name)
    _payload(payload)
    _require(name not in updates and name in by_name, "unknown or duplicate replacement")
    member = by_name[name]
    _require(stat.S_ISREG(member.fields[1]) and member.fields[4] == 1,
             "replacement is not a regular single-link member")
    _mutation_path(name, by_name, ordered_names)
    output_size += _aligned(len(payload)) - _aligned(len(member.payload))
    updates[name] = payload
  new_members: list[tuple[str, bytes, int]] = []
  next_inode = max((member.fields[0] for member in validated.members), default=0)
  new_names: set[str] = set()
  for addition in additions:
    _require(type(addition) is tuple and len(addition) == 2, "invalid addition")
    name, payload = addition
    name = _mutation_name(name)
    _payload(payload)
    _require(name not in by_name and name not in new_names, "duplicate addition")
    _mutation_path(name, by_name, ordered_names)
    next_inode += 1
    _require(next_inode <= _UINT32_MAX, "newc inode space exhausted")
    output_size += _aligned(_HEADER_BYTES + len(name) + 1) + _aligned(len(payload))
    _require(output_size <= MAX_ARCHIVE_BYTES, "transformed archive exceeds bound")
    new_names.add(name)
    new_members.append((name, payload, next_inode))
  _require(output_size <= MAX_ARCHIVE_BYTES, "transformed archive exceeds bound")
  if not updates and not new_members:
    return validated.raw
  records = [_replace_record(member, updates[member.name]) if member.name in updates
             else member.raw for member in validated.members]
  records.extend(_new_record(name, payload, inode) for name, payload, inode in new_members)
  records.append(validated.tail)
  return b"".join(records)


def _directory_identity(info: os.stat_result) -> tuple[int, ...]:
  _require(stat.S_ISDIR(info.st_mode), "filesystem parent is not a directory")
  # Own output creation changes parent times, not its inode/ownership/mode.
  return (info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_gid)


def _file_identity(info: os.stat_result) -> tuple[int, ...]:
  _require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1,
           "filesystem input is not regular and single-link")
  _require(0 <= info.st_size <= MAX_ARCHIVE_BYTES, "filesystem file exceeds bound")
  return (info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_gid,
          info.st_nlink, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


@dataclass(frozen=True)
class _Parent:
  descriptors: tuple[int, ...]
  components: tuple[str, ...]
  identities: tuple[tuple[int, ...], ...]
  leaf: str

  @property
  def descriptor(self) -> int:
    return self.descriptors[-1]

  def named_file(self) -> os.stat_result:
    return os.stat(self.leaf, dir_fd=self.descriptor, follow_symlinks=False)

  def check(self) -> None:
    _require(_directory_identity(os.stat("/", follow_symlinks=False)) == self.identities[0],
             "filesystem root changed")
    for index, descriptor in enumerate(self.descriptors):
      _require(_directory_identity(os.fstat(descriptor)) == self.identities[index],
               "filesystem parent changed")
      if index:
        named = os.stat(self.components[index - 1], dir_fd=self.descriptors[index - 1],
                        follow_symlinks=False)
        _require(_directory_identity(named) == self.identities[index],
                 "filesystem parent path changed")


def _close(descriptors: tuple[int, ...]) -> None:
  failed = False
  for descriptor in reversed(descriptors):
    try:
      os.close(descriptor)
    except OSError:
      failed = True
  _require(not failed, "descriptor close failed")


@contextmanager
def _parent_directory(path: Path) -> Iterator[_Parent]:
  _require(isinstance(path, Path) and path.anchor == "/", "filesystem path must be absolute")
  parts = path.parts[1:]
  _require(0 < len(parts) <= _MAX_DEPTH, "filesystem path exceeds depth bound")
  try:
    encoded = os.fsencode(path)
  except UnicodeError:
    raise ArchiveError("invalid filesystem path encoding") from None
  _require(len(encoded) < MAX_NAME_BYTES, "filesystem path exceeds byte bound")
  _require(all(part not in ("", ".", "..") and len(os.fsencode(part)) <= _MAX_COMPONENT_BYTES
               and all(ord(char) >= 32 and ord(char) != 127 for char in part) for part in parts),
           "unsafe filesystem path")
  descriptors: list[int] = []
  identities: list[tuple[int, ...]] = []
  try:
    descriptors.append(os.open("/", _DIRECTORY_FLAGS))
    identities.append(_directory_identity(os.fstat(descriptors[-1])))
    for part in parts[:-1]:
      before = _directory_identity(os.stat(part, dir_fd=descriptors[-1], follow_symlinks=False))
      descriptors.append(os.open(part, _DIRECTORY_FLAGS, dir_fd=descriptors[-1]))
      identity = _directory_identity(os.fstat(descriptors[-1]))
      _require(identity == before, "filesystem parent changed while opening")
      identities.append(identity)
    parent = _Parent(tuple(descriptors), tuple(parts[:-1]), tuple(identities), parts[-1])
    parent.check()
    yield parent
  except OSError:
    # Filesystem exceptions may contain private host paths. Keep them out of reports.
    raise ArchiveError("filesystem operation failed") from None
  finally:
    _close(tuple(descriptors))


def _read_chunks(descriptor: int, size: int) -> Iterator[bytes]:
  remaining = size
  while remaining:
    chunk = os.read(descriptor, min(remaining, _IO_CHUNK_BYTES))
    _require(bool(chunk), "source shortened while reading")
    remaining -= len(chunk)
    yield chunk
  _require(not os.read(descriptor, 1), "source grew while reading")


def read_regular(path: Path, expected_sha256: str | None = None) -> bytes:
  """Read a pinned regular single-link file, rejecting name or inode drift.

  No parent or leaf symlink is followed. Size, inode, metadata, and the named
  entry are checked before and after reading. Access-time changes are harmless.
  A supplied digest must be canonical lowercase SHA-256 and must match.
  """
  if expected_sha256 is not None:
    _require(type(expected_sha256) is str and len(expected_sha256) == 64
               and all(char in "0123456789abcdef" for char in expected_sha256),
             "invalid expected SHA-256")
  with _parent_directory(path) as parent:
    before = _file_identity(parent.named_file())
    descriptor = os.open(parent.leaf, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC,
                         dir_fd=parent.descriptor)
    try:
      opened = os.fstat(descriptor)
      _require(_file_identity(opened) == before, "source changed while opening")
      payload = b"".join(_read_chunks(descriptor, opened.st_size))
      _require(_file_identity(os.fstat(descriptor)) == before
                 and _file_identity(parent.named_file()) == before, "source changed while reading")
      parent.check()
      if expected_sha256 is not None:
        _require(hashlib.sha256(payload).hexdigest() == expected_sha256, "source SHA-256 mismatch")
      return payload
    finally:
      _close((descriptor,))


def write_new(path: Path, payload: bytes) -> None:
  """Exclusively create, verify, and fsync a mode-0600 file and its parent.

  A failure retains any newly created file, including partial output. The caller
  must inspect it and choose a fresh name; this helper never replaces or unlinks.
  The sandbox, not a string path check, provides the writable containment root.
  """
  _payload(payload)
  with _parent_directory(path) as parent:
    descriptor = os.open(parent.leaf, os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                         0o600, dir_fd=parent.descriptor)
    try:
      created = os.fstat(descriptor)
      _file_identity(created)
      os.fchmod(descriptor, 0o600)
      view = memoryview(payload)
      written = 0
      while written < len(view):
        count = os.write(descriptor, view[written:written + _IO_CHUNK_BYTES])
        _require(count > 0, "output write made no progress")
        written += count
      os.fsync(descriptor)
      completed = os.fstat(descriptor)
      identity = _file_identity(completed)
      _require((completed.st_dev, completed.st_ino, completed.st_uid, completed.st_gid)
               == (created.st_dev, created.st_ino, created.st_uid, created.st_gid)
               and completed.st_mode == stat.S_IFREG | 0o600
               and completed.st_size == len(payload), "output identity, mode, or size changed")
      os.lseek(descriptor, 0, os.SEEK_SET)
      digest = hashlib.sha256()
      for chunk in _read_chunks(descriptor, len(payload)):
        digest.update(chunk)
      _require(digest.digest() == hashlib.sha256(payload).digest(), "output payload changed")
      _require(_file_identity(os.fstat(descriptor)) == identity
                 and _file_identity(parent.named_file()) == identity, "output changed during verification")
      parent.check()
      os.fsync(parent.descriptor)
    finally:
      _close((descriptor,))
