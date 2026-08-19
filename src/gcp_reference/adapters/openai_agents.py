"""Optional OpenAI Agents SDK handoff boundary for GCP transports."""

from dataclasses import dataclass
from typing import Any, Mapping, MutableMapping, Sequence
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from ..action_kernel import DelegationTransition
from ..policy import ActionProposal
from ..transport import FrameworkIdentity, build_transport_envelope

OPENAI_AGENTS_FRAMEWORK = "openai-agents-python"


@dataclass
class OpenAIHandoffState:
    governance_transport: Mapping[str, Any] = None


class OpenAIGovernanceHandoffAdapter:
    def __init__(self, *, runtime_id: str, destination: FrameworkIdentity,
                 signing_key: Ed25519PrivateKey, verification_method: str) -> None:
        self.source = FrameworkIdentity(OPENAI_AGENTS_FRAMEWORK, runtime_id)
        self.destination = destination
        self._key, self._method = signing_key, verification_method

    def export(self, *, transport_id: str, proposal: ActionProposal,
               transitions: Sequence[DelegationTransition], created_at: str,
               expires_at: str, nonce: str) -> Mapping[str, Any]:
        return build_transport_envelope(
            transport_id=transport_id, source=self.source, destination=self.destination,
            proposal=proposal, transitions=transitions, created_at=created_at,
            expires_at=expires_at, nonce=nonce, signing_key=self._key,
            verification_method=self._method)

    def bind_to_run_context(self, wrapper: Any, envelope: Mapping[str, Any]) -> None:
        context = wrapper.context
        if isinstance(context, MutableMapping):
            context["governance_transport"] = envelope
        else:
            setattr(context, "governance_transport", envelope)


def build_openai_on_handoff(adapter: OpenAIGovernanceHandoffAdapter, envelope):
    """Return a callback compatible with the OpenAI on_handoff contract."""
    def on_handoff(ctx):
        adapter.bind_to_run_context(ctx, envelope)
    return on_handoff
