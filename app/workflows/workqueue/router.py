from __future__ import annotations


def route_item(item: dict) -> str:
    return item.get("workflow", "prebill")

