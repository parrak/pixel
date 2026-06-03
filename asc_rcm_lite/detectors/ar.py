"""Deterministic A/R flagging for synthetic ASC RCM claims."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Iterable

from asc_rcm_lite.models import ASCCase, ValidationError, require_non_empty


@dataclass(frozen=True)
class ARFlag:
    flag_id: str
    claim_id: str
    case_id: str
    payer: str
    flag_type: str
    days_in_ar: int
    balance: Decimal
    aging_bucket: str
    last_touch_date: str | None
    next_deadline: str | None
    reason_for_flag: str
    recommended_next_action: str
    owner_role: str
    evidence_citation_ids: tuple[str, ...]
    priority_score: int
    priority_band: str
    human_review_required: bool

    def __post_init__(self) -> None:
        require_non_empty(self.flag_id, "ARFlag.flag_id")
        require_non_empty(self.claim_id, "ARFlag.claim_id")
        require_non_empty(self.case_id, "ARFlag.case_id")
        require_non_empty(self.payer, "ARFlag.payer")
        require_non_empty(self.flag_type, "ARFlag.flag_type")
        require_non_empty(self.aging_bucket, "ARFlag.aging_bucket")
        require_non_empty(self.reason_for_flag, "ARFlag.reason_for_flag")
        require_non_empty(self.recommended_next_action, "ARFlag.recommended_next_action")
        require_non_empty(self.owner_role, "ARFlag.owner_role")
        if not self.evidence_citation_ids:
            raise ValidationError("ARFlag.evidence_citation_ids must not be empty")
        if self.priority_band not in {"urgent", "high", "normal", "low"}:
            raise ValidationError(f"Unsupported priority band: {self.priority_band}")
        if not self.human_review_required:
            raise ValidationError("ARFlag.human_review_required must be true")


def detect_ar_flags(case: ASCCase, *, as_of_date: str) -> tuple[ARFlag, ...]:
    if not case.claims:
        return ()

    today = _parse_date(as_of_date)
    flags: list[ARFlag] = []
    claim = case.claims[0]
    submitted = _parse_date(claim.submitted_date) if claim.submitted_date else today
    days_in_ar = max((today - submitted).days, 0)
    aging_bucket = _aging_bucket(days_in_ar)
    balance = _claim_balance(case)
    work_item = case.work_queue_items[0] if case.work_queue_items else None
    denial = case.denials[0] if case.denials else None
    remit = case.remits[0] if case.remits else None
    contract = next((item for item in case.payer_policies if item.contract_allowed_amount is not None), None)
    due_date = work_item.due_date if work_item else None

    if claim.status.startswith("open_ar") or (days_in_ar >= 60 and claim.status not in {"paid", "paid_under_expected"}):
        if balance >= Decimal("10000.00"):
            flags.append(
                _make_flag(
                    case=case,
                    claim_id=claim.claim_id,
                    payer=claim.payer_id,
                    flag_type="high_dollar_ar",
                    days_in_ar=days_in_ar,
                    balance=balance,
                    aging_bucket=aging_bucket,
                    last_touch_date=None,
                    next_deadline=due_date,
                    reason="High-dollar synthetic A/R balance warrants prioritized follow-up for human review.",
                    action="Biller should validate claim status, prior touches, and follow-up packet before payer outreach, for human review.",
                    owner_role="biller",
                    evidence_ids=_ids(claim.citation.source_id, work_item.citation.source_id if work_item else None),
                    as_of=today,
                )
            )
        if days_in_ar >= 30:
            flags.append(
                _make_flag(
                    case=case,
                    claim_id=claim.claim_id,
                    payer=claim.payer_id,
                    flag_type=f"ar_{aging_bucket}",
                    days_in_ar=days_in_ar,
                    balance=balance,
                    aging_bucket=aging_bucket,
                    last_touch_date=None,
                    next_deadline=due_date,
                    reason=f"Synthetic claim has aged into the {aging_bucket} bucket and needs deterministic A/R review.",
                    action="Biller should validate aging details and prepare the next follow-up step for human review.",
                    owner_role="biller",
                    evidence_ids=_ids(claim.citation.source_id, work_item.citation.source_id if work_item else None),
                    as_of=today,
                )
            )
    if denial is not None and due_date is not None:
        days_to_deadline = (_parse_date(due_date) - today).days
        if days_to_deadline <= 7:
            flags.append(
                _make_flag(
                    case=case,
                    claim_id=claim.claim_id,
                    payer=claim.payer_id,
                    flag_type="appeal_deadline_risk",
                    days_in_ar=days_in_ar,
                    balance=balance,
                    aging_bucket=aging_bucket,
                    last_touch_date=None,
                    next_deadline=due_date,
                    reason="Synthetic denial follow-up deadline is near; review whether appeal or corrected-claim preparation should be escalated for human review.",
                    action="Denial specialist should validate deadline, evidence completeness, and appeal path immediately, for human review.",
                    owner_role="denial_specialist",
                    evidence_ids=_ids(claim.citation.source_id, denial.citation.source_id, work_item.citation.source_id if work_item else None),
                    as_of=today,
                )
            )
    if work_item is not None and work_item.due_date and _parse_date(work_item.due_date) < today:
        flags.append(
            _make_flag(
                case=case,
                claim_id=claim.claim_id,
                payer=claim.payer_id,
                flag_type="stale_followup",
                days_in_ar=days_in_ar,
                balance=balance,
                aging_bucket=aging_bucket,
                last_touch_date=None,
                next_deadline=work_item.due_date,
                reason="Work-queue follow-up appears stale because the synthetic due date has passed without closure; review whether no recent touch exists for human review.",
                action="Assigned owner should validate follow-up history and refresh the next action plan for human review.",
                owner_role=_owner_role_from_queue(work_item.queue),
                evidence_ids=_ids(claim.citation.source_id, work_item.citation.source_id),
                as_of=today,
            )
        )
    if remit is not None and contract is not None and remit.paid_amount < contract.contract_allowed_amount:
        underpaid = contract.contract_allowed_amount - remit.paid_amount
        flags.append(
            _make_flag(
                case=case,
                claim_id=claim.claim_id,
                payer=claim.payer_id,
                flag_type="underpayment",
                days_in_ar=days_in_ar,
                balance=underpaid,
                aging_bucket=aging_bucket,
                last_touch_date=remit.remit_date,
                next_deadline=due_date,
                reason="Synthetic contract allowed amount exceeds paid amount; review whether a recoverable underpayment opportunity exists for human review.",
                action="Underpayment specialist or biller should validate contract terms, payment variance, and follow-up path for human review.",
                owner_role="biller",
                evidence_ids=_ids(claim.citation.source_id, remit.citation.source_id, contract.citation.source_id),
                as_of=today,
            )
        )
    if remit is None and denial is None and claim.status not in {"paid", "paid_under_expected"} and days_in_ar >= 30:
        flags.append(
            _make_flag(
                case=case,
                claim_id=claim.claim_id,
                payer=claim.payer_id,
                flag_type="missing_payer_response",
                days_in_ar=days_in_ar,
                balance=balance,
                aging_bucket=aging_bucket,
                last_touch_date=None,
                next_deadline=due_date,
                reason="No synthetic remit or denial response is present despite aging; review whether payer follow-up is required for human review.",
                action="Biller should validate clearing status and prepare a payer follow-up checklist for human review.",
                owner_role="biller",
                evidence_ids=_ids(claim.citation.source_id, work_item.citation.source_id if work_item else None),
                as_of=today,
            )
        )

    return tuple(_dedupe_flags(flags))


def _make_flag(
    *,
    case: ASCCase,
    claim_id: str,
    payer: str,
    flag_type: str,
    days_in_ar: int,
    balance: Decimal,
    aging_bucket: str,
    last_touch_date: str | None,
    next_deadline: str | None,
    reason: str,
    action: str,
    owner_role: str,
    evidence_ids: tuple[str, ...],
    as_of: date,
) -> ARFlag:
    score = _priority_score(
        balance=balance,
        days_in_ar=days_in_ar,
        next_deadline=next_deadline,
        denial_related=owner_role == "denial_specialist",
        stale=flag_type == "stale_followup",
        underpayment=flag_type == "underpayment",
        as_of=as_of,
    )
    return ARFlag(
        flag_id=f"{case.case_id}-{flag_type}",
        claim_id=claim_id,
        case_id=case.case_id,
        payer=payer,
        flag_type=flag_type,
        days_in_ar=days_in_ar,
        balance=balance,
        aging_bucket=aging_bucket,
        last_touch_date=last_touch_date,
        next_deadline=next_deadline,
        reason_for_flag=reason,
        recommended_next_action=action,
        owner_role=owner_role,
        evidence_citation_ids=evidence_ids,
        priority_score=score,
        priority_band=_priority_band(score),
        human_review_required=True,
    )


def _priority_score(
    *,
    balance: Decimal,
    days_in_ar: int,
    next_deadline: str | None,
    denial_related: bool,
    stale: bool,
    underpayment: bool,
    as_of: date,
) -> int:
    score = 0
    if balance >= Decimal("20000"):
        score += 35
    elif balance >= Decimal("5000"):
        score += 25
    elif balance >= Decimal("1000"):
        score += 15
    else:
        score += 8

    if days_in_ar >= 120:
        score += 30
    elif days_in_ar >= 90:
        score += 22
    elif days_in_ar >= 60:
        score += 15
    elif days_in_ar >= 30:
        score += 8

    if next_deadline:
        delta = (_parse_date(next_deadline) - as_of).days
        if delta <= 3:
            score += 28
        elif delta <= 7:
            score += 20
        elif delta <= 14:
            score += 10
    if denial_related:
        score += 8
    if stale:
        score += 10
    if underpayment:
        score += 6
    return max(0, min(score, 100))


def _priority_band(score: int) -> str:
    if score >= 85:
        return "urgent"
    if score >= 65:
        return "high"
    if score >= 40:
        return "normal"
    return "low"


def _claim_balance(case: ASCCase) -> Decimal:
    claim = case.claims[0]
    remit = case.remits[0] if case.remits else None
    if remit is None:
        return claim.billed_amount
    contract = next((item for item in case.payer_policies if item.contract_allowed_amount is not None), None)
    if contract is not None and remit.paid_amount < contract.contract_allowed_amount:
        return contract.contract_allowed_amount - remit.paid_amount
    return max(claim.billed_amount - remit.paid_amount, Decimal("0.00"))


def _aging_bucket(days_in_ar: int) -> str:
    if days_in_ar >= 120:
        return "120_plus"
    if days_in_ar >= 90:
        return "90"
    if days_in_ar >= 60:
        return "60"
    if days_in_ar >= 30:
        return "30"
    return "current"


def _parse_date(value: str | None) -> date:
    if not value:
        raise ValidationError("Date value is required for deterministic A/R calculations")
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValidationError(f"Invalid deterministic date format: {value}") from exc


def _owner_role_from_queue(queue: str) -> str:
    return {
        "underpayment": "biller",
        "denial": "denial_specialist",
        "ar-follow-up": "biller",
    }.get(queue, "biller")


def _ids(*values: str | None) -> tuple[str, ...]:
    return tuple(dict.fromkeys(value for value in values if value))


def _dedupe_flags(flags: Iterable[ARFlag]) -> list[ARFlag]:
    seen: set[str] = set()
    deduped: list[ARFlag] = []
    for flag in flags:
        if flag.flag_id in seen:
            continue
        seen.add(flag.flag_id)
        deduped.append(flag)
    return deduped
