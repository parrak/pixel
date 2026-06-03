"""Deterministic coding copilot helpers built on authoritative coding detectors."""

from __future__ import annotations

from dataclasses import dataclass

from asc_rcm_lite.detectors.coding import CodingOpportunity, detect_coding_opportunities
from asc_rcm_lite.models import ASCCase, ValidationError, require_non_empty, validate_no_phi_keys


FORBIDDEN_DEFINITIVE_LANGUAGE = (
    "must code",
    "definitely incorrect",
    "guaranteed denial",
    "compliant code",
    "payer must pay",
)


@dataclass(frozen=True)
class CodingCopilotDraft:
    draft_type: str
    case_id: str
    content: str
    cited_evidence_ids: tuple[str, ...]
    human_review_required: bool

    def __post_init__(self) -> None:
        require_non_empty(self.draft_type, "CodingCopilotDraft.draft_type")
        require_non_empty(self.case_id, "CodingCopilotDraft.case_id")
        require_non_empty(self.content, "CodingCopilotDraft.content")
        if not self.cited_evidence_ids:
            raise ValidationError("CodingCopilotDraft.cited_evidence_ids must not be empty")
        if not self.human_review_required:
            raise ValidationError("CodingCopilotDraft.human_review_required must be true")
        if "human review is required" not in self.content.lower():
            raise ValidationError("CodingCopilotDraft.content must include human-review language")
        for phrase in FORBIDDEN_DEFINITIVE_LANGUAGE:
            if phrase in self.content.lower():
                raise ValidationError(f"Forbidden definitive language is not allowed: {phrase}")
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


class CodingCopilot:
    def summarize_case(self, case: ASCCase) -> CodingCopilotDraft:
        issues = detect_coding_opportunities(case)
        evidence_ids = _evidence_for_case(case, issues)
        if issues:
            issue_list = "; ".join(
                f"{item.coding_issue_type} ({item.severity}, Evidence: {', '.join(item.evidence_citation_ids)})"
                for item in issues
            )
            content = (
                f"Coder review summary for {case.case_id}: review whether the synthetic ASC case has the following potential coding issues: {issue_list}.\n"
                "Deterministic coding detectors remain the source of truth, and coder should validate each item against source documentation for human review.\n"
                f"Human review is required before any coding, billing, claim-correction, or payer-facing action.\n"
                f"Evidence reviewed: {', '.join(evidence_ids)}."
            )
        else:
            content = (
                f"Coder review summary for {case.case_id}: no deterministic coding QA opportunities were surfaced from the current synthetic case facts.\n"
                "Coder should validate that source documentation and charge capture remain aligned before closing the review, for human review.\n"
                f"Human review is required before any coding, billing, claim-correction, or payer-facing action.\n"
                f"Evidence reviewed: {', '.join(evidence_ids)}."
            )
        return CodingCopilotDraft(
            draft_type="coder_review_summary",
            case_id=case.case_id,
            content=content,
            cited_evidence_ids=evidence_ids,
            human_review_required=True,
        )

    def explain_issue(self, case: ASCCase, issue: CodingOpportunity) -> CodingCopilotDraft:
        content = (
            f"Charge-line issue explanation for {case.case_id}: review whether {issue.risk_reason}\n"
            f"Suggested action: {issue.suggested_human_review_action}\n"
            f"Affected charge lines: {', '.join(issue.affected_charge_lines) or 'none recorded'}.\n"
            f"Human review is required before any coding, billing, claim-correction, or payer-facing action.\n"
            f"Evidence reviewed: {', '.join(issue.evidence_citation_ids)}."
        )
        return CodingCopilotDraft(
            draft_type="charge_line_issue_explanation",
            case_id=case.case_id,
            content=content,
            cited_evidence_ids=issue.evidence_citation_ids,
            human_review_required=True,
        )

    def generate_missing_documentation_checklist(
        self,
        case: ASCCase,
        issues: tuple[CodingOpportunity, ...] | None = None,
    ) -> CodingCopilotDraft:
        detected = issues if issues is not None else detect_coding_opportunities(case)
        evidence_ids = _evidence_for_case(case, detected)
        checklist_items = [
            f"- Review whether source documentation addresses {item.coding_issue_type} and capture any missing support (Evidence: {', '.join(item.evidence_citation_ids)})."
            for item in detected
        ] or [
            f"- Review whether the operative note, charge detail, and policy references remain aligned (Evidence: {', '.join(evidence_ids)})."
        ]
        content = (
            "Missing documentation checklist:\n"
            + "\n".join(checklist_items)
            + "\nHuman review is required before any coding, billing, claim-correction, or payer-facing action.\n"
            + f"Evidence reviewed: {', '.join(evidence_ids)}."
        )
        return CodingCopilotDraft(
            draft_type="missing_documentation_checklist",
            case_id=case.case_id,
            content=content,
            cited_evidence_ids=evidence_ids,
            human_review_required=True,
        )

    def generate_corrected_claim_checklist(
        self,
        case: ASCCase,
        issues: tuple[CodingOpportunity, ...] | None = None,
    ) -> CodingCopilotDraft:
        detected = issues if issues is not None else detect_coding_opportunities(case)
        evidence_ids = _evidence_for_case(case, detected)
        checklist_items = [
            f"- Review whether issue {item.coding_issue_type} needs claim-edit preparation and supporting documentation validation (Evidence: {', '.join(item.evidence_citation_ids)})."
            for item in detected
        ] or [
            f"- Review whether any claim-edit checklist is necessary based on the current synthetic evidence set (Evidence: {', '.join(evidence_ids)})."
        ]
        content = (
            "Suggested corrected-claim checklist:\n"
            + "\n".join(checklist_items)
            + "\nThis is not a final code selection or claim correction recommendation; coder should validate all changes for human review.\n"
            + "Human review is required before any coding, billing, claim-correction, or payer-facing action.\n"
            + f"Evidence reviewed: {', '.join(evidence_ids)}."
        )
        return CodingCopilotDraft(
            draft_type="suggested_corrected_claim_checklist",
            case_id=case.case_id,
            content=content,
            cited_evidence_ids=evidence_ids,
            human_review_required=True,
        )

    def build_audit_safe_rationale(self, case: ASCCase, issue: CodingOpportunity) -> CodingCopilotDraft:
        content = (
            f"Audit-safe rationale for {case.case_id}: review whether the deterministic coding detector surfaced a potential {issue.coding_issue_type} because {issue.risk_reason}\n"
            "This rationale is based on synthetic policy and structured case facts only, and coder should validate the source documentation for human review.\n"
            f"Human review is required before any coding, billing, claim-correction, or payer-facing action.\n"
            f"Evidence reviewed: {', '.join(issue.evidence_citation_ids)}."
        )
        return CodingCopilotDraft(
            draft_type="audit_safe_rationale",
            case_id=case.case_id,
            content=content,
            cited_evidence_ids=issue.evidence_citation_ids,
            human_review_required=True,
        )


def _evidence_for_case(case: ASCCase, issues: tuple[CodingOpportunity, ...]) -> tuple[str, ...]:
    ids = [case.encounter.citation.source_id]
    if issues:
        for issue in issues:
            ids.extend(issue.evidence_citation_ids)
    else:
        ids.extend(item.citation.source_id for item in case.procedure_cases)
        ids.extend(item.citation.source_id for item in case.charge_lines)
    return tuple(dict.fromkeys(ids))
