from __future__ import annotations

from pathlib import Path

from app.core.ingest import load_charts
from app.workflows.prebill.detector import analyze_chart


def analyze_synthetic_charts(chart_dir: Path = Path("data/synthetic_charts")) -> dict[str, int]:
    charts = load_charts(chart_dir)
    opportunities = sum(len(analyze_chart(chart)) for chart in charts)
    return {"charts": len(charts), "opportunities": opportunities}


if __name__ == "__main__":
    print(analyze_synthetic_charts())

