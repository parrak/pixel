from __future__ import annotations

from app.core.evidence_graph import note_evidence, vital_values
from app.core.evidence_graph import EvidenceGraph
from app.core.models import Opportunity


def detect(graph: EvidenceGraph) -> list[Opportunity]:
    if graph.coded_contains(["acute respiratory failure", "respiratory failure"]):
        return []

    oxygen_evidence = []
    for entity in graph.entities("oxygen"):
        payload = entity.payload
        device = str(payload.get("device", "")).lower()
        flow = float(payload.get("flow_lpm", 0) or 0)
        fio2 = float(payload.get("fio2", 0) or 0)
        if device in {"hfnc", "bipap", "ventilator"} or flow >= 4 or fio2 >= 0.4:
            oxygen_evidence.append(graph.make_item("escalated oxygen support", entity, entity.label))

    low_spo2 = [entity for entity in vital_values(graph, "spo2") if float(entity.payload["value"]) < 90]
    distress = note_evidence(graph, "respiratory distress documented", ["respiratory distress", "accessory muscle", "tachypnea", "hypoxemia"])

    if not oxygen_evidence or not (low_spo2 or distress):
        return []

    evidence = oxygen_evidence[:1]
    if low_spo2:
        evidence.append(graph.make_item("oxygen saturation below 90%", low_spo2[0], str(low_spo2[0].payload["value"])))
    if distress:
        evidence.append(distress)
    evidence = graph.cluster("respiratory-support-hypoxemia", evidence)

    return [
        Opportunity(
            chart_id=graph.chart_id,
            opportunity_id=f"{graph.chart_id}-arf",
            diagnosis_family="acute respiratory failure",
            title="Possible opportunity for reviewer validation: acute respiratory failure documentation",
            summary="Oxygen escalation with hypoxemia or respiratory distress suggests a reviewer should validate whether acute respiratory failure documentation is supported.",
            rank_score=80 + min(len(evidence) * 5, 15),
            evidence=evidence,
            missing_or_weak_documentation="Final coded diagnoses do not include acute respiratory failure.",
            query=(
                "Based on the documented oxygen support, oxygen saturation, and respiratory exam findings, "
                "can the patient's respiratory status be further clarified, if clinically appropriate?"
            ),
            audit_trace=[
                "Respiratory failure detector requires escalated oxygen support plus hypoxemia or respiratory distress.",
                f"Evidence item count: {len(evidence)}.",
            ],
        )
    ]
