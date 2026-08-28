#!/usr/bin/python3
"""Run the real isolation probe without invoking any kernel build."""

from pathlib import Path
import subprocess
import sys


def main() -> None:
  launcher = Path(__file__).with_name("sandbox.py")
  result = subprocess.run(
    [sys.executable, "-I", "-S", "-B", str(launcher), "--probe"],
    stdin=subprocess.DEVNULL, close_fds=True, check=False, timeout=290,
  )
  if result.returncode != 0:
    raise SystemExit(f"FAIL: isolation launcher returned {result.returncode}")
  print("VERDICT: PASS")


if __name__ == "__main__":
  main()
