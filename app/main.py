from __future__ import annotations

from pathlib import Path

from app.core.ingest import load_charts
from app.workflows.prebill.agent import run_prebill_agent


def analyze_synthetic_charts(chart_dir: Path = Path("data/synthetic_charts")) -> dict[str, int]:
    charts = load_charts(chart_dir)
    actions = sum(len(run_prebill_agent(chart.evidence_graph)) for chart in charts)
    return {"charts": len(charts), "reviewer_actions": actions}


if __name__ == "__main__":
    print(analyze_synthetic_charts())
