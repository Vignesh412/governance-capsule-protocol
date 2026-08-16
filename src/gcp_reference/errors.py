"""Deterministic GCP error codes."""

from enum import Enum
from typing import Any, Mapping, Optional


class ErrorCode(str, Enum):
    INVALID_SIGNATURE = "GCP_INVALID_SIGNATURE"
    UNKNOWN_VERIFICATION_METHOD = "GCP_UNKNOWN_VERIFICATION_METHOD"
    UNSUPPORTED_SEMANTICS = "GCP_UNSUPPORTED_SEMANTICS"
    PARENT_MISMATCH = "GCP_PARENT_MISMATCH"
    INVALID_DELEGATION_PROOF = "GCP_INVALID_DELEGATION_PROOF"
    LINEAGE_CYCLE = "GCP_LINEAGE_CYCLE"
    AUTHORITY_EXPANSION = "GCP_AUTHORITY_EXPANSION"
    OBLIGATION_REMOVED = "GCP_OBLIGATION_REMOVED"
    OBLIGATION_MODIFIED = "GCP_OBLIGATION_MODIFIED"
    BUDGET_OVERALLOCATED = "GCP_BUDGET_OVERALLOCATED"
    BUDGET_UNIT_MISMATCH = "GCP_BUDGET_UNIT_MISMATCH"
    TEMPORAL_EXPANSION = "GCP_TEMPORAL_EXPANSION"
    DELEGATION_DEPTH_EXCEEDED = "GCP_DELEGATION_DEPTH_EXCEEDED"


class GCPError(ValueError):
    """A deterministic protocol validation failure."""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        details: Optional[Mapping[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = dict(details or {})

    def as_dict(self) -> Mapping[str, Any]:
        return {"code": self.code.value, "message": self.message, "details": self.details}
