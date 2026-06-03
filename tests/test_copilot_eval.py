from evals.run_asc_copilot_eval import run_asc_copilot_eval


def test_eval_runs():
    metrics = run_asc_copilot_eval()
    assert metrics["cases"] >= 8


def test_eval_guardrail_metrics_hold():
    metrics = run_asc_copilot_eval()
    assert metrics["unsafe_language_count"] == 0
    assert metrics["unsupported_assertion_count"] == 0
    assert metrics["human_review_required_rate"] == 1.0

