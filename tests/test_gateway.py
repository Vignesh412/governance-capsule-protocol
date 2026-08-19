from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from gcp_reference import (
    ActionProposal,
    ActionState,
    CallablePolicyRuntime,
    ErrorCode,
    GCPError,
    GovernanceGraph,
    GovernedActionGateway,
    GraphEdge,
    GraphNode,
    InMemorySupplierConnector,
    JoinType,
    KeyResolver,
    PolicyEffect,
    PolicyEvaluation,
    PolicyLayer,
    verify_artifact,
)


def graph():
    return GovernanceGraph(
        [GraphNode("intake"), GraphNode("compliance"), GraphNode("finance"), GraphNode("approval", JoinType.AND), GraphNode("commit")],
        [GraphEdge("intake", "compliance"), GraphEdge("intake", "finance"), GraphEdge("compliance", "approval"), GraphEdge("finance", "approval"), GraphEdge("approval", "commit")],
    )


def action(action_id="urn:gcp:action:1", digest="sha256:" + "1" * 64):
    return ActionProposal(action_id, "supplier.create", "urn:supplier:42", digest)


def policies(*values):
    return CallablePolicyRuntime("test-policy", lambda proposal: values)


def evaluation(policy_id, layer, effect, controls=()):
    return PolicyEvaluation(policy_id, "1", layer, effect, "TEST", "runtime", effect.value.lower(), controls)


def gateway(runtime, *, approved=True, kernel=lambda proposal: (), connector=None):
    key = Ed25519PrivateKey.generate()
    method = "https://gateway.example/keys/receipt"
    instance = GovernedActionGateway(
        gateway_id="urn:gcp:gateway:test",
        policy_runtime=runtime,
        graph=graph(),
        connector=connector or InMemorySupplierConnector(),
        kernel_verifier=kernel,
        approval_verifier=lambda proposal: approved,
        receipt_key=key,
        receipt_verification_method=method,
    )
    return instance, key, method


def test_commits_supplier_and_signs_bound_receipt():
    connector = InMemorySupplierConnector()
    instance, key, method = gateway(
        policies(evaluation("allow", PolicyLayer.ORGANIZATIONAL, PolicyEffect.ALLOW)),
        connector=connector,
    )
    record = instance.execute(action(), conflict_node="commit")
    assert record.state == ActionState.COMMITTED
    assert connector.commit_calls == 1
    assert record.result_digest
    verify_artifact(record.receipt, KeyResolver({method: key.public_key()}))
    assert record.receipt["proposal_digest"] == record.proposal_digest
    assert record.receipt["graph_digest"] == graph().digest


def test_retry_is_idempotent_and_does_not_call_connector_twice():
    connector = InMemorySupplierConnector()
    instance, _, _ = gateway(
        policies(evaluation("allow", PolicyLayer.TASK, PolicyEffect.ALLOW)),
        connector=connector,
    )
    first = instance.execute(action(), conflict_node="commit")
    second = instance.execute(action(), conflict_node="commit")
    assert second == first
    assert connector.commit_calls == 1


def test_action_id_cannot_be_rebound_to_different_proposal():
    instance, _, _ = gateway(policies(evaluation("allow", PolicyLayer.TASK, PolicyEffect.ALLOW)))
    instance.execute(action(), conflict_node="commit")
    try:
        instance.execute(action(digest="sha256:" + "2" * 64), conflict_node="commit")
        assert False
    except GCPError as error:
        assert error.code == ErrorCode.ACTION_ID_CONFLICT


def test_kernel_failure_short_circuits_policy_and_connector():
    calls = []
    connector = InMemorySupplierConnector()
    runtime = CallablePolicyRuntime("never", lambda proposal: calls.append(proposal) or ())

    def reject(proposal):
        raise GCPError(ErrorCode.REVOKED, "revoked")

    instance, _, _ = gateway(runtime, kernel=reject, connector=connector)
    record = instance.execute(action(), conflict_node="commit")
    assert record.state == ActionState.REJECTED
    assert record.reason_codes == ("GCP_REVOKED",)
    assert calls == []
    assert connector.commit_calls == 0


def test_high_reach_conflict_waits_for_approval_without_committing():
    runtime = policies(
        evaluation("regulatory", PolicyLayer.REGULATORY, PolicyEffect.ALLOW),
        evaluation("organization", PolicyLayer.ORGANIZATIONAL, PolicyEffect.BLOCK),
    )
    connector = InMemorySupplierConnector()
    instance, _, _ = gateway(runtime, approved=False, connector=connector)
    record = instance.execute(action(), conflict_node="intake")
    assert record.state == ActionState.APPROVAL_REQUIRED
    assert connector.commit_calls == 0


def test_acs_style_controls_survive_into_commit_receipt():
    runtime = policies(
        evaluation("transform", PolicyLayer.ORGANIZATIONAL, PolicyEffect.ALLOW, ("ACS_APPLY_TRANSFORM",))
    )
    instance, _, _ = gateway(runtime)
    record = instance.execute(action(), conflict_node="commit")
    assert record.controls == ("ACS_APPLY_TRANSFORM",)
    assert record.receipt["controls"] == ["ACS_APPLY_TRANSFORM"]


def test_ambiguous_success_is_reconciled_without_second_commit():
    connector = InMemorySupplierConnector()
    connector.lose_next_response = True
    instance, _, _ = gateway(
        policies(evaluation("allow", PolicyLayer.TASK, PolicyEffect.ALLOW)),
        connector=connector,
    )
    unknown = instance.execute(action(), conflict_node="commit")
    assert unknown.state == ActionState.COMMIT_OUTCOME_UNKNOWN
    assert connector.commit_calls == 1
    committed = instance.reconcile(action().action_id)
    assert committed.state == ActionState.COMMITTED
    assert connector.commit_calls == 1
    assert committed.result_digest
