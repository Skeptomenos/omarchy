"""Prepare only the fixed E comparison in fresh, reviewed private containment.

E keeps the working image's ATC, TIPD, and every other original module. It adds
the exact packaged DWC3 module and replaces only the required dep/alias indexes.
The authenticated old utilities retain their original pins and strict checks.
In particular, a different regenerated symbol index/dump is a STOP for review,
not authority to change pins, normalize indexes, or accept a broader delta.

The launcher owns the total deadline. No install, staging, live query, fallback,
cleanup, retry, B/G image, or boot action exists here. The final report is last.
"""

import hashlib
import json
import os
from pathlib import Path
import stat
import sys
from types import ModuleType


ASSEMBLY = Path("/inputs/assembly/prepare_image.py")
ASSEMBLY_SHA256 = "00caceb3b7fa236dcc030fb4007d0baa75bfa08fcd1590626f85fcc8c22d5f60"
STOCK_DWC_SHA256 = "d150400f9782c876972b2745d95617cd44e23574452f63980704911a467f7767"
STOCK_ATC_SHA256 = "fd1c3d105bd69a649a38e89e2ca0bcbe6f656200a0f211d58211e8c7b3ec944b"
STOCK_DWC = Path("/inputs/stock/dwc3-apple.ko")
STOCK_ATC = Path("/inputs/stock/phy-apple-atc.ko")
CANDIDATE = Path("/work/initramfs-linux-asahi-dpalt-usbearly1.img")
RESULT = Path("/work/e-assembly-result.json")


def require(condition: bool, detail: str) -> None:
  if not condition:
    raise RuntimeError(detail)


