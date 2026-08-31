from __future__ import annotations

import hashlib
import json
import math
import os
import re
import secrets
import signal
import stat
import struct
import sys
import tempfile
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from pathlib import Path
from types import FrameType

EXPECTED_BOOT_SHA256 = "UNRELEASED"
WINDOW_END_UTC = 0
EXPECTED_KERNEL = "7.1.6-1-1-ARCH"
KERNEL_BUILD_ID = "ed32884ffd7e862fbffbd30b12082d5e8297c420"
APPLE_BUILD_ID = "dd5e291114047bb4d7c83a529cddb4f4ac9292d7"
TIPD_BUILD_ID = "8fd9e3d39ee211f439471a812fb5eaa2622f7585"
TRACE_ROOT = Path("/sys/kernel/tracing")
TARGET = Path("/sys/devices/platform/soc/502280000.usb/power/runtime_status")
STARTUP_SECONDS = 15
CAPTURE_SECONDS = 120
WINDOW_RESERVE_SECONDS = 240
TRACE_LIMIT = 8 * 1024 * 1024
METADATA_LIMIT = 256 * 1024
KINDS = ("discover", "control", "suspend", "resume")
SIGNALS = (signal.SIGINT, signal.SIGTERM, signal.SIGHUP, signal.SIGALRM)


class Refusal(Exception):
  pass


@dataclass(frozen=True)
class Field:
  name: str
  kind: str
  fetch: str

  @property
  def width(self) -> int:
    return int(self.kind[1:]) // 8

  @property
  def signed(self) -> bool:
    return self.kind.startswith("s")


@dataclass(frozen=True)
class Probe:
  kind: str
  event: str
  definition: str
  fields: tuple[Field, ...]


@dataclass(frozen=True)
class Action:
  name: str
  kind: str = ""


@dataclass
class TraceState:
  token: str
  pid: int
  controller: int = 0
  instance_created: bool = False
  attempted: list[Action] = field(default_factory=list)
  journal_ordinal: int = 0
  target_read: bool = False

  @property
  def group(self) -> str:
    return f"dev147_usb_{self.token}"

  def event(self, kind: str) -> str:
    if kind not in KINDS:
      raise Refusal("unknown fixed event")
    return f"{kind}_{self.token}"


@dataclass(frozen=True)
class Record:
  kind: str
  timestamp: str
  values: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class ParsedTrace:
  records: tuple[Record, ...]
  limitations: str = "PM entry is not transition success; return is synchronous API result, not all URBs; identity joins can be ambiguous"


@dataclass(frozen=True)
class CleanupResult:
  completed: tuple[str, ...]
  failures: tuple[str, ...]

  @property
  def complete(self) -> bool:
    return not self.failures


@dataclass(frozen=True)
class Identity:
  kernel: str
  boot_sha256: str
  kernel_build_id: str
  apple_build_id: str
  tipd_build_id: str


@dataclass(frozen=True)
class GlobalTraceState:
  clock: str
  tracer: str
  gate: str
  events: str
  definitions_sha256: str


@dataclass(frozen=True)
class BoundedRead:
  data: bytes
  truncated: bool


def probes(state: TraceState) -> tuple[Probe, ...]:
  if re.fullmatch(r"[0-9a-f]{16}", state.token) is None or not 0 < state.pid < 1 << 31:
    raise Refusal("invalid owned names or PID")
  identity = (
    Field("device", "u64", "$arg1"), Field("bus", "u64", "+80($arg1)"),
    Field("sysdev", "u64", "+8(+80($arg1))"), Field("busnum", "s32", "+16(+80($arg1))"),
    Field("devnum", "s32", "+0($arg1)"),
  )
  setup = (
    Field("request", "u8", "$arg3"), Field("request_type", "u8", "$arg4"),
    Field("value", "u16", "$arg5"), Field("index", "u16", "$arg6"),
    Field("size", "u16", "$arg8"), Field("result", "s32", "$retval"),
  )
  specifications = (
    ("discover", "p", "runtime_status_show", identity[:1]),
    ("control", "r128", "usb_control_msg", identity + setup),
    ("suspend", "p", "usb_suspend_both", identity + (Field("message", "s32", "$arg2"),)),
    ("resume", "p", "usb_resume_both", identity + (Field("message", "s32", "$arg2"),)),
  )
  return tuple(Probe(kind, state.event(kind), f"{prefix}:{state.group}/{state.event(kind)} {symbol} " + " ".join(f"{item.name}={item.fetch}:{item.kind}" for item in fields), fields) for kind, prefix, symbol, fields in specifications)


def controller_filter(pointer: int) -> str:
  if type(pointer) is not int or not (0xffff000000000000 <= pointer < 1 << 64) or pointer % 8:
    raise Refusal("invalid controller pointer or incomplete identity")
  return f"sysdev == {pointer}"


