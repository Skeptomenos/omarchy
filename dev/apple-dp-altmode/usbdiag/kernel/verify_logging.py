"""Offline checks of the exact diagnostic log macros and reservation bodies.

Run only as a workload of the reviewed private sandbox. The generated C uses
unchanged producer fragments, a C11 atomic shim, and a userspace output shim.
This checks counter/format logic. It does not exercise Linux atomic primitives,
kernel printk scheduling, device operations, or hardware behavior.
"""

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess


PINS = {
  "dwc3": ("dwc3-apple.c", "2ce7c85eb7d5324d13629a1030436d8350cb426cd646cf43cd40c0dbd8c1c752"),
  "atc": ("atc.c", "852f5d8e19894473390fc74464496029e20ef440aef37618cf530264b49cb113"),
}
LINK_PINS = {
  "libgcc_s_asneeded.so": "10bc094393cfacd92e7683eff066803c7c5bfd51ac8ee8eb7b57847a4c9b3ebb",
  "libatomic_asneeded.so": "7006f9f3ea0a199cca99d3646c3a7ebd5aa0fea2d45894c205cdb6eab4b4a7de",
  "libatomic.so": "e4e026a2b4d66f9d57c08645dea91ae9d36ebcbea55b34cf2357f312a8682495",
  "libatomic.so.1": "e4e026a2b4d66f9d57c08645dea91ae9d36ebcbea55b34cf2357f312a8682495",
}
LITERAL = re.compile(r'"(?:[^"\\]|\\.)*"')
CHILD_INDEX = 0
SHIM = r"""
#include <assert.h>
#include <limits.h>
#include <pthread.h>
#include <stdarg.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef _Atomic int atomic_t;
#define ATOMIC_INIT(value) (value)
#define static_assert _Static_assert

/* A userspace model of this API's return/update contract, not kernel code. */
static int atomic_fetch_add_unless(atomic_t *counter, int amount, int unless)
{
  int previous = atomic_load(counter);
  while (previous != unless &&
         !atomic_compare_exchange_weak(counter, &previous, previous + amount)) {}
  return previous;
}

static pthread_mutex_t output_lock = PTHREAD_MUTEX_INITIALIZER;
static unsigned int records;

static void log_info(const char *format, ...)
  __attribute__((format(printf, 1, 2)));
static void log_info(const char *format, ...)
{
  char line[384];
  va_list args;
  va_start(args, format);
  int length = vsnprintf(line, sizeof(line), format, args);
  va_end(args);
  if (length < 1 || length >= (int)sizeof(line) || line[length - 1] != '\n')
    abort();
  if (pthread_mutex_lock(&output_lock))
    abort();
  if (++records > 512 || fwrite(line, 1, (size_t)length, stdout) != (size_t)length)
    abort();
  if (pthread_mutex_unlock(&output_lock))
    abort();
}
#define pr_info(...) log_info(__VA_ARGS__)
"""
STRESS = r"""
static void *worker(void *ignored)
{
  (void)ignored;
  for (unsigned int iteration = 0; iteration < 1000; iteration++) {
    DEV147_DWC3_LOG(1U, 1U, "probe", "begin", "");
    DEV147_ATC_LOG(1U, "probe", "begin", "");
  }
  return NULL;
}

static void stress(void)
{
  pthread_t threads[8];
  atomic_store(&dev147_dwc3_sequence, 0);
  atomic_store(&dev147_atc_sequence, 0);
  for (unsigned int index = 0; index < 8; index++)
    if (pthread_create(&threads[index], NULL, worker, NULL))
      abort();
  for (unsigned int index = 0; index < 8; index++)
    if (pthread_join(threads[index], NULL))
      abort();
  if (atomic_load(&dev147_dwc3_sequence) != 128 ||
      atomic_load(&dev147_atc_sequence) != 128 || records != 256)
    abort();
  /* Further calls must keep both budgets saturated without any more output. */
  worker(NULL);
  if (atomic_load(&dev147_dwc3_sequence) != 128 ||
      atomic_load(&dev147_atc_sequence) != 128 || records != 256)
    abort();
}
"""


def require(condition: bool, message: str) -> None:
  if not condition:
    raise RuntimeError(message)


def isolated() -> None:
  require(os.getuid() == 1001 and os.getgid() == 1001, "unexpected workload identity")
  require(Path.cwd() == Path("/work"), "not in private workload directory")
  require(not any(Path(path).exists() for path in (
    "/proc", "/sys", "/run", "/boot", "/home",
  )), "host tree visible")


def arguments(text: str, start: int) -> list[str]:
  """Split the pinned call without evaluating any C expression."""
  result: list[str] = []
  nesting = 1
  quoted = escaped = False
  begin = start
  for index in range(start, len(text)):
    char = text[index]
    if quoted:
      if escaped:
        escaped = False
      elif char == "\\":
        escaped = True
      elif char == '"':
        quoted = False
      continue
    if char == '"':
      quoted = True
    elif char in "([{":
      nesting += 1
    elif char in ")]}":
      nesting -= 1
      if nesting == 0:
        require(char == ")", "bad call terminator")
        result.append(text[begin:index].strip())
        return result
    elif char == "," and nesting == 1:
      result.append(text[begin:index].strip())
      begin = index + 1
  raise RuntimeError("unterminated log call")


