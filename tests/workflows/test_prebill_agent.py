import json
from pathlib import Path

from app.core.ingest import load_bundle
from app.core.normalize import normalize_bundle
from app.workflows.prebill.agent import PrebillWorkflowAgent, run_prebill_agent


def test_prebill_agent_turns_evidence_graph_into_reviewer_actions():
    bundle = load_bundle(Path("data/synthetic_charts/sdx001.json"))
    chart = normalize_bundle(bundle)
    actions = PrebillWorkflowAgent().run(chart.evidence_graph)

    assert actions
    assert all(action.workflow == "prebill" for action in actions)
    assert all(action.action_type == "review_opportunity" for action in actions)
    assert all(action.has_graph_evidence() for action in actions)
    assert all("Evidence graph evaluated by prebill workflow agent." in action.audit_trace.events for action in actions)
    assert all("Graph evidence:" in action.packet for action in actions)
    json.dumps([action.to_json() for action in actions], sort_keys=True)


def test_architecture_pipeline_is_bundle_to_graph_to_agent_to_action():
    bundle = load_bundle(Path("data/synthetic_charts/sdx004.json"))
    chart = normalize_bundle(bundle)
    actions = run_prebill_agent(chart.evidence_graph)

    assert bundle.source_type == "synthetic_chart_json"
    assert chart.encounter_graph.chart_id == bundle.bundle_id
    assert chart.evidence_graph.encounter_graph is chart.encounter_graph
    assert actions
    assert actions[0].chart_id == bundle.bundle_id
