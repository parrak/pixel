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
from asc_rcm_lite.operations import OperationalTask
from asc_rcm_lite.pipeline import DEFAULT_AS_OF_DATE, run_pipeline


def _task_card(label: str, title: str, body: str) -> str:
    return f"""
    <div class="card">
      <div class="eyebrow">{label}</div>
      <h4 style="margin:0.2rem 0 0.55rem 0;">{title}</h4>
      <p style="margin:0;">{body}</p>
    </div>
    """


def _outcome_from_decision(task: OperationalTask, decision: str, recommendation: object) -> dict[str, object]:
    title = getattr(recommendation, "title", "Recommendation")
    if decision == "Approve recommendation":
        return {
            "status": "Recovery pipeline advanced",
            "impact_summary": f"{task.workflow_name} moved forward with an approved action.",
            "value_realized": str(task.amount_at_risk or "0.00"),
            "notes": f"{title} was accepted for synthetic execution.",
        }
    if decision == "Escalate for manager review":
        return {
            "status": "Escalated",
            "impact_summary": "Task escalated to manager review due to workflow risk or ambiguity.",
            "value_realized": "0.00",
            "notes": "Synthetic escalation created for manager oversight.",
        }
    return {
        "status": "Rerouted",
        "impact_summary": "Recommendation rejected and task returned to workflow routing.",
        "value_realized": "0.00",
        "notes": "Synthetic task sent back for alternative handling.",
    }


st.set_page_config(page_title="Citron Health Operations Command Center", layout="wide")

st.markdown(
    """
    <style>
    .stApp { background: linear-gradient(180deg, #f4f2ea 0%, #fbfaf6 35%, #ffffff 100%); }
    .hero {
        padding: 1.25rem 1.4rem;
        border: 1px solid rgba(17, 24, 39, 0.08);
        border-radius: 22px;
        background: radial-gradient(circle at top left, rgba(255, 205, 102, 0.28), transparent 32%),
                    linear-gradient(135deg, #11261f 0%, #1d3a31 52%, #28473d 100%);
        color: #f8f7f2;
        margin-bottom: 1rem;
    }
    .subtle {
        padding: 0.9rem 1rem;
        border-radius: 18px;
        background: rgba(255,255,255,0.85);
        border: 1px solid rgba(17, 24, 39, 0.08);
    }
    .card {
        padding: 1rem;
        border-radius: 18px;
        background: #ffffff;
        border: 1px solid rgba(17, 24, 39, 0.08);
        height: 100%;
    }
    .eyebrow { color: #d8f0c7; letter-spacing: 0.12em; text-transform: uppercase; font-size: 0.75rem; }
    .metric-label { color: #6b7280; font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.08em; }
    .metric-value { color: #111827; font-size: 1.6rem; font-weight: 700; }
    .badge {
        display: inline-block;
        padding: 0.2rem 0.55rem;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 0.35rem;
    }
    .badge-urgent { background: #ffe4dd; color: #9f2d1d; }
    .badge-high { background: #fff0d8; color: #9a5b00; }
    .badge-normal { background: #e7f0ff; color: #234083; }
    .badge-low { background: #edf7eb; color: #2d6a33; }
    </style>
    """,
    unsafe_allow_html=True,
)


def _priority_badge(priority: str) -> str:
    return f"<span class='badge badge-{priority}'>{priority.replace('_', ' ').title()}</span>"


def _format_money(value: object) -> str:
    if value is None:
        return "-"
    return f"${value}"


result = run_pipeline(as_of_date=DEFAULT_AS_OF_DATE)
all_tasks = [task for case in result.cases for task in case.operational_tasks]
all_cases = {case.case_id: case for case in result.cases}

if "demo_decisions" not in st.session_state:
    st.session_state.demo_decisions = {}

