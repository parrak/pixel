from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional

from app.core.encounter_graph import EncounterGraph
from app.core.models import EvidenceItem, EvidenceLink, GraphEntity, NormalizedChart
from app.core.terminology import contains_any


@dataclass
class EvidenceGraph:
    encounter_graph: EncounterGraph
    clusters: Dict[str, List[EvidenceItem]] = field(default_factory=dict)

    @property
    def chart_id(self) -> str:
        return self.encounter_graph.chart_id

    @property
    def coded_diagnoses(self) -> List[str]:
        return [entity.label for entity in self.encounter_graph.by_type("diagnosis")]

    def coded_contains(self, terms: List[str]) -> bool:
        coded = " | ".join(self.coded_diagnoses).lower()
        return any(term.lower() in coded for term in terms)

    def entities(self, entity_type: str, name: Optional[str] = None) -> List[GraphEntity]:
        entities = self.encounter_graph.by_type(entity_type)
        if name is None:
            return entities
        target = name.lower()
        return [entity for entity in entities if str(entity.payload.get("name", entity.label)).lower() == target]

    def make_item(self, criterion: str, entity: GraphEntity, value: Optional[str] = None, relationship: str = "supports") -> EvidenceItem:
        link = EvidenceLink(entity_id=entity.entity_id, relationship=relationship, citation=entity.citation())
        return EvidenceItem(criterion=criterion, citation=entity.citation(), value=value, links=[link])

    def cluster(self, cluster_id: str, evidence: List[EvidenceItem]) -> List[EvidenceItem]:
        self.clusters[cluster_id] = evidence
        return evidence

    def to_json(self) -> Dict[str, Any]:
        return {
            "chart_id": self.chart_id,
            "encounter_graph": self.encounter_graph.to_json(),
            "clusters": {
                cluster_id: [item.to_json() for item in evidence]
                for cluster_id, evidence in self.clusters.items()
            },
        }


def build_evidence_graph(chart: NormalizedChart) -> EvidenceGraph:
    if chart.encounter_graph is None:
        from app.core.encounter_graph import build_encounter_graph

        chart.encounter_graph = build_encounter_graph(chart.raw)
    graph = EvidenceGraph(chart.encounter_graph)
    chart.evidence_graph = graph
    return graph


def note_evidence(graph: EvidenceGraph, criterion: str, terms: Iterable[str]) -> Optional[EvidenceItem]:
    for entity in graph.entities("note"):
        if contains_any(entity.excerpt, terms):
            return graph.make_item(criterion, entity)
    return None


def lab_values(graph: EvidenceGraph, name: str) -> List[GraphEntity]:
    return graph.entities("lab", name)


def vital_values(graph: EvidenceGraph, name: str) -> List[GraphEntity]:
    return graph.entities("vital", name)


def medication_evidence(graph: EvidenceGraph, terms: Iterable[str]) -> Optional[EvidenceItem]:
    for entity in graph.entities("medication"):
        if contains_any(str(entity.payload.get("name", entity.label)), terms):
            return graph.make_item("anti-infective therapy documented", entity)
    return None