def import_prior() -> ModuleType:
  require(os.getuid() == os.getgid() == 1001 and Path.cwd() == Path("/work"),
          "unexpected workload identity/directory")
  require(sys.flags.isolated == 1 and sys.flags.no_site == 1 and sys.dont_write_bytecode,
          "isolated Python flags required")
  require(not any(Path(path).exists() for path in ("/proc", "/sys", "/run", "/home", "/boot")),
          "host tree visible")
  for parent in (Path("/inputs"), ASSEMBLY.parent):
    require(stat.S_ISDIR(parent.lstat().st_mode), "assembler parent is not a real directory")
  before = ASSEMBLY.lstat()
  require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and 0 < before.st_size < 128 * 1024,
          "assembler is not bounded regular single-link input")
  descriptor = os.open(ASSEMBLY, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC)
  def identity(info: os.stat_result) -> tuple[int, ...]:
    return (info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_gid,
            info.st_nlink, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
  with os.fdopen(descriptor, "rb") as stream:
    require(identity(os.fstat(stream.fileno())) == identity(before), "assembler changed on open")
    raw = stream.read(128 * 1024)
    require(identity(os.fstat(stream.fileno())) == identity(before) == identity(ASSEMBLY.lstat()),
            "assembler changed while reading")
  require(len(raw) == before.st_size and hashlib.sha256(raw).hexdigest() == ASSEMBLY_SHA256,
          "assembler source drift")
  name = "dev147_prior_assembler"
  require(name not in sys.modules, "prior assembler already imported")
  module = ModuleType(name)
  module.__file__ = str(ASSEMBLY)
  sys.modules[name] = module
  exec(compile(raw, str(ASSEMBLY), "exec"), module.__dict__)
  return module


prior = import_prior()
control = prior.control
from cpio_image import Archive, MAX_ARCHIVE_BYTES, parse_newc, read_regular, replace_members, write_new


PREFIX = control.ARCHIVE_MODULE_PREFIX
ATC, DWC, DWC_CORE, TIPD = prior.ATC, prior.DWC, prior.DWC_CORE, prior.TIPD
CHANGED_INDEXES = prior.CHANGED_INDEXES


def sha256(raw: bytes) -> str:
  return hashlib.sha256(raw).hexdigest()


def pinned_inputs() -> dict[Path, str]:
  pins = {control.BASE: control.BASE_SHA256, control.HELPER: control.HELPER_SHA256,
          prior.CONTROL: prior.CONTROL_SHA256, ASSEMBLY: ASSEMBLY_SHA256,
          STOCK_DWC: STOCK_DWC_SHA256, STOCK_ATC: STOCK_ATC_SHA256}
  for directory, entries in (("index-inputs", control.INDEX_INPUTS), ("proofs", prior.PROOFS)):
    pins.update({Path("/inputs") / directory / name: digest for name, digest in entries.items()})
  return pins


def archive_delta(before: Archive, after: Archive, replacements: dict[str, bytes],
                  added: bytes) -> list[dict[str, object]]:
  require(type(added) is bytes and sha256(added) == STOCK_DWC_SHA256, "unapproved packaged DWC payload")
  expected_replacements = {PREFIX + name for name in CHANGED_INDEXES}
  require(set(replacements) == expected_replacements, "unapproved archive replacement set")
  require(tuple(member.name for member in after.members) ==
          tuple(member.name for member in before.members) + (PREFIX + DWC,), "archive membership/order differs")
  require(before.tail == after.tail, "trailer or zero tail changed")
  changes: list[dict[str, object]] = []
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
  require(replace_members(early, {}, ()) == early.raw and replace_members(original, {}, ()) == original.raw,
          "no-change archive transformation differs")
  original_modules = control.select_modules(original)
  modules = {str(module.relative): module.member.payload for module in original_modules}
  names = {module.name: str(module.relative) for module in original_modules}
  indexes = control.select_indexes(original)
  proofs = {name: data[Path("/inputs/proofs") / name] for name in prior.PROOFS}
  inputs = {name: data[Path("/inputs/index-inputs") / name] for name in control.INDEX_INPUTS}
  prior.validate_control_proof(prior.json_object(proofs["control-result.json"]))
  prior.validate_index_proof(prior.json_object(proofs["index-control.json"]), indexes)
  builtins = control.builtin_names(inputs["modules.builtin"])
  baseline = prior.validate_lookup_proof(prior.json_object(proofs["binary-lookup.json"]), names, builtins)
  require({ATC, TIPD, DWC_CORE} <= set(modules) and DWC not in modules, "base module placement differs")
  require(modules[ATC] == data[STOCK_ATC], "working-image ATC is not the exact packaged module")
  tipd, atc, dwc = modules[TIPD], modules[ATC], data[STOCK_DWC]
  original_hashes = {name: sha256(raw) for name, raw in modules.items()}
  modules[DWC] = dwc
  names["dwc3_apple"] = DWC
  require(len(modules) == len(names) == 200, "candidate module identities are ambiguous")
  control.save_json("e-assembly-inputs.json", {str(path): digest for path, digest in pins.items()})
  write_new(control.EMPTY_CONFIG, b"")
  config_identity = control.file_identity(control.EMPTY_CONFIG.lstat())
  commands = control.Commands()
  unchanged = commands.run(("/usr/bin/gzip",), payload=original.raw, output_bound=MAX_ARCHIVE_BYTES)
  no_change = early.raw + unchanged
  control.save_json("e-no-change.json", {
    "verdict": "PASS" if no_change == base else "STOP", "base_sha256": control.BASE_SHA256,
    "reconstructed_sha256": sha256(no_change), "byte_identical": no_change == base,
  })
  require(no_change == base, "fresh GNU gzip no-change reconstruction differs")
  # Reuse the exact validators, including strict generated-symbol/dump pins.
  # A different E result stops here with the real scratch outputs preserved.
  candidate_indexes, generated_state = prior.generate_indexes(modules, indexes, inputs, proofs,
                                                               commands, config_identity)
  prior.binary_lookup(modules, candidate_indexes, names, baseline, builtins, proofs, commands, config_identity)
  require(all(sha256(modules[name]) == digest for name, digest in original_hashes.items()),
          "original module bytes changed")
  replacements = {PREFIX + name: candidate_indexes[name] for name in CHANGED_INDEXES}
  main_raw = replace_members(original, replacements, ((PREFIX + DWC, dwc),))
  candidate_main = parse_newc(main_raw)
  changes = archive_delta(original, candidate_main, replacements, dwc)
  # The legacy parameter name is "diagnostics"; these expected bytes are stock
  # DWC and unchanged original ATC. No diagnostic module input is used for E.
  prior.independent_archive_checks(early, candidate_main,
                                   {"phy-apple-atc.ko": atc, "dwc3-apple.ko": dwc}, tipd, commands)
  compressed = commands.run(("/usr/bin/gzip",), payload=main_raw, output_bound=MAX_ARCHIVE_BYTES)
  require(prior.single_gzip(compressed, len(main_raw)) == main_raw, "E gzip roundtrip differs")
  candidate = early.raw + compressed
  require(len(candidate) <= MAX_ARCHIVE_BYTES, "candidate image exceeds bound")
  require(control.snapshot(control.CONTROL_ROOT) == generated_state, "generated root changed after checks")
  prior.verify_empty_config(config_identity)
  for path, digest in pins.items():
    read_regular(path, digest)
  write_new(CANDIDATE, candidate)
  readback = read_regular(CANDIDATE, sha256(candidate))
  require(readback == candidate and readback[:control.MAIN_OFFSET] == early.raw, "E readback differs")
  reread_main = parse_newc(prior.single_gzip(readback[control.MAIN_OFFSET:], len(main_raw)))
  require(archive_delta(original, reread_main, replacements, dwc) == changes, "E readback delta differs")
  prior.verify_empty_config(config_identity)
  for path, digest in pins.items():
    read_regular(path, digest)
  control.save_json("e-image-delta.json", {
    "verdict": "PASS", "base_sha256": control.BASE_SHA256, "candidate_sha256": sha256(readback),
    "early_raw_sha256": sha256(early.raw), "early_records": 7, "original_main_records": 1162,
    "candidate_main_records": len(reread_main.members), "unchanged_main_raw_records": 1160,
    "tail_preserved": True, "changes": changes, "original_module_hashes": original_hashes,
    "atc_sha256_unchanged": sha256(atc), "tipd_sha256_unchanged": sha256(tipd),
  })
  report = {
    "level": "info", "check": "private_e_candidate", "verdict": "PASS", "image_class": "E",
    "candidate": str(CANDIDATE), "candidate_sha256": sha256(readback), "candidate_bytes": len(readback),
    "modules": 200, "original_modules_unchanged": 199, "retained_indexes": 7, "commands": commands.count,
    "all_immutable_inputs_preserved": True, "prior_control_reused": True, "fresh_no_change_bytes": True,
    "independent_stdout_only_module_checks": 3, "binary_only_lookup": True,
    "old_dependency_results_unchanged": 199, "roots_retained": [str(control.CONTROL_ROOT), str(control.LOOKUP_ROOT)],
    "general_archive_extracted": False, "staged": False, "module_loaded": False,
    "rebooted": False, "boot_tested": False, "diagnostic_modules_used": False,
  }
  control.save_json(RESULT.name, report)
  print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
  main()
