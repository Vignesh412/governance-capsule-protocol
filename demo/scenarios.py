"""Real, repeatable scenarios exposed by the visual demonstration."""

from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Dict, Mapping, Tuple

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from gcp_reference import (
    ActionProposal,
    CallablePolicyRuntime,
    DelegatedCapsuleActionVerifier,
    DelegationTransition,
    GovernanceGraph,
    GovernedActionGateway,
    GraphNode,
    InMemorySupplierConnector,
    KeyResolver,
    PolicyEffect,
    PolicyEvaluation,
    PolicyLayer,
    SQLiteActionStore,
    SimulatedProcessCrash,
    StatusRecord, FrameworkIdentity, GoogleADKGovernanceBoundary,
    OpenAIGovernanceHandoffAdapter,
    artifact_digest,
    sign_artifact,
)


NOW = datetime(2026, 8, 19, 9, 0, tzinfo=timezone.utc)
ISSUER = "https://governance.example.com/issuers/procurement"
ISSUER_METHOD = "https://governance.example.com/keys/procurement-demo"
DELEGATOR = "spiffe://example.com/agent/intake"
DELEGATOR_METHOD = "https://governance.example.com/keys/intake-demo"
CHILD = "spiffe://example.com/agent/supplier-operations"

SCENARIOS = (
    {
        "id": "cross-framework",
        "name": "OpenAI → Google ADK",
        "description": "A governed supplier task leaves an OpenAI agent boundary and is verified at a Google ADK boundary before execution.",
        "use_case": "A procurement agent built with the OpenAI Agents SDK delegates supplier #42 to a specialist built with Google ADK.",
        "task": "Carry the task across two independent runtimes without losing authority, audit, budget, revocation, or lineage.",
        "governance": "Create supplier #42 only · retain audit obligation · $2 child budget · online revocation check",
        "change": "The framework changes, but the signed Governance Capsule remains the authoritative contract.",
        "why_it_matters": "This demonstrates the central product claim: governance can travel with work across heterogeneous agent frameworks.",
        "source_agent": "OpenAI procurement agent",
        "source_framework": "OPENAI AGENTS SDK",
        "destination_agent": "Google supplier agent",
        "destination_framework": "GOOGLE ADK",
        "expected": "ALLOW",
        "tone": "allow",
    },
    {
        "id": "valid-delegation",
        "name": "Valid delegation",
        "description": "A child agent receives narrower authority, keeps the audit obligation, and uses only $2 of the $10 budget.",
        "use_case": "A manufacturer needs to onboard Atlas Components as supplier #42.",
        "task": "The procurement agent delegates the final supplier-creation step to Supplier Operations.",
        "governance": "Create suppliers only · keep an audit record · spend no more than $10",
        "change": "The child receives create access only for supplier #42 and a $2 budget.",
        "why_it_matters": "The specialist agent can finish the work without receiving the procurement agent's broader authority.",
        "expected": "ALLOW",
        "tone": "allow",
    },
    {
        "id": "authority-expansion",
        "name": "Authority expansion",
        "description": "The child attempts to add supplier.delete even though the parent granted only supplier.create.",
        "use_case": "A manufacturer needs to onboard Atlas Components as supplier #42.",
        "task": "The procurement agent delegates supplier creation to Supplier Operations.",
        "governance": "The parent can create suppliers, but it cannot delete them.",
        "change": "The child capsule asks for supplier.delete—an authority its parent never had.",
        "why_it_matters": "Delegation must never become a hidden path for gaining new privileges.",
        "expected": "BLOCK",
        "tone": "block",
    },
    {
        "id": "obligation-removed",
        "name": "Obligation removed",
        "description": "The child silently drops the parent's mandatory audit obligation.",
        "use_case": "A regulated supplier must be onboarded with an audit event.",
        "task": "Supplier Operations receives the creation task from Procurement.",
        "governance": "Every supplier creation must produce an audit record before execution.",
        "change": "The child capsule removes that mandatory audit obligation.",
        "why_it_matters": "Required compliance work must survive every handoff, even when the receiving agent would prefer less friction.",
        "expected": "BLOCK",
        "tone": "block",
    },
    {
        "id": "budget-exceeded",
        "name": "Budget exceeded",
        "description": "The child requests $12 although the parent delegated a maximum of $10.",
        "use_case": "Procurement has a $10 automation allowance for this onboarding workflow.",
        "task": "A $2 supplier-creation subtask is delegated to Supplier Operations.",
        "governance": "All delegated work must remain inside the original $10 cost ceiling.",
        "change": "The child capsule claims a $12 budget—more than the parent possesses.",
        "why_it_matters": "Agents must not manufacture additional budget by splitting or rewriting delegated work.",
        "expected": "BLOCK",
        "tone": "block",
    },
    {
        "id": "tampered-proof",
        "name": "Tampered proof",
        "description": "The delegation proof is changed after signing, breaking its cryptographic integrity.",
        "use_case": "Procurement signs a delegation for the trusted Supplier Operations agent.",
        "task": "The signed handoff authorizes supplier #42 to be created.",
        "governance": "The proof binds the parent capsule, child capsule, delegator, and receiving agent.",
        "change": "After signing, the receiving identity is changed to an attacker-controlled agent.",
        "why_it_matters": "A valid-looking handoff must still be rejected when its signed contents have been altered.",
        "expected": "BLOCK",
        "tone": "block",
    },
    {
        "id": "root-revoked",
        "name": "Root revoked",
        "description": "The original authority is revoked after delegation, so the descendant action must stop.",
        "use_case": "Supplier onboarding begins normally, but Procurement later cancels the workflow.",
        "task": "Supplier Operations still holds an earlier delegated creation task.",
        "governance": "The child remains dependent on the root capsule that created its authority.",
        "change": "The root authority is revoked before the child reaches the action boundary.",
        "why_it_matters": "Cancellation must propagate to work already delegated downstream.",
        "expected": "BLOCK",
        "tone": "block",
    },
    {
        "id": "crash-recovery",
        "name": "Crash and recovery",
        "description": "The connector commits, the gateway crashes before recording success, and restart recovery avoids a duplicate call.",
        "use_case": "The supplier system creates supplier #42, but the gateway loses the success response during a crash.",
        "task": "After restart, the gateway must determine whether creation already happened.",
        "governance": "The action ID is bound to the exact proposal and the commit intent is durable.",
        "change": "Execution stops after the side effect but before the final success state is recorded.",
        "why_it_matters": "Recovery must not create the same supplier twice when the outcome is temporarily uncertain.",
        "expected": "RECOVER",
        "tone": "recover",
    },
)


