# Competitive Architecture Report

Date: 2026-08-19  
Status: Primary-source checkpoint  
Scope: Governance Capsule, GCP, CARM, CARM-SE, and RIG-aware evidence handling

## Executive decision

Proceed, but reposition and integrate.

The market and research landscape has moved materially beyond the project's 2026-08-11 review. The original primitives are no longer a defensible product moat by themselves. Monotonic delegation, pre-action policy enforcement, scoped approval, revocation, budget controls, cryptographic receipts, human-escalation protocols, framework adapters, and conformal action gating are all implemented or actively specified elsewhere.

The closest implementation is Microsoft's open-source Agent Governance Toolkit (AGT). Its current repository documents deterministic action interception, delegation scope chains, revocation, policy-as-code, action-bound approval work, audit chains, MCP and A2A bridges, cost/token controls, saga orchestration, and adapters across major agent frameworks. SentinelAgent independently formalizes authority narrowing, policy preservation, forensic reconstructibility, cascade containment, and a non-LLM delegation authority service. Several receipt and escalation specifications cover additional parts of the original GCP scope.

No reviewed source was found to combine all of the following as one implemented system:

1. task-bound governance continuity across heterogeneous runtimes;
2. conserved parent-child governance state;
3. graph snapshots with join semantics and topology confidence;
4. resolution of valid-policy conflicts using downstream cascade consequences;
5. certified selective automation over those conflict resolutions;
6. executable evidence-identifiability contracts;
7. governed evidence acquisition and reevaluation; and
8. explicit ambiguous-commit reconciliation tied to governance reservations and receipts.

The product should therefore center on:

> **Evidence-aware, cascade-aware governed execution across heterogeneous multi-agent workflows.**

GCP remains useful as a small interoperability and task-continuity profile. It should not attempt to become a universal policy engine, identity system, generic approval protocol, or generic receipt standard.

## 1. Method and evidence rules

### 1.1 Review questions

Each system was evaluated for:

- portable task-bound governance;
- monotonic authority delegation;
- mandatory-obligation persistence;
- conserved parent-child budgets;
- complete action-boundary mediation;
- action-bound approval and atomic consumption;
- revocation and descendant behavior;
- signed or tamper-evident receipts;
- durable action lifecycle and ambiguous outcomes;
- workflow-graph and join semantics;
- graph-wide policy-conflict resolution;
- calibrated selective automation;
- evidence sufficiency or identifiability;
- framework and protocol interoperability; and
- implementation versus specification status.

### 1.2 Status vocabulary

- **Implemented/documented**: an official source repository documents runnable code or a current package surface. This report does not independently certify every upstream claim.
- **Specified**: a normative or research document defines behavior, but production implementation was not established from the reviewed source.
- **Planned**: an official ADR, limitation, issue, or roadmap describes future work.
- **Not found**: the reviewed primary sources did not establish the capability. This is not proof of global absence.

### 1.3 Important evidence caution

Repository README performance, test-count, compliance, and security claims are vendor or maintainer assertions unless independently reproduced. This report uses them to establish project scope, not to certify correctness.

## 2. Direct competitor: Microsoft Agent Governance Toolkit

### 2.1 What exists

AGT is an MIT-licensed public-preview project maintained by Microsoft. Its official repository describes packages for Python, TypeScript, .NET, Rust, and Go, plus integrations for OpenAI Agents SDK, Google ADK, LangGraph/LangChain, CrewAI, Microsoft Agent Framework, MCP, and other systems.

The repository documents:

- deterministic interception before agent actions;
- identity, capability grants, and scope chains;
- monotonic capability narrowing and delegation depth;
- credential and trust revocation;
- YAML/JSON policies, OPA/Rego, and a stateless Agent Control Specification;
- allow, deny, transform, warn, and escalation outcomes;
- hash-chain/Merkle audit mechanisms;
- cost, token, collective, SLO, and error-budget controls;
- MCP and A2A bridges;
- saga orchestration, circuit breakers, and kill switches; and
- a broad framework-adapter surface.

Primary evidence:

- [Official AGT repository](https://github.com/microsoft/agent-governance-toolkit), reviewed 2026-08-19.
- [AGT FAQ and release positioning](https://github.com/microsoft/agent-governance-toolkit/blob/main/FAQ.md), reviewed 2026-08-19.
- [AgentMesh architecture](https://github.com/microsoft/agent-governance-toolkit/blob/main/agent-governance-python/agent-mesh/ARCHITECTURE.md), reviewed 2026-08-19.
- [AgentMesh identity and trust specification](https://github.com/microsoft/agent-governance-toolkit/blob/main/docs/specs/AGENTMESH-IDENTITY-TRUST-1.0.md), reviewed 2026-08-19.
- [Agent Control Specification](https://github.com/microsoft/agent-governance-toolkit/blob/main/docs/packages/agent-control-specification.md), reviewed 2026-08-19.
- [Tutorial index: delegation, budgets, and collective policies](https://github.com/microsoft/agent-governance-toolkit/blob/main/docs/tutorials/README.md), reviewed 2026-08-19.

### 2.2 Action-bound approval overlap

AGT's ADR 0030 defines a versioned action-bound approval protocol with:

- canonical action digests;
- exact agent, subject, operation, target, schema, resource, and parameter binding;
- policy and approval-chain version binding;
- durable pending state;
- authenticated approver identities;
- append-only approval entries;
- expiry, cancellation, and fail-closed timeout;
- idempotent delivery;
- execution-time revalidation; and
- atomic one-time consumption at the execution/idempotency boundary.

The ADR uses future-tense implementation steps and acceptance criteria, so this report classifies the complete shared protocol as **specified/in progress**, not fully proven shipped across every adapter.

Primary evidence: [AGT action-bound approval ADR 0030](https://github.com/microsoft/agent-governance-toolkit/blob/main/docs/adr/0030-action-bound-approval-protocol.md), reviewed 2026-08-19.

### 2.3 Security boundary overlap and difference

The AGT Agent Control Specification is explicit that it protects only mediated paths and that the host owns I/O. Its security model says direct calls that bypass the runtime are not protected, a host may ignore the verdict, and ACS does not provide durable session state, backend authorization, idempotency, payment controls, or compensation.

That is the strongest reason to retain the Governance Capsule **Governed Action Gateway**: the first product profile should hold connector credentials and own the commit coordinator instead of returning a verdict to an untrusted host. However, AGT also contains MCP gateway and runtime components, so the difference must be demonstrated with bypass and ambiguous-outcome tests rather than asserted from architecture diagrams.

Primary evidence:

- [AGT policy-engine security model](https://github.com/microsoft/agent-governance-toolkit/blob/main/policy-engine/docs/security-model.md), reviewed 2026-08-19.
- [AGT known limitations](https://github.com/microsoft/agent-governance-toolkit/blob/main/docs/LIMITATIONS.md), reviewed 2026-08-19.

### 2.4 What was not found in AGT

The reviewed sources did not establish an implemented mechanism equivalent to:

- mandatory task-obligation inheritance across heterogeneous runtimes;
- exact conserved parent-child allocation across cost, token, time, and risk dimensions;
- a signed task capsule revision and amendment lifecycle shared across vendors;
- graph snapshots carrying explicit join semantics and topology confidence into each decision;
- PE/NR/EB selection based on valid-policy severity and downstream reach;
- CARM-SE-style calibrated selective resolution of policy conflicts;
- RIG-style executable identifiability requirements and evidence acquisition; or
- one governance reservation state machine linking unknown external outcomes to reconciliation.

AGT does have circuit breakers, cascade revocation, workflow-policy plans, trust scoring, and SRE concepts. Those are adjacent and must not be inaccurately described as absent graph reasoning.

## 3. Near-direct research competitor: SentinelAgent

SentinelAgent introduces a Delegation Chain Calculus and Intent-Preserving Delegation Protocol enforced by a non-LLM Delegation Authority Service. Its deterministic properties include:

- authority narrowing;
- policy preservation;
- forensic reconstructibility;
- cascade containment;
- scope-action conformance; and
- output-schema conformance.

The paper reports TLA+ model checking and a live LangChain integration. This overlaps strongly with the original GCP kernel and invalidates any broad claim that formally verified delegation-chain enforcement is untouched.

The reviewed paper did not establish conserved task-budget allocation, approval/amendment/revocation artifacts equivalent to the full GCP lifecycle, graph-reach-conditioned policy-conflict resolution, CARM-SE, or RIG evidence contracts.

Primary evidence: [SentinelAgent paper, arXiv:2604.02767](https://arxiv.org/abs/2604.02767), reviewed 2026-08-19.

## 4. Authorization and receipt protocols

### 4.1 Delegation Receipt Protocol

The Delegation Receipt Protocol (DRP) Internet-Draft defines a user-signed pre-execution Authorization Object containing scope, boundaries, a validity window, operator-instruction hash, and model-state commitment. It requires anchoring to an append-only log before agent execution and defines linked micro-receipts.

DRP focuses on user-to-operator authorization integrity. It is complementary to downstream workload identity and does not establish the complete task-governance, budget, obligation, graph, or conflict-resolution model proposed here.

It is an individual Internet-Draft with no IETF endorsement or formal standing.

Primary evidence: [Delegation Receipt Protocol draft-04](https://datatracker.ietf.org/doc/draft-nelson-agent-delegation-receipts/04/), reviewed 2026-08-19.

### 4.2 Agent Receipts Protocol

Agent Receipts Protocol v0.4 defines signed action receipts with:

- authorization context;
- parent delegation references;
- chain identifiers and monotonic sequence;
- previous-receipt hashes;
- idempotency keys;
- success, failure, and pending outcomes;
- before/after state hashes;
- reversibility and reversal references; and
- optional trusted timestamps.

This is sufficiently close to the planned generic receipt layer that GCP should not invent an incompatible receipt format without first testing whether a governance profile or extension can carry GCP policy, graph, evidence, and calibration bindings.

Primary evidence: [Agent Receipts Protocol v0.4](https://agentreceipts.ai/spec/v0.4.0/), reviewed 2026-08-19.

### 4.3 Human Escalation Mechanism

The HEM Internet-Draft defines a Governance Execution Controller, formal `HEM_PENDING` behavior, structured escalation requests, ordered human designation chains, a prohibition on state transitions while pending, policy rationale declarations, and decision rationale records.

HEM overlaps with approval, suspension, and human escalation. GCP should map to or extend compatible lifecycle semantics rather than define a competing generic human-escalation protocol prematurely.

HEM is also an individual Internet-Draft and is not an adopted IETF standard.

Primary evidence: [Human Escalation Mechanism draft-05](https://datatracker.ietf.org/doc/draft-sato-soos-hem/), reviewed 2026-08-19.

## 5. Portable policy artifacts

Policy Cards define a JSON-Schema-based deployment artifact containing allow/deny rules, obligations, escalation requirements, evidence requirements, time-bound exceptions, and mappings to NIST AI RMF, ISO/IEC 42001, and the EU AI Act.

Policy Cards attach normative policy to a deployed agent. Governance Capsules attach the effective governance state to a task revision and delegation lineage. The distinction remains meaningful, but obligation and evidence vocabularies should be compared before creating overlapping schemas.

Primary evidence: [Policy Cards paper, arXiv:2510.24383](https://arxiv.org/abs/2510.24383), reviewed 2026-08-19.

## 6. Selective risk-control competitors

### 6.1 CORA

CORA is a post-policy, pre-action safety controller for mobile GUI agents. It uses an action-conditional Guardian, conformal risk control, execute/abstain decisions, and a diagnostic intervention model. It demonstrates that calibrated pre-action selective execution is already an active agent-safety direction.

CORA is action- and domain-specific; it does not provide delegated governance continuity, a task-governance graph, or valid-policy conflict cascades.

Primary evidence: [CORA paper, arXiv:2604.09155](https://arxiv.org/abs/2604.09155), reviewed 2026-08-19.

### 6.2 ToolChain-CRC

ToolChain-CRC treats an entire retrieval/tool-use trajectory as the calibration unit, builds step-level risk diagnostics, and adds drift-aware and anytime escalation behavior. It is particularly relevant to CARM-SE because it addresses upstream evidence and tool risks that final-action calibration can miss.

It does not define portable authority, conserved delegation state, graph-wide policy-conflict resolution, or RIG-style normative fact requirements.

Primary evidence: [ToolChain-CRC paper, arXiv:2606.18467](https://arxiv.org/abs/2606.18467), reviewed 2026-08-19.

### 6.3 Conformal Selective Acting

Conformal Selective Acting studies anytime-valid selective-risk control for adaptive specialist models. Its statistical methods may be relevant to future CARM-SE certification under online updates. It is not a governance protocol or multi-agent conflict-resolution product.

Primary evidence: [Conformal Selective Acting, arXiv:2605.20270](https://arxiv.org/abs/2605.20270), reviewed 2026-08-19.

## 7. Capability matrix

Legend: `I` implemented/documented; `S` specified or research-demonstrated; `P` partial/adjacent; `-` not established in reviewed sources.

| System | Task governance | Authority narrowing | Obligation continuity | Conserved child budgets | Action boundary | Scoped approval | Revocation | Verifiable receipts | Graph conflict cascade | Selective risk | RIG evidence |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Microsoft AGT | P | I | P | P | I/P | S/I | I | I/P | P | - | - |
| SentinelAgent/IPDP | P | S | S | - | S | - | P | S | P | P intent | - |
| DRP | P | P | P boundaries | - | S | P user signing | - | S | - | - | - |
| Agent Receipts v0.4 | - | P references | - | - | P proxy/SDK | P auth context | - | S/I | - | - | - |
| HEM | - | - | P policy trigger | P exhausted budget trigger | S | S | P terminal state | S | - | - | P human rationale |
| Policy Cards | P agent-bound | - | S | - | P integration | S | P versioning | P audit linkage | - | - | S evidence fields |
| CORA | - | - | - | P risk budget | S | P confirm | - | P diagnostics | - | S | P diagnostics |
| ToolChain-CRC | - | - | - | P risk target | P trajectory gate | - | - | P diagnostics | P trajectory | S | P evidence risk |
| Governance Capsule current code | S/I kernel | I | I | I process-local | - | I process-local | I/P | schema only | research only | research only | research only |

The matrix compares capability shape, not maturity or correctness. `I` does not mean independently audited. Mixed cells indicate separate components or a documented boundary between shipped and in-progress behavior.

## 8. Claims that must change

### 8.1 Claims to retire

Do not claim novelty for:

- monotonic agent delegation;
- pre-tool deterministic enforcement;
- policy-as-code for agents;
- human approval before actions;
- signed or hash-chained receipts;
- agent/workload identity and revocation;
- cost or token controls considered alone;
- framework-neutral governance middleware;
- MCP governance gateways;
- generic conformal execute/abstain control; or
- formal delegation-chain verification.

### 8.2 Claims that remain testable

The project may test, but must not yet advertise as proven:

- one portable task-governance profile combining authority, mandatory obligations, conserved allocations, approvals, amendments, revocation, and evidence references;
- consistent semantics when the same governed task crosses independent runtimes;
- graph-reach-conditioned resolution of valid-policy conflicts;
- join-aware and uncertainty-aware cascade decisions across organizational boundaries;
- CARM-SE selective automation certified for exact policy, graph, evidence, and workflow scopes;
- RIG-aware minimum evidence requirements and governed evidence acquisition;
- preservation of governance reservations across ambiguous external outcomes; and
- receipts that bind the full policy/graph/evidence/calibration/commit context.

## 9. Build, integrate, or defer

| Layer | Decision | Reason |
|---|---|---|
| Workload/user identity | Reuse | Use SPIFFE, OIDC, OAuth, existing key registries, or AGT identity adapters. |
| Generic policy engine | Integrate | Use ACS/OPA/Cedar behind a stable adapter; do not create another policy language. |
| Major framework adapters | Reuse first | Start with one native adapter and one AGT integration; do not race AGT's adapter count. |
| MCP/A2A transport | Extend | Define narrow GCP bindings over existing protocol extension points. |
| Human escalation lifecycle | Align | Map to HEM concepts and AGT action-bound approval where compatible. |
| Generic action receipt | Profile/extend | Evaluate Agent Receipts v0.4 before finalizing a competing format. |
| GCP task capsule | Build narrowly | Retain only task continuity, lineage, obligations, conserved allocations, and references needed across runtimes. |
| Transactional commit coordinator | Build | Needed to own credentials, reservations, idempotency, unknown outcomes, and reconciliation. |
| Governance Graph | Build | Core differentiation: versioned dependency, governance, evidence, and decision projection. |
| CARM baseline | Build and reproduce | Implement the paper's mechanism and compare with most-restrictive and local-policy baselines. |
| CARM-SE certification | Build after baseline | Distinctive only if certification scope, shift failure, expiry, and fallback are executable. |
| RIG evidence contracts | Build | Make missing/stale/conflicting evidence operational rather than explanatory prose. |
| Universal legal interpretation | Do not build | Outside scope and not safely automatable as a generic product claim. |
| Fully decentralized federation | Defer | Prove centralized state and recovery first. |

## 10. Recommended product architecture after comparison

```text
Existing agent frameworks and protocols
        OpenAI / ADK / LangGraph / A2A / MCP
                         |
        Existing governance and policy runtimes
             AGT ACS / OPA / Cedar / IAM
                         |
             GCP task-continuity profile
      lineage / obligations / allocations / evidence refs
                         |
             Governed Commit Coordinator
       credentials / reservations / idempotency / recovery
                         |
                 Governance Graph
      dependencies / joins / policies / evidence / receipts
                         |
              CARM -> CARM-SE -> RIG
       cascade resolution / certification / evidence gap
                         |
       Profiled receipts + external verification
```

This architecture treats existing systems as substrates rather than competitors to reimplement. Governance Capsule adds value only where it composes information and guarantees that those systems do not already share.

## 11. Product moat hypothesis

The moat is not a schema or a single policy algorithm. It would need to emerge from:

- a high-quality Governance Graph built from real heterogeneous executions;
- verified mappings between task governance and existing policy/identity systems;
- reproducible cascade and intervention benchmarks;
- decision-relevant evidence schemas and acquisition workflows;
- CARM-SE certification and drift/fallback evidence;
- outcome reconciliation across real tools; and
- a conformance corpus spanning multiple independent runtimes.

This is a systems-and-evidence moat. It cannot be established by naming a protocol.

## 12. Go/no-go conditions

### Proceed now if

Within the next two milestones the project can demonstrate:

1. a governance property preserved across two runtimes that AGT or either runtime does not natively preserve end to end;
2. a CARM decision that materially differs from local or most-restrictive policy because of verified downstream graph consequences;
3. a RIG case where the system requests a specific missing fact, reevaluates, and safely resolves or abstains;
4. an ambiguous external outcome reconciled without duplicate approval or budget release; and
5. integration with at least one existing governance runtime rather than only a greenfield stack.

### Narrow or stop if

- GCP reduces to a renamed capability token or receipt wrapper;
- the Governance Graph cannot be populated reliably enough to improve decisions;
- CARM does not outperform simpler baselines under realistic non-oracle assumptions;
- CARM-SE cannot maintain a useful certification envelope under measured drift;
- RIG evidence contracts remain bespoke prompts instead of executable schemas; or
- an existing project implements the combined graph/evidence/recovery layer more credibly before this project demonstrates it.

## 13. Immediate next experiment

Do not build a full standalone platform next.

Build a **competitive vertical slice**:

1. run one two-agent supplier workflow through Microsoft AGT or its ACS policy runtime;
2. attach the current GCP capsule only for task continuity, obligations, and conserved child allocation;
3. route one consequential MCP action through our commit coordinator;
4. record a versioned Governance Graph snapshot;
5. create one valid-policy conflict whose correct handling changes with downstream reach;
6. compare most-restrictive, AGT/local, CARM, and human decisions;
7. create one missing-evidence RIG case;
8. simulate one ambiguous connector timeout and reconciliation; and
9. emit a receipt mapped to Agent Receipts fields plus explicit GCP extensions.

The result will show whether the proposed differentiation is real, measurable, and composable with the strongest adjacent implementation.

## 14. Final conclusion

Governance Capsule is still worth pursuing, but not under the broad claim that governance continuity primitives are missing everywhere. They are rapidly being built.

The defensible opportunity is to connect those primitives into a cross-runtime system that reasons about downstream consequences, knows when evidence is insufficient, acquires the missing facts, controls the actual commit boundary, and leaves verifiable decision evidence.

The next proof must be comparative. A greenfield demo that ignores AGT, SentinelAgent, current receipt protocols, and conformal action controllers would no longer establish novelty or product value.
