from __future__ import annotations

from app.core.evidence_graph import EvidenceGraph, build_evidence_graph
from app.core.models import NormalizedChart, Opportunity
from app.rules.clinical import aki, respiratory_failure, sepsis


DETECTORS = [aki.detect, sepsis.detect, respiratory_failure.detect]


def analyze_chart(chart: NormalizedChart) -> list[Opportunity]:
    return analyze_evidence_graph(build_evidence_graph(chart))


def analyze_evidence_graph(graph: EvidenceGraph) -> list[Opportunity]:
    opportunities: list[Opportunity] = []
    for detector in DETECTORS:
        opportunities.extend(detector(graph))
    deduped = {opportunity.opportunity_id: opportunity for opportunity in opportunities}
    return sorted(deduped.values(), key=lambda item: item.rank_score, reverse=True)
