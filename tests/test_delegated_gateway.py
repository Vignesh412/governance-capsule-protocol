from copy import deepcopy
from datetime import datetime, timezone

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from gcp_reference import (
    ActionProposal, ActionState, CallablePolicyRuntime, DelegatedCapsuleActionVerifier,
    DelegationTransition, GovernanceGraph, GovernedActionGateway, GraphNode,
    InMemorySupplierConnector, KeyResolver, PolicyEffect, PolicyEvaluation,
    PolicyLayer, StatusRecord, artifact_digest, sign_artifact,
)


NOW = datetime(2026, 8, 19, 9, 0, tzinfo=timezone.utc)
ISSUER = "https://governance.example.com/issuers/procurement"
ISSUER_METHOD = "https://governance.example.com/keys/procurement"
DELEGATOR = "spiffe://example.com/agent/intake"
DELEGATOR_METHOD = "https://governance.example.com/keys/intake"
CHILD = "spiffe://example.com/agent/supplier-operations"


def artifacts(child_action="supplier.create", child_resource="urn:supplier:42"):
    issuer_key = Ed25519PrivateKey.generate()
    delegator_key = Ed25519PrivateKey.generate()
    obligation = {
        "obligation_id": "urn:gcp:obligation:audit", "type": "https://gcp-protocol.dev/obligations/audit",
        "version": "0.1", "mandatory": True, "satisfaction_point": "before_action",
        "parameters": {"event": "supplier.create"},
        "source": {"issuer": ISSUER, "policy_ref": "https://governance.example.com/policies/supplier/v1", "policy_digest": "sha256:" + "a" * 64},
    }
    validity = {
        "not_before": "2026-08-19T00:00:00Z", "expires_at": "2026-08-20T00:00:00Z",
        "freshness": {"profile": "online-strict", "status_endpoint": "https://governance.example.com/status"},
        "replay": {"mode": "multi-use", "max_uses": 10},
    }
    root = sign_artifact({
        "gcp_version": "0.1", "kind": "root", "capsule_id": "urn:gcp:capsule:root-delegation", "revision": 0,
        "task": {"task_id": "urn:gcp:task:supplier-onboarding", "workflow_id": "urn:gcp:workflow:supplier-onboarding", "purpose": "Onboard supplier"},
        "issuer": ISSUER, "subject": DELEGATOR,
        "authority": [{"grant_id": "urn:gcp:grant:root-create", "action": "supplier.create", "resource": {"match": "prefix", "uri": "urn:supplier:"}}],
        "obligations": [obligation], "budgets": [{"dimension": "cost", "quantity": "10", "unit": "USD"}],
        "delegation_depth": 2, "validity": validity, "sequence": 0,
    }, issuer_key, ISSUER_METHOD, created="2026-08-19T00:00:00Z")
    child_unsigned = {
        "gcp_version": "0.1", "kind": "derived", "capsule_id": "urn:gcp:capsule:child-delegation", "revision": 0,
        "task": {"task_id": "urn:gcp:task:supplier-create", "workflow_id": "urn:gcp:workflow:supplier-onboarding", "purpose": "Create supplier"},
        "issuer": ISSUER, "delegator": DELEGATOR, "subject": CHILD,
        "parent": {"capsule_id": root["capsule_id"], "task_id": root["task"]["task_id"], "digest": artifact_digest(root)},
        "authority": [{"grant_id": "urn:gcp:grant:child-create", "action": child_action, "resource": {"match": "exact", "uri": child_resource}}],
        "obligations": [obligation], "budgets": [{"dimension": "cost", "quantity": "2", "unit": "USD"}],
        "delegation_depth": 1, "validity": validity, "sequence": 0,
    }
    child = sign_artifact(child_unsigned, issuer_key, ISSUER_METHOD, created="2026-08-19T00:05:00Z")
    proof = sign_artifact({
        "gcp_version": "0.1", "proof_id": "urn:gcp:delegation-proof:supplier-create",
        "parent_capsule": {"capsule_id": root["capsule_id"], "task_id": root["task"]["task_id"], "digest": artifact_digest(root)},
        "child_capsule": {"capsule_id": child["capsule_id"], "task_id": child["task"]["task_id"], "digest": artifact_digest(child)},
        "delegator": DELEGATOR, "child_subject": CHILD, "issued_at": "2026-08-19T00:05:00Z",
    }, delegator_key, DELEGATOR_METHOD, created="2026-08-19T00:05:00Z", proof_purpose="authentication")
    resolver = KeyResolver({ISSUER_METHOD: issuer_key.public_key(), DELEGATOR_METHOD: delegator_key.public_key()})
    return root, child, proof, resolver, issuer_key, delegator_key


