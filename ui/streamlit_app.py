from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
THEME_PATH = ROOT / "ui" / "citron_theme.css"
LOGO_PATH = ROOT / "ui" / "assets" / "logo-mark.svg"
LOGO_DATA_URI = "data:image/svg+xml;utf8," + LOGO_PATH.read_text(encoding="utf-8").replace('"', "'").replace("#", "%23").replace("\n", "")

from asc_rcm_lite.copilot.ar_copilot import ARCopilot
from asc_rcm_lite.copilot.denial_copilot import DenialCopilot
from asc_rcm_lite.copilot.payer_intelligence_copilot import PayerIntelligenceCopilot
from asc_rcm_lite.copilot.workflow_assistant import WorkflowAssistant
from asc_rcm_lite.operations import OperationalTask, simulate_acquisition
from asc_rcm_lite.pipeline import DEFAULT_AS_OF_DATE, run_pipeline


ROLE_LABELS = {
    "manager": "VP Revenue Cycle",
    "denial_specialist": "Denial Specialist",
    "biller": "AR Specialist",
    "coder": "Coding Specialist",
    "auth_specialist": "Authorization Specialist",
}


def _priority_badge(priority: str) -> str:
    return f"<span class='badge badge-{priority}'>{priority.replace('_', ' ').title()}</span>"


def _task_card(label: str, title: str, body: str) -> str:
    return f"""
    <div class="card">
      <div class="eyebrow">{label}</div>
      <h4 style="margin:0.2rem 0 0.55rem 0;">{title}</h4>
      <p style="margin:0;">{body}</p>
    </div>
    """


def _format_money(value: object) -> str:
    if value in (None, "", "None"):
        return "-"
    return f"${value}"