def literal(expression: str) -> str:
  parts = LITERAL.findall(expression)
  require(bool(parts) and not LITERAL.sub("", expression).strip(), "nonliteral log field")
  return "".join(json.loads(part) for part in parts)


def fragments(component: str, source: str) -> str:
  upper = component.upper()
  prefix = f"DEV147_{upper}"
  lower = f"dev147_{component}"
  # These fixed boundaries deliberately fail on producer layout drift.
  constants = source[source.index(f"#define {prefix}_LIMIT"):
                     source.index(f"static atomic_t {lower}_generations")]
  reserve = source[source.index(f"static unsigned int {lower}_reserve"):
                   source.index("/*\n * Only literal")]
  macro_start = source.index(f"#define {prefix}_LOG")
  bool_start = source.index(f"#define {prefix}_BOOL")
  macros = source[macro_start:source.index("\n", bool_start) + 1]
  return constants + reserve + macros


def format_cases(component: str, source: str) -> tuple[list[str], list[dict[str, object]]]:
  upper = component.upper()
  macro = f"DEV147_{upper}_LOG"
  generated: list[str] = []
  expected: list[dict[str, object]] = []
  prefix_conversions = 3 if component == "dwc3" else 2
  event_index = prefix_conversions - 1
  for match in re.finditer(rf"\b{macro}\(", source):
    line_begin = source.rfind("\n", 0, match.start()) + 1
    if source[line_begin:match.start()].lstrip().startswith("#define"):
      continue
    args = arguments(source, match.end())
    event, phase, fields = (
      literal(args[event_index]), literal(args[event_index + 1]),
      literal(args[event_index + 2]),
    )
    conversions = re.findall(r"%(.)", fields)
    require("%" not in re.sub(r"%[uds]", "", fields), "unsupported format")
    require(len(conversions) + prefix_conversions <= 8, "conversion budget exceeded")
    require(len(args[event_index + 3:]) == len(conversions), "vararg count mismatch")
    require(all(item in "uds" for item in conversions), "unsupported scalar")
    values = [
      "UINT_MAX" if item == "u" else "INT_MIN" if item == "d"
      else f"DEV147_{upper}_BOOL(0)" for item in conversions
    ]
    fixed = ["UINT_MAX"] * (prefix_conversions - 1)
    fixed += args[event_index:event_index + 3]
    generated.append(f"  atomic_store(&dev147_{component}_sequence, 126);")
    generated.append(f"  {macro}({', '.join(fixed + values)});")
    expected.append({
      "component": component, "event": event, "phase": phase,
      "conversions": len(conversions) + prefix_conversions,
    })
  require(bool(expected), "no actual call sites found")
  return generated, expected


def checked_run(command: list[str]) -> bytes:
  global CHILD_INDEX
  prefix = Path(f"/work/child-{CHILD_INDEX:02d}")
  CHILD_INDEX += 1
  try:
    result = subprocess.run(command, check=False, capture_output=True, timeout=30,
                            env=dict(os.environ, LD_LIBRARY_PATH="/inputs/link-runtime"))
  except subprocess.TimeoutExpired as error:
    with prefix.with_suffix(".timeout.json").open("x", encoding="ascii") as stream:
      json.dump({"command": command, "timed_out": True}, stream)
    for suffix, payload in ((".stdout", error.stdout), (".stderr", error.stderr)):
      with prefix.with_suffix(suffix).open("xb") as stream:
        stream.write(payload or b"")
    raise
  for suffix, payload in ((".stdout", result.stdout), (".stderr", result.stderr)):
    with prefix.with_suffix(suffix).open("xb") as stream:
      stream.write(payload)
  with prefix.with_suffix(".result.json").open("x", encoding="ascii") as stream:
    json.dump({"command": command, "exit_code": result.returncode, "timed_out": False}, stream)
  require(result.returncode == 0, "workload child failed")
  require(result.stderr == b"", "workload child wrote stderr")
  require(len(result.stdout) <= 512 * 384, "unexpected child output size")
  return result.stdout


def parsed(raw: bytes) -> list[dict[str, object]]:
  lines = raw.splitlines(keepends=True)
  require(all(line.endswith(b"\n") and len(line) < 384 for line in lines), "record bound")
  records: list[dict[str, object]] = []
  for line in lines:
    item = json.loads(line.decode("ascii"))
    require(isinstance(item, dict), "record must be an object")
    require(item["revision"] == "dev147-usbdiag1-v1", "revision changed")
    require(item["board"] == "j413" and item["target"] == "front_lower", "target changed")
    records.append(item)
  return records


