from __future__ import annotations

from typing import Iterable


DEFINITIVE_PHRASES = [
    "patient has ",
    "the patient has ",
    "diagnosed with ",
    "meets criteria for ",
    "confirmed ",
    "definitive ",
]


def contains_any(text: str, terms: Iterable[str]) -> bool:
    haystack = text.lower()
    return any(term.lower() in haystack for term in terms)


def count_unsupported_assertions(text: str) -> int:
    lowered = text.lower()
    return sum(1 for phrase in DEFINITIVE_PHRASES if phrase in lowered)

