"""Source-faithful OF target-gate tests, only inside the reviewed private sandbox.

The production gate, reservation, log macros, and first probe prefix are
byte-extracted after full input-pin checks. OF naming/path/compatibility logic
and dynamic get/put bodies are likewise extracted from the exact kernel.
The C template supplies only bounded metadata fixtures and bookkeeping.
These are userspace semantic tests, not kernel concurrency or hardware tests.

The frozen v1 runner established generation-zero RED before the source change.
These fixed v2 pins run the same target assertions against the correction.
Setup/compile/pin failures are never semantic RED. Strict trace validation is
separate; this harness does not import a trace or binary validator.
"""

from dataclasses import dataclass, field
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import stat
import subprocess
import unittest


PRODUCER_PINS: dict[str, tuple[str, str]] = {
  "dwc3": ("dwc3-apple.c", "247f8bbe481699e288dc9476a6b1143484b3b9dbf9b1aaab5d7f9ea8241e4de1"),
  "atc": ("atc.c", "352bfd35397e76a487176404a715f2388595f070b97ad2c657cdf08f0e439ac4"),
}
OF_PINS: dict[str, str] = {
  "base.c": "9ab60bed4e0d85ed147f13ce2e12652e0d52e679949d9dbed8e891e627dd2d94",
  "dynamic.c": "28676346fac59a9625c529a95d1b96a527698f907fb160418d4e1d1cf7c321a8",
  "property.c": "640e222c0ef04707eb7ab893717a57c266d43ef47cbab04bc45418927d57a0fb",
  "of.h": "8edbbe739df26f11e2eaf182b86b2b278583bb5927a5aaa0ba070e7321496d5f",
  "string.h": "f362d7eb69bbb57a8815fb54d6c2bfdd5e2e781e5ca587b0e0fef69f1ab4ce7c",
}
FDT_PINS: dict[str, str] = {
  "fdt.c": "cc8a838a16e904560042b61e37613c8d51a09d2c83bd43733c50bf97e9dcdaeb",
  "fdt_ro.c": "0a0c999a8192903b8c8129fe4c99becbe725330204eaf3f7a4783705d2d0507a",
  "fdt_sw.c": "e9d193f023880f4359c3ed9954d678b51a87b1d66b783318a9d69a8122378122",
  "fdt_rw.c": "6ef7b4f967b71fb39eb93e8a15f2fd2030394f9a5776c1227043a342bb0f91bd",
  "fdt_wip.c": "a26966b2d991b432473f5c7f6740a3db97ae51313da0ad9eba56048d56c06c73",
  "fdt_empty_tree.c": "f3cdbfa1bcc86cc841544fee5a16c2f66a4da86b1065eaadab9700addb858369",
  "fdt.h": "f1762a7e8de699e4c2dde3f39b2c1bee7380e8a13017036f7096b688efa059d4",
  "libfdt.h": "f590bcb2d4fd6bfdd95af31f90aa4967a7a5bef9e9953f01ffb3f587c782ba1b",
  "libfdt_env.h": "687b9e736f5e5b26812dc3e01609ba3a90c902442cd6f9446030a1f093a0f911",
  "libfdt_internal.h": "d1ce78803d05f85c7c277b3032596d9f3c0fe151c3bdf32c0701fdb6e3d581bf",
}
LINK_PINS: dict[str, str] = {
  "libgcc_s_asneeded.so": "10bc094393cfacd92e7683eff066803c7c5bfd51ac8ee8eb7b57847a4c9b3ebb",
  "libatomic_asneeded.so": "7006f9f3ea0a199cca99d3646c3a7ebd5aa0fea2d45894c205cdb6eab4b4a7de",
  "libatomic.so": "e4e026a2b4d66f9d57c08645dea91ae9d36ebcbea55b34cf2357f312a8682495",
  "libatomic.so.1": "e4e026a2b4d66f9d57c08645dea91ae9d36ebcbea55b34cf2357f312a8682495",
}
TEMPLATE_PIN = "1ab587b56f4bb0426db584cb45db654b170b5b34d610dd7afb2a4ca71f419670"
COMPONENTS = ("dwc3", "atc")
POSITIVE_CASES = ("front_target", "uppercase_board", "later_compatible_board")
NEGATIVE_CASES = (
  "wrong_board_j313", "soc_only_board", "board_suffix", "missing_compatible",
  "rear_port", "other_parent", "bridge_soc", "soc_unit", "soc_case",
  "foreign_same_path", "missing_target", "null_node", "null_root",
  "null_root_and_node", "null_node_missing_target", "leading_zero_address", "address_suffix",
  "name_prefix", "changed_address", "name_case",
)
SPECIAL_CASES = (
  "probe_retries", "reject_between_retries", "cap_via_probe", "interleaved_components",
)
CASE_NAMES = frozenset(POSITIVE_CASES + NEGATIVE_CASES + SPECIAL_CASES)
WORK = Path("/work")


