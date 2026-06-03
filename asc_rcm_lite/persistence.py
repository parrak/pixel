"""Lightweight local persistence for synthetic workflow state."""

from __future__ import annotations

import json
import warnings
from pathlib import Path

from asc_rcm_lite.models import validate_no_phi_keys


def load_persistence(path: str | Path) -> dict[str, object]:
    file_path = Path(path)
    if not file_path.exists():
        return {"work_items": {}, "audit_log": []}
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except Exception:
        warnings.warn("Persistence file is corrupted; ignoring and continuing with empty state.", RuntimeWarning, stacklevel=2)
        return {"work_items": {}, "audit_log": []}
    validate_no_phi_keys(data)
    return data


def save_persistence(path: str | Path, data: dict[str, object]) -> None:
    validate_no_phi_keys(data)
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def update_work_item_status(path: str | Path, *, work_item_id: str, status: str, owner_role: str, reviewer_note: str) -> dict[str, object]:
    data = load_persistence(path)
    work_items = dict(data.get("work_items", {}))
    work_items[work_item_id] = {
        "status": status,
        "owner_role": owner_role,
        "reviewer_note": reviewer_note,
    }
    data["work_items"] = work_items
    data.setdefault("audit_log", []).append(
        {
            "work_item_id": work_item_id,
            "status": status,
            "owner_role": owner_role,
        }
    )
    save_persistence(path, data)
    return data
