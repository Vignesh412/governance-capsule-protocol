#!/usr/bin/env python3
"""Execute supplier creation using a real signed Governance Capsule."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gcp_reference import (  # noqa: E402
    ActionProposal, CallablePolicyRuntime, CapsuleActionVerifier, GovernanceGraph,
    GovernedActionGateway, GraphNode, InMemorySupplierConnector, KeyResolver,
    PolicyEffect, PolicyEvaluation, PolicyLayer, StatusRecord, sign_artifact,
)


def main():
    issuer = "https://governance.example.com/issuers/procurement"
    method = "https://governance.example.com/keys/procurement-demo"
    issuer_key = Ed25519PrivateKey.generate()
    capsule = sign_artifact({
        "gcp_version": "0.1", "kind": "root",
        "capsule_id": "urn:gcp:capsule:demo-supplier", "revision": 0,
        "task": {"task_id": "urn:gcp:task:demo-supplier", "workflow_id": "urn:gcp:workflow:supplier-onboarding", "purpose": "Create approved supplier"},
        "issuer": issuer,
        "subject": "spiffe://example.com/agent/procurement",
        "authority": [{"grant_id": "urn:gcp:grant:supplier-create", "action": "supplier.create", "resource": {"match": "prefix", "uri": "urn:supplier:"}}],
        "obligations": [{
            "obligation_id": "urn:gcp:obligation:audit", "type": "https://gcp-protocol.dev/obligations/audit",
            "version": "0.1", "mandatory": True, "satisfaction_point": "before_action",
            "parameters": {"event": "supplier.create"},
            "source": {"issuer": issuer, "policy_ref": "https://governance.example.com/policies/supplier/v1", "policy_digest": "sha256:" + "a" * 64},
        }],
        "budgets": [], "delegation_depth": 1,
        "validity": {
            "not_before": "2026-08-19T00:00:00Z", "expires_at": "2026-08-20T00:00:00Z",
            "freshness": {"profile": "online-strict", "status_endpoint": "https://governance.example.com/status"},
            "replay": {"mode": "multi-use", "max_uses": 5},
        },
        "sequence": 0,
    }, issuer_key, method, created="2026-08-19T00:00:00Z")
    now = datetime(2026, 8, 19, 8, 0, tzinfo=timezone.utc)

    def status(endpoint, digest):
        return StatusRecord(digest, now, False, authenticated=True)

    kernel = CapsuleActionVerifier(
        capsule,
        presenter="spiffe://example.com/agent/procurement",
        now=lambda: now,
        resolver=KeyResolver({method: issuer_key.public_key()}),
        authorized_issuers={issuer: (method,)},
        status_provider=status,
        obligation_verifier=lambda obligation, proposal: obligation["type"].endswith("/audit"),
    )
    policy = CallablePolicyRuntime(
        "demo-local-policy",
        lambda proposal: (PolicyEvaluation(
            "urn:policy:supplier:create", "1", PolicyLayer.ORGANIZATIONAL,
            PolicyEffect.ALLOW, "SUPPLIER_CREATE_ALLOWED",
        ),),
    )
    connector = InMemorySupplierConnector()
    gateway = GovernedActionGateway(
        gateway_id="urn:gcp:gateway:signed-demo",
        policy_runtime=policy,
        graph=GovernanceGraph([GraphNode("commit")], []),
        connector=connector,
        kernel_verifier=kernel,
        approval_verifier=lambda proposal: True,
        receipt_key=Ed25519PrivateKey.generate(),
        receipt_verification_method="https://gateway.example.com/keys/demo",
    )
    record = gateway.execute(ActionProposal(
        "urn:gcp:action:signed-demo", "supplier.create", "urn:supplier:42",
        "sha256:" + "b" * 64,
    ), conflict_node="commit")
    print(json.dumps({
        "state": record.state.value,
        "decision": record.decision.value,
        "connector_commit_calls": connector.commit_calls,
        "suppliers_created": len(connector.suppliers),
        "kernel_controls": [value for value in record.controls if value.startswith("GCP_")],
        "receipt_proposal_digest": record.receipt["proposal_digest"],
        "claim_boundary": "Root capsule and live status are verified; delegated lineage and durable replay state remain next work.",
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
