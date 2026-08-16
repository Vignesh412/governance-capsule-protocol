# Decision 0003: Adopt tree delegation, strict inherited obligations, and explicit revocation freshness

- Status: Accepted
- Date: 2026-08-12

## Context

Milestone 1 requires invariants precise enough to implement. Arbitrary workflow joins, shared budgets, obligation refinement, and instantaneous revocation introduce unresolved distributed-state and semantic-composition problems.

External feedback on the first public project post also highlighted revocation propagation as a critical test: authority may change while descendants are already executing.

## Decision

GCP v0.1 will:

1. model delegation as a rooted tree with exactly one parent per child;
2. allocate child budgets atomically before issuance;
3. treat allocated budget as unavailable until an authenticated future settlement mechanism returns it;
4. require mandatory inherited obligations to remain byte-equivalent after canonicalization during ordinary delegation;
5. reserve obligation weakening and authority expansion for explicit authorized amendments;
6. distinguish task cancellation from governance revocation;
7. support `online-strict`, `bounded-stale`, and `offline-until-expiry` revocation freshness profiles; and
8. state revocation guarantees as bounded freshness behavior, not instantaneous propagation.

## Consequences

- The first validator can be deterministic and property-tested.
- Parallel budget safety requires an allocation authority or serialized ledger; the capsule alone is insufficient.
- Multi-parent joins and automatic unused-budget reclamation are deferred.
- Offline execution remains possible only as an explicit, auditable risk choice.
- Revocation can prevent future governed actions but cannot undo committed side effects.
