from asc_rcm_lite.copilot.workflow_assistant import WorkflowAssistant
from asc_rcm_lite.workflow.state import WorkflowItem


def _item(owner_role: str, queue_type: str = "ar_followup") -> WorkflowItem:
    return WorkflowItem(
        work_item_id=f"WQ-{owner_role}",
        case_id="ASC-CASE-TEST",
        owner_role=owner_role,
        queue_type=queue_type,
        current_state="needs_review",
        reason="synthetic queue reason",
        cited_evidence_ids=("SRC-TEST",),
        audit_trace=(),
    )


def test_coder_sees_coding_specific_workflow_actions():
    actions = WorkflowAssistant().allowed_actions(_item("coder", "coding_qa"), role="coder")
    assert "mark_coder_review_needed" in actions or "prepare_corrected_claim" in actions


def test_biller_sees_ar_followup_actions():
    assert "prepare_payer_followup" in WorkflowAssistant().allowed_actions(_item("biller"), role="biller")


def test_denial_specialist_sees_appeal_actions():
    assert "prepare_appeal_packet" in WorkflowAssistant().allowed_actions(_item("denial_specialist", "denial"), role="denial_specialist")


def test_auth_specialist_sees_auth_actions():
    assert "request_provider_documentation" in WorkflowAssistant().allowed_actions(_item("auth_specialist", "auth"), role="auth_specialist")


def test_manager_sees_escalation_and_queue_summary_actions():
    actions = WorkflowAssistant().allowed_actions(_item("manager"), role="manager")
    assert "escalate_to_manager" in actions


def test_every_workflow_action_writes_audit_trace():
    assistant = WorkflowAssistant()
    updated = assistant.apply_action(_item("biller"), action="prepare_payer_followup", actor_role="biller", reason="Follow up")
    assert len(updated.audit_trace) == 1


def test_invalid_state_transitions_are_rejected():
    assistant = WorkflowAssistant()
    item = _item("biller")
    try:
        assistant.apply_action(item, action="assign_owner", actor_role="biller", reason="skip")
    except Exception as exc:
        assert "Invalid workflow transition" in str(exc)
    else:
        raise AssertionError("Expected invalid transition error")


def test_generated_notes_include_citations_and_human_review_language():
    note = WorkflowAssistant().generate_role_specific_note(_item("coder", "coding_qa"), role="coder")
    assert "SRC-TEST" in note.content
    assert "Human review is required" in note.content
