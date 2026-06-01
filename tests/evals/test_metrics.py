from app.evals.metrics import run_prebill_eval


def test_eval_metrics_meet_v01_bar():
    metrics = run_prebill_eval()
    assert metrics["charts"] >= 10
    assert metrics["opportunity_recall"] == 1.0
    assert metrics["false_positive_rate"] == 0.0
    assert metrics["evidence_citation_completeness"] == 1.0
    assert metrics["unsupported_assertion_count"] == 0
    assert metrics["provider_query_safety_pass_rate"] == 1.0
    assert metrics["reviewer_packet_completeness"] == 1.0
