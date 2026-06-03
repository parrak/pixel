"""Safety and validation helpers for copilot responses."""

from __future__ import annotations

from asc_rcm_lite.models import ValidationError

from .models import CopilotRequest, CopilotResponse


def validate_request(request: CopilotRequest) -> None:
    if request.task_type == "answer_user_question_from_case_context" and not request.structured_context.get("question"):
        raise ValidationError("Question text is required for answer_user_question_from_case_context")


def validate_response(response: CopilotResponse) -> None:
    if not response.cited_evidence_ids:
        raise ValidationError("Copilot response must include citations")
