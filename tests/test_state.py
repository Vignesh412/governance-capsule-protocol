from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from threading import Barrier

import pytest

from gcp_reference import (
    AllocationLedger,
    ErrorCode,
    GCPError,
    RevocationEvaluator,
    StatusRecord,
    UseRegistry,
    artifact_digest,
    validate_audience,
)


NOW = datetime(2026, 8, 12, 1, 0, tzinfo=timezone.utc)


def budget(quantity, dimension="cost", unit="USD"):
    return [{"dimension": dimension, "quantity": quantity, "unit": unit}]


def assert_code(code, callable_):
    with pytest.raises(GCPError) as caught:
        callable_()
    assert caught.value.code == code


def test_conserved_batch_commits_atomically(signed_transition):
    parent, _, _, _ = signed_transition
    ledger = AllocationLedger()
    parent_digest = ledger.register_parent(parent)
    ledger.allocate_batch(
        parent_digest,
        {"child-a": budget("4.00"), "child-b": budget("6.00")},
    )
    assert set(ledger.snapshot(parent_digest)["allocations"]) == {"child-a", "child-b"}


def test_overallocated_batch_has_no_partial_commit(signed_transition):
    parent, _, _, _ = signed_transition
    ledger = AllocationLedger()
    parent_digest = ledger.register_parent(parent)
    assert_code(
        ErrorCode.BUDGET_OVERALLOCATED,
        lambda: ledger.allocate_batch(
            parent_digest,
            {"child-a": budget("6.00"), "child-b": budget("6.00")},
        ),
    )
    assert ledger.snapshot(parent_digest)["allocations"] == {}


def test_concurrent_allocation_serializes(signed_transition):
    parent, _, _, _ = signed_transition
    ledger = AllocationLedger()
    parent_digest = ledger.register_parent(parent)
    barrier = Barrier(2)

    def allocate(child_id):
        barrier.wait()
        try:
            ledger.allocate_batch(parent_digest, {child_id: budget("6.00")})
            return "committed"
        except GCPError as exc:
            return exc.code

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(allocate, ("child-a", "child-b")))
    assert results.count("committed") == 1
    assert results.count(ErrorCode.BUDGET_OVERALLOCATED) == 1


def test_allocation_is_not_implicitly_reclaimed(signed_transition):
    parent, _, _, _ = signed_transition
    ledger = AllocationLedger()
    parent_digest = ledger.register_parent(parent)
    ledger.allocate_batch(parent_digest, {"finished-child": budget("10.00")})
    assert_code(
        ErrorCode.BUDGET_OVERALLOCATED,
        lambda: ledger.allocate_batch(parent_digest, {"new-child": budget("0.01")}),
    )


def test_duplicate_child_allocation_conflicts(signed_transition):
    parent, _, _, _ = signed_transition
    ledger = AllocationLedger()
    parent_digest = ledger.register_parent(parent)
    ledger.allocate_batch(parent_digest, {"child-a": budget("1.00")})
    assert_code(
        ErrorCode.ALLOCATION_CONFLICT,
        lambda: ledger.allocate_batch(parent_digest, {"child-a": budget("1.00")}),
    )


def test_wrong_audience_fails(signed_transition):
    _, child, _, _ = signed_transition
    assert_code(
        ErrorCode.WRONG_AUDIENCE,
        lambda: validate_audience(child, "spiffe://example.com/agent/attacker"),
    )
    validate_audience(child, child["subject"])


def test_single_use_replay_fails(signed_transition):
    _, child, _, _ = signed_transition
    registry = UseRegistry()
    assert registry.commit_capsule(child) == 1
    assert_code(ErrorCode.REPLAY_DETECTED, lambda: registry.commit_capsule(child))


def test_concurrent_single_use_has_one_winner(signed_transition):
    _, child, _, _ = signed_transition
    registry = UseRegistry()
    barrier = Barrier(2)

    def commit(_):
        barrier.wait()
        try:
            registry.commit_capsule(child)
            return "committed"
        except GCPError as exc:
            return exc.code

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(commit, range(2)))
    assert results.count("committed") == 1
    assert results.count(ErrorCode.REPLAY_DETECTED) == 1


