# Progress Log

## 2026-08-11 - Project foundation

### Completed

- Established the mission and research question.
- Separated the Governance Capsule Model, GCP, and CARM.
- Defined initial scope and non-goals.
- Recorded foundational invariants.
- Defined the initial threat model.
- Created milestone exit criteria and go/no-go conditions.
- Created a structured landscape-research template.
- Recorded the decision to describe GCP as a protocol candidate until interoperability is demonstrated.

### Current hypothesis

Governance continuity across heterogeneous agent delegation boundaries is not comprehensively specified by current agent SDKs or interoperability protocols.

### Next work

Complete the primary-source landscape review and convert the working gap hypothesis into a supported, narrowed conclusion.

### Open questions

- What is the minimum useful common representation of authority across vendors?
- Which obligations can be transported without exposing confidential policy content?
- Should v0.1 support joins, or only tree-shaped delegation with preallocated budgets?
- Which identity and signing profile minimizes new infrastructure?
- How quickly must revocation propagate to be meaningful?

### Evidence produced

- `CHARTER.md`
- `ROADMAP.md`
- `research/landscape-matrix.md`
- `research/decisions/0001-project-positioning.md`

## 2026-08-11 - Milestone 0 landscape review

### Completed

- Reviewed OpenAI Agents SDK, Claude Agent SDK and Managed Agents, Google ADK, A2A, MCP, Microsoft Agent Framework, Amazon Bedrock/AgentCore, and LangGraph from primary sources.
- Compared native features, extension points, application-defined behavior, and missing protocol guarantees.
- Reviewed adjacent standards for fine-grained authorization, token exchange, workload identity, signed claims, and information-flow control.
- Identified Microsoft FIDES as a relevant near-neighbor rather than ignoring an overlapping idea.
- Replaced the preliminary research template with a completed comparison matrix.
- Produced a detailed source-backed landscape report.
- Recorded Decision 0002 narrowing GCP to task-governance continuity and constrained transformation.

### Result

The gap hypothesis survived, but became narrower and more credible.

GCP should not replace handoffs, guardrails, identity, OAuth, tracing, MCP, or A2A. It should define how task governance is inherited, attenuated, amended, divided, revoked, and evidenced across those systems.

### Integration direction

- A2A extension/profile for agent-to-agent task transport
- MCP profile for governed tool calls
- Framework-native hooks and middleware for enforcement
- Existing authorization, workload-identity, and signed-claims standards where applicable

### Next milestone

Formalize the minimal GCP model and turn four invariants into executable properties:

1. authority attenuation;
2. mandatory-obligation persistence;
3. lineage integrity; and
4. preallocated budget conservation for tree-shaped delegation.

### New evidence

- `research/milestone-0-landscape-report.md`
- `research/landscape-matrix.md`
- `research/decisions/0002-milestone-0-gap-and-integration.md`

## 2026-08-12 - Milestone 1 formal model

### Completed

- Defined the initial task, capsule, party, authority, obligation, budget, approval, amendment, receipt, and revocation concepts.
- Restricted v0.1 to rooted delegation trees with exactly one parent per child.
- Formalized authority attenuation, mandatory-obligation persistence, lineage integrity, and preallocated budget conservation.
- Defined supporting rules for audience, time, delegation depth, replay, and fail-closed unknown semantics.
- Added three explicit revocation freshness profiles: online-strict, bounded-stale, and offline-until-expiry.
- Defined cascading ancestor revocation and behavior for in-progress work.
- Mapped abuse cases to prevention, detection, or accepted residual risk.
- Defined 24 executable properties and generated-test coverage targets.
- Recorded Decision 0003.

### Key design result

A capsule cannot provide instantaneous revocation or prevent concurrent budget double spending by itself. Revocation requires authenticated status with an explicit freshness policy. Parallel allocation requires an atomic allocation authority or serialized ledger.

### Deferred deliberately

