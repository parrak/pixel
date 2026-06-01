from __future__ import annotations

from app.core.evidence_graph import lab_values, note_evidence
from app.core.evidence_graph import EvidenceGraph
from app.core.models import Opportunity


def detect(graph: EvidenceGraph) -> list[Opportunity]:
    if graph.coded_contains(["acute kidney injury", " aki"]):
        return []

    creatinines = lab_values(graph, "creatinine")
    if len(creatinines) < 2:
        return []

    lowest = min(creatinines, key=lambda entity: float(entity.payload["value"]))
    highest = max(creatinines, key=lambda entity: float(entity.payload["value"]))
    delta = float(highest.payload["value"]) - float(lowest.payload["value"])
    ratio = float(highest.payload["value"]) / max(float(lowest.payload["value"]), 0.1)
    if delta < 0.3 and ratio < 1.5:
        return []

    evidence = [
        graph.make_item("lowest observed creatinine", lowest, f"{lowest.payload['value']} {lowest.payload.get('unit', '')}".strip()),
        graph.make_item("subsequent creatinine rise", highest, f"{highest.payload['value']} {highest.payload.get('unit', '')}".strip()),
    ]
    context = note_evidence(graph, "renal risk or treatment context", ["iv fluids", "nephrotoxin", "oliguria", "renal"])
    if context:
        evidence.append(context)
    evidence = graph.cluster("aki-creatinine-trend", evidence)

    return [
        Opportunity(
            chart_id=graph.chart_id,
            opportunity_id=f"{graph.chart_id}-aki",
            diagnosis_family="AKI",
            title="Possible opportunity for reviewer validation: acute kidney injury documentation",
            summary="Creatinine trend suggests a reviewer should validate whether acute kidney injury documentation is supported.",
            rank_score=75 + min(int(delta * 10), 20),
            evidence=evidence,
            missing_or_weak_documentation="Final coded diagnoses do not include acute kidney injury.",
            query=(
                "Based on the documented creatinine trend and renal management, can the patient's renal status "
                "be further clarified in the medical record, if clinically appropriate?"
            ),
            audit_trace=[
                "AKI detector skipped charts already coded with AKI.",
                f"Creatinine delta {delta:.2f}; ratio {ratio:.2f}.",
            ],
        )
    ]
