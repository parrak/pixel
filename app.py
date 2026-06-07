from __future__ import annotations

import json
from functools import lru_cache
from html import escape
from pathlib import Path
from urllib.parse import parse_qs

from asc_rcm_lite.operations import simulate_acquisition
from asc_rcm_lite.pipeline import DEFAULT_AS_OF_DATE, PipelineResult, run_pipeline


LOGO_MARK = Path(__file__).resolve().parent / "ui" / "assets" / "logo-mark.svg"


def _logo_svg() -> str:
    return LOGO_MARK.read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def _load_result() -> PipelineResult:
    return run_pipeline(as_of_date=DEFAULT_AS_OF_DATE)


def _selected_case(case_id: str | None):
    result = _load_result()
    if case_id:
        for case in result.cases:
            if case.case_id == case_id:
                return case
    return next((case for case in result.cases if case.operational_tasks), result.cases[0])


def _json_response(start_response, payload: object, status: str = "200 OK"):
    body = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
    start_response(
        status,
        [
            ("Content-Type", "application/json; charset=utf-8"),
            ("Content-Length", str(len(body))),
            ("Cache-Control", "public, max-age=60"),
        ],
    )
    return [body]


def _html_response(start_response, body: str, status: str = "200 OK"):
    raw = body.encode("utf-8")
    start_response(
        status,
        [
            ("Content-Type", "text/html; charset=utf-8"),
            ("Content-Length", str(len(raw))),
            ("Cache-Control", "public, max-age=60"),
        ],
    )
    return [raw]


def _serialize_case(case_result) -> dict[str, object]:
    return {
        "case_id": case_result.case_id,
        "operational_tasks": [
            {
                "task_id": task.task_id,
                "organization": task.organization_name,
                "facility": task.facility_name,
                "team": task.team_name,
                "assignee": task.assignee_name,
                "workflow": task.workflow_name,
                "priority": task.priority_band,
                "amount_at_risk": str(task.amount_at_risk),
                "recommendation": task.recommendations[0].title,
                "history": [
                    {
                        "decision": record.decision.decision,
                        "actor": record.decision.actor_name,
                        "outcome": record.outcome.status,
                        "financial_result": str(record.outcome.financial_result),
                        "resolution_time_hours": record.outcome.resolution_time_hours,
                    }
                    for record in task.history
                ],
            }
            for task in case_result.operational_tasks
        ],
    }