- Multi-parent governance joins
- Automatic unused-budget reclamation
- Type-specific obligation weakening
- Distributed consensus
- Proof that signed enforcement claims are truthful
- Compensation semantics for completed external side effects

### Next milestone

Translate the formal semantics into framework-independent schemas and canonical examples without weakening the invariants.

### New evidence

- `spec/formal-model-v0.1.md`
- `spec/executable-properties-v0.1.md`
- `research/milestone-1-threat-model.md`
- `research/decisions/0003-milestone-1-core-semantics.md`

## 2026-08-12 - Milestone 2 capsule data model

### Completed

- Defined seven framework-independent JSON Schema artifacts covering capsules, delegation proofs, approvals, amendments, revocations, enforcement decisions, and task lifecycle transitions.
- Selected JSON Schema 2020-12, RFC 8785 JCS, SHA-256 digests, and Ed25519 as the v0.1 wire profile.
- Used decimal strings for conserved quantities to avoid floating-point ambiguity.
- Required strict rejection of unknown core fields and deferred extensions until negotiation and downgrade rules exist.
- Separated structural validation from cross-document semantic enforcement.
- Added examples for issuance, delegation, constraint, approval, amendment, completion, rejection, and revocation.
- Added invalid fixtures for illegal root lineage, malformed freshness policy, authority expansion, obligation removal, and budget overallocation.
- Added a reproducible validation tool and recorded Decision 0004.

### Validation result

All seven schemas pass Draft 2020-12 self-checks. Nine valid fixtures are accepted, two structurally invalid fixtures are rejected, and three semantic-invalid manifests resolve to their expected deterministic error codes.

### Key design result

A valid JSON document is not necessarily a valid governance transition. Schema validation establishes shape; the Milestone 3 semantic validator must establish signatures, lineage, attenuation, obligation persistence, budget conservation, approval scope, and revocation freshness.

### Next milestone

Build the core reference library and executable conformance tests, beginning with canonicalization, hashing, signing, verification, and deterministic semantic error codes.

### New evidence

- `spec/wire-profile-v0.1.md`
- `schema/`
- `examples/`
- `tools/validate_schemas.py`
- `research/decisions/0004-milestone-2-wire-profile.md`

## 2026-08-15 - Milestone 3 first executable slice

### Completed

- Created the framework-neutral Python reference package.
- Implemented deterministic canonicalization for the GCP v0.1 JSON value domain.
- Implemented proof-excluded SHA-256 digests and Ed25519 signing and verification.
- Implemented a minimal trusted-key resolver.
- Implemented ordinary delegation checks for authority attenuation, mandatory-obligation persistence, parent binding, lineage cycles, child-budget containment, validity windows, and delegation depth.
- Implemented signed delegation-proof binding checks.
- Added deterministic error codes and 21 unit/adversarial tests.
- Preserved the distinction between schema fixtures with placeholder proofs and cryptographically valid test artifacts.
- Recorded Decision 0005.

### Test result

`python3 -m pytest`: 21 passed.

The independent Milestone 2 schema suite also remains green: nine valid fixtures accepted, two structural-invalid fixtures rejected, and three semantic-invalid manifests recognized.

### Learning

Stateless semantic verification and stateful governance enforcement are different components. A parent-child validator can prove attenuation and signed linkage for one transition, but it cannot truthfully claim aggregate budget conservation, replay prevention, or current revocation status without trusted shared state.

### Next work

Implement the atomic allocation ledger, replay/use registry, and revocation freshness evaluator before calling Milestone 3 complete.

### New evidence

- `src/gcp_reference/`
- `tests/`
- `docs/reference-library.md`
- `research/decisions/0005-reference-library-boundary.md`

## 2026-08-16 - Public repository launched

### Published

- Published the project at `https://github.com/Vignesh412/governance-capsule-protocol`.
- Made `main` the default branch.
- Included the charter, roadmap, primary-source research, formal model, schemas, examples, reference-library slice, tests, decision records, progress log, and build-in-public visuals.
- Excluded local caches, scratch outputs, secrets, and extracted third-party source material.
- Kept the repository all rights reserved until a license is selected deliberately.

