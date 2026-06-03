"""Typed request and response models for the ASC RCM copilot."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from asc_rcm_lite.models import ValidationError, require_non_empty, validate_no_phi_keys


USER_ROLES = {"coder", "biller", "denial_specialist", "manager"}
TASK_TYPES = {
    "summarize_case_context",
    "explain_opportunity",
    "suggest_next_best_action",
    "draft_coder_review_note",
    "draft_ar_followup_note",
    "draft_denial_appeal",
    "generate_missing_info_checklist",
    "answer_user_question_from_case_context",
}


@dataclass(frozen=True)
class CopilotRequest:
    request_id: str
    case_id: str
    user_role: str
    task_type: str
    structured_context: dict[str, Any]

    def __post_init__(self) -> None:
        require_non_empty(self.request_id, "CopilotRequest.request_id")
        require_non_empty(self.case_id, "CopilotRequest.case_id")
        if self.user_role not in USER_ROLES:
            raise ValidationError(f"Unsupported copilot user role: {self.user_role}")
        if self.task_type not in TASK_TYPES:
            raise ValidationError(f"Unsupported copilot task type: {self.task_type}")
        if not isinstance(self.structured_context, dict):
            raise ValidationError("CopilotRequest.structured_context must be a dictionary")
        validate_no_phi_keys(self.structured_context, "$.structured_context")


@dataclass(frozen=True)
class CopilotResponse:
    request_id: str
    case_id: str
    user_role: str
    task_type: str
    structured_context: dict[str, Any]
    response_text: str
    cited_evidence_ids: tuple[str, ...]
    safety_flags: tuple[str, ...]
    human_review_required: bool
    generated_at: str

    def __post_init__(self) -> None:
        require_non_empty(self.request_id, "CopilotResponse.request_id")
        require_non_empty(self.case_id, "CopilotResponse.case_id")
        require_non_empty(self.response_text, "CopilotResponse.response_text")
        if self.user_role not in USER_ROLES:
            raise ValidationError(f"Unsupported copilot user role: {self.user_role}")
        if self.task_type not in TASK_TYPES:
            raise ValidationError(f"Unsupported copilot task type: {self.task_type}")
        if not isinstance(self.structured_context, dict):
            raise ValidationError("CopilotResponse.structured_context must be a dictionary")
        validate_no_phi_keys(self.structured_context, "$.structured_context")
        if not self.cited_evidence_ids:
            raise ValidationError("CopilotResponse.cited_evidence_ids must not be empty")
        if not self.human_review_required:
            raise ValidationError("CopilotResponse.human_review_required must be true")
        lowered = self.response_text.lower()
        if "human review is required" not in lowered:
            raise ValidationError("CopilotResponse.response_text must state that human review is required")
        for evidence_id in self.cited_evidence_ids:
            require_non_empty(evidence_id, "CopilotResponse.cited_evidence_ids[]")
            if evidence_id not in self.response_text:
                raise ValidationError(
                    f"CopilotResponse.response_text must cite evidence id {evidence_id}"
                )
        _assert_safe_language(self.response_text)
        _assert_timestamp(self.generated_at)


@dataclass(frozen=True)
class CopilotDraft:
    response_text: str
    cited_evidence_ids: tuple[str, ...]
    safety_flags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        require_non_empty(self.response_text, "CopilotDraft.response_text")
        if not self.cited_evidence_ids:
            raise ValidationError("CopilotDraft.cited_evidence_ids must not be empty")


def default_generated_at() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _assert_safe_language(text: str) -> None:
    lowered = text.lower()
    banned_phrases = (
        "this is coded correctly",
        "coded correctly",
        "payer must pay",
        "must pay this claim",
        "definitively supports",
        "confirmed diagnosis",
        "patient has",
    )
    for phrase in banned_phrases:
        if phrase in lowered:
            raise ValidationError(f"Unsafe definitive language is not allowed: {phrase}")


def _assert_timestamp(value: str) -> None:
    require_non_empty(value, "CopilotResponse.generated_at")
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValidationError("CopilotResponse.generated_at must be ISO-8601 compatible") from exc
