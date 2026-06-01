from pathlib import Path

from clinical_ri_lite.ingestion import load_charts
from clinical_ri_lite.pipeline import analyze_chart
from clinical_ri_lite.reviewer.packet import packet_is_complete, render_reviewer_packet
from clinical_ri_lite.text import count_unsupported_assertions


def test_packets_are_complete_and_do_not_assert_diagnosis():
    for chart in load_charts(Path("data/charts")):
        for opportunity in analyze_chart(chart):
            packet = render_reviewer_packet(chart, opportunity)
            assert packet_is_complete(packet)
            assert count_unsupported_assertions(packet) == 0


def test_queries_are_neutral_and_non_leading():
    banned = ["please document", "patient has", "diagnose", "meets criteria", "confirm"]
    for chart in load_charts(Path("data/charts")):
        for opportunity in analyze_chart(chart):
            query = opportunity.query.lower()
            assert "if clinically appropriate" in query
            assert not any(term in query for term in banned)

