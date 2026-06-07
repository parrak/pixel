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
from asc_rcm_lite.journeys import execute_journey
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


def _format_number(value: object) -> str:
    if value in (None, "", "None"):
        return "-"
    return str(value)


st.set_page_config(page_title="Citron Health Workflow System", layout="wide")
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
all_work_objects = portfolio.get("work_objects", [])
orgs = portfolio["organizations"]
org_names = [org["name"] for org in orgs]
st.sidebar.image(str(LOGO_PATH), width=44)
st.sidebar.markdown(
    """
    <div class="brand-lockup" style="margin-bottom:0.9rem;">
        <div class="brand-wordmark">
          <div class="brand-title">Citron<b> Health</b></div>
          <div class="brand-subtitle">Workflow System Of Record</div>
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
role_work_objects = [
    item
    for item in all_work_objects
    if item["organization_name"] == selected_org_name and item["owner_role"] == selected_role_key
] or [
    item for item in all_work_objects if item["organization_name"] == selected_org_name
]
selected_work_object_label = st.sidebar.selectbox(
    "Work Object",
    [f"{item['work_object_id']} | {item['title']}" for item in role_work_objects],
)
selected_work_object = next(item for item in role_work_objects if f"{item['work_object_id']} | {item['title']}" == selected_work_object_label)
selected_task = next(task for task in role_tasks if task.task_id == selected_work_object["task_id"])
selected_case = all_cases[selected_task.case_id]
selected_workflow = st.sidebar.selectbox("Workflow", [workflow.name for workflow in result.workflow_definitions], index=0)

st.markdown(
    f"""
    <div class="hero">
      <div class="brand-lockup" style="margin-bottom:0.9rem;">
        <img class="brand-mark" src="{LOGO_DATA_URI}" alt="Citron Health logo" />
        <div class="brand-wordmark">
          <div class="brand-title" style="color:#f8f7f2;">Citron<b style="color:#cfe84f;"> Health</b></div>
          <div class="brand-subtitle" style="color:#d8f0c7;">Workflow System Of Record</div>
        </div>
      </div>
      <div class="eyebrow">Workflow-Native Reset</div>
      <h1 style="margin:0.2rem 0 0.5rem 0;">Work Begins With The Work Object</h1>
      <p style="margin:0;max-width:58rem;">
        Citron exists to help AR, denial, authorization, and coding teams resolve work. The primary object is now the
        work object: claim-linked operational work with a visible timeline, evidence, generated work product, actions,
        outcome, and institutional memory.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.warning("Synthetic data only. Human review required. No external APIs. No autonomous workflows.")

holdco = portfolio["holdco"]
holdco_dashboard = portfolio["holdco_dashboard"]
decision_intelligence = portfolio["decision_intelligence"]

metric_cols = st.columns(5)
metric_cols[0].markdown(
    f"<div class='subtle'><div class='metric-label'>Portfolio Revenue</div><div class='metric-value'>${holdco_dashboard['portfolio_revenue']}</div></div>",
    unsafe_allow_html=True,
)
metric_cols[1].markdown(
    f"<div class='subtle'><div class='metric-label'>Portfolio EBITDA</div><div class='metric-value'>${holdco_dashboard['portfolio_ebitda']}</div></div>",
    unsafe_allow_html=True,
)
metric_cols[2].markdown(
    f"<div class='subtle'><div class='metric-label'>Revenue At Risk</div><div class='metric-value'>${holdco_dashboard['revenue_at_risk']}</div></div>",
    unsafe_allow_html=True,
)
metric_cols[3].markdown(
    f"<div class='subtle'><div class='metric-label'>Open Work</div><div class='metric-value'>{holdco_dashboard['open_work']}</div></div>",
    unsafe_allow_html=True,
)
metric_cols[4].markdown(
    f"<div class='subtle'><div class='metric-label'>Value Creation</div><div class='metric-value'>{_format_number(holdco_dashboard['value_creation_progress']['progress_pct'])}%</div></div>",
    unsafe_allow_html=True,
)

tabs = st.tabs(
    [
        "Work Queue",
        "Operational Journeys",
        "HoldCo Command Center",
        "Value Creation",
        "Portfolio Benchmarks",
        "Playbooks",
        "Executive Review",
        "Monday Morning",
        "Role Queues",
        "Decision Intelligence",
        "Workflow Engine",
        "Acquisition Integration",
        "Legacy Features",
    ]
)

with tabs[0]:
    st.subheader(f"{selected_role} Work Queue")
    st.caption("Operators begin with work. Each item is a workflow-native work object with its own timeline, evidence, work product, actions, outcome, and memory.")
    work_rows = [
        {
            "work_object_id": item["work_object_id"],
            "type": item["work_object_type"],
            "title": item["title"],
            "priority": item["priority"],
            "status": item["status"],
            "workflow_status": item["workflow_status"],
            "financial_impact": _format_money(item["financial_impact"]),
            "owner": item["owner_name"] or ROLE_LABELS.get(item["owner_role"], item["owner_role"]),
        }
        for item in role_work_objects
    ]
    st.dataframe(work_rows, use_container_width=True)
    summary_left, summary_right = st.columns([1.05, 0.95])
    summary_left.markdown(
        f"""
        <div class="card">
          <div class="eyebrow">{selected_work_object['work_object_type']}</div>
          <h3 style="margin:0.2rem 0 0.6rem 0;">{selected_work_object['title']}</h3>
          {_priority_badge(selected_work_object['priority'])}
          <span class="badge badge-normal">{selected_work_object['status']}</span>
          <p style="margin-top:0.8rem;"><strong>Financial Impact:</strong> {_format_money(selected_work_object['financial_impact'])}<br/>
          <strong>Owner:</strong> {selected_work_object['owner_name'] or ROLE_LABELS.get(selected_work_object['owner_role'], selected_work_object['owner_role'])}<br/>
          <strong>Account:</strong> {selected_work_object['account_id']}<br/>
          <strong>Claim:</strong> {selected_work_object['claim_id'] or '-'}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    summary_right.json(
        {
            "outcome": selected_work_object["outcome"],
            "recommendations": selected_work_object["recommendations"],
            "actions": selected_work_object["actions"],
        }
    )
    timeline_col, evidence_col = st.columns(2)
    timeline_col.dataframe(selected_work_object["timeline"], use_container_width=True)
    evidence_col.dataframe(selected_work_object["evidence"], use_container_width=True)
    docs_col, memory_col = st.columns(2)
    docs_col.dataframe(selected_work_object["documents"], use_container_width=True)
    memory_col.dataframe(selected_work_object["institutional_memory"], use_container_width=True)

with tabs[1]:
    st.subheader("End-to-End Operational Journeys")
    st.caption("Run a realistic day-in-the-life workflow from queue identification through decision, outcome, and impact.")
    journey_options = {
        "AR Specialist": "ar_specialist",
        "AR Manager": "ar_manager",
        "VP Revenue Cycle": "vp_revenue_cycle",
    }
    selected_journey_label = st.selectbox("Role", list(journey_options), key="journey_role")
    journey = execute_journey(journey_options[selected_journey_label]).to_dict()
    top_left, top_right = st.columns([1.05, 0.95])
    top_left.markdown(
        _task_card(
            journey["persona"],
            journey["title"],
            journey["scenario"],
        ),
        unsafe_allow_html=True,
    )
    top_right.json(
        {
            "metrics_before": journey["metrics_before"],
            "metrics_after": journey["metrics_after"],
            "institutional_memory_update": journey["institutional_memory_update"],
        }
    )
    st.json(
        {
            "queue_snapshot": journey["queue_snapshot"],
            "recommendation_history": journey["recommendation_history"],
            "final_outcome": journey["final_outcome"],
        }
    )
    st.dataframe(journey["steps"], use_container_width=True)
    if journey["payer_history"] or journey["claim_history"] or journey["prior_follow_up_activity"]:
        history_left, history_right, history_third = st.columns(3)
        history_left.json({"payer_history": journey["payer_history"]})
        history_right.json({"claim_history": journey["claim_history"]})
        history_third.json({"prior_follow_up_activity": journey["prior_follow_up_activity"]})

with tabs[2]:
    st.subheader("HoldCo Dashboard")
    st.caption("What should leadership focus on today across the specialty RCM platform?")
    lead_left, lead_right = st.columns([1.05, 0.95])
    lead_left.markdown(
        _task_card(
            holdco["name"],
            "Enterprise Value Flow",
            " -> ".join(holdco_dashboard["enterprise_value_flow"]),
        ),
        unsafe_allow_html=True,
    )
    lead_right.json(
        {
            "thesis": holdco["thesis"],
            "focus_today": holdco_dashboard["focus_today"],
            "critical_bottlenecks": holdco_dashboard["critical_bottlenecks"],
        }
    )

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
            "portfolio_health": holdco_dashboard["portfolio_health"],
            "operational_risks": holdco_dashboard["operational_risks"],
            "recent_acquisitions": holdco_dashboard["recent_acquisitions"],
        }
    )
    right.json(
        {
            "productivity_trends": holdco_dashboard["productivity_trends"],
            "value_creation_progress": holdco_dashboard["value_creation_progress"],
            "portfolio_operational_health": portfolio["portfolio_metrics"]["operational_health"],
        }
    )

with tabs[3]:
    st.subheader("Value Creation System")
    st.caption("Operational changes tied directly to expected and realized EBITDA impact.")
    initiative_rows = [
        {
            "initiative": item["name"],
            "owner": f"{item['owner_name']} · {item['owner_title']}",
            "status": item["status"],
            "timeline": item["timeline"],
            "target": item["target"],
            "expected_ebitda_impact": _format_money(item["expected_ebitda_impact"]),
            "realized_ebitda_impact": _format_money(item["realized_ebitda_impact"]),
        }
        for item in portfolio["value_creation_initiatives"]
    ]
    st.dataframe(initiative_rows, use_container_width=True)
    selected_initiative = portfolio["value_creation_initiatives"][0]
    st.json(selected_initiative)

with tabs[4]:
    st.subheader("Portfolio Benchmarking")
    st.caption("Compare every organization to the portfolio average, top quartile, and best-in-class.")
    benchmark_org = next(item for item in portfolio["portfolio_benchmarks"]["organizations"] if item["name"] == selected_org_name)
    benchmark_rows = [
        {
            "metric": item["label"],
            "organization_value": item["organization_value"],
            "portfolio_average": item["portfolio_average"],
            "top_quartile": item["top_quartile"],
            "best_in_class": item["best_in_class"],
            "direction": item["direction"],
            "variance_to_average": item["variance_to_average"],
        }
        for item in benchmark_org["benchmarks"]
    ]
    st.dataframe(benchmark_rows, use_container_width=True)
    st.info(portfolio["portfolio_benchmarks"]["narrative"])

with tabs[5]:
    st.subheader("Playbook System")
    st.caption("Reusable operating playbooks standardize acquired operators across the platform.")
    selected_playbook_name = st.selectbox("Playbook", [item["name"] for item in portfolio["playbooks"]], key="playbook_selector")
    playbook = next(item for item in portfolio["playbooks"] if item["name"] == selected_playbook_name)
    playbook_rows = [
        {
            "title": item["title"],
            "owner_role": ROLE_LABELS.get(item["owner_role"], item["owner_role"]),
            "dependency": item["dependency"],
            "expected_outcome": item["expected_outcome"],
            "financial_impact": _format_money(item["financial_impact"]),
        }
        for item in playbook["tasks"]
    ]
    st.dataframe(playbook_rows, use_container_width=True)
    st.json(playbook)

with tabs[6]:
    review = portfolio["executive_operating_review"]
    st.subheader("Executive Operating Review")
    st.caption("Monthly board-style readout for leadership, operating partners, and future executives.")
    summary_col, perf_col = st.columns([1.1, 0.9])
    summary_col.json(
        {
            "month": review["month"],
            "executive_summary": review["executive_summary"],
            "required_decisions": review["required_decisions"],
        }
    )
    perf_col.json(
        {
            "financial_performance": review["financial_performance"],
            "operational_performance": review["operational_performance"],
            "value_creation_progress": review["value_creation_progress"],
        }
    )
    st.json({"risks": review["risks"], "wins": review["wins"], "benchmark_excerpt": review["benchmark_excerpt"]})

with tabs[7]:
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

with tabs[8]:
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

with tabs[9]:
    st.subheader("Decision Intelligence Foundation")
    st.caption("Recommendation -> decision -> outcome memory with portfolio-wide visibility into what creates value.")
    st.json(decision_intelligence["summary"])
    intel_left, intel_right = st.columns(2)
    intel_left.json({"what_works": decision_intelligence["what_works"], "what_fails": decision_intelligence["what_fails"]})
    intel_right.dataframe(decision_intelligence["patterns"], use_container_width=True)
    st.markdown("---")
    st.caption("Task-level history remains visible below.")
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

with tabs[10]:
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

with tabs[11]:
    st.subheader("Acquisition Integration Center")
    st.caption("Post-acquisition integration experience that translates workflow standardization into value creation.")
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
            "current_state_assessment": simulation["current_state_assessment"],
            "operational_gaps": simulation["operational_gaps"],
            "operational_risks": simulation["operational_risks"],
            "technology_gaps": simulation["technology_gaps"],
        }
    )
    right.json(
        {
            "standardization_opportunities": simulation["standardization_opportunities"],
            "integration_plan": simulation["integration_plan"],
            "ninety_day_roadmap": simulation["ninety_day_roadmap"],
            "value_creation_opportunities": simulation["value_creation_opportunities"],
            "operating_model": simulation["operating_model"],
        }
    )

with tabs[12]:
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
