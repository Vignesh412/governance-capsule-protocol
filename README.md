# Governance Capsule

Governance Capsule is an executable research prototype for carrying governance with delegated AI-agent work.

It explores a simple requirement: when one agent delegates a task to another, the task must not silently gain authority, lose mandatory obligations, exceed its allocated budgets, break its verifiable lineage, or continue under revoked authority.

The intended destination is the **Governance Capsule Protocol (GCP)**: a vendor-neutral protocol for portable, verifiable task governance across agents, tools, runtimes, and organizational boundaries. GCP is currently a **protocol candidate**, not a standard or production security system.

## What is built

The repository contains a working Python reference implementation with the following capabilities.

### Portable governance artifacts

- Governance Capsules describing task identity, provenance, authority, obligations, budgets, validity, audience, and revocation requirements.
- Delegation proofs binding a parent capsule to a child capsule.
- Approvals, amendments, revocations, enforcement receipts, and lifecycle receipts.
- Strict JSON Schemas plus valid, structurally invalid, and semantically invalid examples.
- Deterministic JSON canonicalization, SHA-256 digests, and Ed25519 signatures.

### Delegation verification

- Every capsule and delegation proof is schema-checked and signature-verified.
- Capsule issuers, delegators, and signing keys are checked against assigned roles.
- Delegated authority may narrow but cannot expand.
- Mandatory obligations must survive delegation.
- Child budgets must remain within the parent allocation.
- Capsule lineage must be continuous and cryptographically bound.
- Audience, validity windows, replay limits, and approval scope are enforced.
- Revocation checks include ancestor capsules, so revoking an upstream authority stops its descendants.

### Governed Action Gateway

The reference gateway acts as a trusted decision and commit boundary before a protected supplier action. It:

1. verifies the signed capsule or delegation chain;
2. evaluates local policy and required approvals;
3. applies the CARM conflict-resolution decision;
4. rejects, escalates, constrains, or allows the proposed action;
5. records the decision and controls in a signed receipt; and
6. invokes the connector only after governance checks succeed.

Action identifiers are bound to exact proposal digests. Reusing an identifier for different input is rejected, while a legitimate retry can return the recorded result without duplicating the side effect.

### Durable execution and recovery

- A SQLite action ledger persists proposals, decisions, controls, states, receipts, and connector results.
- Commit intent is written before connector invocation.
- Pending `COMMITTING` and `COMMIT_OUTCOME_UNKNOWN` actions can be recovered after restart.
- Recovery reconciles by action ID before retrying the connector.
- Fault-injection tests cover crashes immediately before and immediately after connector invocation.
- In the demonstrated single-host profile, recovery completes the action without creating a duplicate supplier.

This is a single-host durability result using an idempotent connector. It is not yet a distributed transaction guarantee.

### Governance Graph and CARM

- A validated Governance Graph represents dependencies among governed tasks.
- `AND`, `OR`, and `UNKNOWN` joins model downstream execution structure.
- Graph snapshots have deterministic digests.
- Downstream reach and topology confidence contribute to conflict assessment.
- CARM produces deterministic resolution outcomes from normalized policy evidence and graph context.
- Escalation decisions cannot be relaxed by downstream conflict resolution.

The current implementation demonstrates graph-sensitive resolution behavior. It does not claim that graph reach alone proves the correctness of a policy decision.

### Cross-framework transport

- An OpenAI Agents SDK handoff-shaped adapter exports application-owned governance into a signed transport envelope.
- The envelope binds source, destination, exact proposal, complete delegation lineage, expiry, and a replay-protected nonce.
- A Google ADK tool-callback-shaped boundary verifies the transport before composing it into the existing delegated-capsule verifier.
- Cross-framework controls survive into the signed gateway receipt.
- Tampering, replay, authority expansion, and cascading revocation stop before connector access.

This is currently a deterministic SDK-contract proof. Native OpenAI Agents SDK and Google ADK execution is the next integration gate.

## Demonstrated scenarios

