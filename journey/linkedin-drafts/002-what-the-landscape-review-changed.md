# LinkedIn Draft 002 - What the landscape review changed

Status: Draft; ready for factual review before publishing.

I began with a hypothesis:

**Governance should travel with the work when AI agents delegate tasks.**

Before designing a protocol, I reviewed how eight major agent ecosystems currently handle handoffs, permissions, state, approvals, identity, and auditability:

- OpenAI Agents SDK
- Anthropic Claude Agent SDK and Managed Agents
- Google ADK
- Agent2Agent Protocol (A2A)
- Model Context Protocol (MCP)
- Microsoft Agent Framework
- Amazon Bedrock and AgentCore
- LangGraph

The research changed the proposal in an important way.

The industry already has strong building blocks:

- agent handoffs and subagents;
- runtime guardrails and middleware;
- human approval gates;
- persistent workflow state;
- workload identity and OAuth authorization;
- execution traces;
- A2A task transport; and
- MCP tool connectivity.

So a Governance Capsule Protocol should not try to replace any of those.

The narrower gap is what happens to **task governance across their boundaries**.

I did not find a vendor-neutral specification that combines:

1. authority that can only decrease during ordinary delegation;
2. mandatory obligations that cannot silently disappear;
3. conserved budgets across parallel child tasks;
4. cryptographically linked delegation lineage;
5. scoped approvals and amendments;
6. enforcement receipts; and
7. governance-aware replay and revocation rules.

One particularly relevant near-neighbor is Microsoft Agent Framework's FIDES security model, which propagates integrity and confidentiality labels with content. That is valuable prior art—not something to ignore. It appears complementary to task-level authority, budgets, approvals, and delegation lineage rather than a replacement for them.

The project direction is now clearer:

- use A2A as the agent-to-agent transport;
- use MCP at governed tool boundaries;
- use each framework's native hooks and middleware for enforcement;
- reuse established authorization and workload-identity standards; and
- focus GCP itself on governance inheritance, constrained transformation, and evidence.

The next milestone is intentionally small: formalize four invariants and make them executable tests.

- Authority attenuation
- Obligation persistence
- Lineage integrity
- Preallocated budget conservation

The working thesis is now more precise:

> GCP is a protocol candidate for verifiable continuity and constrained transformation of task governance across heterogeneous AI-agent systems.

The full landscape matrix, sources, and design decision will be published with the project repository.

What governance property do you believe is most likely to be lost at an agent handoff?
