"""Synthetic delta failures plus pinned proof checks; never call assembly main.

These fixtures were authored after the implementation draft. They are not
evidence of a test-first RED phase. Run only in the same reviewed sandbox with
the documented source/proof mounts. No fixture creates a candidate image.
"""

from copy import deepcopy
import json
from pathlib import Path
import stat
import unittest
import zlib

import prepare_image as subject
from cpio_image import Archive, parse_newc, read_regular, replace_members


UDC = "kernel/drivers/usb/gadget/udc/udc-core.ko"
NAMES = {"dwc3": subject.DWC_CORE, "udc_core": UDC, "phy_apple_atc": subject.ATC}
OLD_DEPS = {subject.DWC_CORE: (UDC,), UDC: (), subject.ATC: ()}
BASE_ALIASES = subject.ALIASES_HEADER + b"alias of:N*T*Cfixture,base phy_apple_atc\n"
NEW_ALIASES = BASE_ALIASES + ("\n".join(subject.DWC_ALIASES) + "\n").encode("ascii")
SYMBOLS = subject.SYMBOLS_HEADER + b"alias symbol:fixture_symbol phy_apple_atc\n"
SOFTDEPS = subject.SOFTDEP_HEADER + b"softdep lrw pre: ecb\n"


def dependencies(entries: dict[str, tuple[str, ...]]) -> bytes:
  return "".join(name + ":" + (" " + " ".join(values) if values else "") + "\n"
                 for name, values in entries.items()).encode("ascii")


def lookup_entry(name: str, paths: list[str]) -> dict[str, object]:
  return {"module": name, "filename": subject.lookup_filename(NAMES[name]),
          "insmod": [subject.lookup_filename(path) for path in paths], "builtin": []}


def lookup_entries() -> dict[str, dict[str, object]]:
  return {"dwc3": lookup_entry("dwc3", [UDC, subject.DWC_CORE]),
          "udc_core": lookup_entry("udc_core", [UDC]),
          "phy_apple_atc": lookup_entry("phy_apple_atc", [subject.ATC])}


def candidate_lookup() -> dict[str, dict[str, object]]:
  entries = lookup_entries()
  target = subject.lookup_filename(subject.DWC)
  entries["dwc3_apple"] = {"module": "dwc3_apple", "filename": target,
                           "insmod": entries["dwc3"]["insmod"] + [target], "builtin": []}
  return entries


def record(name: str, payload: bytes = b"", *, inode: int = 1,
           mode: int = stat.S_IFREG | 0o644, links: int = 0) -> bytes:
  encoded = name.encode("ascii") + b"\0"
  fields = (inode, mode, 0, 0, links, 1234, len(payload), 0, 0, 0, 0, len(encoded), 0)
  raw = b"070701" + b"".join(f"{value:08x}".encode("ascii") for value in fields) + encoded
  return raw + b"\0" * (-len(raw) % 4) + payload + b"\0" * (-len(payload) % 4)


def fixture_archive() -> Archive:
  files = {subject.PREFIX + subject.ATC: b"old-atc", subject.PREFIX + subject.TIPD: b"keep-tipd",
           subject.PREFIX + subject.DWC_CORE: b"keep-dwc-core", "etc/fixture": b"keep-config",
           **{subject.PREFIX + name: ("old-" + name).encode("ascii") for name in subject.CHANGED_INDEXES}}
  parents = {str(parent) for name in files for parent in Path(name).parents if parent != Path(".")}
  records = [record(name + "/", inode=index, mode=stat.S_IFDIR | 0o755)
             for index, name in enumerate(sorted(parents, key=lambda name: (name.count("/"), name)), 1)]
  records.extend(record(name, raw, inode=index) for index, (name, raw) in enumerate(files.items(), len(records) + 1))
  records.append(record("lib", b"/usr/lib", inode=len(records) + 1, mode=stat.S_IFLNK | 0o777))
  raw = b"".join(records) + record("TRAILER!!!", mode=0, inode=0, links=1)
  return parse_newc(raw + b"\0" * (-len(raw) % 512))