### Verified

- The repository is publicly visible.
- The README, semantic validator, adversarial tests, and ignore rules are accessible from the default branch.
- The GitHub owner account has administrative and push access.

## 2026-08-16 - Milestone 3 stateful enforcement slice

### Completed

- Implemented an atomic process-local allocation ledger for aggregate sibling budgets.
- Implemented all-or-nothing batch allocation and duplicate-allocation rejection.
- Confirmed that allocations are not implicitly reclaimed.
- Implemented an atomic replay and use-count registry.
- Added capsule audience validation.
- Implemented `online-strict`, `bounded-stale`, and `offline-until-expiry` revocation evaluation.
- Added cascading ancestor-revocation checks and explicit offline residual-risk evidence.
- Added deterministic error codes for allocation conflicts, wrong audience, replay, revocation, stale or unavailable status, and disallowed offline execution.
- Recorded Decision 0006.

### Test result

`python3 -m pytest`: 39 passed.

The suite includes two-thread races for competing budget reservations and single-use authority. The independent schema suite remains green.

### Learning

Portable proof and shared enforcement state are complementary. The capsule and delegation proof establish what one transition claims. Atomic ledgers, use registries, and freshness-aware status services establish whether that transition may still be acted upon in a concurrent system.

### Remaining before Milestone 3 completion

- Cryptographically verify signed revocation artifacts through the status adapter.
- Implement approval consumption and amendment authorization.
- Integrate structural schema validation into the public API.
- Generate signed enforcement and lifecycle receipts.
- Add the required randomized property-test coverage.

## 2026-08-16 - Milestone 3 scoped-control slice

### Completed

- Integrated Draft 2020-12 structural validation into the public Python API with deterministic error details.
- Implemented verification and runtime adaptation of signed revocation records targeting one exact capsule revision.
- Required declared revocation issuers, approvers, and amendment authorities to be bound to explicitly permitted verification methods.
- Implemented approval validation for exact capsule digest, operation type, action, resource, amendment-change digest, validity window, and use limit.
- Implemented atomic approval consumption, including a concurrent single-use race test.
- Implemented amendment authorization over signed previous/result capsule digests, the approved change declaration, same capsule/task identity, and consecutive revision and sequence rules.
- Corrected the capsule schema so a lineage root may advance revision through amendment without acquiring a parent or delegator.
- Recorded Decision 0007.

### Test result

`python3 -m pytest`: 49 passed.

The independent schema suite remains green: nine valid fixtures accepted, two structurally invalid fixtures rejected, and three semantic-invalid manifests recognized.

### Learning

Trusting a key and trusting a claimed role are separate decisions. Signature verification proves possession of a private key; an enforcement domain must also bind the artifact's declared issuer, approver, or authority to the verification methods permitted to act in that role.

A signed revocation record proves revocation when one is present and effective. It does not prove that no revocation exists. A cryptographically complete online check therefore needs a signed active/revoked status-response profile, not only signed revocation events.

### Remaining before Milestone 3 completion

- Recompute declared amendment paths and old/new digests from the actual capsule diff.
- Define and verify signed active/revoked status responses.
- Generate signed enforcement and lifecycle receipts.
- Add the required randomized property-test coverage.

### New evidence

- `src/gcp_reference/schema.py`
- `src/gcp_reference/approval.py`
- `src/gcp_reference/revocation.py`
- `tests/test_protocol_controls.py`
- `research/decisions/0007-scoped-control-verification.md`

## 2026-08-19 - Unified product architecture checkpoint

### Completed

