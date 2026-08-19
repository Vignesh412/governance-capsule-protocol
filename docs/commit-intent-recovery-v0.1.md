# Durable Commit-Intent Recovery v0.1

Status: executable single-host fault-injection slice

## Problem

A database transaction cannot include an external supplier API. A process can stop after recording authorization but before calling the connector, or after the connector succeeds but before the result is saved. Treating either case as an ordinary failure can lose work or duplicate the side effect.

## Mechanism

Before connector invocation, the gateway durably persists:

- state `COMMITTING`;
- action ID and exact proposal digest;
- the recoverable proposal payload;
- decision and required controls;
- graph and policy snapshot digests; and
- the receipt context accumulated so far.

On restart, `recover_pending()` enumerates `COMMITTING` and `COMMIT_OUTCOME_UNKNOWN` records and asks the connector to reconcile each action ID.

- If the connector reports committed, the gateway records `COMMITTED` without calling commit again.
- If it reports not committed for a `COMMITTING` intent, the gateway verifies the persisted proposal digest and invokes commit once using the same action ID.
- If the outcome remains unknown, the gateway keeps the action unresolved rather than releasing or retrying blindly.

## Connector exception contract

Once `ProtectedConnector.commit()` begins, an exception is not evidence that
the external action failed. A timeout, transport error, or adapter exception
can occur after the side effect has already committed. The gateway therefore
converts every ordinary exception raised by `commit()` into
`COMMIT_OUTCOME_UNKNOWN`, preserving the record for reconciliation instead of
marking it `FAILED`.

A protected connector must:

- use `action_id` as an idempotency key or stable external correlation key;
- return an explicit outcome when it can determine one;
- provide authoritative, side-effect-free lookup through `reconcile(action_id)`;
- never report `NOT_COMMITTED` when the external outcome is still ambiguous; and
- return the same stable result reference and digest for an already committed action.

Exceptions before connector invocation remain gateway failures or governance
rejections as appropriate. Process termination is deliberately not converted
to `UNKNOWN`; the durable `COMMITTING` intent is reconciled after restart.

## Reproduce

```sh
python3 tools/run_outbox_recovery_demo.py
```

The tool fault-injects two process stops:

| Crash point | Calls before restart | Calls after recovery | Suppliers |
|---|---:|---:|---:|
| Immediately before connector | 0 | 1 | 1 |
| Immediately after connector success | 1 | 1 | 1 |

Both durable records are `COMMITTING` at the simulated crash and `COMMITTED` after recovery.

## Claim boundary

This is a durable commit-intent pattern, not yet a full transactional outbox service. SQLite stores the intent and proposal on one host, and recovery is invoked explicitly. The gateway preserves commit-time exceptions as ambiguous outcomes, while the connector must provide authoritative lookup by action ID and compatible idempotency semantics.

Still required:

- leased multi-worker intent claiming;
- attempt counters and backoff;
- revision-checked state transitions;
- durable connector credentials and a real external system;
- dead-letter and operator intervention states;
- atomic approval-use and budget reservation in the intent transaction;
- PostgreSQL multi-instance tests; and
- kill-based subprocess tests in addition to deterministic fault injection.
