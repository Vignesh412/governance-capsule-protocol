"""Atomic in-memory budget allocation authority."""

from copy import deepcopy
from decimal import Decimal
from threading import Lock
from typing import Any, Dict, Mapping, Sequence

from .crypto import artifact_digest
from .errors import ErrorCode, GCPError


BudgetVector = Dict[str, Dict[str, str]]


def _vector(items: Sequence[Mapping[str, str]]) -> BudgetVector:
    result: BudgetVector = {}
    for item in items:
        dimension = item["dimension"]
        if dimension in result:
            raise GCPError(
                ErrorCode.UNSUPPORTED_SEMANTICS,
                "Budget dimension occurs more than once",
                {"dimension": dimension},
            )
        result[dimension] = {"quantity": item["quantity"], "unit": item["unit"]}
    return result


class AllocationLedger:
    """Serializes preallocated child budgets for registered parents.

    The implementation is process-local reference code. A production adapter
    must provide equivalent atomicity using durable transactional storage.
    """

    def __init__(self) -> None:
        self._lock = Lock()
        self._parents: Dict[str, Dict[str, Any]] = {}

    def register_parent(self, parent: Mapping[str, Any]) -> str:
        digest = artifact_digest(parent)
        limits = _vector(parent["budgets"])
        with self._lock:
            existing = self._parents.get(digest)
            if existing is not None and existing["limits"] != limits:
                raise GCPError(ErrorCode.ALLOCATION_CONFLICT, "Parent digest has conflicting limits")
            self._parents.setdefault(digest, {"limits": limits, "allocations": {}})
        return digest

    def allocate_batch(
        self,
        parent_digest: str,
        child_allocations: Mapping[str, Sequence[Mapping[str, str]]],
    ) -> None:
        """Atomically reserve all child allocations or reserve none."""

        requested = {child_id: _vector(items) for child_id, items in child_allocations.items()}
        with self._lock:
            state = self._parents.get(parent_digest)
            if state is None:
                raise GCPError(ErrorCode.ALLOCATION_CONFLICT, "Parent is not registered")
            duplicate_ids = set(requested).intersection(state["allocations"])
            if duplicate_ids:
                raise GCPError(
                    ErrorCode.ALLOCATION_CONFLICT,
                    "Child allocation identifier already exists",
                    {"child_ids": sorted(duplicate_ids)},
                )

            totals: Dict[str, Decimal] = {
                dimension: Decimal("0") for dimension in state["limits"]
            }
            for allocation in state["allocations"].values():
                self._accumulate(totals, state["limits"], allocation)
            for allocation in requested.values():
                self._accumulate(totals, state["limits"], allocation)

            for dimension, total in totals.items():
                limit = Decimal(state["limits"][dimension]["quantity"])
                if total > limit:
                    raise GCPError(
                        ErrorCode.BUDGET_OVERALLOCATED,
                        "Aggregate child allocation exceeds parent budget",
                        {
                            "dimension": dimension,
                            "requested_total": str(total),
                            "limit": str(limit),
                        },
                    )

            state["allocations"].update(deepcopy(requested))

    @staticmethod
    def _accumulate(
        totals: Dict[str, Decimal],
        limits: BudgetVector,
        allocation: BudgetVector,
    ) -> None:
        for dimension, item in allocation.items():
            limit = limits.get(dimension)
            if limit is None:
                raise GCPError(
                    ErrorCode.BUDGET_OVERALLOCATED,
                    "Child allocates a dimension absent from parent",
                    {"dimension": dimension},
                )
            if item["unit"] != limit["unit"]:
                raise GCPError(
                    ErrorCode.BUDGET_UNIT_MISMATCH,
                    "Child and parent budget units differ",
                    {"dimension": dimension},
                )
            totals[dimension] += Decimal(item["quantity"])

    def snapshot(self, parent_digest: str) -> Mapping[str, Any]:
        with self._lock:
            state = self._parents.get(parent_digest)
            if state is None:
                raise GCPError(ErrorCode.ALLOCATION_CONFLICT, "Parent is not registered")
            return deepcopy(state)
