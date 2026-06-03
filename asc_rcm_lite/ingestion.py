"""Load synthetic ASC / surgical RCM JSON fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import (
    ASCCase,
    Authorization,
    ChargeLine,
    Claim,
    Denial,
    PatientEncounter,
    PayerPolicy,
    ProcedureCase,
    RCMOpportunity,
    Remit,
    ValidationError,
    WorkQueueItem,
    dataclass_from_mapping,
    validate_no_phi_keys,
)


DEFAULT_CASE_DIR = Path(__file__).resolve().parents[1] / "data" / "asc_cases"


def load_asc_cases(case_dir: str | Path = DEFAULT_CASE_DIR) -> list[ASCCase]:
    """Load and validate all synthetic case JSON files from a directory."""

    directory = Path(case_dir)
    if not directory.exists():
        raise FileNotFoundError(f"ASC case directory does not exist: {directory}")

    cases = [load_asc_case(path) for path in sorted(directory.glob("*.json"))]
    if not cases:
        raise ValidationError(f"No ASC case JSON files found in {directory}")
    return cases


def load_asc_case(path: str | Path) -> ASCCase:
    source = Path(path)
    with source.open(encoding="utf-8") as file:
        raw = json.load(file)

    validate_no_phi_keys(raw)
    return _case_from_mapping(raw)


def _required(raw: dict[str, Any], key: str) -> Any:
    if key not in raw:
        raise ValidationError(f"Case fixture is missing required key: {key}")
    return raw[key]


def _case_from_mapping(raw: dict[str, Any]) -> ASCCase:
    return ASCCase(
        case_id=_required(raw, "case_id"),
        scenario=_required(raw, "scenario"),
        encounter=dataclass_from_mapping(PatientEncounter, _required(raw, "encounter")),
        procedure_cases=tuple(dataclass_from_mapping(ProcedureCase, item) for item in _required(raw, "procedure_cases")),
        charge_lines=tuple(dataclass_from_mapping(ChargeLine, item) for item in _required(raw, "charge_lines")),
        claims=tuple(dataclass_from_mapping(Claim, item) for item in _required(raw, "claims")),
        authorizations=tuple(dataclass_from_mapping(Authorization, item) for item in _required(raw, "authorizations")),
        payer_policies=tuple(dataclass_from_mapping(PayerPolicy, item) for item in _required(raw, "payer_policies")),
        denials=tuple(dataclass_from_mapping(Denial, item) for item in _required(raw, "denials")),
        remits=tuple(dataclass_from_mapping(Remit, item) for item in _required(raw, "remits")),
        opportunities=tuple(dataclass_from_mapping(RCMOpportunity, item) for item in _required(raw, "opportunities")),
        work_queue_items=tuple(dataclass_from_mapping(WorkQueueItem, item) for item in _required(raw, "work_queue_items")),
    )
