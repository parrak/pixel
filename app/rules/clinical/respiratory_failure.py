from __future__ import annotations

from app.core.evidence_graph import note_evidence, vital_values
from app.core.models import EvidenceItem, NormalizedChart, Opportunity


def detect(chart: NormalizedChart) -> list[Opportunity]:
    if chart.coded_contains(["acute respiratory failure", "respiratory failure"]):
        return []

    oxygen_evidence = []
    for fact in chart.facts:
        if fact.kind != "oxygen":
            continue
        payload = fact.value
        device = str(payload.get("device", "")).lower()
        flow = float(payload.get("flow_lpm", 0) or 0)
        fio2 = float(payload.get("fio2", 0) or 0)
        if device in {"hfnc", "bipap", "ventilator"} or flow >= 4 or fio2 >= 0.4:
            oxygen_evidence.append(EvidenceItem("escalated oxygen support", fact.citation, fact.citation.label))

    low_spo2 = [fact for fact in vital_values(chart, "spo2") if float(fact.value) < 90]
    distress = note_evidence(chart, "respiratory distress documented", ["respiratory distress", "accessory muscle", "tachypnea", "hypoxemia"])

    if not oxygen_evidence or not (low_spo2 or distress):
        return []

    evidence = oxygen_evidence[:1]
    if low_spo2:
        evidence.append(EvidenceItem("oxygen saturation below 90%", low_spo2[0].citation, str(low_spo2[0].value)))
    if distress:
        evidence.append(distress)

    return [
        Opportunity(
            chart_id=chart.chart_id,
            opportunity_id=f"{chart.chart_id}-arf",
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
