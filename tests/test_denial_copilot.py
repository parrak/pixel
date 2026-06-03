from pathlib import Path

from dataclasses import replace

from asc_rcm_lite.copilot.denial_copilot import DenialCopilot
from asc_rcm_lite.detectors.denials import detect_denial_opportunities
from asc_rcm_lite.ingestion import load_asc_case


def _load_case(name: str):
    return load_asc_case(Path("data/asc_cases") / name)


def test_prior_auth_denial_classified_correctly():
    item = detect_denial_opportunities(_load_case("002_missing_prior_authorization_denial.json"))[0]
    assert item.denial_category == "prior_authorization"


def test_medical_necessity_denial_classified_correctly():
    item = detect_denial_opportunities(_load_case("004_missing_conservative_therapy_medical_necessity.json"))[0]
    assert item.denial_category == "medical_necessity"


def test_modifier_or_bundling_denial_classifies_timely_when_text_says_so():
    case = _load_case("002_missing_prior_authorization_denial.json")
    item = detect_denial_opportunities(case)[0]
    assert item.appealability in {"likely", "uncertain", "unlikely"}


def test_appeal_draft_includes_cited_evidence():
    item = detect_denial_opportunities(_load_case("002_missing_prior_authorization_denial.json"))[0]
    draft = DenialCopilot().appeal_letter_draft(item)
    assert draft.cited_evidence_ids
    assert all(evidence in draft.content for evidence in draft.cited_evidence_ids)


def test_appeal_draft_blocks_unsafe_language():
    item = detect_denial_opportunities(_load_case("002_missing_prior_authorization_denial.json"))[0]
    draft = DenialCopilot().appeal_letter_draft(item)
    lowered = draft.content.lower()
    assert "payer must pay" not in lowered
    assert "guaranteed" not in lowered


def test_denial_detector_returns_empty_when_denial_exists_without_claim():
    case = _load_case("002_missing_prior_authorization_denial.json")
    claimless_case = replace(case, claims=())
    assert detect_denial_opportunities(claimless_case) == ()
