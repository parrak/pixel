"""Import validation for synthetic ASC case JSON."""

from __future__ import annotations

import json
from pathlib import Path

from asc_rcm_lite.models import ValidationError, validate_no_phi_keys


def validate_synthetic_case_json(path: str | Path) -> dict[str, object]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValidationError("Synthetic ASC case JSON must be an object")
    validate_no_phi_keys(data)
    required = {"case_id", "encounter", "procedure_cases", "charge_lines"}
    missing = required - set(data)
    if missing:
        raise ValidationError(f"Synthetic ASC case JSON is missing required fields: {sorted(missing)}")
    for section in ("encounter",):
        if "citation" not in data.get(section, {}):
            raise ValidationError(f"{section} must include citation metadata")
    return data
