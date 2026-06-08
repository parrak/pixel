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
from asc_rcm_lite.personas import PERSONA_CONFIGS, build_operator_os_landing, build_persona_experiences
from asc_rcm_lite.pipeline import DEFAULT_AS_OF_DATE, run_pipeline


ROLE_LABELS = {
    "manager": "Manager",
    "vp_revenue_cycle": "VP Revenue Cycle",
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


def _workflow_graph_html(graph: dict[str, object]) -> str:
    stages = graph.get("stages", [])
    nodes = []
    for stage in stages:
        status = stage.get("status", "pending")
        nodes.append(
            f"""
            <div class="graph-node graph-{status}">
              <strong>{stage.get("label", "-")}</strong>
              <span>{stage.get("owner", "-")}</span>
            </div>
            """
        )
    return f"""
    <div class="graph-summary">
      <div><span>Current State</span><strong>{graph.get("current_state", "-")}</strong></div>
      <div><span>Owner</span><strong>{graph.get("owner", "-")}</strong></div>
      <div><span>Waiting On</span><strong>{graph.get("waiting_on", "-")}</strong></div>
      <div><span>Days In State</span><strong>{graph.get("days_in_state", "-")}</strong></div>
      <div><span>Deadline</span><strong>{graph.get("deadline_days_remaining", "-")} days remaining</strong></div>
      <div><span>Expected Recovery</span><strong>{_format_money(graph.get("expected_recovery"))}</strong></div>
    </div>
    <div class="workflow-graph">{''.join(nodes)}</div>
    """


def _workflow_graph_for(item: dict[str, object]) -> dict[str, object]:
    graph = item.get("workflow_graph")
    if graph:
        return graph
    owner = item.get("owner_name") or ROLE_LABELS.get(str(item.get("owner_role")), str(item.get("owner_role", "Operator")))
    current_state = item.get("workflow_status") or item.get("status") or "Human Action Required"
    return {
        "current_state": current_state,
        "owner": owner,
        "waiting_on": "Waiting on Operator Review",
        "days_in_state": "-",
        "deadline_days_remaining": "-",
        "expected_recovery": item.get("financial_impact"),
        "stages": [
            {"label": "Patient", "status": "complete", "owner": "Facility"},
            {"label": "Procedure", "status": "complete", "owner": "Facility"},
            {"label": "Coding", "status": "complete", "owner": "Coding Team"},
            {"label": "Claim", "status": "complete", "owner": "AR Specialist"},
            {"label": current_state, "status": "current", "owner": owner},
            {"label": "Next Action", "status": "next", "owner": owner},
            {"label": "Resolution", "status": "pending", "owner": "Operator"},
        ],
    }


def _render_persona_section(container, title: str, rows: list[dict[str, object]]) -> None:
    container.markdown(f"**{title}**")
    if rows:
        container.dataframe(rows, use_container_width=True)
    else:
        container.info("No items for this role.")


def _persona_card_html(persona: dict[str, object], role_key: str, fallback_label: str) -> str:
    config = PERSONA_CONFIGS.get(role_key, {})
    label = persona.get("label") or config.get("label") or fallback_label
    question = persona.get("operator_question") or config.get("operator_question") or "What work needs to get done?"
    primary_objects = persona.get("primary_objects") or config.get("primary_objects") or ["Work Object"]
    navigation = persona.get("navigation") or config.get("navigation") or ["My Work", "My Queue", "Recommended Actions"]
    metrics = persona.get("metrics") or {}
    current_item = (persona.get("my_work") or persona.get("my_queue") or [{}])[0]
    return f"""
    <div class="card">
      <div class="eyebrow">Role-Specific OS</div>
      <h3 style="margin:0.25rem 0;">{label}</h3>
      <p style="margin:0.35rem 0 0.85rem;color:var(--ink-500);">{question}</p>
      <div class="persona-layout">
        <div>
          <span>Primary Objects</span>
          <div class="persona-nav">{''.join(f"<strong>{item}</strong>" for item in primary_objects)}</div>
        </div>
        <div>
          <span>Navigation</span>
          <div class="persona-nav">{''.join(f"<strong>{item}</strong>" for item in navigation)}</div>
        </div>
        <div>
          <span>Queue State</span>
          <p><strong>{metrics.get('open_work', '-')}</strong> open work · <strong>{metrics.get('blocked_work', '-')}</strong> blocked · <strong>{metrics.get('urgent_work', '-')}</strong> urgent</p>
        </div>
        <div>
          <span>Current Object</span>
          <p><strong>{current_item.get('title', 'No current work object')}</strong><br/>
          {current_item.get('primary_object', 'Work Object')} · {current_item.get('current_state', '-')} · waiting on {current_item.get('dependency', '-')}</p>
        </div>
      </div>
    </div>
    """


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
    .workflow-graph {
        display: flex;
        gap: 0.65rem;
        overflow-x: auto;
        padding: 0.4rem 0 0.9rem;
    }
    .graph-node {
        min-width: 8.7rem;
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 0.75rem;
        background: var(--surface);
        position: relative;
    }
    .graph-node:not(:last-child)::after {
        content: ">";
        position: absolute;
        right: -0.55rem;
        top: 50%;
        transform: translateY(-50%);
        color: var(--ink-500);
        font-weight: 800;
    }
    .graph-node strong,
    .graph-node span {
        display: block;
    }
    .graph-node span {
        color: var(--ink-500);
        font-size: 0.78rem;
        margin-top: 0.25rem;
    }
    .graph-complete { background: var(--pine-50); }
    .graph-current {
        border-color: var(--pine-600);
        box-shadow: 0 0 0 2px rgba(27, 122, 94, 0.12);
    }
    .graph-next { background: var(--citron-100); }
    .graph-summary {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.7rem;
        margin: 0.7rem 0 0.9rem;
    }
    .graph-summary div {
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 0.75rem;
        background: var(--surface);
    }
    .graph-summary span,
    .persona-nav span {
        display: block;
        color: var(--ink-500);
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 700;
    }
    .persona-nav {
        display: flex;
        flex-wrap: wrap;
        gap: 0.55rem;
        margin: 0.75rem 0;
    }
    .persona-nav strong {
        border: 1px solid var(--border);
        border-radius: 999px;
        padding: 0.45rem 0.75rem;
        background: var(--surface);
    }
    .persona-layout {
        display: grid;
        grid-template-columns: 1.15fr 1.35fr 0.8fr 1fr;
        gap: 0.85rem;
        align-items: start;
    }
    .persona-layout span {
        display: block;
        color: var(--ink-500);
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 700;
        margin-bottom: 0.35rem;
    }
    .persona-layout p {
        margin: 0.45rem 0 0;
        color: var(--ink-500);
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
account_workspaces = portfolio.get("account_workspaces", [])
denial_workspaces = portfolio.get("denial_resolution_workspaces", [])
ar_workspaces = portfolio.get("ar_recovery_workspaces", [])
decision_registry = portfolio.get("decision_memory_registry", {})
payer_graph = portfolio.get("payer_intelligence_graph", {})
manager_system = portfolio.get("manager_intervention_system", {})
recovery_center = portfolio.get("revenue_recovery_command_center", {})
denial_factory = portfolio.get("denial_recovery_factory", {})
appeal_workspace = portfolio.get("appeal_workspace", {})
evidence_engine = portfolio.get("evidence_engine", {})
recovery_copilot_outputs = portfolio.get("recovery_copilot_outputs", {})
similar_recoveries = portfolio.get("similar_recoveries", {})
payer_playbooks = portfolio.get("payer_playbooks", {})
manager_recovery_operations = portfolio.get("manager_recovery_operations", {})
recovery_outcomes = portfolio.get("recovery_outcome_tracking", {})
nimble_recovery = portfolio.get("nimble_recovery_evaluation", {})
persona_experiences = portfolio.get("persona_experiences", {})
operator_os_landing = portfolio.get("operator_os_landing", {})
if not persona_experiences and all_work_objects:
    persona_experiences = build_persona_experiences(all_work_objects, recovery_center=recovery_center)
if not operator_os_landing and persona_experiences:
    operator_os_landing = build_operator_os_landing(persona_experiences=persona_experiences, recovery_center=recovery_center)
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
selected_account_workspace = next(
    (
        item
        for item in account_workspaces
        if item["organization_name"] == selected_org_name
        and any(work["owner_role"] == selected_role_key for work in item["open_work_objects"])
    ),
    account_workspaces[0] if account_workspaces else None,
)
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
      <div class="eyebrow">Monday Morning</div>
      <h1 style="margin:0.2rem 0 0.5rem 0;">Workflow System Of Record</h1>
      <p style="margin:0;max-width:58rem;">
        Operators begin inside their work. Citron shows the object, where it sits in the transaction lifecycle,
        who owns it, what is blocking it, and what happens next.
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
    f"<div class='subtle'><div class='metric-label'>Revenue At Risk</div><div class='metric-value'>{_format_money(operator_os_landing.get('revenue_at_risk'))}</div></div>",
    unsafe_allow_html=True,
)
metric_cols[1].markdown(
    f"<div class='subtle'><div class='metric-label'>Open Work</div><div class='metric-value'>{_format_number(operator_os_landing.get('open_work'))}</div></div>",
    unsafe_allow_html=True,
)
metric_cols[2].markdown(
    f"<div class='subtle'><div class='metric-label'>Critical Appeals</div><div class='metric-value'>{_format_number(operator_os_landing.get('critical_appeals'))}</div></div>",
    unsafe_allow_html=True,
)
metric_cols[3].markdown(
    f"<div class='subtle'><div class='metric-label'>Auths At Risk</div><div class='metric-value'>{_format_number(operator_os_landing.get('authorizations_at_risk'))}</div></div>",
    unsafe_allow_html=True,
)
metric_cols[4].markdown(
    f"<div class='subtle'><div class='metric-label'>Coding Pending</div><div class='metric-value'>{_format_number(operator_os_landing.get('coding_reviews_pending'))}</div></div>",
    unsafe_allow_html=True,
)

tabs = st.tabs(
    [
        "Revenue Recovery",
        "Account Workspace",
        "Work Queue",
        "Operational Journeys",
        "Denial Workspace",
        "AR Recovery",
        "Manager OS",
        "Decision Memory",
        "Payer Graph",
        "Nimble Evaluation",
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
    st.subheader("Revenue Recovery Command Center")
    st.caption(
        "Work-first operating console for denials, appeals, underpayments, and AR follow-up. "
        "The center shows what to work, what to escalate, what is blocked, and where money is trapped."
    )
    selected_persona = persona_experiences.get(selected_role_key, {})
    st.markdown(_persona_card_html(selected_persona, selected_role_key, selected_role), unsafe_allow_html=True)
    persona_cols = st.columns(5)
    _render_persona_section(persona_cols[0], "My Work", selected_persona.get("my_work", []))
    _render_persona_section(persona_cols[1], "My Queue", selected_persona.get("my_queue", []))
    _render_persona_section(persona_cols[2], "Today's Priorities", selected_persona.get("todays_priorities", []))
    _render_persona_section(persona_cols[3], "Blocked Work", selected_persona.get("blocked_work", []))
    _render_persona_section(persona_cols[4], "Recommended Actions", selected_persona.get("recommended_actions", []))
    recovery_metrics = recovery_center.get("metrics", {})
    recovery_cols = st.columns(5)
    recovery_cols[0].metric("Revenue At Risk", _format_money(recovery_metrics.get("revenue_at_risk")))
    recovery_cols[1].metric("Recoverable Revenue", _format_money(recovery_metrics.get("recoverable_revenue")))
    recovery_cols[2].metric("Appeals In Progress", _format_number(recovery_metrics.get("appeals_in_progress")))
    recovery_cols[3].metric("Near Deadline", _format_number(recovery_metrics.get("claims_near_deadline")))
    recovery_cols[4].metric("Recovered This Month", _format_money(recovery_metrics.get("recovered_this_month")))

    recovery_subtabs = st.tabs(
        [
            "Today",
            "Denial Factory",
            "Appeals",
            "Evidence",
            "Work Product",
            "Similar Recoveries",
            "Payer Playbooks",
            "Manager Ops",
            "Outcomes",
            "Nimble Scenario",
        ]
    )
    with recovery_subtabs[0]:
        st.markdown("#### Work Today")
        today_left, today_right = st.columns([1.1, 0.9])
        today_left.dataframe(recovery_center.get("work_today", []), use_container_width=True)
        today_right.dataframe(recovery_center.get("escalate", []), use_container_width=True)
        st.markdown("#### Money Trapped")
        st.dataframe(recovery_center.get("money_trapped", []), use_container_width=True)
        st.json(recovery_center.get("dataset_summary", {}))
    with recovery_subtabs[1]:
        st.markdown("#### Denial Recovery Factory")
        st.caption("Every denial opens with timeline, evidence, required documents, recommendation, and outcome.")
        st.dataframe(denial_factory.get("denials", [])[:40], use_container_width=True)
        st.write("Supported denial types:", ", ".join(denial_factory.get("supported_types", [])))
    with recovery_subtabs[2]:
        st.markdown("#### Appeal Workspace")
        appeals = appeal_workspace.get("appeals", [])
        st.dataframe(
            [
                {
                    "appeal_id": item["appeal_id"],
                    "payer": item["denial"]["payer"],
                    "denial_type": item["denial"]["denial_type"],
                    "financial_impact": _format_money(item["denial"]["financial_impact"]),
                    "submission_status": item["submission_status"],
                    "package_status": item["appeal_package"]["status"],
                }
                for item in appeals[:40]
            ],
            use_container_width=True,
        )
        if appeals:
            st.json(appeals[0])
    with recovery_subtabs[3]:
        st.markdown("#### Evidence Engine")
        evidence_packets = evidence_engine.get("evidence_packets", [])
        st.dataframe(
            [
                {
                    "claim_id": item["claim_id"],
                    "payer": item["payer"],
                    "denial_type": item["denial_type"],
                    "packet_readiness": item["packet_readiness"],
                }
                for item in evidence_packets[:50]
            ],
            use_container_width=True,
        )
        st.write("Evidence types:", ", ".join(evidence_engine.get("evidence_types", [])))
    with recovery_subtabs[4]:
        st.markdown("#### Generated Work Product")
        st.caption("Copilot output is represented as usable operational artifacts, not chat.")
        st.dataframe(recovery_copilot_outputs.get("outputs", []), use_container_width=True)
    with recovery_subtabs[5]:
        st.markdown("#### Similar Recovery Intelligence")
        st.dataframe(similar_recoveries.get("patterns", []), use_container_width=True)
    with recovery_subtabs[6]:
        st.markdown("#### Payer Playbooks")
        st.dataframe(payer_playbooks.get("playbooks", []), use_container_width=True)
    with recovery_subtabs[7]:
        st.markdown("#### Manager Recovery Operations")
        mgr_left, mgr_right = st.columns(2)
        mgr_left.dataframe(manager_recovery_operations.get("prioritize_revenue", []), use_container_width=True)
        mgr_right.dataframe(manager_recovery_operations.get("escalate_cases", []), use_container_width=True)
        st.markdown("#### Reassign Work")
        st.dataframe(manager_recovery_operations.get("reassign_work", []), use_container_width=True)
        st.markdown("#### Capacity")
        st.dataframe(manager_recovery_operations.get("allocate_capacity", []), use_container_width=True)
    with recovery_subtabs[8]:
        st.markdown("#### Recovery Outcomes")
        st.json(recovery_outcomes.get("rollup", {}))
        st.dataframe(recovery_outcomes.get("recoveries", []), use_container_width=True)
    with recovery_subtabs[9]:
        st.markdown("#### Nimble Evaluation Scenario")
        st.caption(nimble_recovery.get("scenario", ""))
        nimble_cols = st.columns(4)
        nimble_cols[0].metric("Denials", _format_number(nimble_recovery.get("denials")))
        nimble_cols[1].metric("Revenue At Risk", _format_money(nimble_recovery.get("revenue_at_risk")))
        nimble_cols[2].metric("Likely Recovery", _format_money(nimble_recovery.get("likely_recovery")))
        nimble_cols[3].metric("Recovered Walkthrough", _format_money(nimble_recovery.get("walkthrough_outcome", {}).get("recovered_revenue")))
        scenario_left, scenario_right = st.columns(2)
        scenario_left.dataframe(nimble_recovery.get("work_first", []), use_container_width=True)
        scenario_right.dataframe(nimble_recovery.get("where_money_is_trapped", []), use_container_width=True)
        st.write(nimble_recovery.get("actions_maximizing_collections", []))
        st.json(nimble_recovery.get("walkthrough_outcome", {}))

with tabs[1]:
    st.subheader("Account Workspace")
    st.caption("Primary operating screen. Financial impact, claim summary, timeline, evidence, work objects, artifacts, actions, prior outcomes, and activity history live in one workspace.")
    if selected_account_workspace:
        left, right = st.columns([1.05, 0.95])
        left.json(
            {
                "account_id": selected_account_workspace["account_id"],
                "claim_summary": selected_account_workspace["claim_summary"],
                "payer_summary": selected_account_workspace["payer_summary"],
                "current_owner": selected_account_workspace["current_owner"],
                "status": selected_account_workspace["status"],
                "recovery_potential": selected_account_workspace["recovery_potential"],
            }
        )
        right.json(
            {
                "recommended_actions": selected_account_workspace["recommended_actions"],
                "prior_outcomes": selected_account_workspace["prior_outcomes"],
            }
        )
        timeline_col, work_col = st.columns(2)
        timeline_col.dataframe(selected_account_workspace["timeline"], use_container_width=True)
        work_col.dataframe(
            [
                {
                    "work_object_id": item["work_object_id"],
                    "type": item["work_object_type"],
                    "status": item["status"],
                    "workflow_status": item["workflow_status"],
                    "financial_impact": _format_money(item["financial_impact"]),
                }
                for item in selected_account_workspace["open_work_objects"]
            ],
            use_container_width=True,
        )
        evidence_col, artifact_col = st.columns(2)
        evidence_col.dataframe(selected_account_workspace["evidence"], use_container_width=True)
        artifact_col.dataframe(selected_account_workspace["generated_artifacts"], use_container_width=True)
        st.markdown("#### Workflow Graph")
        st.markdown(_workflow_graph_html(_workflow_graph_for(selected_account_workspace["open_work_objects"][0])), unsafe_allow_html=True)
        st.dataframe(selected_account_workspace["activity_history"], use_container_width=True)
    else:
        st.info("No account workspace available.")

with tabs[2]:
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
    st.markdown("#### Workflow Graph")
    st.markdown(_workflow_graph_html(_workflow_graph_for(selected_work_object)), unsafe_allow_html=True)
    docs_col, memory_col = st.columns(2)
    docs_col.dataframe(selected_work_object["documents"], use_container_width=True)
    memory_col.dataframe(selected_work_object["institutional_memory"], use_container_width=True)

with tabs[3]:
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

with tabs[4]:
    st.subheader("Denial Resolution Workspace")
    st.caption("Complete denial lifecycle from receipt through payment.")
    if denial_workspaces:
        selected_denial = denial_workspaces[0]
        st.json(
            {
                "work_object_id": selected_denial["work_object_id"],
                "title": selected_denial["title"],
                "claim_id": selected_denial["claim_id"],
                "financial_impact": _format_money(selected_denial["financial_impact"]),
                "outcome": selected_denial["outcome"],
            }
        )
        left, right = st.columns(2)
        left.dataframe(selected_denial["stages"], use_container_width=True)
        right.dataframe(selected_denial["timeline"], use_container_width=True)
        st.markdown("#### Workflow Graph")
        st.markdown(_workflow_graph_html(_workflow_graph_for(selected_denial)), unsafe_allow_html=True)
        artifact_col, evidence_col = st.columns(2)
        artifact_col.dataframe(selected_denial["artifacts"], use_container_width=True)
        evidence_col.dataframe(selected_denial["evidence"], use_container_width=True)
    else:
        st.info("No denial workspace available.")

with tabs[5]:
    st.subheader("AR Recovery Workspace")
    st.caption("AR specialists can review, research, document, escalate, and resolve work without leaving Citron.")
    if ar_workspaces:
        selected_ar = ar_workspaces[0]
        st.json(
            {
                "work_object_id": selected_ar["work_object_id"],
                "title": selected_ar["title"],
                "scenario_tags": selected_ar["scenario_tags"],
                "financial_impact": _format_money(selected_ar["financial_impact"]),
                "outcome": selected_ar["outcome"],
            }
        )
        left, right = st.columns(2)
        left.dataframe(selected_ar["actions"], use_container_width=True)
        right.dataframe(selected_ar["timeline"], use_container_width=True)
        st.markdown("#### Workflow Graph")
        st.markdown(_workflow_graph_html(_workflow_graph_for(selected_ar)), unsafe_allow_html=True)
        evidence_col, artifact_col = st.columns(2)
        evidence_col.dataframe(selected_ar["evidence"], use_container_width=True)
        artifact_col.dataframe(selected_ar["generated_artifacts"], use_container_width=True)
    else:
        st.info("No AR recovery workspace available.")

with tabs[6]:
    st.subheader("Manager Intervention System")
    st.caption("Managers operate. They rebalance work, remove blockers, override priorities, and create measurable workflow impact.")
    st.json(manager_system)

with tabs[7]:
    st.subheader("Decision Memory")
    st.caption("Every completed work object records problem, evidence, recommendation, decision, resolution, operator, payer, and financial result.")
    st.dataframe(decision_registry.get("records", []), use_container_width=True)
    left, right = st.columns(2)
    left.json({"similar_cases": decision_registry.get("similar_cases", {}), "successful_recoveries": decision_registry.get("successful_recoveries", [])[:4]})
    right.json({"failed_recoveries": decision_registry.get("failed_recoveries", []), "payer_history": decision_registry.get("payer_history", {})})

with tabs[8]:
    st.subheader("Payer Intelligence Graph")
    st.caption("Workflow outcomes become payer operating knowledge: denial patterns, appeal success, evidence effectiveness, recovery time, escalation paths, and response times.")
    st.json(payer_graph.get("questions", []))
    st.dataframe(payer_graph.get("payers", []), use_container_width=True)

with tabs[9]:
    st.subheader("Nimble Evaluation Mode")
    st.caption("10-minute operator walkthrough: revenue at risk appears, work is created, specialists process work, managers intervene, work product is generated, recovery happens, and knowledge compounds.")
    nimble_steps = [
        "Revenue at risk and open work objects appear in the account workspace.",
        "Specialists review evidence, generated artifacts, and timelines without leaving Citron.",
        "Managers rebalance queue work, remove blockers, and override priorities.",
        "Outcomes update payer intelligence, decision memory, and institutional knowledge.",
        "The result feels like working software rather than an AI demonstration.",
    ]
    st.json(
        {
            "audience": ["ASC operators", "RCM managers", "denial leaders", "AR leaders", "coding managers", "Nimble executives"],
            "walkthrough": nimble_steps,
            "account_workspace": selected_account_workspace["account_id"] if selected_account_workspace else None,
            "manager_capacity": manager_system.get("capacity_planning", {}),
        }
    )

with tabs[10]:
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

with tabs[11]:
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

with tabs[12]:
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

with tabs[13]:
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

with tabs[14]:
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

with tabs[15]:
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

with tabs[16]:
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

with tabs[17]:
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

with tabs[18]:
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

with tabs[19]:
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

with tabs[20]:
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
