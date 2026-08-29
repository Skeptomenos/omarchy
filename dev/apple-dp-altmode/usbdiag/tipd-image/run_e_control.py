"""Pure boundaries for a new, fixed E-only no-change control.

The runner authenticates the pure dependency chain before importing this
module. Historical C2 index bytes are test inputs only, never a completed
fresh-control proof. These functions read no file and launch no command.

Operational control and T1 assembly remain unavailable at this checkpoint.
"""

from dataclasses import dataclass
import hashlib
from pathlib import Path
import re
from typing import NoReturn

from cpio_image import Archive, parse_newc
from prepare_image import (
  ALIASES_HEADER, SYMBOLS_HEADER, WEAKDEP_HEADER, alias_entries,
  dependency_entries, single_gzip, validate_binary_dump,
)
from verify_control import Module, module_name, regular_member, select_indexes


KERNEL = "7.1.6-1-1-ARCH"
PREFIX = f"usr/lib/modules/{KERNEL}/"
E_SHA256 = "4d4f0557af57eebcc33322f004bcc7968254e644b069a11102375df0b31a52ae"
E_BYTES = 19191513
EARLY_SHA256 = "967bc6adcff42e59abcfb4e509f6c80fd65588e0861d8c1c3189a135f10955b4"
MAIN_SHA256 = "7be7b4b03367b5ce4b356fe35977edba6540af0a7df930dbff990286c9b98e28"
EARLY_BYTES = 10240
MAIN_BYTES = 61286668
PAYLOAD_SHA256 = {
  PREFIX + "kernel/drivers/usb/typec/tipd/tps6598x-core.ko":
    "bc02723db427639c6586d29eea7918e084874c741b60bf145585c6349fd07d70",
  PREFIX + "kernel/drivers/usb/typec/tipd/tps6598x.ko":
    "f9b9e0f01270016b72cf242178eeb2810e32888e2cd6e68cf0d6f549500e1308",
  PREFIX + "kernel/drivers/phy/apple/phy-apple-atc.ko":
    "fd1c3d105bd69a649a38e89e2ca0bcbe6f656200a0f211d58211e8c7b3ec944b",
  PREFIX + "kernel/drivers/usb/dwc3/dwc3-apple.ko":
    "d150400f9782c876972b2745d95617cd44e23574452f63980704911a467f7767",
}
INDEX_SHA256 = {
  "modules.alias.bin": "ca6ca7be95509eb294c2e67090bfa84dcbab855fb0489e504804593a257c4ea9",
  "modules.builtin.alias.bin": "9635eaa0d8c3d2f89c98789adce44dfd047f8cb11c7c9d0aa60199defc2ad962",
  "modules.builtin.bin": "edf2e707c121431f4f77b842ffd0a37fad5c0a6df198296fd6ef0b7f3227ac74",
  "modules.dep.bin": "436095f4779ccbd9f0c44b90febef13b62be50c9518dd499c151843fdf1feb3d",
  "modules.devname": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "modules.softdep": "6a8f2009d87deba7a2de46e3d0c46b114fe388d188b00b9a382fc2156aabb676",
  "modules.symbols.bin": "a3f1e745b7675daaec99c7c7ebadc7d67b318143901e063674494c210b12ace6",
}
GENERATED_SHA256 = {
  **INDEX_SHA256,
  "modules.symbols.bin": "5077fb001a5c48a2135ce8f651606b18578610bc660f430a59114e76be4f9437",
  "modules.alias": "9ea85f8fd754e394a63c6de9a93f9d8445ad3ebaf3d75eb8101a460dcf4127ac",
  "modules.dep": "48b6e5f5befe58918639ae27e3271984629ade44d7de8f46fa46e92c7b9150fe",
  "modules.symbols": "91299d9a80705a17c92068869293aa32c86985f751a5e6ea84024cb511ca539a",
  "modules.weakdep": "a1fffe1059d8150b5d402b3f284f507025a8d4b5881810cb17b3fda8b8ab9304",
}
DUMP_SHA256 = "c562726938a6e3d11d5b3661352508f00b74efd9cbadbb559c3680663da72c05"
INDEX_INPUT_SHA256 = {
  "modules.order": "497c8546d3131d01191f7a66b68047abce5e5235ae982890180007f55c51a927",
  "modules.builtin": "74de5bab05fe70496f7702d83974adf8816ea826f1d8579f3b3f4b28a3890d2b",
  "modules.builtin.modinfo": "702d4cabaa9bdc1b282d0e419ba091f64dc06ba737fe7319928bb3003adeea4b",
}
ALIASES = (
  "of:Nusb-pdT(null)Capple,cd321x", "of:Ndwc3T(null)Capple,t8103-dwc3",
  "of:Natc-phyT(null)Capple,t8103-atcphy",
)
EXPORTS = (
  "tipd_sn201202x_data", "tps6598x_regmap_config", "tipd_init", "tipd_cd321x_data",
  "tipd_tps6598x_data", "tipd_tps25750_data", "tipd_remove", "tipd_suspend", "tipd_resume",
)
CONTROL_ROOT = "/work/control-root"
LOOKUP_ROOT = "/work/lookup-root"
EMPTY_CONFIG = "/work/empty-modprobe.conf"
EARLY_PATH = "/work/e-early.cpio"
MAIN_PATH = "/work/e-main.cpio"
MAX_INDEX_BYTES = 64 * 1024 * 1024
MODULE_MODEL_SHA256 = "eee8ad06a36c1537d53e0c416db998110d10638076a32bdd3fc8987f65b54bff"


