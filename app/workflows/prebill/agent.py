from __future__ import annotations

from app.core.evidence_graph import EvidenceGraph
from app.core.models import AuditTrace, ReviewerAction
from app.workflows.prebill.detector import analyze_evidence_graph
from app.workflows.prebill.packet import render_reviewer_action_packet


class PrebillWorkflowAgent:
    workflow_name = "prebill"

    def run(self, graph: EvidenceGraph) -> list[ReviewerAction]:
        actions = []
        for opportunity in analyze_evidence_graph(graph):
            audit_trace = AuditTrace(
                [
                    "Encounter bundle normalized into shared encounter graph.",
                    "Evidence graph evaluated by prebill workflow agent.",
                    *opportunity.audit_trace,
                ]
            )
            action = ReviewerAction(
                action_id=f"{opportunity.opportunity_id}-review",
                workflow=self.workflow_name,
                chart_id=opportunity.chart_id,
                action_type="review_opportunity",
                title=opportunity.title,
                priority=opportunity.rank_score,
                opportunity=opportunity,
                packet="",
                audit_trace=audit_trace,
            )
            action.packet = render_reviewer_action_packet(action)
            actions.append(action)
        return actions


def run_prebill_agent(graph: EvidenceGraph) -> list[ReviewerAction]:
    return PrebillWorkflowAgent().run(graph)
