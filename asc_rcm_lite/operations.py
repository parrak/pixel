"""Portfolio operating-system layer for synthetic specialty RCM workflows."""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta
from decimal import Decimal
from functools import lru_cache
from pathlib import Path

from asc_rcm_lite.detectors.ar import ARFlag
from asc_rcm_lite.detectors.coding import CodingOpportunity
from asc_rcm_lite.detectors.denials import DenialOpportunity
from asc_rcm_lite.models import ASCCase, ValidationError, require_non_empty


WORKFLOW_STATUSES = {"open", "in_progress", "blocked", "completed"}
WORKFLOW_CONFIG_PATH = Path(__file__).resolve().parents[1] / "data" / "workflows" / "specialty_rcm_workflows.json"


@dataclass(frozen=True)
class WorkflowStage:
    stage_id: str
    label: str
    description: str

    def __post_init__(self) -> None:
        require_non_empty(self.stage_id, "WorkflowStage.stage_id")
        require_non_empty(self.label, "WorkflowStage.label")
        require_non_empty(self.description, "WorkflowStage.description")


@dataclass(frozen=True)
class WorkflowDefinition:
    workflow_id: str
    name: str
    description: str
    queue_name: str
    owner_roles: tuple[str, ...]
    default_team_name: str
    trigger_sources: tuple[str, ...]
    target_outcomes: tuple[str, ...]
    service_level_hours: int
    stages: tuple[WorkflowStage, ...]
    decision_options: tuple[str, ...]

    def __post_init__(self) -> None:
        require_non_empty(self.workflow_id, "WorkflowDefinition.workflow_id")
        require_non_empty(self.name, "WorkflowDefinition.name")
        require_non_empty(self.description, "WorkflowDefinition.description")
        require_non_empty(self.queue_name, "WorkflowDefinition.queue_name")
        require_non_empty(self.default_team_name, "WorkflowDefinition.default_team_name")
        if not self.owner_roles:
            raise ValidationError("WorkflowDefinition.owner_roles must not be empty")
        if not self.trigger_sources:
            raise ValidationError("WorkflowDefinition.trigger_sources must not be empty")
        if not self.target_outcomes:
            raise ValidationError("WorkflowDefinition.target_outcomes must not be empty")
        if not self.stages:
            raise ValidationError("WorkflowDefinition.stages must not be empty")
        if not self.decision_options:
            raise ValidationError("WorkflowDefinition.decision_options must not be empty")
        if self.service_level_hours <= 0:
            raise ValidationError("WorkflowDefinition.service_level_hours must be positive")


@dataclass(frozen=True)
class Organization:
    organization_id: str
    name: str
    specialty: str
    thesis: str

    def __post_init__(self) -> None:
        require_non_empty(self.organization_id, "Organization.organization_id")
        require_non_empty(self.name, "Organization.name")
        require_non_empty(self.specialty, "Organization.specialty")
        require_non_empty(self.thesis, "Organization.thesis")


@dataclass(frozen=True)
class HoldCo:
    holdco_id: str
    name: str
    thesis: str

    def __post_init__(self) -> None:
        require_non_empty(self.holdco_id, "HoldCo.holdco_id")
        require_non_empty(self.name, "HoldCo.name")
        require_non_empty(self.thesis, "HoldCo.thesis")


@dataclass(frozen=True)
class Facility:
    facility_id: str
    organization_id: str
    name: str
    market: str

    def __post_init__(self) -> None:
        require_non_empty(self.facility_id, "Facility.facility_id")
        require_non_empty(self.organization_id, "Facility.organization_id")
        require_non_empty(self.name, "Facility.name")
        require_non_empty(self.market, "Facility.market")


@dataclass(frozen=True)
class Team:
    team_id: str
    organization_id: str
    name: str
    focus: str
    workflow_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        require_non_empty(self.team_id, "Team.team_id")
        require_non_empty(self.organization_id, "Team.organization_id")
        require_non_empty(self.name, "Team.name")
        require_non_empty(self.focus, "Team.focus")
        if not self.workflow_ids:
            raise ValidationError("Team.workflow_ids must not be empty")


@dataclass(frozen=True)
class OperatorUser:
    user_id: str
    organization_id: str
    team_id: str
    facility_id: str
    display_name: str
    role: str
    title: str

    def __post_init__(self) -> None:
        require_non_empty(self.user_id, "OperatorUser.user_id")
        require_non_empty(self.organization_id, "OperatorUser.organization_id")
        require_non_empty(self.team_id, "OperatorUser.team_id")
        require_non_empty(self.facility_id, "OperatorUser.facility_id")
        require_non_empty(self.display_name, "OperatorUser.display_name")
        require_non_empty(self.role, "OperatorUser.role")
        require_non_empty(self.title, "OperatorUser.title")


@dataclass(frozen=True)
class ValueCreationInitiative:
    initiative_id: str
    name: str
    owner_name: str
    owner_title: str
    target: str
    current_state: str
    expected_ebitda_impact: Decimal
    realized_ebitda_impact: Decimal
    status: str
    timeline: str
    organization_ids: tuple[str, ...]
    workflow_ids: tuple[str, ...]
    operational_link: str

    def __post_init__(self) -> None:
        require_non_empty(self.initiative_id, "ValueCreationInitiative.initiative_id")
        require_non_empty(self.name, "ValueCreationInitiative.name")
        require_non_empty(self.owner_name, "ValueCreationInitiative.owner_name")
        require_non_empty(self.owner_title, "ValueCreationInitiative.owner_title")
        require_non_empty(self.target, "ValueCreationInitiative.target")
        require_non_empty(self.current_state, "ValueCreationInitiative.current_state")
        require_non_empty(self.status, "ValueCreationInitiative.status")
        require_non_empty(self.timeline, "ValueCreationInitiative.timeline")
        require_non_empty(self.operational_link, "ValueCreationInitiative.operational_link")
        if not self.organization_ids:
            raise ValidationError("ValueCreationInitiative.organization_ids must not be empty")
        if not self.workflow_ids:
            raise ValidationError("ValueCreationInitiative.workflow_ids must not be empty")


@dataclass(frozen=True)
class PortfolioBenchmark:
    metric_id: str
    label: str
    unit: str
    organization_id: str
    portfolio_average: Decimal
    top_quartile: Decimal
    best_in_class: Decimal
    organization_value: Decimal
    direction: str

    def __post_init__(self) -> None:
        require_non_empty(self.metric_id, "PortfolioBenchmark.metric_id")
        require_non_empty(self.label, "PortfolioBenchmark.label")
        require_non_empty(self.unit, "PortfolioBenchmark.unit")
        require_non_empty(self.organization_id, "PortfolioBenchmark.organization_id")
        require_non_empty(self.direction, "PortfolioBenchmark.direction")


@dataclass(frozen=True)
class PlaybookTask:
    title: str
    owner_role: str
    dependency: str
    expected_outcome: str
    financial_impact: Decimal

    def __post_init__(self) -> None:
        require_non_empty(self.title, "PlaybookTask.title")
        require_non_empty(self.owner_role, "PlaybookTask.owner_role")
        require_non_empty(self.dependency, "PlaybookTask.dependency")
        require_non_empty(self.expected_outcome, "PlaybookTask.expected_outcome")


