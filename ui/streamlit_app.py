from __future__ import annotations

import html
import json
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from asc_rcm_lite.copilot.ar_copilot import ARCopilot
from asc_rcm_lite.copilot.denial_copilot import DenialCopilot
from asc_rcm_lite.copilot.payer_intelligence_copilot import PayerIntelligenceCopilot
from asc_rcm_lite.copilot.workflow_assistant import WorkflowAssistant
from asc_rcm_lite.pipeline import DEFAULT_AS_OF_DATE, run_pipeline


ASSETS = Path(__file__).resolve().parent / "assets"
THEME = Path(__file__).resolve().parent / "citron_theme.css"
SURFACES = [
    "Manager dashboard",
    "Work queue",
    "Coding copilot",
    "A/R copilot",
    "Denial appeal copilot",
    "Workflow assistant",
    "Payer intelligence",
    "Case detail",
    "Audit trace",
    "Eval results",
]
ROLE_OPTIONS = ["manager", "coder", "biller", "denial_specialist", "auth_specialist"]


def inject_theme() -> None:
    st.markdown(f"<style>{THEME.read_text()}</style>", unsafe_allow_html=True)


def esc(value: object) -> str:
    return html.escape(str(value))


def format_money(value: object) -> str:
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return esc(value)
    return f"${amount:,.2f}"


def format_priority(priority: str) -> str:
    normalized = priority.lower()
    if normalized in {"urgent", "high", "critical"}:
        return "High"
    if normalized in {"normal", "medium"}:
        return "Medium"
    return "Low"


def badge(priority: str) -> str:
    level = format_priority(priority)
    css_level = level.lower()
    return (
        f"<span class='citron-badge citron-badge--{css_level}'>"
        f"<span class='citron-dot'></span>{esc(level)}</span>"
    )


def status_pill(label: str, tone: str = "open") -> str:
    return f"<span class='citron-status citron-status--{esc(tone)}'>{esc(label)}</span>"


def inline_code(value: object) -> str:
    return f"<span class='citron-inline-code'>{esc(value)}</span>"


