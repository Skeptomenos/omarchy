#!/usr/bin/python3
"""One-boot, one-open Apple DCP crash-flag observation; live use is locked."""

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
from dataclasses import asdict, dataclass
from pathlib import Path
from types import FrameType

EXPECTED_BOOT_SHA256 = "PRIVATE_BOOT_SHA256_NOT_SET"
EXPECTED_KERNEL = "7.1.6-1-1-ARCH"
APPLE_MODULE_SHA256 = "dbffe74e13a43e15e47fdc5eafe32eb1829b114a3f02f15fe6b18507d622b0e3"
APPLE_BUILD_ID = "dd5e291114047bb4d7c83a529cddb4f4ac9292d7"
TIPD_BUILD_ID = "40aa54382047ba36b02c9ac0da65a213862a77ad"
TARGET = Path("/sys/kernel/debug/dri/2/DP-1/ColorElements")
TRACE_ROOT = Path("/sys/kernel/tracing")
DRM_ROOT = Path("/sys/devices/platform/soc/soc:display-subsystem/drm/card2")
MODULE = Path(f"/usr/lib/modules/{EXPECTED_KERNEL}/kernel/drivers/gpu/drm/apple/appledrm.ko")
DEADLINE_SECONDS = 10
PROBE_FETCH = (
  "appledrm:chunk_color_open+0x1c "
  "crashed=+64(+136(+2256(%x2))):u8 "
  "connector_type=+14140(+136(+2256(%x2))):s32"
)


class Refusal(Exception):
  """A failed safety or evidence check; never a diagnostic PASS."""


@dataclass(frozen=True)
class Identity:
  kernel: str
  boot_sha256: str
  module_sha256: str
  apple_build_id: str
  tipd_build_id: str


@dataclass(frozen=True)
class Observation:
  crashed: int
  connector_type: int
  pid: int


@dataclass(frozen=True)
class Action:
  name: str
  value: str = ""


@dataclass(frozen=True)
class CleanupResult:
  operations: tuple[str, ...]
  failures: tuple[str, ...]


@dataclass(frozen=True)
class TraceEvidence:
  raw_sha256: str
  raw_bytes: int
  sanitized_text: str
  content_label: str = "sanitized trace, not raw trace"


@dataclass
class TraceState:
  group: str
  event: str
  instance: str
  pid: int
  definition_attempted: bool = False
  instance_created: bool = False
  event_enable_attempted: bool = False
  trace_enable_attempted: bool = False

  @property
  def definition(self) -> str:
    return f"p:{self.group}/{self.event} {PROBE_FETCH}"

  @property
  def serialized_definition(self) -> str:
    return self.definition.replace("chunk_color_open+0x1c", "chunk_color_open+28")


def verify_identity(identity: Identity, expected_boot: str) -> None:
  if not re.fullmatch(r"[0-9a-f]{64}", expected_boot):
    raise Refusal("private boot binding missing")
  if identity != Identity(EXPECTED_KERNEL, expected_boot, APPLE_MODULE_SHA256, APPLE_BUILD_ID, TIPD_BUILD_ID):
    raise Refusal("kernel, boot, or module identity mismatch")


def parse_build_id(data: bytes) -> str:
  if len(data) != 36 or struct.unpack("<III", data[:12]) != (4, 20, 3) or data[12:16] != b"GNU\0":
    raise Refusal("unexpected GNU note")
  return data[16:].hex()


def parse_mounts(text: str) -> None:
  required = {"/sys/kernel/tracing": "tracefs", "/sys/kernel/debug": "debugfs"}
  seen: set[str] = set()
  for line in text.splitlines():
    halves = line.split(" - ")
    if len(halves) != 2 or len(halves[0].split()) < 6 or len(halves[1].split()) < 3:
      raise Refusal("unparseable mount table")
    point = halves[0].split()[4]
    if point in required:
      if point in seen or halves[1].split()[0] != required[point]:
        raise Refusal("unexpected tracing/debug mount")
      seen.add(point)
    elif any(point.startswith(root + "/") for root in required):
      raise Refusal("nested mount under tracing/debug root")
  if seen != set(required):
    raise Refusal("preexisting tracefs and debugfs mounts required")