class SetupError(RuntimeError):
  """A containment, extraction, dependency, or child failure, not semantic RED."""


def require(condition: bool, message: str) -> None:
  if not condition:
    raise SetupError(message)


def isolated() -> None:
  require(os.getuid() == 1001 and os.getgid() == 1001, "unexpected workload identity")
  require(Path.cwd() == WORK, "not in the private workload directory")
  require(not any(Path(path).exists() for path in (
    "/proc", "/sys", "/run", "/boot", "/home",
  )), "host tree visible")


def pinned_bytes(path: Path, digest: str) -> bytes:
  metadata = path.lstat()
  require(stat.S_ISREG(metadata.st_mode) and metadata.st_nlink == 1,
          f"input is not a single-link regular file: {path.name}")
  require(0 < metadata.st_size <= 256 * 1024, f"input size bound: {path.name}")
  raw = path.read_bytes()
  require(hashlib.sha256(raw).hexdigest() == digest, f"source pin drift: {path.name}")
  return raw


def unique_offset(source: str, marker: str) -> int:
  require(source.count(marker) == 1, f"missing/duplicate extraction anchor: {marker}")
  return source.index(marker)


def function(source: str, signature: str) -> str:
  """Keep an exact Linux-style function through its unindented closing brace."""
  begin = unique_offset(source, signature)
  end = source.find("\n}\n", begin)
  require(end > begin and "\n{\n" in source[begin:end], f"function boundary: {signature}")
  return source[begin:end + 3]


def macro(source: str, name: str) -> str:
  lines = source.splitlines(keepends=True)
  matches = [
    index for index, line in enumerate(lines)
    if re.match(rf"^#define {re.escape(name)}(?:\(|\s)", line)
  ]
  require(len(matches) == 1, f"macro boundary: {name}")
  begin = matches[0]
  end = begin
  while lines[end].endswith("\\\n"):
    end += 1
    require(end < len(lines), f"unterminated macro: {name}")
  return "".join(lines[begin:end + 1])


def of_fragments(sources: dict[str, str]) -> str:
  header = sources["of.h"]
  # Exclude the CONFIG_OF=n fallback with a unique pinned preprocessor boundary.
  enabled = header[:unique_offset(header, "\n#else /* CONFIG_OF */\n")]
  chunks = [
    function(sources["string.h"], "static inline const char *kbasename("),
    macro(header, "of_compat_cmp"),
    macro(header, "of_prop_cmp"),
    macro(header, "for_each_property_of_node"),
    function(enabled, "static inline const char *of_node_full_name("),
    function(enabled, "static inline struct device_node *of_find_node_by_path("),
    function(enabled, "static inline bool of_machine_is_compatible("),
    function(sources["dynamic.c"], "struct device_node *of_node_get("),
    function(sources["dynamic.c"], "void of_node_put("),
    function(sources["property.c"], "const char *of_prop_next_string("),
  ]
  base = sources["base.c"]
  for signature in (
    "static struct property *__of_find_property(",
    "const void *__of_get_property(",
    "bool of_node_name_eq(",
    "static bool __of_node_is_type(",
    "static int __of_device_is_compatible(",
    "int of_device_is_compatible(",
    "int of_device_compatible_match(",
    "bool of_machine_compatible_match(",
    "static struct device_node *__of_get_next_child(",
  ):
    chunks.append(function(base, signature))
  chunks.append(macro(base, "__for_each_child_of_node"))
  for signature in (
    "struct device_node *__of_find_node_by_path(",
    "struct device_node *__of_find_node_by_full_path(",
    "struct device_node *of_find_node_opts_by_path(",
  ):
    chunks.append(function(base, signature))
  return "\n".join(chunks)


