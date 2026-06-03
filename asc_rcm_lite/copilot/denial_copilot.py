"""Deterministic denial and appeal copilot drafts."""

from __future__ import annotations

from dataclasses import dataclass

from asc_rcm_lite.detectors.denials import DenialOpportunity
from asc_rcm_lite.models import ValidationError, require_non_empty, validate_no_phi_keys


@dataclass(frozen=True)
class DenialCopilotDraft:
    draft_type: str
    case_id: str
    content: str
    cited_evidence_ids: tuple[str, ...]
    human_review_required: bool

    def __post_init__(self) -> None:
        require_non_empty(self.draft_type, "DenialCopilotDraft.draft_type")
        require_non_empty(self.case_id, "DenialCopilotDraft.case_id")
        require_non_empty(self.content, "DenialCopilotDraft.content")
        if not self.cited_evidence_ids:
            raise ValidationError("DenialCopilotDraft.cited_evidence_ids must not be empty")
        if not self.human_review_required:
            raise ValidationError("DenialCopilotDraft.human_review_required must be true")
        if "human review is required" not in self.content.lower():
            raise ValidationError("DenialCopilotDraft.content must include human-review language")
        if "for reviewer validation" not in self.content.lower():
            raise ValidationError("DenialCopilotDraft.content must include reviewer-validation language")
        for evidence_id in self.cited_evidence_ids:
            if evidence_id not in self.content:
                raise ValidationError(f"Denial draft must cite evidence id {evidence_id}")
        banned = ("payer must pay", "definitely incorrect", "guaranteed", "compliant code", "patient has")
        lowered = self.content.lower()
        for phrase in banned:
            if phrase in lowered:
                raise ValidationError(f"Unsafe denial draft language is not allowed: {phrase}")
        validate_no_phi_keys(
            {
                "draft_type": self.draft_type,
                "case_id": self.case_id,
                "content": self.content,
                "cited_evidence_ids": list(self.cited_evidence_ids),
            }
        )


class DenialCopilot:
    def denial_summary(self, opportunity: DenialOpportunity) -> DenialCopilotDraft:
        return self._draft(
            "denial_summary",
            opportunity,
            f"Denial summary for reviewer validation: category {opportunity.denial_category}, appealability {opportunity.appealability}, and path {opportunity.recommended_path} (Evidence: {', '.join(opportunity.evidence_citation_ids)}). Human review is required before use.",
        )

    def appeal_packet_summary(self, opportunity: DenialOpportunity) -> DenialCopilotDraft:
        return self._draft(
            "appeal_packet_summary",
            opportunity,
            f"Appeal packet summary for reviewer validation: review whether the denial root cause '{opportunity.root_cause_hypothesis}' and missing evidence {', '.join(opportunity.missing_evidence)} support the next step '{opportunity.next_best_action}' (Evidence: {', '.join(opportunity.evidence_citation_ids)}). Human review is required before use.",
        )

    def appeal_letter_draft(self, opportunity: DenialOpportunity) -> DenialCopilotDraft:
        return self._draft(
            "appeal_letter_draft",
            opportunity,
            f"Appeal letter draft for reviewer validation: request review of denial {opportunity.denial_id} based on synthetic case evidence and cited supporting materials (Evidence: {', '.join(opportunity.evidence_citation_ids)}). This draft does not guarantee payment or a final coding outcome. Human review is required before use.",
        )

    def evidence_checklist(self, opportunity: DenialOpportunity) -> DenialCopilotDraft:
        return self._draft(
            "evidence_checklist",
            opportunity,
            f"Evidence checklist for reviewer validation: confirm denial evidence, payer policy support, and missing items {', '.join(opportunity.missing_evidence)} before any appeal or corrected-claim workflow (Evidence: {', '.join(opportunity.evidence_citation_ids)}). Human review is required before use.",
        )

    def payer_followup_call_script(self, opportunity: DenialOpportunity) -> DenialCopilotDraft:
        return self._draft(
            "payer_followup_call_script",
            opportunity,
            f"Payer follow-up call script for reviewer validation: confirm denial status, deadline, and required evidence for {opportunity.denial_category} without asserting payment entitlement (Evidence: {', '.join(opportunity.evidence_citation_ids)}). Human review is required before use.",
        )

    def root_cause_note(self, opportunity: DenialOpportunity) -> DenialCopilotDraft:
        return self._draft(
            "root_cause_note",
            opportunity,
            f"Internal denial root-cause note for reviewer validation: {opportunity.root_cause_hypothesis} Recommended path: {opportunity.recommended_path} (Evidence: {', '.join(opportunity.evidence_citation_ids)}). Human review is required before use.",
        )

    def prevention_recommendation(self, opportunity: DenialOpportunity) -> DenialCopilotDraft:
        text = (
            "Review whether upstream workflow, coding QA, or documentation capture changes could reduce recurrence"
            if opportunity.appealability != "unlikely"
            else "Review whether write-off review or manager escalation is more appropriate than a strong appeal"
        )
        return self._draft(
            "prevention_recommendation",
            opportunity,
            f"Prevention recommendation for reviewer validation: {text} based on category {opportunity.denial_category} (Evidence: {', '.join(opportunity.evidence_citation_ids)}). Human review is required before use.",
        )

    def _draft(self, draft_type: str, opportunity: DenialOpportunity, text: str) -> DenialCopilotDraft:
        return DenialCopilotDraft(
            draft_type=draft_type,
            case_id=opportunity.case_id,
            content=text,
            cited_evidence_ids=opportunity.evidence_citation_ids,
            human_review_required=True,
        )
