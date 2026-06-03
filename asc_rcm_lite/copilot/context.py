"""Structured context builders for ASC RCM copilot tasks."""

from __future__ import annotations

from typing import Any

from asc_rcm_lite.models import ASCCase


def build_case_context(
    case: ASCCase,
    *,
    question: str | None = None,
    opportunity_id: str | None = None,
) -> dict[str, Any]:
    selected_opportunity = next(
        (opportunity for opportunity in case.opportunities if opportunity.opportunity_id == opportunity_id),
        case.opportunities[0] if case.opportunities else None,
    )
    active_claim = case.claims[0] if case.claims else None
    denial = case.denials[0] if case.denials else None
    work_item = case.work_queue_items[0] if case.work_queue_items else None
    authorization = case.authorizations[0] if case.authorizations else None
    policy = case.payer_policies[0] if case.payer_policies else None

    evidence_map = {
        case.encounter.citation.source_id: case.encounter.citation.reference,
        **{item.citation.source_id: item.citation.reference for item in case.procedure_cases},
        **{item.citation.source_id: item.citation.reference for item in case.charge_lines},
        **{item.citation.source_id: item.citation.reference for item in case.claims},
        **{item.citation.source_id: item.citation.reference for item in case.authorizations},
        **{item.citation.source_id: item.citation.reference for item in case.payer_policies},
        **{item.citation.source_id: item.citation.reference for item in case.denials},
        **{item.citation.source_id: item.citation.reference for item in case.remits},
        **{item.citation.source_id: item.citation.reference for item in case.opportunities},
        **{item.citation.source_id: item.citation.reference for item in case.work_queue_items},
    }

    return {
        "case_id": case.case_id,
        "scenario": case.scenario,
        "question": question or "",
        "encounter": {
            "encounter_id": case.encounter.encounter_id,
            "service_date": case.encounter.service_date,
            "specialty": case.encounter.specialty,
            "place_of_service": case.encounter.place_of_service,
            "primary_diagnosis_code": case.encounter.primary_diagnosis_code,
            "evidence_id": case.encounter.citation.source_id,
        },
        "procedures": [
            {
                "procedure_case_id": item.procedure_case_id,
                "cpt_code": item.cpt_code,
                "description": item.description,
                "laterality": item.laterality,
                "status": item.status,
                "evidence_id": item.citation.source_id,
            }
            for item in case.procedure_cases
        ],
        "charges": [
            {
                "charge_line_id": item.charge_line_id,
                "cpt_code": item.cpt_code,
                "revenue_code": item.revenue_code,
                "units": item.units,
                "charge_amount": str(item.charge_amount),
                "modifiers": list(item.modifiers),
                "description": item.description,
                "evidence_id": item.citation.source_id,
            }
            for item in case.charge_lines
        ],
        "claims": [
            {
                "claim_id": item.claim_id,
                "payer_id": item.payer_id,
                "billed_amount": str(item.billed_amount),
                "status": item.status,
                "submitted_date": item.submitted_date or "",
                "charge_line_ids": list(item.charge_line_ids),
                "evidence_id": item.citation.source_id,
            }
            for item in case.claims
        ],
        "denials": [
            {
                "denial_id": item.denial_id,
                "claim_id": item.claim_id,
                "denial_code": item.denial_code,
                "reason": item.reason,
                "denied_amount": str(item.denied_amount),
                "evidence_id": item.citation.source_id,
            }
            for item in case.denials
        ],
        "authorizations": [
            {
                "authorization_id": item.authorization_id,
                "status": item.status,
                "authorized_cpt_codes": list(item.authorized_cpt_codes),
                "valid_from": item.valid_from or "",
                "valid_to": item.valid_to or "",
                "evidence_id": item.citation.source_id,
            }
            for item in case.authorizations
        ],
        "payer_policies": [
            {
                "payer_policy_id": item.payer_policy_id,
                "policy_type": item.policy_type,
                "cpt_code": item.cpt_code,
                "requirement": item.requirement,
                "contract_allowed_amount": (
                    str(item.contract_allowed_amount) if item.contract_allowed_amount is not None else ""
                ),
                "evidence_id": item.citation.source_id,
            }
            for item in case.payer_policies
        ],
        "opportunities": [
            {
                "opportunity_id": item.opportunity_id,
                "opportunity_type": item.opportunity_type,
                "description": item.description,
                "estimated_value": str(item.estimated_value),
                "priority": item.priority,
                "evidence_id": item.citation.source_id,
            }
            for item in case.opportunities
        ],
        "work_queue_items": [
            {
                "work_queue_item_id": item.work_queue_item_id,
                "queue": item.queue,
                "reason": item.reason,
                "status": item.status,
                "due_date": item.due_date or "",
                "evidence_id": item.citation.source_id,
            }
            for item in case.work_queue_items
        ],
        "selected_opportunity": (
            {
                "opportunity_id": selected_opportunity.opportunity_id,
                "opportunity_type": selected_opportunity.opportunity_type,
                "description": selected_opportunity.description,
                "estimated_value": str(selected_opportunity.estimated_value),
                "priority": selected_opportunity.priority,
                "evidence_id": selected_opportunity.citation.source_id,
            }
            if selected_opportunity is not None
            else None
        ),
        "active_claim": (
            {
                "claim_id": active_claim.claim_id,
                "payer_id": active_claim.payer_id,
                "status": active_claim.status,
                "submitted_date": active_claim.submitted_date or "",
                "billed_amount": str(active_claim.billed_amount),
                "evidence_id": active_claim.citation.source_id,
            }
            if active_claim is not None
            else None
        ),
        "active_denial": (
            {
                "denial_id": denial.denial_id,
                "denial_code": denial.denial_code,
                "reason": denial.reason,
                "denied_amount": str(denial.denied_amount),
                "evidence_id": denial.citation.source_id,
            }
            if denial is not None
            else None
        ),
        "active_work_queue_item": (
            {
                "work_queue_item_id": work_item.work_queue_item_id,
                "queue": work_item.queue,
                "reason": work_item.reason,
                "status": work_item.status,
                "due_date": work_item.due_date or "",
                "evidence_id": work_item.citation.source_id,
            }
            if work_item is not None
            else None
        ),
        "active_authorization": (
            {
                "authorization_id": authorization.authorization_id,
                "status": authorization.status,
                "authorized_cpt_codes": list(authorization.authorized_cpt_codes),
                "evidence_id": authorization.citation.source_id,
            }
            if authorization is not None
            else None
        ),
        "active_policy": (
            {
                "payer_policy_id": policy.payer_policy_id,
                "policy_type": policy.policy_type,
                "cpt_code": policy.cpt_code,
                "requirement": policy.requirement,
                "contract_allowed_amount": (
                    str(policy.contract_allowed_amount) if policy.contract_allowed_amount is not None else ""
                ),
                "evidence_id": policy.citation.source_id,
            }
            if policy is not None
            else None
        ),
        "evidence_index": evidence_map,
    }
