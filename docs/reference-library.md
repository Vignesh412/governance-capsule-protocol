# GCP Reference Library

Status: Milestone 3 core controls plus the first Milestone 5 comparative slice

The Python package under `src/gcp_reference` turns the v0.1 wire profile and formal invariants into executable checks.

## Implemented

- deterministic canonical JSON over the GCP v0.1 value domain;
- proof-excluded SHA-256 artifact digests;
- Ed25519 artifact signing and verification;
- in-memory verification-method resolution;
- ordinary authority attenuation for exact actions, exact/prefix resources, and registered constraints;
- mandatory-obligation persistence;
- parent linkage and delegation-proof binding;
- single-child budget containment and unit checks;
- temporal attenuation and delegation-depth checks;
- atomic process-local sibling-budget allocation;
- atomic replay and use-count tracking;
- audience validation;
- online-strict, bounded-stale, and offline-until-expiry evaluation;
- cascading ancestor-revocation checks;
- structured revocation evidence for future receipts;
- public structural-validation API over the v0.1 schema bundle;
- signed capsule-revision revocation verification and runtime-status adaptation;
- declared issuer, approver, and amendment-authority binding to permitted signing keys;
- exact capsule, action, resource, amendment-change, and validity scoping for approvals;
- atomic approval use consumption; and
- amendment binding to signed previous/result capsule digests and consecutive revisions; and
- a validated and digest-bound Governance Graph with explicit join semantics;
- join-aware downstream-reach and topology-confidence evidence;
- a framework-neutral policy-runtime adapter boundary;
- a source-shaped Microsoft ACS adapter preserving all five native verdicts and evidence;
- deterministic CARM PE, NR, and EB selection with outcome-aware blocking safeguards;
- most-restrictive and fixed-priority comparison baselines; and
- deterministic protocol error codes.

## Deliberately not implemented yet

- generated property-test coverage targets; and
- receipt creation and verification helpers.

The allocation ledger, use registry, and status cache are process-local reference implementations. Production adapters must provide equivalent atomicity and durability through transactional storage.

`status_from_signed_revocation` proves and adapts a positive, signed revocation record for one exact capsule revision. Absence of a revocation record is not cryptographic proof that a capsule remains active; online active-status responses still rely on a trusted adapter pending a signed status-response profile.

Amendments bind the signed previous capsule, signed result capsule, ordered change declaration, approval, identity, and consecutive revision. This slice does not yet recompute every declared JSON Pointer and old/new value digest from the actual capsule diff. Until that lands, the declaration is tamper-evident but not independently proven complete.

Root capsules may advance beyond revision zero through amendment while remaining lineage roots. They still cannot acquire `parent` or `delegator` fields.

These remaining guarantees require additional protocol rules and must not be implied by the current validator.

## Run

From the repository root:

```sh
python3 -m pytest
python3 tools/validate_schemas.py
python3 tools/run_competitive_slice.py
```

The competitive slice demonstrates that CARM decisions can change with verified downstream reach while topology-blind baselines do not. It is not evidence that the selected decisions are correct or safer. See `docs/competitive-slice-v0.1.md` for the scenario, result, and limitations.

The Microsoft ACS adapter is contract-tested against the published Python result shapes. The native ACS wheel requires Python 3.11+, while this workspace currently runs Python 3.9.6, so live ACS execution remains an explicit integration gate. See `docs/microsoft-acs-integration.md`.

The schema examples contain placeholder proofs and digests because they test representation. The cryptographic tests construct fresh Ed25519 keys and internally consistent signed artifacts.
