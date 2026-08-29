"""Bounded fixture helpers for the separately reviewed E-only control.

There is no operational control or assembler entry. Only a later reviewed
recipe may bind real E bytes, use these helpers and accept a complete proof.
"""

from contextlib import ExitStack
from dataclasses import dataclass, field
import hashlib
import json
import math
import os
from pathlib import Path
import re
import selectors
import stat
import subprocess
import time
from typing import BinaryIO, NoReturn

from cpio_image import read_regular, write_new
from prepare_image import dependency_output
from verify_control import TreeState, file_identity, module_name, snapshot


KERNEL = "7.1.6-1-1-ARCH"
CONTROL_ROOT = Path("/work/control-root")
LOOKUP_ROOT = Path("/work/lookup-root")
MODULE_DIRECTORY = Path("lib/modules") / KERNEL
MAX_COMMANDS = 424
CONTROL_SECONDS = 270.0
MAX_BYTES = 64 * 1024 * 1024
INDEX_NAMES = frozenset((
  "modules.alias.bin", "modules.builtin.alias.bin", "modules.builtin.bin",
  "modules.dep.bin", "modules.devname", "modules.softdep", "modules.symbols.bin",
))
INDEX_INPUTS = frozenset(("modules.order", "modules.builtin", "modules.builtin.modinfo"))
EMPTY_CONFIG = Path("/work/empty-modprobe.conf")
STREAMS = ("/work/e-early.cpio", "/work/e-main.cpio")
MEMBERS = tuple(f"usr/lib/modules/{KERNEL}/kernel/{relative}" for relative in (
  "drivers/usb/typec/tipd/tps6598x-core.ko", "drivers/usb/typec/tipd/tps6598x.ko",
  "drivers/phy/apple/phy-apple-atc.ko", "drivers/usb/dwc3/dwc3-apple.ko",
))
ALIASES = (
  "of:Nusb-pdT(null)Capple,cd321x", "of:Ndwc3T(null)Capple,t8103-dwc3",
  "of:Natc-phyT(null)Capple,t8103-atcphy",
)
EXPORTS = (
  "tipd_sn201202x_data", "tps6598x_regmap_config", "tipd_init", "tipd_cd321x_data",
  "tipd_tps6598x_data", "tipd_tps25750_data", "tipd_remove", "tipd_suspend", "tipd_resume",
)
ENVIRONMENT = {"PATH": "/usr/bin:/bin", "LC_ALL": "C", "LANG": "C", "TMPDIR": "/tmp"}

# Only these literal Python self-checks may join the six control tools.
# The real 424-child E workload must never call one of them.
SELF_CHECKS = (
  "import sys; sys.stdout.buffer.write(b'x' * 65537)",
  "import sys; sys.stderr.buffer.write(b'e' * 65537)",
  "import sys; sys.stderr.write('fixture stderr\\n')",
  "raise SystemExit(7)",
  "import time; time.sleep(1)",
  "import os, time; os.write(1, b'x' * 9); time.sleep(5)",
  "import os, time; os.write(2, b'e' * 9); time.sleep(5)",
)


class ControlError(RuntimeError):
  """A fixed control refusal; never a hardware or operational verdict."""


def require(condition: bool, code: str) -> None:
  if not condition:
    raise ControlError(code)


def finite_positive(value: float, maximum: float) -> bool:
  return type(value) in (int, float) and math.isfinite(value) and 0 < value <= maximum