def producer_fragments(component: str, source: str) -> str:
  require(component in COMPONENTS, "unknown component")
  upper = component.upper()
  begin = unique_offset(source, f"#define DEV147_{upper}_LIMIT 128\n")
  bool_macro = macro(source, f"DEV147_{upper}_BOOL")
  end = unique_offset(source, bool_macro) + len(bool_macro)
  require(end > begin, "producer block boundary")
  block = source[begin:end]
  require(block.count(f"static unsigned int dev147_{component}_new_generation(") == 1,
          "generation function excluded or duplicated")
  probe = "dwc3_apple_probe" if component == "dwc3" else "atcphy_probe"
  pointer = "appledwc" if component == "dwc3" else "atcphy"
  probe_begin = unique_offset(source, f"static int {probe}(struct platform_device *pdev)\n{{\n")
  allocation = f"\n\t{pointer} = devm_kzalloc(&pdev->dev, sizeof(*{pointer}), GFP_KERNEL);\n"
  probe_end = unique_offset(source, allocation)
  require(probe_end > probe_begin, "probe setup precedes entry")
  prefix = source[probe_begin:probe_end]
  declarations = (
    "\tstruct device *dev = &pdev->dev;\n\tstruct dwc3_apple *appledwc;\n"
    if component == "dwc3" else
    "\tstruct apple_atcphy *atcphy;\n\tstruct device *dev = &pdev->dev;\n"
  )
  log_arguments = 'dev147_generation, 0, "probe", "begin", ""' if component == "dwc3" else (
    'dev147_generation, "probe", "begin", ""'
  )
  expected_prefix = (
    f"static int {probe}(struct platform_device *pdev)\n{{\n"
    + declarations
    + "\tint ret;\n"
    + f"\tunsigned int dev147_generation = dev147_{component}_new_generation(dev);\n\n"
    + f"\tDEV147_{upper}_LOG({log_arguments});\n"
  )
  require(prefix == expected_prefix, "probe prefix drift; first marker must precede setup")
  # The original prefix is unchanged. This tail observes its generation only.
  tail = f"\n\t(void)&{pointer};\n\t(void)&ret;\n\treturn (int)dev147_generation;\n}}\n"
  return block + "\n" + prefix + tail


def child_limits() -> None:
  """Bound retained output even when a compiler or assertion fails."""
  _, hard = resource.getrlimit(resource.RLIMIT_FSIZE)
  limit = 512 * 1024 if hard == resource.RLIM_INFINITY else min(512 * 1024, hard)
  resource.setrlimit(resource.RLIMIT_FSIZE, (limit, limit))


def checked_run(command: list[str], label: str) -> bytes:
  require(re.fullmatch(r"[a-z0-9_-]{1,80}", label) is not None, "invalid child label")
  output = WORK / f"{label}.stdout"
  errors = WORK / f"{label}.stderr"
  timed_out = False
  return_code: int | None = None
  with output.open("xb") as stdout, errors.open("xb") as stderr:
    try:
      completed = subprocess.run(
        command, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
        check=False, timeout=30, preexec_fn=child_limits,
        env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C",
             "LD_LIBRARY_PATH": "/inputs/link-runtime"},
      )
      return_code = completed.returncode
    except subprocess.TimeoutExpired:
      timed_out = True
  with (WORK / f"{label}.result.json").open("x", encoding="ascii") as stream:
    json.dump({"command": command, "exit_code": return_code, "timed_out": timed_out},
              stream, sort_keys=True)
  require(not timed_out, f"child timeout: {label}")
  require(return_code == 0, f"child failed: {label}, code={return_code}")
  require(output.stat().st_size <= 512 * 1024 and errors.stat().st_size <= 512 * 1024,
          f"child output bound: {label}")
  require(errors.read_bytes() == b"", f"child stderr: {label}")
  return output.read_bytes()


def check_dynamic(path: str, label: str) -> None:
  raw = checked_run(["/usr/bin/readelf", "-d", path], label)
  needed = set(re.findall(rb"Shared library: \[([^]]+)\]", raw))
  require(needed <= {
    b"libc.so.6", b"libgcc_s.so.1", b"libatomic.so.1", b"ld-linux-aarch64.so.1",
  }, "unreviewed dynamic dependency")
  require(b"(RPATH)" not in raw and b"(RUNPATH)" not in raw, "dynamic search override")


