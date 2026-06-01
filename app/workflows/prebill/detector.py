from __future__ import annotations

from app.core.models import NormalizedChart, Opportunity
from app.rules.clinical import aki, respiratory_failure, sepsis


DETECTORS = [aki.detect, sepsis.detect, respiratory_failure.detect]


def analyze_chart(chart: NormalizedChart) -> list[Opportunity]:
    opportunities: list[Opportunity] = []
    for detector in DETECTORS:
        opportunities.extend(detector(chart))
    deduped = {opportunity.opportunity_id: opportunity for opportunity in opportunities}
    return sorted(deduped.values(), key=lambda item: item.rank_score, reverse=True)
