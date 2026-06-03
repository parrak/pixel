from decimal import Decimal

from asc_rcm_lite.detectors.ar import ARFlag
from asc_rcm_lite.workqueue import build_work_queue, filter_work_queue, manager_summary


def _flag(flag_id: str, *, payer: str, owner_role: str, aging_bucket: str, opportunity_type: str, score: int):
    return ARFlag(
        flag_id=flag_id,
        claim_id=f"CLM-{flag_id}",
        case_id=f"CASE-{flag_id}",
        payer=payer,
        flag_type=opportunity_type,
        days_in_ar=120 if aging_bucket == "120_plus" else 30,
        balance=Decimal("1000.00"),
        aging_bucket=aging_bucket,
        last_touch_date=None,
        next_deadline="2026-02-10",
        reason_for_flag="Synthetic queue item for human review.",
        recommended_next_action="Review and route for human review.",
        owner_role=owner_role,
        evidence_citation_ids=(f"SRC-{flag_id}",),
        priority_score=score,
        priority_band="urgent" if score >= 85 else "high",
        human_review_required=True,
    )


def test_work_queue_filters_work():
    queue = build_work_queue(
        (
            _flag("1", payer="PAYER-A", owner_role="biller", aging_bucket="120_plus", opportunity_type="high_dollar_ar", score=90),
            _flag("2", payer="PAYER-B", owner_role="denial_specialist", aging_bucket="60", opportunity_type="appeal_deadline_risk", score=88),
        )
    )

    assert len(filter_work_queue(queue, payer="PAYER-A")) == 1
    assert len(filter_work_queue(queue, owner_role="denial_specialist")) == 1
    assert len(filter_work_queue(queue, aging_bucket="120_plus")) == 1
    assert len(filter_work_queue(queue, opportunity_type="appeal_deadline_risk")) == 1


def test_work_queue_sort_is_deterministic():
    queue = build_work_queue(
        (
            _flag("b", payer="PAYER-A", owner_role="biller", aging_bucket="60", opportunity_type="ar_60", score=70),
            _flag("a", payer="PAYER-A", owner_role="biller", aging_bucket="60", opportunity_type="ar_60", score=70),
            _flag("c", payer="PAYER-A", owner_role="biller", aging_bucket="120_plus", opportunity_type="high_dollar_ar", score=90),
        )
    )

    assert [item.work_item_id for item in queue] == ["c", "a", "b"]


def test_manager_summary_metrics_are_computed():
    queue = build_work_queue(
        (
            _flag("1", payer="PAYER-A", owner_role="biller", aging_bucket="120_plus", opportunity_type="high_dollar_ar", score=90),
            _flag("2", payer="PAYER-B", owner_role="denial_specialist", aging_bucket="60", opportunity_type="appeal_deadline_risk", score=88),
        )
    )

    summary = manager_summary(queue)
    assert summary["total_items"] == 2
    assert summary["urgent_items"] == 2
