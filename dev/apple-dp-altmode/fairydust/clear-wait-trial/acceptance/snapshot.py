from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

RELEASE = "7.1.12-dev147-clearwait100"
OUTPUT = Path("/home/david/Work/dev147-clear-wait-trial/acceptance")
TYPEC_FIELDS = (
  "data_role",
  "power_role",
  "port_type",
  "preferred_role",
  "power_operation_mode",
  "orientation",
  "supports_usb_power_delivery",
  "usb_power_delivery_revision",
  "accessory_mode",
)
PINS = {
  "/boot/efi/m1n1/boot.bin": "1ae29a2bfadb309562c205520d8c28e2a8df2283bc88bbfb52474e54333c3dff",
  "/boot/efi/m1n1/dev147-recovery/boot.bin.old-203ab702": "203ab7027536c8d16f373d02c1f6346a5c34cfe095a9dafd0cfe37d2b354090c",
  "/etc/pacman.d/hooks/05-omarchy-m2-displayport-guard.hook": "469820ad7cfd015a22cff979b0aa70d62e82dcc7cc05951dca92f40cd660f2bd",
}
DRIVERS = (
  "apple-dcp",
  "dcp",
  "dptx",
  "displayport",
  "atcphy",
  "apple-typec",
  "typec",
  "thunderbolt",
  "usb4",
  "afk",
)
ERROR_WORDS = (
  "error",
  "failed",
  "failure",
  "timeout",
  "timed out",
  "fault",
  "panic",
  "oops",
  "warning",
  "abort",
  "underrun",
)
STATE_WORDS = (
  "connected",
  "disconnected",
  "link",
  "training",
  "hotplug",
  "hpd",
  "mode",
  "display",
  "phy",
  "ready",
  "shutdown",
  "power",
)


@dataclass(frozen=True)
class Issue:
  source: str
  code: str


@dataclass(frozen=True)
class Connector:
  name: str
  status: str | None
  enabled: str | None
  modes: list[str]


@dataclass(frozen=True)
class TypeCPort:
  name: str
  attributes: dict[str, str | None]


@dataclass(frozen=True)
class JournalRecord:
  monotonic_us: int
  priority: int
  drivers: list[str]
  observations: list[str]
  error: bool
  scope: str = "recent"
  controller: str | None = None
  endpoint: int | None = None
  service: str | None = None
  channel: int | None = None
  dcp_boot: bool = False
  origin: str = "kernel"


@dataclass
class Snapshot:
  label: str
  utc_started: str
  monotonic_started_ns: int
  boot_id: str | None = None
  release: str | None = None
  machine: str = field(default_factory=lambda: os.uname().machine)
  connectors: list[Connector] = field(default_factory=list)
  typec: list[TypeCPort] = field(default_factory=list)
  pins: dict[str, str] = field(default_factory=dict)
  issues: list[Issue] = field(default_factory=list)
  journal_records: int = 0
  journal_errors: int = 0
  firmware_error_records: int = 0
  host_error_records: int = 0
  journal_window: str = "last 15 minutes, at most 1000 matching kernel records"
  journal_available: bool = False
  summary_controller: str = "271c00000.dcp"
  summary_endpoint: str = "0x28"
  service_announcements: int = 0
  announcement_pairs: int = 0
  unpaired_announcements: int = 0
  pairing_limit: str = "Count pairs only; journal announcements do not prove logical generation boundaries or occupied host slots."
  host_slot_count: int | None = None
  dcp_boots: dict[str, int] = field(default_factory=dict)
  monotonic_finished_ns: int = 0
  status: str = "SNAPSHOT_INCOMPLETE"
  endurance_accepted: bool = False


def read_attribute(path: Path) -> str:
  with path.open("rb") as stream:
    value = stream.read(4097)
  if len(value) > 4096:
    raise ValueError("attribute exceeds limit")
  return value.decode("utf-8").strip()


def command(arguments: list[str]) -> subprocess.CompletedProcess[str]:
  return subprocess.run(
    arguments,
    capture_output=True,
    text=True,
    check=False,
    timeout=15,
    env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"},
  )


def tokens(message: str, vocabulary: tuple[str, ...]) -> list[str]:
  return [
    word
    for word in vocabulary
    if re.search(r"(?<![a-z0-9])" + re.escape(word) + r"(?![a-z0-9])", message)
  ]


