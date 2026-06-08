"""Workflow-native work object model for specialty RCM operations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from asc_rcm_lite.models import ASCCase, Claim, ValidationError, require_non_empty
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
    workflow_graph: dict[str, object]
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
        if not self.workflow_graph:
            raise ValidationError("WorkObject.workflow_graph must not be empty")
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


def build_account_workspaces(work_objects: tuple[WorkObject, ...]) -> tuple[dict[str, object], ...]:
    grouped: dict[str, list[WorkObject]] = {}
    for item in work_objects:
        grouped.setdefault(item.account_id, []).append(item)

    workspaces: list[dict[str, object]] = []
    for account_id, items in sorted(grouped.items()):
        items = sorted(items, key=lambda work: (_priority_rank(work.priority), work.work_object_id))
        primary = items[0]
        timeline = sorted(
            [event for item in items for event in item.timeline],
            key=lambda event: (event.timestamp, event.event_id),
        )
        evidence = _dedupe_by_id([entry for item in items for entry in item.evidence], "evidence_id")
        documents = _dedupe_by_id([entry for item in items for entry in item.documents], "artifact_id")
        memory = _dedupe_by_id([entry for item in items for entry in item.institutional_memory], "memory_id")
        recovery_potential = sum((item.financial_impact or Decimal("0.00") for item in items), Decimal("0.00"))
        workspaces.append(
            {
                "account_id": account_id,
                "organization_name": primary.organization_name,
                "facility_name": primary.facility_name,
                "claim_summary": {
                    "claim_id": primary.claim_id,
                    "open_work_objects": len(items),
                    "financial_impact": _money(recovery_potential),
                    "status": primary.workflow_status,
                },
                "payer_summary": {
                    "payer_id": _payer_from_account(account_id),
                    "current_owner": primary.owner_name or primary.owner_role,
                    "recovery_potential": _money(recovery_potential),
                },
                "timeline": [_timeline_to_dict(event) for event in timeline],
                "open_work_objects": [serialize_work_object(item) for item in items],
                "evidence": [_evidence_to_dict(item) for item in evidence],
                "generated_artifacts": [_document_to_dict(item) for item in documents],
                "recommended_actions": [recommendation for item in items for recommendation in item.recommendations],
                "prior_outcomes": [item.outcome for item in items if item.outcome.get("status") != "Pending"],
                "activity_history": [_memory_to_dict(item) for item in memory],
                "current_owner": primary.owner_name or primary.owner_role,
                "status": primary.status,
                "recovery_potential": _money(recovery_potential),
            }
        )
    return tuple(workspaces)


def build_denial_resolution_workspaces(work_objects: tuple[WorkObject, ...]) -> tuple[dict[str, object], ...]:
    spaces = []
    for item in work_objects:
        if "Denial" not in item.work_object_type and item.work_object_type not in {"Appeal", "Authorization"}:
            continue
        stages = _stage_map(
            current=item.workflow_status,
            ordered=(
                "Denial Received",
                "Classification",
                "Evidence Gathering",
                "Packet Assembly",
                "Appeal Generation",
                "Submission",
                "Payer Review",
                "Resolution",
                "Payment",
            ),
        )
        spaces.append(
            {
                "work_object_id": item.work_object_id,
                "title": item.title,
                "claim_id": item.claim_id,
                "organization_name": item.organization_name,
                "financial_impact": _money(item.financial_impact),
                "stages": stages,
                "workflow_graph": item.workflow_graph,
                "timeline": [_timeline_to_dict(event) for event in item.timeline],
                "artifacts": [_document_to_dict(doc) for doc in item.documents],
                "evidence": [_evidence_to_dict(evidence) for evidence in item.evidence],
                "outcome": item.outcome,
            }
        )
    return tuple(spaces)


def build_ar_recovery_workspaces(work_objects: tuple[WorkObject, ...]) -> tuple[dict[str, object], ...]:
    spaces = []
    for item in work_objects:
        if item.work_object_type not in {"AR Follow-Up", "Underpayment"}:
            continue
        scenario_tags = []
        financial_impact = item.financial_impact or Decimal("0.00")
        if any("90" in event.detail or "120" in event.detail for event in item.timeline):
            scenario_tags.append("90+ Day Aging")
        if "no-response" in item.title.lower() or "missing" in item.title.lower():
            scenario_tags.append("No Response")
        if item.work_object_type == "Underpayment":
            scenario_tags.append("Underpayment")
        if any(doc.artifact_type == "Payer Summary" for doc in item.documents):
            scenario_tags.append("Stale Follow-Up")
        if not scenario_tags:
            scenario_tags.append("AR Follow-Up")
        spaces.append(
            {
                "work_object_id": item.work_object_id,
                "title": item.title,
                "financial_impact": _money(financial_impact),
                "scenario_tags": scenario_tags,
                "actions": [_action_to_dict(action) for action in item.actions],
                "workflow_graph": item.workflow_graph,
                "evidence": [_evidence_to_dict(evidence) for evidence in item.evidence],
                "generated_artifacts": [_document_to_dict(doc) for doc in item.documents],
                "timeline": [_timeline_to_dict(event) for event in item.timeline],
                "outcome": item.outcome,
            }
        )
    return tuple(spaces)


def build_decision_intelligence_registry(work_objects: tuple[WorkObject, ...]) -> dict[str, object]:
    records = []
    similar_case_index: dict[str, list[dict[str, object]]] = {}
    for item in work_objects:
        for memory in item.institutional_memory:
            record = {
                "work_object_id": item.work_object_id,
                "problem": item.work_object_type,
                "evidence": [_evidence_to_dict(evidence) for evidence in item.evidence[:2]],
                "recommendation": item.recommendations[0]["title"],
                "resolution": item.outcome["status"],
                "financial_result": item.outcome["financial_result"],
                "time_to_resolution": item.outcome["resolution_time_hours"],
                "operator": item.owner_name or item.owner_role,
                "facility": item.facility_name,
                "payer": _payer_from_account(item.account_id),
                "specialty": "ASC",
                "outcome": item.outcome["impact_summary"],
                "memory": memory.summary,
            }
            records.append(record)
            similar_case_index.setdefault(item.work_object_type, []).append(record)
    successful = [record for record in records if record["financial_result"] not in {None, "0.00"}]
    failed = [record for record in records if record["resolution"] == "Pending"]
    return {
        "records": records,
        "similar_cases": {key: value[:3] for key, value in similar_case_index.items()},
        "successful_recoveries": successful[:10],
        "failed_recoveries": failed[:10],
        "appeal_history": [record for record in records if record["problem"] in {"Appeal", "Medical Necessity Denial", "Missing Documentation"}],
        "payer_history": _group_counts(records, "payer"),
    }


def build_payer_intelligence_graph(work_objects: tuple[WorkObject, ...]) -> dict[str, object]:
    graph: dict[str, dict[str, object]] = {}
    for item in work_objects:
        payer = _payer_from_account(item.account_id)
        node = graph.setdefault(
            payer,
            {
                "payer": payer,
                "denial_patterns": {},
                "appeal_success_rates": {},
                "evidence_effectiveness": {},
                "recovery_rates": {},
                "recovery_time_hours": [],
                "escalation_paths": [],
                "authorization_requirements": [],
                "response_times": [],
                "playbook_answers": {},
            },
        )
        node["denial_patterns"][item.work_object_type] = node["denial_patterns"].get(item.work_object_type, 0) + 1
        if item.work_object_type in {"Appeal", "Medical Necessity Denial", "Missing Documentation"}:
            result = Decimal(item.outcome["financial_result"] or "0.00")
            node["appeal_success_rates"][item.work_object_type] = "high" if result > 0 else "low"
        for evidence in item.evidence:
            node["evidence_effectiveness"][evidence.category] = node["evidence_effectiveness"].get(evidence.category, 0) + 1
        node["recovery_rates"][item.work_object_type] = item.outcome["financial_result"]
        if item.outcome["resolution_time_hours"] is not None:
            node["recovery_time_hours"].append(item.outcome["resolution_time_hours"])
            node["response_times"].append(item.outcome["resolution_time_hours"])
        if any(action.label.lower().startswith("escalate") for action in item.actions):
            node["escalation_paths"].append(f"{item.work_object_type} -> manager escalation")
        if item.work_object_type == "Authorization":
            node["authorization_requirements"].extend(recommendation["payer_rules"] for recommendation in item.recommendations)
        node["playbook_answers"][item.work_object_type] = f"What works: lead with {item.evidence[0].title.lower()} and generated {item.documents[0].artifact_type.lower()}."
    for node in graph.values():
        if node["recovery_time_hours"]:
            avg = sum(node["recovery_time_hours"]) / len(node["recovery_time_hours"])
            node["average_recovery_time_hours"] = round(avg, 1)
        else:
            node["average_recovery_time_hours"] = None
    return {
        "payers": list(graph.values()),
        "questions": [
            {
                "question": "What typically works for this payer and denial combination?",
                "answers": {node["payer"]: next(iter(node["playbook_answers"].values()), "No pattern available.") for node in graph.values()},
            }
        ],
    }


def build_manager_intervention_system(work_objects: tuple[WorkObject, ...]) -> dict[str, object]:
    open_items = [item for item in work_objects if item.status != "Completed"]
    urgent_items = [item for item in open_items if item.priority == "urgent"]
    blocked_items = [item for item in open_items if item.workflow_status == "blocked"]
    return {
        "queue_rebalancing": [
            {
                "action": "Redistribute highest-value AR work to available specialists",
                "target_work_objects": [item.work_object_id for item in urgent_items[:3]],
                "impact": "Recovered dollars accelerate when top balances are worked first.",
            }
        ],
        "escalation_routing": [
            {
                "action": "Escalate unresolved denial and authorization blockers",
                "target_work_objects": [item.work_object_id for item in blocked_items[:3]],
                "impact": "Blockers are removed earlier and queue aging declines.",
            }
        ],
        "workload_redistribution": [
            {
                "owner": item.owner_name or item.owner_role,
                "open_work_objects": sum(1 for work in open_items if work.owner_name == item.owner_name),
            }
            for item in open_items[:5]
        ],
        "priority_overrides": [
            {
                "work_object_id": item.work_object_id,
                "previous_priority": item.priority,
                "override_priority": "urgent",
                "reason": "High financial impact and stale timeline activity.",
            }
            for item in sorted(open_items, key=lambda work: work.financial_impact or Decimal("0.00"), reverse=True)[:3]
        ],
        "capacity_planning": {
            "open_work_objects": len(open_items),
            "urgent_work_objects": len(urgent_items),
            "blocked_work_objects": len(blocked_items),
        },
    }


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
        "workflow_graph": item.workflow_graph,
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
        workflow_graph=_workflow_graph(task=task, case=case, workflow=workflow, claim=claim, work_type=work_type, as_of_date=as_of_date),
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


def _workflow_graph(
    *,
    task: OperationalTask,
    case: ASCCase,
    workflow: WorkflowDefinition,
    claim: Claim | None,
    work_type: str,
    as_of_date: str,
) -> dict[str, object]:
    stage_labels = _lifecycle_labels(work_type)
    current_index = _current_stage_index(work_type=work_type, task=task, claim=claim)
    owner_name = task.assignee_name or task.owner_role.replace("_", " ").title()
    owner_role = task.owner_role
    team_name = task.team_name or workflow.default_team_name
    dependency = _current_dependency(work_type=work_type, task=task)
    blocker = dependency if task.status == "blocked" else _current_blocker(work_type=work_type, task=task)
    days_in_state = 12 if work_type in {"Appeal", "Medical Necessity Denial", "Missing Documentation"} else max(3, min(task.aging_days or 9, 21))
    deadline_days_remaining = max(1, 20 - min(days_in_state, 19))
    stages = []
    for index, label in enumerate(stage_labels):
        if index < current_index:
            status = "complete"
        elif index == current_index:
            status = "current"
        else:
            status = "next" if index == current_index + 1 else "pending"
        stages.append(
            {
                "state_id": _state_id(label),
                "label": label,
                "status": status,
                "owner": owner_name if status == "current" else _stage_owner(label),
                "team": team_name if status == "current" else _stage_team(label),
                "dependency": dependency if status == "current" else _stage_dependency(label),
                "blocker": blocker if status == "current" else "",
            }
        )
    current = stages[current_index]
    next_stage = stages[current_index + 1] if current_index + 1 < len(stages) else current
    return {
        "object_type": work_type,
        "current_state": current["label"],
        "current_state_id": current["state_id"],
        "owner": owner_name,
        "owner_role": owner_role,
        "team": team_name,
        "dependency": dependency,
        "blocker": blocker,
        "waiting_on": dependency,
        "days_in_state": days_in_state,
        "deadline_days_remaining": deadline_days_remaining,
        "expected_recovery": _money(task.amount_at_risk),
        "next_state": next_stage["label"],
        "next_state_id": next_stage["state_id"],
        "stages": stages,
        "source_claim_id": claim.claim_id if claim else None,
        "source_case_id": case.case_id,
    }


def _lifecycle_labels(work_type: str) -> list[str]:
    if work_type in {"Medical Necessity Denial", "Missing Documentation", "Appeal"}:
        return ["Patient", "Procedure", "Coding", "Claim", "Denial", "Appeal", "Resolution", "Payment"]
    if work_type == "Authorization":
        return ["Patient Scheduled", "Authorization", "Procedure", "Coding", "Claim Submission", "Payer Review", "Payment"]
    if work_type in {"AR Follow-Up", "Underpayment"}:
        return ["Patient", "Procedure", "Coding", "Claim", "Payer Review", "Recovery Workflow", "Resolution", "Payment"]
    if work_type in {"Coding Review", "Charge Capture"}:
        return ["Patient", "Encounter", "Procedure", "Documentation", "Coding Review", "Charge Capture", "Claim Submission", "Payment"]
    return ["Patient", "Procedure", "Coding", "Claim Submission", "Payer Review", "Payment"]


def _current_stage_index(*, work_type: str, task: OperationalTask, claim: Claim | None) -> int:
    labels = _lifecycle_labels(work_type)
    if task.status == "completed":
        return max(len(labels) - 1, 0)
    if work_type in {"Medical Necessity Denial", "Missing Documentation"}:
        return labels.index("Appeal") if task.status in {"in_progress", "blocked"} else labels.index("Denial")
    if work_type == "Appeal":
        return labels.index("Appeal")
    if work_type == "Authorization":
        return labels.index("Authorization")
    if work_type in {"AR Follow-Up", "Underpayment"}:
        return labels.index("Recovery Workflow")
    if work_type in {"Coding Review", "Charge Capture"}:
        return labels.index("Coding Review")
    if claim and claim.status == "submitted":
        return labels.index("Claim Submission") if "Claim Submission" in labels else labels.index("Claim")
    return min(3, len(labels) - 1)


def _current_dependency(*, work_type: str, task: OperationalTask) -> str:
    if task.status == "blocked":
        return "Waiting on Payer"
    if work_type in {"Medical Necessity Denial", "Missing Documentation", "Appeal"}:
        return "Waiting on Payer" if task.status == "in_progress" else "Waiting on Provider Documentation"
    if work_type == "Authorization":
        return "Waiting on Authorization"
    if work_type in {"Coding Review", "Charge Capture"}:
        return "Waiting on Coding Review"
    if work_type in {"AR Follow-Up", "Underpayment"}:
        return "Waiting on Payer"
    return "Waiting on Operator Review"


def _current_blocker(*, work_type: str, task: OperationalTask) -> str:
    if task.priority_band == "urgent":
        return "Deadline risk"
    if work_type in {"Medical Necessity Denial", "Missing Documentation"}:
        return "Provider documentation"
    if work_type == "Authorization":
        return "Payer requirements"
    if work_type in {"AR Follow-Up", "Underpayment"}:
        return "Payer response"
    if work_type in {"Coding Review", "Charge Capture"}:
        return "Documentation completeness"
    return "None"


def _stage_owner(label: str) -> str:
    if label in {"Patient", "Encounter", "Procedure", "Patient Scheduled"}:
        return "Facility"
    if label in {"Authorization"}:
        return "Authorization Specialist"
    if label in {"Coding", "Coding Review", "Charge Capture", "Documentation"}:
        return "Coding Team"
    if label in {"Denial", "Appeal", "Resolution"}:
        return "Denial Specialist"
    if label in {"Payer Review", "Payment"}:
        return "Payer"
    if label in {"Claim", "Claim Submission", "Recovery Workflow"}:
        return "AR Specialist"
    return "Operator"


def _stage_team(label: str) -> str:
    owner = _stage_owner(label)
    if owner == "Payer":
        return "External"
    if owner == "Facility":
        return "Facility Operations"
    return owner


def _stage_dependency(label: str) -> str:
    if label in {"Payer Review", "Payment"}:
        return "Waiting on Payer"
    if label in {"Authorization"}:
        return "Waiting on Authorization"
    if label in {"Coding", "Coding Review", "Charge Capture", "Documentation"}:
        return "Waiting on Coding Review"
    if label in {"Denial", "Appeal"}:
        return "Waiting on Evidence"
    return "None"


def _state_id(label: str) -> str:
    return label.lower().replace(" ", "_").replace("-", "_")


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


def _timeline_to_dict(event: WorkTimelineEvent) -> dict[str, object]:
    return {
        "event_id": event.event_id,
        "timestamp": event.timestamp,
        "label": event.label,
        "detail": event.detail,
        "actor": event.actor,
        "next_step": event.next_step,
    }


def _evidence_to_dict(item: WorkEvidence) -> dict[str, object]:
    return {
        "evidence_id": item.evidence_id,
        "category": item.category,
        "title": item.title,
        "detail": item.detail,
        "source_id": item.source_id,
        "recovery_probability": _money(item.recovery_probability) if item.recovery_probability is not None else None,
        "expected_financial_impact": _money(item.expected_financial_impact),
    }


def _document_to_dict(item: GeneratedWorkProduct) -> dict[str, object]:
    return {
        "artifact_id": item.artifact_id,
        "artifact_type": item.artifact_type,
        "title": item.title,
        "status": item.status,
        "summary": item.summary,
    }


def _action_to_dict(item: WorkAction) -> dict[str, object]:
    return {
        "action_id": item.action_id,
        "label": item.label,
        "owner_role": item.owner_role,
        "status": item.status,
        "detail": item.detail,
    }


def _memory_to_dict(item: InstitutionalMemoryEntry) -> dict[str, object]:
    return {
        "memory_id": item.memory_id,
        "summary": item.summary,
        "linked_outcome": item.linked_outcome,
        "financial_result": _money(item.financial_result),
    }


def _dedupe_by_id(items, field_name: str):
    seen = {}
    for item in items:
        seen[getattr(item, field_name)] = item
    return list(seen.values())


def _payer_from_account(account_id: str) -> str:
    parts = account_id.split("-")
    return parts[-1] if parts else account_id


def _stage_map(*, current: str, ordered: tuple[str, ...]) -> list[dict[str, object]]:
    statuses = []
    completed = current == "completed"
    for index, label in enumerate(ordered):
        if completed:
            status = "completed"
        elif index == 0:
            status = "current"
        else:
            status = "up_next"
        statuses.append({"label": label, "status": status})
    return statuses


def _group_counts(records: list[dict[str, object]], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        key = str(record[field])
        counts[key] = counts.get(key, 0) + 1
    return counts
