# Signed Capsule Gateway v0.1

Status: executable root-capsule authorization slice

## What changed

The gateway no longer needs a permissive mock to represent capsule authorization. `CapsuleActionVerifier` consumes a real signed Governance Capsule and runs before the local policy runtime or protected connector.

For every proposed action it verifies:

1. capsule JSON Schema;
2. Ed25519/JCS integrity proof;
3. issuer-to-verification-method role authorization;
4. capsule subject against the presenting runtime;
5. `not_before` and `expires_at`;
6. authenticated revocation status using the declared freshness profile;
7. action and exact/prefix resource containment in a capsule grant;
8. registered critical authority constraints;
9. mandatory `before_action` obligations; and
10. replay/use limits with idempotent binding of an action ID to one capsule digest.

Failures become deterministic GCP reason codes in a signed gateway receipt and short-circuit all later stages.

## Reproduce

```sh
python3 tools/run_signed_capsule_gateway_demo.py
```

The command creates a fresh issuer key, signs a root capsule, supplies authenticated active status, satisfies its audit obligation, executes one authorized supplier action, and prints the resulting kernel controls and receipt binding.

## Negative evidence

The tests prove that these cases never reach policy evaluation or the connector:

- content mutated after signature;
- unauthorized issuer/key role binding;
- expired capsule;
- revoked capsule;
- action absent from delegated authority; and
- unsatisfied mandatory pre-action obligation.

## Remaining boundaries

- The current gateway demonstration consumes one root capsule. Derived-capsule lineage and delegation-proof verification exist in the library but are not yet composed into this action verifier.
- Constraint and obligation satisfaction use registered deterministic verifier callbacks; defining portable evidence profiles remains future protocol work.
- Replay use and action-to-capsule bindings are process-local in this verifier. They must join the durable gateway transaction.
- Online active status is authenticated by the status-provider trust boundary; the signed active-status response profile is still pending.
- Budget consumption is not yet reserved as part of action commit.
