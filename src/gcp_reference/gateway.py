"""In-memory Governed Action Gateway reference profile.

The gateway is the sole caller of a protected connector. It demonstrates the
transaction and recovery semantics before a durable PostgreSQL implementation.
"""

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from threading import RLock
from typing import Any, Callable, Dict, Mapping, Optional, Protocol, Tuple

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from .carm import RuntimeDecision, resolve_carm
from .crypto import artifact_digest, sign_artifact
from .errors import ErrorCode, GCPError
from .governance_graph import GovernanceGraph
from .policy import ActionProposal, PolicyEvaluation, PolicyRuntime


class ActionState(str, Enum):
    PROPOSED = "PROPOSED"
    VALIDATING = "VALIDATING"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    AUTHORIZED = "AUTHORIZED"
    RESERVED = "RESERVED"
    COMMITTING = "COMMITTING"
    COMMITTED = "COMMITTED"
    COMMIT_OUTCOME_UNKNOWN = "COMMIT_OUTCOME_UNKNOWN"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


class ConnectorOutcome(str, Enum):
    COMMITTED = "COMMITTED"
    NOT_COMMITTED = "NOT_COMMITTED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ConnectorResult:
    outcome: ConnectorOutcome
    result_reference: Optional[str] = None
    result_digest: Optional[str] = None


class ProtectedConnector(Protocol):
    def commit(self, action_id: str, proposal: ActionProposal) -> ConnectorResult: ...
    def reconcile(self, action_id: str) -> ConnectorResult: ...


KernelVerifier = Callable[[ActionProposal], Tuple[str, ...]]
ApprovalVerifier = Callable[[ActionProposal], bool]


@dataclass(frozen=True)
class ActionRecord:
    action_id: str
    proposal_digest: str
    state: ActionState
    attempt: int
    decision: Optional[RuntimeDecision] = None
    controls: Tuple[str, ...] = ()
    reason_codes: Tuple[str, ...] = ()
    graph_digest: Optional[str] = None
    policy_snapshot_digest: Optional[str] = None
    result_reference: Optional[str] = None
    result_digest: Optional[str] = None
    receipt: Optional[Mapping[str, Any]] = None
    proposal: Optional[Mapping[str, Any]] = None


class ActionStore(Protocol):
    """Durable state boundary used by the gateway."""

    def claim(self, record: ActionRecord) -> Optional[ActionRecord]: ...
    def get(self, action_id: str) -> Optional[ActionRecord]: ...
    def put(self, record: ActionRecord) -> None: ...
    def delete_waiting(self, action_id: str, expected: ActionState) -> None: ...
    def pending_commits(self) -> Tuple[ActionRecord, ...]: ...


class InMemoryActionStore:
    def __init__(self) -> None:
        self._records: Dict[str, ActionRecord] = {}
        self._lock = RLock()

    def claim(self, record: ActionRecord) -> Optional[ActionRecord]:
        with self._lock:
            existing = self._records.get(record.action_id)
            if existing is None:
                self._records[record.action_id] = record
            return existing

    def get(self, action_id: str) -> Optional[ActionRecord]:
        with self._lock:
            return self._records.get(action_id)

    def put(self, record: ActionRecord) -> None:
        with self._lock:
            self._records[record.action_id] = record

    def delete_waiting(self, action_id: str, expected: ActionState) -> None:
        with self._lock:
            current = self._records.get(action_id)
            if current is None or current.state != expected:
                raise GCPError(ErrorCode.ACTION_STATE_INVALID, "Action state changed before resume")
            del self._records[action_id]

    def pending_commits(self) -> Tuple[ActionRecord, ...]:
        with self._lock:
            return tuple(
                record for record in self._records.values()
                if record.state in {ActionState.COMMITTING, ActionState.COMMIT_OUTCOME_UNKNOWN}
            )


def _proposal_document(proposal: ActionProposal) -> Mapping[str, Any]:
    return {
        "action_id": proposal.action_id,
        "action": proposal.action,
        "resource": proposal.resource,
        "parameters_digest": proposal.parameters_digest,
        "metadata": dict(proposal.metadata),
    }


def _policy_document(evaluations: Tuple[PolicyEvaluation, ...]) -> Mapping[str, Any]:
    return {
        "evaluations": [
            {
                "policy_id": item.policy_id,
                "policy_version": item.policy_version,
                "layer": item.layer.value,
                "effect": item.effect.value,
                "rationale_code": item.rationale_code,
                "runtime_id": item.runtime_id,
                "native_verdict": item.native_verdict,
                "required_controls": list(item.required_controls),
                "evidence_artifact": item.evidence_artifact,
            }
            for item in evaluations
        ]
    }


