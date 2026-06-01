from __future__ import annotations

from smarterdx_lite.detectors.common import lab_values, medication_evidence, note_evidence, vital_values
from smarterdx_lite.models import EvidenceItem, NormalizedChart, Opportunity


ANTIBIOTICS = ["ceftriaxone", "vancomycin", "piperacillin", "zosyn", "cefepime", "azithromycin"]


def detect(chart: NormalizedChart) -> list[Opportunity]:
    if chart.coded_contains(["sepsis", "severe sepsis", "septic shock"]):
        return []

    infection = note_evidence(chart, "infection concern documented", ["pneumonia", "uti", "bacteremia", "infected", "purulent"])
    antibiotic = medication_evidence(chart, ANTIBIOTICS)
    if not infection or not antibiotic:
        return []

    evidence = [infection, antibiotic]
    dysfunction = []

    lactates = [fact for fact in lab_values(chart, "lactate") if float(fact.value) >= 2.0]
    if lactates:
        fact = max(lactates, key=lambda item: float(item.value))
        dysfunction.append(EvidenceItem("elevated lactate", fact.citation, f"{fact.value} {fact.unit}".strip()))

    sbps = [fact for fact in vital_values(chart, "sbp") if float(fact.value) < 90]
    if sbps:
        dysfunction.append(EvidenceItem("hypotension", sbps[0].citation, str(sbps[0].value)))

    wbcs = [fact for fact in lab_values(chart, "wbc") if float(fact.value) >= 12 or float(fact.value) < 4]
    if wbcs:
        dysfunction.append(EvidenceItem("abnormal white blood cell count", wbcs[0].citation, f"{wbcs[0].value} {wbcs[0].unit}".strip()))

    temps = [fact for fact in vital_values(chart, "temperature_f") if float(fact.value) >= 100.4 or float(fact.value) < 96.8]
    if temps:
        dysfunction.append(EvidenceItem("abnormal temperature", temps[0].citation, str(temps[0].value)))

    if len(dysfunction) < 2:
        return []

    evidence.extend(dysfunction)
    title = "Opportunity for reviewer validation: sepsis or severe sepsis documentation"
    if any(item.criterion in {"elevated lactate", "hypotension"} for item in dysfunction):
        title = "Opportunity for reviewer validation: sepsis or severe sepsis documentation"

    return [
        Opportunity(
            chart_id=chart.chart_id,
            opportunity_id=f"{chart.chart_id}-sepsis",
            diagnosis_family="sepsis",
            title=title,
            summary="Infection treatment plus physiologic abnormalities suggest a reviewer should validate whether sepsis-related documentation is supported.",
            rank_score=82 + min(len(dysfunction) * 4, 16),
            evidence=evidence,
            missing_or_weak_documentation="Final coded diagnoses do not include sepsis or severe sepsis.",
            query=(
                "Based on the documented infection concern, antimicrobial treatment, and physiologic findings, "
                "can the infectious condition and any related organ dysfunction be further clarified, if clinically appropriate?"
            ),
            audit_trace=[
                "Sepsis detector requires infection evidence, antibiotic evidence, and at least two physiologic abnormalities.",
                f"Physiologic abnormality count: {len(dysfunction)}.",
            ],
        )
    ]

