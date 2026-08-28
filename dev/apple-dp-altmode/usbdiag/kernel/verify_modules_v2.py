"""Verify only the fixed private C2 v2 pair; never load or build a module.

There is no version selector or identity override. Tool output is bounded while
it is read, retained before interpretation, and never used to learn new pins.
ELF checks cover this fixed AArch64 relocatable pair, not general ELF loading.
The approved no-install exception uses frozen stdlib models and JSON records.
"""

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import stat
import struct
import subprocess
import sys
import time
from types import ModuleType


HELPER = Path("/inputs/helper/cpio_image.py")
HELPER_SHA256 = "a32eddd159263d19ff87d7e9caee9d53d17ef5c350fbffe9e7eb142cb43ebf58"
SYMVERS_SHA256 = "d5eea549b9333f717fdc932683ea6633d58049c1e3f8f9e0be12e05d7610dd82"
REVISION = "dev147-usbdiag2-v1"
MAX_INPUT = 16 * 1024 * 1024
FIELDS = ("name", "vermagic", "depends", "alias")
ADDITIONS = frozenset(("_printk", "alt_cb_patch_nops", "of_machine_compatible_match",
                       "of_find_node_opts_by_path", "of_node_put"))


class VerificationError(RuntimeError):
  """A fixed identity, metadata, or containment contract failed."""


def require(condition: bool, detail: str) -> None:
  if not condition:
    raise VerificationError(detail)


def isolated() -> None:
  require(os.getuid() == os.getgid() == 1001 and Path.cwd() == Path("/work"), "unexpected workload identity/directory")
  require(sys.flags.isolated == 1 and sys.flags.no_site == 1 and sys.dont_write_bytecode,
          "isolated Python flags required")
  require(not any(Path(path).exists() for path in ("/proc", "/sys", "/run", "/home", "/boot")), "host tree visible")


