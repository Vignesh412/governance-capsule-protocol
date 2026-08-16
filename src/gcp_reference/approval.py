"""Scoped approval consumption and amendment authorization."""

from datetime import datetime
from typing import Any, Mapping, Optional, Sequence

from .crypto import KeyResolver, artifact_digest, verify_artifact
from .errors import ErrorCode, GCPError
from .replay import UseRegistry


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _authorized_signer(
    artifact: Mapping[str, Any],
    identity_field: str,
    authorized: Mapping[str, Sequence[str]],
    error_code: ErrorCode,
) -> None:
    identity = artifact[identity_field]
    method = artifact["proof"]["verification_method"]
    if method not in authorized.get(identity, ()):
        raise GCPError(
            error_code,
            "Declared authority is not bound to this signing key",
            {identity_field: identity, "verification_method": method},
        )


def amendment_change_digest(amendment: Mapping[str, Any]) -> str:
    """Digest the ordered change declaration approved by a human or policy."""

    return artifact_digest({"changes": amendment["changes"]})


def validate_approval(
    approval: Mapping[str, Any],
    capsule: Mapping[str, Any],
    *,
    action: str,
    resource: str,
    now: datetime,
    resolver: KeyResolver,
    authorized_approvers: Mapping[str, Sequence[str]],
    scope_type: str = "action",
    change_digest: Optional[str] = None,
    validate_schema: bool = True,
) -> None:
    if validate_schema:
        from .schema import validate_structure

        validate_structure(approval, "approval.schema.json")
    verify_artifact(approval, resolver)
    _authorized_signer(
        approval, "approver", authorized_approvers, ErrorCode.UNAUTHORIZED_APPROVER
    )
    if approval["capsule_digest"] != artifact_digest(capsule):
        raise GCPError(
            ErrorCode.APPROVAL_SCOPE_MISMATCH,
            "Approval is bound to another capsule revision",
        )
    if now < _parse_time(approval["issued_at"]):
        raise GCPError(ErrorCode.APPROVAL_NOT_YET_VALID, "Approval is not yet valid")
    if now >= _parse_time(approval["expires_at"]):
        raise GCPError(ErrorCode.APPROVAL_EXPIRED, "Approval has expired")
    scope = approval["scope"]
    if (
        scope["type"] != scope_type
        or scope["action"] != action
        or scope["resource"] != resource
        or (scope_type == "amendment" and scope.get("change_digest") != change_digest)
    ):
        raise GCPError(
            ErrorCode.APPROVAL_SCOPE_MISMATCH,
            "Approval does not authorize this operation",
            {"expected_type": scope_type, "action": action, "resource": resource},
        )


class ApprovalRegistry:
    """Verify an approval before atomically consuming one permitted use."""

    def __init__(self) -> None:
        self._uses = UseRegistry()

    def consume(
        self,
        approval: Mapping[str, Any],
        capsule: Mapping[str, Any],
        **validation: Any,
    ) -> int:
        validate_approval(approval, capsule, **validation)
        return self._uses.commit(
            approval["approval_id"], max_uses=approval["max_uses"]
        )

    def count(self, approval_id: str) -> int:
        return self._uses.count(approval_id)


def validate_amendment(
    amendment: Mapping[str, Any],
    previous_capsule: Mapping[str, Any],
    result_capsule: Mapping[str, Any],
    approval: Mapping[str, Any],
    *,
    now: datetime,
    resolver: KeyResolver,
    authorized_authorities: Mapping[str, Sequence[str]],
    authorized_approvers: Mapping[str, Sequence[str]],
    approval_registry: ApprovalRegistry,
    validate_schema: bool = True,
) -> int:
    if validate_schema:
        from .schema import validate_structure

        validate_structure(previous_capsule, "capsule.schema.json")
        validate_structure(result_capsule, "capsule.schema.json")
        validate_structure(amendment, "amendment.schema.json")
    verify_artifact(amendment, resolver)
    _authorized_signer(
        amendment,
        "authority",
        authorized_authorities,
        ErrorCode.UNAUTHORIZED_AMENDMENT,
    )
    if "expires_at" in amendment and now >= _parse_time(amendment["expires_at"]):
        raise GCPError(ErrorCode.APPROVAL_EXPIRED, "Amendment has expired")
    if now < _parse_time(amendment["issued_at"]):
        raise GCPError(ErrorCode.APPROVAL_NOT_YET_VALID, "Amendment is not yet valid")
    if (
        amendment["previous_capsule_digest"] != artifact_digest(previous_capsule)
        or amendment["result_capsule_digest"] != artifact_digest(result_capsule)
        or amendment["approval_id"] != approval["approval_id"]
        or previous_capsule["capsule_id"] != result_capsule["capsule_id"]
        or previous_capsule["task"]["task_id"] != result_capsule["task"]["task_id"]
        or result_capsule["revision"] != previous_capsule["revision"] + 1
        or result_capsule["sequence"] <= previous_capsule["sequence"]
    ):
        raise GCPError(
            ErrorCode.AMENDMENT_MISMATCH,
            "Amendment does not bind one consecutive revision of the same task",
        )
    return approval_registry.consume(
        approval,
        previous_capsule,
        action="capsule.amend",
        resource=previous_capsule["capsule_id"],
        now=now,
        resolver=resolver,
        authorized_approvers=authorized_approvers,
        scope_type="amendment",
        change_digest=amendment_change_digest(amendment),
        validate_schema=validate_schema,
    )