def parse_event(text: str, state: TraceState) -> Observation:
  records = [line for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]
  if len(records) != 1:
    raise Refusal("expected exactly one trace record")
  pattern = (
    rf"\s*[^\n]+-(\d+)\s+\[\d+\]\s+\S+\s+\d+\.\d+:\s+{re.escape(state.event)}:\s+"
    r"\([^\n]*\)\s+crashed=(0|1)\s+connector_type=(10)\s*"
  )
  match = re.fullmatch(pattern, records[0])
  if match is None or int(match[1]) != state.pid:
    raise Refusal("unexpected PID, connector, flag, or trace syntax")
  return Observation(int(match[2]), int(match[3]), int(match[1]))


def sanitize_trace(text: str) -> TraceEvidence:
  raw = text.encode("ascii")
  if len(raw) > 512 * 1024:
    raise Refusal("trace evidence exceeded bound")
  sanitized = re.sub(r"\([^\n]*?\)", "(<probe-site-redacted>)", text)
  sanitized = re.sub(r"(?i)\b(?:0x[0-9a-f]+|[0-9a-f]{8,})\b", "<hex-redacted>", sanitized)
  return TraceEvidence(hashlib.sha256(raw).hexdigest(), len(raw), sanitized)


def verify_profile(text: str, state: TraceState) -> None:
  rows = [line.split() for line in text.splitlines() if line.split() and line.split()[0] == state.event]
  if rows != [[state.event, "1", "0"]]:
    raise Refusal("probe profile is not one hit and zero misses")


def verify_cpu_stats(text: str) -> None:
  for name in ("overrun", "commit overrun", "dropped events"):
    matches = re.findall(rf"^{re.escape(name)}:\s*(\d+)\s*$", text, re.MULTILINE)
    if matches != ["0"]:
      raise Refusal("missing or nonzero per-CPU loss counter")


def verify_format(text: str, event_id: str, state: TraceState) -> None:
  if not event_id.strip().isdigit() or int(event_id) <= 0:
    raise Refusal("invalid event ID")
  if re.findall(r"^name:\s*(\S+)\s*$", text, re.MULTILINE) != [state.event]:
    raise Refusal("event name mismatch")
  if re.findall(r"^ID:\s*(\d+)\s*$", text, re.MULTILINE) != [event_id.strip()]:
    raise Refusal("event ID mismatch")
  for field, field_type, offset, width, signed in (("crashed", "u8", "16", "1", "0"), ("connector_type", "s32", "17", "4", "1")):
    fields = re.findall(rf"field:(\S+)\s{field};\s*offset:(\d+);\s*size:(\d+);\s*signed:(\d+);", text)
    if fields != [(field_type, offset, width, signed)]:
      raise Refusal("numeric event field format mismatch")


def _validate_names(state: TraceState) -> None:
  match = re.fullmatch(r"dev147_cf_([0-9a-f]{16})", state.group)
  if match is None or state.instance != state.group or state.event != f"observe_{match[1]}" or state.pid <= 0:
    raise Refusal("invalid owned tracing names or PID")


def _own_definitions(text: str, state: TraceState) -> list[str]:
  return [line.strip() for line in text.splitlines() if line.split() and line.split()[0].partition(":")[2] == f"{state.group}/{state.event}"]


def setup_actions(state: TraceState, definitions: str, instances: tuple[str, ...]) -> tuple[Action, ...]:
  _validate_names(state)
  if state.group in definitions or state.event in definitions or state.instance in instances:
    raise Refusal("owned name collision")
  return (
    Action("create_instance"), Action("stop_trace"), Action("set_buffer", "16"),
    Action("set_pid", str(state.pid)), Action("append_definition", state.definition),
    Action("enable_event"), Action("start_trace"), Action("open_target_once"),
    Action("stop_trace"), Action("disable_event"),
  )


def cleanup_actions(state: TraceState, definitions: str) -> tuple[Action, ...]:
  _validate_names(state)
  actions: list[Action] = []
  if state.instance_created:
    if state.trace_enable_attempted:
      actions.append(Action("stop_trace"))
    if state.event_enable_attempted:
      actions.append(Action("disable_event"))
    actions.append(Action("remove_instance"))
  if state.definition_attempted:
    own = _own_definitions(definitions, state)
    if own == [state.serialized_definition]:
      actions.append(Action("delete_definition", f"-:{state.group}/{state.event}"))
    elif own:
      actions.append(Action("refuse_definition_delete"))
  return tuple(actions)


