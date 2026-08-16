# Decision 0001: Position Governance Capsule as a protocol candidate

- Status: Accepted
- Date: 2026-08-11

## Context

The initial idea described a portable governance object traveling with delegated work and CARM enforcing it at runtime. A portable object alone is a data model or architectural pattern, not a protocol.

## Decision

Use **Governance Capsule** as the current project name. Use **Governance Capsule Protocol (GCP)** for the intended protocol specification, while clearly labeling all early artifacts as drafts or protocol candidates.

The project will claim protocol status only after it defines:

- message types;
- lifecycle states and transitions;
- sender and receiver obligations;
- canonical representation and integrity rules;
- delegation, amendment, approval, revocation, fork, and join semantics;
- deterministic failure behavior;
- version and capability negotiation; and
- independently testable conformance requirements.

## Consequences

- Public communication must not describe the current work as an adopted standard.
- Schema work cannot substitute for behavioral semantics.
- Cross-framework interoperability is a required success condition.
- The project can stop or reposition if landscape research invalidates the gap hypothesis.
