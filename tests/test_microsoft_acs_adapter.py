from enum import Enum

import pytest

from gcp_reference import (
    ACSInterventionRuntime,
    ActionProposal,
    ErrorCode,
    GCPError,
    GovernanceGraph,
    GraphNode,
    PolicyEffect,
    PolicyLayer,
    ResolutionMode,
    RuntimeDecision,
    resolve_carm,
)


class NativeDecision(str, Enum):
    ALLOW = "allow"


class FakeControl:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def evaluate(self, intervention_point, snapshot):
        self.calls.append((intervention_point, snapshot))
        return self.result


def proposal():
    return ActionProposal("call-7", "create_vendor", "vendor:42", "sha256:params")


def runtime(result):
    return ACSInterventionRuntime(
        FakeControl(result),
        policy_id="urn:acs:policy:supplier",
        policy_version="7d0cef5",
        layer=PolicyLayer.ORGANIZATIONAL,
    )


@pytest.mark.parametrize(
    "native,effect,controls",
    [
        ("allow", PolicyEffect.ALLOW, ()),
        ("warn", PolicyEffect.ALLOW, ("ACS_WARNING_AUDIT",)),
        ("transform", PolicyEffect.ALLOW, ("ACS_APPLY_TRANSFORM",)),
        ("deny", PolicyEffect.BLOCK, ()),
        ("escalate", PolicyEffect.REQUIRE_APPROVAL, ()),
    ],
)
def test_maps_all_published_acs_verdicts_without_losing_controls(native, effect, controls):
    adapter = runtime(
        {
            "verdict": {
                "decision": native,
                "reason": "acs_test_reason",
                "evidence": {"artefact": "sha256:acs-proof"},
            }
        }
    )
    result = adapter.evaluate(proposal())[0]
    assert result.effect == effect
    assert result.native_verdict == native
    assert result.required_controls == controls
    assert result.evidence_artifact == "sha256:acs-proof"


def test_supports_object_and_enum_shaped_sdk_results():
    class Verdict:
        decision = NativeDecision.ALLOW
        reason = "object_result"
        evidence = None

    class Result:
        verdict = Verdict()

    assert runtime(Result()).evaluate(proposal())[0].effect == PolicyEffect.ALLOW


def test_builds_the_published_pre_tool_call_snapshot_shape():
    control = FakeControl({"verdict": {"decision": "allow"}})
    adapter = ACSInterventionRuntime(
        control,
        policy_id="policy",
        policy_version="1",
        layer=PolicyLayer.TASK,
    )
    adapter.evaluate(proposal())
    point, snapshot = control.calls[0]
    assert point == "pre_tool_call"
    assert snapshot["tool_call"]["name"] == "create_vendor"
    assert snapshot["tool_call"]["args"]["resource"] == "vendor:42"


def test_supports_acs_host_session_keyword_snapshot_surface():
    class HostSessionShape:
        def __init__(self):
            self.body = None

        def evaluate(self, intervention_point, **body):
            self.body = (intervention_point, body)
            return {"verdict": {"decision": "allow"}}

    session = HostSessionShape()
    adapter = ACSInterventionRuntime(
        session,
        policy_id="policy",
        policy_version="1",
        layer=PolicyLayer.TASK,
    )
    adapter.evaluate(proposal())
    assert session.body[0] == "pre_tool_call"
    assert session.body[1]["tool_call"]["id"] == "call-7"


def test_acs_escalation_is_not_relaxed_by_carm():
    evaluation = runtime({"verdict": {"decision": "escalate"}}).evaluate(proposal())
    result = resolve_carm(evaluation, GovernanceGraph([GraphNode("commit")], []), "commit")
    assert result.mode == ResolutionMode.ESCALATION_BOUNDARY
    assert result.decision == RuntimeDecision.APPROVAL_REQUIRED
    assert result.reason_codes == ("CARM_UPSTREAM_APPROVAL_REQUIRED",)


def test_unknown_verdict_fails_closed_at_adapter_boundary():
    with pytest.raises(GCPError) as caught:
        runtime({"verdict": {"decision": "permit"}}).evaluate(proposal())
    assert caught.value.code == ErrorCode.POLICY_RUNTIME_UNSUPPORTED_VERDICT


def test_runtime_exception_is_redacted_and_fails_closed():
    class BrokenControl:
        def evaluate(self, intervention_point, snapshot):
            raise RuntimeError("secret policy service detail")

    adapter = ACSInterventionRuntime(
        BrokenControl(),
        policy_id="policy",
        policy_version="1",
        layer=PolicyLayer.TASK,
    )
    with pytest.raises(GCPError) as caught:
        adapter.evaluate(proposal())
    assert caught.value.code == ErrorCode.POLICY_RUNTIME_UNAVAILABLE
    assert "secret" not in str(caught.value.as_dict())
