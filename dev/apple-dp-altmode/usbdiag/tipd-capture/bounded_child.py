"""Private bounded subprocess capture; no live command or public override.

Receipts retain actual argv and observed/retained counts. They never claim
the total emitted bytes, journal provenance or overall capture acceptance.
"""

from dataclasses import asdict, dataclass, field
import hashlib
import json
import os
from pathlib import Path
import selectors
import signal
import stat
import subprocess
import time
from types import FrameType
from typing import Literal


CHILD_ENV = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"}


@dataclass(frozen=True)
class _Limits:
  duration_us: int
  stdout_limit: int
  stderr_limit: int
  cleanup_us: int


@dataclass(frozen=True)
class ChildCapture:
  argv: tuple[str, ...]
  status: Literal["ok", "error", "timeout", "stdout_limit", "stderr_limit", "interrupted"]
  pid: int
  process_group: int
  exit_code: int | None
  killed: bool
  reaped: bool
  start_monotonic_us: int
  end_monotonic_us: int
  stdout_observed: int
  stderr_observed: int
  stdout_retained: int
  stderr_retained: int
  stdout_sha256: str
  stderr_sha256: str
  stdout_eof: bool
  stderr_eof: bool
  emitted_bytes_known: Literal[False] = False
  overall_capture_accepted: Literal[False] = False
  execution_policy: Literal["clean-env:null-stdin:close-fds:new-session"] = "clean-env:null-stdin:close-fds:new-session"


class CollectionError(RuntimeError):
  """A fixed code; partial private files remain for inspection."""


@dataclass
class _Stream:
  descriptor: int
  limit: int
  observed: int = 0
  retained: int = 0
  eof: bool = False
  broken: bool = False
  retained_data: bytearray = field(default_factory=bytearray)


def _identity(info: os.stat_result) -> tuple[int, ...]:
  return (info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_gid, info.st_nlink)


def _private_directory(path: Path) -> int:
  """Walk without following symlinks; require a private owned final parent."""
  if not isinstance(path, Path) or not path.is_absolute() or ".." in path.parts:
    raise CollectionError("invalid_private_directory")
  descriptor = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
  try:
    for component in path.parts[1:]:
      child = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=descriptor)
      os.close(descriptor)
      descriptor = child
    info = os.fstat(descriptor)
    if stat.S_IMODE(info.st_mode) != 0o700 or (info.st_uid, info.st_gid) != (os.getuid(), os.getgid()):
      raise CollectionError("invalid_private_directory")
    return descriptor
  except BaseException:
    os.close(descriptor)
    raise


def _new_directory(path: Path) -> int:
  parent = _private_directory(path.parent)
  try:
    os.mkdir(path.name, 0o700, dir_fd=parent)
    descriptor = os.open(path.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=parent)
  except OSError:
    raise CollectionError("private_output_collision_or_error") from None
  finally:
    os.close(parent)
  return descriptor


def _open_new(directory: int, name: str) -> int:
  try:
    return os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600, dir_fd=directory)
  except OSError:
    raise CollectionError("private_file_collision_or_error") from None


def _read_back(directory: int, name: str, limit: int, expected: tuple[int, ...] | None = None) -> bytes:
  descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=directory)
  try:
    before = os.fstat(descriptor)
    if (
      not stat.S_ISREG(before.st_mode) or stat.S_IMODE(before.st_mode) != 0o600
      or (before.st_uid, before.st_gid, before.st_nlink) != (os.getuid(), os.getgid(), 1)
      or not 0 <= before.st_size <= limit
      or (expected is not None and _identity(before) != expected)
    ):
      raise CollectionError("private_readback_mismatch")
    raw = bytearray()
    while len(raw) <= limit:
      chunk = os.read(descriptor, min(65_536, limit + 1 - len(raw)))
      if not chunk:
        break
      raw.extend(chunk)
    after = os.fstat(descriptor)
    named = os.stat(name, dir_fd=directory, follow_symlinks=False)
    if (
      len(raw) != before.st_size or _identity(before) != _identity(after)
      or (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_size, after.st_mtime_ns, after.st_ctime_ns)
      or _identity(after) != _identity(named)
      or (after.st_size, after.st_mtime_ns, after.st_ctime_ns) != (named.st_size, named.st_mtime_ns, named.st_ctime_ns)
    ):
      raise CollectionError("private_readback_mismatch")
    return bytes(raw)
  finally:
    os.close(descriptor)


