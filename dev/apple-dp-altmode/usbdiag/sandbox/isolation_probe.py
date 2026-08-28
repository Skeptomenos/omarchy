#!/usr/bin/python3
"""Trusted D1 isolation checks. This is not a kernel or hardware test."""

import ctypes
import errno
import fcntl
import json
import os
from pathlib import Path
import resource
import socket
import stat
import subprocess
import sys


CLONE_NEWUSER = 0x10000000
CLONE_NEWNS = 0x00020000


class CapHeader(ctypes.Structure):
  _fields_ = [("version", ctypes.c_uint32), ("pid", ctypes.c_int)]


class CapData(ctypes.Structure):
  _fields_ = [
    ("effective", ctypes.c_uint32),
    ("permitted", ctypes.c_uint32),
    ("inheritable", ctypes.c_uint32),
  ]


def require(condition: bool, reason: str) -> None:
  if not condition:
    raise RuntimeError(reason)


def namespace_denied(flag: int, return_value: int, error_number: int) -> bool:
  if return_value != -1:
    return False
  # Bubblewrap's user-namespace count limit can deny creation with ENOSPC.
  if flag == CLONE_NEWUSER:
    return error_number in (errno.EPERM, errno.ENOSPC)
  if flag == CLONE_NEWNS:
    return error_number == errno.EPERM
  return False


