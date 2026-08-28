"""Private no-change archive/index control. Run only inside a fresh reviewed R4.

Required read-only mounts are /inputs/base, /inputs/helper/cpio_image.py, and
/inputs/index-inputs/{modules.order,modules.builtin,modules.builtin.modinfo}.
This workload never extracts a general archive or constructs a diagnostic image.
It lists archive streams, recompresses the unchanged main stream with GNU gzip's
stdin defaults, and requires full byte identity before any index control.

Only verified regular, non-hardlinked archive modules enter two fresh private
roots. Archive nlink 0 or 1 is allowed; each physical copy must have st_nlink 1.
The regeneration root retains its text inputs and every generated output. The
lookup root contains only the same modules and seven byte-identical indexes, so
text-index fallback cannot satisfy binary lookup checks. No file is removed.
Every modprobe invocation has explicit no-load flags, root, version, and an empty
private configuration. No retry, alternative compression, or repair is allowed.
"""

from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import stat
import subprocess
import sys
from typing import BinaryIO
import zlib


KERNEL = "7.1.6-1-1-ARCH"
BASE = Path("/inputs/base")
BASE_SHA256 = "ae8f1ed7f4f258f89931209cd7de6030be9f6875372d7329151b822a6ba2281f"
BASE_BYTES = 19184103
MAIN_OFFSET = 10240
MAIN_BYTES = 61265920
HELPER = Path("/inputs/helper/cpio_image.py")
HELPER_SHA256 = "a32eddd159263d19ff87d7e9caee9d53d17ef5c350fbffe9e7eb142cb43ebf58"
INDEX_INPUTS = {
  "modules.order": "497c8546d3131d01191f7a66b68047abce5e5235ae982890180007f55c51a927",
  "modules.builtin": "74de5bab05fe70496f7702d83974adf8816ea826f1d8579f3b3f4b28a3890d2b",
  "modules.builtin.modinfo": "702d4cabaa9bdc1b282d0e419ba091f64dc06ba737fe7319928bb3003adeea4b",
}
INDEX_NAMES = frozenset((
  "modules.alias.bin", "modules.builtin.alias.bin", "modules.builtin.bin",
  "modules.dep.bin", "modules.devname", "modules.softdep", "modules.symbols.bin",
))
EXTRA_TEXT_INDEXES = frozenset((
  "modules.alias", "modules.dep", "modules.symbols", "modules.weakdep",
))
ARCHIVE_MODULE_PREFIX = f"usr/lib/modules/{KERNEL}/"
MODULE_DIRECTORY = Path("lib/modules") / KERNEL
CONTROL_ROOT = Path("/work/control-root")
LOOKUP_ROOT = Path("/work/lookup-root")
EMPTY_CONFIG = Path("/work/empty-modprobe.conf")
ENVIRONMENT = {"PATH": "/usr/bin:/bin", "LC_ALL": "C", "LANG": "C", "TMPDIR": "/tmp"}


def require(condition: bool, message: str) -> None:
  if not condition:
    raise RuntimeError(message)


