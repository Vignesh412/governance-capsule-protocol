# Decision 0002: Narrow GCP and build it as an A2A/MCP governance profile

- Status: Accepted
- Date: 2026-08-11

## Context

Milestone 0 reviewed OpenAI, Anthropic, Google ADK, A2A, MCP, Microsoft Agent Framework, Amazon Bedrock/AgentCore, LangGraph, and adjacent identity, authorization, and signed-claims standards.

The review found extensive existing support for handoffs, guardrails, permissions, approvals, workflow state, identity, traces, and interoperability. It did not find a complete vendor-neutral task-governance lifecycle combining attenuation, obligation persistence, budget conservation, cryptographic delegation lineage, enforcement receipts, and governance-aware revocation.

## Decision

Proceed to Milestone 1 with GCP positioned as:

> A protocol candidate for verifiable continuity and constrained transformation of task governance across heterogeneous AI-agent and tool boundaries.

GCP will not define a new general agent transport, tool protocol, workload identity system, or OAuth replacement.

The first protocol bindings will target:

1. A2A for remote agent tasks and lifecycle transport
2. MCP for governed tool calls
3. Native SDK middleware/hooks for local enforcement

## Required reuse evaluation

- OAuth Rich Authorization Requests for fine-grained authority details
- OAuth Token Exchange for minting audience-bound downstream credentials
- SPIFFE or cloud workload identity for runtime identity
- W3C Verifiable Credentials versus simpler signed envelopes for assertions
- Microsoft FIDES labels as complementary information-flow obligations

## Consequences

- GCP novelty rests on lifecycle semantics and conformance, not its JSON fields.
- A2A extension downgrade must fail closed when GCP is required.
- Capsules must not contain reusable downstream bearer credentials.
- Traces are supporting evidence, not enforcement receipts by default.
- v0.1 will focus on tree-shaped delegation with preallocated budgets.
- Join semantics remain deferred until the core invariants are executable.
