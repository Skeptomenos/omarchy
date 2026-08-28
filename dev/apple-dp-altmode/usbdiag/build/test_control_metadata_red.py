"""Test the pinned old control builder's real metadata block, without building.

Run only in the reviewed private sandbox. Packaged inputs have both existing
extensionless mounts and normal .ko names. The two control modules are retained
real binaries, not generated fixtures. Setup proves the normal metadata reads
and matching bytes before either production-block assertion can count as RED.
No compiler, make, module loader, or live-system query is invoked.

The approved no-install exception uses unittest and typed stdlib models instead
of adding pytest/Pydantic dependencies to the pinned sandbox.
"""

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import unittest


BUILDER = Path("/inputs/old-builder")
BUILDER_SHA256 = "6bc859eee12b4b7db6a113e42b6a82918460b32a797959683c8c562f4c17f74e"
WORK = Path("/work/metadata-fixtures")
FIELDS = ("name", "vermagic", "depends", "alias")
START = "  for field in name vermagic depends alias; do\n"
END = '  /usr/bin/nm -u "$module.ko"'
ENVIRONMENT = {"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C", "TMPDIR": "/tmp"}


@dataclass(frozen=True)
class ModuleInput:
  name: str
  stock_sha256: str
  control_sha256: str


MODULES = (
  ModuleInput("dwc3-apple", "d150400f9782c876972b2745d95617cd44e23574452f63980704911a467f7767",
              "d213e676593c1c4f9daceba1002f2381b6d390ce3eff9995043991a4d1e20975"),
  ModuleInput("phy-apple-atc", "fd1c3d105bd69a649a38e89e2ca0bcbe6f656200a0f211d58211e8c7b3ec944b",
              "edb76a5fd6458406f6371f842a7a6a2b5f8b22b404ba622a5d081302662cc568"),
)


def require(condition: bool, detail: str) -> None:
  if not condition:
    raise RuntimeError(detail)


def identity(info: os.stat_result) -> tuple[int, ...]:
  return (info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_gid,
          info.st_nlink, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def pinned(path: Path, digest: str) -> bytes:
  before = path.lstat()
  require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and
          0 < before.st_size < 16 * 1024 * 1024, "unbounded or nonregular test input")
  descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC)
  with os.fdopen(descriptor, "rb") as stream:
    require(identity(os.fstat(stream.fileno())) == identity(before), "input changed on open")
    raw = stream.read(16 * 1024 * 1024)
    require(identity(os.fstat(stream.fileno())) == identity(before) == identity(path.lstat()),
            "input changed while reading")
  require(len(raw) == before.st_size and hashlib.sha256(raw).hexdigest() == digest,
          "input source pin mismatch")
  return raw


def metadata_block(raw: bytes) -> str:
  source = raw.decode("ascii")
  require(source.count(START) == source.count(END) == 1, "metadata extraction anchor drift")
  start, end = source.index(START), source.index(END)
  require(start < end, "metadata extraction order drift")
  block = source[start:end]
  require(block.endswith("  done\n") and block.count("/usr/bin/modinfo") == 2,
          "metadata extraction boundary drift")
  return block


def save(path: Path, raw: bytes) -> None:
  with path.open("xb") as stream:
    stream.write(raw)
    stream.flush()
    os.fsync(stream.fileno())


@dataclass(frozen=True)
class Observation:
  returncode: int | None
  timed_out: bool
  stdout: bytes
  stderr: bytes


def run(label: str, command: tuple[str, ...]) -> Observation:
  stdout, stderr = WORK / f"{label}.stdout", WORK / f"{label}.stderr"
  timed_out = False
  returncode: int | None = None
  with stdout.open("xb") as output, stderr.open("xb") as errors:
    try:
      result = subprocess.run(command, cwd=WORK, env=ENVIRONMENT, stdin=subprocess.DEVNULL,
                              stdout=output, stderr=errors, timeout=10, check=False)
      returncode = result.returncode
    except subprocess.TimeoutExpired:
      timed_out = True
    output.flush()
    errors.flush()
    os.fsync(output.fileno())
    os.fsync(errors.fileno())
  save(WORK / f"{label}.json", (json.dumps({
    "command": command, "returncode": returncode, "timed_out": timed_out,
    "stdout_bytes": stdout.stat().st_size, "stderr_bytes": stderr.stat().st_size,
  }, sort_keys=True) + "\n").encode("ascii"))
  require(stdout.stat().st_size <= 65536 and stderr.stat().st_size <= 65536,
          "bounded metadata output exceeded")
  return Observation(returncode, timed_out, stdout.read_bytes(), stderr.read_bytes())


