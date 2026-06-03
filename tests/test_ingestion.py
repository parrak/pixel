import json
from dataclasses import fields, is_dataclass

import pytest

from asc_rcm_lite.ingestion import load_asc_case, load_asc_cases
from asc_rcm_lite.models import ChargeLine, EvidenceCitation, PHI_LIKE_KEYS, ValidationError, dataclass_from_mapping


def _walk(value):
    if is_dataclass(value):
        yield value
        for field in fields(value):
            yield from _walk(getattr(value, field.name))
    elif isinstance(value, (tuple, list)):
        for item in value:
            yield from _walk(item)


def test_ingestion_loads_all_cases():
    cases = load_asc_cases()

    assert len(cases) == 8
    assert {case.case_id for case in cases} == {
        "ASC-CASE-001",
        "ASC-CASE-002",
        "ASC-CASE-003",
        "ASC-CASE-004",
        "ASC-CASE-005",
        "ASC-CASE-006",
        "ASC-CASE-007",
        "ASC-CASE-008",
    }


def test_no_phi_like_fields_exist():
    cases = load_asc_cases()

    for item in _walk(cases):
        if not is_dataclass(item):
            continue
        field_names = {field.name.lower() for field in fields(item)}
        assert field_names.isdisjoint(PHI_LIKE_KEYS)


def test_every_fact_has_citation_metadata():
    cases = load_asc_cases()

    for item in _walk(cases):
        if isinstance(item, EvidenceCitation):
            assert item.source_id
            assert item.source_type
            assert item.reference
        elif is_dataclass(item) and hasattr(item, "citation"):
            citation = item.citation
            assert isinstance(citation, EvidenceCitation)
            assert citation.source_id
            assert citation.source_type
            assert citation.reference


def test_every_case_has_claim_or_prebill_work_item():
    cases = load_asc_cases()

    for case in cases:
        assert case.claims or any(item.queue == "pre-bill" for item in case.work_queue_items)


def test_load_asc_cases_requires_directory(tmp_path):
    not_a_directory = tmp_path / "cases.json"
    not_a_directory.write_text("{}", encoding="utf-8")

    with pytest.raises(NotADirectoryError, match="not a directory"):
        load_asc_cases(not_a_directory)


def test_load_asc_case_requires_json_object_root(tmp_path):
    case_file = tmp_path / "case.json"
    case_file.write_text(json.dumps([]), encoding="utf-8")

    with pytest.raises(ValidationError, match="Expected JSON object at root"):
        load_asc_case(case_file)


def test_dataclass_from_mapping_requires_mapping():
    with pytest.raises(ValidationError, match="Expected a dictionary for ChargeLine"):
        dataclass_from_mapping(ChargeLine, None)
