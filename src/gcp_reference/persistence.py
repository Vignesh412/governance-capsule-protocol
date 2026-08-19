"""SQLite persistence for the restart-safe gateway reference profile."""

import json
import sqlite3
from pathlib import Path
from threading import RLock
from typing import Optional, Union

from .carm import RuntimeDecision
from .errors import ErrorCode, GCPError
from .gateway import ActionRecord, ActionState


class SQLiteActionStore:
    """Transactional action ledger with an action-id uniqueness boundary.

    SQLite supplies durable single-host semantics for the demonstration. It is
    not presented as the final multi-instance PostgreSQL deployment profile.
    """

    def __init__(self, path: Union[str, Path]) -> None:
        self.path = str(path)
        self._lock = RLock()
        self._connection = sqlite3.connect(self.path, check_same_thread=False)
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.execute("PRAGMA synchronous=FULL")
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS governed_actions (
                action_id TEXT PRIMARY KEY,
                proposal_digest TEXT NOT NULL,
                state TEXT NOT NULL,
                attempt INTEGER NOT NULL,
                decision TEXT,
                controls_json TEXT NOT NULL,
                reason_codes_json TEXT NOT NULL,
                graph_digest TEXT,
                policy_snapshot_digest TEXT,
                result_reference TEXT,
                result_digest TEXT,
                receipt_json TEXT
                ,proposal_json TEXT
            )
            """
        )
        columns = {
            row[1] for row in self._connection.execute("PRAGMA table_info(governed_actions)")
        }
        if "proposal_json" not in columns:
            self._connection.execute("ALTER TABLE governed_actions ADD COLUMN proposal_json TEXT")
        self._connection.commit()

    def close(self) -> None:
        with self._lock:
            self._connection.close()

    def claim(self, record: ActionRecord) -> Optional[ActionRecord]:
        with self._lock, self._connection:
            cursor = self._connection.execute(
                """
                INSERT OR IGNORE INTO governed_actions (
                    action_id, proposal_digest, state, attempt, decision, controls_json,
                    reason_codes_json, graph_digest, policy_snapshot_digest,
                    result_reference, result_digest, receipt_json, proposal_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._values(record),
            )
            if cursor.rowcount == 1:
                return None
            return self._get_unlocked(record.action_id)

    def get(self, action_id: str) -> Optional[ActionRecord]:
        with self._lock:
            return self._get_unlocked(action_id)

    def put(self, record: ActionRecord) -> None:
        with self._lock, self._connection:
            cursor = self._connection.execute(
                """
                UPDATE governed_actions SET
                    proposal_digest=?, state=?, attempt=?, decision=?, controls_json=?,
                    reason_codes_json=?, graph_digest=?, policy_snapshot_digest=?,
                    result_reference=?, result_digest=?, receipt_json=?, proposal_json=?
                WHERE action_id=?
                """,
                self._values(record)[1:] + (record.action_id,),
            )
            if cursor.rowcount != 1:
                raise GCPError(ErrorCode.ACTION_STATE_INVALID, "Action record does not exist")

    def delete_waiting(self, action_id: str, expected: ActionState) -> None:
        with self._lock, self._connection:
            cursor = self._connection.execute(
                "DELETE FROM governed_actions WHERE action_id=? AND state=?",
                (action_id, expected.value),
            )
            if cursor.rowcount != 1:
                raise GCPError(ErrorCode.ACTION_STATE_INVALID, "Action state changed before resume")

    def pending_commits(self):
        with self._lock:
            rows = self._connection.execute(
                "SELECT * FROM governed_actions WHERE state IN (?, ?) ORDER BY action_id",
                (ActionState.COMMITTING.value, ActionState.COMMIT_OUTCOME_UNKNOWN.value),
            ).fetchall()
            return tuple(self._record(row) for row in rows)

    def _get_unlocked(self, action_id: str) -> Optional[ActionRecord]:
        row = self._connection.execute(
            "SELECT * FROM governed_actions WHERE action_id=?", (action_id,)
        ).fetchone()
        return self._record(row) if row else None

    @staticmethod
    def _values(record: ActionRecord):
        return (
            record.action_id,
            record.proposal_digest,
            record.state.value,
            record.attempt,
            record.decision.value if record.decision else None,
            json.dumps(list(record.controls), separators=(",", ":")),
            json.dumps(list(record.reason_codes), separators=(",", ":")),
            record.graph_digest,
            record.policy_snapshot_digest,
            record.result_reference,
            record.result_digest,
            json.dumps(record.receipt, separators=(",", ":"), sort_keys=True) if record.receipt else None,
            json.dumps(record.proposal, separators=(",", ":"), sort_keys=True) if record.proposal else None,
        )

    @staticmethod
    def _record(row) -> ActionRecord:
        return ActionRecord(
            action_id=row[0],
            proposal_digest=row[1],
            state=ActionState(row[2]),
            attempt=row[3],
            decision=RuntimeDecision(row[4]) if row[4] else None,
            controls=tuple(json.loads(row[5])),
            reason_codes=tuple(json.loads(row[6])),
            graph_digest=row[7],
            policy_snapshot_digest=row[8],
            result_reference=row[9],
            result_digest=row[10],
            receipt=json.loads(row[11]) if row[11] else None,
            proposal=json.loads(row[12]) if len(row) > 12 and row[12] else None,
        )
