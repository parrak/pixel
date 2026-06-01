from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List

from app.core.models import GraphEdge, GraphEntity, NormalizedChart


ENTITY_TYPES = {
    "note",
    "lab",
    "vital",
    "medication",
    "order",
    "procedure",
    "diagnosis",
    "claim",
    "charge",
    "denial_letter",
    "payer_policy",
    "oxygen",
}


@dataclass
class EncounterGraph:
    chart_id: str
    patient: Dict[str, Any]
    encounter: Dict[str, Any]
    entities: Dict[str, GraphEntity] = field(default_factory=dict)
    edges: List[GraphEdge] = field(default_factory=list)

    def add_entity(self, entity: GraphEntity) -> GraphEntity:
        if entity.entity_type not in ENTITY_TYPES:
            raise ValueError(f"Unsupported graph entity type: {entity.entity_type}")
        self.entities[entity.entity_id] = entity
        return entity

    def add_edge(self, source_entity_id: str, target_entity_id: str, relationship: str) -> None:
        if source_entity_id not in self.entities:
            raise KeyError(f"Unknown source entity: {source_entity_id}")
        if target_entity_id not in self.entities:
            raise KeyError(f"Unknown target entity: {target_entity_id}")
        self.edges.append(GraphEdge(source_entity_id, target_entity_id, relationship))

    def by_type(self, entity_type: str) -> List[GraphEntity]:
        return [entity for entity in self.entities.values() if entity.entity_type == entity_type]

    def timeline(self) -> List[GraphEntity]:
        return sorted(self.entities.values(), key=lambda entity: entity.timestamp)

    def to_json(self) -> Dict[str, Any]:
        return {
            "chart_id": self.chart_id,
            "patient": self.patient,
            "encounter": self.encounter,
            "entities": [entity.to_json() for entity in self.timeline()],
            "edges": [edge.to_json() for edge in self.edges],
        }


def build_encounter_graph(chart: dict) -> EncounterGraph:
    graph = EncounterGraph(
        chart_id=chart["chart_id"],
        patient=chart.get("patient", {}),
        encounter=chart.get("encounter", {}),
    )

    for lab in chart.get("labs", []):
        graph.add_entity(
            GraphEntity(
                entity_id=_entity_id("lab", lab["id"]),
                entity_type="lab",
                timestamp=lab["timestamp"],
                label=f"{lab['name']} {lab['value']} {lab.get('unit', '')}".strip(),
                payload={**lab, "name": lab["name"].lower()},
                source_id=lab["id"],
                source_type="lab",
                excerpt=f"{lab['name']} {lab['value']} {lab.get('unit', '')}".strip(),
            )
        )

    for vital in chart.get("vitals", []):
        for key, value in vital.items():
            if key in {"id", "timestamp"}:
                continue
            graph.add_entity(
                GraphEntity(
                    entity_id=_entity_id("vital", vital["id"], key),
                    entity_type="vital",
                    timestamp=vital["timestamp"],
                    label=f"{key} {value}",
                    payload={"id": vital["id"], "timestamp": vital["timestamp"], "name": key.lower(), "value": value},
                    source_id=vital["id"],
                    source_type="vital",
                    excerpt=f"{key} {value}",
                )
            )

    for oxygen in chart.get("oxygen", []):
        detail = oxygen.get("detail", oxygen.get("device", "oxygen support"))
        graph.add_entity(
            GraphEntity(
                entity_id=_entity_id("oxygen", oxygen["id"]),
                entity_type="oxygen",
                timestamp=oxygen["timestamp"],
                label=detail,
                payload=oxygen,
                source_id=oxygen["id"],
                source_type="oxygen",
                excerpt=detail,
            )
        )

    for med in chart.get("medications", []):
        graph.add_entity(
            GraphEntity(
                entity_id=_entity_id("medication", med["id"]),
                entity_type="medication",
                timestamp=med["timestamp"],
                label=med["name"],
                payload={**med, "name": med["name"].lower()},
                source_id=med["id"],
                source_type="medication",
                excerpt=f"{med['name']} {med.get('route', '')}".strip(),
            )
        )

    for note in chart.get("notes", []):
        graph.add_entity(
            GraphEntity(
                entity_id=_entity_id("note", note["id"]),
                entity_type="note",
                timestamp=note["timestamp"],
                label=note.get("type", "note"),
                payload=note,
                source_id=note["id"],
                source_type=note.get("type", "note"),
                excerpt=note["text"],
            )
        )

    for diagnosis in chart.get("coded_diagnoses", []):
        graph.add_entity(
            GraphEntity(
                entity_id=_entity_id("diagnosis", _slug(diagnosis)),
                entity_type="diagnosis",
                timestamp=chart.get("encounter", {}).get("discharge", ""),
                label=diagnosis,
                payload={"description": diagnosis, "coded": True},
                source_id=_slug(diagnosis),
                source_type="coded_diagnosis",
                excerpt=diagnosis,
            )
        )

    _add_optional_entities(graph, chart.get("orders", []), "order")
    _add_optional_entities(graph, chart.get("procedures", []), "procedure")
    _add_optional_entities(graph, chart.get("claims", []), "claim")
    _add_optional_entities(graph, chart.get("charges", []), "charge")
    _add_optional_entities(graph, chart.get("denial_letters", []), "denial_letter")
    _add_optional_entities(graph, chart.get("payer_policies", []), "payer_policy")
    _link_timeline(graph)

    return graph


def timeline(chart: NormalizedChart) -> Iterable[GraphEntity]:
    graph = chart.encounter_graph
    if graph is None:
        graph = build_encounter_graph(chart.raw)
    return graph.timeline()


def _add_optional_entities(graph: EncounterGraph, rows: list[dict], entity_type: str) -> None:
    for row in rows:
        row_id = str(row.get("id", _slug(str(row))))
        label = str(row.get("name") or row.get("title") or row.get("description") or row_id)
        excerpt = str(row.get("text") or row.get("excerpt") or label)
        graph.add_entity(
            GraphEntity(
                entity_id=_entity_id(entity_type, row_id),
                entity_type=entity_type,
                timestamp=str(row.get("timestamp", "")),
                label=label,
                payload=row,
                source_id=row_id,
                source_type=entity_type,
                excerpt=excerpt,
            )
        )


def _link_timeline(graph: EncounterGraph) -> None:
    entities = graph.timeline()
    for prior, current in zip(entities, entities[1:]):
        graph.add_edge(prior.entity_id, current.entity_id, "next_event")


def _entity_id(entity_type: str, *parts: str) -> str:
    return ":".join([entity_type, *[str(part) for part in parts]])


def _slug(value: str) -> str:
    return "".join(char.lower() if char.isalnum() else "-" for char in value).strip("-")
