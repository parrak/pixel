from asc_rcm_lite.pipeline import run_pipeline


def test_persona_routing_exposes_role_specific_navigation():
    personas = run_pipeline().portfolio_snapshot["persona_experiences"]

    assert personas["coder"]["primary_objects"] == ["Patient", "Encounter", "Procedure", "Documentation", "Coding Review", "Charge Capture"]
    assert personas["coder"]["navigation"] == ["My Reviews", "Documentation Gaps", "Coding Queue", "Procedure Explorer", "Completed Reviews", "Knowledge Base"]
    assert all(item["work_object_type"] in {"Coding Review", "Charge Capture"} for item in personas["coder"]["work_items"])

    assert personas["biller"]["navigation"] == ["My AR Queue", "Escalations", "High-Dollar Accounts", "Underpayments", "Completed Recoveries"]
    assert all(item["work_object_type"] in {"AR Follow-Up", "Underpayment"} for item in personas["biller"]["work_items"])

    assert personas["manager"]["navigation"] == ["Operations", "Assignments", "Escalations", "Blockers", "Team Performance"]
    assert personas["manager"]["work_items"]


def test_operator_os_landing_starts_with_monday_morning_work():
    landing = run_pipeline().portfolio_snapshot["operator_os_landing"]

    assert landing["title"] == "Monday Morning"
    assert landing["revenue_at_risk"] == "2500000.00"
    assert landing["open_work"] == 126
    assert landing["critical_appeals"] >= 14
    assert landing["authorizations_at_risk"] >= 8
    assert landing["coding_reviews_pending"] >= 22
    assert landing["sections"] == ["My Work", "My Queue", "Today's Priorities", "Blocked Work", "Recommended Actions"]


def test_every_work_object_has_valid_workflow_graph_contract():
    work_objects = run_pipeline().portfolio_snapshot["work_objects"]

    assert work_objects
    for item in work_objects:
        graph = item["workflow_graph"]
        current = [stage for stage in graph["stages"] if stage["status"] == "current"]

        assert graph["current_state"]
        assert graph["owner"]
        assert graph["next_state"]
        assert graph["dependency"]
        assert graph["waiting_on"]
        assert graph["days_in_state"] >= 1
        assert graph["deadline_days_remaining"] >= 1
        assert graph["expected_recovery"] is not None
        assert len(current) == 1
        assert current[0]["label"] == graph["current_state"]
        assert current[0]["owner"]
        assert current[0]["dependency"]


def test_persona_builder_tolerates_legacy_work_objects_without_graph():
    work_object = run_pipeline().portfolio_snapshot["work_objects"][0].copy()
    work_object.pop("workflow_graph")

    from asc_rcm_lite.personas import build_persona_experiences

    personas = build_persona_experiences([work_object], recovery_center={})

    routed_items = [item for persona in personas.values() for item in persona["work_items"]]
    assert routed_items
    assert routed_items[0]["current_state"]
    assert routed_items[0]["next_state"] == "Next Action"


def test_denial_lifecycle_graph_progresses_from_patient_to_payment():
    item = next(
        work
        for work in run_pipeline(case_id="ASC-CASE-004").portfolio_snapshot["work_objects"]
        if work["work_object_type"] == "Medical Necessity Denial"
    )
    graph = item["workflow_graph"]
    labels = [stage["label"] for stage in graph["stages"]]

    assert labels == ["Patient", "Procedure", "Coding", "Claim", "Denial", "Appeal", "Resolution", "Payment"]
    assert graph["current_state"] in {"Denial", "Appeal", "Payment"}
    assert graph["owner"]
    assert graph["next_state"]
    assert graph["dependency"] in {"Waiting on Payer", "Waiting on Provider Documentation"}
    assert item["timeline"]
