"""Fixed private source preparation and ELF evidence; no live-machine entry."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import struct
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

COMMIT = "e2e1930a9595bffafad92cec2b5504525efb9cd4"
PATCH_SHA256 = "58413a7a58c2084f87ecded07f959dc7acec871633fbc23d8e3630367c662b6b"
HUNK = b"@@ -930,7 +930,24 @@ void DCP_FW_NAME(iomfb_poweroff)(struct apple_dcp *dcp)\n"


@dataclass(frozen=True)
class SourceFile:
  path: str
  git_blob: str
  size: int
  sha256: str


def source_file(value: object) -> SourceFile:
  if not isinstance(value, dict) or set(value) != {"path", "git_blob", "bytes", "sha256", "origin"}:
    raise ValueError("unexpected source record")
  path, git_blob, size, digest = value["path"], value["git_blob"], value["bytes"], value["sha256"]
  if not isinstance(path, str) or not isinstance(git_blob, str) or not isinstance(digest, str) or type(size) is not int:
    raise ValueError("invalid source field type")
  if not 0 < size <= 100000 or re.fullmatch(r"[0-9a-f]{40}", git_blob) is None or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
    raise ValueError("invalid source size or hash")
  relative = PurePosixPath(path)
  if relative.is_absolute() or ".." in relative.parts or str(relative) != path:
    raise ValueError("unsafe source path")
  return SourceFile(path, git_blob, size, digest)


def save_json(path: Path, value: object) -> None:
  with path.open("x", encoding="utf-8") as output:
    json.dump(value, output, sort_keys=True, indent=2)
    output.write("\n")


def prepare(mode: str) -> None:
  payload: object = json.loads(Path("/inputs/source-manifest").read_text(encoding="utf-8"))
  if not isinstance(payload, dict) or set(payload) != {"schema", "commit", "files"} or payload["schema"] != "dev147-pr582-source-v1" or payload["commit"] != COMMIT or not isinstance(payload["files"], list):
    raise ValueError("unexpected source manifest")
  entries = tuple(source_file(value) for value in payload["files"])
  names = {entry.path for entry in entries}
  if len(entries) != 40 or len(names) != 40 or sum(entry.size for entry in entries) != 330384:
    raise ValueError("source inventory count or size mismatch")
  source = Path("/inputs/source")
  members = tuple(source.rglob("*"))
  if any(item.is_symlink() or not (item.is_file() or item.is_dir()) for item in members):
    raise ValueError("source tree contains a link or special file")
  if {str(item.relative_to(source)) for item in members if item.is_file()} != names or {str(item.relative_to(source)) for item in members if item.is_dir()} != {"epic"}:
    raise ValueError("source tree has missing or extra members")
  destination = Path("/work/apple")
  destination.mkdir(mode=0o700)
  (destination / "epic").mkdir(mode=0o700)
  for entry in entries:
    with (source / entry.path).open("rb") as input_file:
      raw = input_file.read(entry.size + 1)
    if len(raw) != entry.size or hashlib.sha256(raw).hexdigest() != entry.sha256 or hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest() != entry.git_blob:
      raise ValueError("source bytes do not match pinned manifest")
    with (destination / entry.path).open("xb") as output:
      output.write(raw)
  patch = Path("/inputs/upstream-patch").read_bytes()
  if hashlib.sha256(patch).hexdigest() != PATCH_SHA256 or patch.count(HUNK) != 1:
    raise ValueError("upstream patch mismatch")
  hunk = patch.split(HUNK, 1)[1].splitlines(keepends=True)
  if any(line[:1] not in (b" ", b"+", b"-") for line in hunk):
    raise ValueError("unexpected patch suffix")
  before = b"".join(line[1:] for line in hunk if line[:1] in (b" ", b"-"))
  after = b"".join(line[1:] for line in hunk if line[:1] in (b" ", b"+"))
  template = destination / "iomfb_template.c"
  original = template.read_bytes()
  if len(before.splitlines()) != 7 or len(after.splitlines()) != 24 or original.count(before) != 1:
    raise ValueError("exact single hunk does not apply")
  result = original if mode == "baseline" else original.replace(before, after, 1)
  if mode == "patched":
    template.write_bytes(result)
  save_json(Path("/work/preparation.json"), {"mode": mode, "commit": COMMIT, "files": len(entries), "upstream_patch_sha256": PATCH_SHA256, "template_before_sha256": hashlib.sha256(original).hexdigest(), "template_after_sha256": hashlib.sha256(result).hexdigest(), "changed_source_paths": [] if mode == "baseline" else ["iomfb_template.c"]})


def elf_sections(path: Path) -> dict[str, object]:
  raw = path.read_bytes()
  if len(raw) < 64 or raw[:6] != b"\x7fELF\x02\x01":
    raise ValueError("expected little-endian ELF64")
  header = struct.unpack_from("<16sHHIQQQIHHHHHH", raw)
  offset, entry_size, count, strings_index = header[6], header[11], header[12], header[13]
  if header[1:3] != (1, 183) or entry_size != 64 or not 0 < count <= 4096 or not 0 < strings_index < count or offset + count * entry_size > len(raw):
    raise ValueError("unexpected ARM64 relocatable ELF section table")
  entries = tuple(struct.unpack_from("<IIQQQQIIQQ", raw, offset + index * entry_size) for index in range(count))
  string_header = entries[strings_index]
  if string_header[4] + string_header[5] > len(raw):
    raise ValueError("section string table out of bounds")
  names = raw[string_header[4]:string_header[4] + string_header[5]]
  result: list[dict[str, object]] = []
  for index, section in enumerate(entries):
    name_offset, kind, flags, _, start, size, _, _, _, _ = section
    if name_offset >= len(names) or b"\0" not in names[name_offset:]:
      raise ValueError("section name out of bounds")
    name = names[name_offset:].split(b"\0", 1)[0].decode("ascii")
    if kind != 8 and start + size > len(raw):
      raise ValueError("section bytes out of bounds")
    digest = None if kind == 8 else hashlib.sha256(raw[start:start + size]).hexdigest()
    result.append({"index": index, "name": name, "type": kind, "flags": flags, "size": size, "sha256": digest})
  return {"path": str(path.relative_to(Path("/work/apple"))), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "sections": result}


def inspect() -> None:
  root = Path("/work/apple")
  objects = sorted(root.rglob("*.o"))
  if not 17 <= len(objects) <= 32 or any(path.is_symlink() or not stat.S_ISREG(path.stat().st_mode) for path in objects):
    raise ValueError("unexpected compiled object inventory")
  module = elf_sections(root / "appledrm.ko")
  sections = module["sections"]
  if not isinstance(sections, list) or not {".BTF", ".debug_info"}.issubset({section["name"] for section in sections}):
    raise ValueError("module is missing BTF or DWARF")
  save_json(Path("/work/inspection/object-sections.json"), {"module": module, "objects": [elf_sections(path) for path in objects]})


def main(arguments: list[str]) -> None:
  if os.geteuid() != 1001 or any(Path(path).exists() for path in ("/proc", "/sys", "/boot")):
    raise ValueError("requires the reviewed unprivileged offline sandbox")
  if len(arguments) == 2 and arguments[0] == "prepare" and arguments[1] in ("baseline", "patched") and Path.cwd() == Path("/work"):
    prepare(arguments[1])
  elif arguments == ["sections"] and Path.cwd() == Path("/work/apple"):
    inspect()
  else:
    raise ValueError("unexpected private workload invocation")


if __name__ == "__main__":
  main(sys.argv[1:])
