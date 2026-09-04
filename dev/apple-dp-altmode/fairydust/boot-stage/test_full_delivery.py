from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from test_stage import HELPER, RELEASE, StageTests, digest

OUTPUT = Path(
  "/home/david/Work/dev147-fairydust-boot-20260905/stage/full-delivery-sandbox"
)
DELIVERY = Path("/home/david/Work/dev147-fairydust-boot-20260905/delivery")
MANIFEST = "f33054856e60d3baf5cb7630cb8d7dfc60ffa586e16456c3e7313fffe6f7c59d"


def main() -> None:
  OUTPUT.mkdir(mode=0o700, parents=True, exist_ok=True)
  os.environ["TMPDIR"] = str(OUTPUT)
  assert digest(DELIVERY / "SHA256SUMS") == MANIFEST
  case = StageTests()
  case.setUp()
  try:
    launcher = HELPER.with_name("launch.sh").read_text()
    bootstrap = launcher.split("<<'DEV147_STAGE_BOOTSTRAP'\n", 1)[1].split(
      "\nDEV147_STAGE_BOOTSTRAP", 1
    )[0]
    helper_hash = launcher.split("helper_hash=", 1)[1].splitlines()[0]
    assert helper_hash == digest(HELPER)
    command = case.command()[:-3] + [
      "-c",
      bootstrap,
      str(HELPER),
      helper_hash,
      str(DELIVERY),
      MANIFEST,
    ]
    with (
      (OUTPUT / "stdout.json").open("w") as stdout,
      (OUTPUT / "stderr.log").open("w") as stderr,
    ):
      result = subprocess.run(
        command, stdout=stdout, stderr=stderr, timeout=280, check=False
      )
    assert result.returncode == 0, (OUTPUT / "stderr.log").read_text()
    for path, expected in case.before.items():
      assert digest(case.root / path) == expected, path
    published = case.root / f"modules/{RELEASE}"
    module_count = len(list(published.rglob("*.ko")))
    assert module_count == 1862
    for module in published.rglob("*"):
      if module.is_file():
        assert digest(module) == digest(
          DELIVERY / "root/lib/modules" / RELEASE / module.relative_to(published)
        )
    for name in ("Image", "initramfs.img", "boot.bin", "config", "t8112-j413.dtb"):
      assert digest(case.root / f"boot/dev147-fairydust-{RELEASE}" / name) == digest(
        DELIVERY / name
      )
    report = {
      "verdict": "PASS",
      "command": command,
      "exit": result.returncode,
      "modules": module_count,
      "manifest_sha256": MANIFEST,
      "helper_sha256": helper_hash,
      "protected_fixture_preserved": True,
      "scope": "Full frozen delivery through exact launcher bootstrap and root stage entrypoint in unprivileged bwrap; disposable targets only; no live installation or selection.",
    }
    (OUTPUT / "receipt.json").write_text(json.dumps(report, indent=2) + "\n")
    print(
      f"PASS: full frozen delivery staged in sandbox; {module_count} modules; protected fixtures preserved"
    )
  finally:
    case.tearDown()


if __name__ == "__main__":
  main()
