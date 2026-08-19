# Governance Capsule Product Architecture RFC v0.1

Status: Accepted working architecture  
Date: 2026-08-19  
Audience: protocol authors, runtime implementers, adapter authors, security reviewers, and product engineers

## 1. Executive summary

Governance Capsule is one product with four cooperating mechanisms:

1. **GCP** is the portable, signed governance contract and lifecycle protocol.
2. **CARM** is the Cascade-Aware Resolution Mechanism for conflicts among otherwise valid policies.
3. **CARM-SE** is a selectively automated resolver operating only inside a certified risk envelope.
4. **RIG-aware evidence handling** detects when the available facts cannot identify the correct resolution and requests evidence or abstains.

The product governs committed side effects, not model reasoning. Agents and models are untrusted proposal generators. A trusted enforcement point placed before every consequential action verifies GCP invariants, reserves state, invokes CARM when valid policies conflict, and permits a connector to commit the side effect only after authorization.

The primary product guarantee is:

> A governed action is not intentionally committed through a conforming gateway unless the gateway verifies current delegated authority, mandatory obligations, conserved budgets, required approvals, revocation freshness, evidence requirements, and applicable local policy.

This guarantee is conditional on complete mediation: a governed agent must not have an alternate path to the protected tool or resource.

## 2. Product boundary

### 2.1 Product name and layers

- **Governance Capsule**: the unified product and open engineering project.
- **Governance Capsule Protocol (GCP)**: the framework-neutral interchange and lifecycle protocol candidate.
- **CARM**: the cascade-aware policy-conflict resolution engine embedded in the enforcement service.
- **CARM-SE**: the certified selective-automation extension to CARM.
- **Governance Control Plane**: enterprise policy, identity, approval, revocation, calibration, and audit administration.

GCP and CARM are not separate products. GCP preserves governance context and authority across boundaries; CARM decides how to handle conflicts at an action boundary. Neither is sufficient alone.

### 2.2 What is governed

The unit of enforcement is a proposed **governed action**, including:

- delegation or amendment of authority;
- allocation or consumption of a conserved budget;
- use of a scoped approval;
- agent-to-tool invocation;
- data disclosure or transmission;
- mutation of external state;
- payment or financial commitment;
- task completion, cancellation, or compensation; and
- other organization-registered consequential operations.

Internal model reasoning is not treated as an enforceable boundary. Model output becomes relevant when it is converted into a governed action proposal.

### 2.3 Explicit non-goals for the initial product

- Proving that a signed assertion is factually true.
- Determining legal compliance from law automatically.
- Inferring a complete cross-organization workflow graph.
- Guaranteeing that a human reviewer makes the correct decision.
- Allowing learned models to mint authority or bypass deterministic rules.
- Supporting cyclic workflows, multi-parent governance joins, or fully decentralized trust in v0.1.
- Claiming that an enforcement receipt proves real-world compliance or honest tool execution.

## 3. Design principles

1. **Models propose; deterministic components authorize.**
2. **Complete mediation is mandatory.** Every protected side effect passes through a trusted gateway.
3. **Protocol invalidity is not a policy conflict.** Invalid authority cannot be negotiated by CARM.
4. **Unknown is not false.** Missing topology is not zero reach; absent evidence is not negative evidence.
5. **A signature proves integrity and attribution, not truth.**
6. **Resolvability is not identifiability.** A safe resolution may exist even when available evidence cannot identify it.
7. **Stateful guarantees use atomic state.** Budgets, approval uses, replay, reservations, and revocation observations are not JSON-only checks.
8. **Adaptive automation has an expiring certification envelope.**
9. **Every guarantee names its assumptions and residual risk.**
10. **Receipts describe evaluated claims precisely and do not overclaim.**

## 4. Trust and threat model

### 4.1 Trusted computing base

The minimum trusted computing base contains:

- canonicalization, hashing, and signature verification;
- identity-to-verification-method authorization;
- schema and semantic validators;
- delegation, approval, amendment, and revocation state machines;
- transactional reservation and use-count storage;
- deterministic policy evaluation;
- the governed action gateway and connector credential boundary;
- enforcement and lifecycle receipt signing; and
- configuration and key material required by those components.

The TCB must not depend on an LLM response to establish a hard authorization fact.

### 4.2 Untrusted or advisory components

