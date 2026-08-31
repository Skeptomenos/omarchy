from __future__ import annotations

import ast
import importlib.util
import io
import os
import signal
import struct
import subprocess
import sys
import tempfile
import tokenize
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("capture", Path(__file__).with_name("capture.py"))
if SPEC is None or SPEC.loader is None:
  raise RuntimeError("capture module missing")
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def state() -> MODULE.TraceState:
  return MODULE.TraceState("0123456789abcdef", 42)


def trace_line(kind: str, payload: str, pid: int = 42) -> str:
  return f" python3-{pid} [002] .... 123.000001: {state().event(kind)}: (probe+0x0/0x20) {payload}\n"


def identity_payload() -> str:
  return f"device={0xffff800000000010} bus={0xffff800000000020} sysdev={0xffff800000000030} busnum=17 devnum=2"


def control_line(result: str = "-71") -> str:
  return trace_line("control", f"{identity_payload()} request=6 request_type=128 value=256 index=0 size=18 result={result}")


def format_text(probe: MODULE.Probe) -> str:
  offset = 24 if probe.kind == "control" else 16
  rows = [f"name: {probe.event}", "ID: 42", "format:"]
  rows.extend(("field:unsigned short common_type; offset:0; size:2; signed:0;", "field:unsigned char common_flags; offset:2; size:1; signed:0;", "field:unsigned char common_preempt_count; offset:3; size:1; signed:0;", "field:int common_pid; offset:4; size:4; signed:1;"))
  if probe.kind == "control":
    rows.extend(("field:unsigned long __probe_func; offset:8; size:8; signed:0;", "field:unsigned long __probe_ret_ip; offset:16; size:8; signed:0;"))
  else:
    rows.append("field:unsigned long __probe_ip; offset:8; size:8; signed:0;")
  for field in probe.fields:
    rows.append(f"field:{field.kind} {field.name}; offset:{offset}; size:{field.width}; signed:{int(field.signed)};")
    offset += field.width
  return "\n".join(rows) + "\n"


