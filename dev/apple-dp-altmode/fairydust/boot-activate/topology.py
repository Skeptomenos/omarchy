from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path

EXPECTED = {
  "/": {
    "target": "/",
    "source": "/dev/nvme0n1p5",
    "fstype": "ext4",
    "uuid": "e24cf117-3c89-4392-a3b8-def187becda8",
    "partuuid": "ca156abe-b9ce-46ea-88ca-87e8c03de497",
  },
  "/boot/efi": {
    "target": "/boot/efi",
    "source": "/dev/nvme0n1p4",
    "fstype": "vfat",
    "uuid": "0A48-269E",
    "partuuid": "190f2e7d-4e97-4f75-975b-8bd6aa85174f",
  },
}
DIRECTORIES = ("/boot", "/boot/grub", "/boot/efi", "/boot/efi/m1n1")


class TopologyFailure(Exception):
  pass


def parse_mount(content: bytes, target: str) -> dict[str, str]:
  value: object = json.loads(content)
  if not isinstance(value, dict) or set(value) != {"filesystems"}:
    raise TopologyFailure("invalid mount response")
  rows = value["filesystems"]
  if not isinstance(rows, list) or len(rows) != 1 or rows[0] != EXPECTED[target]:
    raise TopologyFailure(f"mount topology differs: {target}")
  return dict(EXPECTED[target])


def validate_relationships(devices: dict[str, int], root_device: int) -> None:
  if (
    devices["/boot"] != root_device
    or devices["/boot"] != devices["/boot/grub"]
    or devices["/boot/efi"] != devices["/boot/efi/m1n1"]
    or devices["/boot"] == devices["/boot/efi"]
  ):
    raise TopologyFailure("boot and ESP device relationships differ")


def discover() -> dict[str, int]:
  for target in EXPECTED:
    result = subprocess.run(
      [
        "/usr/bin/findmnt",
        "-J",
        "-T",
        target,
        "-o",
        "TARGET,SOURCE,FSTYPE,UUID,PARTUUID",
      ],
      capture_output=True,
      check=True,
      timeout=10,
    )
    record = parse_mount(result.stdout, target)
    device = Path(record["source"]).stat()
    if not stat.S_ISBLK(device.st_mode) or device.st_rdev != Path(target).stat().st_dev:
      raise TopologyFailure(f"mount source device differs: {target}")
  devices: dict[str, int] = {}
  for name in DIRECTORIES:
    path = Path(name)
    info = path.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_mode & 0o022:
      raise TopologyFailure(f"unsafe mount directory: {name}")
    devices[name] = info.st_dev
  validate_relationships(devices, Path("/").stat().st_dev)
  return devices


if __name__ == "__main__":
  print(
    json.dumps(
      {
        "status": "READ_ONLY_TOPOLOGY_PASS",
        "directory_devices": discover(),
        "uid": os.getuid(),
      },
      indent=2,
    )
  )