def file_identity(info: os.stat_result) -> tuple[int, ...]:
  # Reading a sealed input can change atime; it must not change these fields.
  return (info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_gid,
          info.st_nlink, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def isolated() -> None:
  require(os.getuid() == 1001 and os.getgid() == 1001, "unexpected workload identity")
  require(Path.cwd() == Path("/work"), "not in the fresh workload directory")
  require(sys.flags.isolated == 1 and sys.flags.no_site == 1 and sys.dont_write_bytecode,
          "isolated Python flags required")
  require(not any(Path(path).exists() for path in ("/proc", "/sys", "/run", "/boot", "/home")),
          "host tree visible")
  require(stat.S_ISDIR(Path("/work").lstat().st_mode), "work root is not a real directory")


def authenticate_helper() -> None:
  isolated()
  require("cpio_image" not in sys.modules, "an unverified helper is already imported")
  for directory in (Path("/inputs"), HELPER.parent):
    require(stat.S_ISDIR(directory.lstat().st_mode), "helper parent is not a real directory")
  named = HELPER.lstat()
  require(stat.S_ISREG(named.st_mode) and named.st_nlink == 1 and 0 < named.st_size < 128 * 1024,
          "helper is not a bounded regular single-link file")
  descriptor = os.open(HELPER, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC)
  with os.fdopen(descriptor, "rb") as stream:
    before = os.fstat(stream.fileno())
    require(file_identity(before) == file_identity(named), "helper changed while opening")
    raw = stream.read(128 * 1024)
    after = os.fstat(stream.fileno())
  for actual in (after, HELPER.lstat()):
    require(file_identity(before) == file_identity(actual), "helper changed while reading")
  require(len(raw) == before.st_size and hashlib.sha256(raw).hexdigest() == HELPER_SHA256,
          "helper source drift")
  # The launcher independently pins this entire read-only directory before/after.
  sys.path.insert(0, str(HELPER.parent))


authenticate_helper()
from cpio_image import Archive, Member, parse_newc, read_regular, replace_members, write_new
require(sys.modules["cpio_image"].__file__ == str(HELPER), "wrong helper was imported")


def save_json(name: str, value: object) -> None:
  write_new(Path("/work") / name, (json.dumps(value, sort_keys=True, indent=2) + "\n").encode("ascii"))


def output_stream(path: Path) -> BinaryIO:
  require(path.parent == Path("/work"), "child output escaped work root")
  descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
  return os.fdopen(descriptor, "wb")


@dataclass
class Commands:
  count: int = 0

  def run(self, command: tuple[str, ...], *, payload: bytes | None = None,
          output_bound: int = 8 * 1024 * 1024) -> bytes:
    prefix = f"child-{self.count:03d}"
    self.count += 1
    stdout = Path("/work") / f"{prefix}.stdout"
    stderr = Path("/work") / f"{prefix}.stderr"
    timed_out = False
    returncode: int | None = None
    with output_stream(stdout) as output, output_stream(stderr) as errors:
      try:
        result = subprocess.run(command, input=payload, stdin=None if payload is not None else subprocess.DEVNULL,
                                stdout=output, stderr=errors, env=ENVIRONMENT, check=False, timeout=90)
        returncode = result.returncode
      except subprocess.TimeoutExpired:
        timed_out = True
      finally:
        output.flush()
        errors.flush()
        os.fsync(output.fileno())
        os.fsync(errors.fileno())
    save_json(f"{prefix}.result.json", {
      "command": command, "exit_code": returncode, "timed_out": timed_out,
      "stdout": stdout.name, "stderr": stderr.name,
      "requested_stdin_bytes": len(payload) if payload is not None else 0,
    })
    # Raw output and status are already durable even when a check fails.
    require(not timed_out and returncode == 0, "workload child failed; inspect its retained result")
    require(stderr.stat().st_size == 0, "workload child wrote stderr; stop for review")
    require(stdout.stat().st_size <= output_bound, "workload child output exceeds bound")
    return read_regular(stdout)


def main_stream(base: bytes) -> bytes:
  compressed = base[MAIN_OFFSET:]
  require(compressed[:3] == b"\x1f\x8b\x08", "fixed gzip boundary is wrong")
  decoder = zlib.decompressobj(16 + zlib.MAX_WBITS)
  try:
    raw = decoder.decompress(compressed, MAIN_BYTES + 1)
  except zlib.error:
    raise RuntimeError("invalid main gzip stream") from None
  require(len(raw) == MAIN_BYTES, "main stream size differs or exceeds bound")
  require(decoder.eof and not decoder.unconsumed_tail and not decoder.unused_data,
          "truncated, concatenated, or trailing gzip data")
  return raw


def member_report(member: Member) -> dict[str, object]:
  return {
    "name": member.name, "raw_name_hex": member.raw_name.hex(), "fields": member.fields,
    "payload_sha256": hashlib.sha256(member.payload).hexdigest(),
    "record_sha256": hashlib.sha256(member.raw).hexdigest(),
  }


def listed_names(raw: bytes, archive: Archive) -> tuple[str, ...]:
  require(raw.endswith(b"\n") and b"\r" not in raw, "unexpected archive-list line format")
  lines = raw[:-1].decode("ascii").split("\n")
  require(len(lines) == len(archive.members), "archive-list count differs")
  names: list[str] = []
  for line, member in zip(lines, archive.members, strict=True):
    # Listing tools may add a directory slash. Raw parser rules stay unchanged.
    if line in (".", "./"):
      normalized = "."
    else:
      normalized = line[2:] if line.startswith("./") else line
      if stat.S_ISDIR(member.fields[1]) and normalized.endswith("/"):
        normalized = normalized[:-1]
    require(normalized == member.name, "archive-list name/order differs")
    names.append(normalized)
  return tuple(names)


def archive_control(base: bytes, commands: Commands) -> Archive:
  early_raw, main_raw = base[:MAIN_OFFSET], main_stream(base)
  early, main = parse_newc(early_raw), parse_newc(main_raw)
  require(len(early.members) == 7 and len(main.members) == 1162, "archive member counts differ")
  require(replace_members(early, {}, ()) == early_raw and replace_members(main, {}, ()) == main_raw,
          "no-op archive transformation changed bytes")
  save_json("archive-members.json", {
    "early": [member_report(member) for member in early.members],
    "main": [member_report(member) for member in main.members],
    "early_tail_sha256": hashlib.sha256(early.tail).hexdigest(),
    "main_tail_sha256": hashlib.sha256(main.tail).hexdigest(),
  })
  for label, archive in (("early", early), ("main", main)):
    path = Path("/work") / f"{label}.cpio"
    write_new(path, archive.raw)
    cpio = commands.run(("/usr/bin/cpio", "--list", "--quiet", "--file", str(path)))
    bsdtar = commands.run(("/usr/bin/bsdtar", "--list", "--file", str(path)))
    require(listed_names(cpio, archive) == listed_names(bsdtar, archive), "archive tools disagree")
  # Installed mkinitcpio create_image pipes newc to gzip with COMPRESSION_OPTIONS=().
  recompressed = commands.run(("/usr/bin/gzip",), payload=main_raw, output_bound=256 * 1024 * 1024)
  reconstructed = early_raw + recompressed
  identical = reconstructed == base
  save_json("archive-control.json", {
    "verdict": "PASS" if identical else "STOP",
    "base_sha256": BASE_SHA256, "base_bytes": len(base), "gzip_offset": MAIN_OFFSET,
    "main_uncompressed_bytes": len(main_raw), "main_compressed_bytes": len(recompressed),
    "reconstructed_sha256": hashlib.sha256(reconstructed).hexdigest(),
    "byte_identical": identical, "general_archive_extracted": False, "diagnostic_image_created": False,
  })
  require(identical, "GNU gzip reconstruction differs; stop without trying another compressor setting")
  return main


@dataclass(frozen=True)
class Module:
  name: str
  relative: Path
  member: Member


def regular_member(member: Member) -> None:
  require(stat.S_ISREG(member.fields[1]) and member.fields[4] in (0, 1),
          "selected archive input is not regular and non-hardlinked")


def module_name(filename: str) -> str:
  match = re.fullmatch(r"([A-Za-z0-9_][A-Za-z0-9_-]*)\.ko(?:\.(?:gz|xz|zst))?", filename)
  if match is None:
    raise RuntimeError("unsupported module filename")
  return match.group(1).replace("-", "_")


def select_modules(archive: Archive) -> tuple[Module, ...]:
  modules: list[Module] = []
  names: set[str] = set()
  for member in archive.members:
    filename = Path(member.name).name
    if re.search(r"\.ko(?:\.|$)", filename) is None:
      continue
    require(member.name.startswith(ARCHIVE_MODULE_PREFIX), "module outside the fixed kernel tree")
    regular_member(member)
    relative = Path(member.name.removeprefix(ARCHIVE_MODULE_PREFIX))
    require(relative.parts[0] == "kernel" and all(not char.isspace() for char in str(relative)),
            "unexpected module placement")
    name = module_name(filename)
    require(name not in names, "ambiguous module lookup name")
    names.add(name)
    modules.append(Module(name, relative, member))
  require(len(modules) == 199, "base module count differs")
  require("phy_apple_atc" in names and "tps6598x_core" in names and "dwc3_apple" not in names,
          "base module identities differ")
  return tuple(modules)


def select_indexes(archive: Archive) -> dict[str, bytes]:
  indexes: dict[str, bytes] = {}
  for member in archive.members:
    if not member.name.startswith(ARCHIVE_MODULE_PREFIX):
      continue
    relative = member.name.removeprefix(ARCHIVE_MODULE_PREFIX)
    if "/" not in relative and relative.startswith("modules."):
      require(relative in INDEX_NAMES, "unexpected retained image index")
      regular_member(member)
      indexes[relative] = member.payload
  require(set(indexes) == INDEX_NAMES, "retained image index set differs")
  return indexes


@dataclass(frozen=True)
class FileState:
  identity: tuple[int, ...]
  sha256: str


@dataclass(frozen=True)
class TreeState:
  directories: dict[str, tuple[int, ...]]
  files: dict[str, FileState]


def snapshot(root: Path) -> TreeState:
  files: dict[str, FileState] = {}
  directories: dict[str, tuple[int, ...]] = {}
  pending = [root]
  while pending:
    directory = pending.pop()
    info = directory.lstat()
    require(stat.S_ISDIR(info.st_mode), "non-directory in private tree")
    directories[str(directory.relative_to(root))] = (
      info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_gid,
    )
    with os.scandir(directory) as entries:
      for entry in entries:
        info = entry.stat(follow_symlinks=False)
        path = Path(entry.path)
        if stat.S_ISDIR(info.st_mode):
          pending.append(path)
        else:
          require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1,
                  "non-regular or hardlinked private tree entry")
          payload = read_regular(path)
          after = path.lstat()
          require(file_identity(info) == file_identity(after),
                  "private tree file changed during its snapshot")
          files[str(path.relative_to(root))] = FileState(
            file_identity(info), hashlib.sha256(payload).hexdigest(),
          )
        require(len(files) + len(directories) + len(pending) <= 8192, "private tree exceeds bound")
  return TreeState(directories, files)


