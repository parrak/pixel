from __future__ import annotations

from clinical_ri_lite.detectors.common import lab_values, note_evidence
from clinical_ri_lite.models import EvidenceItem, NormalizedChart, Opportunity


def detect(chart: NormalizedChart) -> list[Opportunity]:
    if chart.coded_contains(["acute kidney injury", " aki"]):
        return []

    creatinines = lab_values(chart, "creatinine")
    if len(creatinines) < 2:
        return []

    lowest = min(creatinines, key=lambda fact: float(fact.value))
    highest = max(creatinines, key=lambda fact: float(fact.value))
    delta = float(highest.value) - float(lowest.value)
    ratio = float(highest.value) / max(float(lowest.value), 0.1)
    if delta < 0.3 and ratio < 1.5:
        return []

    evidence = [
        EvidenceItem("lowest observed creatinine", lowest.citation, f"{lowest.value} {lowest.unit}".strip()),
        EvidenceItem("subsequent creatinine rise", highest.citation, f"{highest.value} {highest.unit}".strip()),
    ]
    context = note_evidence(chart, "renal risk or treatment context", ["iv fluids", "nephrotoxin", "oliguria", "renal"])
    if context:
        evidence.append(context)

    return [
        Opportunity(
            chart_id=chart.chart_id,
            opportunity_id=f"{chart.chart_id}-aki",
            diagnosis_family="AKI",
            title="Opportunity for reviewer validation: acute kidney injury documentation",
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

