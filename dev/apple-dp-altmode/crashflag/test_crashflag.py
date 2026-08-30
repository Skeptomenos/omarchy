"""Offline contracts only. These tests do not validate tracefs or hardware."""

from __future__ import annotations

import os
import signal
import hashlib
import errno
import struct
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from dataclasses import replace
from importlib.util import module_from_spec, spec_from_file_location
from io import StringIO
from pathlib import Path

SPEC = spec_from_file_location("crashflag", Path(__file__).with_name("crashflag.py"))
if SPEC is None or SPEC.loader is None:
  raise RuntimeError("adjacent offline helper unavailable")
MODULE = module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

from crashflag import (  # noqa: E402
  APPLE_BUILD_ID,
  APPLE_MODULE_SHA256,
  EXPECTED_BOOT_SHA256,
  EXPECTED_KERNEL,
  TIPD_BUILD_ID,
  TARGET,
  Action,
  Identity,
  Observation,
  Refusal,
  TraceFiles,
  TraceState,
  _cleanup_deadline,
  _interrupted,
  _preflight,
  cleanup,
  cleanup_actions,
  main,
  parse_build_id,
  parse_event,
  parse_mounts,
  read_regular,
  remaining_seconds,
  sanitize_trace,
  setup_actions,
  verify_cpu_stats,
  verify_format,
  verify_identity,
  verify_profile,
)

BOOT = "a" * 64


def state() -> TraceState:
  return TraceState("dev147_cf_0123456789abcdef", "observe_0123456789abcdef", "dev147_cf_0123456789abcdef", 1234)


def event_line(crashed: str = "1", connector: str = "10", pid: int = 1234) -> str:
  return f" python3-{pid} [002] .... 123.000001: {state().event}: (chunk_color_open+0x1c/0x30 [appledrm]) crashed={crashed} connector_type={connector}\n"


class IdentityTests(unittest.TestCase):
  def test_exact_identity(self) -> None:
    identity = Identity(EXPECTED_KERNEL, BOOT, APPLE_MODULE_SHA256, APPLE_BUILD_ID, TIPD_BUILD_ID)
    verify_identity(identity, BOOT)

  def test_unbound_public_helper_and_every_mismatch_refuse(self) -> None:
    identity = Identity(EXPECTED_KERNEL, BOOT, APPLE_MODULE_SHA256, APPLE_BUILD_ID, TIPD_BUILD_ID)
    for expected in (EXPECTED_BOOT_SHA256, "", "0" * 63):
      with self.subTest(expected=expected), self.assertRaises(Refusal):
        verify_identity(identity, expected)
    for field in ("kernel", "boot_sha256", "module_sha256", "apple_build_id", "tipd_build_id"):
      with self.subTest(field=field), self.assertRaises(Refusal):
        verify_identity(replace(identity, **{field: "wrong"}), BOOT)

  def test_gnu_note_exact(self) -> None:
    note = struct.pack("<III", 4, 20, 3) + b"GNU\0" + bytes.fromhex(APPLE_BUILD_ID)
    self.assertEqual(parse_build_id(note), APPLE_BUILD_ID)
    for bad in (b"", note[:-1], note + b"junk", note.replace(b"GNU", b"BAD")):
      with self.subTest(bad=bad), self.assertRaises(Refusal):
        parse_build_id(bad)

  def test_preexisting_exact_mount_types(self) -> None:
    valid = "1 0 0:1 / /sys/kernel/tracing rw - tracefs tracefs rw\n2 0 0:2 / /sys/kernel/debug rw - debugfs debugfs rw\n"
    parse_mounts(valid)
    for bad in ("", valid.replace("tracefs tracefs", "tmpfs tmpfs"), valid + valid.splitlines()[0] + "\n"):
      with self.subTest(bad=bad), self.assertRaises(Refusal):
        parse_mounts(bad)


