from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(__file__).parent
OUTPUT = Path("/home/david/Work/dev147-fairydust-acceptance-20260905")
PINS = (
  "/boot/efi/m1n1/boot.bin",
  "/boot/efi/m1n1/dev147-recovery/boot.bin.old-203ab702",
  "/etc/pacman.d/hooks/05-omarchy-m2-displayport-guard.hook",
)


class SnapshotTests(unittest.TestCase):
  def setUp(self) -> None:
    self.temporary = tempfile.TemporaryDirectory(prefix="dev147-acceptance-test.")
    self.root = Path(self.temporary.name)
    for name in ("drm/card2-DP-1", "typec/port0", "output"):
      (self.root / name).mkdir(parents=True, mode=0o700)
    for name, value in {
      "status": "connected\n",
      "enabled": "enabled\n",
      "modes": "2560x1440\n",
    }.items():
      (self.root / "drm/card2-DP-1" / name).write_text(value)
    (self.root / "typec/port0/data_role").write_text("[host] device\n")
    os.mkfifo(self.root / "typec/port0/usb_mode")
    self.uname = self.root / "uname"
    self.uname.write_text('#!/bin/bash\nprintf "7.1.12-dev147-fairydust1\\n"\n')
    self.uname.chmod(0o700)
    self.journal = self.root / "journalctl"
    self.journal_output(
      [
        {
          "MESSAGE": "apple-dcp display connected",
          "PRIORITY": "6",
          "__MONOTONIC_TIMESTAMP": "123000000",
        }
      ]
    )

  def journal_output(self, records: list[dict[str, str]], status: int = 0) -> None:
    content = "\n".join(json.dumps(record) for record in records)
    self.journal.write_text(
      "#!/usr/bin/python3\nimport sys\nprint("
      + repr(content)
      + ")\nsys.exit("
      + str(status)
      + ")\n"
    )
    self.journal.chmod(0o700)

  def tearDown(self) -> None:
    for directory, _, _ in os.walk(self.root):
      Path(directory).chmod(0o700)
    self.temporary.cleanup()

  def run_snapshot(self, expected: int = 0) -> tuple[dict[str, object], Path]:
    command = [
      "/usr/bin/bwrap",
      "--die-with-parent",
      "--ro-bind",
      "/",
      "/",
      "--ro-bind",
      str(self.root / "drm"),
      "/sys/class/drm",
      "--ro-bind",
      str(self.root / "typec"),
      "/sys/class/typec",
      "--bind",
      str(self.root / "output"),
      str(OUTPUT),
      "--ro-bind",
      str(self.uname),
      "/usr/bin/uname",
      "--ro-bind",
      str(self.journal),
      "/usr/bin/journalctl",
      "/usr/bin/python3",
      str(SOURCE / "snapshot.py"),
      "front-fixture",
    ]
    result = subprocess.run(
      command, capture_output=True, text=True, check=False, timeout=25
    )
    self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
    summary: dict[str, object] = json.loads(result.stdout)
    reported = summary["directory"]
    self.assertIsInstance(reported, str)
    saved = self.root / "output" / Path(str(reported)).name
    document: dict[str, object] = json.loads((saved / "snapshot.json").read_text())
    return document, saved

  def test_complete_capture_is_not_endurance_acceptance(self) -> None:
    document, saved = self.run_snapshot()
    self.assertEqual(document["status"], "SNAPSHOT_CAPTURED")
    self.assertFalse(document["endurance_accepted"])
    self.assertEqual((saved / "snapshot.json").stat().st_mode & 0o777, 0o400)

  def test_wrong_release_is_incomplete(self) -> None:
    self.uname.write_text('#!/bin/bash\nprintf "wrong-kernel\\n"\n')
    document, _ = self.run_snapshot(1)
    self.assertEqual(document["status"], "SNAPSHOT_INCOMPLETE")
    self.assertIn("wrong_release", json.dumps(document))

  def test_absent_external_connector_is_incomplete(self) -> None:
    shutil.rmtree(self.root / "drm/card2-DP-1")
    document, _ = self.run_snapshot(1)
    self.assertEqual(document["status"], "SNAPSHOT_INCOMPLETE")
    self.assertIn("external_connector_absent", json.dumps(document))

  def test_empty_journal_is_incomplete(self) -> None:
    self.journal_output([])
    document, _ = self.run_snapshot(1)
    self.assertEqual(document["status"], "SNAPSHOT_INCOMPLETE")
    self.assertIn("journal_unavailable", json.dumps(document))

  def test_mixed_controller_services_do_not_combine_endpoint_capacity(self) -> None:
    records = [
      {
        "MESSAGE": f"apple-dcp {controller}: AFK[ep:28]: new service DCPDP13Service on channel {channel}",
        "PRIORITY": "6",
        "__MONOTONIC_TIMESTAMP": str(channel * 1000000),
      }
      for controller in ("231c00000.dcp", "271c00000.dcp")
      for channel in range(1, 20, 2)
    ]
    self.journal_output(records)
    document, saved = self.run_snapshot()
    self.assertEqual(document["service_announcements"], 10)
    self.assertEqual(document["announcement_pairs"], 5)
    self.assertEqual(document["summary_controller"], "271c00000.dcp")
    self.assertEqual(document["summary_endpoint"], "0x28")
    parsed = [
      json.loads(line) for line in (saved / "journal.jsonl").read_text().splitlines()
    ]
    self.assertEqual(
      {record["controller"] for record in parsed}, {"231c00000.dcp", "271c00000.dcp"}
    )
    self.assertEqual({record["endpoint"] for record in parsed}, {0x28})

  def test_service_channels_are_not_host_slot_occupancy(self) -> None:
    records = [
      {
        "MESSAGE": f"apple-dcp 271c00000.dcp: AFK[ep:28]: new service DCPDP13Service on channel {channel}",
        "PRIORITY": "6",
        "__MONOTONIC_TIMESTAMP": str(channel * 1000000),
      }
      for channel in (21, 23)
    ]
    records.append(
      {
        "MESSAGE": "apple-dcp 271c00000.dcp: DCP booted",
        "PRIORITY": "6",
        "__MONOTONIC_TIMESTAMP": "100",
      }
    )
    self.journal_output(records)
    document, saved = self.run_snapshot()
    self.assertEqual(document["service_announcements"], 2)
    self.assertEqual(document["announcement_pairs"], 1)
    self.assertIsNone(document["host_slot_count"])
    parsed = [
      json.loads(line) for line in (saved / "journal.jsonl").read_text().splitlines()
    ]
    self.assertEqual(
      {record["channel"] for record in parsed if record["service"]}, {21, 23}
    )
    self.assertEqual(document["dcp_boots"], {"271c00000.dcp": 1})

  def test_journal_failure_is_incomplete(self) -> None:
    self.journal_output([], 1)
    document, _ = self.run_snapshot(1)
    self.assertEqual(document["status"], "SNAPSHOT_INCOMPLETE")
    self.assertIn("journal_unavailable", json.dumps(document))

  def test_error_records_are_not_a_pass_or_raw_identifier_export(self) -> None:
    self.journal_output(
      [
        {
          "MESSAGE": "apple-dcp timeout error SerialNumber=DO-NOT-EXPORT 192.0.2.9",
          "PRIORITY": "3",
          "__MONOTONIC_TIMESTAMP": "123000000",
        },
        {
          "MESSAGE": "authentication failed for private-user",
          "PRIORITY": "3",
          "__MONOTONIC_TIMESTAMP": "124000000",
        },
      ]
    )
    document, saved = self.run_snapshot(1)
    self.assertEqual(document["status"], "SNAPSHOT_CAPTURED_WITH_ERRORS")
    exported = "".join(path.read_text() for path in saved.iterdir())
    for forbidden in ("DO-NOT-EXPORT", "192.0.2.9", "private-user", "SerialNumber"):
      self.assertNotIn(forbidden, exported)
    self.assertIn("timeout", exported)


if __name__ == "__main__":
  unittest.main()
