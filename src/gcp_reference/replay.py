"""Atomic replay and use-count tracking."""

from threading import Lock
from typing import Any, Dict, Mapping, Optional

from .errors import ErrorCode, GCPError


class UseRegistry:
    """Process-local reference registry for one enforcement domain."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._counts: Dict[str, int] = {}

    def commit(self, identifier: str, *, max_uses: Optional[int]) -> int:
        with self._lock:
            previous = self._counts.get(identifier, 0)
            if max_uses is not None and previous >= max_uses:
                raise GCPError(
                    ErrorCode.REPLAY_DETECTED,
                    "Authority use limit has been exhausted",
                    {"identifier": identifier, "max_uses": max_uses},
                )
            current = previous + 1
            self._counts[identifier] = current
            return current

    def commit_capsule(self, capsule: Mapping[str, Any]) -> int:
        replay = capsule["validity"]["replay"]
        if replay["mode"] == "single-use":
            limit = 1
        elif replay["mode"] == "multi-use":
            limit = replay.get("max_uses")
        else:
            raise GCPError(ErrorCode.UNSUPPORTED_SEMANTICS, "Unknown replay mode")
        return self.commit(capsule["capsule_id"], max_uses=limit)

    def count(self, identifier: str) -> int:
        with self._lock:
            return self._counts.get(identifier, 0)