def scenario_catalog():
    return SCENARIOS


def _obligation() -> Dict[str, Any]:
    return {
        "obligation_id": "urn:gcp:obligation:audit",
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
    }


def _artifacts() -> Tuple[Mapping[str, Any], Mapping[str, Any], Mapping[str, Any], Any, Any]:
    issuer_key = Ed25519PrivateKey.generate()
    delegator_key = Ed25519PrivateKey.generate()
    validity = {
        "not_before": "2026-08-19T00:00:00Z",
        "expires_at": "2026-08-20T00:00:00Z",
        "freshness": {
            "profile": "online-strict",
            "status_endpoint": "https://governance.example.com/status",
        },
        "replay": {"mode": "multi-use", "max_uses": 10},
    }
    root = sign_artifact(
        {
            "gcp_version": "0.1",
            "kind": "root",
            "capsule_id": "urn:gcp:capsule:demo-root",
            "revision": 0,
            "task": {
                "task_id": "urn:gcp:task:supplier-onboarding",
                "workflow_id": "urn:gcp:workflow:supplier-onboarding",
                "purpose": "Onboard supplier",
            },
            "issuer": ISSUER,
            "subject": DELEGATOR,
            "authority": [
                {
                    "grant_id": "urn:gcp:grant:root-create",
                    "action": "supplier.create",
                    "resource": {"match": "prefix", "uri": "urn:supplier:"},
                }
            ],
            "obligations": [_obligation()],
            "budgets": [{"dimension": "cost", "quantity": "10", "unit": "USD"}],
            "delegation_depth": 2,
            "validity": validity,
            "sequence": 0,
        },
        issuer_key,
        ISSUER_METHOD,
        created="2026-08-19T00:00:00Z",
    )
    child_unsigned = {
        "gcp_version": "0.1",
        "kind": "derived",
        "capsule_id": "urn:gcp:capsule:demo-child",
        "revision": 0,
        "task": {
            "task_id": "urn:gcp:task:supplier-create",
            "workflow_id": "urn:gcp:workflow:supplier-onboarding",
            "purpose": "Create supplier 42",
        },
        "issuer": ISSUER,
        "delegator": DELEGATOR,
        "subject": CHILD,
        "parent": {
            "capsule_id": root["capsule_id"],
            "task_id": root["task"]["task_id"],
            "digest": artifact_digest(root),
        },
        "authority": [
            {
                "grant_id": "urn:gcp:grant:child-create",
                "action": "supplier.create",
                "resource": {"match": "exact", "uri": "urn:supplier:42"},
            }
        ],
        "obligations": [_obligation()],
        "budgets": [{"dimension": "cost", "quantity": "2", "unit": "USD"}],
        "delegation_depth": 1,
        "validity": validity,
        "sequence": 0,
    }
    child = sign_artifact(
        child_unsigned,
        issuer_key,
        ISSUER_METHOD,
        created="2026-08-19T00:05:00Z",
    )
    proof = _proof(root, child, delegator_key)
    return root, child, proof, issuer_key, delegator_key


