from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from smarterdx_lite.ingestion import load_charts
from smarterdx_lite.pipeline import analyze_chart
from smarterdx_lite.reviewer.packet import packet_is_complete, render_reviewer_packet
from smarterdx_lite.text import count_unsupported_assertions


CHART_DIR = ROOT / "data" / "charts"


def _families(items: Iterable[str]) -> set[str]:
    return {item.lower() for item in items}


def run_eval() -> dict:
    charts = load_charts(CHART_DIR)
    expected_total = 0
    true_positive = 0
    false_positive = 0
    emitted_total = 0
    citation_complete = 0
    unsupported_assertions = 0
    query_safe = 0
    packet_complete = 0

    for chart in charts:
        expected = _families(chart.raw.get("gold_opportunities", []))
        opportunities = analyze_chart(chart)
        emitted = _families(opportunity.diagnosis_family for opportunity in opportunities)
        expected_total += len(expected)
        emitted_total += len(opportunities)
        true_positive += len(expected & emitted)
        false_positive += len(emitted - expected)

        for opportunity in opportunities:
            if opportunity.has_evidence():
                citation_complete += 1
            packet = render_reviewer_packet(chart, opportunity)
            unsupported_assertions += count_unsupported_assertions(packet)
            if _query_is_safe(opportunity.query):
                query_safe += 1
            if packet_is_complete(packet):
                packet_complete += 1

    return {
        "charts": len(charts),
        "opportunities_expected": expected_total,
        "opportunities_emitted": emitted_total,
        "opportunity_recall": true_positive / expected_total if expected_total else 1.0,
        "false_positive_rate": false_positive / emitted_total if emitted_total else 0.0,
        "evidence_citation_completeness": citation_complete / emitted_total if emitted_total else 1.0,
        "unsupported_assertion_count": unsupported_assertions,
        "provider_query_safety_pass_rate": query_safe / emitted_total if emitted_total else 1.0,
        "reviewer_packet_completeness": packet_complete / emitted_total if emitted_total else 1.0,
    }


def _query_is_safe(query: str) -> bool:
    lowered = query.lower()
    banned = ["please document", "patient has", "diagnose", "meets criteria", "confirm"]
    return "if clinically appropriate" in lowered and not any(term in lowered for term in banned)


if __name__ == "__main__":
    print(json.dumps(run_eval(), indent=2, sort_keys=True))
