from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.ingest import load_charts
from app.workflows.prebill.agent import run_prebill_agent


CHART_DIR = ROOT / "data" / "synthetic_charts"


st.set_page_config(page_title="Clinical RI Lite", layout="wide")
st.title("Clinical RI Lite v0.1")
st.caption("Synthetic deterministic-first clinical revenue integrity copilot. No PHI. No external APIs.")

charts = load_charts(CHART_DIR)
chart_ids = [chart.chart_id for chart in charts]
selected_id = st.sidebar.selectbox("Synthetic chart", chart_ids)
chart = next(item for item in charts if item.chart_id == selected_id)
actions = run_prebill_agent(chart.evidence_graph)
opportunities = [action.opportunity for action in actions]

st.sidebar.metric("Reviewer actions", len(actions))
st.sidebar.write("Gold labels:", chart.raw.get("gold_opportunities", []))

left, right = st.columns([0.95, 1.05])

with left:
    st.subheader("Encounter bundle")
    st.write({"patient": chart.patient, "encounter": chart.encounter})
    st.subheader("Coded diagnoses")
    st.write(chart.coded_diagnoses or ["None"])

    st.subheader("Encounter graph timeline")
    for entity in chart.encounter_graph.timeline():
        with st.expander(f"{entity.timestamp} | {entity.entity_type} | {entity.label}", expanded=False):
            st.write(entity.excerpt)

with right:
    st.subheader("Reviewer actions")
    if not actions:
        st.info("No workflow agent action emitted for this synthetic encounter bundle.")
    for action in actions:
        opportunity = action.opportunity
        st.markdown(f"### {opportunity.title}")
        st.metric("Rank score", opportunity.rank_score)
        st.write(opportunity.summary)
        st.write(f"Documentation gap: {opportunity.missing_or_weak_documentation}")

        st.markdown("Graph-backed evidence citations")
        for item in opportunity.evidence:
            graph_links = ", ".join(link.entity_id for link in item.links)
            st.write(
                f"- {item.criterion}: {item.citation.source_type} {item.citation.source_id} "
                f"at {item.citation.timestamp} — {item.citation.excerpt} (`{graph_links}`)"
            )

        st.markdown("Neutral provider query")
        st.info(opportunity.query)

        st.markdown("Reviewer packet")
        st.text_area(
            f"Packet {opportunity.opportunity_id}",
            action.packet,
            height=320,
        )

        st.markdown("Audit trace")
        st.code("\n".join(opportunity.audit_trace))
