from asc_rcm_lite.journeys import execute_workflow_journey


def test_missing_documentation_denial_workflow_acceptance():
    run = execute_workflow_journey("missing_documentation_denial").to_dict()

    assert run["queue_snapshot"]["work_object_type"] == "Medical Necessity Denial" or run["queue_snapshot"]["work_object_type"] == "Missing Documentation"
    assert run["queue_snapshot"]["documents"]
    assert run["queue_snapshot"]["timeline"]
    assert run["queue_snapshot"]["institutional_memory"]
    assert run["metrics_before"]["open_work"] == 1
    assert run["metrics_after"]["open_work"] == 0


def test_medical_necessity_appeal_workflow_acceptance():
    run = execute_workflow_journey("medical_necessity_appeal").to_dict()

    assert run["queue_snapshot"]["work_object_type"] == "Medical Necessity Denial"
    assert run["recommendation_history"]
    assert any(step["label"] == "Clinical Evidence" for step in run["steps"])
    assert any(document["artifact_type"] == "Appeal Packet" for document in run["queue_snapshot"]["documents"])
    assert run["final_outcome"]["financial_result"] is not None


def test_ar_follow_up_workflow_acceptance():
    run = execute_workflow_journey("ar_follow_up").to_dict()

    assert run["queue_snapshot"]["financial_impact"] == "12500.00"
    assert run["payer_history"]
    assert run["prior_follow_up_activity"]
    assert run["workflow_trace"]
    assert run["final_outcome"]["financial_result"] == "12500.00"


def test_authorization_failure_workflow_acceptance():
    run = execute_workflow_journey("authorization_failure").to_dict()

    assert run["queue_snapshot"]["work_object_type"] == "Authorization"
    assert run["queue_snapshot"]["documents"]
    assert any(step["label"] == "Coordination" for step in run["steps"])
    assert run["institutional_memory_update"]["entries"] >= 1
    assert run["metrics_after"]["open_work"] == 0


def test_workflow_acceptance_updates_artifacts_and_timeline_integrity():
    run = execute_workflow_journey("medical_necessity_appeal").to_dict()

    assert run["queue_snapshot"]["timeline"]
    assert run["queue_snapshot"]["documents"]
    assert run["queue_snapshot"]["institutional_memory"]
    assert run["final_outcome"]["status"]
