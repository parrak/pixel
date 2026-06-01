from __future__ import annotations

from app.rules.coding.icd10_candidates import suggest_icd10_candidates


def suggest_codes(chart) -> list[dict]:
    return suggest_icd10_candidates(chart)