def verifier(root, child, proof, resolver, *, revoked_root=False):
    root_digest = artifact_digest(root)

    def status(endpoint, digest):
        return StatusRecord(digest, NOW, digest == root_digest and revoked_root,
                            cascade=digest == root_digest and revoked_root, authenticated=True)

    return DelegatedCapsuleActionVerifier(
        [DelegationTransition(root, child, proof)], presenter=CHILD, now=lambda: NOW,
        resolver=resolver, authorized_issuers={ISSUER: (ISSUER_METHOD,)},
        authorized_delegators={DELEGATOR: (DELEGATOR_METHOD,)}, status_provider=status,
        obligation_verifier=lambda obligation, proposal: True,
    )


def execute(kernel):
    connector = InMemorySupplierConnector()
    policy_calls = []
    policy = CallablePolicyRuntime("policy", lambda proposal: policy_calls.append(proposal) or (
        PolicyEvaluation("urn:policy:supplier", "1", PolicyLayer.ORGANIZATIONAL, PolicyEffect.ALLOW, "ALLOW"),
    ))
    gateway = GovernedActionGateway(
        gateway_id="urn:gcp:gateway:delegation", policy_runtime=policy,
        graph=GovernanceGraph([GraphNode("commit")], []), connector=connector,
        kernel_verifier=kernel, approval_verifier=lambda proposal: True,
        receipt_key=Ed25519PrivateKey.generate(), receipt_verification_method="https://gateway.example.com/keys/receipt",
    )
    record = gateway.execute(ActionProposal(
        "urn:gcp:action:delegated-create", "supplier.create", "urn:supplier:42", "sha256:" + "c" * 64,
    ), conflict_node="commit")
    return record, connector, policy_calls


def test_delegated_leaf_action_commits_with_lineage_receipt_control():
    root, child, proof, resolver, _, _ = artifacts()
    record, connector, policy_calls = execute(verifier(root, child, proof, resolver))
    assert record.state == ActionState.COMMITTED
    assert connector.commit_calls == 1
    assert len(policy_calls) == 1
    assert "GCP_DELEGATION_LINEAGE_VERIFIED" in record.receipt["controls"]


def assert_lineage_rejected(kernel, code):
    record, connector, policy_calls = execute(kernel)
    assert record.state == ActionState.REJECTED
    assert record.reason_codes == (code,)
    assert connector.commit_calls == 0
    assert policy_calls == []


def test_authority_expansion_in_child_is_rejected_before_policy():
    root, _, _, resolver, issuer_key, delegator_key = artifacts()
    _, expanded, expanded_proof, _, _, _ = artifacts("supplier.delete", "urn:supplier:42")
    # Rebind a freshly signed expanded child to the actual root.
    child_unsigned = deepcopy(expanded)
    child_unsigned.pop("proof")
    child_unsigned["parent"] = {"capsule_id": root["capsule_id"], "task_id": root["task"]["task_id"], "digest": artifact_digest(root)}
    child = sign_artifact(child_unsigned, issuer_key, ISSUER_METHOD)
    proof_unsigned = deepcopy(expanded_proof)
    proof_unsigned.pop("proof")
    proof_unsigned["parent_capsule"] = {"capsule_id": root["capsule_id"], "task_id": root["task"]["task_id"], "digest": artifact_digest(root)}
    proof_unsigned["child_capsule"] = {"capsule_id": child["capsule_id"], "task_id": child["task"]["task_id"], "digest": artifact_digest(child)}
    proof = sign_artifact(proof_unsigned, delegator_key, DELEGATOR_METHOD, proof_purpose="authentication")
    resolver = KeyResolver({ISSUER_METHOD: issuer_key.public_key(), DELEGATOR_METHOD: delegator_key.public_key()})
    assert_lineage_rejected(verifier(root, child, proof, resolver), "GCP_AUTHORITY_EXPANSION")


def test_tampered_delegation_proof_is_rejected_before_policy():
    root, child, proof, resolver, _, _ = artifacts()
    tampered = deepcopy(proof)
    tampered["child_subject"] = "spiffe://example.com/agent/attacker"
    assert_lineage_rejected(verifier(root, child, tampered, resolver), "GCP_INVALID_DELEGATION_PROOF")


def test_cascading_root_revocation_stops_leaf_action():
    root, child, proof, resolver, _, _ = artifacts()
    assert_lineage_rejected(verifier(root, child, proof, resolver, revoked_root=True), "GCP_REVOKED")
