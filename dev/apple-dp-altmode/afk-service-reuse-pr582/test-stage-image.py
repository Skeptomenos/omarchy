from __future__ import annotations

import base64
import hashlib
import importlib.util
import os
import re
import stat
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parent
PUBLISHER = ROOT / "stage-image.py"
BOOTSTRAP = ROOT / "stage-image-bootstrap.txt"
EXPECTED_SOURCE = Path(
  "/home/david/o/.dev147-stage/afk-pr582-combined-offline-20260904.hdfiJZaOUn/"
  "image-build/initramfs-linux-asahi-m2-displayport-afk-pr582.img"
)
EXPECTED_SOURCE_SHA256 = "3207dd0ff346765f4514b34a137c1c7456c459082463355e51047216dedc2867"
EXPECTED_SOURCE_SIZE = 21_599_177
EXPECTED_ACCEPTED_IMAGE_SHA256 = "a93dd0c1b3a6c4d81bf76f2f43c7c7a2b8b7e1e0306bc487de018667f9c8c196"
EXPECTED_DEFAULT_IMAGE_SHA256 = "c4cffb397cfbd0158d3b1423c0512e1622053d53e0c75a17f5312986276324e0"
EXPECTED_GRUB_SHA256 = "57d839b9bc7d3488402a8cf7c9e45328dc0097731fc395b0514c467d06b7a327"
EXPECTED_AFK_IMAGE_SHA256 = "ebd383c21a35d6b0eff22ffe6f144ea7790c31d7cf058a1c3afa5e39c2375acd"
EXPECTED_ROLLBACK_SHA256 = "3357ac75cd7a7d330d2c751bf819e342758491d71e3b34234afacf2f83264e19"
EXPECTED_RECOVERY_SHA256 = "5fda712442fd860bb8c31d8441e350c66e1ecfb1c4054206f638119106dead78"
REJECTED_PRE_AVD_DEFAULT_IMAGE_SHA256 = "625641095075a9a2396bc701ffd48ac58f2c8a1758e250fa3f6b55b29dcae296"
REJECTED_PRE_CLEANUP_GRUB_SHA256 = "68c36bbbb3c530dba8647f9435252da53adf53942b37b76e399ccd234cc0f24d"
EXPECTED_BOOTSTRAP_PREFIX = (
  "/usr/bin/sudo /usr/bin/env -i PATH=/usr/bin:/bin LANG=C.UTF-8 "
  "/usr/bin/bash -s <<'DEV147_AFK_PR582_ROOT_BOOTSTRAP'"
)
REJECTED_HASH_THEN_SOURCE = """afkreuse_load_library() {
  local path="$1"
  hash=$(afkreuse_clean /usr/bin/sha256sum -- "$path")
  [[ ${hash%% *} == "$AFKREUSE_LIBRARY_SHA256" ]]
  source "$path"
}
readonly AFKREUSE_LIBRARY="/home/david/owned/stage-library.sh"
"""


def digest(data: bytes) -> str:
  return hashlib.sha256(data).hexdigest()


def load_publisher():
  spec = importlib.util.spec_from_file_location("dev147_stage_image", PUBLISHER)
  if spec is None or spec.loader is None:
    raise RuntimeError("cannot load publisher specification")
  module = importlib.util.module_from_spec(spec)
  sys.modules[spec.name] = module
  spec.loader.exec_module(module)
  return module


def bootstrap_payload(text: str) -> tuple[str, bytes]:
  hash_match = re.search(r'^readonly wrapper_sha="([0-9a-f]{64})"$', text, re.MULTILINE)
  payload_match = re.search(
    r"<<'DEV147_AFK_PR582_STAGE_IMAGE_PAYLOAD'\n([A-Za-z0-9+/=\n]+)\nDEV147_AFK_PR582_STAGE_IMAGE_PAYLOAD$",
    text,
    re.MULTILINE,
  )
  if hash_match is None or payload_match is None:
    raise AssertionError("bootstrap payload contract is missing")
  encoded = payload_match.group(1).replace("\n", "")
  return hash_match.group(1), base64.b64decode(encoded, validate=True)


def bootstrap_body(text: str) -> str:
  first_line, body = text.split("\n", 1)
  if "/usr/bin/bash -s <<'DEV147_AFK_PR582_ROOT_BOOTSTRAP'" not in first_line:
    raise AssertionError("bootstrap does not start from root Bash stdin")
  body = body.rstrip("\n")
  suffix = "\nDEV147_AFK_PR582_ROOT_BOOTSTRAP"
  if not body.endswith(suffix):
    raise AssertionError("bootstrap terminator is missing")
  return body[: -len(suffix)] + "\n"


def run_bootstrap(
  boot: Path,
  body: str,
  command_overrides: tuple[tuple[Path, str], ...] = (),
) -> subprocess.CompletedProcess[str]:
  command = [
    "/usr/bin/bwrap",
    "--die-with-parent",
    "--unshare-user",
    "--uid",
    "0",
    "--gid",
    "0",
    "--ro-bind",
    "/",
    "/",
    "--dev-bind",
    "/dev",
    "/dev",
    "--proc",
    "/proc",
    "--bind",
    str(boot),
    "/boot",
  ]
  for source, destination in command_overrides:
    command.extend(("--ro-bind", str(source), destination))
  command.extend(
    (
      "--chdir",
      "/",
      "/usr/bin/env",
      "-i",
      "PATH=/usr/bin:/bin",
      "LANG=C.UTF-8",
      "/usr/bin/bash",
      "-s",
    )
  )
  return subprocess.run(
    command,
    input=body,
    check=False,
    capture_output=True,
    text=True,
    timeout=30,
  )


