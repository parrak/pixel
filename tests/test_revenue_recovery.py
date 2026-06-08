from asc_rcm_lite.journeys import available_workflow_journeys, execute_workflow_journey
from asc_rcm_lite.pipeline import run_pipeline
from asc_rcm_lite.revenue_recovery import DENIAL_TYPES, PAYERS


def _portfolio():
    return run_pipeline().portfolio_snapshot


def test_revenue_recovery_command_center_generates_realistic_claim_volume():
    center = _portfolio()["revenue_recovery_command_center"]

    assert center["dataset_summary"]["claims"] >= 500
    assert center["dataset_summary"]["denials"] >= 100
    assert center["dataset_summary"]["appeals"] >= 50
    assert center["metrics"]["revenue_at_risk"] != "0.00"
    assert center["metrics"]["recoverable_revenue"] != "0.00"
    assert center["work_today"]
    assert center["money_trapped"]


def test_denial_recovery_factory_supports_required_denial_types():
    factory = _portfolio()["denial_recovery_factory"]

    assert set(DENIAL_TYPES).issubset(set(factory["supported_types"]))
    assert factory["denials"]
    denial = factory["denials"][0]
    assert denial["timeline"]
    assert denial["evidence"]
    assert denial["required_documents"]
    assert denial["recommendations"]
    assert "financial_impact" in denial


def test_appeal_workspace_and_evidence_engine_generate_work_product():
    portfolio = _portfolio()
    appeal = portfolio["appeal_workspace"]["appeals"][0]
    evidence = portfolio["evidence_engine"]
    outputs = portfolio["recovery_copilot_outputs"]["outputs"]

    assert appeal["appeal_package"]["status"] == "ready"
    assert "Appeal Packet" in appeal["appeal_package"]["artifacts"]
    assert "Cover Letter" in appeal["appeal_package"]["artifacts"]
    assert "Payer Rules" in evidence["evidence_types"]
    assert "Clinical Documentation" in evidence["evidence_types"]
    assert outputs
    assert all(item["ready_for_workflow"] for item in outputs)
    assert any("Appeal Packet" in item["work_product"] for item in outputs)


def test_payer_playbooks_and_similar_recoveries_cover_core_payers():
    portfolio = _portfolio()
    playbooks = portfolio["payer_playbooks"]["playbooks"]
    patterns = portfolio["similar_recoveries"]["patterns"]

    assert {item["payer"] for item in playbooks} == set(PAYERS)
    assert all(item["required_evidence"] for item in playbooks)
    assert patterns
    assert all("winning_evidence" in item for item in patterns)


def test_manager_recovery_operations_change_work_and_track_outcomes():
    portfolio = _portfolio()
    manager_ops = portfolio["manager_recovery_operations"]
    outcomes = portfolio["recovery_outcome_tracking"]

    assert manager_ops["prioritize_revenue"]
    assert manager_ops["reassign_work"]
    assert manager_ops["escalate_cases"]
    assert manager_ops["allocate_capacity"]
    assert outcomes["rollup"]["recovered_revenue"] != "0.00"
    assert outcomes["recoveries"]


def test_nimble_recovery_scenario_matches_evaluation_prompt():
    scenario = _portfolio()["nimble_recovery_evaluation"]

    assert scenario["denials"] == 100
    assert scenario["revenue_at_risk"] == "2500000.00"
    assert scenario["work_first"]
    assert scenario["where_money_is_trapped"]
    assert scenario["walkthrough_outcome"]["updated_decision_memory"]


def test_recovery_workflow_journeys_are_executable_end_to_end():
    assert "underpayment_recovery" in available_workflow_journeys()
    assert "manager_intervention" in available_workflow_journeys()

    underpayment = execute_workflow_journey("underpayment_recovery").to_dict()
    manager = execute_workflow_journey("manager_intervention").to_dict()

    assert underpayment["metrics_after"]["recovered_revenue"] == "400.00"
    assert underpayment["institutional_memory_update"]["pattern"] == "Underpayment recovery"
    assert any(step["label"] == "Work Redistribution" for step in manager["steps"])
    assert manager["metrics_after"]["realized_financial_result"] == "15900.00"
