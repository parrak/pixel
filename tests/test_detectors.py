from pathlib import Path

from smarterdx_lite.ingestion import load_chart, load_charts
from smarterdx_lite.pipeline import analyze_chart


def families(chart_id: str) -> set[str]:
    chart = load_chart(Path(f"data/charts/{chart_id}.json"))
    return {opportunity.diagnosis_family for opportunity in analyze_chart(chart)}


def test_aki_detector_finds_first_positive():
    assert "AKI" in families("sdx004")


def test_all_detectors_match_gold_labels():
    for chart in load_charts(Path("data/charts")):
        expected = set(chart.raw.get("gold_opportunities", []))
        found = {opportunity.diagnosis_family for opportunity in analyze_chart(chart)}
        assert found == expected, chart.chart_id


def test_no_opportunity_without_evidence():
    for chart in load_charts(Path("data/charts")):
        for opportunity in analyze_chart(chart):
            assert opportunity.has_evidence()