def _proof(root, child, key):
    return sign_artifact(
        {
            "gcp_version": "0.1",
            "proof_id": "urn:gcp:delegation-proof:demo",
            "parent_capsule": {
                "capsule_id": root["capsule_id"],
                "task_id": root["task"]["task_id"],
                "digest": artifact_digest(root),
            },
            "child_capsule": {
                "capsule_id": child["capsule_id"],
                "task_id": child["task"]["task_id"],
                "digest": artifact_digest(child),
            },
            "delegator": DELEGATOR,
            "child_subject": CHILD,
            "issued_at": "2026-08-19T00:05:00Z",
        },
        key,
        DELEGATOR_METHOD,
        created="2026-08-19T00:05:00Z",
        proof_purpose="authentication",
    )


def _resign_child(root, child, issuer_key, **updates):
    unsigned = deepcopy(child)
    unsigned.pop("proof")
    unsigned.update(updates)
    unsigned["parent"] = {
        "capsule_id": root["capsule_id"],
        "task_id": root["task"]["task_id"],
        "digest": artifact_digest(root),
    }
    return sign_artifact(unsigned, issuer_key, ISSUER_METHOD, created="2026-08-19T00:05:00Z")


def _policy():
    return CallablePolicyRuntime(
        "gcp-demo-policy",
        lambda proposal: (
            PolicyEvaluation(
                "urn:policy:supplier-create",
                "1",
                PolicyLayer.ORGANIZATIONAL,
                PolicyEffect.ALLOW,
                "SUPPLIER_CREATE_ALLOWED",
                required_controls=("AUDIT_EVENT_REQUIRED",),
            ),
        ),
    )


def _gateway(kernel, connector, *, store=None, before_connector=None, receipt_key=None):
    return GovernedActionGateway(
        gateway_id="urn:gcp:gateway:visual-demo",
        policy_runtime=_policy(),
        graph=GovernanceGraph([GraphNode("commit")], []),
        connector=connector,
        kernel_verifier=kernel,
        approval_verifier=lambda proposal: True,
        receipt_key=receipt_key or Ed25519PrivateKey.generate(),
        receipt_verification_method="https://gateway.example.com/keys/visual-demo",
        action_store=store,
        before_connector=before_connector,
    )


