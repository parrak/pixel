from asc_rcm_lite.pipeline import run_pipeline


def test_all_cases_run_end_to_end():
    result = run_pipeline()
    assert len(result.cases) >= 8


def test_expected_opportunities_are_emitted():
    result = run_pipeline(case_id="ASC-CASE-005")
    case = result.cases[0]
    assert any(item.coding_issue_type == "bundled_procedure_risk" for item in case.coding_opportunities)


def test_no_duplicate_opportunities_for_same_root_cause():
    result = run_pipeline(case_id="ASC-CASE-008")
    case = result.cases[0]
    ids = [item.flag_id for item in case.ar_flags]
    assert len(ids) == len(set(ids))


def test_every_packet_has_human_review_required():
    result = run_pipeline(case_id="ASC-CASE-002")
    assert all(packet.human_review_required for packet in result.cases[0].reviewer_packets)


def test_every_work_item_has_priority_score_and_owner_role():
    result = run_pipeline(case_id="ASC-CASE-008")
    assert all(item.priority_score >= 0 and item.owner_role for item in result.cases[0].work_queue)


def test_pipeline_summary_includes_manager_level_metrics():
    result = run_pipeline()
    assert "total_items" in result.manager_metrics