class ContractTests(unittest.TestCase):
  def test_exact_four_probes_have_no_payload_or_stack_arguments(self) -> None:
    probes = MODULE.probes(state())
    self.assertEqual(tuple(probe.kind for probe in probes), ("discover", "control", "suspend", "resume"))
    self.assertIn("r128:", probes[1].definition)
    self.assertIn("sysdev=+8(+80($arg1)):u64", probes[1].definition)
    for probe in probes:
      self.assertNotIn("$arg7", probe.definition)
      self.assertNotIn("$arg9", probe.definition)
      self.assertNotIn("string", probe.definition)
      self.assertNotIn("stack", probe.definition)
      MODULE.verify_format(format_text(probe), "42\n", probe)

  def test_format_signedness_offsets_and_extra_fields_refuse(self) -> None:
    probe = MODULE.probes(state())[1]
    valid = format_text(probe)
    for bad in (valid.replace("offset:24", "offset:16"), valid.replace("s32 result", "u32 result"), valid.replace("int common_pid", "unsigned int common_pid"), valid + "field:u8 data; offset:70; size:1; signed:0;\n"):
      with self.subTest(bad=bad), self.assertRaises(MODULE.Refusal):
        MODULE.verify_format(bad, "42", probe)

  def test_controller_pointer_filter_is_fixed_numeric(self) -> None:
    self.assertEqual(MODULE.controller_filter(0xffff800000000030), f"sysdev == {0xffff800000000030}")
    for value in (0, -1, 1 << 64, 17, True):
      with self.subTest(value=value), self.assertRaises(MODULE.Refusal):
        MODULE.controller_filter(value)

  def test_discovery_one_own_record_but_profile_may_include_other_calls(self) -> None:
    raw = trace_line("discover", f"device={0xffff800000000030}")
    self.assertEqual(MODULE.parse_discovery(raw, state()), 0xffff800000000030)
    MODULE.verify_profile(f"{state().event('discover')} 8 0\n", (MODULE.probes(state())[0],), discovery=True)
    for bad in (raw * 2, raw.replace("-42 ", "-43 "), raw.replace(str(0xffff800000000030), "0"), raw + "LOST EVENTS\n"):
      with self.subTest(bad=bad), self.assertRaises(MODULE.Refusal):
        MODULE.parse_discovery(bad, state())

  def test_control_result_and_pm_entry_not_success_are_preserved(self) -> None:
    raw = control_line() + trace_line("suspend", identity_payload() + " message=1026")
    parsed = MODULE.parse_measurements(raw, state(), 0xffff800000000030)
    self.assertEqual(parsed.records[0].values[-1], ("result", -71))
    self.assertEqual(parsed.records[1].kind, "suspend")
    self.assertEqual(parsed.records[1].values[-1], ("message", 1026))
    self.assertIn("entry", parsed.limitations)
    MODULE.parse_measurements(control_line("18"), state(), 0xffff800000000030)

  def test_scope_malformed_ranges_and_identity_faults_refuse(self) -> None:
    valid = control_line()
    for bad in (valid.replace(str(0xffff800000000030), str(0xffff800000000040)), valid.replace("busnum=17", "busnum=0"), valid.replace("request=6", "request=256"), valid.replace("result=-71", "result=2147483648"), valid.replace("result=-71", "result=(fault)"), valid + "unparsed\n"):
      with self.subTest(bad=bad), self.assertRaises(MODULE.Refusal):
        MODULE.parse_measurements(bad, state(), 0xffff800000000030)

  def test_loss_and_ambiguous_profiles_refuse(self) -> None:
    probe = MODULE.probes(state())[1]
    MODULE.verify_profile(f"unrelated 1 0\n{probe.event} 4 0\n", (probe,))
    for bad in ("", f"{probe.event} 4 1", f"{probe.event} 4 0\n{probe.event} 4 0"):
      with self.subTest(bad=bad), self.assertRaises(MODULE.Refusal):
        MODULE.verify_profile(bad, (probe,))
    good = "overrun: 0\ncommit overrun: 0\ndropped events: 0\n"
    MODULE.verify_cpu_stats(good)
    for bad in (good.replace("overrun: 0", "overrun: 1", 1), good + "overrun: 0\n", ""):
      with self.subTest(bad=bad), self.assertRaises(MODULE.Refusal):
        MODULE.verify_cpu_stats(bad)

  def test_boundaries_names_cpus_deadlines(self) -> None:
    self.assertEqual(MODULE.remaining_seconds(10.0, 11.0, 15), 14)
    for now in (9.0, 25.0, float("nan"), float("inf")):
      with self.subTest(now=now), self.assertRaises(MODULE.Refusal):
        MODULE.remaining_seconds(10.0, now, 15)
    for token in ("../x", "x" * 16, "0" * 15):
      with self.subTest(token=token), self.assertRaises(MODULE.Refusal):
        MODULE.probes(MODULE.TraceState(token, 42))
    self.assertEqual(len(MODULE.cpu_names(tuple(f"cpu{i}" for i in range(16)))), 16)
    for names in ((), ("cpu0", "cpu0"), ("cpu0", "other"), tuple(f"cpu{i}" for i in range(17))):
      with self.subTest(names=names), self.assertRaises(MODULE.Refusal):
        MODULE.cpu_names(names)

  def test_build_notes_and_public_binding(self) -> None:
    note = struct.pack("<III", 4, 20, 3) + b"GNU\0" + bytes.fromhex(MODULE.KERNEL_BUILD_ID)
    self.assertEqual(MODULE.parse_build_id(note), MODULE.KERNEL_BUILD_ID)
    for value in (note[:-1], note + note, b""):
      with self.subTest(value=value), self.assertRaises(MODULE.Refusal):
        MODULE.parse_build_id(value)
    with self.assertRaises(MODULE.Refusal):
      MODULE.check_release(1.0)

  def test_preflight_mount_and_trace_conflicts(self) -> None:
    mounts = "1 0 0:1 / /sys/kernel/tracing rw - tracefs tracefs rw\n"
    MODULE.verify_mount(mounts)
    for bad in ("", mounts.replace("tracefs", "tmpfs"), mounts + mounts, mounts + "2 1 0:2 / /sys/kernel/tracing/instances rw - tmpfs tmpfs rw\n"):
      with self.subTest(bad=bad), self.assertRaises(MODULE.Refusal):
        MODULE.verify_mount(bad)
    MODULE.verify_trace_idle("nop\n", "0\n", (), "", state())
    for tracer, enabled, instances, definitions in (("function", "0", (), ""), ("nop", "X", (), ""), ("nop", "0", ("other",), ""), ("nop", "0", (), state().group)):
      with self.subTest(tracer=tracer), self.assertRaises(MODULE.Refusal):
        MODULE.verify_trace_idle(tracer, enabled, instances, definitions, state())


