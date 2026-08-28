#!/usr/bin/python3
"""Public archival D1 sandbox; its fixed paths are deliberately unusable.

Do not run this copy. R4's isolation proof belongs to the private pinned
original, not this redacted launcher. No input manifest is published here.

Tooling exception: D1 forbids dependency installation. Dataclasses and explicit
validation replace Pydantic; the real isolation probe replaces pytest here.
Ruff and mypy are unavailable, so their gates are not claimed as passed.
"""

import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import signal
import stat
import struct
import subprocess
import sys
import tempfile
import time


BASE = Path("/LOCAL_ONLY_DEV147_SANDBOX")
STAGE = Path("/LOCAL_ONLY_DEV147_STAGE")
GCC = Path("/usr/lib/gcc/aarch64-unknown-linux-gnu/16.1.1")
PERL = Path("/usr/lib/perl5/5.42/core_perl")
HEADERS = STAGE / "work/private-header-root/usr/lib/modules/7.1.6-1-1-ARCH/build"
ENVIRONMENT = {"PATH": "/usr/bin:/bin", "LC_ALL": "C"}
TOOLS = """bwrap bash sh make gcc cc cpp as ld ld.bfd ar nm objcopy objdump readelf
size strings strip ranlib perl jq bsdtar cpio gzip gunzip zcat depmod modprobe modinfo
kmod gpgv cat cp mkdir mv rm ln touch chmod stat readlink realpath dirname
basename find xargs grep sed gawk awk sort uniq head tail cut tr wc printf echo
test true false cmp diff od dd install sha256sum mktemp env date sleep timeout
expr uname nproc getconf which python3 python3.14""".split()

# Installed UAPI: EM_AARCH64=183, AUDIT_ARCH_64BIT=0x80000000,
# AUDIT_ARCH_LE=0x40000000; add_key/request_key/keyctl are 217/218/219.
# A foreign audit architecture is killed rather than interpreting wrong numbers.
KEYRING_FILTER = b"".join(struct.pack("<HBBI", *instruction) for instruction in (
  (0x20, 0, 0, 4), (0x15, 1, 0, 0xC00000B7), (0x06, 0, 0, 0x80000000),
  (0x20, 0, 0, 0), (0x15, 0, 1, 217), (0x06, 0, 0, 0x00050001),
  (0x15, 0, 1, 218), (0x06, 0, 0, 0x00050001),
  (0x15, 0, 1, 219), (0x06, 0, 0, 0x00050001), (0x06, 0, 0, 0x7FFF0000),
))


@dataclass(frozen=True, slots=True)
class Mount:
  source: str
  target: str
  fingerprint: str


def require(condition: bool, reason: str) -> None:
  if not condition:
    raise ValueError(reason)


def plain_path(path: Path, root: Path) -> Path:
  require(path.is_absolute() and ".." not in path.parts, "path must be absolute without traversal")
  require(path != root and path.is_relative_to(root), f"path is outside approved root: {path}")
  require(path.resolve(strict=True) == path, f"symlinked path rejected: {path}")
  current = path
  while current != root.parent:
    require(not current.is_symlink(), f"symlinked ancestor rejected: {current}")
    current = current.parent
  return path


def digest(path: Path) -> str:
  with path.open("rb") as stream:
    return hashlib.file_digest(stream, "sha256").hexdigest()


def fingerprint(path: Path, private: bool = False) -> str:
  result = hashlib.sha256()
  paths = [path]
  if path.is_dir():
    paths.extend(sorted(path.rglob("*")))
  for entry in paths:
    info = entry.lstat()
    require(stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode), f"special input rejected: {entry}")
    if private and stat.S_ISREG(info.st_mode):
      require(info.st_uid == 1001 and info.st_nlink == 1, f"private input ownership/hardlink rejected: {entry}")
    if entry.is_symlink():
      resolved = entry.resolve(strict=True)
      boundary = path if private else Path("/usr")
      require(resolved.is_relative_to(boundary), f"escaping input link rejected: {entry}")
      content = os.readlink(entry)
      require(not private or not Path(content).is_absolute(), f"absolute private link rejected: {entry}")
    elif entry.is_file():
      content = digest(entry)
    else:
      content = ""
    record = (
      str(entry.relative_to(path)), info.st_mode, info.st_uid, info.st_gid,
      info.st_nlink, info.st_size, info.st_dev, info.st_ino, info.st_mtime_ns,
      content,
    )
    result.update(json.dumps(record, separators=(",", ":")).encode())
    result.update(b"\n")
  return result.hexdigest()