def main() -> None:
  isolated()
  for name, digest in LINK_PINS.items():
    require(hashlib.sha256((Path("/inputs/link-runtime") / name).read_bytes()).hexdigest() == digest,
            "link runtime hash drift")
  dynamic = checked_run(["/usr/bin/readelf", "-d", "/inputs/link-runtime/libatomic.so"])
  needed = set(re.findall(rb"Shared library: \[([^]]+)\]", dynamic))
  require(needed <= {b"libc.so.6", b"libgcc_s.so.1", b"ld-linux-aarch64.so.1"},
          "unreviewed libatomic dependency")
  require(b"(RPATH)" not in dynamic and b"(RUNPATH)" not in dynamic, "unexpected library search override")
  fragments_to_compile: list[str] = [SHIM]
  calls: list[str] = []
  expected: list[dict[str, object]] = []
  for component, (name, digest) in PINS.items():
    path = Path("/inputs/kernel") / name
    require(path.stat().st_size < 256 * 1024, "source exceeds bound")
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == digest, "source hash drift")
    source = raw.decode("ascii")
    fragments_to_compile.append(fragments(component, source))
    generated, cases = format_cases(component, source)
    calls.extend(generated)
    expected.extend(cases)
  calls += [
    "  atomic_store(&dev147_dwc3_sequence, 127);",
    "  (void)dev147_dwc3_reserve(UINT_MAX, UINT_MAX);",
    "  atomic_store(&dev147_atc_sequence, 127);",
    "  (void)dev147_atc_reserve(UINT_MAX);",
  ]
  format_function = "static void format_cases(void)\n{\n" + "\n".join(calls) + "\n}\n"
  entry = r"""
int main(int argc, char **argv)
{
  DEV147_DWC3_LOG(0U, UINT_MAX, "probe", "begin", "");
  DEV147_ATC_LOG(0U, "probe", "begin", "");
  if (records || atomic_load(&dev147_dwc3_sequence) ||
      atomic_load(&dev147_atc_sequence))
    abort();
  if (argc != 2)
    abort();
  if (!strcmp(argv[1], "format"))
    format_cases();
  else if (!strcmp(argv[1], "stress"))
    stress();
  else
    abort();
  return fflush(stdout) ? EXIT_FAILURE : EXIT_SUCCESS;
}
"""
  with Path("/work/logging-harness.c").open("x", encoding="ascii") as stream:
    stream.write("\n".join(fragments_to_compile + [format_function, STRESS, entry]))
  checked_run([
    "/usr/bin/gcc", "-std=gnu11", "-O2", "-Wall", "-Wextra", "-Werror",
    "-pthread", "-L/inputs/link-runtime", "/work/logging-harness.c", "-o", "/work/logging-harness",
  ])
  dynamic = checked_run(["/usr/bin/readelf", "-d", "/work/logging-harness"])
  needed = set(re.findall(rb"Shared library: \[([^]]+)\]", dynamic))
  require(needed <= {b"libc.so.6", b"libgcc_s.so.1", b"libatomic.so.1", b"ld-linux-aarch64.so.1"},
          "unreviewed harness dependency")
  require(b"(RPATH)" not in dynamic and b"(RUNPATH)" not in dynamic, "unexpected harness search override")
  raw = checked_run(["/work/logging-harness", "format"])
  with Path("/work/format-records.jsonl").open("xb") as stream:
    stream.write(raw)
  records = parsed(raw)
  require(len(records) == len(expected) + 2, "wrong format output count")
  for actual, case in zip(records[:-2], expected, strict=True):
    for key in ("component", "event", "phase"):
      require(actual[key] == case[key], "wrong actual macro record")
    require(actual["generation"] == (1 << 32) - 1 and actual["seq"] == 127, "integer width")
    if actual["component"] == "dwc3":
      require(actual["attempt"] == (1 << 32) - 1, "attempt width")
  for item in records[-2:]:
    require(item["event"] == "capture_capped" and item["seq"] == 128, "cap format")
    require(item["generation"] == (1 << 32) - 1, "cap generation width")
  for iteration in range(10):
    raw_stress = checked_run(["/work/logging-harness", "stress"])
    with Path(f"/work/stress-{iteration:02d}.jsonl").open("xb") as stream:
      stream.write(raw_stress)
    stress_records = parsed(raw_stress)
    require(len(stress_records) == 256, "wrong total component budgets")
    for component in PINS:
      own = [item for item in stress_records if item["component"] == component]
      require(len(own) == 128, "wrong component budget")
      require({item["seq"] for item in own} == set(range(1, 129)), "duplicate/missing reservation")
      caps = [item for item in own if item["event"] == "capture_capped"]
      require(len(caps) == 1 and caps[0]["seq"] == 128, "wrong cap count")
  print(json.dumps({
    "level": "info", "check": "producer_logging", "verdict": "PASS",
    "actual_call_sites": len(expected),
    "maximum_conversions": max(int(item["conversions"]) for item in expected),
    "maximum_record_bytes_with_newline": max(len(line) for line in raw.splitlines(keepends=True)),
    "component_budget": 128, "cap_markers_per_component": 1,
    "concurrency_rounds": 10, "threads_per_round": 8,
    "kernel_primitives_or_hardware_executed": False,
  }, sort_keys=True))


if __name__ == "__main__":
  main()