st.markdown(
    """
    <div class="hero">
      <div class="eyebrow">Citron Health Phase 2</div>
      <h1 style="margin:0.2rem 0 0.5rem 0;">Operations Command Center</h1>
      <p style="margin:0;max-width:52rem;">
        Citron Health is the operating system for specialty revenue cycle. Start from the work queue,
        route operational tasks, review recommendations, record decisions, and track outcomes.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.warning("Synthetic data only. Human review required. No external APIs. No real payer submission.")

workflow_filter = st.sidebar.selectbox("Workflow", ["All"] + sorted({task.workflow_name for task in all_tasks}))
owner_filter = st.sidebar.selectbox("Owner", ["All"] + sorted({task.owner_role for task in all_tasks}))
priority_filter = st.sidebar.selectbox("Priority", ["All", "urgent", "high", "normal", "low"])
case_filter = st.sidebar.selectbox("Case", ["All"] + sorted(all_cases))

filtered_tasks = all_tasks
if workflow_filter != "All":
    filtered_tasks = [task for task in filtered_tasks if task.workflow_name == workflow_filter]
if owner_filter != "All":
    filtered_tasks = [task for task in filtered_tasks if task.owner_role == owner_filter]
if priority_filter != "All":
    filtered_tasks = [task for task in filtered_tasks if task.priority_band == priority_filter]
if case_filter != "All":
    filtered_tasks = [task for task in filtered_tasks if task.case_id == case_filter]

selected_task_label = st.sidebar.selectbox(
    "Task",
    [f"{task.task_id} | {task.workflow_name} | {task.title}" for task in filtered_tasks] or ["No tasks available"],
)
selected_task = next(
    (
        task
        for task in filtered_tasks
        if f"{task.task_id} | {task.workflow_name} | {task.title}" == selected_task_label
    ),
    filtered_tasks[0] if filtered_tasks else all_tasks[0],
)
selected_case = all_cases[selected_task.case_id]

metric_cols = st.columns(4)
metric_cols[0].markdown(
    f"<div class='subtle'><div class='metric-label'>Revenue At Risk</div><div class='metric-value'>${result.operational_metrics['revenue_at_risk']}</div></div>",
    unsafe_allow_html=True,
)
metric_cols[1].markdown(
    f"<div class='subtle'><div class='metric-label'>Open Work</div><div class='metric-value'>{result.operational_metrics['open_work']}</div></div>",
    unsafe_allow_html=True,
)
metric_cols[2].markdown(
    f"<div class='subtle'><div class='metric-label'>Urgent Tasks</div><div class='metric-value'>{result.operational_metrics['operational_health']['urgent_tasks']}</div></div>",
    unsafe_allow_html=True,
)
metric_cols[3].markdown(
    f"<div class='subtle'><div class='metric-label'>Recovery Pipeline</div><div class='metric-value'>${result.operational_metrics['recovery_pipeline']}</div></div>",
    unsafe_allow_html=True,
)

tabs = st.tabs(
    [
        "Operations Command Center",
        "Manager Dashboard",
        "Workflow Engine",
        "Decision Lab",
        "Legacy Copilots",
        "Audit & Eval",
    ]
)

with tabs[0]:
    st.subheader("Work Queue")
    st.caption("Primary Phase 2 surface: queue-first operations management for specialty RCM workflows.")
    rows = [
        {
            "task_id": task.task_id,
            "workflow": task.workflow_name,
            "title": task.title,
            "owner": task.owner_role,
            "priority": task.priority_band,
            "amount_at_risk": _format_money(task.amount_at_risk),
            "due_date": task.due_date or "-",
            "aging_days": task.aging_days if task.aging_days is not None else "-",
            "case_id": task.case_id,
        }
        for task in filtered_tasks
    ]
    st.dataframe(rows, use_container_width=True)

    left, right = st.columns([1.1, 0.9])
    with left:
        st.markdown(
            f"""
            <div class="card">
              <div class="eyebrow">{selected_task.workflow_name}</div>
              <h3 style="margin:0.2rem 0 0.6rem 0;">{selected_task.title}</h3>
              {_priority_badge(selected_task.priority_band)}
              <span class="badge badge-normal">{selected_task.owner_role.replace('_', ' ').title()}</span>
              <p style="margin-top:0.8rem;">{selected_task.description}</p>
              <p><strong>Case:</strong> {selected_task.case_id}<br/>
              <strong>Scenario:</strong> {selected_task.source_case_scenario}<br/>
              <strong>Amount at risk:</strong> {_format_money(selected_task.amount_at_risk)}<br/>
              <strong>Due date:</strong> {selected_task.due_date or "-"}<br/>
              <strong>Evidence:</strong> {", ".join(selected_task.cited_evidence_ids)}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right:
        recommendation = selected_task.recommendations[0]
        st.markdown(
            f"""
            <div class="card">
              <div class="eyebrow">Recommendation</div>
              <h3 style="margin:0.2rem 0 0.6rem 0;">{recommendation.title}</h3>
              <p><strong>Producer:</strong> {recommendation.producer}<br/>
              <strong>Confidence:</strong> {recommendation.confidence_label}<br/>
              <strong>Suggested action:</strong> {recommendation.suggested_action}</p>
              <p>{recommendation.summary}</p>
              <p><strong>Rationale:</strong> {recommendation.rationale}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

with tabs[1]:
    st.subheader("Manager Dashboard")
    dashboard_cols = st.columns(2)
    dashboard_cols[0].json(
        {
            "revenue_at_risk": result.operational_metrics["revenue_at_risk"],
            "open_work": result.operational_metrics["open_work"],
            "recovery_pipeline": result.operational_metrics["recovery_pipeline"],
            "queue_aging": result.operational_metrics["queue_aging"],
        }
    )
    dashboard_cols[1].json(
        {
            "workflow_bottlenecks": result.operational_metrics["workflow_bottlenecks"],
            "workflow_counts": result.operational_metrics["workflow_counts"],
            "specialist_productivity": result.operational_metrics["specialist_productivity"],
            "operational_health": result.operational_metrics["operational_health"],
        }
    )
    st.subheader("Operational Intelligence")
    st.json(result.payer_intelligence.payer_friction_score)

with tabs[2]:
    st.subheader("Workflow Engine")
    st.caption("Workflow definitions are first-class Phase 2 concepts.")
    workflow_rows = [
        {
            "workflow_id": workflow.workflow_id,
            "name": workflow.name,
            "queue_name": workflow.queue_name,
            "owner_roles": ", ".join(workflow.owner_roles),
            "sla_hours": workflow.service_level_hours,
            "trigger_sources": ", ".join(workflow.trigger_sources),
            "target_outcomes": ", ".join(workflow.target_outcomes),
        }
        for workflow in result.workflow_definitions
    ]
    st.dataframe(workflow_rows, use_container_width=True)

with tabs[3]:
    st.subheader("Task -> Recommendation -> Decision -> Outcome")
    st.caption("Synthetic interactive workflow for the selected operational task.")
    recommendation = selected_task.recommendations[0]
    decision_key = f"{selected_task.task_id}:decision"
    rationale_key = f"{selected_task.task_id}:rationale"
    simulated = st.session_state.demo_decisions.get(selected_task.task_id)

    decision = st.radio(
        "Human decision",
        ["Approve recommendation", "Escalate for manager review", "Reject and reroute"],
        key=decision_key,
        horizontal=True,
    )
    st.text_input(
        "Decision rationale",
        value=st.session_state.get(rationale_key, "Validated synthetic evidence and chose the next operational step."),
        key=rationale_key,
    )
    if st.button("Record synthetic outcome", use_container_width=True):
        rationale = st.session_state.get(rationale_key, "")
        st.session_state.demo_decisions[selected_task.task_id] = {
            "decision": decision,
            "rationale": rationale,
            "outcome": _outcome_from_decision(selected_task, decision, recommendation),
        }
        simulated = st.session_state.demo_decisions[selected_task.task_id]

    chain_cols = st.columns(4)
    chain_cols[0].markdown(_task_card("Task", selected_task.title, selected_task.workflow_name), unsafe_allow_html=True)
    chain_cols[1].markdown(_task_card("Recommendation", recommendation.title, recommendation.suggested_action), unsafe_allow_html=True)
    chain_cols[2].markdown(
        _task_card("Decision", simulated["decision"] if simulated else "Awaiting human choice", simulated["rationale"] if simulated else "No decision recorded"),
        unsafe_allow_html=True,
    )
    chain_cols[3].markdown(
        _task_card(
            "Outcome",
            simulated["outcome"]["status"] if simulated else "Outcome pending",
            simulated["outcome"]["impact_summary"] if simulated else "Record a synthetic decision to preview outcome tracking.",
        ),
        unsafe_allow_html=True,
    )
    if simulated:
        st.json(simulated["outcome"])

with tabs[4]:
    st.subheader("Legacy Copilot Surfaces")
    legacy_tabs = st.tabs(["Coding", "A/R", "Denials", "Workflow Assistant", "Payer Intelligence", "Case Detail"])

    with legacy_tabs[0]:
        for issue in selected_case.coding_opportunities:
            st.markdown(f"### {issue.coding_issue_type}")
            st.write(issue.risk_reason)
            st.caption(f"Evidence: {', '.join(issue.evidence_citation_ids)}")
        if not selected_case.coding_opportunities:
            st.info("No coding opportunities for the selected synthetic case.")

    with legacy_tabs[1]:
        ar = ARCopilot()
        if selected_case.ar_flags:
            st.text(ar.generate_internal_followup_note(selected_case.ar_flags[0]).content)
            st.text(ar.generate_payer_call_script(selected_case.ar_flags[0]).content)
        else:
            st.info("No A/R flags for the selected synthetic case.")

    with legacy_tabs[2]:
        denial = DenialCopilot()
        if selected_case.denial_opportunities:
            item = selected_case.denial_opportunities[0]
            st.text(denial.denial_summary(item).content)
            st.text(denial.appeal_letter_draft(item).content)
            st.text(denial.evidence_checklist(item).content)
        else:
            st.info("No denial opportunities for the selected synthetic case.")

    with legacy_tabs[3]:
        assistant = WorkflowAssistant()
        if selected_case.workflow_items:
            item = selected_case.workflow_items[0]
            st.write(
                {
                    "current_state": item.current_state,
                    "allowed_actions": assistant.allowed_actions(item, role=item.owner_role),
                }
            )
            st.text(assistant.generate_role_specific_note(item, role=item.owner_role).content)
        else:
            st.info("No workflow items for the selected synthetic case.")

    with legacy_tabs[4]:
        intelligence = PayerIntelligenceCopilot()
        st.text(intelligence.answer("Which work items should a manager review today?", result.payer_intelligence).response_text)
        st.json(
            {
                "denials_by_payer": result.payer_intelligence.denials_by_payer,
                "denials_by_cpt": result.payer_intelligence.denials_by_cpt,
                "top_root_causes": result.payer_intelligence.top_preventable_root_causes,
            }
        )

    with legacy_tabs[5]:
        st.json(
            {
                "case_id": selected_case.case_id,
                "coding_opportunities": [item.coding_issue_type for item in selected_case.coding_opportunities],
                "ar_flags": [item.flag_type for item in selected_case.ar_flags],
                "denial_categories": [item.denial_category for item in selected_case.denial_opportunities],
            }
        )

with tabs[5]:
    st.subheader("Audit & Eval")
    if selected_case.workflow_items:
        st.write([event.__dict__ for event in selected_case.workflow_items[0].audit_trace])
    else:
        st.info("No workflow audit events have been recorded yet.")
    from evals.run_asc_copilot_eval import run_asc_copilot_eval

    st.json(run_asc_copilot_eval())
