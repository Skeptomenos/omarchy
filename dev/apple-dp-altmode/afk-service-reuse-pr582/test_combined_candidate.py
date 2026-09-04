from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Sequence


EXPECTED_SOURCE_COMMIT = "e2e1930a9595bffafad92cec2b5504525efb9cd4"
AFK_FILES = (
  Path("drivers/gpu/drm/apple/afk.c"),
  Path("drivers/gpu/drm/apple/afk.h"),
  Path("drivers/gpu/drm/apple/epic/dpavservep.c"),
  Path("drivers/gpu/drm/apple/epic/dpavservep.h"),
  Path("drivers/gpu/drm/apple/iomfb.c"),
)
TIMEOUT_FILE = Path("drivers/gpu/drm/apple/iomfb_template.c")
DCP_FILE = Path("drivers/gpu/drm/apple/dcp.c")
COMBINED_FILES = (*AFK_FILES, TIMEOUT_FILE)
POWER_WAIT = "ret = wait_for_completion_timeout(&cookie->done, msecs_to_jiffies(50));"
CRASH_STORE = "dcp->crashed = true;"
WARNING = '"%s: timed out waiting for the poweroff clear swap; continuing\\n",'


class ContractError(RuntimeError):
  pass


def run(arguments: Sequence[str], cwd: Path) -> subprocess.CompletedProcess[str]:
  return subprocess.run(
    list(arguments),
    cwd=cwd,
    check=False,
    capture_output=True,
    text=True,
    timeout=45,
  )


def require(condition: bool, message: str) -> None:
  if not condition:
    raise ContractError(message)


def require_success(result: subprocess.CompletedProcess[str], action: str) -> None:
  require(
    result.returncode == 0,
    f"{action} failed\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}",
  )


def extract_function(source: str, marker: str) -> str:
  name_position = source.find(marker)
  require(name_position >= 0, f"function marker missing: {marker}")
  opening_brace = source.find("{", name_position)
  require(opening_brace >= 0, f"function body missing: {marker}")
  depth = 0
  for position in range(opening_brace, len(source)):
    character = source[position]
    if character == "{":
      depth += 1
    elif character == "}":
      depth -= 1
      if depth == 0:
        return source[name_position : position + 1]
  raise ContractError(f"function body incomplete: {marker}")


def require_order(source: str, tokens: Sequence[str], name: str) -> None:
  position = -1
  for token in tokens:
    next_position = source.find(token, position + 1)
    require(next_position >= 0, f"{name} missing token: {token}")
    position = next_position


def verify_source(source_root: Path) -> None:
  revision = run(("git", "rev-parse", "HEAD"), source_root)
  require_success(revision, "source revision check")
  require(
    revision.stdout.strip() == EXPECTED_SOURCE_COMMIT,
    f"source revision mismatch: {revision.stdout.strip()}",
  )
  status = run(
    (
      "git",
      "status",
      "--porcelain=v1",
      "--untracked-files=no",
      "--",
      *(str(path) for path in (*COMBINED_FILES, DCP_FILE)),
    ),
    source_root,
  )
  require_success(status, "source cleanliness check")
  require(not status.stdout, f"accepted source files are modified: {status.stdout.strip()}")


def copy_sources(source_root: Path, build_root: Path) -> None:
  for relative_path in (*COMBINED_FILES, DCP_FILE):
    destination = build_root / relative_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_root / relative_path, destination)


def apply_patch(build_root: Path, patch_path: Path) -> None:
  checked = run(("git", "apply", "--check", str(patch_path)), build_root)
  require_success(checked, f"patch check: {patch_path.name}")
  applied = run(("git", "apply", str(patch_path)), build_root)
  require_success(applied, f"patch application: {patch_path.name}")


def changed_files(source_root: Path, build_root: Path) -> tuple[Path, ...]:
  return tuple(
    path
    for path in (*COMBINED_FILES, DCP_FILE)
    if (source_root / path).read_bytes() != (build_root / path).read_bytes()
  )


def verify_patch_text(timeout_patch: Path) -> None:
  text = timeout_patch.read_text(encoding="utf-8")
  added_comments = ("+//", "+/*", "+ *", "+\t//", "+\t/*")
  require(
    not any(line.startswith(added_comments) for line in text.splitlines()),
    "timeout patch adds a code comment",
  )
  removed_code = tuple(
    line[1:].strip()
    for line in text.splitlines()
    if line.startswith("-") and not line.startswith("---")
  )
  added_code = tuple(
    line[1:].strip()
    for line in text.splitlines()
    if line.startswith("+") and not line.startswith("+++")
  )
  require(removed_code == (CRASH_STORE,), f"unexpected removed code: {removed_code}")
  require(
    added_code == (
      "dev_warn(dcp->dev,",
      '"%s: timed out waiting for the poweroff clear swap; continuing\\n",',
      "__func__);",
    ),
    f"unexpected added code: {added_code}",
  )


