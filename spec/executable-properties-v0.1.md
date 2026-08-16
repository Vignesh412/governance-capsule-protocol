# GCP Executable Properties v0.1

Status: Acceptance specification for the reference model

Date: 2026-08-12

These properties define what Milestone 3 code must eventually prove through unit, generated, and adversarial tests. Milestone 1 is complete when each property has deterministic inputs, expected outcomes, and failure codes.

## P1. Valid narrowing succeeds

Given a valid parent, a child that narrows actions, resource scope, numeric limits, validity, depth, and budget while retaining all mandatory obligations must validate.

Expected: `VALID`.

## P2. Action expansion fails

Add an action not covered by any parent grant.

Expected: `GCP_AUTHORITY_EXPANSION`.

## P3. Resource expansion fails

Change an exact or hierarchical resource to a broader scope.

Expected: `GCP_AUTHORITY_EXPANSION`.

## P4. Constraint relaxation fails

Increase `amount_max`, enlarge an allowed region set, or remove a parent constraint.

Expected: `GCP_AUTHORITY_EXPANSION`.

## P5. Mandatory-obligation removal fails

Remove one mandatory inherited obligation.

Expected: `GCP_OBLIGATION_REMOVED`.

## P6. Mandatory-obligation mutation fails

Keep the obligation ID but modify its type, version, or parameters.

Expected: `GCP_OBLIGATION_MODIFIED`.

## P7. Additional obligation succeeds

Retain all inherited mandatory obligations and add a receiver-required obligation.

Expected: `VALID`.

## P8. Parent mutation breaks lineage

Change any protected parent field after the child parent digest is computed.

Expected: `GCP_PARENT_MISMATCH`.

## P9. Child mutation breaks delegation proof

Change any protected child field after the delegation proof is produced.

Expected: `GCP_INVALID_DELEGATION_PROOF`.

## P10. Cycle fails

Construct a lineage in which an ancestor ID or digest is revisited.

Expected: `GCP_LINEAGE_CYCLE`.

## P11. Conserved allocation succeeds

Allocate child budgets whose sum for every dimension equals or is below the parent delegable budget.

Expected: all allocations commit atomically.

## P12. Overallocation fails without partial commit

Attempt a batch whose sum exceeds the parent budget in one dimension.

Expected: `GCP_BUDGET_OVERALLOCATED`; no child allocation in the batch is recorded.

## P13. Concurrent allocation is serialized

Two concurrent allocations individually fit the starting balance but do not fit together.

Expected: at most one commits; the other receives `GCP_BUDGET_OVERALLOCATED` or an allocation-conflict retry result.

## P14. Budget is not implicitly reclaimed

Complete, cancel, expire, or revoke a child and attempt to reallocate its allocation without a settlement record.

Expected: allocation remains charged; new allocation fails if insufficient balance remains.

## P15. Temporal expansion fails

Set child `not_before` earlier than the parent or child expiry later than the parent.

Expected: `GCP_TEMPORAL_EXPANSION`.

## P16. Delegation-depth reset fails

Set child depth greater than `parent.depth - 1`, or delegate from depth zero.

Expected: `GCP_DELEGATION_DEPTH_EXCEEDED`.

## P17. Wrong audience fails

Present a valid capsule using a subject identity outside its audience.

Expected: `GCP_WRONG_AUDIENCE`.

## P18. Strict revocation stops execution

Under `online-strict`, revoke an ancestor before a governed action.

Expected: `GCP_REVOKED`; the action executor is never called.

## P19. Strict status outage fails closed

Under `online-strict`, make authenticated status unavailable.

Expected: `GCP_STATUS_UNAVAILABLE`; the action executor is never called.

## P20. Bounded stale cache behavior is exact

Under `bounded-stale(T)`, cached non-revoked status of age `<= T` may be used. Status of age `> T` must be refreshed. If refresh fails, execution must fail closed.

Expected: deterministic boundary behavior with `GCP_REVOCATION_STATUS_STALE` or `GCP_STATUS_UNAVAILABLE` as appropriate.

## P21. Cascading ancestor revocation fails descendants

Revoke an ancestor with `cascade=true` and validate a descendant whose direct capsule is not separately listed as revoked.

Expected: `GCP_REVOKED`.

## P22. Offline residual risk is visible

Under `offline-until-expiry`, execute using a capsule whose issuer has revoked it but whose receiver has no newer status and whose expiry has not passed.

Expected: protocol permits execution only if local policy permits this profile; receipt records the offline profile and last-known status time.

## P23. Replay fails for single-use authority

Commit the same single-use capsule or approval identifier twice at one enforcement domain.

Expected: first use succeeds; second returns `GCP_REPLAY_DETECTED`.

## P24. Unknown critical semantics fail closed

Introduce an unknown authority constraint, obligation marked critical, budget dimension, or freshness profile.

Expected: `GCP_UNSUPPORTED_SEMANTICS`.

## Generated-test requirements

Property-based generators must create valid parent capsules and then produce both valid narrowing children and one-mutation adversarial children. The test oracle must be independent of serialized field order.

Minimum generated coverage targets for the first reference implementation:

- 10,000 valid derivations;
- 10,000 authority mutations;
- 10,000 obligation mutations;
- 10,000 randomized budget-allocation batches;
- 5,000 randomized lineage graphs constrained to trees, plus injected cycles; and
- boundary tests for all time and freshness comparisons.

Passing generated tests is evidence about the implementation under the modeled semantics, not proof that the model captures every real governance policy.