class FilesystemTests(unittest.TestCase):
  def setUp(self) -> None:
    self.root = Path(tempfile.mkdtemp(prefix="files-"))
    self.trace = self.root / "tracing"
    self.trace.mkdir(mode=0o700)
    (self.trace / "instances").mkdir(mode=0o700)
    self.evidence = self.root / "evidence"
    self.evidence.mkdir(mode=0o700)
    self.own = state()
    self.files = MODULE.TraceFiles(self.trace, self.evidence, self.own)

  def file(self, path: Path, value: bytes = b"") -> Path:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    path.write_bytes(value)
    path.chmod(0o600)
    return path

  def test_safe_read_rejects_symlink_parent_special_and_oversize(self) -> None:
    path = self.file(self.root / "input", b"abc")
    self.assertEqual(MODULE.read_regular(path, 3), b"abc")
    with self.assertRaises(MODULE.Refusal):
      MODULE.read_regular(path, 2)
    link = self.root / "link"
    link.symlink_to(path)
    fifo = self.root / "fifo"
    os.mkfifo(fifo, 0o600)
    parent = self.root / "parent"
    parent.symlink_to(self.root, target_is_directory=True)
    for bad in (link, fifo, parent / "input", Path("relative")):
      with self.subTest(bad=bad), self.assertRaises(MODULE.Refusal):
        MODULE.read_regular(bad, 8)

  def test_bounded_trace_prefix_is_retained_with_explicit_truncation(self) -> None:
    path = self.file(self.root / "trace", b"abcdef")
    self.assertEqual(MODULE.read_bounded(path, 3), MODULE.BoundedRead(b"abc", True))
    self.assertEqual(MODULE.read_bounded(path, 6), MODULE.BoundedRead(b"abcdef", False))

  def test_action_attempt_is_durable_before_failed_write(self) -> None:
    with self.assertRaises(MODULE.Refusal):
      self.files.perform(MODULE.Action("stop"))
    self.assertEqual(self.own.attempted, [MODULE.Action("stop")])
    journal = sorted(self.evidence.iterdir())
    self.assertEqual(len(journal), 1)
    self.assertIn(b'"phase": "attempted"', journal[0].read_bytes())

  def test_controls_change_only_owned_instance_and_preserve_global_gate(self) -> None:
    global_gate = self.file(self.trace / "tracing_on", b"1\n")
    own_gate = self.file(self.files.instance / "tracing_on", b"1\n")
    self.files.perform(MODULE.Action("stop"))
    self.assertEqual(own_gate.read_bytes(), b"0\n")
    self.assertEqual(global_gate.read_bytes(), b"1\n")
    self.assertEqual(len(tuple(self.evidence.iterdir())), 2)

  def test_append_only_definitions_and_exact_cleanup_selection(self) -> None:
    probe = MODULE.probes(self.own)[1]
    path = self.file(self.trace / "kprobe_events", b"p:other/event unrelated\n")
    self.files.perform(MODULE.Action("define", "control"))
    self.assertEqual(path.read_text(), "p:other/event unrelated\n" + probe.definition + "\n")
    selected = MODULE.cleanup_plan(self.own, path.read_text())
    self.assertEqual(selected[-1], MODULE.Action("undefine", "control"))
    changed = path.read_text().replace("usb_control_msg", "other_function")
    self.assertIn(MODULE.Action("retain", "control"), MODULE.cleanup_plan(self.own, changed))
    self.assertNotIn(MODULE.Action("undefine", "control"), MODULE.cleanup_plan(self.own, changed))

  def test_cleanup_attempts_continue_and_failure_never_passes(self) -> None:
    self.own.instance_created = True
    self.own.attempted = [MODULE.Action("start"), MODULE.Action("enable", "control")]
    self.file(self.trace / "kprobe_events")
    result = MODULE.cleanup(self.files)
    self.assertFalse(result.complete)
    self.assertGreaterEqual(len(result.failures), 2)
    self.assertTrue(any(action.name == "disable" for action in self.own.attempted))
    self.assertTrue(any(action.name == "remove" for action in self.own.attempted))

  def test_cleanup_stops_before_optional_completion_journal(self) -> None:
    self.own.instance_created = True
    self.own.attempted = [MODULE.Action("start"), MODULE.Action("enable", "control")]
    gate = self.file(self.files.instance / "tracing_on", b"1\n")
    event = self.file(self.files.event_root("control") / "enable", b"1\n")
    self.file(self.trace / "kprobe_events")
    self.file(self.evidence / "action-0001.json", b"existing\n")
    result = MODULE.cleanup(self.files)
    self.assertEqual(gate.read_bytes(), b"0\n")
    self.assertEqual(event.read_bytes(), b"0\n")
    self.assertFalse(result.complete)
    self.assertTrue(any("journal:stop:completed" in failure for failure in result.failures))
    for path in self.evidence.iterdir():
      if path.name != "action-0001.json":
        self.assertNotIn(b'"phase": "attempted"', path.read_bytes())

  def test_collision_create_and_fresh_evidence_refuse(self) -> None:
    self.files.instance.mkdir()
    with self.assertRaises((MODULE.Refusal, OSError)):
      self.files.perform(MODULE.Action("create"))
    MODULE.save_new(self.evidence, "same.json", {"status": "first"})
    with self.assertRaises((MODULE.Refusal, OSError)):
      MODULE.save_new(self.evidence, "same.json", {"status": "second"})

  def test_filter_readback_is_required_before_enable(self) -> None:
    self.own.controller = 0xffff800000000030
    event = self.files.event_root("control")
    self.file(event / "filter", b"sysdev == 0\n")
    gate = self.file(event / "enable", b"0\n")
    with self.assertRaises(MODULE.Refusal):
      self.files.perform(MODULE.Action("enable", "control"))
    self.assertEqual(gate.read_bytes(), b"0\n")

  def test_inherited_stack_options_must_be_exactly_disabled(self) -> None:
    kernel_stack = self.file(self.files.instance / "options/stacktrace", b"0\n")
    user_stack = self.file(self.files.instance / "options/userstacktrace", b"0\n")
    MODULE.verify_stack_options(self.files)
    receipt = (self.evidence / "stack-options.json").read_bytes()
    self.assertIn(b'"stacktrace": 0', receipt)
    self.assertIn(b'"userstacktrace": 0', receipt)
    for path in (kernel_stack, user_stack):
      for bad in (b"1\n", b"unknown\n", b"", b"0 \n"):
        kernel_stack.write_bytes(b"0\n")
        user_stack.write_bytes(b"0\n")
        path.write_bytes(bad)
        with self.subTest(path=path, bad=bad), self.assertRaises(MODULE.Refusal):
          MODULE.verify_stack_options(self.files)
      kernel_stack.write_bytes(b"0\n")
      user_stack.write_bytes(b"0\n")
      path.unlink()
      with self.subTest(path=path, missing=True), self.assertRaises(MODULE.Refusal):
        MODULE.verify_stack_options(self.files)
      path.write_bytes(b"0\n")
      path.chmod(0o600)

  def test_interruption_raises_without_cleanup_claim(self) -> None:
    with self.assertRaises(MODULE.Refusal):
      MODULE.interrupted(signal.SIGTERM, None)


