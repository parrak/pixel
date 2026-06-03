from pathlib import Path

from asc_rcm_lite.detectors.ar import detect_ar_flags
from asc_rcm_lite.detectors.coding import detect_coding_opportunities
from asc_rcm_lite.detectors.denials import detect_denial_opportunities
from asc_rcm_lite.ingestion import load_asc_case
from asc_rcm_lite.reviewer.drafts import validate_draft_text
from asc_rcm_lite.reviewer.packet import packet_is_complete, render_packet_for_ar, render_packet_for_coding, render_packet_for_denial


def _load_case(name: str):
    return load_asc_case(Path("data/asc_cases") / name)


def test_packet_completeness():
    packet = render_packet_for_ar(detect_ar_flags(_load_case("008_high_value_120_day_ar_followup.json"), as_of_date="2026-06-03")[0])
    assert packet_is_complete(packet)


def test_coding_packet_includes_charge_line_evidence():
    packet = render_packet_for_coding(detect_coding_opportunities(_load_case("005_modifier_59_bundled_risk.json"))[0])
    assert any("SRC-005" in item for item in packet.evidence_table)


def test_appeal_packet_includes_denial_reason_and_policy_citation():
    packet = render_packet_for_denial(detect_denial_opportunities(_load_case("002_missing_prior_authorization_denial.json"))[0])
    assert any("SRC-002-835" in item for item in packet.evidence_table)
    assert any("SRC-002-POLICY" in item for item in packet.evidence_table)


def test_ar_packet_includes_aging_and_balance_evidence():
    packet = render_packet_for_ar(detect_ar_flags(_load_case("008_high_value_120_day_ar_followup.json"), as_of_date="2026-06-03")[0])
    assert "balance" in packet.claim_summary.lower()


def test_unsafe_definitive_language_is_rejected():
    try:
        validate_draft_text("payer must pay this claim for reviewer validation. Human review is required. Evidence: SRC-1", ("SRC-1",))
    except Exception as exc:
        assert "Unsafe definitive language" in str(exc)
    else:
        raise AssertionError("Expected validation error")

