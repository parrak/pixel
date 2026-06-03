import os

from asc_rcm_lite.copilot.provider import MockLLMProvider, get_copilot_provider
from asc_rcm_lite.copilot.service import CopilotService
from asc_rcm_lite.ingestion import load_asc_case


def test_mock_provider_is_default():
    os.environ.pop("ASC_RCM_COPILOT_PROVIDER", None)
    assert isinstance(get_copilot_provider(), MockLLMProvider)


def test_unknown_provider_falls_back_safely():
    os.environ["ASC_RCM_COPILOT_PROVIDER"] = "unknown"
    assert isinstance(get_copilot_provider(), MockLLMProvider)
    os.environ.pop("ASC_RCM_COPILOT_PROVIDER", None)


def test_copilot_service_works_through_provider_interface():
    case = load_asc_case("data/asc_cases/008_high_value_120_day_ar_followup.json")
    response = CopilotService().run_for_case(case, request_id="provider-1", user_role="biller", task_type="summarize_case_context")
    assert response.human_review_required is True

