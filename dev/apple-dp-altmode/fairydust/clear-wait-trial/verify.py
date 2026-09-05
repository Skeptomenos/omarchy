import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

BASE = "83604c8b18e4673ed91e1172aef9aebeb0af20ce"
CANDIDATE = "d2f36591abdb0db296ac24e5a2b9dade5ae40ef1"
TARGET = "drivers/gpu/drm/apple/iomfb_template.c"
COMPLETION_HASH = "79f10c4e41095aa647591de8edec1ed037fff51737d2b1082e8b88ebbdedcfbe"
OLD = "ret = wait_for_completion_timeout(&cookie->done, msecs_to_jiffies(50));"
NEW = OLD.replace("(50)", "(100)")
HERE = Path(__file__).resolve().parent


def run(command: list[str], cwd: Path) -> str:
  return subprocess.check_output(command, cwd=cwd, text=True, timeout=30)


def extract(source: str, signature: str) -> str:
  assert source.count(signature) == 1, signature
  start = source.index(signature)
  end = source.index("\n}", start) + 2
  return source[start:end] + "\n"


def main() -> None:
  assert len(sys.argv) == 4, "verify.py SOURCE NEW_OUTPUT baseline|candidate"
  source, output = Path(sys.argv[1]), Path(sys.argv[2])
  mode = sys.argv[3]
  assert mode in ("baseline", "candidate")
  output.mkdir(mode=0o700)
  base = run(["git", "show", f"{BASE}:{TARGET}"], source)
  assert base.count(OLD) == 1
  actual = (source / TARGET).read_text()
  expected = base if mode == "baseline" else base.replace(OLD, NEW)
  assert actual == expected, "unexpected template change"
  assert run(["git", "rev-parse", "HEAD"], source).strip() == (
    BASE if mode == "baseline" else CANDIDATE
  )
  assert run(["git", "status", "--porcelain"], source) == ""
  completion = (source / "kernel/sched/completion.c").read_bytes()
  assert hashlib.sha256(completion).hexdigest() == COMPLETION_HASH
  signatures = (
    "static void complete_with_flags(",
    "void complete(struct completion *x)",
    "static inline long __sched\ndo_wait_for_common(",
    "static inline long __sched\n__wait_for_common(",
    "static long __sched\nwait_for_common(",
    "unsigned long __sched\nwait_for_completion_timeout(",
  )
  extracted = "\n".join(extract(completion.decode(), item) for item in signatures)
  (output / "completion-extracted.c").write_text(extracted)
  command = [
    "cc",
    "-std=gnu11",
    "-Wall",
    "-Wextra",
    "-Werror",
    "-O2",
    "-fsanitize=undefined",
    "-fno-sanitize-recover=undefined",
    "-I",
    str(output),
    str(HERE / "completion-harness.c"),
    "-o",
    str(output / "completion-harness"),
  ]
  run(command, source)
  budget_match = re.search(
    r"msecs_to_jiffies\((\d+)\)", OLD if mode == "baseline" else NEW
  )
  assert budget_match
  result = subprocess.run(
    [str(output / "completion-harness"), budget_match[1]],
    capture_output=True,
    text=True,
    timeout=10,
    check=False,
  )
  (output / "harness.stdout").write_text(result.stdout)
  (output / "harness.stderr").write_text(result.stderr)
  assert result.returncode == (1 if mode == "baseline" else 0), result.stderr
  if mode == "candidate":
    assert not result.stderr
    names = run(["git", "diff", "--name-only", BASE], source).splitlines()
    assert names == [TARGET], names
    diff = run(
      ["git", "diff", "--no-ext-diff", "--no-renames", BASE, "--", TARGET], source
    )
    assert diff == (HERE / "clear-wait-100ms.patch").read_text(), "patch mismatch"
    assert run(["git", "ls-files", "--others", "--exclude-standard"], source) == ""
  receipt = {
    "status": "EXPECTED_RED" if mode == "baseline" else "PASS_OFFLINE_ONLY",
    "source_head": run(["git", "rev-parse", "HEAD"], source).strip(),
    "base": BASE,
    "template_sha256": hashlib.sha256(actual.encode()).hexdigest(),
    "completion_sha256": COMPLETION_HASH,
    "compiler_command": command,
    "harness_status": result.returncode,
    "limit": "Real Linux completion functions; deterministic single-thread scheduler/time and lock shims at HZ1000. No firmware, callback-lifetime, concurrency, KMS, wall-clock or hardware proof.",
  }
  (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
  print(json.dumps(receipt))


if __name__ == "__main__":
  main()
