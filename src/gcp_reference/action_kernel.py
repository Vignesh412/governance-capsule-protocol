"""Concrete signed-capsule verifier for governed action boundaries."""

from datetime import datetime
from threading import RLock
from dataclasses import dataclass
from typing import Any, Callable, Dict, Mapping, Optional, Sequence, Tuple

from .crypto import KeyResolver, artifact_digest, verify_artifact
from .errors import ErrorCode, GCPError
from .policy import ActionProposal
from .replay import UseRegistry
from .revocation import RevocationEvaluator, StatusProvider
from .schema import validate_structure
from .semantics import validate_audience
from .semantics import validate_delegation, validate_delegation_proof


ConstraintVerifier = Callable[[Mapping[str, Any], ActionProposal], bool]
ObligationVerifier = Callable[[Mapping[str, Any], ActionProposal], bool]


@dataclass(frozen=True)
class DelegationTransition:
    parent: Mapping[str, Any]
    child: Mapping[str, Any]
    proof: Mapping[str, Any]


def _time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _resource_matches(grant: Mapping[str, Any], resource: str) -> bool:
    rule = grant["resource"]
    if rule["match"] == "exact":
        return resource == rule["uri"]
    if rule["match"] == "prefix":
        return resource.startswith(rule["uri"])
    raise GCPError(ErrorCode.UNSUPPORTED_SEMANTICS, "Unknown resource match rule")


class CapsuleActionVerifier:
    """Verify one capsule revision before a proposed action reaches policy."""

    def __init__(
        self,
        capsule: Mapping[str, Any],
        *,
        presenter: str,
        now: Callable[[], datetime],
        resolver: KeyResolver,
        authorized_issuers: Mapping[str, Sequence[str]],
        ancestors: Sequence[Mapping[str, Any]] = (),
        revocation_evaluator: Optional[RevocationEvaluator] = None,
        status_provider: Optional[StatusProvider] = None,
        allow_offline: bool = False,
        constraint_verifiers: Optional[Mapping[str, ConstraintVerifier]] = None,
        obligation_verifier: Optional[ObligationVerifier] = None,
        use_registry: Optional[UseRegistry] = None,
    ) -> None:
        self.capsule = capsule
        self.presenter = presenter
        self._now = now
        self._resolver = resolver
        self._authorized_issuers = authorized_issuers
        self._ancestors = tuple(ancestors)
        self._revocations = revocation_evaluator or RevocationEvaluator()
        self._status_provider = status_provider
        self._allow_offline = allow_offline
        self._constraint_verifiers = dict(constraint_verifiers or {})
        self._obligation_verifier = obligation_verifier or (lambda obligation, proposal: False)
        self._uses = use_registry or UseRegistry()
        self._action_bindings: Dict[str, str] = {}
        self._lock = RLock()

    def __call__(self, proposal: ActionProposal) -> Tuple[str, ...]:
        validate_structure(self.capsule, "capsule.schema.json")
        verify_artifact(self.capsule, self._resolver)
        method = self.capsule["proof"]["verification_method"]
        issuer = self.capsule["issuer"]
        if method not in self._authorized_issuers.get(issuer, ()):
            raise GCPError(
                ErrorCode.UNAUTHORIZED_CAPSULE_ISSUER,
                "Capsule issuer is not authorized to use this verification method",
                {"issuer": issuer, "verification_method": method},
            )
        validate_audience(self.capsule, self.presenter)
        current = self._now()
        if current < _time(self.capsule["validity"]["not_before"]):
            raise GCPError(ErrorCode.CAPSULE_NOT_YET_VALID, "Capsule is not yet valid")
        if current >= _time(self.capsule["validity"]["expires_at"]):
            raise GCPError(ErrorCode.CAPSULE_EXPIRED, "Capsule has expired")

        self._revocations.evaluate(
            self.capsule,
            ancestors=self._ancestors,
            now=current,
            provider=self._status_provider,
            allow_offline=self._allow_offline,
        )

        matching = [
            grant for grant in self.capsule["authority"]
            if grant["action"] == proposal.action and _resource_matches(grant, proposal.resource)
        ]
        authorized = False
        for grant in matching:
            if all(self._constraint_satisfied(item, proposal) for item in grant.get("constraints", ())):
                authorized = True
                break
        if not authorized:
            raise GCPError(
                ErrorCode.ACTION_NOT_AUTHORIZED,
                "Capsule authority does not permit this action and resource",
                {"action": proposal.action, "resource": proposal.resource},
            )

        missing = [
            obligation["obligation_id"]
            for obligation in self.capsule["obligations"]
            if obligation["mandatory"]
            and obligation["satisfaction_point"] == "before_action"
            and not self._obligation_verifier(obligation, proposal)
        ]
        if missing:
            raise GCPError(
                ErrorCode.OBLIGATION_UNSATISFIED,
                "Mandatory pre-action obligations are not satisfied",
                {"obligation_ids": missing},
            )

        digest = artifact_digest(self.capsule)
        with self._lock:
            bound = self._action_bindings.get(proposal.action_id)
            if bound is not None and bound != digest:
                raise GCPError(ErrorCode.ACTION_ID_CONFLICT, "Action id is bound to another capsule")
            if bound is None:
                replay = self.capsule["validity"]["replay"]
                max_uses = 1 if replay["mode"] == "single-use" else replay.get("max_uses", 1)
                self._uses.commit(digest, max_uses=max_uses)
                self._action_bindings[proposal.action_id] = digest
        return (
            "GCP_CAPSULE_SCHEMA_VERIFIED",
            "GCP_CAPSULE_SIGNATURE_VERIFIED",
            "GCP_CAPSULE_AUTHORITY_VERIFIED",
            "GCP_REVOCATION_FRESHNESS_VERIFIED",
            "GCP_OBLIGATIONS_VERIFIED",
        )

    def _constraint_satisfied(
        self, constraint: Mapping[str, Any], proposal: ActionProposal
    ) -> bool:
        verifier = self._constraint_verifiers.get(constraint["name"])
        if verifier is None:
            if constraint.get("critical", True):
                return False
            return True
        return bool(verifier(constraint, proposal))


