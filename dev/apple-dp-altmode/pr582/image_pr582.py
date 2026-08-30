"""Two private AppleDRM-only T1 images; never install, load, stage, or boot.

Run only in the accepted sandbox with fixed /inputs bindings. The frozen launcher
pins this source and all inputs. The manifest hash intentionally remains unbound
until independent build review supplies the matched module identities and closure.
Stdlib dataclasses replace Pydantic under the existing no-install exception.
"""

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
from types import ModuleType
import zlib


KERNEL = "7.1.6-1-1-ARCH"
PREFIX = f"usr/lib/modules/{KERNEL}/"
RELATIVE = "kernel/drivers/gpu/drm/apple/appledrm.ko"
TARGET = PREFIX + RELATIVE
SOURCE_COMMIT = "e2e1930a9595bffafad92cec2b5504525efb9cd4"
PATCH_COMMIT = "6b70d02bcb5758a625d8bcedbff340cf544a4496"
BASE_SHA256 = "c72c36736cebba0d6d5b67f47b02330c35d3ef81fed9bf5b3315095b0dd765fe"
BASE_BYTES = 19209545
EARLY_BYTES = 10240
EARLY_SHA256 = "967bc6adcff42e59abcfb4e509f6c80fd65588e0861d8c1c3189a135f10955b4"
MAIN_BYTES = 61400828
MAIN_SHA256 = "2be5aaa3fcd979aa8204e2c00e3e839f7da3e8ba54b1aac86c940e33a6b94a4f"
STOCK_SHA256 = "dbffe74e13a43e15e47fdc5eafe32eb1829b114a3f02f15fe6b18507d622b0e3"
INDEXES = {
  "modules.alias.bin": "ca6ca7be95509eb294c2e67090bfa84dcbab855fb0489e504804593a257c4ea9",
  "modules.builtin.alias.bin": "9635eaa0d8c3d2f89c98789adce44dfd047f8cb11c7c9d0aa60199defc2ad962",
  "modules.builtin.bin": "edf2e707c121431f4f77b842ffd0a37fad5c0a6df198296fd6ef0b7f3227ac74",
  "modules.dep.bin": "436095f4779ccbd9f0c44b90febef13b62be50c9518dd499c151843fdf1feb3d",
  "modules.devname": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "modules.softdep": "6a8f2009d87deba7a2de46e3d0c46b114fe388d188b00b9a382fc2156aabb676",
  "modules.symbols.bin": "a3f1e745b7675daaec99c7c7ebadc7d67b318143901e063674494c210b12ace6",
}
SOURCES = {
  Path("/inputs/assembly/prepare_image.py"): "00caceb3b7fa236dcc030fb4007d0baa75bfa08fcd1590626f85fcc8c22d5f60",
  Path("/inputs/control/verify_control.py"): "10b5afe6cff38df7b6ebe5619fd9a34935932a4b369f3a9ad2a51923c32932d8",
  Path("/inputs/helper/cpio_image.py"): "a32eddd159263d19ff87d7e9caee9d53d17ef5c350fbffe9e7eb142cb43ebf58",
}
MODULE_MANIFEST_SHA256: str | None = None


class ImageError(RuntimeError):
  """The bounded image contract was not satisfied; retain all partial outputs."""


def require(condition: bool, message: str) -> None:
  if not condition:
    raise ImageError(message)


def sha256(raw: bytes) -> str:
  return hashlib.sha256(raw).hexdigest()


