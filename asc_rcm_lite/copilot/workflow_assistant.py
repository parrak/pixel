"""Role-aware workflow assistant for ASC RCM items."""

from __future__ import annotations

from dataclasses import dataclass

from asc_rcm_lite.models import ValidationError, require_non_empty, validate_no_phi_keys
from asc_rcm_lite.workflow.actions import ALLOWED_TRANSITIONS, apply_workflow_action
from asc_rcm_lite.workflow.state import WorkflowItem


ROLE_ACTIONS = {
    "coder": ("mark_coder_review_needed", "prepare_corrected_claim", "request_provider_documentation"),
    "biller": ("prepare_payer_followup", "mark_pending_payer", "close_resolved"),
    "denial_specialist": ("prepare_appeal_packet", "mark_pending_payer", "escalate_to_manager"),
    "auth_specialist": ("request_provider_documentation", "escalate_to_manager"),
    "manager": ("assign_owner", "escalate_to_manager", "recommend_writeoff", "close_resolved"),
}


@dataclass(frozen=True)
class WorkflowAssistantNote:
    note_type: str
    work_item_id: str
    content: str
    cited_evidence_ids: tuple[str, ...]
    human_review_required: bool

    def __post_init__(self) -> None:
        require_non_empty(self.note_type, "WorkflowAssistantNote.note_type")
        require_non_empty(self.work_item_id, "WorkflowAssistantNote.work_item_id")
        require_non_empty(self.content, "WorkflowAssistantNote.content")
        if not self.cited_evidence_ids:
            raise ValidationError("WorkflowAssistantNote.cited_evidence_ids must not be empty")
        if not self.human_review_required:
            raise ValidationError("WorkflowAssistantNote.human_review_required must be true")
        if "human review is required" not in self.content.lower():
            raise ValidationError("WorkflowAssistantNote.content must include human-review language")
        for evidence_id in self.cited_evidence_ids:
            if evidence_id not in self.content:
                raise ValidationError(f"Workflow assistant note must cite evidence id {evidence_id}")
        validate_no_phi_keys(
            {
                "note_type": self.note_type,
                "work_item_id": self.work_item_id,
                "content": self.content,
                "cited_evidence_ids": list(self.cited_evidence_ids),
            }
        )


class WorkflowAssistant:
    def allowed_actions(self, item: WorkflowItem, *, role: str) -> tuple[str, ...]:
        role_actions = ROLE_ACTIONS.get(role, ())
        state_actions = set(ALLOWED_TRANSITIONS.get(item.current_state, {}))
        return tuple(action for action in role_actions if action in state_actions)

    def explain_queue_reason(self, item: WorkflowItem) -> WorkflowAssistantNote:
        content = (
            f"Workflow queue reason for {item.work_item_id}: {item.reason} (Evidence: {', '.join(item.cited_evidence_ids)}).\n"
            f"The item is currently in state {item.current_state} and should be handled under queue {item.queue_type}.\n"
            "Human review is required before any coding, billing, appeal, or payer-facing action.\n"
            f"Evidence reviewed: {', '.join(item.cited_evidence_ids)}."
        )
        return WorkflowAssistantNote("queue_reason", item.work_item_id, content, item.cited_evidence_ids, True)

    def suggest_next_action(self, item: WorkflowItem, *, role: str) -> WorkflowAssistantNote:
        actions = self.allowed_actions(item, role=role)
        action = actions[0] if actions else "no_allowed_action"
        content = (
            f"Suggested next workflow action for {item.work_item_id}: {action} based on current state {item.current_state} and role {role} (Evidence: {', '.join(item.cited_evidence_ids)}).\n"
            "This is a workflow suggestion for reviewer validation only.\n"
            "Human review is required before any coding, billing, appeal, or payer-facing action.\n"
            f"Evidence reviewed: {', '.join(item.cited_evidence_ids)}."
        )
        return WorkflowAssistantNote("next_action", item.work_item_id, content, item.cited_evidence_ids, True)

    def generate_checklist(self, item: WorkflowItem, *, role: str) -> WorkflowAssistantNote:
        actions = self.allowed_actions(item, role=role)
        action_text = ", ".join(actions) if actions else "review queue context"
        content = (
            f"Workflow checklist for {item.work_item_id}: review evidence, confirm owner role {role}, and validate whether these actions are appropriate: {action_text} (Evidence: {', '.join(item.cited_evidence_ids)}).\n"
            "Human review is required before any coding, billing, appeal, or payer-facing action.\n"
            f"Evidence reviewed: {', '.join(item.cited_evidence_ids)}."
        )
        return WorkflowAssistantNote("workflow_checklist", item.work_item_id, content, item.cited_evidence_ids, True)

    def generate_role_specific_note(self, item: WorkflowItem, *, role: str) -> WorkflowAssistantNote:
        content = (
            f"Role-specific note for {role} on {item.work_item_id}: review whether the current workflow state {item.current_state} and queue reason '{item.reason}' support the next step for human review (Evidence: {', '.join(item.cited_evidence_ids)}).\n"
            "Human review is required before any coding, billing, appeal, or payer-facing action.\n"
            f"Evidence reviewed: {', '.join(item.cited_evidence_ids)}."
        )
        return WorkflowAssistantNote("role_specific_note", item.work_item_id, content, item.cited_evidence_ids, True)

    def explain_missing_evidence(self, item: WorkflowItem) -> WorkflowAssistantNote:
        content = (
            f"Missing evidence review for {item.work_item_id}: validate whether any additional documentation, policy context, or workflow notes are needed beyond cited evidence {', '.join(item.cited_evidence_ids)}.\n"
            "Human review is required before any coding, billing, appeal, or payer-facing action.\n"
            f"Evidence reviewed: {', '.join(item.cited_evidence_ids)}."
        )
        return WorkflowAssistantNote("missing_evidence", item.work_item_id, content, item.cited_evidence_ids, True)

    def recommend_escalation(self, item: WorkflowItem) -> WorkflowAssistantNote:
        content = (
            f"Escalation recommendation for {item.work_item_id}: review whether the current state {item.current_state} and queue reason '{item.reason}' warrant manager escalation for human review (Evidence: {', '.join(item.cited_evidence_ids)}).\n"
            "Human review is required before any coding, billing, appeal, or payer-facing action.\n"
            f"Evidence reviewed: {', '.join(item.cited_evidence_ids)}."
        )
        return WorkflowAssistantNote("escalation_recommendation", item.work_item_id, content, item.cited_evidence_ids, True)

    def apply_action(
        self,
        item: WorkflowItem,
        *,
        action: str,
        actor_role: str,
        reason: str,
    ) -> WorkflowItem:
        return apply_workflow_action(
            item,
            action=action,
            actor_role=actor_role,
            reason=reason,
            cited_evidence_ids=item.cited_evidence_ids,
        )
