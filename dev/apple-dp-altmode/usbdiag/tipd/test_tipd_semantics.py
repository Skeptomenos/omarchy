"""Source-extracted TIPD checks; run only in the reviewed private sandbox.

The unchanged working HPD control and the fixed T1 subject must satisfy the
original independent operation ledgers. The original two positive entry tests
first failed against the frozen control, before instrumentation was written.
Partial-function and bounded atomic-thread fixtures are not kernel probes,
complete captured traces, ABI proofs, or hardware scheduling simulations.
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


CORE_SHA256 = "bb19187a1c41517e4b9f0fc3da7089fd41d26851774001ae3ad10c43139f2e15"
CONTROL_PINS: dict[str, str] = {
  "core.c": CORE_SHA256,
  "tps6598x.h": "1126fc478ac09242b6c36b36a370812138f7d56d1bd0686acb9ecf6a7dfc0f73",
  "trace.c": "1aa4062980d6c62ddec438abdff474408ee6ff9c891ca134153a8187fbb92e87",
  "trace.h": "21a469e23cf48152c31f61c0eea8723d43b650facb730bbb352193c73e27e4e6",
  "Makefile": "cd9faacfe10e725e71957aa226b5b0712b3d3de4bb70bec20c1d9b4d17a4ab72",
}
SUBJECT_PINS: dict[str, str] = {
  **CONTROL_PINS,
  "core.c": "215051ed006431c73f2e402e5a1d503daaa41dc9d4b9e2bb66a82ac868892a92",
}
HEADER_PINS: dict[str, str] = {
  "linux/usb/typec.h": "8365f2bc6ee3c43bd4b6a08c766fadf5a3c2e9f13059a56922af7e8031f1c23b",
  "linux/usb/typec_mux.h": "6f9017a5c9f24078c63ac58fc4caa494474bb6a1334a19583594ffd661645c46",
  "linux/usb/typec_dp.h": "601bc7daf26aee18d4efce18e18af659c9b5937ca59b16f4026e7cde04ba2c50",
  "linux/usb/typec_tbt.h": "4e7613286cc3e318736a794c30422fe236acef16c805f1665c4f6570ed7f109d",
  "linux/usb/typec_altmode.h": "7ee0d359d692edd3e1071e4ad1beb76eccaec21836c8a63a4ff9253c0b88948b",
  "linux/usb/role.h": "c0b27bebba441449a2cc461e405a48c7ed77dc7df3e499fc0015d02b25660d7e",
  "drm/drm_connector.h": "934f2a08aa2bfcd7d8acd85037c16b17b7d67750bc7505a26d751658aa0dd687",
  "linux/interrupt.h": "c63519d510a76163be986e4627acf5eb950b6f6cdc154b2f9b92c8ce8791f6ee",
  "linux/gpio/consumer.h": "9edf0c4bc684ca85bc8e085ebe57d7d22715fad4a901a3e5955d24450d618c73",
  "linux/err.h": "e7fab3f021ae4d0c5f7e34497eca5cd3473cca904cb59a853b015720a74b04e9",
  "linux/bits.h": "fec9de74956535b6664b36ef4e1b0399af0cdc63e50002dbe83c09e1c066825f",
  "vdso/bits.h": "ef5190bae70874421bd1cd564885f483787203cb65485af5104d57991238538b",
  "linux/bitfield.h": "e98046198bfaa7e05909cc88986c66c87b9638881fdcf88b5e090552d8d2eb77",
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
TEMPLATE_PINS: dict[str, str] = {
  "semantic_adapter.c": "5e62d669b64a24f7a3bbd476792a9c3bcd4cfdbba96e2c74a85162c6f70a514c",
  "semantic_fixture.c": "2e55a4fa1d154f70262e288bd1784459a2392d837063e5e878875b7812d7b530",
  "of_fixture.c": "c501f6cb2ee737c1e45463f9315270e7d44efc2b58762b83cf822d23586db7bb",
  "diagnostic_fixture.c": "f8a177274b98f33f91a296ddb29aac91704d8408b4716fbecb0f1a9f770f803b",
}
FUNCTIONS = (
  "static void cd321x_typec_update_mode(",
  "static void cd321x_update_work(",
  "static void cd321x_queue_status(",
  "static int cd321x_connect(",
  "int tipd_init(",
)
WORK = Path("/work")
type Event = tuple[str, int, int, int, int, int]
type Scalar = str | int | bool
HELPERS_BEGIN = "/* DEV147_T1_HELPERS_BEGIN: exact source extraction boundary. */\n"
HELPERS_END = "/* DEV147_T1_HELPERS_END */\n"


class SetupError(RuntimeError):
  """Containment, input, extraction, compiler or observation failure; not RED."""


def require(condition: bool, message: str) -> None:
  if not condition:
    raise SetupError(message)


def pinned(path: Path, digest: str) -> str:
  meta = path.lstat()
  require(stat.S_ISREG(meta.st_mode) and meta.st_nlink == 1, f"input type: {path.name}")
  require(0 < meta.st_size <= 512 * 1024, f"input size: {path.name}")
  raw = path.read_bytes()
  require(hashlib.sha256(raw).hexdigest() == digest, f"input drift: {path.name}")
  return raw.decode("utf-8")


def unique(source: str, marker: str) -> int:
  require(source.count(marker) == 1, f"missing or duplicate anchor: {marker}")
  return source.index(marker)


def function(source: str, signature: str) -> str:
  begin = unique(source, signature)
  end = source.find("\n}\n", begin)
  require(end > begin and "\n{\n" in source[begin:end], f"function boundary: {signature}")
  return source[begin:end + 3]


def declaration(source: str, start: str) -> str:
  begin = unique(source, start)
  end = source.find("\n};\n", begin)
  require(end > begin, f"declaration boundary: {start}")
  return source[begin:end + 4]


def helpers(source: str) -> str:
  begin, end = unique(source, HELPERS_BEGIN), unique(source, HELPERS_END)
  require(end > begin, "helper boundary order")
  return source[begin:end + len(HELPERS_END)]


def macro(source: str, name: str) -> str:
  lines = source.splitlines(keepends=True)
  found = [i for i, line in enumerate(lines)
           if re.match(rf"^#define {re.escape(name)}(?:\(|\s)", line)]
  require(len(found) == 1, f"macro boundary: {name}")
  begin = end = found[0]
  while lines[end].endswith("\\\n"):
    end += 1
    require(end < len(lines), f"unterminated macro: {name}")
  return "".join(lines[begin:end + 1])


def of_fragments(sources: dict[str, str]) -> str:
  header = sources["of.h"]
  enabled = header[:unique(header, "\n#else /* CONFIG_OF */\n")]
  chunks = [
    function(sources["string.h"], "static inline const char *kbasename("),
    *(macro(header, name) for name in ("of_compat_cmp", "of_prop_cmp", "for_each_property_of_node")),
    function(enabled, "static inline const char *of_node_full_name("),
    function(enabled, "static inline struct device_node *of_find_node_by_path("),
    function(enabled, "static inline bool of_machine_is_compatible("),
    function(sources["dynamic.c"], "struct device_node *of_node_get("),
    function(sources["dynamic.c"], "void of_node_put("),
    function(sources["property.c"], "const char *of_prop_next_string("),
  ]
  base = sources["base.c"]
  chunks.extend(function(base, signature) for signature in (
    "static struct property *__of_find_property(", "const void *__of_get_property(",
    "bool of_node_name_eq(", "static bool __of_node_is_type(",
    "static int __of_device_is_compatible(", "int of_device_is_compatible(",
    "int of_device_compatible_match(", "bool of_machine_compatible_match(",
    "static struct device_node *__of_get_next_child(",
  ))
  chunks.append(macro(base, "__for_each_child_of_node"))
  chunks.extend(function(base, signature) for signature in (
    "struct device_node *__of_find_node_by_path(",
    "struct device_node *__of_find_node_by_full_path(",
    "struct device_node *of_find_node_opts_by_path(",
  ))
  return "\n".join(chunks)


def definitions(headers: dict[str, str], core: str) -> str:
  bits = headers["linux/bits.h"]
  begin = unique(bits, "#if !defined(__ASSEMBLY__)\n")
  end = unique(bits, "\n#else /* defined(__ASSEMBLY__) */\n")
  require(end > begin, "bits.h non-assembly branch order")
  c_bits = bits[begin:end]
  chunks = [
    macro(headers["vdso/bits.h"], "BIT"), macro(headers["vdso/bits.h"], "BIT_ULL"),
    *(macro(c_bits, name) for name in (
      "GENMASK_INPUT_CHECK", "GENMASK_TYPE", "GENMASK",
    )),
    macro(headers["linux/bitfield.h"], "__bf_shf"),
  ]
  err = headers["linux/err.h"]
  chunks.extend(macro(err, name) for name in ("MAX_ERRNO", "IS_ERR_VALUE"))
  chunks.extend(function(err, signature) for signature in (
    "static __always_inline void * __must_check ERR_PTR(",
    "static __always_inline long __must_check PTR_ERR(",
    "static __always_inline bool __must_check IS_ERR(",
  ))
  typec = headers["linux/usb/typec.h"]
  chunks.extend(declaration(typec, f"enum {name} {{") for name in (
    "typec_data_role", "typec_role", "typec_pwr_opmode", "typec_accessory", "typec_orientation",
  ))
  chunks.extend(declaration(typec, f"struct {name} {{") for name in (
    "enter_usb_data", "usb_pd_identity", "typec_partner_desc",
  ))
  chunks.extend((
    declaration(headers["linux/usb/role.h"], "enum usb_role {"),
    declaration(headers["linux/usb/typec_mux.h"], "struct typec_mux_state {"),
    declaration(headers["linux/usb/typec_altmode.h"], "enum {\n\tTYPEC_STATE_SAFE,"),
    declaration(headers["linux/usb/typec_altmode.h"], "enum {\n\tTYPEC_MODE_USB2 ="),
    declaration(headers["linux/usb/typec_dp.h"], "enum {\n\tTYPEC_DP_STATE_A ="),
    declaration(headers["linux/usb/typec_dp.h"], "struct typec_displayport_data {"),
    macro(headers["linux/usb/typec_tbt.h"], "TYPEC_TBT_MODE"),
    declaration(headers["linux/usb/typec_tbt.h"], "struct typec_thunderbolt_data {"),
    declaration(headers["drm/drm_connector.h"], "enum drm_connector_status {"),
  ))
  gpio = headers["linux/gpio/consumer.h"]
  chunks.extend(macro(gpio, name) for name in (
    "GPIOD_FLAGS_BIT_DIR_SET", "GPIOD_FLAGS_BIT_DIR_OUT", "GPIOD_FLAGS_BIT_DIR_VAL",
    "GPIOD_FLAGS_BIT_OPEN_DRAIN",
  ))
  chunks.append(declaration(gpio, "enum gpiod_flags {"))
  chunks.extend(macro(headers["linux/interrupt.h"], name) for name in ("IRQF_SHARED", "IRQF_ONESHOT"))
  chunks.extend(macro(core, name) for name in (
    "TPS_REG_VID", "TPS_REG_INT_MASK1", "TPS_SETUP_MS", "CD321X_DEBOUNCE_DELAY_MS", "POLL_INTERVAL",
  ))
  chunks.append(declaration(core, "enum {\n\tTPS_MODE_APP,"))
  return "\n".join(chunks)


def substitute(source: str, marker: str, value: str) -> str:
  unique(source, marker)
  return source.replace(marker, value)


def limits() -> None:
  _, hard = resource.getrlimit(resource.RLIMIT_FSIZE)
  bound = 512 * 1024 if hard == resource.RLIM_INFINITY else min(512 * 1024, hard)
  resource.setrlimit(resource.RLIMIT_FSIZE, (bound, bound))


def run(command: list[str], label: str) -> bytes:
  require(re.fullmatch(r"[a-z0-9_-]{1,80}", label) is not None, "child label")
  output, errors = WORK / f"{label}.stdout", WORK / f"{label}.stderr"
  code: int | None = None
  timed_out = False
  with output.open("xb") as stdout, errors.open("xb") as stderr:
    try:
      result = subprocess.run(
        command, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
        check=False, timeout=30, preexec_fn=limits,
        env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C",
             "LD_LIBRARY_PATH": "/inputs/link-runtime"},
      )
      code = result.returncode
    except subprocess.TimeoutExpired:
      timed_out = True
  with (WORK / f"{label}.result.json").open("x", encoding="ascii") as stream:
    json.dump({"command": command, "exit_code": code, "timed_out": timed_out},
              stream, sort_keys=True)
  require(not timed_out and code == 0, f"child failure: {label}, code={code}, timeout={timed_out}")
  require(output.stat().st_size <= 512 * 1024 and errors.stat().st_size <= 512 * 1024,
          f"child output bound: {label}")
  require(errors.read_bytes() == b"", f"child stderr: {label}")
  return output.read_bytes()


def object_fields(value: object, names: frozenset[str]) -> dict[str, object]:
  require(isinstance(value, dict), "expected object")
  if not isinstance(value, dict):
    raise SetupError("expected object")
  result: dict[str, object] = {}
  for key, item in value.items():
    require(isinstance(key, str), "non-string key")
    if not isinstance(key, str):
      raise SetupError("non-string key")
    result[key] = item
  require(result.keys() == names, "observation fields")
  return result


def number(value: object) -> int:
  if type(value) is not int or not -4096 <= value <= 0xFFFFFFFF:
    raise SetupError("bounded integer expected")
  return value


def numbers(value: object, length: int) -> tuple[int, ...]:
  if not isinstance(value, list) or len(value) != length:
    raise SetupError("integer-list length")
  return tuple(number(item) for item in value)


def observed_ledger(value: object) -> tuple[Event, ...]:
  if not isinstance(value, list) or len(value) > 1024:
    raise SetupError("ledger bound")
  ledger: list[Event] = []
  for row in value:
    if not isinstance(row, list) or len(row) != 6 or not isinstance(row[0], str):
      raise SetupError("ledger row")
    require(re.fullmatch(r"[a-z_]{1,32}", row[0]) is not None, "operation name")
    ledger.append((row[0], number(row[1]), number(row[2]), number(row[3]),
                   number(row[4]), number(row[5])))
  return tuple(ledger)


def observed_records(value: object) -> tuple[str, ...]:
  if not isinstance(value, list) or len(value) > 128:
    raise SetupError("record bound")
  records: list[str] = []
  for record in value:
    if not isinstance(record, str) or not record.isascii() or not 0 < len(record) + 2 <= 384:
      raise SetupError("record size/encoding, including INFO prefix")
    require(record.endswith("\n"), "unterminated record")
    records.append(record)
  return tuple(records)


SNAPSHOT_FIELDS = frozenset(("plug", "usb2", "usb3", "hpd", "flip", "device", "power"))
ENVELOPE_FIELDS = frozenset(("rev", "board", "target", "component", "seq", "gen", "worker"))
RECORD_FIELDS: dict[tuple[str, str], frozenset[str]] = {
  ("init", "begin"): frozenset(), ("init", "end"): frozenset(("reason", "ret")),
  ("cache", "stored"): SNAPSHOT_FIELDS,
  ("queue", "queued"): SNAPSHOT_FIELDS | {"disconnect", "hpd_change"},
  ("worker", "begin"): SNAPSHOT_FIELDS | {"disconnect", "hpd_change", "connector", "cached_device"},
  ("worker", "end"): frozenset(("reason", "ret")),
  ("mux", "begin"): frozenset(("kind", "mode")),
  ("mux", "returned"): frozenset(("kind", "mode", "ret")),
  ("mux", "skip"): frozenset(("kind", "mode", "reason")),
  ("role", "begin"): frozenset(("which", "value")),
  ("role", "returned"): frozenset(("which", "value", "ret")),
  ("role", "skip"): frozenset(("which", "value", "reason")),
  ("hpd", "begin"): frozenset(("which",)), ("hpd", "returned"): frozenset(("which",)),
  ("hpd", "skip"): frozenset(("which", "reason")),
  ("cap", "end"): frozenset(("limit", "reason")),
}


def source_records(raw_records: tuple[str, ...]) -> tuple[dict[str, Scalar], ...]:
  """Check producer shape/budget, not captured-trace lifecycle or artifact identity."""
  records: list[dict[str, Scalar]] = []
  for raw in raw_records:
    value: object = json.loads(raw)
    require(isinstance(value, dict), "native record object")
    if not isinstance(value, dict):
      raise SetupError("native record object")
    event_name, phase = value.get("event"), value.get("phase")
    require(isinstance(event_name, str) and isinstance(phase, str), "record event/phase")
    if not isinstance(event_name, str) or not isinstance(phase, str):
      raise SetupError("record event/phase")
    key = (event_name, phase)
    require(key in RECORD_FIELDS, "record event/phase grammar")
    item = object_fields(value, ENVELOPE_FIELDS | {"event", "phase"} | RECORD_FIELDS[key])
    require(all(item[name] == expected for name, expected in (
      ("rev", "dev147-tipddiag1-v1"), ("board", "j413"),
      ("target", "front_lower"), ("component", "tipd"),
    )), "fixed source record labels")
    require(1 <= number(item["seq"]) <= 128 and 1 <= number(item["gen"]) <= 0x7FFFFFFF,
            "record sequence/generation bounds")
    worker = number(item["worker"])
    require(0 <= worker <= 0x7FFFFFFF, "record worker bound")
    require(event_name == "cap" or (worker == 0 if event_name in ("init", "cache", "queue")
                                    else worker > 0), "record worker ownership")
    for name in SNAPSHOT_FIELDS - {"power"} | {"disconnect", "hpd_change", "connector", "cached_device"}:
      if name in item:
        require(type(item[name]) is bool, "record boolean field")
    if "power" in item:
      require(0 <= number(item["power"]) <= 3, "record power field")
    for name in ("ret", "mode", "value", "limit"):
      if name in item:
        number(item[name])
    if key == ("worker", "end"):
      require(-4095 <= number(item["ret"]) <= -1 if item["reason"] == "partner_error"
              else item["ret"] == 0, "worker terminal return contract")
    converted: dict[str, Scalar] = {}
    for name, field_value in item.items():
      if type(field_value) not in (str, int, bool):
        raise SetupError("record scalar type")
      if not isinstance(field_value, (str, int, bool)):
        raise SetupError("record scalar type")
      converted[name] = field_value
    records.append(converted)
  sequences = [number(item["seq"]) for item in records]
  require(sorted(sequences) == list(range(1, len(records) + 1)), "source sequence gap/duplicate")
  if len(records) >= 127:
    require(len(records) == 128, "normal 127 requires automatic cap 128")
    by_sequence = {number(item["seq"]): item for item in records}
    cap, previous = by_sequence[128], by_sequence[127]
    require(cap["event"] == "cap" and cap["phase"] == "end" and
            cap["limit"] == 128 and cap["reason"] == "budget", "terminal cap shape")
    require((cap["gen"], cap["worker"]) == (previous["gen"], previous["worker"]), "cap ownership")
  require(all(item["event"] != "cap" or item["seq"] == 128 for item in records), "early cap")
  return tuple(records)


def details(records: tuple[dict[str, Scalar], ...]) -> tuple[dict[str, Scalar], ...]:
  return tuple({key: value for key, value in item.items() if key not in ENVELOPE_FIELDS}
               for item in records)


@dataclass(frozen=True)
class Observation:
  result: int
  board_match: bool
  target_match: bool
  ledger: tuple[Event, ...]
  records: tuple[str, ...]
  snapshot: tuple[int, ...]
  snapshots: tuple[tuple[int, ...], ...]
  state: tuple[int, ...]
  partner: int
  identity: int
  pending: tuple[int, ...]
  dispatches: int
  production_refs: tuple[int, ...]
  diagnostic_counts: tuple[int, ...]
  tail: tuple[int, ...]

  @classmethod
  def parse(cls, raw: bytes, scenario: str) -> "Observation":
    payload: object = json.loads(raw)
    item = object_fields(payload, frozenset((
      "scenario", "result", "board_match", "target_match", "precheck_refs",
      "production_refs", "ledger", "records", "snapshot", "snapshots",
      "state", "partner", "identity", "pending", "dispatches", "allocation_bounds",
      "diagnostic_counts", "tail",
    )))
    require(item["scenario"] == scenario and item["allocation_bounds"] is True, "fixture identity/bounds")
    for key in ("precheck_refs", "production_refs"):
      refs = numbers(item[key], 2)
      require(refs[0] == refs[1], "unbalanced metadata reference")
    board, target = item["board_match"], item["target_match"]
    require(type(board) is bool and type(target) is bool, "metadata booleans")
    if not isinstance(board, bool) or not isinstance(target, bool):
      raise SetupError("metadata booleans")
    snapshots_value = item["snapshots"]
    if not isinstance(snapshots_value, list) or len(snapshots_value) > 4:
      raise SetupError("snapshot bound")
    return cls(
      number(item["result"]), board, target, observed_ledger(item["ledger"]), observed_records(item["records"]),
      numbers(item["snapshot"], 24), tuple(numbers(row, 24) for row in snapshots_value),
      numbers(item["state"], 3), number(item["partner"]), number(item["identity"]),
      numbers(item["pending"], 2), number(item["dispatches"]), numbers(item["production_refs"], 2),
      numbers(item["diagnostic_counts"], 3), numbers(item["tail"], 2),
    )


@dataclass(frozen=True)
class DiagnosticObservation:
  counts: tuple[int, ...]
  refs: tuple[int, ...]
  conversions: int
  wrapper_offset: int
  tail_offset: int
  prefix_bytes: int
  wrapper_bytes: int
  contexts: tuple[tuple[int, ...], ...]
  outcomes: tuple[int, ...]
  records: tuple[str, ...]
  ledger: tuple[Event, ...]

  @classmethod
  def parse(cls, raw: bytes, name: str) -> "DiagnosticObservation":
    payload: object = json.loads(raw)
    item = object_fields(payload, frozenset((
      "case", "counts", "refs", "conversions", "wrapper_offset", "tail_offset", "prefix_bytes",
      "wrapper_bytes", "bounds", "contexts", "outcomes", "records", "ledger",
    )))
    require(item["case"] == name and item["bounds"] is True, "diagnostic identity/bounds")
    contexts, outcomes = item["contexts"], item["outcomes"]
    if not isinstance(contexts, list) or len(contexts) > 16:
      raise SetupError("diagnostic context count")
    if not isinstance(outcomes, list) or len(outcomes) > 4:
      raise SetupError("diagnostic outcome count")
    refs = numbers(item["refs"], 2)
    require(refs[0] == refs[1], "diagnostic reference balance")
    return cls(
      numbers(item["counts"], 3), refs, number(item["conversions"]),
      number(item["wrapper_offset"]), number(item["tail_offset"]),
      number(item["prefix_bytes"]), number(item["wrapper_bytes"]),
      tuple(numbers(context, 2) for context in contexts), tuple(number(outcome) for outcome in outcomes),
      observed_records(item["records"]), observed_ledger(item["ledger"]),
    )


@dataclass
class Harness:
  core: str
  subject_core: str
  observations: dict[tuple[str, tuple[str, ...]], Observation] = field(default_factory=dict)
  diagnostics: dict[tuple[str, ...], DiagnosticObservation] = field(default_factory=dict)

  @classmethod
  def prepare(cls) -> "Harness":
    require(os.getuid() == 1001 and os.getgid() == 1001 and Path.cwd() == WORK, "sandbox identity/cwd")
    require(not any(Path(path).exists() for path in (
      "/proc", "/sys", "/run", "/boot", "/home", "/etc",
    )), "host tree visible")
    for name, digest in LINK_PINS.items():
      # Binary link inputs are checked separately from text source decoding.
      path = Path("/inputs/link-runtime") / name
      meta = path.lstat()
      require(stat.S_ISREG(meta.st_mode) and meta.st_nlink == 1 and
              0 < meta.st_size <= 512 * 1024, "link input type/size")
      require(hashlib.sha256(path.read_bytes()).hexdigest() == digest, "link input drift")
    for name, digest in FDT_PINS.items():
      pinned(Path("/inputs/libfdt") / name, digest)
    headers = {name: pinned(Path("/inputs/headers/include") / name, digest)
               for name, digest in HEADER_PINS.items()}
    of_sources = {name: pinned(Path("/inputs/of") / name, digest)
                  for name, digest in OF_PINS.items()}
    templates = {name: pinned(Path("/inputs/tests") / name, digest)
                 for name, digest in TEMPLATE_PINS.items()}
    metadata = substitute(templates["of_fixture.c"], "/* @PINNED_OF@ */", of_fragments(of_sources))
    retained: dict[str, str] = {}
    for label in ("control", "subject"):
      source_pins = CONTROL_PINS if label == "control" else SUBJECT_PINS
      sources = {name: pinned(Path("/inputs") / label / name, digest)
                 for name, digest in source_pins.items()}
      core = sources["core.c"]
      retained[label] = core
      header = sources["tps6598x.h"]
      header = header[unique(header, "#ifndef __TPS6598X_H__"):]
      generated = templates["semantic_adapter.c"]
      for marker, replacement in (
        ("/* @PINNED_DEFINITIONS@ */", definitions(headers, core)),
        ("/* @OF_FIXTURE@ */", metadata),
        ("/* @PINNED_TIPD_HEADER@ */", header),
        ("/* @T1_HELPERS@ */", "#define TIPD_T1_PRESENT 0\n" if label == "control" else
         "#define TIPD_T1_PRESENT 1\n" + helpers(core)),
        ("/* @PINNED_FUNCTIONS@ */", "\n".join(function(core, name) for name in FUNCTIONS)),
        ("/* @PINNED_DATA_TABLE@ */", "\n".join(declaration(core, f"const struct tipd_data {name} = {{")
                                              for name in ("tipd_cd321x_data", "tipd_sn201202x_data"))),
        ("/* @DIAGNOSTIC_FIXTURE@ */", templates["diagnostic_fixture.c"]),
        ("/* @FIXTURE_MAIN@ */", templates["semantic_fixture.c"]),
      ):
        generated = substitute(generated, marker, replacement)
      require("/* @" not in generated, "unfilled extraction marker")
      source_path = WORK / f"{label}.c"
      with source_path.open("x", encoding="utf-8") as stream:
        stream.write(generated)
      run([
        "/usr/bin/gcc", "-std=gnu11", "-O2", "-Wall", "-Wextra", "-Werror", "-pthread",
        "-I/inputs/libfdt", "-L/inputs/link-runtime", str(source_path),
        *[str(Path("/inputs/libfdt") / name) for name in FDT_PINS if name.endswith(".c")],
        "-o", str(WORK / label),
      ], f"compile-{label}")
      dynamic = run(["/usr/bin/readelf", "-d", str(WORK / label)], f"dynamic-{label}")
      needed = set(re.findall(rb"Shared library: \[([^]]+)\]", dynamic))
      require(needed <= {b"libc.so.6", b"libgcc_s.so.1", b"libatomic.so.1", b"ld-linux-aarch64.so.1"},
              "unreviewed dynamic dependency")
      require(b"(RPATH)" not in dynamic and b"(RUNPATH)" not in dynamic, "dynamic search override")
    with (WORK / "setup.json").open("x", encoding="ascii") as stream:
      json.dump({
        "status": "PASS", "control_pins": CONTROL_PINS, "subject_pins": SUBJECT_PINS,
        "headers": HEADER_PINS, "of": OF_PINS, "libfdt": FDT_PINS, "templates": TEMPLATE_PINS,
        "scope": "source semantics only; no kernel layout/concurrency/hardware proof",
      }, stream, sort_keys=True)
    print("SETUP PASS: exact working control and T1 bodies compiled; source semantics only.")
    return cls(retained["control"], retained["subject"])

  def observe(self, label: str, arguments: tuple[str, ...]) -> Observation:
    require(label in ("control", "subject") and 1 <= len(arguments) <= 17, "fixture arguments")
    require(arguments[0] in ("init", "worker", "mode", "queue", "connect",
                             "init_cap", "worker_cap", "mode_cap"), "fixture scenario")
    require(all(re.fullmatch(r"-?[0-9]{1,10}", item) is not None for item in arguments[1:]),
            "non-numeric fixture parameter")
    key = (label, arguments)
    if key not in self.observations:
      child_label = f"fixture-{len(self.observations):04d}-{label}-{arguments[0]}"
      raw = run([str(WORK / label), *arguments], child_label)
      self.observations[key] = Observation.parse(raw, arguments[0])
    return self.observations[key]

  def inspect(self, arguments: tuple[str, ...]) -> DiagnosticObservation:
    require(1 <= len(arguments) <= 3, "diagnostic argument count")
    name = arguments[0]
    require(name in ("guard", "retry", "cap_terminal", "parallel", "limits"), "diagnostic case")
    require(all(re.fullmatch(r"[0-9]{1,2}", item) is not None for item in arguments[1:]),
            "diagnostic numeric argument")
    if arguments not in self.diagnostics:
      label = f"diagnostic-{len(self.diagnostics):03d}-{name}"
      raw = run([str(WORK / "subject"), "diagnostic", *arguments], label)
      self.diagnostics[arguments] = DiagnosticObservation.parse(raw, name)
    return self.diagnostics[arguments]


def event(name: str, *values: int) -> Event:
  require(len(values) <= 5, "expected-event width")
  padded = values + (0,) * (5 - len(values))
  return (name, padded[0], padded[1], padded[2], padded[3], padded[4])


@dataclass(frozen=True)
class Worker:
  status: int = 1
  changed: int = 0
  data: int = 0x8111
  data_changed: int = 0
  cached_data: int = 0x8111
  old_role: int = 0
  partner: int = 0
  power_mode: int = 3
  changed_identity: int = 0
  connector: int = 1
  partner_error: int = 0
  role_result: int = 0
  mux_result: int = 0
  alt: int = 0
  mode: int = 0
  metadata: int = 0

  def arguments(self) -> tuple[str, ...]:
    return ("worker", *(str(value) for value in (
      self.status, self.changed, self.data, self.data_changed, self.cached_data,
      self.old_role, self.partner, self.power_mode, self.changed_identity,
      self.connector, self.partner_error, self.role_result, self.mux_result,
      self.alt, self.mode, self.metadata,
    )))


def expected_mux(data: int, alt: int, mode: int, payload: int) -> tuple[list[Event], tuple[int, ...]]:
  """Independent expectations from the reviewed branch table, not extracted code."""
  previous = (alt, mode, payload)
  if not data & 1:
    return ([], previous) if mode == 0 else ([event("mux_call", 0, 0)], (0, 0, 0))
  if data & 0x100:
    pin = ((data >> 10) & 3) * 2 + ((data >> 5) & 1)
    mapping = {0: 6, 1: 7, 2: 4, 3: 5, 4: 2, 6: 3}
    if pin not in mapping:
      return [event("error", 1)], previous
    selected = mapping[pin]
    if alt == 1 and mode == selected:
      return [], previous
    return [event("mux_call", 1, selected, 22, 23)], (1, selected, 0)
  if data & 0x10000:
    if (alt, mode) == (2, 2):
      return [], previous
    return [event("mux_call", 2, 2, 34, 33, 32)], (2, 2, 0)
  if data & 0x800000:
    if (alt, mode) == (0, 4):
      return [], previous
    return [event("mux_call", 0, 4, 41, int(bool(data & 0x100000)))], (0, 4, 0)
  if (alt, mode) == (0, 1):
    return [], previous
  return [event("mux_call", 0, 1)], (0, 1, 0)


def expected_worker(case: Worker, payload: int = 1) -> tuple[list[Event], tuple[int, ...], int, int]:
  """Specify original API order independently, including NULL/error partners."""
  connected = bool(case.status & 1)
  disconnected = bool(case.changed & 1)
  hpd = bool(case.data & 0x8000)
  hpd_changed = bool(case.data_changed & 0x8000)
  role = (2 if case.cached_data & 0x80 else 1) if case.data & 0x30 else 0
  power = case.power_mode if connected else 0
  partner_kind = case.partner
  identity = 10 + case.changed_identity
  state = (case.alt, case.mode, payload)
  expected = [event("lock"), event("get_role", case.old_role)]
  if case.old_role and (case.old_role != role or disconnected):
    expected.append(event("set_role", 0, case.role_result))
  if case.connector and (not hpd or hpd_changed):
    expected.append(event("hpd_call", 2))
  replace_partner = bool(partner_kind and connected and (
    disconnected or (power == 3 and case.changed_identity)
  ))
  if not connected or replace_partner:
    if partner_kind != 2:
      expected.append(event("partner_unregister", partner_kind))
    partner_kind = 0
  if not connected or disconnected:
    state = (0, 0, 0)
    expected.append(event("safe_mode", 0))
  expected.extend((
    event("pwr_mode", power), event("pwr_role", int(bool(case.status & 0x20))),
    event("vconn", int(bool(case.status & 0x80))),
    event("orientation", (2 if case.status & 0x10 else 1) if connected else 0),
    event("data_role", int(bool(case.status & 0x40))), event("power_changed"),
  ))
  if not connected:
    return expected + [event("unlock")], state, partner_kind, identity
  if not partner_kind:
    pd = int(power == 3)
    expected.append(event("partner_register", pd, pd, 10 if pd else 0, case.partner_error))
    if case.partner_error:
      return expected + [event("warning", 1), event("unlock")], state, 2, identity
    partner_kind = 1
    if pd:
      expected.append(event("identity_set"))
      identity = 10
  calls, state = expected_mux(case.data, *state)
  expected.extend(calls)
  expected.append(event("set_role", role, case.role_result))
  if case.connector and hpd:
    expected.append(event("hpd_call", 1))
  expected.extend((event("power_changed"), event("unlock")))
  return expected, state, partner_kind, identity


RESET, TPS25750, NO_POWER, PATCH = 1, 2, 4, 8
ATTACHED, CONNECTOR, IRQ, WAKEUP = 16, 32, 64, 128
CONNECT_ERROR, DURING_IRQ, CLEANUP_ERROR, SCHEDULE_FALSE = 256, 512, 1024, 2048
NORMAL = ATTACHED | CONNECTOR | IRQ


def expected_init(failure: int, flags: int) -> tuple[list[Event], int]:
  present = int(bool(flags & CONNECTOR))
  path = [event("gpio_get", 3)]
  if flags & RESET:
    path.append(event("sleep", 1000))
  path.append(event("device_compatible"))
  if not flags & TPS25750:
    path.append(event("vid_read", 0))
  if not flags & NO_POWER:
    path.append(event("power_switch", 0))
  path.append(event("mode_read"))
  if flags & PATCH:
    path.append(event("patch_init"))
  path.extend((event("mask_write", 22, 1538), event("status_read"), event("connector_get")))
  if present:
    path.append(event("purge_suppliers"))
  path.extend((event("role_get", present), event("psy_register"), event("port_register", present)))
  if flags & ATTACHED:
    path.extend((event("power_read"), event("data_read")))
    if flags & CONNECT_ERROR:
      path.extend((event("connect_error", 1), event("error", 2)))
    else:
      path.extend((event("cancel_update", 1, 1, 1), event("schedule_update", 500)))
  if flags & IRQ:
    path.append(event("irq_request", 7, 8320))
    if flags & DURING_IRQ:
      worker, _, _, _ = expected_worker(Worker(
        changed=1, data_changed=0x8111, connector=present,
      ), payload=0)
      path.extend(worker)
  else:
    path.extend((event("warning", 2), event("poll_init"), event("queue_poll", 500)))
  path.extend((event("connector_put", present), event("wakeup_read")))
  if flags & WAKEUP and flags & IRQ:
    path.extend((event("wakeup_init"), event("irq_wake", 7)))

  reset = [event("reset")]
  clear = [event("mask_write", 22, 0)] + reset
  fwnode = [event("connector_put", present)] + clear
  role = [event("role_put")] + fwnode
  port = [event("port_unregister")] + role
  disconnect = [event("generic_disconnect", 0)] + port
  # Failure operation, original return, and exact independently reviewed unwind.
  stops: dict[int, tuple[str, int, list[Event]]] = {
    1: ("gpio_get", -5, [event("gpio_error", -5)]),
    2: ("vid_read", -19, []), 3: ("vid_read", -19, []),
    4: ("power_switch", -5, []), 5: ("mode_read", -5, []),
    6: ("patch_init", -5, []), 7: ("mask_write", -5, reset),
    8: ("status_read", -19, clear), 9: ("role_get", -517, fwnode),
    10: ("psy_register", -5, role), 11: ("port_register", -5, role),
    12: ("power_read", -22, port), 13: ("data_read", -22, port),
    14: ("irq_request", -5, disconnect),
  }
  if failure:
    stop, result, suffix = stops[failure]
    index = next(i for i, row in enumerate(path) if row[0] == stop)
    if failure == 14 and flags & DURING_IRQ:
      index = max(i for i, row in enumerate(path) if row[0] == "unlock")
    return path[:index + 1] + suffix, result
  if flags & ATTACHED and flags & CONNECT_ERROR and not flags & IRQ:
    index = next(i for i, row in enumerate(path) if row[0] == "queue_poll")
    return path[:index + 1] + disconnect, -5
  return path, 0


def entry_count(observation: Observation, event_name: str) -> int:
  """Positive RED assertion only; not the future complete T1 trace validator."""
  count = 0
  for raw in observation.records:
    item: object = json.loads(raw)
    if isinstance(item, dict) and all(item.get(key) == value for key, value in (
      ("rev", "dev147-tipddiag1-v1"), ("board", "j413"),
      ("target", "front_lower"), ("component", "tipd"),
      ("event", event_name), ("phase", "begin"),
    )):
      count += 1
  return count


def record(event_name: str, phase: str, **values: Scalar) -> dict[str, Scalar]:
  return {"event": event_name, "phase": phase, **values}


def stored_fields(status: int, data: int, power: int) -> dict[str, Scalar]:
  return {
    "plug": bool(status & 1), "usb2": bool(data & 0x10), "usb3": bool(data & 0x20),
    "hpd": bool(data & 0x8000), "flip": bool(status & 0x10),
    "device": bool(data & 0x80), "power": power,
  }


def expected_mux_records(data: int, alt: int, mode: int, payload: int,
                         returned: int) -> list[dict[str, Scalar]]:
  operations, state = expected_mux(data, alt, mode, payload)
  if operations and operations[0][0] == "error":
    return [record("mux", "skip", kind="dp", mode=-1, reason="invalid_dp_pin")]
  kind = "safe" if not data & 1 else "dp" if data & 0x100 else \
    "tbt" if data & 0x10000 else "usb4" if data & 0x800000 else "usb"
  if not operations:
    return [record("mux", "skip", kind=kind, mode=state[1], reason="unchanged")]
  return [record("mux", "begin", kind=kind, mode=state[1]),
          record("mux", "returned", kind=kind, mode=state[1], ret=returned)]


def expected_worker_records(case: Worker) -> tuple[dict[str, Scalar], ...]:
  role = (2 if case.cached_data & 0x80 else 1) if case.data & 0x30 else 0
  rows = [record("worker", "begin", **stored_fields(case.status, case.data, case.power_mode),
                 disconnect=bool(case.changed & 1), hpd_change=bool(case.data_changed & 0x8000),
                 connector=bool(case.connector), cached_device=bool(case.cached_data & 0x80))]
  if case.old_role and (case.old_role != role or case.changed & 1):
    rows.extend((record("role", "begin", which="none", value=0),
                 record("role", "returned", which="none", value=0, ret=case.role_result)))
  else:
    rows.append(record("role", "skip", which="none", value=0, reason="no_transition"))
  if case.connector and (not case.data & 0x8000 or case.data_changed & 0x8000):
    rows.extend((record("hpd", "begin", which="disconnected"),
                 record("hpd", "returned", which="disconnected")))
  else:
    rows.append(record("hpd", "skip", which="disconnected",
                       reason="level_high_unchanged" if case.connector else "no_connector"))
  operations, _, _, _ = expected_worker(case)
  reason = "disconnected" if not case.status & 1 else \
    "partner_error" if any(row[0] == "warning" for row in operations) else "complete"
  if reason != "complete":
    rows.extend((record("mux", "skip", kind="none", mode=-1, reason=reason),
                 record("role", "skip", which="final", value=role, reason=reason),
                 record("hpd", "skip", which="connected", reason=reason)))
  else:
    alt, mode, payload = (0, 0, 0) if case.changed & 1 else (case.alt, case.mode, 1)
    rows.extend(expected_mux_records(case.data, alt, mode, payload, case.mux_result))
    rows.extend((record("role", "begin", which="final", value=role),
                 record("role", "returned", which="final", value=role, ret=case.role_result)))
    if case.connector and case.data & 0x8000:
      rows.extend((record("hpd", "begin", which="connected"),
                   record("hpd", "returned", which="connected")))
    else:
      rows.append(record("hpd", "skip", which="connected",
                         reason="level_low" if case.connector else "no_connector"))
  rows.append(record("worker", "end", reason=reason, ret=-5 if reason == "partner_error" else 0))
  return tuple(rows)


class TipdSemanticsTests(unittest.TestCase):
  harness: Harness

  @classmethod
  def setUpClass(cls) -> None:
    cls.harness = Harness.prepare()

  def paired(self, arguments: tuple[str, ...]) -> Observation:
    control = self.harness.observe("control", arguments)
    subject = self.harness.observe("subject", arguments)
    self.assertEqual(control.records, (), "authenticated control must not emit T1 records")
    self.assertEqual(control.diagnostic_counts, (0, 0, 0))
    self.assertEqual(control.production_refs, (0, 0))
    for name in ("result", "ledger", "snapshot", "snapshots", "state", "partner",
                 "identity", "pending", "dispatches", "board_match", "target_match"):
      self.assertEqual(getattr(control, name), getattr(subject, name), f"paired {name}")
    rows = source_records(subject.records)
    self.assertEqual(subject.diagnostic_counts[2], len(rows), "one global record reservation budget")
    if arguments[0] == "mode":
      data, alt, mode, payload, returned = (int(value) for value in arguments[1:6])
      if subject.board_match and subject.target_match:
        self.assertEqual(details(rows), tuple(expected_mux_records(data, alt, mode, payload, returned)))
      else:
        self.assertEqual(rows, ())
    return subject

  def check_init(self, failure: int, flags: int, metadata: int = 0) -> Observation:
    result = self.paired(("init", str(failure), str(flags), str(metadata)))
    expected, returned = expected_init(failure, flags)
    self.assertEqual(result.ledger, tuple(expected), "independent init operation ledger")
    self.assertEqual(result.result, returned, "original init return")
    rows = source_records(result.records)
    eligible = result.board_match and result.target_match and not flags & (NO_POWER | CONNECT_ERROR)
    if not eligible:
      self.assertEqual(rows, ())
      self.assertEqual(result.diagnostic_counts, (0, 0, 0))
      self.assertEqual(result.tail, (0, 0))
      if flags & (NO_POWER | CONNECT_ERROR):
        self.assertEqual(result.production_refs, (0, 0), "variant guard must precede OF lookup")
      return result
    self.assertEqual(details(rows[:1]), (record("init", "begin"),))
    reasons = {0: "complete", 1: "gpio", 2: "vid", 3: "vid", 4: "power_state", 5: "mode",
               6: "patch", 7: "mask", 8: "status", 9: "role", 10: "psy", 11: "port",
               12: "power_read", 13: "data_read", 14: "irq"}
    self.assertEqual(details(rows[-1:]), (record("init", "end", reason=reasons[failure], ret=returned),))
    self.assertEqual(sum(row["event"] == "init" for row in rows), 2)
    self.assertTrue(all(row["gen"] == 1 for row in rows))
    self.assertEqual(result.diagnostic_counts[:2], (1, result.dispatches))
    self.assertEqual(result.tail, (1, 0))
    queued = tuple(row for row in rows if row["event"] in ("cache", "queue"))
    if any(row[0] == "cancel_update" for row in result.ledger):
      expected_fields = stored_fields(1, 0x8111, 3)
      self.assertEqual(details(queued), (
        record("cache", "stored", **expected_fields),
        record("queue", "queued", **expected_fields, disconnect=True, hpd_change=True),
      ))
    else:
      self.assertEqual(queued, ())
    workers = tuple(row for row in rows if number(row["worker"]) > 0)
    if result.dispatches:
      self.assertEqual(details(workers), expected_worker_records(Worker(
        changed=1, data_changed=0x8111, connector=int(bool(flags & CONNECTOR)),
      )))
      self.assertTrue(all(row["worker"] == 1 for row in workers))
    else:
      self.assertEqual(workers, ())
    return result

  def check_worker(self, case: Worker) -> Observation:
    result = self.paired(case.arguments())
    expected, state, partner_kind, identity = expected_worker(case)
    self.assertEqual(result.ledger, tuple(expected), "independent worker operation ledger")
    self.assertEqual(result.state, state)
    self.assertEqual((result.partner, result.identity), (partner_kind, identity))
    self.assertEqual(result.snapshot[:5], (
      case.status, case.power_mode << 2, case.data, 0, 0,
    ), "worker must clear only the queued masks after using their snapshot")
    rows = source_records(result.records)
    if result.board_match and result.target_match:
      self.assertEqual(details(rows), expected_worker_records(case))
      self.assertEqual(result.diagnostic_counts[:2], (1, 1))
      self.assertEqual(result.tail, (1, 0))
      self.assertTrue(all((row["gen"], row["worker"]) == (1, 1) for row in rows))
    else:
      self.assertEqual(rows, ())
      self.assertEqual(result.diagnostic_counts, (0, 0, 0))
    return result

  def test_required_init_entry_record(self) -> None:
    result = self.check_init(0, NORMAL | DURING_IRQ)
    self.assertTrue(result.board_match and result.target_match)
    self.assertEqual(result.dispatches, 1)
    self.assertEqual(entry_count(result, "init"), 1, "missing actual T1 init.begin record")

  def test_required_worker_entry_record(self) -> None:
    result = self.check_init(0, NORMAL | DURING_IRQ)
    self.assertTrue(result.board_match and result.target_match)
    self.assertEqual(result.dispatches, 1)
    self.assertEqual(entry_count(result, "worker"), 1, "missing actual T1 worker.begin record")

  def test_init_exact_failures_and_unwind(self) -> None:
    for failure in range(1, 15):
      with self.subTest(failure=failure):
        flags = NORMAL | (PATCH if failure == 6 else 0)
        self.check_init(failure, flags)
        if failure >= 7:
          self.check_init(failure, flags | CLEANUP_ERROR)

  def test_init_optional_branches_and_connect_contract(self) -> None:
    for flags in (
      NORMAL, NORMAL | RESET, NORMAL | TPS25750, NORMAL | NO_POWER,
      NORMAL | PATCH, NORMAL | WAKEUP, NORMAL & ~CONNECTOR, NORMAL & ~ATTACHED,
      NORMAL & ~IRQ, (NORMAL & ~IRQ) | WAKEUP,
      NORMAL | CONNECT_ERROR, (NORMAL & ~IRQ) | CONNECT_ERROR,
      NORMAL | SCHEDULE_FALSE, NORMAL | DURING_IRQ,
    ):
      with self.subTest(flags=flags):
        self.check_init(0, flags)
    result = self.check_init(14, NORMAL | DURING_IRQ)
    self.assertEqual(result.dispatches, 1, "existing init failure can follow queued work")
    self.assertNotIn("cancel_update", [row[0] for row in result.ledger[-6:]])

  def test_queue_full_snapshots_and_accumulated_edges(self) -> None:
    result = self.paired(("queue",))
    self.assertEqual(result.ledger, ())
    initial = (1, 12, 0x8010, 1, 0x8010, 10, 11, 12, 13, 14, 15,
               1, 21, 22, 23, 24, 2, 31, 32, 33, 34, 3, 41, 42)
    latest = (1, 4, 0x8010, 1, 0x8010, 110, 111, 112, 113, 114, 115,
              1, 121, 122, 123, 124, 2, 131, 132, 133, 134, 3, 141, 142)
    self.assertEqual(result.snapshots, (initial, initial, latest))
    self.assertEqual(result.snapshot, latest)

  def test_connect_order_delay_and_ignored_schedule_return(self) -> None:
    for pending in (0, 1):
      for false_schedule in (0, 1):
        with self.subTest(pending=pending, false_schedule=false_schedule):
          result = self.paired(("connect", str(pending), str(false_schedule)))
          self.assertEqual(result.result, 0)
          self.assertEqual(result.ledger, (
            event("cancel_update", 1, 1, 1), event("schedule_update", 500),
          ))
          self.assertEqual(result.snapshot[:5], (1, 12, 16, 1, 16))
          self.assertEqual(result.pending, (1, 0))

  def test_mux_all_modes_pins_precedence_skips_and_errors(self) -> None:
    cases: list[tuple[int, int, int, int]] = [
      (0, 0, 0, 1), (0, 1, 2, 1), (1, 0, 0, 1), (1, 0, 1, 1),
      (0x10001, 0, 0, 1), (0x10001, 2, 2, 1),
      (0x900001, 0, 0, 1), (0x900001, 0, 4, 1),
      (0x810100, 1, 2, 1), (0x810101, 0, 0, 1),
      (0x810001, 0, 0, 1),
    ]
    for pin in range(8):
      data = 0x101 | ((pin >> 1) << 10) | ((pin & 1) << 5)
      cases.append((data, 0, 0, 1))
      if pin in (0, 1, 2, 3, 4, 6):
        selected = {0: 6, 1: 7, 2: 4, 3: 5, 4: 2, 6: 3}[pin]
        cases.append((data, 1, selected, 1))
    for data, alt, mode, payload in cases:
      for error in (0, -5):
        with self.subTest(data=data, alt=alt, mode=mode, error=error):
          result = self.paired(("mode", *(str(value) for value in (
            data, alt, mode, payload, error, 0,
          ))))
          expected, state = expected_mux(data, alt, mode, payload)
          self.assertEqual(result.ledger, tuple(expected))
          self.assertEqual(result.state, state)

  def test_worker_roles_disconnects_and_current_cache_direction(self) -> None:
    for old_role in (0, 1, 2):
      for disconnected in (0, 1):
        for cached in (0x8111, 0x8191, 0):
          with self.subTest(role=old_role, changed=disconnected, cached=cached):
            self.check_worker(Worker(old_role=old_role, changed=disconnected, cached_data=cached))
    self.check_worker(Worker(data=0x8101, cached_data=0x8191, old_role=1))
    self.check_worker(Worker(status=0xF1))

  def test_worker_hpd_call_and_skip_matrix(self) -> None:
    for connector in (0, 1):
      for high in (0, 1):
        for changed in (0, 1):
          with self.subTest(connector=connector, high=high, changed=changed):
            self.check_worker(Worker(
              connector=connector, data=0x111 | (high << 15), data_changed=changed << 15,
            ))

  def test_worker_partner_terminals_and_identity(self) -> None:
    for partner_kind in (0, 1, 2):
      self.check_worker(Worker(status=0, partner=partner_kind))
      for power in (0, 3):
        for changed in (0, 1):
          with self.subTest(partner=partner_kind, power=power, identity=changed):
            self.check_worker(Worker(
              partner=partner_kind, power_mode=power, changed_identity=changed,
            ))
      self.check_worker(Worker(partner=partner_kind, changed=1))
    self.check_worker(Worker(partner_error=1))
    self.check_worker(Worker(partner=1, changed=1, partner_error=1))

  def test_worker_mux_and_role_errors_do_not_suppress_hpd(self) -> None:
    for case in (
      Worker(alt=1, mode=6),
      Worker(data=0x8921),  # Invalid DP pin encoding five.
      Worker(role_result=-5, mux_result=-5, old_role=2, data_changed=0x8000),
      Worker(data=0x8000, mode=1, role_result=-5),
    ):
      self.check_worker(case)

  def test_real_of_fixture_and_rejected_target_operation_invariance(self) -> None:
    reference = self.check_init(0, NORMAL)
    for kind in range(1, 12):
      with self.subTest(kind=kind):
        result = self.check_init(0, NORMAL, kind)
        self.assertEqual(result.ledger, reference.ledger)
        self.assertEqual(result.board_match, kind not in (2, 11))
        self.assertEqual(result.target_match, kind in (1, 2))

  def test_pin_and_extraction_drift_are_setup_errors(self) -> None:
    altered = WORK / "deliberate-source-drift.c"
    with altered.open("x", encoding="utf-8") as stream:
      stream.write(self.harness.core + "\n/* deliberate test drift */\n")
    with self.assertRaisesRegex(SetupError, "input drift"):
      pinned(altered, CORE_SHA256)
    for signature in FUNCTIONS:
      with self.subTest(signature=signature):
        extracted = function(self.harness.core, signature)
        self.assertTrue(extracted.startswith(signature))
        self.assertTrue(extracted.endswith("\n}\n"))
        with self.assertRaisesRegex(SetupError, "missing or duplicate"):
          function(self.harness.core + extracted, signature)
        with self.assertRaisesRegex(SetupError, "missing or duplicate"):
          function(self.harness.core.replace(signature, "changed_signature(", 1), signature)

  def test_exact_source_scope_and_helper_extraction(self) -> None:
    candidate = self.harness.subject_core
    block = helpers(candidate)
    with self.assertRaisesRegex(SetupError, "missing or duplicate"):
      helpers(candidate + block)
    with self.assertRaisesRegex(SetupError, "missing or duplicate"):
      helpers(candidate.replace(HELPERS_BEGIN, "/* changed boundary */\n", 1))
    with self.assertRaisesRegex(SetupError, "helper boundary order"):
      helpers(HELPERS_END + HELPERS_BEGIN)
    for name in ("tipd_sn201202x_data", "tipd_tps6598x_data", "tipd_tps25750_data"):
      anchor = f"const struct tipd_data {name} = {{"
      self.assertEqual(declaration(candidate, anchor), declaration(self.harness.core, anchor))
    self.assertEqual(function(candidate, "static int cd321x_connect("),
                     function(self.harness.core, "static int cd321x_connect("))
    restored = candidate.replace(block + "\n", "", 1)
    self.assertEqual(restored.count("#include <linux/atomic.h>\n"), 1)
    restored = restored.replace("#include <linux/atomic.h>\n", "", 1)
    for signature in FUNCTIONS:
      restored = restored.replace(function(restored, signature), function(self.harness.core, signature), 1)
    anchor = "const struct tipd_data tipd_cd321x_data = {"
    table = declaration(restored, anchor)
    self.assertEqual(table.count("sizeof(struct tipd_t1_cd321x)"), 1)
    self.assertEqual(table.replace("sizeof(struct tipd_t1_cd321x)", "sizeof(struct cd321x)"),
                     declaration(self.harness.core, anchor))
    restored = restored.replace(table, declaration(self.harness.core, anchor), 1)
    self.assertEqual(restored, self.harness.core, "all other original source bytes must remain exact")
    self.assertEqual({key: value for key, value in SUBJECT_PINS.items() if key != "core.c"},
                     {key: value for key, value in CONTROL_PINS.items() if key != "core.c"})

  def test_real_target_variant_wrapper_and_reference_matrix(self) -> None:
    for kind in range(23):
      for variant in range(5):
        with self.subTest(kind=kind, variant=variant):
          result = self.harness.inspect(("guard", str(kind), str(variant)))
          rows = source_records(result.records)
          self.assertEqual(result.ledger, ())
          self.assertEqual(result.wrapper_offset, 0)
          self.assertEqual(result.tail_offset, result.prefix_bytes)
          self.assertGreater(result.wrapper_bytes, result.prefix_bytes)
          eligible = variant == 0 and kind in (0, 1)
          if eligible:
            self.assertEqual(result.counts, (1, 1, 2))
            self.assertEqual(result.contexts, ((1, 0), (1, 0), (1, 1), (1, 0)))
            self.assertEqual(details(rows), (
              record("cache", "stored", **stored_fields(0, 0, 0)),
              record("worker", "end", reason="complete", ret=0),
            ))
            self.assertGreater(result.conversions, 0)
            self.assertGreater(result.refs[0], 1)
          else:
            self.assertEqual(result.counts, (0, 0, 0), "rejects must not consume any counter")
            self.assertEqual(result.contexts, ((0, 0),) * 4)
            self.assertEqual(rows, ())
          if variant:
            self.assertEqual(result.conversions, 0, "exact variant check must precede wrapper conversion")
            self.assertEqual(result.refs, (0, 0), "non-CD variants must not inspect the OF tree")
          elif kind in (4, 10):
            self.assertEqual(result.refs, (1, 1), "null node permits board-root reference only")
          elif kind in (11, 22):
            self.assertEqual(result.refs, (0, 0), "absent root must fail board check")

  def test_target_rejection_preserves_full_paths_and_lookup_is_init_only(self) -> None:
    reference = self.check_init(0, NORMAL)
    with_worker = self.check_init(0, NORMAL | DURING_IRQ)
    self.assertEqual(with_worker.production_refs, reference.production_refs,
                     "queue, worker and mux must add no OF lookup")
    for kind in range(2, 23):
      with self.subTest(kind=kind):
        result = self.check_init(0, NORMAL, kind)
        self.assertEqual(result.ledger, reference.ledger)
        self.assertEqual(result.records, ())
        worker = self.check_worker(Worker(metadata=kind))
        self.assertEqual(worker.records, ())
        mode = self.paired(("mode", "33041", "0", "0", "1", "-5", str(kind)))
        expected, state = expected_mux(33041, 0, 0, 1)
        self.assertEqual(mode.ledger, tuple(expected))
        self.assertEqual(mode.state, state)
        self.assertEqual(mode.records, ())

  def test_cache_queue_and_connect_record_snapshots(self) -> None:
    result = self.paired(("queue",))
    expected: list[dict[str, Scalar]] = []
    for status, data, power in ((1, 0x8010, 3), (1, 0x8010, 3), (0, 0, 3), (1, 0x8010, 1)):
      fields = stored_fields(status, data, power)
      expected.extend((record("cache", "stored", **fields),
                       record("queue", "queued", **fields, disconnect=True, hpd_change=True)))
    rows = source_records(result.records)
    self.assertEqual(details(rows), tuple(expected))
    self.assertTrue(all((row["gen"], row["worker"]) == (1, 0) for row in rows))
    self.assertEqual(result.diagnostic_counts, (1, 0, 8))
    for pending in (0, 1):
      for false_schedule in (0, 1):
        with self.subTest(pending=pending, false_schedule=false_schedule):
          connected = self.paired(("connect", str(pending), str(false_schedule)))
          self.assertEqual(details(source_records(connected.records)), (
            record("cache", "stored", **stored_fields(1, 0x10, 3)),
            record("queue", "queued", **stored_fields(1, 0x10, 3), disconnect=True, hpd_change=False),
          ))
          self.assertEqual(connected.diagnostic_counts, (1, 0, 2))

  def test_init_retries_two_instances_and_permitted_worker_overlap(self) -> None:
    result = self.harness.inspect(("retry",))
    rows = source_records(result.records)
    self.assertEqual(result.outcomes, (-5, 0, 0))
    self.assertEqual(result.contexts, ((1, 0), (2, 0), (3, 0), (2, 0)))
    self.assertEqual(result.counts[:2], (3, 2))
    self.assertEqual(result.counts[2], len(rows))
    failed, _ = expected_init(1, NORMAL | DURING_IRQ)
    success, _ = expected_init(0, NORMAL | DURING_IRQ)
    self.assertEqual(result.ledger, tuple(failed + success + success))
    for generation, worker in ((1, 0), (2, 1), (3, 2)):
      selected = tuple(row for row in rows if row["gen"] == generation)
      self.assertEqual(details(selected[:1]), (record("init", "begin"),))
      self.assertEqual(details(selected[-1:]), (
        record("init", "end", reason="gpio" if generation == 1 else "complete",
               ret=-5 if generation == 1 else 0),
      ))
      active = tuple(row for row in selected if number(row["worker"]) > 0)
      if worker:
        self.assertEqual(details(active), expected_worker_records(Worker(changed=1, data_changed=0x8111)))
        self.assertTrue(all(row["worker"] == worker for row in active))
        self.assertLess(number(active[-1]["seq"]), number(selected[-1]["seq"]),
                        "worker may finish before init.end")
      else:
        self.assertEqual(active, ())
    one_init = self.harness.inspect(("guard", "0", "0"))
    self.assertEqual(result.refs, tuple(3 * value for value in one_init.refs))

  def test_automatic_cap_when_normal_127_is_terminal(self) -> None:
    result = self.harness.inspect(("cap_terminal",))
    rows = source_records(result.records)
    self.assertEqual(result.counts, (1, 1, 128))
    self.assertEqual(result.ledger, ())
    self.assertEqual(details(rows[-2:]), (
      record("worker", "end", reason="complete", ret=0),
      record("cap", "end", limit=128, reason="budget"),
    ))
    self.assertEqual([(row["seq"], row["gen"], row["worker"]) for row in rows[-2:]],
                     [(127, 1, 1), (128, 1, 1)])
    with self.assertRaisesRegex(SetupError, "127 requires automatic cap"):
      source_records(result.records[:-1])
    with self.assertRaisesRegex(SetupError, "sequence gap/duplicate"):
      source_records(result.records[:-1] + result.records[-2:-1])

  def test_parallel_cap_and_print_arrival_reordering(self) -> None:
    for reordered in (0, 1):
      with self.subTest(reordered=reordered):
        result = self.harness.inspect(("parallel", str(reordered)))
        rows = source_records(result.records)
        self.assertEqual(result.counts, (1, 0, 128))
        self.assertEqual(result.ledger, ())
        normal = tuple(row for row in rows if row["event"] != "cap")
        self.assertEqual(details(normal), (record("cache", "stored", **stored_fields(0, 0, 0)),) * 127)
        self.assertTrue(all((row["gen"], row["worker"]) == (1, 0) for row in rows))
        if reordered:
          arrival = [row["seq"] for row in rows]
          self.assertLess(arrival.index(2), arrival.index(1), "reservation order is not printk arrival order")

  def test_exhausted_logging_preserves_original_operations(self) -> None:
    cases = [
      ("init", "0", str(NORMAL | DURING_IRQ), "0"),
      ("init", "14", str(NORMAL | DURING_IRQ), "0"),
      Worker(old_role=2, role_result=-5, mux_result=-5, data_changed=0x8000).arguments(),
      Worker(status=0, partner=0).arguments(), Worker(partner_error=1).arguments(),
      ("mode", "33041", "0", "0", "1", "-5", "0"),
      ("mode", "35105", "0", "0", "1", "0", "0"),
    ]
    for arguments in cases:
      with self.subTest(arguments=arguments):
        reference = self.paired(arguments)
        capped = self.paired((arguments[0] + "_cap", *arguments[1:]))
        for name in ("result", "ledger", "snapshot", "snapshots", "state", "partner",
                     "identity", "pending", "dispatches"):
          self.assertEqual(getattr(capped, name), getattr(reference, name), f"capped original {name}")
        rows = source_records(capped.records)
        self.assertEqual(capped.diagnostic_counts[2], 128)
        self.assertEqual(sum(row["event"] == "cap" for row in rows), 1)
        self.assertTrue(all(row["event"] in ("cache", "cap") for row in rows),
                        "the complete original function still runs after output is exhausted")

  def test_counter_limits_do_not_emit_stale_or_zero_worker_records(self) -> None:
    result = self.harness.inspect(("limits",))
    rows = source_records(result.records)
    maximum = 0x7FFFFFFF
    self.assertEqual(result.counts[:2], (maximum, maximum))
    self.assertEqual(result.contexts, ((maximum, 0), (maximum, 0), (0, 0)))
    self.assertEqual(result.counts[2], len(rows))
    self.assertTrue(all((row["gen"], row["worker"]) == (maximum, maximum) for row in rows))
    case = Worker(status=0, data=0, cached_data=0, power_mode=0, connector=0)
    self.assertEqual(details(rows), expected_worker_records(case))
    operations, _, _, _ = expected_worker(case, payload=0)
    mux, _ = expected_mux(1, 0, 0, 0)
    self.assertEqual(result.ledger, tuple(operations + mux),
                     "artificial counter exhaustion must still preserve every original operation")


if __name__ == "__main__":
  unittest.main(verbosity=2)
