"""Versioned governance dependency graph and join-aware reach estimation."""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Dict, Iterable, Mapping, Set, Tuple

from .crypto import artifact_digest
from .errors import ErrorCode, GCPError


class JoinType(str, Enum):
    SINGLE = "SINGLE"
    OR = "OR"
    AND = "AND"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class GraphNode:
    node_id: str
    join_type: JoinType = JoinType.SINGLE
    declaration_confidence: Decimal = Decimal("1")


@dataclass(frozen=True)
class GraphEdge:
    source: str
    target: str
    required: bool = True
    declaration_confidence: Decimal = Decimal("1")


@dataclass(frozen=True)
class ReachEstimate:
    score: Decimal
    reachable_nodes: Tuple[str, ...]
    topology_confidence: Decimal
    unknown_join_nodes: Tuple[str, ...]
    graph_digest: str


class GovernanceGraph:
    """A deterministic DAG projection used as CARM decision evidence."""

    def __init__(self, nodes: Iterable[GraphNode], edges: Iterable[GraphEdge]) -> None:
        self._nodes: Dict[str, GraphNode] = {}
        for node in nodes:
            if node.node_id in self._nodes:
                self._fail("Duplicate governance-graph node", node_id=node.node_id)
            if not Decimal("0") <= node.declaration_confidence <= Decimal("1"):
                self._fail("Node confidence must be between zero and one", node_id=node.node_id)
            self._nodes[node.node_id] = node
        self._edges = tuple(edges)
        self._outgoing: Dict[str, Set[str]] = {node_id: set() for node_id in self._nodes}
        self._incoming: Dict[str, Set[str]] = {node_id: set() for node_id in self._nodes}
        self._edge_confidence: Dict[Tuple[str, str], Decimal] = {}
        for edge in self._edges:
            if edge.source not in self._nodes or edge.target not in self._nodes:
                self._fail(
                    "Governance-graph edge references an unknown node",
                    source=edge.source,
                    target=edge.target,
                )
            if edge.source == edge.target:
                self._fail("Governance-graph self-edge is invalid", node_id=edge.source)
            if not Decimal("0") <= edge.declaration_confidence <= Decimal("1"):
                self._fail("Edge confidence must be between zero and one")
            key = (edge.source, edge.target)
            if key in self._edge_confidence:
                self._fail("Duplicate governance-graph edge", source=edge.source, target=edge.target)
            self._outgoing[edge.source].add(edge.target)
            self._incoming[edge.target].add(edge.source)
            self._edge_confidence[key] = edge.declaration_confidence
        self._validate_join_types()
        self._validate_acyclic()

    @staticmethod
    def _fail(message: str, **details: object) -> None:
        raise GCPError(ErrorCode.INVALID_GOVERNANCE_GRAPH, message, details)

    def _validate_join_types(self) -> None:
        for node_id, incoming in self._incoming.items():
            join_type = self._nodes[node_id].join_type
            if len(incoming) <= 1 and join_type in {JoinType.AND, JoinType.OR}:
                self._fail(
                    "AND and OR join types require multiple incoming dependencies",
                    node_id=node_id,
                )
            if len(incoming) > 1 and join_type == JoinType.SINGLE:
                self._fail(
                    "A multi-parent dependency must declare AND, OR, or UNKNOWN semantics",
                    node_id=node_id,
                )

    def _validate_acyclic(self) -> None:
        indegree = {node_id: len(values) for node_id, values in self._incoming.items()}
        ready = sorted(node_id for node_id, degree in indegree.items() if degree == 0)
        visited = 0
        while ready:
            current = ready.pop(0)
            visited += 1
            for target in sorted(self._outgoing[current]):
                indegree[target] -= 1
                if indegree[target] == 0:
                    ready.append(target)
                    ready.sort()
        if visited != len(self._nodes):
            self._fail("Governance graph must be acyclic")

    @property
    def digest(self) -> str:
        document = {
            "nodes": [
                {
                    "node_id": node.node_id,
                    "join_type": node.join_type.value,
                    "declaration_confidence": str(node.declaration_confidence),
                }
                for node in sorted(self._nodes.values(), key=lambda value: value.node_id)
            ],
            "edges": [
                {
                    "source": edge.source,
                    "target": edge.target,
                    "required": edge.required,
                    "declaration_confidence": str(edge.declaration_confidence),
                }
                for edge in sorted(self._edges, key=lambda value: (value.source, value.target))
            ],
        }
        return artifact_digest(document)

    def estimate_reach(self, source: str) -> ReachEstimate:
        if source not in self._nodes:
            self._fail("Reach source is not in the governance graph", source=source)
        reachable: Set[str] = set()
        frontier = sorted(self._outgoing[source])
        confidence = self._nodes[source].declaration_confidence
        while frontier:
            current = frontier.pop(0)
            if current in reachable:
                continue
            reachable.add(current)
            confidence = min(confidence, self._nodes[current].declaration_confidence)
            for parent in self._incoming[current]:
                confidence = min(confidence, self._edge_confidence[(parent, current)])
            frontier.extend(sorted(self._outgoing[current] - reachable))

        score = Decimal("0")
        unknown = []
        for node_id in sorted(reachable):
            incoming_count = len(self._incoming[node_id])
            join_type = self._nodes[node_id].join_type
            if join_type == JoinType.OR:
                score += Decimal("1") / Decimal(max(1, incoming_count))
            else:
                # AND and single-parent nodes are fully exposed. UNKNOWN is
                # conservatively weighted as exposed and lowers confidence.
                score += Decimal("1")
                if join_type == JoinType.UNKNOWN:
                    unknown.append(node_id)
                    confidence = min(confidence, Decimal("0.5"))
        return ReachEstimate(
            score=score,
            reachable_nodes=tuple(sorted(reachable)),
            topology_confidence=confidence,
            unknown_join_nodes=tuple(unknown),
            graph_digest=self.digest,
        )

    def snapshot(self) -> Mapping[str, object]:
        return {"graph_digest": self.digest, "node_count": len(self._nodes), "edge_count": len(self._edges)}