- Reframed Governance Capsule as one product rather than separate GCP and CARM efforts.
- Defined GCP as the portable governance contract, the Governed Action Gateway as the trusted reference monitor, and CARM as the Cascade-Aware Resolution Mechanism for conflicts among otherwise valid policies.
- Positioned CARM-SE behind an expiring certification envelope and made baseline CARM its mandatory fallback.
- Turned the Resolution Identifiability Gap into an executable evidence-sufficiency, acquisition, and abstention contract.
- Defined the trusted computing base and separated deterministic authorization from advisory model intelligence.
- Defined governance data, control, and evidence planes.
- Defined the versioned Governance Graph and topology-confidence requirements.
- Defined the governed action state machine, atomic reservations, idempotency, outbox, ambiguous connector outcomes, reconciliation, and compensation states.
- Selected a centralized PostgreSQL-backed deployment profile before cross-organization federation.
- Specified the supplier-onboarding flagship demonstration and revised the roadmap around one end-to-end product.
- Recorded Decision 0008.

### Key design result

A travelling capsule is not self-enforcing. It carries signed governance claims. The defensible product guarantee comes from complete mediation at a trusted action boundary: agents propose, the deterministic kernel verifies, CARM resolves valid-policy conflicts, CARM-SE automates only within certification, RIG requests evidence or abstains, and the gateway alone commits the protected side effect.

### Next work

Finish Milestone 3 with amendment-diff verification, signed active-status responses, signed receipt helpers, and randomized property coverage. Then begin the transactional Governed Action Gateway defined by the architecture RFC.

### New evidence

- `docs/product-architecture-rfc-v0.1.md`
- `research/decisions/0008-unified-product-architecture.md`

## 2026-08-19 - Competitive architecture checkpoint

### Completed

- Re-ran the competitive review against current primary specifications, repositories, and papers rather than relying on the 2026-08-11 framework comparison.
- Identified Microsoft Agent Governance Toolkit as the closest implementation baseline and a potential integration substrate.
- Compared SentinelAgent, Delegation Receipt Protocol, Agent Receipts Protocol, Human Escalation Mechanism, Policy Cards, CORA, ToolChain-CRC, and Conformal Selective Acting.
- Separated implemented/documented behavior from specified, planned, and not-found behavior.
- Retired novelty claims for monotonic delegation, generic pre-action policy enforcement, approvals, receipts, identity, adapters, budgets considered alone, and conformal execute/abstain control.
- Narrowed GCP to a task-governance continuity and interoperability profile.
- Chose to reuse or integrate existing identity, policy, approval, escalation, receipt, and adapter layers.
- Concentrated the original build on conserved cross-runtime task state, the transactional commit coordinator, Governance Graph, CARM, CARM-SE certification, RIG evidence contracts, and outcome recovery.
- Added falsifiable go/no-go criteria and a comparative vertical-slice experiment.
- Recorded Decision 0009.

### Key design result

The original primitives are becoming a category, not a moat. Product value must come from composing them into evidence-aware, cascade-aware governed execution and proving that the combination improves real decisions and recovery across heterogeneous systems.

## 2026-08-19 - First graph-sensitive comparative slice

### Completed

- Added a framework-neutral policy-runtime boundary intended for AGT ACS, OPA, Cedar, or another evaluator.
- Implemented a deterministic Governance Graph with DAG validation, snapshot digests, explicit AND/OR/UNKNOWN join semantics, and declaration confidence.
- Implemented join-aware downstream reach using the CARM paper's AND and OR weights.
- Implemented deterministic CARM conflict detection and PE, NR, and EB selection.
- Added outcome-aware rerouting so a tentative automated block requires escalation in the default profile.
- Added most-restrictive and fixed-priority baselines.
- Created a reproducible supplier-onboarding experiment and recorded Decision 0010.

### Test result

`python3 -m pytest`: 59 passed.

The independent schema suite remains green: nine valid fixtures accepted, two structurally invalid fixtures rejected, and three semantic-invalid manifests recognized.

### Result

With the same regulatory `ALLOW` and organizational `BLOCK` evaluations, most-restrictive always blocks and fixed priority always allows. CARM requires approval when the conflict occurs at the intake node with downstream reach 4, but selects priority enforcement and allows at the final node with downstream reach 0.