| Scenario | Verified result |
| --- | --- |
| Valid signed delegation | The narrowed child action is committed once. |
| Authority expansion | The child delegation is rejected before connector access. |
| Removed mandatory obligation | The delegation is rejected. |
| Budget overallocation | The delegation is rejected. |
| Tampered delegation proof | Signature or content verification rejects the chain. |
| Revoked root capsule | The descendant action is rejected through cascading revocation. |
| Crash before connector call | Recovery reconstructs the proposal and commits once. |
| Crash after connector success | Recovery discovers the prior commit and does not call the connector again. |

## Run locally

The core reference implementation requires Python 3.9 or newer.

```sh
python3 -m pip install -e .
python3 -m pytest
python3 tools/validate_schemas.py
```

### Open the interactive demo

On macOS, double-click **Open GCP Demo.command** in the repository folder.

Alternatively, run:

```sh
python3 demo/server.py
```

The command opens [http://127.0.0.1:8765](http://127.0.0.1:8765). The guided visual demo leads with the OpenAI-to-Google-ADK transport, followed by valid delegation, authority expansion, obligation removal, budget overallocation, proof tampering, cascading root revocation, and crash recovery without duplicate execution.

Run the product demonstrations:

```sh
python3 tools/run_gateway_demo.py
python3 tools/run_durable_gateway_demo.py
python3 tools/run_outbox_recovery_demo.py
python3 tools/run_signed_capsule_gateway_demo.py
python3 tools/run_delegated_gateway_demo.py
python3 tools/run_cross_framework_demo.py
```

The delegated-action demonstration should finish with `lineage_verified: true`, state `COMMITTED`, and exactly one connector call. The recovery demonstration should show one committed supplier in both injected crash cases without a duplicate connector call.

## Verification status

Verified on 2026-08-19:

- **100 tests passed**.
- **2 optional native integration tests were skipped**: the external-policy runtime and cross-framework SDK construction gates require their optional Python 3.11 dependencies.
- **9 valid schema fixtures** were accepted.
- **2 structurally invalid fixtures** were rejected.
- **3 semantic-invalid manifests** were recognized: authority expansion, budget overallocation, and mandatory-obligation removal.
- The signed delegated-action, cross-framework transport, durable recovery, and all eight interactive-demo scenarios completed successfully.

## Trust boundary

The gateway, trusted key registry, revocation source, approval source, action store, policy evaluator, and protected connector are trusted components in the current prototype. A Governance Capsule cannot make a compromised enforcement point trustworthy by itself.

The implementation does not yet provide:

- a completed independent security review;
- Byzantine or compromised-host protection;
- a multi-instance PostgreSQL ledger and leased asynchronous outbox;
- instantaneous revocation across disconnected systems;
- production key management or identity federation;
- finalized interoperability profiles across independent agent frameworks; or
- a ratified protocol or standard.

Do not use this prototype as a production authorization or compliance system.

## Project documentation

- [Project charter](CHARTER.md)
- [Roadmap](ROADMAP.md)
- [Product architecture](docs/product-architecture-rfc-v0.1.md)
- [Formal model](spec/formal-model-v0.1.md)
- [Wire profile](spec/wire-profile-v0.1.md)
- [Schema guide](schema/README.md)
- [Reference library](docs/reference-library.md)
- [Governed Action Gateway](docs/gateway-slice-v0.1.md)
- [Durable gateway](docs/durable-gateway-slice-v0.1.md)
- [Commit-intent recovery](docs/commit-intent-recovery-v0.1.md)
- [Signed-capsule gateway](docs/signed-capsule-gateway-v0.1.md)
- [Delegated gateway](docs/delegated-gateway-v0.1.md)
- [Cross-framework proof](docs/cross-framework-proof-v0.1.md)
- [Interactive demo](demo/)
- [Security policy](SECURITY.md)
- [Progress log](journey/progress-log.md)

## Project status

This repository is experimental research code. The schemas, APIs, receipt format, and lifecycle semantics may change as the protocol candidate is tested across additional runtimes and failure conditions.

## License

No license has been selected yet. Until one is added, the repository contents remain all rights reserved by default.
