from asc_rcm_lite.pipeline import run_pipeline


def test_pipeline_emits_work_objects():
    result = run_pipeline()
    work_objects = result.portfolio_snapshot["work_objects"]

    assert work_objects
    assert all(item["work_object_id"] for item in work_objects)
    assert all(item["timeline"] for item in work_objects)
    assert all(item["evidence"] for item in work_objects)
    assert all(item["documents"] for item in work_objects)
    assert all(item["recommendations"] for item in work_objects)
    assert all(item["actions"] for item in work_objects)
    assert all(item["institutional_memory"] for item in work_objects)


def test_work_objects_follow_hierarchy():
    result = run_pipeline(case_id="ASC-CASE-008")
    item = result.portfolio_snapshot["work_objects"][0]

    assert item["organization_id"]
    assert item["facility_id"]
    assert item["account_id"]
    assert item["claim_id"]
    assert item["task_id"]


def test_work_object_recommendations_are_evidence_first():
    result = run_pipeline(case_id="ASC-CASE-004")
    item = result.portfolio_snapshot["work_objects"][0]
    recommendation = item["recommendations"][0]

    assert recommendation["payer_rules"]
    assert recommendation["supporting_documentation"]
    assert recommendation["recovery_probability"]
    assert recommendation["expected_financial_impact"] is not None
