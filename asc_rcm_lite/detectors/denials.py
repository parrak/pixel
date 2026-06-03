"""Deterministic denial classification for synthetic ASC RCM claims."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from asc_rcm_lite.models import ASCCase, ValidationError, require_non_empty


@dataclass(frozen=True)
class DenialOpportunity:
    denial_id: str
    claim_id: str
    case_id: str
    denial_category: str
    root_cause_hypothesis: str
    appealability: str
    missing_evidence: tuple[str, ...]
    next_best_action: str
    deadline: str | None
    amount_at_risk: Decimal
    evidence_citation_ids: tuple[str, ...]
    recommended_path: str
    human_review_required: bool

    def __post_init__(self) -> None:
        require_non_empty(self.denial_id, "DenialOpportunity.denial_id")
        require_non_empty(self.claim_id, "DenialOpportunity.claim_id")
        require_non_empty(self.case_id, "DenialOpportunity.case_id")
        require_non_empty(self.denial_category, "DenialOpportunity.denial_category")
        require_non_empty(self.root_cause_hypothesis, "DenialOpportunity.root_cause_hypothesis")
        require_non_empty(self.appealability, "DenialOpportunity.appealability")
        require_non_empty(self.next_best_action, "DenialOpportunity.next_best_action")
        require_non_empty(self.recommended_path, "DenialOpportunity.recommended_path")
        if not self.evidence_citation_ids:
            raise ValidationError("DenialOpportunity.evidence_citation_ids must not be empty")
        if not self.human_review_required:
            raise ValidationError("DenialOpportunity.human_review_required must be true")


def detect_denial_opportunities(case: ASCCase) -> tuple[DenialOpportunity, ...]:
    if not case.denials:
        return ()
    claim = case.claims[0]
    work_item = case.work_queue_items[0] if case.work_queue_items else None
    deadline = work_item.due_date if work_item else None
    opportunities = []
    for denial in case.denials:
        category, path, appealability, root = _categorize(case, denial.reason)
        evidence_ids = [
            denial.citation.source_id,
            claim.citation.source_id,
        ]
        if work_item is not None:
            evidence_ids.append(work_item.citation.source_id)
        evidence_ids.extend(item.citation.source_id for item in case.payer_policies)
        evidence_ids.extend(item.citation.source_id for item in case.authorizations)
        evidence_ids.extend(item.citation.source_id for item in case.procedure_cases)
        missing_evidence = _missing_evidence(case, category)
        next_action = _next_action(category, appealability)
        opportunities.append(
            DenialOpportunity(
                denial_id=denial.denial_id,
                claim_id=claim.claim_id,
                case_id=case.case_id,
                denial_category=category,
                root_cause_hypothesis=root,
                appealability=appealability,
                missing_evidence=missing_evidence,
                next_best_action=next_action,
                deadline=deadline,
                amount_at_risk=denial.denied_amount,
                evidence_citation_ids=tuple(dict.fromkeys(evidence_ids)),
                recommended_path=path,
                human_review_required=True,
            )
        )
    return tuple(opportunities)


def _categorize(case: ASCCase, reason: str) -> tuple[str, str, str, str]:
    lowered = reason.lower()
    scenario = case.scenario.lower()
    if "authorization" in lowered or "precertification" in lowered or "auth" in scenario:
        return (
            "prior_authorization",
            "appeal",
            "likely",
            "Potential authorization mismatch or absent authorization support based on synthetic denial evidence.",
        )
    if "medical necessity" in lowered or "conservative therapy" in lowered:
        return (
            "medical_necessity",
            "provider_documentation",
            "uncertain",
            "Potential medical-necessity documentation gap based on synthetic payer policy.",
        )
    if "modifier" in lowered:
        return (
            "coding_modifier",
            "corrected_claim",
            "uncertain",
            "Potential modifier support gap requiring coder review.",
        )
    if "bundled" in lowered:
        return (
            "bundled_service",
            "corrected_claim",
            "uncertain",
            "Potential bundled-service edit requiring documentation review.",
        )
    if "timely filing" in lowered:
        return (
            "timely_filing",
            "writeoff_review",
            "unlikely",
            "Potential missed filing or appeal deadline based on synthetic denial text.",
        )
    return (
        "payer_processing_error",
        "payer_call",
        "uncertain",
        "Potential payer processing issue requiring reviewer validation.",
    )


def _missing_evidence(case: ASCCase, category: str) -> tuple[str, ...]:
    if category == "prior_authorization":
        return ("authorization revision",) if case.authorizations else ("authorization record",)
    if category == "medical_necessity":
        return ("conservative therapy documentation",)
    if category in {"coding_modifier", "bundled_service"}:
        return ("modifier support documentation",)
    if category == "timely_filing":
        return ("filing deadline proof",)
    return ("payer processing notes",)


def _next_action(category: str, appealability: str) -> str:
    if appealability == "unlikely":
        return "Review whether write-off review or manager review is more appropriate than a strong appeal, for human review."
    action_map = {
        "prior_authorization": "Review whether an appeal packet or authorization correction packet can be assembled, for human review.",
        "medical_necessity": "Review whether missing documentation should be obtained before appeal drafting, for human review.",
        "coding_modifier": "Review whether coder validation and corrected-claim preparation are needed, for human review.",
        "bundled_service": "Review whether bundling support exists before any corrected-claim workflow, for human review.",
    }
    return action_map.get(category, "Review whether payer call or additional evidence gathering is needed, for human review.")
