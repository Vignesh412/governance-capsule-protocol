"""Stateless semantic validation for ordinary GCP delegation."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Iterable, Mapping, Optional, Set

from .crypto import KeyResolver, artifact_digest, verify_artifact
from .errors import ErrorCode, GCPError


def _time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _constraint_map(grant: Mapping[str, Any]) -> Dict[str, Mapping[str, Any]]:
    return {constraint["name"]: constraint for constraint in grant.get("constraints", [])}


def _constraint_attenuates(child: Mapping[str, Any], parent: Mapping[str, Any]) -> bool:
    if child.get("operator") != parent.get("operator"):
        return False
    operator = parent["operator"]
    if operator == "equals":
        return child["value"] == parent["value"]
    if operator == "decimal_lte":
        return Decimal(child["value"]) <= Decimal(parent["value"])
    if operator == "set_subset":
        return set(child["value"]).issubset(parent["value"])
    raise GCPError(
        ErrorCode.UNSUPPORTED_SEMANTICS,
        "Unknown authority constraint operator",
        {"operator": operator},
    )


def _resource_contained(child: Mapping[str, str], parent: Mapping[str, str]) -> bool:
    if parent["match"] == "exact":
        return child["match"] == "exact" and child["uri"] == parent["uri"]
    if parent["match"] == "prefix":
        return child["uri"].startswith(parent["uri"])
    raise GCPError(ErrorCode.UNSUPPORTED_SEMANTICS, "Unknown resource match rule")


def _grant_contained(child: Mapping[str, Any], parent: Mapping[str, Any]) -> bool:
    if child["action"] != parent["action"] or not _resource_contained(child["resource"], parent["resource"]):
        return False
    child_constraints = _constraint_map(child)
    for name, parent_constraint in _constraint_map(parent).items():
        child_constraint = child_constraints.get(name)
        if child_constraint is None or not _constraint_attenuates(child_constraint, parent_constraint):
            return False
    return True


def _validate_authority(parent: Mapping[str, Any], child: Mapping[str, Any]) -> None:
    for child_grant in child["authority"]:
        if not any(_grant_contained(child_grant, parent_grant) for parent_grant in parent["authority"]):
            raise GCPError(
                ErrorCode.AUTHORITY_EXPANSION,
                "Child authority is not contained by parent authority",
                {"grant_id": child_grant["grant_id"]},
            )


def _validate_obligations(parent: Mapping[str, Any], child: Mapping[str, Any]) -> None:
    child_by_id = {item["obligation_id"]: item for item in child["obligations"]}
    for parent_obligation in parent["obligations"]:
        if not parent_obligation["mandatory"]:
            continue
        obligation_id = parent_obligation["obligation_id"]
        child_obligation = child_by_id.get(obligation_id)
        if child_obligation is None:
            raise GCPError(
                ErrorCode.OBLIGATION_REMOVED,
                "Inherited mandatory obligation is missing",
                {"obligation_id": obligation_id},
            )
        if child_obligation != parent_obligation:
            raise GCPError(
                ErrorCode.OBLIGATION_MODIFIED,
                "Inherited mandatory obligation was modified",
                {"obligation_id": obligation_id},
            )


def _budget_map(capsule: Mapping[str, Any]) -> Dict[str, Mapping[str, str]]:
    return {item["dimension"]: item for item in capsule["budgets"]}


def _validate_child_budget(parent: Mapping[str, Any], child: Mapping[str, Any]) -> None:
    parent_budgets = _budget_map(parent)
    for dimension, child_item in _budget_map(child).items():
        parent_item = parent_budgets.get(dimension)
        if parent_item is None:
            raise GCPError(
                ErrorCode.BUDGET_OVERALLOCATED,
                "Child allocates a budget dimension absent from parent",
                {"dimension": dimension},
            )
        if child_item["unit"] != parent_item["unit"]:
            raise GCPError(
                ErrorCode.BUDGET_UNIT_MISMATCH,
                "Child and parent budget units differ",
                {"dimension": dimension},
            )
        if Decimal(child_item["quantity"]) > Decimal(parent_item["quantity"]):
            raise GCPError(
                ErrorCode.BUDGET_OVERALLOCATED,
                "Child budget exceeds parent budget",
                {"dimension": dimension},
            )


def validate_delegation(
    parent: Mapping[str, Any],
    child: Mapping[str, Any],
    *,
    verified_ancestor_ids: Optional[Iterable[str]] = None,
) -> None:
    """Validate one ordinary parent-to-child transition.

    Aggregate sibling allocation is intentionally not checked here; it requires
    the stateful allocation authority specified separately in Milestone 3.
    """

    parent_ref = child.get("parent")
    if not isinstance(parent_ref, dict):
        raise GCPError(ErrorCode.PARENT_MISMATCH, "Derived capsule has no parent reference")
    if (
        child.get("kind") != "derived"
        or parent_ref.get("capsule_id") != parent.get("capsule_id")
        or parent_ref.get("task_id") != parent.get("task", {}).get("task_id")
        or parent_ref.get("digest") != artifact_digest(parent)
        or child.get("task", {}).get("workflow_id") != parent.get("task", {}).get("workflow_id")
    ):
        raise GCPError(ErrorCode.PARENT_MISMATCH, "Child does not bind the verified parent")

    ancestors: Set[str] = set(verified_ancestor_ids or ())
    if child["capsule_id"] == parent["capsule_id"] or child["capsule_id"] in ancestors:
        raise GCPError(ErrorCode.LINEAGE_CYCLE, "Capsule identifier repeats in lineage")

    parent_depth = parent["delegation_depth"]
    if parent_depth == 0 or child["delegation_depth"] > parent_depth - 1:
        raise GCPError(ErrorCode.DELEGATION_DEPTH_EXCEEDED, "Child exceeds remaining delegation depth")

    if (
        _time(child["validity"]["not_before"]) < _time(parent["validity"]["not_before"])
        or _time(child["validity"]["expires_at"]) > _time(parent["validity"]["expires_at"])
    ):
        raise GCPError(ErrorCode.TEMPORAL_EXPANSION, "Child validity expands parent validity")

    _validate_authority(parent, child)
    _validate_obligations(parent, child)
    _validate_child_budget(parent, child)


def validate_delegation_proof(
    proof: Mapping[str, Any],
    parent: Mapping[str, Any],
    child: Mapping[str, Any],
    resolver: KeyResolver,
) -> None:
    expected_parent = {
        "capsule_id": parent["capsule_id"],
        "task_id": parent["task"]["task_id"],
        "digest": artifact_digest(parent),
    }
    expected_child = {
        "capsule_id": child["capsule_id"],
        "task_id": child["task"]["task_id"],
        "digest": artifact_digest(child),
    }
    if (
        proof.get("parent_capsule") != expected_parent
        or proof.get("child_capsule") != expected_child
        or proof.get("delegator") != child.get("delegator")
        or proof.get("child_subject") != child.get("subject")
    ):
        raise GCPError(ErrorCode.INVALID_DELEGATION_PROOF, "Delegation proof does not bind this transition")
    try:
        verify_artifact(proof, resolver)
    except GCPError as exc:
        if exc.code in {ErrorCode.INVALID_SIGNATURE, ErrorCode.UNKNOWN_VERIFICATION_METHOD}:
            raise GCPError(ErrorCode.INVALID_DELEGATION_PROOF, "Delegation proof signature is invalid") from exc
        raise
