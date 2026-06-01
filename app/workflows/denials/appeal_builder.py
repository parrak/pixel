from __future__ import annotations


def build_appeal_packet(evidence_graph, evidence: list[dict]) -> dict:
    _ = evidence_graph
    return {"evidence": evidence}
