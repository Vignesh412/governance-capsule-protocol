# Decision 0008: Build one product around a trusted action boundary

- Status: Accepted
- Date: 2026-08-19

## Context

The project began with GCP as a portable governance-continuity protocol candidate and CARM as a runtime enforcer. The latest CARM mechanism is more specific: it resolves policy conflicts using severity and downstream reach, CARM-SE selectively automates some escalations under calibrated risk, and the Resolution Identifiability Gap explains why structural evidence cannot always identify the correct action.

Treating these as separate products would create overlapping decision surfaces and unclear guarantees. Treating a travelling capsule as self-enforcing would also be incorrect: a signed artifact carries claims, while enforcement requires complete mediation at a trusted side-effect boundary.

## Decision

Governance Capsule will be developed as one product with:

1. GCP as the signed portable governance contract and lifecycle protocol;
2. a deterministic verification kernel for non-negotiable invariants;
3. a Governed Action Gateway as the reference monitor for protected side effects;
4. CARM as the resolver for conflicts among otherwise valid policies;
5. CARM-SE as an optional, certified selective-automation layer behind CARM;
6. a RIG-aware evidence plane that requests evidence or abstains when the correct resolution is not identifiable;
7. a versioned Governance Graph for dependency and decision context; and
8. signed receipts for every attempted governed action.

Protocol-invalid authority, signatures, budgets, approvals, revocation status, or mandatory obligations cannot be relaxed by CARM or CARM-SE.

The initial production-shaped profile is centralized and uses transactional state. Cross-organization federation follows after single-domain state and recovery semantics are demonstrated.

## Consequences

- The product governs action commitments rather than model reasoning.
- Protected connector credentials must remain behind the gateway.
- Learned components remain outside the trusted authorization kernel.
- CARM decisions must bind exact policy, graph, and evidence snapshots.
- CARM-SE must fail back to baseline CARM outside an active certification envelope.
- RIG becomes an executable evidence sufficiency and abstention contract.
- Ambiguous connector outcomes become explicit states requiring reconciliation.
- The roadmap now builds the gateway and CARM baseline before cross-framework federation.

## Reference

The detailed architecture, service contracts, state machine, trust model, and delivery sequence are defined in `docs/product-architecture-rfc-v0.1.md`.