def journal_records(content: str, scope: str = "recent") -> list[JournalRecord]:
  if len(content) > 4_194_304:
    raise ValueError("journal exceeds limit")
  result: list[JournalRecord] = []
  for line in content.splitlines():
    value: object = json.loads(line)
    if not isinstance(value, dict) or not isinstance(value.get("MESSAGE"), str):
      raise TypeError("invalid journal record")
    message = value["MESSAGE"].lower()
    drivers = tokens(message, DRIVERS)
    if not drivers:
      continue
    priority_text: object = value.get("PRIORITY")
    timestamp_text: object = value.get("__MONOTONIC_TIMESTAMP")
    if (
      not isinstance(priority_text, str)
      or not re.fullmatch("[0-7]", priority_text)
      or not isinstance(timestamp_text, str)
      or not timestamp_text.isdecimal()
    ):
      raise ValueError("invalid journal metadata")
    errors = tokens(message, ERROR_WORDS)
    controller_match = re.search(r"apple-dcp ([0-9a-f]{1,16}\.dcp):", message)
    service_match = re.search(
      r"AFK\[ep:(\d{1,3})\]: new service (DCP[A-Za-z0-9]{1,60}Service) on channel (\d{1,10})",
      value["MESSAGE"],
    )
    record = JournalRecord(
      int(timestamp_text),
      int(priority_text),
      drivers,
      errors + tokens(message, STATE_WORDS),
      bool(errors) or int(priority_text) <= 3,
      scope,
      controller_match.group(1) if controller_match else None,
      int(service_match.group(1), 16) if service_match else None,
      service_match.group(2) if service_match else None,
      int(service_match.group(3)) if service_match else None,
      "dcp booted" in message,
      "firmware_syslog" if "rtkit: syslog message:" in message else "kernel",
    )
    if scope == "recent" or record.service is not None or record.dcp_boot:
      result.append(record)
  return result


def collect_journal(snapshot: Snapshot) -> list[JournalRecord]:
  base = ["/usr/bin/journalctl", "--boot", "--dmesg", "--no-pager", "--output=json"]
  try:
    availability = command(
      base + ["--lines=1", "--output-fields=__MONOTONIC_TIMESTAMP,_BOOT_ID"]
    )
    if (
      availability.returncode
      or availability.stderr.strip()
      or not availability.stdout.strip()
    ):
      snapshot.issues.append(Issue("journal", "journal_unavailable"))
      return []
    marker: object = json.loads(availability.stdout.splitlines()[-1])
    if (
      not isinstance(marker, dict)
      or not str(marker.get("__MONOTONIC_TIMESTAMP", "")).isdecimal()
    ):
      raise ValueError("invalid availability marker")
    snapshot.journal_available = True
    selected = command(
      base
      + [
        "--since=-15min",
        "--lines=1000",
        "--output-fields=MESSAGE,PRIORITY,__MONOTONIC_TIMESTAMP,_BOOT_ID",
        "--case-sensitive=no",
        "--grep=" + "|".join(DRIVERS),
      ]
    )
    if selected.returncode or selected.stderr.strip():
      snapshot.issues.append(Issue("journal", "journal_failed"))
      return []
    records = journal_records(selected.stdout)
    if len(selected.stdout.splitlines()) >= 1000:
      snapshot.issues.append(Issue("journal", "recent_record_limit_reached"))
    boot = command(
      base
      + [
        "--lines=1000",
        "--output-fields=MESSAGE,PRIORITY,__MONOTONIC_TIMESTAMP,_BOOT_ID",
        "--case-sensitive=no",
        "--grep=AFK\\[ep:28\\]: new service|DCP booted",
      ]
    )
    if boot.returncode or boot.stderr.strip():
      snapshot.issues.append(Issue("journal", "boot_service_journal_failed"))
      return records
    if len(boot.stdout.splitlines()) >= 1000:
      snapshot.issues.append(Issue("journal", "boot_service_record_limit_reached"))
    boot_records = journal_records(boot.stdout, "current_boot_service")
    snapshot.service_announcements = sum(
      record.controller == snapshot.summary_controller
      and record.endpoint == 0x28
      and record.service == "DCPDP13Service"
      for record in boot_records
    )
    snapshot.announcement_pairs, snapshot.unpaired_announcements = divmod(
      snapshot.service_announcements, 2
    )
    for record in boot_records:
      if record.dcp_boot and record.controller:
        snapshot.dcp_boots[record.controller] = (
          snapshot.dcp_boots.get(record.controller, 0) + 1
        )
    snapshot.journal_records = len(records)
    snapshot.journal_errors = sum(record.error for record in records)
    snapshot.firmware_error_records = sum(
      record.error and record.origin == "firmware_syslog" for record in records
    )
    snapshot.host_error_records = sum(
      record.error and record.origin == "kernel" for record in records
    )
    return records + boot_records
  except (OSError, subprocess.TimeoutExpired, ValueError, TypeError, UnicodeError):
    snapshot.issues.append(Issue("journal", "journal_invalid_or_timed_out"))
    return []


