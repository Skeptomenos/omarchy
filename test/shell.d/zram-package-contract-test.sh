#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

require_command python3
require_command makepkg

ROOT="$ROOT" python3 <<'PY'
import os
import re
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


def dependency_names(path: Path, *, common_only: bool) -> set[str]:
  try:
    metadata = subprocess.run(
      ["makepkg", "--printsrcinfo"],
      cwd=path.parent,
      check=True,
      capture_output=True,
      text=True,
    ).stdout
  except subprocess.CalledProcessError as error:
    raise ValueError(f"{path}: makepkg --printsrcinfo failed: {error.stderr.strip()}") from error

  dependencies = set()
  for line in metadata.splitlines():
    key, separator, value = line.strip().partition(" = ")
    if separator and (key == "depends" or (not common_only and key.startswith("depends_"))):
      dependencies.add(re.split(r"[<>=]", value, maxsplit=1)[0])
  return dependencies


root = Path(os.environ["ROOT"])
home = Path.home()
pkgs_candidates = [
  root.parent / "omarchy-pkgs/pkgbuilds",
  root.parent / "omarchy/omarchy-pkgs/pkgbuilds",
  root.parent.parent / "omarchy-pkgs/pkgbuilds",
  root.parent / "omacom/omarchy-pkgs/pkgbuilds",
  root.parent.parent / "omacom/omarchy-pkgs/pkgbuilds",
  home / "Work/omacom/omarchy-pkgs/pkgbuilds",
]
override = os.environ.get("OMARCHY_PKGS_PATH")
if override:
  pkgs_candidates = [Path(override) / "pkgbuilds", Path(override)] + pkgs_candidates

pkgs_root = next((path for path in pkgs_candidates if path.is_dir()), None)
if pkgs_root is None:
  print("not ok - omarchy-pkgs checkout found for zram package coverage", file=sys.stderr)
  print(
    "looked in:\n  " + "\n  ".join(str(path) for path in pkgs_candidates) +
    "\nset OMARCHY_PKGS_PATH to the omarchy-pkgs checkout",
    file=sys.stderr,
  )
  sys.exit(1)

errors = []
target_packages = ("omarchy", "omarchy-dev")
settings_packages = ("omarchy-settings", "omarchy-settings-dev")

with TemporaryDirectory(prefix="omarchy-zram-recipes-") as work:
  prepared = Path(work) / "recipes"
  try:
    subprocess.run(
      ["bash", str(root / "build-inputs/prepare-recipes.sh"), str(pkgs_root), str(prepared)],
      check=True,
      env={**os.environ, "OMARCHY_ALLOW_CUSTOM_RECIPES": "0"},
    )
  except subprocess.CalledProcessError:
    print("not ok - pinned recipe preparation failed", file=sys.stderr)
    sys.exit(1)

  for package in target_packages + settings_packages:
    pkgbuild = prepared / "pkgbuilds" / package / "PKGBUILD"
    if not pkgbuild.is_file():
      errors.append(f"missing PKGBUILD: {pkgbuild}")
      continue

    try:
      dependencies = dependency_names(pkgbuild, common_only=package in target_packages)
    except ValueError as error:
      errors.append(str(error))
      continue

    if package in target_packages and "zram-generator" not in dependencies:
      errors.append(f"{package} must hard-depend on zram-generator in common depends")
    if package in settings_packages and "zram-generator" in dependencies:
      errors.append(
        f"{package} must not hard-depend on zram-generator because it is installed in the live ISO"
      )

other_packages = {
  line.split("#", 1)[0].strip()
  for line in (root / "install/omarchy-other.packages").read_text().splitlines()
  if line.split("#", 1)[0].strip()
}
if "zram-generator" not in other_packages:
  errors.append("install/omarchy-other.packages must keep zram-generator available to the ISO builder")

if errors:
  print("\n".join(errors), file=sys.stderr)
  sys.exit(1)
PY

pass "pinned prepared target packages require zram-generator in common depends without making settings unsafe for the live ISO"