def main() -> None:
  require(os.getuid() == os.geteuid() == 1001, "unexpected or elevated UID")
  require(os.getgid() == os.getegid() == 1001, "unexpected or elevated GID")
  require(Path.cwd() == Path("/work"), "unexpected working directory")
  require(resource.getrlimit(resource.RLIMIT_CORE) == (0, 0), "core dumps are not disabled")
  allowed_environment = {"PATH", "LC_ALL", "TMPDIR", "PWD", "PYTHONDONTWRITEBYTECODE"}
  require(set(os.environ) <= allowed_environment, "unexpected inherited environment")
  for name in ("/home", "/root", "/run", "/sys", "/proc", "/boot", "/etc", "/usr/lib/modules"):
    require(not Path(name).exists(), f"forbidden path visible: {name}")
  require(list(Path("/dev").iterdir()) == [Path("/dev/null")], "unexpected device nodes")
  require(not any(os.isatty(fd) for fd in (0, 1, 2)), "inherited terminal")
  null_stat = Path("/dev/null").stat()
  require(stat.S_ISCHR(null_stat.st_mode), "null is not a pseudo-device")
  require(os.fstat(0).st_rdev == null_stat.st_rdev, "stdin is not null")
  for fd, name in ((1, "stdout.log"), (2, "stderr.log")):
    actual = os.fstat(fd)
    expected = Path("/work", name).stat()
    require(stat.S_ISREG(actual.st_mode), "output is not a private regular file")
    require((actual.st_dev, actual.st_ino) == (expected.st_dev, expected.st_ino), "output escaped work")
    require(actual.st_nlink == 1, "output has a hardlink")
  limit = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
  require(0 < limit <= 1048576, "unexpected descriptor bound")
  for fd in range(3, limit):
    try:
      fcntl.fcntl(fd, fcntl.F_GETFD)
    except OSError as error:
      require(error.errno == errno.EBADF, "descriptor scan failed")
    else:
      raise RuntimeError(f"inherited descriptor: {fd}")

  libc = ctypes.CDLL("libc.so.6", use_errno=True)
  libc.prctl.restype = ctypes.c_int
  require(libc.prctl(39, 0, 0, 0, 0) == 1, "no_new_privs is not set")
  require(libc.prctl(21, 0, 0, 0, 0) == 2, "seccomp filtering is not active")
  # Invalid arguments cannot enumerate/read keys if a filter is missing.
  # The reviewed filter must return EPERM before argument interpretation.
  libc.syscall.restype = ctypes.c_long
  for number in (217, 218, 219):
    ctypes.set_errno(0)
    result = libc.syscall(ctypes.c_long(number), ctypes.c_long(-1), 0, 0, 0, 0)
    require(result == -1 and ctypes.get_errno() == errno.EPERM, "keyring syscall is not denied")
  header = CapHeader(0x20080522, 0)
  data = (CapData * 2)()
  require(libc.capget(ctypes.byref(header), ctypes.byref(data)) == 0, "capget failed")
  require(all(item.effective == item.permitted == item.inheritable == 0 for item in data), "capabilities remain")
  for capability in range(64):
    value = libc.prctl(23, capability, 0, 0, 0)
    if value == -1 and ctypes.get_errno() == errno.EINVAL:
      break
    require(value == 0, "capability bounding set is not empty")
  libc.unshare.argtypes = [ctypes.c_int]
  libc.unshare.restype = ctypes.c_int
  for namespace in (CLONE_NEWUSER, CLONE_NEWNS):
    ctypes.set_errno(0)
    unshare_result = libc.unshare(namespace)
    unshare_errno = ctypes.get_errno()
    print(json.dumps({
      "level": "info", "check": "namespace_denial", "namespace_flag": namespace,
      "return_value": unshare_result, "errno": unshare_errno,
    }, sort_keys=True), flush=True)
    require(namespace_denied(namespace, unshare_result, unshare_errno), "namespace denial was not verified")

  # UDP connect performs a route lookup; no packet is sent.
  for family, address in ((socket.AF_INET, ("192.0.2.1", 9)), (socket.AF_INET6, ("2001:db8::1", 9))):
    try:
      with socket.socket(family, socket.SOCK_DGRAM) as connection:
        connection.connect(address)
    except OSError as error:
      require(error.errno in (errno.ENETUNREACH, errno.EAFNOSUPPORT), "unexpected route result")
    else:
      raise RuntimeError("a network route remains")

  for name in ("/work/probe-write", "/tmp/probe-write"):
    with Path(name).open("x") as stream:
      stream.write("private sandbox write\n")
  for name in ("/outside-work", "/usr/outside-work"):
    try:
      descriptor = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except OSError as error:
      require(error.errno == errno.EROFS, "root was not read-only")
    else:
      os.close(descriptor)
      raise RuntimeError("write outside private directories succeeded")
  try:
    descriptor = os.open("/inputs/proof", os.O_WRONLY)
  except OSError as error:
    require(error.errno == errno.EROFS, "input was not read-only")
  else:
    os.close(descriptor)
    raise RuntimeError("input opened for writing")

  versions: dict[str, str] = {}
  for tool in ("gcc", "make", "ld", "perl", "jq", "bsdtar", "gzip", "cpio", "depmod", "gpgv"):
    result = subprocess.run(
      [f"/usr/bin/{tool}", "--version"], check=True, text=True,
      stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
      close_fds=True, timeout=15,
    )
    versions[tool] = next(line for line in result.stdout.splitlines() if line.strip())
  require("16.1.1" in versions["gcc"], "unexpected GCC version")
  require("4.4.1" in versions["make"], "unexpected Make version")
  smoke = subprocess.run(
    ["/usr/bin/python3.14", "-I", "-S", "-B", "-m", "unittest", "discover", "-s", "/sandbox", "-p", "stdlib_smoke_test.py"],
    check=True, text=True, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT, close_fds=True, timeout=15,
  )
  require("Ran 7 tests" in smoke.stdout and "OK" in smoke.stdout, "stdlib and namespace tests did not run")
  print(json.dumps({
    "verdict": "PASS", "uid": os.getuid(), "gid": os.getgid(),
    "descriptor_scan_upper_bound": limit, "inherited_fds": [0, 1, 2],
    "no_new_privs": True, "capabilities": "empty", "bounding_set": "empty", "core_limit": 0,
    "seccomp": "filter mode", "keyring_syscalls": "EPERM; invalid arguments only",
    "nested_user_and_mount_namespaces": "denied", "ipv4_ipv6_routes": "absent",
    "proc_sys_run_home_boot": "absent", "device_nodes": ["/dev/null"],
    "writable_storage": ["/work", "/tmp"], "input_write_open": "EROFS",
    "versions": versions, "unittest_lazy_import_smoke": "PASS: 7 tests",
  }, sort_keys=True), flush=True)
  if len(sys.argv) > 1:
    require(Path(sys.argv[1]).is_absolute(), "sandbox command must use an absolute path")
    os.execv(sys.argv[1], sys.argv[1:])


if __name__ == "__main__":
  main()