st.set_page_config(page_title="Citron Health Operator OS", layout="wide")
st.markdown(f"<style>{THEME_PATH.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
st.markdown(
    """
    <style>
    .stApp { background: linear-gradient(180deg, #fafaf7 0%, #f5f6f2 36%, #ffffff 100%); }
    [data-testid="stSidebar"] {
        background: var(--surface);
        border-right: 1px solid var(--border);
    }
    .hero {
        padding: 1.3rem 1.5rem;
        border: 1px solid var(--border);
        border-radius: 24px;
        background:
          radial-gradient(circle at top left, rgba(207, 232, 79, 0.28), transparent 32%),
          linear-gradient(135deg, var(--pine-700) 0%, var(--pine-600) 52%, var(--pine-500) 100%);
        color: #f8f7f2;
        margin-bottom: 1rem;
    }
    .subtle {
        padding: 0.9rem 1rem;
        border-radius: 18px;
        background: var(--surface);
        border: 1px solid var(--border);
        box-shadow: var(--shadow-sm);
    }
    .card {
        padding: 1rem;
        border-radius: 18px;
        background: var(--surface);
        border: 1px solid var(--border);
        box-shadow: var(--shadow-sm);
        height: 100%;
    }
    .brand-lockup {
        display: flex;
        align-items: center;
        gap: 0.85rem;
    }
    .brand-mark {
        width: 2.7rem;
        height: 2.7rem;
        border-radius: 12px;
    }
    .brand-wordmark {
        display: flex;
        flex-direction: column;
        gap: 0.06rem;
    }
    .brand-title {
        font-size: 1.08rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        color: var(--ink-900);
    }
    .brand-title b { color: var(--pine-600); }
    .brand-subtitle {
        color: var(--ink-500);
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 700;
    }
    .eyebrow { color: #d8f0c7; letter-spacing: 0.12em; text-transform: uppercase; font-size: 0.75rem; font-weight: 700; }
    .metric-label { color: var(--ink-500); font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 700; }
    .metric-value { color: var(--ink-900); font-size: 1.6rem; font-weight: 800; }
    .badge {
        display: inline-block;
        padding: 0.2rem 0.55rem;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 0.35rem;
    }
    .badge-urgent { background: var(--danger-100); color: var(--danger-700); }
    .badge-high { background: var(--warning-100); color: var(--warning-700); }
    .badge-normal { background: var(--info-100); color: var(--info-700); }
    .badge-low { background: var(--success-100); color: var(--success-700); }
    </style>
    """,
    unsafe_allow_html=True,
)

result = run_pipeline(as_of_date=DEFAULT_AS_OF_DATE)
portfolio = result.portfolio_snapshot
all_tasks = [task for case in result.cases for task in case.operational_tasks]
all_cases = {case.case_id: case for case in result.cases}
orgs = portfolio["organizations"]
org_names = [org["name"] for org in orgs]
st.sidebar.image(str(LOGO_PATH), width=44)
st.sidebar.markdown(
    """
    <div class="brand-lockup" style="margin-bottom:0.9rem;">
      <div class="brand-wordmark">
        <div class="brand-title">Citron<b> Health</b></div>
        <div class="brand-subtitle">Operator Operating System</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)
selected_org_name = st.sidebar.selectbox("Organization", org_names, index=0)
selected_org = next(org for org in orgs if org["name"] == selected_org_name)
selected_role = st.sidebar.selectbox("Role View", [ROLE_LABELS[key] for key in ROLE_LABELS], index=0)
selected_role_key = next(key for key, value in ROLE_LABELS.items() if value == selected_role)
org_tasks = [task for task in all_tasks if task.organization_name == selected_org_name]
role_tasks = [task for task in org_tasks if task.owner_role == selected_role_key] or org_tasks
selected_task_label = st.sidebar.selectbox(
    "Task",
    [f"{task.task_id} | {task.title}" for task in role_tasks],
)
selected_task = next(task for task in role_tasks if f"{task.task_id} | {task.title}" == selected_task_label)
selected_case = all_cases[selected_task.case_id]
selected_workflow = st.sidebar.selectbox("Workflow", [workflow.name for workflow in result.workflow_definitions], index=0)

st.markdown(
    f"""
    <div class="hero">
      <div class="brand-lockup" style="margin-bottom:0.9rem;">
        <img class="brand-mark" src="{LOGO_DATA_URI}" alt="Citron Health logo" />
        <div class="brand-wordmark">
          <div class="brand-title" style="color:#f8f7f2;">Citron<b style="color:#cfe84f;"> Health</b></div>
          <div class="brand-subtitle" style="color:#d8f0c7;">Specialty Revenue Cycle OS</div>
        </div>
      </div>
      <div class="eyebrow">Citron Health Phase 3</div>
      <h1 style="margin:0.2rem 0 0.5rem 0;">Operator Operating System</h1>
      <p style="margin:0;max-width:58rem;">
        Citron exists to make acquired specialty RCM businesses better operators. The center of gravity is now
        portfolio workflow ownership: organization, facility, team, user, task, recommendation, decision, and outcome.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.warning("Synthetic data only. Human review required. No external APIs. No autonomous workflows.")

metric_cols = st.columns(5)
metric_cols[0].markdown(
    f"<div class='subtle'><div class='metric-label'>Revenue At Risk</div><div class='metric-value'>${portfolio['portfolio_metrics']['revenue_at_risk']}</div></div>",
    unsafe_allow_html=True,
)
metric_cols[1].markdown(
    f"<div class='subtle'><div class='metric-label'>Open Work</div><div class='metric-value'>{portfolio['portfolio_metrics']['open_work']}</div></div>",
    unsafe_allow_html=True,
)
metric_cols[2].markdown(
    f"<div class='subtle'><div class='metric-label'>Recovery Pipeline</div><div class='metric-value'>${portfolio['portfolio_metrics']['recovery_pipeline']}</div></div>",
    unsafe_allow_html=True,
)
metric_cols[3].markdown(
    f"<div class='subtle'><div class='metric-label'>Workflow Bottlenecks</div><div class='metric-value'>{len(portfolio['portfolio_metrics']['workflow_bottlenecks'])}</div></div>",
    unsafe_allow_html=True,
)
metric_cols[4].markdown(
    f"<div class='subtle'><div class='metric-label'>Organizations</div><div class='metric-value'>{len(portfolio['organizations'])}</div></div>",
    unsafe_allow_html=True,
)

tabs = st.tabs(
    [
        "Portfolio OS",
        "Monday Morning",
        "Role Queues",
        "Decision Memory",
        "Workflow Engine",
        "Acquisition Simulator",
        "Legacy Features",
    ]
)

with tabs[0]:
    st.subheader("Portfolio Dashboard")
    st.caption("Rollup thesis first: portfolio health across ASC Alpha, ASC Bravo, and ASC Charlie.")
    org_rows = [
        {
            "organization": summary["name"],
            "specialty": summary["specialty"],
            "revenue_at_risk": _format_money(summary["revenue_at_risk"]),
            "open_work": summary["open_work"],
            "recovery_pipeline": _format_money(summary["recovery_pipeline"]),
            "completed_outcomes": summary["productivity"]["completed_outcomes"],
            "financial_result": _format_money(summary["productivity"]["financial_result"]),
            "urgent_tasks": summary["operational_health"]["urgent_tasks"],
        }
        for summary in portfolio["organization_summaries"]
    ]
    st.dataframe(org_rows, use_container_width=True)

    left, right = st.columns(2)
    selected_org_summary = next(summary for summary in portfolio["organization_summaries"] if summary["name"] == selected_org_name)
    left.json(
        {
            "organization": selected_org_summary["name"],
            "thesis": selected_org_summary["thesis"],
            "aging": selected_org_summary["aging"],
            "operational_health": selected_org_summary["operational_health"],
        }
    )
    right.json(
        {
            "portfolio_operational_health": portfolio["portfolio_metrics"]["operational_health"],
            "workflow_counts": portfolio["portfolio_metrics"]["workflow_counts"],
            "specialist_productivity": portfolio["portfolio_metrics"]["specialist_productivity"],
        }
    )

with tabs[1]:
    monday = portfolio["monday_morning"]
    st.subheader(monday["title"])
    st.caption("Guided day-in-the-life experience for an acquired ASC operator running inside Citron.")
    vp, assign, outcomes = st.columns([1.2, 1, 1])
    vp.markdown(
        _task_card(
            "VP Revenue Cycle",
            f"{monday['vp_user']['display_name']} · {monday['vp_user']['organization']}",
            " ".join(monday["executive_brief"]),
        ),
        unsafe_allow_html=True,
    )
    assign.json({"assignments": monday["assignments"], "critical_work": monday["critical_work"]})
    outcomes.json({"workflow_bottlenecks": monday["workflow_bottlenecks"], "outcomes": monday["outcomes"]})

with tabs[2]:
    st.subheader(f"{selected_role} Queue")
    st.caption(f"Operational queue for {selected_org_name}. This view is role-first rather than detector-first.")
    role_rows = [
        {
            "task_id": task.task_id,
            "title": task.title,
            "workflow": task.workflow_name,
            "priority": task.priority_band,
            "facility": task.facility_name,
            "assignee": task.assignee_name,
            "amount_at_risk": _format_money(task.amount_at_risk),
            "status": task.status,
        }
        for task in role_tasks
    ]
    st.dataframe(role_rows, use_container_width=True)
    role_view = next(view for view in portfolio["role_views"] if view["role"] == selected_role_key)
    st.json(role_view)

    left, right = st.columns([1.1, 0.9])
    recommendation = selected_task.recommendations[0]
    left.markdown(
        f"""
        <div class="card">
          <div class="eyebrow">{selected_task.organization_name} · {selected_task.team_name}</div>
          <h3 style="margin:0.2rem 0 0.6rem 0;">{selected_task.title}</h3>
          {_priority_badge(selected_task.priority_band)}
          <span class="badge badge-normal">{ROLE_LABELS[selected_task.owner_role]}</span>
          <p style="margin-top:0.8rem;">{selected_task.description}</p>
          <p><strong>Facility:</strong> {selected_task.facility_name}<br/>
          <strong>Assignee:</strong> {selected_task.assignee_name}<br/>
          <strong>Workflow Stage:</strong> {selected_task.workflow_stage}<br/>
          <strong>Due Date:</strong> {selected_task.due_date or "-"}<br/>
          <strong>Amount at Risk:</strong> {_format_money(selected_task.amount_at_risk)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    right.markdown(
        f"""
        <div class="card">
          <div class="eyebrow">Recommendation</div>
          <h3 style="margin:0.2rem 0 0.6rem 0;">{recommendation.title}</h3>
          <p><strong>Producer:</strong> {recommendation.producer}<br/>
          <strong>Confidence:</strong> {recommendation.confidence_label}<br/>
          <strong>Suggested Action:</strong> {recommendation.suggested_action}</p>
          <p>{recommendation.summary}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with tabs[3]:
    st.subheader("Decision Memory")
    st.caption("Visible history for why work exists, what humans did, and what outcomes resulted.")
    history_rows = [
        {
            "record_id": record.record_id,
            "workflow_stage": record.workflow_stage,
            "recommendation": record.recommendation_title,
            "decision": record.decision.decision,
            "actor": record.decision.actor_name,
            "role": ROLE_LABELS.get(record.decision.actor_role, record.decision.actor_role),
            "outcome": record.outcome.status,
            "financial_result": _format_money(record.outcome.financial_result),
            "resolution_hours": record.outcome.resolution_time_hours,
            "timestamp": record.decision.timestamp,
        }
        for record in selected_task.history
    ]
    st.dataframe(history_rows, use_container_width=True)
    if selected_task.history:
        record = selected_task.history[0]
        st.json(
            {
                "why_recommendation_exists": record.recommendation_summary,
                "decision_rationale": record.decision.rationale,
                "outcome_summary": record.outcome.impact_summary,
                "notes": record.outcome.notes,
            }
        )

with tabs[4]:
    st.subheader("Workflow Definition Engine")
    st.caption("Workflow definitions are configuration-backed and future specialties can plug into the same engine.")
    workflow = next(workflow for workflow in result.workflow_definitions if workflow.name == selected_workflow)
    st.json(
        {
            "workflow_id": workflow.workflow_id,
            "name": workflow.name,
            "queue_name": workflow.queue_name,
            "default_team_name": workflow.default_team_name,
            "owner_roles": workflow.owner_roles,
            "decision_options": workflow.decision_options,
            "service_level_hours": workflow.service_level_hours,
            "target_outcomes": workflow.target_outcomes,
        }
    )
    stage_rows = [
        {
            "stage_id": stage.stage_id,
            "label": stage.label,
            "description": stage.description,
        }
        for stage in workflow.stages
    ]
    st.dataframe(stage_rows, use_container_width=True)

with tabs[5]:
    st.subheader("Acquisition Integration Simulator")
    st.caption("Demonstrates how software creates value across acquisitions instead of acting as a standalone point tool.")
    col1, col2, col3 = st.columns(3)
    specialty = col1.selectbox("Specialty", portfolio["acquisition_defaults"]["specialties"], index=0)
    headcount = col2.slider("Headcount", min_value=15, max_value=150, value=75, step=5)
    maturity = col3.selectbox("Workflow Maturity", portfolio["acquisition_defaults"]["workflow_maturity_levels"], index=1)
    systems = st.multiselect(
        "Systems",
        portfolio["acquisition_defaults"]["systems"],
        default=["EHR", "Practice Management", "Clearinghouse", "Payer Portals", "Spreadsheets"],
    )
    simulation = simulate_acquisition(
        specialty=specialty,
        headcount=headcount,
        workflow_maturity=maturity,
        systems=tuple(systems),
    )
    left, right = st.columns(2)
    left.json(
        {
            "workflow_map": simulation["workflow_map"],
            "operational_gaps": simulation["operational_gaps"],
            "standardization_opportunities": simulation["standardization_opportunities"],
        }
    )
    right.json(
        {
            "deployment_plan": simulation["deployment_plan"],
            "operating_model": simulation["operating_model"],
        }
    )

with tabs[6]:
    st.subheader("Legacy Features")
    st.caption("Existing ASC RCM features remain in the system as workflow-supporting modules.")
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
            st.write({"current_state": item.current_state, "allowed_actions": assistant.allowed_actions(item, role=item.owner_role)})
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
                "organization": selected_task.organization_name,
                "facility": selected_task.facility_name,
                "coding_opportunities": [item.coding_issue_type for item in selected_case.coding_opportunities],
                "ar_flags": [item.flag_type for item in selected_case.ar_flags],
                "denial_categories": [item.denial_category for item in selected_case.denial_opportunities],
            }
        )