def check_release(now: float) -> None:
  if re.fullmatch(r"[0-9a-f]{64}", EXPECTED_BOOT_SHA256) is None or not math.isfinite(now) or not WINDOW_RESERVE_SECONDS <= WINDOW_END_UTC - now <= 900:
    raise Refusal("UNRELEASED: private boot and attended window binding required")


def parse_build_id(data: bytes) -> str:
  identifiers: list[str] = []
  offset = 0
  while offset < len(data):
    if len(data) - offset < 12:
      raise Refusal("truncated ELF note")
    name_size, value_size, kind = struct.unpack_from("<III", data, offset)
    name_start = offset + 12
    value_start = name_start + (name_size + 3) // 4 * 4
    end = value_start + (value_size + 3) // 4 * 4
    if end > len(data):
      raise Refusal("truncated ELF note value")
    if data[name_start:name_start + name_size] == b"GNU\0" and kind == 3:
      if value_size != 20:
        raise Refusal("unexpected build identifier width")
      identifiers.append(data[value_start:value_start + value_size].hex())
    offset = end
  if len(identifiers) != 1:
    raise Refusal("missing or duplicate GNU build identifier")
  return identifiers[0]


def verify_mount(text: str) -> None:
  found = 0
  for line in text.splitlines():
    halves = line.split(" - ")
    if len(halves) != 2 or len(halves[0].split()) < 6 or len(halves[1].split()) < 3:
      raise Refusal("unparseable mount metadata")
    point = halves[0].split()[4]
    if point == str(TRACE_ROOT):
      if halves[1].split()[0] != "tracefs":
        raise Refusal("existing tracefs mount required")
      found += 1
    elif point.startswith(str(TRACE_ROOT) + "/"):
      raise Refusal("nested tracing mount refused")
  if found != 1:
    raise Refusal("exactly one existing tracefs mount required")


def verify_trace_idle(tracer: str, enabled: str, instances: tuple[str, ...], definitions: str, state: TraceState) -> None:
  probes(state)
  if tracer.strip() != "nop" or enabled.strip() != "0" or instances:
    raise Refusal("existing tracing activity or instances; no state changed")
  if state.group in definitions or any(state.event(kind) in definitions for kind in KINDS):
    raise Refusal("owned tracing name collision")


def verify_format(text: str, event_id: str, probe: Probe) -> None:
  if not re.fullmatch(r"[1-9][0-9]*\n?", event_id):
    raise Refusal("invalid event identifier")
  if re.findall(r"^name:\s*(\S+)\s*$", text, re.MULTILINE) != [probe.event] or re.findall(r"^ID:\s*(\d+)\s*$", text, re.MULTILINE) != [event_id.strip()]:
    raise Refusal("event name or identifier mismatch")
  rows = re.findall(r"field:([^;\n]+?)\s+(\w+);\s*offset:(\d+);\s*size:(\d+);\s*signed:(\d+);", text)
  expected = [("unsigned short", "common_type", "0", "2", "0"), ("unsigned char", "common_flags", "2", "1", "0"), ("unsigned char", "common_preempt_count", "3", "1", "0"), ("int", "common_pid", "4", "4", "1")]
  if probe.kind == "control":
    expected.extend((("unsigned long", "__probe_func", "8", "8", "0"), ("unsigned long", "__probe_ret_ip", "16", "8", "0")))
  else:
    expected.append(("unsigned long", "__probe_ip", "8", "8", "0"))
  offset = 24 if probe.kind == "control" else 16
  for item in probe.fields:
    expected.append((item.kind, item.name, str(offset), str(item.width), str(int(item.signed))))
    offset += item.width
  if rows != expected or text.count("field:") != len(rows):
    raise Refusal("event fields differ from fixed signed packed layout")


def _records(text: str, allowed: tuple[Probe, ...]) -> tuple[tuple[Probe, str, int, tuple[tuple[str, int], ...]], ...]:
  if len(text.encode("ascii")) > TRACE_LIMIT:
    raise Refusal("trace exceeds byte limit")
  rows: list[tuple[Probe, str, int, tuple[tuple[str, int], ...]]] = []
  by_name = {probe.event: probe for probe in allowed}
  for line in text.splitlines():
    if not line.strip() or line.startswith("#"):
      continue
    match = re.fullmatch(r"\s*[^\n]+-(\d+)\s+\[(\d+)\]\s+\S+\s+(\d+\.\d+):\s+(\w+):\s+\([^\n]*\)\s+(.+)", line)
    if match is None or match[4] not in by_name or int(match[2]) >= 16:
      raise Refusal("malformed, lost or off-scope trace record")
    probe = by_name[match[4]]
    chunks = match[5].split()
    if len(chunks) != len(probe.fields):
      raise Refusal("trace field count mismatch")
    values: list[tuple[str, int]] = []
    for item, chunk in zip(probe.fields, chunks, strict=True):
      pair = re.fullmatch(rf"{re.escape(item.name)}=(-?[0-9]+)", chunk)
      if pair is None:
        raise Refusal("trace field syntax or numeric fetch failure")
      value = int(pair[1])
      lower = -(1 << (item.width * 8 - 1)) if item.signed else 0
      upper = (1 << (item.width * 8 - int(item.signed))) - 1
      if not lower <= value <= upper:
        raise Refusal("trace numeric field outside width")
      values.append((item.name, value))
    rows.append((probe, match[3], int(match[1]), tuple(values)))
  return tuple(rows)


