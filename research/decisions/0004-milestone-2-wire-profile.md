# Decision 0004: Adopt a strict JSON/JCS/Ed25519 wire profile

- Status: Accepted
- Date: 2026-08-12

## Context

Milestone 2 must represent the formal model without confusing structural schema validation with cross-document semantic enforcement.

Budget conservation requires exact arithmetic. Lineage and signed evidence require deterministic bytes. Unknown governance fields cannot be silently ignored. Enforcement decisions and task lifecycle transitions are related but distinct assertions.

## Decision

GCP v0.1 will use:

1. JSON encoded as UTF-8;
2. JSON Schema Draft 2020-12;
3. absolute URI identifiers;
4. RFC 3339 timestamps;
5. non-negative decimal strings for conserved quantities;
6. RFC 8785 JCS for canonicalization;
7. SHA-256 digests formatted as `sha256:<lowercase hex>`;
8. Ed25519 signatures with unpadded base64url proof values;
9. strict rejection of unknown core properties; and
10. separate enforcement and lifecycle receipts.

Embedded `proof` is excluded before canonicalization and signing. Each core artifact is independently signed.

## Consequences

- JSON Schema validates representation but does not enforce authority attenuation, obligation persistence, digest linkage, aggregate budgets, or revocation freshness.
- Semantic arrays require deterministic producer ordering before signing.
- An extension container remains deferred until negotiation and downgrade semantics are defined.
- Using a Data Integrity-shaped proof does not make GCP a Verifiable Credentials implementation.