def static_command(arguments: list[str]) -> str:
  result = subprocess.run(
    arguments, check=True, text=True, stdin=subprocess.DEVNULL,
    stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=ENVIRONMENT,
    close_fds=True, timeout=20,
  )
  return result.stdout


def tool_mounts() -> list[Mount]:
  selected: dict[str, Path] = {}
  queue: list[Path] = []

  def add(path: Path) -> None:
    path = Path(os.path.normpath(path))
    source = path.resolve(strict=True)
    require(source.is_relative_to(Path("/usr")), f"tool escapes /usr: {path}")
    target = Path("/usr") / path.relative_to("/") if path.parts[1] == "lib" else path
    previous = selected.get(str(target))
    require(previous is None or previous == source, f"conflicting tool destination: {target}")
    if previous is None:
      selected[str(target)] = source
      queue.append(source)

  for name in TOOLS:
    add(Path("/usr/bin", name))
  for directory in (GCC, PERL):
    add(directory)
    queue.extend(entry for entry in directory.rglob("*") if entry.is_file())
  # Use only the installed C library/UAPI header packages, not all /usr/include.
  for package in ("glibc", "linux-api-headers"):
    for line in static_command(["/usr/bin/pacman", "-Ql", package]).splitlines():
      package_path = Path(line.split(" ", 1)[1])
      if package_path.is_relative_to("/usr/include") and package_path != Path("/usr/include"):
        relative = package_path.relative_to("/usr/include")
        add(Path("/usr/include", relative.parts[0]))
  for name in (
    "crt1.o", "Scrt1.o", "crti.o", "crtn.o", "libc.so", "libc.so.6",
    "libc_nonshared.a", "libgcc_s.so", "libgcc_s.so.1", "libpthread.a",
    "libm.so", "libm.so.6", "libmvec.so.1", "ld-linux-aarch64.so.1",
  ):
    add(Path("/usr/lib", name))
  add(Path("/usr/share/pacman/keyrings/archlinuxarm.gpg"))
  # Pin the package-owned stdlib so ordinary lazy imports do not widen mounts
  # during a later run. Third-party site-packages are never exposed.
  python_root = Path("/usr/lib/python3.14")
  standard_library: set[Path] = set()
  for line in static_command(["/usr/bin/pacman", "-Ql", "python"]).splitlines():
    path = Path(line.split(" ", 1)[1])
    if path != python_root and path.is_relative_to(python_root):
      relative = path.relative_to(python_root)
      if relative.parts[0] == "lib-dynload":
        # Tk is optional and its libtk8.6 dependency is absent on this host.
        # This fixed GUI-only exclusion does not apply to any other extension.
        if path.is_file() and path.name != "_tkinter.cpython-314-aarch64-linux-gnu.so":
          standard_library.add(path)
      elif relative.parts[0] != "site-packages":
        standard_library.add(python_root / relative.parts[0])
  for path in sorted(standard_library):
    add(path)
    if path.is_dir():
      queue.extend(entry for entry in path.rglob("*") if entry.is_file())
  queue.extend((HEADERS / "scripts/basic/fixdep", HEADERS / "scripts/mod/modpost"))
  seen: set[Path] = set()
  while queue:
    path = queue.pop()
    if path in seen or path.is_dir():
      continue
    seen.add(path)
    with path.open("rb") as stream:
      if stream.read(4) != b"\x7fELF":
        continue
    output = static_command(["/usr/bin/readelf", "-l", "-d", str(path)])
    search = [Path("/usr/lib")]
    for encoded in re.findall(r"\((?:RUNPATH|RPATH)\).*\[([^\]]+)\]", output):
      for element in encoded.split(":"):
        expanded = element.replace("${ORIGIN}", str(path.parent)).replace("$ORIGIN", str(path.parent))
        require("$" not in expanded and expanded.startswith("/usr/"), f"unsupported ELF search path: {path}")
        search.insert(0, Path(expanded))
    for soname in re.findall(r"\(NEEDED\).*\[([^\]]+)\]", output):
      require("/" not in soname, f"unsupported ELF dependency: {path}")
      match = next((folder / soname for folder in search if (folder / soname).exists()), None)
      require(match is not None, f"missing ELF dependency {soname}: {path}")
      if match is not None:
        add(match)
    for interpreter in re.findall(r"Requesting program interpreter: ([^\]]+)\]", output):
      add(Path(interpreter))
  return [Mount(str(source), target, fingerprint(source)) for target, source in sorted(selected.items())]


