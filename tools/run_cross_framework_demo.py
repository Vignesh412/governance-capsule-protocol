#!/usr/bin/env python3
"""Run the deterministic OpenAI-to-Google-ADK governed handoff proof."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from demo.scenarios import run_scenario  # noqa: E402


def main():
    result = run_scenario("cross-framework")
    print(json.dumps({
        "route": "OpenAI Agents SDK -> GCP transport -> Google ADK -> gateway",
        "state": result["state"],
        "decision": result["decision"],
        "transport_digest": result["transport_digest"],
        "cross_framework_controls": [
            item for item in result["controls"]
            if "OPENAI" in item or "GOOGLE_ADK" in item or "CROSS_FRAMEWORK" in item
        ],
        "lineage_verified": "GCP_DELEGATION_LINEAGE_VERIFIED" in result["controls"],
        "connector_calls": result["connector_calls"],
        "suppliers_created": result["suppliers_created"],
        "claim_boundary": "Deterministic SDK-contract proof; native SDK/model execution is not yet demonstrated.",
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