This establishes deterministic graph sensitivity, not decision correctness or superiority. No external governance runtime, human escalation execution, CARM-SE, or RIG behavior is included yet.

### Next work

Integrate Microsoft AGT ACS through the policy-runtime boundary, bind full decision receipts to policy/graph/evidence/configuration snapshots, and define outcome and review-burden measurements.

### New evidence

- `src/gcp_reference/governance_graph.py`
- `src/gcp_reference/policy.py`
- `src/gcp_reference/carm.py`
- `tests/test_carm.py`
- `tools/run_competitive_slice.py`
- `docs/competitive-slice-v0.1.md`
- `research/decisions/0010-graph-sensitive-comparative-slice.md`

## 2026-08-19 - Microsoft ACS adapter contract

### Completed

- Verified the current ACS architecture and Python host interfaces against Microsoft source at commit `7d0cef5d9820a865c3c19b07bd39ecf7053b58a1`.
- Added an optional, structurally typed ACS adapter without introducing a mandatory Microsoft dependency.
- Preserved `allow`, `warn`, `deny`, `escalate`, and `transform` rather than reducing the interface to a Boolean decision.
- Made warning audit and transformed-target application explicit downstream controls.
- Made ACS escalation a non-negotiable approval requirement at the CARM boundary.
- Preserved ACS evidence artefacts and stable reason codes while redacting runtime exception text.
- Added support for the synchronous ACS `HostSession` shape and mapping/object result forms.

### Test result

`python3 -m pytest`: 70 passed.

The schema suite remains green.

### Limitation

The reviewed ACS Python SDK `0.3.1b1` requires Python 3.11+. This workspace runs Python 3.9.6. The adapter is therefore source-contract tested but has not yet executed the native ACS runtime. We will not call this a completed external integration until the pinned live-manifest gate passes under Python 3.11+.

### Next work

Run a pinned native ACS manifest through `HostSession`, exercise all five verdicts, and bind the resulting policy evidence into a complete CARM decision receipt.

## 2026-08-19 - First Governed Action Gateway product slice

### Completed

- Implemented the in-memory governed-action state machine through validation, approval, reservation, commit, unknown outcome, reconciliation, rejection, and failure.
- Bound every action ID to one exact proposal digest and made identical retries return the recorded result.
- Placed an idempotent supplier connector exclusively behind the gateway interface.
- Ordered kernel verification before policy evaluation and connector access.
- Integrated normalized external-policy controls and CARM decisions.
- Signed experimental product receipts binding proposal, graph, policy, controls, decision, and result snapshots.
- Simulated supplier creation followed by a lost response and reconciled it without a second commit.

### Test result

`python3 -m pytest`: 77 passed, 1 native-ACS test skipped on local Python 3.9.

The schema suite remains green.

### Product result

The repository now contains an executable product-shaped path, not only schemas and isolated validators. One command demonstrates proposal-to-commit governance and ambiguous-outcome recovery.

### Limitations

State and transaction boundaries remain process-local. Full capsule, revocation, and scoped-approval artifacts are still injected through interfaces. The supplier connector is a reference implementation. The signed receipt is experimental and has not yet been reconciled with the frozen wire schema.

### New evidence

- `src/gcp_reference/gateway.py`
- `tests/test_gateway.py`
- `tools/run_gateway_demo.py`
- `docs/gateway-slice-v0.1.md`

## 2026-08-19 - Restart-safe gateway ledger

### Completed

- Refactored gateway state behind an action-store contract.
- Implemented a transactional SQLite store with action-ID uniqueness, WAL journaling, and full synchronous durability.
- Persisted proposal bindings, states, decisions, controls, snapshot digests, connector results, and signed receipts.
- Recreated the gateway with a new store connection after an ambiguous connector response.
- Reconciled the durable unknown state to committed without issuing another connector call.
- Verified that an action ID cannot be rebound to a different proposal after restart.

### Test result

`python3 -m pytest`: 79 passed, 1 native-ACS test skipped locally.

### Demonstrated result

