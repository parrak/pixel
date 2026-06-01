from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class Citation:
    source_id: str
    source_type: str
    timestamp: str
    label: str
    excerpt: str

    def to_json(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_type": self.source_type,
            "timestamp": self.timestamp,
            "label": self.label,
            "excerpt": self.excerpt,
        }


@dataclass(frozen=True)
class Fact:
    kind: str
    name: str
    value: Any
    unit: str
    timestamp: str
    citation: Citation

    def to_json(self) -> Dict[str, Any]:
        return {
            "kind": self.kind,
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp,
            "citation": self.citation.to_json(),
        }


@dataclass(frozen=True)
class GraphEntity:
    entity_id: str
    entity_type: str
    timestamp: str
    label: str
    payload: Dict[str, Any]
    source_id: str
    source_type: str
    excerpt: str

    def citation(self) -> Citation:
        return Citation(
            source_id=self.source_id,
            source_type=self.source_type,
            timestamp=self.timestamp,
            label=self.label,
            excerpt=self.excerpt,
        )

    def to_json(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "timestamp": self.timestamp,
            "label": self.label,
            "payload": self.payload,
            "source_id": self.source_id,
            "source_type": self.source_type,
            "excerpt": self.excerpt,
        }


@dataclass(frozen=True)
class GraphEdge:
    source_entity_id: str
    target_entity_id: str
    relationship: str

    def to_json(self) -> Dict[str, Any]:
        return {
            "source_entity_id": self.source_entity_id,
            "target_entity_id": self.target_entity_id,
            "relationship": self.relationship,
        }


@dataclass(frozen=True)
class EvidenceLink:
    entity_id: str
    relationship: str
    citation: Citation

    def to_json(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "relationship": self.relationship,
            "citation": self.citation.to_json(),
        }


@dataclass
class EvidenceItem:
    criterion: str
    citation: Citation
    value: Optional[str] = None
    links: List[EvidenceLink] = field(default_factory=list)

    def to_json(self) -> Dict[str, Any]:
        return {
            "criterion": self.criterion,
            "citation": self.citation.to_json(),
            "value": self.value,
            "links": [link.to_json() for link in self.links],
        }


@dataclass
class EvidenceCluster:
    cluster_id: str
    label: str
    evidence: List[EvidenceItem]

    def to_json(self) -> Dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "label": self.label,
            "evidence": [item.to_json() for item in self.evidence],
        }


@dataclass
class AuditTrace:
    events: List[str] = field(default_factory=list)

    def add(self, event: str) -> None:
        self.events.append(event)

    def to_json(self) -> Dict[str, Any]:
        return {"events": list(self.events)}


@dataclass
class EncounterBundle:
    bundle_id: str
    source_type: str
    payload: Dict[str, Any]

    @property
    def chart_id(self) -> str:
        return self.bundle_id

    def to_json(self) -> Dict[str, Any]:
        return {
            "bundle_id": self.bundle_id,
            "source_type": self.source_type,
            "payload": self.payload,
        }


@dataclass
class NormalizedChart:
    chart_id: str
    patient: Dict[str, Any]
    encounter: Dict[str, Any]
    coded_diagnoses: List[str]
    facts: List[Fact]
    raw: Dict[str, Any]
    encounter_graph: Optional[Any] = None
    evidence_graph: Optional[Any] = None

    def coded_contains(self, terms: List[str]) -> bool:
        coded = " | ".join(self.coded_diagnoses).lower()
        return any(term.lower() in coded for term in terms)

@dataclass
class Opportunity:
    chart_id: str
    opportunity_id: str
    diagnosis_family: str
    title: str
    summary: str
    rank_score: int
    evidence: List[EvidenceItem]
    missing_or_weak_documentation: str
    query: str
    audit_trace: List[str] = field(default_factory=list)

    def has_evidence(self) -> bool:
        return bool(self.evidence) and all(item.citation.excerpt and item.links for item in self.evidence)

    def to_json(self) -> Dict[str, Any]:
        return {
            "chart_id": self.chart_id,
            "opportunity_id": self.opportunity_id,
            "diagnosis_family": self.diagnosis_family,
            "title": self.title,
            "summary": self.summary,
            "rank_score": self.rank_score,
            "evidence": [item.to_json() for item in self.evidence],
            "missing_or_weak_documentation": self.missing_or_weak_documentation,
            "query": self.query,
            "audit_trace": list(self.audit_trace),
        }


@dataclass
class ReviewerAction:
    action_id: str
    workflow: str
    chart_id: str
    action_type: str
    title: str
    priority: int
    opportunity: Opportunity
    packet: str
    audit_trace: AuditTrace

    def has_graph_evidence(self) -> bool:
        return self.opportunity.has_evidence()

    def to_json(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "workflow": self.workflow,
            "chart_id": self.chart_id,
            "action_type": self.action_type,
            "title": self.title,
            "priority": self.priority,
            "opportunity": self.opportunity.to_json(),
            "packet": self.packet,
            "audit_trace": self.audit_trace.to_json(),
        }
