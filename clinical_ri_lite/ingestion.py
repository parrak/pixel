from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List

from clinical_ri_lite.models import Citation, Fact, NormalizedChart


def load_chart(path: Path) -> NormalizedChart:
    with path.open() as f:
        chart = json.load(f)
    return normalize_chart(chart)


def load_charts(directory: Path) -> List[NormalizedChart]:
    return [load_chart(path) for path in sorted(directory.glob("*.json"))]


def normalize_chart(chart: dict) -> NormalizedChart:
    facts: List[Fact] = []

    for lab in chart.get("labs", []):
        citation = Citation(
            source_id=lab["id"],
            source_type="lab",
            timestamp=lab["timestamp"],
            label=f"{lab['name']} {lab['value']} {lab.get('unit', '')}".strip(),
            excerpt=f"{lab['name']} {lab['value']} {lab.get('unit', '')}".strip(),
        )
        facts.append(Fact("lab", lab["name"].lower(), lab["value"], lab.get("unit", ""), lab["timestamp"], citation))

    for vital in chart.get("vitals", []):
        for key, value in vital.items():
            if key in {"id", "timestamp"}:
                continue
            citation = Citation(
                source_id=vital["id"],
                source_type="vital",
                timestamp=vital["timestamp"],
                label=f"{key} {value}",
                excerpt=f"{key} {value}",
            )
            facts.append(Fact("vital", key.lower(), value, "", vital["timestamp"], citation))

    for oxygen in chart.get("oxygen", []):
        detail = oxygen.get("detail", oxygen.get("device", "oxygen support"))
        citation = Citation(
            source_id=oxygen["id"],
            source_type="oxygen",
            timestamp=oxygen["timestamp"],
            label=detail,
            excerpt=detail,
        )
        facts.append(Fact("oxygen", oxygen.get("device", "oxygen").lower(), oxygen, "", oxygen["timestamp"], citation))

    for med in chart.get("medications", []):
        citation = Citation(
            source_id=med["id"],
            source_type="medication",
            timestamp=med["timestamp"],
            label=med["name"],
            excerpt=f"{med['name']} {med.get('route', '')}".strip(),
        )
        facts.append(Fact("medication", med["name"].lower(), med, "", med["timestamp"], citation))

    for note in chart.get("notes", []):
        citation = Citation(
            source_id=note["id"],
            source_type=note.get("type", "note"),
            timestamp=note["timestamp"],
            label=note.get("type", "note"),
            excerpt=note["text"],
        )
        facts.append(Fact("note", note.get("type", "note").lower(), note["text"], "", note["timestamp"], citation))

    return NormalizedChart(
        chart_id=chart["chart_id"],
        patient=chart.get("patient", {}),
        encounter=chart.get("encounter", {}),
        coded_diagnoses=chart.get("coded_diagnoses", []),
        facts=sorted(facts, key=lambda fact: fact.timestamp),
        raw=chart,
    )


def facts_by_name(chart: NormalizedChart, kind: str, name: str) -> Iterable[Fact]:
    target = name.lower()
    return (fact for fact in chart.facts if fact.kind == kind and fact.name == target)