def replacements() -> dict[str, bytes]:
  return {subject.PREFIX + subject.ATC: b"new-atc",
          **{subject.PREFIX + name: ("new-" + name).encode("ascii") for name in subject.CHANGED_INDEXES}}


def transformed(before: Archive) -> Archive:
  return parse_newc(replace_members(before, replacements(), ((subject.PREFIX + subject.DWC, b"new-dwc"),)))


def altered_field(archive: Archive, name: str, field: int, value: bytes) -> Archive:
  records: list[bytes] = []
  for member in archive.members:
    raw = member.raw
    if member.name == name:
      offset = 6 + field * 8
      raw = raw[:offset] + value + raw[offset + 8:]
    records.append(raw)
  return parse_newc(b"".join(records) + archive.tail)


class ProofTests(unittest.TestCase):
  def test_pinned_real_control_proof_is_accepted(self) -> None:
    raw = read_regular(Path("/inputs/proofs/control-result.json"), subject.PROOFS["control-result.json"])
    subject.validate_control_proof(subject.json_object(raw))

  def test_failed_changed_or_boolean_coerced_control_proof_is_rejected(self) -> None:
    raw = read_regular(Path("/inputs/proofs/control-result.json"), subject.PROOFS["control-result.json"])
    good = subject.json_object(raw)
    for key, value in (("verdict", "STOP"), ("commands", 405), ("base_sha256", "0" * 64),
                        ("module_loaded", True), ("binary_only_lookup", 1)):
      bad = deepcopy(good)
      bad[key] = value
      with self.subTest(key=key), self.assertRaises(RuntimeError):
        subject.validate_control_proof(bad)

  def test_duplicate_json_nonfinite_and_nonobject_proofs_are_rejected(self) -> None:
    for raw in (b'{"a":1,"a":2}', b'{"a":NaN}', b'[]'):
      with self.subTest(raw=raw), self.assertRaises(RuntimeError):
        subject.json_object(raw)

  def test_index_proof_binds_all_seven_payloads(self) -> None:
    indexes = {name: name.encode("ascii") for name in subject.control.INDEX_NAMES}
    proof = {"verdict": "PASS", "indexes": [
      {"name": name, "actual_sha256": subject.sha256(raw), "expected_sha256": subject.sha256(raw),
       "byte_identical": True} for name, raw in indexes.items()
    ]}
    subject.validate_index_proof(proof, indexes)
    for field, value in (("actual_sha256", "0" * 64), ("byte_identical", 1), ("name", "modules.dep")):
      bad = deepcopy(proof)
      bad["indexes"][0][field] = value
      with self.subTest(field=field), self.assertRaises(RuntimeError):
        subject.validate_index_proof(bad, indexes)

  def test_lookup_proof_requires_no_load_exact_paths_and_complete_coverage(self) -> None:
    entries = lookup_entries()
    proof = {"verdict": "PASS", "no_load": True, "text_index_fallback_available": False,
             "module_count": len(entries), "modules": list(entries.values())}
    self.assertEqual(subject.validate_lookup_proof(proof, NAMES, set()), entries)
    for key, value in (("no_load", False), ("text_index_fallback_available", True), ("module_count", True)):
      bad = deepcopy(proof)
      bad[key] = value
      with self.subTest(key=key), self.assertRaises(RuntimeError):
        subject.validate_lookup_proof(bad, NAMES, set())
    bad = deepcopy(proof)
    bad["modules"][0]["filename"] = "/lib/modules/host.ko"
    with self.assertRaises(RuntimeError):
      subject.validate_lookup_proof(bad, NAMES, set())
    bad = deepcopy(proof)
    bad["modules"][1] = bad["modules"][0]
    with self.assertRaises(RuntimeError):
      subject.validate_lookup_proof(bad, NAMES, set())