def parse_discovery(text: str, state: TraceState) -> int:
  rows = _records(text, probes(state)[:1])
  if len(rows) != 1 or rows[0][2] != state.pid:
    raise Refusal("discovery requires exactly one own-PID event")
  pointer = rows[0][3][0][1]
  controller_filter(pointer)
  return pointer


def parse_measurements(text: str, state: TraceState, controller: int) -> ParsedTrace:
  controller_filter(controller)
  records: list[Record] = []
  for probe, timestamp, pid, values in _records(text, probes(state)[1:]):
    del pid
    fields = dict(values)
    if fields["sysdev"] != controller or fields["device"] == 0 or fields["bus"] == 0 or not 0 < fields["busnum"] < 1 << 31 or not 0 <= fields["devnum"] <= 127:
      raise Refusal("off-controller or incomplete USB identity")
    records.append(Record(probe.kind, timestamp, values))
  return ParsedTrace(tuple(records))


def verify_profile(text: str, selected: tuple[Probe, ...], discovery: bool = False) -> None:
  for probe in selected:
    rows = [line.split() for line in text.splitlines() if line.split() and line.split()[0] == probe.event]
    if len(rows) != 1 or len(rows[0]) != 3 or not all(value.isdigit() for value in rows[0][1:]) or int(rows[0][2]) != 0 or (discovery and int(rows[0][1]) < 1):
      raise Refusal("missing, ambiguous or nonzero probe loss profile")


def verify_cpu_stats(text: str) -> None:
  for name in ("overrun", "commit overrun", "dropped events"):
    if re.findall(rf"^{name}:\s*(\d+)\s*$", text, re.MULTILINE) != ["0"]:
      raise Refusal("missing, duplicated or nonzero ring loss counter")


def cpu_names(names: tuple[str, ...]) -> tuple[str, ...]:
  if not 1 <= len(names) <= 16 or len(set(names)) != len(names) or any(re.fullmatch(r"cpu(?:[0-9]|1[0-5])", name) is None for name in names):
    raise Refusal("unexpected CPU set or more than 16 CPU buffers")
  return tuple(sorted(names))


def remaining_seconds(start: float, now: float, limit: int) -> float:
  remaining = limit - (now - start)
  if limit not in (STARTUP_SECONDS, CAPTURE_SECONDS) or not math.isfinite(remaining) or not 0 < remaining <= limit:
    raise Refusal("cooperative deadline expired or monotonic clock invalid")
  return remaining


def open_checked(path: Path, flags: int, directory: bool = False) -> int:
  if not path.is_absolute() or ".." in path.parts or len(path.parts) < 2:
    raise Refusal("unsafe absolute path")
  current = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
  descriptor = -1
  try:
    for part in path.parts[1:-1]:
      child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=current)
      os.close(current)
      current = child
      info = os.fstat(current)
      if info.st_uid != 0 or info.st_mode & 0o022:
        raise Refusal("unsafe ancestor ownership or permissions")
    before = os.stat(path.name, dir_fd=current, follow_symlinks=False)
    if before.st_uid != 0 or before.st_mode & 0o022 or not (stat.S_ISDIR(before.st_mode) if directory else stat.S_ISREG(before.st_mode)):
      raise Refusal("unsafe file metadata before open")
    descriptor = os.open(path.name, flags | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK, dir_fd=current)
    info = os.fstat(descriptor)
    if info.st_uid != 0 or info.st_mode & 0o022 or (before.st_dev, before.st_ino) != (info.st_dev, info.st_ino) or not (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode)):
      raise Refusal("unsafe file type, ownership or permissions")
    returned, descriptor = descriptor, -1
    return returned
  except OSError as error:
    raise Refusal(f"path open refused: {path}, errno={error.errno}") from error
  finally:
    if descriptor >= 0:
      os.close(descriptor)
    os.close(current)


