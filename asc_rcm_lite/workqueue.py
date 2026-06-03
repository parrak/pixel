"""Deterministic ASC RCM work queue prioritization."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from asc_rcm_lite.detectors.ar import ARFlag
from asc_rcm_lite.models import ValidationError, require_non_empty


@dataclass(frozen=True)
class WorkQueueEntry:
    work_item_id: str
    case_id: str
    claim_id: str
    payer: str
    queue_type: str
    owner_role: str
    aging_bucket: str
    opportunity_type: str
    priority_score: int
    priority_band: str
    balance: Decimal
    next_deadline: str | None
    cited_evidence_ids: tuple[str, ...]
    human_review_required: bool

    def __post_init__(self) -> None:
        require_non_empty(self.work_item_id, "WorkQueueEntry.work_item_id")
        require_non_empty(self.case_id, "WorkQueueEntry.case_id")
        require_non_empty(self.claim_id, "WorkQueueEntry.claim_id")
        require_non_empty(self.payer, "WorkQueueEntry.payer")
        require_non_empty(self.queue_type, "WorkQueueEntry.queue_type")
        require_non_empty(self.owner_role, "WorkQueueEntry.owner_role")
        require_non_empty(self.aging_bucket, "WorkQueueEntry.aging_bucket")
        require_non_empty(self.opportunity_type, "WorkQueueEntry.opportunity_type")
        if not self.cited_evidence_ids:
            raise ValidationError("WorkQueueEntry.cited_evidence_ids must not be empty")
        if not self.human_review_required:
            raise ValidationError("WorkQueueEntry.human_review_required must be true")


def build_work_queue(flags: tuple[ARFlag, ...]) -> tuple[WorkQueueEntry, ...]:
    entries = [
        WorkQueueEntry(
            work_item_id=flag.flag_id,
            case_id=flag.case_id,
            claim_id=flag.claim_id,
            payer=flag.payer,
            queue_type=_queue_type(flag.flag_type),
            owner_role=flag.owner_role,
            aging_bucket=flag.aging_bucket,
            opportunity_type=flag.flag_type,
            priority_score=flag.priority_score,
            priority_band=flag.priority_band,
            balance=flag.balance,
            next_deadline=flag.next_deadline,
            cited_evidence_ids=flag.evidence_citation_ids,
            human_review_required=True,
        )
        for flag in flags
    ]
    return tuple(sorted(entries, key=lambda item: (-item.priority_score, item.case_id, item.work_item_id)))


def filter_work_queue(
    queue: tuple[WorkQueueEntry, ...],
    *,
    payer: str | None = None,
    owner_role: str | None = None,
    aging_bucket: str | None = None,
    opportunity_type: str | None = None,
) -> tuple[WorkQueueEntry, ...]:
    filtered = queue
    if payer is not None:
        filtered = tuple(item for item in filtered if item.payer == payer)
    if owner_role is not None:
        filtered = tuple(item for item in filtered if item.owner_role == owner_role)
    if aging_bucket is not None:
        filtered = tuple(item for item in filtered if item.aging_bucket == aging_bucket)
    if opportunity_type is not None:
        filtered = tuple(item for item in filtered if item.opportunity_type == opportunity_type)
    return filtered


def manager_summary(queue: tuple[WorkQueueEntry, ...]) -> dict[str, object]:
    return {
        "total_items": len(queue),
        "total_balance": str(sum((item.balance for item in queue), Decimal("0.00"))),
        "urgent_items": sum(1 for item in queue if item.priority_band == "urgent"),
        "high_items": sum(1 for item in queue if item.priority_band == "high"),
        "owner_roles": {role: sum(1 for item in queue if item.owner_role == role) for role in sorted({item.owner_role for item in queue})},
        "payers": {payer: sum(1 for item in queue if item.payer == payer) for payer in sorted({item.payer for item in queue})},
    }


def _queue_type(flag_type: str) -> str:
    if flag_type == "underpayment":
        return "underpayment"
    if "appeal" in flag_type or "denial" in flag_type:
        return "denial"
    return "ar_followup"