- agents and model outputs;
- natural-language policy extraction;
- semantic conflict suggestions;
- inferred workflow edges;
- learned cascade estimates;
- CARM-SE predictions outside their certification checks;
- generated explanations; and
- claims made by remote organizations unless separately trusted or attested.

These components may produce signed proposals or observations. The deterministic kernel decides how much authority, if any, those claims possess.

### 4.3 Primary threats

- authority expansion during delegation;
- mandatory-obligation removal or mutation;
- concurrent budget double allocation;
- replay or double use of approvals;
- stale, suppressed, or mis-targeted revocation status;
- role spoofing with another trusted key;
- bypass of the action gateway;
- time-of-check/time-of-use races;
- forged or incomplete dependency topology;
- cross-organization reach understatement;
- evidence corruption, staleness, or contradiction;
- CARM-SE distribution shift;
- threshold gaming near escalation boundaries;
- receipt omission or equivocation; and
- ambiguous connector outcomes after network failure.

## 5. System planes

### 5.1 Governance data plane

The data plane runs synchronously at action boundaries. It:

1. authenticates the caller and resolves the enforcement domain;
2. validates the capsule and supporting artifacts;
3. computes effective authority from inherited authority, local policy, and connector capability;
4. evaluates expiry, audience, replay, approvals, budgets, revocation, and evidence freshness;
5. evaluates applicable policies;
6. invokes CARM only when two or more valid policies conflict;
7. reserves consumable governance state atomically;
8. invokes the protected connector with gateway-held credentials;
9. records the observed outcome; and
10. issues signed enforcement and lifecycle receipts.

### 5.2 Governance control plane

The control plane manages:

- issuers, trust domains, keys, and identity-role bindings;
- versioned policy publication and rollback;
- approver groups and approval queues;
- revocation and lineage suspension;
- obligation and constraint registries;
- graph declarations and cross-domain exposure attestations;
- CARM configuration and thresholds;
- CARM-SE certification, promotion, expiry, and rollback;
- adapter and connector registration;
- audit search and receipt verification; and
- administrative changes, which themselves require governed authorization.

### 5.3 Evidence plane

The evidence plane stores or references decision-relevant facts with:

- evidence identifier and schema;
- source identity and verification method;
- collection method;
- subject, purpose, and permitted reuse;
- issue, observation, and expiry times;
- content digest and external URI;
- confidence and source class;
- contradiction relationships; and
- invalidation or supersession state.

Large evidence remains external where possible. Capsules and decisions carry digests and references rather than duplicating sensitive content.

## 6. Major components

### 6.1 GCP verification kernel

The kernel implements the portable invariants already defined by the formal model:

- authority attenuation;
- mandatory-obligation persistence;
- lineage integrity;
- temporal and delegation-depth attenuation;
- budget containment and aggregate allocation conservation;
- audience and replay checks;
- scoped approval and amendment authorization;
- revocation freshness; and
- deterministic rejection of unknown critical semantics.

The kernel returns structured facts and failures, not a prose judgment.

### 6.2 Governed Action Gateway

The gateway is the reference monitor and sole credential holder for protected tools in the first deployment profile. Agents receive logical tool handles, never unrestricted underlying credentials.

The gateway API is idempotent. Each proposal carries an `action_id` unique within its enforcement domain. Repeated submission returns the previously recorded state or continues recovery; it does not consume governance state twice.

### 6.3 Policy evaluation service

Runtime enforcement uses typed, versioned policies. Natural-language policy ingestion may be LLM-assisted, but promotion requires review and produces a deterministic intermediate representation.

A policy version includes:

- source and owner;
- applicability predicate;
- effect or required outcome;
- precedence class;
- negotiability and mandatory status;
- required evidence types;
- effective interval; and
- canonical digest.

### 6.4 Governance Graph

The Governance Graph is a versioned projection joining:

- tasks and capsule revisions;
- agents, runtimes, tools, and organizations;
- delegation and dependency edges;
- authority grants and obligations;
- policies and conflicts;
- budgets and reservations;
- evidence and approvals;
- decisions, actions, and receipts; and
- revocations and affected descendants.

Dependency edges include their semantics:

- required versus optional input;
- `AND`, `OR`, fallback, or unknown join type;
- timeout and failure behavior;
- declaring organization;
- declaration source and timestamp; and
- confidence or attestation state.

Graph snapshots used by a decision have stable digests. Unknown or stale topology increases uncertainty and can force escalation.