def remaining_seconds(start: float, now: float) -> float:
  remaining = DEADLINE_SECONDS - (now - start)
  if not math.isfinite(remaining) or not 0 < remaining <= DEADLINE_SECONDS:
    raise Refusal("diagnostic deadline expired or clock invalid")
  return remaining


def _open_checked(path: Path, flags: int, owner: int = 0, directory: bool = False) -> int:
  """Walk absolute paths without symlinks; production ancestors must be root-only writable."""
  if not path.is_absolute() or ".." in path.parts or len(path.parts) < 2:
    raise Refusal("unsafe path")
  current = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
  try:
    for part in path.parts[1:-1]:
      next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=current)
      os.close(current)
      current = next_fd
      info = os.fstat(current)
      if info.st_uid not in (0, owner) or (owner == 0 and info.st_mode & 0o022):
        raise Refusal("unsafe ancestor ownership or permissions")
    fd = os.open(path.name, flags | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK, dir_fd=current)
    info = os.fstat(fd)
    acceptable = stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode)
    if info.st_uid != owner or not acceptable or (owner == 0 and info.st_mode & 0o022):
      os.close(fd)
      raise Refusal("unexpected file type, ownership, or permissions")
    return fd
  except OSError as error:
    raise Refusal("safe path open refused") from error
  finally:
    os.close(current)


def read_regular(path: Path, limit: int, owner: int = 0) -> bytes:
  if limit <= 0:
    raise Refusal("invalid read bound")
  with os.fdopen(_open_checked(path, os.O_RDONLY, owner), "rb") as source:
    data = source.read(limit + 1)
  if len(data) > limit:
    raise Refusal("read exceeded bound")
  return data


def _text(path: Path, limit: int = 65536, owner: int = 0) -> str:
  try:
    return read_regular(path, limit, owner).decode("ascii")
  except UnicodeError as error:
    raise Refusal("unexpected non-ASCII kernel metadata") from error


def _write_control(path: Path, value: str, append: bool, owner: int) -> None:
  flags = os.O_WRONLY | (os.O_APPEND if append else 0)
  fd = _open_checked(path, flags, owner)
  try:
    data = (value + "\n").encode("ascii")
    if os.write(fd, data) != len(data):
      raise Refusal("partial control write")
  finally:
    os.close(fd)


@dataclass
class TraceFiles:
  root: Path
  target: Path
  owner: int = 0
  target_opened: bool = False

  def perform(self, action: Action, state: TraceState) -> None:
    """Execute only fixed operations; fixture paths are not exposed by the CLI."""
    _validate_names(state)
    instance = self.root / "instances" / state.instance
    event = instance / "events" / state.group / state.event / "enable"
    if action.name == "create_instance":
      parent = _open_checked(self.root / "instances", os.O_RDONLY | os.O_DIRECTORY, self.owner, True)
      blocked = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGINT, signal.SIGTERM, signal.SIGHUP, signal.SIGALRM})
      try:
        os.mkdir(state.instance, mode=0o700, dir_fd=parent)
        state.instance_created = True
      finally:
        os.close(parent)
        signal.pthread_sigmask(signal.SIG_SETMASK, blocked)
    elif action.name == "remove_instance":
      parent = _open_checked(self.root / "instances", os.O_RDONLY | os.O_DIRECTORY, self.owner, True)
      try:
        os.rmdir(state.instance, dir_fd=parent)
        state.instance_created = False
      finally:
        os.close(parent)
    elif action.name in ("append_definition", "delete_definition"):
      if action.name == "append_definition":
        if action.value != state.definition:
          raise Refusal("probe definition differs from fixed contract")
        state.definition_attempted = True
      else:
        if action.value != f"-:{state.group}/{state.event}" or _own_definitions(_text(self.root / "kprobe_events", owner=self.owner), state) != [state.serialized_definition]:
          raise Refusal("owned probe changed before deletion")
      _write_control(self.root / "kprobe_events", action.value, True, self.owner)
    elif action.name == "set_buffer":
      if action.value != "16":
        raise Refusal("unexpected buffer request")
      _write_control(instance / "buffer_size_kb", action.value, False, self.owner)
    elif action.name == "set_pid":
      if action.value != str(state.pid):
        raise Refusal("unexpected PID filter")
      _write_control(instance / "set_event_pid", action.value, False, self.owner)
    elif action.name in ("enable_event", "disable_event"):
      if action.name == "enable_event":
        if _text(instance / "set_event_pid", owner=self.owner).split() != [str(state.pid)]:
          raise Refusal("PID filter readback mismatch")
        state.event_enable_attempted = True
      _write_control(event, "1" if action.name == "enable_event" else "0", False, self.owner)
    elif action.name in ("start_trace", "stop_trace"):
      if action.name == "start_trace":
        state.trace_enable_attempted = True
      _write_control(instance / "tracing_on", "1" if action.name == "start_trace" else "0", False, self.owner)
    elif action.name == "open_target_once":
      if self.target_opened:
        raise Refusal("second target open forbidden")
      self.target_opened = True
      os.close(_open_checked(self.target, os.O_RDONLY, self.owner))
    elif action.name == "refuse_definition_delete":
      raise Refusal("owned probe definition changed; retained for manual review")
    else:
      raise Refusal("unknown action")


