# GCP v0.1 Schemas

These JSON Schema Draft 2020-12 documents define the framework-independent wire shape for Milestone 2.

## Artifacts

- `capsule.schema.json` — governed task state and inherited constraints
- `delegation-proof.schema.json` — signed parent-to-child linkage
- `approval.schema.json` — scoped, expiring authorization by an approver
- `amendment.schema.json` — explicit authorized governance changes
- `revocation.schema.json` — authority invalidation and propagation instruction
- `enforcement-receipt.schema.json` — runtime action decision and evidence
- `lifecycle-receipt.schema.json` — signed task completion or rejection
- `common.schema.json` — shared identifiers, quantities, proofs, and domain types

The normative serialization and signing choices are in [the wire profile](../spec/wire-profile-v0.1.md).

## Validate

From the repository root, run:

```sh
python3 tools/validate_schemas.py
```

The command checks schema correctness, accepts every fixture in `examples/valid`, rejects every structural fixture in `examples/invalid`, and verifies the expected error-code manifests in `examples/semantic-invalid`.

Schema validation only checks document structure. Cross-document properties such as signature verification, authority attenuation, obligation persistence, budget conservation, and revocation freshness are Milestone 3 semantic checks.