def verify_combined_contract(build_root: Path) -> None:
  iomfb = (build_root / TIMEOUT_FILE).read_text(encoding="utf-8")
  dcp = (build_root / DCP_FILE).read_text(encoding="utf-8")
  poweroff = extract_function(iomfb, "void DCP_FW_NAME(iomfb_poweroff)")
  crash_callback = extract_function(dcp, "static void dcp_rtk_crashed")
  atomic_check = extract_function(dcp, "int dcp_crtc_atomic_check")
  require(poweroff.count(POWER_WAIT) == 1, "50 ms poweroff wait changed or duplicated")
  require(CRASH_STORE not in poweroff, "AFK-only timeout crash store remains")
  require_order(
    poweroff,
    (
      POWER_WAIT,
      "swap_id = cookie->swap_id;",
      "kref_put(&cookie->refcount, release_swap_cookie);",
      "if (ret <= 0) {",
      "dev_warn(dcp->dev,",
      WARNING,
      "__func__);",
      "return;",
      "dev_dbg(dcp->dev, \"%s: clear swap submitted: %u\\n\", __func__, swap_id);",
    ),
    "poweroff timeout flow",
  )
  require(dcp.count(CRASH_STORE) == 1, "genuine crash writer count changed")
  require(CRASH_STORE in crash_callback, "RTKit crash writer changed")
  require('dev_err(dcp->dev, "DCP has crashed\\n");' in crash_callback, "RTKit crash log changed")
  require_order(
    atomic_check,
    ("if (dcp->crashed)", "return -EINVAL;"),
    "atomic crash guard",
  )


def mutation_must_fail(build_root: Path, path: Path, old: str, new: str, name: str) -> None:
  target = build_root / path
  original = target.read_text(encoding="utf-8")
  require(original.count(old) == 1, f"negative control input is ambiguous: {name}")
  target.write_text(original.replace(old, new), encoding="utf-8")
  try:
    verify_combined_contract(build_root)
  except ContractError:
    pass
  else:
    raise ContractError(f"negative control passed: {name}")
  finally:
    target.write_text(original, encoding="utf-8")


def run_afk_lifecycle(source_root: Path, afk_root: Path) -> None:
  result = run(
    (
      sys.executable,
      "-I",
      "-S",
      "-B",
      str(afk_root / "test_afk_service_reuse.py"),
      "--source-root",
      str(source_root),
    ),
    afk_root,
  )
  sys.stdout.write(result.stdout)
  sys.stderr.write(result.stderr)
  require_success(result, "AFK lifecycle suite")


def parse_arguments(arguments: Sequence[str]) -> tuple[Path, bool]:
  require(
    len(arguments) in (2, 3) and arguments[0] == "--source-root",
    "usage: test_combined_candidate.py --source-root PATH [--red-only]",
  )
  red_only = len(arguments) == 3 and arguments[2] == "--red-only"
  require(
    len(arguments) == 2 or red_only,
    "usage: test_combined_candidate.py --source-root PATH [--red-only]",
  )
  return Path(arguments[1]).resolve(), red_only


def main(arguments: Sequence[str]) -> int:
  try:
    source_root, red_only = parse_arguments(arguments)
    verify_source(source_root)
    combined_root = Path(__file__).resolve().parent
    afk_root = combined_root.parent / "afk-service-reuse"
    timeout_patch = combined_root / "pr582-timeout.patch"
    verify_patch_text(timeout_patch)

    with tempfile.TemporaryDirectory(prefix="dev147-afk-pr582-") as directory:
      build_root = Path(directory)
      copy_sources(source_root, build_root)
      apply_patch(build_root, afk_root / "afk-service-reuse.patch")

      if red_only:
        try:
          verify_combined_contract(build_root)
        except ContractError as error:
          require("AFK-only timeout crash store remains" in str(error), f"unexpected RED: {error}")
          print(f"RED: {error}", file=sys.stderr)
          return 1
        raise ContractError("AFK-only source unexpectedly passed the combined contract")

      require(
        changed_files(source_root, build_root) == AFK_FILES,
        "AFK patch changed an unexpected source set",
      )
      apply_patch(build_root, timeout_patch)
      require(
        changed_files(source_root, build_root) == COMBINED_FILES,
        "combined patch changed an unexpected source set",
      )
      verify_combined_contract(build_root)
      mutation_must_fail(build_root, TIMEOUT_FILE, "msecs_to_jiffies(50)", "msecs_to_jiffies(49)", "wait")
      mutation_must_fail(
        build_root,
        TIMEOUT_FILE,
        "\t\t\t __func__);\n\t\treturn;\n\t}\n\n\tdev_dbg",
        "\t\t\t __func__);\n\t}\n\n\tdev_dbg",
        "return",
      )
      mutation_must_fail(
        build_root,
        TIMEOUT_FILE,
        "\tif (ret <= 0) {\n\t\tdev_warn(dcp->dev,",
        f"\tif (ret <= 0) {{\n\t\t{CRASH_STORE}\n\t\tdev_warn(dcp->dev,",
        "timeout store",
      )
      mutation_must_fail(build_root, DCP_FILE, CRASH_STORE, "dcp->crashed = false;", "RTKit writer")
      mutation_must_fail(build_root, DCP_FILE, "if (dcp->crashed)\n\t\treturn -EINVAL;", "if (false)\n\t\treturn -EINVAL;", "atomic guard")

    run_afk_lifecycle(source_root, afk_root)
    print("PASS: exact AFK lifecycle and PR582 timeout contracts passed")
    return 0
  except (ContractError, OSError, subprocess.SubprocessError) as error:
    print(f"ERROR: {error}", file=sys.stderr)
    return 2


if __name__ == "__main__":
  raise SystemExit(main(sys.argv[1:]))
