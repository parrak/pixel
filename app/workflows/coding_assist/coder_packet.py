from __future__ import annotations


def build_coder_packet(evidence_graph, candidates: list[dict]) -> dict:
    _ = evidence_graph
    return {"candidates": candidates}