@dataclass(frozen=True)
class OperatingPlaybook:
    playbook_id: str
    name: str
    owner_title: str
    focus: str
    tasks: tuple[PlaybookTask, ...]
    expected_outcomes: tuple[str, ...]
    financial_impact: Decimal
    historical_results: str

    def __post_init__(self) -> None:
        require_non_empty(self.playbook_id, "OperatingPlaybook.playbook_id")
        require_non_empty(self.name, "OperatingPlaybook.name")
        require_non_empty(self.owner_title, "OperatingPlaybook.owner_title")
        require_non_empty(self.focus, "OperatingPlaybook.focus")
        require_non_empty(self.historical_results, "OperatingPlaybook.historical_results")
        if not self.tasks:
            raise ValidationError("OperatingPlaybook.tasks must not be empty")
        if not self.expected_outcomes:
            raise ValidationError("OperatingPlaybook.expected_outcomes must not be empty")


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
    actor_name: str
    rationale: str
    timestamp: str

    def __post_init__(self) -> None:
        require_non_empty(self.decision_id, "HumanDecision.decision_id")
        require_non_empty(self.task_id, "HumanDecision.task_id")
        require_non_empty(self.recommendation_id, "HumanDecision.recommendation_id")
        require_non_empty(self.decision, "HumanDecision.decision")
        require_non_empty(self.actor_role, "HumanDecision.actor_role")
        require_non_empty(self.actor_name, "HumanDecision.actor_name")
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
    financial_result: Decimal | None = None
    resolution_time_hours: int | None = None

    def __post_init__(self) -> None:
        require_non_empty(self.outcome_id, "TaskOutcome.outcome_id")
        require_non_empty(self.task_id, "TaskOutcome.task_id")
        require_non_empty(self.status, "TaskOutcome.status")
        require_non_empty(self.impact_summary, "TaskOutcome.impact_summary")
        require_non_empty(self.notes, "TaskOutcome.notes")


@dataclass(frozen=True)
class DecisionMemoryRecord:
    record_id: str
    task_id: str
    workflow_stage: str
    recommendation_title: str
    recommendation_summary: str
    decision: HumanDecision
    outcome: TaskOutcome

    def __post_init__(self) -> None:
        require_non_empty(self.record_id, "DecisionMemoryRecord.record_id")
        require_non_empty(self.task_id, "DecisionMemoryRecord.task_id")
        require_non_empty(self.workflow_stage, "DecisionMemoryRecord.workflow_stage")
        require_non_empty(self.recommendation_title, "DecisionMemoryRecord.recommendation_title")
        require_non_empty(self.recommendation_summary, "DecisionMemoryRecord.recommendation_summary")


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
    organization_id: str | None = None
    organization_name: str | None = None
    facility_id: str | None = None
    facility_name: str | None = None
    team_id: str | None = None
    team_name: str | None = None
    assignee_user_id: str | None = None
    assignee_name: str | None = None
    workflow_stage: str | None = None
    history: tuple[DecisionMemoryRecord, ...] = ()

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


def workflow_catalog() -> tuple[WorkflowDefinition, ...]:
    return _load_workflow_catalog()


