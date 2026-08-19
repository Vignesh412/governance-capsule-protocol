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
- Ordinary connector exceptions after invocation begins are treated as ambiguous outcomes and recovered through authoritative action-ID reconciliation.
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

### Contract integrity versus runtime judgment

GCP proves who issued a governance assertion, that it was not altered, and that
delegation obeyed the protocol's attenuation, obligation, budget, lineage, and
revocation rules. It does not prove that an authorized action is factually
correct, beneficial, or safe.

The demonstration therefore keeps two decisions separate. GCP first verifies
the portable delegation contract. CARM then evaluates normalized local policy
and trusted runtime evidence before the action gateway can call a connector.
The `Authorized, but risky` scenario presents a valid supplier-creation capsule
alongside an unresolved screening signal. GCP reports `VERIFIED`; CARM reports
`RISK_DETECTED`; the gateway records `APPROVAL_REQUIRED` with zero side effects.

This is a policy-enforcement demonstration, not a claim that CARM can determine
the truth of arbitrary tool output or detect every coherent-but-flawed plan.

### Cross-framework transport

- An OpenAI Agents SDK handoff-shaped adapter exports application-owned governance into a signed transport envelope.
- The envelope binds source, destination, exact proposal, complete delegation lineage, expiry, and a replay-protected nonce.
- A Google ADK tool-callback-shaped boundary verifies the transport before composing it into the existing delegated-capsule verifier.
- Cross-framework controls survive into the signed gateway receipt.
- Tampering, replay, authority expansion, and cascading revocation stop before connector access.

The deterministic SDK-contract proof remains the always-available path. Two optional **Live Native Mode** scenarios are now implemented: a real OpenAI Agents SDK agent invokes a governed-delegation tool, GCP signs an application-owned transport, a real Google ADK agent requests the protected supplier tool, and the GCP callback verifies the transport before the gateway can call the sandboxed connector. One path commits exactly once; the other introduces cascading root revocation and must finish with zero connector calls. The browser receives progressive runtime events rather than presenting the native run as a precomputed animation.

Live mode requires Python 3.11+, the `frameworks` extra, and provider credentials. It has not been executed in this workspace because API credentials are not configured and restricted network access prevented downloading the missing OpenAI package. Its SDK-independent orchestration and enforcement boundary are covered deterministically in tests; the UI labels live readiness explicitly.

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
| Live OpenAI → Google ADK | Optional credentialed mode executes both native runtimes and streams every boundary to the UI. |
| Live cascading revocation | Both native runtimes execute, but the revoked task is blocked with zero connector calls. |
| Authorized, but risky | GCP verifies the contract; CARM escalates trusted risk evidence and the connector remains untouched. |

## Run locally

The core reference implementation requires Python 3.9 or newer.

```sh
python3 -m pip install -e .
python3 -m pytest -m "not frameworks_native and not acs_live"
python3 tools/validate_schemas.py
```

The marker-filtered test command is the reproducible core profile and does not
require the optional agent-framework or Microsoft ACS packages. Running plain
`python3 -m pytest` also discovers native integration gates; its pass/skip count
therefore depends on which optional extras are installed.

### Open the interactive demo

On macOS, double-click **Open GCP Demo.command** in the repository folder.

Alternatively, run:

```sh
python3 demo/server.py
```

The command opens [http://127.0.0.1:8765](http://127.0.0.1:8765). The guided visual demo leads with the OpenAI-to-Google-ADK transport, followed by valid delegation, authority expansion, obligation removal, budget overallocation, proof tampering, cascading root revocation, and crash recovery without duplicate execution.

### Enable Live Native Mode

Install the isolated Python 3.11 profile:

```sh
uv sync --python 3.11 --extra frameworks --extra test
```

Set credentials in your terminal—never commit them:

```sh
export OPENAI_API_KEY="..."
export GOOGLE_API_KEY="..."
.venv/bin/python demo/server.py
```

For Google Vertex AI credentials, set `GOOGLE_GENAI_USE_VERTEXAI=true`, `GOOGLE_CLOUD_PROJECT`, and application-default credentials instead of `GOOGLE_API_KEY`. `GCP_GOOGLE_MODEL` may override the default `gemini-flash-latest` model. The UI exposes `/api/native/status`, selects live mode automatically only when it is ready, and otherwise keeps the deterministic demonstration fully usable.

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

- **Core profile:** `python3 -m pytest -m "not frameworks_native and not acs_live"` completed **104 tests**. The two framework-native tests were deselected; the unavailable ACS module is reported as one collection-time skip.
- **Current workspace, plain test run:** `python3 -m pytest` completed **105 passed, 2 skipped**. Google ADK is installed, so its native constructor gate passed. Microsoft ACS and the OpenAI Agents SDK package are not installed, so those integration gates skipped.
- **Optional frameworks profile:** install `.[frameworks,test]` on Python 3.11+ to enable both OpenAI Agents SDK and Google ADK construction gates. This profile is not reported as locally verified until both packages are present and the unfiltered suite is rerun.
- **9 valid schema fixtures** were accepted.
- **2 structurally invalid fixtures** were rejected.
- **3 semantic-invalid manifests** were recognized: authority expansion, budget overallocation, and mandatory-obligation removal.
- The signed delegated-action, cross-framework transport, durable recovery, and all nine deterministic interactive-demo scenarios completed successfully.
- The optional tenth and eleventh scenarios are credentialed live-native allow and revocation paths. Their no-LLM governance orchestration contracts pass locally; provider-backed execution still requires credentials and downloaded SDK dependencies.

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

Licensed under the [Apache License 2.0](LICENSE). You may use, modify, and distribute the project, including commercially, subject to the license terms.