def read_bounded(path: Path, limit: int) -> BoundedRead:
  if not 0 < limit <= TRACE_LIMIT:
    raise Refusal("invalid read bound")
  descriptor = open_checked(path, os.O_RDONLY)
  chunks: list[bytes] = []
  total = 0
  try:
    while total <= limit:
      chunk = os.read(descriptor, min(65536, limit + 1 - total))
      if not chunk:
        return BoundedRead(b"".join(chunks), False)
      total += len(chunk)
      chunks.append(chunk)
    return BoundedRead(b"".join(chunks)[:limit], True)
  finally:
    os.close(descriptor)


def read_regular(path: Path, limit: int) -> bytes:
  result = read_bounded(path, limit)
  if result.truncated:
    raise Refusal("read exceeded bound")
  return result.data


def text(path: Path, limit: int = 65536) -> str:
  try:
    return read_regular(path, limit).decode("ascii")
  except UnicodeError as error:
    raise Refusal("non-ASCII metadata or trace") from error


def directory_names(path: Path) -> tuple[str, ...]:
  descriptor = open_checked(path, os.O_RDONLY | os.O_DIRECTORY, True)
  try:
    names = tuple(os.listdir(descriptor))
    if len(names) > 4096:
      raise Refusal("directory entry bound exceeded")
    return names
  finally:
    os.close(descriptor)


def save_new(directory: Path, name: str, value: object) -> None:
  if re.fullmatch(r"[a-z0-9][a-z0-9_.-]{0,95}", name) is None:
    raise Refusal("invalid evidence filename")
  payload = value if isinstance(value, bytes) else (json.dumps(value, sort_keys=True) + "\n").encode("ascii")
  if len(payload) > TRACE_LIMIT:
    raise Refusal("evidence exceeds byte bound")
  parent = open_checked(directory, os.O_RDONLY | os.O_DIRECTORY, True)
  try:
    descriptor = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600, dir_fd=parent)
    with os.fdopen(descriptor, "wb") as target:
      target.write(payload)
      target.flush()
      os.fsync(target.fileno())
    os.fsync(parent)
  finally:
    os.close(parent)


def write_control(path: Path, value: str, append: bool = False, truncate: bool = False) -> None:
  flags = os.O_WRONLY | (os.O_APPEND if append else 0) | (os.O_TRUNC if truncate else 0)
  descriptor = open_checked(path, flags)
  try:
    payload = (value + "\n").encode("ascii")
    if os.write(descriptor, payload) != len(payload):
      raise Refusal("partial control write")
  finally:
    os.close(descriptor)


def own_definitions(definitions: str, state: TraceState, kind: str) -> tuple[str, ...]:
  key = f"{state.group}/{state.event(kind)}"
  return tuple(line.strip() for line in definitions.splitlines() if line.split() and line.split()[0].partition(":")[2] == key)


