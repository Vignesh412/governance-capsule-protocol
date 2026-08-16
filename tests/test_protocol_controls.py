from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timezone
from threading import Barrier

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from gcp_reference import (
    ApprovalRegistry,
    ErrorCode,
    GCPError,
    KeyResolver,
    amendment_change_digest,
    artifact_digest,
    sign_artifact,
    status_from_signed_revocation,
    validate_amendment,
    validate_structure,
)


NOW = datetime(2026, 8, 12, 1, 30, tzinfo=timezone.utc)
ISSUER = "https://governance.example.com/issuers/procurement"
ISSUER_METHOD = "https://governance.example.com/keys/procurement"
APPROVER = "https://identity.example.com/users/risk-officer"
APPROVER_METHOD = "https://identity.example.com/keys/risk-officer"


def assert_code(code, callable_):
    with pytest.raises(GCPError) as caught:
        callable_()
    assert caught.value.code == code


@pytest.fixture
def control_material(signed_transition):
    root, _, _, _ = signed_transition
    issuer_key = Ed25519PrivateKey.generate()
    approver_key = Ed25519PrivateKey.generate()
    resolver = KeyResolver()
    resolver.add(ISSUER_METHOD, issuer_key.public_key())
    resolver.add(APPROVER_METHOD, approver_key.public_key())
    return root, issuer_key, approver_key, resolver


def signed_revocation(capsule, key, **overrides):
    record = {
        "gcp_version": "0.1",
        "revocation_id": "urn:gcp:revocation:test",
        "issuer": ISSUER,
        "target": {
            "type": "capsule_revision",
            "id": capsule["capsule_id"],
            "digest": artifact_digest(capsule),
        },
        "cascade": True,
        "effective_at": "2026-08-12T01:00:00Z",
        "reason_code": "AUTHORITY_WITHDRAWN",
        "sequence": 1,
    }
    record.update(overrides)
    return sign_artifact(record, key, ISSUER_METHOD, created="2026-08-12T01:00:00Z")


def signed_approval(capsule, key, *, change_digest=None, max_uses=1):
    scope = {
        "type": "amendment" if change_digest else "action",
        "action": "capsule.amend" if change_digest else "vendor.approve",
        "resource": capsule["capsule_id"] if change_digest else "https://api.example.com/vendors/acme",
    }
    if change_digest:
        scope["change_digest"] = change_digest
    approval = {
        "gcp_version": "0.1",
        "approval_id": "urn:gcp:approval:test",
        "approver": APPROVER,
        "capsule_digest": artifact_digest(capsule),
        "scope": scope,
        "issued_at": "2026-08-12T01:00:00Z",
        "expires_at": "2026-08-12T02:00:00Z",
        "max_uses": max_uses,
        "evidence": [
            {
                "uri": "https://audit.example.com/approvals/test",
                "digest": "sha256:" + "e" * 64,
            }
        ],
    }
    return sign_artifact(approval, key, APPROVER_METHOD, created="2026-08-12T01:00:00Z")


def test_schema_api_accepts_valid_and_rejects_unknown_field(control_material):
    capsule, _, _, _ = control_material
    validate_structure(capsule, "capsule.schema.json")
    invalid = deepcopy(capsule)
    invalid["surprise"] = True
    assert_code(
        ErrorCode.SCHEMA_INVALID,
        lambda: validate_structure(invalid, "capsule.schema.json"),
    )


def test_signed_revocation_is_verified_and_adapted(control_material):
    capsule, issuer_key, _, resolver = control_material
    record = signed_revocation(capsule, issuer_key)
    status = status_from_signed_revocation(
        record,
        capsule,
        resolver=resolver,
        authorized_issuers={ISSUER: [ISSUER_METHOD]},
        checked_at=NOW,
    )
    assert status.revoked is True
    assert status.cascade is True
    assert status.status_digest == artifact_digest(record)


def test_future_revocation_is_not_effective_yet(control_material):
    capsule, issuer_key, _, resolver = control_material
    record = signed_revocation(capsule, issuer_key, effective_at="2026-08-12T02:00:00Z")
    status = status_from_signed_revocation(
        record,
        capsule,
        resolver=resolver,
        authorized_issuers={ISSUER: [ISSUER_METHOD]},
        checked_at=NOW,
    )
    assert status.revoked is False


def test_revocation_requires_issuer_key_binding(control_material):
    capsule, issuer_key, _, resolver = control_material
    record = signed_revocation(capsule, issuer_key)
    assert_code(
        ErrorCode.UNAUTHORIZED_REVOCATION,
        lambda: status_from_signed_revocation(
            record,
            capsule,
            resolver=resolver,
            authorized_issuers={ISSUER: [APPROVER_METHOD]},
            checked_at=NOW,
        ),
    )


def test_revocation_target_must_match_exact_revision(control_material):
    capsule, issuer_key, _, resolver = control_material
    wrong_target = {"type": "capsule_revision", "id": capsule["capsule_id"], "digest": "sha256:" + "0" * 64}
    record = signed_revocation(capsule, issuer_key, target=wrong_target)
    assert_code(
        ErrorCode.REVOCATION_TARGET_MISMATCH,
        lambda: status_from_signed_revocation(
            record,
            capsule,
            resolver=resolver,
            authorized_issuers={ISSUER: [ISSUER_METHOD]},
            checked_at=NOW,
        ),
    )


