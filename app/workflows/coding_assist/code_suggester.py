from __future__ import annotations

from app.rules.coding.icd10_candidates import suggest_icd10_candidates


def suggest_codes(evidence_graph) -> list[dict]:
    return suggest_icd10_candidates(evidence_graph)
