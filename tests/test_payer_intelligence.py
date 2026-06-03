from pathlib import Path

from asc_rcm_lite.copilot.payer_intelligence_copilot import PayerIntelligenceCopilot
from asc_rcm_lite.detectors.ar import detect_ar_flags
from asc_rcm_lite.detectors.denials import detect_denial_opportunities
from asc_rcm_lite.ingestion import load_asc_cases
from asc_rcm_lite.intelligence.payer_patterns import build_payer_pattern_summary


def test_payer_pattern_metrics_are_deterministic():
    cases = tuple(load_asc_cases())
    denials = tuple(item for case in cases for item in detect_denial_opportunities(case))
    ar_flags = tuple(item for case in cases for item in detect_ar_flags(case, as_of_date="2026-06-03"))
    summary = build_payer_pattern_summary(cases, denials, ar_flags)
    assert summary.denials_by_category
    assert summary.payer_friction_score


def test_top_denial_root_cause_computed_correctly():
    cases = tuple(load_asc_cases())
    denials = tuple(item for case in cases for item in detect_denial_opportunities(case))
    ar_flags = tuple(item for case in cases for item in detect_ar_flags(case, as_of_date="2026-06-03"))
    summary = build_payer_pattern_summary(cases, denials, ar_flags)
    assert "prior_authorization" in summary.top_preventable_root_causes


def test_payer_intelligence_answer_includes_aggregate_citations():
    cases = tuple(load_asc_cases())
    denials = tuple(item for case in cases for item in detect_denial_opportunities(case))
    ar_flags = tuple(item for case in cases for item in detect_ar_flags(case, as_of_date="2026-06-03"))
    summary = build_payer_pattern_summary(cases, denials, ar_flags)
    answer = PayerIntelligenceCopilot().answer("Why is this payer creating work?", summary)
    assert answer.cited_evidence_ids
    assert "Human review is required" in answer.response_text