class EvidenceTests(unittest.TestCase):
  def test_sanitized_trace_preserves_fingerprint_and_redacts_addresses(self) -> None:
    for raw in (event_line(), "malformed (0xffff800012345678) pointer=ffffabcd12345678 address=0x1234 crashed=1\n"):
      with self.subTest(raw=raw):
        result = sanitize_trace(raw)
        self.assertEqual(result.raw_sha256, hashlib.sha256(raw.encode("ascii")).hexdigest())
        self.assertEqual(result.raw_bytes, len(raw.encode("ascii")))
        self.assertEqual(result.content_label, "sanitized trace, not raw trace")
        self.assertNotIn("chunk_color_open", result.sanitized_text)
        self.assertNotIn("0xffff800012345678", result.sanitized_text)
        self.assertNotIn("ffffabcd12345678", result.sanitized_text)
        self.assertNotIn("0x1234", result.sanitized_text)
        self.assertIn("crashed=1", result.sanitized_text)

  def test_only_one_own_pid_dp_event_with_boolean_flag(self) -> None:
    self.assertEqual(parse_event("# tracer: nop\n" + event_line(), state()), Observation(1, 10, 1234))
    self.assertEqual(parse_event(event_line("0"), state()), Observation(0, 10, 1234))
    for bad in ("", event_line() * 2, event_line("2"), event_line(connector="14"), event_line(pid=999), event_line("(fault)"), event_line() + "lost events\n"):
      with self.subTest(bad=bad), self.assertRaises(Refusal):
        parse_event(bad, state())

  def test_profile_requires_unique_single_hit_zero_misses(self) -> None:
    name = state().event
    verify_profile(f"unrelated/e 7 0\n{name} 1 0\n", state())
    for bad in ("", f"{name} 0 0", f"{name} 2 0", f"{name} 1 1", f"{name} 1 0\n{name} 1 0"):
      with self.subTest(bad=bad), self.assertRaises(Refusal):
        verify_profile(bad, state())

  def test_cpu_stats_all_loss_counters_present_and_zero(self) -> None:
    valid = "entries: 1\noverrun: 0\ncommit overrun: 0\nbytes: 80\noldest event ts: 1\nnow ts: 2\ndropped events: 0\nread events: 0\n"
    verify_cpu_stats(valid)
    for bad in ("", valid.replace("overrun: 0", "overrun: 1", 1), valid.replace("dropped events: 0", "dropped events: 2"), valid.replace("commit overrun: 0\n", "")):
      with self.subTest(bad=bad), self.assertRaises(Refusal):
        verify_cpu_stats(bad)

  def test_numeric_field_format_and_id(self) -> None:
    valid = f"name: {state().event}\nID: 42\nformat:\n field:u8 crashed; offset:16; size:1; signed:0;\n field:s32 connector_type; offset:17; size:4; signed:1;\n"
    verify_format(valid, "42\n", state())
    for text, event_id in ((valid, "43"), (valid.replace("size:1", "size:8"), "42"), (valid.replace("signed:1", "signed:0"), "42")):
      with self.subTest(text=text), self.assertRaises(Refusal):
        verify_format(text, event_id, state())


