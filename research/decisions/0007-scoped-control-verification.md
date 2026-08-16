# Decision 0007: Bind governance roles to keys and consume approvals atomically

Date: 2026-08-16  
Status: Accepted for v0.1 reference implementation

## Context

Cryptographic signature verification alone establishes that a known private key signed an artifact. It does not establish that the key may act as the issuer, approver, or amendment authority named inside that artifact. Approvals also become unsafe when validation and use-count consumption are separate, racing operations.

The original capsule schema additionally fixed all root capsules at revision zero, contradicting the amendment model's requirement to produce a new revision of the same capsule.

## Decision

- Each enforcement domain supplies an explicit mapping from a governance identity to the verification methods authorized for that identity.
- Revocation, approval, and amendment verification checks both the signature and that identity-to-key binding.
- An approval binds an exact capsule digest, operation type, action, resource, time window, maximum use count, and—when used for amendment—the digest of the ordered change declaration.
- Approval uses are committed atomically only after all validation succeeds.
- An amendment binds signed previous and result capsule digests, the approval identifier, the same capsule and task identities, and a consecutive revision with an advancing sequence.
- A lineage-root capsule may advance beyond revision zero through amendment but may never acquire a parent or delegator.

## Consequences and limits

The reference implementation can reject role spoofing by another otherwise trusted key and concurrent reuse of a single-use approval.

A positive signed revocation record can be verified. Absence of such a record is not a signed active-status assertion; a future status-response profile must address this.

The change declaration is signed and approval-bound, but the current implementation does not yet recompute every JSON Pointer and old/new value digest from the actual capsule diff. That guarantee remains explicitly incomplete.