@dataclass
class TraceFiles:
  root: Path
  evidence: Path
  state: TraceState
  journal_failures: list[str] = field(default_factory=list)

  @property
  def instance(self) -> Path:
    return self.root / "instances" / self.state.group

  def event_root(self, kind: str) -> Path:
    return self.instance / "events" / self.state.group / self.state.event(kind)

  def record(self, action: Action, phase: str) -> None:
    self.state.journal_ordinal += 1
    save_new(self.evidence, f"action-{self.state.journal_ordinal:04}.json", {"action": asdict(action), "phase": phase, "monotonic_ns": time.monotonic_ns()})

  def record_action(self, action: Action, phase: str, safety_cleanup: bool) -> None:
    try:
      self.record(action, phase)
    except (Refusal, OSError) as error:
      if not safety_cleanup:
        raise
      self.journal_failures.append(f"journal:{action.name}:{phase}:{type(error).__name__}")

  def perform(self, action: Action, safety_cleanup: bool = False) -> None:
    available = {probe.kind: probe for probe in probes(self.state)}
    if safety_cleanup and action.name not in ("stop", "disable", "remove", "undefine", "retain"):
      raise Refusal("cleanup override cannot activate or configure tracing")
    if not safety_cleanup:
      self.record_action(action, "attempted", False)
    self.state.attempted.append(action)
    if action.name in ("create", "remove"):
      parent = open_checked(self.root / "instances", os.O_RDONLY | os.O_DIRECTORY, True)
      blocked = signal.pthread_sigmask(signal.SIG_BLOCK, set(SIGNALS))
      try:
        if action.name == "create":
          os.mkdir(self.state.group, mode=0o700, dir_fd=parent)
          self.state.instance_created = True
        else:
          os.rmdir(self.state.group, dir_fd=parent)
          self.state.instance_created = False
      finally:
        os.close(parent)
        signal.pthread_sigmask(signal.SIG_SETMASK, blocked)
    elif action.name in ("define", "undefine") and action.kind in available:
      probe = available[action.kind]
      existing = own_definitions(text(self.root / "kprobe_events", 1024 * 1024), self.state, action.kind)
      if action.name == "define":
        if existing:
          raise Refusal("probe name already exists")
        write_control(self.root / "kprobe_events", probe.definition, append=True)
      else:
        if existing != (probe.definition,):
          raise Refusal("changed or missing definition; retained")
        write_control(self.root / "kprobe_events", f"-:{self.state.group}/{probe.event}", append=True)
    elif action.name in ("stop", "start", "buffer", "clock", "pid", "clear_pid", "clear"):
      controls = {"stop": ("tracing_on", "0"), "start": ("tracing_on", "1"), "buffer": ("buffer_size_kb", "64"), "clock": ("trace_clock", "mono"), "pid": ("set_event_pid", str(self.state.pid)), "clear_pid": ("set_event_pid", ""), "clear": ("trace", "")}
      if action.name in ("clear_pid", "clear"):
        if text(self.instance / "tracing_on").strip() != "0" or text(self.event_root("discover") / "enable").strip() != "0":
          raise Refusal("discovery must stop before changing instance filters or buffer")
        if action.name == "clear_pid":
          for kind in KINDS[1:]:
            self.verify_filter(kind)
      relative, value = controls[action.name]
      write_control(self.instance / relative, value, truncate=action.name in ("clear_pid", "clear"))
      if action.name in ("stop", "start") and text(self.instance / relative).strip() != value:
        raise Refusal("private tracing gate readback mismatch")
    elif action.name == "filter" and action.kind in KINDS[1:]:
      write_control(self.event_root(action.kind) / "filter", controller_filter(self.state.controller))
      self.verify_filter(action.kind)
    elif action.name in ("enable", "disable") and action.kind in available:
      if action.name == "enable":
        if action.kind == "discover":
          if text(self.instance / "set_event_pid").split() != [str(self.state.pid)]:
            raise Refusal("own PID restriction missing")
        else:
          self.verify_filter(action.kind)
      write_control(self.event_root(action.kind) / "enable", "1" if action.name == "enable" else "0")
      if text(self.event_root(action.kind) / "enable").strip() != ("1" if action.name == "enable" else "0"):
        raise Refusal("owned event gate readback mismatch")
    elif action.name == "read_target":
      if self.state.target_read:
        raise Refusal("second discovery read forbidden")
      self.state.target_read = True
      descriptor = open_checked(TARGET, os.O_RDONLY)
      try:
        result = os.read(descriptor, 128)
      finally:
        os.close(descriptor)
      if result not in (b"active\n", b"suspended\n", b"suspending\n", b"resuming\n", b"unsupported\n", b"error\n"):
        raise Refusal("unexpected discovery status read")
      save_new(self.evidence, "target-status.json", {"status": result.decode("ascii").strip()})
    else:
      raise Refusal("unknown or refused owned action")
    self.record_action(action, "completed", safety_cleanup)

  def verify_filter(self, kind: str) -> None:
    if text(self.event_root(kind) / "filter").strip() != controller_filter(self.state.controller):
      raise Refusal("controller filter readback mismatch")


def cleanup_plan(state: TraceState, definitions: str) -> tuple[Action, ...]:
  actions: list[Action] = []
  if state.instance_created:
    actions.append(Action("stop"))
    actions.extend(Action("disable", kind) for kind in KINDS if Action("enable", kind) in state.attempted)
    actions.append(Action("remove"))
  for probe in probes(state):
    if Action("define", probe.kind) in state.attempted:
      existing = own_definitions(definitions, state, probe.kind)
      if existing:
        actions.append(Action("undefine" if existing == (probe.definition,) else "retain", probe.kind))
  return tuple(actions)


def interrupted(number: int, frame: FrameType | None) -> None:
  del number, frame
  raise Refusal("interrupted or cooperative deadline expired")


@contextmanager
def cooperative_limit(seconds: float) -> Iterator[None]:
  signal.setitimer(signal.ITIMER_REAL, seconds)
  try:
    yield
  finally:
    signal.setitimer(signal.ITIMER_REAL, 0)


