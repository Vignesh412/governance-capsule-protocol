from copy import deepcopy

import pytest

from gcp_reference import ErrorCode, GCPError, artifact_digest, verify_artifact
from gcp_reference.canonical import canonicalize


def test_canonicalization_is_independent_of_object_member_order():
    first = {"z": 1, "a": {"two": 2, "one": 1}}
    second = {"a": {"one": 1, "two": 2}, "z": 1}
    assert canonicalize(first) == canonicalize(second)


def test_digest_excludes_embedded_proof(signed_transition):
    root, _, _, _ = signed_transition
    changed_proof = deepcopy(root)
    changed_proof["proof"]["created"] = "2030-01-01T00:00:00Z"
    assert artifact_digest(root) == artifact_digest(changed_proof)


def test_valid_signature_verifies(signed_transition):
    root, child, proof, resolver = signed_transition
    verify_artifact(root, resolver)
    verify_artifact(child, resolver)
    verify_artifact(proof, resolver)


def test_protected_mutation_invalidates_signature(signed_transition):
    root, _, _, resolver = signed_transition
    root["task"]["purpose"] = "Tampered purpose"
    with pytest.raises(GCPError) as caught:
        verify_artifact(root, resolver)
    assert caught.value.code == ErrorCode.INVALID_SIGNATURE


def test_floating_point_content_fails_closed(signed_transition):
    root, _, _, _ = signed_transition
    root["unexpected"] = 0.1
    with pytest.raises(GCPError) as caught:
        artifact_digest(root)
    assert caught.value.code == ErrorCode.UNSUPPORTED_SEMANTICS
