from dataclasses import replace
from decimal import Decimal
from pathlib import Path

from asc_rcm_lite.copilot.coding_copilot import CodingCopilot
from asc_rcm_lite.detectors.coding import detect_coding_opportunities
from asc_rcm_lite.ingestion import load_asc_case


def _load_case(name: str):
    return load_asc_case(Path("data/asc_cases") / name)


def _issue_types(case_name: str) -> set[str]:
    return {item.coding_issue_type for item in detect_coding_opportunities(_load_case(case_name))}


def test_missing_modifier_case_is_flagged():
    case = _load_case("001_clean_paid_orthopedic_arthroscopy.json")
    missing_modifier_case = replace(
        case,
        charge_lines=(
            replace(case.charge_lines[0], modifiers=()),
        ),
    )

    issue_types = {item.coding_issue_type for item in detect_coding_opportunities(missing_modifier_case)}

    assert "missing_modifier" in issue_types


def test_bundled_procedure_risk_is_flagged():
    assert "bundled_procedure_risk" in _issue_types("005_modifier_59_bundled_risk.json")


def test_implant_supply_missing_charge_is_flagged():
    assert "missing_implant_supply_charge" in _issue_types("006_implant_supply_charge_capture_miss.json")


def test_documentation_insufficiency_is_flagged():
    assert "documentation_missing_medical_necessity" in _issue_types(
        "004_missing_conservative_therapy_medical_necessity.json"
    )


def test_laterality_mismatch_is_flagged_if_synthetic_case_supports_it():
    case = _load_case("001_clean_paid_orthopedic_arthroscopy.json")
    mismatch_case = replace(
        case,
        charge_lines=(
            replace(case.charge_lines[0], modifiers=("LT",)),
        ),
    )

    issue_types = {item.coding_issue_type for item in detect_coding_opportunities(mismatch_case)}

    assert "laterality_mismatch" in issue_types


def test_clean_claim_has_no_coding_opportunity():
    assert detect_coding_opportunities(_load_case("001_clean_paid_orthopedic_arthroscopy.json")) == ()


def test_every_coding_opportunity_has_citations():
    issues = detect_coding_opportunities(_load_case("005_modifier_59_bundled_risk.json"))

    assert issues
    assert all(item.evidence_citation_ids for item in issues)


def test_coding_copilot_draft_includes_human_review_language():
    case = _load_case("005_modifier_59_bundled_risk.json")
    draft = CodingCopilot().summarize_case(case)

    assert "Human review is required" in draft.content


def test_coding_copilot_draft_does_not_include_forbidden_definitive_language():
    case = _load_case("005_modifier_59_bundled_risk.json")
    draft = CodingCopilot().summarize_case(case)

    lowered = draft.content.lower()
    assert "must code" not in lowered
    assert "definitely incorrect" not in lowered
    assert "guaranteed denial" not in lowered
    assert "compliant code" not in lowered
    assert "payer must pay" not in lowered


def test_no_phi_like_fields_appear_in_coding_outputs():
    case = _load_case("006_implant_supply_charge_capture_miss.json")
    issue = detect_coding_opportunities(case)[0]
    draft = CodingCopilot().explain_issue(case, issue)

    output = {
        "opportunity_id": issue.opportunity_id,
        "case_id": issue.case_id,
        "claim_id": issue.claim_id,
        "affected_charge_lines": list(issue.affected_charge_lines),
        "coding_issue_type": issue.coding_issue_type,
        "severity": issue.severity,
        "risk_reason": issue.risk_reason,
        "evidence_citation_ids": list(issue.evidence_citation_ids),
        "suggested_human_review_action": issue.suggested_human_review_action,
        "financial_impact_estimate": (
            str(issue.financial_impact_estimate)
            if isinstance(issue.financial_impact_estimate, Decimal)
            else None
        ),
        "human_review_required": issue.human_review_required,
        "source": issue.source,
        "draft_content": draft.content,
    }

    forbidden = {
        "name",
        "first_name",
        "last_name",
        "email",
        "phone",
        "address",
        "dob",
        "mrn",
        "ssn",
    }
    assert forbidden.isdisjoint(output.keys())
