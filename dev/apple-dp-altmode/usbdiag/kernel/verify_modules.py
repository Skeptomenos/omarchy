"""Check already-built diagnostic module identities and exact import deltas.

This is an offline workload for the reviewed private sandbox. It never loads a
module or changes an image. All child output is retained before interpretation.
"""

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess


EXPECTED = {
  "dwc3-apple": (
    "d333ce2d82789d5da8acdc563fd04ea9cde3872472cde423ed1a51710cf38ef4",
    "4e3a8536657283ecc0ac9d5c49e19990a32150db",
    "d213e676593c1c4f9daceba1002f2381b6d390ce3eff9995043991a4d1e20975",
  ),
  "phy-apple-atc": (
    "504fc2b82e62e7497532dfe4b955228d7298a3f2c9b34d1e9623ed9188912547",
    "5e40dcc39aef0914b9fcba1a779b237f99a39f48",
    "edb76a5fd6458406f6371f842a7a6a2b5f8b22b404ba622a5d081302662cc568",
  ),
}
ADDITIONS = {"_printk", "alt_cb_patch_nops", "of_machine_compatible_match", "strcmp"}
RUN = 0


def require(condition: bool, detail: str) -> None:
  if not condition:
    raise RuntimeError(detail)


def run(args: list[str]) -> str:
  global RUN
  prefix = Path(f"/work/module-child-{RUN:02d}")
  RUN += 1
  try:
    result = subprocess.run(args, check=False, capture_output=True, timeout=20)
  except subprocess.TimeoutExpired as error:
    with prefix.with_suffix(".timeout.json").open("x") as stream:
      json.dump({"command": args, "timed_out": True}, stream)
    for suffix, payload in ((".stdout", error.stdout), (".stderr", error.stderr)):
      with prefix.with_suffix(suffix).open("xb") as stream:
        stream.write(payload or b"")
    raise
  for suffix, payload in ((".stdout", result.stdout), (".stderr", result.stderr)):
    with prefix.with_suffix(suffix).open("xb") as stream:
      stream.write(payload)
  with prefix.with_suffix(".result.json").open("x") as stream:
    json.dump({"command": args, "exit_code": result.returncode, "timed_out": False}, stream)
  require(result.returncode == 0 and result.stderr == b"", "metadata command failed")
  return result.stdout.decode("utf-8")


def main() -> None:
  require(os.getuid() == 1001 and os.getgid() == 1001, "unexpected workload identity")
  require(Path.cwd() == Path("/work"), "not in private work directory")
  require(not any(Path(path).exists() for path in ("/proc", "/sys", "/run", "/boot", "/home")),
          "host trees visible")
  symvers = Path("/inputs/symvers").read_bytes()
  require(hashlib.sha256(symvers).hexdigest() ==
          "d5eea549b9333f717fdc932683ea6633d58049c1e3f8f9e0be12e05d7610dd82", "symvers drift")
  exports = {fields[1]: fields[2:] for line in symvers.decode("ascii").splitlines()
             if len(fields := line.split()) >= 4}
  for symbol in ADDITIONS:
    require(exports[symbol] == ["vmlinux", "EXPORT_SYMBOL"], "unreviewed export owner/type")
  for module, (digest, build_id, control_digest) in EXPECTED.items():
    diagnostic = f"/inputs/diagnostic/{module}.ko"
    control = f"/inputs/control/{module}.ko"
    require(hashlib.sha256(Path(diagnostic).read_bytes()).hexdigest() == digest, "diagnostic drift")
    require(hashlib.sha256(Path(control).read_bytes()).hexdigest() == control_digest, "control drift")
    for field in ("name", "vermagic", "depends", "alias"):
      require(run(["/usr/bin/modinfo", "-F", field, diagnostic]) ==
              run(["/usr/bin/modinfo", "-F", field, control]), "module metadata differs")
    actual = {line.split()[-1] for line in run(["/usr/bin/nm", "-u", diagnostic]).splitlines()}
    baseline = {line.split()[-1] for line in run(["/usr/bin/nm", "-u", control]).splitlines()}
    require(actual - baseline == ADDITIONS and not baseline - actual, "unexpected import delta")
    notes = run(["/usr/bin/readelf", "-n", diagnostic])
    require(re.findall(r"Build ID: ([0-9a-f]+)", notes) == [build_id], "build identity mismatch")
    sections = run(["/usr/bin/readelf", "-SW", diagnostic])
    require(re.search(r"\s\.BTF\s+PROGBITS\s", sections) is not None, "BTF absent")
    print(json.dumps({"check": "diagnostic_module", "level": "info", "verdict": "PASS",
                      "module": module, "build_id": build_id, "sha256": digest,
                      "added_imports": sorted(ADDITIONS), "removed_imports": [],
                      "new_module_dependency": False, "module_loaded": False}, sort_keys=True))


if __name__ == "__main__":
  main()