class IndexDeltaTests(unittest.TestCase):
  def test_only_new_dwc_closure_is_accepted(self) -> None:
    candidate = OLD_DEPS | {subject.DWC: (subject.DWC_CORE, UDC)}
    subject.validate_dependency_delta(dependencies(OLD_DEPS), dependencies(candidate), set(OLD_DEPS))

  def test_existing_dependency_change_or_reordering_is_rejected(self) -> None:
    candidate = OLD_DEPS | {subject.DWC: (subject.DWC_CORE, UDC), subject.ATC: (UDC,)}
    with self.assertRaises(RuntimeError):
      subject.validate_dependency_delta(dependencies(OLD_DEPS), dependencies(candidate), set(OLD_DEPS))
    baseline = OLD_DEPS | {subject.ATC: (UDC, subject.DWC_CORE)}
    candidate = baseline | {subject.DWC: (subject.DWC_CORE, UDC), subject.ATC: (subject.DWC_CORE, UDC)}
    with self.assertRaises(RuntimeError):
      subject.validate_dependency_delta(dependencies(baseline), dependencies(candidate), set(baseline))

  def test_missing_extra_self_or_duplicate_new_dependencies_are_rejected(self) -> None:
    for values in ((subject.DWC_CORE,), (subject.DWC_CORE, UDC, subject.ATC),
                   (subject.DWC_CORE, UDC, subject.DWC), (subject.DWC_CORE, UDC, UDC)):
      candidate = OLD_DEPS | {subject.DWC: values}
      with self.subTest(values=values), self.assertRaises(RuntimeError):
        subject.validate_dependency_delta(dependencies(OLD_DEPS), dependencies(candidate), set(OLD_DEPS))

  def test_dependency_duplicate_keys_unsafe_paths_and_bad_lines_are_rejected(self) -> None:
    raw = dependencies(OLD_DEPS)
    for bad in (raw + raw, raw[:-1], raw.replace(UDC.encode(), b"../escape.ko"),
                raw.replace(b": ", b":  "), raw + b"unknown.ko:\n"):
      with self.subTest(bad=bad[:80]), self.assertRaises(RuntimeError):
        subject.dependency_entries(bad, set(OLD_DEPS))

  def test_alias_delta_is_exact_base_plus_two_known_entries(self) -> None:
    subject.validate_alias_delta(BASE_ALIASES, NEW_ALIASES)

  def test_alias_removals_duplicates_wrong_targets_and_extra_entries_are_rejected(self) -> None:
    for bad in (NEW_ALIASES + b"alias unexpected extra\n", NEW_ALIASES + NEW_ALIASES[len(BASE_ALIASES):],
                NEW_ALIASES.replace(b"phy_apple_atc", b"other"),
                NEW_ALIASES.replace(b"dwc3_apple", b"other"), BASE_ALIASES):
      with self.subTest(bad=bad[:80]), self.assertRaises(RuntimeError):
        subject.validate_alias_delta(BASE_ALIASES, bad)

  def test_unrelated_indexes_symbols_and_weakdeps_must_be_byte_identical(self) -> None:
    before = {name: ("old-" + name).encode() for name in subject.control.INDEX_NAMES}
    after = before | {name: ("new-" + name).encode() for name in subject.CHANGED_INDEXES}
    subject.validate_static_indexes(before, after, SYMBOLS, subject.WEAKDEP_HEADER, SYMBOLS)
    for name in subject.STATIC_INDEXES:
      bad = after | {name: b"drift"}
      with self.subTest(name=name), self.assertRaises(RuntimeError):
        subject.validate_static_indexes(before, bad, SYMBOLS, subject.WEAKDEP_HEADER, SYMBOLS)
    for symbols, weakdeps in ((SYMBOLS + b"extra\n", subject.WEAKDEP_HEADER),
                              (SYMBOLS, subject.WEAKDEP_HEADER + b"weakdep dwc3_apple extra\n")):
      with self.subTest(weakdeps=weakdeps), self.assertRaises(RuntimeError):
        subject.validate_static_indexes(before, after, symbols, weakdeps, SYMBOLS)

  def test_unchanged_necessary_binary_index_and_extra_index_are_rejected(self) -> None:
    before = {name: name.encode() for name in subject.control.INDEX_NAMES}
    for after in (before, before | {"modules.dep": b"unexpected"}):
      with self.subTest(names=tuple(after)), self.assertRaises(RuntimeError):
        subject.validate_static_indexes(before, after, SYMBOLS, subject.WEAKDEP_HEADER, SYMBOLS)

  def binary_dump(self) -> bytes:
    # R3 fixture correction: kmod normalizes these two DWC binary alias keys.
    binary_aliases = NEW_ALIASES[len(subject.ALIASES_HEADER):].replace(b"t8103-dwc3", b"t8103_dwc3")
    return (SOFTDEPS[len(subject.SOFTDEP_HEADER):] + subject.CONFIG_SEPARATOR +
            binary_aliases + SYMBOLS[len(subject.SYMBOLS_HEADER):])

  def test_binary_dump_matches_all_alias_symbol_entries_and_only_expected_softdep(self) -> None:
    subject.validate_binary_dump(self.binary_dump(), NEW_ALIASES, SYMBOLS, SOFTDEPS)

  def test_binary_dump_rejects_install_options_alias_or_symbol_changes(self) -> None:
    good = self.binary_dump()
    for bad in (b"install dwc3_apple /bin/true\n" + good, b"options dwc3_apple arbitrary=1\n" + good,
                good + b"alias hidden unknown\n", good.replace(b"fixture_symbol", b"other_symbol"),
                good.replace(b"pre: ecb", b"pre: extra"), good + subject.CONFIG_SEPARATOR):
      with self.subTest(bad=bad[:80]), self.assertRaises(RuntimeError):
        subject.validate_binary_dump(bad, NEW_ALIASES, SYMBOLS, SOFTDEPS)