def work_path(path: Path) -> bool:
  if not isinstance(path, Path) or not path.is_absolute():
    return False
  parts = path.parts
  return (len(parts) >= 3 and parts[:2] == ("/", "work") and
          all(re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]*", part) for part in parts[2:]))


def real_parents(path: Path) -> None:
  require(work_path(path), "CHILD_INPUT")
  for parent in path.parents:
    if parent == Path("/"):
      break
    require(stat.S_ISDIR(parent.lstat().st_mode), "CHILD_INPUT")


def stream_hash(stream: BinaryIO, size: int) -> str:
  digest = hashlib.sha256()
  remaining = size + 1
  total = 0
  while remaining:
    raw = stream.read(min(1024 * 1024, remaining))
    if not raw:
      break
    digest.update(raw)
    total += len(raw)
    remaining -= len(raw)
  require(total == size, "CHILD_INPUT")
  return digest.hexdigest()


def approved_command(command: tuple[str, ...]) -> bool:
  if type(command) is not tuple or not 1 <= len(command) <= 13 or not all(
    type(part) is str and 0 < len(part) < 1024 and "\x00" not in part for part in command
  ):
    return False
  if command == ("/usr/bin/gzip", "-n"):
    return True
  if len(command) == 6 and command[:5] == ("/usr/bin/python3.14", "-I", "-S", "-B", "-c"):
    return command[5] in SELF_CHECKS
  if len(command) == 5 and command[:4] == ("/usr/bin/cpio", "--list", "--quiet", "--file"):
    return command[4] in STREAMS
  if len(command) == 4 and command[:3] == ("/usr/bin/bsdtar", "--list", "--file"):
    return command[3] in STREAMS
  if len(command) == 6 and command[:5] == (
    "/usr/bin/bsdtar", "--extract", "--to-stdout", "--file", STREAMS[1],
  ):
    return command[5] in MEMBERS
  if command == ("/usr/bin/depmod", "-b", str(CONTROL_ROOT), KERNEL):
    return True
  if len(command) == 8 and command[:7] == (
    "/usr/bin/modinfo", "-b", str(LOOKUP_ROOT), "-k", KERNEL, "-F", "filename",
  ):
    return re.fullmatch(r"[A-Za-z0-9_]{1,128}", command[7]) is not None
  if len(command) == 10 and command[:4] == (
    "/usr/bin/modprobe", "--dry-run", "--show-depends", "-d",
  ) and command[5:9] == ("-S", KERNEL, "-C", str(EMPTY_CONFIG)):
    root, target = command[4], command[9]
    if root == str(CONTROL_ROOT):
      return target == "--show-config"
    if root == str(LOOKUP_ROOT):
      return (target == "--show-config" or target in ALIASES or
              target in tuple(f"symbol:{name}" for name in EXPORTS) or
              re.fullmatch(r"[A-Za-z0-9_]{1,128}", target) is not None)
  return False


def open_stdin(path: Path, digest: str) -> tuple[BinaryIO, tuple[int, ...]]:
  try:
    require(type(digest) is str and re.fullmatch(r"[0-9a-f]{64}", digest) is not None, "CHILD_INPUT")
    real_parents(path)
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and
            0 <= before.st_size <= MAX_BYTES, "CHILD_INPUT")
    descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC)
    stream = os.fdopen(descriptor, "rb")
    try:
      expected = file_identity(before)
      require(file_identity(os.fstat(stream.fileno())) == expected, "CHILD_INPUT")
      actual = stream_hash(stream, before.st_size)
      require(actual == digest and file_identity(os.fstat(stream.fileno())) == expected ==
              file_identity(path.lstat()), "CHILD_INPUT")
      stream.seek(0)
      return stream, expected
    except (OSError, RuntimeError, ValueError):
      stream.close()
      raise
  except (OSError, ValueError) as error:
    raise ControlError("CHILD_INPUT") from error


def exclusive_output(path: Path) -> BinaryIO:
  try:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
  except FileExistsError as error:
    raise ControlError("CHILD_OUTPUT_EXISTS") from error
  return os.fdopen(descriptor, "wb")


@dataclass(frozen=True)
class Lookup:
  module: str
  filename: str
  insmod: tuple[str, ...]
  builtin: tuple[str, ...]


