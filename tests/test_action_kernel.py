from copy import deepcopy
from datetime import datetime, timezone

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from gcp_reference import (
    ActionProposal,
    ActionState,
    CallablePolicyRuntime,
    CapsuleActionVerifier,
    GovernanceGraph,
    GovernedActionGateway,
    GraphNode,
    InMemorySupplierConnector,
    KeyResolver,
    PolicyEffect,
    PolicyEvaluation,
    PolicyLayer,
    RevocationEvaluator,
    StatusRecord,
    artifact_digest,
    sign_artifact,
)


NOW = datetime(2026, 8, 19, 8, 0, tzinfo=timezone.utc)
ISSUER = "https://governance.example.com/issuers/procurement"
ISSUER_METHOD = "https://governance.example.com/keys/procurement"


def unsigned_capsule():
    return {
        "gcp_version": "0.1",
        "kind": "root",
        "capsule_id": "urn:gcp:capsule:supplier-create",
        "revision": 0,
        "task": {
            "task_id": "urn:gcp:task:supplier-create",
            "workflow_id": "urn:gcp:workflow:supplier-onboarding",
            "purpose": "Create an approved supplier",
        },
        "issuer": ISSUER,
        "subject": "spiffe://example.com/agent/procurement",
        "authority": [{
            "grant_id": "urn:gcp:grant:supplier-create",
            "action": "supplier.create",
            "resource": {"match": "prefix", "uri": "urn:supplier:"},
        }],
        "obligations": [{
            "obligation_id": "urn:gcp:obligation:audit-supplier-create",
            "type": "https://gcp-protocol.dev/obligations/audit",
            "version": "0.1",
            "mandatory": True,
            "satisfaction_point": "before_action",
            "parameters": {"event": "supplier.create"},
            "source": {
                "issuer": ISSUER,
                "policy_ref": "https://governance.example.com/policies/supplier/v1",
                "policy_digest": "sha256:" + "a" * 64,
            },
        }],
        "budgets": [],
        "delegation_depth": 1,
        "validity": {
            "not_before": "2026-08-19T00:00:00Z",
            "expires_at": "2026-08-20T00:00:00Z",
            "freshness": {
                "profile": "online-strict",
                "status_endpoint": "https://governance.example.com/status",
            },
            "replay": {"mode": "multi-use", "max_uses": 10},
        },
        "sequence": 0,
    }


def signed_capsule(mutator=None):
    key = Ed25519PrivateKey.generate()
    value = unsigned_capsule()
    if mutator:
        mutator(value)
    signed = sign_artifact(value, key, ISSUER_METHOD, created="2026-08-19T00:00:00Z")
    return signed, key


def proposal(action="supplier.create", resource="urn:supplier:42"):
    return ActionProposal(
        "urn:gcp:action:signed-supplier-42",
        action,
        resource,
        "sha256:" + "b" * 64,
    )


def verifier(capsule, key, *, revoked=False, issuer_methods=None, obligation=True):
    def status(endpoint, digest):
        return StatusRecord(digest, NOW, revoked, authenticated=True)

    return CapsuleActionVerifier(
        capsule,
        presenter="spiffe://example.com/agent/procurement",
        now=lambda: NOW,
        resolver=KeyResolver({ISSUER_METHOD: key.public_key()}),
        authorized_issuers=issuer_methods or {ISSUER: (ISSUER_METHOD,)},
        revocation_evaluator=RevocationEvaluator(),
        status_provider=status,
        obligation_verifier=lambda item, action: obligation,
    )


def gateway(kernel, connector, policy_calls):
    policy = CallablePolicyRuntime(
        "local-policy",
        lambda item: policy_calls.append(item) or (
            PolicyEvaluation("urn:policy:supplier", "1", PolicyLayer.ORGANIZATIONAL,
                             PolicyEffect.ALLOW, "SUPPLIER_ALLOWED"),
        ),
    )
    return GovernedActionGateway(
        gateway_id="urn:gcp:gateway:signed-kernel",
        policy_runtime=policy,
        graph=GovernanceGraph([GraphNode("commit")], []),
        connector=connector,
        kernel_verifier=kernel,
        approval_verifier=lambda item: True,
        receipt_key=Ed25519PrivateKey.generate(),
        receipt_verification_method="https://gateway.example.com/keys/receipt",
    )


def test_signed_capsule_reaches_supplier_and_verification_controls_enter_receipt():
    capsule, key = signed_capsule()
    connector = InMemorySupplierConnector()
    policy_calls = []
    record = gateway(verifier(capsule, key), connector, policy_calls).execute(
        proposal(), conflict_node="commit"
    )
    assert record.state == ActionState.COMMITTED
    assert connector.commit_calls == 1
    assert len(policy_calls) == 1
    assert "GCP_CAPSULE_SIGNATURE_VERIFIED" in record.controls
    assert "GCP_REVOCATION_FRESHNESS_VERIFIED" in record.receipt["controls"]


def assert_rejected_before_policy_and_connector(kernel, expected_code):
    connector = InMemorySupplierConnector()
    policy_calls = []
    record = gateway(kernel, connector, policy_calls).execute(proposal(), conflict_node="commit")
    assert record.state == ActionState.REJECTED
    assert record.reason_codes == (expected_code,)
    assert connector.commit_calls == 0
    assert policy_calls == []


def test_expired_capsule_never_reaches_policy_or_connector():
    capsule, key = signed_capsule(lambda value: value["validity"].update(expires_at="2026-08-19T07:00:00Z"))
    assert_rejected_before_policy_and_connector(verifier(capsule, key), "GCP_CAPSULE_EXPIRED")


def test_revoked_capsule_never_reaches_policy_or_connector():
    capsule, key = signed_capsule()
    assert_rejected_before_policy_and_connector(verifier(capsule, key, revoked=True), "GCP_REVOKED")


def test_unauthorized_action_never_reaches_policy_or_connector():
    capsule, key = signed_capsule()
    kernel = verifier(capsule, key)
    connector = InMemorySupplierConnector()
    policy_calls = []
    record = gateway(kernel, connector, policy_calls).execute(
        proposal(action="supplier.delete"), conflict_node="commit"
    )
    assert record.state == ActionState.REJECTED
    assert record.reason_codes == ("GCP_ACTION_NOT_AUTHORIZED",)
    assert connector.commit_calls == 0
    assert policy_calls == []


def test_unsatisfied_mandatory_obligation_never_reaches_policy_or_connector():
    capsule, key = signed_capsule()
    assert_rejected_before_policy_and_connector(
        verifier(capsule, key, obligation=False), "GCP_OBLIGATION_UNSATISFIED"
    )


def test_untrusted_issuer_role_binding_fails_even_with_valid_signature():
    capsule, key = signed_capsule()
    assert_rejected_before_policy_and_connector(
        verifier(capsule, key, issuer_methods={ISSUER: ()}),
        "GCP_UNAUTHORIZED_CAPSULE_ISSUER",
    )


def test_capsule_mutation_after_signature_never_reaches_policy_or_connector():
    capsule, key = signed_capsule()
    mutated = deepcopy(capsule)
    mutated["authority"][0]["resource"]["uri"] = "urn:supplier:anything:"
    assert artifact_digest(mutated) != artifact_digest(capsule)
    assert_rejected_before_policy_and_connector(verifier(mutated, key), "GCP_INVALID_SIGNATURE")
