from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

SOURCE = Path(__file__).parent
EMU = Path(
  "/home/david/Work/dev147-fairydust-boot-20260905/research/activation-design/grub-emu-build/grub-core/grub-emu"
)
UUID = "e24cf117-3c89-4392-a3b8-def187becda8"


def main() -> None:
  assert len(sys.argv) == 2
  output = Path(sys.argv[1])
  output.mkdir()
  menu = (SOURCE / "candidate.cfg").read_text()
  assert menu.count("menuentry ") == 2
  assert "7.1.6" not in menu
  results: list[dict[str, object]] = []
  for index, release in enumerate(
    ("trial-7.1.12-dev147-clearwait100", "fairydust-7.1.12-dev147-fairydust1")
  ):
    case = output / str(index)
    root = case / "root/boot/grub"
    root.mkdir(parents=True)
    wrappers = """function probe_linux {
  echo RETURN_LINUX_ARGC=$#
  echo RETURN_LINUX_ARGS=$*
}
function probe_initrd {
  echo RETURN_INITRD_ARGC=$#
  echo RETURN_INITRD_ARGS=$*
  echo RETURN_ENV=$fallback,$next_entry,$saved_entry,$gfxpayload
  exit
}
"""
    probe = (
      menu.replace("set timeout=5", "set timeout=0")
      .replace("  linux ", "  probe_linux ")
      .replace("  initrd ", "  probe_initrd ")
    )
    if index:
      probe = probe.replace("set default=0", "set default=1")
    (root / "menu.cfg").write_text(wrappers + probe)
    (root / "grub.cfg").write_text(
      "set fallback=stale\nset next_entry=stale\nset saved_entry=stale\nset default=stale\nconfigfile /boot/grub/menu.cfg\nexit\n"
    )
    image = case / "root.img"
    command = [
      "mkfs.ext4",
      "-q",
      "-F",
      "-U",
      UUID,
      "-d",
      str(case / "root"),
      str(image),
      "16384",
    ]
    subprocess.run(command, check=True, capture_output=True, timeout=30)
    mapping = case / "device.map"
    mapping.write_text(f"(hd0) {image}\n")
    command = [str(EMU), "-r", "hd0", "-m", str(mapping), "-d", "/boot/grub"]
    result = subprocess.run(
      command,
      capture_output=True,
      text=True,
      check=False,
      timeout=15,
      env={"PATH": "/usr/bin", "TERM": "dumb"},
    )
    log = result.stdout + result.stderr
    (case / "runtime.log").write_text(log)
    compact = re.sub(r"\s+", "", re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", log))
    assert result.returncode == 0, log
    assert "RETURN_LINUX_ARGC=6" in compact and "RETURN_INITRD_ARGC=1" in compact, log
    assert (
      f"RETURN_LINUX_ARGS=/boot/dev147-{release}/Imageroot=UUID={UUID}rwloglevel=3quietdisablehooks=encrypt"
      in compact
    ), log
    assert f"RETURN_INITRD_ARGS=/boot/dev147-{release}/initramfs.img" in compact, log
    assert "RETURN_ENV=,,,keep" in compact, log
    results.append(
      {
        "selection": index,
        "release": release,
        "command": command,
        "exit": result.returncode,
      }
    )
  (output / "receipt.json").write_text(
    json.dumps(
      {
        "status": "PASS_REAL_GRUB_MENU",
        "menu_sha256": hashlib.sha256(menu.encode()).hexdigest(),
        "emulator_sha256": hashlib.sha256(EMU.read_bytes()).hexdigest(),
        "cases": results,
        "limits": "Real GRUB parser/menu/search against disposable ext4 image. Kernel/initrd commands capture arguments; timeout is zero. Second-entry selection substitutes default1. No kernel load, firmware or EFI execution.",
      },
      indent=2,
    )
    + "\n"
  )
  print(
    "PASS: actual menu default trial and selectable Fairydust1; stale selection variables cleared"
  )


if __name__ == "__main__":
  main()