def cleanup(files: TraceFiles) -> CleanupResult:
  completed: list[str] = []
  failures: list[str] = []

  def attempt(action: Action) -> None:
    try:
      with cooperative_limit(2):
        files.perform(action, safety_cleanup=True)
      completed.append(f"{action.name}:{action.kind}")
    except (Refusal, OSError) as error:
      failures.append(f"{action.name}:{action.kind}:{type(error).__name__}")

  for action in cleanup_plan(files.state, ""):
    attempt(action)
  try:
    with cooperative_limit(2):
      definitions = text(files.root / "kprobe_events", 1024 * 1024)
    for action in cleanup_plan(files.state, definitions):
      if action.name in ("undefine", "retain"):
        attempt(action)
  except (Refusal, OSError):
    failures.append("definition cleanup could not be selected")
  try:
    with cooperative_limit(2):
      definitions = text(files.root / "kprobe_events", 1024 * 1024)
      if any(own_definitions(definitions, files.state, kind) for kind in KINDS):
        failures.append("owned definition remains")
      if files.state.group in directory_names(files.root / "instances"):
        failures.append("owned instance remains")
  except (Refusal, OSError):
    failures.append("cleanup absence readback failed")
  return CleanupResult(tuple(completed), tuple(failures + files.journal_failures))


def retain_partial_capture(files: TraceFiles) -> tuple[str, ...]:
  failures: list[str] = []
  if not files.state.instance_created:
    return ()
  for action in cleanup_plan(files.state, ""):
    if action.name not in ("stop", "disable"):
      continue
    try:
      with cooperative_limit(2):
        files.perform(action, safety_cleanup=True)
    except (Refusal, OSError) as error:
      failures.append(f"partial-stop:{action.name}:{type(error).__name__}")
  try:
    with cooperative_limit(15):
      if "capture.trace" not in directory_names(files.evidence) and files.state.controller:
        collect_phase(files, "capture", probes(files.state)[1:])
  except (Refusal, OSError) as error:
    failures.append(f"partial-evidence:{type(error).__name__}")
  return tuple(failures)


def identity() -> Identity:
  if os.uname().machine != "aarch64" or os.uname().release != EXPECTED_KERNEL:
    raise Refusal("kernel or architecture mismatch")
  result = Identity(EXPECTED_KERNEL, hashlib.sha256(read_regular(Path("/proc/sys/kernel/random/boot_id"), 128)).hexdigest(), parse_build_id(read_regular(Path("/sys/kernel/notes"), 65536)), parse_build_id(read_regular(Path("/sys/module/appledrm/notes/.note.gnu.build-id"), 64)), parse_build_id(read_regular(Path("/sys/module/tps6598x_core/notes/.note.gnu.build-id"), 64)))
  if result != Identity(EXPECTED_KERNEL, EXPECTED_BOOT_SHA256, KERNEL_BUILD_ID, APPLE_BUILD_ID, TIPD_BUILD_ID):
    raise Refusal("boot, kernel or loaded display module binding mismatch")
  return result


def global_trace_state(root: Path) -> GlobalTraceState:
  return GlobalTraceState(text(root / "trace_clock"), text(root / "current_tracer"), text(root / "tracing_on"), text(root / "events/enable"), hashlib.sha256(read_regular(root / "kprobe_events", 1024 * 1024)).hexdigest())


def verify_stack_options(files: TraceFiles) -> None:
  for name in ("stacktrace", "userstacktrace"):
    if text(files.instance / "options" / name, 16) != "0\n":
      raise Refusal("inherited stack capture option is not exactly disabled")
  save_new(files.evidence, "stack-options.json", {"stacktrace": 0, "userstacktrace": 0})


def verify_probe(files: TraceFiles, kind: str) -> None:
  probe = next(probe for probe in probes(files.state) if probe.kind == kind)
  if own_definitions(text(files.root / "kprobe_events", 1024 * 1024), files.state, kind) != (probe.definition,):
    raise Refusal("probe definition readback mismatch")
  event_format = text(files.event_root(kind) / "format")
  event_id = text(files.event_root(kind) / "id")
  verify_format(event_format, event_id, probe)
  save_new(files.evidence, f"format-{kind}.json", {"format": event_format, "id": event_id, "definition": probe.definition})


def collect_phase(files: TraceFiles, name: str, selected: tuple[Probe, ...]) -> str:
  bounded = read_bounded(files.instance / "trace", 65536 if name == "discovery" else TRACE_LIMIT)
  raw = bounded.data
  save_new(files.evidence, f"{name}.trace", raw)
  save_new(files.evidence, f"{name}-bytes.json", {"bytes": len(raw), "truncated": bounded.truncated, "sha256": hashlib.sha256(raw).hexdigest()})
  profile = text(files.root / "kprobe_profile", 1024 * 1024)
  own_profile = "\n".join(line for line in profile.splitlines() if line.split() and line.split()[0] in {probe.event for probe in selected}) + "\n"
  save_new(files.evidence, f"{name}-profile.json", {"profile": own_profile})
  errors = ["trace truncated at byte bound"] if bounded.truncated else []
  try:
    verify_profile(own_profile, selected, discovery=name == "discovery")
  except Refusal as error:
    errors.append(str(error))
  for cpu in cpu_names(directory_names(files.instance / "per_cpu")):
    statistics = text(files.instance / "per_cpu" / cpu / "stats")
    save_new(files.evidence, f"{name}-{cpu}.json", {"stats": statistics})
    try:
      verify_cpu_stats(statistics)
    except Refusal as error:
      errors.append(f"{cpu}: {error}")
  if errors:
    raise Refusal("; ".join(errors))
  try:
    return raw.decode("ascii")
  except UnicodeError as error:
    raise Refusal("non-ASCII raw trace retained") from error


