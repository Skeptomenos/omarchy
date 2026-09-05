from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

RELEASE = "7.1.12-dev147-fairydust1"
RUNNING_KERNEL = "7.1.6-1-1-ARCH"
ROOT = Path("/home/david/Work/dev147-fairydust-boot-20260905")
DELIVERY = ROOT / "delivery"
MANUAL = ROOT / "stage/manual-results"
BOOT = Path(f"/boot/dev147-fairydust-{RELEASE}")
MODULES = Path(f"/usr/lib/modules/{RELEASE}")
PROTECTED_STATE = Path(f"/var/lib/dev147-fairydust-stage/{RELEASE}")
MANIFEST_HASH = "f33054856e60d3baf5cb7630cb8d7dfc60ffa586e16456c3e7313fffe6f7c59d"
HELPER_HASH = "12501982dfd4adb347103671ce5dbf9650b53b628474a434de3c458fd98ad6a7"
LAUNCHER_HASH = "748810653d9f083113052afc0b19acc1e0b1d73ec99b4165906a46a83e856c15"
ACTIVATION = "not performed; paired m1n1 and GRUB activation requires separate review"
CONFIGURATION_PATHS = frozenset(
  (
    "/boot/grub/grub.cfg",
    "/boot/grub/grubenv",
    "/boot/grub/custom.cfg",
    "/etc/default/grub",
    "/etc/grub.d/custom.cfg",
    "/etc/grub.d/40_custom",
    "/etc/grub.d/41_custom",
  )
)
ACTIVE_PINS = {
  "/boot/efi/m1n1/boot.bin": "203ab7027536c8d16f373d02c1f6346a5c34cfe095a9dafd0cfe37d2b354090c",
  "/etc/pacman.d/hooks/05-omarchy-m2-displayport-guard.hook": "469820ad7cfd015a22cff979b0aa70d62e82dcc7cc05951dca92f40cd660f2bd",
  "/boot/efi/vendorfw/firmware.cpio": "7c2ce145ec9bb390c2377e6e83d1aacc3817dd227909b0e62b0febe96d2f451f",
  "/usr/lib/firmware/vendor/.vendorfw.manifest": "2f3ab6e0d7d2fb8ab11746094c1d02a3ef00da9a8037bfdac583eb4b8d31cea1",
}


class VerificationFailure(Exception):
  pass


@dataclass(frozen=True)
class StageExport:
  status: str
  protected_identities: dict[str, str]
  boot_configuration: dict[str, str]


def require(condition: bool, message: str) -> None:
  if not condition:
    raise VerificationFailure(message)


def no_symlink_components(path: Path) -> None:
  require(path.is_absolute(), "path must be absolute")
  for component in reversed((path, *path.parents)):
    require(not stat.S_ISLNK(component.lstat().st_mode), f"symlink path: {component}")


def check_path(path: Path, owner: int, private: bool = False) -> os.stat_result:
  no_symlink_components(path)
  info = path.lstat()
  require(info.st_uid == owner, f"wrong owner: {path}")
  require(
    not (info.st_mode & (0o077 if private else 0o022)), f"unsafe permissions: {path}"
  )
  require(
    stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode), f"special file: {path}"
  )
  if stat.S_ISREG(info.st_mode):
    require(info.st_nlink == 1, f"hardlinked file: {path}")
  return info


