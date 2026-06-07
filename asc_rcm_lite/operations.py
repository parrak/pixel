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


def build_portfolio_snapshot(tasks: tuple[OperationalTask, ...], workflows: tuple[WorkflowDefinition, ...]) -> dict[str, object]:
    blueprint = _portfolio_blueprint()
    organizations = blueprint["organizations"]
    users = blueprint["users"]
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
    for organization in organizations:
        org_tasks = [task for task in tasks if task.organization_id == organization.organization_id]
        org_histories = [record for task in org_tasks for record in task.history]
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

    return {
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
        "organization_summaries": org_summaries,
        "role_views": role_views,
        "monday_morning": monday_story,
        "acquisition_defaults": {
            "specialties": ["ASC", "Ophthalmology", "GI", "Orthopedics"],
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
        "Authorization intake",
        "Coding review",
        "Denial management",
        "AR follow-up",
        "Management review",
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
    return {
        "specialty": specialty,
        "headcount": headcount,
        "workflow_maturity": workflow_maturity,
        "systems": list(systems),
        "workflow_map": workflow_map,
        "operational_gaps": gaps,
        "standardization_opportunities": opportunities,
        "deployment_plan": deployment_plan,
        "operating_model": {
            "integration_layer": sorted(set(systems)),
            "citron_layers": ["Workflow Engine", "Decision Memory", "Portfolio Rollup", "Operator Queues"],
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


def _parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def _quantize_amount(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"))