class RecipeError(RuntimeError):
  """A fixed E-control boundary failed; it is not a hardware verdict."""


@dataclass(frozen=True)
class ESelection:
  early: Archive
  main: Archive
  modules: tuple[Module, ...]
  indexes: dict[str, bytes]


@dataclass(frozen=True)
class Regeneration:
  dependencies: dict[str, tuple[str, ...]]
  alias_mappings: int
  symbol_mappings: int
  retained_symbol_sha256: str
  generated_symbol_sha256: str


def _require(condition: bool, code: str) -> None:
  if not condition:
    raise RecipeError(code)


def _sha256(raw: bytes) -> str:
  return hashlib.sha256(raw).hexdigest()


def _validated_names(value: dict[str, str]) -> dict[str, str]:
  _require(type(value) is dict and len(value) == 200, "E_MODULE_MODEL")
  _require(all(
    type(name) is str and re.fullmatch(r"[A-Za-z0-9_]{1,128}", name) is not None
    and type(relative) is str and re.fullmatch(
      r"kernel/(?:[A-Za-z0-9_-]+/)*[A-Za-z0-9_][A-Za-z0-9_-]*\.ko", relative,
    ) is not None
    for name, relative in value.items()
  ), "E_MODULE_MODEL")
  try:
    _require(all(module_name(Path(relative).name) == name for name, relative in value.items()),
             "E_MODULE_MODEL")
  except (RuntimeError, ValueError, TypeError):
    raise RecipeError("E_MODULE_MODEL") from None
  _require(len(set(value.values())) == 200, "E_MODULE_MODEL")
  serialized = "".join(f"{name}={value[name]}\n" for name in sorted(value)).encode("ascii")
  _require(_sha256(serialized) == MODULE_MODEL_SHA256, "E_MODULE_MODEL")
  expected = {
    module_name(Path(path).name): path.removeprefix(PREFIX)
    for path in PAYLOAD_SHA256
  }
  _require(all(value.get(name) == relative for name, relative in expected.items()) and
           "lrw" in value, "E_MODULE_MODEL")
  return dict(value)


def select_e(base: bytes) -> ESelection:
  """Select the one authenticated E image without using the old W selector."""
  _require(type(base) is bytes and len(base) == E_BYTES and _sha256(base) == E_SHA256,
           "E_BASE_IDENTITY")
  try:
    early = parse_newc(base[:EARLY_BYTES])
    main_raw = single_gzip(base[EARLY_BYTES:], MAIN_BYTES)
    main = parse_newc(main_raw)
  except (RuntimeError, ValueError, KeyError, TypeError):
    raise RecipeError("E_ARCHIVE_MODEL") from None
  _require(
    len(early.members) == 7 and len(early.raw) == EARLY_BYTES
    and _sha256(early.raw) == EARLY_SHA256
    and len(main.members) == 1163 and len(main.raw) == MAIN_BYTES
    and _sha256(main.raw) == MAIN_SHA256,
    "E_ARCHIVE_MODEL",
  )
  _require(all(
    b"".join(member.raw for member in archive.members) + archive.tail == archive.raw
    for archive in (early, main)
  ), "E_ARCHIVE_MODEL")

  modules: list[Module] = []
  names: set[str] = set()
  try:
    for member in main.members:
      filename = Path(member.name).name
      if re.search(r"\.ko(?:\.|$)", filename) is None:
        continue
      _require(member.name.startswith(PREFIX + "kernel/") and member.name.endswith(".ko"),
               "E_MODULE_MODEL")
      regular_member(member)
      relative = Path(member.name.removeprefix(PREFIX))
      _require(relative.parts[0] == "kernel" and not any(
        part in ("", ".", "..") or any(char.isspace() for char in part)
        for part in relative.parts
      ), "E_MODULE_MODEL")
      name = module_name(filename)
      _require(name not in names, "E_MODULE_MODEL")
      names.add(name)
      modules.append(Module(name, relative, member))
  except (RuntimeError, ValueError, KeyError, TypeError, IndexError):
    raise RecipeError("E_MODULE_MODEL") from None
  _require(len(modules) == len(names) == 200, "E_MODULE_MODEL")
  by_path = {member.name: member for member in main.members}
  _require(all(path in by_path and _sha256(by_path[path].payload) == digest
               for path, digest in PAYLOAD_SHA256.items()), "E_MODULE_MODEL")
  _validated_names({module.name: str(module.relative) for module in modules})

  try:
    indexes = select_indexes(main)
  except (RuntimeError, ValueError, KeyError, TypeError):
    raise RecipeError("E_INDEX_SET") from None
  _require({name: _sha256(raw) for name, raw in indexes.items()} == INDEX_SHA256,
           "E_INDEX_IDENTITY")
  return ESelection(early, main, tuple(modules), dict(indexes))


