"""Workflow-native work object model for specialty RCM operations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from asc_rcm_lite.models import ASCCase, Authorization, Claim, Denial, PayerPolicy, Remit, ValidationError, require_non_empty
from asc_rcm_lite.operations import OperationalTask, WorkflowDefinition


TEAMING_STATES = {"Agent Processing", "Human Action Required", "Completed"}


@dataclass(frozen=True)
class WorkTimelineEvent:
    event_id: str
    timestamp: str
    label: str
    detail: str
    actor: str
    next_step: str

    def __post_init__(self) -> None:
        require_non_empty(self.event_id, "WorkTimelineEvent.event_id")
        require_non_empty(self.timestamp, "WorkTimelineEvent.timestamp")
        require_non_empty(self.label, "WorkTimelineEvent.label")
        require_non_empty(self.detail, "WorkTimelineEvent.detail")
        require_non_empty(self.actor, "WorkTimelineEvent.actor")
        require_non_empty(self.next_step, "WorkTimelineEvent.next_step")


@dataclass(frozen=True)
class WorkEvidence:
    evidence_id: str
    category: str
    title: str
    detail: str
    source_id: str
    recovery_probability: Decimal | None
    expected_financial_impact: Decimal | None

    def __post_init__(self) -> None:
        require_non_empty(self.evidence_id, "WorkEvidence.evidence_id")
        require_non_empty(self.category, "WorkEvidence.category")
        require_non_empty(self.title, "WorkEvidence.title")
        require_non_empty(self.detail, "WorkEvidence.detail")
        require_non_empty(self.source_id, "WorkEvidence.source_id")


@dataclass(frozen=True)
class GeneratedWorkProduct:
    artifact_id: str
    artifact_type: str
    title: str
    status: str
    summary: str

    def __post_init__(self) -> None:
        require_non_empty(self.artifact_id, "GeneratedWorkProduct.artifact_id")
        require_non_empty(self.artifact_type, "GeneratedWorkProduct.artifact_type")
        require_non_empty(self.title, "GeneratedWorkProduct.title")
        require_non_empty(self.status, "GeneratedWorkProduct.status")
        require_non_empty(self.summary, "GeneratedWorkProduct.summary")


@dataclass(frozen=True)
class WorkAction:
    action_id: str
    label: str
    owner_role: str
    status: str
    detail: str

    def __post_init__(self) -> None:
        require_non_empty(self.action_id, "WorkAction.action_id")
        require_non_empty(self.label, "WorkAction.label")
        require_non_empty(self.owner_role, "WorkAction.owner_role")
        require_non_empty(self.status, "WorkAction.status")
        require_non_empty(self.detail, "WorkAction.detail")


@dataclass(frozen=True)
class InstitutionalMemoryEntry:
    memory_id: str
    summary: str
    linked_outcome: str
    financial_result: Decimal | None

    def __post_init__(self) -> None:
        require_non_empty(self.memory_id, "InstitutionalMemoryEntry.memory_id")
        require_non_empty(self.summary, "InstitutionalMemoryEntry.summary")
        require_non_empty(self.linked_outcome, "InstitutionalMemoryEntry.linked_outcome")


@dataclass(frozen=True)
class WorkObject:
    work_object_id: str
    organization_id: str
    organization_name: str
    facility_id: str
    facility_name: str
    account_id: str
    claim_id: str | None
    task_id: str
    work_object_type: str
    title: str
    financial_impact: Decimal | None
    priority: str
    owner_role: str
    owner_name: str | None
    status: str
    workflow_status: str
    timeline: tuple[WorkTimelineEvent, ...]
    evidence: tuple[WorkEvidence, ...]
    documents: tuple[GeneratedWorkProduct, ...]
    recommendations: tuple[dict[str, object], ...]
    actions: tuple[WorkAction, ...]
    outcome: dict[str, object]
    institutional_memory: tuple[InstitutionalMemoryEntry, ...]

    def __post_init__(self) -> None:
        require_non_empty(self.work_object_id, "WorkObject.work_object_id")
        require_non_empty(self.organization_id, "WorkObject.organization_id")
        require_non_empty(self.organization_name, "WorkObject.organization_name")
        require_non_empty(self.facility_id, "WorkObject.facility_id")
        require_non_empty(self.facility_name, "WorkObject.facility_name")
        require_non_empty(self.account_id, "WorkObject.account_id")
        require_non_empty(self.task_id, "WorkObject.task_id")
        require_non_empty(self.work_object_type, "WorkObject.work_object_type")
        require_non_empty(self.title, "WorkObject.title")
        require_non_empty(self.priority, "WorkObject.priority")
        require_non_empty(self.owner_role, "WorkObject.owner_role")
        require_non_empty(self.status, "WorkObject.status")
        require_non_empty(self.workflow_status, "WorkObject.workflow_status")
        if self.status not in TEAMING_STATES:
            raise ValidationError(f"Unsupported work object status: {self.status}")
        if not self.timeline:
            raise ValidationError("WorkObject.timeline must not be empty")
        if not self.evidence:
            raise ValidationError("WorkObject.evidence must not be empty")
        if not self.documents:
            raise ValidationError("WorkObject.documents must not be empty")
        if not self.recommendations:
            raise ValidationError("WorkObject.recommendations must not be empty")
        if not self.actions:
            raise ValidationError("WorkObject.actions must not be empty")


def build_work_objects(
    *,
    cases: tuple[ASCCase, ...],
    tasks: tuple[OperationalTask, ...],
    workflows: tuple[WorkflowDefinition, ...],
    as_of_date: str,
) -> tuple[WorkObject, ...]:
    cases_by_id = {case.case_id: case for case in cases}
    workflows_by_id = {workflow.workflow_id: workflow for workflow in workflows}
    objects = []
    for task in tasks:
        case = cases_by_id.get(task.case_id)
        workflow = workflows_by_id.get(task.workflow_id)
        if case is None or workflow is None:
            continue
        objects.append(_build_work_object(task=task, case=case, workflow=workflow, as_of_date=as_of_date))
    return tuple(sorted(objects, key=lambda item: (_priority_rank(item.priority), item.organization_name, item.work_object_id)))


def serialize_work_object(item: WorkObject) -> dict[str, object]:
    return {
        "work_object_id": item.work_object_id,
        "organization_id": item.organization_id,
        "organization_name": item.organization_name,
        "facility_id": item.facility_id,
        "facility_name": item.facility_name,
        "account_id": item.account_id,
        "claim_id": item.claim_id,
        "task_id": item.task_id,
        "work_object_type": item.work_object_type,
        "title": item.title,
        "financial_impact": _money(item.financial_impact),
        "priority": item.priority,
        "owner_role": item.owner_role,
        "owner_name": item.owner_name,
        "status": item.status,
        "workflow_status": item.workflow_status,
        "timeline": [
            {
                "event_id": event.event_id,
                "timestamp": event.timestamp,
                "label": event.label,
                "detail": event.detail,
                "actor": event.actor,
                "next_step": event.next_step,
            }
            for event in item.timeline
        ],
        "evidence": [
            {
                "evidence_id": evidence.evidence_id,
                "category": evidence.category,
                "title": evidence.title,
                "detail": evidence.detail,
                "source_id": evidence.source_id,
                "recovery_probability": _money(evidence.recovery_probability) if evidence.recovery_probability is not None else None,
                "expected_financial_impact": _money(evidence.expected_financial_impact),
            }
            for evidence in item.evidence
        ],
        "documents": [
            {
                "artifact_id": document.artifact_id,
                "artifact_type": document.artifact_type,
                "title": document.title,
                "status": document.status,
                "summary": document.summary,
            }
            for document in item.documents
        ],
        "recommendations": list(item.recommendations),
        "actions": [
            {
                "action_id": action.action_id,
                "label": action.label,
                "owner_role": action.owner_role,
                "status": action.status,
                "detail": action.detail,
            }
            for action in item.actions
        ],
        "outcome": item.outcome,
        "institutional_memory": [
            {
                "memory_id": entry.memory_id,
                "summary": entry.summary,
                "linked_outcome": entry.linked_outcome,
                "financial_result": _money(entry.financial_result),
            }
            for entry in item.institutional_memory
        ],
    }


def _build_work_object(*, task: OperationalTask, case: ASCCase, workflow: WorkflowDefinition, as_of_date: str) -> WorkObject:
    claim = case.claims[0] if case.claims else None
    account_id = _account_id(task, claim)
    work_type = _work_object_type(task)
    return WorkObject(
        work_object_id=f"WO-{task.task_id}",
        organization_id=task.organization_id or "unknown_org",
        organization_name=task.organization_name or "Unknown Organization",
        facility_id=task.facility_id or "unknown_facility",
        facility_name=task.facility_name or "Unknown Facility",
        account_id=account_id,
        claim_id=claim.claim_id if claim else None,
        task_id=task.task_id,
        work_object_type=work_type,
        title=task.title,
        financial_impact=task.amount_at_risk,
        priority=task.priority_band,
        owner_role=task.owner_role,
        owner_name=task.assignee_name,
        status=_teaming_state(task),
        workflow_status=task.status,
        timeline=_timeline(task=task, case=case, workflow=workflow, claim=claim, as_of_date=as_of_date),
        evidence=_evidence(task=task, case=case, claim=claim),
        documents=_documents(task=task, case=case, work_type=work_type),
        recommendations=_recommendations(task=task, case=case),
        actions=_actions(task=task, workflow=workflow),
        outcome=_outcome(task),
        institutional_memory=_institutional_memory(task),
    )


def _account_id(task: OperationalTask, claim: Claim | None) -> str:
    payer = claim.payer_id if claim else "unassigned"
    return f"ACC-{task.organization_id or 'ORG'}-{payer}"


def _work_object_type(task: OperationalTask) -> str:
    mapping = {
        "underpayment": "Underpayment",
        "medical_necessity": "Medical Necessity Denial",
        "prior_authorization": "Authorization",
        "appeal_deadline_risk": "Appeal",
        "stale_followup": "AR Follow-Up",
        "missing_payer_response": "AR Follow-Up",
        "high_dollar_aging": "AR Follow-Up",
        "timely_filing": "Timely Filing",
        "bundled_procedure_risk": "Coding Review",
        "documentation_insufficiency": "Missing Documentation",
        "missing_implant_charge": "Coding Review",
    }
    return mapping.get(task.task_type, task.task_type.replace("_", " ").title())


def _teaming_state(task: OperationalTask) -> str:
    if task.status == "completed":
        return "Completed"
    if task.history:
        return "Human Action Required"
    return "Agent Processing"


def _timeline(*, task: OperationalTask, case: ASCCase, workflow: WorkflowDefinition, claim: Claim | None, as_of_date: str) -> tuple[WorkTimelineEvent, ...]:
    events: list[WorkTimelineEvent] = []
    if claim and claim.submitted_date:
        events.append(
            WorkTimelineEvent(
                event_id=f"{task.task_id}-claim-submitted",
                timestamp=claim.submitted_date,
                label="Claim Submitted",
                detail=f"Claim {claim.claim_id} was submitted to payer {claim.payer_id}.",
                actor="System of Record",
                next_step="Wait for adjudication or trigger work if exceptions appear.",
            )
        )
    for remit in case.remits[:1]:
        events.append(
            WorkTimelineEvent(
                event_id=f"{task.task_id}-{remit.remit_id}",
                timestamp=remit.remit_date,
                label="Remit Received",
                detail=f"Remit posted with paid amount ${remit.paid_amount:.2f} and allowed amount ${remit.allowed_amount:.2f}.",
                actor="Payer",
                next_step="Validate whether payment or denial created follow-up work.",
            )
        )
    for denial in case.denials[:1]:
        events.append(
            WorkTimelineEvent(
                event_id=f"{task.task_id}-{denial.denial_id}",
                timestamp=_days_before(as_of_date, 10),
                label="Denial Classified",
                detail=f"Denial {denial.denial_code} classified as {task.task_type.replace('_', ' ')}.",
                actor="Citron",
                next_step="Collect evidence and generate the required work product.",
            )
        )
    events.append(
        WorkTimelineEvent(
            event_id=f"{task.task_id}-assigned",
            timestamp=_days_before(as_of_date, 4),
            label="Work Assigned",
            detail=f"{task.title} routed to {task.assignee_name or task.owner_role} in {task.team_name or workflow.default_team_name}.",
            actor="Citron",
            next_step="Review evidence before taking the next workflow action.",
        )
    )
    events.append(
        WorkTimelineEvent(
            event_id=f"{task.task_id}-evidence",
            timestamp=_days_before(as_of_date, 3),
            label="Evidence Generated",
            detail=f"Citron assembled payer, claim, and workflow evidence for {task.title.lower()}.",
            actor="Citron",
            next_step="Operator should validate evidence and generated work product.",
        )
    )
    for index, record in enumerate(task.history, start=1):
        events.append(
            WorkTimelineEvent(
                event_id=f"{task.task_id}-decision-{index}",
                timestamp=record.decision.timestamp,
                label="Human Decision",
                detail=record.decision.decision,
                actor=record.decision.actor_name,
                next_step=record.outcome.status,
            )
        )
        events.append(
            WorkTimelineEvent(
                event_id=f"{task.task_id}-outcome-{index}",
                timestamp=record.decision.timestamp,
                label="Resolution",
                detail=record.outcome.impact_summary,
                actor="Citron + Operator",
                next_step="Institutional memory updated.",
            )
        )
    return tuple(events)


def _evidence(*, task: OperationalTask, case: ASCCase, claim: Claim | None) -> tuple[WorkEvidence, ...]:
    evidence: list[WorkEvidence] = []
    if claim:
        evidence.append(
            WorkEvidence(
                evidence_id=f"EV-{task.task_id}-claim",
                category="Supporting Documentation",
                title="Claim History",
                detail=f"Claim {claim.claim_id} billed at ${claim.billed_amount:.2f} with status {claim.status}.",
                source_id=claim.citation.source_id,
                recovery_probability=Decimal("0.72"),
                expected_financial_impact=task.amount_at_risk,
            )
        )
    for policy in case.payer_policies[:1]:
        evidence.append(
            WorkEvidence(
                evidence_id=f"EV-{task.task_id}-{policy.payer_policy_id}",
                category="Payer Rules",
                title=policy.policy_type.replace("_", " ").title(),
                detail=policy.requirement,
                source_id=policy.citation.source_id,
                recovery_probability=Decimal("0.68"),
                expected_financial_impact=task.amount_at_risk,
            )
        )
    if task.history:
        record = task.history[0]
        evidence.append(
            WorkEvidence(
                evidence_id=f"EV-{task.task_id}-prior-outcome",
                category="Prior Outcomes",
                title="Similar prior result",
                detail=record.outcome.impact_summary,
                source_id=record.record_id,
                recovery_probability=Decimal("0.64"),
                expected_financial_impact=record.outcome.financial_result,
            )
        )
    else:
        evidence.append(
            WorkEvidence(
                evidence_id=f"EV-{task.task_id}-similar-case",
                category="Similar Cases",
                title="Comparable synthetic workflow",
                detail=f"Similar {task.workflow_name.lower()} work resolved when evidence and packet were prepared first.",
                source_id=task.cited_evidence_ids[0],
                recovery_probability=Decimal("0.61"),
                expected_financial_impact=task.amount_at_risk,
            )
        )
    return tuple(evidence)


def _documents(*, task: OperationalTask, case: ASCCase, work_type: str) -> tuple[GeneratedWorkProduct, ...]:
    artifacts = [
        GeneratedWorkProduct(
            artifact_id=f"DOC-{task.task_id}-timeline",
            artifact_type="Claim Timeline",
            title="Claim Timeline",
            status="generated",
            summary=f"Chronological work record for {task.title.lower()} with claim, denial, and operator events.",
        )
    ]
    if "Denial" in work_type or work_type in {"Appeal", "Authorization"}:
        artifacts.append(
            GeneratedWorkProduct(
                artifact_id=f"DOC-{task.task_id}-packet",
                artifact_type="Appeal Packet" if "Denial" in work_type or work_type == "Appeal" else "Authorization Packet",
                title="Operational Packet",
                status="generated",
                summary=f"Cited evidence and supporting documentation assembled for {task.title.lower()}.",
            )
        )
    if work_type == "AR Follow-Up" or work_type == "Underpayment":
        artifacts.append(
            GeneratedWorkProduct(
                artifact_id=f"DOC-{task.task_id}-payer-summary",
                artifact_type="Payer Summary",
                title="Payer Summary",
                status="generated",
                summary="Condensed payer history, prior touches, and next-step plan prepared for outreach.",
            )
        )
    artifacts.append(
        GeneratedWorkProduct(
            artifact_id=f"DOC-{task.task_id}-checklist",
            artifact_type="Documentation Checklist",
            title="Documentation Checklist",
            status="generated",
            summary=f"Operator checklist prepared for {work_type.lower()} completion.",
        )
    )
    return tuple(artifacts)


def _recommendations(*, task: OperationalTask, case: ASCCase) -> tuple[dict[str, object], ...]:
    recommendation = task.recommendations[0]
    return (
        {
            "recommendation_id": recommendation.recommendation_id,
            "title": recommendation.title,
            "summary": recommendation.summary,
            "suggested_action": recommendation.suggested_action,
            "payer_rules": [policy.requirement for policy in case.payer_policies[:1]],
            "prior_outcomes": [record.outcome.status for record in task.history[:1]],
            "similar_cases": [task.source_case_scenario],
            "supporting_documentation": list(task.cited_evidence_ids),
            "recovery_probability": "0.68",
            "expected_financial_impact": _money(task.amount_at_risk),
        },
    )


def _actions(*, task: OperationalTask, workflow: WorkflowDefinition) -> tuple[WorkAction, ...]:
    current = "completed" if task.status == "completed" else "ready"
    return tuple(
        WorkAction(
            action_id=f"ACT-{task.task_id}-{index}",
            label=label.replace("_", " ").title(),
            owner_role=task.owner_role,
            status=current if index == 0 else ("available" if task.status != "completed" else "completed"),
            detail=f"{workflow.name} action available to {task.owner_role}.",
        )
        for index, label in enumerate(workflow.decision_options[:3], start=1)
    )


def _outcome(task: OperationalTask) -> dict[str, object]:
    if task.outcome is not None:
        return {
            "status": task.outcome.status,
            "financial_result": _money(task.outcome.financial_result),
            "resolution_time_hours": task.outcome.resolution_time_hours,
            "impact_summary": task.outcome.impact_summary,
            "notes": task.outcome.notes,
        }
    if task.history:
        record = task.history[-1]
        return {
            "status": record.outcome.status,
            "financial_result": _money(record.outcome.financial_result),
            "resolution_time_hours": record.outcome.resolution_time_hours,
            "impact_summary": record.outcome.impact_summary,
            "notes": record.outcome.notes,
        }
    return {
        "status": "Pending",
        "financial_result": "0.00",
        "resolution_time_hours": None,
        "impact_summary": "Waiting for operator action.",
        "notes": "Citron has prepared evidence and suggested next actions.",
    }


def _institutional_memory(task: OperationalTask) -> tuple[InstitutionalMemoryEntry, ...]:
    if not task.history:
        return (
            InstitutionalMemoryEntry(
                memory_id=f"MEMORY-{task.task_id}-pending",
                summary="No prior human decision has been captured yet. The next operator action will create institutional memory.",
                linked_outcome="Pending",
                financial_result=Decimal("0.00"),
            ),
        )
    return tuple(
        InstitutionalMemoryEntry(
            memory_id=f"MEMORY-{record.record_id}",
            summary=f"{record.decision.actor_name} chose '{record.decision.decision}' and produced '{record.outcome.status}'.",
            linked_outcome=record.outcome.status,
            financial_result=record.outcome.financial_result,
        )
        for record in task.history
    )


def _days_before(base_date: str, days: int) -> str:
    return (date.fromisoformat(base_date) - timedelta(days=days)).isoformat()


def _money(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return f"{value:.2f}"


def _priority_rank(priority: str) -> tuple[int, str]:
    order = {"urgent": 0, "high": 1, "normal": 2, "low": 3}
    return (order.get(priority, 4), priority)
