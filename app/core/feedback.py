from __future__ import annotations


def record_feedback(chart_id: str, opportunity_id: str, decision: str) -> dict[str, str]:
    return {"chart_id": chart_id, "opportunity_id": opportunity_id, "decision": decision}