class DelegatedCapsuleActionVerifier:
    """Verify an entire ordinary delegation chain before authorizing its leaf."""

    def __init__(
        self,
        transitions: Sequence[DelegationTransition],
        *,
        presenter: str,
        now: Callable[[], datetime],
        resolver: KeyResolver,
        authorized_issuers: Mapping[str, Sequence[str]],
        authorized_delegators: Mapping[str, Sequence[str]],
        revocation_evaluator: Optional[RevocationEvaluator] = None,
        status_provider: Optional[StatusProvider] = None,
        allow_offline: bool = False,
        constraint_verifiers: Optional[Mapping[str, ConstraintVerifier]] = None,
        obligation_verifier: Optional[ObligationVerifier] = None,
        use_registry: Optional[UseRegistry] = None,
    ) -> None:
        if not transitions:
            raise GCPError(ErrorCode.PARENT_MISMATCH, "Delegated action requires a lineage transition")
        self._transitions = tuple(transitions)
        self._resolver = resolver
        self._authorized_issuers = authorized_issuers
        self._authorized_delegators = authorized_delegators
        self._validate_chain_shape()
        ancestors = [self._transitions[0].parent]
        ancestors.extend(item.child for item in self._transitions[:-1])
        self._leaf = CapsuleActionVerifier(
            self._transitions[-1].child,
            presenter=presenter,
            now=now,
            resolver=resolver,
            authorized_issuers=authorized_issuers,
            ancestors=ancestors,
            revocation_evaluator=revocation_evaluator,
            status_provider=status_provider,
            allow_offline=allow_offline,
            constraint_verifiers=constraint_verifiers,
            obligation_verifier=obligation_verifier,
            use_registry=use_registry,
        )

    def __call__(self, proposal: ActionProposal) -> Tuple[str, ...]:
        ancestor_ids = []
        for transition in self._transitions:
            self._verify_capsule(transition.parent)
            self._verify_capsule(transition.child)
            validate_delegation(
                transition.parent,
                transition.child,
                verified_ancestor_ids=ancestor_ids,
            )
            validate_structure(transition.proof, "delegation-proof.schema.json")
            validate_delegation_proof(
                transition.proof,
                transition.parent,
                transition.child,
                self._resolver,
            )
            delegator = transition.proof["delegator"]
            method = transition.proof["proof"]["verification_method"]
            if method not in self._authorized_delegators.get(delegator, ()):
                raise GCPError(
                    ErrorCode.INVALID_DELEGATION_PROOF,
                    "Delegator is not authorized to use this verification method",
                    {"delegator": delegator, "verification_method": method},
                )
            ancestor_ids.append(transition.parent["capsule_id"])
        return tuple(self._leaf(proposal)) + ("GCP_DELEGATION_LINEAGE_VERIFIED",)

    def _validate_chain_shape(self) -> None:
        for previous, current in zip(self._transitions, self._transitions[1:]):
            if artifact_digest(previous.child) != artifact_digest(current.parent):
                raise GCPError(
                    ErrorCode.PARENT_MISMATCH,
                    "Delegation transitions do not form one continuous chain",
                )

    def _verify_capsule(self, capsule: Mapping[str, Any]) -> None:
        validate_structure(capsule, "capsule.schema.json")
        verify_artifact(capsule, self._resolver)
        issuer = capsule["issuer"]
        method = capsule["proof"]["verification_method"]
        if method not in self._authorized_issuers.get(issuer, ()):
            raise GCPError(
                ErrorCode.UNAUTHORIZED_CAPSULE_ISSUER,
                "Capsule issuer is not authorized to use this verification method",
                {"issuer": issuer, "verification_method": method},
            )
