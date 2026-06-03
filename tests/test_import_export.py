import csv
import json
from pathlib import Path

from asc_rcm_lite.export import export_json, export_packet_markdown, export_work_queue_csv
from asc_rcm_lite.import_validation import validate_synthetic_case_json
from asc_rcm_lite.pipeline import run_pipeline


def test_exports_are_deterministic(tmp_path: Path):
    result = run_pipeline(case_id="ASC-CASE-008")
    path = tmp_path / "queue.csv"
    export_work_queue_csv(path, result)
    rows = list(csv.DictReader(path.open()))
    assert rows


def test_exported_packet_includes_citations(tmp_path: Path):
    result = run_pipeline(case_id="ASC-CASE-002")
    path = tmp_path / "packet.md"
    export_packet_markdown(path, result.cases[0].reviewer_packets[0])
    text = path.read_text(encoding="utf-8")
    assert "Evidence:" in text


def test_invalid_synthetic_case_json_fails_validation_with_useful_error(tmp_path: Path):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"case_id": "X"}), encoding="utf-8")
    try:
        validate_synthetic_case_json(path)
    except Exception as exc:
        assert "missing required fields" in str(exc)
    else:
        raise AssertionError("Expected validation failure")


def test_phi_like_fields_rejected(tmp_path: Path):
    path = tmp_path / "phi.json"
    path.write_text(json.dumps({"case_id": "X", "encounter": {"citation": {}}, "procedure_cases": [], "charge_lines": [], "name": "bad"}), encoding="utf-8")
    try:
        validate_synthetic_case_json(path)
    except Exception as exc:
        assert "PHI-like field" in str(exc)
    else:
        raise AssertionError("Expected PHI validation failure")