class LookupDeltaTests(unittest.TestCase):
  def test_candidate_adds_only_dwc_with_prior_core_closure(self) -> None:
    subject.validate_candidate_lookup(candidate_lookup(), lookup_entries())

  def test_changed_old_result_missing_new_target_and_wrong_order_are_rejected(self) -> None:
    bad = candidate_lookup()
    bad["phy_apple_atc"]["insmod"] = []
    with self.assertRaises(RuntimeError):
      subject.validate_candidate_lookup(bad, lookup_entries())
    for paths in ([subject.lookup_filename(subject.DWC)],
                   list(reversed(candidate_lookup()["dwc3_apple"]["insmod"]))):
      bad = candidate_lookup()
      bad["dwc3_apple"]["insmod"] = paths
      with self.subTest(paths=paths), self.assertRaises(RuntimeError):
        subject.validate_candidate_lookup(bad, lookup_entries())

  def test_dependency_output_accepts_only_known_no_load_descriptions(self) -> None:
    expected = lookup_entries()["dwc3"]
    raw = "".join("insmod " + path + "\n" for path in expected["insmod"]).encode("ascii")
    self.assertEqual(subject.dependency_output(raw, "dwc3", NAMES, set()), expected)
    for bad in (raw + b"install dwc3 /bin/true\n", raw + b"insmod /host/other.ko\n",
                raw + b"builtin unknown\n", raw + raw, raw.replace(b"\n", b" option=1\n")):
      with self.subTest(bad=bad[:80]), self.assertRaises(RuntimeError):
        subject.dependency_output(bad, "dwc3", NAMES, set())

  def test_each_constructed_modprobe_command_keeps_the_full_guard_set(self) -> None:
    for target in ("--show-config", "dwc3_apple", "of:Ndwc3T(null)Capple,t8103-dwc3"):
      command = subject.control.modprobe_command(target)
      self.assertEqual(command, ("/usr/bin/modprobe", "--dry-run", "--show-depends", "-d",
                                 "/work/lookup-root", "-S", subject.KERNEL, "-C",
                                 "/work/empty-modprobe.conf", target))


