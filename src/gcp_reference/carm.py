"""Deterministic CARM baseline and comparison policies."""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from itertools import combinations
from typing import Iterable, Tuple

from .governance_graph import GovernanceGraph, ReachEstimate
from .policy import PolicyEffect, PolicyEvaluation


class ResolutionMode(str, Enum):
    NO_CONFLICT = "NO_CONFLICT"
    PRIORITY_ENFORCEMENT = "PRIORITY_ENFORCEMENT"
    NEGOTIATED_RELAXATION = "NEGOTIATED_RELAXATION"
    ESCALATION_BOUNDARY = "ESCALATION_BOUNDARY"


class RuntimeDecision(str, Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"


@dataclass(frozen=True)
class PolicyConflict:
    left: PolicyEvaluation
    right: PolicyEvaluation
    severity: int


@dataclass(frozen=True)
class CARMConfig:
    severity_threshold: int = 4
    reach_threshold: Decimal = Decimal("2")
    minimum_topology_confidence: Decimal = Decimal("0")
    prevent_automated_blocking: bool = True


@dataclass(frozen=True)
class Resolution:
    mode: ResolutionMode
    decision: RuntimeDecision
    severity: int
    reach: ReachEstimate
    conflicts: Tuple[PolicyConflict, ...]
    reason_codes: Tuple[str, ...]


def detect_conflicts(evaluations: Iterable[PolicyEvaluation]) -> Tuple[PolicyConflict, ...]:
    values = tuple(value for value in evaluations if value.effect != PolicyEffect.REQUIRE_APPROVAL)
    conflicts = []
    for left, right in combinations(values, 2):
        if left.effect == right.effect:
            continue
        conflicts.append(
            PolicyConflict(
                left=left,
                right=right,
                severity=left.layer.weight * right.layer.weight,
            )
        )
    return tuple(sorted(conflicts, key=lambda value: (value.left.policy_id, value.right.policy_id)))


def _priority_effect(conflicts: Tuple[PolicyConflict, ...]) -> PolicyEffect:
    policies = {}
    for conflict in conflicts:
        policies[(conflict.left.policy_id, conflict.left.policy_version)] = conflict.left
        policies[(conflict.right.policy_id, conflict.right.policy_version)] = conflict.right
    ordered = sorted(
        policies.values(),
        key=lambda value: (-value.layer.weight, value.policy_id, value.policy_version),
    )
    return ordered[0].effect


def resolve_carm(
    evaluations: Iterable[PolicyEvaluation],
    graph: GovernanceGraph,
    conflict_node: str,
    *,
    config: CARMConfig = CARMConfig(),
) -> Resolution:
    values = tuple(evaluations)
    reach = graph.estimate_reach(conflict_node)
    if any(value.effect == PolicyEffect.REQUIRE_APPROVAL for value in values):
        return Resolution(
            ResolutionMode.ESCALATION_BOUNDARY,
            RuntimeDecision.APPROVAL_REQUIRED,
            0,
            reach,
            (),
            ("CARM_UPSTREAM_APPROVAL_REQUIRED",),
        )
    conflicts = detect_conflicts(values)
    if not conflicts:
        decision = (
            RuntimeDecision.BLOCK
            if any(value.effect == PolicyEffect.BLOCK for value in values)
            else RuntimeDecision.ALLOW
        )
        return Resolution(
            ResolutionMode.NO_CONFLICT,
            decision,
            0,
            reach,
            (),
            ("CARM_NO_POLICY_CONFLICT",),
        )

    severity = max(conflict.severity for conflict in conflicts)
    if reach.topology_confidence < config.minimum_topology_confidence:
        return Resolution(
            ResolutionMode.ESCALATION_BOUNDARY,
            RuntimeDecision.APPROVAL_REQUIRED,
            severity,
            reach,
            conflicts,
            ("CARM_TOPOLOGY_CONFIDENCE_INSUFFICIENT",),
        )
    if severity >= config.severity_threshold and reach.score >= config.reach_threshold:
        return Resolution(
            ResolutionMode.ESCALATION_BOUNDARY,
            RuntimeDecision.APPROVAL_REQUIRED,
            severity,
            reach,
            conflicts,
            ("CARM_HIGH_SEVERITY_HIGH_REACH",),
        )
    if severity >= config.severity_threshold:
        effect = _priority_effect(conflicts)
        if effect == PolicyEffect.BLOCK and config.prevent_automated_blocking:
            return Resolution(
                ResolutionMode.ESCALATION_BOUNDARY,
                RuntimeDecision.APPROVAL_REQUIRED,
                severity,
                reach,
                conflicts,
                ("CARM_AUTOMATED_BLOCK_REROUTED",),
            )
        return Resolution(
            ResolutionMode.PRIORITY_ENFORCEMENT,
            RuntimeDecision(effect.value),
            severity,
            reach,
            conflicts,
            ("CARM_HIGH_SEVERITY_LOW_REACH",),
        )
    return Resolution(
        ResolutionMode.NEGOTIATED_RELAXATION,
        RuntimeDecision.ALLOW,
        severity,
        reach,
        conflicts,
        ("CARM_LOW_SEVERITY_RELAXATION",),
    )


def most_restrictive(evaluations: Iterable[PolicyEvaluation]) -> RuntimeDecision:
    return (
        RuntimeDecision.BLOCK
        if any(value.effect == PolicyEffect.BLOCK for value in evaluations)
        else RuntimeDecision.ALLOW
    )


def fixed_priority(evaluations: Iterable[PolicyEvaluation]) -> RuntimeDecision:
    values = tuple(evaluations)
    if not values:
        return RuntimeDecision.ALLOW
    selected = sorted(
        values,
        key=lambda value: (-value.layer.weight, value.policy_id, value.policy_version),
    )[0]
    return RuntimeDecision(selected.effect.value)
