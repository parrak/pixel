"""Deterministic coding QA detectors for synthetic ASC RCM cases."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

from asc_rcm_lite.models import ASCCase, ValidationError, require_non_empty


@dataclass(frozen=True)
class CodingOpportunity:
    opportunity_id: str
    case_id: str
    claim_id: str | None
    affected_charge_lines: tuple[str, ...]
    coding_issue_type: str
    severity: str
    risk_reason: str
    evidence_citation_ids: tuple[str, ...]
    suggested_human_review_action: str
    financial_impact_estimate: Decimal | None
    human_review_required: bool
    source: str

    def __post_init__(self) -> None:
        require_non_empty(self.opportunity_id, "CodingOpportunity.opportunity_id")
        require_non_empty(self.case_id, "CodingOpportunity.case_id")
        require_non_empty(self.coding_issue_type, "CodingOpportunity.coding_issue_type")
        require_non_empty(self.severity, "CodingOpportunity.severity")
        require_non_empty(self.risk_reason, "CodingOpportunity.risk_reason")
        require_non_empty(
            self.suggested_human_review_action,
            "CodingOpportunity.suggested_human_review_action",
        )
        require_non_empty(self.source, "CodingOpportunity.source")
        if self.severity not in {"low", "medium", "high", "critical"}:
            raise ValidationError(f"Unsupported coding severity: {self.severity}")
        if not self.evidence_citation_ids:
            raise ValidationError("CodingOpportunity.evidence_citation_ids must not be empty")
        if not self.human_review_required:
            raise ValidationError("CodingOpportunity.human_review_required must be true")


def detect_coding_opportunities(case: ASCCase) -> tuple[CodingOpportunity, ...]:
    opportunities: list[CodingOpportunity] = []
    claim_id = case.claims[0].claim_id if case.claims else None

    opportunities.extend(_detect_missing_facility_charge(case, claim_id))
    opportunities.extend(_detect_site_of_service_mismatch(case, claim_id))
    opportunities.extend(_detect_cpt_op_note_mismatch(case, claim_id))
    opportunities.extend(_detect_laterality_issues(case, claim_id))
    opportunities.extend(_detect_bundled_modifier_risk(case, claim_id))
    opportunities.extend(_detect_missing_implant_charge(case, claim_id))
    opportunities.extend(_detect_documentation_insufficiency(case, claim_id))

    return tuple(opportunities)


def _detect_missing_facility_charge(case: ASCCase, claim_id: str | None) -> list[CodingOpportunity]:
    if case.charge_lines:
        return []
    evidence = [case.encounter.citation.source_id, *[item.citation.source_id for item in case.procedure_cases]]
    return [
        _make_opportunity(
            case=case,
            claim_id=claim_id,
            issue_type="missing_facility_charge",
            severity="critical",
            risk_reason="Potential missing facility charge line for the performed ASC procedure; review whether a synthetic facility charge should be present for human review.",
            evidence_ids=evidence,
            action="Coder should validate whether the case is missing the expected ASC facility charge line before any claim workflow proceeds, for human review.",
            amount=None,
            charge_line_ids=(),
        )
    ]


def _detect_site_of_service_mismatch(case: ASCCase, claim_id: str | None) -> list[CodingOpportunity]:
    if case.encounter.place_of_service == "24":
        return []
    return [
        _make_opportunity(
            case=case,
            claim_id=claim_id,
            issue_type="site_of_service_mismatch",
            severity="high",
            risk_reason="Potential site-of-service mismatch because the encounter is not tagged with ASC POS 24; review whether the synthetic case metadata aligns with the intended ASC workflow for human review.",
            evidence_ids=(case.encounter.citation.source_id,),
            action="Coder should validate whether the site-of-service metadata should be corrected before further billing workflow, for human review.",
            amount=None,
            charge_line_ids=tuple(item.charge_line_id for item in case.charge_lines),
        )
    ]


def _detect_cpt_op_note_mismatch(case: ASCCase, claim_id: str | None) -> list[CodingOpportunity]:
    procedure_codes = {item.cpt_code for item in case.procedure_cases}
    opportunities: list[CodingOpportunity] = []
    for charge_line in case.charge_lines:
        if not charge_line.cpt_code[:1].isdigit():
            continue
        if charge_line.cpt_code in procedure_codes:
            continue
        evidence = (charge_line.citation.source_id, *[item.citation.source_id for item in case.procedure_cases])
        opportunities.append(
            _make_opportunity(
                case=case,
                claim_id=claim_id,
                issue_type="cpt_op_note_mismatch",
                severity="high",
                risk_reason=f"Potential mismatch between charged CPT {charge_line.cpt_code} and documented procedure codes; review whether the op note supports this charge line for human review.",
                evidence_ids=evidence,
                action="Coder should validate whether the documented procedure supports the charged CPT and whether any correction checklist is needed, for human review.",
                amount=charge_line.charge_amount,
                charge_line_ids=(charge_line.charge_line_id,),
            )
        )
    return opportunities


def _detect_laterality_issues(case: ASCCase, claim_id: str | None) -> list[CodingOpportunity]:
    opportunities: list[CodingOpportunity] = []
    procedures_by_cpt = {item.cpt_code: item for item in case.procedure_cases}
    for charge_line in case.charge_lines:
        procedure = procedures_by_cpt.get(charge_line.cpt_code)
        if procedure is None:
            continue
        normalized_laterality = _normalize_laterality(procedure.laterality)
        if normalized_laterality is None:
            continue
        modifiers = set(charge_line.modifiers)
        expected, opposite = normalized_laterality
        evidence = (procedure.citation.source_id, charge_line.citation.source_id)
        if "50" in modifiers:
            continue
        if expected not in modifiers and opposite not in modifiers:
            opportunities.append(
                _make_opportunity(
                    case=case,
                    claim_id=claim_id,
                    issue_type="missing_modifier",
                    severity="high",
                    risk_reason=f"Potential missing laterality modifier for CPT {charge_line.cpt_code}; review whether {expected} should appear on the charge line for human review.",
                    evidence_ids=evidence,
                    action=f"Coder should validate whether the charge line needs laterality modifier {expected} based on the documented procedure, for human review.",
                    amount=charge_line.charge_amount,
                    charge_line_ids=(charge_line.charge_line_id,),
                )
            )
        elif opposite in modifiers:
            opportunities.append(
                _make_opportunity(
                    case=case,
                    claim_id=claim_id,
                    issue_type="laterality_mismatch",
                    severity="critical",
                    risk_reason=f"Potential laterality mismatch because the procedure is documented as {expected} while the charge line carries {opposite}; coder should validate before any correction workflow for human review.",
                    evidence_ids=evidence,
                    action="Coder should validate the laterality on the procedure note and charge line and document the correction checklist for human review.",
                    amount=charge_line.charge_amount,
                    charge_line_ids=(charge_line.charge_line_id,),
                )
            )
    return opportunities


def _normalize_laterality(laterality: str) -> tuple[str, str] | None:
    normalized = laterality.strip().upper()
    if normalized in {"RT", "RIGHT"}:
        return ("RT", "LT")
    if normalized in {"LT", "LEFT"}:
        return ("LT", "RT")
    if normalized in {"BIL", "BILATERAL", "BL"}:
        return None
    return None


def _detect_bundled_modifier_risk(case: ASCCase, claim_id: str | None) -> list[CodingOpportunity]:
    opportunities: list[CodingOpportunity] = []
    bundling_policies = [policy for policy in case.payer_policies if policy.policy_type == "bundling"]
    if not bundling_policies:
        return opportunities
    policy = bundling_policies[0]
    for charge_line in case.charge_lines:
        modifiers = set(charge_line.modifiers)
        if "59" not in modifiers and "XS" not in modifiers:
            continue
        if charge_line.cpt_code != policy.cpt_code:
            continue
        evidence = (charge_line.citation.source_id, policy.citation.source_id)
        if len(case.procedure_cases) > 1:
            evidence = evidence + tuple(item.citation.source_id for item in case.procedure_cases)
        opportunities.append(
            _make_opportunity(
                case=case,
                claim_id=claim_id,
                issue_type="bundled_procedure_risk",
                severity="high",
                risk_reason=f"Potential bundled procedure risk because modifier review is needed for CPT {charge_line.cpt_code} based on synthetic policy guidance; coder should validate whether separate-site documentation exists for human review.",
                evidence_ids=evidence,
                action="Coder should validate whether modifier 59 or XS is supported by separate-site documentation before claim release, for human review.",
                amount=policy.contract_allowed_amount,
                charge_line_ids=(charge_line.charge_line_id,),
            )
        )
    return opportunities


def _detect_missing_implant_charge(case: ASCCase, claim_id: str | None) -> list[CodingOpportunity]:
    implant_opportunities = [
        item
        for item in case.opportunities
        if "implant" in item.description.lower() or "implant" in item.opportunity_type.lower()
    ]
    if not implant_opportunities:
        return []
    has_implant_charge = any(
        charge_line.cpt_code.startswith("L") or "implant" in charge_line.description.lower()
        for charge_line in case.charge_lines
    )
    if has_implant_charge:
        return []
    policy = next((item for item in case.payer_policies if item.cpt_code.startswith("L")), None)
    evidence_ids = [implant_opportunities[0].citation.source_id]
    if policy is not None:
        evidence_ids.append(policy.citation.source_id)
    evidence_ids.extend(item.citation.source_id for item in case.procedure_cases)
    return [
        _make_opportunity(
            case=case,
            claim_id=claim_id,
            issue_type="missing_implant_supply_charge",
            severity="critical",
            risk_reason="Potential missing implant or supply charge because the synthetic case evidence references an implant but no separate implant HCPCS charge line is present; review whether the charge capture is incomplete for human review.",
            evidence_ids=evidence_ids,
            action="Coder should validate the implant log, invoice support, and charge capture checklist before any claim release, for human review.",
            amount=policy.contract_allowed_amount if policy is not None else implant_opportunities[0].estimated_value,
            charge_line_ids=tuple(item.charge_line_id for item in case.charge_lines),
        )
    ]


def _detect_documentation_insufficiency(case: ASCCase, claim_id: str | None) -> list[CodingOpportunity]:
    opportunities: list[CodingOpportunity] = []
    policy = next((item for item in case.payer_policies if item.policy_type == "medical_necessity"), None)
    if policy is None:
        return opportunities
    related_denial = next(
        (
            item
            for item in case.denials
            if "documentation" in item.reason.lower() or "medical necessity" in item.reason.lower()
        ),
        None,
    )
    evidence = [policy.citation.source_id]
    if related_denial is not None:
        evidence.append(related_denial.citation.source_id)
    evidence.extend(item.citation.source_id for item in case.procedure_cases)
    opportunities.append(
        _make_opportunity(
            case=case,
            claim_id=claim_id,
            issue_type="documentation_missing_medical_necessity",
            severity="high",
            risk_reason=f"Potential documentation insufficiency based on synthetic policy requiring '{policy.requirement}'; coder should validate whether source documentation supports the billed service for human review.",
            evidence_ids=evidence,
            action="Coder should validate whether the case includes the required medical-necessity support and build a missing-document checklist for human review.",
            amount=policy.contract_allowed_amount,
            charge_line_ids=tuple(item.charge_line_id for item in case.charge_lines),
        )
    )
    return opportunities


def _make_opportunity(
    *,
    case: ASCCase,
    claim_id: str | None,
    issue_type: str,
    severity: str,
    risk_reason: str,
    evidence_ids: Iterable[str],
    action: str,
    amount: Decimal | None,
    charge_line_ids: tuple[str, ...],
) -> CodingOpportunity:
    deduped_evidence = tuple(dict.fromkeys(evidence_ids))
    return CodingOpportunity(
        opportunity_id=f"{case.case_id}-{issue_type}",
        case_id=case.case_id,
        claim_id=claim_id,
        affected_charge_lines=charge_line_ids,
        coding_issue_type=issue_type,
        severity=severity,
        risk_reason=risk_reason,
        evidence_citation_ids=deduped_evidence,
        suggested_human_review_action=action,
        financial_impact_estimate=amount,
        human_review_required=True,
        source="coding_detector",
    )
