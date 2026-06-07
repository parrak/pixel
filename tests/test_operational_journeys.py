import json
import subprocess
import sys
from pathlib import Path

from asc_rcm_lite.journeys import execute_ar_manager_journey, execute_ar_specialist_journey, execute_vp_revenue_cycle_journey


def test_ar_specialist_journey_runs_end_to_end():
    run = execute_ar_specialist_journey().to_dict()

    assert run["queue_snapshot"]["task_id"] == "TASK-JOURNEY-AR-SPECIALIST"
    assert run["recommendation_history"]
    assert run["steps"][0]["label"] == "Receive work in queue"
    assert run["steps"][-1]["label"] == "Record outcome"
    assert run["workflow_trace"][-1]["next_state"] == "closed"
    assert run["final_task"]["status"] == "completed"
    assert run["final_outcome"]["financial_result"] == "12500.00"
    assert run["institutional_memory_update"]["history_records_added"] >= 1
    assert run["metrics_before"]["realized_financial_result"] == "0.00"
    assert run["metrics_after"]["realized_financial_result"] == "12500.00"


def test_ar_manager_journey_captures_manager_intervention_and_metric_updates():
    run = execute_ar_manager_journey().to_dict()

    assert len(run["queue_snapshot"]["queue_before"]) == 3
    assert run["queue_snapshot"]["blocked_candidates"]
    assert run["queue_snapshot"]["escalation_candidates"]
    assert any(step["label"] == "Reassign work" for step in run["steps"])
    assert any(step["label"] == "Escalate critical items" for step in run["steps"])
    assert run["metrics_before"]["blocked_work"] > run["metrics_after"]["blocked_work"]
    assert run["metrics_after"]["realized_financial_result"] == "15900.00"
    assert run["institutional_memory_update"]["history_records_added"] >= 2
    assert run["workflow_trace"]


def test_vp_journey_connects_financial_impact_to_operational_actions():
    run = execute_vp_revenue_cycle_journey().to_dict()

    assert run["queue_snapshot"]["holdco_dashboard"]["portfolio_revenue"]
    assert run["prior_follow_up_activity"]
    assert any(step["label"] == "Approve operational actions" for step in run["steps"])
    assert run["final_task"]["approved_actions"]
    assert run["final_outcome"]["collections_gap_delta"] == "165000.00"
    assert run["metrics_before"]["quarterly_collections_gap"] == "420000.00"
    assert run["metrics_after"]["quarterly_collections_gap"] == "255000.00"
    assert run["institutional_memory_update"]["executive_decisions_captured"] == 3


def test_demo_scripts_are_executable_and_emit_json():
    root = Path(__file__).resolve().parents[1]
    for script_name, persona in (
        ("demo_ar_specialist.py", "AR Specialist"),
        ("demo_ar_manager.py", "AR Manager"),
        ("demo_vp_revenue_cycle.py", "VP Revenue Cycle"),
    ):
        output = subprocess.run(
            [sys.executable, str(root / script_name)],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(output.stdout)
        assert payload["persona"] == persona
        assert payload["steps"]
        assert payload["metrics_after"]
