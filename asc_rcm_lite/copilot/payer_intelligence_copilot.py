"""Copilot responses for synthetic payer intelligence."""

from __future__ import annotations

from dataclasses import dataclass

from asc_rcm_lite.intelligence.payer_patterns import PayerPatternSummary
from asc_rcm_lite.models import ValidationError, require_non_empty


@dataclass(frozen=True)
class PayerIntelligenceAnswer:
    question: str
    response_text: str
    cited_evidence_ids: tuple[str, ...]
    human_review_required: bool

    def __post_init__(self) -> None:
        require_non_empty(self.question, "PayerIntelligenceAnswer.question")
        require_non_empty(self.response_text, "PayerIntelligenceAnswer.response_text")
        if not self.cited_evidence_ids:
            raise ValidationError("PayerIntelligenceAnswer.cited_evidence_ids must not be empty")
        if not self.human_review_required:
            raise ValidationError("PayerIntelligenceAnswer.human_review_required must be true")
        if "human review is required" not in self.response_text.lower():
            raise ValidationError("Payer intelligence response must include human-review language")
        for evidence_id in self.cited_evidence_ids:
            if evidence_id not in self.response_text:
                raise ValidationError(f"Payer intelligence response must cite evidence id {evidence_id}")


class PayerIntelligenceCopilot:
    def answer(self, question: str, summary: PayerPatternSummary) -> PayerIntelligenceAnswer:
        response = (
            f"Synthetic payer intelligence answer: {question}. Top denial root causes: {summary.top_preventable_root_causes}. "
            f"Payer friction scores: {summary.payer_friction_score}. This aggregate memory is synthetic and non-authoritative. "
            f"Human review is required before operational use. Evidence: {', '.join(summary.aggregate_evidence_ids)}."
        )
        return PayerIntelligenceAnswer(
            question=question,
            response_text=response,
            cited_evidence_ids=summary.aggregate_evidence_ids,
            human_review_required=True,
        )
