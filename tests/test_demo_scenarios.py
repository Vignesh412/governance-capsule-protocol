from demo.scenarios import run_scenario, scenario_catalog


def test_every_visual_demo_scenario_reaches_its_documented_outcome():
    catalog = scenario_catalog()
    for item in catalog:
        assert item["use_case"]
        assert item["task"]
        assert item["governance"]
        assert item["change"]
        assert item["why_it_matters"]
    results = {item["id"]: run_scenario(item["id"]) for item in catalog}

    cross_framework = results["cross-framework"]
    assert cross_framework["state"] == "COMMITTED"
    assert cross_framework["connector_calls"] == 1
    assert "GCP_SOURCE_OPENAI_HANDOFF_VERIFIED" in cross_framework["controls"]
    assert "GCP_DESTINATION_GOOGLE_ADK_BOUNDARY_VERIFIED" in cross_framework["controls"]

    allowed = results["valid-delegation"]
    assert allowed["state"] == "COMMITTED"
    assert allowed["connector_calls"] == 1
    assert allowed["suppliers_created"] == 1
    assert "GCP_DELEGATION_LINEAGE_VERIFIED" in allowed["controls"]

    expected_rejections = {
        "authority-expansion": "GCP_AUTHORITY_EXPANSION",
        "obligation-removed": "GCP_OBLIGATION_REMOVED",
        "budget-exceeded": "GCP_BUDGET_OVERALLOCATED",
        "tampered-proof": "GCP_INVALID_DELEGATION_PROOF",
        "root-revoked": "GCP_REVOKED",
    }
    for scenario_id, reason in expected_rejections.items():
        result = results[scenario_id]
        assert result["state"] == "REJECTED"
        assert result["reason_codes"] == [reason]
        assert result["connector_calls"] == 0
        assert result["suppliers_created"] == 0

    recovery = results["crash-recovery"]
    assert recovery["state"] == "COMMITTED"
    assert recovery["recovery"]["durable_state_at_crash"] == "COMMITTING"
    assert recovery["recovery"]["connector_calls_before_restart"] == 1
    assert recovery["recovery"]["connector_calls_after_recovery"] == 1
    assert recovery["suppliers_created"] == 1
