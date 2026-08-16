# Governance Capsule

Governance Capsule is an open research and engineering project exploring how governance can remain attached to work as that work moves between AI agents, tools, runtimes, and organizations.

The intended destination is the **Governance Capsule Protocol (GCP)**: a vendor-neutral protocol for carrying verifiable authority, mandatory obligations, budgets, approvals, provenance, and enforcement evidence through delegated agent workflows.

The project is deliberately not claiming to be a protocol or standard yet. It must first demonstrate interoperable behavior, precise lifecycle semantics, and enforceable security properties.

## Working hypothesis

Existing agent systems provide combinations of permissions, guardrails, context, handoffs, workflow state, and traces. Governance continuity across heterogeneous delegation boundaries remains largely application-defined.

GCP is worth building if it can demonstrate that a governed task can cross independent agent runtimes without:

- gaining unauthorized authority;
- losing mandatory obligations;
- exceeding conserved budgets;
- breaking its verifiable delegation lineage; or
- continuing after its authority has been revoked.

## Project layers

1. **Governance Capsule Model** - the portable governance data model.
2. **Governance Capsule Protocol** - the lifecycle and interchange rules.
3. **CARM** - a reference runtime that evaluates inherited governance and issues enforcement decisions and receipts.

## Current status

Milestone 0 is complete. The primary-source landscape review found that the gap survives in a narrower form: verifiable continuity and constrained transformation of task governance across heterogeneous systems.

Milestone 1 is complete. It defines the minimal model, explicit revocation freshness guarantees, a threat analysis, and 24 executable properties for the first reference implementation.

Milestone 2 is complete. It defines a strict framework-independent wire profile; schemas for capsules, delegation proofs, approvals, amendments, revocations, enforcement receipts, and lifecycle receipts; and valid, structurally invalid, and semantically invalid examples.

Milestone 3 is in progress. Its first executable slice implements deterministic canonicalization, SHA-256 artifact digests, Ed25519 signing and verification, ordinary-delegation validation, delegation-proof validation, and deterministic failures for authority, obligation, lineage, budget, time, and depth violations. Stateful allocation, replay, and revocation enforcement remain next.

See [CHARTER.md](CHARTER.md), [ROADMAP.md](ROADMAP.md), [research/milestone-0-landscape-report.md](research/milestone-0-landscape-report.md), [spec/formal-model-v0.1.md](spec/formal-model-v0.1.md), [spec/wire-profile-v0.1.md](spec/wire-profile-v0.1.md), [schema/README.md](schema/README.md), [docs/reference-library.md](docs/reference-library.md), and [journey/progress-log.md](journey/progress-log.md).

## Run locally

The current reference slice requires Python 3.9 or newer.

```sh
python3 -m pip install -e .
python3 -m pytest
python3 tools/validate_schemas.py
```

The example schema fixtures contain placeholder proof values. The cryptographic test suite creates fresh Ed25519 keys and internally consistent signed artifacts.

## Repository status

This is experimental research code. It has not completed a security review and must not be used as a production authorization or compliance system. See [SECURITY.md](SECURITY.md) and [CONTRIBUTING.md](CONTRIBUTING.md).

## Evidence standard

Claims about vendor capabilities must be linked to current primary documentation or source code and dated. “Can be implemented with custom code” is not the same as native or protocol-defined support.

## License

No license has been selected yet. Until one is added, the repository contents remain all rights reserved by default.
