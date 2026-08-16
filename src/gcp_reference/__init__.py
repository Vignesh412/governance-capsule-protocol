"""Governance Capsule Protocol candidate reference library."""

from .allocation import AllocationLedger
from .approval import (
    ApprovalRegistry,
    amendment_change_digest,
    validate_amendment,
    validate_approval,
)
from .crypto import KeyResolver, artifact_digest, sign_artifact, verify_artifact
from .errors import ErrorCode, GCPError
from .replay import UseRegistry
from .revocation import (
    RevocationEvaluator,
    RevocationEvidence,
    RevocationResult,
    StatusRecord,
    status_from_signed_revocation,
)
from .schema import SchemaValidator, validate_structure
from .semantics import validate_audience, validate_delegation, validate_delegation_proof

__all__ = [
    "AllocationLedger",
    "ApprovalRegistry",
    "ErrorCode",
    "GCPError",
    "KeyResolver",
    "RevocationEvaluator",
    "RevocationEvidence",
    "RevocationResult",
    "StatusRecord",
    "SchemaValidator",
    "UseRegistry",
    "artifact_digest",
    "amendment_change_digest",
    "sign_artifact",
    "status_from_signed_revocation",
    "validate_audience",
    "validate_amendment",
    "validate_approval",
    "validate_delegation",
    "validate_delegation_proof",
    "verify_artifact",
    "validate_structure",
]