def write_json(path: Path, payload: object) -> None:
  with path.open("x", encoding="utf-8") as stream:
    json.dump(payload, stream, indent=2, sort_keys=True)
    stream.write("\n")


def read_mounts(path: Path) -> list[Mount]:
  value: object = json.loads(path.read_text(encoding="utf-8"))
  require(isinstance(value, list), "invalid tool manifest")
  mounts: list[Mount] = []
  if isinstance(value, list):
    for record in value:
      require(isinstance(record, dict) and set(record) == {"source", "target", "fingerprint"}, "invalid mount record")
      if isinstance(record, dict):
        source, target, pin = record["source"], record["target"], record["fingerprint"]
        require(isinstance(source, str) and isinstance(target, str) and isinstance(pin, str), "invalid mount field")
        if isinstance(source, str) and isinstance(target, str) and isinstance(pin, str):
          require(Path(source).is_relative_to("/usr") and Path(target).is_relative_to("/usr"), "tool manifest escapes /usr")
          require(".." not in Path(source).parts + Path(target).parts, "tool manifest contains traversal")
          require(Path(source).resolve(strict=True) == Path(source), "tool source changed to symlink")
          require(re.fullmatch(r"[0-9a-f]{64}", pin) is not None, "invalid fingerprint")
          mounts.append(Mount(source, target, pin))
  require(bool(mounts) and len({item.target for item in mounts}) == len(mounts), "empty or duplicate tool manifest")
  return mounts


def verify(mounts: list[Mount], deadline: float) -> None:
  for mount in mounts:
    require(time.monotonic() < deadline, "deadline reached while verifying inputs")
    require(fingerprint(Path(mount.source), private=mount.target.startswith("/inputs/")) == mount.fingerprint, f"input drift: {mount.source}")


def run(mounts: list[Mount], inputs: list[str], command: list[str], deadline: float) -> int:
  require(not Path("/var/lib/pacman/db.lck").exists(), "package transaction is active")
  names = {"proof"}
  proof = BASE / "proof-input.txt"
  mounts.append(Mount(str(proof), "/inputs/proof", fingerprint(proof, private=True)))
  probe = BASE / "isolation_probe.py"
  mounts.append(Mount(str(probe), "/sandbox/isolation_probe.py", fingerprint(probe, private=True)))
  smoke = BASE / "stdlib_smoke_test.py"
  mounts.append(Mount(str(smoke), "/sandbox/stdlib_smoke_test.py", fingerprint(smoke, private=True)))
  for value in inputs:
    name, separator, source = value.partition("=")
    require(separator == "=" and re.fullmatch(r"[a-z][a-z0-9_-]{0,31}", name) is not None, "input must be NAME=ABSOLUTE_PATH")
    require(name not in names, "duplicate or reserved input name")
    names.add(name)
    path = plain_path(Path(source), STAGE)
    require(not BASE.is_relative_to(path), "input contains launcher or output root")
    mounts.append(Mount(str(path), f"/inputs/{name}", fingerprint(path, private=True)))
  verify(mounts, deadline)
  run_root = Path(tempfile.mkdtemp(prefix="run-", dir=BASE))
  work, temporary = run_root / "work", run_root / "tmp"
  work.mkdir(mode=0o700)
  temporary.mkdir(mode=0o700)
  filter_path = run_root / "keyring-deny.bpf"
  with filter_path.open("xb") as stream:
    stream.write(KEYRING_FILTER)
  filter_fd = os.open(filter_path, os.O_RDONLY | os.O_CLOEXEC)
  arguments = [
    "/usr/bin/bwrap", "--unshare-user", "--unshare-ipc", "--unshare-pid",
    "--unshare-net", "--unshare-uts", "--unshare-cgroup", "--uid", "1001",
    "--gid", "1001", "--disable-userns", "--assert-userns-disabled",
    "--cap-drop", "ALL", "--new-session", "--die-with-parent", "--hostname", "d1-offline",
    "--clearenv", "--setenv", "PATH", "/usr/bin:/bin", "--setenv", "LC_ALL", "C",
    "--setenv", "TMPDIR", "/tmp", "--setenv", "PYTHONDONTWRITEBYTECODE", "1",
    "--seccomp", str(filter_fd),
  ]
  for mount in sorted(mounts, key=lambda item: (len(Path(item.target).parts), item.target)):
    arguments.extend(("--ro-bind", mount.source, mount.target))
  arguments.extend((
    "--symlink", "usr/bin", "/bin", "--symlink", "usr/lib", "/lib",
    "--dev-bind", "/dev/null", "/dev/null", "--bind", str(work), "/work",
    "--bind", str(temporary), "/tmp", "--chdir", "/work", "--remount-ro", "/",
    "--", "/usr/bin/python3.14", "-I", "-S", "-B", "/sandbox/isolation_probe.py",
  ))
  arguments.extend(command)
  write_json(run_root / "inputs.json", [asdict(item) for item in mounts])
  write_json(run_root / "command.json", arguments)
  write_json(run_root / "security.json", {
    "seccomp_sha256": hashlib.sha256(KEYRING_FILTER).hexdigest(),
    "audit_arch": "0xc00000b7", "foreign_architecture": "kill_process",
    "denied_syscalls": {"add_key": 217, "request_key": 218, "keyctl": 219},
    "filter_fd_mode": "read_only",
  })
  print(f"Retained run: {run_root}", flush=True)
  # Deliberately mark one private writable descriptor inheritable. The probe
  # must prove that close_fds removed it before any requested command starts.
  sentinel = os.open(work / "descriptor-sentinel", os.O_CREAT | os.O_EXCL | os.O_RDWR, 0o600)
  os.set_inheritable(sentinel, True)
  timed_out = False
  with (work / "stdout.log").open("x") as output, (work / "stderr.log").open("x") as errors:
    process = subprocess.Popen(
      arguments, cwd=BASE, env=ENVIRONMENT, stdin=subprocess.DEVNULL,
      stdout=output, stderr=errors, close_fds=True, pass_fds=(filter_fd,), start_new_session=True,
    )
    os.close(filter_fd)
    os.close(sentinel)
    try:
      result = process.wait(timeout=max(1, deadline - time.monotonic() - 5))
    except subprocess.TimeoutExpired:
      timed_out = True
      os.killpg(process.pid, signal.SIGKILL)
      result = process.wait(timeout=5)
  require(not timed_out, f"sandbox timed out; retained evidence: {run_root}")
  verify(mounts, deadline)
  require(not Path("/var/lib/pacman/db.lck").exists(), "package transaction started during run")
  write_json(run_root / "result.json", {"exit_code": result, "inputs_unchanged": True, "timed_out": False})
  return result


