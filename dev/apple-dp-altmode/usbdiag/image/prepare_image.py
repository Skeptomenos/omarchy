"""Prepare one private diagnostic candidate inside the reviewed R4 sandbox.

The launcher must enforce its 280-second total budget (outer wrapper <=290s).
Children use the pinned control's 90-second bound. This is not a live installer.
Required mounts are /inputs/{base,helper,control,index-inputs,diagnostic,proofs};
all source, image, module, index-input, and prior-control proof bytes are pinned.
The passed 406-child control is reused, not rerun. No host fallback is allowed.

Only ATC, the dependency/alias binary indexes, and one added DWC module may
change the main archive. Two fresh module roots contain independent regular
copies, never archive symlinks or hardlinks. All child output and scratch roots
remain on failure. No cleanup, retry, preload, hook, or boot-file edit occurs.
The exclusive final result is written last; its absence means INCOMPLETE.
"""

from collections import Counter
from contextlib import ExitStack
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import stat
import sys
from types import ModuleType
from typing import Any
import zlib


CONTROL = Path("/inputs/control/verify_control.py")
CONTROL_SHA256 = "10b5afe6cff38df7b6ebe5619fd9a34935932a4b369f3a9ad2a51923c32932d8"


def require(condition: bool, detail: str) -> None:
  if not condition:
    raise RuntimeError(detail)


