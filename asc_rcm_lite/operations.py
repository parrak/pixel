"""Task-centric operating-system layer for synthetic specialty RCM workflows."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from asc_rcm_lite.detectors.ar import ARFlag
from asc_rcm_lite.detectors.coding import CodingOpportunity
from asc_rcm_lite.detectors.denials import DenialOpportunity
from asc_rcm_lite.models import ASCCase, ValidationError, require_non_empty


WORKFLOW_STATUSES = {"open", "in_progress", "blocked", "completed"}


@dataclass(frozen=True)
class WorkflowDefinition:
    workflow_id: str
    name: str
    description: str
    queue_name: str
    owner_roles: tuple[str, ...]
    trigger_sources: tuple[str, ...]
    target_outcomes: tuple[str, ...]
    service_level_hours: int

    def __post_init__(self) -> None:
        require_non_empty(self.workflow_id, "WorkflowDefinition.workflow_id")
        require_non_empty(self.name, "WorkflowDefinition.name")
        require_non_empty(self.description, "WorkflowDefinition.description")
        require_non_empty(self.queue_name, "WorkflowDefinition.queue_name")
        if not self.owner_roles:
            raise ValidationError("WorkflowDefinition.owner_roles must not be empty")
        if self.service_level_hours <= 0:
            raise ValidationError("WorkflowDefinition.service_level_hours must be positive")


@dataclass(frozen=True)
class TaskRecommendation:
    recommendation_id: str
    task_id: str
    producer: str
    category: str
    title: str
    summary: str
    rationale: str
    suggested_action: str
    confidence_label: str
    priority_band: str
    cited_evidence_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        require_non_empty(self.recommendation_id, "TaskRecommendation.recommendation_id")
        require_non_empty(self.task_id, "TaskRecommendation.task_id")
        require_non_empty(self.producer, "TaskRecommendation.producer")
        require_non_empty(self.category, "TaskRecommendation.category")
        require_non_empty(self.title, "TaskRecommendation.title")
        require_non_empty(self.summary, "TaskRecommendation.summary")
        require_non_empty(self.rationale, "TaskRecommendation.rationale")
        require_non_empty(self.suggested_action, "TaskRecommendation.suggested_action")
        require_non_empty(self.confidence_label, "TaskRecommendation.confidence_label")
        require_non_empty(self.priority_band, "TaskRecommendation.priority_band")
        if not self.cited_evidence_ids:
            raise ValidationError("TaskRecommendation.cited_evidence_ids must not be empty")


@dataclass(frozen=True)
class HumanDecision:
    decision_id: str
    task_id: str
    recommendation_id: str
    decision: str
    actor_role: str
    rationale: str
    timestamp: str

    def __post_init__(self) -> None:
        require_non_empty(self.decision_id, "HumanDecision.decision_id")
        require_non_empty(self.task_id, "HumanDecision.task_id")
        require_non_empty(self.recommendation_id, "HumanDecision.recommendation_id")
        require_non_empty(self.decision, "HumanDecision.decision")
        require_non_empty(self.actor_role, "HumanDecision.actor_role")
        require_non_empty(self.rationale, "HumanDecision.rationale")
        require_non_empty(self.timestamp, "HumanDecision.timestamp")


@dataclass(frozen=True)
class TaskOutcome:
    outcome_id: str
    task_id: str
    status: str
    impact_summary: str
    value_realized: Decimal | None
    notes: str

    def __post_init__(self) -> None:
        require_non_empty(self.outcome_id, "TaskOutcome.outcome_id")
        require_non_empty(self.task_id, "TaskOutcome.task_id")
        require_non_empty(self.status, "TaskOutcome.status")
        require_non_empty(self.impact_summary, "TaskOutcome.impact_summary")
        require_non_empty(self.notes, "TaskOutcome.notes")


@dataclass(frozen=True)
class OperationalTask:
    task_id: str
    case_id: str
    workflow_id: str
    workflow_name: str
    queue_name: str
    task_type: str
    title: str
    description: str
    status: str
    owner_role: str
    priority_band: str
    amount_at_risk: Decimal | None
    due_date: str | None
    aging_days: int | None
    source_case_scenario: str
    cited_evidence_ids: tuple[str, ...]
    recommendations: tuple[TaskRecommendation, ...]
    source_refs: tuple[str, ...]
    decision: HumanDecision | None = None
    outcome: TaskOutcome | None = None

    def __post_init__(self) -> None:
        require_non_empty(self.task_id, "OperationalTask.task_id")
        require_non_empty(self.case_id, "OperationalTask.case_id")
        require_non_empty(self.workflow_id, "OperationalTask.workflow_id")
        require_non_empty(self.workflow_name, "OperationalTask.workflow_name")
        require_non_empty(self.queue_name, "OperationalTask.queue_name")
        require_non_empty(self.task_type, "OperationalTask.task_type")
        require_non_empty(self.title, "OperationalTask.title")
        require_non_empty(self.description, "OperationalTask.description")
        require_non_empty(self.status, "OperationalTask.status")
        require_non_empty(self.owner_role, "OperationalTask.owner_role")
        require_non_empty(self.priority_band, "OperationalTask.priority_band")
        require_non_empty(self.source_case_scenario, "OperationalTask.source_case_scenario")
        if self.status not in WORKFLOW_STATUSES:
            raise ValidationError(f"Unsupported OperationalTask.status: {self.status}")
        if not self.cited_evidence_ids:
            raise ValidationError("OperationalTask.cited_evidence_ids must not be empty")
        if not self.recommendations:
            raise ValidationError("OperationalTask.recommendations must not be empty")


WORKFLOW_CATALOG = (
    WorkflowDefinition(
        workflow_id="asc_authorization",
        name="ASC Authorization",
        description="Work needed to validate, obtain, or remediate authorization readiness for ASC claims.",
        queue_name="Authorization",
        owner_roles=("auth_specialist", "manager"),
        trigger_sources=("authorization", "denial"),
        target_outcomes=("authorization secured", "denial prevented"),
        service_level_hours=24,
    ),
    WorkflowDefinition(
        workflow_id="asc_coding_review",
        name="ASC Coding Review",
        description="Pre-bill and post-bill coding validation for specialty ASC encounters.",
        queue_name="Coding Review",
        owner_roles=("coder", "manager"),
        trigger_sources=("coding", "pre_bill"),
        target_outcomes=("claim corrected", "risk avoided"),
        service_level_hours=24,
    ),
    WorkflowDefinition(
        workflow_id="asc_denials",
        name="ASC Denials",
        description="Denial triage, evidence collection, and routing before appeal or escalation.",
        queue_name="Denials",
        owner_roles=("denial_specialist", "manager"),
        trigger_sources=("denial", "ar"),
        target_outcomes=("appeal ready", "denial resolved"),
        service_level_hours=48,
    ),
    WorkflowDefinition(
        workflow_id="asc_appeals",
        name="ASC Appeals",
        description="Appeal drafting, submission readiness, and underpayment recovery workflow.",
        queue_name="Appeals",
        owner_roles=("denial_specialist", "biller", "manager"),
        trigger_sources=("denial", "underpayment"),
        target_outcomes=("recovery submitted", "revenue recovered"),
        service_level_hours=72,
    ),
    WorkflowDefinition(
        workflow_id="asc_charge_capture",
        name="ASC Charge Capture",
        description="Charge integrity and implant or supply capture for specialty facility work.",
        queue_name="Charge Capture",
        owner_roles=("coder", "biller", "manager"),
        trigger_sources=("charge_capture", "pre_bill"),
        target_outcomes=("charge completeness", "additional revenue captured"),
        service_level_hours=24,
    ),
    WorkflowDefinition(
        workflow_id="asc_ar_follow_up",
        name="ASC AR Follow-Up",
        description="A/R aging, status validation, and follow-up orchestration for unresolved specialty claims.",
        queue_name="AR Follow-Up",
        owner_roles=("biller", "manager"),
        trigger_sources=("ar",),
        target_outcomes=("payer response obtained", "claim moved forward"),
        service_level_hours=48,
    ),
)


def workflow_catalog() -> tuple[WorkflowDefinition, ...]:
    return WORKFLOW_CATALOG


def build_operational_tasks(
    case: ASCCase,
    *,
    coding_items: tuple[CodingOpportunity, ...],
    ar_flags: tuple[ARFlag, ...],
    denial_items: tuple[DenialOpportunity, ...],
    as_of_date: str,
) -> tuple[OperationalTask, ...]:
    tasks: list[OperationalTask] = []

    for item in coding_items:
        workflow_id = "asc_charge_capture" if "implant" in item.coding_issue_type else "asc_coding_review"
        definition = _workflow(workflow_id)
        tasks.append(
            OperationalTask(
                task_id=f"TASK-{item.opportunity_id}",
                case_id=item.case_id,
                workflow_id=definition.workflow_id,
                workflow_name=definition.name,
                queue_name=definition.queue_name,
                task_type=item.coding_issue_type,
                title=item.coding_issue_type.replace("_", " ").title(),
                description=item.risk_reason,
                status="open",
                owner_role="coder",
                priority_band=_coding_priority_band(item.severity),
                amount_at_risk=item.financial_impact_estimate,
                due_date=_case_due_date(case),
                aging_days=_case_age_days(case, as_of_date),
                source_case_scenario=case.scenario,
                cited_evidence_ids=item.evidence_citation_ids,
                source_refs=(item.source, item.opportunity_id),
                recommendations=(
                    TaskRecommendation(
                        recommendation_id=f"REC-{item.opportunity_id}",
                        task_id=f"TASK-{item.opportunity_id}",
                        producer="coding_detector",
                        category="coding_review",
                        title="Validate coding risk",
                        summary=item.risk_reason,
                        rationale=item.risk_reason,
                        suggested_action=item.suggested_human_review_action,
                        confidence_label="high",
                        priority_band=_coding_priority_band(item.severity),
                        cited_evidence_ids=item.evidence_citation_ids,
                    ),
                ),
            )
        )

    for item in ar_flags:
        workflow_id = "asc_appeals" if item.flag_type == "underpayment" else "asc_ar_follow_up"
        if item.flag_type == "appeal_deadline_risk":
            workflow_id = "asc_denials"
        definition = _workflow(workflow_id)
        tasks.append(
            OperationalTask(
                task_id=f"TASK-{item.flag_id}",
                case_id=item.case_id,
                workflow_id=definition.workflow_id,
                workflow_name=definition.name,
                queue_name=definition.queue_name,
                task_type=item.flag_type,
                title=_titleize(item.flag_type),
                description=item.reason_for_flag,
                status="open",
                owner_role=item.owner_role,
                priority_band=item.priority_band,
                amount_at_risk=item.balance,
                due_date=item.next_deadline,
                aging_days=item.days_in_ar,
                source_case_scenario=case.scenario,
                cited_evidence_ids=item.evidence_citation_ids,
                source_refs=("ar_flag", item.flag_id),
                recommendations=(
                    TaskRecommendation(
                        recommendation_id=f"REC-{item.flag_id}",
                        task_id=f"TASK-{item.flag_id}",
                        producer="ar_detector",
                        category="operational_follow_up",
                        title="Prioritize operational follow-up",
                        summary=item.reason_for_flag,
                        rationale=item.reason_for_flag,
                        suggested_action=item.recommended_next_action,
                        confidence_label="high",
                        priority_band=item.priority_band,
                        cited_evidence_ids=item.evidence_citation_ids,
                    ),
                ),
            )
        )

    for item in denial_items:
        workflow_id = "asc_appeals" if item.recommended_path == "appeal" else "asc_denials"
        if item.denial_category == "prior_authorization":
            workflow_id = "asc_authorization"
        definition = _workflow(workflow_id)
        priority = "urgent" if item.appealability == "likely" else "high"
        owner = "auth_specialist" if workflow_id == "asc_authorization" else "denial_specialist"
        tasks.append(
            OperationalTask(
                task_id=f"TASK-{item.denial_id}",
                case_id=item.case_id,
                workflow_id=definition.workflow_id,
                workflow_name=definition.name,
                queue_name=definition.queue_name,
                task_type=item.denial_category,
                title=_titleize(item.denial_category),
                description=item.root_cause_hypothesis,
                status="open",
                owner_role=owner,
                priority_band=priority,
                amount_at_risk=item.amount_at_risk,
                due_date=item.deadline,
                aging_days=_case_age_days(case, as_of_date),
                source_case_scenario=case.scenario,
                cited_evidence_ids=item.evidence_citation_ids,
                source_refs=("denial_detector", item.denial_id),
                recommendations=(
                    TaskRecommendation(
                        recommendation_id=f"REC-{item.denial_id}",
                        task_id=f"TASK-{item.denial_id}",
                        producer="denial_detector",
                        category="denial_resolution",
                        title="Review denial path",
                        summary=item.next_best_action,
                        rationale=item.root_cause_hypothesis,
                        suggested_action=item.next_best_action,
                        confidence_label="medium" if item.appealability == "uncertain" else "high",
                        priority_band=priority,
                        cited_evidence_ids=item.evidence_citation_ids,
                    ),
                ),
            )
        )

    if not tasks:
        for item in case.work_queue_items:
            workflow_id = _workflow_id_from_queue(item.queue, item.reason)
            definition = _workflow(workflow_id)
            tasks.append(
                OperationalTask(
                    task_id=f"TASK-{item.work_queue_item_id}",
                    case_id=case.case_id,
                    workflow_id=definition.workflow_id,
                    workflow_name=definition.name,
                    queue_name=definition.queue_name,
                    task_type=item.queue,
                    title=item.reason,
                    description=f"Seeded work queue item for {definition.name.lower()}.",
                    status="open" if item.status == "open" else "in_progress",
                    owner_role=_owner_from_workflow(definition.workflow_id),
                    priority_band="high" if item.due_date else "normal",
                    amount_at_risk=None,
                    due_date=item.due_date,
                    aging_days=_case_age_days(case, as_of_date),
                    source_case_scenario=case.scenario,
                    cited_evidence_ids=(item.citation.source_id,),
                    recommendations=(
                        TaskRecommendation(
                            recommendation_id=f"REC-{item.work_queue_item_id}",
                            task_id=f"TASK-{item.work_queue_item_id}",
                            producer="workflow_seed",
                            category="workflow_routing",
                            title="Route operational work",
                            summary=item.reason,
                            rationale=f"Seeded workflow item from the synthetic {item.queue} queue.",
                            suggested_action=f"Review the {definition.name.lower()} workflow and confirm the next step for human review.",
                            confidence_label="medium",
                            priority_band="high" if item.due_date else "normal",
                            cited_evidence_ids=(item.citation.source_id,),
                        ),
                    ),
                    source_refs=("seeded_work_queue", item.work_queue_item_id),
                )
            )

    return tuple(sorted(tasks, key=lambda task: (_priority_rank(task.priority_band), task.workflow_name, task.task_id)))


def build_operational_dashboard(tasks: tuple[OperationalTask, ...]) -> dict[str, object]:
    total_at_risk = sum((task.amount_at_risk or Decimal("0.00") for task in tasks), Decimal("0.00"))
    workflow_counts = {
        workflow.name: sum(1 for task in tasks if task.workflow_id == workflow.workflow_id)
        for workflow in workflow_catalog()
    }
    owner_load = {
        role: sum(1 for task in tasks if task.owner_role == role)
        for role in sorted({task.owner_role for task in tasks})
    }
    return {
        "total_tasks": len(tasks),
        "open_work": sum(1 for task in tasks if task.status != "completed"),
        "revenue_at_risk": str(total_at_risk),
        "recovery_pipeline": str(
            sum(
                (task.amount_at_risk or Decimal("0.00"))
                for task in tasks
                if task.workflow_id in {"asc_denials", "asc_appeals", "asc_ar_follow_up"}
            )
        ),
        "workflow_counts": workflow_counts,
        "queue_aging": {
            "0_30": sum(1 for task in tasks if task.aging_days is not None and task.aging_days <= 30),
            "31_60": sum(1 for task in tasks if task.aging_days is not None and 31 <= task.aging_days <= 60),
            "61_120": sum(1 for task in tasks if task.aging_days is not None and 61 <= task.aging_days <= 120),
            "120_plus": sum(1 for task in tasks if task.aging_days is not None and task.aging_days > 120),
        },
        "specialist_productivity": {
            role: {"open_tasks": count, "completed_tasks": 0}
            for role, count in owner_load.items()
        },
        "operational_health": {
            "urgent_tasks": sum(1 for task in tasks if task.priority_band == "urgent"),
            "blocked_tasks": sum(1 for task in tasks if task.status == "blocked"),
            "workflows_with_backlog": sum(1 for count in workflow_counts.values() if count > 0),
        },
        "workflow_bottlenecks": [
            workflow
            for workflow, count in workflow_counts.items()
            if count == max(workflow_counts.values() or [0]) and count > 0
        ],
    }


def _workflow(workflow_id: str) -> WorkflowDefinition:
    return next(item for item in workflow_catalog() if item.workflow_id == workflow_id)


def _workflow_id_from_queue(queue: str, reason: str) -> str:
    normalized_queue = queue.lower()
    normalized_reason = reason.lower()
    if "auth" in normalized_queue or "auth" in normalized_reason:
        return "asc_authorization"
    if normalized_queue == "pre-bill" and "implant" in normalized_reason:
        return "asc_charge_capture"
    if normalized_queue == "pre-bill":
        return "asc_coding_review"
    if normalized_queue == "denial":
        return "asc_denials"
    if normalized_queue == "ar-follow-up":
        return "asc_ar_follow_up"
    return "asc_coding_review"


def _coding_priority_band(severity: str) -> str:
    return {
        "critical": "urgent",
        "high": "high",
        "medium": "normal",
        "low": "low",
    }[severity]


def _case_due_date(case: ASCCase) -> str | None:
    return case.work_queue_items[0].due_date if case.work_queue_items else None


def _case_age_days(case: ASCCase, as_of_date: str) -> int | None:
    return max((_parse_date(as_of_date) - _parse_date(case.encounter.service_date)).days, 0)


def _owner_from_workflow(workflow_id: str) -> str:
    return {
        "asc_authorization": "auth_specialist",
        "asc_coding_review": "coder",
        "asc_denials": "denial_specialist",
        "asc_appeals": "denial_specialist",
        "asc_charge_capture": "coder",
        "asc_ar_follow_up": "biller",
    }[workflow_id]


def _priority_rank(priority_band: str) -> tuple[int, str]:
    order = {"urgent": 0, "high": 1, "normal": 2, "low": 3}
    return (order.get(priority_band, 4), priority_band)


def _titleize(value: str) -> str:
    return value.replace("_", " ").title()


def _parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()
