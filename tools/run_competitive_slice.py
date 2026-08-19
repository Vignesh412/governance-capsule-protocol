#!/usr/bin/env python3
"""Reproduce the first graph-sensitive CARM comparison as JSON."""

import json
import sys
from dataclasses import asdict
from decimal import Decimal
from enum import Enum
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gcp_reference import (
    GovernanceGraph,
    GraphEdge,
    GraphNode,
    JoinType,
    PolicyEffect,
    PolicyEvaluation,
    PolicyLayer,
    fixed_priority,
    most_restrictive,
    resolve_carm,
)


def graph():
    return GovernanceGraph(
        [
            GraphNode("intake"),
            GraphNode("compliance"),
            GraphNode("finance"),
            GraphNode("approval", JoinType.AND),
            GraphNode("create-vendor"),
        ],
        [
            GraphEdge("intake", "compliance"),
            GraphEdge("intake", "finance"),
            GraphEdge("compliance", "approval"),
            GraphEdge("finance", "approval"),
            GraphEdge("approval", "create-vendor"),
        ],
    )


POLICIES = (
    PolicyEvaluation(
        "urn:policy:regulatory:continuity",
        "1",
        PolicyLayer.REGULATORY,
        PolicyEffect.ALLOW,
        "REGULATORY_CONTINUITY_REQUIRED",
    ),
    PolicyEvaluation(
        "urn:policy:organization:freeze",
        "1",
        PolicyLayer.ORGANIZATIONAL,
        PolicyEffect.BLOCK,
        "ORGANIZATIONAL_CHANGE_FREEZE",
    ),
)


def serializable(value):
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Decimal):
        return str(value)
    raise TypeError(type(value).__name__)


def main():
    workflow = graph()
    positions = {}
    for node_id in ("intake", "create-vendor"):
        resolution = resolve_carm(POLICIES, workflow, node_id)
        positions[node_id] = asdict(resolution)
    result = {
        "experiment": "competitive-slice-v0.1",
        "claim": "The same valid-policy conflict produces a different CARM mode when verified downstream reach changes.",
        "graph": workflow.snapshot(),
        "baselines": {
            "most_restrictive": most_restrictive(POLICIES),
            "fixed_priority": fixed_priority(POLICIES),
        },
        "positions": positions,
        "limitations": [
            "This demonstrates decision sensitivity, not that either decision is correct.",
            "Policy inputs are supplied by the local adapter; Microsoft AGT/ACS is not integrated yet.",
            "Human escalation is not executed and no CARM-SE or RIG behavior is included.",
        ],
    }
    print(json.dumps(result, indent=2, default=serializable, sort_keys=True))


if __name__ == "__main__":
    main()
