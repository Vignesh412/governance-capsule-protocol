# Roadmap

The roadmap advances only when the exit criteria for the current milestone are satisfied.

## M0 - Foundation and landscape

Status: Complete (2026-08-11)

### Work

- Establish charter, scope, terminology, threat model, and evidence rules.
- Compare major agent SDKs, orchestration frameworks, and interoperability protocols.
- Separate native behavior, extension points, and application-defined possibilities.
- Identify the smallest defensible interoperability gap.

### Exit criteria

- Every material landscape claim has a dated primary source.
- At least OpenAI, Anthropic, Google ADK, A2A, MCP, Microsoft Agent Framework, Amazon Bedrock Agents, and LangGraph are assessed.
- The gap statement survives comparison with adjacent authorization and provenance standards.
- The project records a decision to proceed, narrow, reposition, or stop.

## M1 - Formal model and threat analysis

Status: Complete (2026-08-12)

### Work

- Define task, capsule, issuer, subject, delegator, authority, obligation, budget, approval, amendment, receipt, and revocation.
- Formalize authority attenuation, obligation persistence, budget conservation, lineage integrity, validity, and failure behavior.
- Define fork and join semantics for the initial supported workflow class.
- Enumerate abuse cases and security assumptions.

### Exit criteria

- Invariants are precise enough to turn into executable property tests.
- Each threat maps to a prevention, detection, or explicitly accepted residual risk.
- Unsupported workflow semantics are explicit.

## M2 - Capsule data model v0.1

Status: Complete (2026-08-12)

### Work

- Define capsule, delegation-proof, amendment, approval, and receipt schemas.
- Select canonical serialization, hashing, and signature profiles.
- Publish valid and invalid examples.
- Define version negotiation and unknown-field behavior.

### Exit criteria

- Schemas validate independently of any agent framework.
- Mutation of protected content is detectable.
- Examples cover issuance, delegation, constraint, approval, completion, rejection, and revocation.

## M3 - Core reference library

Status: In progress (started 2026-08-15)

### Work

- Implement building, signing, verifying, deriving, attenuating, revoking, and receipting.
- Implement preallocated child budgets for parallel execution.
- Add deterministic error codes.
- Add unit, property-based, and adversarial tests.

### Exit criteria

- Unauthorized authority expansion is always rejected in generated tests.
- Mandatory obligations cannot be silently removed.
- Child budget allocations cannot exceed the parent balance.
- Replay, wrong-audience, expiry, invalid-signature, and revocation tests pass.

## Architecture checkpoint - Unified product architecture

Status: Complete (2026-08-19)

### Work

- Define Governance Capsule as one product containing GCP, the Governed Action Gateway, CARM, CARM-SE, the Governance Graph, and RIG-aware evidence handling.
- Separate the deterministic trusted kernel from adaptive intelligence.
- Define data, control, and evidence planes.
- Define complete mediation at the action commit boundary.
- Define the action state machine, transactional reservations, idempotency, ambiguous outcomes, reconciliation, and receipt requirements.
- Record Decision 0008 and publish the Product Architecture RFC v0.1.

### Exit criteria

- Protocol-invalid cases are unambiguously outside CARM negotiation.
- Every protected side effect has a named enforcement boundary.
- CARM-SE has an explicit certification and fallback model.
- RIG is represented as executable evidence sufficiency and abstention behavior.
- The build sequence reaches one reproducible end-to-end product rather than disconnected components.

## M4 - Governed Action Gateway and receipts

### Work

- Complete amendment-diff and signed active-status verification in the trusted kernel.
- Generate and verify signed enforcement and lifecycle receipts.
- Implement the governed action state machine with transactional persistence.
- Implement atomic reservations, idempotency, outbox delivery, connector reconciliation, and explicit unknown outcomes.
- Place one protected demonstration connector exclusively behind the gateway.

### Exit criteria

- Enforcement is deterministic for fixed artifacts and snapshots.
- No governed adapter can reach protected credentials outside the gateway.
- Retries cannot duplicate approval use or budget consumption.
- Ambiguous connector outcomes are not treated as failures or silently retried.
- Receipts reconstruct every attempted governed commit.

## M5 - CARM baseline and Governance Graph

### Work

- Implement typed valid-policy conflicts and PE, NR, and EB.
- Build the versioned Governance Graph with declared join semantics and snapshot digests.
- Implement join-aware downstream reach and topology confidence.
- Bind every CARM decision to policy, graph, evidence, and configuration snapshots.
- Generate governance-debt entries for negotiated relaxation.

### Exit criteria

- GCP invalidity cannot enter CARM resolution.
- The same valid conflict produces a deterministic baseline decision for fixed inputs.
- Unknown or stale topology cannot be interpreted as zero downstream reach.
- The paper's baseline mechanism is reproduced before broader product claims.

## M6 - RIG evidence resolver and CARM-SE

### Work

- Define evidence schemas, provenance, freshness, contradiction, and purpose constraints.
- Implement executable identifiability contracts and structured evidence requirements.
- Implement CARM-SE certification envelopes, promotion, expiry, revocation, and fallback.
- Reproduce selective-automation results and test distribution-shift failure behavior.

### Exit criteria

- Missing decision-relevant evidence produces a request or abstention rather than a guessed resolution.
- CARM-SE cannot act outside an active compatible certification envelope.
- Automation rate is not used as a proxy for calibration validity.
- Every selective decision records its risk ceiling, certificate, and evidence snapshot.

## M7 - First framework adapter and MCP tool boundary

### Work

- Integrate one agent SDK's delegation and tool-execution hooks.
- Define an MCP governed-tool binding.
- Preserve capsule identity and receipt correlation across a real multi-agent run.
- Demonstrate malicious child behavior and direct-tool bypass prevention.

### Exit criteria

- A real two-agent workflow passes the core conformance suite.
- The protected MCP tool is accessible only through the gateway.
- Receipts reconstruct the complete governed execution path.
- A malicious child cannot expand authority or bypass the action boundary.

## M8 - Cross-framework supplier-onboarding demonstration

### Work

- Add a second independent agent framework and an A2A binding.
- Exercise delegation, parallel budgets, policy conflict, evidence acquisition, CARM-SE, human approval, ambiguous connector recovery, revocation, and compensation.
- Build a minimal approval queue and governance timeline.
- Publish reproducible traces, measurements, failures, and limitations.

### Exit criteria

- The same GCP semantics and action-boundary guarantees hold across both frameworks and MCP.
- A mid-workflow revocation suspends affected descendants while unaffected work can continue.
- The demonstration is reproducible from a clean environment.
- Latency, review burden, residual risk, and failed cases are published.

## M9 - Protocol bindings, draft, and conformance suite

### Work

- Finalize A2A and MCP bindings, discovery, capability negotiation, and downgrade protection.
- Publish a normative draft using MUST, SHOULD, and MAY consistently.
- Release language-neutral test vectors.
- Invite external implementation and security review.

### Exit criteria

- At least two implementations pass the core conformance profile.
- At least one implementation is meaningfully independent of the reference library.
- Open security questions are documented rather than hidden by the specification.
- No binding requires bearer-token passthrough.
