from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Sequence


CONTROL_SHA256 = "c8fffa9a663760cb3c2f66f8d9123c76f01a6a5dfc51744ece1d36af1e54f7c3"
AFK_SHA256 = "d6332afdf58f4af403201b7a6a469e1202f4370972f85a00054ecd563717d649"
COMBINED_SHA256 = "602765912203e0c8860534c52f6447f8f393ba9b4cb2679af6246b82187c52d8"
CONTROL_BUILD_ID = "8bc7a79d757fc70fbfae14ee050fc7c2353387ad"
AFK_BUILD_ID = "1ca52ad1cea00559d5fdfd32177e4d1e694994e1"
COMBINED_BUILD_ID = "4d6d479dd0ffa6c8c418e410208e73ea2ec9abcf"
AFK_CHANGED_OBJECTS = {
  "afk.o",
  "appledrm.o",
  "audio.o",
  "av.o",
  "dcp.o",
  "dcp_backlight.o",
  "dptxep.o",
  "ibootep.o",
  "iomfb.o",
  "iomfb_v12_3.o",
  "iomfb_v13_3.o",
  "parser.o",
  "systemep.o",
  "trace.o",
}
TIMEOUT_CHANGED_OBJECTS = {"appledrm.o", "iomfb_v12_3.o", "iomfb_v13_3.o"}


class ContractError(RuntimeError):
  pass


def require(condition: bool, message: str) -> None:
  if not condition:
    raise ContractError(message)


def sha256(path: Path) -> str:
  return hashlib.sha256(path.read_bytes()).hexdigest()


def module(build: Path) -> Path:
  return build / "apple/appledrm.ko"


def inspection(build: Path, name: str) -> Path:
  return build / "inspection" / name


def object_hashes(build: Path) -> dict[str, str]:
  return {path.name: sha256(path) for path in (build / "apple").glob("*.o")}


def changed_objects(left: Path, right: Path) -> set[str]:
  left_hashes = object_hashes(left)
  right_hashes = object_hashes(right)
  require(left_hashes.keys() == right_hashes.keys(), "object inventory changed")
  return {name for name in left_hashes if left_hashes[name] != right_hashes[name]}


def build_id(path: Path) -> str:
  result = subprocess.run(
    ("/usr/bin/readelf", "-n", str(path)),
    check=False,
    capture_output=True,
    text=True,
    timeout=20,
  )
  require(result.returncode == 0, f"readelf failed: {path}")
  matches = re.findall(r"Build ID: ([0-9a-f]+)", result.stdout)
  require(len(matches) == 1, f"build ID count changed: {path}")
  return matches[0]


def result_passed(build: Path) -> bool:
  result = json.loads((build / "result.json").read_text(encoding="utf-8"))
  return result == {"exit_code": 0, "inputs_unchanged": True, "timed_out": False}


def main(arguments: Sequence[str]) -> int:
  try:
    require(len(arguments) == 1, "usage: test_build_contract.py ARTIFACT_ROOT")
    root = Path(arguments[0]).resolve()
    control = root / "control-build"
    afk = root / "accepted-afk-build"
    combined = root / "combined-build"
    for build in (control, afk, combined):
      require(result_passed(build), f"sandbox result failed: {build.name}")
      require(inspection(build, "build.stderr").stat().st_size == 0, f"build stderr is not empty: {build.name}")

    require(sha256(module(control)) == CONTROL_SHA256, "control module identity mismatch")
    require(sha256(module(afk)) == AFK_SHA256, "accepted AFK module identity mismatch")
    require(sha256(module(combined)) == COMBINED_SHA256, "combined module identity mismatch")
    require(build_id(module(control)) == CONTROL_BUILD_ID, "control build ID mismatch")
    require(build_id(module(afk)) == AFK_BUILD_ID, "accepted AFK build ID mismatch")
    require(build_id(module(combined)) == COMBINED_BUILD_ID, "combined build ID mismatch")

    for name in ("modinfo.txt", "exports.txt", "apple_dcp-dwarf.txt", "apple_dcp-btf.txt"):
      reference = inspection(control, name).read_bytes()
      require(inspection(afk, name).read_bytes() == reference, f"AFK changed {name}")
      require(inspection(combined, name).read_bytes() == reference, f"combined changed {name}")
    require(inspection(control, "exports.txt").stat().st_size == 0, "module export set is not empty")

    control_imports = set(inspection(control, "imports.txt").read_text(encoding="utf-8").splitlines())
    afk_imports = set(inspection(afk, "imports.txt").read_text(encoding="utf-8").splitlines())
    combined_imports = set(inspection(combined, "imports.txt").read_text(encoding="utf-8").splitlines())
    require(afk_imports == combined_imports, "timeout change altered module imports")
    require(
      afk_imports - control_imports == {"                 U _raw_spin_lock", "                 U _raw_spin_unlock"},
      "AFK import additions changed",
    )
    require(not control_imports - afk_imports, "AFK removed a module import")

    require(changed_objects(control, afk) == AFK_CHANGED_OBJECTS, "AFK object delta changed")
    require(changed_objects(afk, combined) == TIMEOUT_CHANGED_OBJECTS, "timeout object delta escaped expected objects")
    require(changed_objects(control, combined) == AFK_CHANGED_OBJECTS, "combined object delta escaped AFK object set")

    sections = inspection(combined, "elf-sections.txt").read_text(encoding="utf-8")
    for name in (".BTF", ".BTF.base", ".debug_info", ".note.gnu.build-id"):
      require(name in sections, f"combined module section missing: {name}")

    print("PASS: module identities, metadata, ABI, layouts, and object deltas match the contract")
    return 0
  except (ContractError, OSError, ValueError, subprocess.SubprocessError) as error:
    print(f"ERROR: {error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
  raise SystemExit(main(sys.argv[1:]))