@dataclass
class Commands:
  root: Path
  budget_seconds: float = CONTROL_SECONDS
  count: int = field(default=0, init=False)
  deadline: float = field(init=False, repr=False)
  root_identity: tuple[int, ...] = field(init=False, repr=False)

  def __post_init__(self) -> None:
    require(isinstance(self.root, Path) and self.root.parent == Path("/work") and
            re.fullmatch(r"e-control-children-[a-z0-9-]{1,64}", self.root.name) is not None and
            finite_positive(self.budget_seconds, CONTROL_SECONDS), "CHILD_ARGS")
    require(os.getuid() == os.geteuid() == os.getgid() == 1001 and Path.cwd() == Path("/work"),
            "CHILD_ARGS")
    require(stat.S_ISDIR(Path("/work").lstat().st_mode), "CHILD_ARGS")
    self.deadline = time.monotonic() + self.budget_seconds
    try:
      self.root.mkdir(mode=0o700)
    except FileExistsError as error:
      raise ControlError("CHILD_OUTPUT_EXISTS") from error
    self.root_identity = self.directory_identity()

  def directory_identity(self) -> tuple[int, ...]:
    info = self.root.lstat()
    require(stat.S_ISDIR(info.st_mode) and stat.S_IMODE(info.st_mode) == 0o700 and
            info.st_uid == info.st_gid == 1001, "CHILD_OUTPUT_EXISTS")
    return (info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_gid)

  def run(
    self,
    command: tuple[str, ...],
    *,
    stdin: Path | None = None,
    stdin_sha256: str | None = None,
    timeout: float = 30.0,
    stdout_limit: int = 1024 * 1024,
    stderr_limit: int = 65536,
  ) -> bytes:
    """Run one fixed command; stop the child as soon as a bound fails."""
    require(approved_command(command) and finite_positive(timeout, 30.0) and
            type(stdout_limit) is int and 0 < stdout_limit <= MAX_BYTES and
            type(stderr_limit) is int and 0 < stderr_limit <= 65536, "CHILD_ARGS")
    require(type(self.count) is int and 0 <= self.count <= MAX_COMMANDS, "CHILD_ARGS")
    require(self.count < MAX_COMMANDS, "CONTROL_CHILD_LIMIT")
    require(time.monotonic() < self.deadline, "CONTROL_DEADLINE")
    require(self.directory_identity() == self.root_identity, "CHILD_OUTPUT_EXISTS")
    if command[0] == "/usr/bin/gzip":
      require(stdin is not None and stdin_sha256 is not None, "CHILD_INPUT")
    else:
      require(stdin is None and stdin_sha256 is None, "CHILD_INPUT")

    with ExitStack() as stack:
      input_stream: BinaryIO | None = None
      input_identity: tuple[int, ...] | None = None
      if stdin is not None and stdin_sha256 is not None:
        input_stream, input_identity = open_stdin(stdin, stdin_sha256)
        stack.enter_context(input_stream)
      if command[0] == "/usr/bin/modprobe":
        require(read_regular(EMPTY_CONFIG) == b"", "CHILD_INPUT")
      if command[0] in ("/usr/bin/cpio", "/usr/bin/bsdtar"):
        archive = Path(command[command.index("--file") + 1])
        real_parents(archive)
        require(len(read_regular(archive)) <= MAX_BYTES, "CHILD_INPUT")

      paths = tuple(self.root / f"child-{self.count:03d}.{suffix}" for suffix in ("stdout", "stderr", "json"))
      for path in paths:
        try:
          path.lstat()
        except FileNotFoundError:
          continue
        raise ControlError("CHILD_OUTPUT_EXISTS")
      outputs = tuple(stack.enter_context(exclusive_output(path)) for path in paths[:2])
      report = stack.enter_context(exclusive_output(paths[2]))
      require(time.monotonic() < self.deadline, "CONTROL_DEADLINE")
      self.count += 1
      started = time.monotonic()
      child_deadline = min(started + timeout, self.deadline)
      deadline_status = "CONTROL_DEADLINE" if self.deadline <= started + timeout else "CHILD_TIMEOUT"
      retained = [0, 0]
      observed = [0, 0]
      limits = (stdout_limit, stderr_limit)
      status = "ok"
      returncode: int | None = None
      process: subprocess.Popen[bytes] | None = None
      killed = False
      reaped = False
      try:
        process = subprocess.Popen(
          command, stdin=input_stream if input_stream is not None else subprocess.DEVNULL,
          stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd="/work", env=ENVIRONMENT,
          close_fds=True,
        )
        require(process.stdout is not None and process.stderr is not None, "CHILD_START")
        with selectors.DefaultSelector() as selector:
          for index, pipe in enumerate((process.stdout, process.stderr)):
            os.set_blocking(pipe.fileno(), False)
            selector.register(pipe, selectors.EVENT_READ, index)
          while selector.get_map() and status == "ok":
            remaining = child_deadline - time.monotonic()
            if remaining <= 0:
              status = deadline_status
              break
            for key, _ in selector.select(min(remaining, 0.05)):
              index = key.data
              available = limits[index] - retained[index]
              try:
                raw = os.read(key.fd, min(65536, available + 1))
              except (BlockingIOError, InterruptedError):
                continue
              if not raw:
                selector.unregister(key.fileobj)
                continue
              observed[index] += len(raw)
              kept = raw[:available]
              outputs[index].write(kept)
              retained[index] += len(kept)
              if len(raw) > available:
                status = "CHILD_OUTPUT_LIMIT"
                break
          if status == "ok":
            try:
              returncode = process.wait(timeout=max(0.0, child_deadline - time.monotonic()))
              reaped = True
            except subprocess.TimeoutExpired:
              status = deadline_status
      except (OSError, ValueError, ControlError):
        status = "CHILD_IO" if process is not None else "CHILD_START"
      finally:
        if process is not None:
          if process.poll() is None:
            process.kill()
            killed = True
          try:
            returncode = process.wait(timeout=1.0)
            reaped = True
          except subprocess.TimeoutExpired:
            status = "CHILD_REAP"
          for pipe in (process.stdout, process.stderr):
            if pipe is not None:
              pipe.close()
        for output in outputs:
          output.flush()
          os.fsync(output.fileno())

      if status == "ok" and returncode != 0:
        status = "CHILD_EXIT"
      if status == "ok" and retained[1]:
        status = "CHILD_STDERR"
      if input_stream is not None and stdin is not None:
        try:
          input_stream.seek(0)
          require(input_identity is not None and stream_hash(input_stream, input_identity[6]) == stdin_sha256 and
                  file_identity(os.fstat(input_stream.fileno())) == input_identity ==
                  file_identity(stdin.lstat()), "CHILD_INPUT")
        except (OSError, ValueError, ControlError):
          status = "CHILD_INPUT"
      if status == "ok" and time.monotonic() >= self.deadline:
        status = "CONTROL_DEADLINE"
      require(self.directory_identity() == self.root_identity, "CHILD_OUTPUT_EXISTS")
      record = {
        "command": list(command), "status": status, "returncode": returncode,
        "stdout": paths[0].name, "stderr": paths[1].name,
        "retained_bytes": retained, "observed_bytes": observed,
        "stdin_sha256": stdin_sha256, "stdin_bytes": input_identity[6] if input_identity else 0,
        "elapsed_seconds": time.monotonic() - started,
        "pid": process.pid if process is not None else None, "killed": killed, "reaped": reaped,
      }
      report.write((json.dumps(record, sort_keys=True, allow_nan=False) + "\n").encode("ascii"))
      report.flush()
      os.fsync(report.fileno())
      require(status == "ok", status)
      return read_regular(paths[0])