class ArchiveDeltaTests(unittest.TestCase):
  def setUp(self) -> None:
    self.before = fixture_archive()
    self.after = transformed(self.before)

  def validate(self, after: Archive) -> None:
    subject.archive_delta(self.before, after, replacements(), b"new-dwc")

  def test_exact_four_changes_preserve_zero_link_raw_records_and_absolute_symlink(self) -> None:
    changes = subject.archive_delta(self.before, self.after, replacements(), b"new-dwc")
    self.assertEqual(len(changes), 4)
    self.assertEqual(changes[-1]["name"], subject.PREFIX + subject.DWC)
    self.assertEqual(self.before.tail, self.after.tail)

  def test_unrelated_payload_or_tipd_change_is_rejected(self) -> None:
    for name in ("etc/fixture", subject.PREFIX + subject.TIPD):
      changed = parse_newc(replace_members(self.after, {name: b"drift"}, ()))
      with self.subTest(name=name), self.assertRaises(RuntimeError):
        self.validate(changed)

  def test_original_record_removal_reordering_or_extra_hook_is_rejected(self) -> None:
    records = [member.raw for member in self.after.members]
    for changed in (parse_newc(b"".join(records[1:]) + self.after.tail),
                    parse_newc(b"".join([records[1], records[0], *records[2:]]) + self.after.tail),
                    parse_newc(replace_members(self.after, {}, (("etc/preload-hook", b"no"),)))):
      with self.subTest(names=[member.name for member in changed.members]), self.assertRaises(RuntimeError):
        self.validate(changed)

  def test_replacement_metadata_and_literal_header_case_change_are_rejected(self) -> None:
    for field, value in ((2, b"00000001"), (4, b"00000001"), (5, b"00000000"), (1, b"000081A4")):
      changed = altered_field(self.after, subject.PREFIX + subject.ATC, field, value)
      with self.subTest(field=field), self.assertRaises(RuntimeError):
        self.validate(changed)

  def test_new_dwc_hardlink_mode_inode_owner_or_timestamp_is_rejected(self) -> None:
    for field, value in ((4, b"00000002"), (1, b"000081ff"), (0, b"00000001"),
                         (2, b"00000001"), (5, b"00000001")):
      changed = altered_field(self.after, subject.PREFIX + subject.DWC, field, value)
      with self.subTest(field=field), self.assertRaises(RuntimeError):
        self.validate(changed)

  def test_zero_tail_change_is_rejected(self) -> None:
    with self.assertRaises(RuntimeError):
      self.validate(parse_newc(self.after.raw + b"\0" * 512))

  def test_missing_change_or_unapproved_replacement_request_is_rejected(self) -> None:
    missing = parse_newc(replace_members(self.before, {}, ((subject.PREFIX + subject.DWC, b"new-dwc"),)))
    with self.assertRaises(RuntimeError):
      self.validate(missing)
    with self.assertRaises(RuntimeError):
      subject.archive_delta(self.before, self.after, replacements() | {"etc/fixture": b"no"}, b"new-dwc")

  def test_wrong_added_payload_is_rejected(self) -> None:
    with self.assertRaises(RuntimeError):
      subject.archive_delta(self.before, self.after, replacements(), b"wrong")


class CompressionAndBoundaryTests(unittest.TestCase):
  def test_single_gzip_roundtrip(self) -> None:
    raw = b"synthetic fixture" * 20
    compressed = zlib.compress(raw, wbits=31)
    self.assertEqual(subject.single_gzip(compressed, len(raw)), raw)

  def test_truncated_concatenated_trailing_or_oversized_gzip_is_rejected(self) -> None:
    raw = b"fixture" * 20
    compressed = zlib.compress(raw, wbits=31)
    for payload, bound in ((compressed[:-1], len(raw)), (compressed + compressed, len(raw)),
                            (compressed + b"\0", len(raw)), (compressed, len(raw) - 1),
                            (compressed, len(raw) + 1)):
      with self.subTest(bound=bound), self.assertRaises(RuntimeError):
        subject.single_gzip(payload, bound)

  def test_all_input_categories_are_pinned_and_outputs_are_private(self) -> None:
    pins = subject.pinned_inputs()
    self.assertEqual(len(pins), 14)
    self.assertTrue(all(str(path).startswith("/inputs/") for path in pins))
    self.assertTrue(all(len(digest) == 64 for digest in pins.values()))
    self.assertEqual(subject.CANDIDATE, Path("/work/initramfs-linux-asahi-dpalt-usbdiag1.img"))
    self.assertEqual(subject.RESULT, Path("/work/assembly-result.json"))
    self.assertFalse(subject.CANDIDATE.exists())
    self.assertFalse(subject.RESULT.exists())


if __name__ == "__main__":
  unittest.main()
