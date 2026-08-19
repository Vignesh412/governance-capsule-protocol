"""Google ADK receiving boundary for signed GCP transports."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Mapping, Optional, Sequence, Tuple
from ..action_kernel import DelegatedCapsuleActionVerifier
from ..crypto import KeyResolver
from ..errors import GCPError
from ..policy import ActionProposal
from ..replay import UseRegistry
from ..revocation import RevocationEvaluator, StatusProvider
from ..transport import FrameworkIdentity, VerifiedTransport, assert_proposal_matches_transport, verify_transport_envelope

GOOGLE_ADK_FRAMEWORK = "google-adk-python"


@dataclass(frozen=True)
class AcceptedADKDelegation:
    verified_transport: VerifiedTransport
    kernel_verifier: Callable[[ActionProposal], Tuple[str, ...]]


class GoogleADKGovernanceBoundary:
    def __init__(self, *, runtime_id: str, presenter: str, now: Callable[[], datetime],
                 resolver: KeyResolver, authorized_transport_sources: Mapping[str, Sequence[str]],
                 authorized_issuers: Mapping[str, Sequence[str]],
                 authorized_delegators: Mapping[str, Sequence[str]],
                 status_provider: Optional[StatusProvider] = None,
                 revocation_evaluator: Optional[RevocationEvaluator] = None,
                 obligation_verifier=None,
                 transport_replay_registry: Optional[UseRegistry] = None) -> None:
        self.identity = FrameworkIdentity(GOOGLE_ADK_FRAMEWORK, runtime_id)
        self.presenter, self._now, self._resolver = presenter, now, resolver
        self._authorized_transport_sources = authorized_transport_sources
        self._authorized_issuers, self._authorized_delegators = authorized_issuers, authorized_delegators
        self._status_provider, self._revocation_evaluator = status_provider, revocation_evaluator
        self._obligation_verifier = obligation_verifier
        self._transport_replay = transport_replay_registry or UseRegistry()

    def accept(self, envelope: Mapping[str, Any]) -> AcceptedADKDelegation:
        verified = verify_transport_envelope(
            envelope, resolver=self._resolver,
            authorized_sources=self._authorized_transport_sources,
            expected_destination=self.identity, now=self._now(),
            replay_registry=self._transport_replay,
            expected_source_framework="openai-agents-python")
        lineage_verifier = DelegatedCapsuleActionVerifier(
            verified.transitions, presenter=self.presenter, now=self._now,
            resolver=self._resolver, authorized_issuers=self._authorized_issuers,
            authorized_delegators=self._authorized_delegators,
            status_provider=self._status_provider,
            revocation_evaluator=self._revocation_evaluator,
            obligation_verifier=self._obligation_verifier)

        def kernel(proposal: ActionProposal) -> Tuple[str, ...]:
            assert_proposal_matches_transport(proposal, verified)
            return (
                "GCP_CROSS_FRAMEWORK_TRANSPORT_VERIFIED",
                "GCP_SOURCE_OPENAI_HANDOFF_VERIFIED",
                "GCP_DESTINATION_GOOGLE_ADK_BOUNDARY_VERIFIED",
            ) + tuple(lineage_verifier(proposal))
        return AcceptedADKDelegation(verified, kernel)


def build_google_adk_before_tool_callback(boundary: GoogleADKGovernanceBoundary, governed_executor=None):
    """Intercept an ADK tool call and route it through the governed executor.

    ADK skips the original tool whenever a before-tool callback returns a dict.
    This adapter therefore never returns None for a protected call: it returns
    either the gateway result or a fail-closed result.
    """
    async def before_tool_callback(tool, args: dict, tool_context):
        envelope = tool_context.state.get("gcp_transport")
        if envelope is None:
            return {"status": "blocked", "reason_code": "GCP_TRANSPORT_MISSING"}
        try:
            accepted = boundary.accept(envelope)
            proposal = ActionProposal(args["action_id"], args["action"], args["resource"],
                                      args["parameters_digest"], args.get("metadata", {}))
            tool_context.state["gcp_transport_digest"] = accepted.verified_transport.digest
            if governed_executor is None:
                return {"status": "blocked", "reason_code": "GCP_GATEWAY_EXECUTOR_REQUIRED"}
            return governed_executor(accepted, proposal)
        except (GCPError, KeyError, TypeError) as error:
            code = error.code.value if isinstance(error, GCPError) else "GCP_TRANSPORT_INVALID"
            return {"status": "blocked", "reason_code": code}
    return before_tool_callback
