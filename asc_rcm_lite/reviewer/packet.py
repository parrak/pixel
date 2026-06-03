"""Unified ASC RCM reviewer packets."""

from __future__ import annotations

from dataclasses import dataclass

from asc_rcm_lite.detectors.ar import ARFlag
from asc_rcm_lite.detectors.coding import CodingOpportunity
from asc_rcm_lite.detectors.denials import DenialOpportunity
from asc_rcm_lite.models import ValidationError, require_non_empty


@dataclass(frozen=True)
class ReviewerPacket:
    packet_id: str
    case_id: str
    claim_id: str | None
    work_item_id: str | None
    opportunity_summary: str
    claim_summary: str
    payer_context: str
    evidence_table: tuple[str, ...]
    financial_impact_estimate: str
    root_cause_hypothesis: str
    recommended_next_action: str
    human_review_checklist: tuple[str, ...]
    audit_trace: tuple[str, ...]
    human_review_required: bool

    def __post_init__(self) -> None:
        require_non_empty(self.packet_id, "ReviewerPacket.packet_id")
        require_non_empty(self.case_id, "ReviewerPacket.case_id")
        require_non_empty(self.opportunity_summary, "ReviewerPacket.opportunity_summary")
        require_non_empty(self.claim_summary, "ReviewerPacket.claim_summary")
        require_non_empty(self.payer_context, "ReviewerPacket.payer_context")
        require_non_empty(self.financial_impact_estimate, "ReviewerPacket.financial_impact_estimate")
        require_non_empty(self.root_cause_hypothesis, "ReviewerPacket.root_cause_hypothesis")
        require_non_empty(self.recommended_next_action, "ReviewerPacket.recommended_next_action")
        if not self.evidence_table:
            raise ValidationError("ReviewerPacket.evidence_table must not be empty")
        if not self.human_review_checklist:
            raise ValidationError("ReviewerPacket.human_review_checklist must not be empty")
        if not self.human_review_required:
            raise ValidationError("ReviewerPacket.human_review_required must be true")


def render_packet_for_coding(opportunity: CodingOpportunity) -> ReviewerPacket:
    return ReviewerPacket(
        packet_id=f"PKT-{opportunity.opportunity_id}",
        case_id=opportunity.case_id,
        claim_id=opportunity.claim_id,
        work_item_id=opportunity.opportunity_id,
        opportunity_summary=opportunity.risk_reason,
        claim_summary=f"Coding issue {opportunity.coding_issue_type} for case {opportunity.case_id}",
        payer_context="Synthetic coding review context",
        evidence_table=tuple(f"Evidence: {item}" for item in opportunity.evidence_citation_ids),
        financial_impact_estimate=str(opportunity.financial_impact_estimate) if opportunity.financial_impact_estimate is not None else "unknown",
        root_cause_hypothesis=opportunity.risk_reason,
        recommended_next_action=opportunity.suggested_human_review_action,
        human_review_checklist=(
            "Review charge-line evidence",
            "Review operative note support",
            "Confirm synthetic policy context",
        ),
        audit_trace=("coding_detector", "human_review_required"),
        human_review_required=True,
    )


def render_packet_for_ar(flag: ARFlag) -> ReviewerPacket:
    return ReviewerPacket(
        packet_id=f"PKT-{flag.flag_id}",
        case_id=flag.case_id,
        claim_id=flag.claim_id,
        work_item_id=flag.flag_id,
        opportunity_summary=flag.reason_for_flag,
        claim_summary=f"A/R aging {flag.aging_bucket}, balance {flag.balance}",
        payer_context=f"Synthetic payer {flag.payer}",
        evidence_table=tuple(f"Evidence: {item}" for item in flag.evidence_citation_ids),
        financial_impact_estimate=str(flag.balance),
        root_cause_hypothesis=flag.reason_for_flag,
        recommended_next_action=flag.recommended_next_action,
        human_review_checklist=("Review aging evidence", "Review balance evidence", "Validate next deadline"),
        audit_trace=("ar_detector", "priority_scoring"),
        human_review_required=True,
    )


def render_packet_for_denial(opportunity: DenialOpportunity) -> ReviewerPacket:
    return ReviewerPacket(
        packet_id=f"PKT-{opportunity.denial_id}",
        case_id=opportunity.case_id,
        claim_id=opportunity.claim_id,
        work_item_id=opportunity.denial_id,
        opportunity_summary=f"Denial {opportunity.denial_category}",
        claim_summary=f"Denial amount at risk {opportunity.amount_at_risk}",
        payer_context=f"Synthetic denial path {opportunity.recommended_path}",
        evidence_table=tuple(f"Evidence: {item}" for item in opportunity.evidence_citation_ids),
        financial_impact_estimate=str(opportunity.amount_at_risk),
        root_cause_hypothesis=opportunity.root_cause_hypothesis,
        recommended_next_action=opportunity.next_best_action,
        human_review_checklist=("Review denial reason", "Review policy citation", "Review missing evidence"),
        audit_trace=("denial_detector", "human_review_required"),
        human_review_required=True,
    )


def packet_is_complete(packet: ReviewerPacket) -> bool:
    return (
        packet.human_review_required
        and bool(packet.evidence_table)
        and bool(packet.human_review_checklist)
        and bool(packet.audit_trace)
    )
