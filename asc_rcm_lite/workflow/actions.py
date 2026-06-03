"""Workflow transitions for ASC RCM items."""

from __future__ import annotations

from dataclasses import replace

from asc_rcm_lite.models import ValidationError

from .state import WorkflowAuditEvent, WorkflowItem, utc_now_iso


WORKFLOW_ACTIONS = {
    "assign_owner",
    "request_provider_documentation",
    "mark_coder_review_needed",
    "prepare_corrected_claim",
    "prepare_appeal_packet",
    "prepare_payer_followup",
    "escalate_to_manager",
    "mark_pending_payer",
    "close_resolved",
    "recommend_writeoff",
}

ALLOWED_TRANSITIONS = {
    "new": {
        "assign_owner": "needs_review",
        "mark_coder_review_needed": "needs_review",
        "prepare_payer_followup": "needs_review",
        "prepare_appeal_packet": "needs_review",
    },
    "needs_review": {
        "request_provider_documentation": "needs_provider_info",
        "prepare_corrected_claim": "ready_for_correction",
        "prepare_appeal_packet": "ready_for_appeal",
        "prepare_payer_followup": "pending_payer",
        "escalate_to_manager": "escalated",
        "close_resolved": "closed",
        "recommend_writeoff": "written_off",
    },
    "needs_provider_info": {
        "mark_coder_review_needed": "needs_review",
        "escalate_to_manager": "escalated",
    },
    "ready_for_correction": {
        "mark_pending_payer": "pending_payer",
        "close_resolved": "closed",
    },
    "ready_for_appeal": {
        "mark_pending_payer": "pending_payer",
        "escalate_to_manager": "escalated",
    },
    "pending_payer": {
        "close_resolved": "closed",
        "escalate_to_manager": "escalated",
    },
    "escalated": {
        "prepare_appeal_packet": "ready_for_appeal",
        "prepare_corrected_claim": "ready_for_correction",
        "close_resolved": "closed",
        "recommend_writeoff": "written_off",
    },
    "closed": {},
    "written_off": {},
}


def apply_workflow_action(
    item: WorkflowItem,
    *,
    action: str,
    actor_role: str,
    reason: str,
    cited_evidence_ids: tuple[str, ...],
) -> WorkflowItem:
    if action not in WORKFLOW_ACTIONS:
        raise ValidationError(f"Unsupported workflow action: {action}")
    next_state = ALLOWED_TRANSITIONS.get(item.current_state, {}).get(action)
    if next_state is None:
        raise ValidationError(
            f"Invalid workflow transition from {item.current_state} using {action}"
        )
    event = WorkflowAuditEvent(
        event_id=f"{item.work_item_id}-{len(item.audit_trace) + 1}",
        work_item_id=item.work_item_id,
        previous_state=item.current_state,
        next_state=next_state,
        action=action,
        actor_role=actor_role,
        timestamp=utc_now_iso(),
        reason=reason,
        cited_evidence_ids=cited_evidence_ids,
    )
    return replace(
        item,
        current_state=next_state,
        audit_trace=item.audit_trace + (event,),
    )