@lru_cache(maxsize=1)
def _load_workflow_catalog() -> tuple[WorkflowDefinition, ...]:
    raw = json.loads(WORKFLOW_CONFIG_PATH.read_text(encoding="utf-8"))
    workflows = []
    for item in raw:
        workflows.append(
            WorkflowDefinition(
                workflow_id=item["workflow_id"],
                name=item["name"],
                description=item["description"],
                queue_name=item["queue_name"],
                owner_roles=tuple(item["owner_roles"]),
                default_team_name=item["default_team_name"],
                trigger_sources=tuple(item["trigger_sources"]),
                target_outcomes=tuple(item["target_outcomes"]),
                service_level_hours=int(item["service_level_hours"]),
                stages=tuple(
                    WorkflowStage(
                        stage_id=stage["stage_id"],
                        label=stage["label"],
                        description=stage["description"],
                    )
                    for stage in item["stages"]
                ),
                decision_options=tuple(item["decision_options"]),
            )
        )
    return tuple(workflows)


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
        task = OperationalTask(
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
        tasks.append(_enrich_task(task, case, definition, as_of_date))

    for item in ar_flags:
        workflow_id = "asc_ar_followup"
        if item.flag_type == "appeal_deadline_risk":
            workflow_id = "asc_denial_review"
        definition = _workflow(workflow_id)
        task = OperationalTask(
            task_id=f"TASK-{item.flag_id}",
            case_id=item.case_id,
            workflow_id=definition.workflow_id,
            workflow_name=definition.name,
            queue_name=definition.queue_name,
            task_type=item.flag_type,
            title=_titleize(item.flag_type),
            description=item.reason_for_flag,
            status="in_progress" if item.priority_band == "urgent" else "open",
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
        tasks.append(_enrich_task(task, case, definition, as_of_date))

    for item in denial_items:
        workflow_id = "asc_authorization" if item.denial_category == "prior_authorization" else "asc_denial_review"
        definition = _workflow(workflow_id)
        priority = "urgent" if item.appealability == "likely" else "high"
        owner = "auth_specialist" if workflow_id == "asc_authorization" else "denial_specialist"
        task = OperationalTask(
            task_id=f"TASK-{item.denial_id}",
            case_id=item.case_id,
            workflow_id=definition.workflow_id,
            workflow_name=definition.name,
            queue_name=definition.queue_name,
            task_type=item.denial_category,
            title=_titleize(item.denial_category),
            description=item.root_cause_hypothesis,
            status="in_progress" if priority == "urgent" else "open",
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
        tasks.append(_enrich_task(task, case, definition, as_of_date))

    if not tasks:
        for item in case.work_queue_items:
            workflow_id = _workflow_id_from_queue(item.queue, item.reason)
            definition = _workflow(workflow_id)
            task = OperationalTask(
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
            tasks.append(_enrich_task(task, case, definition, as_of_date))

    return tuple(sorted(tasks, key=lambda task: (_priority_rank(task.priority_band), task.organization_name or "", task.task_id)))


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
    completed_histories = [record for task in tasks for record in task.history]
    return {
        "total_tasks": len(tasks),
        "open_work": sum(1 for task in tasks if task.status != "completed"),
        "revenue_at_risk": str(total_at_risk),
        "recovery_pipeline": str(
            sum(
                (task.amount_at_risk or Decimal("0.00"))
                for task in tasks
                if task.workflow_id in {"asc_denial_review", "asc_ar_followup", "asc_authorization"}
            )
        ),
        "workflow_counts": workflow_counts,
        "queue_aging": _aging_summary(tasks),
        "specialist_productivity": {
            role: {
                "open_tasks": count,
                "completed_tasks": sum(1 for record in completed_histories if record.decision.actor_role == role),
                "financial_result": str(
                    sum(
                        (record.outcome.financial_result or Decimal("0.00"))
                        for record in completed_histories
                        if record.decision.actor_role == role
                    )
                ),
            }
            for role, count in owner_load.items()
        },
        "operational_health": {
            "urgent_tasks": sum(1 for task in tasks if task.priority_band == "urgent"),
            "blocked_tasks": sum(1 for task in tasks if task.status == "blocked"),
            "workflows_with_backlog": sum(1 for count in workflow_counts.values() if count > 0),
            "average_resolution_hours": round(
                sum(record.outcome.resolution_time_hours or 0 for record in completed_histories) / max(len(completed_histories), 1),
                1,
            ),
        },
        "workflow_bottlenecks": [
            workflow
            for workflow, count in workflow_counts.items()
            if count == max(workflow_counts.values() or [0]) and count > 0
        ],
    }


def build_portfolio_snapshot(
    tasks: tuple[OperationalTask, ...],
    workflows: tuple[WorkflowDefinition, ...],
    *,
    cases: tuple[ASCCase, ...] = (),
    as_of_date: str | None = None,
) -> dict[str, object]:
    blueprint = _portfolio_blueprint()
    holdco = blueprint["holdco"]
    organizations = blueprint["organizations"]
    users = blueprint["users"]
    initiatives = _value_creation_initiatives()
    playbooks = _operating_playbooks()
    role_views = []

    for role in ("manager", "denial_specialist", "biller", "coder", "auth_specialist"):
        role_tasks = [task for task in tasks if task.owner_role == role]
        role_histories = [record for task in role_tasks for record in task.history]
        role_views.append(
            {
                "role": role,
                "label": _role_label(role),
                "queue_size": len(role_tasks),
                "revenue_at_risk": str(sum((task.amount_at_risk or Decimal("0.00") for task in role_tasks), Decimal("0.00"))),
                "completed_outcomes": len(role_histories),
                "financial_result": str(sum((record.outcome.financial_result or Decimal("0.00") for record in role_histories), Decimal("0.00"))),
                "tasks": [task.task_id for task in role_tasks[:6]],
            }
        )

    org_summaries = []
    organization_role_views = []
    for organization in organizations:
        org_tasks = [task for task in tasks if task.organization_id == organization.organization_id]
        org_histories = [record for task in org_tasks for record in task.history]
        org_role_views = [
            {
                "role": role,
                "label": _role_label(role),
                "queue_size": sum(1 for task in org_tasks if task.owner_role == role),
                "revenue_at_risk": str(
                    sum(
                        (task.amount_at_risk or Decimal("0.00"))
                        for task in org_tasks
                        if task.owner_role == role
                    )
                ),
                "completed_outcomes": sum(1 for record in org_histories if record.decision.actor_role == role),
                "financial_result": str(
                    sum(
                        (record.outcome.financial_result or Decimal("0.00"))
                        for record in org_histories
                        if record.decision.actor_role == role
                    )
                ),
            }
            for role in ("manager", "denial_specialist", "biller", "coder", "auth_specialist")
        ]
        org_summaries.append(
            {
                "organization_id": organization.organization_id,
                "name": organization.name,
                "specialty": organization.specialty,
                "thesis": organization.thesis,
                "revenue_at_risk": str(sum((task.amount_at_risk or Decimal("0.00") for task in org_tasks), Decimal("0.00"))),
                "open_work": sum(1 for task in org_tasks if task.status != "completed"),
                "recovery_pipeline": str(
                    sum(
                        (task.amount_at_risk or Decimal("0.00"))
                        for task in org_tasks
                        if task.workflow_id in {"asc_denial_review", "asc_ar_followup", "asc_authorization"}
                    )
                ),
                "productivity": {
                    "completed_outcomes": len(org_histories),
                    "financial_result": str(sum((record.outcome.financial_result or Decimal("0.00") for record in org_histories), Decimal("0.00"))),
                },
                "aging": _aging_summary(tuple(org_tasks)),
                "operational_health": {
                    "urgent_tasks": sum(1 for task in org_tasks if task.priority_band == "urgent"),
                    "critical_workflows": sorted({task.workflow_name for task in org_tasks if task.priority_band == "urgent"}),
                },
            }
        )
        organization_role_views.append(
            {
                "organization_id": organization.organization_id,
                "name": organization.name,
                "roles": org_role_views,
            }
        )

    vp_user = next(user for user in users if user.role == "manager" and user.organization_id == "org_alpha")
    monday_tasks = [task for task in tasks if task.organization_id == "org_alpha"]
    monday_story = {
        "title": "Monday Morning",
        "vp_user": {
            "user_id": vp_user.user_id,
            "display_name": vp_user.display_name,
            "title": vp_user.title,
            "organization": "ASC Alpha",
        },
        "executive_brief": [
            "Revenue at risk is concentrated in denials and aging AR across ASC Alpha.",
            "Charge capture and authorization tasks are open but still within service levels.",
            "The operating system recommends denial and AR assignment first because those queues hold the highest recoverable value.",
        ],
        "assignments": [
            _assignment_for_role(monday_tasks, "denial_specialist"),
            _assignment_for_role(monday_tasks, "biller"),
            _assignment_for_role(monday_tasks, "coder"),
            _assignment_for_role(monday_tasks, "auth_specialist"),
        ],
        "critical_work": [task.title for task in monday_tasks if task.priority_band == "urgent"][:4],
        "workflow_bottlenecks": _aging_bottlenecks(monday_tasks),
        "outcomes": [
            {
                "role": view["label"],
                "completed_outcomes": view["completed_outcomes"],
                "financial_result": view["financial_result"],
            }
            for view in role_views
            if view["role"] in {"denial_specialist", "biller", "coder", "auth_specialist"}
        ],
    }

    holdco_dashboard = _build_holdco_dashboard(tasks, org_summaries, initiatives)
    benchmarking = _build_portfolio_benchmarks(tasks, org_summaries)
    decision_intelligence = _build_decision_intelligence(tasks, initiatives, playbooks)
    executive_review = _build_executive_review(holdco_dashboard, org_summaries, initiatives, benchmarking, decision_intelligence)

    work_objects_payload = []
    account_workspaces = []
    denial_workspaces = []
    ar_workspaces = []
    decision_registry = {}
    payer_graph = {}
    manager_interventions = {}
    if cases and as_of_date is not None:
        from asc_rcm_lite.work_objects import (
            build_account_workspaces,
            build_ar_recovery_workspaces,
            build_decision_intelligence_registry,
            build_denial_resolution_workspaces,
            build_manager_intervention_system,
            build_payer_intelligence_graph,
            build_work_objects,
            serialize_work_object,
        )

        built_work_objects = build_work_objects(cases=cases, tasks=tasks, workflows=workflows, as_of_date=as_of_date)
        work_objects_payload = [serialize_work_object(item) for item in built_work_objects]
        account_workspaces = list(build_account_workspaces(built_work_objects))
        denial_workspaces = list(build_denial_resolution_workspaces(built_work_objects))
        ar_workspaces = list(build_ar_recovery_workspaces(built_work_objects))
        decision_registry = build_decision_intelligence_registry(built_work_objects)
        payer_graph = build_payer_intelligence_graph(built_work_objects)
        manager_interventions = build_manager_intervention_system(built_work_objects)

    return {
        "holdco": {
            "holdco_id": holdco.holdco_id,
            "name": holdco.name,
            "thesis": holdco.thesis,
        },
        "organizations": [
            {
                "organization_id": item.organization_id,
                "name": item.name,
                "specialty": item.specialty,
                "thesis": item.thesis,
            }
            for item in organizations
        ],
        "facilities": [
            {
                "facility_id": item.facility_id,
                "organization_id": item.organization_id,
                "name": item.name,
                "market": item.market,
            }
            for item in blueprint["facilities"]
        ],
        "teams": [
            {
                "team_id": item.team_id,
                "organization_id": item.organization_id,
                "name": item.name,
                "focus": item.focus,
                "workflow_ids": list(item.workflow_ids),
            }
            for item in blueprint["teams"]
        ],
        "users": [
            {
                "user_id": item.user_id,
                "organization_id": item.organization_id,
                "team_id": item.team_id,
                "facility_id": item.facility_id,
                "display_name": item.display_name,
                "role": item.role,
                "title": item.title,
            }
            for item in users
        ],
        "workflow_definitions": [
            {
                "workflow_id": workflow.workflow_id,
                "name": workflow.name,
                "queue_name": workflow.queue_name,
                "default_team_name": workflow.default_team_name,
                "owner_roles": list(workflow.owner_roles),
                "service_level_hours": workflow.service_level_hours,
                "decision_options": list(workflow.decision_options),
                "stages": [
                    {
                        "stage_id": stage.stage_id,
                        "label": stage.label,
                        "description": stage.description,
                    }
                    for stage in workflow.stages
                ],
            }
            for workflow in workflows
        ],
        "portfolio_metrics": build_operational_dashboard(tasks),
        "holdco_dashboard": holdco_dashboard,
        "organization_summaries": org_summaries,
        "organization_role_views": organization_role_views,
        "role_views": role_views,
        "monday_morning": monday_story,
        "value_creation_initiatives": [
            {
                "initiative_id": item.initiative_id,
                "name": item.name,
                "owner_name": item.owner_name,
                "owner_title": item.owner_title,
                "target": item.target,
                "current_state": item.current_state,
                "expected_ebitda_impact": str(item.expected_ebitda_impact),
                "realized_ebitda_impact": str(item.realized_ebitda_impact),
                "status": item.status,
                "timeline": item.timeline,
                "organization_ids": list(item.organization_ids),
                "workflow_ids": list(item.workflow_ids),
                "operational_link": item.operational_link,
            }
            for item in initiatives
        ],
        "portfolio_benchmarks": benchmarking,
        "playbooks": [
            {
                "playbook_id": item.playbook_id,
                "name": item.name,
                "owner_title": item.owner_title,
                "focus": item.focus,
                "tasks": [
                    {
                        "title": task.title,
                        "owner_role": task.owner_role,
                        "dependency": task.dependency,
                        "expected_outcome": task.expected_outcome,
                        "financial_impact": str(task.financial_impact),
                    }
                    for task in item.tasks
                ],
                "expected_outcomes": list(item.expected_outcomes),
                "financial_impact": str(item.financial_impact),
                "historical_results": item.historical_results,
            }
            for item in playbooks
        ],
        "work_objects": work_objects_payload,
        "account_workspaces": account_workspaces,
        "denial_resolution_workspaces": denial_workspaces,
        "ar_recovery_workspaces": ar_workspaces,
        "decision_memory_registry": decision_registry,
        "payer_intelligence_graph": payer_graph,
        "manager_intervention_system": manager_interventions,
        "decision_intelligence": decision_intelligence,
        "executive_operating_review": executive_review,
        "acquisition_defaults": {
            "specialties": ["ASC", "Ophthalmology", "GI", "Orthopedics", "Cardiology"],
            "workflow_maturity_levels": ["fragmented", "developing", "scaled"],
            "systems": ["EHR", "Practice Management", "Clearinghouse", "Payer Portals", "Spreadsheets"],
        },
    }


def simulate_acquisition(*, specialty: str, headcount: int, workflow_maturity: str, systems: tuple[str, ...]) -> dict[str, object]:
    require_non_empty(specialty, "simulate_acquisition.specialty")
    require_non_empty(workflow_maturity, "simulate_acquisition.workflow_maturity")
    normalized_maturity = workflow_maturity.lower()
    maturity_gap = {
        "fragmented": "high",
        "developing": "medium",
        "scaled": "low",
    }.get(normalized_maturity, "medium")
    workflow_map = [
        {"workflow": "Authorization intake", "maturity": workflow_maturity, "owner": "Authorization team"},
        {"workflow": "Coding review", "maturity": workflow_maturity, "owner": "Coding team"},
        {"workflow": "Denial management", "maturity": workflow_maturity, "owner": "Denials team"},
        {"workflow": "AR follow-up", "maturity": workflow_maturity, "owner": "AR team"},
        {"workflow": "Management review", "maturity": workflow_maturity, "owner": "Revenue leadership"},
    ]
    gaps = [
        f"{specialty} acquisition relies on disconnected operator handoffs across {len(systems)} systems.",
        f"Workflow maturity is {workflow_maturity}, which implies {maturity_gap} standardization urgency.",
    ]
    if headcount >= 60:
        gaps.append("The operator base is large enough that role clarity and queue ownership must be standardized immediately.")
    if "Spreadsheets" in systems:
        gaps.append("Spreadsheet-based exception handling is likely hiding queue aging and decision latency.")
    opportunities = [
        "Standardize task states, decision logging, and outcome capture across facilities.",
        "Assign queue ownership by team rather than by tribal knowledge.",
        "Roll executive reporting up to portfolio-level operating health.",
    ]
    deployment_plan = [
        "Map current workflows to Citron workflow definitions.",
        "Stand up organization, facility, team, and user views for the acquired operator.",
        "Import queue work into task -> recommendation -> decision -> outcome flows.",
        "Track financial result and resolution time to measure post-acquisition improvement.",
    ]
    current_state_assessment = {
        "operating_model": f"{specialty} work is managed with {workflow_maturity} workflow maturity across {headcount} operators.",
        "systems_posture": f"{len(systems)} systems currently mediate operator work, with Citron positioned above them rather than replacing them.",
        "leadership_risk": f"{maturity_gap.title()} risk that queue ownership and workflow accountability are inconsistent across the acquired business.",
    }
    operational_risks = [
        "Queue aging is likely hidden inside payer portals and spreadsheet sidecars.",
        "Decision latency will vary by team until standard workflow ownership is enforced.",
        "Revenue leadership will struggle to connect workflow changes to EBITDA without explicit decision and outcome capture.",
    ]
    technology_gaps = [
        "No unified operating layer for cross-system workflow routing.",
        "Limited queue-level auditability for handoffs and escalations.",
        "No shared decision memory to transfer knowledge across acquisitions.",
    ]
    roadmap = [
        {"window": "Days 0-30", "focus": "Current-state workflow mapping and queue normalization"},
        {"window": "Days 31-60", "focus": "Role assignment, playbook rollout, and operational KPI baselining"},
        {"window": "Days 61-90", "focus": "Benchmarking, value-creation initiative launch, and executive operating review"},
    ]
    value_creation_opportunities = [
        {
            "initiative": "Workflow Standardization",
            "expected_ebitda_impact": "180000.00" if maturity_gap == "high" else "95000.00",
            "reason": "Consistent queue ownership reduces leakage and speeds resolution.",
        },
        {
            "initiative": "Authorization Optimization",
            "expected_ebitda_impact": "110000.00",
            "reason": "Fewer preventable denials improves recoverability and accelerates cash conversion.",
        },
        {
            "initiative": "Productivity Improvements",
            "expected_ebitda_impact": "85000.00",
            "reason": "Standard roles and reusable playbooks increase revenue per employee.",
        },
    ]
    return {
        "specialty": specialty,
        "headcount": headcount,
        "workflow_maturity": workflow_maturity,
        "systems": list(systems),
        "workflow_map": workflow_map,
        "current_state_assessment": current_state_assessment,
        "operational_gaps": gaps,
        "operational_risks": operational_risks,
        "technology_gaps": technology_gaps,
        "standardization_opportunities": opportunities,
        "integration_plan": deployment_plan,
        "ninety_day_roadmap": roadmap,
        "value_creation_opportunities": value_creation_opportunities,
        "deployment_plan": deployment_plan,
        "operating_model": {
            "integration_layer": sorted(set(systems)),
            "citron_layers": [
                "Workflow Engine",
                "Decision Memory",
                "Portfolio Rollup",
                "Value Creation System",
                "Operator Queues",
            ],
            "value_thesis": "Software increases value by standardizing operators across acquisitions rather than replacing systems of record.",
        },
    }


def _workflow(workflow_id: str) -> WorkflowDefinition:
    return next(item for item in workflow_catalog() if item.workflow_id == workflow_id)


def _enrich_task(task: OperationalTask, case: ASCCase, workflow: WorkflowDefinition, as_of_date: str) -> OperationalTask:
    blueprint = _portfolio_blueprint()
    assignment = blueprint["case_assignments"][case.case_id]
    team = next(
        item
        for item in blueprint["teams"]
        if item.organization_id == assignment["organization_id"]
        and _role_matches_team(task.owner_role, item.name)
    )
    user = next(
        item
        for item in blueprint["users"]
        if item.organization_id == assignment["organization_id"] and item.team_id == team.team_id and item.role == task.owner_role
    )
    history = _build_task_history(task, workflow, user, as_of_date)
    return replace(
        task,
        organization_id=assignment["organization_id"],
        organization_name=assignment["organization_name"],
        facility_id=assignment["facility_id"],
        facility_name=assignment["facility_name"],
        team_id=team.team_id,
        team_name=team.name,
        assignee_user_id=user.user_id,
        assignee_name=user.display_name,
        workflow_stage=workflow.stages[0].stage_id,
        history=history,
    )


def _role_matches_team(role: str, team_name: str) -> bool:
    checks = {
        "manager": "Revenue Leadership",
        "denial_specialist": "Denials",
        "biller": "AR",
        "coder": "Coding",
        "auth_specialist": "Authorization",
    }
    return checks.get(role, "") in team_name


def _build_task_history(
    task: OperationalTask,
    workflow: WorkflowDefinition,
    user: OperatorUser,
    as_of_date: str,
) -> tuple[DecisionMemoryRecord, ...]:
    recommendation = task.recommendations[0]
    record_date = _parse_date(as_of_date) - timedelta(days=(len(task.task_id) % 4) + 1)
    stage = workflow.stages[min(1, len(workflow.stages) - 1)].stage_id
    decision = HumanDecision(
        decision_id=f"DEC-{task.task_id}",
        task_id=task.task_id,
        recommendation_id=recommendation.recommendation_id,
        decision=workflow.decision_options[0],
        actor_role=user.role,
        actor_name=user.display_name,
        rationale=f"{user.title} acted on the cited recommendation to keep the workflow moving.",
        timestamp=record_date.isoformat(),
    )
    amount = task.amount_at_risk or Decimal("0.00")
    realized = _quantize_amount(amount * Decimal("0.32")) if amount else Decimal("0.00")
    outcome = TaskOutcome(
        outcome_id=f"OUT-{task.task_id}",
        task_id=task.task_id,
        status=_outcome_status(task.workflow_id),
        impact_summary=f"{workflow.name} advanced with a documented operator action.",
        value_realized=realized,
        notes="Synthetic decision-memory record used to demonstrate operational learning.",
        financial_result=realized,
        resolution_time_hours=max(workflow.service_level_hours - 6, 6),
    )
    return (
        DecisionMemoryRecord(
            record_id=f"MEM-{task.task_id}",
            task_id=task.task_id,
            workflow_stage=stage,
            recommendation_title=recommendation.title,
            recommendation_summary=recommendation.summary,
            decision=decision,
            outcome=outcome,
        ),
    )


def _portfolio_blueprint() -> dict[str, object]:
    holdco = HoldCo(
        "holdco_citron",
        "Citron Specialty RCM Platform",
        "Acquire specialty RCM operators, standardize workflow, compound knowledge, and expand enterprise value.",
    )
    organizations = (
        Organization("org_alpha", "ASC Alpha", "ASC", "Standardize denial and AR execution first."),
        Organization("org_bravo", "ASC Bravo", "ASC", "Tighten coding and charge capture throughput."),
        Organization("org_charlie", "ASC Charlie", "ASC", "Create executive visibility across a smaller but aging book."),
    )
    facilities = (
        Facility("fac_alpha", "org_alpha", "ASC Alpha Surgical Center", "Phoenix"),
        Facility("fac_bravo", "org_bravo", "ASC Bravo Specialty Pavilion", "Dallas"),
        Facility("fac_charlie", "org_charlie", "ASC Charlie Outpatient Center", "Atlanta"),
    )
    teams = (
        Team("team_alpha_rev", "org_alpha", "ASC Alpha Revenue Leadership", "Executive portfolio management", tuple(item.workflow_id for item in workflow_catalog())),
        Team("team_alpha_denials", "org_alpha", "ASC Alpha Denials Team", "Denials operations", ("asc_denial_review",)),
        Team("team_alpha_ar", "org_alpha", "ASC Alpha AR Team", "A/R operations", ("asc_ar_followup",)),
        Team("team_alpha_coding", "org_alpha", "ASC Alpha Coding Team", "Coding and charge capture", ("asc_charge_capture", "asc_coding_review")),
        Team("team_alpha_auth", "org_alpha", "ASC Alpha Authorization Team", "Authorization readiness", ("asc_authorization",)),
        Team("team_bravo_rev", "org_bravo", "ASC Bravo Revenue Leadership", "Executive portfolio management", tuple(item.workflow_id for item in workflow_catalog())),
        Team("team_bravo_denials", "org_bravo", "ASC Bravo Denials Team", "Denials operations", ("asc_denial_review",)),
        Team("team_bravo_ar", "org_bravo", "ASC Bravo AR Team", "A/R operations", ("asc_ar_followup",)),
        Team("team_bravo_coding", "org_bravo", "ASC Bravo Coding Team", "Coding and charge capture", ("asc_charge_capture", "asc_coding_review")),
        Team("team_bravo_auth", "org_bravo", "ASC Bravo Authorization Team", "Authorization readiness", ("asc_authorization",)),
        Team("team_charlie_rev", "org_charlie", "ASC Charlie Revenue Leadership", "Executive portfolio management", tuple(item.workflow_id for item in workflow_catalog())),
        Team("team_charlie_denials", "org_charlie", "ASC Charlie Denials Team", "Denials operations", ("asc_denial_review",)),
        Team("team_charlie_ar", "org_charlie", "ASC Charlie AR Team", "A/R operations", ("asc_ar_followup",)),
        Team("team_charlie_coding", "org_charlie", "ASC Charlie Coding Team", "Coding and charge capture", ("asc_charge_capture", "asc_coding_review")),
        Team("team_charlie_auth", "org_charlie", "ASC Charlie Authorization Team", "Authorization readiness", ("asc_authorization",)),
    )
    users = (
        OperatorUser("user_alpha_vp", "org_alpha", "team_alpha_rev", "fac_alpha", "Morgan Lee", "manager", "VP Revenue Cycle"),
        OperatorUser("user_alpha_denial", "org_alpha", "team_alpha_denials", "fac_alpha", "Jasmine Brooks", "denial_specialist", "Denial Specialist"),
        OperatorUser("user_alpha_ar", "org_alpha", "team_alpha_ar", "fac_alpha", "Daniel Ortiz", "biller", "AR Specialist"),
        OperatorUser("user_alpha_coding", "org_alpha", "team_alpha_coding", "fac_alpha", "Priya Shah", "coder", "Coding Specialist"),
        OperatorUser("user_alpha_auth", "org_alpha", "team_alpha_auth", "fac_alpha", "Elena Park", "auth_specialist", "Authorization Specialist"),
        OperatorUser("user_bravo_vp", "org_bravo", "team_bravo_rev", "fac_bravo", "Alicia Monroe", "manager", "VP Revenue Cycle"),
        OperatorUser("user_bravo_denial", "org_bravo", "team_bravo_denials", "fac_bravo", "Terrence Cole", "denial_specialist", "Denial Specialist"),
        OperatorUser("user_bravo_ar", "org_bravo", "team_bravo_ar", "fac_bravo", "Marcos Vega", "biller", "AR Specialist"),
        OperatorUser("user_bravo_coding", "org_bravo", "team_bravo_coding", "fac_bravo", "Nina Patel", "coder", "Coding Specialist"),
        OperatorUser("user_bravo_auth", "org_bravo", "team_bravo_auth", "fac_bravo", "Olivia Chen", "auth_specialist", "Authorization Specialist"),
        OperatorUser("user_charlie_vp", "org_charlie", "team_charlie_rev", "fac_charlie", "Sonia Clarke", "manager", "VP Revenue Cycle"),
        OperatorUser("user_charlie_denial", "org_charlie", "team_charlie_denials", "fac_charlie", "Rafael Kim", "denial_specialist", "Denial Specialist"),
        OperatorUser("user_charlie_ar", "org_charlie", "team_charlie_ar", "fac_charlie", "Maya Foster", "biller", "AR Specialist"),
        OperatorUser("user_charlie_coding", "org_charlie", "team_charlie_coding", "fac_charlie", "Ivy Reynolds", "coder", "Coding Specialist"),
        OperatorUser("user_charlie_auth", "org_charlie", "team_charlie_auth", "fac_charlie", "Grace Lin", "auth_specialist", "Authorization Specialist"),
    )
    case_assignments = {
        "ASC-CASE-001": {"organization_id": "org_alpha", "organization_name": "ASC Alpha", "facility_id": "fac_alpha", "facility_name": "ASC Alpha Surgical Center"},
        "ASC-CASE-002": {"organization_id": "org_alpha", "organization_name": "ASC Alpha", "facility_id": "fac_alpha", "facility_name": "ASC Alpha Surgical Center"},
        "ASC-CASE-003": {"organization_id": "org_alpha", "organization_name": "ASC Alpha", "facility_id": "fac_alpha", "facility_name": "ASC Alpha Surgical Center"},
        "ASC-CASE-004": {"organization_id": "org_bravo", "organization_name": "ASC Bravo", "facility_id": "fac_bravo", "facility_name": "ASC Bravo Specialty Pavilion"},
        "ASC-CASE-005": {"organization_id": "org_bravo", "organization_name": "ASC Bravo", "facility_id": "fac_bravo", "facility_name": "ASC Bravo Specialty Pavilion"},
        "ASC-CASE-006": {"organization_id": "org_bravo", "organization_name": "ASC Bravo", "facility_id": "fac_bravo", "facility_name": "ASC Bravo Specialty Pavilion"},
        "ASC-CASE-007": {"organization_id": "org_charlie", "organization_name": "ASC Charlie", "facility_id": "fac_charlie", "facility_name": "ASC Charlie Outpatient Center"},
        "ASC-CASE-008": {"organization_id": "org_charlie", "organization_name": "ASC Charlie", "facility_id": "fac_charlie", "facility_name": "ASC Charlie Outpatient Center"},
    }
    return {
        "holdco": holdco,
        "organizations": organizations,
        "facilities": facilities,
        "teams": teams,
        "users": users,
        "case_assignments": case_assignments,
    }


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
        return "asc_denial_review"
    if normalized_queue == "ar-follow-up":
        return "asc_ar_followup"
    return "asc_coding_review"


def _coding_priority_band(severity: str) -> str:
    return {"critical": "urgent", "high": "high", "medium": "normal", "low": "low"}[severity]


def _case_due_date(case: ASCCase) -> str | None:
    return case.work_queue_items[0].due_date if case.work_queue_items else None


def _case_age_days(case: ASCCase, as_of_date: str) -> int | None:
    return max((_parse_date(as_of_date) - _parse_date(case.encounter.service_date)).days, 0)


def _owner_from_workflow(workflow_id: str) -> str:
    return {
        "asc_authorization": "auth_specialist",
        "asc_coding_review": "coder",
        "asc_denial_review": "denial_specialist",
        "asc_charge_capture": "coder",
        "asc_ar_followup": "biller",
    }[workflow_id]


def _aging_summary(tasks: tuple[OperationalTask, ...] | list[OperationalTask]) -> dict[str, int]:
    return {
        "0_30": sum(1 for task in tasks if task.aging_days is not None and task.aging_days <= 30),
        "31_60": sum(1 for task in tasks if task.aging_days is not None and 31 <= task.aging_days <= 60),
        "61_120": sum(1 for task in tasks if task.aging_days is not None and 61 <= task.aging_days <= 120),
        "120_plus": sum(1 for task in tasks if task.aging_days is not None and task.aging_days > 120),
    }


def _aging_bottlenecks(tasks: list[OperationalTask]) -> list[str]:
    aging = _aging_summary(tasks)
    highest = max(aging.values() or [0])
    return [bucket for bucket, count in aging.items() if count == highest and count > 0]


def _assignment_for_role(tasks: list[OperationalTask], role: str) -> dict[str, object]:
    role_tasks = [task for task in tasks if task.owner_role == role]
    top_task = sorted(role_tasks, key=lambda item: _priority_rank(item.priority_band))[0] if role_tasks else None
    return {
        "role": _role_label(role),
        "queue_size": len(role_tasks),
        "top_task": top_task.title if top_task else "No work queued",
        "recommended_action": top_task.recommendations[0].suggested_action if top_task else "No action required",
    }


def _priority_rank(priority_band: str) -> tuple[int, str]:
    order = {"urgent": 0, "high": 1, "normal": 2, "low": 3}
    return (order.get(priority_band, 4), priority_band)


def _role_label(role: str) -> str:
    return {
        "manager": "VP Revenue Cycle",
        "denial_specialist": "Denial Specialist",
        "biller": "AR Specialist",
        "coder": "Coding Specialist",
        "auth_specialist": "Authorization Specialist",
    }.get(role, role.replace("_", " ").title())


def _outcome_status(workflow_id: str) -> str:
    return {
        "asc_denial_review": "Appeal path documented",
        "asc_ar_followup": "Follow-up completed",
        "asc_authorization": "Authorization remediation documented",
        "asc_charge_capture": "Charge action recorded",
        "asc_coding_review": "Coding review documented",
    }[workflow_id]


def _titleize(value: str) -> str:
    return value.replace("_", " ").title()


def _value_creation_initiatives() -> tuple[ValueCreationInitiative, ...]:
    return (
        ValueCreationInitiative(
            "init_coding_automation",
            "Coding Automation",
            "Alicia Monroe",
            "Regional VP Revenue Cycle",
            "Reduce manual coding review load by 18%",
            "Bravo coding and charge capture queues are standardized, but throughput variance remains above target.",
            Decimal("180000.00"),
            Decimal("64000.00"),
            "in_flight",
            "Q3 FY26",
            ("org_bravo",),
            ("asc_coding_review", "asc_charge_capture"),
            "Raise coder productivity and recover missed implant charges faster.",
        ),
        ValueCreationInitiative(
            "init_denial_reduction",
            "Denial Reduction",
            "Morgan Lee",
            "VP Revenue Cycle",
            "Reduce preventable denial rate below 6.0%",
            "Alpha denial work is recoverable, but prior-auth leakage still drives urgent assignments.",
            Decimal("225000.00"),
            Decimal("92000.00"),
            "in_flight",
            "Q3 FY26",
            ("org_alpha",),
            ("asc_denial_review", "asc_authorization"),
            "Lower avoidable rework and improve near-term cash recovery.",
        ),
        ValueCreationInitiative(
            "init_auth_optimization",
            "Authorization Optimization",
            "Grace Lin",
            "Authorization Lead",
            "Cut authorization cycle time to under 20 hours",
            "Authorization work is documented, but portfolio variance is still too wide.",
            Decimal("140000.00"),
            Decimal("51000.00"),
            "scaling",
            "Q4 FY26",
            ("org_alpha", "org_charlie"),
            ("asc_authorization",),
            "Reduce preventable denials before they hit AR and appeals queues.",
        ),
        ValueCreationInitiative(
            "init_offshore_migration",
            "Offshore Migration",
            "Sonia Clarke",
            "Portfolio Operations Director",
            "Move low-variance AR follow-up work into standardized pods",
            "Charlie has enough repeatable AR work to absorb a shared-service model after queue cleanup.",
            Decimal("120000.00"),
            Decimal("0.00"),
            "planned",
            "Q1 FY27",
            ("org_charlie",),
            ("asc_ar_followup",),
            "Lower cost to serve without losing queue accountability.",
        ),
        ValueCreationInitiative(
            "init_workflow_standardization",
            "Workflow Standardization",
            "Sonia Clarke",
            "Portfolio Operations Director",
            "Run every acquired operator on one workflow taxonomy",
            "Cross-portfolio workflow definitions are live, but playbook adoption is mid-rollout.",
            Decimal("260000.00"),
            Decimal("118000.00"),
            "in_flight",
            "Q3 FY26",
            ("org_alpha", "org_bravo", "org_charlie"),
            ("asc_authorization", "asc_denial_review", "asc_ar_followup", "asc_charge_capture", "asc_coding_review"),
            "Create comparable queue ownership, decision memory, and operating reviews across the platform.",
        ),
        ValueCreationInitiative(
            "init_contract_optimization",
            "Contract Optimization",
            "Daniel Ortiz",
            "AR Excellence Lead",
            "Improve underpayment recovery discipline",
            "Underpayment follow-up is consistent but still fragmented by payer workflow.",
            Decimal("90000.00"),
            Decimal("28000.00"),
            "planned",
            "Q4 FY26",
            ("org_charlie", "org_alpha"),
            ("asc_ar_followup",),
            "Turn payer-specific recovery tactics into reusable operating knowledge.",
        ),
        ValueCreationInitiative(
            "init_productivity_improvements",
            "Productivity Improvements",
            "Morgan Lee",
            "VP Revenue Cycle",
            "Increase revenue per employee across the portfolio",
            "Leadership can now see workload and outcomes, but staffing leverage is not yet uniform.",
            Decimal("210000.00"),
            Decimal("76000.00"),
            "in_flight",
            "Q4 FY26",
            ("org_alpha", "org_bravo", "org_charlie"),
            ("asc_denial_review", "asc_ar_followup", "asc_coding_review"),
            "Connect operator throughput improvements to EBITDA expansion.",
        ),
    )


def _operating_playbooks() -> tuple[OperatingPlaybook, ...]:
    return (
        OperatingPlaybook(
            "playbook_asc_integration",
            "ASC Integration",
            "Portfolio Operations Director",
            "Stand up a newly acquired ASC operator inside Citron within 90 days.",
            (
                PlaybookTask("Map current workflow lanes", "manager", "Acquisition close", "Current-state queue map completed", Decimal("25000.00")),
                PlaybookTask("Assign facility teams", "manager", "Workflow map", "Named owners for each queue", Decimal("18000.00")),
                PlaybookTask("Normalize denial and AR queues", "denial_specialist", "Team assignment", "Urgent backlog visible in one operating view", Decimal("42000.00")),
            ),
            ("Faster post-close standardization", "Comparable operator metrics across the platform"),
            Decimal("145000.00"),
            "Reduced time-to-standardization across the last two synthetic acquisitions.",
        ),
        OperatingPlaybook(
            "playbook_denial_excellence",
            "Denial Excellence",
            "VP Revenue Cycle",
            "Reduce avoidable denials and compress appeal cycle times.",
            (
                PlaybookTask("Triage urgent appeal deadlines", "denial_specialist", "Daily queue refresh", "High-risk denials assigned within the SLA", Decimal("38000.00")),
                PlaybookTask("Link denial root causes to auth workflow", "auth_specialist", "Appeal path documented", "Preventable denial loops shrink over time", Decimal("27000.00")),
            ),
            ("Lower denial rate", "Higher recoverability on denied claims"),
            Decimal("132000.00"),
            "Synthetic portfolio shows fewer urgent escalations where this playbook is applied first.",
        ),
        OperatingPlaybook(
            "playbook_coding_excellence",
            "Coding Excellence",
            "Coding Director",
            "Improve coding throughput and capture missed revenue before billing.",
            (
                PlaybookTask("Prioritize high-impact coding variance", "coder", "Daily coding queue", "High-dollar issues reviewed first", Decimal("22000.00")),
                PlaybookTask("Validate implant charge support", "coder", "Supply log reconciliation", "Missed charge capture declines", Decimal("19000.00")),
            ),
            ("Higher coder productivity", "Lower pre-bill leakage"),
            Decimal("98000.00"),
            "Charge capture variance narrows fastest in organizations following the shared review sequence.",
        ),
        OperatingPlaybook(
            "playbook_authorization_excellence",
            "Authorization Excellence",
            "Authorization Lead",
            "Reduce preventable denials by tightening pre-service authorization workflow.",
            (
                PlaybookTask("Review auth deficiencies before service", "auth_specialist", "Scheduling handoff", "Fewer missing-auth denials downstream", Decimal("26000.00")),
                PlaybookTask("Escalate payers with repeated delays", "auth_specialist", "Cycle-time outlier detected", "Cycle time variance declines", Decimal("14000.00")),
            ),
            ("Lower auth cycle time", "Less preventable revenue risk"),
            Decimal("104000.00"),
            "Authorization cycle time improves when remediation steps are standardized across facilities.",
        ),
        OperatingPlaybook(
            "playbook_manager_review",
            "Manager Operating Review",
            "Operating Partner",
            "Run a weekly management cadence tied to financial and operational outcomes.",
            (
                PlaybookTask("Review portfolio bottlenecks", "manager", "Updated holdco dashboard", "Leadership focuses on the highest-leverage constraints", Decimal("12000.00")),
                PlaybookTask("Approve initiative owners and next actions", "manager", "Benchmark variance reviewed", "Value creation plans stay accountable", Decimal("16000.00")),
            ),
            ("Clear executive focus", "Faster escalation on underperforming workflows"),
            Decimal("76000.00"),
            "Organizations with a consistent operating review show tighter queue discipline.",
        ),
        OperatingPlaybook(
            "playbook_revenue_recovery",
            "Revenue Recovery",
            "AR Excellence Lead",
            "Recover aged AR and underpayments with explicit queue ownership.",
            (
                PlaybookTask("Work 120+ day accounts first", "biller", "Aging snapshot refreshed", "Highest-risk dollars receive attention first", Decimal("31000.00")),
                PlaybookTask("Document payer follow-up outcomes", "biller", "Touch completed", "Recovery tactics become reusable decision memory", Decimal("15000.00")),
            ),
            ("Higher recovery rate", "Improved cash conversion on aged balances"),
            Decimal("118000.00"),
            "Historical results improve when account prioritization is combined with shared payer tactics.",
        ),
    )


def _build_holdco_dashboard(
    tasks: tuple[OperationalTask, ...],
    org_summaries: list[dict[str, object]],
    initiatives: tuple[ValueCreationInitiative, ...],
) -> dict[str, object]:
    annualized_revenue = Decimal("18450000.00")
    ebitda = Decimal("4180000.00")
    completed_histories = [record for task in tasks for record in task.history]
    total_financial_result = sum((record.outcome.financial_result or Decimal("0.00") for record in completed_histories), Decimal("0.00"))
    expected_impact = sum((item.expected_ebitda_impact for item in initiatives), Decimal("0.00"))
    realized_impact = sum((item.realized_ebitda_impact for item in initiatives), Decimal("0.00"))
    urgent_tasks = [task for task in tasks if task.priority_band == "urgent"]
    workflow_counts = build_operational_dashboard(tasks)["workflow_counts"]
    busiest_workflow_count = max(workflow_counts.values() or [0])
    bottlenecks = [name for name, count in workflow_counts.items() if count == busiest_workflow_count and count > 0]
    return {
        "portfolio_revenue": str(annualized_revenue),
        "portfolio_ebitda": str(ebitda),
        "revenue_at_risk": str(sum((task.amount_at_risk or Decimal("0.00") for task in tasks), Decimal("0.00"))),
        "open_work": sum(1 for task in tasks if task.status != "completed"),
        "critical_bottlenecks": bottlenecks,
        "productivity_trends": {
            "documented_outcomes": len(completed_histories),
            "realized_financial_result": str(total_financial_result),
            "revenue_per_employee": "410000.00",
            "coder_productivity_delta_pct": "9.4",
        },
        "portfolio_health": {
            "healthy_orgs": sum(1 for summary in org_summaries if summary["operational_health"]["urgent_tasks"] <= 1),
            "watchlist_orgs": [summary["name"] for summary in org_summaries if summary["operational_health"]["urgent_tasks"] > 1],
        },
        "operational_risks": [
            "ASC Alpha still concentrates urgent denial value in a small set of cases.",
            "ASC Charlie aging AR remains above target until shared-service cleanup is complete.",
            "Workflow standardization is live, but playbook adherence is not uniform across organizations.",
        ],
        "value_creation_progress": {
            "expected_ebitda_impact": str(expected_impact),
            "realized_ebitda_impact": str(realized_impact),
            "progress_pct": str(round((realized_impact / expected_impact) * Decimal("100"), 1) if expected_impact else Decimal("0.0")),
        },
        "recent_acquisitions": [
            {"name": "ASC Bravo", "close_date": "2026-02-14", "integration_status": "playbooks live"},
            {"name": "ASC Charlie", "close_date": "2026-04-03", "integration_status": "benchmarking baseline complete"},
        ],
        "focus_today": [
            "Protect near-term recovery by clearing urgent denial and authorization work at ASC Alpha.",
            "Push coding automation and charge capture standardization further at ASC Bravo.",
            "Reduce 120+ day AR exposure at ASC Charlie before launching shared-service migration.",
        ],
        "enterprise_value_flow": [
            "Acquisition",
            "Standardization",
            "Operational Improvement",
            "Knowledge Compounding",
            "EBITDA Expansion",
            "Enterprise Value Creation",
        ],
    }


def _build_portfolio_benchmarks(tasks: tuple[OperationalTask, ...], org_summaries: list[dict[str, object]]) -> dict[str, object]:
    metric_templates = (
        ("collection_rate", "Collection Rate", "%", "higher_better"),
        ("denial_rate", "Denial Rate", "%", "lower_better"),
        ("ar_aging", "AR Aging", "days", "lower_better"),
        ("coder_productivity", "Coder Productivity", "claims/day", "higher_better"),
        ("authorization_cycle_time", "Authorization Cycle Time", "hours", "lower_better"),
        ("revenue_per_employee", "Revenue Per Employee", "$", "higher_better"),
        ("margin", "Margin", "%", "higher_better"),
        ("recovery_rate", "Recovery Rate", "%", "higher_better"),
    )
    values_by_org = {
        "org_alpha": {
            "collection_rate": Decimal("96.8"),
            "denial_rate": Decimal("7.1"),
            "ar_aging": Decimal("39.0"),
            "coder_productivity": Decimal("18.5"),
            "authorization_cycle_time": Decimal("22.0"),
            "revenue_per_employee": Decimal("402000.00"),
            "margin": Decimal("22.0"),
            "recovery_rate": Decimal("72.0"),
        },
        "org_bravo": {
            "collection_rate": Decimal("97.9"),
            "denial_rate": Decimal("5.8"),
            "ar_aging": Decimal("31.0"),
            "coder_productivity": Decimal("21.4"),
            "authorization_cycle_time": Decimal("18.0"),
            "revenue_per_employee": Decimal("428000.00"),
            "margin": Decimal("24.2"),
            "recovery_rate": Decimal("78.0"),
        },
        "org_charlie": {
            "collection_rate": Decimal("95.4"),
            "denial_rate": Decimal("6.6"),
            "ar_aging": Decimal("52.0"),
            "coder_productivity": Decimal("17.2"),
            "authorization_cycle_time": Decimal("24.0"),
            "revenue_per_employee": Decimal("389000.00"),
            "margin": Decimal("20.5"),
            "recovery_rate": Decimal("69.0"),
        },
    }
    org_rows = []
    for summary in org_summaries:
        organization_id = summary["organization_id"]
        benchmarks = []
        for metric_id, label, unit, direction in metric_templates:
            org_value = values_by_org[organization_id][metric_id]
            peer_values = [entry[metric_id] for entry in values_by_org.values()]
            portfolio_average = _quantize_amount(sum(peer_values, Decimal("0.00")) / Decimal(str(len(peer_values))))
            top_quartile = max(peer_values) if direction == "higher_better" else min(peer_values)
            best_in_class = (top_quartile + portfolio_average) / Decimal("2") if direction == "higher_better" else (top_quartile + min(peer_values)) / Decimal("2")
            benchmark = PortfolioBenchmark(
                metric_id,
                label,
                unit,
                organization_id,
                portfolio_average,
                _quantize_amount(top_quartile),
                _quantize_amount(best_in_class),
                org_value,
                direction,
            )
            benchmarks.append(
                {
                    "metric_id": benchmark.metric_id,
                    "label": benchmark.label,
                    "unit": benchmark.unit,
                    "organization_value": str(benchmark.organization_value),
                    "portfolio_average": str(benchmark.portfolio_average),
                    "top_quartile": str(benchmark.top_quartile),
                    "best_in_class": str(benchmark.best_in_class),
                    "direction": benchmark.direction,
                    "variance_to_average": str(_quantize_amount(benchmark.organization_value - benchmark.portfolio_average)),
                }
            )
        org_rows.append(
            {
                "organization_id": organization_id,
                "name": summary["name"],
                "benchmarks": benchmarks,
            }
        )
    return {
        "metrics": [label for _, label, _, _ in metric_templates],
        "organizations": org_rows,
        "narrative": "Portfolio variance is visible so leadership can copy what works and intervene where operators are drifting.",
    }


def _build_decision_intelligence(
    tasks: tuple[OperationalTask, ...],
    initiatives: tuple[ValueCreationInitiative, ...],
    playbooks: tuple[OperatingPlaybook, ...],
) -> dict[str, object]:
    records = [record for task in tasks for record in task.history]
    realized = sum((record.outcome.financial_result or Decimal("0.00") for record in records), Decimal("0.00"))
    avg_resolution = round(sum(record.outcome.resolution_time_hours or 0 for record in records) / max(len(records), 1), 1)
    return {
        "summary": {
            "recommendations_logged": len(tasks),
            "decisions_logged": len(records),
            "outcomes_logged": len(records),
            "financial_result": str(realized),
            "average_resolution_hours": avg_resolution,
        },
        "what_works": [
            "Denial and authorization decisions with explicit ownership resolve fastest in the synthetic portfolio.",
            "AR follow-up recommendations tied to clear escalation criteria create the highest immediate cash recovery.",
            "Playbooks that sequence queue triage before specialist execution reduce operational variance.",
        ],
        "what_fails": [
            "Spreadsheet-mediated queue management obscures urgency and delays human decisions.",
            "Workflows without named owners create slower resolution times and weaker financial results.",
        ],
        "patterns": [
            {
                "organization": task.organization_name,
                "workflow": task.workflow_name,
                "playbook": playbooks[len(task.task_id) % len(playbooks)].name,
                "initiative": initiatives[len(task.task_id) % len(initiatives)].name,
                "decision": task.history[0].decision.decision,
                "owner": task.history[0].decision.actor_name,
                "outcome": task.history[0].outcome.status,
                "financial_result": str(task.history[0].outcome.financial_result or Decimal("0.00")),
                "resolution_time_hours": task.history[0].outcome.resolution_time_hours,
            }
            for task in tasks[:8]
            if task.history
        ],
    }


def _build_executive_review(
    holdco_dashboard: dict[str, object],
    org_summaries: list[dict[str, object]],
    initiatives: tuple[ValueCreationInitiative, ...],
    benchmarking: dict[str, object],
    decision_intelligence: dict[str, object],
) -> dict[str, object]:
    weakest_org = max(org_summaries, key=lambda item: item["aging"]["120_plus"])
    strongest_org = max(org_summaries, key=lambda item: Decimal(item["productivity"]["financial_result"]))
    return {
        "month": "June 2026",
        "executive_summary": [
            "The portfolio is standardizing around one workflow model, with HoldCo visibility now linking operations to EBITDA.",
            "Value creation is concentrated in denial reduction, workflow standardization, and productivity improvements.",
            "Leadership attention should stay on Alpha denial urgency and Charlie aging AR while Bravo scales coding throughput gains.",
        ],
        "financial_performance": {
            "portfolio_revenue": holdco_dashboard["portfolio_revenue"],
            "portfolio_ebitda": holdco_dashboard["portfolio_ebitda"],
            "revenue_at_risk": holdco_dashboard["revenue_at_risk"],
            "realized_financial_result": decision_intelligence["summary"]["financial_result"],
        },
        "operational_performance": {
            "open_work": holdco_dashboard["open_work"],
            "critical_bottlenecks": holdco_dashboard["critical_bottlenecks"],
            "top_org": strongest_org["name"],
            "watchlist_org": weakest_org["name"],
        },
        "risks": holdco_dashboard["operational_risks"],
        "wins": [
            f"{strongest_org['name']} is converting the highest documented financial result in the portfolio.",
            "Workflow definitions and decision memory are now reusable across all active organizations.",
            "Value creation initiatives have a visible realized EBITDA impact instead of only a roadmap hypothesis.",
        ],
        "required_decisions": [
            "Approve shared-service AR migration after Charlie backlog drops below target.",
            "Fund the next wave of coding automation once Bravo playbook adherence is stable.",
            "Decide whether denial-reduction playbooks should become mandatory at every new acquisition close.",
        ],
        "value_creation_progress": {
            "expected_ebitda_impact": holdco_dashboard["value_creation_progress"]["expected_ebitda_impact"],
            "realized_ebitda_impact": holdco_dashboard["value_creation_progress"]["realized_ebitda_impact"],
            "active_initiatives": sum(1 for item in initiatives if item.status in {"in_flight", "scaling"}),
        },
        "benchmark_excerpt": benchmarking["organizations"][0]["benchmarks"][:3],
    }


def _parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def _quantize_amount(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"))
