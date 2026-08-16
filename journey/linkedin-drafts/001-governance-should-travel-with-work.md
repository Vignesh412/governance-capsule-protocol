# LinkedIn Draft 001 - Governance should travel with the work

Status: Draft; hold until the landscape study is ready to link.

Enterprise AI governance is usually enforced around the agent currently taking an action.

But what happens when that agent delegates the work?

In a multi-agent workflow, permissions, policy constraints, approval requirements, risk limits, and accountability may be reinterpreted at every boundary. Existing frameworks provide powerful handoffs, guardrails, state, permissions, and traces—but governance continuity across heterogeneous systems appears to remain largely application-defined.

My working hypothesis is simple:

**Governance should travel with the work.**

I am beginning an open research and engineering project around the Governance Capsule: a portable, verifiable governance contract attached to a task as it moves among agents, tools, runtimes, and organizations.

The intended destination is a Governance Capsule Protocol. It is not a protocol or standard yet. Before making that claim, the project must define lifecycle behavior, authority delegation, obligation persistence, budget conservation, revocation, audit evidence, security, and interoperable implementations.

The first milestone is not code. It is a primary-source comparison of how OpenAI, Anthropic, Google, Microsoft, AWS, MCP, A2A, and major orchestration frameworks handle governance at delegation boundaries.

I plan to share the research, design decisions, prototypes, failures, and revisions as the work develops.

The question guiding the first stage:

**When one AI agent delegates work to another, what guarantees that the original governance requirements survive?**
