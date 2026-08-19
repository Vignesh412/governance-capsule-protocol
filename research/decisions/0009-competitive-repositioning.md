# Decision 0009: Integrate existing governance primitives and build the graph/evidence layer

- Status: Accepted
- Date: 2026-08-19

## Context

A primary-source landscape refresh found material overlap that did not appear in the project's 2026-08-11 framework-focused review. Microsoft Agent Governance Toolkit now documents deterministic action governance, scope-narrowing delegation chains, revocation, policy-as-code, budgets, audit, framework adapters, MCP/A2A bridges, and an action-bound approval protocol in progress. SentinelAgent formalizes verifiable delegation-chain properties. DRP, Agent Receipts, HEM, Policy Cards, CORA, and ToolChain-CRC cover authorization receipts, escalation, portable policy, and selective risk control.

Building all of those primitives again would make Governance Capsule broad, slow, and difficult to distinguish.

## Decision

The project will:

1. retain GCP as a narrow task-governance continuity and interoperability profile;
2. integrate established identity and authorization standards;
3. use an adapter over an existing deterministic policy runtime such as AGT ACS, OPA, or Cedar instead of inventing a universal policy language;
4. evaluate compatibility with Agent Receipts and HEM before finalizing generic receipt or escalation formats;
5. treat Microsoft AGT as the primary implementation baseline and an integration target;
6. build the transactional commit coordinator only where it supplies stronger credential ownership, reservation, idempotency, reconciliation, and outcome semantics;
7. concentrate original implementation on the Governance Graph, CARM, CARM-SE certification, RIG-aware evidence contracts, and conserved cross-runtime task state; and
8. require comparative evaluation rather than a greenfield-only demonstration.

## Consequences

- Monotonic delegation, generic policy enforcement, approval gates, receipts, adapters, and conformal action gating are no longer positioned as individually novel.
- The next vertical slice must integrate with an existing governance runtime.
- GCP schema growth is paused unless a field is required for cross-runtime task continuity or the comparative slice.
- The product claim becomes evidence-aware, cascade-aware governed execution across heterogeneous multi-agent workflows.
- Failure to demonstrate graph/evidence/recovery advantages against strong baselines is a reason to narrow or stop.

## Evidence

The source-by-source comparison, capability matrix, build-versus-integrate decisions, and go/no-go conditions are recorded in `research/competitive-architecture-report-2026-08-19.md`.
