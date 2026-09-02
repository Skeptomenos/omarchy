from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


EXPECTED_SOURCE_COMMIT = "e2e1930a9595bffafad92cec2b5504525efb9cd4"
SOURCE_FILES = (
  Path("drivers/gpu/drm/apple/afk.c"),
  Path("drivers/gpu/drm/apple/afk.h"),
  Path("drivers/gpu/drm/apple/epic/dpavservep.c"),
  Path("drivers/gpu/drm/apple/epic/dpavservep.h"),
  Path("drivers/gpu/drm/apple/iomfb.c"),
)
AFK_FUNCTIONS = (
  "afk_epic_service_can_reuse",
  "afk_epic_try_retire_locked",
  "afk_epic_reserve_command_locked",
  "afk_epic_release_command_locked",
  "afk_epic_prepare_service",
  "afk_service_get",
  "afk_service_put",
  "afk_service_request_retirement",
  "afk_send_command",
)
DPAV_FUNCTIONS = (
  "dcpavserv_init",
  "dcpavserv_teardown",
  "dcpdpserv_teardown",
  "dcpavserv_get",
  "dcpavserv_put",
)
BASELINE_CAPACITY = "if (ep->num_channels >= AFK_MAX_CHANNEL)"
BASELINE_ALLOCATION = "ch_idx = ep->num_channels++;"
HELPER_PLACEHOLDER = "AFK_CANDIDATE_HELPER_BODY"


@dataclass(frozen=True)
class Configuration:
  source_root: Path
  red_only: bool


@dataclass(frozen=True)
class CommandResult:
  returncode: int
  stdout: str
  stderr: str


@dataclass(frozen=True)
class CandidateSources:
  afk: Path
  dpav: Path
  iomfb: Path


def parse_arguments(arguments: Sequence[str]) -> Configuration:
  if len(arguments) not in (2, 3) or arguments[0] != "--source-root":
    raise ValueError("usage: test_afk_service_reuse.py --source-root PATH [--red-only]")

  red_only = len(arguments) == 3 and arguments[2] == "--red-only"
  if len(arguments) == 3 and not red_only:
    raise ValueError("usage: test_afk_service_reuse.py --source-root PATH [--red-only]")

  return Configuration(source_root=Path(arguments[1]).resolve(), red_only=red_only)


def run(command: Sequence[str], cwd: Path) -> CommandResult:
  completed = subprocess.run(
    list(command),
    cwd=cwd,
    check=False,
    capture_output=True,
    text=True,
    timeout=30,
  )
  return CommandResult(completed.returncode, completed.stdout, completed.stderr)


def require_success(result: CommandResult, action: str) -> None:
  if result.returncode == 0:
    return
  raise RuntimeError(f"{action} failed\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}")


def verify_source(source_root: Path) -> None:
  revision = run(("git", "rev-parse", "HEAD"), source_root)
  require_success(revision, "source identity check")
  if revision.stdout.strip() != EXPECTED_SOURCE_COMMIT:
    raise RuntimeError(
      f"source identity mismatch: expected {EXPECTED_SOURCE_COMMIT}, got {revision.stdout.strip()}"
    )

  source_status = run(
    (
      "git",
      "status",
      "--porcelain=v1",
      "--untracked-files=no",
      "--",
      *(str(path) for path in SOURCE_FILES),
    ),
    source_root,
  )
  require_success(source_status, "source cleanliness check")
  if source_status.stdout:
    raise RuntimeError(f"accepted source files are modified: {source_status.stdout.strip()}")

  afk_text = (source_root / SOURCE_FILES[0]).read_text(encoding="utf-8")
  if BASELINE_CAPACITY not in afk_text or BASELINE_ALLOCATION not in afk_text:
    raise RuntimeError("accepted source no longer contains the monotonic allocator contract")


def extract_function(source_text: str, function_name: str) -> str:
  name_position = source_text.find(f"{function_name}(")
  if name_position < 0:
    raise RuntimeError(f"candidate function not found: {function_name}")

  start = source_text.rfind("\n\n", 0, name_position)
  opening_brace = source_text.find("{", name_position)
  if opening_brace < 0:
    raise RuntimeError(f"candidate function declaration is incomplete: {function_name}")
  start = 0 if start < 0 else start + 2

  depth = 0
  for position in range(opening_brace, len(source_text)):
    character = source_text[position]
    if character == "{":
      depth += 1
    elif character == "}":
      depth -= 1
      if depth == 0:
        return source_text[start : position + 1]

  raise RuntimeError(f"candidate function body is incomplete: {function_name}")