def test_scoped_approval_is_consumed_once(control_material):
    capsule, _, approver_key, resolver = control_material
    approval = signed_approval(capsule, approver_key)
    registry = ApprovalRegistry()
    args = dict(
        action="vendor.approve",
        resource="https://api.example.com/vendors/acme",
        now=NOW,
        resolver=resolver,
        authorized_approvers={APPROVER: [APPROVER_METHOD]},
    )
    assert registry.consume(approval, capsule, **args) == 1
    assert_code(ErrorCode.REPLAY_DETECTED, lambda: registry.consume(approval, capsule, **args))


def test_approval_scope_is_exact(control_material):
    capsule, _, approver_key, resolver = control_material
    approval = signed_approval(capsule, approver_key)
    registry = ApprovalRegistry()
    assert_code(
        ErrorCode.APPROVAL_SCOPE_MISMATCH,
        lambda: registry.consume(
            approval,
            capsule,
            action="vendor.delete",
            resource="https://api.example.com/vendors/acme",
            now=NOW,
            resolver=resolver,
            authorized_approvers={APPROVER: [APPROVER_METHOD]},
        ),
    )
    assert registry.count(approval["approval_id"]) == 0


def test_concurrent_single_use_approval_has_one_winner(control_material):
    capsule, _, approver_key, resolver = control_material
    approval = signed_approval(capsule, approver_key)
    registry = ApprovalRegistry()
    barrier = Barrier(2)

    def consume(_):
        barrier.wait()
        try:
            registry.consume(
                approval,
                capsule,
                action="vendor.approve",
                resource="https://api.example.com/vendors/acme",
                now=NOW,
                resolver=resolver,
                authorized_approvers={APPROVER: [APPROVER_METHOD]},
            )
            return "committed"
        except GCPError as exc:
            return exc.code

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(consume, range(2)))
    assert results.count("committed") == 1
    assert results.count(ErrorCode.REPLAY_DETECTED) == 1


def test_signed_amendment_binds_capsules_change_scope_and_approval(control_material):
    previous, issuer_key, approver_key, resolver = control_material
    result = deepcopy(previous)
    result.pop("proof")
    result["revision"] += 1
    result["sequence"] += 1
    result["validity"]["expires_at"] = "2026-08-12T11:00:00Z"
    result = sign_artifact(result, issuer_key, ISSUER_METHOD, created="2026-08-12T01:05:00Z")
    amendment = {
        "gcp_version": "0.1",
        "amendment_id": "urn:gcp:amendment:test",
        "previous_capsule_digest": artifact_digest(previous),
        "result_capsule_digest": artifact_digest(result),
        "authority": ISSUER,
        "approval_id": "urn:gcp:approval:test",
        "changes": [{
            "operation": "replace",
            "path": "/validity/expires_at",
            "old_digest": "sha256:" + "1" * 64,
            "new_digest": "sha256:" + "2" * 64,
        }],
        "rationale": "Risk officer approved a bounded validity change.",
        "issued_at": "2026-08-12T01:05:00Z",
        "expires_at": "2026-08-12T02:00:00Z",
    }
    amendment = sign_artifact(amendment, issuer_key, ISSUER_METHOD, created="2026-08-12T01:05:00Z")
    approval = signed_approval(previous, approver_key, change_digest=amendment_change_digest(amendment))
    assert validate_amendment(
        amendment,
        previous,
        result,
        approval,
        now=NOW,
        resolver=resolver,
        authorized_authorities={ISSUER: [ISSUER_METHOD]},
        authorized_approvers={APPROVER: [APPROVER_METHOD]},
        approval_registry=ApprovalRegistry(),
    ) == 1


def test_amendment_rejects_nonconsecutive_result(control_material):
    previous, issuer_key, approver_key, resolver = control_material
    result = deepcopy(previous)
    result.pop("proof")
    result["revision"] += 2
    result["sequence"] += 1
    result = sign_artifact(result, issuer_key, ISSUER_METHOD)
    amendment = {
        "gcp_version": "0.1", "amendment_id": "urn:gcp:amendment:test",
        "previous_capsule_digest": artifact_digest(previous), "result_capsule_digest": artifact_digest(result),
        "authority": ISSUER, "approval_id": "urn:gcp:approval:test",
        "changes": [{"operation": "replace", "path": "/revision", "old_digest": "sha256:" + "1" * 64, "new_digest": "sha256:" + "2" * 64}],
        "rationale": "Test invalid revision jump.", "issued_at": "2026-08-12T01:05:00Z",
    }
    amendment = sign_artifact(amendment, issuer_key, ISSUER_METHOD)
    approval = signed_approval(previous, approver_key, change_digest=amendment_change_digest(amendment))
    assert_code(
        ErrorCode.AMENDMENT_MISMATCH,
        lambda: validate_amendment(
            amendment, previous, result, approval, now=NOW, resolver=resolver,
            authorized_authorities={ISSUER: [ISSUER_METHOD]},
            authorized_approvers={APPROVER: [APPROVER_METHOD]},
            approval_registry=ApprovalRegistry(),
        ),
    )
