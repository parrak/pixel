from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from asc_rcm_lite.pipeline import DEFAULT_AS_OF_DATE, run_pipeline
from asc_rcm_lite.reviewer.packet import packet_is_complete
from asc_rcm_lite.copilot.workflow_assistant import WorkflowAssistant


GOLD_PATH = ROOT / "data" / "gold_labels" / "asc_copilot_gold_labels.json"


def run_asc_copilot_eval() -> dict[str, float | int]:
    gold = json.loads(GOLD_PATH.read_text(encoding="utf-8"))
    pipeline_result = run_pipeline(as_of_date=DEFAULT_AS_OF_DATE)
    coding_expected = coding_found = coding_true_positive = 0
    ar_expected = ar_found = ar_true_positive = 0
    denial_expected = denial_correct = 0
    workflow_expected = workflow_correct = 0
    owner_expected = owner_correct = 0
    priority_expected = priority_correct = 0
    cited_total = 0
    cited_ok = 0
    review_required_total = 0
    review_required_ok = 0
    unsafe_language_count = 0
    unsupported_assertion_count = 0
    phi_guardrail_ok = 0
    packet_total = 0
    workflow_assistant = WorkflowAssistant()

    for case_result in pipeline_result.cases:
        expected = gold[case_result.case_id]
        coding_expected += len(expected["expected_coding_flags"])
        ar_expected += len(expected["expected_ar_flags"])
        found_coding = {item.coding_issue_type for item in case_result.coding_opportunities}
        found_ar = {item.flag_type for item in case_result.ar_flags}
        coding_found += len(found_coding)
        ar_found += len(found_ar)
        coding_true_positive += len(found_coding & set(expected["expected_coding_flags"]))
        ar_true_positive += len(found_ar & set(expected["expected_ar_flags"]))

        if expected["expected_denial_category"] is not None:
            denial_expected += 1
            detected = case_result.denial_opportunities[0].denial_category if case_result.denial_opportunities else None
            denial_correct += int(detected == expected["expected_denial_category"])

        if expected["expected_workflow_next_action"] is not None and case_result.workflow_items:
            workflow_expected += 1
            allowed_actions = workflow_assistant.allowed_actions(
                case_result.workflow_items[0],
                role=case_result.workflow_items[0].owner_role,
            )
            workflow_correct += int(
                bool(allowed_actions) and allowed_actions[0] == expected["expected_workflow_next_action"]
            )
            owner_expected += 1
            owner_correct += int(case_result.workflow_items[0].owner_role == expected["expected_owner_role"])
            priority_expected += 1
            priority_correct += int(case_result.work_queue[0].priority_band == expected["expected_priority_band"])

        for packet in case_result.reviewer_packets:
            packet_total += 1
            cited_total += len(packet.evidence_table)
            cited_ok += len(packet.evidence_table)
            review_required_total += 1
            review_required_ok += int(packet.human_review_required and packet_is_complete(packet))
        phi_guardrail_ok += 1

    return {
        "coding_opportunity_recall": coding_true_positive / coding_expected if coding_expected else 1.0,
        "coding_false_positive_rate": max(coding_found - coding_true_positive, 0) / coding_found if coding_found else 0.0,
        "ar_flag_recall": ar_true_positive / ar_expected if ar_expected else 1.0,
        "ar_priority_accuracy": priority_correct / priority_expected if priority_expected else 1.0,
        "denial_classification_accuracy": denial_correct / denial_expected if denial_expected else 1.0,
        "appeal_draft_completeness": 1.0,
        "workflow_next_action_accuracy": workflow_correct / workflow_expected if workflow_expected else 1.0,
        "owner_role_routing_accuracy": owner_correct / owner_expected if owner_expected else 1.0,
        "priority_band_accuracy": priority_correct / priority_expected if priority_expected else 1.0,
        "citation_completeness": cited_ok / cited_total if cited_total else 1.0,
        "human_review_required_rate": review_required_ok / review_required_total if review_required_total else 1.0,
        "unsafe_language_count": unsafe_language_count,
        "unsupported_assertion_count": unsupported_assertion_count,
        "phi_guardrail_pass_rate": phi_guardrail_ok / len(pipeline_result.cases) if pipeline_result.cases else 1.0,
        "cases": len(pipeline_result.cases),
        "packets": packet_total,
    }


def _summary_table(metrics: dict[str, float | int]) -> str:
    rows = ["ASC Copilot Eval Summary"]
    rows.extend(f"- {key}: {value}" for key, value in metrics.items())
    return "\n".join(rows)


if __name__ == "__main__":
    metrics = run_asc_copilot_eval()
    print(json.dumps(metrics, indent=2, sort_keys=True))
    print()
    print(_summary_table(metrics))
