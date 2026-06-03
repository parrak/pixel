"""End-to-end synthetic ASC RCM pipeline."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from asc_rcm_lite.copilot.ar_copilot import ARCopilot
from asc_rcm_lite.copilot.coding_copilot import CodingCopilot
from asc_rcm_lite.copilot.denial_copilot import DenialCopilot
from asc_rcm_lite.copilot.payer_intelligence_copilot import PayerIntelligenceCopilot
from asc_rcm_lite.copilot.workflow_assistant import WorkflowAssistant
from asc_rcm_lite.detectors.ar import ARFlag, detect_ar_flags
from asc_rcm_lite.detectors.coding import CodingOpportunity, detect_coding_opportunities
from asc_rcm_lite.detectors.denials import DenialOpportunity, detect_denial_opportunities
from asc_rcm_lite.ingestion import DEFAULT_CASE_DIR, load_asc_case, load_asc_cases
from asc_rcm_lite.intelligence.payer_patterns import PayerPatternSummary, build_payer_pattern_summary
from asc_rcm_lite.models import ASCCase
from asc_rcm_lite.reviewer.packet import ReviewerPacket, render_packet_for_ar, render_packet_for_coding, render_packet_for_denial
from asc_rcm_lite.workflow.state import WorkflowItem
from asc_rcm_lite.workqueue import WorkQueueEntry, build_work_queue, manager_summary


DEFAULT_AS_OF_DATE = "2026-06-03"


@dataclass(frozen=True)
class CasePipelineResult:
    case_id: str
    coding_opportunities: tuple[CodingOpportunity, ...]
    ar_flags: tuple[ARFlag, ...]
    denial_opportunities: tuple[DenialOpportunity, ...]
    work_queue: tuple[WorkQueueEntry, ...]
    workflow_items: tuple[WorkflowItem, ...]
    reviewer_packets: tuple[ReviewerPacket, ...]
    copilot_summaries: tuple[str, ...]


@dataclass(frozen=True)
class PipelineResult:
    cases: tuple[CasePipelineResult, ...]
    payer_intelligence: PayerPatternSummary
    manager_metrics: dict[str, object]


def run_pipeline(
    *,
    case_id: str | None = None,
    case_dir: str | Path = DEFAULT_CASE_DIR,
    as_of_date: str = DEFAULT_AS_OF_DATE,
) -> PipelineResult:
    cases = load_asc_cases(case_dir)
    if case_id is not None:
        cases = [case for case in cases if case.case_id == case_id]
    coding_copilot = CodingCopilot()
    ar_copilot = ARCopilot()
    denial_copilot = DenialCopilot()
    workflow_assistant = WorkflowAssistant()
    all_denials: list[DenialOpportunity] = []
    all_ar_flags: list[ARFlag] = []
    results: list[CasePipelineResult] = []

    for case in cases:
        result = _run_case(
            case,
            as_of_date=as_of_date,
            coding_copilot=coding_copilot,
            ar_copilot=ar_copilot,
            denial_copilot=denial_copilot,
            workflow_assistant=workflow_assistant,
        )
        results.append(result)
        all_denials.extend(result.denial_opportunities)
        all_ar_flags.extend(result.ar_flags)

    payer_summary = build_payer_pattern_summary(tuple(cases), tuple(all_denials), tuple(all_ar_flags))
    queue = tuple(item for result in results for item in result.work_queue)
    return PipelineResult(cases=tuple(results), payer_intelligence=payer_summary, manager_metrics=manager_summary(queue))


def _run_case(
    case: ASCCase,
    *,
    as_of_date: str,
    coding_copilot: CodingCopilot,
    ar_copilot: ARCopilot,
    denial_copilot: DenialCopilot,
    workflow_assistant: WorkflowAssistant,
) -> CasePipelineResult:
    coding_items = detect_coding_opportunities(case)
    ar_flags = detect_ar_flags(case, as_of_date=as_of_date)
    denial_items = detect_denial_opportunities(case)
    work_queue = build_work_queue(ar_flags)
    workflow_items = tuple(
        WorkflowItem(
            work_item_id=item.work_item_id,
            case_id=item.case_id,
            owner_role=item.owner_role,
            queue_type=item.queue_type,
            current_state="needs_review",
            reason=item.opportunity_type,
            cited_evidence_ids=item.cited_evidence_ids,
            audit_trace=(),
        )
        for item in work_queue
    )
    packets = tuple(render_packet_for_coding(item) for item in coding_items) + tuple(
        render_packet_for_ar(item) for item in ar_flags
    ) + tuple(render_packet_for_denial(item) for item in denial_items)
    summaries: list[str] = []
    summaries.append(coding_copilot.summarize_case(case).content)
    if ar_flags:
        summaries.append(ar_copilot.summarize_followup(case, as_of_date=as_of_date).content)
    for item in denial_items:
        summaries.append(denial_copilot.denial_summary(item).content)
    for item in workflow_items:
        summaries.append(workflow_assistant.suggest_next_action(item, role=item.owner_role).content)
    return CasePipelineResult(
        case_id=case.case_id,
        coding_opportunities=coding_items,
        ar_flags=ar_flags,
        denial_opportunities=denial_items,
        work_queue=work_queue,
        workflow_items=workflow_items,
        reviewer_packets=packets,
        copilot_summaries=tuple(summaries),
    )


def _jsonable(result: PipelineResult) -> dict[str, object]:
    return {
        "cases": [
            {
                "case_id": item.case_id,
                "coding_opportunities": [opportunity.opportunity_id for opportunity in item.coding_opportunities],
                "ar_flags": [flag.flag_id for flag in item.ar_flags],
                "denial_opportunities": [opportunity.denial_id for opportunity in item.denial_opportunities],
                "work_queue_items": [queue_item.work_item_id for queue_item in item.work_queue],
                "packet_ids": [packet.packet_id for packet in item.reviewer_packets],
            }
            for item in result.cases
        ],
        "manager_metrics": result.manager_metrics,
        "payer_friction_score": result.payer_intelligence.payer_friction_score,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-id")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--as-of-date", default=DEFAULT_AS_OF_DATE)
    args = parser.parse_args(argv)

    result = run_pipeline(case_id=None if args.all or args.summary else args.case_id, as_of_date=args.as_of_date)
    if args.summary:
        print(json.dumps(result.manager_metrics, indent=2, sort_keys=True))
    else:
        print(json.dumps(_jsonable(result), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
