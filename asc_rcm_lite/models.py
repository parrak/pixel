"""Typed synthetic ASC / surgical RCM domain objects."""

from __future__ import annotations

from dataclasses import dataclass, fields
from decimal import Decimal
from typing import Any, ClassVar, Self


class ValidationError(ValueError):
    """Raised when a synthetic RCM record violates the schema."""


PHI_LIKE_KEYS = {
    "address",
    "birth_date",
    "city",
    "date_of_birth",
    "dob",
    "email",
    "first_name",
    "full_name",
    "last_name",
    "member_name",
    "mrn",
    "name",
    "patient_address",
    "patient_dob",
    "patient_email",
    "patient_name",
    "patient_phone",
    "phone",
    "ssn",
    "street",
    "zip",
}


def validate_no_phi_keys(value: Any, path: str = "$") -> None:
    """Reject common PHI-like field names in nested fixture data."""

    if isinstance(value, dict):
        for key, nested in value.items():
            normalized = key.lower()
            if normalized in PHI_LIKE_KEYS:
                raise ValidationError(f"PHI-like field {path}.{key} is not allowed")
            validate_no_phi_keys(nested, f"{path}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            validate_no_phi_keys(nested, f"{path}[{index}]")


def require_non_empty(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{field_name} is required")


def as_decimal(value: Any, field_name: str) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception as exc:  # pragma: no cover - Decimal exception details vary
        raise ValidationError(f"{field_name} must be decimal-compatible") from exc


@dataclass(frozen=True)
class EvidenceCitation:
    source_id: str
    source_type: str
    reference: str

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> Self:
        return cls(**data)

    def __post_init__(self) -> None:
        require_non_empty(self.source_id, "citation.source_id")
        require_non_empty(self.source_type, "citation.source_type")
        require_non_empty(self.reference, "citation.reference")


@dataclass(frozen=True)
class CitedFact:
    citation: EvidenceCitation

    _required_id_field: ClassVar[str | None] = None

    def __post_init__(self) -> None:
        if not isinstance(self.citation, EvidenceCitation):
            raise ValidationError(f"{type(self).__name__}.citation must be EvidenceCitation")
        if self._required_id_field is not None:
            require_non_empty(
                getattr(self, self._required_id_field),
                f"{type(self).__name__}.{self._required_id_field}",
            )


@dataclass(frozen=True)
class PatientEncounter(CitedFact):
    encounter_id: str
    synthetic_patient_id: str
    facility_id: str
    service_date: str
    specialty: str
    place_of_service: str
    primary_diagnosis_code: str
    citation: EvidenceCitation

    _required_id_field: ClassVar[str | None] = "encounter_id"


@dataclass(frozen=True)
class ProcedureCase(CitedFact):
    procedure_case_id: str
    encounter_id: str
    cpt_code: str
    description: str
    surgeon_id: str
    laterality: str
    status: str
    citation: EvidenceCitation

    _required_id_field: ClassVar[str | None] = "procedure_case_id"


@dataclass(frozen=True)
class ChargeLine(CitedFact):
    charge_line_id: str
    encounter_id: str
    cpt_code: str
    revenue_code: str
    units: int
    charge_amount: Decimal
    modifiers: tuple[str, ...]
    description: str
    citation: EvidenceCitation

    _required_id_field: ClassVar[str | None] = "charge_line_id"

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.units <= 0:
            raise ValidationError("ChargeLine.units must be positive")


@dataclass(frozen=True)
class Claim(CitedFact):
    claim_id: str
    encounter_id: str
    payer_id: str
    billed_amount: Decimal
    status: str
    submitted_date: str | None
    charge_line_ids: tuple[str, ...]
    citation: EvidenceCitation

    _required_id_field: ClassVar[str | None] = "claim_id"


@dataclass(frozen=True)
class Authorization(CitedFact):
    authorization_id: str
    encounter_id: str
    payer_id: str
    status: str
    authorized_cpt_codes: tuple[str, ...]
    valid_from: str | None
    valid_to: str | None
    citation: EvidenceCitation

    _required_id_field: ClassVar[str | None] = "authorization_id"


@dataclass(frozen=True)
class PayerPolicy(CitedFact):
    payer_policy_id: str
    payer_id: str
    policy_type: str
    cpt_code: str
    requirement: str
    contract_allowed_amount: Decimal | None
    citation: EvidenceCitation

    _required_id_field: ClassVar[str | None] = "payer_policy_id"


@dataclass(frozen=True)
class Denial(CitedFact):
    denial_id: str
    claim_id: str
    denial_code: str
    reason: str
    denied_amount: Decimal
    citation: EvidenceCitation

    _required_id_field: ClassVar[str | None] = "denial_id"


@dataclass(frozen=True)
class Remit(CitedFact):
    remit_id: str
    claim_id: str
    paid_amount: Decimal
    allowed_amount: Decimal
    adjustment_codes: tuple[str, ...]
    remit_date: str
    citation: EvidenceCitation

    _required_id_field: ClassVar[str | None] = "remit_id"


@dataclass(frozen=True)
class RCMOpportunity(CitedFact):
    opportunity_id: str
    encounter_id: str
    opportunity_type: str
    description: str
    estimated_value: Decimal
    priority: str
    citation: EvidenceCitation

    _required_id_field: ClassVar[str | None] = "opportunity_id"


@dataclass(frozen=True)
class WorkQueueItem(CitedFact):
    work_queue_item_id: str
    encounter_id: str
    queue: str
    reason: str
    status: str
    due_date: str | None
    citation: EvidenceCitation

    _required_id_field: ClassVar[str | None] = "work_queue_item_id"


@dataclass(frozen=True)
class ASCCase:
    case_id: str
    scenario: str
    encounter: PatientEncounter
    procedure_cases: tuple[ProcedureCase, ...]
    charge_lines: tuple[ChargeLine, ...]
    claims: tuple[Claim, ...]
    authorizations: tuple[Authorization, ...]
    payer_policies: tuple[PayerPolicy, ...]
    denials: tuple[Denial, ...]
    remits: tuple[Remit, ...]
    opportunities: tuple[RCMOpportunity, ...]
    work_queue_items: tuple[WorkQueueItem, ...]

    def __post_init__(self) -> None:
        require_non_empty(self.case_id, "ASCCase.case_id")
        require_non_empty(self.scenario, "ASCCase.scenario")
        if not self.claims and not self.work_queue_items:
            raise ValidationError("Every ASC case must have at least one claim or work queue item")


def dataclass_from_mapping(model: type[Any], data: dict[str, Any]) -> Any:
    model_field_names = {field.name for field in fields(model)}
    unknown = set(data) - model_field_names
    if unknown:
        raise ValidationError(f"{model.__name__} has unknown fields: {sorted(unknown)}")

    converted = dict(data)
    if "citation" in converted:
        converted["citation"] = EvidenceCitation.from_mapping(converted["citation"])
    for field_name in ("charge_amount", "billed_amount", "denied_amount", "paid_amount", "allowed_amount", "estimated_value"):
        if field_name in converted:
            converted[field_name] = as_decimal(converted[field_name], field_name)
    if "contract_allowed_amount" in converted and converted["contract_allowed_amount"] is not None:
        converted["contract_allowed_amount"] = as_decimal(converted["contract_allowed_amount"], "contract_allowed_amount")
    for field_name in ("modifiers", "charge_line_ids", "authorized_cpt_codes", "adjustment_codes"):
        if field_name in converted:
            converted[field_name] = tuple(converted[field_name])

    return model(**converted)