One supplier was created, the response was lost, gateway state was closed and reopened, the action was reconciled, and an identical retry returned `COMMITTED`. Connector commit count remained one.

### Limitation

This proves restart-safe action-ledger behavior on one host. It does not yet prove multi-instance serialization, durable outbox recovery, or atomic composition with approval and budget reservations.

### New evidence

- `src/gcp_reference/persistence.py`
- `tools/run_durable_gateway_demo.py`
- `docs/durable-gateway-slice-v0.1.md`

## 2026-08-19 - Durable commit-intent recovery

### Completed

- Persisted the recoverable action proposal alongside every commit intent.
- Added pending-intent enumeration for `COMMITTING` and `COMMIT_OUTCOME_UNKNOWN`.
- Added digest verification before reconstructing a proposal for recovery.
- Added a restart worker that reconciles committed intents and commits only confirmed-not-committed intents.
- Fault-injected a process stop immediately before connector invocation.
- Fault-injected a process stop immediately after connector success but before gateway result persistence.

### Test result

`python3 -m pytest`: 81 passed, 1 native-ACS test skipped locally.

### Demonstrated result

The before-call crash produced zero connector calls before restart and exactly one after recovery. The after-success crash produced one connector call before restart and still one after recovery. Both scenarios ended with one committed supplier.

### Limitation

This is an explicitly invoked single-host recovery worker, not yet a leased asynchronous outbox service. Correctness still depends on authoritative connector reconciliation and action-ID idempotency.

### New evidence

- `tools/run_outbox_recovery_demo.py`
- `docs/commit-intent-recovery-v0.1.md`

## 2026-08-19 - Real signed-capsule gateway kernel

### Completed

- Replaced the gateway's permissive authorization callback in the product demo with a concrete signed-capsule verifier.
- Enforced schema, Ed25519/JCS proof, issuer/key role binding, audience, validity, revocation freshness, action/resource authority, constraints, mandatory pre-action obligations, and replay limits.
- Made identical action retries idempotent at the capsule-use boundary.
- Propagated verified kernel facts into the signed gateway receipt controls.
- Added negative end-to-end tests proving failures occur before policy evaluation and connector access.

### Test result

`python3 -m pytest`: 88 passed, 1 native-ACS test skipped locally.

### Demonstrated result

A freshly signed root capsule authorizes exactly one supplier-create path through kernel, local policy, gateway, and connector. Tampering, expiry, revocation, unauthorized action, unsatisfied obligation, and untrusted issuer-role binding produce deterministic rejection without downstream execution.

### Remaining work

Compose derived-capsule lineage and delegation proofs into the action boundary, persist replay and approval state transactionally, and define a signed active-status response profile.

### New evidence

- `src/gcp_reference/action_kernel.py`
- `tests/test_action_kernel.py`
- `tools/run_signed_capsule_gateway_demo.py`
- `docs/signed-capsule-gateway-v0.1.md`

## 2026-08-19 - Signed delegated-work gateway

### Completed

- Composed ordinary derived-capsule lineage into the live action boundary.
- Verified each capsule schema, signature, and issuer/key role.
- Verified continuous parent-child digest linkage and existing attenuation invariants.
- Verified delegation-proof content, signature, and delegator/key role.
- Evaluated leaf and cascading ancestor revocation before local policy.
- Added a signed one-hop intake-to-supplier-operations demonstration.

### Test result

`python3 -m pytest`: 92 passed, 1 native-ACS test skipped locally.

### Adversarial result

Child authority expansion, delegation-proof tampering, and cascading root revocation all reject before policy evaluation and supplier connector access.

### New evidence

- `tests/test_delegated_gateway.py`
- `tools/run_delegated_gateway_demo.py`
- `docs/delegated-gateway-v0.1.md`

### Next work

Finish the remaining trusted-kernel items, then build the competitive vertical slice with an existing policy runtime, one governed MCP action, a versioned graph snapshot, a reach-sensitive conflict, a RIG evidence request, and an ambiguous connector reconciliation.

### New evidence

