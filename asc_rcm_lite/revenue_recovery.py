"""Revenue recovery operating layer built on workflow-native work objects."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from asc_rcm_lite.models import ValidationError, require_non_empty
from asc_rcm_lite.work_objects import WorkObject


PAYERS = ("United", "Aetna", "Humana", "Cigna", "BCBS", "Regional Plans")
DENIAL_TYPES = ("Missing Documentation", "Medical Necessity", "Authorization Denial", "Coding Denial", "Timely Filing", "Eligibility", "COB")
FACILITIES = ("ASC Alpha Surgical Center", "ASC Bravo Specialty Pavilion", "ASC Charlie Outpatient Center", "ASC Delta Surgery Center")
SPECIALISTS = ("Jasmine Brooks", "Daniel Ortiz", "Nina Patel", "Maya Foster", "Rafael Kim", "Grace Lin")
MANAGERS = ("Morgan Lee", "Alicia Monroe", "Sonia Clarke")


@dataclass(frozen=True)
class RecoveryClaim:
    claim_id: str
    facility: str
    payer: str
    denial_type: str | None
    billed_amount: Decimal
    revenue_at_risk: Decimal
    expected_recovery: Decimal
    status: str
    owner: str
    deadline_days: int
    recovery_likelihood: Decimal
    evidence_ready: bool
    appeal_ready: bool
    blocked: bool
    recovered_amount: Decimal
    age_days: int

    def __post_init__(self) -> None:
        require_non_empty(self.claim_id, "RecoveryClaim.claim_id")
        require_non_empty(self.facility, "RecoveryClaim.facility")
        require_non_empty(self.payer, "RecoveryClaim.payer")
        require_non_empty(self.status, "RecoveryClaim.status")
        require_non_empty(self.owner, "RecoveryClaim.owner")


def build_revenue_recovery_center(work_objects: tuple[WorkObject, ...]) -> dict[str, object]:
    claims = build_recovery_dataset(work_objects)
    denials = [claim for claim in claims if claim.denial_type is not None]
    appeals = [claim for claim in denials if claim.appeal_ready]
    blocked = [claim for claim in claims if claim.blocked]
    near_deadline = [claim for claim in claims if claim.deadline_days <= 7 and claim.status != "recovered"]
    recovered = [claim for claim in claims if claim.status == "recovered"]
    revenue_at_risk = sum((claim.revenue_at_risk for claim in claims if claim.status != "recovered"), Decimal("0.00"))
    recoverable = sum((claim.expected_recovery for claim in claims if claim.status != "recovered"), Decimal("0.00"))
    recovered_month = sum((claim.recovered_amount for claim in recovered), Decimal("0.00"))
    expected_recovery = sum((claim.expected_recovery for claim in near_deadline + appeals), Decimal("0.00"))
    recovery_rate = (recovered_month / (recovered_month + revenue_at_risk) * Decimal("100")) if recovered_month + revenue_at_risk else Decimal("0.00")
    velocity = Decimal(str(len(recovered))) / Decimal("30")
    return {
        "metrics": {
            "revenue_at_risk": _money(revenue_at_risk),
            "recoverable_revenue": _money(recoverable),
            "appeals_in_progress": len(appeals),
            "claims_near_deadline": len(near_deadline),
            "claims_recovered": len(recovered),
            "recovery_rate": _pct(recovery_rate),
            "recovery_velocity": f"{velocity:.1f} claims/day",
            "expected_recovery": _money(expected_recovery),
            "recovered_this_month": _money(recovered_month),
        },
        "work_today": [_claim_row(claim) for claim in sorted(claims, key=lambda item: (item.deadline_days, -item.expected_recovery))[:12]],
        "escalate": [_claim_row(claim) for claim in sorted(near_deadline + blocked, key=lambda item: (item.deadline_days, -item.revenue_at_risk))[:10]],
        "blocked": [_claim_row(claim) for claim in blocked[:10]],
        "money_trapped": [_claim_row(claim) for claim in sorted(claims, key=lambda item: item.revenue_at_risk, reverse=True)[:10]],
        "dataset_summary": {
            "claims": len(claims),
            "denials": len(denials),
            "appeals": len(appeals),
            "facilities": len(set(claim.facility for claim in claims)),
            "payers": len(set(claim.payer for claim in claims)),
            "specialists": len(set(claim.owner for claim in claims if claim.owner in SPECIALISTS)),
            "managers": len(MANAGERS),
        },
    }


def build_denial_recovery_factory(work_objects: tuple[WorkObject, ...]) -> dict[str, object]:
    claims = [claim for claim in build_recovery_dataset(work_objects) if claim.denial_type is not None]
    factory = []
    for claim in claims[:120]:
        factory.append(
            {
                "denial_id": f"DEN-{claim.claim_id}",
                "denial_type": claim.denial_type,
                "financial_impact": _money(claim.revenue_at_risk),
                "payer": claim.payer,
                "claim": claim.claim_id,
                "timeline": _recovery_timeline(claim),
                "evidence": _evidence_bundle(claim),
                "required_documents": _required_documents(claim.denial_type or "Missing Documentation"),
                "appeal_history": _appeal_history(claim),
                "recommendations": _recovery_recommendations(claim),
                "recovery_likelihood": _pct(claim.recovery_likelihood * Decimal("100")),
                "deadline": f"{claim.deadline_days} days",
                "owner": claim.owner,
                "status": claim.status,
                "outcome": _outcome(claim),
            }
        )
    return {
        "denials": factory,
        "supported_types": list(DENIAL_TYPES),
    }


def build_appeal_workspace(work_objects: tuple[WorkObject, ...]) -> dict[str, object]:
    denials = build_denial_recovery_factory(work_objects)["denials"]
    appeals = []
    for denial in denials[:60]:
        appeals.append(
            {
                "appeal_id": denial["denial_id"].replace("DEN-", "APP-"),
                "denial": denial,
                "payer_rationale": f"{denial['payer']} denied for {denial['denial_type'].lower()} requirements.",
                "similar_recoveries": _similar_recoveries(denial["payer"], denial["denial_type"]),
                "supporting_evidence": denial["evidence"],
                "appeal_package": {
                    "status": "ready",
                    "artifacts": [
                        "Appeal Packet",
                        "Cover Letter",
                        "Evidence Summary",
                        "Submission Checklist",
                    ],
                },
                "submission_status": "ready_to_submit" if denial["status"] != "recovered" else "resolved",
                "outcome": denial["outcome"],
            }
        )
    return {"appeals": appeals}


def build_evidence_engine(work_objects: tuple[WorkObject, ...]) -> dict[str, object]:
    claims = build_recovery_dataset(work_objects)
    return {
        "evidence_packets": [
            {
                "claim_id": claim.claim_id,
                "payer": claim.payer,
                "denial_type": claim.denial_type or "AR Follow-Up",
                "organized_evidence": _evidence_bundle(claim),
                "packet_readiness": "ready" if claim.evidence_ready else "needs_operator_review",
            }
            for claim in claims[:80]
        ],
        "evidence_types": [
            "Operative Note",
            "Medical Necessity Documentation",
            "Clinical Documentation",
            "Authorization History",
            "Payer Rules",
            "Payer Policies",
            "Supporting Records",
            "Claim History",
            "Timeline",
        ],
    }


def build_recovery_copilot_outputs(work_objects: tuple[WorkObject, ...]) -> dict[str, object]:
    claims = build_recovery_dataset(work_objects)
    return {
        "outputs": [
            {
                "claim_id": claim.claim_id,
                "payer": claim.payer,
                "work_product": [
                    "Appeal Packet",
                    "Cover Letter",
                    "Clinical Summary" if claim.denial_type == "Medical Necessity" else "Evidence Summary",
                    "Submission Checklist",
                    "Payer Brief",
                    "Manager Brief" if claim.blocked else "Escalation Package",
                ],
                "ready_for_workflow": True,
            }
            for claim in claims[:40]
        ]
    }


def build_similar_recovery_intelligence(work_objects: tuple[WorkObject, ...]) -> dict[str, object]:
    claims = build_recovery_dataset(work_objects)
    by_type = {}
    for claim in claims:
        key = claim.denial_type or "AR Follow-Up"
        by_type.setdefault(key, []).append(claim)
    return {
        "patterns": [
            {
                "recovery_type": key,
                "similar_cases": len(items),
                "successful_appeals": sum(1 for item in items if item.status == "recovered"),
                "failed_appeals": sum(1 for item in items if item.status == "written_off"),
                "winning_evidence": _required_documents(key)[:3],
                "recovery_rate": _pct(_rate(items)),
                "average_recovery_time": f"{round(sum(item.age_days for item in items) / max(len(items), 1), 1)} days",
                "expected_recovery": _money(sum((item.expected_recovery for item in items), Decimal("0.00"))),
            }
            for key, items in sorted(by_type.items())
        ]
    }


def build_payer_playbooks(work_objects: tuple[WorkObject, ...]) -> dict[str, object]:
    claims = build_recovery_dataset(work_objects)
    playbooks = []
    for payer in PAYERS:
        payer_claims = [claim for claim in claims if claim.payer == payer]
        playbooks.append(
            {
                "payer": payer,
                "common_denials": _top_counts([claim.denial_type or "AR Follow-Up" for claim in payer_claims])[:4],
                "appeal_success_rate": _pct(_rate(payer_claims)),
                "winning_documentation": ["Payer Policy", "Claim Timeline", "Clinical Documentation", "Authorization History"],
                "typical_recovery_time": f"{round(sum(claim.age_days for claim in payer_claims) / max(len(payer_claims), 1), 1)} days",
                "escalation_paths": [f"{payer} portal escalation", f"{payer} provider relations", "manager review"],
                "common_mistakes": ["Submitting without payer rule citation", "Missing claim timeline", "No proof of prior follow-up"],
                "required_evidence": ["Claim History", "Payer Rules", "Supporting Documentation", "Prior Outcomes"],
            }
        )
    return {"playbooks": playbooks}


def build_manager_recovery_operations(work_objects: tuple[WorkObject, ...]) -> dict[str, object]:
    claims = build_recovery_dataset(work_objects)
    high_value = sorted([claim for claim in claims if claim.status != "recovered"], key=lambda item: item.expected_recovery, reverse=True)[:12]
    blocked = [claim for claim in claims if claim.blocked][:12]
    return {
        "prioritize_revenue": [_claim_row(claim) for claim in high_value],
        "reassign_work": [
            {"claim_id": claim.claim_id, "from": claim.owner, "to": SPECIALISTS[index % len(SPECIALISTS)], "expected_impact": _money(claim.expected_recovery)}
            for index, claim in enumerate(high_value[:8])
        ],
        "escalate_cases": [_claim_row(claim) for claim in blocked],
        "monitor_deadlines": [_claim_row(claim) for claim in sorted(claims, key=lambda item: item.deadline_days)[:12]],
        "identify_blockers": [_claim_row(claim) for claim in blocked],
        "allocate_capacity": [
            {"owner": owner, "assigned_claims": sum(1 for claim in claims if claim.owner == owner), "capacity_action": "rebalance" if index < 3 else "stable"}
            for index, owner in enumerate(SPECIALISTS)
        ],
        "track_recovery_progress": build_revenue_recovery_center(work_objects)["metrics"],
    }


def build_recovery_outcome_tracking(work_objects: tuple[WorkObject, ...]) -> dict[str, object]:
    claims = build_recovery_dataset(work_objects)
    recovered = [claim for claim in claims if claim.status == "recovered"]
    return {
        "recoveries": [
            {
                "claim_id": claim.claim_id,
                "recovery_amount": _money(claim.recovered_amount),
                "recovered_revenue": _money(claim.recovered_amount),
                "appeal_win_rate": _pct(claim.recovery_likelihood * Decimal("100")),
                "time_to_resolution": f"{claim.age_days} days",
                "evidence_used": _required_documents(claim.denial_type or "AR Follow-Up")[:3],
                "operator": claim.owner,
                "payer": claim.payer,
                "facility": claim.facility,
                "denial_type": claim.denial_type or "AR Follow-Up",
            }
            for claim in recovered[:80]
        ],
        "rollup": {
            "recovered_revenue": _money(sum((claim.recovered_amount for claim in recovered), Decimal("0.00"))),
            "recovery_count": len(recovered),
        },
    }


def build_nimble_evaluation_scenario(work_objects: tuple[WorkObject, ...]) -> dict[str, object]:
    claims = build_recovery_dataset(work_objects)
    denials = [claim for claim in claims if claim.denial_type is not None][:100]
    revenue_at_risk = Decimal("2500000.00")
    ready_appeals = [claim for claim in denials if claim.appeal_ready]
    missing_evidence = [claim for claim in denials if not claim.evidence_ready]
    likely_recovery = sum((claim.expected_recovery for claim in ready_appeals[:30]), Decimal("0.00"))
    recovered = likely_recovery * Decimal("0.42")
    return {
        "scenario": "100 denials. $2.5M revenue at risk. A denial manager logs in Monday morning.",
        "denials": len(denials),
        "revenue_at_risk": _money(revenue_at_risk),
        "where_money_is_trapped": [_claim_row(claim) for claim in sorted(denials, key=lambda item: item.revenue_at_risk, reverse=True)[:8]],
        "work_first": [_claim_row(claim) for claim in sorted(denials, key=lambda item: (item.deadline_days, -item.expected_recovery))[:8]],
        "missing_evidence": [_claim_row(claim) for claim in missing_evidence[:8]],
        "appeals_ready": [_claim_row(claim) for claim in ready_appeals[:8]],
        "likely_recovery": _money(likely_recovery),
        "actions_maximizing_collections": [
            "Submit ready appeals before deadline.",
            "Escalate blocked high-dollar denials.",
            "Reassign under-capacity specialists to missing evidence work.",
            "Use payer playbooks to avoid repeat submission mistakes.",
        ],
        "walkthrough_outcome": {
            "recovered_revenue": _money(recovered),
            "operational_learning": "Manager actions, evidence choices, and outcomes are written to decision memory.",
            "updated_payer_intelligence": "Appeal success, evidence effectiveness, and response-time patterns update by payer.",
            "updated_decision_memory": "Similar recoveries become available for the next denial.",
        },
    }


def build_recovery_dataset(work_objects: tuple[WorkObject, ...], *, size: int = 520) -> tuple[RecoveryClaim, ...]:
    seed_claims = [_claim_from_work_object(item, index) for index, item in enumerate(work_objects)]
    claims = list(seed_claims)
    while len(claims) < size:
        index = len(claims)
        payer = PAYERS[index % len(PAYERS)]
        facility = FACILITIES[index % len(FACILITIES)]
        denial_type = DENIAL_TYPES[index % len(DENIAL_TYPES)] if index < 140 or index % 3 == 0 else None
        billed = Decimal(2800 + (index % 37) * 460)
        risk_multiplier = Decimal("0.82") if denial_type else Decimal("0.64")
        revenue_at_risk = (billed * risk_multiplier).quantize(Decimal("0.01"))
        likelihood = Decimal("0.74") - Decimal(str((index % 9) * 0.03))
        expected = (revenue_at_risk * likelihood).quantize(Decimal("0.01"))
        status = "recovered" if index % 5 == 0 else ("blocked" if index % 11 == 0 else ("appeal_in_progress" if denial_type else "follow_up"))
        recovered = expected if status == "recovered" else Decimal("0.00")
        claims.append(
            RecoveryClaim(
                claim_id=f"RR-CLM-{index + 1:04d}",
                facility=facility,
                payer=payer,
                denial_type=denial_type,
                billed_amount=billed,
                revenue_at_risk=revenue_at_risk,
                expected_recovery=expected,
                status=status,
                owner=SPECIALISTS[index % len(SPECIALISTS)],
                deadline_days=(index % 31) + 1,
                recovery_likelihood=likelihood,
                evidence_ready=index % 4 != 0,
                appeal_ready=denial_type is not None and index % 3 != 0,
                blocked=status == "blocked" or index % 17 == 0,
                recovered_amount=recovered,
                age_days=35 + (index % 115),
            )
        )
    return tuple(claims)


def _claim_from_work_object(item: WorkObject, index: int) -> RecoveryClaim:
    denial_type = item.work_object_type if item.work_object_type in DENIAL_TYPES else ("Authorization Denial" if item.work_object_type == "Authorization" else None)
    risk = item.financial_impact or Decimal("2500.00")
    status = "recovered" if item.status == "Completed" else ("blocked" if item.workflow_status == "blocked" else "appeal_in_progress" if denial_type else "follow_up")
    likelihood = Decimal(item.recommendations[0].get("recovery_probability", "0.68"))
    expected = (risk * likelihood).quantize(Decimal("0.01"))
    return RecoveryClaim(
        claim_id=item.claim_id or f"RR-SEED-{index + 1:04d}",
        facility=item.facility_name,
        payer=_payer_from_account(item.account_id),
        denial_type=denial_type,
        billed_amount=risk * Decimal("1.35"),
        revenue_at_risk=risk,
        expected_recovery=expected,
        status=status,
        owner=item.owner_name or item.owner_role,
        deadline_days=(index % 20) + 2,
        recovery_likelihood=likelihood,
        evidence_ready=True,
        appeal_ready=denial_type is not None,
        blocked=item.workflow_status == "blocked",
        recovered_amount=Decimal(item.outcome.get("financial_result") or "0.00"),
        age_days=42 + index,
    )


def _claim_row(claim: RecoveryClaim) -> dict[str, object]:
    return {
        "claim_id": claim.claim_id,
        "facility": claim.facility,
        "payer": claim.payer,
        "denial_type": claim.denial_type,
        "revenue_at_risk": _money(claim.revenue_at_risk),
        "expected_recovery": _money(claim.expected_recovery),
        "status": claim.status,
        "owner": claim.owner,
        "deadline_days": claim.deadline_days,
        "blocked": claim.blocked,
    }


def _recovery_timeline(claim: RecoveryClaim) -> list[dict[str, object]]:
    return [
        {"stage": "Claim Submitted", "status": "complete", "detail": f"{claim.claim_id} submitted to {claim.payer}."},
        {"stage": "Denial Received", "status": "complete" if claim.denial_type else "not_applicable", "detail": claim.denial_type or "No denial."},
        {"stage": "Evidence Assembled", "status": "complete" if claim.evidence_ready else "needs_work", "detail": "Evidence engine assembled required documentation."},
        {"stage": "Appeal Ready", "status": "complete" if claim.appeal_ready else "needs_work", "detail": "Appeal package generated."},
        {"stage": "Resolution", "status": "complete" if claim.status == "recovered" else "open", "detail": _outcome(claim)["summary"]},
    ]


def _evidence_bundle(claim: RecoveryClaim) -> list[dict[str, object]]:
    return [
        {"type": "Claim History", "status": "assembled", "detail": f"Billed ${claim.billed_amount:.2f}; risk ${claim.revenue_at_risk:.2f}."},
        {"type": "Payer Policies", "status": "assembled", "detail": f"{claim.payer} requirements for {claim.denial_type or 'AR follow-up'}."},
        {"type": "Timeline", "status": "assembled", "detail": f"{claim.age_days} days since service/submission."},
        {"type": "Supporting Records", "status": "ready" if claim.evidence_ready else "missing", "detail": "Operative note, authorization history, and documentation checklist."},
    ]


def _required_documents(denial_type: str) -> list[str]:
    defaults = ["Claim Timeline", "Payer Policy", "Evidence Summary", "Submission Checklist"]
    by_type = {
        "Missing Documentation": ["Operative Note", "Documentation Checklist", "Claim Timeline", "Cover Letter"],
        "Medical Necessity": ["Clinical Documentation", "Medical Necessity Summary", "Payer Policy", "Cover Letter"],
        "Authorization Denial": ["Authorization History", "Scheduling Notes", "Payer Policy", "Cover Letter"],
        "Coding Denial": ["Coding Review", "Charge Detail", "Payer Policy", "Corrected Claim Summary"],
        "Timely Filing": ["Submission Proof", "Clearinghouse Acceptance", "Payer Policy", "Cover Letter"],
        "Eligibility": ["Eligibility Snapshot", "Coverage History", "Payer Policy", "COB Summary"],
        "COB": ["COB Investigation", "Primary Payer Evidence", "Patient Account Notes", "Payer Policy"],
    }
    return by_type.get(denial_type, defaults)


def _appeal_history(claim: RecoveryClaim) -> list[dict[str, object]]:
    return [
        {"attempt": "initial", "status": "submitted" if claim.appeal_ready else "draft", "result": "pending" if claim.status != "recovered" else "won"},
        {"attempt": "similar_case", "status": "reference", "result": "won with complete documentation"},
    ]


def _recovery_recommendations(claim: RecoveryClaim) -> list[dict[str, object]]:
    return [
        {
            "title": "Work highest expected recovery before deadline",
            "action": "Submit appeal package" if claim.appeal_ready else "Complete missing evidence",
            "recovery_likelihood": _pct(claim.recovery_likelihood * Decimal("100")),
            "expected_recovery": _money(claim.expected_recovery),
        }
    ]


def _similar_recoveries(payer: str, denial_type: str) -> list[dict[str, object]]:
    return [
        {"payer": payer, "denial_type": denial_type, "result": "won", "winning_evidence": _required_documents(denial_type)[:2], "time_to_recovery": "24 days"},
        {"payer": payer, "denial_type": denial_type, "result": "won", "winning_evidence": _required_documents(denial_type)[1:3], "time_to_recovery": "31 days"},
    ]


def _outcome(claim: RecoveryClaim) -> dict[str, object]:
    if claim.status == "recovered":
        return {"status": "recovered", "amount": _money(claim.recovered_amount), "summary": "Payment recovered and memory updated."}
    if claim.blocked:
        return {"status": "blocked", "amount": "0.00", "summary": "Manager escalation required to unlock recovery."}
    return {"status": "open", "amount": "0.00", "summary": "Recovery workflow in progress."}


def _top_counts(values: list[str]) -> list[dict[str, object]]:
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return [{"label": key, "count": count} for key, count in sorted(counts.items(), key=lambda item: item[1], reverse=True)]


def _rate(claims: list[RecoveryClaim]) -> Decimal:
    if not claims:
        return Decimal("0.00")
    return (Decimal(sum(1 for claim in claims if claim.status == "recovered")) / Decimal(len(claims)) * Decimal("100")).quantize(Decimal("0.01"))


def _payer_from_account(account_id: str) -> str:
    return account_id.split("-")[-1]


def _money(value: Decimal) -> str:
    return f"{value:.2f}"


def _pct(value: Decimal) -> str:
    return f"{value:.1f}%"
