"""Pure binding for the one accepted T1 artifact and user attestations.

No live or protected path is read. Submitted bytes establish consistency,
not staging provenance, initrd selection proof or hardware acceptance.
"""

from dataclasses import dataclass
import hashlib
import re
from typing import Literal

from capture_binding import (
  CaptureError, CaptureFacts, CaptureFiles, _decode, inspect_capture_files,
)


IMAGE_NAME = "initramfs-linux-asahi-dpalt-tipddiag1.img"
IMAGE_SHA256 = "c72c36736cebba0d6d5b67f47b02330c35d3ef81fed9bf5b3315095b0dd765fe"
IMAGE_BYTES = 19_209_545
TIPD_SHA256 = "a0fdadc351261643545e5afd8561923be99431661c447084336c9318f5b0c02f"
TIPD_BUILD_ID = "40aa54382047ba36b02c9ac0da65a213862a77ad"
KERNEL_RELEASE = "7.1.6-1-1-ARCH"
STAGING_HELPER_SHA256 = "6b20d119791f4322e101a92b9e5b850ba3098d35dbf966f2d7918cb3918694f9"
STAGING_PREFIX_SHA256 = "32076acedfc5bd40b88cded89b0d37cd545caaae885d4acd29444e9fe310d03e"
STAGING_PREFIX_BYTES = 5_870
STAGING_KEYS = frozenset((
  "schema", "helper_sha256", "image_sha256", "image_bytes",
  "stdout_sha256", "stderr_sha256", "reported_exit_code",
))
SELECTION_KEYS = frozenset(("schema", "selected_initrd", "boot_id"))


class BindingError(ValueError):
  """A fixed non-sensitive code refuses inconsistent supplied evidence."""


@dataclass(frozen=True)
class FixedBinding:
  facts: CaptureFacts
  status: Literal["consistent_user_attestation", "inconclusive"]
  codes: tuple[str, ...]
  selected_initrd: str
  image_sha256: str
  image_bytes: int
  expected_tipd_sha256: str
  reported_staging_exit_code: int | None
  staging_evidence: Literal["user_attested_only"] = "user_attested_only"
  selection_evidence: Literal["user_attested_only"] = "user_attested_only"
  collection_evidence: Literal["submitted_bytes_consistency_only"] = "submitted_bytes_consistency_only"
  operationally_accepted: Literal[False] = False
  initrd_boot_proven: Literal[False] = False
  earliest_load_proven: Literal[False] = False
  negative_sender_claim: Literal[False] = False
  receiver_delivery_claim: Literal[False] = False
  hardware_acceptance: Literal[False] = False


def _attestation(raw: bytes, keys: frozenset[str], code: str) -> dict[str, object]:
  if not isinstance(raw, bytes) or not 0 < len(raw) <= 16_384:
    raise BindingError(code)
  try:
    value = _decode(raw, code)
  except CaptureError:
    raise BindingError(code) from None
  if not isinstance(value, dict) or set(value) != keys:
    raise BindingError(code)
  return value


def _valid_hash(value: object) -> bool:
  return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _staging(attestation: bytes, stdout: bytes, stderr: bytes) -> int | None:
  value = _attestation(attestation, STAGING_KEYS, "invalid_staging_attestation")
  reported = value["reported_exit_code"]
  if (
    value["schema"] != "dev147-t1-staging-attestation1"
    or type(value["image_bytes"]) is not int
    or not 0 <= value["image_bytes"] <= 2**64 - 1
    or (reported is not None and (type(reported) is not int or not -2**31 <= reported < 2**31))
    or any(not _valid_hash(value[key]) for key in (
      "helper_sha256", "image_sha256", "stdout_sha256", "stderr_sha256",
    ))
  ):
    raise BindingError("invalid_staging_attestation")
  if (
    value["helper_sha256"] != STAGING_HELPER_SHA256
    or value["image_sha256"] != IMAGE_SHA256 or value["image_bytes"] != IMAGE_BYTES
  ):
    raise BindingError("staging_identity_mismatch")
  if not isinstance(stdout, bytes) or not isinstance(stderr, bytes) or len(stdout) > 8_192 or len(stderr) > 65_536:
    raise BindingError("staging_output_mismatch")
  if (
    hashlib.sha256(stdout).hexdigest() != value["stdout_sha256"]
    or hashlib.sha256(stderr).hexdigest() != value["stderr_sha256"]
  ):
    raise BindingError("staging_output_mismatch")
  if stderr or reported not in (None, 0):
    raise BindingError("staging_not_successful")
  prefix, completion = stdout[:STAGING_PREFIX_BYTES], stdout[STAGING_PREFIX_BYTES:]
  if (
    len(prefix) != STAGING_PREFIX_BYTES or prefix.count(b"\n") != 45
    or hashlib.sha256(prefix).hexdigest() != STAGING_PREFIX_SHA256
    or re.fullmatch(
      rb"STAGING ONLY PASS: /boot/initramfs-linux-asahi-dpalt-tipddiag1\.img\n"
      rb"Checks retained in /boot/\.dev147-tipddiag-stage\.[A-Za-z0-9]{10}\n"
      rb"No reboot permission\. Normal boot is unchanged; this T1 TIPD diagnostic image is untested at startup\.\n",
      completion,
    ) is None
  ):
    raise BindingError("staging_output_mismatch")
  return reported


def bind_fixed_t1(
  files: CaptureFiles, *, staging_attestation: bytes, staging_stdout: bytes,
  staging_stderr: bytes, selection_attestation: bytes,
) -> FixedBinding:
  """Qualify user attestations without promoting them to execution proof."""
  try:
    facts = inspect_capture_files(files)
  except CaptureError as error:
    raise BindingError(str(error)) from None
  reported = _staging(staging_attestation, staging_stdout, staging_stderr)
  selection = _attestation(selection_attestation, SELECTION_KEYS, "invalid_selection_attestation")
  if (
    selection["schema"] != "dev147-t1-selection-attestation1"
    or not isinstance(selection["selected_initrd"], str)
    or not isinstance(selection["boot_id"], str)
    or re.fullmatch(r"[0-9a-f]{32}", selection["boot_id"]) is None
  ):
    raise BindingError("invalid_selection_attestation")
  if selection["selected_initrd"] != IMAGE_NAME or selection["boot_id"] != facts.boot_id:
    raise BindingError("selection_mismatch")
  codes: tuple[str, ...] = ()
  if reported is None:
    codes += ("staging_exit_unobserved",)
  if facts.structural_status != "structurally_complete":
    codes += ("capture_" + facts.structural_status,)
  return FixedBinding(
    facts, "inconclusive" if codes else "consistent_user_attestation", codes,
    IMAGE_NAME, IMAGE_SHA256, IMAGE_BYTES, TIPD_SHA256, reported,
  )
