"""Test-first retained-symbol selection with actual pinned review bytes.

The /inputs/index-review files contain only the two reviewed symbol binaries
and the generated stdout dump. Other index bytes are opaque unit fixtures;
these tests do not claim full-image validation or create any output image.
"""

from pathlib import Path
import unittest

import prepare_image as subject
from cpio_image import read_regular


class SymbolRetentionTests(unittest.TestCase):
  def setUp(self) -> None:
    root = Path("/inputs/index-review")
    original = read_regular(root / "base-symbols.bin", subject.BASE_SYMBOLS_SHA256)
    generated = read_regular(root / "generated-symbols.bin", subject.GENERATED_SYMBOLS_SHA256)
    self.dump = read_regular(root / "generated-dump.txt", subject.GENERATED_DUMP_SHA256)
    self.symbols = read_regular(Path("/inputs/proofs/modules.symbols"), subject.PROOFS["modules.symbols"])
    aliases = read_regular(Path("/inputs/proofs/modules.alias"), subject.PROOFS["modules.alias"])
    self.aliases = aliases + ("\n".join(subject.DWC_ALIASES) + "\n").encode("ascii")
    self.before = {name: ("original-" + name).encode("ascii") for name in subject.control.INDEX_NAMES}
    self.before["modules.symbols.bin"] = original
    self.before["modules.softdep"] = subject.SOFTDEP_HEADER + b"softdep lrw pre: ecb\n"
    self.generated = self.before | {
      **{name: ("generated-" + name).encode("ascii") for name in subject.CHANGED_INDEXES},
      "modules.symbols.bin": generated,
    }

  def select(self, *, before: dict[str, bytes] | None = None,
             generated: dict[str, bytes] | None = None, **overrides: bytes) -> dict[str, bytes]:
    arguments = {"symbols": self.symbols, "weakdeps": subject.WEAKDEP_HEADER,
                 "expected_symbols": self.symbols, "generated_dump": self.dump,
                 "expected_aliases": self.aliases} | overrides
    return subject.select_image_indexes(self.before if before is None else before,
                                         self.generated if generated is None else generated, **arguments)

  def assert_invalid(self, *, before: dict[str, bytes] | None = None,
                     generated: dict[str, bytes] | None = None, **overrides: bytes) -> None:
    with self.assertRaises(RuntimeError) as raised:
      self.select(before=before, generated=generated, **overrides)
    self.assertNotIsInstance(raised.exception, NotImplementedError)

  def test_actual_reviewed_priority_drift_keeps_original_symbols_in_final_set(self) -> None:
    selected = self.select()
    self.assertEqual(set(selected), subject.control.INDEX_NAMES)
    self.assertNotEqual(self.before["modules.symbols.bin"], self.generated["modules.symbols.bin"])
    for name in subject.STATIC_INDEXES:
      self.assertEqual(selected[name], self.before[name])
    for name in subject.CHANGED_INDEXES:
      self.assertEqual(selected[name], self.generated[name])

  def test_selection_is_a_new_mapping_and_does_not_overwrite_generated_bytes(self) -> None:
    before, generated = dict(self.before), dict(self.generated)
    selected = self.select()
    self.assertIsNot(selected, self.before)
    self.assertIsNot(selected, self.generated)
    self.assertEqual(self.before, before)
    self.assertEqual(self.generated, generated)
    self.assertEqual(subject.sha256(self.generated["modules.symbols.bin"]), subject.GENERATED_SYMBOLS_SHA256)

  def test_original_symbol_pin_is_required(self) -> None:
    self.assert_invalid(before=self.before | {"modules.symbols.bin": self.before["modules.symbols.bin"] + b"\0"})

  def test_only_the_exact_reviewed_generated_symbol_pin_is_accepted(self) -> None:
    for bad in (self.before["modules.symbols.bin"], self.generated["modules.symbols.bin"] + b"\0", b""):
      with self.subTest(length=len(bad)):
        self.assert_invalid(generated=self.generated | {"modules.symbols.bin": bad})

  def test_generated_dump_pin_is_required_even_for_whitespace_or_extra_rows(self) -> None:
    for bad in (self.dump + b"\n", self.dump + b"alias symbol:extra fixture\n", b""):
      with self.subTest(length=len(bad)):
        self.assert_invalid(generated_dump=bad)

  def test_dump_must_bind_expected_alias_and_symbol_mappings(self) -> None:
    self.assert_invalid(expected_aliases=self.aliases + b"alias extra fixture\n")
    self.assert_invalid(symbols=self.symbols + b"alias symbol:extra fixture\n",
                        expected_symbols=self.symbols + b"alias symbol:extra fixture\n")

  def test_all_other_static_indexes_must_stay_byte_identical(self) -> None:
    for name in subject.STATIC_INDEXES - {"modules.symbols.bin"}:
      with self.subTest(name=name):
        self.assert_invalid(generated=self.generated | {name: b"unexpected"})

  def test_symbol_text_and_weak_dependency_content_remain_exact(self) -> None:
    self.assert_invalid(symbols=self.symbols + b"extra\n")
    self.assert_invalid(weakdeps=subject.WEAKDEP_HEADER + b"weakdep dwc3_apple extra\n")

  def test_missing_or_extra_indexes_are_rejected(self) -> None:
    for target in ("before", "generated"):
      original = self.before if target == "before" else self.generated
      for bad in ({name: raw for name, raw in original.items() if name != "modules.dep.bin"},
                   original | {"modules.dep": b"extra text index"}):
        with self.subTest(target=target, names=tuple(bad)):
          self.assert_invalid(**{target: bad})

  def test_both_necessary_binary_indexes_still_have_to_change(self) -> None:
    for name in subject.CHANGED_INDEXES:
      with self.subTest(name=name):
        self.assert_invalid(generated=self.generated | {name: self.before[name]})

  def test_existing_static_validator_is_not_relaxed(self) -> None:
    with self.assertRaises(RuntimeError):
      subject.validate_static_indexes(self.before, self.generated, self.symbols,
                                       subject.WEAKDEP_HEADER, self.symbols)


if __name__ == "__main__":
  unittest.main()
