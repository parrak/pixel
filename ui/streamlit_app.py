from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.ingest import load_charts
from app.workflows.prebill.detector import analyze_chart
from app.workflows.prebill.packet import render_reviewer_packet


CHART_DIR = ROOT / "data" / "synthetic_charts"


st.set_page_config(page_title="Clinical RI Lite", layout="wide")
st.title("Clinical RI Lite v0.1")
st.caption("Synthetic deterministic-first clinical revenue integrity copilot. No PHI. No external APIs.")

charts = load_charts(CHART_DIR)
chart_ids = [chart.chart_id for chart in charts]
selected_id = st.sidebar.selectbox("Synthetic chart", chart_ids)
chart = next(item for item in charts if item.chart_id == selected_id)
opportunities = analyze_chart(chart)

st.sidebar.metric("Opportunities", len(opportunities))
st.sidebar.write("Gold labels:", chart.raw.get("gold_opportunities", []))

left, right = st.columns([0.95, 1.05])

with left:
    st.subheader("Chart")
    st.write({"patient": chart.patient, "encounter": chart.encounter})
    st.subheader("Coded diagnoses")
    st.write(chart.coded_diagnoses or ["None"])

    st.subheader("Evidence timeline")
    for fact in chart.facts:
        with st.expander(f"{fact.timestamp} | {fact.kind} | {fact.citation.label}", expanded=False):
            st.write(fact.citation.excerpt)

with right:
    st.subheader("Possible opportunities for reviewer validation")
    if not opportunities:
        st.info("No deterministic opportunity emitted for this synthetic chart.")
    for opportunity in opportunities:
        st.markdown(f"### {opportunity.title}")
        st.metric("Rank score", opportunity.rank_score)
        st.write(opportunity.summary)
        st.write(f"Documentation gap: {opportunity.missing_or_weak_documentation}")

        st.markdown("Evidence citations")
        for item in opportunity.evidence:
            st.write(
                f"- {item.criterion}: {item.citation.source_type} {item.citation.source_id} "
                f"at {item.citation.timestamp} — {item.citation.excerpt}"
            )

        st.markdown("Neutral provider query")
        st.info(opportunity.query)

        st.markdown("Reviewer packet")
        st.text_area(
            f"Packet {opportunity.opportunity_id}",
            render_reviewer_packet(chart, opportunity),
            height=320,
        )

        st.markdown("Audit trace")
        st.code("\n".join(opportunity.audit_trace))