def object_fields(value: object, expected: frozenset[str]) -> dict[str, object]:
  if not isinstance(value, dict):
    raise SetupError("expected JSON object")
  result: dict[str, object] = {}
  for key, item in value.items():
    if not isinstance(key, str):
      raise SetupError("non-string object key")
    result[key] = item
  require(result.keys() == expected, "unexpected JSON fields")
  return result


def integer(value: object) -> int:
  if type(value) is not int or not 0 <= value <= 100000:
    raise SetupError("invalid bounded integer")
  return value


def integer_tuple(value: object) -> tuple[int, ...]:
  if not isinstance(value, list) or not 0 < len(value) <= 132:
    raise SetupError("invalid counter list")
  return tuple(integer(item) for item in value)


def text_field(value: object) -> str:
  if not isinstance(value, str) or len(value) > 80 or not value.isascii():
    raise SetupError("invalid fixed-label string")
  return value


def unique_json_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
  result: dict[str, object] = {}
  for key, value in pairs:
    require(key not in result, "duplicate JSON field")
    result[key] = value
  return result


@dataclass(frozen=True)
class Marker:
  component: str
  revision: str
  event: str
  phase: str
  sequence: int
  generation: int
  attempt: int | None

  @classmethod
  def parse(cls, value: object, expected_component: str | None) -> "Marker":
    if not isinstance(value, dict):
      raise SetupError("expected marker object")
    component = text_field(value.get("component"))
    require(component in COMPONENTS and
            (expected_component is None or component == expected_component),
            "wrong marker component")
    fields = frozenset({
      "schema", "revision", "board", "component", "target", "seq", "generation",
      "event", "phase",
    } | ({"attempt"} if component == "dwc3" else set()))
    item = object_fields(value, fields)
    require(integer(item["schema"]) == 1 and item["board"] == "j413" and
            item["component"] == component and item["target"] == "front_lower",
            "wrong marker envelope")
    # This typed observation is not a trace/revision validator. Source pins are
    # exact; semantic RED assertions below never depend on rejecting a revision.
    return cls(
      component=component, revision=text_field(item["revision"]),
      event=text_field(item["event"]), phase=text_field(item["phase"]),
      sequence=integer(item["seq"]), generation=integer(item["generation"]),
      attempt=integer(item["attempt"]) if component == "dwc3" else None,
    )


@dataclass(frozen=True)
class Observation:
  component: str
  case: str
  node_leaf: str | None
  generations: tuple[int, ...]
  sequences: tuple[int, ...]
  reference_gets: int
  reference_puts: int
  live_references: int
  lock_depth: int
  records: tuple[Marker, ...]

  @classmethod
  def parse(cls, raw: bytes, component: str, case: str) -> "Observation":
    require(raw.endswith(b"\n") and len(raw.splitlines()) == 1, "observation framing")
    value: object = json.loads(raw.decode("ascii"), object_pairs_hook=unique_json_pairs)
    item = object_fields(value, frozenset({
      "component", "case", "node_present", "root_present", "node_leaf",
      "reference_gets", "reference_puts", "live_references", "lock_entries",
      "lock_depth", "generations", "sequences", "records",
    }))
    require(item["component"] == component and item["case"] == case, "observation identity")
    require(type(item["node_present"]) is bool and type(item["root_present"]) is bool,
            "presence fields are not booleans")
    leaf_value = item["node_leaf"]
    require((leaf_value is None) == (not item["node_present"]), "node/leaf mismatch")
    leaf = None if leaf_value is None else text_field(leaf_value)
    if leaf is not None:
      require("/" not in leaf, "FDT fixture supplied an absolute full_name")
    integer(item["lock_entries"])
    records = item["records"]
    if not isinstance(records, list) or len(records) > 128:
      raise SetupError("record bound")
    generations = integer_tuple(item["generations"])
    sequences = integer_tuple(item["sequences"])
    require(len(generations) == len(sequences), "counter length mismatch")
    return cls(
      component=component, case=case, node_leaf=leaf,
      generations=generations, sequences=sequences,
      reference_gets=integer(item["reference_gets"]),
      reference_puts=integer(item["reference_puts"]),
      live_references=integer(item["live_references"]), lock_depth=integer(item["lock_depth"]),
      records=tuple(Marker.parse(
        record, None if case == "interleaved_components" else component,
      ) for record in records),
    )