def render_harness(template: str, functions: str) -> str:
  if template.count(HELPER_PLACEHOLDER) != 1:
    raise RuntimeError("harness helper placeholder is missing or duplicated")
  return template.replace(HELPER_PLACEHOLDER, functions)


def build_harness(source: str, build_root: Path) -> Path:
  source_path = build_root / "harness.c"
  binary_path = build_root / "harness"
  source_path.write_text(source, encoding="utf-8")
  compile_result = run(
    (
      "cc",
      "-std=c11",
      "-Wall",
      "-Wextra",
      "-Werror",
      "-Wno-unused-parameter",
      str(source_path),
      "-o",
      str(binary_path),
    ),
    build_root,
  )
  require_success(compile_result, "harness build")
  return binary_path


def apply_candidate_patch(source_root: Path, patch_file: Path, build_root: Path) -> CandidateSources:
  for relative_source in SOURCE_FILES:
    candidate_source = build_root / relative_source
    candidate_source.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_root / relative_source, candidate_source)

  check_result = run(("git", "apply", "--check", str(patch_file)), build_root)
  require_success(check_result, "candidate patch check")
  apply_result = run(("git", "apply", str(patch_file)), build_root)
  require_success(apply_result, "candidate patch application")

  return CandidateSources(
    afk=build_root / SOURCE_FILES[0],
    dpav=build_root / SOURCE_FILES[2],
    iomfb=build_root / SOURCE_FILES[4],
  )


def require_order(source: str, tokens: Sequence[str], contract: str) -> None:
  position = -1
  for token in tokens:
    next_position = source.find(token, position + 1)
    if next_position < 0:
      raise RuntimeError(f"{contract} is missing: {token}")
    position = next_position


def verify_candidate_contract(candidate: CandidateSources, patch_file: Path) -> str:
  afk_text = candidate.afk.read_text(encoding="utf-8")
  dpav_text = candidate.dpav.read_text(encoding="utf-8")
  iomfb_text = candidate.iomfb.read_text(encoding="utf-8")
  patch_text = patch_file.read_text(encoding="utf-8")

  helper_source = "\n\n".join(
    extract_function(afk_text, function_name) for function_name in AFK_FUNCTIONS
  )
  owner_source = "\n\n".join(
    extract_function(dpav_text, function_name) for function_name in DPAV_FUNCTIONS
  )

  require_order(
    extract_function(afk_text, "afk_recv_handle_reply"),
    (
      "rxbuf = service->cmds[idx].rxbuf;",
      "afk_epic_release_command_locked(service, idx);",
      "spin_unlock_irqrestore(&service->lock, flags);",
      "if (rxbuf && rxlen)",
      "dma_free_coherent",
    ),
    "deferred reply-buffer release order",
  )
  send_command_source = extract_function(afk_text, "afk_send_command")
  require_order(
    send_command_source,
    (
      "spin_lock_irqsave(&service->lock, flags);",
      "idx = afk_epic_reserve_command_locked(service);",
      "if (idx < 0)",
      "ret = idx;",
      "goto err_unlock;",
      "service->cmds[idx].completion = &completion;",
      "init_completion(&completion);",
      "ret = afk_send_epic",
      "if (ret)",
      "afk_epic_release_command_locked(service, idx);",
      "goto err_unlock;",
      "spin_unlock_irqrestore(&service->lock, flags);",
    ),
    "serialized command admission and send",
  )
  send_position = send_command_source.find("ret = afk_send_epic")
  first_unlock_position = send_command_source.find(
    "spin_unlock_irqrestore(&service->lock, flags);"
  )
  if first_unlock_position < send_position:
    raise RuntimeError("service lock is released before the command send boundary")
  require_order(
    send_command_source,
    (
      "ret = afk_send_epic",
      "if (ret)",
      "afk_epic_release_command_locked(service, idx);",
      "goto err_unlock;",
      "err_unlock:",
      "spin_unlock_irqrestore(&service->lock, flags);",
      "dma_free_coherent(ep->dcp->dev, payload_len, txbuf, txbuf_dma);",
    ),
    "send-failure command cleanup",
  )
  require_order(
    send_command_source,
    (
      "spin_unlock_irqrestore(&service->lock, flags);",
      "ret = wait_for_completion_timeout",
      "if (ret <= 0)",
      "service->cmds[idx].completion = NULL;",
      "service->cmds[idx].free_on_ack = true;",
      "spin_unlock_irqrestore(&service->lock, flags);",
      "return -ETIMEDOUT;",
    ),
    "successful-send timeout and late-reply behavior",
  )
  send_epic_declaration = afk_text.find("\nint afk_send_epic(")
  if send_epic_declaration < 0:
    raise RuntimeError("afk_send_epic definition is missing")
  send_epic_source = extract_function(
    afk_text[send_epic_declaration + 1 :],
    "afk_send_epic",
  )
  if afk_text.count("spin_lock_irqsave(&ep->lock, flags);") != 1:
    raise RuntimeError("endpoint send lock has an unexpected acquisition path")
  if "spin_lock_irqsave(&ep->lock, flags);" not in send_epic_source:
    raise RuntimeError("endpoint send lock is outside afk_send_epic")
  if "service->lock" in send_epic_source:
    raise RuntimeError("afk_send_epic introduces an endpoint-to-service lock inversion")
  if afk_text.count("bitmap_find_free_region(service->cmd_map") != 1:
    raise RuntimeError("command bitmap allocation bypasses the extracted admission helper")
  require_order(
    iomfb_text,
    (
      "service = dcpavserv_get(&dcp->dcpavserv);",
      "edid = dcpavserv_copy_edid(service);",
      "dcpavserv_put(service);",
    ),
    "protected EDID owner acquisition",
  )
  if "dcp->dcpavserv.enabled" in iomfb_text or "dcp->dcpavserv.service" in iomfb_text:
    raise RuntimeError("iomfb retains an unprotected dcpav service read")
  if dpav_text.count(".reusable = true") != 2:
    raise RuntimeError("reuse opt-in is not limited to the two dpav endpoint services")

  added_comment_prefixes = ("+//", "+/*", "+ *", "+\t//", "+\t/*")
  if any(line.startswith(added_comment_prefixes) for line in patch_text.splitlines()):
    raise RuntimeError("candidate patch adds a code comment")

  return f"{helper_source}\n\n{owner_source}"


