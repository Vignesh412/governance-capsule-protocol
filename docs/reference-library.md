# GCP Reference Library

Status: Milestone 3, first executable slice

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
- deterministic protocol error codes.

## Deliberately not implemented yet

- aggregate and concurrent sibling-budget allocation;
- replay and use-count state;
- online revocation status and bounded-staleness evaluation;
- approval consumption and amendment authorization;
- schema validation as part of the public API;
- generated property-test coverage targets; and
- receipt creation and verification helpers.

These require stateful components or additional protocol rules and must not be implied by the stateless validator.

## Run

From the repository root:

```sh
python3 -m pytest
python3 tools/validate_schemas.py
```

The schema examples contain placeholder proofs and digests because they test representation. The cryptographic tests construct fresh Ed25519 keys and internally consistent signed artifacts.
