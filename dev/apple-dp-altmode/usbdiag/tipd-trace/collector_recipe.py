"""Disabled T1 collector and pure command-plan implementation.

This draft has no command execution, file access, retry, or CLI. A plan is
not a capture, and tests of a plan do not prove active deadline enforcement.
"""

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class CollectorPlan:
  argv: tuple[str, ...]
  deadline_us: int
  stdout_limit: int
  stderr_limit: int
  boot_id_path: str
  tipd_note_path: str


class CollectorClosed(RuntimeError):
  """No live collector is released by the RED draft."""


def collector_plan(boot_id: str) -> CollectorPlan:
  """Return a pure plan. This function does not execute or read the paths."""
  if not isinstance(boot_id, str) or re.fullmatch(r"[0-9a-f]{32}", boot_id) is None:
    raise ValueError("invalid_boot_id")
  return CollectorPlan(
    argv=(
      "/usr/bin/journalctl", "--dmesg", "--boot=" + boot_id,
      "--all", "--output=json", "--no-pager", "--no-tail",
    ),
    deadline_us=30_000_000,
    stdout_limit=8_388_608,
    stderr_limit=65_536,
    boot_id_path="/proc/sys/kernel/random/boot_id",
    tipd_note_path="/sys/module/tps6598x_core/notes/.note.gnu.build-id",
  )


def collect_capture() -> None:
  """An unconditional stop, including for a known current module identity."""
  raise CollectorClosed("artifact_binding_unavailable")
