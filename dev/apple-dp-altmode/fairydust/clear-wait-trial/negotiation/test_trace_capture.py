from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(__file__).parent
OUTPUT = Path("/home/david/Work/dev147-clear-wait-trial/negotiation")
RELEASE = "7.1.12-dev147-clearwait100"


class TraceCaptureTests(unittest.TestCase):
  def run_case(self, mode: str, expected: int, release: str = RELEASE) -> None:
    with tempfile.TemporaryDirectory(prefix="dev147-trace-mock.") as temporary:
      root = Path(temporary)
      for name in (
        "output",
        "tracefs/instances",
        "template/events/dcp",
        "template/per_cpu/cpu0",
        "tools",
      ):
        (root / name).mkdir(parents=True, mode=0o700)
      for name in (
        "tracing_on",
        "events/enable",
        "current_tracer",
        "trace_clock",
        "buffer_size_kb",
        "trace",
      ):
        (root / "template" / name).write_text("0\n")
      (root / "template/per_cpu/cpu0/stats").write_text(
        "entries: 1\noverrun: 2\ncommit overrun: 0\ndropped events: 0\n"
      )
      for event in ("iomfb_push", "iomfb_callback", "dcp_send_msg", "dcp_recv_msg"):
        directory = root / "template/events/dcp" / event
        directory.mkdir()
        (directory / "enable").write_text("0\n")
        if mode == "filter-failure" and event == "dcp_send_msg":
          (directory / "filter").mkdir()
        else:
          (directory / "filter").write_text("none\n")
      for event in ("tps6598x_status", "tps6598x_power_status"):
        if mode == "missing-" + event:
          continue
        directory = root / "template/events/tps6598x" / event
        directory.mkdir(parents=True)
        (directory / "enable").write_text("0\n")
      (root / "tracefs/tracing_on").write_text("GLOBAL_SENTINEL\n")
      (root / "tty").touch()
      (root / "mode").write_text(mode)
      (root / "release").write_text(release)
      programs = {
        "uname": "#!/bin/bash\n[[ $# == 1 && $1 == -r ]] || exit 99\ncat /mock-release\n",
        "sudo": '#!/bin/bash\nexec "$@"\n',
        "mktemp": '#!/bin/bash\nset -e\np=$(/mock-tools/real-mktemp "$@")\nif [[ $p == /sys/kernel/tracing/instances/dev147-negotiation.* ]]; then /usr/bin/touch /mock-created; /usr/bin/cp -a /mock-template/. "$p/"; fi\nprintf "%s\\n" "$p"\n',
        "sleep": '#!/bin/bash\n[[ $1 == 45 ]] || exit 99\nmode=$(cat /mock-mode)\nif [[ $mode == INT || $mode == TERM || $mode == HUP ]]; then kill -s "$mode" "$PPID"; fi\n',
        "rmdir": '#!/usr/bin/python3\nimport pathlib,shutil,sys\np=pathlib.Path(sys.argv[-1])\nassert p.parent==pathlib.Path("/sys/kernel/tracing/instances") and p.name.startswith("dev147-negotiation.")\nassert (p/"tracing_on").read_text().strip()=="0"\nassert (p/"events/enable").read_text().strip()=="0"\nif pathlib.Path("/mock-mode").read_text()=="cleanup-failure": sys.exit(1)\nshutil.rmtree(p)\n',
      }
      for name, text in programs.items():
        text = (
          text.replace("/mock-tools", str(root / "tools"))
          .replace("/mock-template", str(root / "template"))
          .replace("/mock-mode", str(root / "mode"))
          .replace("/mock-release", str(root / "release"))
          .replace("/mock-created", "/sys/kernel/tracing/instance-created")
        )
        (root / "tools" / name).write_text(text)
        (root / "tools" / name).chmod(0o700)
      (root / "tools/real-mktemp").touch()
      command = [
        "/usr/bin/bwrap",
        "--die-with-parent",
        "--ro-bind",
        "/",
        "/",
        "--bind",
        str(root / "output"),
        str(OUTPUT),
        "--bind",
        str(root / "tracefs"),
        "/sys/kernel/tracing",
        "--bind",
        str(root / "tty"),
        "/dev/tty",
        "--ro-bind",
        "/usr/bin/mktemp",
        str(root / "tools/real-mktemp"),
      ]
      for name in programs:
        command += ["--ro-bind", str(root / "tools" / name), "/usr/bin/" + name]
      command += ["/bin/bash", str(SOURCE / "trace-capture.sh"), "monitor-power"]
      result = subprocess.run(
        command, capture_output=True, text=True, check=False, timeout=10
      )
      self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
      outputs = list((root / "output").iterdir())
      self.assertEqual(len(outputs), 1)
      report = (outputs[0] / "report.txt").read_text()
      self.assertEqual(int((outputs[0] / "exit-status").read_text()), expected)
      if release != RELEASE:
        self.assertIn("FAIL: unexpected kernel release", report)
        self.assertNotIn("CLEANUP_BEGIN", report)
        self.assertNotIn("TRACE_BEGIN", report)
        self.assertFalse((root / "tracefs/instance-created").exists())
        self.assertEqual(list((root / "tracefs/instances").iterdir()), [])
        self.assertEqual((root / "tty").read_text(), "")
        self.assertEqual((root / "tracefs/tracing_on").read_text(), "GLOBAL_SENTINEL\n")
        return
      self.assertTrue((root / "tracefs/instance-created").exists())
      if mode == "cleanup-failure":
        self.assertIn("FAIL: own instance removal failed", report)
        self.assertNotIn("CLEANUP_REMOVED", report)
      else:
        self.assertIn("CLEANUP_REMOVED", report)
      self.assertIn("overrun: 2", report)
      self.assertLess(report.index("CPU_STATS"), report.index("TRACE_BEGIN"))
      remaining = list((root / "tracefs/instances").iterdir())
      if mode == "cleanup-failure":
        self.assertEqual(len(remaining), 1)
        self.assertEqual((remaining[0] / "tracing_on").read_text(), "0\n")
        self.assertEqual((remaining[0] / "events/enable").read_text(), "0\n")
      else:
        self.assertEqual(remaining, [])
      self.assertEqual((root / "tracefs/tracing_on").read_text(), "GLOBAL_SENTINEL\n")
      cue = (root / "tty").read_text()
      if mode == "filter-failure" or mode.startswith("missing-"):
        self.assertNotIn("READY", cue)
      else:
        self.assertIn("READY", cue)
        self.assertIn("Keep ALL USB cables connected", cue)
        self.assertIn("Turn the LG27 off with its power button, wait 5 seconds", cue)
        self.assertIn("then turn it on once", cue)
        self.assertIn("Make no further changes until capture ends", cue)
        self.assertNotIn("Disconnect", cue)
        self.assertIn("CAPTURE_MODE monitor-power", report)
        for event in ("tps6598x_status", "tps6598x_power_status"):
          self.assertIn("REQUIRED_EVENT " + event + " enabled", report)
      if mode.startswith("missing-"):
        self.assertIn(
          "FAIL: required event missing: " + mode.removeprefix("missing-"), report
        )
      if mode in ("normal", "cleanup-failure"):
        self.assertIn("CAPTURED:", report)
        self.assertIn("endpoint == 55", report)
      else:
        self.assertNotIn("CAPTURED:", report)

  def test_monitor_power_cue_keeps_all_cables_connected(self) -> None:
    self.run_case("normal", 0)

  def test_baseline_and_unknown_release_stop_before_instance_or_ready(self) -> None:
    for release in ("7.1.12-dev147-fairydust1", "unknown-kernel"):
      with self.subTest(release=release):
        self.run_case("normal", 2, release)

  def test_missing_required_event_refuses_before_ready(self) -> None:
    for event in ("tps6598x_status", "tps6598x_power_status"):
      with self.subTest(event=event):
        self.run_case("missing-" + event, 1)

  def test_invalid_arguments_refuse_before_sudo(self) -> None:
    for arguments in (
      (),
      ("unexpected",),
      ("attach",),
      ("rear-attach",),
      ("reconnect",),
      ("monitor-power", "extra"),
    ):
      result = subprocess.run(
        ["/bin/bash", str(SOURCE / "trace-capture.sh"), *arguments],
        capture_output=True,
        text=True,
        check=False,
        timeout=5,
      )
      self.assertEqual(result.returncode, 2)
      self.assertEqual(result.stdout, "")

  def test_success_with_loss_stats_is_only_captured(self) -> None:
    self.run_case("normal", 0)

  def test_filter_failure_cleans_up_without_ready(self) -> None:
    self.run_case("filter-failure", 1)

  def test_cleanup_failure_is_nonzero_and_retains_disabled_instance(self) -> None:
    self.run_case("cleanup-failure", 1)

  def test_interrupt_cleans_up(self) -> None:
    for signal, code in (("INT", 130), ("TERM", 143), ("HUP", 143)):
      with self.subTest(signal=signal):
        self.run_case(signal, code)


if __name__ == "__main__":
  unittest.main()
