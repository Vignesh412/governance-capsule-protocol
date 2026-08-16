# GCP Formal Model v0.1

Status: Milestone 1 working model

Date: 2026-08-12

This document defines the semantics that the first executable GCP reference model must implement. It intentionally precedes the wire schema and cryptographic profile.

## 1. Supported execution model

GCP v0.1 models delegation as a rooted tree.

- One root capsule governs the original task.
- Every non-root capsule has exactly one parent.
- A parent may create zero or more children.
- Children may execute sequentially or concurrently.
- A child may create descendants only when its remaining delegation depth permits it.
- Joining governance from multiple parents is not supported in v0.1.
- Cyclic delegation is invalid.
- Budgets are preallocated before a child is issued. Children do not share a mutable portable balance.

This restriction makes lineage and budget conservation testable without requiring distributed consensus.

## 2. Entities

### 2.1 Task

A **Task** is a unit of work with a stable `task_id`. A child task is distinct from its parent task even when it contributes to the same workflow.

Task content is not itself authoritative. Model-generated task text cannot change capsule governance.

### 2.2 Capsule

A **Capsule** is the authoritative governance state for one task at one revision. Conceptually:

\[
C = (id, task, parent, issuer, subject, authority, obligations, budgets,
validity, depth, sequence)
\]

The wire representation and signature container are deferred to Milestone 2.

### 2.3 Issuer

An **Issuer** creates a root capsule or an authorized amendment. Its identity must be independently verifiable by the receiver's trust configuration.

### 2.4 Delegator

A **Delegator** derives a child capsule from a parent capsule. The delegator may narrow governance but cannot use ordinary delegation to expand it.

### 2.5 Subject

The **Subject** is the agent or runtime authorized to exercise the capsule. A capsule presented by another subject fails audience validation.

### 2.6 Receiver

A **Receiver** is the enforcement boundary evaluating a capsule. The receiver computes effective authority by intersecting inherited authority with its own local policy and capabilities.

### 2.7 Authority grant

An **Authority Grant** is a normalized tuple:

\[
g = (action, resource, constraints)
\]

Examples:

- `("vendor.read", "vendor/123", {})`
- `("refund.approve", "account/acme", {"amount_max": 500})`

For v0.1:

- actions use exact identifiers;
- resources use exact identifiers or hierarchical prefixes;
- constraints use protocol-registered types with deterministic subset rules;
- unknown constraint types fail closed;
- an omitted constraint is less restrictive than a present constraint.

One grant is no broader than another when its action and resource are contained by the parent grant and every child constraint is at least as restrictive.

### 2.8 Authority

**Authority** is a finite set of authority grants. Effective authority is:

\[
A_{effective}(C, R) = A_C \cap A_{local}(R) \cap A_{capability}(R)
\]

The intersection may reduce authority or make it empty. Local receiver policy never enlarges inherited authority.

### 2.9 Obligation

An **Obligation** is a typed requirement with:

- stable `obligation_id`;
- `type` and version;
- normalized parameters;
- `mandatory` flag;
- issuer or source-policy reference;
- satisfaction point, such as before action, during execution, or before completion.

Examples include human approval, data redaction, regional processing, enhanced audit, or FIDES-compatible information-flow labels.

For v0.1, persistence is identity-based: a mandatory parent obligation must occur unchanged in the child. Narrowing or parameter transformation is deferred until type-specific refinement rules exist.

### 2.10 Budget

A **Budget** is a map from registered dimension to a non-negative quantity:

\[
B = \{d_1:q_1, d_2:q_2, ...\}
\]

Initial dimensions may include `cost`, `tokens`, `risk`, and `time`. Every dimension defines a unit and exact arithmetic rules. Floating-point arithmetic is forbidden for conservation checks.

An absent child dimension means zero allocation, not unlimited allocation. An unknown dimension fails closed.

### 2.11 Delegation depth

`delegation_depth` is a non-negative integer. If a parent has depth `d`, a normally derived child must have depth at most `d - 1`. A parent with depth zero cannot delegate.