def capture(label: str) -> tuple[Snapshot, list[JournalRecord]]:
  snapshot = Snapshot(label, datetime.now(UTC).isoformat(), time.monotonic_ns())
  try:
    snapshot.boot_id = read_attribute(Path("/proc/sys/kernel/random/boot_id"))
    if not re.fullmatch("[0-9a-f-]{36}", snapshot.boot_id):
      raise ValueError("invalid boot identity")
  except (OSError, ValueError, UnicodeError):
    snapshot.issues.append(Issue("boot", "boot_id_unavailable"))
  try:
    kernel = command(["/usr/bin/uname", "-r"])
    snapshot.release = kernel.stdout.strip()
    if kernel.returncode or snapshot.release != RELEASE:
      snapshot.issues.append(Issue("kernel", "wrong_release"))
  except (OSError, subprocess.TimeoutExpired):
    snapshot.issues.append(Issue("kernel", "release_unavailable"))
  for path in sorted(Path("/sys/class/drm").glob("card*-*")):
    if not re.fullmatch(r"card\d+-(?:DP|eDP)-\d+", path.name):
      continue
    attributes: dict[str, str | None] = {}
    for name in ("status", "enabled", "modes"):
      try:
        attributes[name] = read_attribute(path / name)
      except (OSError, ValueError, UnicodeError):
        attributes[name] = None
        snapshot.issues.append(Issue(path.name, name + "_unavailable"))
    snapshot.connectors.append(
      Connector(
        path.name,
        attributes["status"],
        attributes["enabled"],
        (attributes["modes"] or "").splitlines(),
      )
    )
  if not any(
    re.fullmatch(r"card\d+-DP-\d+", item.name) for item in snapshot.connectors
  ):
    snapshot.issues.append(Issue("drm", "external_connector_absent"))
  for path in sorted(Path("/sys/class/typec").glob("port*")):
    if not re.fullmatch(r"port\d+(?:-partner)?", path.name):
      continue
    port_attributes: dict[str, str | None] = {}
    for name in TYPEC_FIELDS:
      try:
        port_attributes[name] = read_attribute(path / name)
      except FileNotFoundError:
        port_attributes[name] = None
      except (OSError, ValueError, UnicodeError):
        port_attributes[name] = None
        snapshot.issues.append(Issue(path.name, name + "_unavailable"))
    snapshot.typec.append(TypeCPort(path.name, port_attributes))
  for name, expected in PINS.items():
    try:
      path = Path(name)
      info = path.lstat()
      if not stat.S_ISREG(info.st_mode) or info.st_size > 16_777_216:
        raise ValueError("invalid pin file")
      descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
      with os.fdopen(descriptor, "rb") as stream:
        content = stream.read(info.st_size + 1)
        if len(content) != info.st_size:
          raise ValueError("pin changed while reading")
        actual = hashlib.sha256(content).hexdigest()
      snapshot.pins[name] = actual
      if actual != expected:
        snapshot.issues.append(Issue(name, "pin_mismatch"))
    except (OSError, ValueError):
      snapshot.issues.append(Issue(name, "pin_unavailable"))
  records = collect_journal(snapshot)
  snapshot.monotonic_finished_ns = time.monotonic_ns()
  snapshot.status = (
    "SNAPSHOT_INCOMPLETE"
    if snapshot.issues
    else (
      "SNAPSHOT_CAPTURED_WITH_ERRORS"
      if snapshot.journal_errors
      else "SNAPSHOT_CAPTURED"
    )
  )
  return snapshot, records


def persist(snapshot: Snapshot, records: list[JournalRecord]) -> Path:
  OUTPUT.mkdir(mode=0o700, parents=True, exist_ok=True)
  info = OUTPUT.lstat()
  if (
    not stat.S_ISDIR(info.st_mode)
    or info.st_uid != os.getuid()
    or stat.S_IMODE(info.st_mode) & 0o077
  ):
    raise ValueError("output root must be a private owned directory")
  directory = Path(tempfile.mkdtemp(prefix=snapshot.label + ".", dir=OUTPUT))
  values = {
    "snapshot.json": json.dumps(asdict(snapshot), indent=2) + "\n",
    "journal.jsonl": "".join(json.dumps(asdict(record)) + "\n" for record in records),
  }
  for name, content in values.items():
    with (directory / name).open("x") as stream:
      stream.write(content)
    (directory / name).chmod(0o400)
  manifest = "".join(
    hashlib.sha256(content.encode()).hexdigest() + "  " + name + "\n"
    for name, content in values.items()
  )
  with (directory / "SHA256SUMS").open("x") as stream:
    stream.write(manifest)
  (directory / "SHA256SUMS").chmod(0o400)
  directory.chmod(0o500)
  return directory


def main() -> int:
  if len(sys.argv) != 2 or not re.fullmatch(
    r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", sys.argv[1]
  ):
    print(
      "Usage: snapshot.py LABEL (1–64 letters, digits, underscores or hyphens)",
      file=sys.stderr,
    )
    return 2
  os.umask(0o077)
  snapshot, records = capture(sys.argv[1])
  directory = persist(snapshot, records)
  print(
    json.dumps(
      {
        "status": snapshot.status,
        "directory": str(directory),
        "label": snapshot.label,
        "release": snapshot.release,
        "connectors": [asdict(item) for item in snapshot.connectors],
        "journal_errors": snapshot.journal_errors,
        "issues": [asdict(issue) for issue in snapshot.issues],
        "endurance_accepted": False,
      }
    )
  )
  return 0 if snapshot.status == "SNAPSHOT_CAPTURED" else 1


if __name__ == "__main__":
  sys.exit(main())