def build_root(
  root: Path,
  modules: dict[str, bytes],
  metadata: dict[str, bytes],
) -> TreeState:
  """Create only an exact, previously absent module-only reduced root."""
  require(root in (CONTROL_ROOT, LOOKUP_ROOT), "ROOT_PATH")
  expected_metadata = INDEX_INPUTS if root == CONTROL_ROOT else INDEX_NAMES
  require(type(metadata) is dict and set(metadata) == expected_metadata and
          all(type(raw) is bytes and len(raw) <= MAX_BYTES for raw in metadata.values()), "ROOT_METADATA")
  require(type(modules) is dict and len(modules) == 200, "ROOT_MODULES")
  names: set[str] = set()
  for relative, raw in modules.items():
    require(type(relative) is str and re.fullmatch(
      r"kernel/(?:[A-Za-z0-9_-]+/)*[A-Za-z0-9_][A-Za-z0-9_-]*\.ko", relative,
    ) is not None and type(raw) is bytes and 0 < len(raw) <= MAX_BYTES, "ROOT_MODULES")
    name = module_name(Path(relative).name)
    require(name not in names, "ROOT_MODULES")
    names.add(name)
  require(sum(len(raw) for raw in (*modules.values(), *metadata.values())) <= MAX_BYTES, "ROOT_MODULES")
  require(os.getuid() == os.geteuid() == os.getgid() == 1001 and Path.cwd() == Path("/work") and
          stat.S_ISDIR(Path("/work").lstat().st_mode), "ROOT_PATH")
  try:
    root.mkdir(mode=0o700)
  except FileExistsError as error:
    raise ControlError("ROOT_EXISTS") from error
  payloads = {MODULE_DIRECTORY / name: raw for name, raw in (modules | metadata).items()}
  directories = {parent for path in payloads for parent in path.parents if parent != Path(".")}
  for directory in sorted(directories, key=lambda path: (len(path.parts), str(path))):
    (root / directory).mkdir(mode=0o700)
  for relative, raw in sorted(payloads.items()):
    write_new(root / relative, raw)
  proof = snapshot(root)
  require({name: state.sha256 for name, state in proof.files.items()} == {
    str(name): hashlib.sha256(raw).hexdigest() for name, raw in payloads.items()
  }, "ROOT_CHANGED")
  return proof


