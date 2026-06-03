"""Deterministic export helpers for demo artifacts."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from asc_rcm_lite.pipeline import PipelineResult
from asc_rcm_lite.reviewer.packet import ReviewerPacket


def export_work_queue_csv(path: str | Path, pipeline_result: PipelineResult) -> None:
    rows = []
    for case in pipeline_result.cases:
        for item in case.work_queue:
            rows.append(
                {
                    "work_item_id": item.work_item_id,
                    "case_id": item.case_id,
                    "claim_id": item.claim_id,
                    "payer": item.payer,
                    "queue_type": item.queue_type,
                    "owner_role": item.owner_role,
                    "priority_score": item.priority_score,
                    "priority_band": item.priority_band,
                }
            )
    with Path(path).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else ["work_item_id"])
        writer.writeheader()
        writer.writerows(rows)


def export_packet_markdown(path: str | Path, packet: ReviewerPacket) -> None:
    Path(path).write_text(
        "\n".join(
            [
                f"# Reviewer Packet {packet.packet_id}",
                f"Case: {packet.case_id}",
                f"Opportunity: {packet.opportunity_summary}",
                "Evidence:",
                *packet.evidence_table,
                "Human review is required before use.",
            ]
        ),
        encoding="utf-8",
    )


def export_json(path: str | Path, payload: dict[str, object]) -> None:
    Path(path).write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
