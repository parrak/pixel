from pathlib import Path

from app.core.ingest import load_charts
from app.core.terminology import count_unsupported_assertions
from app.workflows.prebill.agent import run_prebill_agent
from app.workflows.prebill.detector import analyze_chart
from app.workflows.prebill.packet import packet_is_complete, render_reviewer_packet


def test_packets_are_complete_and_do_not_assert_diagnosis():
    for chart in load_charts(Path("data/synthetic_charts")):
        for opportunity in analyze_chart(chart):
            packet = render_reviewer_packet(chart, opportunity)
            assert packet_is_complete(packet)
            assert count_unsupported_assertions(packet) == 0


def test_queries_are_neutral_and_non_leading():
    banned = ["please document", "patient has", "diagnose", "meets criteria", "confirm"]
    for chart in load_charts(Path("data/synthetic_charts")):
        for opportunity in analyze_chart(chart):
            query = opportunity.query.lower()
            assert "if clinically appropriate" in query
            assert not any(term in query for term in banned)


def test_reviewer_actions_have_complete_packets():
    for chart in load_charts(Path("data/synthetic_charts")):
        for action in run_prebill_agent(chart.evidence_graph):
            assert packet_is_complete(action.packet)
            assert action.has_graph_evidence()
