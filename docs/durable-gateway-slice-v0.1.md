# Durable Gateway Slice v0.1

Status: restart-safe single-host reference profile

## Demonstrated failure sequence

The supplier connector commits successfully, but its response is lost. The first gateway records `COMMIT_OUTCOME_UNKNOWN` in a transactional SQLite ledger and exits. A new gateway instance opens the same database, recovers that state, asks the connector to reconcile the action ID, records `COMMITTED`, and returns the saved result on retry.

```text
gateway A -> connector creates supplier -> response lost
gateway A -> persists COMMIT_OUTCOME_UNKNOWN -> exits
gateway B -> opens action ledger -> recovers unknown state
gateway B -> reconciles action ID -> COMMITTED
client retry -> saved COMMITTED record; no second connector commit
```

Run:

```sh
python3 tools/run_durable_gateway_demo.py
```

Expected evidence:

```text
before restart:          COMMIT_OUTCOME_UNKNOWN
recovered after restart: COMMIT_OUTCOME_UNKNOWN
after reconciliation:    COMMITTED
identical retry:          COMMITTED
connector commit calls:  1
suppliers created:        1
```

## Storage guarantees

The SQLite store:

- uses `action_id` as a primary key;
- atomically claims an action ID with `INSERT OR IGNORE`;
- persists the proposal digest, action state, decision, controls, reason codes, graph and policy digests, connector result, and signed receipt;
- rejects rebinding an existing action ID to another proposal after restart;
- enables WAL journaling and `synchronous=FULL`; and
- conditionally removes approval-waiting records only when their expected state still matches.

## What it does not prove

- The reference connector itself remains in memory. The demonstration preserves it across gateway instances to model an independently durable external supplier system.
- SQLite is a single-host reference profile, not the planned multi-instance PostgreSQL deployment.
- Gateway record updates do not yet use revision-based optimistic concurrency.
- Approval use, budget reservation, and commit-intent outbox are not yet one database transaction.
- A process kill between connector return and unknown-state persistence is not yet covered by a durable outbox worker.
- Receipt signing keys are supplied to both gateway instances in the demonstration; production key custody and rotation remain separate work.

The next slice now persists a recoverable commit intent and fault-injects stops before and after connector invocation. See `docs/commit-intent-recovery-v0.1.md`. A leased asynchronous outbox worker and multi-instance PostgreSQL semantics remain.