def _timeline(record, connector_calls):
    rejected = record.state.value == "REJECTED"
    reasons = set(record.reason_codes)
    signature_failed = "GCP_SIGNATURE_INVALID" in reasons or "GCP_INVALID_DELEGATION_PROOF" in reasons
    semantic_failed = bool(
        reasons.intersection(
            {"GCP_AUTHORITY_EXPANSION", "GCP_OBLIGATION_REMOVED", "GCP_BUDGET_OVERALLOCATED"}
        )
    )
    revoked = "GCP_REVOKED" in reasons
    return [
        {"label": "Capsule received", "detail": "Root and child artifacts loaded", "status": "pass"},
        {
            "label": "Cryptographic proof",
            "detail": "Signatures and delegation binding verified" if not signature_failed else "Proof integrity failed",
            "status": "fail" if signature_failed else "pass",
        },
        {
            "label": "Delegation semantics",
            "detail": "Authority narrowed; obligations and budgets preserved" if not semantic_failed else reasons.pop(),
            "status": "fail" if semantic_failed else ("skip" if signature_failed else "pass"),
        },
        {
            "label": "Revocation freshness",
            "detail": "No active revocation" if not revoked else "Root authority revoked with cascade",
            "status": "fail" if revoked else ("skip" if signature_failed or semantic_failed else "pass"),
        },
        {
            "label": "Protected action",
            "detail": "Connector called exactly once" if connector_calls else "Connector was not called",
            "status": "pass" if connector_calls else ("fail" if rejected else "skip"),
        },
    ]


def _run_delegation(scenario_id):
    root, child, proof, issuer_key, delegator_key = _artifacts()
    revoked = scenario_id == "root-revoked"

    if scenario_id == "authority-expansion":
        child = _resign_child(
            root,
            child,
            issuer_key,
            authority=[
                {
                    "grant_id": "urn:gcp:grant:child-delete",
                    "action": "supplier.delete",
                    "resource": {"match": "exact", "uri": "urn:supplier:42"},
                }
            ],
        )
        proof = _proof(root, child, delegator_key)
    elif scenario_id == "obligation-removed":
        child = _resign_child(root, child, issuer_key, obligations=[])
        proof = _proof(root, child, delegator_key)
    elif scenario_id == "budget-exceeded":
        child = _resign_child(
            root,
            child,
            issuer_key,
            budgets=[{"dimension": "cost", "quantity": "12", "unit": "USD"}],
        )
        proof = _proof(root, child, delegator_key)
    elif scenario_id == "tampered-proof":
        proof = deepcopy(proof)
        proof["child_subject"] = "spiffe://example.com/agent/attacker"

    resolver = KeyResolver(
        {
            ISSUER_METHOD: issuer_key.public_key(),
            DELEGATOR_METHOD: delegator_key.public_key(),
        }
    )
    root_digest = artifact_digest(root)

    def status_provider(endpoint, digest):
        is_revoked = revoked and digest == root_digest
        return StatusRecord(
            digest,
            NOW,
            is_revoked,
            cascade=is_revoked,
            authenticated=True,
        )

    kernel = DelegatedCapsuleActionVerifier(
        [DelegationTransition(root, child, proof)],
        presenter=CHILD,
        now=lambda: NOW,
        resolver=resolver,
        authorized_issuers={ISSUER: (ISSUER_METHOD,)},
        authorized_delegators={DELEGATOR: (DELEGATOR_METHOD,)},
        status_provider=status_provider,
        obligation_verifier=lambda obligation, proposal: True,
    )
    connector = InMemorySupplierConnector()
    record = _gateway(kernel, connector).execute(
        ActionProposal(
            "urn:gcp:action:visual-" + scenario_id,
            "supplier.create",
            "urn:supplier:42",
            "sha256:" + "d" * 64,
        ),
        conflict_node="commit",
    )
    receipt = dict(record.receipt or {})
    proof_value = receipt.get("proof", {}).get("proof_value")
    if proof_value:
        receipt["proof"] = dict(receipt["proof"])
        receipt["proof"]["proof_value"] = proof_value[:28] + "…"
    return {
        "scenario_id": scenario_id,
        "state": record.state.value,
        "decision": record.decision.value if record.decision else None,
        "reason_codes": list(record.reason_codes),
        "controls": list(record.controls),
        "connector_calls": connector.commit_calls,
        "suppliers_created": len(connector.suppliers),
        "lineage": [
            {
                "role": "Root agent",
                "subject": DELEGATOR,
                "authority": "supplier.create · urn:supplier:*",
                "obligations": len(root["obligations"]),
                "budget": root["budgets"][0]["quantity"] + " USD",
                "digest": artifact_digest(root),
            },
            {
                "role": "Delegated agent",
                "subject": CHILD,
                "authority": child["authority"][0]["action"] + " · " + child["authority"][0]["resource"]["uri"],
                "obligations": len(child["obligations"]),
                "budget": child["budgets"][0]["quantity"] + " USD",
                "digest": artifact_digest(child),
            },
        ],
        "timeline": _timeline(record, connector.commit_calls),
        "receipt": receipt,
    }


