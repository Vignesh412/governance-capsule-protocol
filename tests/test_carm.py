from decimal import Decimal

import pytest

from gcp_reference import (
    CARMConfig,
    CallablePolicyRuntime,
    ErrorCode,
    GCPError,
    GovernanceGraph,
    GraphEdge,
    GraphNode,
    JoinType,
    PolicyEffect,
    PolicyEvaluation,
    PolicyLayer,
    ResolutionMode,
    RuntimeDecision,
    fixed_priority,
    most_restrictive,
    resolve_carm,
)


def evaluation(policy_id, layer, effect):
    return PolicyEvaluation(policy_id, "1", layer, effect, "TEST_POLICY")


def supplier_graph(join_type=JoinType.AND):
    return GovernanceGraph(
        [
            GraphNode("intake"),
            GraphNode("compliance"),
            GraphNode("finance"),
            GraphNode("approval", join_type),
            GraphNode("create-vendor"),
        ],
        [
            GraphEdge("intake", "compliance"),
            GraphEdge("intake", "finance"),
            GraphEdge("compliance", "approval"),
            GraphEdge("finance", "approval"),
            GraphEdge("approval", "create-vendor"),
        ],
    )


def assert_code(code, callable_):
    with pytest.raises(GCPError) as caught:
        callable_()
    assert caught.value.code == code


def test_join_aware_reach_distinguishes_and_from_or():
    and_reach = supplier_graph(JoinType.AND).estimate_reach("intake")
    or_reach = supplier_graph(JoinType.OR).estimate_reach("intake")
    assert and_reach.score == Decimal("4")
    assert or_reach.score == Decimal("3.5")


def test_graph_digest_is_independent_of_input_order():
    first = supplier_graph()
    second = GovernanceGraph(
        reversed(
            [
                GraphNode("intake"), GraphNode("compliance"), GraphNode("finance"),
                GraphNode("approval", JoinType.AND), GraphNode("create-vendor"),
            ]
        ),
        reversed(
            [
                GraphEdge("intake", "compliance"), GraphEdge("intake", "finance"),
                GraphEdge("compliance", "approval"), GraphEdge("finance", "approval"),
                GraphEdge("approval", "create-vendor"),
            ]
        ),
    )
    assert first.digest == second.digest


def test_cycle_is_rejected():
    assert_code(
        ErrorCode.INVALID_GOVERNANCE_GRAPH,
        lambda: GovernanceGraph(
            [GraphNode("a"), GraphNode("b")],
            [GraphEdge("a", "b"), GraphEdge("b", "a")],
        ),
    )


def test_multi_parent_node_requires_explicit_join_semantics():
    assert_code(
        ErrorCode.INVALID_GOVERNANCE_GRAPH,
        lambda: GovernanceGraph(
            [GraphNode("a"), GraphNode("b"), GraphNode("c")],
            [GraphEdge("a", "c"), GraphEdge("b", "c")],
        ),
    )


def test_unknown_join_is_conservative_and_visible():
    estimate = supplier_graph(JoinType.UNKNOWN).estimate_reach("intake")
    assert estimate.score == Decimal("4")
    assert estimate.topology_confidence == Decimal("0.5")
    assert estimate.unknown_join_nodes == ("approval",)


def test_same_conflict_changes_mode_with_downstream_reach():
    policies = (
        evaluation("regulatory-continuity", PolicyLayer.REGULATORY, PolicyEffect.ALLOW),
        evaluation("organization-freeze", PolicyLayer.ORGANIZATIONAL, PolicyEffect.BLOCK),
    )
    graph = supplier_graph()
    upstream = resolve_carm(policies, graph, "intake")
    leaf = resolve_carm(policies, graph, "create-vendor")

    assert most_restrictive(policies) == RuntimeDecision.BLOCK
    assert fixed_priority(policies) == RuntimeDecision.ALLOW
    assert upstream.mode == ResolutionMode.ESCALATION_BOUNDARY
    assert upstream.decision == RuntimeDecision.APPROVAL_REQUIRED
    assert leaf.mode == ResolutionMode.PRIORITY_ENFORCEMENT
    assert leaf.decision == RuntimeDecision.ALLOW
    assert upstream.reach.graph_digest == leaf.reach.graph_digest


def test_outcome_aware_selector_reroutes_automated_block():
    policies = (
        evaluation("regulatory-block", PolicyLayer.REGULATORY, PolicyEffect.BLOCK),
        evaluation("organization-allow", PolicyLayer.ORGANIZATIONAL, PolicyEffect.ALLOW),
    )
    result = resolve_carm(policies, supplier_graph(), "create-vendor")
    assert result.mode == ResolutionMode.ESCALATION_BOUNDARY
    assert result.reason_codes == ("CARM_AUTOMATED_BLOCK_REROUTED",)


def test_low_severity_conflict_negotiates_relaxation():
    policies = (
        evaluation("organization-allow", PolicyLayer.ORGANIZATIONAL, PolicyEffect.ALLOW),
        evaluation("task-block", PolicyLayer.TASK, PolicyEffect.BLOCK),
    )
    result = resolve_carm(policies, supplier_graph(), "create-vendor")
    assert result.mode == ResolutionMode.NEGOTIATED_RELAXATION
    assert result.decision == RuntimeDecision.ALLOW


def test_topology_confidence_can_force_escalation():
    policies = (
        evaluation("organization-allow", PolicyLayer.ORGANIZATIONAL, PolicyEffect.ALLOW),
        evaluation("task-block", PolicyLayer.TASK, PolicyEffect.BLOCK),
    )
    result = resolve_carm(
        policies,
        supplier_graph(JoinType.UNKNOWN),
        "intake",
        config=CARMConfig(minimum_topology_confidence=Decimal("0.75")),
    )
    assert result.mode == ResolutionMode.ESCALATION_BOUNDARY
    assert result.reason_codes == ("CARM_TOPOLOGY_CONFIDENCE_INSUFFICIENT",)


def test_policy_runtime_adapter_rejects_duplicate_policy_versions():
    duplicate = evaluation("same-policy", PolicyLayer.TASK, PolicyEffect.ALLOW)
    runtime = CallablePolicyRuntime("test-runtime", lambda proposal: (duplicate, duplicate))
    assert runtime.runtime_id == "test-runtime"
    assert_code(
        ErrorCode.POLICY_EVALUATION_INVALID,
        lambda: runtime.evaluate(object()),
    )
