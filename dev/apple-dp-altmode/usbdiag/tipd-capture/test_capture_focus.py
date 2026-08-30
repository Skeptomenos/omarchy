"""Focused real-child/private-file checks; no live entry is invoked.

The existing three RED methods stay byte-identical. Synthetic consistency
publication is separate from actual Python execution receipts.
"""

import ast
from dataclasses import replace
import errno
import hashlib
import inspect
import json
import os
from pathlib import Path
import signal
import stat
import unittest

import bounded_child as engine
import fixed_t1_collector as collector
from capture_binding import CaptureError, CaptureFiles
from fixed_t1_binding import BindingError, bind_fixed_t1
from test_fixed_capture import (
  BOOT, BOOT_RAW, BUILD_ID, NOTE, encoded, selection_attestation,
  staging_attestation, staging_stdout, synthetic_capture,
)


def write_private(path: Path, raw: bytes) -> None:
  descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
  try:
    offset = 0
    while offset < len(raw):
      offset += os.write(descriptor, raw[offset:])
  finally:
    os.close(descriptor)


def changed_stdout(files: CaptureFiles, stdout: bytes) -> CaptureFiles:
  receipt = json.loads(files.receipt)
  receipt.update(stdout_bytes=len(stdout), stdout_sha256=hashlib.sha256(stdout).hexdigest())
  return replace(files, stdout=stdout, receipt=encoded(receipt))


