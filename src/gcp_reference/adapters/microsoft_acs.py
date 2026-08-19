"""Microsoft Agent Control Specification result adapter.

This module deliberately uses structural typing. Importing gcp_reference must not
require the optional Python 3.11+ ACS wheel, and tests can exercise the published
ACS result contract without pretending that the native runtime executed.
"""

from collections.abc import Mapping
from inspect import Parameter, signature
from typing import Any, Callable, Optional, Tuple

from ..errors import ErrorCode, GCPError
from ..policy import ActionProposal, PolicyEffect, PolicyEvaluation, PolicyLayer


def _member(value: Any, name: str, default: Any = None) -> Any:
    if isinstance(value, Mapping):
        return value.get(name, default)
    return getattr(value, name, default)


def _text(value: Any) -> Optional[str]:
    if value is None:
        return None
    native = getattr(value, "value", value)
    return str(native)


class ACSInterventionRuntime:
    """Normalize one ACS intervention-point verdict into GCP policy evidence."""

    SUPPORTED_VERDICTS = {"allow", "warn", "deny", "escalate", "transform"}

    def __init__(
        self,
        control: Any,
        *,
        policy_id: str,
        policy_version: str,
        layer: PolicyLayer,
        intervention_point: str = "pre_tool_call",
        runtime_id: str = "microsoft-acs",
        snapshot_builder: Optional[Callable[[ActionProposal], Mapping[str, Any]]] = None,
    ) -> None:
        self._control = control
        self._policy_id = policy_id
        self._policy_version = policy_version
        self._layer = layer
        self._intervention_point = intervention_point
        self._runtime_id = runtime_id
        self._snapshot_builder = snapshot_builder or self._default_snapshot

    @property
    def runtime_id(self) -> str:
        return self._runtime_id

    @staticmethod
    def _default_snapshot(proposal: ActionProposal) -> Mapping[str, Any]:
        return {
            "tool_call": {
                "id": proposal.action_id,
                "name": proposal.action,
                "args": {
                    "resource": proposal.resource,
                    "parameters_digest": proposal.parameters_digest,
                },
            },
            "metadata": dict(proposal.metadata),
        }

    def evaluate(self, proposal: ActionProposal) -> Tuple[PolicyEvaluation, ...]:
        evaluate = getattr(self._control, "evaluate", None)
        if not callable(evaluate):
            raise GCPError(
                ErrorCode.POLICY_RUNTIME_UNAVAILABLE,
                "ACS control does not expose the synchronous evaluate interface",
                {"runtime_id": self.runtime_id},
            )
        try:
            snapshot = self._snapshot_builder(proposal)
            parameters = signature(evaluate).parameters.values()
            accepts_snapshot_keywords = any(
                parameter.kind == Parameter.VAR_KEYWORD for parameter in parameters
            )
            if accepts_snapshot_keywords:
                # ACS HostSession.evaluate(point, **snapshot) is the stable
                # synchronous host surface in the Python SDK.
                result = evaluate(self._intervention_point, **snapshot)
            else:
                # Retain compatibility with the documented direct control/test
                # shape evaluate(point, snapshot).
                result = evaluate(self._intervention_point, snapshot)
        except Exception as error:
            raise GCPError(
                ErrorCode.POLICY_RUNTIME_UNAVAILABLE,
                "ACS evaluation failed",
                {"runtime_id": self.runtime_id, "error_type": type(error).__name__},
            ) from error

        verdict = _member(result, "verdict", result)
        decision = (_text(_member(verdict, "decision")) or "").lower()
        if decision not in self.SUPPORTED_VERDICTS:
            raise GCPError(
                ErrorCode.POLICY_RUNTIME_UNSUPPORTED_VERDICT,
                "ACS returned an unsupported verdict",
                {"runtime_id": self.runtime_id, "verdict": decision},
            )

        reason = _text(_member(verdict, "reason")) or "ACS_NO_REASON"
        evidence = _member(verdict, "evidence")
        evidence_artifact = _text(_member(evidence, "artefact")) if evidence else None
        controls = []
        if decision == "warn":
            controls.append("ACS_WARNING_AUDIT")
        elif decision == "transform":
            controls.append("ACS_APPLY_TRANSFORM")

        effect = {
            "allow": PolicyEffect.ALLOW,
            "warn": PolicyEffect.ALLOW,
            "transform": PolicyEffect.ALLOW,
            "deny": PolicyEffect.BLOCK,
            "escalate": PolicyEffect.REQUIRE_APPROVAL,
        }[decision]
        return (
            PolicyEvaluation(
                policy_id=self._policy_id,
                policy_version=self._policy_version,
                layer=self._layer,
                effect=effect,
                rationale_code=reason,
                runtime_id=self.runtime_id,
                native_verdict=decision,
                required_controls=tuple(controls),
                evidence_artifact=evidence_artifact,
            ),
        )
