#!/usr/bin/env python3
"""Prove gateway recovery across a real action-ledger restart."""

import json
import sys
import tempfile
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
    SQLiteActionStore,
)


def build_gateway(store, connector, key):
    runtime = CallablePolicyRuntime(
        "durable-demo-policy",
        lambda proposal: (
            PolicyEvaluation(
                "urn:policy:supplier:create", "1", PolicyLayer.ORGANIZATIONAL,
                PolicyEffect.ALLOW, "SUPPLIER_CREATE_ALLOWED",
            ),
        ),
    )
    return GovernedActionGateway(
        gateway_id="urn:gcp:gateway:durable-demo",
        policy_runtime=runtime,
        graph=GovernanceGraph([GraphNode("create-supplier")], []),
        connector=connector,
        kernel_verifier=lambda proposal: ("VERIFY_CAPSULE_AUTHORITY",),
        approval_verifier=lambda proposal: True,
        receipt_key=key,
        receipt_verification_method="https://gateway.example/keys/durable-demo",
        action_store=store,
    )


def main():
    with tempfile.TemporaryDirectory(prefix="gcp-durable-demo-") as directory:
        database = Path(directory) / "gateway.sqlite3"
        connector = InMemorySupplierConnector()
        connector.lose_next_response = True
        key = Ed25519PrivateKey.generate()
        proposal = ActionProposal(
            "urn:gcp:action:durable-supplier-42",
            "supplier.create",
            "urn:supplier:42",
            "sha256:" + "5" * 64,
        )

        before_restart_store = SQLiteActionStore(database)
        before_restart = build_gateway(before_restart_store, connector, key)
        unknown = before_restart.execute(proposal, conflict_node="create-supplier")
        before_restart_store.close()

        after_restart_store = SQLiteActionStore(database)
        after_restart = build_gateway(after_restart_store, connector, key)
        recovered_state = after_restart.get(proposal.action_id).state.value
        committed = after_restart.reconcile(proposal.action_id)
        retried = after_restart.execute(proposal, conflict_node="create-supplier")
        after_restart_store.close()

        print(json.dumps({
            "before_restart": unknown.state.value,
            "recovered_after_restart": recovered_state,
            "after_reconciliation": committed.state.value,
            "identical_retry": retried.state.value,
            "connector_commit_calls": connector.commit_calls,
            "suppliers_created": len(connector.suppliers),
            "database_removed_after_demo": True,
            "claim_boundary": "Durable single-host action ledger; connector is still an in-memory reference system.",
        }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
