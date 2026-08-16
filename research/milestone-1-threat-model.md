# Milestone 1 Threat and Abuse Analysis

Status: Initial v0.1 analysis

Date: 2026-08-12

## Trust boundary

Trusted in the first prototype:

- configured issuer and delegator public keys;
- canonicalization, validation, allocation, and enforcement code;
- secure key storage;
- authenticated revocation-status service;
- authenticated human-approval service.

Untrusted:

- models and prompts;
- task descriptions;
- agents requesting derivations;
- network and queued messages;
- capsule storage outside the integrity boundary;
- downstream claims not backed by a trusted receipt.

## Threat mapping

| Threat | Example | v0.1 response | Residual risk |
|---|---|---|---|
| Authority expansion | Child changes refund limit from 500 to 5,000 | Deterministic containment validation rejects derivation | Incorrect constraint plug-in could misclassify containment |
| Resource widening | `vendor/123` becomes `vendor/*` | Hierarchical resource containment rejects widening | Resource naming mistakes at policy authoring time |
| Obligation deletion | Child removes human approval | Canonical mandatory set inclusion rejects child | Issuer may wrongly mark an obligation non-mandatory |
| Obligation substitution | Same ID, weaker parameters | Compare canonical content, not ID alone | No safe refinement until type-specific rules exist |
| Parent substitution | Attacker attaches child to a more permissive parent | Parent digest and delegation proof mismatch | Compromised delegator key |
| Lineage truncation | Downstream omits an ancestor with a mandatory restriction | Verified parent chain required; cascading revocation checks ancestors | Availability cost of resolving lineage/status |
| Budget double allocation | Two parallel children each receive all remaining cost | Atomic allocation authority and issued-allocation ledger | Allocation authority availability and compromise |
| Negative or unit-confused budget | Child uses `-10` or changes USD to tokens | Registered dimensions, units, and non-negative exact values | Bad conversion policy outside core protocol |
| Capsule replay | Single-use approval/capsule reused | Unique identifier and replay registry | Offline profile cannot guarantee global single use |
| Wrong audience | Capsule for Agent B exercised by Agent C | Authenticated subject/audience check | Shared credentials defeat subject distinction |
| Expiry extension | Child outlives parent | Temporal attenuation rejects child | Clock synchronization error |
| Delegation-depth reset | Child restores parent depth | Strict depth reduction | Authorized amendment could deliberately expand depth |
| Revocation race | Action commits after final status check | Freshness profiles and checks before governed actions | Non-zero check-to-commit race |
| Offline stale authority | Disconnected agent continues after revocation | Explicit offline profile and short expiry | Accepted by policy; cannot be eliminated by capsule alone |
| Revocation suppression | Intermediary hides revocation event | Receiver queries authenticated status; events alone are not authoritative | Denial of service against status endpoint |
| Protocol downgrade | Peer omits required GCP extension | Required-profile negotiation fails closed | Misconfigured caller may not require GCP |
| Receipt omission | Runtime hides an unfavorable decision | Required receipt sequence and upstream completeness checks in later milestones | Compromised runtime can lie unless attested |
| Forged receipt | Attacker fabricates an allow decision | Runtime signature and trusted identity | Signature proves issuer, not correctness |
| Approval overreach | Approval for one payment reused elsewhere | Bind approval to capsule/action/resource/expiry/reuse count | Compromised approval service or approver |
| Policy confidentiality leak | Capsule embeds private regulatory logic | Carry references, commitments, and necessary parameters only | Metadata can still reveal sensitive business rules |

## Security properties not claimed

GCP v0.1 does not claim:

- Byzantine consensus among organizations;
- truthfulness of signed reach, policy, or enforcement assertions;
- prevention of side effects outside registered enforcement points;
- instantaneous revocation;
- confidentiality merely because content is signed;
- correct legal interpretation; or
- safety when all trusted enforcement components are compromised.
