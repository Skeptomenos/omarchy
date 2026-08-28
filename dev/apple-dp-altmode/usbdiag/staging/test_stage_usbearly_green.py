"""C3 E-only GREEN companion: all 42 test bodies and expectations unchanged.

Run only in the reviewed offline sandbox. Four individual read-only files are
bound at /inputs/test, /inputs/helper, /inputs/baseline and /inputs/proof-spec.
After retained genuine RED and independent helper review, this copy changes
only the exact subject-helper SHA pin and this explanation. No production
constant is substituted and no privileged preflight is called. Real synthetic
file operations stay under /work; they do not certify hardware or root staging.
Stdlib/unittest remains the approved no-install exception. The sealed C2 tree
is never mounted. GREEN requires the actual reviewed full-suite run.
"""

import hashlib
import json
import os
from pathlib import Path
import re
import resource
import signal
import stat
import subprocess
import tempfile
import unittest


HELPER = Path("/inputs/helper")
BASELINE = Path("/inputs/baseline")
PROOF_SPEC = Path("/inputs/proof-spec")
HELPER_SHA256 = "dbfbeac043d77ed1543274322f4f961a7622a2adbf49503bb2f54ee465d4d6fe"
BASELINE_SHA256 = "485a68e30c3b94f430e375286756204f7332446c7878393e40ad22bb8a9ebaff"
PROOF_SPEC_SHA256 = "1ef19e97ff21836091b569a9168a1802f6173f549999a56d12fd20321d3b37aa"
MAX_SOURCE_BYTES = 131072
PUBLIC_C2_ROOT = "/LOCAL_ONLY_DEV147_C2"
E_RELATIVE_SOURCE = "sandbox-tools/run-affn1zit/work/initramfs-linux-asahi-dpalt-usbearly1.img"
E_SHA256 = "4d4f0557af57eebcc33322f004bcc7968254e644b069a11102375df0b31a52ae"
E_SIZE = 19191513
E_DESTINATION = "/boot/initramfs-linux-asahi-dpalt-usbearly1.img"
E_TEMPORARY_BASENAME = ".initramfs-linux-asahi-dpalt-usbearly1.img.tmp"
E_STAGING_TEMPLATE = "/boot/.dev147-usbearly-stage.XXXXXXXXXX"
RETAINED_D3_PIN = (
  "a11bf3a2bac1f105aa57b08ce9fad338c68882851247f7524d09f4b7c94188ca",
  "/boot/initramfs-linux-asahi-dpalt-usbdiag1.img",
)
EXPECTED_C2_PROOFS: tuple[tuple[str, str], ...] = (
  ("b3aa81bfcd2946869d537526ab557fe1b0d9ab630167884ab639d7bab5345f5c", "HANDOFF.md"),
  ("0a810bea90ff983019cb6c717baeddc490955961a8a310cf1d13a2d2fd3bba7e", "SHA256SUMS"),
  ("e7eeb46796f1f04a423b661f7ec3fa9e9655c2a291d034d8c7ff48753849b302", "seal-verification.json"),
  ("f2a186513a36ce68441cfe79511b6635f906e497dfd5ab8064bcaee840d4c46d", "e-independent-qa.json"),
  ("1e44b1f4b212c931a86972bff828cb8cd64c005e95634e444e980d18f181f79d", "c2-final-review.json"),
  ("80df8c3f723c84e8c885550e0b32c808cd5488ba3e4cb5921a4f20039e3e9d29",
   "sandbox-tools/run-affn1zit/work/e-assembly-result.json"),
  ("058a0f0288540eb6b2af0c5876bad783457af668db0bd8d8f28a0789da7c93f2",
   "sandbox-tools/run-affn1zit/work/e-image-delta.json"),
  ("995626ca50174bc34f03fdf59825ddb8c485ffcb59d62d20116b394620ac3a1f",
   "sandbox-tools/run-affn1zit/result.json"),
)
ENVIRONMENT = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"}
PACKAGES = "\n".join((
  "linux-asahi 7.1.6.asahi1-1", "m1n1 1.6.1-1", "mesa 26.1.8-1",
  "mkinitcpio 41.1-1", "openssl 3.6.4-1", "coreutils 9.11-2", "kmod 34.2-1",
))
FIXTURE_UUID = "00000000-0000-0000-0000-000000000000"