class OperationTests(unittest.TestCase):
  def test_plan_pid_filter_precedes_enable_and_exactly_one_open(self) -> None:
    actions = setup_actions(state(), "p:other/e symbol", ())
    names = [action.name for action in actions]
    self.assertLess(names.index("set_pid"), names.index("enable_event"))
    self.assertLess(names.index("enable_event"), names.index("start_trace"))
    self.assertEqual(names.count("open_target_once"), 1)
    self.assertEqual(actions[names.index("set_pid")], Action("set_pid", "1234"))
    self.assertFalse(any(name in names for name in ("mount", "clear_global", "read_target", "set_global_tracer")))

  def test_collision_and_invalid_ownership_names_refuse(self) -> None:
    for definitions, instances in ((state().definition, ()), ("", (state().instance,))):
      with self.subTest(definitions=definitions), self.assertRaises(Refusal):
        setup_actions(state(), definitions, instances)
    with self.assertRaises(Refusal):
      setup_actions(TraceState("../other", "observe", "bad", 1), "", ())

  def test_partial_cleanup_touches_only_owned_objects(self) -> None:
    own = state()
    self.assertEqual(cleanup_actions(own, "p:other/e symbol"), ())
    own.definition_attempted = True
    self.assertEqual(cleanup_actions(own, own.serialized_definition + "\np:other/e symbol"), (Action("delete_definition", f"-:{own.group}/{own.event}"),))
    own.instance_created = True
    own.event_enable_attempted = True
    own.trace_enable_attempted = True
    names = [action.name for action in cleanup_actions(own, own.serialized_definition)]
    self.assertEqual(names, ["stop_trace", "disable_event", "remove_instance", "delete_definition"])
    changed = cleanup_actions(own, own.serialized_definition.replace("+28", "+32"))
    self.assertEqual([action.name for action in changed], ["stop_trace", "disable_event", "remove_instance", "refuse_definition_delete"])

  def test_partial_definition_absence_does_not_delete_anything(self) -> None:
    own = state()
    own.definition_attempted = True
    self.assertEqual(cleanup_actions(own, "p:other/e symbol"), ())

  def test_deadline_is_bounded_and_expiry_refuses(self) -> None:
    self.assertEqual(remaining_seconds(100, 104), 6)
    for now in (99, 110, 111):
      with self.subTest(now=now), self.assertRaises(Refusal):
        remaining_seconds(100, now)


class RealFileTests(unittest.TestCase):
  def test_real_regular_file_bounded_nofollow_read(self) -> None:
    with tempfile.TemporaryDirectory() as directory:
      path = Path(directory) / "note"
      path.write_bytes(b"1234")
      self.assertEqual(read_regular(path, 4, os.geteuid()), b"1234")
      with self.assertRaises(Refusal):
        read_regular(path, 3, os.geteuid())
      link = Path(directory) / "link"
      link.symlink_to(path)
      with self.assertRaises(Refusal):
        read_regular(link, 4, os.geteuid())
      with self.assertRaises(Refusal):
        read_regular(Path(directory), 4, os.geteuid())

  def test_executor_appends_without_truncating_global_file(self) -> None:
    with tempfile.TemporaryDirectory() as directory:
      root = Path(directory)
      global_file = root / "kprobe_events"
      global_file.write_text("p:other/event other_symbol\n")
      own = state()
      files = TraceFiles(root, root / "ColorElements", os.geteuid())
      files.perform(Action("append_definition", own.definition), own)
      self.assertEqual(global_file.read_text(), "p:other/event other_symbol\n" + own.definition + "\n")
      self.assertTrue(own.definition_attempted)
      with self.assertRaises(Refusal):
        files.perform(Action("append_definition", "p:bad/event bad_symbol"), own)

  def test_executor_exact_pid_filter_enable_and_one_open_no_read(self) -> None:
    with tempfile.TemporaryDirectory() as directory:
      root = Path(directory)
      own = state()
      instance = root / "instances" / own.instance
      event = instance / "events" / own.group / own.event
      event.mkdir(parents=True)
      (event / "enable").write_text("0\n")
      (instance / "set_event_pid").write_text("")
      target = root / "ColorElements"
      target.write_bytes(b"untouched target fixture")
      files = TraceFiles(root, target, os.geteuid())
      with self.assertRaises(Refusal):
        files.perform(Action("enable_event"), own)
      files.perform(Action("set_pid", str(own.pid)), own)
      files.perform(Action("enable_event"), own)
      files.perform(Action("open_target_once"), own)
      self.assertEqual((event / "enable").read_text(), "1\n")
      self.assertEqual(target.read_bytes(), b"untouched target fixture")
      with self.assertRaises(Refusal):
        files.perform(Action("open_target_once"), own)

  def test_executor_collision_and_remove_only_owned_empty_instance(self) -> None:
    with tempfile.TemporaryDirectory() as directory:
      root = Path(directory)
      (root / "instances").mkdir()
      (root / "instances" / "other").mkdir()
      own = state()
      files = TraceFiles(root, root / "unused", os.geteuid())
      files.perform(Action("create_instance"), own)
      self.assertTrue(own.instance_created)
      with self.assertRaises(FileExistsError):
        files.perform(Action("create_instance"), own)
      files.perform(Action("remove_instance"), own)
      self.assertTrue((root / "instances" / "other").is_dir())
      self.assertFalse(own.instance_created)

  def test_production_entry_refuses_unprivileged_sandbox_and_arguments(self) -> None:
    self.assertNotEqual(os.geteuid(), 0, "offline suite must run unprivileged")
    with self.assertRaisesRegex(Refusal, "manually invoked root"):
      _preflight()
    for arguments in ([], ["--anything"]):
      with self.subTest(arguments=arguments), redirect_stdout(StringIO()) as output:
        self.assertEqual(main(arguments), 2)
        self.assertIn('"status": "REFUSED"', output.getvalue())

  def test_cleanup_continues_after_real_nonempty_instance_failure(self) -> None:
    with tempfile.TemporaryDirectory() as directory:
      root = Path(directory)
      own = state()
      own.instance_created = own.definition_attempted = True
      own.event_enable_attempted = own.trace_enable_attempted = True
      instance = root / "instances" / own.instance
      event = instance / "events" / own.group / own.event
      event.mkdir(parents=True)
      (instance / "tracing_on").write_text("1\n")
      (event / "enable").write_text("1\n")
      global_file = root / "kprobe_events"
      global_file.write_text("p:other/e symbol\n" + own.serialized_definition + "\n")
      result = cleanup(TraceFiles(root, root / "unused", os.geteuid()), own)
      self.assertEqual(result.operations[:2], ("cleanup:stop_trace", "cleanup:disable_event"))
      self.assertIn("cleanup:delete_definition", result.operations)
      self.assertTrue(any(failure.startswith("remove_instance:") for failure in result.failures))
      self.assertEqual((instance / "tracing_on").read_text(), "0\n")
      self.assertEqual((event / "enable").read_text(), "0\n")
      self.assertTrue(global_file.read_text().startswith("p:other/e symbol\n"))
      self.assertTrue(global_file.read_text().endswith(f"-:{own.group}/{own.event}\n"))
      # Ordinary fixture files do not implement tracefs deletion semantics.
      self.assertIn("owned global probe remains", result.failures)

  def test_real_sigalrm_interrupts_cooperative_cleanup_wait(self) -> None:
    previous = signal.signal(signal.SIGALRM, _interrupted)
    try:
      with self.assertRaisesRegex(Refusal, "deadline expired"):
        with _cleanup_deadline():
          signal.pause()
      self.assertEqual(signal.getitimer(signal.ITIMER_REAL), (0.0, 0.0))
    finally:
      signal.setitimer(signal.ITIMER_REAL, 0)
      signal.signal(signal.SIGALRM, previous)


