from __future__ import annotations

import json
from pathlib import Path
from typing import List

from app.core.models import NormalizedChart
from app.core.normalize import normalize_chart


def load_chart(path: Path) -> NormalizedChart:
    with path.open() as f:
        chart = json.load(f)
    return normalize_chart(chart)


def load_charts(directory: Path) -> List[NormalizedChart]:
    return [load_chart(path) for path in sorted(directory.glob("*.json"))]

