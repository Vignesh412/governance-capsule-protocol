from copy import deepcopy

import pytest

from gcp_reference import (
    ErrorCode,
    GCPError,
    artifact_digest,
    validate_delegation,
    validate_delegation_proof,
)


def assert_error(code, parent, child):
    with pytest.raises(GCPError) as caught:
        validate_delegation(parent, child)
    assert caught.value.code == code


def test_valid_narrowing_and_proof_succeed(signed_transition):
    parent, child, proof, resolver = signed_transition
    validate_delegation(parent, child)
    validate_delegation_proof(proof, parent, child, resolver)


def test_action_expansion_fails(signed_transition):
    parent, child, _, _ = signed_transition
    child["authority"][0]["action"] = "vendor.delete"
    assert_error(ErrorCode.AUTHORITY_EXPANSION, parent, child)


def test_resource_expansion_fails(signed_transition):
    parent, child, _, _ = signed_transition
    child["authority"][0]["resource"] = {
        "match": "prefix",
        "uri": "https://api.example.com/vendors/",
    }
    assert_error(ErrorCode.AUTHORITY_EXPANSION, parent, child)


def test_constraint_removal_fails(signed_transition):
    parent, child, _, _ = signed_transition
    child["authority"][0]["constraints"] = []
    assert_error(ErrorCode.AUTHORITY_EXPANSION, parent, child)


def test_constraint_relaxation_fails(signed_transition):
    parent, child, _, _ = signed_transition
    child["authority"][0]["constraints"][0]["value"] = ["EU", "US", "APAC"]
    assert_error(ErrorCode.AUTHORITY_EXPANSION, parent, child)


def test_mandatory_obligation_removal_fails(signed_transition):
    parent, child, _, _ = signed_transition
    child["obligations"] = child["obligations"][1:]
    assert_error(ErrorCode.OBLIGATION_REMOVED, parent, child)


def test_mandatory_obligation_mutation_fails(signed_transition):
    parent, child, _, _ = signed_transition
    child["obligations"][0]["parameters"]["approver_role"] = "anyone"
    assert_error(ErrorCode.OBLIGATION_MODIFIED, parent, child)


def test_additional_obligation_succeeds(signed_transition):
    parent, child, _, _ = signed_transition
    validate_delegation(parent, child)


def test_parent_digest_mismatch_fails(signed_transition):
    parent, child, _, _ = signed_transition
    parent["task"]["purpose"] = "Mutated after derivation"
    assert_error(ErrorCode.PARENT_MISMATCH, parent, child)


def test_child_budget_over_parent_fails(signed_transition):
    parent, child, _, _ = signed_transition
    child["budgets"][0]["quantity"] = "11.00"
    assert_error(ErrorCode.BUDGET_OVERALLOCATED, parent, child)


def test_temporal_expansion_fails(signed_transition):
    parent, child, _, _ = signed_transition
    child["validity"]["expires_at"] = "2026-08-14T00:00:00Z"
    assert_error(ErrorCode.TEMPORAL_EXPANSION, parent, child)


def test_delegation_depth_reset_fails(signed_transition):
    parent, child, _, _ = signed_transition
    child["delegation_depth"] = parent["delegation_depth"]
    assert_error(ErrorCode.DELEGATION_DEPTH_EXCEEDED, parent, child)


def test_cycle_fails(signed_transition):
    parent, child, _, _ = signed_transition
    child["capsule_id"] = parent["capsule_id"]
    assert_error(ErrorCode.LINEAGE_CYCLE, parent, child)


def test_child_mutation_breaks_delegation_proof(signed_transition):
    parent, child, proof, resolver = signed_transition
    child["task"]["purpose"] = "Mutated after proof issuance"
    with pytest.raises(GCPError) as caught:
        validate_delegation_proof(proof, parent, child, resolver)
    assert caught.value.code == ErrorCode.INVALID_DELEGATION_PROOF


def test_proof_signature_tampering_fails(signed_transition):
    parent, child, proof, resolver = signed_transition
    proof["issued_at"] = "2026-08-12T00:06:00Z"
    with pytest.raises(GCPError) as caught:
        validate_delegation_proof(proof, parent, child, resolver)
    assert caught.value.code == ErrorCode.INVALID_DELEGATION_PROOF


def test_parent_reference_uses_proof_excluded_digest(signed_transition):
    parent, child, _, _ = signed_transition
    parent["proof"]["created"] = "2026-08-12T00:00:01Z"
    assert child["parent"]["digest"] == artifact_digest(parent)
