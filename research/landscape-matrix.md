# Agent Governance Continuity Landscape

Status: Milestone 0 review complete

Last reviewed: 2026-08-11

The detailed reasoning and source notes are in `research/milestone-0-landscape-report.md`.

## Classification

- **N** - Native: explicitly implemented and documented.
- **E** - Extension: possible through an official hook, middleware, metadata, or extension point, but semantics are application-defined.
- **A** - Application-defined: implementers must create their own convention or external service.
- **0** - No mechanism found in the reviewed primary sources.
- **?** - Evidence insufficient.

These labels describe the reviewed feature, not the overall quality or security of the system.

## Evidence rules

1. Prefer normative specifications, official documentation, and official source repositories.
2. Record the source URL and review date for every material conclusion.
3. Do not infer protocol guarantees from illustrative code.
4. Do not treat tracing as enforcement, authentication as delegated authority, or context propagation as governance continuity.
5. Do not treat arbitrary metadata as a native governance contract.
6. Absence means “not found in the reviewed scope,” not proof that no private or newer implementation exists.

## Comparison matrix

| Dimension | OpenAI Agents SDK | Claude Agent SDK / Managed Agents | Google ADK | A2A | MCP | Microsoft Agent Framework | AWS AgentCore / Bedrock | LangGraph |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Durable task identity | A | N session | N session/invocation | **N** | N task capability, otherwise request IDs | N workflow/checkpoint | N session/runtime | N thread/checkpoint |
| Agent/runtime identity | A | N managed runtime; A local SDK | A; N with cloud identity | N auth discovery; identity semantics external | N OAuth client/resource identity | A; deployment identity external | **N** workload identity/IAM | A; deployment identity external |
| Delegation/handoff | **N** | **N** subagents | **N** subagents/workflows | **N** remote agent interaction | A for agent delegation; N for tool/server calls | **N** | **N** supervisor/collaborator or A2A | **N** graph/subagent patterns |
| Context/state transfer | N within run; E filters/context | N within session; E hooks | N within invocation/session | N messages, task/context IDs, metadata | N request/response content and metadata | N synchronized messages/workflow state | N optional conversation history/session | N graph state/checkpoints |
| Local action interception | N guardrails/hooks | N permissions/hooks | N callbacks/plugins | A at server | A at server/client | N middleware/FIDES | N policy/IAM/guardrails | N middleware/interrupts |
| Human approval | N tool approval | N confirmation policies | E callback/action confirmation | N input-required state; decision semantics A | N elicitation; action semantics A | N tool approval/HITL | N service-specific controls | N HITL middleware/interrupts |
| Execution tracing | **N** | N events/transcripts | N events/cloud traces | N task status/history, not full execution audit | N protocol requests, not full execution audit | **N** telemetry | **N** CloudWatch/ADOT | **N** checkpoints/LangSmith |
| Portable authority object | 0 | 0 | 0 | E metadata/extension | E metadata; OAuth tokens are resource-bound | E metadata/security labels | E identity/token/policy services | E graph state |
| Authority attenuation across delegation | A | A | A | 0 | 0; token passthrough forbidden | A | A via application/token service | A |
| Mandatory-obligation persistence | A | A | A | E extension | E metadata | E FIDES labels cover information flow, not general obligations | A | A |
| Budget conservation across forks | A | A | A | 0 | 0 | A | A | A reducers/state |
| Signed delegation lineage | 0 | 0 | 0 | E signed Agent Card does not sign task lineage | 0 at task-governance level | 0 | A through custom identity/evidence | 0 |
| Signed enforcement receipts | 0 | 0 | 0 | E artifacts/metadata, semantics undefined | E result metadata, semantics undefined | 0 | A/custom | 0 |
| Governance revocation | A | A | A | A task cancellation is not authority revocation | N token revocation/expiry where supported; not task governance | A | N IAM/token revocation; task semantics A | A |
| Fork/join governance semantics | A | A | A | 0 | 0 | A | A | A graph reducers |
| Cross-organization portability | A | A | A/A2A | **N transport and discovery** | **N tool connectivity and auth** | A/A2A | N platform services; A/A2A for agents | A/A2A |
| Governance-specific failure codes | A | A | A | E extension errors | E application errors | A | A | A |
| Protocol extension surface | A | A/MCP | N plugins/A2A/MCP | **N** versioned extensions | **N** metadata/capabilities | A | N A2A/MCP support | A |

## What the matrix establishes

### Strong native building blocks already exist

- Agent handoffs and subagent orchestration
- Runtime callbacks, guardrails, middleware, and approval gates
- Persistent sessions, graph checkpoints, and task lifecycles
- Agent/tool authentication and workload identity
- Execution traces and workflow observability
- A2A task transport and extension negotiation
- MCP resource-bound authorization and tool interoperability
- FIDES-style information-flow labels inside Microsoft Agent Framework

GCP must reuse or bind to these features rather than reproduce them.

### The unresolved common layer

The review found no native, vendor-neutral combination of:

1. A portable governance contract bound to a durable task
2. Normative authority-attenuating derivation
3. Mandatory-obligation persistence
4. Conserved budget allocation across task forks
5. Cryptographically linked delegation proofs
6. Scoped approvals and amendments
7. Signed enforcement receipts
8. Governance-aware revocation and replay rules
9. Consistent behavior across heterogeneous runtimes

## Revised integration hypothesis

GCP should be a **governance profile and lifecycle protocol**, not a new general agent transport.

- Use **A2A extensions** for remote agent discovery, negotiation, task carriage, lifecycle updates, and governance-specific errors.
- Use **MCP metadata and authorization boundaries** for governed tool calls, without forwarding bearer credentials.
- Use framework-native hooks, middleware, callbacks, approvals, and traces as local enforcement and evidence adapters.
- Reuse OAuth Rich Authorization Requests or equivalent structures for fine-grained authorization details where suitable.
- Reuse workload identity such as SPIFFE or cloud-native identity rather than defining “agent identity.”
- Evaluate W3C Verifiable Credentials or a simpler signed-envelope profile for issuer/verifier claims; do not automatically adopt VC complexity.
- Treat Microsoft FIDES labels as complementary information-flow controls that could be carried as one GCP obligation type.

## Milestone 0 conclusion

The original gap hypothesis **survives, but is narrowed**.

The opportunity is not “governance for agents” in general. Major systems already offer substantial governance controls. The opportunity is **verifiable continuity and constrained transformation of task governance across independent systems**.
