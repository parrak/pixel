from pathlib import Path

import pytest

from asc_rcm_lite.copilot.context import build_case_context
from asc_rcm_lite.copilot.models import CopilotRequest, CopilotResponse
from asc_rcm_lite.copilot.mock_llm import MockLLM
from asc_rcm_lite.copilot.service import CopilotService
from asc_rcm_lite.ingestion import load_asc_case
from asc_rcm_lite.models import ValidationError


def _load_case(name: str):
    return load_asc_case(Path("data/asc_cases") / name)


def test_copilot_response_requires_citations():
    context = build_case_context(_load_case("005_modifier_59_bundled_risk.json"))

    with pytest.raises(ValidationError, match="cited_evidence_ids must not be empty"):
        CopilotResponse(
            request_id="req-1",
            case_id="ASC-CASE-005",
            user_role="coder",
            task_type="draft_coder_review_note",
            structured_context=context,
            response_text="Human review is required before any coding, billing, appeal, or payer-facing action.",
            cited_evidence_ids=(),
            safety_flags=(),
            human_review_required=True,
            generated_at="2026-06-02T00:00:00+00:00",
        )


def test_copilot_response_requires_human_review_required_true():
    context = build_case_context(_load_case("005_modifier_59_bundled_risk.json"))

    with pytest.raises(ValidationError, match="human_review_required must be true"):
        CopilotResponse(
            request_id="req-2",
            case_id="ASC-CASE-005",
            user_role="coder",
            task_type="draft_coder_review_note",
            structured_context=context,
            response_text="Review CPT 45380 support (Evidence: SRC-005-CDM). Human review is required.",
            cited_evidence_ids=("SRC-005-CDM",),
            safety_flags=(),
            human_review_required=False,
            generated_at="2026-06-02T00:00:00+00:00",
        )


def test_unsafe_definitive_language_is_blocked():
    context = build_case_context(_load_case("005_modifier_59_bundled_risk.json"))

    with pytest.raises(ValidationError, match="Unsafe definitive language"):
        CopilotResponse(
            request_id="req-3",
            case_id="ASC-CASE-005",
            user_role="coder",
            task_type="draft_coder_review_note",
            structured_context=context,
            response_text=(
                "This is coded correctly based on the record (Evidence: SRC-005-CDM). "
                "Human review is required."
            ),
            cited_evidence_ids=("SRC-005-CDM",),
            safety_flags=(),
            human_review_required=True,
            generated_at="2026-06-02T00:00:00+00:00",
        )


def test_mock_copilot_can_summarize_synthetic_asc_case():
    case = _load_case("008_high_value_120_day_ar_followup.json")
    service = CopilotService(MockLLM())

    response = service.run_for_case(
        case,
        request_id="req-4",
        user_role="biller",
        task_type="summarize_case_context",
    )

    assert "ASC-CASE-008" in response.response_text
    assert "ar_follow_up" in response.response_text
    assert "Human review is required" in response.response_text
    assert response.cited_evidence_ids


def test_mock_copilot_can_draft_coder_review_note():
    case = _load_case("005_modifier_59_bundled_risk.json")
    service = CopilotService(MockLLM())

    response = service.run_for_case(
        case,
        request_id="req-5",
        user_role="coder",
        task_type="draft_coder_review_note",
    )

    assert "Coder review draft" in response.response_text
    assert "modifier" in response.response_text.lower()
    assert "SRC-005" in response.response_text
    assert response.human_review_required is True


def test_mock_copilot_can_draft_ar_followup_note():
    case = _load_case("008_high_value_120_day_ar_followup.json")
    service = CopilotService(MockLLM())

    response = service.run_for_case(
        case,
        request_id="req-6",
        user_role="biller",
        task_type="draft_ar_followup_note",
    )

    assert "A/R follow-up draft" in response.response_text
    assert "open_ar_120_plus" in response.response_text
    assert "SRC-008" in response.response_text
    assert response.human_review_required is True


def test_question_task_requires_question_text():
    case = _load_case("002_missing_prior_authorization_denial.json")
    service = CopilotService(MockLLM())
    request = CopilotRequest(
        request_id="req-7",
        case_id=case.case_id,
        user_role="manager",
        task_type="answer_user_question_from_case_context",
        structured_context=build_case_context(case),
    )

    with pytest.raises(ValidationError, match="Question text is required"):
        service.run(request)