def build_root(root: Path, modules: tuple[Module, ...], metadata: dict[str, bytes]) -> TreeState:
  require(root in (CONTROL_ROOT, LOOKUP_ROOT), "unapproved private root")
  root.mkdir(mode=0o700)
  payloads = {MODULE_DIRECTORY / module.relative: module.member.payload for module in modules}
  for name, payload in metadata.items():
    require(name in INDEX_NAMES or name in INDEX_INPUTS, "unapproved root metadata")
    payloads[MODULE_DIRECTORY / name] = payload
  directories: set[Path] = set()
  for relative in payloads:
    directories.update(parent for parent in relative.parents if parent != Path("."))
  for relative in sorted(directories, key=lambda path: (len(path.parts), str(path))):
    (root / relative).mkdir(mode=0o700)
  for relative, payload in payloads.items():
    write_new(root / relative, payload)
  state = snapshot(root)
  require(set(state.files) == {str(path) for path in payloads}, "private root contains unexpected files")
  for relative, payload in payloads.items():
    require(state.files[str(relative)].sha256 == hashlib.sha256(payload).hexdigest(), "root copy differs")
  return state


def index_control(modules: tuple[Module, ...], indexes: dict[str, bytes],
                  inputs: dict[str, bytes], commands: Commands) -> None:
  before = build_root(CONTROL_ROOT, modules, inputs)
  save_json("control-root-before.json", asdict(before))
  commands.run(("/usr/bin/depmod", "-b", str(CONTROL_ROOT), KERNEL))
  after = snapshot(CONTROL_ROOT)
  save_json("control-root-after.json", asdict(after))
  expected_files = set(before.files) | {
    str(MODULE_DIRECTORY / name) for name in INDEX_NAMES | EXTRA_TEXT_INDEXES
  }
  require(set(after.files) == expected_files, "unexpected depmod output set; stop for review")
  require(read_regular(CONTROL_ROOT / MODULE_DIRECTORY / "modules.weakdep") ==
          b"# Weak dependencies extracted from modules themselves.\n",
          "unexpected weak dependency content; stop for review")
  require(after.directories == before.directories, "depmod changed the directory structure or identity")
  require(all(after.files.get(name) == state for name, state in before.files.items()),
          "depmod changed a copied module or one of its pinned text inputs")
  comparisons: list[dict[str, object]] = []
  for name in sorted(INDEX_NAMES):
    actual = read_regular(CONTROL_ROOT / MODULE_DIRECTORY / name)
    comparisons.append({
      "name": name, "expected_sha256": hashlib.sha256(indexes[name]).hexdigest(),
      "actual_sha256": hashlib.sha256(actual).hexdigest(), "byte_identical": actual == indexes[name],
    })
  identical = all(item["byte_identical"] is True for item in comparisons)
  save_json("index-control.json", {"verdict": "PASS" if identical else "STOP", "indexes": comparisons})
  require(identical, "no-change index regeneration differs; stop without rebuilding an image")