def phase(status: str, message: str, evidence: Path | None = None) -> None:
  result = {"level": "info" if status in ("PREPARED", "ARMED", "CAPTURED") else "error", "status": status, "message": message}
  if evidence is not None:
    result["evidence"] = str(evidence)
  print(json.dumps(result, sort_keys=True), file=sys.stderr, flush=True)


def export_evidence(directory: Path) -> None:
  names = tuple(sorted(directory_names(directory)))
  if len(names) > 512:
    raise Refusal("evidence file count exceeds export bound")
  metadata = 0
  trace_bytes = 0
  payloads: list[tuple[str, bytes]] = []
  for name in names:
    if re.fullmatch(r"[a-z0-9][a-z0-9_.-]{0,95}", name) is None:
      raise Refusal("unknown evidence file name")
    data = read_regular(directory / name, TRACE_LIMIT if name.endswith(".trace") else METADATA_LIMIT)
    if name.endswith(".trace"):
      trace_bytes += len(data)
    else:
      metadata += len(data)
    if trace_bytes > TRACE_LIMIT + 65536 or metadata > METADATA_LIMIT:
      raise Refusal("total evidence exceeds export bound; root-private files retained")
    payloads.append((name, data))
  for name, data in payloads:
    header = f"BEGIN {name} {len(data)} {hashlib.sha256(data).hexdigest()}\n".encode("ascii")
    sys.stdout.buffer.write(header + data + f"\nEND {name}\n".encode("ascii"))
  sys.stdout.buffer.flush()


def run_bound_capture() -> int:
  check_release(time.time())
  handlers = {number: signal.signal(number, interrupted) for number in SIGNALS}
  start = time.monotonic()
  signal.setitimer(signal.ITIMER_REAL, STARTUP_SECONDS)
  try:
    return run_with_deadline(start)
  finally:
    signal.setitimer(signal.ITIMER_REAL, 0)
    for number, handler in handlers.items():
      signal.signal(number, handler)


