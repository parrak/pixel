from __future__ import annotations

from pathlib import Path
from typing import Iterable

from app.core.ingest import load_charts
from app.core.terminology import count_unsupported_assertions
from app.evals.assertions import query_is_safe
from app.workflows.prebill.detector import analyze_chart
from app.workflows.prebill.packet import packet_is_complete, render_reviewer_packet


def _families(items: Iterable[str]) -> set[str]:
    return {item.lower() for item in items}


def run_prebill_eval(chart_dir: Path = Path("data/synthetic_charts")) -> dict:
    charts = load_charts(chart_dir)
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
            if query_is_safe(opportunity.query):
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

