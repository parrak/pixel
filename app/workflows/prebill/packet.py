from __future__ import annotations

from app.core.models import NormalizedChart, Opportunity, ReviewerAction


def render_reviewer_packet(chart: NormalizedChart, opportunity: Opportunity) -> str:
    return _render_packet(chart.chart_id, opportunity, opportunity.audit_trace)


def render_reviewer_action_packet(action: ReviewerAction) -> str:
    return _render_packet(action.chart_id, action.opportunity, action.audit_trace.events)


def _render_packet(chart_id: str, opportunity: Opportunity, audit_events: list[str]) -> str:
    evidence_lines = []
    for index, item in enumerate(opportunity.evidence, start=1):
        citation = item.citation
        value = f" Value: {item.value}." if item.value else ""
        graph_links = ", ".join(link.entity_id for link in item.links)
        evidence_lines.append(
            f"{index}. {item.criterion}.{value} Citation: {citation.source_type} {citation.source_id} "
            f"at {citation.timestamp}: {citation.excerpt} Graph evidence: {graph_links}"
        )

    audit_lines = "\n".join(f"- {line}" for line in audit_events)
    evidence_text = "\n".join(evidence_lines)
    return (
        f"Reviewer packet\n"
        f"Chart: {chart_id}\n"
        f"Opportunity: {opportunity.title}\n"
        f"Reviewer framing: {opportunity.summary}\n"
        f"Documentation gap: {opportunity.missing_or_weak_documentation}\n\n"
        f"Evidence cited from chart:\n{evidence_text}\n\n"
        f"Neutral provider query draft:\n{opportunity.query}\n\n"
        f"Audit trace:\n{audit_lines}\n\n"
        f"Compliance note: This packet identifies a possible opportunity for reviewer validation. "
        f"It does not state that the patient definitively has the diagnosis."
    )


def packet_is_complete(packet: str) -> bool:
    required = [
        "Reviewer packet",
        "Opportunity:",
        "Evidence cited from chart:",
        "Neutral provider query draft:",
        "Audit trace:",
        "opportunity for reviewer validation",
    ]
    lowered = packet.lower()
    return all(item.lower() in lowered for item in required)
