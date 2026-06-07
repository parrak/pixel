"""End-to-end operational journeys for key specialty RCM personas."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, timedelta
from decimal import Decimal

from asc_rcm_lite.copilot.workflow_assistant import WorkflowAssistant
from asc_rcm_lite.ingestion import load_asc_cases
from asc_rcm_lite.operations import (
    DecisionMemoryRecord,
    HumanDecision,
    OperationalTask,
    TaskOutcome,
)
from asc_rcm_lite.pipeline import DEFAULT_AS_OF_DATE, run_pipeline
from asc_rcm_lite.work_objects import build_work_objects, serialize_work_object
from asc_rcm_lite.workflow.actions import apply_workflow_action
from asc_rcm_lite.workflow.state import WorkflowItem


ROLE_TITLES = {
    "biller": "AR Specialist",
    "manager": "AR Manager",
    "vp_revenue_cycle": "VP Revenue Cycle",
}


@dataclass(frozen=True)
class JourneyStep:
    step_id: str
    label: str
    actor_role: str
    status_before: str
    status_after: str
    detail: str
    financial_impact: Decimal | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "step_id": self.step_id,
            "label": self.label,
            "actor_role": self.actor_role,
            "status_before": self.status_before,
            "status_after": self.status_after,
            "detail": self.detail,
            "financial_impact": _stringify_decimal(self.financial_impact),
        }


@dataclass(frozen=True)
class OperationalJourneyRun:
    journey_id: str
    persona: str
    title: str
    scenario: str
    queue_snapshot: dict[str, object]
    payer_history: tuple[dict[str, object], ...]
    claim_history: tuple[dict[str, object], ...]
    prior_follow_up_activity: tuple[dict[str, object], ...]
    recommendation_history: tuple[dict[str, object], ...]
    steps: tuple[JourneyStep, ...]
    metrics_before: dict[str, object]
    metrics_after: dict[str, object]
    final_task: dict[str, object]
    final_outcome: dict[str, object]
    institutional_memory_update: dict[str, object]
    workflow_trace: tuple[dict[str, object], ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "journey_id": self.journey_id,
            "persona": self.persona,
            "title": self.title,
            "scenario": self.scenario,
            "queue_snapshot": _jsonable(self.queue_snapshot),
            "payer_history": _jsonable(self.payer_history),
            "claim_history": _jsonable(self.claim_history),
            "prior_follow_up_activity": _jsonable(self.prior_follow_up_activity),
            "recommendation_history": _jsonable(self.recommendation_history),
            "steps": [step.to_dict() for step in self.steps],
            "metrics_before": _jsonable(self.metrics_before),
            "metrics_after": _jsonable(self.metrics_after),
            "final_task": _jsonable(self.final_task),
            "final_outcome": _jsonable(self.final_outcome),
            "institutional_memory_update": _jsonable(self.institutional_memory_update),
            "workflow_trace": _jsonable(self.workflow_trace),
        }


def available_journeys() -> tuple[str, ...]:
    return ("ar_specialist", "ar_manager", "vp_revenue_cycle")


def available_workflow_journeys() -> tuple[str, ...]:
    return (
        "missing_documentation_denial",
        "medical_necessity_appeal",
        "ar_follow_up",
        "authorization_failure",
    )


def execute_journey(journey_id: str, *, as_of_date: str = DEFAULT_AS_OF_DATE) -> OperationalJourneyRun:
    if journey_id == "ar_specialist":
        return execute_ar_specialist_journey(as_of_date=as_of_date)
    if journey_id == "ar_manager":
        return execute_ar_manager_journey(as_of_date=as_of_date)
    if journey_id == "vp_revenue_cycle":
        return execute_vp_revenue_cycle_journey(as_of_date=as_of_date)
    raise ValueError(f"Unsupported journey: {journey_id}")


def execute_workflow_journey(journey_id: str, *, as_of_date: str = DEFAULT_AS_OF_DATE) -> OperationalJourneyRun:
    if journey_id == "missing_documentation_denial":
        return execute_missing_documentation_denial_journey(as_of_date=as_of_date)
    if journey_id == "medical_necessity_appeal":
        return execute_medical_necessity_appeal_journey(as_of_date=as_of_date)
    if journey_id == "ar_follow_up":
        return execute_ar_follow_up_workflow_journey(as_of_date=as_of_date)
    if journey_id == "authorization_failure":
        return execute_authorization_failure_journey(as_of_date=as_of_date)
    raise ValueError(f"Unsupported workflow journey: {journey_id}")


def execute_ar_specialist_journey(*, as_of_date: str = DEFAULT_AS_OF_DATE) -> OperationalJourneyRun:
    assistant = WorkflowAssistant()
    pipeline = run_pipeline(as_of_date=as_of_date)
    case, task = _select_ar_case_and_task(pipeline)
    task = replace(
        task,
        task_id="TASK-JOURNEY-AR-SPECIALIST",
        title="90+ Day No-Payment Follow-up",
        description="Claim submitted 104 days ago. No payment received. Expected reimbursement is $12,500.",
        amount_at_risk=Decimal("12500.00"),
        aging_days=104,
        status="open",
        priority_band="urgent",
        history=(),
    )
    workflow = _workflow_item_from_task(task)
    recommendation = task.recommendations[0]
    recommendation_history = (
        {
            "stage": "initial",
            "title": recommendation.title,
            "summary": recommendation.summary,
            "suggested_action": recommendation.suggested_action,
        },
        {
            "stage": "follow_up_plan",
            "title": "Execute payer follow-up and secure reprocessing confirmation",
            "summary": "Citron recommends same-day payer outreach, reprocessing confirmation, and proof-of-call documentation before close.",
            "suggested_action": "Call payer claims unit, document reference number, and close once reprocessing is confirmed.",
        },
    )
    payer_history = _payer_history(case.claims[0].claim_id, base_date=as_of_date)
    claim_history = _claim_history(case.claims[0].claim_id, base_date=as_of_date, expected_reimbursement=Decimal("12500.00"))
    prior_follow_up = _prior_follow_up(case.claims[0].claim_id, base_date=as_of_date)
    before_metrics = {
        "queue_size": 1,
        "open_work": 1,
        "revenue_at_risk": "12500.00",
        "realized_financial_result": "0.00",
        "institutional_memory_records": 0,
    }

    steps = [
        JourneyStep("1", "Receive work in queue", "biller", "open", "open", "Claim enters the AR queue as a 90+ day no-response follow-up item."),
        JourneyStep("2", "Review payer history", "biller", "open", "open", "Specialist reviews prior payer acknowledgements and missing response windows."),
        JourneyStep("3", "Review claim history", "biller", "open", "open", "Claim submission, filing status, and expected reimbursement are validated."),
        JourneyStep("4", "Review prior follow-up activity", "biller", "open", "open", "Prior call notes confirm stale payer response and no remittance."),
        JourneyStep("5", "Review Citron recommendation", "biller", "open", "open", "Citron recommends immediate payer outreach with same-day documentation."),
        JourneyStep("6", "Generate follow-up plan", "biller", "open", "open", "Specialist plans payer outreach, callback window, and escalation trigger."),
    ]

    workflow = assistant.apply_action(
        workflow,
        action="prepare_payer_followup",
        actor_role="biller",
        reason="Prepared same-day follow-up plan based on 104-day aging and missing payer response.",
    )
    task = replace(task, status="in_progress")
    steps.append(
        JourneyStep(
            "7",
            "Document outreach",
            "biller",
            "open",
            "in_progress",
            "Payer call documented with reference number and 72-hour reprocessing commitment.",
        )
    )
    steps.append(
        JourneyStep(
            "8",
            "Escalate if required",
            "biller",
            "in_progress",
            "in_progress",
            "Escalation path reviewed. No manager escalation required after payer confirms reprocessing and payment release.",
        )
    )

    workflow = assistant.apply_action(
        workflow,
        action="close_resolved",
        actor_role="biller",
        reason="Payer confirmed claim reprocessing and expected payment release within 72 hours.",
    )
    task = _append_memory_record(
        task,
        actor_role="biller",
        actor_name=task.assignee_name or "Daniel Ortiz",
        decision_text="Completed payer follow-up and closed the AR item after reprocessing confirmation.",
        rationale="Validated claim status, documented outreach, and closed after payment was confirmed.",
        outcome_status="Payment confirmed",
        impact_summary="Aged AR item resolved after documented payer outreach.",
        financial_result=Decimal("12500.00"),
        resolution_time_hours=26,
        notes="Call reference and reprocessing confirmation added to institutional memory.",
        timestamp=_journey_timestamp(as_of_date, 0),
    )
    task = replace(task, status="completed")
    steps.append(
        JourneyStep(
            "9",
            "Resolve work item",
            "biller",
            "in_progress",
            "completed",
            "Workflow is closed after payment confirmation and documentation review.",
            financial_impact=Decimal("12500.00"),
        )
    )
    steps.append(
        JourneyStep(
            "10",
            "Record outcome",
            "biller",
            "completed",
            "completed",
            "Outcome, resolution time, and financial result are recorded in decision memory and metrics.",
            financial_impact=Decimal("12500.00"),
        )
    )
    after_metrics = {
        "queue_size": 0,
        "open_work": 0,
        "revenue_at_risk": "0.00",
        "realized_financial_result": "12500.00",
        "institutional_memory_records": len(task.history),
    }
    return OperationalJourneyRun(
        journey_id="ar_specialist",
        persona="AR Specialist",
        title=ROLE_TITLES["biller"],
        scenario="Claim submitted 104 days ago with no payment received. Expected reimbursement is $12,500.",
        queue_snapshot=_serialize_task(task, workflow.current_state),
        payer_history=payer_history,
        claim_history=claim_history,
        prior_follow_up_activity=prior_follow_up,
        recommendation_history=recommendation_history,
        steps=tuple(steps),
        metrics_before=before_metrics,
        metrics_after=after_metrics,
        final_task=_serialize_task(task, workflow.current_state),
        final_outcome=_serialize_history_record(task.history[-1]),
        institutional_memory_update={
            "history_records_added": len(task.history),
            "latest_decision": task.history[-1].decision.decision,
            "latest_outcome": task.history[-1].outcome.status,
        },
        workflow_trace=_serialize_workflow_trace(workflow),
    )


def execute_ar_manager_journey(*, as_of_date: str = DEFAULT_AS_OF_DATE) -> OperationalJourneyRun:
    pipeline = run_pipeline(as_of_date=as_of_date)
    ar_tasks = [
        replace(
            task,
            history=(),
            status="blocked" if index == 1 else "open",
            amount_at_risk=(Decimal("12500.00"), Decimal("9400.00"), Decimal("7600.00"))[index],
            aging_days=(104, 118, 92)[index],
            priority_band=("urgent", "high", "high")[index],
            task_id=f"TASK-JOURNEY-AR-MANAGER-{index + 1}",
        )
        for index, task in enumerate(_select_ar_tasks(pipeline)[:3])
    ]
    workflow_items = [_workflow_item_from_task(task, current_state="needs_review") for task in ar_tasks]
    queue_before = [_serialize_task(task, workflow.current_state) for task, workflow in zip(ar_tasks, workflow_items)]
    blocked_candidates = [task.task_id for task in ar_tasks if task.status == "blocked" or (task.aging_days or 0) >= 110]
    escalation_candidates = [task.task_id for task in ar_tasks if (task.amount_at_risk or Decimal("0.00")) >= Decimal("9000.00")]
    before_metrics = {
        "queue_size": len(ar_tasks),
        "blocked_work": len(blocked_candidates),
        "high_value_recoveries": len(escalation_candidates),
        "realized_financial_result": "0.00",
        "open_work": len(ar_tasks),
    }

    steps = [
        JourneyStep("1", "Identify bottlenecks", "manager", "open", "open", "Manager finds AR aging concentrated in 90+ day items with stale follow-up."),
        JourneyStep("2", "Review specialist workloads", "manager", "open", "open", "Workloads show one specialist carrying the highest-dollar backlog."),
        JourneyStep("3", "Review blocked work", "manager", "open", "open", f"Blocked work candidates: {', '.join(blocked_candidates)}."),
        JourneyStep("4", "Review escalation candidates", "manager", "open", "open", f"High-value escalation candidates: {', '.join(escalation_candidates)}."),
    ]

    ar_tasks[0] = replace(ar_tasks[0], assignee_name="Daniel Ortiz", assignee_user_id="user_alpha_ar", team_name="ASC Alpha AR Team", status="in_progress")
    steps.append(
        JourneyStep(
            "5",
            "Reassign work",
            "manager",
            "open",
            "in_progress",
            "Manager reassigns the top-dollar AR item to a portfolio recovery specialist with current capacity.",
        )
    )

    ar_tasks[0] = replace(ar_tasks[0], priority_band="urgent")
    ar_tasks[1] = replace(ar_tasks[1], priority_band="urgent")
    steps.append(
        JourneyStep(
            "6",
            "Prioritize high-value recoveries",
            "manager",
            "in_progress",
            "in_progress",
            "Manager moves the two largest balances to the top of the queue.",
        )
    )

    workflow_items[1] = apply_workflow_action(
        workflow_items[1],
        action="escalate_to_manager",
        actor_role="manager",
        reason="Payer non-response and 118-day aging require manager escalation.",
        cited_evidence_ids=workflow_items[1].cited_evidence_ids,
    )
    ar_tasks[1] = _append_memory_record(
        ar_tasks[1],
        actor_role="manager",
        actor_name="Morgan Lee",
        decision_text="Escalated blocked AR item and cleared payer escalation path.",
        rationale="Blocked work was aging beyond the queue target and needed direct manager intervention.",
        outcome_status="Escalation approved",
        impact_summary="Manager intervention removed the blocker and restarted the recovery workflow.",
        financial_result=Decimal("3400.00"),
        resolution_time_hours=8,
        notes="Escalation owner, payer path, and due date were recorded for future reuse.",
        timestamp=_journey_timestamp(as_of_date, 1),
    )
    ar_tasks[1] = replace(ar_tasks[1], status="in_progress")
    steps.append(
        JourneyStep(
            "7",
            "Escalate critical items",
            "manager",
            "blocked",
            "in_progress",
            "Manager escalates the blocked balance and clears the next payer action.",
            financial_impact=Decimal("3400.00"),
        )
    )

    workflow_items[0] = apply_workflow_action(
        workflow_items[0],
        action="escalate_to_manager",
        actor_role="manager",
        reason="High-value no-response account needs same-day recovery war-room support.",
        cited_evidence_ids=workflow_items[0].cited_evidence_ids,
    )
    workflow_items[0] = apply_workflow_action(
        workflow_items[0],
        action="close_resolved",
        actor_role="manager",
        reason="Manager intervention secured immediate payer commitment and specialist ownership.",
        cited_evidence_ids=workflow_items[0].cited_evidence_ids,
    )
    ar_tasks[0] = _append_memory_record(
        ar_tasks[0],
        actor_role="manager",
        actor_name="Morgan Lee",
        decision_text="Reassigned and closed the highest-value recovery item through direct intervention.",
        rationale="Manager prioritized near-term cash recovery and used portfolio capacity to resolve the account.",
        outcome_status="Manager-led recovery completed",
        impact_summary="Portfolio intervention shortened resolution time on the highest-value AR item.",
        financial_result=Decimal("12500.00"),
        resolution_time_hours=14,
        notes="Workload rebalance and escalation outcome were captured in institutional memory.",
        timestamp=_journey_timestamp(as_of_date, 0),
    )
    ar_tasks[0] = replace(ar_tasks[0], status="completed")
    after_metrics = {
        "queue_size": len(ar_tasks),
        "blocked_work": 0,
        "high_value_recoveries": 2,
        "realized_financial_result": "15900.00",
        "open_work": sum(1 for task in ar_tasks if task.status != "completed"),
    }
    steps.append(
        JourneyStep(
            "8",
            "Track intervention results",
            "manager",
            "in_progress",
            "completed",
            "Manager sees blocked work drop to zero and realized recovery increase after reassignment and escalation.",
            financial_impact=Decimal("15900.00"),
        )
    )
    return OperationalJourneyRun(
        journey_id="ar_manager",
        persona="AR Manager",
        title=ROLE_TITLES["manager"],
        scenario="Queue aging is increasing and recovery performance is declining across aged AR follow-up work.",
        queue_snapshot={
            "queue_before": queue_before,
            "queue_after": [_serialize_task(task, workflow.current_state) for task, workflow in zip(ar_tasks, workflow_items)],
            "blocked_candidates": blocked_candidates,
            "escalation_candidates": escalation_candidates,
        },
        payer_history=(),
        claim_history=(),
        prior_follow_up_activity=(),
        recommendation_history=(
            {
                "stage": "manager_recommendation",
                "title": "Concentrate management leverage on aged, high-dollar AR first",
                "summary": "Citron flags workload imbalance, blocked work, and stale follow-up as the highest-leverage manager actions.",
                "suggested_action": "Reassign the top balance, escalate blocked work, and track the immediate recovery delta.",
            },
        ),
        steps=tuple(steps),
        metrics_before=before_metrics,
        metrics_after=after_metrics,
        final_task={
            "resolved_task": _serialize_task(ar_tasks[0], workflow_items[0].current_state),
            "escalated_task": _serialize_task(ar_tasks[1], workflow_items[1].current_state),
        },
        final_outcome={
            "resolved_financial_result": "12500.00",
            "escalation_financial_result": "3400.00",
            "intervention_result": "Manager actions directly improved queue health and realized recovery.",
        },
        institutional_memory_update={
            "history_records_added": sum(len(task.history) for task in ar_tasks),
            "manager_decisions_captured": [record.decision.decision for task in ar_tasks for record in task.history],
            "blocked_work_after": 0,
        },
        workflow_trace=tuple(
            trace
            for workflow in workflow_items
            for trace in _serialize_workflow_trace(workflow)
        ),
    )


def execute_vp_revenue_cycle_journey(*, as_of_date: str = DEFAULT_AS_OF_DATE) -> OperationalJourneyRun:
    pipeline = run_pipeline(as_of_date=as_of_date)
    portfolio = pipeline.portfolio_snapshot
    holdco_dashboard = portfolio["holdco_dashboard"]
    payer_intelligence = pipeline.payer_intelligence
    manager_run = execute_ar_manager_journey(as_of_date=as_of_date)
    before_metrics = {
        "quarterly_collections_gap": "420000.00",
        "portfolio_revenue_at_risk": holdco_dashboard["revenue_at_risk"],
        "realized_ebitda_impact": holdco_dashboard["value_creation_progress"]["realized_ebitda_impact"],
        "open_work": holdco_dashboard["open_work"],
    }
    after_metrics = {
        "quarterly_collections_gap": "255000.00",
        "portfolio_revenue_at_risk": _stringify_decimal(Decimal(holdco_dashboard["revenue_at_risk"]) - Decimal("15900.00")),
        "realized_ebitda_impact": _stringify_decimal(Decimal(holdco_dashboard["value_creation_progress"]["realized_ebitda_impact"]) + Decimal("68000.00")),
        "open_work": max(int(holdco_dashboard["open_work"]) - 1, 0),
    }
    steps = [
        JourneyStep("1", "Review operational health", "vp_revenue_cycle", "at_risk", "at_risk", "VP reviews revenue at risk, open work, productivity trends, and operational risks."),
        JourneyStep("2", "Identify root causes", "vp_revenue_cycle", "at_risk", "at_risk", "Root causes cluster around denial leakage, authorization variance, and aged AR recovery."),
        JourneyStep("3", "Drill into workflow failures", "vp_revenue_cycle", "at_risk", "at_risk", "VP drills into ASC Alpha denials and ASC Charlie AR aging to find workflow failure points."),
        JourneyStep("4", "Review payer trends", "vp_revenue_cycle", "at_risk", "at_risk", "Payer friction and repeated delay patterns are reviewed across the portfolio."),
        JourneyStep("5", "Review denial patterns", "vp_revenue_cycle", "at_risk", "at_risk", "Preventable denial categories are tied back to authorization and documentation workflows."),
        JourneyStep("6", "Review productivity trends", "vp_revenue_cycle", "at_risk", "at_risk", "Productivity trends show where manager leverage can create near-term recovery."),
        JourneyStep("7", "Approve operational actions", "vp_revenue_cycle", "at_risk", "in_motion", "VP approves a 90-day recovery push, denial reduction rollout, and authorization optimization."),
        JourneyStep("8", "Measure resulting improvement", "vp_revenue_cycle", "in_motion", "improved", "VP tracks smaller collections gap, lower revenue at risk, and higher realized EBITDA impact.", financial_impact=Decimal("68000.00")),
    ]
    approved_actions = [
        {
            "initiative": "Revenue Recovery",
            "workflow": "ASC_AR_FOLLOWUP",
            "owner": "Morgan Lee",
            "financial_goal": "165000.00",
        },
        {
            "initiative": "Denial Reduction",
            "workflow": "ASC_DENIAL_REVIEW",
            "owner": "Morgan Lee",
            "financial_goal": "225000.00",
        },
        {
            "initiative": "Authorization Optimization",
            "workflow": "ASC_AUTHORIZATION",
            "owner": "Grace Lin",
            "financial_goal": "140000.00",
        },
    ]
    return OperationalJourneyRun(
        journey_id="vp_revenue_cycle",
        persona="VP Revenue Cycle",
        title=ROLE_TITLES["vp_revenue_cycle"],
        scenario="Quarterly collections are below target and leadership must connect financial underperformance to operational action.",
        queue_snapshot={
            "holdco_dashboard": holdco_dashboard,
            "manager_intervention": manager_run.final_outcome,
        },
        payer_history=tuple(
            {"payer": payer, "count": count}
            for payer, count in sorted(payer_intelligence.denials_by_payer.items())
        ),
        claim_history=tuple(
            {"cpt_code": code, "count": count}
            for code, count in sorted(payer_intelligence.denials_by_cpt.items())
        ),
        prior_follow_up_activity=tuple(
            {"root_cause": cause, "count": count}
            for cause, count in list(sorted(payer_intelligence.top_preventable_root_causes.items(), key=lambda item: item[1], reverse=True))[:3]
        ),
        recommendation_history=(
            {
                "stage": "executive_action_plan",
                "title": "Translate financial underperformance into workflow-specific interventions",
                "summary": "Citron recommends combining manager intervention, denial reduction, and authorization standardization to close the collections gap.",
                "suggested_action": "Approve portfolio operating actions and track the resulting revenue-at-risk and EBITDA delta.",
            },
        ),
        steps=tuple(steps),
        metrics_before=before_metrics,
        metrics_after=after_metrics,
        final_task={
            "approved_actions": approved_actions,
            "manager_leverage": manager_run.metrics_after,
            "portfolio_watchlist": holdco_dashboard["portfolio_health"]["watchlist_orgs"],
        },
        final_outcome={
            "collections_gap_delta": "165000.00",
            "revenue_at_risk_delta": "15900.00",
            "realized_ebitda_impact_delta": "68000.00",
            "operating_result": "VP moved from financial impact to workflow action and back to measurable improvement.",
        },
        institutional_memory_update={
            "executive_decisions_captured": len(approved_actions),
            "playbooks_reinforced": ["Revenue Recovery", "Denial Excellence", "Authorization Excellence"],
            "portfolio_learning": "Leadership actions now connect payer trends, workflow failures, and value creation initiatives.",
        },
        workflow_trace=tuple(),
    )


def execute_missing_documentation_denial_journey(*, as_of_date: str = DEFAULT_AS_OF_DATE) -> OperationalJourneyRun:
    pipeline = run_pipeline(case_id="ASC-CASE-004", as_of_date=as_of_date)
    case = next(case for case in load_asc_cases() if case.case_id == "ASC-CASE-004")
    task = next(task for task in pipeline.cases[0].operational_tasks if task.workflow_id == "asc_denial_review")
    work_object = serialize_work_object(
        build_work_objects(cases=(case,), tasks=(task,), workflows=pipeline.workflow_definitions, as_of_date=as_of_date)[0]
    )
    work_object["work_object_type"] = "Missing Documentation"
    work_object["title"] = "Missing Documentation Denial"
    return OperationalJourneyRun(
        journey_id="missing_documentation_denial",
        persona="Denial Specialist",
        title="Missing Documentation Denial",
        scenario="Claim -> denial -> classification -> evidence collection -> packet assembly -> submission -> resolution.",
        queue_snapshot=work_object,
        payer_history=tuple(),
        claim_history=tuple(),
        prior_follow_up_activity=tuple(),
        recommendation_history=tuple(work_object["recommendations"]),
        steps=(
            JourneyStep("1", "Claim", "denial_specialist", "Agent Processing", "Human Action Required", "Denied claim is surfaced as a missing-documentation work object."),
            JourneyStep("2", "Denial", "denial_specialist", "Human Action Required", "Human Action Required", "Denial is classified and linked to missing supporting documentation."),
            JourneyStep("3", "Classification", "denial_specialist", "Human Action Required", "Human Action Required", "Workflow is routed into denial review with claim-linked evidence."),
            JourneyStep("4", "Evidence Collection", "denial_specialist", "Human Action Required", "Human Action Required", "Payer rule, denial text, and supporting documentation checklist are assembled."),
            JourneyStep("5", "Packet Assembly", "denial_specialist", "Human Action Required", "Human Action Required", "Appeal packet and claim timeline are generated as usable work product."),
            JourneyStep("6", "Submission", "denial_specialist", "Human Action Required", "Completed", "Appeal is submitted with assembled documentation."),
            JourneyStep("7", "Resolution", "denial_specialist", "Completed", "Completed", "Outcome, timeline, and memory are recorded for reuse.", financial_impact=Decimal("2950.00")),
        ),
        metrics_before={"open_work": 1, "timeline_events": len(work_object["timeline"]), "financial_impact": work_object["financial_impact"]},
        metrics_after={"open_work": 0, "timeline_events": len(work_object["timeline"]), "financial_impact": work_object["outcome"]["financial_result"]},
        final_task=work_object,
        final_outcome=work_object["outcome"],
        institutional_memory_update={"entries": len(work_object["institutional_memory"]), "timeline_events": len(work_object["timeline"])},
        workflow_trace=tuple(),
    )


def execute_medical_necessity_appeal_journey(*, as_of_date: str = DEFAULT_AS_OF_DATE) -> OperationalJourneyRun:
    pipeline = run_pipeline(case_id="ASC-CASE-004", as_of_date=as_of_date)
    case = next(case for case in load_asc_cases() if case.case_id == "ASC-CASE-004")
    task = next(task for task in pipeline.cases[0].operational_tasks if task.task_type == "medical_necessity")
    work_object = serialize_work_object(
        build_work_objects(cases=(case,), tasks=(task,), workflows=pipeline.workflow_definitions, as_of_date=as_of_date)[0]
    )
    return OperationalJourneyRun(
        journey_id="medical_necessity_appeal",
        persona="Denial Specialist",
        title="Medical Necessity Appeal",
        scenario="Claim -> denial -> clinical evidence -> appeal packet -> submission -> decision.",
        queue_snapshot=work_object,
        payer_history=tuple(),
        claim_history=tuple(),
        prior_follow_up_activity=tuple(),
        recommendation_history=tuple(work_object["recommendations"]),
        steps=(
            JourneyStep("1", "Claim", "denial_specialist", "Agent Processing", "Human Action Required", "Claim lands with a medical-necessity denial work object."),
            JourneyStep("2", "Denial", "denial_specialist", "Human Action Required", "Human Action Required", "Denial category and payer rationale are surfaced."),
            JourneyStep("3", "Clinical Evidence", "denial_specialist", "Human Action Required", "Human Action Required", "Clinical support, payer rule, and similar outcomes are assembled."),
            JourneyStep("4", "Appeal Packet", "denial_specialist", "Human Action Required", "Human Action Required", "Operator receives an appeal packet, claim timeline, and checklist."),
            JourneyStep("5", "Submission", "denial_specialist", "Human Action Required", "Completed", "Appeal is submitted using the generated work product."),
            JourneyStep("6", "Decision", "denial_specialist", "Completed", "Completed", "Result is recorded back into the work object and institutional memory.", financial_impact=Decimal("768.00")),
        ),
        metrics_before={"open_work": 1, "documents_generated": len(work_object["documents"]), "financial_impact": work_object["financial_impact"]},
        metrics_after={"open_work": 0, "documents_generated": len(work_object["documents"]), "financial_impact": work_object["outcome"]["financial_result"]},
        final_task=work_object,
        final_outcome=work_object["outcome"],
        institutional_memory_update={"entries": len(work_object["institutional_memory"]), "documents": len(work_object["documents"])},
        workflow_trace=tuple(),
    )


def execute_ar_follow_up_workflow_journey(*, as_of_date: str = DEFAULT_AS_OF_DATE) -> OperationalJourneyRun:
    pipeline = run_pipeline(case_id="ASC-CASE-008", as_of_date=as_of_date)
    case = next(case for case in load_asc_cases() if case.case_id == "ASC-CASE-008")
    task = next(task for task in pipeline.cases[0].operational_tasks if task.workflow_id == "asc_ar_followup")
    work_object = serialize_work_object(
        build_work_objects(cases=(case,), tasks=(task,), workflows=pipeline.workflow_definitions, as_of_date=as_of_date)[0]
    )
    work_object["financial_impact"] = "12500.00"
    run = execute_ar_specialist_journey(as_of_date=as_of_date)
    return OperationalJourneyRun(
        journey_id="ar_follow_up",
        persona=run.persona,
        title="AR Follow-Up",
        scenario="Claim -> aging trigger -> follow-up -> escalation -> recovery.",
        queue_snapshot=work_object,
        payer_history=run.payer_history,
        claim_history=run.claim_history,
        prior_follow_up_activity=run.prior_follow_up_activity,
        recommendation_history=run.recommendation_history,
        steps=(
            JourneyStep("1", "Claim", "biller", "Agent Processing", "Human Action Required", "Claim is open and aging without payment."),
            JourneyStep("2", "Aging Trigger", "biller", "Human Action Required", "Human Action Required", "90+ day trigger converts the claim into an AR follow-up work object."),
            JourneyStep("3", "Follow-Up", "biller", "Human Action Required", "Human Action Required", "Operator reviews evidence and executes payer outreach."),
            JourneyStep("4", "Escalation", "biller", "Human Action Required", "Human Action Required", "Escalation path is visible if payer response fails."),
            JourneyStep("5", "Recovery", "biller", "Human Action Required", "Completed", "Recovered dollars, timeline, and memory are recorded.", financial_impact=Decimal("12500.00")),
        ),
        metrics_before=run.metrics_before,
        metrics_after=run.metrics_after,
        final_task=run.final_task,
        final_outcome=run.final_outcome,
        institutional_memory_update=run.institutional_memory_update,
        workflow_trace=run.workflow_trace,
    )


def execute_authorization_failure_journey(*, as_of_date: str = DEFAULT_AS_OF_DATE) -> OperationalJourneyRun:
    pipeline = run_pipeline(case_id="ASC-CASE-002", as_of_date=as_of_date)
    case = next(case for case in load_asc_cases() if case.case_id == "ASC-CASE-002")
    task = next(task for task in pipeline.cases[0].operational_tasks if task.workflow_id == "asc_authorization")
    work_object = serialize_work_object(
        build_work_objects(cases=(case,), tasks=(task,), workflows=pipeline.workflow_definitions, as_of_date=as_of_date)[0]
    )
    return OperationalJourneyRun(
        journey_id="authorization_failure",
        persona="Authorization Specialist",
        title="Authorization Failure",
        scenario="Scheduled case -> missing auth -> coordination -> resolution.",
        queue_snapshot=work_object,
        payer_history=tuple(),
        claim_history=tuple(),
        prior_follow_up_activity=tuple(),
        recommendation_history=tuple(work_object["recommendations"]),
        steps=(
            JourneyStep("1", "Scheduled Case", "auth_specialist", "Agent Processing", "Human Action Required", "Scheduled case is linked to a missing-authorization work object."),
            JourneyStep("2", "Missing Auth", "auth_specialist", "Human Action Required", "Human Action Required", "Authorization failure is classified with payer rule evidence."),
            JourneyStep("3", "Coordination", "auth_specialist", "Human Action Required", "Human Action Required", "Authorization packet and checklist are generated for payer/provider coordination."),
            JourneyStep("4", "Resolution", "auth_specialist", "Human Action Required", "Completed", "Resolution and financial impact are written back into the work object.", financial_impact=Decimal("1152.00")),
        ),
        metrics_before={"open_work": 1, "documents_generated": len(work_object["documents"]), "financial_impact": work_object["financial_impact"]},
        metrics_after={"open_work": 0, "documents_generated": len(work_object["documents"]), "financial_impact": work_object["outcome"]["financial_result"]},
        final_task=work_object,
        final_outcome=work_object["outcome"],
        institutional_memory_update={"entries": len(work_object["institutional_memory"]), "timeline_events": len(work_object["timeline"])},
        workflow_trace=tuple(),
    )


def _select_ar_case_and_task(pipeline_result):
    cases_by_id = {case.case_id: case for case in load_asc_cases()}
    for case_result in pipeline_result.cases:
        for task in case_result.operational_tasks:
            if task.workflow_id == "asc_ar_followup":
                case = cases_by_id[task.case_id]
                return case, task
    raise ValueError("No AR follow-up task found in pipeline")


def _select_ar_tasks(pipeline_result) -> list[OperationalTask]:
    tasks = [task for case in pipeline_result.cases for task in case.operational_tasks if task.workflow_id == "asc_ar_followup"]
    if len(tasks) < 3:
        raise ValueError("Expected at least three AR follow-up tasks for manager journey")
    return sorted(tasks, key=lambda item: (item.amount_at_risk or Decimal("0.00")), reverse=True)


def _workflow_item_from_task(task: OperationalTask, *, current_state: str = "needs_review") -> WorkflowItem:
    return WorkflowItem(
        work_item_id=task.task_id.replace("TASK-", "WQ-"),
        case_id=task.case_id,
        owner_role=task.owner_role,
        queue_type=task.queue_name.lower().replace(" ", "_"),
        current_state=current_state,
        reason=task.description,
        cited_evidence_ids=task.cited_evidence_ids,
        audit_trace=(),
    )


def _append_memory_record(
    task: OperationalTask,
    *,
    actor_role: str,
    actor_name: str,
    decision_text: str,
    rationale: str,
    outcome_status: str,
    impact_summary: str,
    financial_result: Decimal,
    resolution_time_hours: int,
    notes: str,
    timestamp: str,
) -> OperationalTask:
    recommendation = task.recommendations[0]
    decision = HumanDecision(
        decision_id=f"DEC-{task.task_id}-{len(task.history) + 1}",
        task_id=task.task_id,
        recommendation_id=recommendation.recommendation_id,
        decision=decision_text,
        actor_role=actor_role,
        actor_name=actor_name,
        rationale=rationale,
        timestamp=timestamp,
    )
    outcome = TaskOutcome(
        outcome_id=f"OUT-{task.task_id}-{len(task.history) + 1}",
        task_id=task.task_id,
        status=outcome_status,
        impact_summary=impact_summary,
        value_realized=financial_result,
        notes=notes,
        financial_result=financial_result,
        resolution_time_hours=resolution_time_hours,
    )
    record = DecisionMemoryRecord(
        record_id=f"MEM-{task.task_id}-{len(task.history) + 1}",
        task_id=task.task_id,
        workflow_stage=task.workflow_stage or "resolution",
        recommendation_title=recommendation.title,
        recommendation_summary=recommendation.summary,
        decision=decision,
        outcome=outcome,
    )
    return replace(task, history=task.history + (record,), decision=decision, outcome=outcome)


def _serialize_task(task: OperationalTask, workflow_state: str) -> dict[str, object]:
    return {
        "task_id": task.task_id,
        "title": task.title,
        "organization": task.organization_name,
        "facility": task.facility_name,
        "queue_name": task.queue_name,
        "owner_role": task.owner_role,
        "assignee_name": task.assignee_name,
        "status": task.status,
        "workflow_state": workflow_state,
        "priority_band": task.priority_band,
        "amount_at_risk": _stringify_decimal(task.amount_at_risk),
        "aging_days": task.aging_days,
        "recommendation": {
            "title": task.recommendations[0].title,
            "summary": task.recommendations[0].summary,
            "suggested_action": task.recommendations[0].suggested_action,
        },
        "history_count": len(task.history),
    }


def _serialize_history_record(record: DecisionMemoryRecord) -> dict[str, object]:
    return {
        "record_id": record.record_id,
        "decision": record.decision.decision,
        "actor_role": record.decision.actor_role,
        "actor_name": record.decision.actor_name,
        "outcome": record.outcome.status,
        "financial_result": _stringify_decimal(record.outcome.financial_result),
        "resolution_time_hours": record.outcome.resolution_time_hours,
        "notes": record.outcome.notes,
    }


def _serialize_workflow_trace(workflow_item: WorkflowItem) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "event_id": event.event_id,
            "previous_state": event.previous_state,
            "next_state": event.next_state,
            "action": event.action,
            "actor_role": event.actor_role,
            "reason": event.reason,
        }
        for event in workflow_item.audit_trace
    )


def _payer_history(claim_id: str, *, base_date: str) -> tuple[dict[str, object], ...]:
    return (
        {"date": _days_before(base_date, 97), "event": "Claim accepted into payer system", "claim_id": claim_id},
        {"date": _days_before(base_date, 74), "event": "No remittance received within standard cycle time", "claim_id": claim_id},
        {"date": _days_before(base_date, 33), "event": "Payer representative requested additional research time", "claim_id": claim_id},
    )


def _claim_history(claim_id: str, *, base_date: str, expected_reimbursement: Decimal) -> tuple[dict[str, object], ...]:
    return (
        {"date": _days_before(base_date, 104), "event": "Claim submitted electronically", "claim_id": claim_id},
        {"date": _days_before(base_date, 103), "event": "Clearinghouse acceptance confirmed", "claim_id": claim_id},
        {"date": _days_before(base_date, 1), "event": "Expected reimbursement still outstanding", "claim_id": claim_id, "expected_reimbursement": _stringify_decimal(expected_reimbursement)},
    )


def _prior_follow_up(claim_id: str, *, base_date: str) -> tuple[dict[str, object], ...]:
    return (
        {"date": _days_before(base_date, 63), "channel": "phone", "summary": "Payer advised claim was under review", "claim_id": claim_id},
        {"date": _days_before(base_date, 29), "channel": "portal", "summary": "No update posted in portal after review window", "claim_id": claim_id},
    )


def _days_before(base_date: str, days: int) -> str:
    value = date.fromisoformat(base_date) - timedelta(days=days)
    return value.isoformat()


def _journey_timestamp(base_date: str, offset_days: int) -> str:
    value = date.fromisoformat(base_date) + timedelta(days=offset_days)
    return f"{value.isoformat()}T09:00:00Z"


def _stringify_decimal(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return f"{value:.2f}"


def _jsonable(value):
    if isinstance(value, Decimal):
        return _stringify_decimal(value)
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    return value