def load_helpers() -> ModuleType:
  require(os.getuid() == os.geteuid() == os.getgid() == os.getegid() == 1001
          and Path.cwd() == Path("/work"), "reviewed offline sandbox required")
  require(sys.flags.isolated == 1 and sys.flags.no_site == 1 and sys.dont_write_bytecode,
          "isolated Python flags required")
  require(not any(Path(path).exists() for path in ("/proc", "/sys", "/home", "/run", "/boot")),
          "host tree visible")
  require(not any(name in sys.modules for name in ("prepare_image", "verify_control", "cpio_image")),
          "dependency already imported")
  loaded: dict[Path, bytes] = {}
  for path, digest in SOURCES.items():
    require(all(stat.S_ISDIR(parent.lstat().st_mode)
                for parent in (Path("/"), Path("/inputs"), path.parent)), "source parent is not real")
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1
            and 0 < before.st_size < 128 * 1024, "source is not bounded regular single-link")
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    with os.fdopen(descriptor, "rb") as stream:
      raw = stream.read(128 * 1024)
      states = (before, os.fstat(stream.fileno()), path.lstat())
    identities = {(item.st_dev, item.st_ino, item.st_mode, item.st_uid, item.st_gid,
                   item.st_nlink, item.st_size, item.st_mtime_ns, item.st_ctime_ns) for item in states}
    require(len(identities) == 1 and len(raw) == before.st_size and sha256(raw) == digest,
            "helper source drift")
    loaded[path] = raw
  path = Path("/inputs/assembly/prepare_image.py")
  module = ModuleType("prepare_image")
  module.__file__ = str(path)
  sys.modules[module.__name__] = module
  # Its reviewed top level authenticates control/cpio; no historical main runs.
  exec(compile(loaded[path], str(path), "exec"), module.__dict__)
  return module


assembly = load_helpers()
from cpio_image import Archive, parse_newc, read_regular, replace_members, write_new
from verify_control import Commands, select_indexes, snapshot


@dataclass(frozen=True)
class ModulePin:
  sha256: str
  size: int
  build_id: str


@dataclass(frozen=True)
class Manifest:
  control: ModulePin
  candidate: ModulePin
  depends: str
  closure: tuple[str, ...]


def manifest_binding(value: str | None) -> str:
  require(type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None,
          "module manifest remains unbound")
  return value


def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
  result: dict[str, object] = {}
  for key, value in pairs:
    require(key not in result, "duplicate manifest key")
    result[key] = value
  return result


def module_pin(value: object) -> ModulePin:
  require(type(value) is dict and set(value) == {"sha256", "bytes", "build_id"}, "module pin schema")
  digest, size, build_id = value["sha256"], value["bytes"], value["build_id"]
  require(type(digest) is str and re.fullmatch(r"[0-9a-f]{64}", digest) is not None
          and type(size) is int and 0 < size <= 64 * 1024 * 1024
          and type(build_id) is str and re.fullmatch(r"[0-9a-f]{40}", build_id) is not None,
          "invalid module identity")
  return ModulePin(digest, size, build_id)


def parse_manifest(raw: bytes) -> Manifest:
  require(type(raw) is bytes and 0 < len(raw) <= 16384, "manifest size")
  try:
    value = json.loads(raw, object_pairs_hook=unique_object)
  except (ValueError, UnicodeError, RecursionError):
    raise ImageError("manifest JSON") from None
  require(type(value) is dict and set(value) == {
    "schema", "source_commit", "patch_commit", "control", "candidate", "depends", "closure"},
    "manifest schema")
  require(value["schema"] == "dev147-pr582-images-v1" and value["source_commit"] == SOURCE_COMMIT
          and value["patch_commit"] == PATCH_COMMIT, "manifest source identity")
  control, candidate = module_pin(value["control"]), module_pin(value["candidate"])
  require(control.sha256 != candidate.sha256 and control.build_id != candidate.build_id,
          "control and candidate must differ")
  depends, closure = value["depends"], value["closure"]
  require(type(depends) is str and re.fullmatch(r"(?:[A-Za-z0-9_]+(?:,[A-Za-z0-9_]+)*)?", depends) is not None,
          "invalid depends")
  require(type(closure) is list and 1 <= len(closure) <= 200
          and all(type(path) is str and re.fullmatch(r"kernel/(?:[A-Za-z0-9_-]+/)*[A-Za-z0-9_-]+\.ko", path)
                  for path in closure), "invalid dependency closure")
  require(len(set(closure)) == len(closure) and closure[-1] == RELATIVE, "closure order or duplicate")
  return Manifest(control, candidate, depends, tuple(closure))


