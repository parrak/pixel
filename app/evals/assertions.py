from __future__ import annotations


def query_is_safe(query: str) -> bool:
    lowered = query.lower()
    banned = ["please document", "patient has", "diagnose", "meets criteria", "confirm"]
    return "if clinically appropriate" in lowered and not any(term in lowered for term in banned)