def unchanged_root(root: Path, expected: TreeState) -> bool:
  """Reject any content, metadata or membership change in the private root."""
  require(root in (CONTROL_ROOT, LOOKUP_ROOT) and type(expected) is TreeState, "ROOT_CHANGED")
  try:
    require(snapshot(root) == expected, "ROOT_CHANGED")
  except (OSError, RuntimeError) as error:
    raise ControlError("ROOT_CHANGED") from error
  return True


def ordered_lookup(
  raw: bytes,
  name: str,
  names: dict[str, str],
  dependencies: dict[str, tuple[str, ...]],
  builtins: set[str],
) -> Lookup:
  """Tighten the pinned text parser to the exact reviewed dependency order."""
  require(type(raw) is bytes and 0 < len(raw) <= 1024 * 1024, "LOOKUP_FORMAT")
  require(type(names) is dict and 0 < len(names) <= 200 and type(name) is str and name in names and
          type(dependencies) is dict and type(builtins) is set and len(builtins) <= 8192, "LOOKUP_MODEL")
  require(all(type(item) is str and re.fullmatch(r"[A-Za-z0-9_]{1,128}", item) is not None
              for item in (*names.keys(), *builtins)), "LOOKUP_MODEL")
  require(all(type(path) is str and re.fullmatch(
    r"kernel/(?:[A-Za-z0-9_-]+/)*[A-Za-z0-9_][A-Za-z0-9_-]*\.ko", path,
  ) is not None and module_name(Path(path).name) == key for key, path in names.items()), "LOOKUP_MODEL")
  require(len(set(names.values())) == len(names) and set(dependencies) == set(names.values()), "LOOKUP_MODEL")
  for path, values in dependencies.items():
    require(type(values) is tuple and len(values) < len(names) and
            all(type(value) is str and value in dependencies and value != path for value in values) and
            len(values) == len(set(values)), "LOOKUP_MODEL")
  try:
    parsed = dependency_output(raw, name, names, builtins)
  except (RuntimeError, ValueError, KeyError) as error:
    raise ControlError("LOOKUP_FORMAT") from error
  insmod, builtin = parsed["insmod"], parsed["builtin"]
  require(type(insmod) is list and type(builtin) is list and
          all(type(item) is str for item in (*insmod, *builtin)), "LOOKUP_FORMAT")
  filename = str(LOOKUP_ROOT / MODULE_DIRECTORY / names[name])
  expected = tuple(str(LOOKUP_ROOT / MODULE_DIRECTORY / path)
                   for path in reversed(dependencies[names[name]])) + (filename,)
  require(tuple(insmod) == expected, "LOOKUP_ORDER")
  expected_builtin = ("ecb",) if name == "lrw" else ()
  require(tuple(builtin) == expected_builtin and (name != "lrw" or "ecb" in builtins), "LOOKUP_BUILTIN")
  canonical = "".join(f"builtin {item}\n" for item in builtin) + "".join(f"insmod {item} \n" for item in insmod)
  require(raw == canonical.encode("ascii"), "LOOKUP_FORMAT")
  return Lookup(name, filename, expected, expected_builtin)


def main() -> NoReturn:
  """A fixture cannot unlock real E control or T1 image assembly."""
  raise ControlError("E_CONTROL_UNAVAILABLE")


if __name__ == "__main__":
  main()