def validate_regeneration(
  original: dict[str, bytes],
  generated: dict[str, bytes],
  dump: bytes,
  names: dict[str, str],
) -> Regeneration:
  """Validate exact fresh depmod outputs and the one symbol-bin exception."""
  _require(type(original) is dict and len(original) == len(INDEX_SHA256)
           and set(original) == set(INDEX_SHA256)
           and type(generated) is dict and len(generated) == len(GENERATED_SHA256)
           and set(generated) == set(GENERATED_SHA256), "E_INDEX_SET")
  _require(all(type(name) is str and type(raw) is bytes for name, raw in original.items())
           and all(type(name) is str and type(raw) is bytes for name, raw in generated.items())
           and sum(map(len, original.values())) <= MAX_INDEX_BYTES
           and sum(map(len, generated.values())) <= MAX_INDEX_BYTES, "E_INDEX_TYPE")
  _require({name: _sha256(raw) for name, raw in original.items()} == INDEX_SHA256,
           "E_INDEX_IDENTITY")
  _require({name: _sha256(raw) for name, raw in generated.items()} == GENERATED_SHA256,
           "E_GENERATED_IDENTITY")
  _require(type(dump) is bytes and len(dump) <= MAX_INDEX_BYTES and _sha256(dump) == DUMP_SHA256,
           "E_DUMP_IDENTITY")
  model = _validated_names(names)
  _require(all(generated[name] == original[name] for name in INDEX_SHA256
               if name != "modules.symbols.bin")
           and generated["modules.symbols.bin"] != original["modules.symbols.bin"],
           "E_GENERATED_IDENTITY")
  try:
    dependencies = dependency_entries(generated["modules.dep"], set(model.values()))
    aliases = alias_entries(generated["modules.alias"], ALIASES_HEADER)
    symbols = alias_entries(generated["modules.symbols"], SYMBOLS_HEADER)
    _require(generated["modules.weakdep"] == WEAKDEP_HEADER, "E_GENERATED_FORMAT")
    validate_binary_dump(dump, generated["modules.alias"], generated["modules.symbols"],
                         original["modules.softdep"])
  except RecipeError:
    raise
  except (RuntimeError, ValueError, KeyError, TypeError):
    raise RecipeError("E_GENERATED_FORMAT") from None
  _require(len(dependencies) == 200 and sum(aliases.values()) == 1408
           and sum(symbols.values()) == 596, "E_GENERATED_FORMAT")
  return Regeneration(
    dict(dependencies), 1408, 596, INDEX_SHA256["modules.symbols.bin"],
    GENERATED_SHA256["modules.symbols.bin"],
  )


def _probe(root: str, target: str) -> tuple[str, ...]:
  return (
    "/usr/bin/modprobe", "--dry-run", "--show-depends", "-d", root,
    "-S", KERNEL, "-C", EMPTY_CONFIG, target,
  )


def command_plan(names: dict[str, str]) -> tuple[tuple[str, ...], ...]:
  """Return the fixed read-only plan; this function launches no subprocess."""
  model = _validated_names(names)
  result: list[tuple[str, ...]] = []
  for path in (EARLY_PATH, MAIN_PATH):
    result.extend((
      ("/usr/bin/cpio", "--list", "--quiet", "--file", path),
      ("/usr/bin/bsdtar", "--list", "--file", path),
    ))
  result.append(("/usr/bin/gzip",))
  for path in PAYLOAD_SHA256:
    result.append((
      "/usr/bin/bsdtar", "--extract", "--to-stdout", "--file", MAIN_PATH, path,
    ))
  result.append(("/usr/bin/depmod", "-b", CONTROL_ROOT, KERNEL))
  result.extend((_probe(CONTROL_ROOT, "--show-config"), _probe(LOOKUP_ROOT, "--show-config")))
  for name in sorted(model):
    result.extend((
      ("/usr/bin/modinfo", "-b", LOOKUP_ROOT, "-k", KERNEL, "-F", "filename", name),
      _probe(LOOKUP_ROOT, name),
    ))
  result.extend(_probe(LOOKUP_ROOT, alias) for alias in ALIASES)
  result.extend(_probe(LOOKUP_ROOT, "symbol:" + symbol) for symbol in EXPORTS)
  _require(len(result) == 424, "E_COMMAND_PLAN")
  return tuple(result)


def main() -> NoReturn:
  """Neither a fixture nor a header can unlock an operational workload."""
  raise RecipeError("E_CONTROL_RECIPE_UNAVAILABLE")


if __name__ == "__main__":
  main()
