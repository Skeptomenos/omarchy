"""Expected v1-to-v2 identity-boundary RED using real authenticated modules.

This is not a claim that the old version-pinned verifier is defective. Setup
checks the real v2/control files with bounded modinfo/readelf subprocesses. The
exact old main then rejects its first v2 hash before its legacy child runner.
No source/global pin is rebound, no module loads, and no image changes.

The approved no-install exception uses typed stdlib models and unittest.
"""

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
from types import ModuleType
import unittest


VERIFIER = Path("/inputs/verifier")
VERIFIER_SHA256 = "404bf6616d6367f44ff47811df5dd20f8afc231cc27c86b5a063862820d652c7"
SYMVERS_SHA256 = "d5eea549b9333f717fdc932683ea6633d58049c1e3f8f9e0be12e05d7610dd82"
WORK = Path("/work/verifier-fixtures")
ENVIRONMENT = {"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C", "TMPDIR": "/tmp"}
FIELDS = ("name", "vermagic", "depends", "alias")
ADDITIONS = frozenset(("_printk", "alt_cb_patch_nops", "of_machine_compatible_match",
                       "of_find_node_opts_by_path", "of_node_put"))


@dataclass(frozen=True)
class Pair:
  name: str
  component: str
  diagnostic_sha256: str
  diagnostic_build_id: str
  control_sha256: str
  control_build_id: str


PAIRS = (
  Pair("dwc3-apple", "dwc3", "d9090119fee0252c9031185128ddd9d03bef9a0cbdfb118d8c71b7161d48b425",
       "92014543045243fb1680ac0e56b34c3ce69cc503",
       "d213e676593c1c4f9daceba1002f2381b6d390ce3eff9995043991a4d1e20975",
       "c0628ff7e26e3e3cb0dda8517bc2a34511ae85be"),
  Pair("phy-apple-atc", "atc", "dea7e4eaee8928441a44480843795a68905e5122d435ae86dacc06fdf7b0efbe",
       "dc5bed70afdb1aa22a8cddd0a7f5ac2a2256ba49",
       "edb76a5fd6458406f6371f842a7a6a2b5f8b22b404ba622a5d081302662cc568",
       "def6d3cb64d2f7fff393c9da6fdde2e9ebbfc2c9"),
)


def require(condition: bool, detail: str) -> None:
  if not condition:
    raise RuntimeError(detail)


def identity(info: os.stat_result) -> tuple[int, ...]:
  return (info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_gid,
          info.st_nlink, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def pinned(path: Path, digest: str) -> bytes:
  require(path.is_absolute() and path.parts[:2] == ("/", "inputs"), "input escaped fixed mount root")
  for parent in path.parents:
    require(stat.S_ISDIR(parent.lstat().st_mode), "input parent is not a real directory")
  before = path.lstat()
  require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and 0 < before.st_size < 16 * 1024 * 1024,
          "unbounded or nonregular input")
  descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC)
  with os.fdopen(descriptor, "rb") as stream:
    require(identity(os.fstat(stream.fileno())) == identity(before), "input changed on open")
    raw = stream.read(16 * 1024 * 1024)
    require(identity(os.fstat(stream.fileno())) == identity(before) == identity(path.lstat()),
            "input changed while reading")
  require(len(raw) == before.st_size and hashlib.sha256(raw).hexdigest() == digest,
          "input source pin mismatch")
  return raw


def save(path: Path, value: object) -> None:
  raw = (json.dumps(value, sort_keys=True) + "\n").encode("ascii")
  with path.open("xb") as stream:
    stream.write(raw)
    stream.flush()
    os.fsync(stream.fileno())


@dataclass
class Prechecks:
  count: int = 0

  def run(self, command: tuple[str, ...]) -> bytes:
    label = f"precheck-{self.count:02d}"
    self.count += 1
    stdout, stderr = WORK / f"{label}.stdout", WORK / f"{label}.stderr"
    code: int | None = None
    timed_out = False
    with stdout.open("xb") as output, stderr.open("xb") as errors:
      try:
        result = subprocess.run(command, cwd=Path("/work"), env=ENVIRONMENT, stdin=subprocess.DEVNULL,
                                stdout=output, stderr=errors, timeout=10, check=False)
        code = result.returncode
      except subprocess.TimeoutExpired:
        timed_out = True
      output.flush()
      errors.flush()
      os.fsync(output.fileno())
      os.fsync(errors.fileno())
    save(WORK / f"{label}.json", {"command": command, "returncode": code, "timed_out": timed_out,
                                 "stdout_bytes": stdout.stat().st_size, "stderr_bytes": stderr.stat().st_size})
    require(not timed_out and code == 0 and stderr.stat().st_size == 0,
            "SETUP: real metadata tool failed")
    require(stdout.stat().st_size <= 1024 * 1024, "SETUP: metadata output bound exceeded")
    return stdout.read_bytes()


