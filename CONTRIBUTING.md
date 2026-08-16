# Contributing

Governance Capsule is currently an early research and engineering project, not a published standard.

Contributions are most useful when they include a concrete failure case, an independently reproducible test, a protocol ambiguity, an interoperability experiment, or primary-source evidence that changes the landscape analysis.

## Before proposing a change

- Read the [project charter](CHARTER.md) and [roadmap](ROADMAP.md).
- Distinguish schema validity from semantic validity and runtime enforcement.
- Do not describe application-defined possibilities as native framework guarantees.
- Preserve deterministic failure behavior and fail closed on unknown critical semantics.
- Include tests for implementation changes.

## Local checks

```sh
python3 -m pytest
python3 tools/validate_schemas.py
```

## Research claims

Material claims about vendor behavior should cite current primary documentation or source code and include the review date.

## Security-sensitive reports

Do not open a public issue for an unpatched vulnerability that could put users at risk. Follow [SECURITY.md](SECURITY.md).

## Licensing

No open-source license has been selected yet. Contributions cannot be accepted until contribution and licensing terms are established.
