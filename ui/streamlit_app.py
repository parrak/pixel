from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from asc_rcm_lite.copilot.ar_copilot import ARCopilot
from asc_rcm_lite.copilot.denial_copilot import DenialCopilot
from asc_rcm_lite.copilot.payer_intelligence_copilot import PayerIntelligenceCopilot
from asc_rcm_lite.copilot.workflow_assistant import WorkflowAssistant
from asc_rcm_lite.pipeline import DEFAULT_AS_OF_DATE, run_pipeline


st.set_page_config(page_title="ASC RCM Copilot Workbench", layout="wide")
st.title("ASC RCM Copilot Workbench")
st.warning("Synthetic data only. Human review required. No external APIs. No real payer submission.")

result = run_pipeline(as_of_date=DEFAULT_AS_OF_DATE)
case_ids = [item.case_id for item in result.cases]
selected_case_id = st.sidebar.selectbox("Synthetic ASC case", case_ids)
selected_case = next(item for item in result.cases if item.case_id == selected_case_id)

st.sidebar.metric("Cases", len(result.cases))
st.sidebar.metric("Work items", sum(len(item.work_queue) for item in result.cases))
st.sidebar.metric("Urgent items", result.manager_metrics.get("urgent_items", 0))

tabs = st.tabs(
    [
        "Manager Dashboard",
        "Work Queue",
        "Coding Copilot",
        "A/R Copilot",
        "Denial Appeal Copilot",
        "Workflow Assistant",
        "Payer Intelligence",
        "Case Detail",
        "Audit Trace",
        "Eval Results",
    ]
)

with tabs[0]:
    st.subheader("Manager Dashboard")
    st.json(result.manager_metrics)
    st.subheader("Synthetic payer friction")
    st.json(result.payer_intelligence.payer_friction_score)

with tabs[1]:
    st.subheader("Work Queue")
    rows = [
        {
            "work_item_id": item.work_item_id,
            "priority_band": item.priority_band,
            "payer": item.payer,
            "claim_id": item.claim_id,
            "owner_role": item.owner_role,
            "amount_at_risk": str(item.balance),
            "aging_bucket": item.aging_bucket,
            "next_deadline": item.next_deadline,
            "queue_type": item.queue_type,
            "evidence_ids": ", ".join(item.cited_evidence_ids),
        }
        for case in result.cases
        for item in case.work_queue
    ]
    st.dataframe(rows, use_container_width=True)

with tabs[2]:
    st.subheader("Coding Copilot")
    for issue in selected_case.coding_opportunities:
        st.markdown(f"### {issue.coding_issue_type}")
        st.write(issue.risk_reason)
        st.caption(f"Evidence: {', '.join(issue.evidence_citation_ids)}")
    if not selected_case.coding_opportunities:
        st.info("No coding opportunities for the selected synthetic case.")
    st.info("Use reviewer packets and coding drafts below; every case-specific assertion cites evidence and requires human review.")

with tabs[3]:
    st.subheader("A/R Copilot")
    ar = ARCopilot()
    if selected_case.ar_flags:
        st.text(ar.generate_internal_followup_note(selected_case.ar_flags[0]).content)
        st.text(ar.generate_payer_call_script(selected_case.ar_flags[0]).content)
    else:
        st.info("No A/R flags for the selected synthetic case.")

with tabs[4]:
    st.subheader("Denial Appeal Copilot")
    denial = DenialCopilot()
    if selected_case.denial_opportunities:
        item = selected_case.denial_opportunities[0]
        st.text(denial.denial_summary(item).content)
        st.text(denial.appeal_letter_draft(item).content)
        st.text(denial.evidence_checklist(item).content)
    else:
        st.info("No denial opportunities for the selected synthetic case.")

with tabs[5]:
    st.subheader("Workflow Assistant")
    assistant = WorkflowAssistant()
    if selected_case.workflow_items:
        item = selected_case.workflow_items[0]
        st.write({"current_state": item.current_state, "allowed_actions": assistant.allowed_actions(item, role=item.owner_role)})
        st.text(assistant.generate_role_specific_note(item, role=item.owner_role).content)
    else:
        st.info("No workflow items for the selected synthetic case.")

with tabs[6]:
    st.subheader("Payer Intelligence")
    intelligence = PayerIntelligenceCopilot()
    st.text(intelligence.answer("Which work items should a manager review today?", result.payer_intelligence).response_text)
    st.json(
        {
            "denials_by_payer": result.payer_intelligence.denials_by_payer,
            "denials_by_cpt": result.payer_intelligence.denials_by_cpt,
            "top_root_causes": result.payer_intelligence.top_preventable_root_causes,
        }
    )

with tabs[7]:
    st.subheader("Case Detail")
    st.json(
        {
            "case_id": selected_case.case_id,
            "coding_opportunities": [item.coding_issue_type for item in selected_case.coding_opportunities],
            "ar_flags": [item.flag_type for item in selected_case.ar_flags],
            "denial_categories": [item.denial_category for item in selected_case.denial_opportunities],
        }
    )

with tabs[8]:
    st.subheader("Audit Trace")
    if selected_case.workflow_items:
        st.write([event.__dict__ for event in selected_case.workflow_items[0].audit_trace])
    else:
        st.info("No workflow audit events have been recorded yet.")

with tabs[9]:
    st.subheader("Eval Results")
    from evals.run_asc_copilot_eval import run_asc_copilot_eval

    st.json(run_asc_copilot_eval())
