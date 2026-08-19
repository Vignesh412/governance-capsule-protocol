# Governed Action Gateway Slice v0.1

Status: executable in-memory product slice

## What it demonstrates

An agent-facing action proposal cannot call the supplier connector directly through this slice. The gateway:

1. binds an `action_id` to the exact proposal digest;
2. invokes the deterministic kernel-verification boundary;
3. obtains normalized policy evidence from a pluggable runtime;
4. invokes CARM when applicable;
5. stops for approval or rejection before connector access;
6. records authorization and reservation states;
7. calls the protected connector with the action ID as its idempotency key;
8. treats a lost response as `COMMIT_OUTCOME_UNKNOWN` rather than failure;
9. reconciles connector state before permitting another commit; and
10. signs a receipt binding the proposal, policy snapshot, graph snapshot, controls, decision, and observed result.

## Run

```sh
python3 tools/run_gateway_demo.py
```

The demonstration intentionally loses the connector response after creating one supplier. Its expected result is:

```text
first observed state: COMMIT_OUTCOME_UNKNOWN
reconciled state:     COMMITTED
retry state:          COMMITTED
connector commits:    1
suppliers created:    1
```

This is the first product-shaped behavior in the repository: an action crosses governance checks and a real commit/recovery state machine rather than stopping at schema or policy evaluation.

## Security properties exercised

- Kernel rejection occurs before policy evaluation and connector access.
- Reusing an action ID with different proposal content is rejected.
- Retrying an identical committed action returns the recorded result.
- ACS-style warning and transformation controls survive into the receipt.
- Approval-required actions do not reach the connector.
- Unknown commit outcomes are reconciled without a second connector call.
- Receipts are signed with the existing Ed25519/JCS integrity profile.

## Deliberate limits

- State, reservations, and the supplier system are process-local and disappear on restart.
- The gateway receipt is an experimental product receipt, not yet the frozen GCP receipt schema.
- The kernel and approval boundaries are injected interfaces in this slice; the tests prove ordering and mediation, while the next slice must wire full capsule, revocation, and scoped-approval artifacts.
- The connector is an idempotent reference connector, not an external ERP or procurement API.
- Holding one process lock cannot substitute for a serializable database transaction.
- Complete mediation is demonstrated only inside this process; production credentials and network controls do not yet exist.

## Next acceptance gate

The action ledger and receipts now have a restart-safe SQLite profile, documented in `docs/durable-gateway-slice-v0.1.md`. The next acceptance gate is a durable commit-intent/outbox transaction covering process termination at every transition boundary, followed by the planned PostgreSQL profile.