class Sandbox:
  def __init__(self, module, base: Path):
    self.module = module
    self.base = base
    self.system = base / "system"
    self.source = base / "source" / "candidate.img"
    self.boot = base / "boot"
    self.destination = self.boot / "candidate.img"
    self.transaction = base / "state" / "transaction.test"
    self.pin = base / "proof" / "protected.bin"
    self.protected_boot = (
      self.boot / "initramfs-linux-asahi-m2-displayport.img",
      self.boot / "initramfs-linux-asahi.img",
      self.boot / "boot.bin",
      self.boot / "grub.cfg",
    )
    self.image = b"candidate-image\x00" * 97
    self.package_output = "\n".join(
      (
        "linux-asahi 7.1.6.asahi1-1",
        "m1n1 1.6.1-1",
        "uboot-asahi 2026.04.asahi2-1",
        "mesa 26.1.8-1",
        "mkinitcpio 41.1-1",
        "openssl 3.6.4-1",
        "coreutils 9.11-2",
        "kmod 34.2-1",
        "avd-fw 0.1-1",
      )
    )
    self.mount_output = "ext4 e24cf117-3c89-4392-a3b8-def187becda8 /"
    self._create()

  def _write(self, relative: str, data: bytes) -> Path:
    path = self.system / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path

  def _create(self) -> None:
    self.source.parent.mkdir(parents=True)
    self.boot.mkdir()
    (self.system / "var/lib/pacman").mkdir(parents=True)
    (self.system / "etc/default").mkdir(parents=True)
    self.transaction.mkdir(parents=True, mode=0o700)
    self.transaction.chmod(0o700)
    (self.transaction / "INCOMPLETE").write_text(
      "INCOMPLETE staging. Retain this transaction. Do not reboot.\n",
      encoding="utf-8",
    )
    (self.transaction / "INCOMPLETE").chmod(0o600)
    self.pin.parent.mkdir(parents=True)
    self.source.write_bytes(self.image)
    self.source.chmod(0o600)
    self.pin.write_bytes(b"protected-state")
    self.pin.chmod(0o600)
    for index, protected in enumerate(self.protected_boot):
      protected.write_bytes(f"protected-boot-{index}".encode())
      protected.chmod(0o600)
    state_fields = (
      *self.module.EXPECTED_STATE_FIELDS[:11],
      ("hook_parent_created", "0"),
      *self.module.EXPECTED_STATE_FIELDS[11:],
    )
    active_state = self.system / self.module.ACTIVE_STATE_RELATIVE
    active_state.parent.mkdir(parents=True)
    active_state.write_text(
      "".join(f"{key}={value}\n" for key, value in state_fields),
      encoding="ascii",
    )
    active_state.chmod(0o600)
    self._write(
      "sys/firmware/devicetree/base/compatible",
      b"apple,j413\x00apple,t8112\x00apple,arm-platform\x00",
    )
    self._write("sys/firmware/devicetree/base/soc/dcp@271c00000/status", b"okay\x00")
    self._write("sys/firmware/devicetree/base/aliases/dcpext", b"/soc/dcp@271c00000\x00")
    self._write("sys/firmware/devicetree/base/soc/dcp@271c00000/phandle", b"\x00\x00\x00\x88")
    self._write(
      "sys/firmware/devicetree/base/soc/i2c@235010000/usb-pd@3f/connector/displayport",
      b"\x00\x00\x00\x88",
    )
    (
      self.system
      / "sys/firmware/devicetree/base/soc/i2c@235010000/usb-pd@38/connector"
    ).mkdir(parents=True)
    self._write(
      "sys/devices/platform/soc/23e400000.smc/macsmc-power/power_supply/"
      "macsmc-battery/capacity",
      b"100\n",
    )
    self._write(
      "sys/devices/platform/soc/23e400000.smc/macsmc-power/power_supply/"
      "macsmc-ac/online",
      b"1\n",
    )

  def config(self):
    return self.module.StageConfig(
      source=self.source,
      source_sha256=digest(self.image),
      source_size=len(self.image),
      destination=self.destination,
      transaction=self.transaction,
      system_root=self.system,
      trusted_root=self.base,
      root_owner=os.geteuid(),
      root_group=os.getegid(),
      source_owner=os.geteuid(),
      source_group=os.getegid(),
      protected_pins=tuple(
        (
          path,
          digest(path.read_bytes()),
          path.stat().st_size,
          os.geteuid(),
          os.getegid(),
          stat.S_IMODE(path.stat().st_mode),
        )
        for path in (self.pin, *self.protected_boot)
      ),
      kernel_release="7.1.6-1-1-ARCH",
      package_output=self.package_output,
      mount_output=self.mount_output,
      copy_chunk_size=64,
      reserve_bytes=1024,
    )

  def facts(self):
    return self.module.HostFacts(
      kernel_release="7.1.6-1-1-ARCH",
      package_output=self.package_output,
      mount_output=self.mount_output,
    )

  def facts_provider(self):
    return self.facts

  def protected_snapshot(self) -> tuple[tuple[Path, bytes, int], ...]:
    return tuple(
      (path, path.read_bytes(), stat.S_IMODE(path.stat().st_mode))
      for path in self.protected_boot
    )

  def assert_protected_snapshot(
    self,
    testcase: unittest.TestCase,
    snapshot: tuple[tuple[Path, bytes, int], ...],
  ) -> None:
    for path, data, mode in snapshot:
      testcase.assertEqual(path.read_bytes(), data)
      testcase.assertEqual(stat.S_IMODE(path.stat().st_mode), mode)