def import_control() -> ModuleType:
  # Authenticate bytes before executing the fixed, read-only control source.
  require(os.getuid() == os.getgid() == 1001, "unexpected workload identity")
  require(Path.cwd() == Path("/work"), "not in the fresh workload directory")
  require(sys.flags.isolated == 1 and sys.flags.no_site == 1 and sys.dont_write_bytecode,
          "isolated Python flags required")
  require(not any(Path(path).exists() for path in ("/proc", "/sys", "/run", "/boot", "/home")),
          "host tree visible")
  require("verify_control" not in sys.modules, "an unverified control is already imported")
  with ExitStack() as stack:
    parent = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    stack.callback(os.close, parent)
    for part in ("inputs", "control"):
      parent = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                       dir_fd=parent)
      stack.callback(os.close, parent)
    descriptor = os.open(CONTROL.name, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC,
                         dir_fd=parent)
    stream = stack.enter_context(os.fdopen(descriptor, "rb"))
    before = os.fstat(stream.fileno())
    require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and 0 < before.st_size < 128 * 1024,
            "control is not a bounded regular single-link source")
    raw = stream.read(128 * 1024)
    def identity(info: os.stat_result) -> tuple[int, ...]:
      return (info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_gid,
              info.st_nlink, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
    require(identity(before) == identity(os.fstat(stream.fileno())) ==
            identity(os.stat(CONTROL.name, dir_fd=parent, follow_symlinks=False)), "control changed")
    require(len(raw) == before.st_size and hashlib.sha256(raw).hexdigest() == CONTROL_SHA256,
            "control source drift")
  module = ModuleType("verify_control")
  module.__file__ = str(CONTROL)
  sys.modules[module.__name__] = module
  exec(compile(raw, str(CONTROL), "exec"), module.__dict__)
  return module


control = import_control()
from cpio_image import Archive, MAX_ARCHIVE_BYTES, parse_newc, read_regular, replace_members, write_new


KERNEL = control.KERNEL
PREFIX = control.ARCHIVE_MODULE_PREFIX
ATC = "kernel/drivers/phy/apple/phy-apple-atc.ko"
DWC = "kernel/drivers/usb/dwc3/dwc3-apple.ko"
DWC_CORE = "kernel/drivers/usb/dwc3/dwc3.ko"
TIPD = "kernel/drivers/usb/typec/tipd/tps6598x-core.ko"
DIAGNOSTICS = {
  "dwc3-apple.ko": "d333ce2d82789d5da8acdc563fd04ea9cde3872472cde423ed1a51710cf38ef4",
  "phy-apple-atc.ko": "504fc2b82e62e7497532dfe4b955228d7298a3f2c9b34d1e9623ed9188912547",
}
PROOFS = {
  "control-result.json": "746516664e917ac3eb7c63c168640921d32de307abd7b4e00410a1ddbaddc03c",
  "binary-lookup.json": "554823bc8a86cddadaea8ac59e48c83839823afda062a8b89a64697701d176cb",
  "index-control.json": "2c57f409e3bb023c48a94902710ab4144b2f8f39bde1a1d30d1f7c77c5e4922e",
  "modules.dep": "8ae00442924415b66e79a554dfefcadda58597be45e55b9e4c88669d81bf6eb6",
  "modules.alias": "20d56450832cfaf43e167d92ea9fa01190487758e39c49baade1db2f1f606fcc",
  "modules.symbols": "91299d9a80705a17c92068869293aa32c86985f751a5e6ea84024cb511ca539a",
}
CHANGED_INDEXES = frozenset(("modules.dep.bin", "modules.alias.bin"))
STATIC_INDEXES = control.INDEX_NAMES - CHANGED_INDEXES
BASE_SYMBOLS_SHA256 = "a3f1e745b7675daaec99c7c7ebadc7d67b318143901e063674494c210b12ace6"
GENERATED_SYMBOLS_SHA256 = "5077fb001a5c48a2135ce8f651606b18578610bc660f430a59114e76be4f9437"
GENERATED_DUMP_SHA256 = "c562726938a6e3d11d5b3661352508f00b74efd9cbadbb559c3680663da72c05"
ALIASES_HEADER = b"# Aliases extracted from modules themselves.\n"
SYMBOLS_HEADER = b"# Aliases for symbols, used by symbol_request().\n"
SOFTDEP_HEADER = b"# Soft dependencies extracted from modules themselves.\n"
WEAKDEP_HEADER = b"# Weak dependencies extracted from modules themselves.\n"
DWC_ALIASES = Counter({
  "alias of:N*T*Capple,t8103-dwc3 dwc3_apple": 1,
  "alias of:N*T*Capple,t8103-dwc3C* dwc3_apple": 1,
})
CONFIG_SEPARATOR = b"\n# End of configuration files. Dumping indexes now:\n\n"
CANDIDATE = Path("/work/initramfs-linux-asahi-dpalt-usbdiag1.img")
RESULT = Path("/work/assembly-result.json")


def sha256(raw: bytes) -> str:
  return hashlib.sha256(raw).hexdigest()


def pinned_inputs() -> dict[Path, str]:
  pins = {control.BASE: control.BASE_SHA256, control.HELPER: control.HELPER_SHA256,
          CONTROL: CONTROL_SHA256}
  for directory, entries in (("index-inputs", control.INDEX_INPUTS),
                             ("diagnostic", DIAGNOSTICS), ("proofs", PROOFS)):
    pins.update({Path("/inputs") / directory / name: digest for name, digest in entries.items()})
  return pins


def text_lines(raw: bytes) -> tuple[str, ...]:
  require(type(raw) is bytes and len(raw) <= 8 * 1024 * 1024 and raw.endswith(b"\n"),
          "invalid bounded text output")
  require(all(char == 10 or 32 <= char <= 126 for char in raw), "non-ASCII text or control byte")
  lines = tuple(raw[:-1].decode("ascii").split("\n"))
  require(len(lines) <= 65536 and all(0 < len(line) <= 8192 for line in lines), "invalid text lines")
  return lines


def json_object(raw: bytes) -> dict[str, Any]:
  require(len(raw) <= 2 * 1024 * 1024, "oversized proof")
  def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
      require(key not in result, "duplicate proof key")
      result[key] = value
    return result
  def invalid_constant(value: str) -> None:
    raise RuntimeError("invalid JSON constant")
  result = json.loads(raw, object_pairs_hook=unique, parse_constant=invalid_constant)
  require(type(result) is dict, "proof is not an object")
  return result


def validate_control_proof(proof: dict[str, Any]) -> None:
  expected = {
    "all_indexes_byte_identical": True, "base_sha256": control.BASE_SHA256,
    "binary_only_lookup": True, "check": "no_change_archive_and_indexes", "commands": 406,
    "diagnostic_image_created": False, "dry_run_dependency_resolution": True,
    "early_members": 7, "general_archive_extracted": False,
    "gzip_reconstruction_byte_identical": True, "level": "info", "main_members": 1162,
    "module_loaded": False, "modules": 199, "retained_indexes": 7,
    "roots_retained": [str(control.CONTROL_ROOT), str(control.LOOKUP_ROOT)], "verdict": "PASS",
  }
  # Canonical JSON equality distinguishes booleans from the integers 0 and 1.
  require(json.dumps(proof, sort_keys=True) == json.dumps(expected, sort_keys=True),
          "prior control proof is not the exact passed no-change result")


def validate_index_proof(proof: dict[str, Any], indexes: dict[str, bytes]) -> None:
  require(set(proof) == {"indexes", "verdict"} and proof["verdict"] == "PASS", "index proof failed")
  entries = proof["indexes"]
  require(type(entries) is list and len(entries) == 7, "index proof count differs")
  names: set[str] = set()
  for entry in entries:
    require(type(entry) is dict and set(entry) ==
            {"name", "actual_sha256", "expected_sha256", "byte_identical"}, "bad index proof entry")
    name = entry["name"]
    require(type(name) is str and name in indexes and name not in names, "index proof name differs")
    require(entry["byte_identical"] is True and
            entry["actual_sha256"] == entry["expected_sha256"] == sha256(indexes[name]),
            "index proof does not bind the base payload")
    names.add(name)
  require(names == control.INDEX_NAMES, "index proof coverage differs")


def lookup_filename(relative: str) -> str:
  return str(control.LOOKUP_ROOT / control.MODULE_DIRECTORY / relative)


def validate_lookup_proof(proof: dict[str, Any], names: dict[str, str],
                          builtins: set[str]) -> dict[str, dict[str, Any]]:
  require(set(proof) == {"module_count", "modules", "no_load", "text_index_fallback_available", "verdict"},
          "unexpected lookup proof fields")
  require(proof["verdict"] == "PASS" and proof["no_load"] is True and
          proof["text_index_fallback_available"] is False, "prior lookup was not binary-only/no-load")
  entries = proof["modules"]
  require(type(proof["module_count"]) is int and proof["module_count"] == len(names) and
          type(entries) is list and len(entries) == len(names), "lookup proof count differs")
  known_files = {lookup_filename(relative) for relative in names.values()}
  result: dict[str, dict[str, Any]] = {}
  for entry in entries:
    require(type(entry) is dict and set(entry) == {"module", "filename", "insmod", "builtin"},
            "unexpected lookup record")
    name = entry["module"]
    require(type(name) is str and name in names and name not in result, "unknown/duplicate lookup module")
    expected = lookup_filename(names[name])
    require(entry["filename"] == expected, "lookup proof filename differs")
    for field, allowed in (("insmod", known_files), ("builtin", builtins)):
      values = entry[field]
      require(type(values) is list and len(values) <= len(allowed) and
              all(type(value) is str and value in allowed for value in values), "unapproved lookup entry")
      require(len(values) == len(set(values)), "duplicate dependency in lookup proof")
    require(expected in entry["insmod"], "target absent from lookup proof")
    result[name] = entry
  require(set(result) == set(names), "lookup proof coverage differs")
  return result


def dependency_entries(raw: bytes, known: set[str]) -> dict[str, tuple[str, ...]]:
  result: dict[str, tuple[str, ...]] = {}
  for line in text_lines(raw):
    require(line.count(":") == 1, "malformed dependency entry")
    name, value = line.split(":")
    require(name in known and name not in result, "unknown/duplicate dependency key")
    require(not value or value.startswith(" "), "malformed dependency separator")
    dependencies = tuple(value[1:].split(" ")) if value else ()
    require(all(item in known and item != name for item in dependencies), "unknown/self dependency")
    require(len(dependencies) == len(set(dependencies)), "duplicate dependency")
    result[name] = dependencies
  require(set(result) == known, "dependency index coverage differs")
  return result


def validate_dependency_delta(before: bytes, after: bytes, original: set[str]) -> None:
  require(DWC not in original and DWC_CORE in original, "wrong baseline DWC identities")
  baseline = dependency_entries(before, original)
  candidate = dependency_entries(after, original | {DWC})
  require(all(candidate[name] == values for name, values in baseline.items()), "existing dependency entry changed")
  expected = {DWC_CORE, *baseline[DWC_CORE]}
  require(set(candidate[DWC]) == expected, "new DWC dependency closure differs")


def alias_entries(raw: bytes, header: bytes) -> Counter[str]:
  require(raw.startswith(header), "unexpected alias/symbol header")
  body = raw[len(header):]
  if not body:
    return Counter()
  lines = text_lines(body)
  for line in lines:
    words = line.split(" ")
    require(len(words) == 3 and words[0] == "alias" and bool(words[1]) and
            re.fullmatch(r"[A-Za-z0-9_]+", words[2]) is not None, "unexpected alias entry")
  return Counter(lines)


def validate_alias_delta(before: bytes, after: bytes) -> None:
  baseline = alias_entries(before, ALIASES_HEADER)
  require(not baseline.keys() & DWC_ALIASES.keys(), "DWC aliases already present")
  require(alias_entries(after, ALIASES_HEADER) == baseline + DWC_ALIASES, "alias delta differs")


def normalize_alias_key(value: str) -> str:
  """Match kmod v34.2 alias_normalize for bounded, nonempty ASCII keys.

  Hyphens outside the first-closing-bracket spans become underscores. The
  private contract rejects control bytes, whitespace, and lengths above 4095.
  Source: https://raw.githubusercontent.com/kmod-project/kmod/v34.2/shared/util.c
  """
  require(type(value) is str and 0 < len(value) < 4096, "invalid alias key type/length")
  require(all(33 <= ord(char) <= 126 for char in value), "invalid alias key bytes")
  result: list[str] = []
  offset = 0
  while offset < len(value):
    char = value[offset]
    require(char != "]", "stray alias bracket")
    if char == "[":
      end = value.find("]", offset + 1)
      require(end != -1, "unterminated alias bracket")
      result.append(value[offset:end + 1])
      offset = end + 1
    else:
      result.append("_" if char == "-" else char)
      offset += 1
  return "".join(result)


def validate_static_indexes(before: dict[str, bytes], after: dict[str, bytes],
                            symbols: bytes, weakdeps: bytes, expected_symbols: bytes) -> None:
  require(set(before) == set(after) == control.INDEX_NAMES, "retained index set differs")
  require(all(after[name] == before[name] for name in STATIC_INDEXES), "unrelated index changed")
  require(all(after[name] != before[name] for name in CHANGED_INDEXES), "necessary binary index did not change")
  require(symbols == expected_symbols, "symbol text index changed")
  require(weakdeps == WEAKDEP_HEADER, "unexpected weak dependencies")


def validate_binary_dump(raw: bytes, aliases: bytes, symbols: bytes, softdeps: bytes) -> None:
  require(raw.count(CONFIG_SEPARATOR) == 1, "unexpected binary dump boundary")
  config, indexes = raw.split(CONFIG_SEPARATOR)
  require(softdeps.startswith(SOFTDEP_HEADER), "unexpected softdep header")
  require(config == softdeps[len(SOFTDEP_HEADER):], "unexpected modprobe configuration")
  expected: Counter[str] = Counter()
  for line, count in alias_entries(aliases, ALIASES_HEADER).items():
    _, key, owner = line.split(" ")
    expected[f"alias {normalize_alias_key(key)} {owner}"] += count
  # The symbol-index writer does not call alias_normalize. Keep its keys literal.
  expected += alias_entries(symbols, SYMBOLS_HEADER)
  require(Counter(text_lines(indexes)) == expected, "binary alias/symbol contents differ")


def select_image_indexes(before: dict[str, bytes], regenerated: dict[str, bytes], *,
                         symbols: bytes, weakdeps: bytes, expected_symbols: bytes,
                         generated_dump: bytes, expected_aliases: bytes) -> dict[str, bytes]:
  """Select original symbol bytes only after authenticating the regenerated proof.

  The two symbol binaries and generated dump must match their exact reviewed
  pins. Their text/binary mappings must match the expected aliases and original
  symbol text. Return a new seven-index dictionary, with the original symbols
  and all final static-index byte-equality checks still enforced. Never mutate
  the input dictionaries or any scratch file.
  """
  require(type(before) is dict and type(regenerated) is dict, "invalid index collections")
  require(set(before) == set(regenerated) == control.INDEX_NAMES, "retained index set differs")
  require(all(type(raw) is bytes for raw in (*before.values(), *regenerated.values())),
          "invalid index payload type")
  require(sha256(before["modules.symbols.bin"]) == BASE_SYMBOLS_SHA256, "original symbol index drift")
  require(sha256(regenerated["modules.symbols.bin"]) == GENERATED_SYMBOLS_SHA256,
          "unreviewed regenerated symbol index")
  require(sha256(generated_dump) == GENERATED_DUMP_SHA256, "unreviewed generated binary dump")
  validate_binary_dump(generated_dump, expected_aliases, expected_symbols, before["modules.softdep"])
  selected = dict(regenerated)
  selected["modules.symbols.bin"] = before["modules.symbols.bin"]
  validate_static_indexes(before, selected, symbols, weakdeps, expected_symbols)
  return selected


def verify_empty_config(expected: tuple[int, ...]) -> None:
  require(read_regular(control.EMPTY_CONFIG) == b"" and
          control.file_identity(control.EMPTY_CONFIG.lstat()) == expected, "private modprobe config changed")


def build_root(root: Path, modules: dict[str, bytes], metadata: dict[str, bytes]) -> Any:
  require(root in (control.CONTROL_ROOT, control.LOOKUP_ROOT), "unapproved private root")
  require(len(modules) == 200 and set(metadata) in (set(control.INDEX_INPUTS), set(control.INDEX_NAMES)),
          "unapproved root file set")
  for relative in modules:
    path = Path(relative)
    require(not path.is_absolute() and path.as_posix() == relative and path.parts[0] == "kernel" and
            not any(part in (".", "..") for part in path.parts) and
            not any(char.isspace() for char in relative), "unsafe module placement")
  root.mkdir(mode=0o700)
  payloads = {control.MODULE_DIRECTORY / relative: payload for relative, payload in (modules | metadata).items()}
  directories = {parent for path in payloads for parent in path.parents if parent != Path(".")}
  for relative in sorted(directories, key=lambda path: (len(path.parts), str(path))):
    (root / relative).mkdir(mode=0o700)
  for relative, payload in payloads.items():
    write_new(root / relative, payload)
  state = control.snapshot(root)
  require(set(state.files) == {str(path) for path in payloads}, "root contains an unexpected file")
  require(all(state.files[str(path)].sha256 == sha256(payload) for path, payload in payloads.items()),
          "private root copy differs")
  return state


def generate_indexes(modules: dict[str, bytes], base_indexes: dict[str, bytes], inputs: dict[str, bytes],
                     proofs: dict[str, bytes], commands: Any,
                     config_identity: tuple[int, ...]) -> tuple[dict[str, bytes], Any]:
  before = build_root(control.CONTROL_ROOT, modules, inputs)
  control.save_json("candidate-root-before.json", asdict(before))
  commands.run(("/usr/bin/depmod", "-b", str(control.CONTROL_ROOT), KERNEL))
  after = control.snapshot(control.CONTROL_ROOT)
  control.save_json("candidate-root-after.json", asdict(after))
  expected = set(before.files) | {
    str(control.MODULE_DIRECTORY / name) for name in control.INDEX_NAMES | control.EXTRA_TEXT_INDEXES
  }
  require(set(after.files) == expected, "unexpected depmod output set")
  require(after.directories == before.directories and
          all(after.files.get(name) == state for name, state in before.files.items()), "depmod changed inputs")
  directory = control.CONTROL_ROOT / control.MODULE_DIRECTORY
  outputs = {name: read_regular(directory / name)
             for name in control.INDEX_NAMES | control.EXTRA_TEXT_INDEXES}
  validate_dependency_delta(proofs["modules.dep"], outputs["modules.dep"], set(modules) - {DWC})
  validate_alias_delta(proofs["modules.alias"], outputs["modules.alias"])
  verify_empty_config(config_identity)
  generated_dump = commands.run(("/usr/bin/modprobe", "--dry-run", "--show-depends", "-d",
                                str(control.CONTROL_ROOT), "-S", KERNEL, "-C",
                                str(control.EMPTY_CONFIG), "--show-config"))
  after_dump = control.snapshot(control.CONTROL_ROOT)
  control.save_json("candidate-root-after-dump.json", asdict(after_dump))
  require(after_dump == after, "generated-index dump changed the scratch root")
  verify_empty_config(config_identity)
  regenerated = {name: outputs[name] for name in control.INDEX_NAMES}
  indexes = select_image_indexes(base_indexes, regenerated, symbols=outputs["modules.symbols"],
                                 weakdeps=outputs["modules.weakdep"], expected_symbols=proofs["modules.symbols"],
                                 generated_dump=generated_dump, expected_aliases=outputs["modules.alias"])
  control.save_json("candidate-indexes.json", {
    "verdict": "PASS", "old_dependency_entries_unchanged": 199,
    "new_dependency_entry": DWC, "new_aliases": sorted(DWC_ALIASES),
    "changed_binary_indexes": sorted(CHANGED_INDEXES), "final_static_indexes_byte_identical": sorted(STATIC_INDEXES),
    "generated_symbols_sha256": sha256(outputs["modules.symbols.bin"]),
    "retained_symbols_sha256": sha256(indexes["modules.symbols.bin"]),
    "generated_binary_dump_sha256": sha256(generated_dump), "generated_symbol_file_preserved": True,
    "symbol_index_policy": "original retained; generated bytes match reviewed priority-only drift",
    "indexes": {name: sha256(raw) for name, raw in indexes.items()},
  })
  return indexes, after


def dependency_output(raw: bytes, name: str, names: dict[str, str],
                      builtins: set[str]) -> dict[str, Any]:
  known_files = {lookup_filename(relative) for relative in names.values()}
  insmod: list[str] = []
  builtin: list[str] = []
  for line in text_lines(raw):
    words = shlex.split(line, comments=False, posix=True)
    require(len(words) == 2, "unexpected dependency output")
    if words[0] == "insmod":
      require(words[1] in known_files and words[1] not in insmod, "unapproved/repeated dependency path")
      insmod.append(words[1])
    elif words[0] == "builtin":
      require(words[1].replace("-", "_") in builtins and words[1] not in builtin, "unapproved builtin")
      builtin.append(words[1])
    else:
      raise RuntimeError("unapproved dry-run action")
  expected = lookup_filename(names[name])
  require(expected in insmod, "target missing from dry-run dependencies")
  return {"module": name, "filename": expected, "insmod": insmod, "builtin": builtin}


def validate_candidate_lookup(actual: dict[str, dict[str, Any]],
                               baseline: dict[str, dict[str, Any]]) -> None:
  require(set(actual) == set(baseline) | {"dwc3_apple"}, "candidate lookup coverage differs")
  require(all(actual[name] == entry for name, entry in baseline.items()), "old dependency resolution changed")
  new_path = lookup_filename(DWC)
  expected = {"module": "dwc3_apple", "filename": new_path,
              "insmod": baseline["dwc3"]["insmod"] + [new_path], "builtin": baseline["dwc3"]["builtin"]}
  require(actual["dwc3_apple"] == expected, "DWC dry-run dependency closure/order differs")


def binary_lookup(modules: dict[str, bytes], indexes: dict[str, bytes], names: dict[str, str],
                  baseline: dict[str, dict[str, Any]], builtins: set[str], proofs: dict[str, bytes],
                  commands: Any, config_identity: tuple[int, ...]) -> None:
  before = build_root(control.LOOKUP_ROOT, modules, indexes)
  require(len(before.files) == 207, "binary-only root count differs")
  control.save_json("candidate-lookup-before.json", asdict(before))
  verify_empty_config(config_identity)
  dump = commands.run(control.modprobe_command("--show-config"))
  aliases = ALIASES_HEADER + ("\n".join(sorted(
    (alias_entries(proofs["modules.alias"], ALIASES_HEADER) + DWC_ALIASES).elements()
  )) + "\n").encode("ascii")
  validate_binary_dump(dump, aliases, proofs["modules.symbols"], indexes["modules.softdep"])
  results: dict[str, dict[str, Any]] = {}
  for name, relative in names.items():
    expected = lookup_filename(relative)
    info = commands.run(("/usr/bin/modinfo", "-b", str(control.LOOKUP_ROOT), "-k", KERNEL,
                         "-F", "filename", name), output_bound=8192)
    require(info == (expected + "\n").encode("ascii"), "binary filename lookup differs")
    raw = commands.run(control.modprobe_command(name), output_bound=1024 * 1024)
    results[name] = dependency_output(raw, name, names, builtins)
  validate_candidate_lookup(results, baseline)
  alias_results: dict[str, dict[str, Any]] = {}
  for alias, name in (("of:Ndwc3T(null)Capple,t8103-dwc3", "dwc3_apple"),
                       ("of:Natc-phyT(null)Capple,t8103-atcphy", "phy_apple_atc")):
    raw = commands.run(control.modprobe_command(alias), output_bound=1024 * 1024)
    actual = dependency_output(raw, name, names, builtins)
    require(actual == results[name], "concrete OF alias resolution differs")
    alias_results[alias] = actual
  after = control.snapshot(control.LOOKUP_ROOT)
  control.save_json("candidate-lookup-after.json", asdict(after))
  require(after == before, "read-only lookup changed its inputs")
  verify_empty_config(config_identity)
  control.save_json("candidate-binary-lookup.json", {
    "verdict": "PASS", "module_count": 200, "old_results_byte_equivalent": 199,
    "no_load": True, "text_index_fallback_available": False,
    "modules": list(results.values()), "concrete_aliases": alias_results,
  })


def archive_delta(before: Archive, after: Archive, replacements: dict[str, bytes],
                  added: bytes) -> list[dict[str, Any]]:
  expected_replacements = {PREFIX + ATC, *(PREFIX + name for name in CHANGED_INDEXES)}
  require(set(replacements) == expected_replacements, "unapproved archive replacement set")
  require(tuple(member.name for member in after.members) ==
          tuple(member.name for member in before.members) + (PREFIX + DWC,), "archive membership/order differs")
  require(before.tail == after.tail, "trailer or zero tail changed")
  changes: list[dict[str, Any]] = []
  seen: set[str] = set()
  for old, new in zip(before.members, after.members[:-1], strict=True):
    if old.name not in replacements:
      require(old.raw == new.raw, "unrelated raw archive record changed")
      continue
    require(new.payload == replacements[old.name] and new.payload != old.payload, "wrong replacement payload")
    require(old.raw_name == new.raw_name and
            all(old.fields[index] == new.fields[index] for index in range(13) if index != 6),
            "replacement metadata changed")
    name_end = (110 + len(old.raw_name) + 3) & ~3
    require(old.raw[:54] == new.raw[:54] and old.raw[62:name_end] == new.raw[62:name_end],
            "replacement rewrote untouched header/name bytes")
    changes.append({"name": old.name, "action": "replace", "old_sha256": sha256(old.payload),
                    "new_sha256": sha256(new.payload), "metadata_preserved_except_size": True})
    seen.add(old.name)
  require(seen == expected_replacements, "required original member missing")
  new = after.members[-1]
  raw_name = (PREFIX + DWC).encode("ascii") + b"\0"
  expected_fields = (max(member.fields[0] for member in before.members) + 1, stat.S_IFREG | 0o644,
                     0, 0, 1, 0, len(added), 0, 0, 0, 0, len(raw_name), 0)
  require(new.payload == added and new.raw_name == raw_name and new.fields == expected_fields,
          "new DWC member payload/metadata differs")
  changes.append({"name": new.name, "action": "add", "new_sha256": sha256(new.payload),
                  "fields": new.fields})
  return changes


def single_gzip(raw: bytes, expected_bytes: int) -> bytes:
  require(0 < len(raw) <= MAX_ARCHIVE_BYTES and 0 < expected_bytes <= MAX_ARCHIVE_BYTES,
          "gzip size bound exceeded")
  decoder = zlib.decompressobj(16 + zlib.MAX_WBITS)
  result = decoder.decompress(raw, expected_bytes + 1)
  require(len(result) == expected_bytes and decoder.eof and not decoder.unconsumed_tail and
          not decoder.unused_data, "wrong, truncated, or concatenated candidate gzip")
  return result


def independent_archive_checks(early: Archive, main: Archive, diagnostics: dict[str, bytes],
                               tipd: bytes, commands: Any) -> None:
  for label, archive in (("early", early), ("candidate-main", main)):
    path = Path("/work") / f"{label}.cpio"
    write_new(path, archive.raw)
    first = commands.run(("/usr/bin/cpio", "--list", "--quiet", "--file", str(path)))
    second = commands.run(("/usr/bin/bsdtar", "--list", "--file", str(path)))
    require(control.listed_names(first, archive) == control.listed_names(second, archive), "archive tools disagree")
  by_name = {member.name: member for member in main.members}
  selected = {PREFIX + ATC: diagnostics["phy-apple-atc.ko"],
              PREFIX + DWC: diagnostics["dwc3-apple.ko"], PREFIX + TIPD: tipd}
  for name, expected in selected.items():
    member = by_name[name]
    control.regular_member(member)
    raw_name = member.raw_name[:-1].decode("ascii")
    # -O sends only the selected regular payload to stdout. No archive path is materialized.
    actual = commands.run(("/usr/bin/bsdtar", "--extract", "--to-stdout", "--file",
                           "/work/candidate-main.cpio", "--", raw_name), output_bound=len(expected))
    require(actual == expected, "independent stdout-only module extraction differs")


def main() -> None:
  control.isolated()
  os.umask(0o077)
  require(not any(path.exists() or path.is_symlink() for path in
                  (control.CONTROL_ROOT, control.LOOKUP_ROOT, control.EMPTY_CONFIG, CANDIDATE, RESULT)),
          "outputs already exist; use a fresh sandbox")
  pins = pinned_inputs()
  data = {path: read_regular(path, digest) for path, digest in pins.items()}
  base = data[control.BASE]
  require(len(base) == control.BASE_BYTES, "base image size differs")
  early = parse_newc(base[:control.MAIN_OFFSET])
  original = parse_newc(control.main_stream(base))
  require(len(early.members) == 7 and len(original.members) == 1162, "base member counts differ")
  original_modules = control.select_modules(original)
  modules = {str(module.relative): module.member.payload for module in original_modules}
  names = {module.name: str(module.relative) for module in original_modules}
  indexes = control.select_indexes(original)
  proofs = {name: data[Path("/inputs/proofs") / name] for name in PROOFS}
  inputs = {name: data[Path("/inputs/index-inputs") / name] for name in control.INDEX_INPUTS}
  diagnostics = {name: data[Path("/inputs/diagnostic") / name] for name in DIAGNOSTICS}
  validate_control_proof(json_object(proofs["control-result.json"]))
  validate_index_proof(json_object(proofs["index-control.json"]), indexes)
  builtins = control.builtin_names(inputs["modules.builtin"])
  baseline = validate_lookup_proof(json_object(proofs["binary-lookup.json"]), names, builtins)
  require({ATC, TIPD, DWC_CORE} <= set(modules) and DWC not in modules, "base module placement differs")
  tipd = modules[TIPD]
  modules[ATC] = diagnostics["phy-apple-atc.ko"]
  modules[DWC] = diagnostics["dwc3-apple.ko"]
  names["dwc3_apple"] = DWC
  require(len(modules) == len(names) == 200, "candidate module identities are ambiguous")
  control.save_json("assembly-inputs.json", {str(path): digest for path, digest in pins.items()})
  write_new(control.EMPTY_CONFIG, b"")
  config_identity = control.file_identity(control.EMPTY_CONFIG.lstat())
  commands = control.Commands()
  candidate_indexes, generated_state = generate_indexes(modules, indexes, inputs, proofs, commands, config_identity)
  binary_lookup(modules, candidate_indexes, names, baseline, builtins, proofs, commands, config_identity)
  replacements = {PREFIX + ATC: diagnostics["phy-apple-atc.ko"],
                   **{PREFIX + name: candidate_indexes[name] for name in CHANGED_INDEXES}}
  main_raw = replace_members(original, replacements, ((PREFIX + DWC, diagnostics["dwc3-apple.ko"]),))
  candidate_main = parse_newc(main_raw)
  changes = archive_delta(original, candidate_main, replacements, diagnostics["dwc3-apple.ko"])
  independent_archive_checks(early, candidate_main, diagnostics, tipd, commands)
  compressed = commands.run(("/usr/bin/gzip",), payload=main_raw, output_bound=MAX_ARCHIVE_BYTES)
  require(single_gzip(compressed, len(main_raw)) == main_raw, "candidate gzip roundtrip differs")
  candidate = early.raw + compressed
  require(len(candidate) <= MAX_ARCHIVE_BYTES, "candidate image exceeds bound")
  require(control.snapshot(control.CONTROL_ROOT) == generated_state, "generated root changed after checks")
  verify_empty_config(config_identity)
  for path, digest in pins.items():
    read_regular(path, digest)
  # No candidate-path write occurs until all independent/index checks above pass.
  write_new(CANDIDATE, candidate)
  readback = read_regular(CANDIDATE, sha256(candidate))
  require(readback == candidate and readback[:control.MAIN_OFFSET] == early.raw, "candidate readback differs")
  reread_early = parse_newc(readback[:control.MAIN_OFFSET])
  reread_main = parse_newc(single_gzip(readback[control.MAIN_OFFSET:], len(main_raw)))
  require(reread_early.raw == early.raw and len(reread_early.members) == 7, "early archive changed")
  require(archive_delta(original, reread_main, replacements, diagnostics["dwc3-apple.ko"]) == changes,
          "readback archive delta differs")
  verify_empty_config(config_identity)
  for path, digest in pins.items():
    read_regular(path, digest)
  control.save_json("image-delta.json", {
    "verdict": "PASS", "base_sha256": control.BASE_SHA256, "candidate_sha256": sha256(readback),
    "early_raw_sha256": sha256(early.raw), "early_records": 7, "original_main_records": 1162,
    "candidate_main_records": len(reread_main.members), "unchanged_main_raw_records": 1159,
    "tail_preserved": True, "changes": changes, "tipd_sha256_unchanged": sha256(tipd),
  })
  report = {
    "level": "info", "check": "private_diagnostic_candidate", "verdict": "PASS",
    "candidate": str(CANDIDATE), "candidate_sha256": sha256(readback), "candidate_bytes": len(readback),
    "modules": 200, "retained_indexes": 7, "commands": commands.count,
    "all_immutable_inputs_preserved": True, "prior_control_reused": True,
    "independent_stdout_only_module_checks": 3, "binary_only_lookup": True,
    "old_dependency_results_unchanged": 199, "roots_retained": [str(control.CONTROL_ROOT), str(control.LOOKUP_ROOT)],
    "general_archive_extracted": False, "staged": False, "module_loaded": False,
    "rebooted": False, "boot_tested": False,
  }
  control.save_json(RESULT.name, report)
  print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
  main()