def builtin_names(raw: bytes) -> set[str]:
  names: set[str] = set()
  for line in raw.decode("ascii").splitlines():
    path = Path(line)
    require(bool(path.parts) and not path.is_absolute() and path.parts[0] == "kernel" and ".." not in path.parts,
            "invalid pinned builtin path")
    names.add(module_name(path.name))
  require(bool(names), "empty pinned builtin list")
  return names


def modprobe_command(*arguments: str) -> tuple[str, ...]:
  return ("/usr/bin/modprobe", "--dry-run", "--show-depends", "-d", str(LOOKUP_ROOT),
          "-S", KERNEL, "-C", str(EMPTY_CONFIG), *arguments)


def binary_lookup(modules: tuple[Module, ...], indexes: dict[str, bytes],
                  builtins: set[str], commands: Commands) -> None:
  before = build_root(LOOKUP_ROOT, modules, indexes)
  save_json("lookup-root-before.json", asdict(before))
  require(len(before.files) == 199 + 7, "binary-only root file count differs")
  write_new(EMPTY_CONFIG, b"")
  commands.run(("/usr/bin/modinfo", "--help"))
  commands.run(modprobe_command("--help"))
  known_files = {str(LOOKUP_ROOT / MODULE_DIRECTORY / module.relative) for module in modules}
  results: list[dict[str, object]] = []
  for module in modules:
    expected = str(LOOKUP_ROOT / MODULE_DIRECTORY / module.relative)
    raw_info = commands.run(("/usr/bin/modinfo", "-b", str(LOOKUP_ROOT), "-k", KERNEL,
                             "-F", "filename", module.name), output_bound=8192)
    require(raw_info == (expected + "\n").encode("ascii"), "binary module lookup differs")
    raw_dependencies = commands.run(modprobe_command(module.name), output_bound=1024 * 1024)
    insmod: list[str] = []
    builtin: list[str] = []
    # These are dry-run descriptions. No returned line is executed.
    for line in raw_dependencies.decode("ascii").splitlines():
      words = shlex.split(line, comments=False, posix=True)
      require(len(words) == 2, "unexpected dry-run dependency output")
      if words[0] == "insmod":
        require(words[1] in known_files, "dependency is outside the base module set")
        insmod.append(words[1])
      elif words[0] == "builtin":
        require(words[1].replace("-", "_") in builtins, "dependency is not a pinned builtin")
        builtin.append(words[1])
      else:
        raise RuntimeError("unexpected dry-run action; no install commands are accepted")
    require(expected in insmod, "dry-run target module is missing")
    results.append({"module": module.name, "filename": expected, "insmod": insmod, "builtin": builtin})
  after = snapshot(LOOKUP_ROOT)
  save_json("lookup-root-after.json", asdict(after))
  require(after == before, "read-only module resolution changed the binary-only root")
  require(read_regular(EMPTY_CONFIG) == b"", "private modprobe configuration changed")
  save_json("binary-lookup.json", {"verdict": "PASS", "module_count": len(results), "modules": results,
                                   "no_load": True, "text_index_fallback_available": False})