### 6.5 CARM baseline

CARM means **Cascade-Aware Resolution Mechanism**. It receives only conflicts among valid policies. Its baseline inputs are:

- proposed action;
- conflicting policy evaluations;
- severity and precedence information;
- governance-graph snapshot;
- estimated downstream reach and topology confidence;
- reversibility and side-effect class;
- local risk limits; and
- available evidence summary.

The paper's baseline modes remain:

- **Priority Enforcement (PE)**;
- **Negotiated Relaxation (NR)**; and
- **Escalation Boundary (EB)**.

At the product API, those modes map into a broader decision vocabulary:

- `ALLOW`;
- `ALLOW_WITH_CONTROLS`;
- `EVIDENCE_REQUIRED`;
- `APPROVAL_REQUIRED`;
- `SUSPEND`; and
- `BLOCK`.

`BLOCK` is used for protocol-invalid or non-negotiable policy outcomes. CARM does not relax protocol invariants. Outcome-aware PE must not silently commit a blocking policy-conflict result when the configured profile requires human fallback.

### 6.6 CARM-SE

CARM-SE processes cases that baseline CARM would send to EB. It may auto-resolve only when all of the following hold:

1. the input matches a promoted certification envelope;
2. required evidence is present, consistent, and fresh;
3. the resolver and feature versions match the certificate;
4. the certificate has not expired or been revoked;
5. the selected mode clears the configured selective-risk bound; and
6. no hard kernel rule or local policy forbids automation.

A certification envelope binds:

- resolver and feature-schema digests;
- workflow and policy-family scope;
- calibration-data digest and procedure;
- risk ceiling and statistical correction;
- sample-size and exclusion conditions;
- issue and expiry times;
- mandatory fallback; and
- approving authority and signature.

Automation rate is not treated as evidence that calibration remains valid. On incompatibility or expired calibration, CARM-SE falls back to baseline CARM.

### 6.7 RIG-aware Evidence Resolver

The Resolution Identifiability Gap (RIG) is represented as an executable abstention rule, not as another scoring model.

For each conflict family, an identifiability contract defines the decision-relevant facts needed to distinguish candidate resolutions. The resolver classifies facts as:

- available and valid;
- missing;
- stale;
- contradictory;
- outside permitted purpose; or
- supplied by an insufficiently trusted source.

It returns an `EvidenceRequirementSet`. The product may acquire evidence through governed connectors, request a scoped human assertion, or abstain. New evidence creates a new decision attempt; it does not mutate the prior receipt.

### 6.8 Receipt service

Every decision attempt emits an append-only signed receipt, including rejections and abstentions. A receipt binds:

- action and capsule digests;
- caller, subject, gateway, and connector identities;
- policy, graph, evidence, and calibration snapshots;
- validation results and deterministic error codes;
- conflicts and candidate modes;
- selected decision and controls;
- reservations and approvals consumed;
- timestamps and observed connector outcome; and
- prior receipt when part of a retry or recovery chain.

A receipt proves integrity and attribution of the runtime assertion. It does not prove factual truth, legal correctness, or honest external execution.

## 7. Action processing state machine

### 7.1 States

```text
PROPOSED
  -> VALIDATING
  -> REJECTED
  -> EVIDENCE_REQUIRED
  -> APPROVAL_REQUIRED
  -> AUTHORIZED
  -> RESERVED
  -> COMMITTING
  -> COMMITTED
  -> COMMIT_OUTCOME_UNKNOWN
  -> COMPENSATION_REQUIRED
  -> COMPENSATED
  -> FAILED
  -> SUSPENDED
  -> REVOKED
  -> EXPIRED
```

### 7.2 Required transition properties

- State transitions use optimistic concurrency or serializable transactions.
- `action_id` makes retries idempotent.
- Approval uses and budgets are reserved atomically with transition to `RESERVED`.
- Reservations are not automatically released after an ambiguous connector timeout.
- `COMMIT_OUTCOME_UNKNOWN` requires connector reconciliation before retry or release.
- Revocation prevents new authorization and suspends non-committed actions at their next enforceable boundary.
- Already committed irreversible effects are not rewritten; they may require compensation.
- Every terminal and waiting state has a signed lifecycle receipt.

### 7.3 Transaction boundary

The database transaction cannot generally include an external tool. The gateway therefore uses a reservation-and-reconciliation pattern:

1. validate and reserve governance state transactionally;
2. write an outbox/commit intent;
3. invoke the connector using `action_id` as its idempotency key where supported;
4. record the observed outcome;
5. reconcile unknown outcomes before releasing or retrying; and
6. initiate compensation when an irreversible action succeeded but later workflow requirements fail.

Exactly-once external execution is not assumed. The product provides effectively-once behavior only when the connector honors compatible idempotency semantics.

## 8. Decision ordering

The runtime evaluates in this order:

1. structural and cryptographic validity;
2. identity-role authorization;
3. lineage, audience, time, and replay;
4. revocation freshness;
5. authority and capability containment;
6. obligations, budgets, and approval prerequisites;
7. evidence applicability and freshness;
8. local and inherited policy evaluation;
9. CARM conflict resolution;
10. CARM-SE selective automation if eligible;
11. RIG-aware evidence acquisition or scoped escalation;
12. atomic reservation;
13. connector commitment; and
14. signed receipt emission.

Earlier failures cannot be overridden by later stages.

## 9. Public service contracts

### 9.1 Evaluate action

```text
POST /v1/actions:evaluate
```

Input:

- `action_id`;
- signed capsule and lineage references;
- action type, resource, parameters digest, and side-effect class;
- caller and intended connector;
- referenced approvals and evidence;
- workflow/dependency context; and
- requested policy profile.

Output:

- decision and controls;
- deterministic failures;
- conflict summary and cascade estimate;
- evidence requirements;
- reservation status;
- receipt; and
- continuation token for approval or evidence resubmission.

### 9.2 Commit action

```text
POST /v1/actions/{action_id}:commit
```

The initial deployment profile may combine evaluate and commit inside the gateway to prevent a client from presenting an authorization result to another tool or after its validity window. If split, the authorization is audience-bound, short-lived, single-use, and atomically consumed.

### 9.3 Delegate

```text
POST /v1/capsules/{capsule_id}:delegate
```

Creates and signs a child capsule only after atomic budget reservation and semantic validation.

### 9.4 Approve, revoke, and supply evidence

```text
POST /v1/approvals
POST /v1/revocations
POST /v1/evidence
```

These endpoints require governed administrative authority and produce signed artifacts plus audit receipts.

## 10. Initial persistence model

The first production-shaped implementation uses PostgreSQL as the authoritative state store. Minimum logical tables:

- `capsule_revisions`;
- `delegation_edges`;
- `budget_accounts` and `budget_reservations`;
- `approval_artifacts` and `approval_uses`;
- `revocation_events` and `status_observations`;
- `policy_versions` and `policy_evaluations`;
- `graph_nodes`, `graph_edges`, and `graph_snapshots`;
- `evidence_artifacts` and `evidence_relations`;
- `action_attempts`, `action_reservations`, and `commit_intents`;
- `enforcement_receipts` and `lifecycle_receipts`;
- `carm_certifications`; and
- `administrative_events`.

Append-only artifacts are immutable. Corrections supersede previous records and preserve history.

## 11. Deployment profile v0

The first usable product is centralized within one enforcement domain:

- one Governance Action Gateway;
- one PostgreSQL database;
- one policy evaluator;
- one receipt signer backed by a protected key;
- framework adapters that route all governed tools through the gateway;
- gateway-held connector credentials;
- a minimal approval and audit UI; and
- asynchronous workers for reconciliation and graph projection.

Cross-organization federation follows only after the single-domain semantics and failure recovery are proven.

## 12. Cross-organization profile direction

Remote organizations disclose the minimum information required for a decision. A future **Cascade Exposure Attestation** may bind:

- task or capsule digest;
- declaring domain;
- aggregate local reach;
- join-profile digest;
- declaration time and expiry;
- disclosure level; and
- signature.

The attestation proves who made an untampered claim. It does not prove the reach value is truthful. Audit sampling, observed receipt consistency, contractual trust, or stronger attestation are separate controls.

No profile passes bearer credentials through the delegation chain.

## 13. Reliability, security, and performance objectives

Initial engineering objectives, to be measured rather than advertised as achieved:

- deterministic evaluation for identical inputs and snapshots;
- p95 kernel validation below 25 ms excluding remote status and policy calls;
- p95 complete cached decision below 100 ms;
- no duplicate approval consumption under concurrent retries;
- no aggregate budget overallocation under concurrent delegation;
- 100% receipt linkage for attempted governed commits;
- fail-closed behavior for unavailable online-strict revocation status;
- recovery drill coverage for ambiguous connector outcomes;
- explicit topology and evidence confidence in every CARM decision; and
- zero paths from governed adapters to protected credentials outside the gateway.

Security work includes property testing, fuzzing, state-machine model checking, fault injection, dependency review, key rotation drills, and an external review before production claims.

## 14. Privacy and minimization

- Capsules carry only governance needed by the receiver.
- Sensitive evidence is referenced by digest and access-controlled URI.
- Receipts separate public verification fields from restricted evidence details.
- Cross-domain graph disclosure is aggregate by default.
- Retention is policy-bound and purpose-limited.
- Explanations are derived from structured decision facts and must not leak hidden policies or unrelated evidence.

## 15. First end-to-end product demonstration

The reference scenario is governed supplier onboarding:

1. an intake agent receives a root capsule;
2. work is delegated to compliance, finance, and risk agents with narrowed authority and preallocated budgets;
3. an agent proposes a sensitive cross-border data action;
4. the GCP kernel verifies that the proposal is structurally authorized;
5. CARM detects conflicting valid policies and estimates the downstream cascade;
6. CARM-SE checks its certification envelope;
7. the RIG resolver identifies missing decision-relevant evidence;
8. a governed connector obtains signed evidence or a human supplies scoped approval;
9. the action is reevaluated and committed through the gateway;
10. a mid-workflow revocation suspends affected descendants at their next action boundary;
11. unaffected work continues; and
12. signed receipts reconstruct the complete governance and decision lineage.

The demo must include one malicious or faulty child, one ambiguous connector failure, and one cross-framework boundary.

## 16. Delivery sequence

### Phase A: finish the trusted kernel

- complete amendment-diff verification;
- define signed active/revoked status responses;
- implement enforcement and lifecycle receipt builders/verifiers;
- add randomized property, fuzz, and concurrency tests.

### Phase B: governed action gateway

- implement the action state machine and PostgreSQL persistence;
- implement reservation, idempotency, outbox, and reconciliation;
- expose evaluate/commit/delegate/approve/revoke/evidence APIs;
- ensure the gateway exclusively controls one demonstration connector.

### Phase C: CARM baseline and Governance Graph

- implement typed policy conflicts;
- implement join-aware reach and topology confidence;
- map PE/NR/EB into product decisions;
- generate decision and governance-debt receipts.

### Phase D: evidence and selective automation

- implement evidence requirement sets and identifiability contracts;
- implement CARM-SE certification envelopes and fallback;
- reproduce the paper's baseline and selective-automation results before product claims.

### Phase E: adapters and demonstration

- integrate one agent framework and MCP;
- build the supplier-onboarding workflow and audit timeline;
- add a second framework and A2A binding;
- publish reproducible traces, latency, failures, and limitations.

## 17. Exit criteria for architecture stability

This RFC may advance beyond working status only when:

1. every protected demonstration action is completely mediated by the gateway;
2. the action state machine survives retry and fault-injection tests;
3. GCP invalidity cannot be relaxed by CARM or CARM-SE;
4. CARM decisions bind exact policy, graph, and evidence snapshots;
5. CARM-SE refuses inputs outside an active certification envelope;
6. RIG cases produce structured evidence requirements rather than guesses;
7. ambiguous external outcomes are reconciled without duplicate use or budget release;
8. receipts reconstruct the entire attempted action lineage; and
9. at least one independent reviewer can reproduce the demonstration from a clean environment.

## 18. Open design questions

- Which policy intermediate representation should be adopted or reused?
- Which connector classes can offer compatible idempotency guarantees?
- How should multi-dimensional risk budgets compose without implying false precision?
- What evidence trust vocabulary is small enough for interoperability?
- How should CARM handle multiple simultaneous conflicts with coupled resolutions?
- What graph disclosure is sufficient across organizations without exposing sensitive topology?
- Which state-machine properties should be model-checked before service implementation?
- What minimum sample and exchangeability evidence is required to promote a CARM-SE certificate?
- How are governance-debt entries closed, expired, or converted into mandatory remediation?
- Which portions of receipts can be disclosed to external verifiers?

These questions are deliberately visible. The architecture must not hide unresolved trust or distributed-systems problems behind model intelligence.