def pinned_text(path: Path, expected_sha256: str) -> str:
  """Authenticate one fixed input before any helper function is sourced."""
  if path.parent != Path("/inputs") or path.is_symlink():
    raise RuntimeError("fixed input path is not a direct nonsymlink file")
  descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
  with os.fdopen(descriptor, "rb") as stream:
    before = os.fstat(stream.fileno())
    if (not stat.S_ISREG(before.st_mode) or before.st_nlink != 1
        or not 0 < before.st_size <= MAX_SOURCE_BYTES):
      raise RuntimeError("fixed input type, link count, or size is invalid")
    payload = stream.read(MAX_SOURCE_BYTES + 1)
    after = os.fstat(stream.fileno())
  if (len(payload) != before.st_size
      or hashlib.sha256(payload).hexdigest() != expected_sha256
      or (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
      != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
      or path.stat().st_ino != before.st_ino):
    raise RuntimeError("fixed input identity or bytes changed")
  return payload.decode("utf-8")


def pin_records(output: str) -> tuple[tuple[str, str], ...]:
  """Parse the real producer's bounded output without checking host files."""
  lines = output.splitlines()
  if (len(output) > 32768 or not 1 <= len(lines) <= 64
      or not output.endswith("\n") or "\r" in output):
    raise RuntimeError("record collector produced an invalid bound")
  result: list[tuple[str, str]] = []
  for line in lines:
    match = re.fullmatch(r"([0-9a-f]{64})  (/[^\r\n]+)", line)
    if match is None:
      raise RuntimeError("record collector produced malformed data")
    result.append((match.group(1), match.group(2)))
  return tuple(result)


class StageHelperTest(unittest.TestCase):
  helper_text: str = ""

  @classmethod
  def setUpClass(cls) -> None:
    if os.getuid() != 1001 or os.geteuid() != 1001 or Path.cwd() != Path("/work"):
      raise RuntimeError("fixtures require the reviewed unprivileged /work sandbox")
    if any(Path(path).exists() for path in ("/boot", "/home", "/proc", "/sys", "/run")):
      raise RuntimeError("host trees must be absent")
    if not HELPER.is_file() or HELPER.is_symlink():
      raise RuntimeError("missing read-only helper input")
    cls.helper_text = pinned_text(HELPER, HELPER_SHA256)
    pinned_text(BASELINE, BASELINE_SHA256)
    pinned_text(PROOF_SPEC, PROOF_SPEC_SHA256)
    with Path("/work/c3-staging-setup.json").open("x") as stream:
      json.dump({"status": "SETUP PASS", "helper_sha256": HELPER_SHA256,
                 "baseline_sha256": BASELINE_SHA256,
                 "proof_spec_sha256": PROOF_SPEC_SHA256,
                 "expectations": "fixed from reviewed sealed C2, not the helper",
                 "production_preflight": False}, stream)
      stream.write("\n")

  def setUp(self) -> None:
    self.root = Path(tempfile.mkdtemp(prefix="stage-case-", dir="/work"))
    self.source = self.root / "source"
    self.payload = b"synthetic diagnostic fixture\n" * 16
    self.source.write_bytes(self.payload)
    self.source.chmod(0o600)
    self.digest = hashlib.sha256(self.payload).hexdigest()
    self.boot = self.root / "fixture-boot"
    self.boot.mkdir(mode=0o700)
    self.temporary = self.boot / "temporary"
    self.destination = self.boot / "new-image"
    self.sequence = 0

  def child(self, arguments: list[str], *, script: str | None = None,
            extra_env: dict[str, str] | None = None,
            file_limit: int | None = None) -> subprocess.CompletedProcess[bytes]:
    self.sequence += 1
    prefix = self.root / f"child-{self.sequence:03d}"
    code = script or 'set -Eeuo pipefail; umask 077; source "$1"; shift; "$@"'
    command = ["/usr/bin/bash", "-c", code, "stage-fixture", str(HELPER), *arguments]
    environment = dict(ENVIRONMENT)
    environment.update(extra_env or {})

    def limits() -> None:
      resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
      if file_limit is not None:
        resource.setrlimit(resource.RLIMIT_FSIZE, (file_limit, file_limit))

    with prefix.with_suffix(".stdout").open("xb") as output, \
         prefix.with_suffix(".stderr").open("xb") as errors:
      try:
        result = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=output,
                                stderr=errors, env=environment, timeout=20,
                                close_fds=True, check=False, preexec_fn=limits)
      except subprocess.TimeoutExpired:
        prefix.with_suffix(".timeout.json").write_text(
          json.dumps({"command": command, "timed_out": True}) + "\n")
        raise
    stdout = prefix.with_suffix(".stdout").read_bytes()
    stderr = prefix.with_suffix(".stderr").read_bytes()
    with prefix.with_suffix(".result.json").open("x") as stream:
      json.dump({"command": command, "exit_code": result.returncode,
                 "timed_out": False}, stream)
      stream.write("\n")
    return subprocess.CompletedProcess(command, result.returncode, stdout, stderr)

  def success(self, function: str, *args: object) -> subprocess.CompletedProcess[bytes]:
    result = self.child([function, *(str(value) for value in args)])
    self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
    return result

  def refusal(self, function: str, *args: object) -> subprocess.CompletedProcess[bytes]:
    result = self.child([function, *(str(value) for value in args)])
    self.assertEqual(result.returncode, 1, result.stderr.decode(errors="replace"))
    self.assertIn(b"REFUSED:", result.stderr)
    self.assertNotIn(b"STAGING ONLY PASS", result.stdout)
    return result

  def make_temporary(self) -> None:
    self.temporary.write_bytes(self.payload)
    self.temporary.chmod(0o600)

  def make_logs(self) -> Path:
    directory = self.boot / "retained-checks"
    directory.mkdir(mode=0o700)
    for name in ("before.sha256", "before-publication.sha256", "after.sha256"):
      path = directory / name
      path.write_text(f"{self.digest}  {self.source}\n")
      path.chmod(0o600)
    return directory

  def test_clean_environment_and_override_rejection(self) -> None:
    self.success("d2stage_check_environment")
    for variable in ("BASH_ENV", "ENV", "LD_PRELOAD", "LD_LIBRARY_PATH",
                     "MKINITCPIO_CONF", "OMARCHY_DPALT_TEST_ROOT", "DPALT_TEST_ROOT",
                     "DPST_TEST_ROOT", "D2ST_TEST_ROOT"):
      with self.subTest(variable=variable):
        # Export inside the already-running fixture, not at Bash startup.
        result = self.child([variable], script='source "$1"; export "$2=unexpected"; d2stage_check_environment')
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn(b"REFUSED:", result.stderr)

  def test_public_configuration_refuses_without_overrides(self) -> None:
    self.refusal("d2stage_require_operational")
    self.refusal("d2stage_main")
    result = self.child(["d2stage_main"], extra_env={"D2ST_SOURCE": str(self.source),
                                                    "D2ST_ROOT_UUID": FIXTURE_UUID})
    self.assertEqual(result.returncode, 1, result.stderr)
    self.assertIn(b"REFUSED:", result.stderr)
    self.assertEqual(self.source.read_bytes(), self.payload)

  def test_main_refuses_arguments_before_any_write(self) -> None:
    self.refusal("d2stage_main", "--output", self.destination)
    self.assertFalse(self.destination.exists())

  def test_canonical_directory_and_owner(self) -> None:
    self.success("d2stage_canonical_path", self.source)
    self.success("d2stage_secure_directory", self.boot, os.geteuid())
    self.refusal("d2stage_secure_directory", self.boot, 0)
    self.boot.chmod(0o777)
    self.refusal("d2stage_secure_directory", self.boot, os.geteuid())

  def test_unsafe_paths_and_symlink_ancestors(self) -> None:
    link = self.root / "linked"
    link.symlink_to(self.boot, target_is_directory=True)
    for path in ("relative", f"{self.boot}/../source", f"{self.boot}/./file",
                 f"{self.boot}/line\nbreak", f"{self.boot}/back\\slash",
                 f"{link}/new"):
      with self.subTest(path=path):
        self.refusal("d2stage_destination_parent", path)

  def test_identity_is_stable_under_reads(self) -> None:
    first = self.success("d2stage_file_identity", self.source).stdout.decode().strip()
    self.source.read_bytes()
    self.success("d2stage_same_identity", self.source, first)

  def test_same_content_inode_replacement_is_rejected(self) -> None:
    first = self.success("d2stage_file_identity", self.source).stdout.decode().strip()
    replacement = self.root / "replacement"
    replacement.write_bytes(self.payload)
    replacement.chmod(0o600)
    replacement.replace(self.source)
    self.refusal("d2stage_same_identity", self.source, first)
    self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(), self.digest)

  def test_regular_single_link_source_required(self) -> None:
    hardlink = self.root / "hardlink"
    os.link(self.source, hardlink)
    self.refusal("d2stage_verified_file", self.source, len(self.payload), self.digest)
    self.assertEqual(hardlink.read_bytes(), self.payload)

  def test_fifo_directory_symlink_and_missing_source_refused(self) -> None:
    fifo = self.root / "fifo"
    os.mkfifo(fifo, 0o600)
    symlink = self.root / "symlink"
    symlink.symlink_to(self.source)
    for path in (fifo, self.boot, symlink, self.root / "missing"):
      with self.subTest(path=path):
        self.refusal("d2stage_verified_file", path, len(self.payload), self.digest)

  def test_size_hash_and_malformed_digest_refused(self) -> None:
    self.success("d2stage_verified_file", self.source, len(self.payload), self.digest)
    for size, digest in ((0, self.digest), (-1, self.digest), (len(self.payload) + 1, self.digest),
                         (len(self.payload) - 1, self.digest), (len(self.payload), "0" * 64),
                         (len(self.payload), "invalid")):
      with self.subTest(size=size, digest=digest):
        self.refusal("d2stage_verified_file", self.source, size, digest)

  def test_protected_hash_allows_existing_package_hardlinks(self) -> None:
    os.link(self.source, self.root / "package-link")
    self.success("d2stage_hash_file", self.source, self.digest)
    self.source.write_bytes(b"changed")
    self.refusal("d2stage_hash_file", self.source, self.digest)

  def test_pins_missing_drift_and_invalid_records(self) -> None:
    self.success("d2stage_check_pins", f"{self.digest}  {self.source}")
    for record in ("", "invalid", f"{self.digest}  {self.root}/missing",
                   f"{'0' * 64}  {self.source}", f"{self.digest}  relative"):
      with self.subTest(record=record):
        self.refusal("d2stage_check_pins", record)

  def test_exact_kernel_and_package_records(self) -> None:
    self.success("d2stage_check_versions", "7.1.6-1-1-ARCH", PACKAGES)
    self.refusal("d2stage_check_versions", "other-kernel", PACKAGES)
    self.refusal("d2stage_check_versions", "7.1.6-1-1-ARCH", PACKAGES.replace("3.6.4-1", "3.6.5-1"))
    self.refusal("d2stage_check_versions", "7.1.6-1-1-ARCH", PACKAGES + "\nunexpected 1-1")

  def test_mount_validation_uses_only_synthetic_records(self) -> None:
    self.success("d2stage_check_mount", f"ext4 {FIXTURE_UUID} /", FIXTURE_UUID)
    for record in (f"tmpfs {FIXTURE_UUID} /", f"ext4 {FIXTURE_UUID} /boot",
                   f"ext4 {FIXTURE_UUID} / extra", f"ext4 {FIXTURE_UUID} /\nextra",
                   "ext4 wrong /"):
      with self.subTest(record=record):
        self.refusal("d2stage_check_mount", record, FIXTURE_UUID)
    self.refusal("d2stage_check_mount", "ext4 LOCAL_ONLY_ROOT_UUID /", "LOCAL_ONLY_ROOT_UUID")

  def test_battery_threshold_and_strict_numbers(self) -> None:
    for value in (51, 100):
      self.success("d2stage_check_battery", value)
    for value in (0, 50, 101, -1, "51\n100", "51%", "999999999999999999"):
      with self.subTest(value=value):
        self.refusal("d2stage_check_battery", value)

  def test_package_lock_presence_and_dangling_link(self) -> None:
    lock = self.root / "db.lck"
    self.success("d2stage_check_absent", lock, "package transaction")
    lock.write_bytes(b"lock")
    self.refusal("d2stage_check_absent", lock, "package transaction")
    dangling = self.root / "dangling-lock"
    dangling.symlink_to(self.root / "absent-target")
    self.refusal("d2stage_check_absent", dangling, "package transaction")

  def test_space_exact_threshold_and_one_byte_short(self) -> None:
    self.success("d2stage_check_space_record", "110 1", 100, 10)
    self.refusal("d2stage_check_space_record", "109 1", 100, 10)
    self.success("d2stage_check_space_record", "1 4096", 100, 10)
    self.refusal("d2stage_check_space_record", "0 4096", 100, 10)
    self.success("d2stage_check_space", self.boot, 100, 10)

  def test_space_overflow_and_malformed_fields(self) -> None:
    self.success("d2stage_check_space_record", "999999999999999999 4096", 100, 10)
    for record in ("-1 4096", "1 0", "1 -1", "1 4096 extra", "1 4096\n2 4096",
                   "999999999999999999999999 4096", "1 $(touch unsafe)", "0x20 4096"):
      with self.subTest(record=record):
        self.refusal("d2stage_check_space_record", record, 100, 10)
    self.refusal("d2stage_check_space_record", "100 4096", "999999999999999999999", 10)

  def test_same_filesystem_uses_real_stat(self) -> None:
    self.success("d2stage_same_filesystem", self.source, self.boot)
    self.assertNotEqual(self.source.stat().st_dev, Path("/dev/null").stat().st_dev)
    self.refusal("d2stage_same_filesystem", self.source, "/dev/null")

  def test_real_copy_and_atomic_publication(self) -> None:
    before = self.source.stat()
    self.success("d2stage_copy_verified", self.source, self.temporary, self.digest, len(self.payload))
    self.assertEqual(self.temporary.read_bytes(), self.payload)
    self.success("d2stage_publish_verified", self.temporary, self.destination, self.digest, len(self.payload))
    self.assertFalse(self.temporary.exists())
    self.assertEqual(self.destination.read_bytes(), self.payload)
    self.assertEqual(stat.S_IMODE(self.destination.stat().st_mode), 0o600)
    self.assertEqual(self.destination.stat().st_nlink, 1)
    self.assertEqual(self.source.stat().st_ino, before.st_ino)
    self.assertEqual(self.source.read_bytes(), self.payload)

  def test_late_destination_file_is_not_overwritten(self) -> None:
    self.make_temporary()
    self.success("d2stage_absent_destination", self.destination)
    self.destination.write_bytes(b"retain existing")
    self.refusal("d2stage_publish_verified", self.temporary, self.destination, self.digest, len(self.payload))
    self.assertEqual(self.destination.read_bytes(), b"retain existing")
    self.assertEqual(self.temporary.read_bytes(), self.payload)

  def test_destination_symlink_dangling_link_directory_and_hardlink(self) -> None:
    self.make_temporary()
    paths = [self.boot / name for name in ("symlink", "dangling", "directory", "hardlink")]
    paths[0].symlink_to(self.source)
    paths[1].symlink_to(self.root / "absent")
    paths[2].mkdir(mode=0o700)
    os.link(self.source, paths[3])
    for path in paths:
      with self.subTest(path=path):
        self.refusal("d2stage_absent_destination", path)
        self.refusal("d2stage_publish_verified", self.temporary, path, self.digest, len(self.payload))
    self.assertEqual(self.source.read_bytes(), self.payload)
    self.assertTrue(paths[0].is_symlink() and paths[1].is_symlink())

  def test_copy_refuses_existing_temporary(self) -> None:
    self.temporary.write_bytes(b"retained previous attempt")
    self.refusal("d2stage_copy_verified", self.source, self.temporary, self.digest, len(self.payload))
    self.assertEqual(self.temporary.read_bytes(), b"retained previous attempt")

  def test_hardlinked_temporary_cannot_be_published(self) -> None:
    self.make_temporary()
    os.link(self.temporary, self.root / "temporary-link")
    self.refusal("d2stage_publish_verified", self.temporary, self.destination, self.digest, len(self.payload))
    self.assertFalse(self.destination.exists())

  def test_publication_refuses_nonprivate_mode(self) -> None:
    self.make_temporary()
    self.temporary.chmod(0o644)
    self.refusal("d2stage_publish_verified", self.temporary, self.destination, self.digest, len(self.payload))
    self.assertFalse(self.destination.exists())

  def test_source_drift_stops_before_copy(self) -> None:
    self.source.write_bytes(self.payload + b"growth")
    self.refusal("d2stage_copy_verified", self.source, self.temporary, self.digest, len(self.payload))
    self.assertFalse(self.temporary.exists())
    self.source.write_bytes(self.payload[:-1])
    self.refusal("d2stage_copy_verified", self.source, self.temporary, self.digest, len(self.payload))

  def test_real_file_size_limit_retains_partial_copy(self) -> None:
    payload = b"x" * 32768
    self.source.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    result = self.child(["d2stage_copy_verified", str(self.source), str(self.temporary),
                         digest, str(len(payload))], file_limit=1024)
    self.assertEqual(result.returncode, 1, result.stderr)
    self.assertIn(b"REFUSED:", result.stderr)
    self.assertTrue(self.temporary.exists())
    self.assertLessEqual(self.temporary.stat().st_size, 1024)
    self.assertEqual(self.source.read_bytes(), payload)
    self.assertFalse(self.destination.exists())

  def test_error_propagates_when_errexit_is_disabled_by_if(self) -> None:
    self.make_temporary()
    self.destination.write_bytes(b"already there")
    result = self.child(["d2stage_publish_verified", str(self.temporary), str(self.destination),
                         self.digest, str(len(self.payload))],
                        script='source "$1"; shift; if "$@"; then exit 0; else exit $?; fi')
    self.assertEqual(result.returncode, 1, result.stderr)
    self.assertEqual(self.destination.read_bytes(), b"already there")
    self.assertEqual(self.temporary.read_bytes(), self.payload)

  def test_real_sync_and_missing_path_failure(self) -> None:
    self.success("d2stage_sync", self.source)
    self.refusal("d2stage_sync", self.root / "missing-sync-path")

  def test_start_is_private_durable_and_exclusive(self) -> None:
    directory = self.make_logs()
    self.success("d2stage_start", directory)
    marker = directory / "INCOMPLETE"
    self.assertTrue(marker.is_file())
    self.assertEqual(stat.S_IMODE(marker.stat().st_mode), 0o600)
    before = marker.read_bytes()
    self.refusal("d2stage_start", directory)
    self.assertEqual(marker.read_bytes(), before)

  def test_completion_requires_intact_output_and_identical_logs(self) -> None:
    directory = self.make_logs()
    self.success("d2stage_start", directory)
    self.destination.write_bytes(self.payload)
    self.destination.chmod(0o600)
    (directory / "after.sha256").write_text("changed protected record\n")
    self.refusal("d2stage_finish", directory, self.destination, self.digest, len(self.payload))
    self.assertTrue((directory / "INCOMPLETE").exists())
    self.assertFalse((directory / "staging-start-marker.txt").exists())

  def test_missing_final_image_keeps_incomplete(self) -> None:
    directory = self.make_logs()
    self.success("d2stage_start", directory)
    self.refusal("d2stage_finish", directory, self.destination, self.digest, len(self.payload))
    self.assertTrue((directory / "INCOMPLETE").exists())

  def test_hardlinked_final_image_keeps_incomplete(self) -> None:
    directory = self.make_logs()
    self.success("d2stage_start", directory)
    self.destination.write_bytes(self.payload)
    self.destination.chmod(0o600)
    os.link(self.destination, self.root / "final-link")
    self.refusal("d2stage_finish", directory, self.destination, self.digest, len(self.payload))
    self.assertTrue((directory / "INCOMPLETE").exists())

  def test_existing_result_is_not_overwritten(self) -> None:
    directory = self.make_logs()
    self.success("d2stage_start", directory)
    self.destination.write_bytes(self.payload)
    self.destination.chmod(0o600)
    (directory / "RESULT.txt").write_bytes(b"retained old result")
    self.refusal("d2stage_finish", directory, self.destination, self.digest, len(self.payload))
    self.assertEqual((directory / "RESULT.txt").read_bytes(), b"retained old result")
    self.assertTrue((directory / "INCOMPLETE").exists())

  def test_success_finalizes_only_after_checks(self) -> None:
    directory = self.make_logs()
    self.success("d2stage_start", directory)
    self.destination.write_bytes(self.payload)
    self.destination.chmod(0o600)
    result = self.success("d2stage_finish", directory, self.destination, self.digest, len(self.payload))
    self.assertFalse((directory / "INCOMPLETE").exists())
    self.assertTrue((directory / "staging-start-marker.txt").is_file())
    self.assertIn("PROVISIONAL", (directory / "RESULT.txt").read_text())
    self.assertIn(b"STAGING ONLY PASS", result.stdout)
    self.refusal("d2stage_finish", directory, self.destination, self.digest, len(self.payload))

  def test_interruption_keeps_started_record(self) -> None:
    directory = self.make_logs()
    result = self.child([str(directory)], script='source "$1"; d2stage_start "$2" || exit $?; kill -TERM "$$"')
    self.assertEqual(result.returncode, -signal.SIGTERM, result.stderr)
    self.assertTrue((directory / "INCOMPLETE").is_file())
    self.assertFalse((directory / "RESULT.txt").exists())

  def test_bound_exit_trap_preserves_failure_after_scope_unwinds(self) -> None:
    for index, (body, status) in enumerate((("(exit 7)", 7), ("return 7", 7),
                                           ('d2stage_die "synthetic failure"', 1))):
      with self.subTest(body=body):
        directory = self.boot / f"retained 'checks' {index}"
        directory.mkdir(mode=0o700)
        self.success("d2stage_start", directory)
        script = 'set -Eeuo pipefail; source "$1"; test_main() { local private_directory="$1"; '
        script += 'd2stage_install_exit_trap "$private_directory"; ' + body + '; }; test_main "$2"'
        result = self.child([str(directory)], script=script)
        self.assertEqual(result.returncode, status, result.stderr)
        self.assertIn(b"STAGING FAILED", result.stderr)
        self.assertIn(str(directory).encode(), result.stderr)
        self.assertNotIn(b"unbound variable", result.stderr)
        self.assertTrue((directory / "INCOMPLETE").is_file())
        self.assertFalse((directory / "RESULT.txt").exists())

  def test_bound_exit_trap_success_does_not_create_failure_marker(self) -> None:
    directory = self.boot / "successful 'checks'"
    directory.mkdir(mode=0o700)
    script = 'set -Eeuo pipefail; source "$1"; test_main() { local private_directory="$1"; '
    script += 'd2stage_install_exit_trap "$private_directory"; return 0; }; test_main "$2"'
    result = self.child([str(directory)], script=script)
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual(result.stderr, b"")
    self.assertFalse((directory / "INCOMPLETE").exists())

  def contract_output(self, script: str, *arguments: str) -> str:
    result = self.child(list(arguments), script=script)
    if result.returncode != 0 or result.stderr or len(result.stdout) > 32768:
      raise RuntimeError("contract collector failed; this is not semantic RED")
    return result.stdout.decode("utf-8")

  def test_e_image_identity_and_staging_names(self) -> None:
    output = self.contract_output(
      'source "$1"; printf "%s\\n" "$D2ST_IMAGE_SHA" "$D2ST_IMAGE_SIZE" '
      '"$D2ST_DESTINATION" "$D2ST_SOURCE" "$D2ST_PROOFS"')
    actual = tuple(output.splitlines())
    expected = (E_SHA256, str(E_SIZE), E_DESTINATION,
                f"{PUBLIC_C2_ROOT}/{E_RELATIVE_SOURCE}", PUBLIC_C2_ROOT)
    self.assertEqual(actual, expected, "old image constants do not select the fixed E image")
    self.assertIn(f'private_directory=$(d2stage_clean /usr/bin/mktemp -d {E_STAGING_TEMPLATE})',
                  self.helper_text)
    self.assertIn(f'temporary="$private_directory/{E_TEMPORARY_BASENAME}"', self.helper_text)
    self.assertEqual(self.helper_text.count(E_STAGING_TEMPLATE), 1)
    self.assertEqual(self.helper_text.count(E_TEMPORARY_BASENAME), 1)

  def test_protected_records_preserve_old32_and_add_retained_d3(self) -> None:
    baseline_output = self.contract_output('source "$2"; d2stage_protected_inputs', str(BASELINE))
    actual_output = self.contract_output('source "$1"; d2stage_protected_inputs')
    baseline = pin_records(baseline_output)
    actual = pin_records(actual_output)
    self.assertEqual(len(baseline), 32)
    self.assertEqual(len(actual), 33)
    self.assertEqual(actual.count(RETAINED_D3_PIN), 1)
    self.assertEqual(tuple(row for row in actual if row != RETAINED_D3_PIN), baseline)
    added_line = f"{RETAINED_D3_PIN[0]}  {RETAINED_D3_PIN[1]}\n"
    self.assertEqual(actual_output.replace(added_line, ""), baseline_output)
    self.assertEqual(len({path for _, path in actual}), 33)

  def test_exact_sealed_c2_proof_records(self) -> None:
    actual = pin_records(self.contract_output('source "$1"; d2stage_proof_inputs'))
    expected = tuple((digest, f"{PUBLIC_C2_ROOT}/{relative}")
                     for digest, relative in EXPECTED_C2_PROOFS)
    self.assertEqual(actual, expected, "old proof constants do not bind the sealed C2 result")
    self.assertEqual(len(actual), 8)
    protected = pin_records(self.contract_output('source "$1"; d2stage_protected_inputs'))
    combined = protected + actual
    self.assertEqual(len(combined), 41)
    self.assertEqual(len({path for _, path in combined}), 41)

  def test_finish_names_uninstrumented_image_without_boot_permission(self) -> None:
    directory = self.make_logs()
    self.success("d2stage_start", directory)
    self.destination.write_bytes(self.payload)
    self.destination.chmod(0o600)
    result = self.success("d2stage_finish", directory, self.destination, self.digest, len(self.payload))
    self.assertIn(b"No reboot permission. Normal boot is unchanged", result.stdout)
    self.assertIn(b"this uninstrumented early-availability image is untested at startup", result.stdout)
    self.assertNotIn(b"diagnostic image", result.stdout)
    self.assertFalse((directory / "INCOMPLETE").exists())
    self.assertTrue((directory / "staging-start-marker.txt").is_file())


if __name__ == "__main__":
  unittest.main(verbosity=2)
