# Post 3 - A signed capsule cannot coordinate a distributed system

Recommended attachment: the six images named `003-carousel-01` through `003-carousel-06` in `journey/visuals`, uploaded in numerical order.

I’ve started building the reference implementation for the Governance Capsule project.

Until now, the work had produced a formal model, schemas, and test cases.

This milestone asks a harder question:

**Can those governance rules actually be enforced in code?**

The first working version can now digitally sign a Governance Capsule, detect changes to its protected contents, verify the parent-to-child delegation link, and reject several invalid transitions.

For example, it rejects a child task that:

- gains a permission its parent did not have;
- removes or changes a mandatory requirement;
- receives more budget than its parent can provide; or
- expands its allowed execution period or delegation depth.

The first test suite is running: **21 tests passed.**

But the most useful outcome wasn’t the number of tests. It was learning where a portable capsule is not enough.

Some checks can be made from the signed documents alone.

An agent can verify whether protected content changed, whether delegated authority only narrowed, whether mandatory requirements survived, and whether the parent-child link is valid.

Other checks require trusted shared state.

Imagine a task has a $100 budget and simultaneously delegates $60 to one child and $60 to another. Each delegation looks valid when examined alone. Together, they allocate $120.

The same issue appears when preventing one-time authority from being reused, determining whether a capsule was recently revoked, or coordinating several agents acting at once.

That led to an important design conclusion:

**A signed capsule can verify a delegation. It cannot coordinate a distributed system by itself.**

GCP will therefore need two complementary parts:

1. A portable, verifiable Governance Capsule that travels with the work.
2. Trusted enforcement state for allocation, replay, and revocation at execution boundaries.

Next, I’m building atomic budget allocation, replay protection, and revocation-freshness checks.

What can safely travel with the task—and what must rely on shared infrastructure?

#AIGovernance #AgenticAI #MultiAgentSystems #AISecurity #DistributedSystems #BuildInPublic

## Plain-language terms

- **Attenuation:** delegated permission can only narrow.
- **Replay:** reusing authority that was intended for one use.
- **Revocation freshness:** how recently the system checked whether authority was withdrawn.
- **Trusted shared state:** a reliable common record used to coordinate decisions across agents.
