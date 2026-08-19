"""Framework-neutral policy-runtime contract for comparative evaluation."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Iterable, Mapping, Optional, Protocol, Tuple

from .errors import ErrorCode, GCPError


class PolicyLayer(str, Enum):
    REGULATORY = "regulatory"
    ORGANIZATIONAL = "organizational"
    TASK = "task"

    @property
    def weight(self) -> int:
        return {
            PolicyLayer.REGULATORY: 3,
            PolicyLayer.ORGANIZATIONAL: 2,
            PolicyLayer.TASK: 1,
        }[self]


class PolicyEffect(str, Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"


@dataclass(frozen=True)
class ActionProposal:
    action_id: str
    action: str
    resource: str
    parameters_digest: str
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PolicyEvaluation:
    policy_id: str
    policy_version: str
    layer: PolicyLayer
    effect: PolicyEffect
    rationale_code: str
    runtime_id: Optional[str] = None
    native_verdict: Optional[str] = None
    required_controls: Tuple[str, ...] = ()
    evidence_artifact: Optional[str] = None


class PolicyRuntime(Protocol):
    """Adapter boundary for AGT ACS, OPA, Cedar, or another evaluator."""

    @property
    def runtime_id(self) -> str: ...

    def evaluate(self, proposal: ActionProposal) -> Tuple[PolicyEvaluation, ...]: ...


class CallablePolicyRuntime:
    """Small adapter used by tests and external-runtime integrations."""

    def __init__(
        self,
        runtime_id: str,
        evaluator: Callable[[ActionProposal], Iterable[PolicyEvaluation]],
    ) -> None:
        self._runtime_id = runtime_id
        self._evaluator = evaluator

    @property
    def runtime_id(self) -> str:
        return self._runtime_id

    def evaluate(self, proposal: ActionProposal) -> Tuple[PolicyEvaluation, ...]:
        values = tuple(self._evaluator(proposal))
        seen = set()
        for value in values:
            key = (value.policy_id, value.policy_version)
            if key in seen:
                raise GCPError(
                    ErrorCode.POLICY_EVALUATION_INVALID,
                    "Policy runtime returned a duplicate policy version",
                    {"policy_id": value.policy_id, "policy_version": value.policy_version},
                )
            seen.add(key)
        return values
