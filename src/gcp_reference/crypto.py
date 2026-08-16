"""Hashing and Ed25519 proof operations for GCP artifacts."""

import base64
import hashlib
from copy import deepcopy
from datetime import datetime, timezone
from typing import Dict, Mapping, Optional

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from .canonical import canonicalize, without_proof
from .errors import ErrorCode, GCPError


def _b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    try:
        return base64.b64decode(value + padding, altchars=b"-_", validate=True)
    except ValueError as exc:
        raise GCPError(ErrorCode.INVALID_SIGNATURE, "Invalid base64url proof value") from exc


def artifact_digest_bytes(artifact: Mapping[str, object]) -> bytes:
    return hashlib.sha256(canonicalize(without_proof(artifact))).digest()


def artifact_digest(artifact: Mapping[str, object]) -> str:
    return "sha256:" + artifact_digest_bytes(artifact).hex()


class KeyResolver:
    """Minimal in-memory verification-method resolver for the v0.1 library."""

    def __init__(self, keys: Optional[Mapping[str, Ed25519PublicKey]] = None) -> None:
        self._keys: Dict[str, Ed25519PublicKey] = dict(keys or {})

    def add(self, verification_method: str, key: Ed25519PublicKey) -> None:
        self._keys[verification_method] = key

    def resolve(self, verification_method: str) -> Ed25519PublicKey:
        try:
            return self._keys[verification_method]
        except KeyError as exc:
            raise GCPError(
                ErrorCode.UNKNOWN_VERIFICATION_METHOD,
                "Verification method is not trusted",
                {"verification_method": verification_method},
            ) from exc


def sign_artifact(
    artifact: Mapping[str, object],
    private_key: Ed25519PrivateKey,
    verification_method: str,
    *,
    created: Optional[str] = None,
    proof_purpose: str = "assertionMethod",
) -> dict:
    """Return a signed copy; the input object is never mutated."""

    if proof_purpose not in {"assertionMethod", "authentication"}:
        raise GCPError(ErrorCode.UNSUPPORTED_SEMANTICS, "Unsupported proof purpose")
    signed = deepcopy(dict(artifact))
    signed.pop("proof", None)
    signature = private_key.sign(artifact_digest_bytes(signed))
    signed["proof"] = {
        "type": "DataIntegrityProof",
        "cryptosuite": "eddsa-jcs-2022",
        "verification_method": verification_method,
        "created": created or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "proof_purpose": proof_purpose,
        "proof_value": _b64url_encode(signature),
    }
    return signed


def verify_artifact(artifact: Mapping[str, object], resolver: KeyResolver) -> None:
    proof = artifact.get("proof")
    if not isinstance(proof, dict):
        raise GCPError(ErrorCode.INVALID_SIGNATURE, "Artifact has no integrity proof")
    if proof.get("type") != "DataIntegrityProof" or proof.get("cryptosuite") != "eddsa-jcs-2022":
        raise GCPError(ErrorCode.UNSUPPORTED_SEMANTICS, "Unsupported integrity proof profile")
    method = proof.get("verification_method")
    value = proof.get("proof_value")
    if not isinstance(method, str) or not isinstance(value, str):
        raise GCPError(ErrorCode.INVALID_SIGNATURE, "Integrity proof is incomplete")
    key = resolver.resolve(method)
    try:
        key.verify(_b64url_decode(value), artifact_digest_bytes(artifact))
    except InvalidSignature as exc:
        raise GCPError(ErrorCode.INVALID_SIGNATURE, "Artifact signature is invalid") from exc