def _landing_page() -> str:
    result = _load_result()
    portfolio = result.portfolio_snapshot
    holdco = portfolio["holdco"]
    holdco_dashboard = portfolio["holdco_dashboard"]
    logo = _logo_svg()
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Citron Health HoldCo Command Center</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@400;500;600;700;800&family=IBM+Plex+Mono:wght@400;500;600&display=swap');
    :root {{
      --canvas: #fafaf7;
      --surface: rgba(255, 255, 255, 0.92);
      --surface-2: #f5f6f2;
      --ink-900: #15201c;
      --ink-500: #69756e;
      --border: #e6e8e1;
      --pine-700: #0f5240;
      --pine-600: #15634d;
      --citron-500: #cfe84f;
      --shadow-sm: 0 1px 3px rgba(20, 32, 28, 0.06), 0 1px 2px rgba(20, 32, 28, 0.04);
      --shadow-md: 0 4px 12px -2px rgba(20, 32, 28, 0.08), 0 2px 6px -2px rgba(20, 32, 28, 0.05);
    }}
    body {{
      margin: 0;
      font-family: "Hanken Grotesk", ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--ink-900);
      background:
        radial-gradient(circle at 0% 0%, rgba(207, 232, 79, 0.22), transparent 26rem),
        radial-gradient(circle at 100% 20%, rgba(15, 118, 110, 0.10), transparent 24rem),
        linear-gradient(180deg, #fbfbf8 0%, var(--canvas) 100%);
    }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 28px 18px 48px; }}
    .brand-lockup {{
      display: inline-flex;
      align-items: center;
      gap: .85rem;
      margin-bottom: 1rem;
    }}
    .brand-mark {{
      width: 2.75rem;
      height: 2.75rem;
      border-radius: 12px;
      overflow: hidden;
      flex: 0 0 auto;
    }}
    .brand-mark svg {{
      width: 100%;
      height: 100%;
      display: block;
    }}
    .brand-wordmark {{
      display: flex;
      flex-direction: column;
      gap: .06rem;
    }}
    .brand-title {{
      font-size: 1.12rem;
      font-weight: 800;
      letter-spacing: -.02em;
    }}
    .brand-title b {{
      color: var(--pine-600);
    }}
    .brand-subtitle {{
      color: var(--ink-500);
      font-size: .72rem;
      text-transform: uppercase;
      letter-spacing: .08em;
      font-weight: 700;
    }}
    .hero, .panel {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 28px;
      box-shadow: var(--shadow-md);
      padding: 28px;
    }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; margin-top: 18px; }}
    .metric {{ padding: 16px; border-radius: 20px; border: 1px solid var(--border); background: var(--surface-2); box-shadow: var(--shadow-sm); }}
    .metric strong {{ display: block; font-size: 2rem; }}
    .button {{ display: inline-block; margin-right: 12px; margin-top: 12px; padding: 12px 18px; border-radius: 999px; text-decoration: none; border: 1px solid var(--border); font-weight: 700; color: var(--ink-900); }}
    .primary {{ background: var(--pine-600); color: white; border-color: var(--pine-600); }}
    p, li {{ color: var(--ink-500); line-height: 1.6; }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <div class="brand-lockup">
        <div class="brand-mark">{logo}</div>
        <div class="brand-wordmark">
          <div class="brand-title">Citron<b> Health</b></div>
          <div class="brand-subtitle">HoldCo Command Center</div>
        </div>
      </div>
      <div style="text-transform:uppercase;letter-spacing:.08em;color:var(--pine-600);font-size:.88rem;font-weight:700;">Citron Health Phase 4</div>
      <h1 style="font-size:clamp(2.4rem,5vw,4.8rem);line-height:.95;margin:.4rem 0 1rem;">HoldCo Command Center for Specialty Revenue Cycle</h1>
      <p>{escape(holdco["thesis"])}</p>
      <p>Citron sits above EHRs, PM systems, payer portals, and clearinghouses to standardize acquired operators, turn workflow changes into EBITDA, and compound reusable knowledge across the portfolio.</p>
      <a class="button primary" href="/demo">Open HoldCo Demo</a>
      <a class="button" href="/api/summary">View Portfolio Summary</a>
    </section>
    <section class="grid">
      <article class="metric"><div>Portfolio revenue</div><strong>${escape(holdco_dashboard["portfolio_revenue"])}</strong></article>
      <article class="metric"><div>Portfolio EBITDA</div><strong>${escape(holdco_dashboard["portfolio_ebitda"])}</strong></article>
      <article class="metric"><div>Revenue at risk</div><strong>${escape(holdco_dashboard["revenue_at_risk"])}</strong></article>
      <article class="metric"><div>Open work</div><strong>{escape(str(holdco_dashboard["open_work"]))}</strong></article>
    </section>
    <section class="panel" style="margin-top:18px;">
      <h2>What Phase 4 adds</h2>
      <ul>
        <li>HoldCo dashboard for portfolio revenue, EBITDA, bottlenecks, and operating risk</li>
        <li>Value creation system tied to expected and realized EBITDA impact</li>
        <li>Portfolio benchmarking and reusable operating playbooks</li>
        <li>Executive operating review with risks, wins, and required decisions</li>
        <li>Acquisition integration center tied to standardization and enterprise value</li>
      </ul>
    </section>
  </main>
</body>
</html>
"""


def _demo_page(selected_case_id: str | None = None) -> str:
    result = _load_result()
    portfolio = result.portfolio_snapshot
    monday = portfolio["monday_morning"]
    holdco_dashboard = portfolio["holdco_dashboard"]
    executive_review = portfolio["executive_operating_review"]
    selected = _selected_case(selected_case_id)
    selected_task = selected.operational_tasks[0]
    logo = _logo_svg()
    role_rows = "".join(
        f"<tr><td>{escape(view['label'])}</td><td>{escape(str(view['queue_size']))}</td><td>${escape(view['revenue_at_risk'])}</td><td>${escape(view['financial_result'])}</td></tr>"
        for view in portfolio["role_views"]
    )
    history_rows = "".join(
        f"<tr><td>{escape(record.decision.actor_name)}</td><td>{escape(record.decision.decision)}</td><td>{escape(record.outcome.status)}</td><td>${escape(str(record.outcome.financial_result))}</td><td>{escape(str(record.outcome.resolution_time_hours))}</td></tr>"
        for record in selected_task.history
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Citron Health HoldCo Demo</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@400;500;600;700;800&family=IBM+Plex+Mono:wght@400;500;600&display=swap');
    :root {{
      --canvas: #fafaf7;
      --surface: rgba(255, 255, 255, 0.92);
      --surface-2: #f5f6f2;
      --ink-900: #15201c;
      --ink-500: #69756e;
      --border: #e6e8e1;
      --pine-700: #0f5240;
      --pine-600: #15634d;
      --warning-100: #fbf0dc;
      --warning-700: #97600f;
      --shadow-sm: 0 1px 3px rgba(20, 32, 28, 0.06), 0 1px 2px rgba(20, 32, 28, 0.04);
      --shadow-md: 0 4px 12px -2px rgba(20, 32, 28, 0.08), 0 2px 6px -2px rgba(20, 32, 28, 0.05);
    }}
    body {{
      margin: 0;
      font-family: "Hanken Grotesk", ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--ink-900);
      background:
        radial-gradient(circle at top left, rgba(207, 232, 79, 0.22), transparent 28rem),
        linear-gradient(180deg, #fbfbf8 0%, var(--canvas) 100%);
    }}
    main {{ max-width: 1200px; margin: 0 auto; padding: 32px 20px 48px; }}
    .brand-lockup {{
      display: inline-flex;
      align-items: center;
      gap: .85rem;
      margin-bottom: 1rem;
    }}
    .brand-mark {{
      width: 2.75rem;
      height: 2.75rem;
      border-radius: 12px;
      overflow: hidden;
      flex: 0 0 auto;
    }}
    .brand-mark svg {{
      width: 100%;
      height: 100%;
      display: block;
    }}
    .brand-wordmark {{
      display: flex;
      flex-direction: column;
      gap: .06rem;
    }}
    .brand-title {{
      font-size: 1.12rem;
      font-weight: 800;
      letter-spacing: -.02em;
    }}
    .brand-title b {{ color: var(--pine-600); }}
    .brand-subtitle {{
      color: var(--ink-500);
      font-size: .72rem;
      text-transform: uppercase;
      letter-spacing: .08em;
      font-weight: 700;
    }}
    .hero, .card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 24px;
      padding: 24px;
      box-shadow: var(--shadow-md);
    }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-top: 18px; }}
    .two-col {{ display: grid; grid-template-columns: 1.1fr .9fr; gap: 18px; margin-top: 18px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ text-align: left; padding: 10px 8px; border-bottom: 1px solid var(--border); vertical-align: top; }}
    .pill {{ display:inline-block;padding:8px 12px;border-radius:999px;background:var(--warning-100);border:1px solid rgba(151,96,15,.18);color:var(--warning-700);font-size:.92rem;font-weight:700; }}
    p, li {{ color: var(--ink-500); line-height: 1.6; }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <div class="brand-lockup">
        <div class="brand-mark">{logo}</div>
        <div class="brand-wordmark">
          <div class="brand-title">Citron<b> Health</b></div>
          <div class="brand-subtitle">HoldCo Command Center</div>
        </div>
      </div>
      <span class="pill">Synthetic data only. Human review required. No autonomous workflows.</span>
      <h1 style="margin:.75rem 0 1rem;">HoldCo Command Center inside Citron</h1>
      <p>{escape(monday['vp_user']['display_name'])}, {escape(monday['vp_user']['title'])}, opens Citron and sees a portfolio value-creation system rather than a detector screen.</p>
      <ul>{"".join(f"<li>{escape(line)}</li>" for line in holdco_dashboard["focus_today"])}</ul>
    </section>
    <section class="grid">
      <article class="card"><div>Portfolio revenue</div><h2>${escape(holdco_dashboard["portfolio_revenue"])}</h2></article>
      <article class="card"><div>Portfolio EBITDA</div><h2>${escape(holdco_dashboard["portfolio_ebitda"])}</h2></article>
      <article class="card"><div>Value creation progress</div><h2>{escape(str(holdco_dashboard["value_creation_progress"]["progress_pct"]))}%</h2></article>
      <article class="card"><div>Critical bottlenecks</div><h2>{escape(", ".join(holdco_dashboard["critical_bottlenecks"]))}</h2></article>
    </section>
    <section class="two-col">
      <article class="card">
        <h2>Role queues</h2>
        <table>
          <thead><tr><th>Role</th><th>Queue</th><th>Revenue at risk</th><th>Financial result</th></tr></thead>
          <tbody>{role_rows}</tbody>
        </table>
      </article>
      <article class="card">
        <h2>Selected task</h2>
        <p><strong>{escape(selected_task.title)}</strong></p>
        <p>{escape(selected_task.description)}</p>
        <p><strong>Organization:</strong> {escape(selected_task.organization_name or "")}<br>
        <strong>Facility:</strong> {escape(selected_task.facility_name or "")}<br>
        <strong>Assignee:</strong> {escape(selected_task.assignee_name or "")}<br>
        <strong>Recommendation:</strong> {escape(selected_task.recommendations[0].title)}</p>
      </article>
    </section>
    <section class="card" style="margin-top:18px;">
      <h2>Executive operating review</h2>
      <p><strong>Month:</strong> {escape(executive_review["month"])}</p>
      <p><strong>Required decisions:</strong> {escape(" | ".join(executive_review["required_decisions"]))}</p>
    </section>
    <section class="card" style="margin-top:18px;">
      <h2>Decision intelligence</h2>
      <table>
        <thead><tr><th>Actor</th><th>Decision</th><th>Outcome</th><th>Financial result</th><th>Resolution hours</th></tr></thead>
        <tbody>{history_rows}</tbody>
      </table>
    </section>
  </main>
</body>
</html>
"""


def app(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    query = parse_qs(environ.get("QUERY_STRING", ""))
    result = _load_result()

    if path == "/health":
        return _json_response(start_response, {"ok": True, "as_of_date": DEFAULT_AS_OF_DATE})

    if path == "/api/summary":
        return _json_response(
            start_response,
            {
                "as_of_date": DEFAULT_AS_OF_DATE,
                "operational_metrics": result.operational_metrics,
                "portfolio_snapshot": result.portfolio_snapshot,
                "cases": [item.case_id for item in result.cases],
            },
        )

    if path == "/api/portfolio":
        return _json_response(start_response, result.portfolio_snapshot)

    if path == "/api/holdco":
        return _json_response(
            start_response,
            {
                "holdco": result.portfolio_snapshot["holdco"],
                "holdco_dashboard": result.portfolio_snapshot["holdco_dashboard"],
                "value_creation_initiatives": result.portfolio_snapshot["value_creation_initiatives"],
                "portfolio_benchmarks": result.portfolio_snapshot["portfolio_benchmarks"],
                "playbooks": result.portfolio_snapshot["playbooks"],
                "executive_operating_review": result.portfolio_snapshot["executive_operating_review"],
                "decision_intelligence": result.portfolio_snapshot["decision_intelligence"],
            },
        )

    if path == "/api/case":
        case_id = query.get("case_id", [None])[0]
        if not case_id:
            return _json_response(start_response, {"error": "case_id query parameter is required"}, "400 Bad Request")
        for item in result.cases:
            if item.case_id == case_id:
                return _json_response(start_response, _serialize_case(item))
        return _json_response(start_response, {"error": f"unknown case_id: {case_id}"}, "404 Not Found")

    if path == "/api/acquisition":
        specialty = query.get("specialty", ["ASC"])[0]
        headcount = int(query.get("headcount", ["75"])[0])
        maturity = query.get("workflow_maturity", ["developing"])[0]
        systems = tuple(query.get("systems", ["EHR", "Practice Management", "Clearinghouse", "Payer Portals", "Spreadsheets"]))
        return _json_response(
            start_response,
            simulate_acquisition(
                specialty=specialty,
                headcount=headcount,
                workflow_maturity=maturity,
                systems=systems,
            ),
        )

    if path == "/" or path == "":
        return _html_response(start_response, _landing_page())

    if path == "/demo":
        selected = query.get("case_id", [None])[0]
        return _html_response(start_response, _demo_page(selected))

    return _json_response(start_response, {"error": "not found"}, "404 Not Found")
