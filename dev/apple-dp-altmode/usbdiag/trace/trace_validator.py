"""Offline trace validation only; this module never queries a running system."""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class SoftwareFinding:
    kind: Literal["early_null_then_late_host_setter"]
    dwc3_generation: int
    attempt: int
    atc_generation: int


@dataclass(frozen=True)
class FailedOperation:
    component: str
    generation: int
    attempt: int
    event: str
    ret: int


@dataclass(frozen=True)
class ValidationResult:
    status: Literal["positive_software_sequence", "inconclusive"]
    findings: tuple[SoftwareFinding, ...]
    issues: tuple[str, ...]
    failed_operations: tuple[FailedOperation, ...]
    negative_late_setter_claim: bool = False
    limitations: tuple[str, ...] = (
        "software_order_only",
        "host_init_is_not_hcd_completion",
        "no_caller_attribution",
        "consecutive_prefix_does_not_prove_tail",
    )


def validate_capture(payload: object, expected_manifest: object) -> ValidationResult:
    """Validate untrusted saved evidence without hardware access.

    The manifest must bind this revision to both reviewed binary hashes and
    build IDs. The capture supplies matching observed identities and the
    original kernel journal envelopes. A complete-looking prefix never proves
    absence of a later setter.
    """
    raise NotImplementedError("RED checkpoint: implement after sandbox fixture run")
