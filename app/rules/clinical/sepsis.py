from __future__ import annotations

from app.core.evidence_graph import lab_values, medication_evidence, note_evidence, vital_values
from app.core.evidence_graph import EvidenceGraph
from app.core.models import Opportunity


ANTIBIOTICS = ["ceftriaxone", "vancomycin", "piperacillin", "zosyn", "cefepime", "azithromycin"]


def detect(graph: EvidenceGraph) -> list[Opportunity]:
    if graph.coded_contains(["sepsis", "severe sepsis", "septic shock"]):
        return []

    infection = note_evidence(graph, "infection concern documented", ["pneumonia", "uti", "bacteremia", "infected", "purulent"])
    antibiotic = medication_evidence(graph, ANTIBIOTICS)
    if not infection or not antibiotic:
        return []

    evidence = [infection, antibiotic]
    dysfunction = []

    lactates = [entity for entity in lab_values(graph, "lactate") if float(entity.payload["value"]) >= 2.0]
    if lactates:
        entity = max(lactates, key=lambda item: float(item.payload["value"]))
        dysfunction.append(graph.make_item("elevated lactate", entity, f"{entity.payload['value']} {entity.payload.get('unit', '')}".strip()))

    sbps = [entity for entity in vital_values(graph, "sbp") if float(entity.payload["value"]) < 90]
    if sbps:
        dysfunction.append(graph.make_item("hypotension", sbps[0], str(sbps[0].payload["value"])))

    wbcs = [entity for entity in lab_values(graph, "wbc") if float(entity.payload["value"]) >= 12 or float(entity.payload["value"]) < 4]
    if wbcs:
        dysfunction.append(graph.make_item("abnormal white blood cell count", wbcs[0], f"{wbcs[0].payload['value']} {wbcs[0].payload.get('unit', '')}".strip()))

    temps = [entity for entity in vital_values(graph, "temperature_f") if float(entity.payload["value"]) >= 100.4 or float(entity.payload["value"]) < 96.8]
    if temps:
        dysfunction.append(graph.make_item("abnormal temperature", temps[0], str(temps[0].payload["value"])))

    if len(dysfunction) < 2:
        return []

    evidence.extend(dysfunction)
    evidence = graph.cluster("sepsis-infection-physiology", evidence)
    title = "Possible opportunity for reviewer validation: sepsis or severe sepsis documentation"
    if any(item.criterion in {"elevated lactate", "hypotension"} for item in dysfunction):
        title = "Possible opportunity for reviewer validation: sepsis or severe sepsis documentation"

    return [
        Opportunity(
            chart_id=graph.chart_id,
            opportunity_id=f"{graph.chart_id}-sepsis",
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