- `research/competitive-architecture-report-2026-08-19.md`
- `research/decisions/0009-competitive-repositioning.md`

## 2026-08-19 - Cross-framework governed delegation proof

### Built

- Added a signed cross-framework GCP transport binding source runtime, destination runtime, exact proposal, complete delegation lineage, expiry, and a single-use nonce.
- Added an OpenAI Agents SDK handoff-shaped source adapter that stores governance in application-owned run context rather than model-generated metadata.
- Added a Google ADK before-tool-shaped receiving boundary that verifies transport before composing the existing delegated-capsule kernel.
- Carried cross-framework source, destination, transport, and lineage controls into the signed gateway receipt.
- Added deterministic rejection coverage for transport tampering, nonce replay, authority expansion, and cascading root revocation.
- Added the cross-framework proof as the first guided visual-demo scenario and a standalone terminal demonstration.
- Generated an official Google ADK prototype scaffold in a temporary directory and adapted only the callback contracts required by the existing product architecture.

### Verification

`python3 -m pytest`: 100 passed, 2 optional native integration gates skipped locally.

`python3 tools/run_cross_framework_demo.py`: OpenAI-to-Google-ADK route committed once with verified lineage, three cross-framework controls, one connector call, and one supplier.

### Claim boundary

This is a deterministic SDK-contract proof, not yet a native model-driven SDK execution result. The native construction test is ready behind the `frameworks` extra, but the restricted sandbox could not download its PyPI dependencies.

## 2026-08-19 - Live native product showcase implementation

### Built

- Added an optional real OpenAI Agents SDK to Google ADK execution path.
- Kept governance in trusted application state: the OpenAI model can request delegation but cannot create authority.
- Passed the signed transport through private ADK session state and bound the Google tool request to the exact transported proposal.
- Intercepted the protected ADK tool before its original body and routed accepted work through the Governed Action Gateway.
- Added progressive NDJSON runtime events so the browser shows OpenAI, signing, ADK verification, and gateway execution while they occur.
- Added explicit readiness reporting and a deterministic fallback when SDKs or credentials are unavailable.

### Verification

The injected-runtime allow test commits exactly once; the injected-runtime revocation test runs both boundaries with zero connector calls; and both prove model output is not used as governance. The installed Google ADK callback/agent constructor gate passes. The complete result is 104 tests passed and 2 optional integrations skipped. Provider-backed execution remains unverified locally because credentials are absent and the restricted workspace could not download `openai-agents` from PyPI.

### Claim boundary

The native product path is implemented and testable with credentials. Until a credentialed run completes, the evidence supports the orchestration and enforcement contract—not a claim that both provider APIs were executed in this workspace.

## 2026-08-19 - Contract integrity and runtime judgment separated

### Built

- Added an `Authorized, but risky` OpenAI-to-Google-ADK deterministic scenario.
- Kept the signed delegation completely valid: authority narrows correctly, the audit obligation survives, the child budget is contained, and no ancestor is revoked.
- Added trusted runtime evidence representing an unresolved possible sanctions match.
- Normalized organizational allow and regulatory block evidence through the existing CARM policy-runtime boundary.
- Routed the resulting high-severity conflict to human approval with zero connector calls and zero side effects.
- Added a three-part UI result: `GCP VERIFIED`, `CARM RISK_DETECTED`, and `ACTION PAUSED`.
- Documented that GCP proves contract integrity, while neither GCP nor CARM proves the truth of arbitrary tool output or catches every coherent-but-flawed plan.

### Verification

`python3 -m pytest`: 105 passed, 2 optional integrations skipped.

The new scenario returns `APPROVAL_REQUIRED`, reason
`CARM_AUTOMATED_BLOCK_REROUTED`, retains both audit and human-review controls,
and leaves the protected supplier connector untouched.

### Claim boundary

CARM acts on trusted, normalized screening evidence in this scenario. It does
not independently discover the sanctions risk and this result is not evidence
of general plan-correctness or AI-safety capability.