def _identity() -> Identity:
  boot = read_regular(Path("/proc/sys/kernel/random/boot_id"), 128)
  return Identity(
    os.uname().release, hashlib.sha256(boot).hexdigest(),
    hashlib.sha256(read_regular(MODULE, 128 * 1024 * 1024)).hexdigest(),
    parse_build_id(read_regular(Path("/sys/module/appledrm/notes/.note.gnu.build-id"), 64)),
    parse_build_id(read_regular(Path("/sys/module/tps6598x_core/notes/.note.gnu.build-id"), 64)),
  )


def _preflight() -> None:
  if os.geteuid() != 0 or os.uname().machine != "aarch64":
    raise Refusal("requires manually invoked root on the bound AArch64 machine")
  verify_identity(_identity(), EXPECTED_BOOT_SHA256)
  parse_mounts(_text(Path(f"/proc/{os.getpid()}/mountinfo"), 1024 * 1024))
  for connector, field, expected in (("DP-1", "status", "connected"), ("DP-1", "enabled", "disabled"), ("eDP-1", "enabled", "enabled")):
    if _text(DRM_ROOT / f"card2-{connector}" / field).strip() != expected:
      raise Refusal("display state changed; diagnostic no longer authorized for this state")
  # O_PATH performs a metadata check; it does not call the debugfs file's open method.
  os.close(_open_checked(TARGET, os.O_PATH))
  os.close(_open_checked(TRACE_ROOT, os.O_RDONLY | os.O_DIRECTORY, directory=True))