def read_file(path: Path, owner: int, private: bool = False) -> bytes:
  before = check_path(path, owner, private)
  require(stat.S_ISREG(before.st_mode), f"not a regular file: {path}")
  descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
  with os.fdopen(descriptor, "rb") as stream:
    require(os.fstat(stream.fileno()) == before, f"file changed before read: {path}")
    content = stream.read()
    after = os.fstat(stream.fileno())
    require(
      (after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
      == (before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns),
      f"file changed during read: {path}",
    )
    return content


def file_hash(path: Path, owner: int) -> str:
  before = check_path(path, owner)
  require(stat.S_ISREG(before.st_mode), f"not a regular file: {path}")
  descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
  with os.fdopen(descriptor, "rb") as stream:
    require(os.fstat(stream.fileno()) == before, f"file changed before hash: {path}")
    digest = hashlib.file_digest(stream, "sha256").hexdigest()
    after = os.fstat(stream.fileno())
    require(
      (after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
      == (before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns),
      f"file changed during hash: {path}",
    )
    return digest


def string_map(value: object) -> dict[str, str]:
  require(isinstance(value, dict), "expected a string map")
  if not isinstance(value, dict):
    raise VerificationFailure("invalid map")
  require(
    all(isinstance(key, str) and isinstance(item, str) for key, item in value.items()),
    "non-string map entry",
  )
  return {str(key): str(item) for key, item in value.items()}


def configuration_hash(identity: str) -> str:
  match = re.fullmatch(r"[0-7]+:0:0:file:([0-9a-f]{64})", identity)
  require(match is not None, "configuration lacks a root-owned file identity")
  if match is None:
    raise VerificationFailure("invalid configuration identity")
  return match.group(1)


def verify_manual(directory: Path) -> StageExport:
  owner = os.getuid()
  check_path(directory, owner, True)
  require(
    read_file(directory / "exit-status", owner, True) == b"0\n",
    "manual stage did not exit zero",
  )
  require(
    read_file(directory / "stderr.log", owner, True) == b"",
    "manual stage emitted diagnostics",
  )
  expected = f"helper_sha256={HELPER_HASH}\nmanifest_sha256={MANIFEST_HASH}\n".encode()
  require(
    read_file(directory / "input-identities", owner, True) == expected,
    "manual input identities differ",
  )
  value: object = json.loads(read_file(directory / "result.json", owner, True))
  require(isinstance(value, dict), "invalid stage report")
  if not isinstance(value, dict):
    raise VerificationFailure("invalid report")
  constants = {
    "status": "STAGED_UNSELECTED",
    "release": RELEASE,
    "manifest_sha256": MANIFEST_HASH,
    "boot_directory": str(BOOT),
    "module_directory": str(MODULES),
    "protected_state": str(PROTECTED_STATE),
    "activation": ACTIVATION,
  }
  require(
    set(value) == set(constants) | {"protected_identities", "boot_configuration"},
    "unexpected stage report fields",
  )
  require(
    all(value.get(key) == expected for key, expected in constants.items()),
    "stage report identity or status differs",
  )
  identities = string_map(value["protected_identities"])
  configuration = string_map(value["boot_configuration"])
  require(
    "/boot/grub/grub.cfg" in configuration
    and set(configuration) <= CONFIGURATION_PATHS,
    "missing or unexpected boot configuration",
  )
  for path, text in configuration.items():
    require(path in identities, "configuration identity missing")
    require(
      hashlib.sha256(text.encode()).hexdigest() == configuration_hash(identities[path]),
      f"saved configuration hash mismatch: {path}",
    )
  return StageExport("STAGED_UNSELECTED", identities, configuration)


def parse_manifest(content: bytes) -> dict[str, str]:
  manifest: dict[str, str] = {}
  for line in content.decode("ascii").splitlines():
    match = re.fullmatch(r"([0-9a-f]{64})  ([A-Za-z0-9_.+/-]+)", line)
    require(match is not None, "invalid manifest line")
    if match is None:
      raise VerificationFailure("invalid manifest")
    digest, name = match.groups()
    require(
      not name.startswith("/")
      and all(part not in ("", ".", "..") for part in name.split("/")),
      "unsafe manifest path",
    )
    require(name not in manifest, "duplicate manifest entry")
    manifest[name] = digest
  require(bool(manifest), "empty manifest")
  return manifest


def verify_tree(root: Path, expected: dict[str, str], owner: int = 0) -> None:
  require(
    stat.S_ISDIR(check_path(root, owner).st_mode), "published root is not a directory"
  )
  actual: set[str] = set()
  for path in root.rglob("*"):
    info = check_path(path, owner)
    if stat.S_ISREG(info.st_mode):
      actual.add(path.relative_to(root).as_posix())
  require(actual == set(expected), f"published inventory mismatch: {root}")
  for name, digest in expected.items():
    require(file_hash(root / name, owner) == digest, f"published hash mismatch: {name}")


def main() -> int:
  try:
    require(len(sys.argv) == 1, "this verifier takes no arguments")
    owner = os.getuid()
    report = verify_manual(MANUAL)
    source = Path(__file__).parent
    require(
      file_hash(source / "stage.py", owner) == HELPER_HASH, "frozen helper changed"
    )
    require(
      file_hash(source / "launch.sh", owner) == LAUNCHER_HASH, "frozen launcher changed"
    )
    content = read_file(DELIVERY / "SHA256SUMS", owner)
    require(
      hashlib.sha256(content).hexdigest() == MANIFEST_HASH,
      "frozen delivery manifest changed",
    )
    manifest = parse_manifest(content)
    module_prefix = f"root/lib/modules/{RELEASE}/"
    boot_expected = {
      name: digest for name, digest in manifest.items() if not name.startswith("root/")
    }
    boot_expected["SHA256SUMS"] = MANIFEST_HASH
    modules_expected = {
      str(PurePosixPath(name).relative_to(module_prefix)): digest
      for name, digest in manifest.items()
      if name.startswith(module_prefix)
    }
    require(
      len(modules_expected) + len(boot_expected) == len(manifest) + 1,
      "unexpected manifest root",
    )
    require(
      sum(name.endswith(".ko") for name in modules_expected) == 1862,
      "module count differs",
    )
    verify_tree(BOOT, boot_expected)
    verify_tree(MODULES, modules_expected)
    for path, expected in ACTIVE_PINS.items():
      require(file_hash(Path(path), 0) == expected, f"active input drift: {path}")
    require(os.uname().release == RUNNING_KERNEL, "running kernel changed")
    current_configuration: dict[str, str] = {}
    unavailable: list[str] = []
    for name in report.boot_configuration:
      try:
        actual = file_hash(Path(name), 0)
      except PermissionError:
        unavailable.append(name)
        continue
      require(
        actual == configuration_hash(report.protected_identities[name]),
        f"current boot configuration differs: {name}",
      )
      current_configuration[name] = actual
    os.umask(0o077)
    output = Path(tempfile.mkdtemp(prefix="staged-verification.", dir=ROOT / "stage"))
    receipt = {
      "verdict": "PASS",
      "timestamp_utc": datetime.now(timezone.utc).isoformat(),
      "scope": "Published stage verified; candidate remains unselected. This does not prove activation, boot or hardware behavior.",
      "release": RELEASE,
      "running_kernel": os.uname().release,
      "helper_sha256": HELPER_HASH,
      "launcher_sha256": LAUNCHER_HASH,
      "manifest_sha256": MANIFEST_HASH,
      "published_boot_files": len(boot_expected),
      "published_module_tree_files": len(modules_expected),
      "modules": 1862,
      "root_owned_regular_inventory": True,
      "manual_exit": 0,
      "manual_stderr_bytes": 0,
      "saved_configuration_hashes": {
        name: configuration_hash(report.protected_identities[name])
        for name in report.boot_configuration
      },
      "current_readable_configuration_hashes": current_configuration,
      "current_configuration_not_readable_without_root": unavailable,
      "active_input_hashes": ACTIVE_PINS,
      "protected_identity_count": len(report.protected_identities),
      "manual_evidence_hashes": {
        name: file_hash(MANUAL / name, owner)
        for name in ("result.json", "input-identities", "exit-status", "stderr.log")
      },
      "limitations": [
        "Root-private snapshots were not reread; saved configuration strings were checked against exported protected identities.",
        "Root GRUB configuration may remain unreadable directly; its captured hash consistency does not replace the later paired-activation review.",
        "No sudo, active boot changes, firmware writes, or system-path writes occurred.",
      ],
    }
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(
      "PASS: published unselected stage; 1862 modules; manual result and active pins verified"
    )
    print(f"Private receipt: {output / 'receipt.json'}")
    return 0
  except (OSError, VerificationFailure, UnicodeError, json.JSONDecodeError) as error:
    print(f"FAIL: {error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
  sys.exit(main())
