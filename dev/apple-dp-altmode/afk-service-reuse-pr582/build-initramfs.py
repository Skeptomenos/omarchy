from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import zlib


KERNEL = "7.1.6-1-1-ARCH"
BASE_SHA256 = "ebd383c21a35d6b0eff22ffe6f144ea7790c31d7cf058a1c3afa5e39c2375acd"
BASE_BYTES = 21598988
EARLY_BYTES = 10240
EARLY_SHA256 = "e7798a1bd4c75ff8b8bdcdf2a0a315f1322a59082f22375d6526094deb3bb4aa"
MAIN_BYTES = 69556136
MAIN_SHA256 = "dbeb47798d44c5eb337b9d0e236ebda3b6682aa6c36b44959f64016e67d158e8"
BASE_MODULE_SHA256 = "d6332afdf58f4af403201b7a6a469e1202f4370972f85a00054ecd563717d649"
CANDIDATE_SHA256 = "602765912203e0c8860534c52f6447f8f393ba9b4cb2679af6246b82187c52d8"
CANDIDATE_BYTES = 8766768
CANDIDATE_BUILD_ID = "4d6d479dd0ffa6c8c418e410208e73ea2ec9abcf"
HELPER_SHA256 = "a32eddd159263d19ff87d7e9caee9d53d17ef5c350fbffe9e7eb142cb43ebf58"
TARGET = f"usr/lib/modules/{KERNEL}/kernel/drivers/gpu/drm/apple/appledrm.ko"
OUTPUT = Path("/work/initramfs-linux-asahi-m2-displayport-afk-pr582.img")


class ImageError(RuntimeError):
  pass


def require(condition: bool, message: str) -> None:
  if not condition:
    raise ImageError(message)


def sha256(payload: bytes) -> str:
  return hashlib.sha256(payload).hexdigest()


def read_input(path: Path, expected_sha256: str, expected_bytes: int | None = None) -> bytes:
  payload = path.read_bytes()
  require(sha256(payload) == expected_sha256, f"input identity mismatch: {path.name}")
  require(expected_bytes is None or len(payload) == expected_bytes, f"input size mismatch: {path.name}")
  return payload


def load_helper() -> object:
  path = Path("/inputs/helper/cpio_image.py")
  read_input(path, HELPER_SHA256)
  specification = importlib.util.spec_from_file_location("dev147_cpio_image", path)
  require(specification is not None and specification.loader is not None, "helper load specification failed")
  module = importlib.util.module_from_spec(specification)
  sys.modules[specification.name] = module
  specification.loader.exec_module(module)
  return module


def run(arguments: tuple[str, ...], payload: bytes | None = None) -> bytes:
  result = subprocess.run(
    arguments,
    input=payload,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"},
    close_fds=True,
    check=False,
    timeout=90,
  )
  require(result.returncode == 0 and not result.stderr, f"command failed: {arguments[0]}")
  require(len(result.stdout) <= 128 * 1024 * 1024, f"command output exceeded bound: {arguments[0]}")
  return result.stdout


def metadata(path: Path, field: str) -> bytes:
  return run(("/usr/bin/modinfo", "-F", field, str(path)))


def main() -> None:
  require(
    os.getuid() == os.geteuid() == os.getgid() == os.getegid() == 1001
    and Path.cwd() == Path("/work")
    and not any(Path(path).exists() for path in ("/proc", "/sys", "/boot", "/home", "/run")),
    "reviewed offline sandbox required",
  )
  helper = load_helper()
  base = read_input(Path("/inputs/base"), BASE_SHA256, BASE_BYTES)
  candidate_path = Path("/inputs/moduledir/appledrm.ko")
  candidate = read_input(candidate_path, CANDIDATE_SHA256, CANDIDATE_BYTES)
  early_raw = base[:EARLY_BYTES]
  compressed_raw = base[EARLY_BYTES:]
  require(sha256(early_raw) == EARLY_SHA256, "early archive identity mismatch")
  require(compressed_raw[:10] == bytes.fromhex("1f8b0800000000000003"), "main gzip header mismatch")
  main_raw = zlib.decompress(compressed_raw, wbits=31)
  require(len(main_raw) == MAIN_BYTES and sha256(main_raw) == MAIN_SHA256, "main archive identity mismatch")
  early = helper.parse_newc(early_raw)
  original = helper.parse_newc(main_raw)
  require(len(early.members) == 7 and len(original.members) == 1162, "archive member count mismatch")
  matches = tuple(member for member in original.members if member.name == TARGET)
  require(len(matches) == 1 and sha256(matches[0].payload) == BASE_MODULE_SHA256, "base AppleDRM identity mismatch")
  transformed_raw = helper.replace_members(original, {TARGET: candidate}, ())
  transformed = helper.parse_newc(transformed_raw)
  require(len(transformed.members) == len(original.members), "transformed member count mismatch")
  changed = tuple(
    before.name
    for before, after in zip(original.members, transformed.members, strict=True)
    if before.raw != after.raw
  )
  require(changed == (TARGET,), "archive change escaped AppleDRM target")
  require(
    next(member.payload for member in transformed.members if member.name == TARGET) == candidate,
    "candidate AppleDRM payload mismatch",
  )
  base_module_path = Path("/work/base-appledrm.ko")
  helper.write_new(base_module_path, matches[0].payload)
  for field in ("name", "vermagic", "depends", "alias"):
    require(metadata(candidate_path, field) == metadata(base_module_path, field), f"module metadata mismatch: {field}")
  note = run(("/usr/bin/readelf", "-n", str(candidate_path)))
  require(
    re.findall(rb"Build ID: ([0-9a-f]+)\n", note) == [CANDIDATE_BUILD_ID.encode()],
    "candidate build ID mismatch",
  )
  compressed = run(("/usr/bin/gzip", "-n"), transformed_raw)
  require(compressed[:10] == bytes.fromhex("1f8b0800000000000003"), "candidate gzip header mismatch")
  require(zlib.decompress(compressed, wbits=31) == transformed_raw, "candidate gzip readback mismatch")
  image = early_raw + compressed
  helper.write_new(OUTPUT, image)
  published = helper.read_regular(OUTPUT, sha256(image))
  require(published[:EARLY_BYTES] == early.raw, "published early archive mismatch")
  published_main = zlib.decompress(published[EARLY_BYTES:], wbits=31)
  published_archive = helper.parse_newc(published_main)
  published_changed = tuple(
    before.name
    for before, after in zip(original.members, published_archive.members, strict=True)
    if before.raw != after.raw
  )
  require(published_changed == (TARGET,), "published image change escaped AppleDRM target")
  receipt = {
    "base_bytes": len(base),
    "base_sha256": sha256(base),
    "candidate_module_build_id": CANDIDATE_BUILD_ID,
    "candidate_module_bytes": len(candidate),
    "candidate_module_sha256": sha256(candidate),
    "changed_member": TARGET,
    "image_bytes": len(published),
    "image_sha256": sha256(published),
    "main_members": len(published_archive.members),
    "offline": True,
    "schema": "dev147-afk-pr582-image-v1",
    "staged": False,
    "status": "PASS",
  }
  helper.write_new(
    Path("/work/afk-pr582-image-result.json"),
    (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode(),
  )
  print("PASS: AppleDRM-only AFK plus PR582 image built offline; nothing staged or loaded")


if __name__ == "__main__":
  try:
    main()
  except (ImageError, OSError, ValueError, RuntimeError, subprocess.SubprocessError, zlib.error):
    print("INCOMPLETE: retain outputs for review; nothing staged or loaded", file=sys.stderr)
    raise SystemExit(1) from None
