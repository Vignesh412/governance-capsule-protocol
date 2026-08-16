"""Revocation freshness evaluation at governed action boundaries."""

from dataclasses import dataclass
from datetime import datetime
from threading import Lock
from typing import Any, Callable, Dict, Mapping, Optional, Sequence, Tuple

from .crypto import artifact_digest
from .errors import ErrorCode, GCPError


@dataclass(frozen=True)
class StatusRecord:
    capsule_digest: str
    checked_at: datetime
    revoked: bool
    cascade: bool = False
    authenticated: bool = True


@dataclass(frozen=True)
class RevocationEvidence:
    capsule_digest: str
    profile: str
    checked_at: Optional[datetime]
    source: str


@dataclass(frozen=True)
class RevocationResult:
    evidence: Tuple[RevocationEvidence, ...]
    offline_residual_risk: bool


StatusProvider = Callable[[str, str], StatusRecord]


class RevocationEvaluator:
    """Evaluate current and ancestor status using each capsule's profile."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._cache: Dict[str, StatusRecord] = {}

    def cache(self, record: StatusRecord) -> None:
        self._validate_authenticated(record)
        with self._lock:
            current = self._cache.get(record.capsule_digest)
            if current is None or record.checked_at >= current.checked_at:
                self._cache[record.capsule_digest] = record

    def evaluate(
        self,
        capsule: Mapping[str, Any],
        *,
        ancestors: Sequence[Mapping[str, Any]] = (),
        now: datetime,
        provider: Optional[StatusProvider] = None,
        allow_offline: bool = False,
    ) -> RevocationResult:
        evidence = []
        offline_risk = False
        lineage = list(ancestors) + [capsule]
        for index, item in enumerate(lineage):
            digest = artifact_digest(item)
            freshness = item["validity"]["freshness"]
            profile = freshness["profile"]
            record, source = self._record_for(
                digest,
                freshness,
                now=now,
                provider=provider,
                allow_offline=allow_offline,
            )
            if profile == "offline-until-expiry":
                offline_risk = True
            evidence.append(
                RevocationEvidence(
                    capsule_digest=digest,
                    profile=profile,
                    checked_at=record.checked_at if record else None,
                    source=source,
                )
            )
            if record and record.revoked and (index == len(lineage) - 1 or record.cascade):
                raise GCPError(
                    ErrorCode.REVOKED,
                    "Capsule or cascading ancestor is revoked",
                    {"capsule_digest": digest, "cascade": record.cascade},
                )
        return RevocationResult(tuple(evidence), offline_risk)

    def _record_for(
        self,
        digest: str,
        freshness: Mapping[str, Any],
        *,
        now: datetime,
        provider: Optional[StatusProvider],
        allow_offline: bool,
    ) -> Tuple[Optional[StatusRecord], str]:
        profile = freshness["profile"]
        if profile == "online-strict":
            return self._fetch(digest, freshness["status_endpoint"], provider), "live"

        if profile == "bounded-stale":
            with self._lock:
                cached = self._cache.get(digest)
            max_age = freshness["max_staleness_seconds"]
            if cached is not None and (now - cached.checked_at).total_seconds() <= max_age:
                self._validate_authenticated(cached)
                return cached, "cache"
            if provider is None:
                raise GCPError(
                    ErrorCode.REVOCATION_STATUS_STALE,
                    "No sufficiently fresh authenticated revocation status is available",
                    {"capsule_digest": digest, "max_staleness_seconds": max_age},
                )
            return self._fetch(digest, freshness["status_endpoint"], provider), "live"

        if profile == "offline-until-expiry":
            if not allow_offline:
                raise GCPError(
                    ErrorCode.OFFLINE_PROFILE_DISALLOWED,
                    "Local policy does not permit offline-until-expiry",
                )
            with self._lock:
                cached = self._cache.get(digest)
            if cached is not None:
                self._validate_authenticated(cached)
            return cached, "cache" if cached else "offline"

        raise GCPError(
            ErrorCode.UNSUPPORTED_SEMANTICS,
            "Unknown revocation freshness profile",
            {"profile": profile},
        )

    def _fetch(
        self,
        digest: str,
        endpoint: str,
        provider: Optional[StatusProvider],
    ) -> StatusRecord:
        if provider is None:
            raise GCPError(ErrorCode.STATUS_UNAVAILABLE, "Revocation status provider is unavailable")
        try:
            record = provider(endpoint, digest)
        except GCPError:
            raise
        except Exception as exc:
            raise GCPError(ErrorCode.STATUS_UNAVAILABLE, "Revocation status lookup failed") from exc
        if record.capsule_digest != digest:
            raise GCPError(ErrorCode.STATUS_UNAVAILABLE, "Status response targets another capsule")
        self._validate_authenticated(record)
        self.cache(record)
        return record

    @staticmethod
    def _validate_authenticated(record: StatusRecord) -> None:
        if not record.authenticated:
            raise GCPError(ErrorCode.STATUS_UNAVAILABLE, "Revocation status is not authenticated")
