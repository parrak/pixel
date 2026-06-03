import json
from pathlib import Path

from asc_rcm_lite.persistence import load_persistence, update_work_item_status


def test_status_transition_persists(tmp_path: Path):
    path = tmp_path / "workflow.json"
    data = update_work_item_status(path, work_item_id="WQ-1", status="closed", owner_role="biller", reviewer_note="synthetic note")
    assert data["work_items"]["WQ-1"]["status"] == "closed"


def test_audit_event_is_recorded(tmp_path: Path):
    path = tmp_path / "workflow.json"
    data = update_work_item_status(path, work_item_id="WQ-1", status="closed", owner_role="biller", reviewer_note="synthetic note")
    assert data["audit_log"]


def test_pipeline_works_without_existing_persistence_file(tmp_path: Path):
    assert load_persistence(tmp_path / "missing.json") == {"work_items": {}, "audit_log": []}


def test_corrupted_persistence_file_is_ignored_with_warning(tmp_path: Path):
    path = tmp_path / "bad.json"
    path.write_text("{bad", encoding="utf-8")
    assert load_persistence(path) == {"work_items": {}, "audit_log": []}