def _write_new(directory: int, name: str, raw: bytes) -> None:
  descriptor = _open_new(directory, name)
  expected = _identity(os.fstat(descriptor))
  try:
    offset = 0
    while offset < len(raw):
      written = os.write(descriptor, raw[offset:])
      if written <= 0:
        raise CollectionError("short_private_write")
      offset += written
  finally:
    os.close(descriptor)
  if _read_back(directory, name, len(raw), expected) != raw:
    raise CollectionError("private_readback_mismatch")


def _pump(
  process: subprocess.Popen[bytes], selector: selectors.BaseSelector,
  streams: dict[str, _Stream], deadline_us: int, enforce_limits: bool,
) -> str:
  while selector.get_map() or process.poll() is None:
    remaining = deadline_us - time.monotonic_ns() // 1_000
    if remaining <= 0:
      return "timeout"
    for key, unused in selector.select(min(remaining / 1_000_000, 0.02)):
      stream = streams[key.data]
      try:
        piece = os.read(key.fd, 4_096)
      except BlockingIOError:
        continue
      if not piece:
        stream.eof = True
        selector.unregister(key.fileobj)
        key.fileobj.close()
        continue
      stream.observed += len(piece)
      retained = piece[:max(0, stream.limit - stream.retained)]
      offset = 0
      while offset < len(retained) and not stream.broken:
        try:
          written = os.write(stream.descriptor, retained[offset:])
          if written <= 0:
            raise OSError("short write")
        except OSError:
          stream.broken = True
          raise
        stream.retained_data.extend(retained[offset:offset + written])
        offset += written
        stream.retained += written
      if enforce_limits and stream.observed > stream.limit:
        return key.data + "_limit"
  return "ok"


def _kill_group(process: subprocess.Popen[bytes]) -> bool:
  try:
    os.killpg(process.pid, signal.SIGKILL)
    return True
  except ProcessLookupError:
    return False


def _reap_until(process: subprocess.Popen[bytes], deadline_us: int) -> None:
  while process.poll() is None:
    remaining = deadline_us - time.monotonic_ns() // 1_000
    if remaining <= 0:
      return
    time.sleep(min(0.005, remaining / 1_000_000))