def _save(directory: Path, name: str, value: object) -> None:
  fd = os.open(directory / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
  with os.fdopen(fd, "w", encoding="utf-8") as target:
    json.dump(value, target, sort_keys=True)
    target.write("\n")


def _interrupted(number: int, frame: FrameType | None) -> None:
  del number, frame
  raise Refusal("interrupted or diagnostic deadline expired")


@contextmanager
def _cleanup_deadline() -> Iterator[None]:
  # Cooperative bound only: Python cannot interrupt an uninterruptible kernel syscall.
  signal.setitimer(signal.ITIMER_REAL, 2)
  try:
    yield
  finally:
    signal.setitimer(signal.ITIMER_REAL, 0)


def cleanup(files: TraceFiles, state: TraceState) -> CleanupResult:
  """Try each owned cleanup operation even when a previous operation fails."""
  operations: list[str] = []
  failures: list[str] = []

  def attempt(action: Action) -> None:
    try:
      with _cleanup_deadline():
        files.perform(action, state)
        operations.append(f"cleanup:{action.name}")
    except (Refusal, OSError) as error:
      failures.append(f"{action.name}: {str(error) if isinstance(error, Refusal) else type(error).__name__}")

  # Stop owned recording first; reading the global table must not delay this attempt.
  for action in cleanup_actions(state, ""):
    attempt(action)
  try:
    with _cleanup_deadline():
      definitions = _text(files.root / "kprobe_events", 1024 * 1024, files.owner)
  except (Refusal, OSError):
    definitions = ""
    failures.append("could not verify owned global probe; no global deletion attempted")
  for action in cleanup_actions(state, definitions):
    if action.name in ("delete_definition", "refuse_definition_delete"):
      attempt(action)
  try:
    with _cleanup_deadline():
      if _own_definitions(_text(files.root / "kprobe_events", 1024 * 1024, files.owner), state):
        failures.append("owned global probe remains")
  except (Refusal, OSError):
    failures.append("global cleanup absence verification failed")
  try:
    with _cleanup_deadline():
      parent = _open_checked(files.root / "instances", os.O_RDONLY | os.O_DIRECTORY, files.owner, True)
      try:
        if state.instance in os.listdir(parent):
          failures.append("owned trace instance remains")
      finally:
        os.close(parent)
  except (Refusal, OSError):
    failures.append("instance cleanup absence verification failed")
  return CleanupResult(tuple(operations), tuple(failures))


def _buffers(instance: Path) -> tuple[Path, ...]:
  value = _text(instance / "buffer_size_kb").strip()
  if not value.isdigit() or not 0 < int(value) <= 64:
    raise Refusal("trace buffer outside bound")
  cpu_root = instance / "per_cpu"
  fd = _open_checked(cpu_root, os.O_RDONLY | os.O_DIRECTORY, directory=True)
  try:
    names = os.listdir(fd)
  finally:
    os.close(fd)
  if not 1 <= len(names) <= 64 or any(re.fullmatch(r"cpu\d+", name) is None for name in names):
    raise Refusal("unexpected tracing CPU list")
  return tuple(cpu_root / name / "stats" for name in sorted(names))


def _fallback(state: TraceState) -> dict[str, object]:
  instance = TRACE_ROOT / "instances" / state.instance
  return {
    "warning": "SIGKILL, kernel failure, or power loss can prevent automatic cleanup. Do not run this diagnostic again.",
    "timing": "Measurement: 10 seconds. Each of at most seven cleanup operations: 2-second cooperative timer. Uninterruptible kernel calls are not hard-bounded.",
    "same_boot_only": True,
    "boot_sha256": EXPECTED_BOOT_SHA256,
    "instance": str(instance),
    "stop_own_trace": str(instance / "tracing_on"),
    "disable_own_event": str(instance / "events" / state.group / state.event / "enable"),
    "remove_only_empty_owned_instance": "rmdir (not recursive) only the exact instance path after stop/disable",
    "delete_only_if_exact_definition_still_matches": state.serialized_definition,
    "append_to_kprobe_events_after_instance_removal": f"-:{state.group}/{state.event}",
    "never": "Never truncate or clear global tracing files. Never delete any other event or instance. Ask for review if a step fails.",
  }


def _run() -> tuple[Path, Observation | None, list[str], list[str]]:
  token = secrets.token_hex(8)
  state = TraceState(f"dev147_cf_{token}", f"observe_{token}", f"dev147_cf_{token}", os.getpid())
  files = TraceFiles(TRACE_ROOT, TARGET)
  instance = TRACE_ROOT / "instances" / state.instance
  definitions = _text(TRACE_ROOT / "kprobe_events", 1024 * 1024)
  parent = _open_checked(TRACE_ROOT / "instances", os.O_RDONLY | os.O_DIRECTORY, directory=True)
  try:
    actions = setup_actions(state, definitions, tuple(os.listdir(parent)))
  finally:
    os.close(parent)
  os.close(_open_checked(Path("/run"), os.O_RDONLY | os.O_DIRECTORY, directory=True))
  evidence = Path(tempfile.mkdtemp(prefix="dev147-crashflag-", dir="/run"))
  _save(evidence, "cleanup.json", _fallback(state))
  print(json.dumps({"level": "info", "status": "PREPARED", "evidence": str(evidence), "cleanup": str(evidence / "cleanup.json")}, sort_keys=True), flush=True)
  journal: list[str] = []
  failures: list[str] = []
  cleanup_failures: list[str] = []
  observation: Observation | None = None
  start = time.monotonic()
  handlers = {number: signal.signal(number, _interrupted) for number in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP, signal.SIGALRM)}
  try:
    signal.alarm(DEADLINE_SECONDS)
    cpu_stats: tuple[Path, ...] = ()
    for action in actions:
      remaining_seconds(start, time.monotonic())
      files.perform(action, state)
      journal.append(action.name)
      if action.name == "set_buffer":
        cpu_stats = _buffers(instance)
        if _text(instance / "current_tracer").strip() != "nop":
          raise Refusal("new instance tracer is not nop")
      elif action.name == "append_definition":
        definition = _own_definitions(_text(TRACE_ROOT / "kprobe_events", 1024 * 1024), state)
        if definition != [state.serialized_definition]:
          raise Refusal("probe definition readback mismatch")
        event_root = instance / "events" / state.group / state.event
        event_format = _text(event_root / "format")
        event_id = _text(event_root / "id")
        verify_format(event_format, event_id, state)
        _save(evidence, "event.json", {"format": event_format, "id": int(event_id), "definition": definition[0]})
    if _text(instance / "tracing_on").strip() != "0" or _text(instance / "events" / state.group / state.event / "enable").strip() != "0":
      raise Refusal("own tracing or event did not stop")
    trace = _text(instance / "trace", 512 * 1024)
    _save(evidence, "trace.json", asdict(sanitize_trace(trace)))
    profile = _text(TRACE_ROOT / "kprobe_profile", 1024 * 1024)
    _save(evidence, "profile.json", {"own_records": [line.split() for line in profile.splitlines() if line.split() and line.split()[0] == state.event]})
    verify_profile(profile, state)
    for path in cpu_stats:
      statistics = _text(path)
      _save(evidence, f"{path.parent.name}-stats.json", {"stats": statistics})
      verify_cpu_stats(statistics)
    observation = parse_event(trace, state)
    _save(evidence, "observation.json", {"observation": asdict(observation), "profile_hits": 1, "profile_misses": 0})
    remaining_seconds(start, time.monotonic())
  except (Refusal, OSError, ValueError) as error:
    failures.append(str(error) if isinstance(error, Refusal) else type(error).__name__)
  finally:
    signal.alarm(0)
    try:
      result = cleanup(files, state)
      journal.extend(result.operations)
      cleanup_failures.extend(result.failures)
    except (Refusal, OSError):
      cleanup_failures.append("cleanup interrupted between operations; use exact owned fallback")
    finally:
      signal.setitimer(signal.ITIMER_REAL, 0)
      for number, handler in handlers.items():
        signal.signal(number, handler)
  _save(evidence, "result.json", {"operations": journal, "failures": failures, "cleanup_failures": cleanup_failures, "observation": asdict(observation) if observation else None})
  return evidence, observation, failures, cleanup_failures


