"""Fail-closed T1 parser subject, deliberately incomplete for semantic RED.

This module is pure. It does not read files, environment variables, journals,
devices, or module metadata. Structural fixture acceptance is not operational
acceptance. No reviewed T1 image/module identity is available in this draft.

No-install exception: typed dataclasses replace Pydantic for this contained
offline tool. The separate test runner uses the standard-library unittest.
"""

from dataclasses import dataclass
from typing import Literal


REVISION = "dev147-tipddiag1-v1"
BOARD = "j413"
TARGET = "front_lower"
COMPONENT = "tipd"


@dataclass(frozen=True)
class SyntheticBinding:
  """An external fixture oracle; never an operational artifact manifest."""

  label: str
  image_sha256: str
  image_size: int
  tipd_sha256: str
  tipd_build_id: str


@dataclass(frozen=True)
class HpdReturn:
  generation: int
  worker: int
  sequence: int


@dataclass(frozen=True)
class FailedOperation:
  generation: int
  worker: int
  event: Literal["init", "worker", "mux", "role"]
  sequence: int
  ret: int


@dataclass(frozen=True)
class TraceResult:
  status: Literal["structurally_complete", "inconclusive", "limited"]
  codes: tuple[str, ...]
  evidence: Literal["synthetic_only", "unbound"]
  record_count: int = 0
  generation_count: int = 0
  worker_count: int = 0
  connected_hpd_returns: tuple[HpdReturn, ...] = ()
  failed_operations: tuple[FailedOperation, ...] = ()
  operationally_accepted: bool = False
  negative_sender_claim: bool = False
  receiver_delivery_claim: bool = False
  usb_or_video_fix_claim: bool = False
  limitations: tuple[str, ...] = (
    "fixture_structure_is_not_boot_evidence",
    "consecutive_prefix_does_not_prove_tail",
    "core_init_entry_is_not_frontend_probe_entry",
    "hpd_return_is_not_receiver_delivery",
    "no_hardware_safety_or_usb_video_fix_claim",
  )


def inspect_fixture_capture(document: str, binding: SyntheticBinding) -> TraceResult:
  """Return the missing-feature result until genuine RED has been retained."""
  return TraceResult(
    status="inconclusive",
    codes=("parser_not_implemented",),
    evidence="synthetic_only",
  )


def validate_capture(document: str) -> TraceResult:
  """Refuse operational use without a later reviewed fixed artifact binding.

  There is intentionally no manifest, expected hash, environment, or caller
  override. A synthetic binding cannot enable this entry point.
  """
  return TraceResult(
    status="inconclusive",
    codes=("artifact_binding_unavailable",),
    evidence="unbound",
  )
