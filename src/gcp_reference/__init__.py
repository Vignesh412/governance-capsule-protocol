"""Governance Capsule Protocol candidate reference library."""

from .allocation import AllocationLedger
from .action_kernel import CapsuleActionVerifier, DelegatedCapsuleActionVerifier, DelegationTransition
from .approval import (
    ApprovalRegistry,
    amendment_change_digest,
    validate_amendment,
    validate_approval,
)
from .adapters import (
    ACSInterventionRuntime,
    GoogleADKGovernanceBoundary,
    OpenAIGovernanceHandoffAdapter,
    OpenAIHandoffState,
    build_google_adk_before_tool_callback,
    build_openai_on_handoff,
)
from .carm import (
    CARMConfig,
    PolicyConflict,
    Resolution,
    ResolutionMode,
    RuntimeDecision,
    detect_conflicts,
    fixed_priority,
    most_restrictive,
    resolve_carm,
)
from .crypto import KeyResolver, artifact_digest, sign_artifact, verify_artifact
from .errors import ErrorCode, GCPError
from .replay import UseRegistry
from .revocation import (
    RevocationEvaluator,
    RevocationEvidence,
    RevocationResult,
    StatusRecord,
    status_from_signed_revocation,
)
from .schema import SchemaValidator, validate_structure
from .governance_graph import (
    GovernanceGraph,
    GraphEdge,
    GraphNode,
    JoinType,
    ReachEstimate,
)
from .gateway import (
    ActionRecord,
    ActionState,
    ConnectorOutcome,
    ConnectorResult,
    GovernedActionGateway,
    InMemorySupplierConnector,
    InMemoryActionStore,
    SimulatedProcessCrash,
)
from .persistence import SQLiteActionStore
from .policy import (
    ActionProposal,
    CallablePolicyRuntime,
    PolicyEffect,
    PolicyEvaluation,
    PolicyLayer,
    PolicyRuntime,
)
from .semantics import validate_audience, validate_delegation, validate_delegation_proof
from .transport import (
    FrameworkIdentity,
    VerifiedTransport,
    assert_proposal_matches_transport,
    build_transport_envelope,
    verify_transport_envelope,
)

__all__ = [
    "AllocationLedger",
    "ApprovalRegistry",
    "ACSInterventionRuntime",
    "ActionProposal",
    "ActionRecord",
    "ActionState",
    "CARMConfig",
    "CallablePolicyRuntime",
    "CapsuleActionVerifier",
    "DelegatedCapsuleActionVerifier",
    "DelegationTransition",
    "ConnectorOutcome",
    "ConnectorResult",
    "ErrorCode",
    "GCPError",
    "GovernanceGraph",
    "GoogleADKGovernanceBoundary",
    "GovernedActionGateway",
    "GraphEdge",
    "GraphNode",
    "JoinType",
    "InMemorySupplierConnector",
    "InMemoryActionStore",
    "SimulatedProcessCrash",
    "KeyResolver",
    "FrameworkIdentity",
    "VerifiedTransport",
    "OpenAIGovernanceHandoffAdapter",
    "OpenAIHandoffState",
    "PolicyConflict",
    "PolicyEffect",
    "PolicyEvaluation",
    "PolicyLayer",
    "PolicyRuntime",
    "ReachEstimate",
    "Resolution",
    "ResolutionMode",
    "RevocationEvaluator",
    "RevocationEvidence",
    "RevocationResult",
    "StatusRecord",
    "RuntimeDecision",
    "SchemaValidator",
    "SQLiteActionStore",
    "UseRegistry",
    "artifact_digest",
    "assert_proposal_matches_transport",
    "build_google_adk_before_tool_callback",
    "build_openai_on_handoff",
    "build_transport_envelope",
    "amendment_change_digest",
    "sign_artifact",
    "status_from_signed_revocation",
    "validate_audience",
    "validate_amendment",
    "validate_approval",
    "validate_delegation",
    "validate_delegation_proof",
    "verify_artifact",
    "verify_transport_envelope",
    "validate_structure",
    "detect_conflicts",
    "fixed_priority",
    "most_restrictive",
    "resolve_carm",
]