def archive_delta(before: bytes, after: bytes, module: bytes, allow_same: bool = False) -> int:
  original, changed = parse_newc(before), parse_newc(after)
  targets = [item for item in original.members if item.name == TARGET]
  require(len(targets) == 1, "missing AppleDRM target")
  require(allow_same or targets[0].payload != module, "unexpected unchanged target")
  require(changed.raw == replace_members(original, {TARGET: module}, ()), "not an AppleDRM-only replacement")
  require(select_indexes(original) == select_indexes(changed), "index delta")
  return int(targets[0].payload != module)


def check_closure(raw: bytes, root: Path, closure: tuple[str, ...]) -> None:
  expected = b"".join(f"insmod {root}/lib/modules/{KERNEL}/{path} \n".encode("ascii") for path in closure)
  require(raw == expected, "unexpected no-load dependency output")


def lookup_payloads(archive: Archive) -> dict[str, bytes]:
  modules: dict[str, bytes] = {}
  for member in archive.members:
    if ".ko" not in Path(member.name).name:
      continue
    require(member.name.startswith(PREFIX) and member.name.endswith(".ko")
            and stat.S_ISREG(member.fields[1]) and member.fields[4] in (0, 1), "invalid module member")
    relative = member.name.removeprefix(PREFIX)
    require(re.fullmatch(r"kernel/(?:[A-Za-z0-9_-]+/)*[A-Za-z0-9_-]+\.ko", relative) is not None,
            "invalid module placement")
    modules[relative] = member.payload
  require(len(modules) == 200 and RELATIVE in modules, "module membership differs")
  return {f"lib/modules/{KERNEL}/{path}": data for path, data in
          (modules | select_indexes(archive)).items()}


def materialize(root: Path, payloads: dict[str, bytes]) -> None:
  require(root in (Path("/work/control-lookup"), Path("/work/candidate-lookup")), "lookup root scope")
  root.mkdir(mode=0o700)
  for relative, payload in payloads.items():
    path = root / relative
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    write_new(path, payload)
  state = snapshot(root)
  require(set(state.files) == set(payloads) and all(
    state.files[name].sha256 == sha256(payload) for name, payload in payloads.items()), "lookup copy drift")


