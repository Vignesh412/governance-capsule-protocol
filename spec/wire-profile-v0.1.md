# GCP Wire Profile v0.1

Status: Milestone 2 draft profile

Date: 2026-08-12

## Representation

- JSON documents use UTF-8.
- Structure is defined with JSON Schema Draft 2020-12.
- Unknown top-level properties are rejected in the v0.1 core artifacts.
- Identifiers are absolute URIs. URNs, HTTPS URLs, and SPIFFE IDs are permitted when valid for the field.
- Timestamps use RFC 3339 `date-time` strings and should be normalized to UTC before signing.
- Conserved numeric quantities are non-negative decimal strings. JSON floating-point numbers are not accepted for budgets.

## Canonicalization and digest

Protected JSON is canonicalized using RFC 8785 JSON Canonicalization Scheme (JCS). The `proof` member is removed before canonicalization of an artifact carrying an embedded proof.

The v0.1 digest profile is:

```text
sha256:<lowercase hexadecimal SHA-256 of JCS bytes>
```

Semantic arrays are not reordered during canonicalization. Producers must create deterministic ordering for authority, obligations, budgets, changes, evidence, controls, and reason codes before signing. Two documents with different semantic-array order may have different digests even if an application considers them equivalent.

## Signature profile

The v0.1 signature profile is Ed25519 over the SHA-256 digest bytes of the proof-excluded JCS document.

The proof container uses:

- `type`: `DataIntegrityProof`
- `cryptosuite`: `eddsa-jcs-2022`
- `verification_method`: URI resolving to the verification key
- `created`: proof creation timestamp
- `proof_purpose`: `assertionMethod` or `authentication`
- `proof_value`: unpadded base64url Ed25519 signature

The name follows an existing Data Integrity cryptosuite convention, but GCP v0.1 does not claim W3C Verifiable Credential conformance merely by using this proof shape.

## Core artifacts

- Governance Capsule
- Delegation Proof
- Approval
- Amendment
- Revocation Record
- Enforcement Receipt
- Task Lifecycle Receipt

Each artifact is independently signed. A delegation proof signs the relationship between already-digested parent and child capsules; it does not replace either capsule signature.

## Schema versus semantic validation

Schema validation checks representation, required fields, formats, supported enums, and conditional structure.

It does not establish:

- signature correctness;
- parent or child digest correctness;
- authority containment;
- obligation persistence;
- temporal comparison between two capsules;
- aggregate budget conservation;
- revocation freshness; or
- approval authorization and remaining-use count.

Those checks belong to the reference semantic validator and conformance suite.

## Critical extension behavior

v0.1 schemas reject unknown core properties. Extension data must eventually use a registered, namespaced extension container. That container is intentionally deferred until extension negotiation and downgrade behavior are specified.

Silently ignoring unknown governance semantics is forbidden.
