# Milestone 0 Landscape Report

## Executive conclusion

Primary-source review of OpenAI, Anthropic, Google ADK, A2A, MCP, Microsoft Agent Framework, AWS AgentCore/Bedrock, and LangGraph did not identify a complete vendor-neutral protocol for governance continuity across delegated AI work.

The review also showed that many parts of the original concept already exist separately. GCP would be redundant if it attempted to replace handoffs, guardrails, workflow state, identity, OAuth, traces, MCP, or A2A.

The defensible gap is narrower:

> No reviewed system normatively defines how a task-level governance contract is inherited, attenuated, amended, divided, revoked, and evidenced across heterogeneous agent and tool boundaries.

This conclusion is bounded by the sources and review date. It is not proof that no unreviewed implementation or emerging draft addresses the gap.

## Method

Review date: 2026-08-11

For each system, the review examined:

- durable task and session identity;
- handoff and delegation behavior;
- context propagation;
- local permissions and policy interception;
- human approval;
- tracing and audit evidence;
- portable authority;
- authority attenuation;
- obligation persistence;
- fork/join and budget semantics;
- cryptographic lineage;
- revocation and replay behavior;
- cross-organization interoperability; and
- extension mechanisms.

Capabilities were classified as native, extension-based, application-defined, absent in reviewed sources, or unknown. Arbitrary state and metadata count as extension surfaces, not governance guarantees.

## 1. OpenAI Agents SDK

### Native mechanisms

OpenAI documents agents, tool use, and agent handoffs as SDK primitives. The runner manages handoffs and tool calls. The SDK also provides local context, guardrails, lifecycle hooks, human-in-the-loop mechanisms, sessions, and tracing.

Handoffs transfer control within a run and can filter or reshape the history presented to the next agent. Application context can carry arbitrary typed state. Traces can record agent and tool activity.

### Governance interpretation

These features provide good adapter points for GCP:

- handoff callbacks for capsule derivation;
- run context for local capsule access;
- tool guardrails/hooks for action enforcement;
- approval interruptions for GCP approval requirements; and
- trace correlation for enforcement receipts.

The reviewed documentation does not define a standard governance object, authority attenuation, inherited mandatory obligations, signed parent-child delegation, conserved fork budgets, or cross-runtime revocation semantics. Application-defined context can implement these, but another OpenAI application would not automatically interpret them the same way.

### Important boundary

Conversation history is not governance authority. A prompt instruction telling a downstream agent to preserve restrictions is not deterministic enforcement.

### Primary sources

