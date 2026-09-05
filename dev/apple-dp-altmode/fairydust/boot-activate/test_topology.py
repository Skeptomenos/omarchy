from __future__ import annotations

import json
import unittest

import topology


class TopologyTests(unittest.TestCase):
  def test_separate_boot_mount_rejected(self) -> None:
    with self.assertRaises(topology.TopologyFailure):
      topology.validate_relationships(
        {"/boot": 2, "/boot/grub": 2, "/boot/efi": 3, "/boot/efi/m1n1": 3}, 1
      )

  def test_expected_mount_record(self) -> None:
    record = topology.EXPECTED["/boot/efi"]
    self.assertEqual(
      topology.parse_mount(json.dumps({"filesystems": [record]}).encode(), "/boot/efi"),
      record,
    )

  def test_wrong_partition(self) -> None:
    record = dict(topology.EXPECTED["/boot/efi"])
    record["partuuid"] = "wrong"
    with self.assertRaises(topology.TopologyFailure):
      topology.parse_mount(json.dumps({"filesystems": [record]}).encode(), "/boot/efi")

  def test_unmounted_esp_directory(self) -> None:
    with self.assertRaises(topology.TopologyFailure):
      topology.parse_mount(
        json.dumps({"filesystems": [topology.EXPECTED["/"]]}).encode(), "/boot/efi"
      )


if __name__ == "__main__":
  unittest.main()
