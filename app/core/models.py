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


@dataclass(frozen=True)
class Fact:
    kind: str
    name: str
    value: Any
    unit: str
    timestamp: str
    citation: Citation


@dataclass
class NormalizedChart:
    chart_id: str
    patient: Dict[str, Any]
    encounter: Dict[str, Any]
    coded_diagnoses: List[str]
    facts: List[Fact]
    raw: Dict[str, Any]

    def coded_contains(self, terms: List[str]) -> bool:
        coded = " | ".join(self.coded_diagnoses).lower()
        return any(term.lower() in coded for term in terms)


@dataclass
class EvidenceItem:
    criterion: str
    citation: Citation
    value: Optional[str] = None


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
        return bool(self.evidence) and all(item.citation.excerpt for item in self.evidence)