class CaptureFocusTests(unittest.TestCase):
  def run_child(
    self, name: str, code: str, *, stdout: int = 1_024, stderr: int = 1_024,
    duration: int = 1_500_000, cleanup: int = 300_000,
  ) -> engine.ChildCapture:
    argv = ("/usr/bin/python3.14", "-I", "-S", "-B", "-c", code)
    result = engine._capture_child(argv, Path("/work") / name, engine._Limits(duration, stdout, stderr, cleanup))
    self.assertEqual(result.argv, argv)
    self.assertTrue(result.reaped)
    self.assertGreater(result.pid, 0)
    self.assertEqual(result.process_group, result.pid)
    self.assertFalse(result.overall_capture_accepted)
    self.assertFalse(result.emitted_bytes_known)
    self.assertEqual(result.execution_policy, "clean-env:null-stdin:close-fds:new-session")
    with self.assertRaises(ProcessLookupError):
      os.kill(result.pid, 0)
    for stream in ("stdout", "stderr"):
      raw = (Path("/work") / name / (stream + ".bin")).read_bytes()
      self.assertEqual(len(raw), getattr(result, stream + "_retained"))
      self.assertEqual(hashlib.sha256(raw).hexdigest(), getattr(result, stream + "_sha256"))
    receipt = json.loads((Path("/work") / name / "child.json").read_bytes())
    self.assertEqual(receipt["argv"], list(argv))
    self.assertEqual(receipt["status"], result.status)
    self.assertEqual(receipt["execution_policy"], "clean-env:null-stdin:close-fds:new-session")
    self.assertLessEqual(result.end_monotonic_us - result.start_monotonic_us, duration)
    return result

  def test_both_caps_below_exact_above_and_concurrent_streams(self) -> None:
    for stream, descriptor, fill in (("stdout", 1, "O"), ("stderr", 2, "E")):
      for count in (31, 32, 33):
        with self.subTest(stream=stream, count=count):
          result = self.run_child(
            f"cap-{stream}-{count}",
            f"import os,time; os.write({descriptor}, b'{fill}' * {count}); time.sleep({0 if count <= 32 else 5})",
            stdout=32, stderr=32,
          )
          self.assertEqual(result.status, "ok" if count <= 32 else stream + "_limit")
          self.assertEqual(getattr(result, stream + "_observed"), count)
          self.assertEqual(getattr(result, stream + "_retained"), min(count, 32))
          self.assertEqual(result.killed, count > 32)
    result = self.run_child(
      "concurrent-streams", "import os; [(os.write(1,b'O'*16),os.write(2,b'E'*16)) for i in range(64)]",
    )
    self.assertEqual((result.status, result.stdout_observed, result.stderr_observed), ("ok", 1_024, 1_024))

  def test_actual_clean_environment_null_stdin_closed_fd_and_error(self) -> None:
    path = Path("/work/inheritable-fixture")
    descriptor = os.open(path, os.O_RDWR | os.O_CREAT | os.O_EXCL, 0o600)
    os.set_inheritable(descriptor, True)
    code = (
      "import json,os\n"
      "closed=False\n"
      f"try: os.fstat({descriptor})\n"
      "except OSError: closed=True\n"
      "value=dict(env=dict(os.environ),stdin=os.read(0,1).hex(),closed=closed,pid=os.getpid(),pgid=os.getpgrp(),sid=os.getsid(0))\n"
      "os.write(1,json.dumps(value,sort_keys=True).encode())\n"
    )
    try:
      result = self.run_child("actual-policy", code)
    finally:
      os.close(descriptor)
    observed = json.loads(Path("/work/actual-policy/stdout.bin").read_bytes())
    self.assertEqual(observed, {
      "env": {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"},
      "stdin": "", "closed": True, "pid": result.pid, "pgid": result.pid, "sid": result.pid,
    })
    error = self.run_child("nonzero-child", "import os; os.write(2,b'fixture error\\n'); os._exit(7)")
    self.assertEqual((error.status, error.exit_code), ("error", 7))
    self.assertEqual(Path("/work/nonzero-child/stderr.bin").read_bytes(), b"fixture error\n")

  def test_absolute_timeout_and_descendant_held_pipes(self) -> None:
    cases = (
      ("silent-timeout", "import time; time.sleep(5)"),
      ("writer-timeout", "import os,time\nwhile True:\n os.write(1,b'x'); time.sleep(.01)"),
      ("ignore-term-timeout", "import signal,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); time.sleep(5)"),
      ("descendant-pipes", "import os,time\nif os.fork()==0: time.sleep(5); os._exit(0)\nos._exit(0)"),
    )
    for name, code in cases:
      with self.subTest(name=name):
        result = self.run_child(name, code, duration=600_000, cleanup=250_000)
        self.assertEqual(result.status, "timeout")
        self.assertTrue(result.killed and result.reaped)
        self.assertEqual(result.exit_code, 0 if name == "descendant-pipes" else -signal.SIGKILL)

  def test_real_int_and_term_interruptions_restore_handlers(self) -> None:
    before = {signum: signal.getsignal(signum) for signum in (signal.SIGINT, signal.SIGTERM)}
    for name, signum in (("sigint", signal.SIGINT), ("sigterm", signal.SIGTERM)):
      with self.subTest(name=name):
        result = self.run_child(
          name, f"import os,time; os.write(1,b'partial'); os.kill(os.getppid(),{int(signum)}); time.sleep(5)",
        )
        self.assertEqual((result.status, result.exit_code), ("interrupted", -signal.SIGKILL))
        self.assertTrue(result.killed and result.reaped)
        self.assertEqual(Path("/work", name, "stdout.bin").read_bytes(), b"partial")
        self.assertEqual({number: signal.getsignal(number) for number in before}, before)

  def test_output_collisions_and_same_inode_tamper_refuse(self) -> None:
    base = Path("/work/collisions")
    base.mkdir(mode=0o700)
    write_private(base / "file", b"sentinel")
    (base / "directory").mkdir(mode=0o700)
    (base / "symlink").symlink_to(base / "file")
    (base / "dangling").symlink_to(base / "absent")
    os.link(base / "file", base / "hardlink")
    for name in ("file", "directory", "symlink", "dangling", "hardlink"):
      with self.subTest(name=name), self.assertRaises(engine.CollectionError):
        engine._capture_child(("/usr/bin/python3.14", "-c", "raise SystemExit(0)"), base / name, engine._Limits(500_000, 32, 32, 200_000))
    self.assertEqual((base / "file").read_bytes(), b"sentinel")
    original_open = engine._open_new
    opened: list[int] = []

    def collide_on_second_open(directory: int, name: str) -> int:
      if name == "stderr.bin":
        collision = original_open(directory, name)
        os.close(collision)
      descriptor = original_open(directory, name)
      opened.append(descriptor)
      return descriptor

    engine._open_new = collide_on_second_open
    try:
      with self.assertRaises(engine.CollectionError):
        engine._capture_child(("/usr/bin/python3.14", "-c", "raise SystemExit(0)"), Path("/work/second-open-fault"), engine._Limits(500_000, 32, 32, 200_000))
    finally:
      engine._open_new = original_open
    self.assertEqual(len(opened), 1)
    with self.assertRaises(OSError):
      os.fstat(opened[0])
    self.assertFalse(Path("/work/second-open-fault/child.json").exists())
    for name, code in (
      ("child-json-collision", "import os; f=os.open('child.json',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600); os.write(f,b'collision'); os.close(f); os.write(2,('child-pid=%d\\n'%os.getpid()).encode())"),
      ("same-inode-tamper", "import os,time\nos.write(1,b'original')\nend=time.monotonic()+3\nwhile os.stat('stdout.bin').st_size!=8 and time.monotonic()<end: time.sleep(.002)\nf=os.open('stdout.bin',os.O_WRONLY); os.write(f,b'altered!'); os.close(f)\nos.write(2,('child-pid=%d\\n'%os.getpid()).encode())"),
    ):
      with self.subTest(name=name), self.assertRaises(engine.CollectionError):
        self.run_child(name, code)
      pid_line = Path("/work", name, "stderr.bin").read_bytes()
      self.assertTrue(pid_line.startswith(b"child-pid=") and pid_line.endswith(b"\n"))
      with self.assertRaises(ProcessLookupError):
        os.kill(int(pid_line.removeprefix(b"child-pid=")), 0)
    self.assertEqual(Path("/work/child-json-collision/child.json").read_bytes(), b"collision")
    self.assertEqual(Path("/work/same-inode-tamper/stdout.bin").read_bytes(), b"altered!")
    self.assertFalse(Path("/work/same-inode-tamper/child.json").exists())

  def test_injected_write_fault_still_kills_and_reaps(self) -> None:
    original = engine.os.write
    failed = False

    def fail_once(descriptor: int, data: bytes) -> int:
      nonlocal failed
      if not failed and data.startswith(b"injected-fault"):
        failed = True
        raise OSError(errno.ENOSPC, "synthetic private-write fault")
      return original(descriptor, data)

    engine.os.write = fail_once
    try:
      result = self.run_child("write-fault", "import os,time; os.write(1,b'injected-fault'); time.sleep(5)")
    finally:
      engine.os.write = original
    self.assertTrue(failed)
    self.assertEqual((result.status, result.exit_code, result.stdout_retained), ("error", -signal.SIGKILL, 0))
    self.assertTrue(result.killed and result.reaped)

  def test_private_sample_bounds_identity_and_replacements(self) -> None:
    base = Path("/work/sample-fixtures")
    base.mkdir(mode=0o700)
    boot, note = base / "boot", base / "note"
    write_private(boot, BOOT_RAW)
    write_private(note, NOTE)
    os.utime(boot, ns=(1, 1))
    before = collector._sample_pair(boot, note, 1001)
    collector._same_samples(before, collector._sample_pair(boot, note, 1001))
    self.assertEqual((before.boot, before.note), (BOOT_RAW, NOTE))
    note.rename(base / "retained-original-note")
    write_private(note, NOTE)
    with self.assertRaisesRegex(engine.CollectionError, "boot_or_module_sample_changed"):
      collector._same_samples(before, collector._sample_pair(boot, note, 1001))
    for name, raw in (("long-boot", BOOT_RAW + b"x"), ("long-note", NOTE + b"x"), ("wrong-note", NOTE[:-1] + b"x")):
      write_private(base / name, raw)
      with self.subTest(name=name), self.assertRaises(engine.CollectionError):
        collector._sample_pair(base / name if "boot" in name else boot, note if "boot" in name else base / name, 1001)
    (base / "boot-link").symlink_to(boot)
    with self.assertRaises(OSError):
      collector._sample_pair(base / "boot-link", note, 1001)

  def test_fixed_wrapper_plan_and_no_fixture_relabeling(self) -> None:
    tree = ast.parse(inspect.getsource(collector))
    entry = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "collect_fixed_t1")
    self.assertEqual((entry.args.args, entry.args.kwonlyargs, entry.args.vararg, entry.args.kwarg), ([], [], None, None))
    calls = sorted(
      ((node.lineno, node) for node in ast.walk(entry) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)),
      key=lambda item: item[0],
    )
    names = [node.func.id for unused, node in calls]
    self.assertEqual(names[0], "_require_local_output")
    self.assertLess(names.index("_sample_pair"), names.index("_capture_child"))
    self.assertLess(names.index("_capture_child"), len(names) - 1 - names[::-1].index("_sample_pair"))
    self.assertLess(names.index("_capture_files"), names.index("_publish_consistency"))
    self.assertEqual(collector._journal_plan(BOOT), (
      "/usr/bin/journalctl", "--dmesg", "--boot=" + BOOT,
      "--all", "--output=json", "--no-pager", "--no-tail",
    ))
    self.assertEqual((collector.DURATION_US, collector.STDOUT_LIMIT, collector.STDERR_LIMIT, collector.CLEANUP_US), (30_000_000, 8_388_608, 65_536, 1_000_000))
    self.assertEqual(str(collector.BOOT_PATH), "/proc/sys/kernel/random/boot_id")
    self.assertEqual(str(collector.NOTE_PATH), "/sys/module/tps6598x_core/notes/.note.gnu.build-id")
    self.assertEqual(collector.JOURNAL_SHA256, "c7de3d70a567a1e9f7f09cd67c8d626c96d14f53149728d3b86ded4a323cda22")
    self.assertEqual(collector.JOURNAL_BYTES, 138_296)
    sample = collector._SamplePair(BOOT_RAW, NOTE, (1,), (2,))
    actual = self.run_child("not-journal", "import os; os.write(1,b'not journal\\n')")
    with self.assertRaisesRegex(engine.CollectionError, "nonjournal_execution"):
      collector._capture_files(sample, sample, actual, b"not journal\n", b"", actual.start_monotonic_us, actual.end_monotonic_us)

  def test_consistency_publication_is_last_exclusive_and_failure_retained(self) -> None:
    sample = synthetic_capture()
    complete = Path("/work/synthetic-publication")
    descriptor = engine._new_directory(complete)
    try:
      collector._publish_consistency(descriptor, sample)
      result = json.loads((complete / "capture-result.json").read_bytes())
      self.assertEqual(result["evidence"], "internally_consistent_only")
      self.assertFalse(result["operationally_accepted"] or result["initrd_boot_proven"] or result["receiver_delivery_claim"])
      self.assertEqual((complete / "journal.receipt.json").read_bytes(), sample.receipt)
      with self.assertRaises(engine.CollectionError):
        collector._publish_consistency(descriptor, sample)
    finally:
      os.close(descriptor)
    for name, files in (
      ("truncated-capture", changed_stdout(sample, sample.stdout[:-1])),
      ("incomplete-capture", changed_stdout(sample, sample.stdout.splitlines(keepends=True)[0])),
    ):
      output = Path("/work") / name
      descriptor = engine._new_directory(output)
      try:
        if name == "truncated-capture":
          with self.assertRaises(CaptureError):
            collector._publish_consistency(descriptor, files)
          self.assertFalse((output / "capture-result.json").exists())
        else:
          collector._publish_consistency(descriptor, files)
          self.assertEqual(json.loads((output / "capture-result.json").read_bytes())["structural_status"], "inconclusive")
      finally:
        os.close(descriptor)
    output = Path("/work/publication-interrupted")
    descriptor = engine._new_directory(output)
    original = collector._write_new

    def interrupt_after_write(directory: int, name: str, raw: bytes) -> None:
      original(directory, name, raw)
      if name == "capture-result.json":
        raise KeyboardInterrupt

    collector._write_new = interrupt_after_write
    try:
      with self.assertRaises(KeyboardInterrupt):
        collector._publish_consistency(descriptor, sample)
    finally:
      collector._write_new = original
      os.close(descriptor)
    self.assertTrue((output / "journal.receipt.json").exists())
    self.assertTrue((output / "capture-result.json").exists())

  def test_new_attestation_schema_and_incomplete_trace_stay_qualified(self) -> None:
    sample = synthetic_capture()
    stdout = staging_stdout()
    values = dict(
      staging_attestation=staging_attestation(stdout), staging_stdout=stdout,
      staging_stderr=b"", selection_attestation=selection_attestation(),
    )
    duplicate = values["staging_attestation"].replace(b'"reported_exit_code":0', b'"reported_exit_code":0,"reported_exit_code":0')
    for changed in (b"{}", duplicate, b"[]", values["staging_attestation"] + b"x", b" " * 16_385):
      with self.subTest(raw=changed[:20]), self.assertRaisesRegex(BindingError, "invalid_staging_attestation"):
        bind_fixed_t1(sample, **dict(values, staging_attestation=changed))
    for field, changed, code in (
      ("after_boot_id", b"11234567-89ab-cdef-0123-456789abcdef\n", "boot_mismatch"),
      ("after_tipd_note", NOTE[:-1] + b"x", "module_mismatch"),
    ):
      receipt = json.loads(sample.receipt)
      key = "boot_id_sha256" if field == "after_boot_id" else "tipd_note_sha256"
      receipt["after"][key] = hashlib.sha256(changed).hexdigest()
      mixed = replace(sample, **{field: changed}, receipt=encoded(receipt))
      with self.subTest(field=field), self.assertRaisesRegex(BindingError, code):
        bind_fixed_t1(mixed, **values)
    incomplete = changed_stdout(sample, sample.stdout.splitlines(keepends=True)[0])
    result = bind_fixed_t1(incomplete, **values)
    self.assertEqual((result.status, result.codes), ("inconclusive", ("capture_inconclusive",)))
    self.assertFalse(result.negative_sender_claim or result.receiver_delivery_claim or result.hardware_acceptance)
