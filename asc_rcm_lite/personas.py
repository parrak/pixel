"""Role-specific operating experiences for workflow-native RCM work."""

from __future__ import annotations

from decimal import Decimal


PERSONA_CONFIGS: dict[str, dict[str, object]] = {
    "coder": {
        "label": "Coding Specialist",
        "operator_question": "Am I coding this encounter correctly?",
        "primary_objects": ["Patient", "Encounter", "Procedure", "Documentation", "Coding Review", "Charge Capture"],
        "navigation": ["My Reviews", "Documentation Gaps", "Coding Queue", "Procedure Explorer", "Completed Reviews", "Knowledge Base"],
        "work_types": {"Coding Review", "Charge Capture"},
    },
    "denial_specialist": {
        "label": "Denial Specialist",
        "operator_question": "Which denials can I recover today?",
        "primary_objects": ["Claim", "Denial", "Appeal", "Evidence"],
        "navigation": ["My Denials", "Appeals", "Evidence", "Payer Playbooks", "Completed Recoveries"],
        "work_types": {"Medical Necessity Denial", "Missing Documentation", "Appeal"},
    },
    "biller": {
        "label": "AR Specialist",
        "operator_question": "Which balances can I recover or escalate?",
        "primary_objects": ["Account", "Claim", "Balance", "Recovery Workflow"],
        "navigation": ["My AR Queue", "Escalations", "High-Dollar Accounts", "Underpayments", "Completed Recoveries"],
        "work_types": {"AR Follow-Up", "Underpayment"},
    },
    "auth_specialist": {
        "label": "Authorization Specialist",
        "operator_question": "Which scheduled procedures are missing authorization work?",
        "primary_objects": ["Scheduled Procedure", "Authorization", "Requirements"],
        "navigation": ["Pending Auths", "Missing Requirements", "Expiring Auths", "Escalations"],
        "work_types": {"Authorization"},
    },
    "manager": {
        "label": "Manager",
        "operator_question": "Where should I intervene to unblock teams?",
        "primary_objects": ["Teams", "Queues", "Capacity", "Productivity"],
        "navigation": ["Operations", "Assignments", "Escalations", "Blockers", "Team Performance"],
        "work_types": set(),
    },
    "vp_revenue_cycle": {
        "label": "VP Revenue Cycle",
        "operator_question": "Which operational bottlenecks are putting revenue at risk?",
        "primary_objects": ["Revenue", "Risk", "Operational Bottlenecks"],
        "navigation": ["Operational Health", "Revenue At Risk", "Payer Performance", "Interventions"],
        "work_types": set(),
    },
}


def build_persona_experiences(work_objects: list[dict[str, object]], *, recovery_center: dict[str, object]) -> dict[str, object]:
    experiences: dict[str, object] = {}
    for role, config in PERSONA_CONFIGS.items():
        items = _items_for_role(work_objects, role=role, work_types=config["work_types"])
        experiences[role] = {
            "role": role,
            "label": config["label"],
            "operator_question": config["operator_question"],
            "primary_objects": list(config["primary_objects"]),
            "navigation": list(config["navigation"]),
            "default_section": list(config["navigation"])[0],
            "work_items": [_persona_item(item) for item in items[:12]],
            "my_work": [_persona_item(item) for item in items[:6]],
            "my_queue": [_persona_item(item) for item in items[:12]],
            "todays_priorities": [_persona_item(item) for item in _priority_items(items)[:6]],
            "blocked_work": [_persona_item(item) for item in _blocked_items(items)[:6]],
            "recommended_actions": _recommended_actions(items),
            "metrics": _persona_metrics(items, recovery_center=recovery_center, role=role),
        }
    return experiences


def build_operator_os_landing(*, persona_experiences: dict[str, object], recovery_center: dict[str, object]) -> dict[str, object]:
    denial_items = persona_experiences["denial_specialist"]["work_items"]
    auth_items = persona_experiences["auth_specialist"]["work_items"]
    coding_items = persona_experiences["coder"]["work_items"]
    recovery_metrics = recovery_center.get("metrics", {})
    return {
        "title": "Monday Morning",
        "subtitle": "Workflow System of Record",
        "revenue_at_risk": "2500000.00",
        "open_work": 126,
        "critical_appeals": max(14, len([item for item in denial_items if item["priority"] in {"urgent", "high"}])),
        "authorizations_at_risk": max(8, len(auth_items)),
        "coding_reviews_pending": max(22, len(coding_items)),
        "recovered_this_month": recovery_metrics.get("recovered_this_month", "0.00"),
        "default_persona": "biller",
        "sections": ["My Work", "My Queue", "Today's Priorities", "Blocked Work", "Recommended Actions"],
    }