class StageImageTest(unittest.TestCase):
  def test_00_rejects_old_mutable_root_code_path(self) -> None:
    text = REJECTED_HASH_THEN_SOURCE
    self.assertIn('readonly AFKREUSE_LIBRARY="/home/david/', text)
    self.assertIn('source "$path"', text)
    self.assertLess(text.index("hash=$(afkreuse_clean /usr/bin/sha256sum"),
      text.index('source "$path"'))

  def test_01_requires_new_authenticated_payload(self) -> None:
    self.assertTrue(PUBLISHER.is_file(), "missing self-contained image publisher")
    self.assertTrue(BOOTSTRAP.is_file(), "missing literal root bootstrap")
    expected_hash, payload = bootstrap_payload(BOOTSTRAP.read_text(encoding="utf-8"))
    self.assertEqual(payload, PUBLISHER.read_bytes())
    self.assertEqual(digest(payload), expected_hash)
    tampered = payload[:-1] + bytes((payload[-1] ^ 1,))
    self.assertNotEqual(digest(tampered), expected_hash)

  def test_01a_production_config_pins_complete_root_baseline(self) -> None:
    module = load_publisher()
    config = module.production_config(Path("/boot/.dev147-afk-pr582-stage.test"))
    self.assertEqual(config.trusted_root, Path("/"))
    self.assertEqual(config.source_owner, 1001)
    self.assertEqual(config.source_group, 1001)
    protected_pins = {pin[0]: pin[1:] for pin in config.protected_pins}
    expected = {
      Path("/boot/efi/m1n1/boot.bin"): (
        "203ab7027536c8d16f373d02c1f6346a5c34cfe095a9dafd0cfe37d2b354090c",
        6_205_569,
        0,
        0,
        0o755,
      ),
      Path("/boot/initramfs-linux-asahi.img"): (
        EXPECTED_DEFAULT_IMAGE_SHA256,
        18_865_707,
        0,
        0,
        0o600,
      ),
      Path("/boot/grub/grub.cfg"): (EXPECTED_GRUB_SHA256, 4_129, 0, 0, 0o600),
      Path("/boot/initramfs-linux-asahi-m2-displayport.img"): (
        EXPECTED_ACCEPTED_IMAGE_SHA256,
        19_184_210,
        0,
        0,
        0o600,
      ),
      Path("/boot/initramfs-linux-asahi-m2-displayport-afk-reuse.img"): (
        EXPECTED_AFK_IMAGE_SHA256,
        21_598_988,
        0,
        0,
        0o600,
      ),
      Path("/etc/pacman.d/hooks/05-omarchy-m2-displayport-guard.hook"): (
        "469820ad7cfd015a22cff979b0aa70d62e82dcc7cc05951dca92f40cd660f2bd",
        303,
        0,
        0,
        0o644,
      ),
      Path("/var/lib/omarchy/m2-displayport/active/rollback.sh"): (
        EXPECTED_ROLLBACK_SHA256,
        42_138,
        0,
        0,
        0o700,
      ),
      Path("/var/lib/omarchy/m2-displayport/active/pre-install-boot.bin"): (
        "203ab7027536c8d16f373d02c1f6346a5c34cfe095a9dafd0cfe37d2b354090c",
        6_205_569,
        0,
        0,
        0o600,
      ),
      Path("/var/lib/omarchy/m2-displayport/active/candidate-boot.bin"): (
        "203ab7027536c8d16f373d02c1f6346a5c34cfe095a9dafd0cfe37d2b354090c",
        6_205_569,
        0,
        0,
        0o600,
      ),
      Path("/var/lib/omarchy/m2-displayport/active/recovery.txt"): (
        EXPECTED_RECOVERY_SHA256,
        949,
        0,
        0,
        0o600,
      ),
      Path("/var/lib/omarchy/m2-displayport/active/bundle.env"): (
        "f967202c3da1f31480b52c51e46ca2679e302f64596f9917edc56d0041449fb7",
        448,
        0,
        0,
        0o600,
      ),
      Path("/var/lib/omarchy/m2-displayport/active/RESULT"): (
        "0ebf65c7984364f0999b4b54018b582a0da08a145e4d88a228ce2438856e7b06",
        7,
        0,
        0,
        0o600,
      ),
      Path(
        "/boot/efi/m1n1/boot.bin.pre-omarchy-m2-displayport-20260902T085339Z"
      ): (
        "203ab7027536c8d16f373d02c1f6346a5c34cfe095a9dafd0cfe37d2b354090c",
        6_205_569,
        0,
        0,
        0o755,
      ),
      Path(
        "/boot/efi/m1n1/RECOVERY-OMARCHY-M2-DISPLAYPORT-20260902T085339Z.txt"
      ): (EXPECTED_RECOVERY_SHA256, 949, 0, 0, 0o755),
    }
    self.assertEqual(protected_pins, expected)
    self.assertEqual(
      module.ACTIVE_STATE_RELATIVE,
      "var/lib/omarchy/m2-displayport/active/state.env",
    )
    default_image_hash = protected_pins[Path("/boot/initramfs-linux-asahi.img")][0]
    grub_hash = protected_pins[Path("/boot/grub/grub.cfg")][0]
    self.assertNotEqual(default_image_hash, REJECTED_PRE_AVD_DEFAULT_IMAGE_SHA256)
    self.assertNotEqual(grub_hash, REJECTED_PRE_CLEANUP_GRUB_SHA256)

  def test_02_successful_exact_publication(self) -> None:
    module = load_publisher()
    with tempfile.TemporaryDirectory(prefix=".stage-success-", dir=ROOT) as temporary:
      sandbox = Sandbox(module, Path(temporary))
      snapshot = sandbox.protected_snapshot()
      result = module.stage_image(sandbox.config(), sandbox.facts_provider())
      self.assertEqual(result, sandbox.destination)
      self.assertEqual(sandbox.destination.read_bytes(), sandbox.image)
      self.assertEqual(stat.S_IMODE(sandbox.destination.stat().st_mode), 0o600)
      self.assertTrue((sandbox.transaction / "COMPLETE").is_file())
      self.assertFalse((sandbox.transaction / "INCOMPLETE").exists())
      self.assertTrue((sandbox.transaction / "transaction.json").is_file())
      self.assertTrue((sandbox.transaction / "REMOVE.txt").is_file())
      sandbox.assert_protected_snapshot(self, snapshot)

  def test_02a_production_contract_exact_publication(self) -> None:
    module = load_publisher()
    self.assertEqual(module.SOURCE, EXPECTED_SOURCE)
    self.assertEqual(module.SOURCE_SHA256, EXPECTED_SOURCE_SHA256)
    self.assertEqual(module.SOURCE_SIZE, EXPECTED_SOURCE_SIZE)
    source_before = module.SOURCE.stat()
    source_hash_before = digest(module.SOURCE.read_bytes())
    self.assertEqual(source_before.st_size, EXPECTED_SOURCE_SIZE)
    self.assertEqual(source_before.st_uid, 1001)
    self.assertEqual(source_before.st_gid, 1001)
    self.assertEqual(source_before.st_nlink, 1)
    self.assertEqual(stat.S_IMODE(source_before.st_mode), 0o600)
    self.assertEqual(source_hash_before, EXPECTED_SOURCE_SHA256)

    with tempfile.TemporaryDirectory(prefix=".stage-production-", dir=ROOT) as temporary:
      sandbox = Sandbox(module, Path(temporary))
      snapshot = sandbox.protected_snapshot()
      config = replace(
        sandbox.config(),
        source=module.SOURCE,
        source_sha256=module.SOURCE_SHA256,
        source_size=module.SOURCE_SIZE,
        source_owner=source_before.st_uid,
        source_group=source_before.st_gid,
        copy_chunk_size=1_048_576,
      )
      result = module.stage_image(config, sandbox.facts_provider())
      self.assertEqual(result, sandbox.destination)
      self.assertEqual(digest(result.read_bytes()), EXPECTED_SOURCE_SHA256)
      self.assertEqual(result.stat().st_size, EXPECTED_SOURCE_SIZE)
      self.assertEqual(stat.S_IMODE(result.stat().st_mode), 0o600)
      self.assertTrue((sandbox.transaction / "COMPLETE").is_file())
      self.assertFalse((sandbox.transaction / "INCOMPLETE").exists())
      sandbox.assert_protected_snapshot(self, snapshot)

    source_after = module.SOURCE.stat()
    self.assertEqual(digest(module.SOURCE.read_bytes()), source_hash_before)
    self.assertEqual(
      (source_after.st_dev, source_after.st_ino, source_after.st_size, source_after.st_mtime_ns),
      (source_before.st_dev, source_before.st_ino, source_before.st_size, source_before.st_mtime_ns),
    )

  def test_03_mutable_source_replacement_is_rejected(self) -> None:
    module = load_publisher()
    with tempfile.TemporaryDirectory(prefix=".stage-source-race-", dir=ROOT) as temporary:
      sandbox = Sandbox(module, Path(temporary))
      snapshot = sandbox.protected_snapshot()

      def replace_source(event: str) -> None:
        if event != "source_verified":
          return
        original = sandbox.source.with_suffix(".opened")
        sandbox.source.rename(original)
        sandbox.source.write_bytes(sandbox.image)
        sandbox.source.chmod(0o600)

      with self.assertRaisesRegex(module.StageFailure, "source identity changed"):
        module.stage_image(sandbox.config(), sandbox.facts_provider(), replace_source)
      self.assertFalse(sandbox.destination.exists())
      self.assertTrue((sandbox.transaction / "INCOMPLETE").is_file())
      sandbox.assert_protected_snapshot(self, snapshot)

  def test_03b_source_fd_mutation_is_rejected(self) -> None:
    module = load_publisher()
    with tempfile.TemporaryDirectory(prefix=".stage-source-fd-", dir=ROOT) as temporary:
      sandbox = Sandbox(module, Path(temporary))

      def mutate_source(event: str) -> None:
        if event == "source_verified":
          with sandbox.source.open("r+b") as source:
            source.seek(0)
            source.write(b"mutated")
            source.flush()
            os.fsync(source.fileno())

      with self.assertRaisesRegex(module.StageFailure, "copied candidate|source identity"):
        module.stage_image(sandbox.config(), sandbox.facts_provider(), mutate_source)
      self.assertFalse(sandbox.destination.exists())
      self.assertTrue((sandbox.transaction / "INCOMPLETE").is_file())

  def test_04_destination_collision_is_preserved(self) -> None:
    module = load_publisher()
    with tempfile.TemporaryDirectory(prefix=".stage-collision-", dir=ROOT) as temporary:
      sandbox = Sandbox(module, Path(temporary))
      collision = b"existing-destination"
      snapshot = sandbox.protected_snapshot()

      def create_collision(event: str) -> None:
        if event == "link":
          sandbox.destination.write_bytes(collision)

      with self.assertRaisesRegex(module.StageFailure, "destination already exists"):
        module.stage_image(sandbox.config(), sandbox.facts_provider(), create_collision)
      self.assertEqual(sandbox.destination.read_bytes(), collision)
      self.assertTrue((sandbox.transaction / "INCOMPLETE").is_file())
      sandbox.assert_protected_snapshot(self, snapshot)

  def test_05_symlink_paths_are_rejected(self) -> None:
    module = load_publisher()
    with tempfile.TemporaryDirectory(prefix=".stage-symlink-", dir=ROOT) as temporary:
      sandbox = Sandbox(module, Path(temporary))
      source_link = sandbox.source.with_name("source-link.img")
      source_link.symlink_to(sandbox.source)
      with self.assertRaisesRegex(module.StageFailure, "symlink"):
        module.stage_image(
          replace(sandbox.config(), source=source_link),
          sandbox.facts_provider(),
        )
      self.assertFalse(sandbox.destination.exists())

    with tempfile.TemporaryDirectory(prefix=".stage-destination-link-", dir=ROOT) as temporary:
      sandbox = Sandbox(module, Path(temporary))
      target = sandbox.boot / "link-target"
      target.write_bytes(b"preserve")
      sandbox.destination.symlink_to(target)
      with self.assertRaisesRegex(module.StageFailure, "destination already exists"):
        module.stage_image(sandbox.config(), sandbox.facts_provider())
      self.assertTrue(sandbox.destination.is_symlink())
      self.assertEqual(target.read_bytes(), b"preserve")

    with tempfile.TemporaryDirectory(prefix=".stage-parent-link-", dir=ROOT) as temporary:
      sandbox = Sandbox(module, Path(temporary))
      linked_boot = sandbox.base / "linked-boot"
      linked_boot.symlink_to(sandbox.boot, target_is_directory=True)
      linked_destination = linked_boot / "candidate.img"
      with self.assertRaisesRegex(module.StageFailure, "symlink"):
        module.stage_image(
          replace(sandbox.config(), destination=linked_destination),
          sandbox.facts_provider(),
        )
      self.assertFalse(sandbox.destination.exists())

  def test_06_partial_copy_signal_cleanup(self) -> None:
    module = load_publisher()
    with tempfile.TemporaryDirectory(prefix=".stage-signal-", dir=ROOT) as temporary:
      sandbox = Sandbox(module, Path(temporary))

      def interrupt_copy(event: str) -> None:
        if event == "copy_chunk":
          raise module.StageInterrupted("test signal")

      with self.assertRaisesRegex(module.StageInterrupted, "test signal"):
        module.stage_image(sandbox.config(), sandbox.facts_provider(), interrupt_copy)
      self.assertFalse(sandbox.destination.exists())
      self.assertFalse(any(sandbox.transaction.glob("*.partial")))
      self.assertTrue((sandbox.transaction / "INCOMPLETE").is_file())
      self.assertTrue((sandbox.transaction / "failure.json").is_file())

  def test_07_protected_pin_drift_is_rejected(self) -> None:
    module = load_publisher()
    with tempfile.TemporaryDirectory(prefix=".stage-pin-drift-", dir=ROOT) as temporary:
      sandbox = Sandbox(module, Path(temporary))

      def drift_pin(event: str) -> None:
        if event == "copy_complete":
          sandbox.pin.write_bytes(b"drifted-state")

      with self.assertRaisesRegex(module.StageFailure, "protected pin (?:metadata|hash)"):
        module.stage_image(sandbox.config(), sandbox.facts_provider(), drift_pin)
      self.assertFalse(sandbox.destination.exists())
      self.assertTrue((sandbox.transaction / "INCOMPLETE").is_file())

  def test_07a_protected_pin_path_replacement_is_rejected(self) -> None:
    module = load_publisher()
    with tempfile.TemporaryDirectory(prefix=".stage-pin-path-", dir=ROOT) as temporary:
      sandbox = Sandbox(module, Path(temporary))
      replaced = False
      original_metadata = sandbox.pin.stat()
      original_fstat = module.os.fstat

      def stable_original_fstat(descriptor: int):
        metadata = original_fstat(descriptor)
        if replaced and metadata.st_ino == original_metadata.st_ino:
          return original_metadata
        return metadata

      def replace_pin_path(event: str) -> None:
        nonlocal replaced
        if event != "pin_hash_chunk" or replaced:
          return
        replaced = True
        original = sandbox.pin.with_suffix(".opened")
        sandbox.pin.rename(original)
        sandbox.pin.write_bytes(original.read_bytes())
        sandbox.pin.chmod(0o600)

      with mock.patch.object(module.os, "fstat", stable_original_fstat):
        with self.assertRaisesRegex(module.StageFailure, "protected pin path changed"):
          module.stage_image(sandbox.config(), sandbox.facts_provider(), replace_pin_path)
      self.assertTrue(replaced)
      self.assertFalse(sandbox.destination.exists())
      self.assertTrue((sandbox.transaction / "INCOMPLETE").is_file())
      self.assertFalse((sandbox.transaction / "COMPLETE").exists())

  def test_07ab_protected_pin_ancestor_replacement_is_rejected(self) -> None:
    module = load_publisher()
    with tempfile.TemporaryDirectory(prefix=".stage-pin-ancestor-", dir=ROOT) as temporary:
      sandbox = Sandbox(module, Path(temporary))
      config = sandbox.config()
      pin_chunks = 0
      replaced = False
      opened_ancestor = sandbox.pin.parent.with_name("proof.opened")

      def replace_pin_ancestor(event: str) -> None:
        nonlocal pin_chunks, replaced
        if event != "pin_hash_chunk":
          return
        pin_chunks += 1
        if pin_chunks != len(config.protected_pins) * 2 + 1:
          return
        sandbox.pin.parent.rename(opened_ancestor)
        sandbox.pin.parent.mkdir()
        sandbox.pin.write_bytes((opened_ancestor / sandbox.pin.name).read_bytes())
        sandbox.pin.chmod(0o600)
        replaced = True

      with self.assertRaisesRegex(module.StageFailure, "protected pin canonical path changed"):
        module.stage_image(config, sandbox.facts_provider(), replace_pin_ancestor)
      self.assertTrue(replaced)
      self.assertEqual(
        digest((opened_ancestor / sandbox.pin.name).read_bytes()),
        digest(sandbox.pin.read_bytes()),
      )
      self.assertFalse(sandbox.destination.exists())
      self.assertTrue((sandbox.transaction / "INCOMPLETE").is_file())
      self.assertFalse((sandbox.transaction / "COMPLETE").exists())

  def test_07ac_active_state_contract_and_drift_are_rejected(self) -> None:
    module = load_publisher()
    with tempfile.TemporaryDirectory(prefix=".stage-state-contract-", dir=ROOT) as temporary:
      sandbox = Sandbox(module, Path(temporary))
      active_state = sandbox.system / module.ACTIVE_STATE_RELATIVE
      active_state.write_text(
        active_state.read_text(encoding="ascii").replace(
          "candidate_image_size=19184210",
          "candidate_image_size=19184211",
        ),
        encoding="ascii",
      )
      with self.assertRaisesRegex(module.StageFailure, "active format-2 state"):
        module.stage_image(sandbox.config(), sandbox.facts_provider())
      self.assertFalse(sandbox.destination.exists())
      self.assertTrue((sandbox.transaction / "INCOMPLETE").is_file())

    with tempfile.TemporaryDirectory(prefix=".stage-state-drift-", dir=ROOT) as temporary:
      sandbox = Sandbox(module, Path(temporary))
      active_state = sandbox.system / module.ACTIVE_STATE_RELATIVE

      def drift_active_state(event: str) -> None:
        if event == "copy_complete":
          with active_state.open("ab") as state_file:
            state_file.write(b"\n")
            state_file.flush()
            os.fsync(state_file.fileno())

      with self.assertRaisesRegex(module.StageFailure, "active format-2 state"):
        module.stage_image(sandbox.config(), sandbox.facts_provider(), drift_active_state)
      self.assertFalse(sandbox.destination.exists())
      self.assertTrue((sandbox.transaction / "INCOMPLETE").is_file())

  def test_07ad_protected_pin_metadata_and_ancestor_mode_are_rejected(self) -> None:
    module = load_publisher()
    with tempfile.TemporaryDirectory(prefix=".stage-pin-mode-", dir=ROOT) as temporary:
      sandbox = Sandbox(module, Path(temporary))
      config = sandbox.config()
      sandbox.pin.chmod(0o644)
      with self.assertRaisesRegex(module.StageFailure, "protected pin metadata mismatch"):
        module.stage_image(config, sandbox.facts_provider())
      self.assertFalse(sandbox.destination.exists())

    with tempfile.TemporaryDirectory(prefix=".stage-unsafe-ancestor-", dir=ROOT) as temporary:
      sandbox = Sandbox(module, Path(temporary))
      sandbox.pin.parent.chmod(0o777)
      with self.assertRaisesRegex(module.StageFailure, "group/world-writable trusted directory"):
        module.stage_image(sandbox.config(), sandbox.facts_provider())
      self.assertFalse(sandbox.destination.exists())

    with tempfile.TemporaryDirectory(prefix=".stage-pin-link-", dir=ROOT) as temporary:
      sandbox = Sandbox(module, Path(temporary))
      os.link(sandbox.pin, sandbox.pin.with_suffix(".linked"))
      with self.assertRaisesRegex(module.StageFailure, "singly linked"):
        module.stage_image(sandbox.config(), sandbox.facts_provider())
      self.assertFalse(sandbox.destination.exists())

  def test_07ae_nonroot_protected_ancestors_are_rejected(self) -> None:
    module = load_publisher()
    for mode in (0o700, 0o755):
      with self.subTest(mode=oct(mode)):
        with tempfile.TemporaryDirectory(prefix=".stage-ancestor-owner-", dir=ROOT) as temporary:
          sandbox = Sandbox(module, Path(temporary))
          ancestor = sandbox.pin.parent
          ancestor.chmod(mode)
          ancestor_inode = ancestor.stat().st_ino
          original_fstat = module.os.fstat

          def nonroot_ancestor(descriptor: int):
            metadata = original_fstat(descriptor)
            if metadata.st_ino != ancestor_inode:
              return metadata
            fields = list(metadata)
            fields[4] = os.geteuid() + 1
            return os.stat_result(fields)

          with mock.patch.object(module.os, "fstat", nonroot_ancestor):
            with self.assertRaisesRegex(module.StageFailure, "trusted directory owner mismatch"):
              module.stage_image(sandbox.config(), sandbox.facts_provider())
          self.assertFalse(sandbox.destination.exists())
          self.assertTrue((sandbox.transaction / "INCOMPLETE").is_file())

  def test_07b_protected_pin_fd_mutation_is_rejected(self) -> None:
    module = load_publisher()
    with tempfile.TemporaryDirectory(prefix=".stage-pin-fd-", dir=ROOT) as temporary:
      sandbox = Sandbox(module, Path(temporary))
      mutated = False

      def mutate_pin(event: str) -> None:
        nonlocal mutated
        if event == "pin_hash_chunk" and not mutated:
          mutated = True
          with sandbox.pin.open("r+b") as protected:
            protected.seek(0)
            protected.write(b"changed")
            protected.flush()
            os.fsync(protected.fileno())

      with self.assertRaisesRegex(module.StageFailure, "protected pin"):
        module.stage_image(sandbox.config(), sandbox.facts_provider(), mutate_pin)
      self.assertFalse(sandbox.destination.exists())
      self.assertTrue((sandbox.transaction / "INCOMPLETE").is_file())

  def test_07c_candidate_metadata_and_hash_fail_closed(self) -> None:
    module = load_publisher()

    def wrong_mode(sandbox: Sandbox):
      sandbox.source.chmod(0o644)
      return sandbox.config()

    def extra_link(sandbox: Sandbox):
      os.link(sandbox.source, sandbox.source.with_suffix(".linked"))
      return sandbox.config()

    def wrong_hash(sandbox: Sandbox):
      sandbox.source.write_bytes(b"wrong-image")
      sandbox.source.chmod(0o600)
      return sandbox.config()

    cases = (
      ("owner", lambda sandbox: replace(sandbox.config(), source_owner=os.geteuid() + 1)),
      ("group", lambda sandbox: replace(sandbox.config(), source_group=os.getegid() + 1)),
      ("mode", wrong_mode),
      ("link", extra_link),
      ("hash", wrong_hash),
    )
    for label, change in cases:
      with self.subTest(label=label):
        with tempfile.TemporaryDirectory(prefix=f".stage-input-{label}-", dir=ROOT) as temporary:
          sandbox = Sandbox(module, Path(temporary))
          config = change(sandbox)
          with self.assertRaises(module.StageFailure):
            module.stage_image(config, sandbox.facts_provider())
          self.assertFalse(sandbox.destination.exists())
          self.assertTrue((sandbox.transaction / "INCOMPLETE").is_file())

  def test_07d_fresh_fact_and_mount_drift_is_rejected(self) -> None:
    module = load_publisher()
    for field in ("kernel_release", "package_output", "mount_output"):
      with self.subTest(field=field):
        with tempfile.TemporaryDirectory(prefix=f".stage-fact-{field}-", dir=ROOT) as temporary:
          sandbox = Sandbox(module, Path(temporary))
          calls = 0

          def drifting_facts():
            nonlocal calls
            calls += 1
            facts = sandbox.facts()
            if calls < 2:
              return facts
            return replace(facts, **{field: "drifted"})

          with self.assertRaises(module.StageFailure):
            module.stage_image(sandbox.config(), drifting_facts)
          self.assertGreaterEqual(calls, 2)
          self.assertFalse(sandbox.destination.exists())
          self.assertTrue((sandbox.transaction / "INCOMPLETE").is_file())

  def test_07da_protected_copy_mismatch_is_rejected(self) -> None:
    module = load_publisher()
    with tempfile.TemporaryDirectory(prefix=".stage-protected-copy-", dir=ROOT) as temporary:
      sandbox = Sandbox(module, Path(temporary))

      def corrupt_protected_copy(event: str) -> None:
        if event != "copy_complete":
          return
        candidate = sandbox.transaction / ".candidate.partial"
        with candidate.open("r+b") as protected:
          protected.seek(0)
          first = protected.read(1)
          protected.seek(0)
          protected.write(bytes((first[0] ^ 1,)))
          protected.flush()
          os.fsync(protected.fileno())

      with self.assertRaisesRegex(module.StageFailure, "published destination hash"):
        module.stage_image(
          sandbox.config(),
          sandbox.facts_provider(),
          corrupt_protected_copy,
        )
      self.assertFalse(sandbox.destination.exists())
      self.assertFalse((sandbox.transaction / "COMPLETE").exists())
      self.assertTrue((sandbox.transaction / "INCOMPLETE").is_file())

  def test_07e_fault_boundaries_preserve_transaction_semantics(self) -> None:
    module = load_publisher()
    precommit_faults = (
      "link",
      "destination_parent_fsync",
      "temp_unlink",
      "destination_verify",
      "final_pin_check",
      "record_write",
      "commit_pin_check",
      "marker_rename",
    )
    for fault in precommit_faults:
      with self.subTest(fault=fault):
        with tempfile.TemporaryDirectory(prefix=f".stage-fault-{fault}-", dir=ROOT) as temporary:
          sandbox = Sandbox(module, Path(temporary))
          snapshot = sandbox.protected_snapshot()

          def inject(event: str) -> None:
            if event == fault:
              raise module.StageInterrupted(f"fault {fault}")

          with self.assertRaises(module.StageInterrupted):
            module.stage_image(sandbox.config(), sandbox.facts_provider(), inject)
          self.assertFalse(sandbox.destination.exists())
          self.assertTrue((sandbox.transaction / "INCOMPLETE").is_file())
          self.assertFalse((sandbox.transaction / "COMPLETE").exists())
          sandbox.assert_protected_snapshot(self, snapshot)

    with tempfile.TemporaryDirectory(prefix=".stage-fault-marker-fsync-", dir=ROOT) as temporary:
      sandbox = Sandbox(module, Path(temporary))

      def fail_marker_fsync(event: str) -> None:
        if event == "marker_dir_fsync":
          raise module.StageInterrupted("fault marker_dir_fsync")

      with self.assertRaises(module.StageInterrupted):
        module.stage_image(sandbox.config(), sandbox.facts_provider(), fail_marker_fsync)
      self.assertFalse(sandbox.destination.exists())
      self.assertFalse((sandbox.transaction / "COMPLETE").exists())
      self.assertTrue((sandbox.transaction / "INCOMPLETE").is_file())

  def test_07f_post_final_check_ancestor_swap_is_rejected(self) -> None:
    module = load_publisher()
    with tempfile.TemporaryDirectory(prefix=".stage-final-ancestor-", dir=ROOT) as temporary:
      sandbox = Sandbox(module, Path(temporary))
      moved = sandbox.pin.parent.with_name("proof.opened-after-final")
      swapped = False

      def swap_after_final_check(event: str) -> None:
        nonlocal swapped
        if event != "record_write":
          return
        sandbox.pin.parent.rename(moved)
        sandbox.pin.parent.mkdir()
        sandbox.pin.write_bytes((moved / sandbox.pin.name).read_bytes())
        sandbox.pin.chmod(0o600)
        swapped = True

      with self.assertRaisesRegex(module.StageFailure, "protected pin identity changed before commit"):
        module.stage_image(
          sandbox.config(),
          sandbox.facts_provider(),
          swap_after_final_check,
        )
      self.assertTrue(swapped)
      self.assertFalse(sandbox.destination.exists())
      self.assertFalse((sandbox.transaction / "COMPLETE").exists())
      self.assertTrue((sandbox.transaction / "INCOMPLETE").is_file())

  def test_08_preflight_matrix_fails_closed(self) -> None:
    module = load_publisher()
    cases = (
      ("kernel", lambda sandbox: replace(sandbox.facts(), kernel_release="wrong")),
      ("package", lambda sandbox: replace(sandbox.facts(), package_output="wrong")),
      ("mount", lambda sandbox: replace(sandbox.facts(), mount_output="wrong")),
    )
    for label, change in cases:
      with self.subTest(label=label):
        with tempfile.TemporaryDirectory(prefix=f".stage-{label}-", dir=ROOT) as temporary:
          sandbox = Sandbox(module, Path(temporary))
          with self.assertRaises(module.StageFailure):
            module.stage_image(sandbox.config(), lambda: change(sandbox))
          self.assertFalse(sandbox.destination.exists())

    file_cases = (
      "sys/firmware/devicetree/base/compatible",
      "sys/devices/platform/soc/23e400000.smc/macsmc-power/power_supply/"
      "macsmc-battery/capacity",
      "sys/devices/platform/soc/23e400000.smc/macsmc-power/power_supply/"
      "macsmc-ac/online",
    )
    for relative in file_cases:
      with self.subTest(relative=relative):
        with tempfile.TemporaryDirectory(prefix=".stage-host-", dir=ROOT) as temporary:
          sandbox = Sandbox(module, Path(temporary))
          (sandbox.system / relative).write_bytes(b"wrong")
          with self.assertRaises(module.StageFailure):
            module.stage_image(sandbox.config(), sandbox.facts_provider())
          self.assertFalse(sandbox.destination.exists())

  def test_09_publisher_is_self_contained_and_bootstrap_uses_stdin(self) -> None:
    source = PUBLISHER.read_text(encoding="utf-8")
    bootstrap = BOOTSTRAP.read_text(encoding="utf-8")
    self.assertEqual(bootstrap.splitlines()[0], EXPECTED_BOOTSTRAP_PREFIX)
    self.assertNotIn("/tmp", source)
    self.assertNotIn("/tmp", bootstrap)
    self.assertNotRegex(bootstrap, r"sudo[^\n]*(?:/home|/tmp)/[^\n]+\.(?:sh|py)")
    self.assertIn("/usr/bin/bash -s", bootstrap)
    self.assertIn('exec /usr/bin/env -i PATH=/usr/bin:/bin LANG=C.UTF-8', bootstrap)
    self.assertNotRegex(source, r"\b(?:exec|eval|compile)\s*\(")
    self.assertNotIn("importlib", source)

  @unittest.skipUnless(Path("/usr/bin/bwrap").is_file(), "bwrap is unavailable")
  def test_10_exact_bootstrap_authenticates_before_preflight(self) -> None:
    text = BOOTSTRAP.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix=".bootstrap-success-", dir=ROOT) as temporary:
      boot = Path(temporary) / "boot"
      boot.mkdir(mode=0o755)
      result = run_bootstrap(boot, bootstrap_body(text))
      self.assertNotEqual(result.returncode, 0)
      self.assertIn("REFUSED: directory owner mismatch: /", result.stderr)
      transactions = tuple(boot.glob(".dev147-afk-pr582-stage.*"))
      self.assertEqual(len(transactions), 1)
      transaction = transactions[0]
      publisher = transaction / "stage-image.py"
      self.assertEqual(stat.S_IMODE(transaction.stat().st_mode), 0o700)
      self.assertEqual(stat.S_IMODE(publisher.stat().st_mode), 0o500)
      self.assertEqual(digest(publisher.read_bytes()), digest(PUBLISHER.read_bytes()))
      self.assertTrue((transaction / "INCOMPLETE").is_file())
      self.assertFalse((transaction / "COMPLETE").exists())

  @unittest.skipUnless(Path("/usr/bin/bwrap").is_file(), "bwrap is unavailable")
  def test_11_exact_bootstrap_tamper_collision_and_signal_controls(self) -> None:
    text = BOOTSTRAP.read_text(encoding="utf-8")
    body = bootstrap_body(text)
    payload_hash, payload = bootstrap_payload(text)
    encoded = base64.b64encode(payload).decode()
    replacement = ("A" if encoded[0] != "A" else "B") + encoded[1:]
    tampered_body = body.replace(
      re.search(
        r"<<'DEV147_AFK_PR582_STAGE_IMAGE_PAYLOAD'\n([A-Za-z0-9+/=\n]+)\nDEV147_AFK_PR582_STAGE_IMAGE_PAYLOAD",
        body,
        re.MULTILINE,
      ).group(1),
      replacement,
    )
    self.assertEqual(payload_hash, digest(payload))

    with tempfile.TemporaryDirectory(prefix=".bootstrap-tamper-", dir=ROOT) as temporary:
      boot = Path(temporary) / "boot"
      boot.mkdir(mode=0o755)
      result = run_bootstrap(boot, tampered_body)
      self.assertNotEqual(result.returncode, 0)
      self.assertIn("publisher payload identity mismatch", result.stderr)
      transaction = next(boot.glob(".dev147-afk-pr582-stage.*"))
      self.assertTrue((transaction / "INCOMPLETE").is_file())
      self.assertFalse((transaction / "failure.json").exists())

    with tempfile.TemporaryDirectory(prefix=".bootstrap-collision-", dir=ROOT) as temporary:
      base = Path(temporary)
      boot = base / "boot"
      transaction = boot / ".dev147-afk-pr582-stage.fixed"
      transaction.mkdir(parents=True, mode=0o700)
      collision = transaction / "stage-image.py"
      collision.write_bytes(b"preserve-collision")
      fake_mktemp = base / "mktemp"
      fake_mktemp.write_text(
        "#!/bin/bash\nprintf '%s\\n' /boot/.dev147-afk-pr582-stage.fixed\n",
        encoding="utf-8",
      )
      fake_mktemp.chmod(0o755)
      result = run_bootstrap(
        boot,
        body,
        ((fake_mktemp, "/usr/bin/mktemp"),),
      )
      self.assertNotEqual(result.returncode, 0)
      self.assertEqual(collision.read_bytes(), b"preserve-collision")
      self.assertTrue((transaction / "INCOMPLETE").is_file())

    with tempfile.TemporaryDirectory(prefix=".bootstrap-signal-", dir=ROOT) as temporary:
      base = Path(temporary)
      boot = base / "boot"
      boot.mkdir(mode=0o755)
      fake_base64 = base / "base64"
      fake_base64.write_text(
        "#!/bin/bash\nkill -TERM \"$PPID\"\nexit 0\n",
        encoding="utf-8",
      )
      fake_base64.chmod(0o755)
      result = run_bootstrap(
        boot,
        body,
        ((fake_base64, "/usr/bin/base64"),),
      )
      self.assertNotEqual(result.returncode, 0)
      transaction = next(boot.glob(".dev147-afk-pr582-stage.*"))
      self.assertTrue((transaction / "INCOMPLETE").is_file())
      self.assertFalse((transaction / "COMPLETE").exists())


if __name__ == "__main__":
  unittest.main(verbosity=2)
