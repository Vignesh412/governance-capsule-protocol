"""Governance Capsule Protocol candidate reference library."""

from .crypto import KeyResolver, artifact_digest, sign_artifact, verify_artifact
from .errors import ErrorCode, GCPError
from .semantics import validate_delegation, validate_delegation_proof

__all__ = [
    "ErrorCode",
    "GCPError",
    "KeyResolver",
    "artifact_digest",
    "sign_artifact",
    "validate_delegation",
    "validate_delegation_proof",
    "verify_artifact",
]
