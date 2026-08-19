# Project Charter

## Mission

Develop and test a vendor-neutral mechanism for preserving verifiable governance across delegated AI work.

## Problem statement

Agent frameworks commonly govern the currently executing agent through permissions, guardrails, middleware, identity, or platform policy. When work is delegated, the continuity of the original authority, obligations, approvals, budgets, and audit lineage is often left to application-specific state and code.

The project investigates whether those properties can be represented and enforced as a portable governance contract attached to the task rather than to a particular agent implementation.

## Research question

Can a governed task cross heterogeneous agent runtimes while maintaining verifiable, authority-attenuating, obligation-preserving, revocable, and auditable delegation semantics?

## Initial claims to test

1. No reviewed implementation yet combines cross-runtime task-governance continuity with graph-wide conflict consequences, certified selective automation, evidence-identifiability contracts, and governed commit recovery.
2. A portable capsule can express a useful common governance subset without embedding entire enterprise policy systems.
3. Deterministic middleware can enforce capsule invariants independently of model behavior.
4. The same capsule semantics can operate across at least two independent agent runtimes and one tool protocol.
5. The security and latency overhead is acceptable for typical multi-agent workflows.

## In scope for v0.1

- Agent-to-agent task delegation
- Agent-to-tool invocation
- Task identity and delegation lineage
- Scoped authority over actions and resources
- Mandatory obligations and constraints
- Cost, token, risk, time, and delegation-depth budgets
- Human approval requirements
- Capsule validity, replay protection, and revocation
- Signed delegation proofs and enforcement receipts
- A2A and MCP bindings
- Reference adapters for two agent frameworks

## Explicit non-goals for v0.1

- Interpreting laws or determining legal compliance
- Creating a universal enterprise policy language
- Governing model training or dataset development
- Replacing identity providers, OAuth, IAM, MCP, or A2A
- Passing bearer credentials through delegation chains
- Fully decentralized trust or global key discovery
- Zero-knowledge policy proofs
- Cyclic workflow support
- Assuming that human approval is necessarily correct

## Intended architecture

### Governance Capsule Model

Defines the current governance contract for a task: identity, provenance, authority, obligations, constraints, budgets, approvals, validity, and integrity commitments.

### Governance Capsule Protocol

Defines discovery, offer, validation, acceptance, constrained acceptance, approval, rejection, delegation, receipt, completion, cancellation, and revocation behavior.

### Governed Action Gateway

Acts as the trusted reference monitor before consequential side effects. It validates GCP artifacts, reserves state atomically, invokes protected connectors with gateway-held credentials, reconciles ambiguous outcomes, and issues signed receipts.

### CARM conflict-resolution runtime

CARM means **Cascade-Aware Resolution Mechanism**. It handles conflicts among otherwise valid policies using severity, downstream reach, topology confidence, and evidence. CARM-SE may selectively automate escalation candidates only within an active certification envelope. RIG-aware evidence handling requests missing decision-relevant facts or abstains when the correct resolution cannot be identified.

Protocol-invalid authority, signatures, budgets, approvals, revocation status, or mandatory obligations are rejected before CARM and cannot be negotiated.

## Foundational invariants

### Authority attenuation

The effective authority of a child task must not exceed either the parent task's delegable authority or the receiver's locally permitted authority.

### Obligation persistence

A mandatory obligation cannot disappear during ordinary delegation. Removing or weakening one requires an explicitly authorized amendment with an auditable rationale.

### Budget conservation

The sum of allocations to child tasks must not exceed the parent's remaining delegable budget.

### Lineage integrity

Every derived capsule must cryptographically bind to its parent capsule.

### Audience restriction

A capsule can authorize only its intended subject or audience.

### Temporal attenuation

A normally delegated child cannot outlive its parent.

### Delegation attenuation

Every handoff must reduce or exhaust the remaining delegation depth.

### Fail-closed validation

Invalid, expired, revoked, replayed, unsupported, or unverifiable capsules cannot authorize execution.

## Threat model for the first prototype

We assume:

- models and model-produced content are untrusted;
- an agent may attempt to broaden permissions or discard obligations;
- messages may be modified, replayed, delayed, or reordered;
- a capsule may be presented to the wrong audience;
- parallel children may attempt to spend the same budget;
- a participant may omit an unfavorable event from the history;
- issuer and enforcement-runtime signing keys are initially trusted and preconfigured;
- deterministic enforcement code and its key store are within the trusted computing base.

The first prototype does not prove that a signed assertion is truthful. It proves who asserted it, that it has not been altered, and whether its transformation follows the protocol rules.

## Go/no-go criteria

Continue toward a public protocol draft only if the prototype demonstrates:

1. One governance property not natively guaranteed by either integrated framework.
2. Identical capsule semantics across two independent agent runtimes.
3. Deterministic rejection of unauthorized transformations.
4. An end-to-end verifiable delegation and receipt chain.
5. Measured overhead compatible with interactive agent workflows.

## Principles

- Enforce outside the model.
- Reuse established identity, authorization, cryptographic, and transport standards.
- Complement MCP and A2A rather than replace them.
- Keep the portable envelope small; store detailed evidence externally when possible.
- Separate what is observed from what is claimed.
- Publish limitations and failed experiments.
- Require interoperable implementations before describing GCP as a standard.
- Integrate strong existing governance primitives instead of recreating them.
- Evaluate against current competitors and simple baselines, not only greenfield examples.
