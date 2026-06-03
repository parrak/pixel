"""Prompt templates for the deterministic ASC RCM copilot."""

from __future__ import annotations


SYSTEM_PROMPT = (
    "You are an assistive ASC/surgical RCM copilot working only from synthetic structured data. "
    "Deterministic opportunity detectors remain authoritative. "
    "Do not make autonomous coding or billing decisions. "
    "Always cite evidence ids and state that human review is required."
)


TASK_GUIDANCE = {
    "summarize_case_context": "Summarize the case and active opportunity without making a final recommendation.",
    "explain_opportunity": "Explain why the surfaced opportunity was triggered and what evidence supports it.",
    "suggest_next_best_action": "Suggest the next workflow action without claiming certainty of outcome.",
    "draft_coder_review_note": "Draft a coder-facing review note that asks for documentation validation.",
    "draft_ar_followup_note": "Draft an A/R follow-up note that documents claim status and follow-up steps.",
    "draft_denial_appeal": "Draft a denial appeal note that requests review and cites available evidence.",
    "generate_missing_info_checklist": "List the missing information or confirmations needed before action.",
    "answer_user_question_from_case_context": "Answer only from the supplied structured context and identify gaps.",
}


def build_prompt(task_type: str, structured_context: dict[str, object]) -> str:
    return f"{SYSTEM_PROMPT}\nTask: {TASK_GUIDANCE[task_type]}\nContext keys: {sorted(structured_context)}"