def import_guard() -> ModuleType:
  isolated()
  for parent in HELPER.parents:
    require(stat.S_ISDIR(parent.lstat().st_mode), "guard parent is not a real directory")
  before = HELPER.lstat()
  require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and 0 < before.st_size < 128 * 1024,
          "guard source is not bounded regular single-link input")
  def identity(info: os.stat_result) -> tuple[int, ...]:
    return (info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_gid,
            info.st_nlink, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
  descriptor = os.open(HELPER, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC)
  with os.fdopen(descriptor, "rb") as stream:
    require(identity(os.fstat(stream.fileno())) == identity(before), "guard changed on open")
    raw = stream.read(128 * 1024)
    require(identity(os.fstat(stream.fileno())) == identity(before) == identity(HELPER.lstat()), "guard changed while reading")
  require(len(raw) == before.st_size and hashlib.sha256(raw).hexdigest() == HELPER_SHA256, "guard source drift")
  name = "dev147_v2_file_guard"
  require(name not in sys.modules, "file guard already imported")
  module = ModuleType(name)
  module.__file__ = str(HELPER)
  sys.modules[name] = module
  exec(compile(raw, str(HELPER), "exec"), module.__dict__)
  return module


guard = import_guard()


class Role(Enum):
  DIAGNOSTIC = "diagnostic"
  CONTROL = "control"


@dataclass(frozen=True)
class Identity:
  name: str
  component: str
  diagnostic_sha256: str
  diagnostic_build_id: str
  control_sha256: str
  control_build_id: str
  marker_count: int
  control_import_count: int


IDENTITIES = (
  Identity("dwc3-apple", "dwc3", "d9090119fee0252c9031185128ddd9d03bef9a0cbdfb118d8c71b7161d48b425",
           "92014543045243fb1680ac0e56b34c3ce69cc503",
           "d213e676593c1c4f9daceba1002f2381b6d390ce3eff9995043991a4d1e20975",
           "c0628ff7e26e3e3cb0dda8517bc2a34511ae85be", 20, 33),
  Identity("phy-apple-atc", "atc", "dea7e4eaee8928441a44480843795a68905e5122d435ae86dacc06fdf7b0efbe",
           "dc5bed70afdb1aa22a8cddd0a7f5ac2a2256ba49",
           "edb76a5fd6458406f6371f842a7a6a2b5f8b22b404ba622a5d081302662cc568",
           "def6d3cb64d2f7fff393c9da6fdde2e9ebbfc2c9", 14, 29),
)


def identity_for(name: str) -> Identity:
  matches = tuple(identity for identity in IDENTITIES if identity.name == name)
  require(len(matches) == 1, "unknown module identity")
  return matches[0]


def expected(name: str, role: Role) -> tuple[str, str]:
  identity = identity_for(name)
  require(type(role) is Role, "unknown module role")
  if role is Role.DIAGNOSTIC:
    return identity.diagnostic_sha256, identity.diagnostic_build_id
  return identity.control_sha256, identity.control_build_id


def read_fixed(path: Path, digest: str) -> bytes:
  require(path.is_absolute() and len(path.parts) <= 32 and not any(part == ".." for part in path.parts), "unsafe input path")
  require(type(digest) is str and re.fullmatch(r"[0-9a-f]{64}", digest) is not None, "invalid input digest")
  # Reuse the pinned no-follow directory/identity guards with a tighter read cap.
  with guard._parent_directory(path) as parent:
    before = parent.named_file()
    identity = guard._file_identity(before)
    require(0 < before.st_size <= MAX_INPUT, "input size bound exceeded")
    descriptor = os.open(parent.leaf, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC,
                         dir_fd=parent.descriptor)
    with os.fdopen(descriptor, "rb") as stream:
      require(guard._file_identity(os.fstat(stream.fileno())) == identity, "input changed on open")
      raw = stream.read(before.st_size + 1)
      require(len(raw) == before.st_size and guard._file_identity(os.fstat(stream.fileno())) ==
              identity == guard._file_identity(parent.named_file()), "input changed while reading")
      parent.check()
    require(hashlib.sha256(raw).hexdigest() == digest, "input digest mismatch")
    return raw


def validate_identity(name: str, role: Role, raw: bytes) -> None:
  digest, _ = expected(name, role)
  require(type(raw) is bytes and 0 < len(raw) <= MAX_INPUT, "invalid module bytes")
  require(hashlib.sha256(raw).hexdigest() == digest, "module identity mismatch")


def ascii_text(raw: bytes, *, bound: int = 1024 * 1024) -> str:
  require(type(bound) is int and 0 < bound <= MAX_INPUT and type(raw) is bytes and len(raw) <= bound,
          "metadata output size exceeded")
  require(all(value in (9, 10) or 32 <= value <= 126 for value in raw), "invalid metadata text")
  return raw.decode("ascii")


@dataclass
class Commands:
  root: Path
  count: int = 0

  def __post_init__(self) -> None:
    require(self.root.parent == Path("/work") and self.root.name.startswith("v2-"), "unsafe output root")
    self.root.mkdir(mode=0o700)

  def run(self, command: tuple[str, ...], *, timeout: float = 20, bound: int = 1024 * 1024) -> bytes:
    require(type(command) is tuple and 1 <= len(command) <= 16 and
            all(type(word) is str and len(word) <= 4096 and "\0" not in word for word in command), "invalid child argv")
    require(command[0] in ("/usr/bin/modinfo", "/usr/bin/nm", "/usr/bin/readelf", "/usr/bin/python3.14"),
            "unapproved metadata/test executable")
    require(type(bound) is int and 0 < bound <= 1024 * 1024 and type(timeout) in (int, float) and
            0 < timeout <= 20, "invalid child bounds")
    label = f"child-{self.count:03d}"
    self.count += 1
    paths = (self.root / f"{label}.stdout", self.root / f"{label}.stderr")
    counts = [0, 0]
    status, code = "ok", None
    process: subprocess.Popen[bytes] | None = None
    with paths[0].open("xb") as output, paths[1].open("xb") as errors, selectors.DefaultSelector() as selector:
      streams = (output, errors)
      try:
        process = subprocess.Popen(command, cwd=Path("/work"), stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   env={"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C", "TMPDIR": "/tmp"})
        require(process.stdout is not None and process.stderr is not None, "child pipes absent")
        selector.register(process.stdout, selectors.EVENT_READ, 0)
        selector.register(process.stderr, selectors.EVENT_READ, 1)
        deadline = time.monotonic() + timeout
        while selector.get_map() and status == "ok":
          remaining = deadline - time.monotonic()
          if remaining <= 0:
            status = "timeout"
            break
          for key, _ in selector.select(min(remaining, 0.1)):
            index = key.data
            capacity = bound - counts[index]
            chunk = os.read(key.fd, min(65536, capacity + 1))
            if not chunk:
              selector.unregister(key.fileobj)
              continue
            streams[index].write(chunk[:capacity])
            counts[index] += len(chunk)
            if len(chunk) > capacity:
              status = "output_overflow"
              break
        if status == "ok":
          try:
            code = process.wait(timeout=max(0.001, deadline - time.monotonic()))
          except subprocess.TimeoutExpired:
            status = "timeout"
      except OSError:
        status = "child_io_error"
      finally:
        if process is not None:
          if process.poll() is None:
            process.kill()
          code = process.wait(timeout=5)
          if process.stdout is not None:
            process.stdout.close()
          if process.stderr is not None:
            process.stderr.close()
        for stream in streams:
          stream.flush()
          os.fsync(stream.fileno())
    guard.write_new(self.root / f"{label}.json", (json.dumps({
      "command": command, "returncode": code, "status": status, "deadline_seconds": timeout,
      "stream_bound": bound, "observed_bytes": counts, "retained_bytes": [path.stat().st_size for path in paths],
    }, sort_keys=True) + "\n").encode("ascii"))
    require(status == "ok", f"child {status}")
    require(code == 0, "child nonzero exit")
    require(counts[1] == 0, "child wrote stderr")
    raw = guard.read_regular(paths[0])
    ascii_text(raw)
    return raw


@dataclass(frozen=True, order=True)
class Import:
  name: str
  binding: str


def parse_imports(raw: bytes) -> tuple[Import, ...]:
  text = ascii_text(raw)
  require(text.endswith("\n") and 0 < len(text.splitlines()) <= 4096, "invalid import lines")
  result: list[Import] = []
  for line in text.splitlines():
    match = re.fullmatch(r"[ \t]*([Uwv]) ([A-Za-z_][A-Za-z0-9_.$]{0,255})", line)
    require(match is not None, "malformed import line")
    result.append(Import(match[2], match[1]))
  require(len({entry.name for entry in result}) == len(result), "duplicate import name")
  return tuple(sorted(result))


def validate_import_delta(name: str, diagnostic: tuple[Import, ...], control: tuple[Import, ...]) -> None:
  identity = identity_for(name)
  baseline, actual = set(control), set(diagnostic)
  added = {Import(symbol, "U") for symbol in ADDITIONS}
  require(len(control) == len(baseline) == identity.control_import_count and
          len(diagnostic) == len(actual) == identity.control_import_count + 5, "import count differs")
  require(all(entry.binding == "U" for entry in control) and not baseline & added,
          "control import binding/set differs")
  require(actual - baseline == added and not baseline - actual, "binding-aware import delta differs")


def validate_exports(raw: bytes) -> None:
  text = ascii_text(raw, bound=MAX_INPUT)
  require(text.endswith("\n") and len(text.splitlines()) <= 32768, "invalid symvers text")
  found: set[str] = set()
  for line in text.splitlines():
    fields = line.split("\t")
    if len(fields) < 2 or fields[1] not in ADDITIONS:
      continue
    require(len(fields) == 5 and re.fullmatch(r"0x[0-9a-fA-F]{8}", fields[0]) is not None and
            fields[2:] == ["vmlinux", "EXPORT_SYMBOL", ""], "unreviewed export owner/type/namespace")
    require(fields[1] not in found, "duplicate required export")
    found.add(fields[1])
  require(found == ADDITIONS, "required export missing")


def validate_markers(name: str, role: Role, raw: bytes) -> None:
  identity_for(name)
  expected(name, role)
  if role is Role.CONTROL:
    require(b"dev147-usbdiag" not in raw, "control contains diagnostic markers")
    return
  identity = identity_for(name)
  prefix = ('{"schema":1,"revision":"dev147-usbdiag2-v1","board":"j413",'
            f'"component":"{identity.component}","target":"front_lower",'
            '"seq":%u,"generation":%u,').encode("ascii")
  if identity.component == "dwc3":
    prefix += b'"attempt":%u,'
  require(raw.count(b"dev147-usbdiag") == raw.count(prefix) == identity.marker_count,
          "diagnostic revision/component/prefix count differs")


@dataclass(frozen=True)
class Section:
  name: str
  kind: int
  offset: int
  size: int


def sections(raw: bytes) -> tuple[Section, ...]:
  require(type(raw) is bytes and 64 <= len(raw) <= MAX_INPUT and raw[:7] == b"\x7fELF\x02\x01\x01",
          "wrong or truncated ELF identification")
  fields = struct.unpack_from("<HHIQQQIHHHHHH", raw, 16)
  kind, machine, version, entry, phoff, shoff, _, ehsize, phsize, phnum, shsize, shnum, names_index = fields
  require((kind, machine, version, entry, phoff, ehsize, phsize, phnum, shsize) ==
          (1, 183, 1, 0, 0, 64, 0, 0, 64), "wrong AArch64 ET_REL header")
  require(0 < shnum <= 4096 and 0 < names_index < shnum and 64 <= shoff <= len(raw) - shnum * 64,
          "section table outside bounded ELF")
  headers = tuple(struct.unpack_from("<IIQQQQIIQQ", raw, shoff + index * 64) for index in range(shnum))
  for section in headers:
    require(section[1] == 8 or (section[4] <= len(raw) and section[5] <= len(raw) - section[4]),
            "section payload outside bounded ELF")
  names = headers[names_index]
  require(names[1] == 3 and names[5] > 0, "section-name string table missing")
  strings = raw[names[4]:names[4] + names[5]]
  result: list[Section] = []
  for header in headers:
    start = header[0]
    require(start < len(strings), "section-name offset out of bounds")
    end = strings.find(b"\0", start)
    require(start <= end <= start + 4096, "section-name terminator missing")
    name = ascii_text(strings[start:end])
    result.append(Section(name, header[1], header[4], header[5]))
  return tuple(result)


def validate_elf(name: str, role: Role, raw: bytes, readelf: bytes) -> None:
  _, build_id = expected(name, role)
  parsed = sections(raw)
  btf = tuple(section for section in parsed if section.name == ".BTF")
  notes = tuple(section for section in parsed if section.name == ".note.gnu.build-id")
  require(len(btf) == 1 and btf[0].kind == 1 and btf[0].size > 0, "nonempty BTF PROGBITS missing")
  require(len(notes) == 1 and notes[0].kind == 7 and notes[0].size == 36, "single bounded build-id note missing")
  note = raw[notes[0].offset:notes[0].offset + notes[0].size]
  require(struct.unpack_from("<III", note) == (4, 20, 3) and note[12:16] == b"GNU\0" and
          note[16:].hex() == build_id, "raw build identity differs")
  text = ascii_text(readelf)
  for pattern in (r"^\s*Class:\s+ELF64\s*$", r"^\s*Data:\s+2's complement, little endian\s*$",
                  r"^\s*Type:\s+REL\s", r"^\s*Machine:\s+AArch64\s*$"):
    require(len(re.findall(pattern, text, re.MULTILINE)) == 1, "readelf header differs")
  require(re.findall(r"Build ID: ([0-9a-f]+)", text) == [build_id], "readelf build identity differs")
  shown = re.findall(r"^\s*\[\s*\d+\]\s+\.BTF\s+PROGBITS\s+[0-9a-fA-F]+\s+"
                     r"([0-9a-fA-F]+)\s+([0-9a-fA-F]+)\s", text, re.MULTILINE)
  require(len(shown) == 1 and tuple(int(value, 16) for value in shown[0]) == (btf[0].offset, btf[0].size),
          "readelf/raw BTF placement differs")


@dataclass(frozen=True)
class Metadata:
  name: bytes
  vermagic: bytes
  depends: bytes
  alias: bytes


def validate_metadata(name: str, diagnostic: Metadata, control: Metadata) -> None:
  identity_for(name)
  for metadata in (diagnostic, control):
    for value in (metadata.name, metadata.vermagic, metadata.depends, metadata.alias):
      ascii_text(value)
  require(diagnostic == control and diagnostic.name == (name.replace("-", "_") + "\n").encode("ascii") and
          diagnostic.vermagic.startswith(b"7.1.6-1-1-ARCH "), "module metadata differs")


def main() -> None:
  isolated()
  os.umask(0o077)
  symvers = read_fixed(Path("/inputs/symvers"), SYMVERS_SHA256)
  validate_exports(symvers)
  commands = Commands(Path("/work/v2-module-checks"))
  reports: list[dict[str, object]] = []
  for identity in IDENTITIES:
    metadata: dict[Role, Metadata] = {}
    imports: dict[Role, tuple[Import, ...]] = {}
    for role in Role:
      path = Path("/inputs") / role.value / f"{identity.name}.ko"
      digest, _ = expected(identity.name, role)
      raw = read_fixed(path, digest)
      validate_identity(identity.name, role, raw)
      validate_markers(identity.name, role, raw)
      metadata[role] = Metadata(*(commands.run(("/usr/bin/modinfo", "-F", field, str(path))) for field in FIELDS))
      imports[role] = parse_imports(commands.run(("/usr/bin/nm", "-u", str(path))))
      validate_elf(identity.name, role, raw, commands.run(("/usr/bin/readelf", "-h", "-n", "-SW", str(path))))
      read_fixed(path, digest)
    validate_metadata(identity.name, metadata[Role.DIAGNOSTIC], metadata[Role.CONTROL])
    validate_import_delta(identity.name, imports[Role.DIAGNOSTIC], imports[Role.CONTROL])
    reports.append({"module": identity.name, "component": identity.component, "revision": REVISION,
                    "sha256": identity.diagnostic_sha256, "build_id": identity.diagnostic_build_id,
                    "control_sha256": identity.control_sha256, "control_build_id": identity.control_build_id,
                    "marker_count": identity.marker_count, "added_imports": sorted(ADDITIONS), "binding": "U"})
  read_fixed(Path("/inputs/symvers"), SYMVERS_SHA256)
  report = {"level": "info", "check": "fixed_c2_v2_module_pair", "verdict": "PASS", "modules": reports,
            "commands": commands.count, "removed_imports": [], "module_loaded": False, "image_changed": False}
  guard.write_new(commands.root / "RESULT.json", (json.dumps(report, sort_keys=True, indent=2) + "\n").encode("ascii"))
  print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
  require(len(sys.argv) == 1, "verifier accepts no arguments")
  main()
