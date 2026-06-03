"""Service layer that routes ASC RCM copilot requests to a local LLM stub."""

from __future__ import annotations

from asc_rcm_lite.models import ASCCase

from .context import build_case_context
from .models import CopilotDraft, CopilotRequest, CopilotResponse, default_generated_at
from .provider import CopilotProvider, get_copilot_provider
from .prompts import build_prompt
from .rules import validate_request, validate_response


class CopilotService:
    def __init__(self, llm: CopilotProvider | None = None) -> None:
        if llm is None:
            llm = get_copilot_provider()
        self.llm = llm

    def create_request(
        self,
        case: ASCCase,
        *,
        request_id: str,
        user_role: str,
        task_type: str,
        question: str | None = None,
        opportunity_id: str | None = None,
    ) -> CopilotRequest:
        return CopilotRequest(
            request_id=request_id,
            case_id=case.case_id,
            user_role=user_role,
            task_type=task_type,
            structured_context=build_case_context(case, question=question, opportunity_id=opportunity_id),
        )

    def run(self, request: CopilotRequest) -> CopilotResponse:
        validate_request(request)
        draft = self.llm.generate(request, build_prompt(request.task_type, request.structured_context))
        response = CopilotResponse(
            request_id=request.request_id,
            case_id=request.case_id,
            user_role=request.user_role,
            task_type=request.task_type,
            structured_context=request.structured_context,
            response_text=draft.response_text,
            cited_evidence_ids=tuple(dict.fromkeys(draft.cited_evidence_ids)),
            safety_flags=tuple(dict.fromkeys(draft.safety_flags + ("human_review_required", "deterministic_rules_authoritative"))),
            human_review_required=True,
            generated_at=default_generated_at(),
        )
        validate_response(response)
        return response

    def run_for_case(
        self,
        case: ASCCase,
        *,
        request_id: str,
        user_role: str,
        task_type: str,
        question: str | None = None,
        opportunity_id: str | None = None,
    ) -> CopilotResponse:
        return self.run(
            self.create_request(
                case,
                request_id=request_id,
                user_role=user_role,
                task_type=task_type,
                question=question,
                opportunity_id=opportunity_id,
            )
        )
