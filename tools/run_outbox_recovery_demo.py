#!/usr/bin/env python3
"""Fault-inject process stops on both sides of connector invocation."""

import json
import sys
import tempfile
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gcp_reference import (  # noqa: E402
    ActionProposal, CallablePolicyRuntime, GovernanceGraph, GovernedActionGateway,
    GraphNode, InMemorySupplierConnector, PolicyEffect, PolicyEvaluation,
    PolicyLayer, SQLiteActionStore, SimulatedProcessCrash,
)


def runtime():
    return CallablePolicyRuntime(
        "outbox-demo-policy",
        lambda proposal: (
            PolicyEvaluation("urn:policy:supplier:create", "1", PolicyLayer.ORGANIZATIONAL,
                             PolicyEffect.ALLOW, "SUPPLIER_CREATE_ALLOWED"),
        ),
    )


def gateway(store, connector, key, before_connector=None):
    return GovernedActionGateway(
        gateway_id="urn:gcp:gateway:outbox-demo",
        policy_runtime=runtime(),
        graph=GovernanceGraph([GraphNode("commit")], []),
        connector=connector,
        kernel_verifier=lambda proposal: (),
        approval_verifier=lambda proposal: True,
        receipt_key=key,
        receipt_verification_method="https://gateway.example/keys/outbox-demo",
        action_store=store,
        before_connector=before_connector,
    )


def scenario(directory, name, crash_after):
    database = Path(directory) / (name + ".sqlite3")
    connector = InMemorySupplierConnector()
    connector.crash_after_next_commit = crash_after
    key = Ed25519PrivateKey.generate()
    proposal = ActionProposal(
        "urn:gcp:action:" + name, "supplier.create", "urn:supplier:" + name,
        "sha256:" + ("6" if crash_after else "7") * 64,
    )

    def before(value):
        if not crash_after:
            raise SimulatedProcessCrash("before connector invocation")

    first_store = SQLiteActionStore(database)
    first = gateway(first_store, connector, key, before)
    try:
        first.execute(proposal, conflict_node="commit")
    except SimulatedProcessCrash:
        pass
    durable_state = first.get(proposal.action_id).state.value
    calls_before_restart = connector.commit_calls
    first_store.close()

    second_store = SQLiteActionStore(database)
    second = gateway(second_store, connector, key)
    recovered = second.recover_pending()[0]
    second_store.close()
    return {
        "durable_state_at_crash": durable_state,
        "connector_calls_before_restart": calls_before_restart,
        "state_after_recovery": recovered.state.value,
        "connector_calls_after_recovery": connector.commit_calls,
        "suppliers_created": len(connector.suppliers),
    }


def main():
    with tempfile.TemporaryDirectory(prefix="gcp-outbox-demo-") as directory:
        print(json.dumps({
            "crash_before_connector": scenario(directory, "before", False),
            "crash_after_connector": scenario(directory, "after", True),
            "claim_boundary": "Single-host durable intent recovery with an idempotent connector.",
        }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