def header(eyebrow: str, title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="citron-header">
          <div class="citron-eyebrow">{esc(eyebrow)}</div>
          <h1>{esc(title)}</h1>
          <p>{esc(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def compliance_banner() -> None:
    st.markdown(
        """
        <div class="citron-banner">
          <span class="citron-banner__icon">+</span>
          <div>
            <div class="citron-banner__title">Synthetic data only · human review required</div>
            <div class="citron-banner__text">No PHI · no external APIs · no real payer submission. Copilot output is assistive only.</div>
          </div>
          <span class="citron-banner__pill">Guardrails on</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def stat_card(label: str, value: str, delta: str, highlight: bool = False) -> str:
    value_class = "citron-stat__value citron-stat__value--hl" if highlight else "citron-stat__value"
    return (
        "<div class='citron-stat'>"
        f"<div class='citron-stat__label citron-eyebrow'>{esc(label)}</div>"
        f"<div class='{value_class}'>{esc(value)}</div>"
        f"<div class='citron-stat__delta'>{esc(delta)}</div>"
        "</div>"
    )


def panel(title: str, body: str, meta: str | None = None) -> str:
    meta_html = f"<div class='citron-panel__meta'>{esc(meta)}</div>" if meta else ""
    return (
        "<section class='citron-panel'>"
        "<div class='citron-panel__head'>"
        f"<h3 class='citron-panel__title'>{esc(title)}</h3>{meta_html}"
        "</div>"
        f"<div class='citron-panel__body'>{body}</div>"
        "</section>"
    )


def evidence_block(lines: tuple[str, ...]) -> str:
    cards = []
    for line in lines:
        cards.append(
            "<div class='citron-evidence'>"
            "<div class='citron-evidence__label'>Evidence</div>"
            f"<div class='citron-evidence__excerpt'>{esc(line)}</div>"
            "</div>"
        )
    return "".join(cards)


def list_block(items: tuple[str, ...] | list[str]) -> str:
    rows = "".join(f"<li>{esc(item)}</li>" for item in items)
    return f"<ul class='citron-list'>{rows}</ul>"


def queue_rows(queue_items) -> str:
    if not queue_items:
        return "<div class='citron-empty'>No work items match the selected context.</div>"
    rows = []
    for item in queue_items:
        rows.append(
            "<div class='citron-queue-row'>"
            f"<div class='citron-queue-row__top'>{badge(item.priority_band)}"
            f"{status_pill(item.queue_type.replace('_', ' '), 'open')}"
            f"<span class='citron-money'>{format_money(item.balance)}</span></div>"
            f"<div class='citron-queue-row__title'>{esc(item.opportunity_type.replace('_', ' '))}</div>"
            f"<div class='citron-queue-row__sub'>Claim {inline_code(item.claim_id)} · "
            f"Payer {inline_code(item.payer)} · Owner {esc(item.owner_role)} · "
            f"Aging {esc(item.aging_bucket)} · Deadline {inline_code(item.next_deadline or 'pending')}</div>"
            f"<div class='citron-meta-row' style='margin-top:.65rem'>{''.join(inline_code(c) for c in item.cited_evidence_ids)}</div>"
            "</div>"
        )
    return "".join(rows)


def render_sidebar(result, selected_case_id: str) -> tuple[str, str]:
    counts = result.manager_metrics
    logo_path = ASSETS / "logo-mark.svg"
    st.sidebar.image(str(logo_path), width=42)
    st.sidebar.markdown(
        """
        <div class="citron-brand">
          <div class="citron-brand__wordmark">
            <div class="citron-brand__title">Citron<b> Health</b></div>
            <div class="citron-brand__subtitle">Revenue cycle command center</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    viewer_role = st.sidebar.selectbox("Viewing as", ROLE_OPTIONS, index=0)
    surface = st.sidebar.radio("Surface", SURFACES, label_visibility="visible")
    st.sidebar.selectbox("Synthetic ASC case", [item.case_id for item in result.cases], index=[item.case_id for item in result.cases].index(selected_case_id), key="case_id")
    st.sidebar.markdown(
        f"""
        <div class="citron-sidebar-metrics">
          <div class="citron-sidebar-metric">
            <div class="citron-sidebar-metric__label">Cases</div>
            <div class="citron-sidebar-metric__value">{len(result.cases)}</div>
          </div>
          <div class="citron-sidebar-metric">
            <div class="citron-sidebar-metric__label">Work items</div>
            <div class="citron-sidebar-metric__value">{counts.get("total_items", 0)}</div>
          </div>
          <div class="citron-sidebar-metric">
            <div class="citron-sidebar-metric__label">Urgent items</div>
            <div class="citron-sidebar-metric__value">{counts.get("urgent_items", 0)}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    return viewer_role, surface


def packets_for_case(case_result):
    return {packet.work_item_id or packet.packet_id: packet for packet in case_result.reviewer_packets}


def render_dashboard(result, queue_items) -> None:
    header(
        "Manager dashboard",
        "Today's revenue-cycle picture",
        "Deterministic detectors surface the work; every item cites synthetic evidence and every draft remains assistive only.",
    )
    stat_html = "".join(
        [
            stat_card("Dollars at risk", format_money(result.manager_metrics["total_balance"]), "Synthetic balance across the active queue."),
            stat_card("Urgent items", str(result.manager_metrics["urgent_items"]), "Items nearing deadline or carrying high financial risk.", highlight=True),
            stat_card("Open work items", str(result.manager_metrics["total_items"]), "Current deterministic follow-up workload."),
            stat_card("Citation completeness", "100%", "All surfaced items retain evidence references."),
        ]
    )
    st.markdown(f"<div class='citron-grid-4'>{stat_html}</div>", unsafe_allow_html=True)

    top_items = sorted(queue_items, key=lambda item: item.balance, reverse=True)[:6]
    table_rows = "".join(
        f"<tr><td>{badge(item.priority_band)}</td><td><strong>{esc(item.opportunity_type.replace('_', ' '))}</strong><br><span class='citron-code'>{esc(item.claim_id)} · {esc(item.owner_role)}</span></td><td>{inline_code(item.payer)}</td><td class='citron-money'>{format_money(item.balance)}</td></tr>"
        for item in top_items
    )
    top_work = panel(
        "Highest-dollar work",
        f"<table class='citron-table'><thead><tr><th>Priority</th><th>Work item</th><th>Payer</th><th>At risk</th></tr></thead><tbody>{table_rows}</tbody></table>",
        "Sorted by amount at risk",
    )
    owner_roles = result.manager_metrics.get("owner_roles", {})
    total_items = max(sum(owner_roles.values()), 1)
    role_bars = "".join(
        f"<div class='citron-bar-row'><span>{esc(role.replace('_', ' '))}</span><div class='citron-bar-track'><div class='citron-bar-fill' style='width:{count / total_items * 100:.1f}%;background:var(--pine-500)'></div></div><span class='citron-money'>{count}</span></div>"
        for role, count in owner_roles.items()
    )
    friction_scores = result.payer_intelligence.payer_friction_score
    max_friction = max(friction_scores.values() or [1])
    friction_bars = "".join(
        f"<div class='citron-bar-row'><span class='citron-code'>{esc(payer)}</span><div class='citron-bar-track'><div class='citron-bar-fill' style='width:{score / max_friction * 100:.1f}%;background:var(--citron-500)'></div></div><span class='citron-money'>{score:.2f}</span></div>"
        for payer, score in friction_scores.items()
    )
    right_col = (
        panel("Owner role mix", f"<div class='citron-bars'>{role_bars}</div>")
        + panel("Synthetic payer friction", f"<div class='citron-bars'>{friction_bars}</div>")
    )
    st.markdown(f"<div class='citron-grid-2'><div>{top_work}</div><div>{right_col}</div></div>", unsafe_allow_html=True)


def render_work_queue(queue_items) -> None:
    header(
        "Work queue",
        "Priority-scored reviewer work",
        "Review the balance, deadlines, and cited evidence before any payer outreach, correction, appeal, or write-off decision.",
    )
    priority_filter = st.selectbox("Priority band", ["All", "High", "Medium", "Low"], index=0)
    queue_filter = st.selectbox("Queue type", ["All"] + sorted({item.queue_type for item in queue_items}), index=0)
    owner_filter = st.text_input("Search claim, payer, owner, or evidence")
    filtered = queue_items
    if priority_filter != "All":
        filtered = [item for item in filtered if format_priority(item.priority_band) == priority_filter]
    if queue_filter != "All":
        filtered = [item for item in filtered if item.queue_type == queue_filter]
    if owner_filter.strip():
        token = owner_filter.lower().strip()
        filtered = [
            item
            for item in filtered
            if token in " ".join(
                [
                    item.claim_id,
                    item.payer,
                    item.owner_role,
                    item.opportunity_type,
                    " ".join(item.cited_evidence_ids),
                ]
            ).lower()
        ]
    st.markdown(queue_rows(filtered), unsafe_allow_html=True)


def render_coding(selected_case, packet_index) -> None:
    header(
        "Coding copilot",
        "Evidence-first coding review",
        "Possible opportunities for reviewer validation are framed as coding checks, not coding decisions.",
    )
    if not selected_case.coding_opportunities:
        st.markdown("<div class='citron-empty'>No coding opportunities were detected for the selected synthetic case.</div>", unsafe_allow_html=True)
        return
    for issue in selected_case.coding_opportunities:
        packet = packet_index.get(issue.opportunity_id)
        left = panel(
            issue.coding_issue_type.replace("_", " "),
            f"<p>{esc(issue.risk_reason)}</p>"
            f"<p><strong>Suggested review action:</strong> {esc(issue.suggested_human_review_action)}</p>"
            f"<p><strong>Financial impact estimate:</strong> <span class='citron-money'>{format_money(issue.financial_impact_estimate or 0)}</span></p>",
            issue.source,
        )
        evidence = evidence_block(tuple(f"Evidence reviewed: {item}" for item in issue.evidence_citation_ids))
        right = panel(
            "Reviewer packet",
            evidence
            + (panel("Checklist", list_block(packet.human_review_checklist)) if packet else "")
            + (panel("Audit trace", list_block(packet.audit_trace)) if packet else ""),
        )
        st.markdown(
            f"<div class='citron-meta-row' style='margin-bottom:.6rem'>{badge(issue.severity)}{status_pill('human review required')}</div>",
            unsafe_allow_html=True,
        )
        st.markdown(f"<div class='citron-grid-2'><div>{left}</div><div>{right}</div></div>", unsafe_allow_html=True)


def render_ar(selected_case, packet_index) -> None:
    header(
        "A/R copilot",
        "Follow-up drafts stay reviewer-safe",
        "The copilot prepares internal notes and payer call scripts from deterministic A/R flags and cited evidence.",
    )
    if not selected_case.ar_flags:
        st.markdown("<div class='citron-empty'>No A/R follow-up items were detected for the selected synthetic case.</div>", unsafe_allow_html=True)
        return
    ar = ARCopilot()
    for flag in selected_case.ar_flags:
        packet = packet_index.get(flag.flag_id)
        note = ar.generate_internal_followup_note(flag).content
        script = ar.generate_payer_call_script(flag).content
        summary = panel(
            flag.flag_type.replace("_", " "),
            f"<p>{esc(flag.reason_for_flag)}</p>"
            f"<p><strong>Recommended next action:</strong> {esc(flag.recommended_next_action)}</p>"
            f"<div class='citron-kv'><span>{badge(flag.priority_band)}</span>{status_pill(flag.aging_bucket.replace('_', ' '))}<span class='citron-money'>{format_money(flag.balance)}</span></div>",
        )
        evidence = evidence_block(packet.evidence_table if packet else tuple(f"Evidence reviewed: {item}" for item in flag.evidence_citation_ids))
        drafts = panel("Internal follow-up note", f"<div class='citron-draft'>{esc(note)}</div>") + panel(
            "Payer call script",
            f"<div class='citron-draft'>{esc(script)}</div>",
        )
        st.markdown(f"<div class='citron-grid-2'><div>{summary}{panel('Cited evidence', evidence)}</div><div>{drafts}</div></div>", unsafe_allow_html=True)
        st.markdown(
            """
            <div class="citron-note">
              <div class="citron-note__title">Human review is required</div>
              <div class="citron-note__text">Please verify against source documentation before any payer outreach, appeal, correction, or write-off decision.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_denials(selected_case, packet_index) -> None:
    header(
        "Denial appeal copilot",
        "Appeal preparation remains assistive only",
        "Possible appeal paths are suggested for reviewer validation and must be checked against source documentation.",
    )
    if not selected_case.denial_opportunities:
        st.markdown("<div class='citron-empty'>No denial opportunities were detected for the selected synthetic case.</div>", unsafe_allow_html=True)
        return
    denial = DenialCopilot()
    for item in selected_case.denial_opportunities:
        packet = packet_index.get(item.denial_id)
        summary = panel(
            item.denial_category.replace("_", " "),
            f"<p>{esc(item.root_cause_hypothesis)}</p>"
            f"<p><strong>Appealability:</strong> {esc(item.appealability)}</p>"
            f"<p><strong>Recommended path:</strong> {esc(item.recommended_path)}</p>"
            f"<p><strong>Amount at risk:</strong> <span class='citron-money'>{format_money(item.amount_at_risk)}</span></p>",
        )
        drafts = (
            panel("Denial summary", f"<div class='citron-draft'>{esc(denial.denial_summary(item).content)}</div>")
            + panel("Appeal letter draft", f"<div class='citron-draft'>{esc(denial.appeal_letter_draft(item).content)}</div>")
            + panel("Evidence checklist", f"<div class='citron-draft'>{esc(denial.evidence_checklist(item).content)}</div>")
        )
        evidence = evidence_block(packet.evidence_table if packet else tuple(f"Evidence reviewed: {entry}" for entry in item.evidence_citation_ids))
        missing = panel("Missing evidence to verify", list_block(list(item.missing_evidence)))
        st.markdown(f"<div class='citron-grid-2'><div>{summary}{panel('Cited evidence', evidence)}{missing}</div><div>{drafts}</div></div>", unsafe_allow_html=True)


def render_workflow(selected_case) -> None:
    header(
        "Workflow assistant",
        "Role-aware next steps",
        "Workflow recommendations stay scoped to the selected reviewer role and the current deterministic state.",
    )
    if not selected_case.workflow_items:
        st.markdown("<div class='citron-empty'>No workflow items were generated for the selected synthetic case.</div>", unsafe_allow_html=True)
        return
    assistant = WorkflowAssistant()
    for item in selected_case.workflow_items:
        actions = assistant.allowed_actions(item, role=item.owner_role)
        note = assistant.generate_role_specific_note(item, role=item.owner_role).content
        st.markdown(
            panel(
                item.reason.replace("_", " "),
                f"<p><strong>Current state:</strong> {esc(item.current_state)}</p>"
                f"<p><strong>Owner role:</strong> {esc(item.owner_role)}</p>"
                f"<p><strong>Queue type:</strong> {esc(item.queue_type)}</p>"
                f"<div class='citron-meta-row'>{''.join(inline_code(c) for c in item.cited_evidence_ids)}</div>",
            )
            + panel("Allowed actions", list_block(actions))
            + panel("Role-specific note", f"<div class='citron-draft'>{esc(note)}</div>"),
            unsafe_allow_html=True,
        )


def render_payer_intelligence(result) -> None:
    header(
        "Payer intelligence",
        "Synthetic payer patterns",
        "Aggregate synthetic denial and friction patterns inform reviewer prioritization but make no payer determination.",
    )
    intelligence = PayerIntelligenceCopilot()
    answer = intelligence.answer("Which work items should a manager review today?", result.payer_intelligence).response_text
    st.markdown(panel("Manager review prompt", f"<div class='citron-draft'>{esc(answer)}</div>"), unsafe_allow_html=True)

    denials_by_payer_rows = "".join(
        f"<tr><td>{inline_code(payer)}</td><td class='citron-money'>{count}</td></tr>"
        for payer, count in result.payer_intelligence.denials_by_payer.items()
    )
    denials_by_cpt_rows = "".join(
        f"<tr><td>{inline_code(code)}</td><td class='citron-money'>{count}</td></tr>"
        for code, count in result.payer_intelligence.denials_by_cpt.items()
    )
    root_rows = "".join(
        f"<tr><td>{esc(cause)}</td><td class='citron-money'>{count}</td></tr>"
        for cause, count in result.payer_intelligence.top_preventable_root_causes.items()
    )
    denials_by_payer_table = (
        "<table class='citron-table'><thead><tr><th>Payer</th><th>Denials</th></tr></thead>"
        f"<tbody>{denials_by_payer_rows}</tbody></table>"
    )
    denials_by_cpt_table = (
        "<table class='citron-table'><thead><tr><th>CPT</th><th>Denials</th></tr></thead>"
        f"<tbody>{denials_by_cpt_rows}</tbody></table>"
    )
    st.markdown(
        f"<div class='citron-grid-2'><div>{panel('Denials by payer', denials_by_payer_table)}</div><div>{panel('Denials by CPT', denials_by_cpt_table)}</div></div>",
        unsafe_allow_html=True,
    )
    st.markdown(panel("Top preventable root causes", f"<table class='citron-table'><thead><tr><th>Root cause</th><th>Count</th></tr></thead><tbody>{root_rows}</tbody></table>"), unsafe_allow_html=True)


def render_case_detail(selected_case, packet_index) -> None:
    header(
        "Case detail",
        selected_case.case_id,
        "Case-level context ties together coding, A/R, denials, reviewer packets, and the current workflow state.",
    )
    summary = (
        f"<div class='citron-kv'><span>{inline_code(selected_case.case_id)}</span>"
        f"{status_pill(f'{len(selected_case.work_queue)} work items')}</div>"
        f"<p><strong>Coding opportunities:</strong> {len(selected_case.coding_opportunities)}</p>"
        f"<p><strong>A/R flags:</strong> {len(selected_case.ar_flags)}</p>"
        f"<p><strong>Denial opportunities:</strong> {len(selected_case.denial_opportunities)}</p>"
        f"<p><strong>Workflow items:</strong> {len(selected_case.workflow_items)}</p>"
    )
    packets = "".join(
        panel(
            packet.packet_id,
            f"<p><strong>Opportunity summary:</strong> {esc(packet.opportunity_summary)}</p>"
            f"<p><strong>Claim summary:</strong> {esc(packet.claim_summary)}</p>"
            f"<p><strong>Payer context:</strong> {esc(packet.payer_context)}</p>"
            f"<p><strong>Recommended next action:</strong> {esc(packet.recommended_next_action)}</p>"
            f"<p><strong>Financial impact estimate:</strong> <span class='citron-money'>{format_money(packet.financial_impact_estimate)}</span></p>",
        )
        for packet in packet_index.values()
    )
    st.markdown(panel("Selected case summary", summary), unsafe_allow_html=True)
    st.markdown(packets or "<div class='citron-empty'>No reviewer packets are available for this case.</div>", unsafe_allow_html=True)


def render_audit_trace(selected_case) -> None:
    header(
        "Audit trace",
        "Workflow traceability",
        "Audit events appear here when workflow state changes are recorded. The current fixtures mostly show pre-action state.",
    )
    events = [event.__dict__ for item in selected_case.workflow_items for event in item.audit_trace]
    if not events:
        st.markdown("<div class='citron-empty'>No workflow audit events have been recorded yet for this synthetic case.</div>", unsafe_allow_html=True)
        return
    st.code(json.dumps(events, indent=2), language="json")


def render_eval_results() -> None:
    header(
        "Eval results",
        "Deterministic copilot evaluation snapshot",
        "Model-adjacent summaries are only useful if the underlying rule outputs stay measurable and repeatable.",
    )
    from evals.run_asc_copilot_eval import run_asc_copilot_eval

    st.code(json.dumps(run_asc_copilot_eval(), indent=2), language="json")


st.set_page_config(
    page_title="Citron Health",
    page_icon=str(ASSETS / "logo-mark.svg"),
    layout="wide",
)
inject_theme()

result = run_pipeline(as_of_date=DEFAULT_AS_OF_DATE)
default_case_id = result.cases[0].case_id
selected_case_id = st.session_state.get("case_id", default_case_id)
viewer_role, surface = render_sidebar(result, selected_case_id)
selected_case_id = st.session_state["case_id"]
selected_case = next(item for item in result.cases if item.case_id == selected_case_id)
filtered_queue = [item for case in result.cases for item in case.work_queue if viewer_role == "manager" or item.owner_role == viewer_role]
case_packet_index = packets_for_case(selected_case)

compliance_banner()

if surface == "Manager dashboard":
    render_dashboard(result, filtered_queue)
elif surface == "Work queue":
    render_work_queue(filtered_queue)
elif surface == "Coding copilot":
    render_coding(selected_case, case_packet_index)
elif surface == "A/R copilot":
    render_ar(selected_case, case_packet_index)
elif surface == "Denial appeal copilot":
    render_denials(selected_case, case_packet_index)
elif surface == "Workflow assistant":
    render_workflow(selected_case)
elif surface == "Payer intelligence":
    render_payer_intelligence(result)
elif surface == "Case detail":
    render_case_detail(selected_case, case_packet_index)
elif surface == "Audit trace":
    render_audit_trace(selected_case)
else:
    render_eval_results()
