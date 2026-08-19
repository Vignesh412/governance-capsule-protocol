# Competitive Slice v0.1

Status: executable research experiment, not a product benchmark

## Question

Can the current CARM mechanism distinguish the same valid policy conflict based on its verified position in a downstream workflow, while simpler merge rules cannot?

## Scenario

The experiment models a supplier-onboarding workflow:

```text
                 +-> compliance --+
intake ----------+                 +-> approval -> create-vendor
                 +-> finance -----+
```

`approval` is an AND join: both compliance and finance are required. A regulatory policy says `ALLOW`, while an organizational change-freeze policy says `BLOCK`. The policy versions and conflict are identical at every tested position.

The graph is validated as acyclic, requires explicit semantics at multi-parent joins, and is reduced to a deterministic digest. Downstream reach is computed from that snapshot. An OR join contributes `1 / indegree`; an AND join contributes `1`. Unknown join semantics are treated conservatively and lower topology confidence.

## Compared mechanisms

- **Most restrictive:** any `BLOCK` wins.
- **Fixed priority:** the highest policy layer wins; ties are deterministic.
- **CARM baseline:** selects priority enforcement (PE), negotiated relaxation (NR), or an escalation boundary (EB) from conflict severity and downstream reach. A tentative automated block is routed to EB by the outcome-aware safeguard.

These are deliberately small comparison baselines. The external policy-runtime interface is ready for an AGT ACS, OPA, or Cedar adapter, but no external runtime is integrated in this version.

## Reproduce

```sh
python3 tools/run_competitive_slice.py
```

Expected summary:

| Mechanism | Conflict at `intake` | Conflict at `create-vendor` |
|---|---:|---:|
| Most restrictive | BLOCK | BLOCK |
| Fixed priority | ALLOW | ALLOW |
| CARM | EB / APPROVAL_REQUIRED | PE / ALLOW |
| Join-aware downstream reach | 4 | 0 |

The graph digest is included in both CARM results, binding the decisions to the same topology snapshot.

## What this demonstrates

For fixed policy inputs and configuration, CARM is deterministic and sensitive to verified downstream consequences. The comparison rules are deterministic too, but they are topology-blind.

This is a mechanism test. It does **not** establish that CARM made the correct decision, reduced risk, outperformed Microsoft Agent Governance Toolkit, or generalized to real workflows. Those claims require outcome labels, an external governance-runtime integration, stale and adversarial topology tests, and human-review measurements.

## Remaining gaps

- Integrate Microsoft AGT ACS as the first external policy runtime.
- Bind a full CARM receipt to policy, graph, evidence, and configuration snapshots.
- Test topology freshness and falsely declared dependencies.
- Define measurable outcome and review-burden metrics.
- Add CARM-SE certification and RIG evidence-sufficiency behavior only after the deterministic baseline is established.