def require_expected_red(result: CommandResult, marker: str, contract: str) -> None:
  sys.stdout.write(result.stdout)
  sys.stderr.write(result.stderr)
  if result.returncode == 0:
    raise RuntimeError(f"{contract} unexpectedly passed")
  if marker not in result.stderr:
    raise RuntimeError(f"{contract} failed outside its expected boundary")


def main(arguments: Sequence[str]) -> int:
  try:
    configuration = parse_arguments(arguments)
    verify_source(configuration.source_root)
    test_root = Path(__file__).resolve().parent
    patch_file = test_root / "afk-service-reuse.patch"
    template = (test_root / "harness.c").read_text(encoding="utf-8")

    with tempfile.TemporaryDirectory(prefix="dev147-afk-reuse-") as temporary_directory:
      build_root = Path(temporary_directory)
      candidate_sources = apply_candidate_patch(
        configuration.source_root,
        patch_file,
        build_root,
      )
      exact_functions = verify_candidate_contract(candidate_sources, patch_file)
      binary = build_harness(render_harness(template, exact_functions), build_root)

      stock = run((str(binary), "stock"), build_root)
      require_expected_red(
        stock,
        "CAPACITY: generation=8 member=0 slots=16",
        "stock generation probe",
      )
      unsafe = run((str(binary), "unsafe"), build_root)
      require_expected_red(
        unsafe,
        "UNSAFE_REUSE: disabled pending slot erased",
        "unsafe disabled-slot candidate probe",
      )
      unsafe_send = run((str(binary), "unsafe-send"), build_root)
      require_expected_red(
        unsafe_send,
        "UNSAFE_SEND: post-teardown command stranded retirement",
        "unsafe post-teardown command probe",
      )
      unsafe_race = run((str(binary), "unsafe-race"), build_root)
      require_expected_red(
        unsafe_race,
        "UNSAFE_RACE: teardown transitioned between reserve and send",
        "unsafe reserve-teardown-send probe",
      )

      if configuration.red_only:
        return 1

      candidate = run((str(binary), "candidate"), build_root)
      sys.stdout.write(candidate.stdout)
      sys.stderr.write(candidate.stderr)
      require_success(candidate, "candidate lifecycle harness")

    print("PASS: all RED controls failed; exact quiescent-retirement code passed")
    return 0
  except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as error:
    print(f"ERROR: {error}", file=sys.stderr)
    return 2


if __name__ == "__main__":
  raise SystemExit(main(sys.argv[1:]))
