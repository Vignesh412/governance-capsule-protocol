#!/usr/bin/env python3
"""Run the first end-to-end Governed Action Gateway product slice."""

import json
import sys
from dataclasses import asdict
from enum import Enum
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gcp_reference import (  # noqa: E402
    ActionProposal,
    CallablePolicyRuntime,
    GovernanceGraph,
    GovernedActionGateway,
    GraphNode,
    InMemorySupplierConnector,
    PolicyEffect,
    PolicyEvaluation,
    PolicyLayer,
)


def encode(value):
    if isinstance(value, Enum):
        return value.value
    raise TypeError(type(value).__name__)


def main():
    connector = InMemorySupplierConnector()
    connector.lose_next_response = True
    runtime = CallablePolicyRuntime(
        "demo-policy-runtime",
        lambda proposal: (
            PolicyEvaluation(
                "urn:policy:supplier:create",
                "1",
                PolicyLayer.ORGANIZATIONAL,
                PolicyEffect.ALLOW,
                "SUPPLIER_CREATE_ALLOWED",
                "demo-policy-runtime",
                "allow",
                ("AUDIT_SUPPLIER_CREATION",),
            ),
        ),
    )
    gateway = GovernedActionGateway(
        gateway_id="urn:gcp:gateway:demo",
        policy_runtime=runtime,
        graph=GovernanceGraph([GraphNode("create-supplier")], []),
        connector=connector,
        kernel_verifier=lambda proposal: ("VERIFY_CAPSULE_AUTHORITY", "CHECK_REVOCATION"),
        approval_verifier=lambda proposal: True,
        receipt_key=Ed25519PrivateKey.generate(),
        receipt_verification_method="https://gateway.example/keys/demo",
    )
    proposal = ActionProposal(
        "urn:gcp:action:supplier-42",
        "supplier.create",
        "urn:supplier:42",
        "sha256:" + "4" * 64,
    )
    first = gateway.execute(proposal, conflict_node="create-supplier")
    reconciled = gateway.reconcile(proposal.action_id)
    retried = gateway.execute(proposal, conflict_node="create-supplier")
    print(
        json.dumps(
            {
                "first_observed_state": first.state,
                "reconciled_state": reconciled.state,
                "retry_state": retried.state,
                "connector_commit_calls": connector.commit_calls,
                "supplier_count": len(connector.suppliers),
                "controls": list(reconciled.controls),
                "receipt": reconciled.receipt,
                "claim_boundary": "Demonstrates in-process mediation and recovery; not durable or production-ready.",
            },
            indent=2,
            default=encode,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