class V2VerifierBoundaryTests(unittest.TestCase):
  old: ModuleType

  @classmethod
  def setUpClass(cls) -> None:
    require(os.getuid() == os.getgid() == 1001 and Path.cwd() == Path("/work"),
            "unexpected test identity/directory")
    require(sys.flags.isolated == 1 and sys.flags.no_site == 1 and sys.dont_write_bytecode,
            "isolated Python flags required")
    require(not any(Path(name).exists() for name in ("/proc", "/sys", "/run", "/home", "/boot")),
            "host tree visible")
    os.umask(0o077)
    source = pinned(VERIFIER, VERIFIER_SHA256)
    require(len(source) < 128 * 1024, "unbounded verifier source")
    symvers = pinned(Path("/inputs/symvers"), SYMVERS_SHA256)
    exports = {fields[1]: fields[2:] for line in symvers.decode("ascii").splitlines()
               if len(fields := line.split()) >= 4}
    for symbol in ADDITIONS | {"strcmp"}:
      require(exports.get(symbol) == ["vmlinux", "EXPORT_SYMBOL"], "SETUP: export contract differs")
    WORK.mkdir(mode=0o700)
    tools = Prechecks()
    for pair in PAIRS:
      metadata: dict[str, tuple[bytes, ...]] = {}
      for role, digest, build_id in (("diagnostic", pair.diagnostic_sha256, pair.diagnostic_build_id),
                                    ("control", pair.control_sha256, pair.control_build_id)):
        path = Path("/inputs") / role / f"{pair.name}.ko"
        raw = pinned(path, digest)
        require(raw[:6] == b"\x7fELF\x02\x01", "SETUP: not ELF64 little-endian")
        if role == "diagnostic":
          prefix = ('{"schema":1,"revision":"dev147-usbdiag2-v1","board":"j413",'
                    f'"component":"{pair.component}","target":"front_lower",').encode("ascii")
          require(prefix in raw and b"dev147-usbdiag1-v1" not in raw, "SETUP: v2 prefix missing/mixed")
        else:
          require(b"dev147-usbdiag" not in raw, "SETUP: control contains diagnostic markers")
        metadata[role] = tuple(tools.run(("/usr/bin/modinfo", "-F", field, str(path))) for field in FIELDS)
        elf = tools.run(("/usr/bin/readelf", "-h", "-n", "-SW", str(path))).decode("ascii")
        require(re.search(r"^\s*Type:\s+REL\s", elf, re.MULTILINE) is not None and
                re.search(r"^\s*Machine:\s+AArch64\s*$", elf, re.MULTILINE) is not None,
                "SETUP: wrong ELF type/machine")
        require(re.findall(r"Build ID: ([0-9a-f]+)", elf) == [build_id], "SETUP: build ID mismatch")
        btf = re.findall(r"^\s*\[\s*\d+\]\s+\.BTF\s+PROGBITS\s+[0-9a-fA-F]+\s+"
                         r"[0-9a-fA-F]+\s+([0-9a-fA-F]+)\s", elf, re.MULTILINE)
        require(len(btf) == 1 and int(btf[0], 16) > 0, "SETUP: nonempty BTF missing")
      require(metadata["diagnostic"] == metadata["control"], "SETUP: diagnostic/control metadata mismatch")
      require(metadata["diagnostic"][0] == (pair.name.replace("-", "_") + "\n").encode("ascii"),
              "SETUP: component/module name mismatch")
    require("v1_module_verifier" not in sys.modules, "old verifier already imported")
    cls.old = ModuleType("v1_module_verifier")
    cls.old.__file__ = str(VERIFIER)
    sys.modules[cls.old.__name__] = cls.old
    exec(compile(source, str(VERIFIER), "exec"), cls.old.__dict__)
    require(cls.old.RUN == 0 and all(cls.old.EXPECTED[pair.name][0] != pair.diagnostic_sha256 for pair in PAIRS),
            "SETUP: verifier is not the untouched legacy identity boundary")
    save(WORK / "setup.json", {"verdict": "PASS", "real_tool_commands": tools.count,
                              "module_pairs": 2, "v2_hash_metadata_elf_btf_prefix": True,
                              "legacy_source_sha256": VERIFIER_SHA256, "symvers_sha256": SYMVERS_SHA256})

  def test_real_v2_pair_is_accepted(self) -> None:
    rejection: str | None = None
    try:
      self.old.main()
    except RuntimeError as error:
      rejection = str(error)
    save(WORK / "v2-boundary-observation.json", {
      "rejection": rejection, "legacy_child_count": self.old.RUN,
      "expected_boundary": "legacy v1 module identity excludes actual v2",
      "legacy_verifier_defect_claimed": False, "module_loaded": False,
    })
    require(rejection in (None, "diagnostic drift"), "unexpected legacy rejection is not version-boundary RED")
    self.assertEqual(self.old.RUN, 0, "legacy child runner must not run in this boundary fixture")
    self.assertIsNone(rejection, "expected version-boundary RED: legacy v1 verifier rejects the valid v2 pair")


if __name__ == "__main__":
  unittest.main(verbosity=2)