- [OpenAI API developer quickstart: Agents SDK handoffs](https://platform.openai.com/docs/quickstart/make-your-first-api-request), reviewed 2026-08-11.
- [OpenAI platform API reference: MCP approvals and tracing](https://platform.openai.com/docs/api-reference/realtime), reviewed 2026-08-11.

## 2. Anthropic Claude Agent SDK and Managed Agents

### Native mechanisms

The official Claude Agent SDK repository documents:

- subagents and session forking;
- tool allowlists and denylists;
- permission modes and `can_use_tool` callbacks;
- pre- and post-tool hooks;
- session identifiers and transcripts; and
- subagent identifiers in lifecycle hook data.

Claude Managed Agents adds server-side tool permission policies. Tools can be automatically allowed or can pause a session until the application supplies an allow/deny confirmation. MCP tools default to asking for approval, while custom-tool execution remains the application's responsibility.

### Governance interpretation

The SDK and Managed Agents provide deterministic permission and approval points. They do not specify a portable parent-to-child governance contract or a vendor-neutral derivation rule. Permissions are configured within the session, agent, toolset, or application. A developer could store and validate a capsule using hooks, but the capsule semantics would remain external.

### Important boundary

“Allowed tools” is not equivalent to delegated authority. An allowlist describes what a runtime will auto-approve or expose; it does not prove which parent task authorized a particular child action.

### Primary sources

- [Anthropic Claude Agent SDK for Python](https://github.com/anthropics/claude-agent-sdk-python), reviewed 2026-08-11.
- [Claude Managed Agents permission policies](https://platform.claude.com/docs/en/managed-agents/permission-policies), reviewed 2026-08-11.

## 3. Google Agent Development Kit

### Native mechanisms

Google ADK supports parent/subagent composition and workflow agents. Subagents in a workflow share invocation and session context; state, events, artifacts, and memory provide persistence mechanisms.

Callbacks wrap agent, model, and tool execution. A before-tool callback can inspect or replace arguments, prevent tool execution, or provide an alternate result. Google recommends plugins for modular security guardrails. ADK also integrates with A2A and MCP.

### Governance interpretation

ADK is highly suitable for a GCP enforcement adapter:

- session state can hold the effective capsule;
- callbacks/plugins can validate handoffs and tool use;
- events can correlate receipts; and
- A2A support can carry GCP across a remote boundary.

The reviewed sources do not make governance state a protected object. Shared mutable state does not itself provide integrity, attenuation, mandatory-obligation persistence, or cross-organization semantics.

### Primary sources

- [Google ADK callbacks](https://adk.dev/callbacks/), reviewed 2026-08-11.
- [Google ADK state](https://adk.dev/sessions/state/), reviewed 2026-08-11.
- [Google ADK Python source](https://github.com/google/adk-python), reviewed 2026-08-11.

## 4. Agent2Agent Protocol

### Native mechanisms

A2A is the closest existing protocol substrate for GCP. It defines:

- server-generated task IDs;
- task lifecycle states;
- context IDs for related interactions;
- messages, artifacts, status events, polling, streaming, and push notifications;
- Agent Cards describing capabilities and security schemes;
- authenticated extended Agent Cards;
- OAuth and OpenID Connect security descriptions;
- optional Agent Card signatures; and
- versioned extension declaration and negotiation.

A2A extensions can contribute structured metadata to messages and artifacts. Clients opt in through binding-specific mechanisms such as HTTP headers, gRPC metadata, or request parameters.

### Governance interpretation

A2A removes the need for GCP to invent agent discovery, remote task lifecycle, streaming, or transport bindings. GCP should initially be an A2A extension/profile.

However, core A2A does not define:

- task-level delegated authority;
- parent-child authority attenuation;
- obligation inheritance;
- budget splitting;
- signed task-delegation chains;
- governance amendments;
- enforcement receipts; or
- governance-specific revocation.

Agent Card signatures protect capability advertisements, not an execution task's governance lineage. A2A task cancellation is operational lifecycle control, not necessarily revocation of delegated authority in descendant systems.

### Primary source

- [A2A Protocol specification](https://a2a-protocol.org/latest/specification/), reviewed 2026-08-11.

## 5. Model Context Protocol

### Native mechanisms

MCP standardizes connections between applications and tool/context servers. Its authorization specification uses OAuth 2.1-related mechanisms, protected-resource metadata, authorization-server discovery, resource indicators, scope challenges, token audience validation, and secure error behavior.

The current specification explicitly forbids token passthrough. Tokens must be issued for and validated by the intended MCP resource. MCP also supports protocol capabilities, structured metadata, and user elicitation.

### Governance interpretation

MCP is the correct GCP boundary for governed tool invocation, but not the source of a task-governance lifecycle.

GCP must not become a vehicle for forwarding the original user's or agent's bearer credential. Instead, a GCP-aware MCP adapter should:

- validate the task capsule locally;
- obtain an appropriately audience-bound credential through normal authorization;
- send action-relevant governance metadata or a capsule digest;
- receive a signed or authenticated enforcement result; and
- correlate the tool action with the task lineage.

MCP authorization answers whether a client can access a resource. It does not by itself specify how obligations, budgets, approvals, or responsibility persist across downstream tasks.

### Primary sources

- [MCP authorization specification](https://modelcontextprotocol.io/specification/draft/basic/authorization), reviewed 2026-08-11.
- [MCP security best practices](https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices), reviewed 2026-08-11.

## 6. Microsoft Agent Framework

### Native mechanisms

Microsoft Agent Framework provides:

- mesh-style handoff orchestration;
- agent-as-tool and several workflow patterns;
- synchronized conversation context across handoff participants;
- durable workflow checkpointing;
- approval-required tools and human-in-the-loop request/response behavior;
- agent, function, and chat-client middleware;
- execution termination from middleware; and
- workflow observability.

### FIDES: the most relevant near-neighbor

Microsoft's FIDES security integration attaches `security_label` data to content. Labels track integrity and confidentiality, and restrictive values dominate when content is combined. Middleware uses the labels to constrain sensitive information flow.

This is materially related to GCP because it demonstrates portable, monotonic security metadata traveling with content inside an agent framework.

It does not eliminate the GCP gap because the reviewed FIDES model does not define:

- task ownership or delegation lineage;
- permitted actions over resources;
- cost/risk/delegation budgets;
- signed cross-organization transformations;
- governance amendments and approvals; or
- cross-vendor lifecycle and receipt semantics.

GCP should avoid competing with FIDES. Integrity and confidentiality labels should be considered a candidate GCP obligation/control type.

### Important boundary

Microsoft explicitly describes Agent Framework authentication, encryption, and external connection security as developer responsibilities. Middleware is an enforcement surface, not a portable protocol guarantee.

### Primary sources

- [Microsoft Agent Framework handoff orchestration](https://learn.microsoft.com/en-us/agent-framework/user-guide/workflows/orchestrations/handoff), reviewed 2026-08-11.
- [Agent Framework middleware](https://learn.microsoft.com/en-us/agent-framework/agents/middleware/), reviewed 2026-08-11.
- [Agent Framework safety](https://learn.microsoft.com/en-us/agent-framework/agents/safety), reviewed 2026-08-11.
- [Agent Security with FIDES](https://learn.microsoft.com/en-us/agent-framework/agents/security), reviewed 2026-08-11.

## 7. Amazon Bedrock Agents and AgentCore

### Current product boundary

AWS documentation states that Bedrock Agents Classic entered maintenance status for new customers in July 2026 and directs new development toward Bedrock AgentCore. The review therefore treats AgentCore as the strategically relevant platform while retaining Classic collaboration behavior for comparison.

### Native mechanisms

Bedrock Agents Classic provides centralized supervisor/collaborator orchestration, optional conversation-history sharing, per-agent tools, action groups, knowledge bases, guardrails, and traces.

AgentCore adds framework-neutral runtime hosting, distinct workload identities, IAM and resource policies, credential management for user-delegated and autonomous access, gateway support for MCP, A2A support, and CloudWatch/OpenTelemetry observability.

### Governance interpretation

AgentCore is the strongest reviewed platform for identity and access infrastructure. It can supply trusted runtime identity, resource authorization, credential acquisition, and audit telemetry to a GCP implementation.

The reviewed sources do not define task-capsule inheritance, parent-child authority attenuation, mandatory-obligation preservation, forked budget conservation, or signed task-governance receipts across non-AWS systems. These can be built with AgentCore services, but their semantics remain application-defined.

### Primary sources

- [Amazon Bedrock multi-agent collaboration](https://docs.aws.amazon.com/en_us/bedrock/latest/userguide/agents-multi-agent-collaboration.html), reviewed 2026-08-11.
- [Amazon Bedrock AgentCore overview](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/), reviewed 2026-08-11.
- [AgentCore Identity](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/identity.html), reviewed 2026-08-11.
- [AgentCore Runtime](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agents-tools-runtime.html), reviewed 2026-08-11.

## 8. LangGraph and LangChain agents

### Native mechanisms

LangGraph provides state graphs, handoffs through state transitions and commands, persistent checkpoints, interrupts, replay, graph forks, and fault-tolerant execution. LangChain middleware can inspect agent steps and tool calls. Human-in-the-loop middleware pauses configured tool calls and supports approval, argument editing, or rejection.

LangSmith traces model calls, tools, decisions, and metadata across runs and threads.

### Governance interpretation

LangGraph is an excellent prototyping environment for GCP fork/join and approval semantics because graph state and reducers are explicit. It does not prescribe what governance state means or protect it from unauthorized mutation. Cross-runtime interoperability, cryptographic derivation, authority attenuation, obligation persistence, and budget conservation remain application-defined.

### Primary sources

- [LangGraph handoffs](https://docs.langchain.com/oss/python/langchain/multi-agent/handoffs), reviewed 2026-08-11.
- [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence), reviewed 2026-08-11.
- [LangGraph interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts), reviewed 2026-08-11.
- [LangChain human-in-the-loop middleware](https://docs.langchain.com/oss/python/langchain/human-in-the-loop), reviewed 2026-08-11.
- [LangSmith observability concepts](https://docs.langchain.com/langsmith/observability-concepts), reviewed 2026-08-11.

## Adjacent standards GCP must reuse or distinguish itself from

### OAuth 2.0 Rich Authorization Requests

RFC 9396 defines structured `authorization_details` for fine-grained access requests. GCP should evaluate whether its action/resource authority profile can reuse or embed RAR-compatible authorization details instead of creating a competing permission vocabulary.

RAR does not define multi-agent task lineage, inherited obligations, conserved budgets, or enforcement receipts.

Source: [RFC 9396](https://www.rfc-editor.org/rfc/rfc9396.html), reviewed 2026-08-11.

### OAuth 2.0 Token Exchange

RFC 8693 defines exchanging a subject token and, optionally, actor information for another token. It includes delegation and impersonation concepts relevant to downstream access.

GCP should use token exchange where actual resource credentials must be minted. It should not copy bearer credentials into capsules. Token exchange still does not provide a complete task-governance lifecycle.

Source: [RFC 8693](https://www.rfc-editor.org/rfc/rfc8693.html), reviewed 2026-08-11.

### SPIFFE

SPIFFE supplies interoperable workload identities, short-lived verifiable identity documents, trust bundles, and federation across trust domains. It is a candidate identity profile for GCP runtimes and signers.

SPIFFE identifies workloads; it does not define the governance contract attached to a delegated task.

Sources: [SPIFFE Workload API](https://spiffe.io/docs/latest/spiffe-specs/spiffe_workload_api/) and [SPIFFE federation](https://spiffe.io/docs/latest/spiffe-specs/spiffe_federation/), reviewed 2026-08-11.

### W3C Verifiable Credentials

The W3C Verifiable Credentials model defines issuer-holder-verifier claims with cryptographic integrity, status/revocation mechanisms, evidence, and extensibility. It is a candidate representation for issuer assertions or approvals.

GCP should not automatically become a VC profile. The project must compare VC complexity, privacy properties, canonicalization, and ecosystem support against simpler signed envelopes before deciding.

Source: [W3C Verifiable Credentials Data Model family](https://www.w3.org/TR/vc-data-model/all/), reviewed 2026-08-11.

## Gap analysis

### What GCP must not claim as novel

- Multi-agent handoffs
- Persistent task or workflow state
- Runtime guardrails and middleware
- Human approval of tools
- Agent/workload identity
- OAuth-based authorization
- Signed claims in general
- Execution tracing
- Information-flow labels
- Agent discovery and transport
- Tool interoperability

### Candidate novel composition

The potentially distinctive contribution is the composition of:

1. A task-bound portable governance contract
2. Normative parent-to-child derivation
3. Authority attenuation
4. Mandatory-obligation persistence
5. Conserved budget allocation
6. Scoped, expiring approval amendments
7. Cryptographic delegation lineage
8. Runtime enforcement receipts
9. Governance-aware replay and revocation rules
10. Bindings that preserve the same semantics across A2A, MCP, and local SDKs

The novelty will depend on the precision of these semantics and independent implementations, not the capsule metaphor.

## Recommended technical direction

### GCP Core

Define only transport-independent governance semantics:

- capsule model;
- derivation and amendment rules;
- fork and join behavior;
- approval scope;
- replay and revocation;
- receipt requirements;
- conformance tests.

### GCP-A2A profile

Use A2A for:

- extension discovery and version negotiation;
- task and context IDs;
- task status transitions;
- durable governance metadata;
- governance-specific failure results; and
- receipt artifacts or references.

### GCP-MCP profile

Use MCP for:

- governed tool-call metadata;
- audience-bound authorization;
- approval/elicitation integration;
- capsule digest and task correlation; and
- tool enforcement receipts.

### Framework adapters

Use native enforcement surfaces:

- OpenAI guardrails, handoff hooks, context, and tracing;
- Anthropic permissions and hooks;
- Google ADK callbacks/plugins and events;
- Microsoft middleware, approvals, and optional FIDES labels;
- AWS identity, policies, runtime, and observability; and
- LangGraph state, reducers, interrupts, and checkpoints.

## Risks discovered

1. **Scope inflation:** “governance” can absorb identity, policy language, compliance, provenance, and observability. GCP must stay focused on continuity and transformation.
2. **Metadata theater:** carrying a capsule is meaningless unless deterministic enforcement points validate it.
3. **False cryptographic confidence:** signatures establish integrity and issuer, not truthfulness or correct enforcement.
4. **Policy confidentiality:** cross-organization capsules cannot expose full internal policy logic.
5. **Distributed budgets:** portable signed state cannot alone prevent parallel double spending.
6. **Revocation latency:** offline or disconnected agents may act before learning of revocation.
7. **Extension downgrade:** optional A2A/MCP extensions can be silently omitted unless GCP negotiation fails closed.
8. **Vocabulary mismatch:** vendors express tools, actions, resources, and approvals differently.
9. **Overlap with emerging work:** FIDES and fast-moving platform features require repeated review.

## Milestone decision

Proceed to Milestone 1, with a narrower thesis:

> GCP is a protocol candidate for verifiable continuity and constrained transformation of task governance across heterogeneous AI-agent and tool boundaries.

The next milestone should formalize only four invariants first:

1. authority attenuation;
2. mandatory-obligation persistence;
3. lineage integrity; and
4. preallocated budget conservation for tree-shaped delegation.

Join semantics, privacy-preserving disclosure, and cross-organization truth verification should remain explicit open problems rather than being hidden inside the v0.1 schema.
