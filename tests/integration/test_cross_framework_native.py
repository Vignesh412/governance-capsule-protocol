"""Native SDK construction gate for the cross-framework adapter callbacks."""

import inspect

import pytest

agents = pytest.importorskip("agents")
google_adk = pytest.importorskip("google.adk")

from google.adk.agents import Agent as ADKAgent

from gcp_reference import (
    FrameworkIdentity,
    GoogleADKGovernanceBoundary,
    OpenAIGovernanceHandoffAdapter,
    build_google_adk_before_tool_callback,
    build_openai_on_handoff,
)


pytestmark = pytest.mark.frameworks_native


def test_native_frameworks_accept_gcp_callback_shapes():
    # No model call occurs. This gate only verifies the installed SDK
    # constructors accept the GCP boundary callbacks.
    openai_callback = build_openai_on_handoff(None, {})
    assert list(inspect.signature(openai_callback).parameters) == ["ctx"]

    target = agents.Agent(name="GCP transport destination")
    native_handoff = agents.handoff(agent=target, on_handoff=openai_callback)
    assert native_handoff is not None

    async def adk_callback(tool, args: dict, tool_context):
        return None

    def protected_supplier_tool(
        action_id: str,
        action: str,
        resource: str,
        parameters_digest: str,
    ) -> dict:
        """Represent a supplier action protected by the GCP callback."""
        return {"status": "not-executed-in-construction-test"}

    native_adk_agent = ADKAgent(
        name="gcp_supplier_operations",
        model="gemini-flash-latest",
        instruction="Use the supplier tool only after the governance callback allows it.",
        tools=[protected_supplier_tool],
        before_tool_callback=adk_callback,
    )
    assert native_adk_agent.before_tool_callback is adk_callback