def main() -> None:
  isolated()
  os.umask(0o077)
  require(not CONTROL_ROOT.exists() and not LOOKUP_ROOT.exists() and not EMPTY_CONFIG.exists(),
          "control outputs already exist; use a fresh sandbox run")
  base = read_regular(BASE, BASE_SHA256)
  require(len(base) == BASE_BYTES, "base image size differs")
  inputs = {name: read_regular(Path("/inputs/index-inputs") / name, digest)
            for name, digest in INDEX_INPUTS.items()}
  commands = Commands()
  main_archive = archive_control(base, commands)
  modules, indexes = select_modules(main_archive), select_indexes(main_archive)
  index_control(modules, indexes, inputs, commands)
  binary_lookup(modules, indexes, builtin_names(inputs["modules.builtin"]), commands)
  # Both scratch roots remain retained, and immutable mounted inputs must still match.
  require(read_regular(BASE, BASE_SHA256) == base, "base image changed")
  for name, digest in INDEX_INPUTS.items():
    require(read_regular(Path("/inputs/index-inputs") / name, digest) == inputs[name], "index input changed")
  read_regular(HELPER, HELPER_SHA256)
  report = {
    "level": "info", "check": "no_change_archive_and_indexes", "verdict": "PASS",
    "base_sha256": BASE_SHA256, "early_members": 7, "main_members": 1162,
    "modules": len(modules), "retained_indexes": len(indexes), "commands": commands.count,
    "gzip_reconstruction_byte_identical": True, "all_indexes_byte_identical": True,
    "binary_only_lookup": True, "dry_run_dependency_resolution": True,
    "roots_retained": [str(CONTROL_ROOT), str(LOOKUP_ROOT)],
    "general_archive_extracted": False, "diagnostic_image_created": False, "module_loaded": False,
  }
  save_json("control-result.json", report)
  print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
  main()
