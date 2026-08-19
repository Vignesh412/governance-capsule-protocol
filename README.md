# Governance Capsule

Governance Capsule is an open research and engineering project exploring how governance can remain attached to work as that work moves between AI agents, tools, runtimes, and organizations.

The intended destination is the **Governance Capsule Protocol (GCP)**: a vendor-neutral protocol for carrying verifiable authority, mandatory obligations, budgets, approvals, provenance, and enforcement evidence through delegated agent workflows.

The project is deliberately not claiming to be a protocol or standard yet. It must first demonstrate interoperable behavior, precise lifecycle semantics, and enforceable security properties.

## Working hypothesis

Existing projects now provide substantial combinations of deterministic action governance, scope-narrowing delegation, approvals, budgets, revocation, receipts, human escalation, and framework adapters. The remaining product hypothesis is narrower: cross-runtime task-governance continuity combined with graph-wide conflict consequences, certified selective automation, evidence-identifiability contracts, and governed commit recovery.

GCP is worth building if it can demonstrate that a governed task can cross independent agent runtimes without:

- gaining unauthorized authority;
- losing mandatory obligations;
- exceeding conserved budgets;
- breaking its verifiable delegation lineage; or
- continuing after its authority has been revoked.

## Project layers

1. **Governance Capsule Model** - the portable governance data model.
2. **Governance Capsule Protocol** - the lifecycle and interchange rules.
3. **Governed Action Gateway** - the trusted reference monitor controlling consequential side effects.
4. **CARM** - the Cascade-Aware Resolution Mechanism for conflicts among otherwise valid policies.
5. **CARM-SE and RIG-aware evidence handling** - certified selective automation plus evidence acquisition or abstention when the correct resolution is not identifiable.

## Current status

Milestone 0 is complete. The primary-source landscape review found that the gap survives in a narrower form: verifiable continuity and constrained transformation of task governance across heterogeneous systems.

Milestone 1 is complete. It defines the minimal model, explicit revocation freshness guarantees, a threat analysis, and 24 executable properties for the first reference implementation.

Milestone 2 is complete. It defines a strict framework-independent wire profile; schemas for capsules, delegation proofs, approvals, amendments, revocations, enforcement receipts, and lifecycle receipts; and valid, structurally invalid, and semantically invalid examples.

Milestone 3 is in progress. The reference library now implements deterministic canonicalization, SHA-256 artifact digests, Ed25519 signing and verification, ordinary-delegation and delegation-proof validation, atomic in-memory budget allocation, replay/use tracking, audience checks, revocation-freshness evaluation, schema validation, signed revocation-record adaptation, scoped approval consumption, and amendment authorization. Receipt helpers, a signed active-status response profile, complete amendment-diff verification, and generated property-test coverage remain.

The first Milestone 5 comparative slice is also executable. It implements a validated, digest-bound Governance Graph, explicit AND/OR/UNKNOWN joins, join-aware downstream reach, topology confidence, normalized policy-runtime inputs, deterministic CARM PE/NR/EB selection, and most-restrictive and fixed-priority baselines. In the supplier workflow, the same policy conflict escalates at the high-reach intake node and uses priority enforcement at the zero-reach commit node. This proves graph-sensitive behavior only—not decision correctness or competitive superiority.

A Microsoft ACS adapter now maps the five published ACS verdicts into normalized GCP policy evidence without losing warning, transform, escalation, or evidence semantics. It is source-contract tested; native ACS execution remains pending because the reviewed ACS Python SDK requires Python 3.11+ and the current workspace runs Python 3.9.6.

The first product-shaped Governed Action Gateway slice is now executable. It mediates one protected supplier connector, binds action IDs to proposal digests, preserves policy controls, stops rejected or approval-bound actions before connector access, signs decision receipts, and reconciles an ambiguous successful commit without issuing a duplicate supplier creation. Its state is process-local and it is not production-ready.

A restart-safe SQLite reference profile now persists the action ledger. The durable demonstration restarts the gateway after an ambiguous successful supplier commit, recovers the unknown state, reconciles it, and returns the recorded committed result on retry without another connector call. This is a single-host durability result, not yet the planned PostgreSQL/outbox production profile.

Durable commit-intent recovery now covers process stops immediately before and immediately after connector invocation. The restart worker reconstructs and verifies the persisted proposal, reconciles by action ID, commits only when the supplier system confirms no prior commit, and never duplicates the after-success case.

The gateway now also has a concrete signed-capsule kernel. A real root capsule is schema-checked, signature-verified, issuer-authorized, audience- and time-checked, revocation-checked, authority-matched, obligation-checked, and replay-limited before local policy or supplier access. Negative tests prove these failures short-circuit the downstream path.

The same gateway path now accepts a signed ordinary delegation chain. It verifies every capsule and attenuation transition, the delegation proof and delegator role, inherited obligations and budget containment, and cascading ancestor revocation before authorizing the leaf agent's supplier action.

The unified product architecture now defines the trust boundary, data/control/evidence planes, action state machine, Governance Graph, CARM/CARM-SE/RIG interaction, persistence model, and first product demonstration.

A 2026-08-19 competitive refresh identified Microsoft Agent Governance Toolkit as the closest implementation baseline and changed the build strategy: reuse existing policy, identity, approval, receipt, escalation, and adapter primitives where possible; build and test the distinct graph/evidence/recovery layer comparatively.

See [CHARTER.md](CHARTER.md), [ROADMAP.md](ROADMAP.md), [docs/product-architecture-rfc-v0.1.md](docs/product-architecture-rfc-v0.1.md), [research/competitive-architecture-report-2026-08-19.md](research/competitive-architecture-report-2026-08-19.md), [research/milestone-0-landscape-report.md](research/milestone-0-landscape-report.md), [spec/formal-model-v0.1.md](spec/formal-model-v0.1.md), [spec/wire-profile-v0.1.md](spec/wire-profile-v0.1.md), [schema/README.md](schema/README.md), [docs/reference-library.md](docs/reference-library.md), and [journey/progress-log.md](journey/progress-log.md).

## Run locally

The current reference slice requires Python 3.9 or newer.

```sh
python3 -m pip install -e .
python3 -m pytest
python3 tools/validate_schemas.py
python3 tools/run_competitive_slice.py
python3 tools/run_gateway_demo.py
python3 tools/run_durable_gateway_demo.py
python3 tools/run_outbox_recovery_demo.py
python3 tools/run_signed_capsule_gateway_demo.py
python3 tools/run_delegated_gateway_demo.py
```

The example schema fixtures contain placeholder proof values. The cryptographic test suite creates fresh Ed25519 keys and internally consistent signed artifacts.

## Repository status

This is experimental research code. It has not completed a security review and must not be used as a production authorization or compliance system. See [SECURITY.md](SECURITY.md) and [CONTRIBUTING.md](CONTRIBUTING.md).

## Evidence standard

Claims about vendor capabilities must be linked to current primary documentation or source code and dated. “Can be implemented with custom code” is not the same as native or protocol-defined support.

## License

No license has been selected yet. Until one is added, the repository contents remain all rights reserved by default.