def _run_recovery():
    with TemporaryDirectory(prefix="gcp-visual-demo-") as directory:
        database = Path(directory) / "actions.sqlite3"
        connector = InMemorySupplierConnector()
        connector.crash_after_next_commit = True
        key = Ed25519PrivateKey.generate()
        proposal = ActionProposal(
            "urn:gcp:action:visual-recovery",
            "supplier.create",
            "urn:supplier:42",
            "sha256:" + "6" * 64,
        )
        first_store = SQLiteActionStore(database)
        first = _gateway(lambda proposal: ("GCP_CAPSULE_VERIFIED",), connector, store=first_store, receipt_key=key)
        try:
            first.execute(proposal, conflict_node="commit")
        except SimulatedProcessCrash:
            pass
        at_crash = first.get(proposal.action_id)
        calls_at_crash = connector.commit_calls
        first_store.close()

        second_store = SQLiteActionStore(database)
        second = _gateway(lambda proposal: ("GCP_CAPSULE_VERIFIED",), connector, store=second_store, receipt_key=key)
        recovered = second.recover_pending()[0]
        second_store.close()
        return {
            "scenario_id": "crash-recovery",
            "state": recovered.state.value,
            "decision": recovered.decision.value,
            "reason_codes": list(recovered.reason_codes),
            "controls": list(recovered.controls),
            "connector_calls": connector.commit_calls,
            "suppliers_created": len(connector.suppliers),
            "lineage": [],
            "timeline": [
                {"label": "Commit intent persisted", "detail": at_crash.state.value, "status": "pass"},
                {"label": "Connector committed", "detail": f"{calls_at_crash} call before process stop", "status": "pass"},
                {"label": "Response lost", "detail": "Gateway stopped before recording success", "status": "warn"},
                {"label": "Restart reconciliation", "detail": "Existing supplier found by action ID", "status": "pass"},
                {"label": "Duplicate prevented", "detail": f"{connector.commit_calls} total connector call", "status": "pass"},
            ],
            "recovery": {
                "durable_state_at_crash": at_crash.state.value,
                "state_after_recovery": recovered.state.value,
                "connector_calls_before_restart": calls_at_crash,
                "connector_calls_after_recovery": connector.commit_calls,
                "suppliers_created": len(connector.suppliers),
            },
            "receipt": dict(recovered.receipt or {}),
        }


