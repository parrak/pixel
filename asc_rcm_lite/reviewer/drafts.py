"""Shared reviewer draft validation."""

from __future__ import annotations

from dataclasses import dataclass

from asc_rcm_lite.models import ValidationError, require_non_empty


@dataclass(frozen=True)
class DraftArtifact:
    draft_type: str
    case_id: str
    text: str
    cited_evidence_ids: tuple[str, ...]
    human_review_required: bool

    def __post_init__(self) -> None:
        require_non_empty(self.draft_type, "DraftArtifact.draft_type")
        require_non_empty(self.case_id, "DraftArtifact.case_id")
        validate_draft_text(self.text, self.cited_evidence_ids)
        if not self.human_review_required:
            raise ValidationError("DraftArtifact.human_review_required must be true")


def validate_draft_text(text: str, cited_evidence_ids: tuple[str, ...]) -> None:
    require_non_empty(text, "draft.text")
    if not cited_evidence_ids:
        raise ValidationError("Draft text requires evidence citations")
    lowered = text.lower()
    required = ("for reviewer validation", "human review is required")
    if not all(item in lowered for item in required):
        raise ValidationError("Draft text must include reviewer-validation and human-review language")
    banned = ("payer must pay", "definitely incorrect", "guaranteed", "compliant code", "patient has")
    for phrase in banned:
        if phrase in lowered:
            raise ValidationError(f"Unsafe definitive language is not allowed: {phrase}")
    for evidence_id in cited_evidence_ids:
        if evidence_id not in text:
            raise ValidationError(f"Draft text must cite evidence id {evidence_id}")
