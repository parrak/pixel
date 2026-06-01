from pathlib import Path

from app.core.ingest import load_charts


def test_corpus_has_required_shape():
    charts = load_charts(Path("data/synthetic_charts"))
    assert len(charts) >= 10
    assert sum(1 for chart in charts if not chart.raw.get("gold_opportunities")) >= 3
    assert all(chart.patient.get("synthetic") is True for chart in charts)
    assert all(chart.facts for chart in charts)
