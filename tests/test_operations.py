from asc_rcm_lite.operations import build_operational_dashboard, simulate_acquisition, workflow_catalog
from asc_rcm_lite.pipeline import run_pipeline


def test_workflow_catalog_includes_phase_two_workflows():
    workflow_ids = {workflow.workflow_id for workflow in workflow_catalog()}
    assert "asc_authorization" in workflow_ids
    assert "asc_coding_review" in workflow_ids
    assert "asc_denial_review" in workflow_ids
    assert "asc_charge_capture" in workflow_ids


def test_pipeline_emits_operational_tasks_with_recommendations():
    result = run_pipeline(case_id="ASC-CASE-002")
    tasks = result.cases[0].operational_tasks

    assert tasks
    assert all(task.recommendations for task in tasks)
    assert any(task.workflow_id == "asc_authorization" for task in tasks)
    assert all(task.organization_name for task in tasks)
    assert all(task.history for task in tasks)


def test_operational_dashboard_exposes_manager_metrics():
    result = run_pipeline()
    tasks = tuple(task for case in result.cases for task in case.operational_tasks)
    dashboard = build_operational_dashboard(tasks)

    assert dashboard["total_tasks"] >= len(result.cases)
    assert "revenue_at_risk" in dashboard
    assert "workflow_bottlenecks" in dashboard


def test_pipeline_emits_portfolio_snapshot():
    result = run_pipeline()

    assert len(result.portfolio_snapshot["organizations"]) == 3
    assert result.portfolio_snapshot["monday_morning"]["title"] == "Monday Morning"
    assert result.portfolio_snapshot["role_views"]


def test_acquisition_simulator_returns_operator_plan():
    plan = simulate_acquisition(
        specialty="GI",
        headcount=75,
        workflow_maturity="developing",
        systems=("EHR", "Practice Management", "Clearinghouse", "Spreadsheets"),
    )

    assert plan["specialty"] == "GI"
    assert plan["workflow_map"]
    assert plan["standardization_opportunities"]
    assert plan["deployment_plan"]