def run_with_deadline(startup_start: float) -> int:
  check_release(time.time())
  if os.geteuid() != 0:
    raise Refusal("manually invoked root required")
  initial_identity = identity()
  verify_mount(text(Path(f"/proc/{os.getpid()}/mountinfo"), 1024 * 1024))
  state = TraceState(secrets.token_hex(8), os.getpid())
  verify_trace_idle(text(TRACE_ROOT / "current_tracer"), text(TRACE_ROOT / "events/enable"), directory_names(TRACE_ROOT / "instances"), text(TRACE_ROOT / "kprobe_events", 1024 * 1024), state)
  global_before = global_trace_state(TRACE_ROOT)
  target_descriptor = open_checked(TARGET, os.O_PATH)
  try:
    target_before = os.fstat(target_descriptor)
  finally:
    os.close(target_descriptor)
  os.close(open_checked(Path("/run"), os.O_RDONLY | os.O_DIRECTORY, True))
  evidence = Path(tempfile.mkdtemp(prefix="dev147-usb-", dir="/run"))
  files = TraceFiles(TRACE_ROOT, evidence, state)
  save_new(evidence, "recovery.json", {"same_boot_sha256": EXPECTED_BOOT_SHA256, "instance": str(files.instance), "definitions": [probe.definition for probe in probes(state)], "event_disable_paths": [str(files.event_root(kind) / "enable") for kind in KINDS], "stop_path": str(files.instance / "tracing_on"), "removal": "rmdir exact owned instance; append -:group/event only after exact definition and disabled readback", "warning": "No retry or automatic rearm. SIGKILL, power loss or uninterruptible kernel calls can prevent cleanup. Never clear global tracing. Ask owner to review exact retained paths."})
  save_new(evidence, "identity-before.json", asdict(initial_identity))
  save_new(evidence, "global-before.json", asdict(global_before))
  phase("PREPARED", "Owned recovery metadata is saved; no cable action yet.", evidence)
  failures: list[str] = []
  result: ParsedTrace | None = None
  cleanup_result = CleanupResult((), ("cleanup not attempted",))
  try:
    with cooperative_limit(remaining_seconds(startup_start, time.monotonic(), STARTUP_SECONDS)):
      for action in (Action("create"), Action("stop"), Action("buffer"), Action("clock"), Action("pid"), Action("define", "discover")):
        files.perform(action)
      if text(files.instance / "current_tracer").strip() != "nop" or text(files.instance / "buffer_size_kb").strip() != "64" or "[mono]" not in text(files.instance / "trace_clock").split():
        raise Refusal("private instance settings readback mismatch")
      cpu_names(directory_names(files.instance / "per_cpu"))
      verify_stack_options(files)
      verify_probe(files, "discover")
      for action in (Action("enable", "discover"), Action("start"), Action("read_target"), Action("stop"), Action("disable", "discover")):
        files.perform(action)
      if text(files.instance / "tracing_on").strip() != "0" or text(files.event_root("discover") / "enable").strip() != "0":
        raise Refusal("discovery did not stop")
      state.controller = parse_discovery(collect_phase(files, "discovery", probes(state)[:1]), state)
      for kind in KINDS[1:]:
        files.perform(Action("define", kind))
        verify_probe(files, kind)
        files.perform(Action("filter", kind))
      files.perform(Action("clear"))
      files.perform(Action("clear_pid"))
      if text(files.instance / "set_event_pid").strip() not in ("", "no pid"):
        raise Refusal("discovery PID restriction did not clear")
      for kind in KINDS[1:]:
        files.perform(Action("enable", kind))
      check_release(time.time())
    with cooperative_limit(CAPTURE_SECONDS + 1):
      files.perform(Action("start"))
      start = time.monotonic()
      phase("ARMED", "Within 120 seconds: disconnect the monitor USB-C cable once, wait five seconds, reconnect the same cable to the same lower-left port. Do not repeat.", evidence)
      while True:
        remaining = CAPTURE_SECONDS - (time.monotonic() - start)
        if remaining <= 0:
          break
        time.sleep(min(0.25, remaining))
    with cooperative_limit(15):
      files.perform(Action("stop"))
      for kind in KINDS[1:]:
        files.perform(Action("disable", kind))
      if text(files.instance / "tracing_on").strip() != "0" or any(text(files.event_root(kind) / "enable").strip() != "0" for kind in KINDS):
        raise Refusal("measurement did not stop")
      result = parse_measurements(collect_phase(files, "capture", probes(state)[1:]), state, state.controller)
      save_new(evidence, "identity-after.json", asdict(identity()))
      descriptor = open_checked(TARGET, os.O_PATH)
      try:
        target_after = os.fstat(descriptor)
      finally:
        os.close(descriptor)
      if (target_before.st_dev, target_before.st_ino) != (target_after.st_dev, target_after.st_ino):
        raise Refusal("fixed controller identity changed")
  except (Refusal, OSError, UnicodeError, ValueError) as error:
    failures.append(f"{type(error).__name__}: {error}")
  finally:
    blocked = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGINT, signal.SIGTERM, signal.SIGHUP})
    signal.setitimer(signal.ITIMER_REAL, 0)
    try:
      if failures:
        failures.extend(retain_partial_capture(files))
      cleanup_result = cleanup(files)
    finally:
      for number in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        if number in signal.sigpending():
          signal.sigwait({number})
          failures.append(f"signal {number} deferred during cleanup")
      signal.pthread_sigmask(signal.SIG_SETMASK, blocked)
  complete = result is not None and not failures and cleanup_result.complete
  try:
    with cooperative_limit(15):
      global_after = global_trace_state(TRACE_ROOT)
      save_new(evidence, "global-after.json", asdict(global_after))
      if global_after != global_before:
        failures.append("global tracing state drifted; no restoration attempted")
        complete = False
      save_new(evidence, "result.json", {"status": "CAPTURED" if complete else "INCOMPLETE", "failures": failures, "cleanup": asdict(cleanup_result), "records": len(result.records) if result else 0, "limitations": "No all-call completeness or hardware-fix claim. Filters follow raw pointer identity; fetch failures, pointer reuse, unfinished calls and untraced URBs remain possible. PM entries are not outcomes."})
      export_evidence(evidence)
  except (Refusal, OSError) as error:
    phase("INCOMPLETE", f"Evidence save/export failed after cleanup; cleanup_complete={cleanup_result.complete}; {type(error).__name__}. Do not retry.", evidence)
    return 1
  phase("CAPTURED" if complete else "INCOMPLETE", "Review saved records and cleanup before any further action. No automatic retry.", evidence)
  return 0 if complete else 1


def main() -> int:
  if len(sys.argv) != 1:
    phase("REFUSED", "arguments are not accepted")
    return 64
  try:
    check_release(time.time())
  except Refusal as error:
    phase("UNRELEASED", str(error))
    return 77
  try:
    return run_bound_capture()
  except (Refusal, OSError) as error:
    phase("REFUSED", f"{type(error).__name__}: {error}")
    return 1


if __name__ == "__main__":
  raise SystemExit(main())