class ControlMetadataTests(unittest.TestCase):
  block: str

  @classmethod
  def setUpClass(cls) -> None:
    require(os.getuid() == os.getgid() == 1001 and Path.cwd() == Path("/work"),
            "unexpected test identity/directory")
    require(sys.flags.isolated == 1 and sys.flags.no_site == 1 and sys.dont_write_bytecode,
            "isolated Python flags required")
    require(not any(Path(name).exists() for name in ("/proc", "/sys", "/run", "/home", "/boot")),
            "host tree visible")
    os.umask(0o077)
    cls.block = metadata_block(pinned(BUILDER, BUILDER_SHA256))
    WORK.mkdir(mode=0o700)
    save(WORK / "extracted-metadata-block.sh", cls.block.encode("ascii"))
    for module in MODULES:
      stock = Path("/inputs/stock") / f"{module.name}.ko"
      original = Path("/inputs") / f"stock-{module.name}"
      control = Path("/inputs/control-modules") / f"{module.name}.ko"
      require(pinned(stock, module.stock_sha256) == pinned(original, module.stock_sha256),
              "dual-name packaged inputs are not identical")
      save(WORK / f"{module.name}.ko", pinned(control, module.control_sha256))
      for field in FIELDS:
        before = run(f"precheck-{module.name}-{field}-stock",
                     ("/usr/bin/modinfo", "-F", field, str(stock)))
        after = run(f"precheck-{module.name}-{field}-control",
                    ("/usr/bin/modinfo", "-F", field, str(WORK / f"{module.name}.ko")))
        require(not before.timed_out and not after.timed_out and
                before.returncode == after.returncode == 0 and not before.stderr and not after.stderr,
                "SETUP: real .ko metadata precheck failed")
        require(before.stdout == after.stdout, "SETUP: retained control metadata differs")
        if field == "name":
          require(before.stdout == (module.name.replace("-", "_") + "\n").encode("ascii"),
                  "SETUP: module name differs")
    save(WORK / "setup.json", b'{"real_metadata_prechecks":"PASS","dual_name_bytes":"PASS"}\n')

  def assert_metadata_accepted(self, name: str) -> None:
    result = run(f"production-{name}", ("/usr/bin/bash", "-eu", "-o", "pipefail", "-c",
                                      "module=$1\n" + self.block, "metadata-gate", name))
    self.assertFalse(result.timed_out, "timeout is not valid regression RED")
    self.assertEqual(result.returncode, 0,
                     f"real matching {name} metadata rejected by the extracted production block; "
                     f"stderr={result.stderr.decode('ascii', errors='backslashreplace')}")
    self.assertEqual(result.stderr, b"")

  def test_dwc3_existing_packaged_file_is_accepted(self) -> None:
    self.assert_metadata_accepted("dwc3-apple")

  def test_atc_existing_packaged_file_is_accepted(self) -> None:
    self.assert_metadata_accepted("phy-apple-atc")

  def test_source_pin_and_extraction_drift_fail_closed(self) -> None:
    raw = pinned(BUILDER, BUILDER_SHA256)
    altered = WORK / "drifted-builder.sh"
    save(altered, raw + b"\n# deliberate fixture drift\n")
    with self.assertRaisesRegex(RuntimeError, "source pin mismatch"):
      pinned(altered, BUILDER_SHA256)
    for bad in (raw.replace(START.encode(), b"# missing anchor\n", 1), raw + START.encode()):
      with self.subTest(drift=bad[-32:]), self.assertRaisesRegex(RuntimeError, "anchor drift"):
        metadata_block(bad)


if __name__ == "__main__":
  unittest.main(verbosity=2)