def _run_cross_framework():
    root, child, proof, issuer_key, delegator_key = _artifacts()
    transport_key = Ed25519PrivateKey.generate()
    transport_method = "https://governance.example.com/keys/openai-visual-transport"
    source_runtime = "urn:runtime:openai:procurement"
    destination_runtime = "urn:runtime:google-adk:supplier-operations"
    resolver = KeyResolver({
        ISSUER_METHOD: issuer_key.public_key(),
        DELEGATOR_METHOD: delegator_key.public_key(),
        transport_method: transport_key.public_key(),
    })
    proposal = ActionProposal(
        "urn:gcp:action:visual-cross-framework", "supplier.create", "urn:supplier:42",
        "sha256:" + "8" * 64, {"supplier_name": "Atlas Components"})
    destination = FrameworkIdentity("google-adk-python", destination_runtime)
    source = OpenAIGovernanceHandoffAdapter(
        runtime_id=source_runtime, destination=destination,
        signing_key=transport_key, verification_method=transport_method)
    envelope = source.export(
        transport_id="urn:gcp:transport:visual-openai-to-adk",
        proposal=proposal, transitions=[DelegationTransition(root, child, proof)],
        created_at="2026-08-19T08:58:00Z", expires_at="2026-08-19T09:08:00Z",
        nonce="urn:gcp:nonce:visual-cross-framework")
    boundary = GoogleADKGovernanceBoundary(
        runtime_id=destination_runtime, presenter=CHILD, now=lambda: NOW, resolver=resolver,
        authorized_transport_sources={source_runtime: (transport_method,)},
        authorized_issuers={ISSUER: (ISSUER_METHOD,)},
        authorized_delegators={DELEGATOR: (DELEGATOR_METHOD,)},
        status_provider=lambda endpoint, digest: StatusRecord(digest, NOW, False, authenticated=True),
        obligation_verifier=lambda obligation, action: True)
    accepted = boundary.accept(envelope)
    connector = InMemorySupplierConnector()
    record = _gateway(accepted.kernel_verifier, connector).execute(proposal, conflict_node="commit")
    return {
        "scenario_id": "cross-framework",
        "state": record.state.value,
        "decision": record.decision.value,
        "reason_codes": list(record.reason_codes),
        "controls": list(record.controls),
        "connector_calls": connector.commit_calls,
        "suppliers_created": len(connector.suppliers),
        "transport_digest": accepted.verified_transport.digest,
        "lineage": [
            {
                "role": "OpenAI source capsule", "subject": DELEGATOR,
                "authority": "supplier.create · urn:supplier:*",
                "obligations": len(root["obligations"]), "budget": "10 USD",
                "digest": artifact_digest(root),
            },
            {
                "role": "Google ADK child capsule", "subject": CHILD,
                "authority": "supplier.create · urn:supplier:42",
                "obligations": len(child["obligations"]), "budget": "2 USD",
                "digest": artifact_digest(child),
            },
        ],
        "timeline": [
            {"label": "OpenAI handoff", "detail": "Application context exports signed governance; model metadata grants no authority", "status": "pass"},
            {"label": "Signed GCP transport", "detail": "Source, destination, proposal, lineage, expiry, and nonce are integrity-bound", "status": "pass"},
            {"label": "Google ADK boundary", "detail": "Receiving callback verifies transport before the protected tool is available", "status": "pass"},
            {"label": "Delegation semantics", "detail": "Authority narrowed; audit obligation and budget survived the framework change", "status": "pass"},
            {"label": "Protected action", "detail": "Governed gateway calls the supplier connector exactly once", "status": "pass"},
        ],
        "receipt": dict(record.receipt or {}),
    }


def run_scenario(scenario_id):
    known = {item["id"] for item in SCENARIOS}
    if scenario_id not in known:
        raise ValueError("Unknown scenario")
    if scenario_id == "crash-recovery":
        return _run_recovery()
    if scenario_id == "cross-framework":
        return _run_cross_framework()
    return _run_delegation(scenario_id)
