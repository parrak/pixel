from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from asc_rcm_lite.copilot.ar_copilot import ARCopilot
from asc_rcm_lite.detectors.ar import detect_ar_flags
from asc_rcm_lite.ingestion import load_asc_case
from asc_rcm_lite.models import ValidationError


def _load_case(name: str):
    return load_asc_case(Path("data/asc_cases") / name)


def test_120_plus_day_high_dollar_ar_gets_urgent_priority():
    flags = detect_ar_flags(_load_case("008_high_value_120_day_ar_followup.json"), as_of_date="2026-02-01")
    target = next(flag for flag in flags if flag.flag_type == "high_dollar_ar")

    assert target.aging_bucket == "120_plus"
    assert target.priority_band == "urgent"


def test_near_deadline_appeal_outranks_lower_risk_ar():
    near_deadline_flags = detect_ar_flags(_load_case("002_missing_prior_authorization_denial.json"), as_of_date="2026-02-02")
    near_deadline = next(flag for flag in near_deadline_flags if flag.flag_type == "appeal_deadline_risk")

    base_case = _load_case("008_high_value_120_day_ar_followup.json")
    lower_risk_case = replace(
        base_case,
        claims=(replace(base_case.claims[0], billed_amount=Decimal("1200.00"), submitted_date="2026-01-01", status="open_ar_60_plus"),),
        work_queue_items=(replace(base_case.work_queue_items[0], due_date="2026-03-15"),),
    )
    lower_risk = next(flag for flag in detect_ar_flags(lower_risk_case, as_of_date="2026-02-02") if flag.flag_type == "ar_30")

    assert near_deadline.priority_score > lower_risk.priority_score


def test_underpayment_flag_is_generated_when_paid_amount_below_contract_allowed_amount():
    flags = detect_ar_flags(_load_case("007_underpayment_against_simple_contract.json"), as_of_date="2026-02-18")

    underpayment = next(flag for flag in flags if flag.flag_type == "underpayment")
    assert underpayment.balance == Decimal("400.00")


def test_stale_followup_is_flagged():
    flags = detect_ar_flags(_load_case("008_high_value_120_day_ar_followup.json"), as_of_date="2026-02-01")

    assert any(flag.flag_type == "stale_followup" for flag in flags)


def test_clean_paid_claim_is_not_flagged():
    assert detect_ar_flags(_load_case("001_clean_paid_orthopedic_arthroscopy.json"), as_of_date="2026-02-01") == ()


def test_ar_copilot_response_includes_citations_and_human_review_language():
    case = _load_case("008_high_value_120_day_ar_followup.json")
    draft = ARCopilot().summarize_followup(case, as_of_date="2026-02-01")

    assert draft.cited_evidence_ids
    assert "Human review is required" in draft.content


def test_no_phi_like_fields_appear_in_ar_outputs():
    flag = detect_ar_flags(_load_case("007_underpayment_against_simple_contract.json"), as_of_date="2026-02-18")[0]
    output = {
        "flag_id": flag.flag_id,
        "claim_id": flag.claim_id,
        "case_id": flag.case_id,
        "payer": flag.payer,
        "flag_type": flag.flag_type,
        "days_in_ar": flag.days_in_ar,
        "balance": str(flag.balance),
        "aging_bucket": flag.aging_bucket,
        "last_touch_date": flag.last_touch_date,
        "next_deadline": flag.next_deadline,
        "reason_for_flag": flag.reason_for_flag,
        "recommended_next_action": flag.recommended_next_action,
        "owner_role": flag.owner_role,
        "evidence_citation_ids": list(flag.evidence_citation_ids),
    }
    forbidden = {"name", "first_name", "last_name", "email", "phone", "address", "dob", "mrn", "ssn"}
    assert forbidden.isdisjoint(output.keys())


def test_invalid_as_of_date_is_rejected_with_validation_error():
    with pytest.raises(ValidationError, match="Invalid deterministic date format"):
        detect_ar_flags(_load_case("008_high_value_120_day_ar_followup.json"), as_of_date="2026/02/01")
