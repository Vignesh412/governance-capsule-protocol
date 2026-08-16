# Decision 0005: Begin with a framework-neutral stateless verification core

- Status: Accepted
- Date: 2026-08-15

## Context

Milestone 3 must make the formal invariants executable without conflating stateless document verification with stateful allocation, replay, or revocation services.

The local project environment supports Python 3.9, `cryptography`, `jsonschema`, and `pytest`. The wire examples intentionally contain fake proof values and placeholder digests because their purpose is schema validation.

## Decision

The first reference implementation will be a framework-neutral Python package. Its initial trusted core will:

1. canonicalize the GCP v0.1 JSON domain;
2. hash, sign, and verify artifacts using the selected wire profile;
3. validate one ordinary parent-to-child transition;
4. validate signed delegation-proof binding; and
5. return deterministic GCP error codes.

Aggregate sibling budgets, replay detection, use counting, and revocation freshness will be separate stateful components. The stateless validator will not claim to enforce them.

## Consequences

- Existing schema fixtures remain unchanged and are not misrepresented as cryptographically valid.
- Cryptographic tests generate fresh, internally consistent signed artifacts.
- A passing stateless delegation check does not authorize execution by itself.
- The public API can later be embedded behind CARM or framework adapters without depending on a particular agent SDK.
