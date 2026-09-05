from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import repair


def main() -> None:
  with tempfile.TemporaryDirectory(prefix="dev147-cleanup-control.") as temporary:
    root = Path(temporary)
    units = root / "units"
    units.mkdir()
    shutil.copyfile(repair.SOURCE / repair.UNIT, units / repair.UNIT)
    drop = units / f"{repair.UNIT}.d"
    drop.mkdir()
    shutil.copyfile(repair.SOURCE / repair.DROP_NAME, drop / repair.DROP_NAME)
    environment = dict(os.environ, SYSTEMD_UNIT_PATH=f"{units}:/usr/lib/systemd/system")
    syntax = subprocess.run(
      ["/usr/bin/systemd-analyze", "verify", repair.UNIT],
      env=environment,
      capture_output=True,
      text=True,
      timeout=30,
      check=False,
    )
    assert syntax.returncode == 0, syntax.stderr
    body = repair.effective_command((drop / repair.DROP_NAME).read_text()).replace(
      "$$", "$"
    )
    original = repair.effective_command((units / repair.UNIT).read_text()).replace(
      "$$", "$"
    )
    skip = "if [[ ${i##*/} = '7.1.12-dev147-fairydust1' || ${i##*/} = '7.1.12-dev147-clearwait100' ]]; then continue; fi; "
    assert body == original.replace("do if [[", "do " + skip + "if [[")
    modules = root / "modules"
    (modules / ".old").mkdir(parents=True)
    releases = [
      os.uname().release,
      "7.0.0-packaged",
      "7.0.0-unowned",
      *(item.release for item in repair.DELIVERIES),
    ]
    for release in releases:
      (modules / release).mkdir()
      (modules / release / "payload").write_text(release)
    pacman = root / "pacman"
    pacman.write_text(
      '#!/bin/bash\n[[ $1 == "-Qo" ]] || exit 99\n[[ $2 == */7.0.0-packaged ]]\n'
    )
    pacman.chmod(0o700)
    command = [
      "/usr/bin/bwrap",
      "--die-with-parent",
      "--ro-bind",
      "/",
      "/",
      "--bind",
      str(modules),
      "/usr/lib/modules",
      "--ro-bind",
      str(pacman),
      "/usr/bin/pacman",
      "/bin/bash",
      "-exc",
      body,
    ]
    result = subprocess.run(
      command, capture_output=True, text=True, check=False, timeout=30
    )
    assert result.returncode == 0, result.stdout + result.stderr
    for release in releases:
      destination = modules / (".old" if release == "7.0.0-unowned" else "") / release
      assert (destination / "payload").read_text() == release
    assert not (modules / "7.0.0-unowned").exists()
    for delivery in repair.DELIVERIES:
      assert not (modules / ".old" / delivery.release).exists()
    print(
      "PASS: systemd syntax and actual cleanup body preserve both candidates/current/packaged, archive unrelated unowned release"
    )
    print(
      "LIMIT: systemd variable expansion is decoded for this pinned unit; pacman ownership is a fixture; bash/rsync/rm run on disposable trees."
    )


if __name__ == "__main__":
  main()