class GovernedActionGateway:
    """Atomic in-process reference monitor for one protected connector."""

    def __init__(
        self,
        *,
        gateway_id: str,
        policy_runtime: PolicyRuntime,
        graph: GovernanceGraph,
        connector: ProtectedConnector,
        kernel_verifier: KernelVerifier,
        approval_verifier: ApprovalVerifier,
        receipt_key: Ed25519PrivateKey,
        receipt_verification_method: str,
        action_store: Optional[ActionStore] = None,
        before_connector: Optional[Callable[[ActionProposal], None]] = None,
    ) -> None:
        self.gateway_id = gateway_id
        self._policy_runtime = policy_runtime
        self._graph = graph
        self._connector = connector
        self._kernel_verifier = kernel_verifier
        self._approval_verifier = approval_verifier
        self._receipt_key = receipt_key
        self._receipt_method = receipt_verification_method
        self._store = action_store or InMemoryActionStore()
        self._before_connector = before_connector
        self._lock = RLock()

    def get(self, action_id: str) -> Optional[ActionRecord]:
        with self._lock:
            return self._store.get(action_id)

    def execute(self, proposal: ActionProposal, *, conflict_node: str) -> ActionRecord:
        proposal_digest = artifact_digest(_proposal_document(proposal))
        with self._lock:
            initial = ActionRecord(
                proposal.action_id,
                proposal_digest,
                ActionState.VALIDATING,
                1,
                proposal=_proposal_document(proposal),
            )
            existing = self._store.claim(initial)
            if existing is not None:
                if existing.proposal_digest != proposal_digest:
                    raise GCPError(
                        ErrorCode.ACTION_ID_CONFLICT,
                        "Action id was already bound to another proposal",
                        {"action_id": proposal.action_id},
                    )
                return existing
            record = initial

            try:
                kernel_controls = tuple(self._kernel_verifier(proposal))
                evaluations = tuple(self._policy_runtime.evaluate(proposal))
                policy_digest = artifact_digest(_policy_document(evaluations))
                resolution = resolve_carm(evaluations, self._graph, conflict_node)
                controls = tuple(
                    sorted(
                        set(kernel_controls).union(
                            control
                            for evaluation in evaluations
                            for control in evaluation.required_controls
                        )
                    )
                )
                if resolution.decision == RuntimeDecision.BLOCK:
                    return self._finish(
                        record,
                        ActionState.REJECTED,
                        resolution.decision,
                        controls,
                        resolution.reason_codes,
                        policy_digest,
                    )
                if (
                    resolution.decision == RuntimeDecision.APPROVAL_REQUIRED
                    and not self._approval_verifier(proposal)
                ):
                    return self._finish(
                        record,
                        ActionState.APPROVAL_REQUIRED,
                        resolution.decision,
                        controls,
                        resolution.reason_codes,
                        policy_digest,
                    )
                record = replace(
                    record,
                    state=ActionState.RESERVED,
                    decision=resolution.decision,
                    controls=controls,
                    reason_codes=resolution.reason_codes,
                    graph_digest=resolution.reach.graph_digest,
                    policy_snapshot_digest=policy_digest,
                )
                self._store.put(replace(record, state=ActionState.COMMITTING))
                if self._before_connector is not None:
                    self._before_connector(proposal)
                result = self._connector.commit(proposal.action_id, proposal)
                return self._apply_connector_result(record, result)
            except GCPError as error:
                return self._finish(
                    record,
                    ActionState.REJECTED,
                    RuntimeDecision.BLOCK,
                    (),
                    (error.code.value,),
                    None,
                )
            except Exception:
                return self._finish(
                    record,
                    ActionState.FAILED,
                    RuntimeDecision.BLOCK,
                    (),
                    ("GCP_GATEWAY_INTERNAL_ERROR",),
                    None,
                )

    def resume_approved(self, proposal: ActionProposal, *, conflict_node: str) -> ActionRecord:
        with self._lock:
            current = self._store.get(proposal.action_id)
            if current is None or current.state != ActionState.APPROVAL_REQUIRED:
                raise GCPError(ErrorCode.ACTION_STATE_INVALID, "Action is not awaiting approval")
            if not self._approval_verifier(proposal):
                return current
            # Remove only the waiting record; the immutable proposal binding is
            # checked before re-entry and the approval verifier must be atomic.
            self._store.delete_waiting(proposal.action_id, ActionState.APPROVAL_REQUIRED)
        return self.execute(proposal, conflict_node=conflict_node)

    def reconcile(self, action_id: str) -> ActionRecord:
        with self._lock:
            record = self._store.get(action_id)
            if record is None or record.state not in {
                ActionState.COMMITTING,
                ActionState.COMMIT_OUTCOME_UNKNOWN,
            }:
                raise GCPError(ErrorCode.ACTION_STATE_INVALID, "Action is not awaiting reconciliation")
            result = self._connector.reconcile(action_id)
            if result.outcome == ConnectorOutcome.NOT_COMMITTED and record.state == ActionState.COMMITTING:
                proposal = self._proposal_from_record(record)
                result = self._connector.commit(action_id, proposal)
            return self._apply_connector_result(record, result)

    def recover_pending(self) -> Tuple[ActionRecord, ...]:
        """Reconcile every durable commit intent after worker or process restart."""

        recovered = []
        for record in self._store.pending_commits():
            recovered.append(self.reconcile(record.action_id))
        return tuple(recovered)

    @staticmethod
    def _proposal_from_record(record: ActionRecord) -> ActionProposal:
        value = record.proposal
        if not isinstance(value, Mapping):
            raise GCPError(
                ErrorCode.ACTION_STATE_INVALID,
                "Commit intent has no recoverable proposal payload",
                {"action_id": record.action_id},
            )
        proposal = ActionProposal(
            action_id=value["action_id"],
            action=value["action"],
            resource=value["resource"],
            parameters_digest=value["parameters_digest"],
            metadata=value.get("metadata", {}),
        )
        if artifact_digest(_proposal_document(proposal)) != record.proposal_digest:
            raise GCPError(
                ErrorCode.ACTION_ID_CONFLICT,
                "Persisted commit payload does not match its proposal digest",
                {"action_id": record.action_id},
            )
        return proposal

    def _apply_connector_result(self, record: ActionRecord, result: ConnectorResult) -> ActionRecord:
        if result.outcome == ConnectorOutcome.COMMITTED:
            return self._finish(
                record,
                ActionState.COMMITTED,
                record.decision or RuntimeDecision.ALLOW,
                record.controls,
                record.reason_codes,
                record.policy_snapshot_digest,
                result,
            )
        if result.outcome == ConnectorOutcome.UNKNOWN:
            return self._finish(
                record,
                ActionState.COMMIT_OUTCOME_UNKNOWN,
                record.decision or RuntimeDecision.ALLOW,
                record.controls,
                ("GCP_COMMIT_OUTCOME_UNKNOWN",),
                record.policy_snapshot_digest,
                result,
            )
        return self._finish(
            record,
            ActionState.FAILED,
            RuntimeDecision.BLOCK,
            record.controls,
            ("GCP_CONNECTOR_NOT_COMMITTED",),
            record.policy_snapshot_digest,
            result,
        )

    def _finish(
        self,
        record: ActionRecord,
        state: ActionState,
        decision: RuntimeDecision,
        controls: Tuple[str, ...],
        reasons: Tuple[str, ...],
        policy_digest: Optional[str],
        result: Optional[ConnectorResult] = None,
    ) -> ActionRecord:
        unsigned = {
            "receipt_version": "0.1-experimental",
            "receipt_id": "urn:gcp:receipt:" + record.action_id,
            "gateway_id": self.gateway_id,
            "action_id": record.action_id,
            "proposal_digest": record.proposal_digest,
            "state": state.value,
            "decision": decision.value,
            "controls": list(controls),
            "reason_codes": list(reasons),
            "graph_digest": self._graph.digest,
            "policy_snapshot_digest": policy_digest,
            "result_reference": result.result_reference if result else None,
            "result_digest": result.result_digest if result else None,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        receipt = sign_artifact(unsigned, self._receipt_key, self._receipt_method)
        finished = replace(
            record,
            state=state,
            decision=decision,
            controls=controls,
            reason_codes=reasons,
            graph_digest=self._graph.digest,
            policy_snapshot_digest=policy_digest,
            result_reference=result.result_reference if result else None,
            result_digest=result.result_digest if result else None,
            receipt=receipt,
        )
        self._store.put(finished)
        return finished


class InMemorySupplierConnector:
    """Protected idempotent supplier connector used by the first product demo."""

    def __init__(self) -> None:
        self.suppliers: Dict[str, Mapping[str, Any]] = {}
        self.commit_calls = 0
        self.lose_next_response = False
        self.crash_after_next_commit = False

    def commit(self, action_id: str, proposal: ActionProposal) -> ConnectorResult:
        self.commit_calls += 1
        if action_id not in self.suppliers:
            self.suppliers[action_id] = {
                "supplier_id": proposal.resource,
                "parameters_digest": proposal.parameters_digest,
            }
        result = ConnectorResult(
            ConnectorOutcome.COMMITTED,
            "urn:gcp:supplier-result:" + action_id,
            artifact_digest(self.suppliers[action_id]),
        )
        if self.lose_next_response:
            self.lose_next_response = False
            return replace(result, outcome=ConnectorOutcome.UNKNOWN)
        if self.crash_after_next_commit:
            self.crash_after_next_commit = False
            raise SimulatedProcessCrash("connector committed before gateway process stopped")
        return result

    def reconcile(self, action_id: str) -> ConnectorResult:
        supplier = self.suppliers.get(action_id)
        if supplier is None:
            return ConnectorResult(ConnectorOutcome.NOT_COMMITTED)
        return ConnectorResult(
            ConnectorOutcome.COMMITTED,
            "urn:gcp:supplier-result:" + action_id,
            artifact_digest(supplier),
        )


class SimulatedProcessCrash(BaseException):
    """Fault-injection signal intentionally not caught by gateway Exception handling."""
