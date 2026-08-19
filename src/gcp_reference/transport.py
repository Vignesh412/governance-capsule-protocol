"""Signed cross-framework transport profile for governed delegation."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Mapping, Sequence, Tuple

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from .action_kernel import DelegationTransition
from .crypto import KeyResolver, artifact_digest, sign_artifact, verify_artifact
from .errors import ErrorCode, GCPError
from .policy import ActionProposal
from .replay import UseRegistry

TRANSPORT_PROFILE = "gcp-cross-framework-0.1"


@dataclass(frozen=True)
class FrameworkIdentity:
    framework: str
    runtime_id: str


@dataclass(frozen=True)
class VerifiedTransport:
    envelope: Mapping[str, Any]
    proposal: ActionProposal
    transitions: Tuple[DelegationTransition, ...]
    source: FrameworkIdentity
    destination: FrameworkIdentity
    digest: str


def _proposal_document(proposal: ActionProposal) -> Mapping[str, Any]:
    return {
        "action_id": proposal.action_id, "action": proposal.action,
        "resource": proposal.resource, "parameters_digest": proposal.parameters_digest,
        "metadata": dict(proposal.metadata),
    }


def build_transport_envelope(
    *, transport_id: str, source: FrameworkIdentity, destination: FrameworkIdentity,
    proposal: ActionProposal, transitions: Sequence[DelegationTransition],
    created_at: str, expires_at: str, nonce: str,
    signing_key: Ed25519PrivateKey, verification_method: str,
) -> Mapping[str, Any]:
    if not transitions:
        raise GCPError(ErrorCode.TRANSPORT_INVALID, "Transport requires a delegation lineage")
    return sign_artifact({
        "gcp_version": "0.1", "transport_profile": TRANSPORT_PROFILE,
        "transport_id": transport_id,
        "source": {"framework": source.framework, "runtime_id": source.runtime_id},
        "destination": {"framework": destination.framework, "runtime_id": destination.runtime_id},
        "proposal": _proposal_document(proposal),
        "lineage": [{"parent": x.parent, "child": x.child, "delegation_proof": x.proof} for x in transitions],
        "created_at": created_at, "expires_at": expires_at, "nonce": nonce,
    }, signing_key, verification_method, created=created_at, proof_purpose="authentication")


def _parse_time(value: Any, field: str) -> datetime:
    if not isinstance(value, str):
        raise GCPError(ErrorCode.TRANSPORT_INVALID, f"Transport {field} must be a timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise GCPError(ErrorCode.TRANSPORT_INVALID, f"Transport {field} is invalid") from exc
    if parsed.tzinfo is None:
        raise GCPError(ErrorCode.TRANSPORT_INVALID, f"Transport {field} requires a timezone")
    return parsed


def _require_keys(value: Mapping[str, Any], keys, label: str) -> None:
    missing, unknown = set(keys).difference(value), set(value).difference(keys)
    if missing or unknown:
        raise GCPError(ErrorCode.TRANSPORT_INVALID, f"{label} has invalid fields",
                       {"missing": sorted(missing), "unknown": sorted(unknown)})


def verify_transport_envelope(
    envelope: Mapping[str, Any], *, resolver: KeyResolver,
    authorized_sources: Mapping[str, Sequence[str]],
    expected_destination: FrameworkIdentity, now: datetime,
    replay_registry: UseRegistry, expected_source_framework: str = None,
    maximum_lifetime: timedelta = timedelta(minutes=10),
) -> VerifiedTransport:
    if not isinstance(envelope, Mapping):
        raise GCPError(ErrorCode.TRANSPORT_INVALID, "Transport envelope must be an object")
    keys = {"gcp_version", "transport_profile", "transport_id", "source", "destination",
            "proposal", "lineage", "created_at", "expires_at", "nonce", "proof"}
    _require_keys(envelope, keys, "Transport envelope")
    if envelope["gcp_version"] != "0.1" or envelope["transport_profile"] != TRANSPORT_PROFILE:
        raise GCPError(ErrorCode.TRANSPORT_INVALID, "Unsupported cross-framework transport profile")
    for field in ("transport_id", "nonce"):
        if not isinstance(envelope[field], str) or not envelope[field]:
            raise GCPError(ErrorCode.TRANSPORT_INVALID, f"Transport {field} must be non-empty")
    source_value, destination_value = envelope["source"], envelope["destination"]
    if not isinstance(source_value, Mapping) or not isinstance(destination_value, Mapping):
        raise GCPError(ErrorCode.TRANSPORT_INVALID, "Framework identities must be objects")
    for value, label in ((source_value, "Source"), (destination_value, "Destination")):
        _require_keys(value, {"framework", "runtime_id"}, label)
    source = FrameworkIdentity(source_value["framework"], source_value["runtime_id"])
    destination = FrameworkIdentity(destination_value["framework"], destination_value["runtime_id"])
    if expected_source_framework is not None and source.framework != expected_source_framework:
        raise GCPError(ErrorCode.TRANSPORT_SOURCE_UNTRUSTED,
                       "Transport source framework does not match the adapter profile")
    if destination != expected_destination:
        raise GCPError(ErrorCode.TRANSPORT_DESTINATION_MISMATCH,
                       "Transport was addressed to another framework boundary")
    proof = envelope["proof"]
    if not isinstance(proof, Mapping):
        raise GCPError(ErrorCode.TRANSPORT_INVALID, "Transport proof is missing")
    method = proof.get("verification_method")
    if method not in authorized_sources.get(source.runtime_id, ()):
        raise GCPError(ErrorCode.TRANSPORT_SOURCE_UNTRUSTED,
                       "Source runtime is not authorized to sign transports")
    verify_artifact(envelope, resolver)
    created, expires = _parse_time(envelope["created_at"], "created_at"), _parse_time(envelope["expires_at"], "expires_at")
    if created > now or expires <= now or expires <= created or expires - created > maximum_lifetime:
        raise GCPError(ErrorCode.TRANSPORT_EXPIRED, "Transport is outside its valid lifetime")
    proposal_value = envelope["proposal"]
    if not isinstance(proposal_value, Mapping):
        raise GCPError(ErrorCode.TRANSPORT_INVALID, "Transport proposal must be an object")
    _require_keys(proposal_value, {"action_id", "action", "resource", "parameters_digest", "metadata"}, "Transport proposal")
    proposal = ActionProposal(proposal_value["action_id"], proposal_value["action"],
                              proposal_value["resource"], proposal_value["parameters_digest"],
                              proposal_value["metadata"])
    lineage = envelope["lineage"]
    if not isinstance(lineage, list) or not lineage:
        raise GCPError(ErrorCode.TRANSPORT_INVALID, "Transport lineage must be non-empty")
    transitions = []
    for item in lineage:
        if not isinstance(item, Mapping):
            raise GCPError(ErrorCode.TRANSPORT_INVALID, "Lineage transition must be an object")
        _require_keys(item, {"parent", "child", "delegation_proof"}, "Lineage transition")
        transitions.append(DelegationTransition(item["parent"], item["child"], item["delegation_proof"]))
    replay_registry.commit(envelope["nonce"], max_uses=1)
    return VerifiedTransport(envelope, proposal, tuple(transitions), source, destination, artifact_digest(envelope))


def assert_proposal_matches_transport(proposal: ActionProposal, verified: VerifiedTransport) -> None:
    if _proposal_document(proposal) != _proposal_document(verified.proposal):
        raise GCPError(ErrorCode.TRANSPORT_PROPOSAL_MISMATCH,
                       "Receiving action does not match the transported proposal")