def main(arguments: list[str]) -> int:
  try:
    if arguments:
      raise Refusal("no arguments accepted")
    if not re.fullmatch(r"[0-9a-f]{64}", EXPECTED_BOOT_SHA256):
      raise Refusal("public helper is intentionally unbound; private boot binding required")
    _preflight()
    evidence, observation, failures, cleanup_failures = _run()
    passed = observation is not None and not failures and not cleanup_failures
    conclusion = "not established"
    if passed and observation is not None:
      conclusion = "crash guard present now; writer and initial link loss not identified" if observation.crashed else "zero observed; latch not established; scalar fetch faults can also yield zero; earlier fault and writer unresolved"
    print(json.dumps({"level": "info" if passed else "error", "status": "OBSERVED" if passed else "INCOMPLETE", "conclusion": conclusion, "observation": asdict(observation) if observation else None, "evidence": str(evidence), "failures": failures, "cleanup_failures": cleanup_failures}, sort_keys=True))
    return 0 if passed else 1
  except (Refusal, OSError, ValueError) as error:
    print(json.dumps({"level": "error", "status": "REFUSED", "reason": str(error) if isinstance(error, Refusal) else type(error).__name__}))
    return 2


if __name__ == "__main__":
  sys.exit(main(sys.argv[1:]))
