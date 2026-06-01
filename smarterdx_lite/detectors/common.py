from __future__ import annotations

from typing import Iterable, List, Optional

from smarterdx_lite.models import EvidenceItem, Fact, NormalizedChart
from smarterdx_lite.text import contains_any


def note_evidence(chart: NormalizedChart, criterion: str, terms: Iterable[str]) -> Optional[EvidenceItem]:
    for fact in chart.facts:
        if fact.kind == "note" and contains_any(str(fact.value), terms):
            return EvidenceItem(criterion, fact.citation)
    return None


def lab_values(chart: NormalizedChart, name: str) -> List[Fact]:
    return [fact for fact in chart.facts if fact.kind == "lab" and fact.name == name.lower()]


def vital_values(chart: NormalizedChart, name: str) -> List[Fact]:
    return [fact for fact in chart.facts if fact.kind == "vital" and fact.name == name.lower()]


def medication_evidence(chart: NormalizedChart, terms: Iterable[str]) -> Optional[EvidenceItem]:
    for fact in chart.facts:
        if fact.kind == "medication" and contains_any(fact.name, terms):
            return EvidenceItem("anti-infective therapy documented", fact.citation)
    return None

