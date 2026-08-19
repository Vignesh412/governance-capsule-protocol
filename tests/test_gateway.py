from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import pytest

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
    SQLiteActionStore,
    SimulatedProcessCrash,
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


def gateway(runtime, *, approved=True, kernel=lambda proposal: (), connector=None, store=None, key=None, before_connector=None):
    key = key or Ed25519PrivateKey.generate()
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
        action_store=store,
        before_connector=before_connector,
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


def test_sqlite_restart_recovers_ambiguous_success_without_second_commit(tmp_path):
    database = tmp_path / "gateway.sqlite3"
    connector = InMemorySupplierConnector()
    connector.lose_next_response = True
    key = Ed25519PrivateKey.generate()
    runtime = policies(evaluation("allow", PolicyLayer.TASK, PolicyEffect.ALLOW))

    first_store = SQLiteActionStore(database)
    first_gateway, _, _ = gateway(runtime, connector=connector, store=first_store, key=key)
    unknown = first_gateway.execute(action(), conflict_node="commit")
    assert unknown.state == ActionState.COMMIT_OUTCOME_UNKNOWN
    first_store.close()

    second_store = SQLiteActionStore(database)
    restarted_gateway, _, _ = gateway(runtime, connector=connector, store=second_store, key=key)
    assert restarted_gateway.get(action().action_id).state == ActionState.COMMIT_OUTCOME_UNKNOWN
    committed = restarted_gateway.reconcile(action().action_id)
    retried = restarted_gateway.execute(action(), conflict_node="commit")
    assert committed.state == ActionState.COMMITTED
    assert retried.state == ActionState.COMMITTED
    assert connector.commit_calls == 1
    assert len(connector.suppliers) == 1
    second_store.close()


def test_sqlite_persists_action_id_binding_across_restart(tmp_path):
    database = tmp_path / "gateway.sqlite3"
    runtime = policies(evaluation("allow", PolicyLayer.TASK, PolicyEffect.ALLOW))
    connector = InMemorySupplierConnector()
    first_store = SQLiteActionStore(database)
    first, key, _ = gateway(runtime, connector=connector, store=first_store)
    first.execute(action(), conflict_node="commit")
    first_store.close()

    second_store = SQLiteActionStore(database)
    restarted, _, _ = gateway(runtime, connector=connector, store=second_store, key=key)
    try:
        restarted.execute(action(digest="sha256:" + "9" * 64), conflict_node="commit")
        assert False
    except GCPError as error:
        assert error.code == ErrorCode.ACTION_ID_CONFLICT
    second_store.close()


def test_restart_recovers_crash_before_connector_call(tmp_path):
    database = tmp_path / "gateway.sqlite3"
    runtime = policies(evaluation("allow", PolicyLayer.TASK, PolicyEffect.ALLOW))
    connector = InMemorySupplierConnector()
    key = Ed25519PrivateKey.generate()

    def crash_before_connector(proposal):
        raise SimulatedProcessCrash("before connector")

    first_store = SQLiteActionStore(database)
    first, _, _ = gateway(
        runtime, connector=connector, store=first_store, key=key,
        before_connector=crash_before_connector,
    )
    with pytest.raises(SimulatedProcessCrash):
        first.execute(action(), conflict_node="commit")
    assert first.get(action().action_id).state == ActionState.COMMITTING
    assert connector.commit_calls == 0
    first_store.close()

    second_store = SQLiteActionStore(database)
    restarted, _, _ = gateway(runtime, connector=connector, store=second_store, key=key)
    recovered = restarted.recover_pending()
    assert len(recovered) == 1
    assert recovered[0].state == ActionState.COMMITTED
    assert connector.commit_calls == 1
    assert len(connector.suppliers) == 1
    second_store.close()


def test_restart_recovers_crash_after_connector_commit(tmp_path):
    database = tmp_path / "gateway.sqlite3"
    runtime = policies(evaluation("allow", PolicyLayer.TASK, PolicyEffect.ALLOW))
    connector = InMemorySupplierConnector()
    connector.crash_after_next_commit = True
    key = Ed25519PrivateKey.generate()

    first_store = SQLiteActionStore(database)
    first, _, _ = gateway(runtime, connector=connector, store=first_store, key=key)
    with pytest.raises(SimulatedProcessCrash):
        first.execute(action(), conflict_node="commit")
    assert first.get(action().action_id).state == ActionState.COMMITTING
    assert connector.commit_calls == 1
    assert len(connector.suppliers) == 1
    first_store.close()

    second_store = SQLiteActionStore(database)
    restarted, _, _ = gateway(runtime, connector=connector, store=second_store, key=key)
    recovered = restarted.recover_pending()
    assert recovered[0].state == ActionState.COMMITTED
    assert connector.commit_calls == 1
    assert len(connector.suppliers) == 1
    second_store.close()
