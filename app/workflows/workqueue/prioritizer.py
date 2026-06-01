from __future__ import annotations


def prioritize(items: list[dict]) -> list[dict]:
    return sorted(items, key=lambda item: item.get("rank_score", 0), reverse=True)