### 2.12 Validity

Validity includes:

- `not_before`;
- `expires_at`;
- capsule status and revocation reference;
- revocation freshness profile;
- replay policy; and
- sequence or issuance identifier.

Ordinary delegation cannot move `not_before` earlier or `expires_at` later than the parent.

### 2.13 Delegation proof

A **Delegation Proof** binds:

- parent capsule digest;
- child capsule digest;
- parent and child task identifiers;
- delegator and child subject identities;
- issuance time and unique identifier; and
- delegator authentication or signature.

The exact digest and signature algorithms are deferred to Milestone 2.

### 2.14 Approval

An **Approval** is authenticated authorization for a defined action or amendment. It must state:

- approver;
- capsule or lineage scope;
- permitted action or change;
- resource scope;
- issue and expiry time;
- reuse count or single-use status; and
- evidence reference.

Approval does not silently rewrite the parent capsule. It authorizes a specific action or an amendment issued by a party allowed to make that change.

### 2.15 Amendment

An **Amendment** is an authorized governance change that ordinary delegation cannot perform, such as expanding authority or resolving a mandatory obligation.

An amendment creates a new capsule revision. It must identify the previous revision, authority authorizing the change, rationale, scope, validity, and evidence. It cannot modify prior signed history.

### 2.16 Enforcement receipt

An **Enforcement Receipt** records a runtime assertion about one decision. It binds the evaluated capsule digest, action, receiver identity, decision, controls, approval reference, timestamp, and evidence references.

A receipt proves integrity and attribution once signed; it does not prove that the runtime evaluated policy correctly or reported honestly.

### 2.17 Revocation record

A **Revocation Record** is an issuer-authorized status event targeting one of:

- one capsule revision;
- a capsule and all descendants;
- an entire task lineage; or
- an issuer key or subject identity.

It records target, effective time, reason code, issuer, sequence, and integrity proof.

## 3. Core invariants

### I1. Authority attenuation

For every ordinary delegation from parent `p` to child `c`:

\[
A_c \preceq A_p
\]

Every child grant must be contained by at least one parent grant. The receiver then applies its local intersection:

\[
A_{effective}(c,R) \preceq A_c \preceq A_p
\]

Failure code: `GCP_AUTHORITY_EXPANSION`.

### I2. Mandatory-obligation persistence

Let `M(C)` be the set of canonical mandatory obligations in capsule `C`. For ordinary delegation:

\[
M(p) \subseteq M(c)
\]

Equality of inherited obligations is defined over canonical content, not only identifier. A child may add obligations. Removing or altering an inherited mandatory obligation requires an authorized amendment.

Failure codes: `GCP_OBLIGATION_REMOVED`, `GCP_OBLIGATION_MODIFIED`.

### I3. Lineage integrity

For every non-root capsule `c` with parent `p`:

\[
c.parent\_digest = Digest(Canonicalize(p))
\]

The delegation proof must bind the same parent and child digests, and the parent must exist in the verified lineage. Duplicate capsule IDs, cycles, mismatched task references, or invalid proofs fail validation.

Failure codes include `GCP_PARENT_MISMATCH`, `GCP_INVALID_DELEGATION_PROOF`, and `GCP_LINEAGE_CYCLE`.

### I4. Preallocated budget conservation

Let `children_issued(p)` include every child allocation recorded against parent `p`, including completed or canceled children unless a future protocol rule explicitly returns unused allocation.

For every budget dimension `d`:

\[
\sum_{c \in children\_issued(p)} B_c[d] \leq B_{delegable,p}[d]
\]

Validation must be atomic at the allocation authority. A portable capsule alone cannot prevent two concurrent issuers from double-allocating the same balance.

For v0.1, allocated budget is not automatically reclaimed when a child finishes, fails, expires, or is revoked. Reclamation is deferred because it requires authenticated consumption settlement.

Failure code: `GCP_BUDGET_OVERALLOCATED`.

