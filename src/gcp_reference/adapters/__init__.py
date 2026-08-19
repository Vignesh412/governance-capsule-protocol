"""Optional policy-runtime adapters."""

from .microsoft_acs import ACSInterventionRuntime
from .openai_agents import (
    OpenAIGovernanceHandoffAdapter,
    OpenAIHandoffState,
    build_openai_on_handoff,
)
from .google_adk import (
    AcceptedADKDelegation,
    GoogleADKGovernanceBoundary,
    build_google_adk_before_tool_callback,
)

__all__ = [
    "ACSInterventionRuntime",
    "AcceptedADKDelegation",
    "GoogleADKGovernanceBoundary",
    "OpenAIGovernanceHandoffAdapter",
    "OpenAIHandoffState",
    "build_google_adk_before_tool_callback",
    "build_openai_on_handoff",
]
