from __future__ import annotations

from app.core.encounter_graph import build_encounter_graph
from app.core.evidence_graph import EvidenceGraph
from app.core.models import Citation, Fact, NormalizedChart


def normalize_chart(chart: dict) -> NormalizedChart:
    facts: list[Fact] = []

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

    encounter_graph = build_encounter_graph(chart)
    normalized = NormalizedChart(
        chart_id=chart["chart_id"],
        patient=chart.get("patient", {}),
        encounter=chart.get("encounter", {}),
        coded_diagnoses=chart.get("coded_diagnoses", []),
        facts=sorted(facts, key=lambda fact: fact.timestamp),
        raw=chart,
        encounter_graph=encounter_graph,
    )
    normalized.evidence_graph = EvidenceGraph(encounter_graph)
    return normalized
