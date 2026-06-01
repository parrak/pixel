import json
from pathlib import Path

from app.core.ingest import load_chart
from app.core.normalize import normalize_chart
from app.core.models import AuditTrace, EvidenceCluster, EvidenceItem, EvidenceLink
from app.workflows.prebill.detector import analyze_chart, analyze_evidence_graph


def test_encounter_graph_contains_required_entity_surfaces():
    chart = load_chart(Path("data/synthetic_charts/sdx001.json"))
    graph = chart.encounter_graph

    assert graph is not None
    assert {"note", "lab", "vital", "medication", "oxygen", "diagnosis"} <= {
        entity.entity_type for entity in graph.entities.values()
    }
    assert graph.by_type("note")
    assert graph.by_type("lab")
    assert graph.by_type("vital")
    assert graph.by_type("medication")
    assert graph.by_type("oxygen")
    assert graph.by_type("diagnosis")


def test_evidence_graph_is_json_serializable():
    chart = load_chart(Path("data/synthetic_charts/sdx001.json"))
    payload = chart.evidence_graph.to_json()

    rendered = json.dumps(payload, sort_keys=True)
    assert "encounter_graph" in payload
    assert "lab:l1" in rendered
    assert "note:n1" in rendered


def test_opportunities_are_backed_by_graph_evidence_links():
    chart = load_chart(Path("data/synthetic_charts/sdx001.json"))
    opportunities = analyze_evidence_graph(chart.evidence_graph)

    assert opportunities
    for opportunity in opportunities:
        assert opportunity.has_evidence()
        for item in opportunity.evidence:
            assert item.links
            assert item.links[0].entity_id in chart.encounter_graph.entities
            json.dumps(item.to_json(), sort_keys=True)


def test_chart_wrapper_uses_same_graph_backed_pipeline():
    chart = load_chart(Path("data/synthetic_charts/sdx001.json"))
    via_chart = [opportunity.to_json() for opportunity in analyze_chart(chart)]
    via_graph = [opportunity.to_json() for opportunity in analyze_evidence_graph(chart.evidence_graph)]

    assert via_chart == via_graph


def test_evidence_models_are_serializable():
    chart = load_chart(Path("data/synthetic_charts/sdx001.json"))
    entity = chart.encounter_graph.by_type("lab")[0]
    link = EvidenceLink("lab:l1", "supports", entity.citation())
    item = EvidenceItem("test criterion", entity.citation(), "1.0 mg/dL", [link])
    cluster = EvidenceCluster("cluster-1", "test cluster", [item])
    trace = AuditTrace(["graph built", "evidence linked"])

    json.dumps(cluster.to_json(), sort_keys=True)
    json.dumps(trace.to_json(), sort_keys=True)


def test_encounter_graph_represents_all_requested_entity_types():
    chart = {
        "chart_id": "graph001",
        "patient": {"synthetic": True},
        "encounter": {"admit": "2026-02-01", "discharge": "2026-02-03"},
        "coded_diagnoses": ["pneumonia"],
        "labs": [{"id": "l1", "timestamp": "2026-02-01T08:00:00", "name": "wbc", "value": 12.1, "unit": "K/uL"}],
        "vitals": [{"id": "v1", "timestamp": "2026-02-01T08:05:00", "hr": 110}],
        "medications": [{"id": "m1", "timestamp": "2026-02-01T09:00:00", "name": "ceftriaxone", "route": "IV"}],
        "notes": [{"id": "n1", "timestamp": "2026-02-01T07:45:00", "type": "H&P", "text": "Synthetic note."}],
        "orders": [{"id": "o1", "timestamp": "2026-02-01T09:10:00", "description": "blood culture order"}],
        "procedures": [{"id": "p1", "timestamp": "2026-02-02T10:00:00", "description": "bronchoscopy"}],
        "claims": [{"id": "c1", "timestamp": "2026-02-04T00:00:00", "description": "synthetic claim"}],
        "charges": [{"id": "ch1", "timestamp": "2026-02-02T12:00:00", "description": "room charge"}],
        "denial_letters": [{"id": "d1", "timestamp": "2026-02-10T00:00:00", "text": "medical necessity denial"}],
        "payer_policies": [{"id": "pol1", "timestamp": "2026-01-01T00:00:00", "title": "inpatient policy"}],
    }

    graph = normalize_chart(chart).encounter_graph
    entity_types = {entity.entity_type for entity in graph.entities.values()}

    assert {
        "note",
        "lab",
        "vital",
        "medication",
        "order",
        "procedure",
        "diagnosis",
        "claim",
        "charge",
        "denial_letter",
        "payer_policy",
    } <= entity_types
    assert graph.edges
    json.dumps(graph.to_json(), sort_keys=True)
