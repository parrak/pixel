"""Deterministic local stub that mimics copilot-style ASC RCM responses."""

from __future__ import annotations

from typing import Any

from .models import CopilotDraft, CopilotRequest


class MockLLM:
    """Structured, deterministic response generator with no external dependencies."""

    def generate(self, request: CopilotRequest, prompt: str) -> CopilotDraft:
        del prompt
        context = request.structured_context
        handlers = {
            "summarize_case_context": self._summarize_case_context,
            "explain_opportunity": self._explain_opportunity,
            "suggest_next_best_action": self._suggest_next_best_action,
            "draft_coder_review_note": self._draft_coder_review_note,
            "draft_ar_followup_note": self._draft_ar_followup_note,
            "draft_denial_appeal": self._draft_denial_appeal,
            "generate_missing_info_checklist": self._generate_missing_info_checklist,
            "answer_user_question_from_case_context": self._answer_question,
        }
        return handlers[request.task_type](context)

    def _summarize_case_context(self, context: dict[str, Any]) -> CopilotDraft:
        encounter = context["encounter"]
        procedure = context["procedures"][0]
        opportunity = context["selected_opportunity"]
        claim = context["active_claim"]
        evidence_ids = self._collect_ids(encounter, procedure, opportunity, claim)
        text = (
            f"Case {context['case_id']} is a synthetic {context['scenario']} involving "
            f"CPT {procedure['cpt_code']} ({procedure['description']}) on {encounter['service_date']} "
            f"for {encounter['specialty']} in POS {encounter['place_of_service']} "
            f"(Evidence: {encounter['evidence_id']}, {procedure['evidence_id']}).\n"
            f"The current surfaced opportunity is {opportunity['opportunity_type']} with priority "
            f"{opportunity['priority']} and estimated value {opportunity['estimated_value']} "
            f"(Evidence: {opportunity['evidence_id']}).\n"
            f"Active claim status is {claim['status']} with billed amount {claim['billed_amount']} "
            f"to payer {claim['payer_id']} (Evidence: {claim['evidence_id']}).\n"
            f"Human review is required before any coding, billing, appeal, or payer-facing action.\n"
            f"Evidence reviewed: {', '.join(evidence_ids)}."
        )
        return CopilotDraft(response_text=text, cited_evidence_ids=evidence_ids)

    def _explain_opportunity(self, context: dict[str, Any]) -> CopilotDraft:
        opportunity = context["selected_opportunity"]
        claim = context["active_claim"]
        work_item = context["active_work_queue_item"]
        evidence_ids = self._collect_ids(opportunity, claim, work_item)
        text = (
            f"The deterministic workflow surfaced {opportunity['opportunity_type']} because the case carries "
            f"the description '{opportunity['description']}' with {opportunity['priority']} priority "
            f"(Evidence: {opportunity['evidence_id']}).\n"
            f"Supporting revenue-cycle context includes claim status {claim['status']} and work queue reason "
            f"'{work_item['reason']}' (Evidence: {claim['evidence_id']}, {work_item['evidence_id']}).\n"
            f"Use this as an assistive explanation only; human review is required before any action.\n"
            f"Evidence reviewed: {', '.join(evidence_ids)}."
        )
        return CopilotDraft(response_text=text, cited_evidence_ids=evidence_ids)

    def _suggest_next_best_action(self, context: dict[str, Any]) -> CopilotDraft:
        opportunity = context["selected_opportunity"]
        work_item = context["active_work_queue_item"]
        policy = context["active_policy"]
        evidence_ids = self._collect_ids(opportunity, work_item, policy)
        suggestion = self._workflow_suggestion(opportunity["opportunity_type"])
        text = (
            f"Suggested next action: {suggestion}\n"
            f"This suggestion is based on the surfaced opportunity '{opportunity['description']}' "
            f"and current queue '{work_item['queue']}' (Evidence: {opportunity['evidence_id']}, {work_item['evidence_id']}).\n"
            f"If payer-policy validation is relevant, review requirement '{policy['requirement']}' "
            f"before moving forward (Evidence: {policy['evidence_id']}).\n"
            f"Human review is required before any coding, billing, appeal, or payer-facing action.\n"
            f"Evidence reviewed: {', '.join(evidence_ids)}."
        )
        return CopilotDraft(response_text=text, cited_evidence_ids=evidence_ids)

    def _draft_coder_review_note(self, context: dict[str, Any]) -> CopilotDraft:
        procedure_codes = ", ".join(item["cpt_code"] for item in context["procedures"])
        charge = context["charges"][0]
        opportunity = context["selected_opportunity"]
        policy = context["active_policy"]
        evidence_ids = self._collect_ids(opportunity, charge, policy, *context["procedures"])
        text = (
            "Coder review draft:\n"
            f"- Review procedure set {procedure_codes} against charge detail for CPT {charge['cpt_code']} "
            f"with modifiers {charge['modifiers']} (Evidence: {charge['evidence_id']}).\n"
            f"- Validate whether the documentation supports the surfaced risk '{opportunity['description']}' "
            f"before claim release (Evidence: {opportunity['evidence_id']}).\n"
            f"- Compare documentation to policy requirement '{policy['requirement']}' and capture any missing support "
            f"for the final human decision (Evidence: {policy['evidence_id']}).\n"
            "Human review is required before any coding, billing, appeal, or payer-facing action.\n"
            f"Evidence reviewed: {', '.join(evidence_ids)}."
        )
        return CopilotDraft(response_text=text, cited_evidence_ids=evidence_ids)

    def _draft_ar_followup_note(self, context: dict[str, Any]) -> CopilotDraft:
        claim = context["active_claim"]
        opportunity = context["selected_opportunity"]
        work_item = context["active_work_queue_item"]
        auth = context["active_authorization"]
        evidence_ids = self._collect_ids(claim, opportunity, work_item, auth)
        text = (
            "A/R follow-up draft:\n"
            f"- Claim {claim['claim_id']} remains in status {claim['status']} after submission on "
            f"{claim['submitted_date']} with billed amount {claim['billed_amount']} (Evidence: {claim['evidence_id']}).\n"
            f"- Current queue reason is '{work_item['reason']}' and surfaced opportunity is "
            f"'{opportunity['description']}' (Evidence: {work_item['evidence_id']}, {opportunity['evidence_id']}).\n"
            f"- Confirm any available authorization or payer documentation before outreach; current authorization status "
            f"is {auth['status']} (Evidence: {auth['evidence_id']}).\n"
            "Human review is required before any coding, billing, appeal, or payer-facing action.\n"
            f"Evidence reviewed: {', '.join(evidence_ids)}."
        )
        return CopilotDraft(response_text=text, cited_evidence_ids=evidence_ids)

    def _draft_denial_appeal(self, context: dict[str, Any]) -> CopilotDraft:
        denial = context["active_denial"]
        claim = context["active_claim"]
        policy = context["active_policy"]
        evidence_ids = self._collect_ids(denial, claim, policy)
        text = (
            "Denial appeal draft:\n"
            f"- Request payer review of denial code {denial['denial_code']} for reason "
            f"'{denial['reason']}' on claim {claim['claim_id']} (Evidence: {denial['evidence_id']}, {claim['evidence_id']}).\n"
            f"- Include supporting policy and case materials relevant to requirement "
            f"'{policy['requirement']}' during human-prepared appeal review (Evidence: {policy['evidence_id']}).\n"
            "- Ask the reviewer to confirm whether any retro-authorization, exception, or documentation packet is available.\n"
            "Human review is required before any coding, billing, appeal, or payer-facing action.\n"
            f"Evidence reviewed: {', '.join(evidence_ids)}."
        )
        return CopilotDraft(response_text=text, cited_evidence_ids=evidence_ids)

    def _generate_missing_info_checklist(self, context: dict[str, Any]) -> CopilotDraft:
        opportunity = context["selected_opportunity"]
        procedure = context["procedures"][0]
        policy = context["active_policy"]
        evidence_ids = self._collect_ids(opportunity, procedure, policy)
        text = (
            "Missing information checklist:\n"
            f"- Confirm documentation or workflow support for '{opportunity['description']}' "
            f"(Evidence: {opportunity['evidence_id']}).\n"
            f"- Confirm the operative detail needed for CPT {procedure['cpt_code']} and any modifier-specific support "
            f"(Evidence: {procedure['evidence_id']}).\n"
            f"- Confirm payer-policy requirement '{policy['requirement']}' has been satisfied or addressed "
            f"(Evidence: {policy['evidence_id']}).\n"
            "Human review is required before any coding, billing, appeal, or payer-facing action.\n"
            f"Evidence reviewed: {', '.join(evidence_ids)}."
        )
        return CopilotDraft(response_text=text, cited_evidence_ids=evidence_ids)

    def _answer_question(self, context: dict[str, Any]) -> CopilotDraft:
        question = context["question"]
        opportunity = context["selected_opportunity"]
        claim = context["active_claim"]
        evidence_ids = self._collect_ids(opportunity, claim)
        text = (
            f"Question: {question}\n"
            f"From the available synthetic case context, the active issue is '{opportunity['description']}' "
            f"and the claim is currently in status {claim['status']} (Evidence: {opportunity['evidence_id']}, {claim['evidence_id']}).\n"
            "If additional workflow or documentation details are needed, request them explicitly rather than inferring them.\n"
            "Human review is required before any coding, billing, appeal, or payer-facing action.\n"
            f"Evidence reviewed: {', '.join(evidence_ids)}."
        )
        return CopilotDraft(response_text=text, cited_evidence_ids=evidence_ids)

    def _collect_ids(self, *items: dict[str, Any] | None) -> tuple[str, ...]:
        ids = []
        for item in items:
            if item and item.get("evidence_id"):
                ids.append(item["evidence_id"])
        return tuple(dict.fromkeys(ids))

    def _workflow_suggestion(self, opportunity_type: str) -> str:
        suggestions = {
            "ar_follow_up": "Confirm claim aging details, verify prior touches, and prepare a human-reviewed payer follow-up note.",
            "prebill_coding_review": "Route to coder review with documentation and policy comparison before claim release.",
            "appeal_or_writeoff_prevention": "Check for retro-authorization, exception support, and appeal packet requirements.",
        }
        return suggestions.get(
            opportunity_type,
            "Review the surfaced evidence, confirm missing data, and route to the appropriate human work queue.",
        )
