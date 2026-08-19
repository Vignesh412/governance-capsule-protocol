import asyncio
from copy import deepcopy
from datetime import datetime, timezone

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from demo.scenarios import (
    CHILD,
    DELEGATOR,
    DELEGATOR_METHOD,
    ISSUER,
    ISSUER_METHOD,
    _artifacts,
    _gateway,
    _proof,
    _resign_child,
)
from gcp_reference import (
    ActionProposal,
    DelegationTransition,
    FrameworkIdentity,
    GoogleADKGovernanceBoundary,
    InMemorySupplierConnector,
    OpenAIGovernanceHandoffAdapter,
    StatusRecord,
    artifact_digest,
    build_google_adk_before_tool_callback,
    build_openai_on_handoff,
)


NOW = datetime(2026, 8, 19, 9, 0, tzinfo=timezone.utc)
OPENAI_RUNTIME = "urn:runtime:openai:procurement"
ADK_RUNTIME = "urn:runtime:google-adk:supplier-operations"
TRANSPORT_METHOD = "https://governance.example.com/keys/openai-transport"


def system(*, child_updates=None, revoked=False):
    root, child, _, issuer_key, delegator_key = _artifacts()
    if child_updates:
        child = _resign_child(root, child, issuer_key, **child_updates)
    proof = _proof(root, child, delegator_key)
    transport_key = Ed25519PrivateKey.generate()
    from gcp_reference import KeyResolver
    resolver = KeyResolver({
        ISSUER_METHOD: issuer_key.public_key(),
        DELEGATOR_METHOD: delegator_key.public_key(),
        TRANSPORT_METHOD: transport_key.public_key(),
    })
    destination = FrameworkIdentity("google-adk-python", ADK_RUNTIME)
    source = OpenAIGovernanceHandoffAdapter(
        runtime_id=OPENAI_RUNTIME, destination=destination,
        signing_key=transport_key, verification_method=TRANSPORT_METHOD)
    proposal = ActionProposal(
        "urn:gcp:action:cross-framework", "supplier.create", "urn:supplier:42",
        "sha256:" + "9" * 64, {"supplier_name": "Atlas Components"})
    envelope = source.export(
        transport_id="urn:gcp:transport:openai-to-adk",
        proposal=proposal, transitions=[DelegationTransition(root, child, proof)],
        created_at="2026-08-19T08:58:00Z", expires_at="2026-08-19T09:08:00Z",
        nonce="urn:gcp:nonce:cross-framework")
    root_digest = artifact_digest(root)
    boundary = GoogleADKGovernanceBoundary(
        runtime_id=ADK_RUNTIME, presenter=CHILD, now=lambda: NOW, resolver=resolver,
        authorized_transport_sources={OPENAI_RUNTIME: (TRANSPORT_METHOD,)},
        authorized_issuers={ISSUER: (ISSUER_METHOD,)},
        authorized_delegators={DELEGATOR: (DELEGATOR_METHOD,)},
        status_provider=lambda endpoint, digest: StatusRecord(
            digest, NOW, revoked and digest == root_digest,
            cascade=revoked and digest == root_digest, authenticated=True),
        obligation_verifier=lambda obligation, action: True)
    return source, boundary, envelope, proposal


def test_openai_to_google_adk_transport_commits_once_with_cross_framework_evidence():
    _, boundary, envelope, proposal = system()
    accepted = boundary.accept(envelope)
    connector = InMemorySupplierConnector()
    record = _gateway(accepted.kernel_verifier, connector).execute(proposal, conflict_node="commit")
    assert record.state.value == "COMMITTED"
    assert connector.commit_calls == 1
    assert "GCP_SOURCE_OPENAI_HANDOFF_VERIFIED" in record.controls
    assert "GCP_DESTINATION_GOOGLE_ADK_BOUNDARY_VERIFIED" in record.controls
    assert "GCP_DELEGATION_LINEAGE_VERIFIED" in record.controls


def test_tampered_transport_is_rejected_before_receiving_tool_or_connector():
    _, boundary, envelope, _ = system()
    tampered = deepcopy(envelope)
    tampered["proposal"]["resource"] = "urn:supplier:attacker"
    connector = InMemorySupplierConnector()
    try:
        boundary.accept(tampered)
    except Exception as error:
        assert getattr(error, "code").value == "GCP_INVALID_SIGNATURE"
    else:
        raise AssertionError("tampered transport accepted")
    assert connector.commit_calls == 0


def test_transport_nonce_replay_is_rejected():
    _, boundary, envelope, _ = system()
    boundary.accept(envelope)
    try:
        boundary.accept(envelope)
    except Exception as error:
        assert getattr(error, "code").value == "GCP_REPLAY_DETECTED"
    else:
        raise AssertionError("transport replay accepted")


def test_authority_expansion_crosses_transport_but_fails_before_connector():
    expanded = [{
        "grant_id": "urn:gcp:grant:child-delete", "action": "supplier.delete",
        "resource": {"match": "exact", "uri": "urn:supplier:42"},
    }]
    _, boundary, envelope, proposal = system(child_updates={"authority": expanded})
    accepted = boundary.accept(envelope)
    connector = InMemorySupplierConnector()
    record = _gateway(accepted.kernel_verifier, connector).execute(proposal, conflict_node="commit")
    assert record.state.value == "REJECTED"
    assert record.reason_codes == ("GCP_AUTHORITY_EXPANSION",)
    assert connector.commit_calls == 0


def test_cascading_revocation_blocks_cross_framework_descendant():
    _, boundary, envelope, proposal = system(revoked=True)
    accepted = boundary.accept(envelope)
    connector = InMemorySupplierConnector()
    record = _gateway(accepted.kernel_verifier, connector).execute(proposal, conflict_node="commit")
    assert record.reason_codes == ("GCP_REVOKED",)
    assert connector.commit_calls == 0


def test_framework_callback_shapes_keep_governance_in_application_state():
    source, boundary, envelope, proposal = system()

    class Wrapper:
        context = {}

    build_openai_on_handoff(source, envelope)(Wrapper())
    assert Wrapper.context["governance_transport"] is envelope

    class ToolContext:
        state = {"gcp_transport": envelope}

    connector = InMemorySupplierConnector()

    def governed_executor(accepted, transported_proposal):
        record = _gateway(accepted.kernel_verifier, connector).execute(
            transported_proposal, conflict_node="commit")
        return {"status": "committed", "state": record.state.value}

    callback = build_google_adk_before_tool_callback(boundary, governed_executor)
    result = asyncio.run(callback(None, {
        "action_id": proposal.action_id, "action": proposal.action,
        "resource": proposal.resource, "parameters_digest": proposal.parameters_digest,
        "metadata": dict(proposal.metadata),
    }, ToolContext()))
    assert result == {"status": "committed", "state": "COMMITTED"}
    assert connector.commit_calls == 1
    assert ToolContext.state["gcp_transport_digest"].startswith("sha256:")


def test_adk_callback_fails_closed_without_governed_gateway_executor():
    _, boundary, envelope, proposal = system()

    class ToolContext:
        state = {"gcp_transport": envelope}

    callback = build_google_adk_before_tool_callback(boundary)
    result = asyncio.run(callback(None, {
        "action_id": proposal.action_id, "action": proposal.action,
        "resource": proposal.resource, "parameters_digest": proposal.parameters_digest,
        "metadata": dict(proposal.metadata),
    }, ToolContext()))
    assert result == {"status": "blocked", "reason_code": "GCP_GATEWAY_EXECUTOR_REQUIRED"}
