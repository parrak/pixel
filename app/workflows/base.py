from __future__ import annotations

from typing import Protocol

from app.core.evidence_graph import EvidenceGraph
from app.core.models import ReviewerAction


class WorkflowAgent(Protocol):
    workflow_name: str

    def run(self, graph: EvidenceGraph) -> list[ReviewerAction]:
        """Return reviewer actions backed by graph evidence."""

