# Decision 0006: Model shared enforcement state as separate atomic services

- Status: Accepted
- Date: 2026-08-16

## Context

A portable signed capsule cannot independently prevent concurrent sibling overallocation, repeated use of one-time authority, or action based on stale revocation information. These properties require state shared by an enforcement domain.

Combining them prematurely into CARM would make it difficult to test which guarantee comes from which state transition.

## Decision

Milestone 3 models three separate process-local reference services:

1. `AllocationLedger` atomically reserves preallocated child budgets and never reclaims them implicitly.
2. `UseRegistry` atomically records single-use or limited-use authority consumption.
3. `RevocationEvaluator` evaluates the current capsule and relevant ancestors using `online-strict`, `bounded-stale`, or `offline-until-expiry` semantics.

Audience validation remains a stateless semantic check.

The revocation evaluator consumes authenticated status assertions from a trusted provider adapter. Cryptographic validation of signed revocation artifacts remains a separate unfinished integration step.

## Consequences

- Concurrent allocations and uses can be tested deterministically with threads.
- A batch allocation either commits fully or not at all.
- Child completion, cancellation, expiry, or revocation does not reclaim allocation automatically.
- Offline residual risk is returned explicitly for later inclusion in an enforcement receipt.
- The process-local services demonstrate semantics but are not durable production infrastructure.
- CARM can later compose these services at an action boundary without redefining their behavior.
