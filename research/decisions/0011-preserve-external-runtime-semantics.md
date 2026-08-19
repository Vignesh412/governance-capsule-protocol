# Decision 0011: Preserve non-Boolean external-runtime semantics

Date: 2026-08-19  
Status: Accepted

## Context

Microsoft ACS returns five verdicts: `allow`, `warn`, `deny`, `escalate`, and `transform`. Mapping these to a Boolean allow/block interface would lose required audit, transformation, and approval behavior. It could also let CARM accidentally relax an upstream escalation.

## Decision

External policy-runtime adapters must preserve:

- the native verdict and stable reason code;
- policy and runtime identity;
- evidence artefacts;
- mandatory downstream controls; and
- explicit approval requirements.

`warn` and `transform` may normalize to an allowing policy effect only when their required controls remain attached. `escalate` normalizes to `REQUIRE_APPROVAL` and is handled before ordinary CARM conflict negotiation. Unsupported verdicts and runtime failures fail closed.

## Consequences

- The normalized policy model is richer than an allow/block pair.
- The Governed Action Gateway must prove that warning audit and transformation controls were applied before commit.
- CARM cannot override an external runtime's explicit escalation request.
- Adapter conformance must cover every native verdict, not only allow and deny.
- A source-contract test does not count as a completed live integration.
