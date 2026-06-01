from __future__ import annotations

from smarterdx_lite.detectors import aki, respiratory_failure, sepsis
from smarterdx_lite.models import NormalizedChart, Opportunity


DETECTORS = [aki.detect, sepsis.detect, respiratory_failure.detect]


def analyze_chart(chart: NormalizedChart) -> list[Opportunity]:
    opportunities: list[Opportunity] = []
    for detector in DETECTORS:
        opportunities.extend(detector(chart))
    deduped = {opportunity.opportunity_id: opportunity for opportunity in opportunities}
    return sorted(deduped.values(), key=lambda item: item.rank_score, reverse=True)