def main() -> None:
  manifest_sha = manifest_binding(MODULE_MANIFEST_SHA256)
  os.umask(0o077)
  base = read_regular(Path("/inputs/base"), BASE_SHA256)
  require(len(base) == BASE_BYTES and sha256(base[:EARLY_BYTES]) == EARLY_SHA256, "T1 base identity")
  main_raw = assembly.single_gzip(base[EARLY_BYTES:], MAIN_BYTES)
  require(sha256(main_raw) == MAIN_SHA256, "T1 main identity")
  early, original = parse_newc(base[:EARLY_BYTES]), parse_newc(main_raw)
  require(len(early.members) == 7 and len(original.members) == 1163, "T1 member counts")
  require({key: sha256(value) for key, value in select_indexes(original).items()} == INDEXES, "T1 index pins")
  require(sha256(next(item.payload for item in original.members if item.name == TARGET)) == STOCK_SHA256,
          "T1 AppleDRM identity")
  manifest_raw = read_regular(Path("/inputs/manifest"), manifest_sha)
  manifest = parse_manifest(manifest_raw)
  module_bytes = {label: read_regular(Path(f"/inputs/modules/{label}.ko"), pin.sha256)
                  for label, pin in (("control", manifest.control), ("candidate", manifest.candidate))}
  for label, pin in (("control", manifest.control), ("candidate", manifest.candidate)):
    require(len(module_bytes[label]) == pin.size, "module size")
  commands = Commands()
  require(base[:EARLY_BYTES] + commands.run(("/usr/bin/gzip", "-n"), payload=main_raw,
                                           output_bound=64 * 1024 * 1024) == base, "T1 no-change gzip differs")
  config = Path("/work/empty-modprobe.conf")
  write_new(config, b"")
  outputs: dict[str, object] = {}
  for label, pin in (("control", manifest.control), ("candidate", manifest.candidate)):
    module = module_bytes[label]
    transformed = replace_members(original, {TARGET: module}, ())
    changes = archive_delta(main_raw, transformed, module, label == "control")
    compressed = commands.run(("/usr/bin/gzip", "-n"), payload=transformed, output_bound=64 * 1024 * 1024)
    require(compressed[:10] == bytes.fromhex("1f8b0800000000000003")
            and assembly.single_gzip(compressed, len(transformed)) == transformed, "candidate gzip differs")
    image = base[:EARLY_BYTES] + compressed
    destination = Path(f"/work/initramfs-linux-asahi-dpalt-pr582-{label}.img")
    write_new(destination, image)
    readback = read_regular(destination, sha256(image))
    require(readback[:EARLY_BYTES] == early.raw, "early archive differs")
    actual_main = assembly.single_gzip(readback[EARLY_BYTES:], len(transformed))
    archive_delta(main_raw, actual_main, module, label == "control")
    root = Path(f"/work/{label}-lookup")
    payloads = lookup_payloads(parse_newc(actual_main))
    require(all(f"lib/modules/{KERNEL}/{path}" in payloads for path in manifest.closure), "closure member missing")
    materialize(root, payloads)
    initial = snapshot(root)
    note = commands.run(("/usr/bin/readelf", "-n", f"/inputs/modules/{label}.ko"), output_bound=65536)
    require(re.findall(rb"Build ID: ([0-9a-f]+)\n", note) == [pin.build_id.encode()], "module build ID")
    for field, expected in (("filename", str(root / f"lib/modules/{KERNEL}/{RELATIVE}")),
                            ("name", "appledrm"), ("depends", manifest.depends)):
      actual = commands.run(("/usr/bin/modinfo", "-b", str(root), "-k", KERNEL, "-F", field, "appledrm"),
                            output_bound=65536)
      require(actual == (expected + "\n").encode(), "targeted module metadata differs")
    closure = commands.run(("/usr/bin/modprobe", "--dry-run", "--show-depends", "-d", str(root),
                            "-S", KERNEL, "-C", str(config), "appledrm"), output_bound=65536)
    check_closure(closure, root, manifest.closure)
    require(snapshot(root) == initial and read_regular(config) == b"", "lookup inputs changed")
    outputs[label] = {"name": destination.name, "sha256": sha256(readback), "bytes": len(readback),
                      "module_sha256": pin.sha256, "module_build_id": pin.build_id,
                      "changed_records": changes, "unchanged_other_records": 1162,
                      "unchanged_indexes": 7, "no_load_lookup": True}
  require(read_regular(Path("/inputs/base"), BASE_SHA256) == base
          and read_regular(Path("/inputs/manifest"), manifest_sha) == manifest_raw, "input changed")
  for path, digest in SOURCES.items():
    read_regular(path, digest)
  for label, pin in (("control", manifest.control), ("candidate", manifest.candidate)):
    require(read_regular(Path(f"/inputs/modules/{label}.ko"), pin.sha256) == module_bytes[label], "module changed")
    descriptor = outputs[label]
    image = read_regular(Path("/work") / descriptor["name"], descriptor["sha256"])
    require(len(image) == descriptor["bytes"], "published image changed")
  require(commands.count == 13, "unexpected child count")
  result = {"schema": "dev147-pr582-image-result-v1", "status": "PASS", "offline": True,
            "source_commit": SOURCE_COMMIT, "patch_commit": PATCH_COMMIT, "base_sha256": BASE_SHA256,
            "manifest_sha256": manifest_sha, "images": outputs, "children": commands.count,
            "staged": False, "module_loaded": False, "rebooted": False, "boot_tested": False}
  write_new(Path("/work/pr582-image-result.json"), (json.dumps(result, sort_keys=True, indent=2) + "\n").encode())
  print("PASS: private matched images verified; not staged or boot-tested")


if __name__ == "__main__":
  try:
    main()
  except (ImageError, OSError, ValueError, RuntimeError, zlib.error):
    print("INCOMPLETE: retained outputs are not accepted; stop for review", file=sys.stderr)
    raise SystemExit(1) from None
