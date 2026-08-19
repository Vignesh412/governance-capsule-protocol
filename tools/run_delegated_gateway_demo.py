#!/usr/bin/env python3
"""Execute a supplier action through one signed agent-to-agent delegation."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gcp_reference import (  # noqa: E402
    ActionProposal, CallablePolicyRuntime, DelegatedCapsuleActionVerifier,
    DelegationTransition, GovernanceGraph, GovernedActionGateway, GraphNode,
    InMemorySupplierConnector, KeyResolver, PolicyEffect, PolicyEvaluation,
    PolicyLayer, StatusRecord, artifact_digest, sign_artifact,
)


def main():
    issuer = "https://governance.example.com/issuers/procurement"
    issuer_method = "https://governance.example.com/keys/procurement-demo"
    delegator = "spiffe://example.com/agent/intake"
    delegator_method = "https://governance.example.com/keys/intake-demo"
    child_subject = "spiffe://example.com/agent/supplier-operations"
    issuer_key, delegator_key = Ed25519PrivateKey.generate(), Ed25519PrivateKey.generate()
    validity = {
        "not_before": "2026-08-19T00:00:00Z", "expires_at": "2026-08-20T00:00:00Z",
        "freshness": {"profile": "online-strict", "status_endpoint": "https://governance.example.com/status"},
        "replay": {"mode": "multi-use", "max_uses": 5},
    }
    root = sign_artifact({
        "gcp_version": "0.1", "kind": "root", "capsule_id": "urn:gcp:capsule:demo-root", "revision": 0,
        "task": {"task_id": "urn:gcp:task:onboarding", "workflow_id": "urn:gcp:workflow:supplier-onboarding", "purpose": "Onboard supplier"},
        "issuer": issuer, "subject": delegator,
        "authority": [{"grant_id": "urn:gcp:grant:root-create", "action": "supplier.create", "resource": {"match": "prefix", "uri": "urn:supplier:"}}],
        "obligations": [], "budgets": [{"dimension": "cost", "quantity": "10", "unit": "USD"}],
        "delegation_depth": 2, "validity": validity, "sequence": 0,
    }, issuer_key, issuer_method)
    child = sign_artifact({
        "gcp_version": "0.1", "kind": "derived", "capsule_id": "urn:gcp:capsule:demo-child", "revision": 0,
        "task": {"task_id": "urn:gcp:task:create-supplier", "workflow_id": "urn:gcp:workflow:supplier-onboarding", "purpose": "Create supplier 42"},
        "issuer": issuer, "delegator": delegator, "subject": child_subject,
        "parent": {"capsule_id": root["capsule_id"], "task_id": root["task"]["task_id"], "digest": artifact_digest(root)},
        "authority": [{"grant_id": "urn:gcp:grant:child-create", "action": "supplier.create", "resource": {"match": "exact", "uri": "urn:supplier:42"}}],
        "obligations": [], "budgets": [{"dimension": "cost", "quantity": "2", "unit": "USD"}],
        "delegation_depth": 1, "validity": validity, "sequence": 0,
    }, issuer_key, issuer_method)
    proof = sign_artifact({
        "gcp_version": "0.1", "proof_id": "urn:gcp:delegation-proof:demo",
        "parent_capsule": {"capsule_id": root["capsule_id"], "task_id": root["task"]["task_id"], "digest": artifact_digest(root)},
        "child_capsule": {"capsule_id": child["capsule_id"], "task_id": child["task"]["task_id"], "digest": artifact_digest(child)},
        "delegator": delegator, "child_subject": child_subject, "issued_at": "2026-08-19T00:05:00Z",
    }, delegator_key, delegator_method, proof_purpose="authentication")
    resolver = KeyResolver({issuer_method: issuer_key.public_key(), delegator_method: delegator_key.public_key()})
    now = datetime(2026, 8, 19, 9, 0, tzinfo=timezone.utc)
    kernel = DelegatedCapsuleActionVerifier(
        [DelegationTransition(root, child, proof)], presenter=child_subject, now=lambda: now,
        resolver=resolver, authorized_issuers={issuer: (issuer_method,)},
        authorized_delegators={delegator: (delegator_method,)},
        status_provider=lambda endpoint, digest: StatusRecord(digest, now, False, authenticated=True),
    )
    connector = InMemorySupplierConnector()
    gateway = GovernedActionGateway(
        gateway_id="urn:gcp:gateway:delegated-demo",
        policy_runtime=CallablePolicyRuntime("demo-policy", lambda proposal: (
            PolicyEvaluation("urn:policy:supplier", "1", PolicyLayer.ORGANIZATIONAL, PolicyEffect.ALLOW, "ALLOW"),
        )),
        graph=GovernanceGraph([GraphNode("commit")], []), connector=connector,
        kernel_verifier=kernel, approval_verifier=lambda proposal: True,
        receipt_key=Ed25519PrivateKey.generate(), receipt_verification_method="https://gateway.example.com/keys/demo",
    )
    record = gateway.execute(ActionProposal(
        "urn:gcp:action:delegated-demo", "supplier.create", "urn:supplier:42", "sha256:" + "d" * 64,
    ), conflict_node="commit")
    print(json.dumps({
        "state": record.state.value, "decision": record.decision.value,
        "delegation_hops": 1, "root_authority": "supplier.create urn:supplier:*",
        "child_authority": "supplier.create urn:supplier:42",
        "lineage_verified": "GCP_DELEGATION_LINEAGE_VERIFIED" in record.controls,
        "connector_commit_calls": connector.commit_calls, "suppliers_created": len(connector.suppliers),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