@dataclass
class Harness:
  sources: dict[str, str]
  observations: dict[tuple[str, str], Observation] = field(default_factory=dict)

  @classmethod
  def prepare(cls) -> "Harness":
    isolated()
    for name, digest in LINK_PINS.items():
      pinned_bytes(Path("/inputs/link-runtime") / name, digest)
    for name, digest in FDT_PINS.items():
      pinned_bytes(Path("/inputs/libfdt") / name, digest)
    of_sources = {
      name: pinned_bytes(Path("/inputs/of") / name, digest).decode("utf-8")
      for name, digest in OF_PINS.items()
    }
    producers = {
      component: pinned_bytes(Path("/inputs/kernel") / name, digest).decode("utf-8")
      for component, (name, digest) in PRODUCER_PINS.items()
    }
    template = pinned_bytes(
      Path("/inputs/target-tests/target_gate_harness.c"), TEMPLATE_PIN,
    ).decode("utf-8")
    additions = {
      "/* @PINNED_OF_FRAGMENTS@ */": of_fragments(of_sources),
      "/* @PINNED_PRODUCER_FRAGMENTS@ */": "\n".join(
        producer_fragments(component, producers[component]) for component in COMPONENTS
      ),
    }
    for placeholder, replacement in additions.items():
      unique_offset(template, placeholder)
      template = template.replace(placeholder, replacement)
    generated = WORK / "target-gate-generated.c"
    with generated.open("x", encoding="utf-8") as stream:
      stream.write(template)
    check_dynamic("/inputs/link-runtime/libatomic.so", "link-runtime-dynamic")
    checked_run([
      "/usr/bin/gcc", "-std=gnu11", "-O2", "-Wall", "-Wextra", "-Werror",
      "-I/inputs/libfdt", "-L/inputs/link-runtime", str(generated),
      *[str(Path("/inputs/libfdt") / name) for name in FDT_PINS if name.endswith(".c")],
      "-o", "/work/target-gate-harness",
    ], "compile-target-gates")
    check_dynamic("/work/target-gate-harness", "harness-dynamic")
    with (WORK / "target-gate-inputs.json").open("x", encoding="ascii") as stream:
      json.dump({
        "producer_pins": PRODUCER_PINS, "of_pins": OF_PINS, "libfdt_pins": FDT_PINS,
        "template_sha256": TEMPLATE_PIN,
        "generated_sha256": hashlib.sha256(template.encode("utf-8")).hexdigest(),
        "scope": "metadata and exact probe prefix; no hardware or kernel scheduling",
      }, stream, sort_keys=True)
    return cls(producers)

  def observe(self, component: str, case: str) -> Observation:
    require(component in COMPONENTS and case in CASE_NAMES, "unknown fixture")
    key = (component, case)
    if key not in self.observations:
      raw = checked_run(
        ["/work/target-gate-harness", component, case], f"case-{component}-{case}",
      )
      self.observations[key] = Observation.parse(raw, component, case)
    return self.observations[key]


