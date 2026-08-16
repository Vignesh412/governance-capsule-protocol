# GCP Reference Library

Status: Milestone 3, second executable slice

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
- temporal attenuation and delegation-depth checks; and
- atomic process-local sibling-budget allocation;
- atomic replay and use-count tracking;
- audience validation;
- online-strict, bounded-stale, and offline-until-expiry evaluation;
- cascading ancestor-revocation checks;
- structured revocation evidence for future receipts; and
- deterministic protocol error codes.

## Deliberately not implemented yet

- approval consumption and amendment authorization;
- schema validation as part of the public API;
- generated property-test coverage targets; and
- receipt creation and verification helpers.

The allocation ledger, use registry, and status cache are process-local reference implementations. Production adapters must provide equivalent atomicity and durability through transactional storage.

The revocation evaluator accepts `StatusRecord` values from a trusted adapter and requires `authenticated=True`. This slice does not yet cryptographically verify a signed revocation artifact inside the evaluator. The distinction is intentional and must remain visible.

These require stateful components or additional protocol rules and must not be implied by the stateless validator.

## Run

From the repository root:

```sh
python3 -m pytest
python3 tools/validate_schemas.py
```

The schema examples contain placeholder proofs and digests because they test representation. The cryptographic tests construct fresh Ed25519 keys and internally consistent signed artifacts.