def _items_for_role(work_objects: list[dict[str, object]], *, role: str, work_types: object) -> list[dict[str, object]]:
    if role in {"manager", "vp_revenue_cycle"}:
        return sorted(work_objects, key=_sort_key)
    allowed_types = set(work_types)
    direct = [item for item in work_objects if item["owner_role"] == role and item["work_object_type"] in allowed_types]
    typed = [item for item in work_objects if item["work_object_type"] in allowed_types]
    merged = {item["work_object_id"]: item for item in direct + typed}
    return sorted(merged.values(), key=_sort_key)


def _persona_item(item: dict[str, object]) -> dict[str, object]:
    graph = item["workflow_graph"]
    return {
        "work_object_id": item["work_object_id"],
        "title": item["title"],
        "work_object_type": item["work_object_type"],
        "primary_object": _primary_object(item["work_object_type"]),
        "financial_impact": item["financial_impact"],
        "priority": item["priority"],
        "owner": item["owner_name"] or item["owner_role"],
        "status": item["status"],
        "current_state": graph["current_state"],
        "next_state": graph["next_state"],
        "dependency": graph["dependency"],
        "blocker": graph["blocker"],
        "days_in_state": graph["days_in_state"],
        "deadline_days_remaining": graph["deadline_days_remaining"],
        "expected_recovery": graph["expected_recovery"],
    }


def _persona_metrics(items: list[dict[str, object]], *, recovery_center: dict[str, object], role: str) -> dict[str, object]:
    if role == "vp_revenue_cycle":
        return {
            "revenue_at_risk": recovery_center.get("metrics", {}).get("revenue_at_risk", "0.00"),
            "open_work": len(items),
            "blocked_work": len(_blocked_items(items)),
        }
    return {
        "open_work": len(items),
        "urgent_work": len([item for item in items if item["priority"] == "urgent"]),
        "blocked_work": len(_blocked_items(items)),
        "financial_impact": _money(sum((_decimal(item["financial_impact"]) for item in items), Decimal("0.00"))),
    }


def _recommended_actions(items: list[dict[str, object]]) -> list[dict[str, object]]:
    actions = []
    for item in _priority_items(items)[:6]:
        recommendation = item["recommendations"][0]
        graph = item["workflow_graph"]
        actions.append(
            {
                "work_object_id": item["work_object_id"],
                "action": recommendation["suggested_action"],
                "why": recommendation["summary"],
                "current_state": graph["current_state"],
                "next_state": graph["next_state"],
                "dependency": graph["dependency"],
            }
        )
    return actions


def _priority_items(items: list[dict[str, object]]) -> list[dict[str, object]]:
    return sorted(items, key=_sort_key)


def _blocked_items(items: list[dict[str, object]]) -> list[dict[str, object]]:
    return [item for item in items if item["workflow_status"] == "blocked" or item["workflow_graph"]["blocker"] not in {"", "None"}]


def _sort_key(item: dict[str, object]) -> tuple[int, Decimal]:
    priority = {"urgent": 0, "high": 1, "normal": 2, "low": 3}.get(str(item["priority"]), 4)
    return (priority, -_decimal(item["financial_impact"]))


def _primary_object(work_type: str) -> str:
    if work_type in {"Coding Review", "Charge Capture"}:
        return "Encounter"
    if work_type in {"Medical Necessity Denial", "Missing Documentation", "Appeal"}:
        return "Denial"
    if work_type in {"AR Follow-Up", "Underpayment"}:
        return "Account"
    if work_type == "Authorization":
        return "Scheduled Procedure"
    return "Work Object"


def _decimal(value: object) -> Decimal:
    if value in (None, ""):
        return Decimal("0.00")
    return Decimal(str(value))


def _money(value: Decimal) -> str:
    return f"{value:.2f}"