## 4. Supporting validity rules

These rules accompany, but are not counted among, the first four headline invariants:

- child audience must name the intended subject;
- child expiry must not exceed parent expiry;
- child `not_before` must not precede parent `not_before`;
- delegation depth must decrease;
- all quantities must be non-negative and use registered units;
- a capsule must use a supported protocol version;
- unknown critical fields or semantics fail closed;
- a capsule subject to single-use policy cannot be replayed;
- a revoked capsule cannot authorize a new governed action after the revocation effective time, subject to its freshness profile.

## 5. Revocation and freshness

Revocation is not instantaneous in a distributed system. GCP therefore specifies what a receiver can guarantee rather than claiming immediate global propagation.

### 5.1 `online-strict`

The receiver must obtain current, authenticated status before every governed action.

- Cached status is not sufficient.
- If status cannot be obtained, execution fails closed.
- Intended for high-impact or irreversible actions.
- Guarantee: no action begins after the receiver learns an authenticated revocation; the residual race is between status response and action commitment.

Failure codes: `GCP_REVOKED` or `GCP_STATUS_UNAVAILABLE`.

### 5.2 `bounded-stale`

The receiver may use authenticated cached status no older than `max_staleness`.

- If the cache is older, status must be refreshed.
- If refresh fails, execution fails closed.
- Worst-case acceptance window is bounded by `max_staleness` plus clock and action-commit races.

Failure codes: `GCP_REVOCATION_STATUS_STALE`, `GCP_STATUS_UNAVAILABLE`, or `GCP_REVOKED`.

### 5.3 `offline-until-expiry`

The receiver may act without live status until capsule expiry.

- The issuer explicitly accepts that revocation may not reach an offline receiver before expiry.
- This profile must not be used for actions whose policy requires online revocation.
- The residual risk is visible in the capsule and receipt.

### 5.4 Descendant revocation

A revocation marked `cascade=true` invalidates the target capsule and all descendants whose verified lineage contains the target digest. Receivers do not need a list of every descendant to evaluate this rule, but they do need current status for relevant ancestors according to the freshness profile.

### 5.5 In-progress work

Revocation prevents future governed actions once detected. It cannot undo an external side effect already committed.

A receiver that detects revocation during execution must:

1. stop before the next governed action;
2. mark the task suspended or revoked;
3. emit a revocation enforcement receipt; and
4. invoke a separately defined compensation action when one exists.

Compensation semantics are application-specific in v0.1.

## 6. Validation order

A conforming reference validator should evaluate in this order so failures are deterministic:

1. protocol and semantic-version support;
2. structural validity and registered types;
3. canonical digest and integrity proof;
4. trusted issuer/delegator identity;
5. lineage linkage and cycle checks;
6. time validity;
7. audience/subject;
8. replay policy;
9. revocation and freshness;
10. delegation depth and temporal attenuation;
11. authority attenuation;
12. obligation persistence;
13. budget conservation/allocation;
14. receiver-local policy and capability intersection.

Structural and inherited-governance validation occurs before local policy reconciliation. A receiver must not “repair” an invalid child by silently reducing it and treating the invalid derivation as valid; it may reject the child and offer a newly derived constrained capsule.

## 7. Unsupported semantics

The following are explicitly unsupported in this model:

- governance joins with more than one parent;
- cyclic workflows;
- shared portable budgets without an allocation authority;
- automatic return of unused child budget;
- wildcard action semantics without a registered containment rule;
- arbitrary obligation weakening;
- universal policy-language translation;
- proof that an issuer or runtime assertion is truthful;
- guaranteed instantaneous revocation across disconnected receivers;
- automatic reversal of completed external side effects.

## 8. Milestone 2 implications

The wire model must be able to represent every concept and distinguish:

- ordinary derivation from authorized amendment;
- allocated from consumed budget;
- capsule expiry from revocation status freshness;
- trace references from signed enforcement receipts; and
- task cancellation from governance revocation.

Schema design must not weaken these semantics for convenience.
