from __future__ import annotations

import json
from pathlib import Path
from typing import List

from app.core.models import EncounterBundle


def load_encounter_bundle(path: Path) -> EncounterBundle:
    with path.open() as f:
        payload = json.load(f)
    return EncounterBundle(
        bundle_id=payload["chart_id"],
        source_type="synthetic_chart_json",
        payload=payload,
    )


def load_encounter_bundles(directory: Path) -> List[EncounterBundle]:
    return [load_encounter_bundle(path) for path in sorted(directory.glob("*.json"))]