def _capture_child(
  argv: tuple[str, ...], output_dir: Path, limits: _Limits, *, _deadline_us: int | None = None,
) -> ChildCapture:
  start = time.monotonic_ns() // 1_000
  if (
    not isinstance(argv, tuple) or not 1 <= len(argv) <= 16
    or any(not isinstance(arg, str) or not arg or "\0" in arg or len(arg) > 16_384 for arg in argv)
    or not argv[0].startswith("/") or not isinstance(limits, _Limits)
    or any(type(value) is not int for value in (
      limits.duration_us, limits.stdout_limit, limits.stderr_limit, limits.cleanup_us,
    ))
    or not 0 < limits.cleanup_us < limits.duration_us <= 30_000_000
    or not 0 < limits.stdout_limit <= 8_388_608 or not 0 < limits.stderr_limit <= 65_536
    or (_deadline_us is not None and (
      type(_deadline_us) is not int or not start + limits.cleanup_us < _deadline_us <= start + limits.duration_us
    ))
  ):
    raise CollectionError("invalid_internal_child_plan")
  directory = _new_directory(output_dir)
  streams: dict[str, _Stream] = {}
  identities: dict[str, tuple[int, ...]] = {}
  selector = selectors.DefaultSelector()
  process: subprocess.Popen[bytes] | None = None
  previous_handlers: dict[int, object] = {}
  interrupted = False
  interruptible = False

  def request_stop(signum: int, frame: FrameType | None) -> None:
    nonlocal interrupted
    interrupted = True
    if process is not None and interruptible:
      raise KeyboardInterrupt

  status = "error"
  killed = False
  deadline = start + limits.duration_us if _deadline_us is None else _deadline_us
  try:
    for name, limit in (("stdout", limits.stdout_limit), ("stderr", limits.stderr_limit)):
      descriptor = _open_new(directory, name + ".bin")
      streams[name] = _Stream(descriptor, limit)
      identities[name] = _identity(os.fstat(descriptor))
    try:
      for signum in (signal.SIGINT, signal.SIGTERM):
        previous_handlers[signum] = signal.signal(signum, request_stop)
      process = subprocess.Popen(
        argv, cwd=output_dir, env=CHILD_ENV, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True, start_new_session=True,
      )
      for name, pipe in (("stdout", process.stdout), ("stderr", process.stderr)):
        if pipe is None:
          raise CollectionError("missing_child_pipe")
        os.set_blocking(pipe.fileno(), False)
        selector.register(pipe, selectors.EVENT_READ, name)
      interruptible = True
      if interrupted:
        raise KeyboardInterrupt
      status = _pump(process, selector, streams, deadline - limits.cleanup_us, True)
    except KeyboardInterrupt:
      status = "interrupted"
    except (OSError, CollectionError):
      status = "error"
    finally:
      interruptible = False
      if process is not None:
        if status != "ok" or process.poll() is None:
          killed = _kill_group(process)
          try:
            _pump(process, selector, streams, deadline, False)
          except (OSError, KeyboardInterrupt):
            status = "error"
          _reap_until(process, deadline)
        elif _kill_group(process):
          killed = True
          status = "error"
        process.poll()
      for key in list(selector.get_map().values()):
        selector.unregister(key.fileobj)
        key.fileobj.close()
      selector.close()
      for stream in streams.values():
        os.close(stream.descriptor)
        stream.descriptor = -1
      interruptible = True
    if interrupted and status == "ok":
      status = "interrupted"
    end = time.monotonic_ns() // 1_000
    reaped = process is not None and process.returncode is not None
    if not reaped or end > deadline or (status == "ok" and process.returncode != 0):
      status = "error" if status == "ok" else status
    stdout = _read_back(directory, "stdout.bin", limits.stdout_limit, identities["stdout"])
    stderr = _read_back(directory, "stderr.bin", limits.stderr_limit, identities["stderr"])
    if (
      len(stdout) != streams["stdout"].retained or len(stderr) != streams["stderr"].retained
      or stdout != streams["stdout"].retained_data or stderr != streams["stderr"].retained_data
    ):
      raise CollectionError("retained_size_mismatch")
    result = ChildCapture(
      argv, status, 0 if process is None else process.pid, 0 if process is None else process.pid,
      None if process is None else process.returncode, killed, reaped, start, end,
      streams["stdout"].observed, streams["stderr"].observed,
      len(stdout), len(stderr), hashlib.sha256(stdout).hexdigest(), hashlib.sha256(stderr).hexdigest(),
      streams["stdout"].eof, streams["stderr"].eof,
    )
    named = _private_directory(output_dir)
    try:
      if _identity(os.fstat(named)) != _identity(os.fstat(directory)):
        raise CollectionError("private_directory_replaced")
    finally:
      os.close(named)
    _write_new(directory, "child.json", json.dumps(asdict(result), separators=(",", ":")).encode("ascii") + b"\n")
    if interrupted and result.status == "ok":
      raise CollectionError("collection_interrupted")
    return result
  finally:
    for signum, previous in previous_handlers.items():
      signal.signal(signum, previous)
    selector.close()
    for stream in streams.values():
      if stream.descriptor >= 0:
        os.close(stream.descriptor)
    os.close(directory)
