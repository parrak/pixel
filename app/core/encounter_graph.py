from __future__ import annotations

from app.core.models import NormalizedChart


def timeline(chart: NormalizedChart):
    return sorted(chart.facts, key=lambda fact: fact.timestamp)