def test_online_strict_fetches_every_time(signed_transition):
    _, child, _, _ = signed_transition
    evaluator = RevocationEvaluator()
    calls = []

    def provider(endpoint, digest):
        calls.append((endpoint, digest))
        return StatusRecord(digest, NOW, revoked=False)

    evaluator.evaluate(child, now=NOW, provider=provider)
    evaluator.evaluate(child, now=NOW + timedelta(seconds=1), provider=provider)
    assert len(calls) == 2


def test_online_strict_revocation_blocks(signed_transition):
    _, child, _, _ = signed_transition
    evaluator = RevocationEvaluator()

    def provider(endpoint, digest):
        return StatusRecord(digest, NOW, revoked=True)

    assert_code(
        ErrorCode.REVOKED,
        lambda: evaluator.evaluate(child, now=NOW, provider=provider),
    )


def test_online_strict_outage_fails_closed(signed_transition):
    _, child, _, _ = signed_transition
    evaluator = RevocationEvaluator()
    assert_code(
        ErrorCode.STATUS_UNAVAILABLE,
        lambda: evaluator.evaluate(child, now=NOW),
    )


def test_bounded_stale_boundary_is_inclusive(signed_transition):
    parent, _, _, _ = signed_transition
    evaluator = RevocationEvaluator()
    digest = artifact_digest(parent)
    evaluator.cache(StatusRecord(digest, NOW - timedelta(seconds=60), revoked=False))
    result = evaluator.evaluate(parent, now=NOW)
    assert result.evidence[0].source == "cache"


def test_bounded_stale_record_over_boundary_fails(signed_transition):
    parent, _, _, _ = signed_transition
    evaluator = RevocationEvaluator()
    digest = artifact_digest(parent)
    evaluator.cache(StatusRecord(digest, NOW - timedelta(seconds=61), revoked=False))
    assert_code(
        ErrorCode.REVOCATION_STATUS_STALE,
        lambda: evaluator.evaluate(parent, now=NOW),
    )


def test_bounded_stale_refreshes_old_cache(signed_transition):
    parent, _, _, _ = signed_transition
    evaluator = RevocationEvaluator()
    digest = artifact_digest(parent)
    evaluator.cache(StatusRecord(digest, NOW - timedelta(seconds=61), revoked=False))

    def provider(endpoint, requested_digest):
        return StatusRecord(requested_digest, NOW, revoked=False)

    result = evaluator.evaluate(parent, now=NOW, provider=provider)
    assert result.evidence[0].source == "live"


def test_cascading_ancestor_revocation_blocks_descendant(signed_transition):
    parent, child, _, _ = signed_transition
    evaluator = RevocationEvaluator()
    parent_digest = artifact_digest(parent)

    def provider(endpoint, digest):
        return StatusRecord(
            digest,
            NOW,
            revoked=digest == parent_digest,
            cascade=digest == parent_digest,
        )

    assert_code(
        ErrorCode.REVOKED,
        lambda: evaluator.evaluate(child, ancestors=[parent], now=NOW, provider=provider),
    )


def test_non_cascading_ancestor_revocation_does_not_block_child(signed_transition):
    parent, child, _, _ = signed_transition
    evaluator = RevocationEvaluator()
    parent_digest = artifact_digest(parent)

    def provider(endpoint, digest):
        return StatusRecord(digest, NOW, revoked=digest == parent_digest, cascade=False)

    evaluator.evaluate(child, ancestors=[parent], now=NOW, provider=provider)


def test_offline_profile_requires_local_permission(signed_transition):
    _, child, _, _ = signed_transition
    offline = deepcopy(child)
    offline["validity"]["freshness"] = {"profile": "offline-until-expiry"}
    evaluator = RevocationEvaluator()
    assert_code(
        ErrorCode.OFFLINE_PROFILE_DISALLOWED,
        lambda: evaluator.evaluate(offline, now=NOW),
    )
    result = evaluator.evaluate(offline, now=NOW, allow_offline=True)
    assert result.offline_residual_risk is True
    assert result.evidence[0].source == "offline"


def test_known_offline_revocation_still_blocks(signed_transition):
    _, child, _, _ = signed_transition
    offline = deepcopy(child)
    offline["validity"]["freshness"] = {"profile": "offline-until-expiry"}
    evaluator = RevocationEvaluator()
    digest = artifact_digest(offline)
    evaluator.cache(StatusRecord(digest, NOW - timedelta(days=1), revoked=True))
    assert_code(
        ErrorCode.REVOKED,
        lambda: evaluator.evaluate(offline, now=NOW, allow_offline=True),
    )
