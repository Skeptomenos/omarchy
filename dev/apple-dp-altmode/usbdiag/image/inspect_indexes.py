"""Inspect two retained binary index sets without editing either root.

The first inspection stopped on real kmod alias normalization. This revision
compares alias keys with the bounded rule in kmod v34.2 shared/util.c:65-99.
Symbol keys and module names stay unchanged. No module or image is created.
"""

from collections import Counter
import hashlib
import json
from pathlib import Path
import stat
import sys


source = Path("/inputs/assembly/prepare_image.py")
info = source.lstat()
if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
  raise RuntimeError("assembly source is not a regular single-link input")
if hashlib.sha256(source.read_bytes()).hexdigest() != "1bf91b538d63de95a2f74075c6d17443cfdb8f4bdb165662b448baf2f048a2bd":
  raise RuntimeError("assembly source drift")
sys.path.insert(0, "/inputs/assembly")
import prepare_image as subject


def normalized_key(key: str) -> str:
  subject.require(type(key) is str and 0 < len(key) < 4096 and
                  all(33 <= ord(char) <= 126 for char in key), "unbounded/non-ASCII alias key")
  pieces: list[str] = []
  offset = 0
  while offset < len(key):
    char = key[offset]
    subject.require(char != "]", "stray closing bracket")
    if char == "[":
      end = key.find("]", offset + 1)
      subject.require(end != -1, "unterminated bracket")
      pieces.append(key[offset:end + 1])
      offset = end + 1
    else:
      pieces.append("_" if char == "-" else char)
      offset += 1
  return "".join(pieces)


def inspect_dump(raw: bytes, aliases: bytes, symbols: bytes, softdeps: bytes) -> dict[str, int]:
  subject.require(raw.count(subject.CONFIG_SEPARATOR) == 1, "unexpected binary dump boundary")
  config, indexes = raw.split(subject.CONFIG_SEPARATOR)
  subject.require(softdeps.startswith(subject.SOFTDEP_HEADER) and
                  config == softdeps[len(subject.SOFTDEP_HEADER):], "configuration differs")
  original = subject.alias_entries(aliases, subject.ALIASES_HEADER)
  normalized: Counter[str] = Counter()
  changed = 0
  for line, count in original.items():
    _, key, owner = line.split(" ")
    normalized_line = f"alias {normalized_key(key)} {owner}"
    normalized[normalized_line] += count
    if normalized_line != line:
      changed += count
  symbol_rows = subject.alias_entries(symbols, subject.SYMBOLS_HEADER)
  expected = normalized + symbol_rows
  subject.require(Counter(subject.text_lines(indexes)) == expected, "binary mappings differ")
  return {"alias_mappings": sum(normalized.values()), "symbol_mappings": sum(symbol_rows.values()),
          "alias_keys_normalized": changed, "total_mappings": sum(expected.values())}


control = subject.control
control.isolated()
for before, after in (("x-[a-z]-y", "x_[a-z]_y"), ("[[]-x", "[[]_x"),
                       ("x-[]-y", "x_[]_y"), ("x\\-y", "x\\_y"),
                       ("[a[b-c]d-e", "[a[b-c]d_e")):
  subject.require(normalized_key(before) == after, "normalization sanity check failed")
for invalid in ("x]", "[", "[[a-z]]", "", "x y", "x" * 4096):
  try:
    normalized_key(invalid)
  except RuntimeError:
    pass
  else:
    raise RuntimeError("invalid alias sanity check was accepted")
proofs = {name: subject.read_regular(Path("/inputs/proofs") / name, subject.PROOFS[name])
          for name in ("modules.alias", "modules.symbols")}
baseline_aliases = proofs["modules.alias"]
candidate_aliases = baseline_aliases + ("\n".join(subject.DWC_ALIASES.elements()) + "\n").encode("ascii")
subject.write_new(control.EMPTY_CONFIG, b"")
commands = control.Commands()
reports = []
for label, root, aliases, symbol_hash, total in (
  ("baseline", Path("/inputs/base-root"), baseline_aliases,
   "a3f1e745b7675daaec99c7c7ebadc7d67b318143901e063674494c210b12ace6", 2002),
  ("regenerated", Path("/inputs/generated-root"), candidate_aliases,
   "5077fb001a5c48a2135ce8f651606b18578610bc660f430a59114e76be4f9437", 2004),
):
  before = control.snapshot(root)
  directory = root / control.MODULE_DIRECTORY
  subject.read_regular(directory / "modules.symbols.bin", symbol_hash)
  if label == "regenerated":
    subject.read_regular(directory / "modules.symbols", subject.PROOFS["modules.symbols"])
    subject.read_regular(directory / "modules.dep.bin", "436095f4779ccbd9f0c44b90febef13b62be50c9518dd499c151843fdf1feb3d")
    subject.read_regular(directory / "modules.alias.bin", "ca6ca7be95509eb294c2e67090bfa84dcbab855fb0489e504804593a257c4ea9")
  softdeps = subject.read_regular(
    directory / "modules.softdep", "6a8f2009d87deba7a2de46e3d0c46b114fe388d188b00b9a382fc2156aabb676"
  )
  command = ("/usr/bin/modprobe", "--dry-run", "--show-depends", "-d", str(root),
             "-S", control.KERNEL, "-C", str(control.EMPTY_CONFIG), "--show-config")
  raw = commands.run(command)
  counts = inspect_dump(raw, aliases, proofs["modules.symbols"], softdeps)
  subject.require(counts["total_mappings"] == total, "unexpected mapping count")
  subject.require(control.snapshot(root) == before, "read-only index root changed")
  reports.append({"root": label, "verdict": "PASS", "symbol_index_sha256": symbol_hash,
                  **counts, "symbols_match_baseline": True, "root_unchanged": True})
subject.require(subject.read_regular(control.EMPTY_CONFIG) == b"", "private config changed")
result = {"check": "retained_binary_index_mappings", "verdict": "PASS", "roots": reports,
          "commands": commands.count, "module_loaded": False, "image_created": False,
          "rule_source": "https://github.com/kmod-project/kmod/blob/v34.2/shared/util.c#L65"}
control.save_json("index-inspection.json", result)
print(json.dumps(result, sort_keys=True))