class TargetGateTests(unittest.TestCase):
  harness: Harness

  @classmethod
  def setUpClass(cls) -> None:
    cls.harness = Harness.prepare()

  def assert_references_released(self, observation: Observation) -> None:
    self.assertEqual(observation.reference_gets, observation.reference_puts)
    self.assertEqual(observation.live_references, 0)
    self.assertEqual(observation.lock_depth, 0)

  def assert_front_marker(self, component: str, case: str) -> None:
    observed = self.harness.observe(component, case)
    self.assert_references_released(observed)
    leaf = "usb@502280000" if component == "dwc3" else "phy@503000000"
    self.assertEqual(observed.node_leaf, leaf)
    self.assertEqual(
      observed.generations, (1,),
      f"{component} correct FDT target returned generation {observed.generations}; "
      f"sequence={observed.sequences}, first_markers={len(observed.records)}",
    )
    self.assertEqual(observed.sequences, (1,))
    self.assertEqual(len(observed.records), 1)
    marker = observed.records[0]
    self.assertEqual((marker.component, marker.event, marker.phase),
                     (component, "probe", "begin"))
    self.assertEqual(marker.revision, "dev147-usbdiag2-v1")
    self.assertEqual((marker.generation, marker.sequence), (1, 1))
    self.assertEqual(marker.attempt, 0 if component == "dwc3" else None)

  def test_dwc3_correct_target_reaches_first_probe(self) -> None:
    self.assert_front_marker("dwc3", "front_target")

  def test_atc_correct_target_reaches_first_probe(self) -> None:
    self.assert_front_marker("atc", "front_target")

  def test_existing_board_compatibility_semantics(self) -> None:
    for component in COMPONENTS:
      for case in ("uppercase_board", "later_compatible_board"):
        with self.subTest(component=component, case=case):
          self.assert_front_marker(component, case)

  def test_non_targets_consume_no_counters_or_references(self) -> None:
    for component in COMPONENTS:
      for case in NEGATIVE_CASES:
        with self.subTest(component=component, case=case):
          observed = self.harness.observe(component, case)
          self.assert_references_released(observed)
          self.assertEqual(observed.generations, (0,))
          self.assertEqual(observed.sequences, (0,))
          self.assertEqual(observed.records, ())
          if case in ("null_node", "null_node_missing_target"):
            self.assertEqual((observed.reference_gets, observed.reference_puts), (1, 1))

  def test_probe_retry_generations_survive_rejection(self) -> None:
    for component in COMPONENTS:
      for case, generations, sequences in (
        ("probe_retries", (1, 2, 3), (1, 2, 3)),
        ("reject_between_retries", (1, 0, 2), (1, 1, 2)),
      ):
        with self.subTest(component=component, case=case):
          observed = self.harness.observe(component, case)
          self.assert_references_released(observed)
          self.assertEqual(observed.generations, generations)
          self.assertEqual(observed.sequences, sequences)
          self.assertEqual(tuple(record.generation for record in observed.records),
                           tuple(value for value in generations if value))

  def test_interleaved_components_have_independent_counters(self) -> None:
    for component in COMPONENTS:
      with self.subTest(first_component=component):
        peer = "atc" if component == "dwc3" else "dwc3"
        observed = self.harness.observe(component, "interleaved_components")
        self.assert_references_released(observed)
        self.assertEqual(observed.generations, (1, 1, 2, 2))
        self.assertEqual(observed.sequences, (1, 1, 2, 2))
        self.assertEqual(tuple(record.component for record in observed.records),
                         (component, peer, component, peer))
        self.assertEqual(tuple(record.generation for record in observed.records),
                         (1, 1, 2, 2))
        self.assertEqual(tuple(record.sequence for record in observed.records),
                         (1, 1, 2, 2))

  def test_cap_is_reached_through_actual_generation_gate(self) -> None:
    for component in COMPONENTS:
      with self.subTest(component=component):
        observed = self.harness.observe(component, "cap_via_probe")
        self.assert_references_released(observed)
        self.assertEqual(observed.generations, tuple(range(1, 133)))
        self.assertEqual(observed.sequences, tuple(min(index, 128) for index in range(1, 133)))
        self.assertEqual(len(observed.records), 128)
        self.assertEqual(tuple(record.sequence for record in observed.records),
                         tuple(range(1, 129)))
        self.assertEqual([(record.event, record.sequence) for record in observed.records
                          if record.event == "capture_capped"], [("capture_capped", 128)])

  def test_probe_prefix_extraction_rejects_drift(self) -> None:
    for component in COMPONENTS:
      with self.subTest(component=component):
        source = self.harness.sources[component]
        changed = source.replace("\tint ret;\n\tunsigned int dev147_generation",
                                 "\tint ret;\n\tint extra;\n\tunsigned int dev147_generation")
        self.assertNotEqual(changed, source)
        with self.assertRaisesRegex(SetupError, "probe prefix drift"):
          producer_fragments(component, changed)
        with self.assertRaisesRegex(SetupError, "missing/duplicate"):
          producer_fragments(component, source + source)

  def test_source_pin_rejects_changed_private_copy(self) -> None:
    for component, (_, digest) in PRODUCER_PINS.items():
      with self.subTest(component=component):
        path = WORK / f"drift-{component}.c"
        with path.open("xb") as stream:
          stream.write(self.harness.sources[component].encode("utf-8") + b"\n")
        with self.assertRaisesRegex(SetupError, "source pin drift"):
          pinned_bytes(path, digest)

  def test_json_duplicate_fields_fail_closed(self) -> None:
    with self.assertRaisesRegex(SetupError, "duplicate JSON"):
      json.loads('{"case":"front_target","case":"rear_port"}',
                 object_pairs_hook=unique_json_pairs)


if __name__ == "__main__":
  unittest.main(verbosity=2)
