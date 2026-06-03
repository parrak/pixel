"""Deterministic A/R copilot drafts based on authoritative A/R flags."""

from __future__ import annotations

from dataclasses import dataclass

from asc_rcm_lite.detectors.ar import ARFlag, detect_ar_flags
from asc_rcm_lite.models import ASCCase, ValidationError, require_non_empty, validate_no_phi_keys


@dataclass(frozen=True)
class ARCopilotDraft:
    draft_type: str
    case_id: str
    content: str
    cited_evidence_ids: tuple[str, ...]
    human_review_required: bool

    def __post_init__(self) -> None:
        require_non_empty(self.draft_type, "ARCopilotDraft.draft_type")
        require_non_empty(self.case_id, "ARCopilotDraft.case_id")
        require_non_empty(self.content, "ARCopilotDraft.content")
        if not self.cited_evidence_ids:
            raise ValidationError("ARCopilotDraft.cited_evidence_ids must not be empty")
        if not self.human_review_required:
            raise ValidationError("ARCopilotDraft.human_review_required must be true")
        if "human review is required" not in self.content.lower():
            raise ValidationError("ARCopilotDraft.content must include human-review language")
        for evidence_id in self.cited_evidence_ids:
            if evidence_id not in self.content:
                raise ValidationError(f"Draft content must cite evidence id {evidence_id}")
        validate_no_phi_keys(
            {
                "draft_type": self.draft_type,
                "case_id": self.case_id,
                "content": self.content,
                "cited_evidence_ids": list(self.cited_evidence_ids),
            }
        )


class ARCopilot:
    def summarize_followup(self, case: ASCCase, *, as_of_date: str) -> ARCopilotDraft:
        flags = detect_ar_flags(case, as_of_date=as_of_date)
        evidence_ids = _evidence_ids(flags)
        summary = "; ".join(
            f"{flag.flag_type} ({flag.priority_band}, Evidence: {', '.join(flag.evidence_citation_ids)})"
            for flag in flags
        ) or "no deterministic A/R flags"
        content = (
            f"A/R follow-up summary for {case.case_id}: {summary}.\n"
            "Deterministic A/R flags remain authoritative, and each follow-up recommendation is for human review only.\n"
            f"Human review is required before any payer outreach, appeal, correction, or write-off decision.\n"
            f"Evidence reviewed: {', '.join(evidence_ids)}."
        )
        return ARCopilotDraft("ar_followup_summary", case.case_id, content, evidence_ids, True)

    def generate_payer_call_script(self, flag: ARFlag) -> ARCopilotDraft:
        content = (
            f"Payer call script for {flag.case_id}: review whether the synthetic claim needs follow-up for {flag.flag_type} and confirm current status, deadlines, and missing items before any external conversation (Evidence: {', '.join(flag.evidence_citation_ids)}).\n"
            "State that this is a synthetic workflow exercise and capture only reviewer-safe next steps.\n"
            "Human review is required before any payer outreach, appeal, correction, or write-off decision.\n"
            f"Evidence reviewed: {', '.join(flag.evidence_citation_ids)}."
        )
        return ARCopilotDraft("payer_call_script", flag.case_id, content, flag.evidence_citation_ids, True)

    def generate_internal_followup_note(self, flag: ARFlag) -> ARCopilotDraft:
        content = (
            f"Internal follow-up note for {flag.case_id}: {flag.reason_for_flag} Recommended next action: {flag.recommended_next_action}\n"
            f"Priority is {flag.priority_band} ({flag.priority_score}) with balance {flag.balance} in aging bucket {flag.aging_bucket} (Evidence: {', '.join(flag.evidence_citation_ids)}).\n"
            "Human review is required before any payer outreach, appeal, correction, or write-off decision.\n"
            f"Evidence reviewed: {', '.join(flag.evidence_citation_ids)}."
        )
        return ARCopilotDraft("internal_followup_note", flag.case_id, content, flag.evidence_citation_ids, True)

    def generate_missing_information_checklist(self, flag: ARFlag) -> ARCopilotDraft:
        content = (
            "Missing information checklist:\n"
            f"- Review whether the current status and deadline data are complete for {flag.flag_type} (Evidence: {', '.join(flag.evidence_citation_ids)}).\n"
            "- Review whether prior touches, supporting remit or denial details, and queue ownership are documented before action.\n"
            "Human review is required before any payer outreach, appeal, correction, or write-off decision.\n"
            f"Evidence reviewed: {', '.join(flag.evidence_citation_ids)}."
        )
        return ARCopilotDraft("missing_information_checklist", flag.case_id, content, flag.evidence_citation_ids, True)

    def explain_next_best_action(self, flag: ARFlag) -> ARCopilotDraft:
        content = (
            f"Next-best-action explanation for {flag.case_id}: review whether the next step should be '{flag.recommended_next_action}' because the deterministic flag reason is '{flag.reason_for_flag}' (Evidence: {', '.join(flag.evidence_citation_ids)}).\n"
            "This explanation is assistive only and does not guarantee payer response or payment.\n"
            "Human review is required before any payer outreach, appeal, correction, or write-off decision.\n"
            f"Evidence reviewed: {', '.join(flag.evidence_citation_ids)}."
        )
        return ARCopilotDraft("next_best_action_explanation", flag.case_id, content, flag.evidence_citation_ids, True)

    def generate_manager_escalation_summary(self, flag: ARFlag) -> ARCopilotDraft:
        content = (
            f"Manager escalation summary for {flag.case_id}: {flag.flag_type} is prioritized as {flag.priority_band} with score {flag.priority_score} and balance {flag.balance} (Evidence: {', '.join(flag.evidence_citation_ids)}).\n"
            f"Review whether deadline pressure, aging, or balance warrants escalation under the synthetic workflow guardrails. Recommended owner role: {flag.owner_role}.\n"
            "Human review is required before any payer outreach, appeal, correction, or write-off decision.\n"
            f"Evidence reviewed: {', '.join(flag.evidence_citation_ids)}."
        )
        return ARCopilotDraft("manager_escalation_summary", flag.case_id, content, flag.evidence_citation_ids, True)


def _evidence_ids(flags: tuple[ARFlag, ...]) -> tuple[str, ...]:
    ids: list[str] = []
    for flag in flags:
        ids.extend(flag.evidence_citation_ids)
    return tuple(dict.fromkeys(ids)) or ("NO-EVIDENCE",)
