import json
from copy import deepcopy
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from gcp_reference import KeyResolver, artifact_digest, sign_artifact


ROOT = Path(__file__).resolve().parents[1]
ISSUER_METHOD = "https://governance.example.com/keys/test-issuer"
DELEGATOR_METHOD = "https://governance.example.com/keys/test-delegator"


def load_example(name):
    return json.loads((ROOT / "examples" / "valid" / name).read_text())


@pytest.fixture
def key_material():
    issuer = Ed25519PrivateKey.generate()
    delegator = Ed25519PrivateKey.generate()
    resolver = KeyResolver(
        {
            ISSUER_METHOD: issuer.public_key(),
            DELEGATOR_METHOD: delegator.public_key(),
        }
    )
    return issuer, delegator, resolver


@pytest.fixture
def signed_transition(key_material):
    issuer, delegator, resolver = key_material
    root = load_example("root-capsule.json")
    root.pop("proof")
    root = sign_artifact(root, issuer, ISSUER_METHOD, created="2026-08-12T00:00:00Z")

    child = load_example("child-capsule.json")
    child.pop("proof")
    child["parent"]["digest"] = artifact_digest(root)
    child = sign_artifact(child, issuer, ISSUER_METHOD, created="2026-08-12T00:05:00Z")

    proof = load_example("delegation-proof.json")
    proof.pop("proof")
    proof["parent_capsule"]["digest"] = artifact_digest(root)
    proof["child_capsule"]["digest"] = artifact_digest(child)
    proof = sign_artifact(
        proof,
        delegator,
        DELEGATOR_METHOD,
        created="2026-08-12T00:05:00Z",
        proof_purpose="authentication",
    )
    return deepcopy(root), deepcopy(child), deepcopy(proof), resolver
