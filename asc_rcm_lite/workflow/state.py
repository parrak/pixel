"""Role-aware workflow state objects."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from asc_rcm_lite.models import ValidationError, require_non_empty


WORKFLOW_STATES = {
    "new",
    "needs_review",
    "needs_provider_info",
    "ready_for_correction",
    "ready_for_appeal",
    "pending_payer",
    "escalated",
    "closed",
    "written_off",
}


@dataclass(frozen=True)
class WorkflowAuditEvent:
    event_id: str
    work_item_id: str
    previous_state: str
    next_state: str
    action: str
    actor_role: str
    timestamp: str
    reason: str
    cited_evidence_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        require_non_empty(self.event_id, "WorkflowAuditEvent.event_id")
        require_non_empty(self.work_item_id, "WorkflowAuditEvent.work_item_id")
        require_non_empty(self.previous_state, "WorkflowAuditEvent.previous_state")
        require_non_empty(self.next_state, "WorkflowAuditEvent.next_state")
        require_non_empty(self.action, "WorkflowAuditEvent.action")
        require_non_empty(self.actor_role, "WorkflowAuditEvent.actor_role")
        require_non_empty(self.timestamp, "WorkflowAuditEvent.timestamp")
        require_non_empty(self.reason, "WorkflowAuditEvent.reason")
        if not self.cited_evidence_ids:
            raise ValidationError("WorkflowAuditEvent.cited_evidence_ids must not be empty")
        _validate_state(self.previous_state)
        _validate_state(self.next_state)


@dataclass(frozen=True)
class WorkflowItem:
    work_item_id: str
    case_id: str
    owner_role: str
    queue_type: str
    current_state: str
    reason: str
    cited_evidence_ids: tuple[str, ...]
    audit_trace: tuple[WorkflowAuditEvent, ...]

    def __post_init__(self) -> None:
        require_non_empty(self.work_item_id, "WorkflowItem.work_item_id")
        require_non_empty(self.case_id, "WorkflowItem.case_id")
        require_non_empty(self.owner_role, "WorkflowItem.owner_role")
        require_non_empty(self.queue_type, "WorkflowItem.queue_type")
        require_non_empty(self.current_state, "WorkflowItem.current_state")
        require_non_empty(self.reason, "WorkflowItem.reason")
        if not self.cited_evidence_ids:
            raise ValidationError("WorkflowItem.cited_evidence_ids must not be empty")
        _validate_state(self.current_state)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _validate_state(state: str) -> None:
    if state not in WORKFLOW_STATES:
        raise ValidationError(f"Unsupported workflow state: {state}")
