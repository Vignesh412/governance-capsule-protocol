# Delegated Gateway v0.1

Status: executable signed one-hop delegation slice

## Demonstrated path

```text
intake agent
  root authority: supplier.create urn:supplier:*
        |
        | signed delegation proof
        v
supplier-operations agent
  child authority: supplier.create urn:supplier:42
        |
        v
Governed Action Gateway -> supplier connector
```

Before the leaf action reaches local policy or the connector, the kernel verifies:

- every capsule schema and signature;
- issuer/key role authorization for every capsule;
- continuity between adjacent lineage transitions;
- parent and child digest bindings;
- authority attenuation;
- mandatory-obligation persistence;
- child budget containment;
- time and delegation-depth attenuation;
- delegation-proof signature and content bindings;
- delegator/key role authorization;
- leaf audience, validity, authority, constraints, obligations, and replay; and
- current leaf and cascading ancestor revocation status.

Run:

```sh
python3 tools/run_delegated_gateway_demo.py
```

The resulting signed gateway receipt contains `GCP_DELEGATION_LINEAGE_VERIFIED`.

## Adversarial evidence

The end-to-end tests prove that these cases stop before policy and connector access:

- child authority expands from `supplier.create` to `supplier.delete`;
- delegation proof content changes after signing; and
- the root capsule is revoked with cascading effect.

## Remaining boundaries

- The executable demo uses one delegation hop, although the verifier accepts a continuous sequence of ordinary transitions.
- v0.1 remains a rooted tree with one parent per derived capsule; governance joins are graph evidence, not multi-parent capsule lineage.
- Aggregate sibling budget conservation still relies on the allocation ledger and is not atomically composed with action commit.
- Lineage artifacts are supplied directly to the gateway; discovery, transport negotiation, and confidential evidence disclosure profiles remain.
- Cross-framework and cross-organization transport have not yet been exercised in this product path.
