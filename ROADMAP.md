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

## M4 - CARM enforcement point

### Work

- Accept a capsule, proposed action, receiver policy, capabilities, and workflow context.
- Return allow, allow-with-controls, approval-required, or block.
- Generate signed enforcement receipts.
- Measure decision overhead.

### Exit criteria

- Enforcement is deterministic for a fixed input.
- No model output can bypass the decision point.
- Human approval is scoped, authenticated, expiring, and auditable.

## M5 - First framework adapter

### Work

- Integrate with one agent SDK's handoff and tool-execution hooks.
- Preserve capsule identity and trace correlation across a multi-agent run.
- Demonstrate malicious child behavior being rejected.

### Exit criteria

- A real two-agent workflow passes the full conformance suite.
- Enforcement receipts reconstruct the complete governed execution path.

## M6 - Protocol bindings

### Work

- Define an A2A extension binding.
- Define an MCP tool-call binding.
- Specify discovery and capability negotiation.
- Implement downgrade protection and unsupported-policy behavior.

### Exit criteria

- Critical governance state is attached to durable protocol objects rather than transient messages.
- No binding requires bearer-token passthrough.
- Independent producer and consumer implementations exchange a valid capsule.

## M7 - Cross-framework demonstration

### Work

- Run supplier onboarding across two agent frameworks and one governed MCP service.
- Exercise delegation, forked budgets, human approval, revocation, and completion.
- Publish reproducible traces and measurements.

### Exit criteria

- The same invariants hold across all boundaries.
- The demonstration can be reproduced from a clean environment.
- Limitations and failed cases are published with the successful result.

## M8 - Draft protocol and conformance suite

### Work

- Publish a normative draft using MUST, SHOULD, and MAY consistently.
- Release language-neutral test vectors.
- Invite external implementation and security review.

### Exit criteria

- At least two implementations pass the core conformance profile.
- At least one implementation is meaningfully independent of the reference library.
- Open security questions are documented rather than hidden by the specification.
