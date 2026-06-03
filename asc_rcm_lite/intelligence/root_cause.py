"""Root-cause aggregation helpers."""

from __future__ import annotations

from collections import Counter

from asc_rcm_lite.detectors.denials import DenialOpportunity


def top_root_causes(opportunities: tuple[DenialOpportunity, ...]) -> dict[str, int]:
    return dict(Counter(item.denial_category for item in opportunities).most_common())
