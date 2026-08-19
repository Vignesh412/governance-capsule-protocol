# Decision 0010: Prove graph sensitivity before claiming governance improvement

Date: 2026-08-19  
Status: Accepted

## Context

The competitive refresh showed that delegation controls, approvals, budgets, receipts, adapters, and pre-action policy enforcement already exist in adjacent projects. Implementing another isolated policy engine would not demonstrate the remaining Governance Capsule product hypothesis.

CARM claims a narrower distinction: policy conflicts should be handled with awareness of their downstream consequences. That claim must first be made executable and compared with simpler rules under identical inputs.

## Decision

The first competitive slice will:

1. consume normalized evaluations through a framework-neutral policy-runtime boundary;
2. validate and digest a Governance Graph with explicit AND, OR, and UNKNOWN join semantics;
3. compute join-aware downstream reach and topology confidence;
4. reproduce deterministic PE, NR, and EB selection, including outcome-aware rerouting of automated blocking;
5. compare the same conflict with most-restrictive and fixed-priority baselines; and
6. report limitations alongside results.

The experiment may claim decision sensitivity to verified graph position. It may not claim correctness, safety improvement, or competitive superiority without labelled outcomes and an external-runtime comparison.

## Consequences

- A graph snapshot digest becomes required evidence for graph-sensitive CARM decisions.
- Multi-parent dependencies without declared join semantics are invalid; UNKNOWN is explicit and conservative.
- Low topology confidence can force escalation instead of being interpreted as low reach.
- Microsoft AGT ACS remains the first planned external policy-runtime integration.
- CARM-SE and RIG are kept out of this slice so their benefits cannot mask errors in the deterministic CARM baseline.