class EntrypointTests(unittest.TestCase):
  def test_armed_start_and_flush_share_capture_deadline(self) -> None:
    tree = ast.parse(Path(__file__).with_name("capture.py").read_text())
    runner = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "run_with_deadline")
    window = next(node for node in ast.walk(runner) if isinstance(node, ast.With) and any(isinstance(item.context_expr, ast.Call) and ast.unparse(item.context_expr) == "cooperative_limit(CAPTURE_SECONDS + 1)" for item in node.items))
    window_calls = tuple(ast.unparse(node) for node in ast.walk(window) if isinstance(node, ast.Call))
    self.assertIn("files.perform(Action('start'))", window_calls)
    self.assertTrue(any(call.startswith("phase('ARMED',") for call in window_calls))

  def test_full_stderr_pipe_is_interrupted_by_cooperative_deadline(self) -> None:
    read_fd, write_fd = os.pipe()
    try:
      os.set_blocking(write_fd, False)
      while True:
        try:
          os.write(write_fd, b"x" * 4096)
        except BlockingIOError:
          break
      os.set_blocking(write_fd, True)
      source = "\n".join((
        "import importlib.util, os, signal, sys",
        "spec = importlib.util.spec_from_file_location('capture', '/work/capture.py')",
        "module = importlib.util.module_from_spec(spec)",
        "sys.modules[spec.name] = module",
        "spec.loader.exec_module(module)",
        "signal.signal(signal.SIGALRM, module.interrupted)",
        "try:",
        "  with module.cooperative_limit(0.05):",
        "    module.phase('ARMED', 'blocked pipe fixture')",
        "except module.Refusal:",
        "  os._exit(0)",
        "os._exit(1)",
      ))
      result = subprocess.run(["/usr/bin/python3.14", "-I", "-S", "-B", "-c", source], stdout=subprocess.PIPE, stderr=write_fd, timeout=2, check=False)
      self.assertEqual(result.returncode, 0)
    finally:
      os.close(write_fd)
      os.close(read_fd)

  def test_unreleased_entrypoint_refuses_before_host_io(self) -> None:
    result = subprocess.run(
      ["/usr/bin/python3.14", "-I", "-S", "-B", str(Path(__file__).with_name("capture.py"))],
      capture_output=True,
      check=False,
      timeout=2,
    )
    self.assertEqual(result.returncode, 77)
    self.assertEqual(result.stdout, b"")
    self.assertIn(b"UNRELEASED", result.stderr)

  def test_arguments_and_stdin_do_not_release_helper(self) -> None:
    result = subprocess.run(
      ["/usr/bin/python3.14", "-I", "-S", "-B", "/work/capture.py", "--record", "/sys"],
      input=b"release=true\n",
      capture_output=True,
      check=False,
      timeout=2,
    )
    self.assertEqual(result.returncode, 64)
    self.assertEqual(result.stdout, b"")

  def test_syntax_and_no_code_comments(self) -> None:
    for name in ("capture.py", "test_capture.py"):
      source = Path(__file__).with_name(name).read_bytes()
      ast.parse(source)
      self.assertFalse(any(token.type == tokenize.COMMENT for token in tokenize.tokenize(io.BytesIO(source).readline)))


if __name__ == "__main__":
  unittest.main(verbosity=2)
