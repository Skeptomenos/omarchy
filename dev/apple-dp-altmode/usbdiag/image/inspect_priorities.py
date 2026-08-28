"""Read-only field comparison for the two pinned kmod symbol indexes.

The disk layout follows kmod v34.2 libkmod/libkmod-index.c:51-73. This is a
one-off evidence check, not an index writer or a general file-format library.
"""

import hashlib
import json
from pathlib import Path
import re
import stat
import struct


def require(condition: bool, message: str) -> None:
  if not condition:
    raise RuntimeError(message)


def read_index(path: Path, expected: str) -> bytes:
  info = path.lstat()
  require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_size == 31021,
          "unexpected symbol index file")
  data = path.read_bytes()
  require(len(data) == 31021 and hashlib.sha256(data).hexdigest() == expected, "index pin differs")
  return data


def parse(data: bytes) -> dict[tuple[str, str], tuple[int, int]]:
  require(len(data) == 31021, "unexpected byte count")
  magic, version, root = struct.unpack_from(">III", data)
  require((magic, version) == (0xB007F457, 0x00020001), "unexpected binary format")
  covered = bytearray(len(data))
  covered[:12] = b"\1" * 12
  entries: dict[tuple[str, str], tuple[int, int]] = {}
  nodes: set[int] = set()
  pending = [("", root)]

  def integer(at: int) -> tuple[int, int]:
    require(0 <= at <= len(data) - 4, "truncated integer")
    return struct.unpack_from(">I", data, at)[0], at + 4

  def string(at: int) -> tuple[str, int]:
    end = data.find(b"\0", at, min(at + 4096, len(data)))
    require(end != -1, "unterminated string")
    raw = data[at:end]
    require(all(32 < byte < 127 for byte in raw), "unexpected index character")
    return raw.decode("ascii"), end + 1

  while pending:
    prefix, flagged = pending.pop()
    require(len(nodes) < 4096 and not flagged & 0x10000000, "invalid node flags/count")
    start = flagged & 0x0FFFFFFF
    require(12 <= start < len(data) and start not in nodes, "invalid/repeated node")
    nodes.add(start)
    position = start
    key = prefix
    if flagged & 0x80000000:
      suffix, position = string(position)
      key += suffix
    require(len(key) < 4096, "overlong key")
    children = []
    if flagged & 0x20000000:
      require(position + 2 <= len(data), "truncated child range")
      first, last = data[position:position + 2]
      position += 2
      require(0 < first <= last < 128, "invalid child range")
      for character in range(first, last + 1):
        child, position = integer(position)
        if child:
          children.append((key + chr(character), child))
    if flagged & 0x40000000:
      count, position = integer(position)
      require(0 < count <= 596, "invalid value count")
      for _ in range(count):
        priority_offset = position
        priority, position = integer(position)
        owner, position = string(position)
        require(key.startswith("symbol:") and re.fullmatch(r"[A-Za-z0-9_]+", owner) is not None,
                "unexpected symbol mapping")
        identity = (key, owner)
        require(identity not in entries and len(entries) < 596, "duplicate/excess mapping")
        entries[identity] = (priority, priority_offset)
    require(position > start and not any(covered[start:position]), "overlapping node data")
    covered[start:position] = b"\1" * (position - start)
    pending.extend(children)
  require(len(entries) == 596 and all(covered), "incomplete mapping or byte coverage")
  return entries


before = read_index(Path("/inputs/before"), "a3f1e745b7675daaec99c7c7ebadc7d67b318143901e063674494c210b12ace6")
after = read_index(Path("/inputs/after"), "5077fb001a5c48a2135ce8f651606b18578610bc660f430a59114e76be4f9437")
original = parse(before)
regenerated = parse(after)
require(original.keys() == regenerated.keys(), "mapping identity changed")
priority_bytes: set[int] = set()
shifted = 0
owners: set[str] = set()
for identity, (priority, offset) in original.items():
  updated, updated_offset = regenerated[identity]
  require(offset == updated_offset and 0 <= priority < 199 and 0 <= updated < 200,
          "field placement or priority bounds changed")
  require(updated - priority in (0, 1), "unexpected priority delta")
  priority_bytes.update(range(offset, offset + 4))
  if updated != priority:
    shifted += 1
    owners.add(identity[1])
different = {index for index, (left, right) in enumerate(zip(before, after, strict=True)) if left != right}
require(bool(different) and different <= priority_bytes, "a non-priority byte changed")
print(json.dumps({"verdict": "PASS", "bytes_each": len(before), "mappings_each": len(original),
                  "changed_bytes": len(different), "priority_fields_incremented_by_one": shifted,
                  "owners_with_shifted_priority": len(owners), "all_other_bytes_identical": True,
                  "input_files_read_only": True, "module_loaded": False, "image_created": False,
                  "format_source": "https://github.com/kmod-project/kmod/blob/v34.2/libkmod/libkmod-index.c#L51"},
                 sort_keys=True))
