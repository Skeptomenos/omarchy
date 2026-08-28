"""Correction fixtures written before the alias normalization implementation.

Use a fresh R4 process with prepare_image imported before cpio_image. These
checks do not call assembly main, launch tools, or create a candidate image.
"""

import unittest

import prepare_image as subject


MODULE = "fixture_driver"
SOFTDEPS = subject.SOFTDEP_HEADER + b"softdep lrw pre: ecb\n"


def aliases(*keys: str) -> bytes:
  return subject.ALIASES_HEADER + "".join(f"alias {key} {MODULE}\n" for key in keys).encode("ascii")


def symbols(key: str = "fixture_symbol") -> bytes:
  return subject.SYMBOLS_HEADER + f"alias symbol:{key} {MODULE}\n".encode("ascii")


def dump(keys: tuple[str, ...], *, symbol: str = "fixture_symbol", owner: str = MODULE) -> bytes:
  rows = "".join(f"alias {key} {owner}\n" for key in keys)
  rows += f"alias symbol:{symbol} {MODULE}\n"
  return SOFTDEPS[len(subject.SOFTDEP_HEADER):] + subject.CONFIG_SEPARATOR + rows.encode("ascii")


class AliasNormalizationTests(unittest.TestCase):
  def assert_invalid(self, value: object) -> None:
    with self.assertRaises(RuntimeError) as raised:
      subject.normalize_alias_key(value)
    self.assertNotIsInstance(raised.exception, NotImplementedError)

  def test_plain_keys_and_existing_underscores_are_unchanged(self) -> None:
    for value in ("platform:fixture_driver", "of:N*T*Cfixture,unit", "crypto:aes_generic"):
      with self.subTest(value=value):
        self.assertEqual(subject.normalize_alias_key(value), value)

  def test_only_outside_hyphens_become_underscores(self) -> None:
    for before, after in (("crypto:842-generic", "crypto:842_generic"),
                           ("of:N*T*Capple,t8103-dwc3C*", "of:N*T*Capple,t8103_dwc3C*"),
                           ("x--y", "x__y")):
      with self.subTest(before=before):
        self.assertEqual(subject.normalize_alias_key(before), after)

  def test_bracket_ranges_and_literal_inside_hyphens_are_preserved(self) -> None:
    for before, after in (("x-[a-z]-y", "x_[a-z]_y"), ("x-[-]-y", "x_[-]_y"),
                           ("x-[!-a]-y", "x_[!-a]_y"), ("x-[]-y", "x_[]_y")):
      with self.subTest(before=before):
        self.assertEqual(subject.normalize_alias_key(before), after)

  def test_first_closing_bracket_not_nested_bracket_parsing(self) -> None:
    for before, after in (("[[]-x", "[[]_x"), ("x-[[a-z]-y", "x_[[a-z]_y"),
                           ("[a[b-c]d-e", "[a[b-c]d_e")):
      with self.subTest(before=before):
        self.assertEqual(subject.normalize_alias_key(before), after)

  def test_backslashes_do_not_escape_normalization(self) -> None:
    for before, after in ((r"x\-y", r"x\_y"), (r"x\[a-z]-y", r"x\[a-z]_y")):
      with self.subTest(before=before):
        self.assertEqual(subject.normalize_alias_key(before), after)

  def test_stray_and_unterminated_brackets_are_rejected(self) -> None:
    for value in ("x]", "[", "[a-z", "[[a-z]]", "[[]]", "[]]-x"):
      with self.subTest(value=value):
        self.assert_invalid(value)

  def test_strict_ascii_nonempty_and_type_guards(self) -> None:
    for value in ("", "x y", "x\ty", "x\ny", "x\0y", "x\x7fy", "café", b"x-y", None, 3, True):
      with self.subTest(value=value):
        self.assert_invalid(value)

  def test_4095_byte_limit_does_not_copy_c_truncation_or_bracket_overrun(self) -> None:
    self.assertEqual(subject.normalize_alias_key("x" * 4095), "x" * 4095)
    self.assertEqual(subject.normalize_alias_key("[" + "x" * 4093 + "]"), "[" + "x" * 4093 + "]")
    self.assert_invalid("x" * 4096)
    self.assert_invalid("[" + "x" * 4094 + "]")


class BinaryAliasNormalizationTests(unittest.TestCase):
  def test_real_style_hyphenated_alias_matches_normalized_binary_key(self) -> None:
    subject.validate_binary_dump(dump(("crypto:842_generic",)), aliases("crypto:842-generic"),
                                  symbols(), SOFTDEPS)

  def test_binary_range_hyphens_must_remain_hyphens(self) -> None:
    expected = aliases("fixture:[a-z]-suffix")
    subject.validate_binary_dump(dump(("fixture:[a-z]_suffix",)), expected, symbols(), SOFTDEPS)
    with self.assertRaises(RuntimeError):
      subject.validate_binary_dump(dump(("fixture:[a_z]_suffix",)), expected, symbols(), SOFTDEPS)

  def test_normalization_collisions_preserve_multiplicity(self) -> None:
    expected = aliases("fixture:x-y", "fixture:x_y")
    subject.validate_binary_dump(dump(("fixture:x_y", "fixture:x_y")), expected, symbols(), SOFTDEPS)
    with self.assertRaises(RuntimeError):
      subject.validate_binary_dump(dump(("fixture:x_y",)), expected, symbols(), SOFTDEPS)

  def test_symbol_keys_are_not_alias_normalized(self) -> None:
    expected_aliases = aliases("fixture:x-y")
    expected_symbols = symbols("export-with-hyphen")
    subject.validate_binary_dump(dump(("fixture:x_y",), symbol="export-with-hyphen"),
                                  expected_aliases, expected_symbols, SOFTDEPS)
    with self.assertRaises(RuntimeError):
      subject.validate_binary_dump(dump(("fixture:x_y",), symbol="export_with_hyphen"),
                                    expected_aliases, expected_symbols, SOFTDEPS)

  def test_target_module_names_cannot_be_rewritten_or_changed(self) -> None:
    with self.assertRaises(RuntimeError):
      subject.validate_binary_dump(dump(("fixture:x_y",), owner="fixture-driver"),
                                    aliases("fixture:x-y"), symbols(), SOFTDEPS)

  def test_text_alias_delta_still_compares_original_not_normalized_spelling(self) -> None:
    before = aliases("fixture:x-y")
    additions = ("\n".join(subject.DWC_ALIASES) + "\n").encode("ascii")
    subject.validate_alias_delta(before, before + additions)
    with self.assertRaises(RuntimeError):
      subject.validate_alias_delta(before, aliases("fixture:x_y") + additions)


if __name__ == "__main__":
  unittest.main()
