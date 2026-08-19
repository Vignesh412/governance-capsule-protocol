"""Native Microsoft ACS gate. Run only in the Python 3.11 ACS CI job."""

import pytest

acs = pytest.importorskip("agent_control_specification")

from gcp_reference import (  # noqa: E402
    ACSInterventionRuntime,
    ActionProposal,
    PolicyEffect,
    PolicyLayer,
)


MANIFEST = {
    "agent_control_specification_version": "0.3.1-beta",
    "metadata": {"name": "gcp-acs-live-gate", "version": "0.1.0"},
    "policies": {
        "gcp_test_policy": {"type": "custom", "adapter": "gcp_test_dispatcher"}
    },
    "intervention_points": {
        "pre_tool_call": {
            "policy_target": "$.tool_call.args",
            "policy_target_kind": "tool_args",
            "tool_name_from": "$.tool_call.name",
            "policy": {"id": "gcp_test_policy"},
        }
    },
    "tools": {"create_vendor": {"clearance": "internal"}},
}


class FixedVerdictDispatcher:
    def __init__(self, decision):
        self.decision = decision
        self.invocations = []

    def evaluate(self, invocation):
        self.invocations.append(invocation)
        verdict = {
            "decision": self.decision,
            "reason": "gcp_native_gate",
            "evidence": {"artefact": "sha256:native-acs-gate"},
        }
        if self.decision == "transform":
            verdict["transform"] = {
                "path": "$policy_target.resource",
                "value": "vendor:redacted",
            }
        return verdict


def run_native(decision):
    dispatcher = FixedVerdictDispatcher(decision)
    control = acs.AgentControl.from_native(MANIFEST, policy_dispatcher=dispatcher)
    session = acs.HostSession(control)
    adapter = ACSInterventionRuntime(
        session,
        policy_id="gcp_test_policy",
        policy_version="0.3.1b1",
        layer=PolicyLayer.ORGANIZATIONAL,
        runtime_id="microsoft-acs:0.3.1b1",
    )
    evaluation = adapter.evaluate(
        ActionProposal(
            "native-call-1",
            "create_vendor",
            "vendor:42",
            "sha256:params",
        )
    )[0]
    assert dispatcher.invocations
    return evaluation


@pytest.mark.acs_live
@pytest.mark.parametrize(
    "decision,effect,controls",
    [
        ("allow", PolicyEffect.ALLOW, ()),
        ("warn", PolicyEffect.ALLOW, ("ACS_WARNING_AUDIT",)),
        ("deny", PolicyEffect.BLOCK, ()),
        ("escalate", PolicyEffect.REQUIRE_APPROVAL, ()),
        ("transform", PolicyEffect.ALLOW, ("ACS_APPLY_TRANSFORM",)),
    ],
)
def test_native_acs_verdict_round_trip(decision, effect, controls):
    evaluation = run_native(decision)
    assert evaluation.native_verdict == decision
    assert evaluation.effect == effect
    assert evaluation.required_controls == controls
    assert evaluation.evidence_artifact == "sha256:native-acs-gate"
    assert evaluation.runtime_id == "microsoft-acs:0.3.1b1"