def main() -> int:
  deadline = time.monotonic() + 280
  os.umask(0o077)
  resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
  require(os.getuid() == os.geteuid() == 1001 and os.getgid() == os.getegid() == 1001, "this launcher is only for unprivileged D1 uid/gid 1001")
  plain_path(BASE, STAGE)
  parser = argparse.ArgumentParser(description=__doc__)
  mode = parser.add_mutually_exclusive_group()
  mode.add_argument("--pin", action="store_true")
  mode.add_argument("--probe", action="store_true")
  parser.add_argument("--manifest", type=Path, default=BASE / "toolchain-v4.json")
  parser.add_argument("--input", action="append", default=[])
  parser.add_argument("command", nargs=argparse.REMAINDER)
  options = parser.parse_args()
  manifest = options.manifest
  require(manifest.parent == BASE and not manifest.is_symlink(), "manifest must be a direct private file")
  if options.pin:
    require(not options.input and not options.command, "pin mode accepts no command or inputs")
    require(not manifest.exists(), "manifest already exists; retain it and choose a new name")
    require(not Path("/var/lib/pacman/db.lck").exists(), "package transaction is active")
    mounts = tool_mounts()
    require(time.monotonic() < deadline, "deadline reached while pinning toolchain")
    write_json(manifest, [asdict(item) for item in mounts])
    print(f"Pinned {len(mounts)} read-only tool/runtime mounts: {manifest}")
    return 0
  command = options.command
  if command and command[0] == "--":
    command = command[1:]
  require(not options.probe or not command, "probe mode accepts no command")
  require(options.probe or bool(command), "provide --probe or an explicit sandbox command")
  return run(read_mounts(plain_path(manifest, BASE)), options.input, command, deadline)


if __name__ == "__main__":
  try:
    raise SystemExit(main())
  except (ValueError, OSError, subprocess.SubprocessError) as error:
    print(f"STOP: {error}", file=sys.stderr)
    raise SystemExit(1) from error
