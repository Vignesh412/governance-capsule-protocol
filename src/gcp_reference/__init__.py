"""Governance Capsule Protocol candidate reference library."""

from .allocation import AllocationLedger
from .crypto import KeyResolver, artifact_digest, sign_artifact, verify_artifact
from .errors import ErrorCode, GCPError
from .replay import UseRegistry
from .revocation import RevocationEvaluator, RevocationEvidence, RevocationResult, StatusRecord
from .semantics import validate_audience, validate_delegation, validate_delegation_proof

__all__ = [
    "AllocationLedger",
    "ErrorCode",
    "GCPError",
    "KeyResolver",
    "RevocationEvaluator",
    "RevocationEvidence",
    "RevocationResult",
    "StatusRecord",
    "UseRegistry",
    "artifact_digest",
    "sign_artifact",
    "validate_audience",
    "validate_delegation",
    "validate_delegation_proof",
    "verify_artifact",
]
