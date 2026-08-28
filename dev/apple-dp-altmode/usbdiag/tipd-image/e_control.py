"""Incomplete E-only control subject for a separately reviewed semantic RED.

No archive, module, child, reduced root, or image is constructed by this
draft. The placeholders return no acceptance. The operational entry is
closed until the real control orchestration receives a separate review.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import NoReturn

from verify_control import TreeState


KERNEL = "7.1.6-1-1-ARCH"
CONTROL_ROOT = Path("/work/control-root")
LOOKUP_ROOT = Path("/work/lookup-root")
MODULE_DIRECTORY = Path("lib/modules") / KERNEL
MAX_COMMANDS = 424
CONTROL_SECONDS = 270.0

# Only these literal Python self-checks may join the six control tools.
# The real 424-child E workload must never call one of them.
SELF_CHECKS = (
  "import sys; sys.stdout.buffer.write(b'x' * 65537)",
  "import sys; sys.stderr.buffer.write(b'e' * 65537)",
  "import sys; sys.stderr.write('fixture stderr\\n')",
  "raise SystemExit(7)",
  "import time; time.sleep(1)",
)


class ControlError(RuntimeError):
  """A fixed control refusal; never a hardware or operational verdict."""


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

  def run(
    self,
    command: tuple[str, ...],
    *,
    stdin: Path | None = None,
    stdin_sha256: str | None = None,
    timeout: float = 30.0,
    stdout_limit: int = 1024 * 1024,
    stderr_limit: int = 65536,
  ) -> bytes | None:
    """Return no result until active bounds have a retained RED."""
    return None


def build_root(
  root: Path,
  modules: dict[str, bytes],
  metadata: dict[str, bytes],
) -> TreeState | None:
  """Return no root proof until the narrow copy boundary is implemented."""
  return None


def unchanged_root(root: Path, expected: TreeState) -> bool:
  """Return no acceptance until exact post-readback is implemented."""
  return False


def ordered_lookup(
  raw: bytes,
  name: str,
  names: dict[str, str],
  dependencies: dict[str, tuple[str, ...]],
  builtins: set[str],
) -> Lookup | None:
  """Return no acceptance for the unimplemented ordered lookup check."""
  return None


def main() -> NoReturn:
  """A fixture cannot unlock real E control or T1 image assembly."""
  raise ControlError("E_CONTROL_UNAVAILABLE")


if __name__ == "__main__":
  main()