class FixedTargetPathTests(unittest.TestCase):
  def test_target_uses_confirmed_named_directory(self) -> None:
    self.assertEqual(TARGET, Path("/sys/kernel/debug/dri/soc:display-subsystem/DP-1/ColorElements"))

  def test_named_directory_opens_but_numeric_alias_stays_refused(self) -> None:
    with tempfile.TemporaryDirectory() as directory:
      root = Path(directory)
      named = root / "soc:display-subsystem"
      connector = named / "DP-1"
      connector.mkdir(parents=True)
      (connector / "ColorElements").write_bytes(b"fixture")
      (root / "2").symlink_to(named.name, target_is_directory=True)
      self.assertEqual(read_regular(connector / "ColorElements", 7, os.geteuid()), b"fixture")
      with self.assertRaises(Refusal):
        read_regular(root / "2" / "DP-1" / "ColorElements", 7, os.geteuid())

  def test_missing_path_reports_requested_path_and_numeric_errno_only(self) -> None:
    with tempfile.TemporaryDirectory() as directory:
      missing = Path(directory) / "soc:display-subsystem" / "DP-1" / "ColorElements"
      with self.assertRaises(Refusal) as caught:
        read_regular(missing, 7, os.geteuid())
      self.assertEqual(str(caught.exception), f"safe path open refused: path={missing} errno={errno.ENOENT}")


if __name__ == "__main__":
  unittest.main()
